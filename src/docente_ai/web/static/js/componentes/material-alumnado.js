import { request, token, api } from '../api.js';
import { switchEgyptTab, renderEgyptInfographic } from '../infografias/egipto.js';
import { store } from '../state.js';
import {
  render, toast, dialog, e, formatMarkdown, icon, modal,
  normalizeAuthorDisplay, normalizeAuthorsDisplay
} from '../ui.js';
import {
  POLYPHONY_LISTENINGS,
  getRunListenings,
  is15thCenturyPolyphony,
  isAncientEgypt,
  isNTAMSubject,
  normalizeTopic,
  renderEgyptListeningsHTML,
  renderListeningCardItem,
  renderStudentDiscographySection,
} from './audiciones.js';
import { renderStudentInfographic } from '../infografias/musica.js';
import { initScorePreviews } from './partituras.js';
import { renderDidacticComponent, initDidacticInteractions } from './didacticos/index.js';
// Módulo local: responsabilidad separada sin alterar el contenido.

export function cleanStudentText(text, isConsigna = false) {
  if (!text) return '';
  let res = String(text);
  if (isConsigna) {
    res = res.replace(/pasajes\s+de\s+S\d+/gi, 'pasajes de las fuentes');
    res = res.replace(/\(?\s*Fuente:\s*S\d+\s*\)?/gi, '');
    res = res.replace(/\(\s*S\d+(?:\s*,\s*S\d+)*\s*\)/g, '');
    res = res.replace(/\bS\d+(?:\s+quote[_\s-]?\d+)?\b/g, '');
  } else {
    res = res.replace(/pasajes\s+de\s+S\d+/gi, 'pasajes de las fuentes documentales');
    res = res.replace(/Fuente:\s*S\d+/gi, '');
    res = res.replace(/\(\s*S\d+(?:\s*,\s*S\d+)*\s*\)/g, '');
    res = res.replace(/\bS\d+\b/g, '');
  }
  res = res.replace(/\(\s*\)/g, '').replace(/ {2,}/g, ' ').trim();
  return res;
}

export function formatStudentResource(item) {
  if (!item) return null;
  if (typeof item === 'string') {
    const cleaned = cleanStudentText(item, true);
    return cleaned || null;
  }
  if (typeof item === 'object') {
    const rec = cleanStudentText(item.recurso || '', true);
    const tipo = (item.tipo || '').toLowerCase().trim();
    const pendiente = Boolean(item.pendiente);
    if (tipo === 'dato' && pendiente) {
      return null;
    }
    if (pendiente) {
      const descMap = {
        partitura: 'partitura que te entregará el profesor',
        grabacion: 'grabación que escucharemos en clase',
        texto: 'texto que te entregará el profesor',
        imagen: 'imagen que proyectará el profesor',
      };
      const desc = descMap[tipo] || 'material que te entregará el profesor';
      if (rec) {
        return `${rec} (${desc})`;
      }
      return desc.charAt(0).toUpperCase() + desc.slice(1);
    }
    return rec || null;
  }
  return cleanStudentText(String(item), true);
}

export function renderDidacticSection(run, options = {}) {
  const comps = run.result?.resolved_didactic_components || [];
  if (!comps.length) return '';
  const filtered = comps.filter(dc => !(options.skipTimeline && dc.tipo === 'linea_temporal'));
  if (!filtered.length) return '';
  return [
    '    <!-- COMPONENTES DIDÁCTICOS Y MODELOS ACÚSTICOS CALCULADOS -->\n',
    '    <section class="student-section section-didactic-models">\n',
    '      <div class="student-section-header">\n',
    '        <span class="student-section-number">📐</span>\n',
    '        <div>\n',
    '          <h2>Modelos gráficos y acústicos calculados</h2>\n',
    '          <p class="student-section-intro">' +
    'Componentes interactivos calculados deterministamente a partir de la teoría musical clásica.</p>\n',
    '        </div>\n      </div>\n      <div class="didactic-models-container">\n',
    filtered.map(dc => renderDidacticComponent(dc)).join(''),
    '\n      </div>\n    </section>\n\n',
  ].join('');
}

