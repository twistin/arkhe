import { e, formatMarkdown, normalizeAuthorsDisplay } from '../ui.js';

// Secciones de teoría compartidas por la guía del profesor y el material del alumnado.
// Cada claim de la propuesta es una sección con título, explicación, ideas clave y
// ejemplos musicales reales (partituras del catálogo o verificadas por el profesor).

const NOTAS_ES = { C: 'do', D: 're', E: 'mi', F: 'fa', G: 'sol', A: 'la', B: 'si' };

export function notaEnEspanol(nota) {
  const m = /^([A-G])([♯♭#-]*)(-?\d+)?$/.exec(String(nota || '').trim());
  if (!m) return String(nota || '');
  const alter = m[2].replace(/#/g, '♯').replace(/-/g, '♭');
  return `${NOTAS_ES[m[1]]}${alter}${m[3] ?? ''}`;
}

function primeraFrase(texto, max = 70) {
  const limpio = String(texto || '').replace(/\s+/g, ' ').trim();
  const frase = (limpio.split(/(?<=[.:;])\s/)[0] || limpio).replace(/[.:;]$/, '');
  if (frase.length <= max) return frase;
  const corte = frase.slice(0, max);
  return corte.slice(0, corte.lastIndexOf(' ') > 30 ? corte.lastIndexOf(' ') : max) + '…';
}

export function sectionTitle(claim, index) {
  if (claim?.title) return claim.title;
  return primeraFrase(claim?.text) || `Contenido ${index + 1}`;
}

export function hasStructuredSections(run) {
  return (run.result?.claims || []).some(c => c && c.title);
}

// Ejemplos musicales mostrables: repertorio real del catálogo, teoría calculada o
// partituras verificadas desde la interfaz por el profesor.
export function isShowableScore(item) {
  if (!item?.ejemplo) return false;
  const ej = item.ejemplo;
  if (item.status === 'resuelto_repertorio' && ej.edicion_reconocida) return true;
  if (item.status !== 'resuelto_catalogo') return false;
  const isTheory = ej.calculado_teoria || ej.fuente === 'Calculado a partir de la teoría' ||
    item.origen === 'calculado_teoria';
  return Boolean(isTheory || (item.verificado && ej.verificado_por && ej.verificado_en));
}

export function examplesForClaim(run, claim) {
  const ids = new Set(claim?.example_ids || []);
  if (!ids.size) return [];
  return (run.result?.resolved_music_requests || [])
    .filter(item => ids.has(item.request_id) && isShowableScore(item));
}

export function unlinkedExamples(run) {
  const linked = new Set((run.result?.claims || []).flatMap(c => c?.example_ids || []));
  return (run.result?.resolved_music_requests || [])
    .filter(item => !linked.has(item.request_id) && isShowableScore(item));
}

export function analysisSummary(analisis) {
  if (!analisis || !analisis.entradas?.length) return '';
  const orden = analisis.entradas
    .map(en => `${en.voz} (c. ${en.compas}, ${notaEnEspanol(en.nota)})`).join(' → ');
  return [
    `<p class="score-analysis"><strong>Análisis calculado sobre la partitura `,
    `(c. ${e(analisis.compases)}):</strong> orden de entrada ${e(orden)}. `,
    `${e(analisis.porcentaje_ataques_simultaneos)} % de ataques simultáneos: `,
    `${e(analisis.textura_calculada)}.</p>`
  ].join('');
}

export function scoreExampleCard(item, runId, { teacher = false } = {}) {
  const ej = item.ejemplo;
  const isTheory = ej.calculado_teoria || item.origen === 'calculado_teoria';
  const titulo = [ej.obra || item.request?.work || 'Ejemplo musical', ej.seccion].filter(Boolean).join(' · ');
  const compositor = ej.compositor || item.request?.composer || '';
  const observar = ej.que_observar || item.request?.description || '';
  const voz = ej.voz_resaltada || (item.status === 'resuelto_repertorio' ? 'ninguna' : '');
  let edicion = `Fuente: ${ej.fuente || 'Catálogo del profesor'}`;
  if (isTheory) edicion = 'Calculado a partir de la teoría';
  else if (item.status === 'resuelto_repertorio') edicion = `Edición: ${ej.fuente}`;
  const [ini, fin] = String(ej.compases || '1-8').split('-').map(n => parseInt(n, 10));
  const vozAttr = voz ? ` data-voice="${e(voz)}"` : '';
  return [
    `\n<figure class="music-example score-candidate-item" data-candidate-id="${e(ej.id)}" `,
    `data-run-id="${e(runId)}"${vozAttr}>\n  <figcaption class="music-example-head">\n`,
    `    <span class="music-example-kicker">🎼 Ejemplo musical</span>\n    <strong>${e(titulo)}</strong>`,
    compositor ? ` <span class="music-example-composer">— ${e(compositor)}</span>` : '',
    `\n    <small>Compases ${e(ini || 1)}–${e(fin || 8)} · ${e(edicion)}</small>\n  </figcaption>\n`,
    teacher ? [
      `  <div class="music-example-range"><label>Compases `,
      `<input class="score-start-input" type="number" min="1" value="${e(ini || 1)}"></label>`,
      `<label>a <input class="score-end-input" type="number" min="1" value="${e(fin || 8)}"></label></div>\n`
    ].join('') : '',
    `  <div class="score-preview-container"><div class="score-preview-box" data-candidate-id="${e(ej.id)}" `,
    `data-run-id="${e(runId)}" data-current-mode="svg"${vozAttr}>`,
    `<div class="score-loading"><span class="spinner"></span> Renderizando partitura…</div></div></div>\n`,
    observar ? `  <p class="music-example-observe"><strong>Observa:</strong> ${e(observar)}</p>\n` : '',
    teacher ? analysisSummary(ej.analisis) : '',
    `</figure>\n`
  ].join('');
}

// Notas numeradas: cada cita (fuente + pasaje) recibe un número único.
export function buildNotes(run) {
  const notes = [];
  const index = new Map();
  const refsByClaim = [];
  for (const claim of run.result?.claims || []) {
    const refs = [];
    for (const ev of claim?.evidence || []) {
      const key = `${ev.source_id}:::${ev.quote}`;
      if (!index.has(key)) {
        const src = (run.evidence || []).find(s => s.source_id === ev.source_id);
        notes.push({ n: notes.length + 1, ev, src });
        index.set(key, notes.length);
      }
      const n = index.get(key);
      if (!refs.includes(n)) refs.push(n);
    }
    refsByClaim.push(refs);
  }
  return { notes, refsByClaim };
}

export function noteRefs(refs) {
  if (!refs?.length) return '';
  return `<span class="note-refs" aria-label="Notas">${refs.map(n =>
    `<a href="#nota-${e(n)}" class="note-ref">${e(n)}</a>`).join('')}</span>`;
}

export function notesListHTML(notes, locatorLabel) {
  if (!notes.length) return '';
  return [
    `<ol class="notes-list">`,
    notes.map(({ n, ev, src }) => {
      const m = src?.metadata || {};
      const autores = normalizeAuthorsDisplay(m.authors).join('; ') || 'Sin autor identificado';
      const loc = src ? locatorLabel(src.locator || {}) : '';
      return [
        `<li id="nota-${e(n)}"><span class="note-source"><strong>${e(autores)}</strong>`,
        m.year ? ` (${e(m.year)})` : '',
        `, <em>${e(m.title || 'Fuente')}</em>`, loc ? `, ${e(loc)}` : '', `.</span>`,
        ev.quote ? `<blockquote>«${e(ev.quote)}»</blockquote>` : '',
        `</li>`
      ].join('');
    }).join(''),
    `</ol>`
  ].join('');
}

export function keyPointsHTML(points, label = 'Ideas clave') {
  if (!points?.length) return '';
  return [
    `<aside class="key-points"><strong>${e(label)}</strong><ul>`,
    points.map(p => `<li>${e(p)}</li>`).join(''),
    `</ul></aside>`
  ].join('');
}

export function markdownBlock(text) {
  return formatMarkdown(text || '');
}

export const actions = {};
