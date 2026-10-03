// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  store
} from './state.js';

export const $ = (s, root = document) => root.querySelector(s);
export const e = value => String(value ?? '').replace(/[&<>"']/g, c => ({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
} [c]));
const paths = {
  library: '<path d="M4 4h4v16H4zM10 4h4v16h-4zM16 5l4-1 4 15-4 1z"/>',
  spark: '<path d="m12 3 2.8 6.2L21 12l-6.2 2.8L12 21l-2.8-6.2L3 12l6.2-2.8L12 3Z"/><path ' +
    'd="m20 2 .8 1.7L22.5 4l-1.7.8L20 6.5l-.8-1.7L17.5 4l1.7-.3Z"/>',
  document: '<path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6"/>',
  settings: '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="15" cy="17" r="3"/>',
  folder: '<path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10H3z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
  up: '<path d="M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
  external: '<path d="M13 4h7v7m0-7L10 14M9 4H4v16h16v-5"/>',
  download: '<path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4"/>',
  refresh: '<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',
  edit: '<path d="m15 4 5 5M4 20l5-1L21 7l-5-5L4 14z"/>',
  arrowleft: '<path d="M19 12H5m5-5-5 5 5 5"/>',
  copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8V3H3v13h5"/>',
  record: '<path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 ' +
    '2-2z"/><path d="M9 7h6M7 12h10M7 17h7"/>',
  trash: '<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 ' +
    '2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/>'
};
export const icon = name => [
  `<svg class="icon" viewBox="0 0 25 25" aria-hidden="true">${paths[name] || paths.document}</svg>`
].join('');
export const formatPeriod = p => store.state?.config.subjects
  .flatMap(s => s.periods || []).find(period => period.id === p)?.nombre || p || '';

// Paleta fija sin identificadores de materias; hash estable entre navegadores.
const subjectPalette = [
  ['#0284c7', '#e0f2fe', '#0369a1', '#7dd3fc'],
  ['#16a34a', '#dcfce7', '#15803d', '#86efac'],
  ['#9333ea', '#f3e8ff', '#7e22ce', '#d8b4fe'],
  ['#0d9488', '#ccfbf1', '#0f766e', '#5eead4'],
  ['#d97706', '#fef3c7', '#92400e', '#fcd34d'],
];
export function subjectStyle(id) {
  let hash = 0;
  for (const char of id || '') hash = (Math.imul(hash, 31) + char.codePointAt(0)) >>> 0;
  const color = store.state?.config.subjects.find(s => s.id === id)?.color?.toLowerCase();
  let palette = id && id !== 'none' && id !== 'xeral' ? subjectPalette[hash % subjectPalette.length] :
    ['#94a3b8', '#f1f5f9', '#475569', '#cbd5e1'];
  if (/^#[0-9a-f]{6}$/.test(color || '')) {
    palette = subjectPalette.find(p => p[0] === color) || [color, color + '18', color, color + '80'];
  }
  return ['--subject-color', '--subject-bg', '--subject-ink', '--subject-border']
    .map((name, i) => `${name}:${palette[i]}`).join(';');
}
export const main = $('#main'),
  dialog = $('#dialog');
export const option = (value, text, selectedValue) => [
  `<option value="${e(value)}" ${value === selectedValue ? 'selected' : ''}>${e(text)}</option>`
].join('');
export const subjectOptions = (value, blank = false) => (blank ? option('', 'Elige una materia', value) :
  '') + store.state.config.subjects.map(s => option(s.id, s.name, value)).join('');
export const statusBadge = doc => doc.enabled ? doc.indexed ? '<span class="badge">Preparada</span>' :
  '<span class="badge pending">Por preparar</span>' : '<span class="badge off">Por revisar</span>';
export const dateLabel = value => new Intl.DateTimeFormat('es', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit'
}).format(new Date(value));
export const runStatus = value => ({
  draft: 'Borrador',
  abstained: 'Sin respaldo suficiente',
  failed: 'No completado',
  running: 'En curso',
  cancelled: 'Cancelado'
} [value] || value);

export function toast(message, error = false) {
  const element = $('#toast');
  element.textContent = message;
  element.className = error ? 'error' : '';
  element.hidden = false;
  clearTimeout(store.toastTimer);
  store.toastTimer = setTimeout(() => element.hidden = true, error ? 12000 : 5500);
}

