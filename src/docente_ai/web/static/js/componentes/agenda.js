// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  store,
  view
} from '../state.js';
import {
  e,
  subjectStyle,
  icon
} from '../ui.js';

export function dailyAgenda() {
  const agenda = store.state.agenda,
    sessions = agenda?.sessions || [];
  const feedbackMode = view() === 'diario';
  const day = new Date(`${agenda?.date||new Date().toISOString().slice(0,10)}T12:00:00`);
  const label = new Intl.DateTimeFormat('es', {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  }).format(day);
  const cards = sessions.map(session => {
    const start = new Date(session.start),
      end = new Date(session.end),
      now = new Date();
    const status = now >= start && now < end ? 'Ahora' : now < start ? 'Próxima' : 'Finalizada';
    const time = new Intl.DateTimeFormat('es', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(start);
    const subjId = session.subject_id || 'none';
    return [
      `<button class="agenda-session subject-colored" style="${e(subjectStyle(subjId))}" data-subject="${e(subjId)}" `,
      [
        `${
          feedbackMode ? `data-feedback-session="${e(session.id)}"` : [
            `data-prepare-session="${e(session.id)}"`
          ].join('')
        }`
      ].join(''),
      [
        ` aria-label="${feedbackMode?'Registrar feedback de':'Preparar'} ${e(session.subject)} a las `
      ].join(''),
      [
        `${e(time)}"><span class="agenda-time">${e(time)}</span><span class="agenda-copy"><strong title="`
      ].join(''),
      `${e(session.subject)}">${e(session.subject)}</strong><small title="${e(session.group)}`,
      `${session.room?' · '+e(session.room):''}">${e(session.group)}`,
      `${session.room?' · '+e(session.room):''}</small></span><span class="agenda-status `,
      `${e(status.toLowerCase())}">${status}</span><span class="agenda-action">`,
      `${feedbackMode?'Dar feedback':'Preparar'} ${icon('arrow')}</span></button>`
    ].join('');
  }).join('');
  return [
    `<section class="daily-agenda" aria-label="Clases de hoy"><div `,
    [
      `class="agenda-heading"><div><span class="eyebrow">HOY · ${e(label.toLocaleUpperCase('es'))}`
    ].join(''),
    `</span><h2>`,
    [
      `${
        sessions.length
          ? `${e(sessions.length)} ${sessions.length===1?'clase':'clases'} en tu agenda`
          : 'Hoy no tienes clases programadas'
      }`
    ].join(''),
    `</h2></div><span class="agenda-note">`,
    [
      `${
        sessions.length ? (feedbackMode ? 'Selecciona una clase para dejar tu valoración.' :
          'Selecciona una clase para preparar su propuesta.') : 'Tu horario está al día.'
      }`
    ].join(''),
    `</span></div>${sessions.length?`<div class="agenda-track">${cards}</div>`:''}</section>`
  ].join('');
}
