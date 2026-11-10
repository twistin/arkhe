import { api, request, token } from '../api.js';
import { store } from '../state.js';
import { $, dialog, e, icon, toast } from '../ui.js';
import { cleanStudentText } from './material-alumnado.js';

let currentRun = null;
let currentSlides = [];
let currentIndex = 0;

export function buildSlides(run) {
  const context = run?.request?.pedagogy || {};
  const result = run?.result || {};
  const plan = result?.plan || {};
  const group = context?.group || {};
  const session = context?.session || {};
  const topic = run?.display_title || run?.title || run?.request?.display_title ||
    run?.request?.question || 'Presentación pedagógica';
  const byId = Object.fromEntries(
    (run?.evidence || []).filter(item => item?.source_id).map(item => [item.source_id, item])
  );
  const slides = [];

  const metaBadges = [];
  if (group.name) {
    const lvl = group.level ? ` (${group.level})` : '';
    metaBadges.push(`${group.name}${lvl}`);
  }
  if (context.duration_minutes) {
    metaBadges.push(`${context.duration_minutes} min`);
  }
  if (session.date) {
    metaBadges.push(String(session.date));
  }

  slides.push({
    tipo: 'portada',
    kicker: 'Presentación pedagógica · Arkhé',
    titulo: topic,
    subtitulo: 'Material docente estructurado para proyección en el aula',
    metadatos: metaBadges
  });

  const objectives = (plan.objectives || []).map(o => cleanStudentText(o, true)).filter(Boolean);
  if (objectives.length) {
    slides.push({
      tipo: 'objetivos',
      kicker: 'Hoja de ruta',
      titulo: '¿Qué vamos a trabajar hoy?',
      subtitulo: 'Objetivos de aprendizaje de la sesión',
      items: objectives
    });
  }

  const claims = result.claims || [];
  const resolvedById = Object.fromEntries(
    (result.resolved_music_requests || []).map(r => [r.request_id, r])
  );
  claims.forEach((claim, idx) => {
    const ctitle = claim.title || `Concepto ${idx + 1}`;
    const csummary = cleanStudentText(claim.student_summary || claim.text || '', false);
    const pts = (claim.key_points || []).map(p => String(p).trim()).filter(Boolean);
    let ejInfo = null;
    for (const exId of (claim.example_ids || [])) {
      const item = resolvedById[exId] || {};
      const ej = item.ejemplo || {};
      if (item.status === 'resuelto_repertorio' && ej.obra) {
        ejInfo = {
          obra: [ej.obra, ej.seccion].filter(Boolean).join(' · '),
          compositor: ej.compositor || '',
          compases: ej.compases || '1-8',
          que_observar: ej.que_observar || ''
        };
        break;
      }
    }
    slides.push({
      tipo: 'concepto',
      kicker: `Contenido clave ${String(idx + 1).padStart(2, '0')}`,
      titulo: ctitle,
      resumen: csummary,
      puntos_clave: pts,
      ejemplo: ejInfo
    });
  });

  const visuals = result.visualizations || [];
  visuals.forEach(visual => {
    slides.push({
      tipo: 'esquema',
      kicker: 'Esquema conceptual',
      titulo: visual.title || 'Estructura',
      caption: visual.caption || '',
      items: visual.items || []
    });
  });

  const didacticComps = result.resolved_didactic_components || [];
  didacticComps.forEach(dc => {
    const tipo = dc.tipo || '';
    const tit = dc.titulo || tipo.replace(/_/g, ' ');
    const items = [];
    if (tipo === 'monocordio') {
      (dc.divisiones || []).slice(0, 6).forEach(div => {
        items.push({
          label: `${div.fraccion || ''} (${div.proporcion || ''})`,
          detail: `${div.intervalo_moderno || ''} · ${Number(div.freq_hz || 0).toFixed(1)} Hz`
        });
      });
    } else if (tipo === 'tetracordos') {
      const afin = dc.afinacion_pitagorica || {};
      Object.values(afin.generos || {}).forEach(gen => {
        items.push({
          label: gen.nombre || '',
          detail: `${gen.formula || ''} (cents: ${(gen.cents || []).join(' + ')})`
        });
      });
    } else {
      items.push({
        label: 'Modelo acústico',
        detail: dc.descripcion || 'Cálculo determinista de teoría musical'
      });
    }
    slides.push({
      tipo: 'componente_didactico',
      kicker: 'Modelo didáctico determinista',
      titulo: tit,
      caption: dc.descripcion || '',
      items
    });
  });

  const activities = plan.activities || [];
  activities.forEach((act, idx) => {
    slides.push({
      tipo: 'actividad',
      kicker: `Actividad ${String(idx + 1).padStart(2, '0')} · ${act.minutes || 0} min`,
      titulo: act.title || `Actividad ${idx + 1}`,
      agrupamiento: act.grouping || 'En el aula',
      minutos: act.minutes || 0,
      consigna: cleanStudentText(act.student_task || act.instructions || '', true),
      recursos: act.materials || act.resources || []
    });
  });

  slides.push({
    tipo: 'cierre',
    kicker: 'Cierre de la sesión',
    titulo: 'Conclusiones y balance',
    subtitulo: 'Puntos esenciales fijados en el aula',
    items: [
      'Puesta en común de dudas y resultados del trabajo práctico.',
      'Síntesis de los conceptos clave abordados.',
      'Orientaciones y entrega para la siguiente sesión.'
    ]
  });

  return slides;
}

