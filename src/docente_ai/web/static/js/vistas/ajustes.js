// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  store,
  subjectName
} from '../state.js';
import {
  e,
  header,
  icon,
  option
} from '../ui.js';

export function runStatsPanel() {
  const stats = store.selectedRunStats || store.state.run_stats;
  if (!stats) return '';
  const names = {
    json_format: 'Formato JSON',
    contract: 'Contrato',
    extra_fields: 'Campos extra',
    invalid_enum: 'Valor no permitido',
    quote_unresolved: 'Cita no resoluble',
    length: 'Límite de tokens',
    network: 'Red o disponibilidad',
    authorization: 'Autorización',
    source_changed: 'Fuente cambiada',
    context_budget: 'Presupuesto de contexto',
    provider: 'Proveedor',
    internal: 'Otro fallo',
    legacy_untyped: 'Histórico sin tipo registrado'
  };
  return [
    `<section class="panel"><div class="panel-header"><h2>Calidad de generación</h2>`,
    `</div><form data-form="run-stats"><label class="label" for="stats-limit">Últimas `,
    `ejecuciones</label><div class="form-footer"><input id="stats-limit" name="limit" `,
    `type="number" min="1" max="10000" value="${stats.limit}`,
    `" required><button class="button small" type="submit">Actualizar</button></div>`,
    `<div class="form-error" role="alert"></div></form><p class="muted-small">${stats.total}`,
    ` ejecuciones · porcentajes sobre el total seleccionado.</p>`,
    [
      `${
        [
          ['draft', 'Borradores válidos'],
          ['failed', 'Fallidas'],
          ['abstained', 'Sin respaldo']
        ].map(([key, label]) => [
          [
            `<div class="setting-row"><span>${label}</span><strong>${stats.counts[key]} · ${stats.rates[key]}`
          ].join(''),
          `%</strong></div>`
        ].join('')).join('')
      }`
    ].join(''),
    [
      `<p class="muted-small">${stats.repaired_drafts} borradores recuperados mediante reparación · `
    ].join(''),
    `${stats.counts.cancelled} canceladas · ${stats.counts.running}`,
    ` en curso.</p><details class="metadata"><summary>Errores por tipo</summary>`,
    [
      `${
        Object.entries(stats.errors).map(([key, count]) => [
            `<div class="setting-row"><span>${e(names[key]||key)}</span><strong>${count}</strong></div>`
          ].join('')).join('') ||
          '<p class="muted-small">Sin errores en este periodo.</p>'
      }`
    ].join(''),
    `</details></section>`
  ].join('');
}

export function providerSettingsPanel() {
  const info = store.state.provider_info || {},
    presets = store.state.provider_presets || {},
    current = store.state.generation_provider || 'ollama';
  return [
    `<section class="panel"><div class="panel-header"><h2>Motor de IA</h2><button `,
    [
      `class="icon-button" data-action="status" aria-label="Comprobar conexión">${icon('refresh')}`
    ].join(''),
    `</button></div><p>${e(info.indicator||'Proveedor sin configurar')}`,
    `</p><p class="muted-small">Embeddings siempre locales. Biblioteca y diario `,
    `permanecen en tu equipo.</p><form data-form="models" class="model-form"><div `,
    `class="field"><label class="label" for="model-provider">Proveedor</label><select `,
    `name="provider" id="model-provider">`,
    `${
      Object.entries(presets).map(([key, p]) => option(key, p.name, current)).join('')
    }`,
    `</select></div><div class="field"><label class="label" for="model-generation">`,
    `Modelo generativo</label><input id="model-generation" name="generation" value="`,
    `${e(info.model||store.state.generation_model)}`,
    `" required list="provider-models"><datalist id="provider-models">`,
    [
      `${
        Object.keys(presets[current]?.models || {}).map(m => `<option value="${e(m)}">`).join('')
      }`
    ].join(''),
    `</datalist></div><div class="field custom-only" ${current!=='custom'?'hidden':''}`,
    `><label class="label" for="provider-url">URL base HTTPS</label><input `,
    `name="base_url" id="provider-url" type="url" value="${e(info.base_url||'')}`,
    `" placeholder="https://servidor.example/v1"></div><div class="field remote-only" `,
    `${!info.is_remote?'hidden':''}`,
    `><label class="label" for="model-apikey">Clave del proveedor</label><input `,
    [
      `id="model-apikey" name="api_key" type="password" autocomplete="off" value=""><p class="field-note">`
    ].join(''),
    `${store.state.api_key_configured?'Clave configurada.':'Clave pendiente.'}`,
    ` Se guarda en el Llavero; deja vacío para conservarla.</p><button type="button" `,
    `class="button ghost small" data-action="delete-api-key">Borrar clave del `,
    `proveedor activo</button><label class="label" for="response-format">Capacidad `,
    `declarada de salida</label><select id="response-format" name="response_format">`,
    [
      `${
        [
          ['', 'Usar capacidad del preset'],
          ['none', 'Sin response_format'],
          ['json_object', 'JSON object'],
          ['json_schema', 'JSON schema']
        ].map(([key, label]) => option(key, label, '')).join('')
      }`
    ].join(''),
    `</select></div><div class="field"><label class="label" for="model-embeddings">`,
    `Embeddings (Ollama local)</label><input name="embeddings" id="model-embeddings" value="`,
    `${e(store.modelStatus?.embeddings||'bge-m3')}`,
    `" required></div><div class="form-error" role="alert"></div><button `,
    `class="button small" type="submit">Guardar proveedor</button></form>`,
    [
      `${
        info.is_remote ? [
          `<p class="field-note">`,
          [
            `${
        info.remote_confirmed ? 'Envío remoto confirmado para este destino.' :
          'Antes de consultar se pedirá autorización para enviar la pregunta y los fragmentos.'
        }`
          ].join(''),
          `</p><button class="button ghost small" data-action="confirm-provider">Revisar y `,
          `confirmar envío</button>`
        ].join('') : ''
      }`
    ].join(''),
    `</section>`
  ].join('');
}

