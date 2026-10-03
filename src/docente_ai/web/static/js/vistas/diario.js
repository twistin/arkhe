// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  api
} from '../api.js';
import {
  store
} from '../state.js';
import {
  e,
  header,
  icon,
  modal,
  option,
  primary
} from '../ui.js';

export function diary() {
  const records = store.state.records || [];
  return header('ESPACIO DEL PROFESOR', 'Diario docente.',
      'Registra lo que ocurrió en el aula. Tu feedback orientará las próximas propuestas.', primary(
        'Registrar otra sesión', 'new-feedback', 'record')) + [
      `<section class="folder-banner diary-folder"><div class="folder-symbol">${icon('folder')}`,
      `</div><div class="folder-copy"><h3>Material de sesiones ordenado por fecha</h3>`,
      `<p>Guías, material del alumnado, anexos y feedback se guardan en 03 Diario `,
      `docente.</p></div><button class="button ghost" data-action="reveal-diary">Abrir carpeta `,
      `${icon('external')}</button></section>`
    ].join('') +
    (records.length ? `<div class="diary-list">${records.map(entradaDiario).join('')}</div>` : [
      [
        `<section class="empty-library diary-empty"><div class="onboarding-mark">${icon('record')}`
      ].join(''),
      `</div><h2>Tu experiencia también forma parte del sistema.</h2><p>Después de cada `,
      `clase, anota qué funcionó, qué cambiarías y por dónde continuar.</p>`,
      `${primary('Registrar la primera sesión','new-feedback','record')}</section>`
    ].join(''));
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
      `${e(run?.request?.question||'')}`,
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
    `<div class="record-summary"><span>${e(record.session_date)} · ${record.duration_minutes}`,
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
    `${record.duration_minutes} min</span><h3>${e(record.topic)}</h3><p>`,
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
