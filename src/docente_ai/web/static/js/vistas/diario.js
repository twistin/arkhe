import { refresh } from '../componentes/trabajos.js';
import { dialog, toast, e, header, icon, modal, option, primary, render, subjectStyle } from '../ui.js';
import { api, request } from '../api.js';
import { store } from '../state.js';
// Módulo local: responsabilidad separada sin alterar el contenido.

let currentViewMode = 'planner';

export function diary() {
  const records = store.state.records || [];
  const planner = store.state.planner;

  const modeTabs = [
    `<nav class="planner-mode-tabs" aria-label="Modo de vista">`,
    `  <button class="planner-tab-btn ${currentViewMode === 'planner' ? 'active' : ''}" ` +
      `data-action="set-planner-mode" data-mode="planner">`,
    `    ${icon('document')} Planificador semanal`,
    `  </button>`,
    `  <button class="planner-tab-btn ${currentViewMode === 'history' ? 'active' : ''}" ` +
      `data-action="set-planner-mode" data-mode="history">`,
    `    ${icon('record')} Historial de registros (${e(records.length)})`,
    `  </button>`,
    `</nav>`
  ].join('');

  const bodyContent = currentViewMode === 'planner'
    ? renderPlannerWeek(planner)
    : renderHistoryList(records);

  return header('ESPACIO DEL PROFESOR', 'Planificador y diario docente.',
      'Organiza tus sesiones semanales, vincula propuestas y registra lo ocurrido en el aula.', primary(
        'Registrar otra sesión', 'new-feedback', 'record')) +
    modeTabs +
    bodyContent;
}

function renderHistoryList(records) {
  return [
    `<section class="folder-banner diary-folder"><div class="folder-symbol">${icon('folder')}`,
    `</div><div class="folder-copy"><h3>Material de sesiones ordenado por fecha</h3>`,
    `<p>Guías, material del alumnado, anexos y feedback se guardan en 03 Diario `,
    `docente.</p></div><button class="button ghost" data-action="reveal-diary">Abrir carpeta `,
    `${icon('external')}</button></section>`
  ].join('') +
  (records.length ? `<div class="diary-list">${records.map(entradaDiario).join('')}</div>` : [
    `<section class="empty-library diary-empty"><div class="onboarding-mark">${icon('record')}</div>`,
    `<h2>Tu experiencia también forma parte del sistema.</h2><p>Después de cada `,
    `clase, anota qué funcionó, qué cambiarías y por dónde continuar.</p>`,
    `${primary('Registrar la primera sesión','new-feedback','record')}</section>`
  ].join(''));
}

function renderPlannerWeek(planner) {
  if (!planner || !planner.days || !planner.days.length) {
    return [
      `<section class="empty-library diary-empty">`,
      `<div class="onboarding-mark">${icon('record')}</div>`,
      `<h2>Sin horario configurado para esta semana.</h2>`,
      `<p>Define tus grupos y reglas de horario en Ajustes para ver la planificación semanal.</p>`,
      `</section>`
    ].join('');
  }

  const navBar = [
    `<div class="planner-nav-bar">`,
    `  <div class="planner-nav-left">`,
    `    <button class="button small ghost" data-action="planner-prev" ` +
      `data-date="${e(planner.prev_week)}" title="Semana anterior">`,
    `      ${icon('arrowleft')} Anterior`,
    `    </button>`,
    `    <button class="button small ghost" data-action="planner-today" title="Ir a la semana actual">`,
    `      Hoy`,
    `    </button>`,
    `    <button class="button small ghost" data-action="planner-next" ` +
      `data-date="${e(planner.next_week)}" title="Semana siguiente">`,
    `      Siguiente ${icon('arrow')}`,
    `    </button>`,
    `  </div>`,
    `  <div class="planner-nav-center">`,
    `    <h3 class="planner-week-title">${e(planner.week_label)}</h3>`,
    `  </div>`,
    `  <div class="planner-nav-right">`,
    `    <label class="planner-date-picker-label" title="Saltar a una fecha concreta">`,
    `      <span>Ir a:</span>`,
    `      <input type="date" class="input input-small planner-date-input" ` +
      `data-action="planner-jump-date" value="${e(planner.selected_date)}">`,
    `    </label>`,
    `    <button class="button small ghost" data-action="download-calendar" ` +
      `title="Descargar horario completo en formato iCalendar (.ics)">`,
    `      ${icon('download')} Horario .ics`,
    `    </button>`,
    `  </div>`,
    `</div>`
  ].join('');

  const daysHTML = planner.days.map(renderPlannerDay).join('');

  return [
    `<section class="planner-section">`,
    navBar,
    `<div class="planner-week-grid">${daysHTML}</div>`,
    `</section>`
  ].join('');
}