export function studentDocumentHTML(run) {
  const context = run.request?.pedagogy || {},
    plan = run.result?.plan || {},
    claims = run.result?.claims || [];
  const session = context.session;
  const sources = [...new Map((run.evidence || []).map(item => [item.document_id, item.metadata])).values()];
  const rawQuestion = (run.original_topic || run.request?.original_topic || run.request?.question || '').trim();
  const normalizedQuestion = normalizeTopic(rawQuestion);
  const rawTitle = (run.display_title || run.title || run.request?.display_title || '').trim();
  const title = rawTitle || (normalizedQuestion.charAt(0).toLocaleUpperCase('es') + normalizedQuestion.slice(1));
  const visuals = run.result?.visualizations || [];
  const isNTAM = isNTAMSubject(run);
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : getRunListenings(run);
  const isFichaVerified = Boolean(run.ficha?.verificado === true);
  const timelineComp = (run.result?.resolved_didactic_components || []).find(c => c.tipo === 'linea_temporal');
  let timelineRendered = false;
  const section2Title = isPolyphony ? 'MODELOS Y ANÁLISIS DE TEXTURAS' : 'ESQUEMA CONCEPTUAL Y ESTRUCTURAS';
  const hasFichaConceptos = Boolean(run.ficha?.conceptos?.length);
  const resolvedScores = (run.result?.resolved_music_requests || []).filter(item => {
    if (item.status !== 'resuelto_catalogo' || !item.ejemplo) return false;
    const ej = item.ejemplo;
    const isTheory = ej.calculado_teoria || ej.fuente === 'Calculado a partir de la teoría' ||
      item.origen === 'calculado_teoria';
    const hasUiVerification = Boolean(ej.verificado_por && ej.verificado_en);
    return isTheory || (Boolean(item.verificado) && hasUiVerification);
  });
  let elapsed = 0;

  // Extraer autores citados realmente
  const citedAuthors = [];
  for (const s of sources) {
    for (const a of (s?.authors || [])) {
      const norm = normalizeAuthorDisplay(a);
      if (norm && !citedAuthors.includes(norm)) citedAuthors.push(norm);
    }
  }
  let authorsSubtitle = '';
  if (citedAuthors.length === 1) {
    authorsSubtitle = ` (${citedAuthors[0]})`;
  } else if (citedAuthors.length === 2) {
    authorsSubtitle = ` (${citedAuthors[0]} y ${citedAuthors[1]})`;
  } else if (citedAuthors.length > 2) {
    authorsSubtitle = ` (${citedAuthors.slice(0, -1).join(', ')} y ${citedAuthors[citedAuthors.length - 1]})`;
  }

  // Fuentes deduplicadas por autor
  const seenAuthors = new Set();
  const studentSources = [];
  for (const s of sources) {
    const t = s?.title || '';
    if (!t || t.includes('Fuente de evaluación:') || t.toLowerCase().includes('prueba')) continue;
    const primaryAuthor = s.authors?.[0]?.toLowerCase()?.trim();
    if (primaryAuthor && seenAuthors.has(primaryAuthor)) continue;
    if (primaryAuthor) seenAuthors.add(primaryAuthor);
    studentSources.push(s);
  }

  return [
    `<article class="student-handout">\n    <header class="student-cover">\n      `,
    `<div class="student-brand">\n        <span class="student-pill">ARKHÉ · `,
    `MATERIAL DE CLASE</span>\n        <span class="student-topic-tag">CUADERNO `,
    `DIDÁCTICO DEL ALUMNADO</span>\n      </div>\n      <h1>${e(title)}</h1>\n`,
    `      <div class="student-meta">\n        <strong>${e(context.group?.name || 'Grupo')}</strong>\n` +
    `        <span>${e(context.group?.level || 'Conservatorio')}</span>\n` +
    `        <span>⏱ ${e(context.duration_minutes || 60)} minutos</span>\n` +
    `        ${session ? `<span>📅 ${e(session.date)}</span>` : ''}\n      </div>\n    </header>\n\n`,
    `    <!-- OBJETIVOS DIDÁCTICOS -->\n    <section class="student-section section-intro">\n`,
    `      <div class="student-section-header">\n        <span class="student-section-number">🎯</span>\n`,
    `        <div>\n          <h2>Qué vamos a aprender</h2>\n          <p class="student-section-intro">`,
    `Objetivos y competencias formativas que desarrollaremos a lo largo de la sesión.</p>\n`,
    `        </div>\n      </div>\n      <ol class="student-objectives">\n        `,
    `${(plan.objectives || []).map(item => `<li>${e(cleanStudentText(item, true))}</li>`).join('')}`,
    `\n      </ol>\n    </section>\n\n`,
    `    <!-- SECCIÓN 01: CONTENIDO TEÓRICO DE LAS FUENTES -->\n`,
    `    <section class="student-section section-theory">\n      <div class="student-section-header">\n`,
    `        <span class="student-section-number">01</span>\n        <div>\n`,
    `          <h2>Contenido teórico de las fuentes</h2>\n`,
    `          <p class="student-section-intro">Análisis musicológico e histórico basado en las fuentes `,
    `documentales autorizadas${e(authorsSubtitle)}.</p>\n        </div>\n      </div>\n`,
    `      <div class="theory-claims-list">\n`,
    claims.map((claim, index) => {
      const ev0 = claim.evidence?.[0];
      let sourceBadge = '';
      if (ev0) {
        const src = (run.evidence || []).find(it => it.source_id === ev0.source_id);
        const author = normalizeAuthorDisplay(src?.metadata?.authors?.[0]?.split(',')[0]?.trim());
        const pIdx = src?.locator?.pdf_page_index;
        const loc = pIdx ? ('pág. ' + String(pIdx)) : '';
        const badgeLabel = author ? (loc ? (author + ', ' + loc) : author) : '';
        if (badgeLabel) {
          sourceBadge = `<div class="claim-source-badge"><span>📖 ${e(badgeLabel)}</span></div>`;
        }
      }
      return [
        `\n          <div class="student-content theory-claim-card">\n`,
        `            <span class="claim-index-badge">${e(String(index + 1).padStart(2, '0'))}</span>\n`,
        `            <div class="claim-body">\n`,
        `              ${formatMarkdown(cleanStudentText(claim.student_summary || claim.text, false))}\n`,
        `              ${sourceBadge}\n`,
        `            </div>\n          </div>\n        `
      ].join('');
    }).join(''),
    `\n      </div>\n    </section>\n\n`,
    `    <!-- SECCIÓN 02: ESQUEMA GRÁFICO -->\n    <section class="student-section section-infographic">\n`,
    `      <div class="student-section-header">\n        <span class="student-section-number">02</span>\n`,
    `        <div>\n          <h2>Esquema gráfico y estructuras</h2>\n`,
    `          <p class="student-section-intro">Estructuras formales y esquemas conceptuales para el aula.</p>\n`,
    `        </div>\n      </div>\n`,
    (isFichaVerified ?
      (isEgypt ? renderEgyptInfographic(run) : (isPolyphony ? renderStudentInfographic(run) : '')) : '') || (
      visuals.length ? [
        `\n        <div class="infographic-poster">\n          <div class="infographic-main-head">\n`,
        `            <div class="info-tag-row"><span class="info-badge">${e(title.toUpperCase())}</span></div>\n`,
        `            <h2>${e(section2Title)}</h2>\n`,
        `          </div>\n          <div class="visual-items">\n`,
        visuals.map(v => {
          const isChronological = v.type === 'timeline' ||
            /cronolog|tiempo|hist[oó]ric|siglo/i.test(v.title || '') ||
            (v.items || []).some(it => /a\.\s*c\.|d\.\s*c\.|siglo|\b\d{3,4}\b/i.test(it.label || ''));
          if (isChronological && timelineComp) {
            timelineRendered = true;
            return renderDidacticComponent(timelineComp);
          }
          return [
            `            <div class="visual-card">\n              <h3>${e(v.title)}</h3>\n`,
            v.caption ? `              <p class="visual-caption">${e(v.caption)}</p>\n` : '',
            `              <div class="visual-items">\n`,
            (v.items || []).map(it => [
              `                <div class="visual-item">\n                  <strong>${e(it.label)}</strong>\n`,
              `                  <span>${e(it.detail)}</span>\n                </div>\n`
            ].join('')).join(''),
            `              </div>\n            </div>\n`
          ].join('');
        }).join(''),
        `          </div>\n        </div>\n`
      ].join('') : [
        `\n        <div class="infographic-poster">\n          <div class="infographic-main-head">\n`,
        `            <div class="info-tag-row"><span class="info-badge">${e(title.toUpperCase())}</span></div>\n`,
        `            <h2>${e(section2Title)}</h2>\n          </div>\n`,
        `          <div class="visual-items">\n`,
        claims.slice(0, 4).map((c, i) => [
          `            <div class="visual-item"><strong>Eje ${e(i + 1)}</strong>`,
          `<span>${e(cleanStudentText(c.text.slice(0, 180), false))}…</span></div>\n`
        ].join('')).join(''),
        `          </div>\n        </div>\n`
      ].join('')
    ),
    `\n    </section>\n\n`,
    renderDidacticSection(run, { skipTimeline: timelineRendered }),
    hasFichaConceptos ? [
      `    <!-- SECCIÓN 03: CONCEPTOS OBLIGATORIOS PARA APRENDER -->\n`,
      `    <section class="student-section section-concepts">\n      <div class="student-section-header">\n`,
      `        <span class="student-section-number">03</span>\n        <div>\n`,
      `          <h2>Conceptos obligatorios para aprender</h2>\n`,
      `          <p class="student-section-intro">Vocabulario técnico y conceptos analíticos indispensables.</p>\n`,
      `        </div>\n      </div>\n`,
      `      <div class="concept-grid">\n`,
      run.ficha.conceptos.map(c => [
        `\n        <div class="concept-card">\n          <div class="concept-head">`,
        `<span class="concept-badge">${e(c.categoria || (isFichaVerified ? 'CONCEPTO' : 'REVISIÓN'))}</span>`,
        `<strong>${e(c.termino)}</strong></div>\n          <p>${e(c.definicion)}</p>\n        </div>\n`
      ].join('')).join(''),
      `\n      </div>\n    </section>\n\n`
    ].join('') : '',
    `${(isNTAM || (!isEgypt && !isPolyphony && (!listenings || !listenings.length))) ? '' : [
      `<!-- SECCIÓN 04: RELACIÓN DE AUDICIONES COMENTADAS -->\n`,
      `    <section class="student-section section-listenings">\n`,
      `      <div class="student-section-header">\n`,
      `        <span class="student-section-number">04</span>\n`,
      `        <div>\n          <h2>Relación de audiciones comentadas</h2>\n`,
      `          <p class="student-section-intro">Obras y repertorio de audición activa con análisis formal.</p>\n`,
      `        </div>\n      </div>\n      <div class="listening-grid">\n        `,
      `${
        isEgypt ? renderEgyptListeningsHTML(false) : isPolyphony ? POLYPHONY_LISTENINGS.map(l =>
          renderListeningCardItem(l, false)).join('') : (listenings?.length ? listenings.map(l =>
          renderListeningCardItem(l, false)).join('') : '')
      }`,
      `\n      </div>\n    </section>\n\n`
    ].join('')}`,
    `<!-- SECCIÓN 05: TRABAJOS PARA EL ALUMNADO (Única lista unificada de tareas) -->\n`,
    `    <section class="student-section section-assignments">\n`,
    `      <div class="student-section-header">\n`,
    `        <span class="student-section-number">05</span>\n        <div>\n`,
    `          <h2>Trabajos para el alumnado</h2>\n`,
    `          <p class="student-section-intro">Secuencia de actividades prácticas y análisis desarrolladas `,
    `en la sesión de clase.</p>\n        </div>\n      </div>\n\n`,
    `      <div class="assignment-grid">\n`,
    (() => {
      const renderedScoreKeys = new Set();
      return (plan.activities || []).map((activity, index) => {
        const mins = Number(activity.minutes) || 0;
        const start = elapsed;
        elapsed += mins;
        const taskText = cleanStudentText(activity.student_task || activity.instructions || '', true);
        const groupTag = activity.grouping ? ` [${e(activity.grouping)}]` : '';

        const actScores = resolvedScores.filter(m => {
          const key = m.ejemplo?.id || m.request_id || m.request?.work || '';
          if (key && renderedScoreKeys.has(key)) return false;
          let match = false;
          if (m.request?.activity_title && m.request.activity_title === activity.title) {
            match = true;
          } else if (m.request_id && activity.music_request_id === m.request_id) {
            match = true;
          } else {
            const obra = m.ejemplo?.obra || m.request?.work || '';
            if (obra && activity.title && activity.title.toLowerCase().includes(obra.toLowerCase())) {
              match = true;
            } else if (resolvedScores.length === 1 && (
              activity.title?.toLowerCase().includes('notacion') ||
              activity.title?.toLowerCase().includes('seikilos')
            )) {
              match = true;
            }
          }
          if (match) {
            if (key) renderedScoreKeys.add(key);
            return true;
          }
          return false;
        });

        const scoreBoxesHtml = actScores.map(m => {
          const ej = m.ejemplo;
          const isTheory = ej.calculado_teoria || ej.fuente === 'Calculado a partir de la teoría';
          const badgeText = isTheory ? '✓ Calculado a partir de la teoría' : '✓ Partitura verificada';
          const obraStr = ej.obra || m.request?.work || 'Obra musical';
          const secStr = ej.seccion || m.request?.section || '';
          const scoreTitle = obraStr + (secStr ? ' · ' + secStr : '');
          const compStr = ej.compositor || m.request?.composer || 'Anónimo';
          return [
            `\n          <div class="student-score-box score-card-verified score-candidate-item" ` +
            `data-candidate-id="${e(ej.id)}" data-run-id="${e(run.id)}">\n`,
            `            <div class="score-card-head">\n              <div>\n`,
            `                <span class="badge info">${badgeText}</span>\n`,
            `                <h4>${e(scoreTitle)} — ${e(compStr)}</h4>\n`,
            `                <small class="score-meta">Compases ${e(ej.compases || '1-3')} · ` +
            `Fuente: ${e(ej.fuente || 'Catálogo')}</small>\n`,
            `              </div>\n            </div>\n`,
            `            <div class="score-preview-container">\n`,
            `              <div class="score-preview-box" data-candidate-id="${e(ej.id)}" ` +
            `data-run-id="${e(run.id)}" data-current-mode="svg">\n`,
            `                <div class="score-loading"><span class="spinner"></span> ` +
            `Renderizando partitura con Verovio…</div>\n`,
            `              </div>\n            </div>\n`,
            `          </div>\n`
          ].join('');
        }).join('');

        return [
          `\n        <div class="assignment-card">\n          <div class="assign-head">\n`,
          `            <span class="assign-tag">${start}–${elapsed} min</span>\n`,
          `            <strong>${e(index + 1)}. ${e(activity.title)}${groupTag}</strong>\n`,
          `          </div>\n`,
          taskText ? `          <p class="activity-task"><strong>Tarea:</strong> ${e(taskText)}</p>\n` : '',
          activity.deliverable ? [
            `          <p class="activity-deliverable"><strong>Entregable:</strong> `,
            `${e(cleanStudentText(activity.deliverable, true))}</p>\n`
          ].join('') : '',
          scoreBoxesHtml,
          `        </div>\n`
        ].join('');
      }).join('');
    })(),
    (isFichaVerified && run.ficha?.tareas_adicionales_casa?.length) ? [
      `\n      <div class="homework-tasks-block">\n`,
      `        <h3 class="homework-title">🏠 Tareas adicionales para casa</h3>\n`,
      run.ficha.tareas_adicionales_casa.map(t => [
        `        <div class="assignment-card homework-card">\n          <div class="assign-head">\n`,
        `            <span class="assign-tag">${e(t.tag || 'CASA')}</span>\n`,
        `            <strong>${e(t.titulo)}</strong>\n          </div>\n`,
        `          <p><strong>Objetivo:</strong> ${e(t.objetivo)}</p>\n`,
        `        </div>\n`
      ].join('')).join(''),
      `      </div>\n`
    ].join('') : '',
    `\n      </div>\n    </section>\n\n`,
    `    <!-- SECCIÓN 06: FUENTES Y BIBLIOGRAFÍA DE CONSULTA -->\n`,
    `    <section class="student-section section-sources">\n      <div class="student-section-header">\n`,
    `        <span class="student-section-number">06</span>\n        <div>\n`,
    `          <h2>Fuentes y antologías de consulta</h2>\n`,
    `          <p class="student-section-intro">Bibliografía autorizada utilizada para elaborar este material.</p>\n`,
    `        </div>\n      </div>\n      <div class="sources-pills-list">\n`,
    studentSources.map(meta => [
      `\n        <div class="source-pill-card">\n          <span class="source-pill-icon">📖</span>\n`,
      `          <div>\n            <strong>${e(meta.title || 'Fuente documental')}</strong>\n`,
      `            <small>${e(normalizeAuthorsDisplay(meta.authors).join(', ') || 'Biblioteca Arkhé')}`,
      `${meta.year ? ` · ${e(meta.year)}` : ''}</small>\n          </div>\n        </div>\n`
    ].join('')).join(''),
    `\n      </div>\n    </section>\n  </article>`
  ].join('');
}