export function renderSlideCard(s, idx, total, groupName) {
  const kicker = s.kicker ? `<div class="slide-kicker-text">${e(s.kicker)}</div>` : '';
  const title = `<h2 class="slide-heading-text">${e(s.titulo || '')}</h2>`;
  const lead = s.subtitulo ? `<p class="slide-lead-text">${e(s.subtitulo)}</p>` : '';

  let body = '';
  if (s.tipo === 'portada') {
    const chips = (s.metadatos || []).map(m => `<span class="slide-chip">${e(m)}</span>`).join('');
    body = [
      lead,
      chips ? `<div class="slide-chips">${chips}</div>` : ''
    ].join('');
  } else if (s.tipo === 'objetivos' || s.tipo === 'cierre') {
    const iconMark = s.tipo === 'cierre' ? '✦' : '✓';
    const lis = (s.items || []).map(item => [
      `<li><span class="bullet-icon">${iconMark}</span><div>${e(item)}</div></li>`
    ].join('')).join('');
    body = [lead, `<ul class="slide-objectives-list">${lis}</ul>`].join('');
  } else if (s.tipo === 'concepto') {
    const quote = s.resumen ? `<div class="slide-quote-box"><p>${e(s.resumen)}</p></div>` : '';
    const pts = (s.puntos_clave || []).length ? [
      `<div class="slide-keypoints-box"><h4>Aspectos clave</h4><ul>`,
      (s.puntos_clave || []).map(p => `<li>${e(p)}</li>`).join(''),
      `</ul></div>`
    ].join('') : '';
    let ejHTML = '';
    if (s.ejemplo) {
      const ej = s.ejemplo;
      ejHTML = [
        `<div class="slide-example-panel"><strong>🎼 ${e(ej.obra)}</strong>`,
        ` — ${e(ej.compositor)} (c. ${e(ej.compases)})`,
        ej.que_observar ? `<p class="example-obs">${e(ej.que_observar)}</p>` : '',
        `</div>`
      ].join('');
    }
    body = `${quote}${pts}${ejHTML}`;
  } else if (s.tipo === 'esquema' || s.tipo === 'componente_didactico') {
    const cards = (s.items || []).map(itm => [
      `<div class="slide-schema-box"><strong>${e(itm.label || '')}</strong>`,
      `<p>${e(itm.detail || '')}</p></div>`
    ].join('')).join('');
    body = [lead, `<div class="slide-schema-container">${cards}</div>`].join('');
  } else if (s.tipo === 'actividad') {
    const meta = [
      `<div class="slide-activity-meta"><span class="slide-chip highlight">`,
      `⏱️ ${e(s.minutos)} minutos</span><span class="slide-chip">`,
      `Modalidad: ${e(s.agrupamiento)}</span></div>`
    ].join('');
    const task = [
      `<div class="slide-activity-task-box"><h4>Consigna de trabajo</h4>`,
      `<p>${e(s.consigna)}</p></div>`
    ].join('');
    body = `${meta}${task}`;
  }

  const foot = [
    `<footer class="slide-card-footer"><span>Arkhé · ${e(groupName || 'Espacio docente')}</span>`,
    `<span>${e(idx + 1)} / ${e(total)}</span></footer>`
  ].join('');

  return [
    `<div class="presentation-slide-card"><div class="slide-head-wrap">${kicker}${title}</div>`,
    `<div class="slide-body-container">${body}</div>${foot}</div>`
  ].join('');
}