function renderPlannerDay(day) {
  const isTodayClass = day.is_today ? ' is-today' : '';
  const eventsHTML = (day.events || []).map(ev => [
    `<div class="planner-event-card priority-${e(ev.prioridad || 'normal')}">`,
    `<span class="planner-event-time">${e(ev.hora || 'Evento')}</span>`,
    `<strong class="planner-event-title">${e(ev.titulo)}</strong>`,
    `</div>`
  ].join('')).join('');

  const sessionsHTML = (day.sessions && day.sessions.length)
    ? day.sessions.map(renderPlannerSessionCard).join('')
    : `<div class="planner-empty-day"><span class="muted-small">Sin clases</span></div>`;

  return [
    `<div class="planner-day-col${isTodayClass}">`,
    `  <div class="planner-day-header">`,
    `    <span class="planner-day-name">${e(day.weekday_name)}</span>`,
    `    <strong class="planner-day-num">${e(day.day_label)}</strong>`,
    `    ${day.is_today ? '<span class="today-chip">Hoy</span>' : ''}`,
    `  </div>`,
    eventsHTML ? `<div class="planner-day-events">${eventsHTML}</div>` : '',
    `  <div class="planner-day-sessions">${sessionsHTML}</div>`,
    `</div>`
  ].join('');
}

