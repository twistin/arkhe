// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  store
} from '../state.js';
import {
  $,
  e,
  modal,
  option,
  subjectOptions
} from '../ui.js';

export function subjectModal(id) {
  const subject = store.state.config.subjects.find(s => s.id === id);
  modal(subject ? 'Editar materia' : 'Nueva materia', [
    `<p>Cada materia tendrá su propio ámbito de conocimiento y sus carpetas.</p><form `,
    `data-form="subject"><input type="hidden" name="id" value="${e(subject?.id||'')}`,
    `"><div class="field"><label class="label" for="subject-name">Nombre de la `,
    `materia</label><input class="input" id="subject-name" name="name" required `,
    [
      `maxlength="200" placeholder="Por ejemplo, Historia de la Música I" value="${e(subject?.name||'')}`
    ].join(''),
    `"></div><div class="field"><label for="subject-color">Color (opcional)</label>`,
    `<input class="input" id="subject-color" name="color" pattern="#[0-9A-Fa-f]{6}" `,
    `placeholder="Automático" value="${e(subject?.color || '')}"></div>`,
    `<div class="field"><label for="subject-periods">Períodos, en orden</label>`,
    `<textarea id="subject-periods" name="periods" class="input" rows="5">`,
    `${e((subject?.periods || []).map(p => p.id + ' | ' + p.nombre).join('\n'))}</textarea>`,
    `<p class="field-note">Una línea por período: carpeta | nombre. Vacío: sin períodos. `,
    `Cambiar un identificador crea otra carpeta; los archivos existentes se conservan.</p></div>`,
    `<div class="dialog-actions"><button class="button ghost" type="button" `,
    `data-action="close-dialog">Cancelar</button><button class="button primary" `,
    `type="submit">Guardar materia</button></div></form>`
  ].join(''));
  $('#subject-name').focus();
}

export function groupModal(id) {
  if (!store.state.config.subjects.length) {
    subjectModal();
    return;
  }
  const current = store.state.config.groups.find(g => g.id === id),
    now = new Date(),
    year = current ? Number(store.state.config.academic_years.find(y => y.id === current.academic_year_id)
      .start_date.slice(0, 4)) : (now.getMonth() >= 8 ? now.getFullYear() : now.getFullYear() - 1);
  modal(current ? 'Editar grupo' : 'Nuevo grupo', [
    `<p>El asistente usará estos datos para ajustar el nivel y el idioma de las `,
    [
      `propuestas.</p><form data-form="group"><input type="hidden" name="id" value="${e(current?.id||'')}`
    ].join(''),
    `"><div class="form-row"><div class="field"><label class="label" for="group-name">`,
    `Nombre del grupo</label><input class="input" id="group-name" name="name" `,
    `required placeholder="Por ejemplo, 3º GP · Grupo A" value="${e(current?.name||'')}`,
    `"></div><div class="field"><label class="label" for="group-level">Nivel</label>`,
    `<input class="input" id="group-level" name="level" required placeholder="Por `,
    `ejemplo, 3º de Grado Profesional" value="${e(current?.level||'')}`,
    `"></div></div><div class="field"><label class="label" for="group-subject">`,
    `Materia</label><select id="group-subject" name="subject" required>`,
    `${subjectOptions(current?.subject_id||store.selected,true)}`,
    `</select></div><div class="form-row"><div class="field"><label class="label" `,
    `for="group-center">Centro</label><input class="input" id="group-center" `,
    `name="center" required value="`,
    [
      `${
        e((current ? store.state.config.centers.find(c => c.id === current.center_id) : store.state.config.centers[0])
          ?.name || '')
      }`
    ].join(''),
    `"></div><div class="field"><label class="label" for="group-teacher">`,
    `Profesor</label><input class="input" id="group-teacher" name="teacher" required value="`,
    [
      `${
        e((current ? store.state.config.teachers.find(t => t.id === current.teacher_id) : store.state.config.teachers[
          0])?.name || '')
      }`
    ].join(''),
    `"></div></div><div class="form-row"><div class="field"><label class="label" `,
    `for="group-year">Año de inicio del curso</label><input class="input" `,
    `id="group-year" name="year" type="number" min="2000" max="2100" value="${e(year)}`,
    `" required><p class="field-note">De septiembre a agosto del año siguiente.</p>`,
    `</div><div class="field"><label class="label" for="group-language">Idioma de las `,
    `propuestas</label><select id="group-language" name="language">`,
    [
      `${
        [
          ['es', 'Castellano'],
          ['gl', 'Galego'],
          ['ca', 'Català'],
          ['eu', 'Euskara'],
          ['en', 'English'],
          ['pt', 'Português']
        ].map(([v, t]) => option(v, t, current?.language || 'es')).join('')
      }`
    ].join(''),
    `</select></div></div><div class="dialog-actions"><button class="button ghost" `,
    `type="button" data-action="close-dialog">Cancelar</button><button class="button `,
    `primary">Guardar grupo</button></div></form>`
  ].join(''));
}
