import { $, dialog, e, navigate, render, toast } from '../ui.js';
import { api, jobEvents } from '../api.js';
import { store, view } from '../state.js';
// Módulo local: responsabilidad separada sin alterar el contenido.

export async function refresh(renderPage = true) {
  store.state = await api('/state');
  if (!store.state.config.subjects.some(s => s.id === store.selected)) store.selected = '';
  if (renderPage) render();
  $('#source-count').textContent = store.state.documents.length;
  return store.state;
}

export async function openRun(id) {
  store.currentRun = await api('/runs/' + encodeURIComponent(id));
  const route = store.currentRun.request.pedagogy ? 'propuestas' : 'asistente';
  if (view() !== route) navigate(route);
  else render();
  setTimeout(() => {
    $('.result')?.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }, 100);
}

export async function checkStatus() {
  store.modelStatus = await api('/status');
  const remote = store.state?.provider_info?.is_remote;
  const name = store.state?.provider_info?.name || 'Ollama';
  const label = name + (store.modelStatus.connected ? (remote ? ' · clave configurada' : ' conectado') : (
    remote ? ' · sin clave' : ' sin conexión'));
  $('#connection').innerHTML = [
    `<span class="status-dot ${store.modelStatus.connected?'':'offline'}"></span><span>${e(label)}</span>`
  ].join('');
  if (view() === 'ajustes') render();
}

export async function monitor() {
  if (store.polling) return;
  store.polling = true;
  try {
    if (store.isClosed) return;
    const jobs = await api('/jobs');
    store.connectionLost = false;
    const active = jobs.filter(j => ['queued', 'running'].includes(j.status));
    const completed = jobs.filter(j => store.knownJobs.has(j.id) && store.knownJobs.get(j.id) !== j
      .status && ['done', 'failed', 'cancelled'].includes(j.status));
    jobs.forEach(j => store.knownJobs.set(j.id, j.status));
    for (const job of jobs) {
      const preview = previews.get(job.id);
      if (preview && ['done', 'failed', 'cancelled'].includes(job.status)) {
        Object.assign(preview, {status: job.status, text: '', error: job.error});
        preview.controller?.abort();
      }
    }
    active.filter(j => j.cancellable).forEach(connectLive);
    for (const [id, preview] of previews) {
      if (!jobs.some(job => job.id === id)) {
        preview.controller?.abort();
        previews.delete(id);
      }
    }
    const tray = $('#job-tray');
    tray.hidden = !active.length;
    if (active.length) {
      const running = active.find(j => j.status === 'running') || active[0];
      tray.innerHTML = [
        `<span class="spinner"></span><div><strong>${e(running.title)}</strong><small>`,
        [
          `${
            running.progress ? [
              `${e(running.progress.done)} de ${e(running.progress.total)} fragmentos · `,
              `${e(Math.round(100*running.progress.done/running.progress.total))}% · `
            ].join('') : ''
          }`
        ].join(''),
        `${active.length>1?`${e(active.length-1)} en espera · `:''}`,
        `Puedes seguir trabajando en tu espacio.</small></div>`
      ].join('');
      if (running.cancellable) {
        const cancel = document.createElement('button');
        cancel.className = 'button secondary';
        cancel.dataset.action = 'cancel-job';
        cancel.dataset.job = running.id;
        cancel.textContent = 'Cancelar';
        tray.append(cancel);
      }
      tray.dataset.job = running.id;
      /* La vista conserva el panel independiente del aviso global. */
      renderLivePanel();

    }
    renderLivePanel();
    if (completed.length) {
      await refresh();
      for (const job of completed) {
        if (job.status === 'failed') toast(job.error, true);
        else if (job.status === 'cancelled') toast('Consulta cancelada.');
        else if (job.result?.run_id) {
          const result = store.state.runs.find(r => r.id === job.result.run_id),
            destination = result?.kind === 'proposal' ? 'propuestas' : 'asistente';
          if (view() === destination && !dialog.open) await openRun(job.result.run_id);
          else toast(destination === 'propuestas' ? 'Tu propuesta está lista en Propuestas.' :
            'La respuesta está lista en Asistente.');
        } else {
          toast(job.result?.status === 'failed' ? 'No se pudo extraer el documento. Revisa su ficha.' :
            'Biblioteca actualizada.', job.result?.status === 'failed');
        }
      }
    }
  } catch (error) {
    if (store.state && !store.connectionLost) {
      toast('No hay conexión con Arkhé. Si lo has vuelto a abrir, recarga esta página.', true);
      store.connectionLost = true;
    }
  } finally {
    store.polling = false;
  }
}

export async function queue(path, data) {
  const response = await api(path, data);
  store.knownJobs.set(response.job_id, 'new');
  await monitor();
  return response;
}

// Acciones y formularios de este módulo; delegación central en main.js.
async function accionOpenRun({target}) {
  if (dialog.open) dialog.close();
  await openRun(target.dataset.run);
}

async function accionCloseRun() {
  store.currentRun = null;
  render();
}

async function accionReload() {
  await refresh();
}

export const actions = {
  'open-run': accionOpenRun,
  'close-run': accionCloseRun,
  'reload': accionReload,
  'cancel-job': accionCancelJob,
  'dismiss-live': accionDismissLive,
};

export const clickBindings = [
  {priority: 2, matches: target => target.dataset.run, action: 'open-run'},
];


const previews = new Map();