function renderPlannerSessionCard(s) {
  const start = new Date(s.start);
  const end = new Date(s.end);
  const tStart = start.toLocaleTimeString('es', {hour: '2-digit', minute: '2-digit'});
  const tEnd = end.toLocaleTimeString('es', {hour: '2-digit', minute: '2-digit'});
  const timeStr = `${tStart} – ${tEnd}`;
  const subjId = s.subject_id || 'none';
  const styleStr = subjectStyle(subjId);

  let proposalBlock = '';
  if (s.proposal) {
    const isReady = s.proposal.status !== 'draft';
    const obrasBadge = s.proposal.music_examples_count
      ? `<span class="resource-badge" title="${e(s.proposal.music_examples_count)} obras">` +
        `${icon('document')}${e(s.proposal.music_examples_count)}</span>`
      : '';
    const compBadge = s.proposal.components_count
      ? `<span class="resource-badge" title="Componente interactivo">${icon('spark')}</span>`
      : '';
    proposalBlock = [
      `<div class="planner-card-proposal">`,
      `  <div class="planner-prop-head">`,
      `    <span class="badge ${isReady ? 'ready' : 'pending'}">${isReady ? 'Guía lista' : 'Borrador'}</span>`,
      `    ${obrasBadge}`,
      `    ${compBadge}`,
      `  </div>`,
      `  <strong class="planner-prop-title" title="${e(s.proposal.title)}">${e(s.proposal.title)}</strong>`,
      `  <div class="planner-prop-actions">`,
      `    <button class="button small ghost" data-expand-proposal="${e(s.proposal.id)}">Guía docente</button>`,
      `    <button class="button small ghost" data-student-run="${e(s.proposal.id)}">Alumnado</button>`,
      `    <button class="button small ghost" data-presentation-run="${e(s.proposal.id)}">Proyectar</button>`,
      `  </div>`,
      `</div>`
    ].join('');
  } else {
    const unitTitle = s.curriculum_unit ? `Programación: ${s.curriculum_unit.title}` : 'Sin propuesta preparada';
    proposalBlock = [
      `<div class="planner-card-proposal-empty">`,
      `  <small class="muted-small planner-unit-hint" title="${e(unitTitle)}">${e(unitTitle)}</small>`,
      `  <button class="button small primary planner-prepare-btn" data-prepare-session="${e(s.id)}">`,
      `    ${icon('spark')} Preparar sesión`,
      `  </button>`,
      `</div>`
    ].join('');
  }

  let recordBlock = '';
  if (s.record) {
    const noteText = s.record.what_worked || s.record.next_session_note || s.record.topic || 'Feedback registrado';
    recordBlock = [
      `<div class="planner-card-record recorded">`,
      `  <div class="planner-record-head">`,
      `    <span class="badge badge-success">✓ En diario</span>`,
      `    <button class="icon-button small" data-session-record="${e(s.record.id)}" ` +
        `title="Editar feedback" aria-label="Editar feedback">${icon('edit')}</button>`,
      `  </div>`,
      `  <p class="planner-record-snippet">${e(noteText)}</p>`,
      `</div>`
    ].join('');
  } else {
    recordBlock = [
      `<div class="planner-card-record empty">`,
      `  <button class="button small ghost planner-feedback-btn" data-feedback-session="${e(s.id)}">`,
      `    ${icon('record')} Anotar clase`,
      `  </button>`,
      `</div>`
    ].join('');
  }

  return [
    `<article class="planner-session-card subject-colored" style="${e(styleStr)}" data-session-id="${e(s.id)}">`,
    `  <div class="planner-session-top">`,
    `    <span class="planner-session-time">${e(timeStr)}${s.room ? ' · ' + e(s.room) : ''}</span>`,
    `  </div>`,
    `  <div class="planner-session-info">`,
    `    <h4 class="planner-session-subject" title="${e(s.subject)}">${e(s.subject)}</h4>`,
    `    <span class="planner-session-group" title="${e(s.group)}">${e(s.group)}</span>`,
    `  </div>`,
    proposalBlock,
    recordBlock,
    `</article>`
  ].join('');
}

export function recordModal(runId, run) {
  const ctx = run?.request?.pedagogy;
  const today = new Date().toISOString().slice(0, 10);
  const groupOptions = (store.state.config.groups || []).map(g => option(g.id, g.name, ctx?.group?.id)).join(
    '');
  modal('Registrar clase impartida',
    [
      `<p class="muted-small">Anota qué se impartió de verdad. Esta información `,
      [
        `alimenta la memoria del asistente para las próximas sesiones.</p>\n    <form data-form="record" `
      ].join(''),
      `${runId?`data-run="${e(runId)}"`:''}`,
      `>\n      <div class="field"><label class="label" for="rec-group">Grupo</label>`,
      `<select id="rec-group" name="group_id" required>${groupOptions}`,
      `</select></div>\n      <div class="field"><label class="label" for="rec-date">`,
      [
        `Fecha de la sesión</label><input id="rec-date" name="session_date" type="date" value="${e(today)}`
      ].join(''),
      `" required></div>\n      <div class="field"><label class="label" `,
      `for="rec-duration">Duración real (minutos)</label><input id="rec-duration" `,
      [
        `name="duration_minutes" type="number" min="1" max="480" value="${e(ctx?.duration_minutes||50)}`
      ].join(''),
      `" required></div>\n      <div class="field"><label class="label" for="rec-topic">`,
      `Qué se impartió</label><textarea id="rec-topic" name="topic" maxlength="2000" `,
      `rows="3" required placeholder="Tema o contenido impartido realmente en la sesión…">`,
      `${e(run?.display_title || run?.title || run?.request?.display_title || run?.request?.question || '')}`,
      `</textarea></div>\n      <div class="field"><label class="label" for="rec-notes">`,
      `Notas de la sesión (opcional)</label><textarea id="rec-notes" name="notes" `,
      `maxlength="4000" rows="2" placeholder="Asistencia, incidencias o cambios sobre `,
      `lo planificado…"></textarea></div>\n      <div class="feedback-fields"><div `,
      `class="field"><label class="label" for="rec-worked">Qué funcionó</label>`,
      `<textarea id="rec-worked" name="what_worked" maxlength="2000" rows="2" `,
      `placeholder="Actividad, explicación o dinámica que dio buen resultado…">`,
      `</textarea></div><div class="field"><label class="label" for="rec-failed">Qué `,
      `conviene ajustar</label><textarea id="rec-failed" name="what_failed" `,
      `maxlength="2000" rows="2" placeholder="Dificultades, ritmo, materiales o puntos `,
      `que revisar…"></textarea></div><div class="field"><label class="label" `,
      `for="rec-next">Para la próxima sesión</label><textarea id="rec-next" `,
      `name="next_session_note" maxlength="2000" rows="2" placeholder="Por dónde `,
      `continuar y qué conviene preparar…"></textarea></div></div>\n      <div `,
      `class="form-error" role="alert"></div>\n      <div class="dialog-actions">\n     `,
      `   <button class="button ghost" type="button" data-action="close-dialog">`,
      [
        `Cancelar</button>\n        <button class="button primary" type="submit">${icon('record')}`
      ].join(''),
      `Guardar registro</button>\n      </div>\n    </form>`
    ].join('')
  );
}