export async function printStudentDocument() {
  const handout = document.querySelector('.student-dialog .student-handout');
  if (!handout) {
    document.body.classList.add('student-printing');
    window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), {
      once: true
    });
    window.print();
    return;
  }

  // Esperar a que terminen los renderizados Verovio y SVG de componentes antes de clonar
  const boxes = Array.from(document.querySelectorAll('.student-dialog .score-preview-box'));
  await Promise.all(boxes.map(b => b._renderPromise || Promise.resolve()));

  // Clone handout content so the on-screen modal stays intact
  const clone = handout.cloneNode(true);

  // For Ancient Egypt sheets: remove interactive tabs and show both sheets sequentially
  clone.querySelectorAll('.egypt-sheet-tabs').forEach(el => el.remove());
  clone.querySelectorAll('.egypt-sheet').forEach(el => {
    el.style.display = 'block';
  });

  // Remove buttons and interactive elements
  clone.querySelectorAll('.button, button, [data-action], .score-loading').forEach(el => el.remove());

  // Use an isolated hidden iframe for 100% clean, non-modal browser printing
  let iframe = document.getElementById('student-print-frame');
  if (iframe) iframe.remove();

  iframe = document.createElement('iframe');
  iframe.id = 'student-print-frame';
  iframe.style.position = 'fixed';
  iframe.style.right = '0';
  iframe.style.bottom = '0';
  iframe.style.width = '0';
  iframe.style.height = '0';
  iframe.style.border = '0';
  iframe.style.visibility = 'hidden';
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow.document;
  const docTitle = document.querySelector('.student-cover h1')?.textContent?.trim() ||
    'Material para el alumnado';

  doc.open();
  doc.write('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>' + docTitle +
    ' · Arkhé</title></head><body class="print-isolated-body"></body></html>');
  doc.close();

  // Copy all style elements and stylesheets so custom typography, colors, and layout apply
  document.querySelectorAll('link[rel="stylesheet"], style').forEach(node => {
    doc.head.appendChild(node.cloneNode(true));
  });

  doc.body.appendChild(clone);

  if (iframe.contentWindow.document.fonts) {
    await iframe.contentWindow.document.fonts.ready;
  }
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

  try {
    iframe.contentWindow.focus();
    iframe.contentWindow.print();
  } catch (e) {
    document.body.classList.add('student-printing');
    window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), {
      once: true
    });
    window.print();
  }
}