export function presentationModalHTML(run, slideIndex) {
  const slides = currentSlides.length ? currentSlides : buildSlides(run);
  const total = slides.length;
  const idx = Math.max(0, Math.min(slideIndex, total - 1));
  const current = slides[idx] || {};
  const groupName = run?.request?.pedagogy?.group?.name || '';
  const progressPct = total > 0 ? ((idx + 1) / total) * 100 : 0;
  const title = run?.display_title || run?.title || 'Presentación para el aula';

  return [
    `<div class="presentation-app"><header class="presentation-toolbar">`,
    `<div class="presentation-toolbar-title"><span class="badge-pres">Proyector</span>`,
    `<span>${e(title)}</span></div><div class="presentation-toolbar-actions">`,
    `<button data-action="presentation-prev" aria-label="Anterior diapositiva" title="Anterior">`,
    `${icon('arrowleft')} Anterior</button><span class="presentation-counter" id="pres-counter">`,
    `${e(idx + 1)} / ${e(total)}</span><button data-action="presentation-next" `,
    `aria-label="Siguiente diapositiva" title="Siguiente">Siguiente ${icon('arrow')}</button>`,
    `<button data-action="toggle-presentation-fullscreen" title="Pantalla completa (F)">`,
    `${icon('screen')} Pantalla completa</button>`,
    `<button data-action="open-presentation-tab" data-run-id="${e(run?.id || '')}" `,
    `title="Abrir en pestaña nueva">${icon('external')} Pestaña</button>`,
    `<button data-action="download-presentation-html" data-run-id="${e(run?.id || '')}" `,
    `title="Descargar presentación HTML">${icon('download')} HTML</button>`,
    `<button data-action="download-presentation-md" data-run-id="${e(run?.id || '')}" `,
    `title="Descargar presentación Markdown">${icon('document')} MD</button>`,
    `<button data-action="print-presentation" title="Imprimir / PDF">${icon('record')} PDF</button>`,
    `<button class="danger" data-action="close-presentation" aria-label="Cerrar presentación" `,
    `title="Cerrar">${icon('close')}</button></div></header><main class="presentation-stage" `,
    `id="presentation-stage">${renderSlideCard(current, idx, total, groupName)}</main>`,
    `<div class="presentation-progress-bar"><div class="presentation-progress-fill" `,
    `id="pres-progress" style="width: ${e(progressPct.toFixed(1))}%;"></div></div></div>`
  ].join('');
}

export function updateSlide(newIndex) {
  if (!currentSlides.length) return;
  if (newIndex < 0) newIndex = 0;
  if (newIndex >= currentSlides.length) newIndex = currentSlides.length - 1;
  currentIndex = newIndex;

  const stage = $('#presentation-stage');
  const counter = $('#pres-counter');
  const progress = $('#pres-progress');
  const groupName = currentRun?.request?.pedagogy?.group?.name || '';

  if (stage && currentSlides[currentIndex]) {
    stage.innerHTML = renderSlideCard(
      currentSlides[currentIndex],
      currentIndex,
      currentSlides.length,
      groupName
    );
  }
  if (counter) {
    counter.textContent = `${currentIndex + 1} / ${currentSlides.length}`;
  }
  if (progress) {
    const pct = ((currentIndex + 1) / currentSlides.length) * 100;
    progress.style.width = `${pct.toFixed(1)}%`;
  }
}