export function feedbackModal(session = null) {
  const today = store.state.agenda?.date || new Date().toISOString().slice(0, 10),
    group = session?.group_id || store.state.config.groups[0]?.id || '';
  modal('Feedback de la clase', [
    `<p class="muted-small">Tu valoración se guarda en el diario y se incorpora al `,
    `contexto de las próximas propuestas del grupo.</p><form data-form="feedback">`,
    `<div class="form-row"><div class="field"><label class="label" for="fb-group">`,
    `Grupo</label><select id="fb-group" name="group_id" required>`,
    `${
      store.state.config.groups.map(item => option(item.id, item.name, group)).join('')
    }`,
    `</select></div><div class="field"><label class="label" for="fb-date">`,
    [
      `Fecha</label><input class="input" id="fb-date" name="session_date" type="date" value="${e(today)}`
    ].join(''),
    `" required></div><div class="field"><label class="label" for="fb-duration">`,
    `Duración real</label><input class="input" id="fb-duration" `,
    [
      `name="duration_minutes" type="number" min="1" max="480" value="${e(session?.duration_minutes||60)}`
    ].join(''),
    `" required></div></div><div class="field"><label class="label" for="fb-topic">`,
    `Contenido impartido</label><input class="input" id="fb-topic" name="topic" `,
    `maxlength="2000" required placeholder="Qué se trabajó realmente en el aula">`,
    `</div><div class="field"><label class="label" for="fb-worked">Qué `,
    `funcionó</label><textarea id="fb-worked" name="what_worked" maxlength="2000" `,
    `rows="3" placeholder="Explicaciones, ejercicios o dinámicas eficaces…">`,
    `</textarea></div><div class="field"><label class="label" for="fb-failed">Qué `,
    `conviene ajustar</label><textarea id="fb-failed" name="what_failed" `,
    `maxlength="2000" rows="3" placeholder="Dificultades, tiempo, nivel o `,
    `materiales…"></textarea></div><div class="field"><label class="label" `,
    `for="fb-next">Para la próxima sesión</label><textarea id="fb-next" `,
    `name="next_session_note" maxlength="2000" rows="3" placeholder="Qué continuar, `,
    `reforzar o preparar…"></textarea></div><div class="field"><label class="label" `,
    `for="fb-notes">Otras notas (opcional)</label><textarea id="fb-notes" `,
    `name="notes" maxlength="4000" rows="2"></textarea></div><div class="form-error" `,
    `role="alert"></div><div class="dialog-actions"><button class="button ghost" `,
    `type="button" data-action="close-dialog">Cancelar</button><button class="button `,
    `primary" type="submit">${icon('record')}Guardar en el diario</button></div></form>`
  ].join(''));
}