export async function studentMaterialModal(id) {
  const run = await api('/runs/' + encodeURIComponent(id));
  if (!run.request?.pedagogy || !run.result?.plan) throw new Error(
    'Esta propuesta todavía no tiene material válido para el alumnado.');
  modal('Material para el alumnado', [
    `${studentDocumentHTML(run)}`,
    `<div class="student-share-actions"><div><strong>Listo para compartir</strong><p>`,
    `Copia el contenido en Google Classroom o guárdalo como PDF.</p></div><button `,
    `class="button" data-copy-student="${e(id)}">${icon('copy')}`,
    `Copiar para Classroom</button><button class="button" data-download-student="${e(id)}">`,
    `${icon('download')}Descargar Markdown</button><button class="button primary" `,
    `data-action="print-student">${icon('document')}Imprimir / Guardar PDF</button></div>`
  ].join(''));
  dialog.classList.add('student-dialog');
  initScorePreviews();
  initDidacticInteractions(dialog);
}

// Acciones y formularios de este módulo; delegación central en main.js.
async function accionOpenStudentRun({target}) {
  await studentMaterialModal(target.dataset.studentRun);
}

async function accionOpenCopyStudent({target}) {
  const response = await request('/api/runs/' + encodeURIComponent(target.dataset.copyStudent) +
    '?student=1', {
      headers: {
        'X-Docente-Token': token
      }
    });
  if (!response.ok) throw new Error('No se pudo preparar el material para el alumnado.');
  await navigator.clipboard.writeText(await response.text());
  toast('Material copiado. Ya puedes pegarlo en Google Classroom.');
}