export async function openPresentation(runId) {
  let run = store.currentRun?.id === runId ? store.currentRun : null;
  if (!run) {
    run = await api('/runs/' + encodeURIComponent(runId));
  }
  if (!run) throw new Error('No se pudo cargar la propuesta para proyectar.');

  currentRun = run;
  currentSlides = buildSlides(run);
  currentIndex = 0;

  dialog.innerHTML = presentationModalHTML(run, 0);
  dialog.classList.add('presentation-dialog');
  if (!dialog.open) {
    dialog.showModal();
  }
}

async function accionOpenPresentationRun({ target }) {
  const id = target.dataset.presentationRun;
  if (id) {
    await openPresentation(id);
  }
}

function accionPrevSlide() {
  updateSlide(currentIndex - 1);
}

function accionNextSlide() {
  updateSlide(currentIndex + 1);
}

function accionToggleFullscreen() {
  if (!document.fullscreenElement) {
    dialog.requestFullscreen?.().catch(() => {});
  } else {
    document.exitFullscreen?.().catch(() => {});
  }
}

function accionOpenPresentationTab({ target }) {
  const id = target.dataset.runId || currentRun?.id;
  if (id) {
    window.open(`/api/runs/${encodeURIComponent(id)}?presentation=1`, '_blank');
  }
}

async function accionDownloadPresentationHtml({ target }) {
  const id = target.dataset.runId || currentRun?.id;
  if (!id) return;
  const res = await request(`/api/runs/${encodeURIComponent(id)}?presentation=1&format=html`, {
    headers: { 'X-Docente-Token': token }
  });
  if (!res.ok) throw new Error('No se pudo generar la presentación HTML.');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `presentacion-${id}.html`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast('Presentación HTML descargada para proyección local.');
}

async function accionDownloadPresentationMd({ target }) {
  const id = target.dataset.runId || currentRun?.id;
  if (!id) return;
  const res = await request(`/api/runs/${encodeURIComponent(id)}?presentation=1&format=md`, {
    headers: { 'X-Docente-Token': token }
  });
  if (!res.ok) throw new Error('No se pudo generar la presentación Markdown.');
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `presentacion-${id}.md`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast('Presentación Markdown descargada.');
}

function accionPrintPresentation() {
  document.body.classList.add('presentation-printing');
  window.addEventListener('afterprint', () => {
    document.body.classList.remove('presentation-printing');
  }, { once: true });
  window.print();
}

function accionClosePresentation() {
  if (document.fullscreenElement) {
    document.exitFullscreen?.().catch(() => {});
  }
  dialog.classList.remove('presentation-dialog');
  dialog.close();
}

export const actions = {
  'open-presentation-run': accionOpenPresentationRun,
  'presentation-prev': accionPrevSlide,
  'presentation-next': accionNextSlide,
  'toggle-presentation-fullscreen': accionToggleFullscreen,
  'open-presentation-tab': accionOpenPresentationTab,
  'download-presentation-html': accionDownloadPresentationHtml,
  'download-presentation-md': accionDownloadPresentationMd,
  'print-presentation': accionPrintPresentation,
  'close-presentation': accionClosePresentation
};

export const clickBindings = [
  { priority: 4, matches: target => target.dataset.presentationRun, action: 'open-presentation-run' }
];

export const windowEvents = {
  keydown: event => {
    if (!dialog?.open || !dialog?.classList.contains('presentation-dialog')) return;
    if (event.key === 'ArrowRight' || event.key === ' ' || event.key === 'PageDown') {
      event.preventDefault();
      updateSlide(currentIndex + 1);
    } else if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
      event.preventDefault();
      updateSlide(currentIndex - 1);
    } else if (event.key === 'Home') {
      event.preventDefault();
      updateSlide(0);
    } else if (event.key === 'End') {
      event.preventDefault();
      updateSlide(currentSlides.length - 1);
    } else if (event.key === 'f' || event.key === 'F') {
      event.preventDefault();
      accionToggleFullscreen();
    } else if (event.key === 'Escape') {
      accionClosePresentation();
    }
  }
};
