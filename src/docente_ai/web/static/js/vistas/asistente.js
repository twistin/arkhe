// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  resultHTML
} from '../componentes/documentos.js';
import {
  draft,
  readyDocs,
  store,
  subjectName
} from '../state.js';
import {
  dateLabel,
  e,
  header,
  icon,
  option,
  runStatus,
  subjectOptions
} from '../ui.js';

export function assistant() {
  const subject = draft('ask-form', 'subject', store.selected || store.state.config.subjects[0]?.id || '');
  const count = readyDocs(subject).length;
  return header('ASISTENTE DOCUMENTAL', 'Piensa con tus fuentes.',
    'Consulta, contrasta y desarrolla ideas a partir de tu biblioteca.') + [
    `<div class="workspace-grid"><div><form id="ask-form" class="panel" `,
    `data-form="ask"><div class="field"><label class="label" for="ask-subject">¿En `,
    `qué materia estás trabajando?</label><select id="ask-subject" name="subject" required>`,
    `${subjectOptions(subject,true)}`,
    `</select></div><label class="label" for="question">Tu pregunta</label><textarea `,
    `id="question" name="question" class="question-box" maxlength="4000" required `,
    `placeholder="¿Qué te gustaría comprender o preparar?">${e(draft('ask-form','question'))}`,
    `</textarea><div class="field"><label class="label" for="ask-category">`,
    `Utilizar</label><select id="ask-category" name="category">`,
    [
      `${
        [
          ['all', 'Fuentes y materiales propios'],
          ['documental', 'Solo documentación'],
          ['profesor', 'Solo mis materiales']
        ].map(([v, t]) => option(v, t, draft('ask-form', 'category', 'all'))).join('')
      }`
    ].join(''),
    `</select></div><div class="form-error" role="alert"></div><div `,
    `class="form-footer"><p>Respuestas con referencias.<br>Siempre bajo tu `,
    `revisión.</p><button class="button primary" type="submit" `,
    `${!store.state.config.subjects.length?'disabled':''}>${icon('spark')}`,
    `Consultar fuentes</button></div></form><div id="answer-result">`,
    [
      `${
        store.currentRun && !store.currentRun.request.pedagogy ? resultHTML(store.currentRun) : ''
      }`
    ].join(''),
    [
      `</div></div><aside class="panel context-panel"><div class="aside-title">TU CONTEXTO</div><h3>`
    ].join(''),
    [
      `${e(subjectName(subject))}</h3><div class="context-number">${e(count)}</div><div class="context-label">`
    ].join(''),
    `${count===1?'fuente preparada':'fuentes preparadas'}`,
    `</div><hr class="context-rule"><p class="muted-small">`,
    [
      `${
        count ? 'El asistente consultará solo las fuentes que has autorizado para esta materia.' :
          'Añade y autoriza una fuente para que el asistente pueda trabajar con ella.'
      }`
    ].join(''),
    `</p><a href="#biblioteca" class="button ghost small">Ir a la biblioteca ${icon('arrow')}`,
    `</a><hr class="context-rule"><div class="aside-title">CONSULTAS RECIENTES</div>`,
    [
      `${
        store.state.runs.filter(r => r.kind === 'answer').slice(0, 5).map(r => [
          [
            `<button class="recent-item" data-run="${e(r.id)}">${e(r.title)}<span>${e(dateLabel(r.created_at))} · `
          ].join(''),
          `${e(runStatus(r.status))}</span></button>`
        ].join('')).join('') || '<p class="muted-small">Tus consultas aparecerán aquí.</p>'
      }`
    ].join(''),
    [
      `${
        store.state.runs.filter(r => r.kind === 'answer').length > 5 ?
          '<button class="button ghost small" data-action="all-answers">Ver todas las consultas</button>' : ''
      }`
    ].join(''),
    `</aside></div>`
  ].join('');
}