async function accionOpenDownloadStudent({target}) {
  const identifier = target.dataset.downloadStudent;
  const response = await request('/api/runs/' + encodeURIComponent(identifier) + '?student=1', {
    headers: {
      'X-Docente-Token': token
    }
  });
  if (!response.ok) throw new Error('No se pudo descargar el material para el alumnado.');
  const url = URL.createObjectURL(await response.blob()),
    link = document.createElement('a');
  link.href = url;
  const headerFilename = response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1];
  link.download = headerFilename || ('material-alumnado-' + identifier + '.md');
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast('Material para el alumnado descargado.');
}

async function accionEgyptTab({target}) {
  switchEgyptTab(target, target.dataset.tab);
  store.tab = target.dataset.tab;
  render();
}

async function accionPrintStudent() {
  printStudentDocument();
}

export const actions = {
  'open-student-run': accionOpenStudentRun,
  'copy-student': accionOpenCopyStudent,
  'download-student': accionOpenDownloadStudent,
  'egypt-tab': accionEgyptTab,
  'print-student': accionPrintStudent,
};

export const clickBindings = [
  {priority: 3, matches: target => target.dataset.studentRun, action: 'open-student-run'},
  {priority: 5, matches: target => target.dataset.copyStudent, action: 'copy-student'},
  {priority: 7, matches: target => target.dataset.downloadStudent, action: 'download-student'},
  {priority: -1, matches: target => target.matches('.egypt-tab-btn'), action: 'egypt-tab'},
];

export const windowEvents = {
  'beforeprint': () => {
    if (dialog?.open && dialog?.classList.contains('student-dialog')) {
      document.body.classList.add('student-printing');
      dialog.querySelectorAll('.egypt-sheet').forEach(el => {
        el.style.display = 'block';
      });
    }
  },
  'afterprint': () => {
    document.body.classList.remove('student-printing');
  },
};
