// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  api
} from '../api.js';
import {
  store,
  view
} from '../state.js';
import {
  $,
  dialog,
  e,
  navigate,
  render,
  toast
} from '../ui.js';

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
      .status && ['done', 'failed'].includes(j.status));
    jobs.forEach(j => store.knownJobs.set(j.id, j.status));
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
    }
    if (completed.length) {
      await refresh();
      for (const job of completed) {
        if (job.status === 'failed') toast(job.error, true);
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
      toast('No hay conexión con Enjambre. Si lo has vuelto a abrir, recarga esta página.', true);
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