const dias = ['', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

function horarioRegla(regla) {
  const [horas, minutos] = regla.start_time.split(':').map(Number);
  const fin = horas * 60 + minutos + regla.duration_minutes;
  const horaFinal = [
    `${String(Math.floor(fin / 60) % 24).padStart(2, '0')}:${String(fin % 60).padStart(2, '0')}`
  ].join('');
  return `${e(regla.start_time)}–${e(horaFinal)} · ${e(regla.room || 'Aula sin indicar')}`;
}

function excepcionHorario(excepcion, regla) {
  const contenido = excepcion.cancelled ?
    'Clase cancelada' :
    horarioRegla({
      ...regla,
      ...excepcion
    });
  return `<small>${e(excepcion.date)} · ${contenido}</small>`;
}

function grupoHorario(grupo, reglas, excepciones) {
  const sesiones = reglas.filter(regla => regla.group_id === grupo.id)
    .sort((a, b) => a.weekday - b.weekday || a.start_time.localeCompare(b.start_time));
  const filas = sesiones.map(regla => {
    const cambios = excepciones.filter(item => item.schedule_rule_id === regla.id)
      .sort((a, b) => a.date.localeCompare(b.date))
      .map(item => excepcionHorario(item, regla)).join('');
    return `<small>${e(dias[regla.weekday])} · ${horarioRegla(regla)}</small>${cambios}`;
  }).join('') || '<small>Sin horario. Importa o crea las reglas de este grupo.</small>';
  return `<div class="setting-row"><span>${e(grupo.name)} (${e(grupo.level)})${filas}</span></div>`;
}

export function schedulePanel() {
  const {
    groups = [], schedule_rules = [], calendar_exceptions = []
  } = store.state.config;
  const grupos = groups.map(grupo => grupoHorario(grupo, schedule_rules, calendar_exceptions)).join('');
  return `<section class="panel"><div class="panel-header"><h2>Horario y Calendario</h2>` + [
      `<button class="button primary small" data-action="download-calendar">${icon('download')}`,
      `Descargar .ics</button>`
    ].join('') +
    '</div><p class="muted-small">Sincroniza tus clases semanales con Apple Calendar, Google Calendar u Outlook, ' +
    'con recordatorios configurados 15 min antes.</p>' +
    (grupos ||
      '<p class="muted-small">Crea grupos y horarios o importa tu configuración para ver las clases.</p>') +
    '</section>';
}

function panelMaterias() {
  return [
    `<section class="panel"><div class="panel-header"><h2>Materias</h2><button `,
    `class="button small" data-action="new-subject">${icon('plus')}Añadir</button></div>`,
    [
      `${
        store.state.config.subjects.map(s => [
          `<div class="setting-row"><span>${e(s.name)}<small>`,
          `${store.state.documents.filter(d=>d.subjects.includes(s.id)).length}`,
          ` documentos</small></span><button class="icon-button" data-edit-subject="${e(s.id)}`,
          `" aria-label="Editar ${e(s.name)}">${icon('edit')}</button></div>`
        ].join('')).join('') || '<p class="muted-small">Crea una materia para empezar a organizar tus fuentes.</p>'
      }`
    ].join(''),
    `</section>`
  ].join('');
}

function panelGrupos() {
  return [
    `<section class="panel"><div class="panel-header"><h2>Grupos</h2><button `,
    `class="button small" data-action="new-group">${icon('plus')}Añadir</button></div>`,
    [
      `${
        store.state.config.groups.map(g => [
            [
              `<div class="setting-row"><span>${e(g.name)}<small>${e(subjectName(g.subject_id))} · ${e(g.level)}`
            ].join(''),
            [
              `</small></span><button class="icon-button" data-edit-group="${e(g.id)}" aria-label="Editar `
            ].join(''),
            `${e(g.name)}">${icon('edit')}</button></div>`
          ].join('')).join('') ||
          '<p class="muted-small">Añade tus grupos para preparar propuestas adaptadas a su nivel.</p>'
      }`
    ].join(''),
    `</section>`
  ].join('');
}

function panelConocimiento() {
  return [
    `<section class="panel"><div class="panel-header"><h2>Tu carpeta de conocimiento</h2>`,
    [
      `${icon('folder')}</div><p class="muted-small">Los documentos permanecen en tu equipo. Fuentes `
    ].join(''),
    `documentales y materiales propios se guardan por separado.</p><p class="path">`,
    [
      `${e(store.state.knowledge_path)}</p><button class="button" data-action="reveal">${icon('external')}`
    ].join(''),
    `Abrir en Finder</button><button class="button ghost" data-action="scan">Revisar `,
    `archivos</button></section>`
  ].join('');
}

export function settings() {
  return header('MI ESPACIO', 'A tu manera.', 'Organiza tus materias, grupos y entorno de trabajo local.') + [
    [
      `<div class="settings-grid">${runStatsPanel()}\n  ${panelMaterias()}\n  ${panelGrupos()}\n  `
    ].join(''),
    `${schedulePanel()}\n  ${panelConocimiento()}\n  ${providerSettingsPanel()}`,
    `</div><div class="form-footer"><span></span><button class="button ghost small" `,
    `data-action="shutdown-dialog">Cerrar Enjambre</button></div>`
  ].join('');
}