export function fail(error) {
  const target = dialog.open ? $('.form-error', dialog) : null;
  if (target) target.textContent = error.message;
  else toast(error.message, true);
}

export function header(eyebrow, title, description, actions = '') {
  return [
    [
      `<section class="page-head"><div><span class="eyebrow">${e(eyebrow)}</span><h1>${e(title)}</h1><p>`
    ].join(''),
    [
      `${e(description)}</p></div>${actions ? `<div class="head-actions">${actions}</div>` : ''}</section>`
    ].join('')
  ].join('');
}

export function primary(text, action, name = 'plus') {
  return `<button class="button primary" data-action="${e(action)}">${icon(name)}${e(text)}</button>`;
}

export function formatMarkdown(text) {
  if (!text) return '';
  let out = e(text);

  // Generic code blocks remain escaped; generated text is never executable markup.
  out = out.replace(/```([a-z0-9_-]*)\s*([\s\S]*?)```/gi, (_, lang, code) => [
    `<pre><code>${code.trim()}</code></pre>`
  ].join(''));

  // Markdown tables: | col1 | col2 |
  out = out.replace(/((?:\|[^\n]+\|\r?\n)+)/g, match => {
    const rows = match.trim().split('\n').map(r => r.trim()).filter(Boolean);
    if (rows.length < 2) return match;
    const isSep = r => /^\|(?:\s*:?-+:?\s*\|)+$/.test(r);
    let htmlTable = '<div class="table-wrapper"><table class="analysis-table">';
    let inBody = false;
    for (let i = 0; i < rows.length; i++) {
      if (i === 1 && isSep(rows[i])) {
        inBody = true;
        continue;
      }
      const cells = rows[i].split('|').slice(1, -1).map(c => c.trim());
      if (i === 0 && !inBody) {
        htmlTable += '<thead><tr>' + cells.map(c => `<th>${c}</th>`).join('') +
          '</tr></thead><tbody>';
      } else {
        htmlTable += '<tr>' + cells.map(c => `<td>${c}</td>`).join('') + '</tr>';
      }
    }
    htmlTable += inBody ? '</tbody></table></div>' : '</table></div>';
    return htmlTable;
  });

  // Headings: ### H3, #### H4
  out = out.replace(/^###\s+(.+)$/gm, '<h3>$1</h3>');
  out = out.replace(/^####\s+(.+)$/gm, '<h4>$1</h4>');

  // Bold, italic, inline code
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Split blocks into paragraphs
  const blocks = out.split(/\n\n+/);
  return blocks.map(b => {
    const trimmed = b.trim();
    if (!trimmed) return '';
    if (/^<(div|table|pre|h3|h4|ul|ol)/i.test(trimmed)) return trimmed;
    if (/^-\s+/m.test(trimmed)) {
      const items = trimmed.split('\n').filter(l => l.trim().startsWith('-')).map(l =>
        `<li>${l.trim().replace(/^-\s+/, '')}</li>`).join('');
      return `<ul>${items}</ul>`;
    }
    return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
  }).join('');
}

function dialogHTML(title, content) {
  return [
    `<div class="dialog-head"><h2 id="dialog-title">${e(title)}`,
    [
      `</h2><button class="icon-button" data-action="close-dialog" aria-label="Cerrar">${icon('close')}`
    ].join(''),
    [
      `</button></div><div class="dialog-body"><div class="form-error" role="alert"></div>${content}</div>`
    ].join('')
  ].join('');
}

export function modal(title, content) {
  dialog.classList.remove('student-dialog');
  $('#dialog-content').innerHTML = dialogHTML(title, content);
  if (store.state?.server_mode) {
    dialog.querySelectorAll('[data-action="reveal"], [data-action="reveal-diary"], ' +
      '[data-action="shutdown"], [data-action="shutdown-dialog"], ' +
      '[data-action="delete-api-key"]').forEach(node => node.remove());
  }
  if (!dialog.open) dialog.showModal();
}

export function render() {
  document.dispatchEvent(new CustomEvent('enjambre:render'));
}
export function navigate(route) {
  document.dispatchEvent(new CustomEvent('enjambre:navigate', {
    detail: route
  }));
}