export async function existingFeedbackModal(id) {
  const record = await api('/records/' + encodeURIComponent(id)),
    fb = record.feedback || {};
  modal('Feedback de la clase', [
    `<div class="record-summary"><span>${e(record.session_date)} · ${e(record.duration_minutes)}`,
    [
      ` min</span><h3>${e(record.topic)}</h3></div><form data-form="feedback" data-record="${e(id)}`
    ].join(''),
    `"><div class="field"><label class="label" for="fb-worked">Qué funcionó</label>`,
    [
      `<textarea id="fb-worked" name="what_worked" maxlength="2000" rows="3">${e(fb.what_worked||'')}`
    ].join(''),
    `</textarea></div><div class="field"><label class="label" for="fb-failed">Qué `,
    [
      `conviene ajustar</label><textarea id="fb-failed" name="what_failed" maxlength="2000" rows="3">`
    ].join(''),
    `${e(fb.what_failed||'')}`,
    `</textarea></div><div class="field"><label class="label" for="fb-next">Para la `,
    [
      `próxima sesión</label><textarea id="fb-next" name="next_session_note" maxlength="2000" rows="3">`
    ].join(''),
    [
      `${e(fb.next_session_note||'')}</textarea></div><div class="form-error" role="alert"></div><div `
    ].join(''),
    `class="dialog-actions"><button class="button ghost" type="button" `,
    `data-action="close-dialog">Cancelar</button><button class="button primary" `,
    `type="submit">Guardar cambios</button></div></form>`
  ].join(''));
}

function nombreGrupo(id) {
  return store.state.config.groups.find(group => group.id === id)?.name || id;
}

function entradaDiario(record) {
  const fb = record.feedback || {};
  const complete = !!(fb.what_worked || fb.what_failed || fb.next_session_note);
  return [
    [
      `<article class="diary-entry"><div class="diary-date"><strong>${e(record.session_date.slice(8,10))}`
    ].join(''),
    `</strong><span>`,
    [
      `${
        e(new Intl.DateTimeFormat('es', {
          month: 'short'
        }).format(new Date(record.session_date + 'T12:00:00')))
      }`
    ].join(''),
    [
      `</span></div><div class="diary-entry-copy"><span class="eyebrow">${e(nombreGrupo(record.group_id))} · `
    ].join(''),
    `${e(record.duration_minutes)} min</span><h3>${e(record.topic)}</h3><p>`,
    [
      `${
        complete ? e(fb.next_session_note || fb.what_worked || 'Feedback registrado') : 'Feedback pendiente'
      }`
    ].join(''),
    [
      `</p></div><span class="badge ${complete?'':'pending'}">${complete?'Registrado':'Pendiente'}`
    ].join(''),
    `</span><button class="button small" data-session-record="${e(record.id)}">`,
    `${complete?'Revisar feedback':'Completar feedback'}`,
    `</button><button class="icon-button" data-reveal-record="${e(record.id)}`,
    [
      `" aria-label="Abrir carpeta de la sesión" title="Abrir carpeta">${icon('folder')}</button></article>`
    ].join('')
  ].join('');
}

// Acciones y formularios de este módulo; delegación central en main.js.
async function accionOpenRecordRun({target}) {
  recordModal(target.dataset.recordRun, store.currentRun);
}

async function accionOpenFeedbackSession({target}) {
  const session = store.state.agenda.sessions.find(item => item.id === target.dataset
    .feedbackSession);
  feedbackModal(session);
}

async function accionOpenSessionRecord({target}) {
  await existingFeedbackModal(target.dataset.sessionRecord);
}

async function accionOpenRevealRecord({target}) {
  const path = '/api/records/' + encodeURIComponent(target.dataset.revealRecord);
  if (store.state.server_mode) {
    const response = await request(path + '/download');
    if (!response.ok) throw new Error('No se pudo descargar la sesión.');
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    link.download = 'sesion.zip';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } else await api(path.replace('/api', '') + '/reveal', {});
}

async function accionNewFeedback() {
  feedbackModal();
}

async function accionRevealDiary() {
  await api('/reveal-diary', {});
}