function connectLive(job) {
  let preview = previews.get(job.id);
  if (!preview) {
    preview = {id: job.id, stage: job.title, text: '', cursor: 0, status: job.status, attempt: 0};
    previews.set(job.id, preview);
  }
  if (!['done', 'failed', 'cancelled'].includes(preview.status)) preview.status = job.status;
  if (preview.controller || ['done', 'failed', 'cancelled'].includes(preview.status)) return;
  const controller = new AbortController();
  preview.controller = controller;
  jobEvents(job.id, preview.cursor, event => receiveLive(preview, event), controller.signal)
    .catch(() => { /* El sondeo mantiene el resultado y vuelve a conectar el canal. */ })
    .finally(() => { preview.controller = null; });
}

function receiveLive(preview, {id, event, data}) {
  preview.cursor = id;
  if (event === 'snapshot') Object.assign(preview, data, {stage: data.title});
  if (event === 'stage') preview.stage = data.message;
  if (event === 'relevance') {
    const phase = data.phase === 'completed' ? 'Revisado' : 'Revisando';
    preview.stage = `${phase}: lote ${data.batch} de ${data.total}`;
  }
  if (event === 'attempt') {
    preview.text = '';
    preview.tokens = null;
    preview.attempt = data.attempt;
  }
  if (event === 'repair') {
    preview.text = '';
    preview.stage = `Corrigiendo respuesta: intento ${data.attempt} de ${data.total}`;
  }
  if (event === 'token') preview.text = (preview.text + data.text).slice(0, 100000);
  if (event === 'streaming') preview.streaming = data.enabled;
  if (event === 'usage') preview.tokens = data.tokens;
  if (event === 'terminal') {
    preview.text = '';
    preview.status = data.status;
    preview.error = data.error;
    if (data.status === 'done') preview.controller?.abort();
    void monitor();
  }
  renderLivePanel();
}

// Extraer únicamente texto de claims, incluso mientras la cadena JSON está incompleta.
// El contenido siempre se asigna a textContent; no se interpreta HTML ni Markdown provisional.
function provisionalText(raw) {
  const texts = [];
  const pattern = /"text"\s*:\s*"((?:[^"\\]|\\.)*)/g;
  for (const match of raw.matchAll(pattern)) {
    let text = match[1];
    if (text.endsWith('\\')) text = text.slice(0, -1);
    text = text.replace(/\\u[0-9a-f]{0,3}$/i, '');
    try { texts.push(JSON.parse('"' + text + '"')); } catch {}
  }
  return texts.join('\n\n');
}

function renderLivePanel() {
  if (!['asistente', 'propuestas'].includes(view())) {
    $('#live-panel')?.remove();
    return;
  }
  const preview = [...previews.values()].at(-1);
  if (!preview || preview.status === 'done') {
    $('#live-panel')?.remove();
    return;
  }
  const panel = $('#live-panel') || document.createElement('section');
  panel.id = 'live-panel';
  panel.className = 'live-panel card';
  panel.setAttribute('aria-label', 'Progreso de la consulta');
  const title = panel.querySelector('h2') || document.createElement('h2');
  const notice = panel.querySelector('.live-notice') || document.createElement('p');
  const progress = panel.querySelector('.live-progress') || document.createElement('p');
  const content = panel.querySelector('.live-text') || document.createElement('div');
  notice.className = 'live-notice';
  title.textContent = 'Borrador sin verificar';
  notice.textContent = 'Puede contener errores. El resultado final se mostrará después de comprobar sus citas.';
  progress.className = 'live-progress';
  progress.setAttribute('role', 'status');
  const count = preview.tokens == null ? `${preview.text.length} caracteres recibidos` :
    `${preview.tokens} tokens generados`;
  progress.textContent = `${preview.stage} · Intento ${preview.attempt || 1} · ${count}`;
  content.className = 'live-text';
  content.textContent = provisionalText(preview.text) || (preview.streaming === false ?
    'Este proveedor entrega el texto al terminar; se siguen mostrando las etapas y reparaciones.' :
    'Esperando texto del modelo…');
  if (!panel.children.length) panel.append(title, notice, progress, content);
  const finished = ['failed', 'cancelled'].includes(preview.status);
  const button = panel.querySelector('button') || document.createElement('button');
  button.className = 'button secondary';
  button.dataset.job = preview.id;
  button.dataset.action = finished ? 'dismiss-live' : 'cancel-job';
  button.textContent = finished ? 'Cerrar aviso' : 'Cancelar consulta';
  button.disabled = Boolean(preview.cancelling && !finished);
  if (finished) {
    title.textContent = preview.status === 'cancelled' ? 'Consulta cancelada' : 'Consulta fallida';
    notice.textContent = preview.error || 'No se ha publicado ningún resultado provisional.';
    content.textContent = '';
  }
  progress.hidden = finished;
  content.hidden = finished;
  if (!button.parentNode) panel.append(button);
  if (!panel.parentNode) {
    $('#main')?.prepend(panel);
  }

}

async function accionCancelJob({target}) {
  const id = target.dataset.job;
  const result = await api('/jobs/' + encodeURIComponent(id) + '/cancel', {});
  if (result.accepted) {
    const preview = previews.get(id);
    if (preview) preview.cancelling = true;
    target.disabled = true;
  }
}

function accionDismissLive({target}) {
  previews.delete(target.dataset.job);
  renderLivePanel();
}

document.addEventListener('enjambre:render', () => queueMicrotask(renderLivePanel));