async function formularioRecord({form, data}) {
  const payload = {
    ...data,
    duration_minutes: Number(data.duration_minutes),
    run_id: form.dataset.run || undefined
  };
  const result = await api('/records', payload);
  dialog.close();
  toast([
    `Clase registrada: ${result.id}`,
    `. El asistente tendrá en cuenta esta sesión en las próximas propuestas.`
  ].join(''));
}

async function formularioFeedback({form, data}) {
  const result = form.dataset.record ? await api('/records/' + encodeURIComponent(form.dataset
    .record) + '/feedback', data) : await api('/records', {
    ...data,
    duration_minutes: Number(data.duration_minutes)
  });
  dialog.close();
  await refresh();
  toast(`Feedback guardado en el diario de ${result.session_date}.`);
}

async function accionPlannerPrev({target}) {
  const btn = target.closest('[data-date]');
  const dateStr = btn?.dataset.date;
  if (!dateStr) return;
  toast('Cargando semana anterior...');
  const res = await api('/planner?date=' + encodeURIComponent(dateStr));
  store.state.planner = res;
  render();
}

async function accionPlannerNext({target}) {
  const btn = target.closest('[data-date]');
  const dateStr = btn?.dataset.date;
  if (!dateStr) return;
  toast('Cargando semana siguiente...');
  const res = await api('/planner?date=' + encodeURIComponent(dateStr));
  store.state.planner = res;
  render();
}

async function accionPlannerToday() {
  toast('Cargando semana actual...');
  const res = await api('/planner');
  store.state.planner = res;
  render();
}

async function accionPlannerJumpDate({target}) {
  const isInput = target.classList?.contains('planner-date-input');
  const input = isInput ? target : target.querySelector?.('.planner-date-input');
  const dateVal = input?.value || target.value;
  if (!dateVal) return;
  toast('Cargando semana...');
  const res = await api('/planner?date=' + encodeURIComponent(dateVal));
  store.state.planner = res;
  render();
}

function accionSetPlannerMode({target}) {
  const btn = target.closest('[data-mode]');
  if (btn && btn.dataset.mode) {
    currentViewMode = btn.dataset.mode;
    render();
  }
}

export const actions = {
  'record-run': accionOpenRecordRun,
  'feedback-session': accionOpenFeedbackSession,
  'session-record': accionOpenSessionRecord,
  'reveal-record': accionOpenRevealRecord,
  'new-feedback': accionNewFeedback,
  'reveal-diary': accionRevealDiary,
  'planner-prev': accionPlannerPrev,
  'planner-next': accionPlannerNext,
  'planner-today': accionPlannerToday,
  'planner-jump-date': accionPlannerJumpDate,
  'set-planner-mode': accionSetPlannerMode,
};

export const forms = {
  'record': formularioRecord,
  'feedback': formularioFeedback,
};

export const clickBindings = [
  {
    priority: 14,
    matches: target => target.dataset.action === 'set-planner-mode' ||
      target.closest('[data-action="set-planner-mode"]'),
    action: 'set-planner-mode'
  },
  {
    priority: 15,
    matches: target => target.dataset.action === 'planner-prev' ||
      target.closest('[data-action="planner-prev"]'),
    action: 'planner-prev'
  },
  {
    priority: 15,
    matches: target => target.dataset.action === 'planner-next' ||
      target.closest('[data-action="planner-next"]'),
    action: 'planner-next'
  },
  {
    priority: 15,
    matches: target => target.dataset.action === 'planner-today' ||
      target.closest('[data-action="planner-today"]'),
    action: 'planner-today'
  },
  {priority: 18, matches: target => target.dataset.recordRun, action: 'record-run'},
  {priority: 19, matches: target => target.dataset.feedbackSession, action: 'feedback-session'},
  {priority: 20, matches: target => target.dataset.sessionRecord, action: 'session-record'},
  {priority: 21, matches: target => target.dataset.revealRecord, action: 'reveal-record'},
];

export const events = {
  change: {
    '.planner-date-input': accionPlannerJumpDate,
  }
};
