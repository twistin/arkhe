import { request, token, api } from '../api.js';
import { switchEgyptTab, renderEgyptInfographic } from '../infografias/egipto.js';
import { renderStudentInfographic } from '../infografias/musica.js';
import { store } from '../state.js';
import {
  render, toast, dialog, e, formatMarkdown, icon, modal,
  normalizeAuthorDisplay, normalizeAuthorsDisplay
} from '../ui.js';
import {
  getRunListenings,
  normalizeTopic,
  renderListeningCardItem,
} from './audiciones.js';
import { initScorePreviews } from './partituras.js';
import { renderDidacticComponent, initDidacticInteractions } from './didacticos/index.js';
import {
  sectionTitle, examplesForClaim, unlinkedExamples, scoreExampleCard, keyPointsHTML
} from './secciones.js';
// Módulo local: material para el alumnado estructurado por requisitos.

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

export function limitWords(text, maxWords = 60) {
  if (!text) return '';
  const trimmed = String(text).trim();
  const words = trimmed.split(/\s+/);
  if (words.length <= maxWords) return trimmed;
  return words.slice(0, maxWords).join(' ') + '…';
}

export function formatStudentRequirementTitle(req, index) {
  if (!req) return `Sección ${index + 1}`;
  if (req.student_title) return req.student_title;
  let desc = String(req.description || '').trim();
  desc = desc.replace(
    /^(?:explicar|exponer|presentar|analizar|describir|comprender|incluir|representar|citar|distinguir|resumir)\s+/i,
    ''
  ).replace(/^(?:los|las|el|la|un|una|a\s+los|a\s+las)\s+/i, '');
  if (!desc) return `Tema ${index + 1}`;
  return desc.charAt(0).toUpperCase() + desc.slice(1);
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

export function renderStudentScoreBox(score, runId) {
  const ej = score.ejemplo;
  if (!ej) return '';
  const isTheory = ej.calculado_teoria || ej.fuente === 'Calculado a partir de la teoría';
  const badgeText = isTheory ? '✓ Calculado a partir de la teoría' : '✓ Partitura verificada';
  const obraStr = ej.obra || score.request?.work || 'Obra musical';
  const secStr = ej.seccion || score.request?.section || '';
  const scoreTitle = obraStr + (secStr ? ' · ' + secStr : '');
  const compStr = ej.compositor || score.request?.composer || 'Anónimo';
  return [
    `\n          <div class="student-score-box score-card-verified score-candidate-item" `,
    `data-candidate-id="${e(ej.id)}" data-run-id="${e(runId)}">\n`,
    `            <div class="score-card-head">\n              <div>\n`,
    `                <span class="badge info">${badgeText}</span>\n`,
    `                <h4>${e(scoreTitle)} — ${e(compStr)}</h4>\n`,
    `                <small class="score-meta">Compases ${e(ej.compases || '1-3')} · `,
    `Fuente: ${e(ej.fuente || 'Catálogo')}</small>\n`,
    `              </div>\n            </div>\n`,
    `            <div class="score-preview-container">\n`,
    `              <div class="score-preview-box" data-candidate-id="${e(ej.id)}" `,
    `data-run-id="${e(runId)}" data-current-mode="svg">\n`,
    `                <div class="score-loading"><span class="spinner"></span> `,
    `Renderizando partitura con Verovio…</div>\n`,
    `              </div>\n            </div>\n`,
    `          </div>\n`
  ].join('');
}

export function studentVisualHTML(visual) {
  const type = ['sequence', 'relationship', 'table'].includes(visual?.type) ? visual.type : 'relationship';
  const items = (visual?.items || []).map(item =>
    `<div class="visual-node"><strong>${e(item.label)}</strong>` +
    `<span>${e(cleanStudentText(item.detail, false))}</span></div>`
  ).join('');
  return [
    `<div class="student-visual source-visual source-visual-${e(type)}"><h3>${e(visual.title)}</h3>`,
    `<div class="visual-canvas">${items}</div>`,
    visual.caption ? `<p class="visual-caption">${e(cleanStudentText(visual.caption, false))}</p>` : '',
    `</div>`
  ].join('');
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

export function renderFichaInfographic(run) {
  if (!run?.ficha?.verificado || !run?.ficha?.infografia) return '';
  const infog = run.ficha.infografia;
  if (infog.organologia) {
    return renderEgyptInfographic(run);
  }
  if (infog.modelos_misa) {
    return renderStudentInfographic(run);
  }
  return '';
}

export function studentDocumentHTML(run) {
  const context = run.request?.pedagogy || {},
    plan = run.result?.plan || {},
    claims = run.result?.claims || [],
    coverage = run.result?.coverage || [],
    fulfillment = run.result?.fulfillment || [];
  const session = context.session;
  const sources = [...new Map((run.evidence || []).map(item => [item.document_id, item.metadata])).values()];
  const rawQuestion = (run.original_topic || run.request?.original_topic || run.request?.question || '').trim();
  const normalizedQuestion = normalizeTopic(rawQuestion);
  const rawTitle = (run.display_title || run.title || run.request?.display_title || '').trim();
  const title = rawTitle || (normalizedQuestion.charAt(0).toLocaleUpperCase('es') + normalizedQuestion.slice(1));
  const listenings = getRunListenings(run);
  const isFichaVerified = Boolean(
    run.ficha?.verificado === true && run.ficha?.verificado_por && run.ficha?.verificado_en
  );
  const fichaConceptos = isFichaVerified ? (run.ficha?.conceptos || []) : [];
  const requirements = run.result?.requirements || run.request?.pedagogy?.requirements ||
    run.request?.requirements || [];
  const resolvedComps = run.result?.resolved_didactic_components || [];
  let elapsed = 0;

  // Fuentes deduplicadas por autor para el pie
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

  // Identificar requisitos no cumplidos para omitirlos y saber qué actividades quedan afectadas
  const unmetReqIds = new Set();
  for (const f of fulfillment) {
    if (f.estado === 'pendiente_profesor' || f.estado === 'sin_fuentes') {
      unmetReqIds.add(f.requirement_id);
    }
  }
  if (!fulfillment.length) {
    for (const c of coverage) {
      if (c.status === 'sin_fuentes' || c.status === 'pendiente_profesor') {
        unmetReqIds.add(c.requirement_id);
      }
    }
  }

  // --- 1. PORTADA Y ENCABEZADO ---
  const headerHtml = [
    `<article class="student-handout">\n    <header class="student-cover">\n      `,
    `<div class="student-brand">\n        <span class="student-pill">ARKHÉ · `,
    `MATERIAL DE CLASE</span>\n        <span class="student-topic-tag">CUADERNO `,
    `DIDÁCTICO DEL ALUMNADO</span>\n      </div>\n      <h1>${e(title)}</h1>\n`,
    `      <div class="student-meta">\n        <strong>${e(context.group?.name || 'Grupo')}</strong>\n` +
    `        <span>${e(context.group?.level || 'Conservatorio')}</span>\n` +
    `        <span>⏱ ${e(context.duration_minutes || 60)} minutos</span>\n` +
    `        ${session ? `<span>📅 ${e(session.date)}</span>` : ''}\n      </div>\n    </header>\n\n`
  ].join('');

  // --- 2. QUÉ VAMOS A APRENDER ---
  const introHtml = [
    `    <!-- OBJETIVOS DIDÁCTICOS -->\n    <section class="student-section section-intro">\n`,
    `      <div class="student-section-header">\n        <span class="student-section-number">🎯</span>\n`,
    `        <div>\n          <h2>Qué vamos a aprender</h2>\n          <p class="student-section-intro">`,
    `Objetivos y competencias formativas que desarrollaremos a lo largo de la sesión.</p>\n`,
    `        </div>\n      </div>\n      <ol class="student-objectives">\n        `,
    `${(plan.objectives || []).map(item => `<li>${e(cleanStudentText(item, true))}</li>`).join('')}`,
    `\n      </ol>\n    </section>\n\n`
  ].join('');

  // --- 3. CUERPO: SECCIONES DE TEORÍA CON EJEMPLOS Y GRÁFICOS ---
  // Cada sección procede de un bloque de contenido de la propuesta (título, explicación para el
  // alumnado, ideas clave y ejemplos musicales reales). Los requisitos no cumplidos no generan
  // texto de relleno: sus partituras pendientes simplemente no aparecen.
  let sectionsHtml = '';
  let sectionIndex = 0;
  const renderedArtifacts = new Set();
  const usedGlossaryTerms = new Set();
  const covByClaim = new Map();
  for (const c of coverage) {
    for (const cid of c.claim_ids || []) {
      if (!covByClaim.has(cid)) covByClaim.set(cid, c.requirement_id);
    }
  }
  const compsForClaim = (claimIndex) => resolvedComps.filter(dc => {
    if (renderedArtifacts.has('comp:' + dc.tipo)) return false;
    const reqId = covByClaim.get(claimIndex + 1);
    return Boolean(dc.requirement_id && reqId && dc.requirement_id === reqId);
  });

  claims.forEach((claim, i) => {
    sectionIndex += 1;
    const secNum = String(sectionIndex).padStart(2, '0');
    const secTitle = sectionTitle(claim, i);
    const bodyText = cleanStudentText(claim.student_summary || claim.text, false);
    const maxWords = claim.student_summary ? 180 : 90;

    let artifactsHtml = '';
    for (const dc of compsForClaim(i)) {
      renderedArtifacts.add('comp:' + dc.tipo);
      artifactsHtml += renderDidacticComponent(dc);
    }
    for (const item of examplesForClaim(run, claim)) {
      const key = 'score:' + item.ejemplo.id;
      if (renderedArtifacts.has(key)) continue;
      renderedArtifacts.add(key);
      artifactsHtml += scoreExampleCard(item, run.id);
    }

    let glossaryHtml = '';
    if (fichaConceptos.length > 0) {
      const fullSecStr = (secTitle + ' ' + bodyText).toLowerCase();
      for (const conc of fichaConceptos) {
        const term = (conc.termino || '').toLowerCase();
        if (term && fullSecStr.includes(term) && !usedGlossaryTerms.has(conc.termino)) {
          usedGlossaryTerms.add(conc.termino);
          glossaryHtml += [
            `<aside class="glossary-callout"><div class="glossary-callout-header">`,
            `<span class="glossary-callout-badge">GLOSARIO</span><strong>${e(conc.termino)}</strong></div>`,
            `<p>${e(limitWords(conc.definicion, 60))}</p></aside>`
          ].join('');
        }
      }
    }

    sectionsHtml += [
      `    <section class="student-section section-theory">\n`,
      `      <div class="student-section-header"><span class="student-section-number">${e(secNum)}</span>`,
      `<div><h2>${e(secTitle)}</h2></div></div>\n`,
      `      <div class="theory-layout">\n`,
      `        <div class="theory-text">${formatMarkdown(limitWords(bodyText, maxWords))}</div>\n`,
      keyPointsHTML(claim.key_points),
      glossaryHtml,
      `      </div>\n`,
      artifactsHtml ? `      <div class="section-artifacts">${artifactsHtml}</div>\n` : '',
      `    </section>\n\n`
    ].join('');
  });

  // Ejemplos y gráficos no ligados a una sección concreta
  let extraArtifacts = '';
  for (const item of unlinkedExamples(run)) {
    const key = 'score:' + item.ejemplo.id;
    if (renderedArtifacts.has(key)) continue;
    renderedArtifacts.add(key);
    extraArtifacts += scoreExampleCard(item, run.id);
  }
  for (const dc of resolvedComps) {
    if (renderedArtifacts.has('comp:' + dc.tipo)) continue;
    renderedArtifacts.add('comp:' + dc.tipo);
    extraArtifacts += renderDidacticComponent(dc);
  }
  const visualsHtml = (run.result?.visualizations || []).map(v => studentVisualHTML(v)).join('');
  const infographicHtml = renderFichaInfographic(run);
  if (extraArtifacts || visualsHtml || infographicHtml) {
    sectionIndex += 1;
    sectionsHtml += [
      `    <section class="student-section section-schemes">\n`,
      `      <div class="student-section-header">`,
      `<span class="student-section-number">${e(String(sectionIndex).padStart(2, '0'))}</span>`,
      `<div><h2>Esquemas y ejemplos</h2>`,
      `<p class="student-section-intro">Para repasar y comparar lo visto en clase.</p></div></div>\n`,
      infographicHtml, visualsHtml,
      extraArtifacts ? `      <div class="section-artifacts">${extraArtifacts}</div>\n` : '',
      `    </section>\n\n`
    ].join('');
  }

  // --- 4. AUDICIONES COMENTADAS (si existen en la ficha o criterios) ---
  let listeningsHtml = '';
  if (listenings && listenings.length > 0) {
    sectionIndex += 1;
    const secNum = String(sectionIndex).padStart(2, '0');
    listeningsHtml = [
      `    <!-- AUDICIONES COMENTADAS -->\n`,
      `    <section class="student-section section-listenings">\n`,
      `      <div class="student-section-header">\n`,
      `        <span class="student-section-number">${e(secNum)}</span>\n`,
      `        <div>\n`,
      `          <h2>Relación de audiciones comentadas</h2>\n`,
      `          <p class="student-section-intro">Obras y repertorio de audición activa con análisis formal.</p>\n`,
      `        </div>\n`,
      `      </div>\n`,
      `      <div class="listening-grid">\n`,
      listenings.map(l => renderListeningCardItem(l, false)).join(''),
      `\n      </div>\n`,
      `    </section>\n\n`
    ].join('');
  }

  // --- 5. TRABAJOS PARA EL ALUMNADO ---
  sectionIndex += 1;
  const assignSecNum = String(sectionIndex).padStart(2, '0');
  const assignmentsHtml = [
    `    <!-- TRABAJOS PARA EL ALUMNADO -->\n`,
    `    <section class="student-section section-assignments">\n`,
    `      <div class="student-section-header">\n`,
    `        <span class="student-section-number">${e(assignSecNum)}</span>\n`,
    `        <div>\n`,
    `          <h2>Trabajos para el alumnado</h2>\n`,
    `          <p class="student-section-intro">Secuencia de actividades prácticas y análisis desarrolladas `,
    `en la sesión de clase.</p>\n`,
    `        </div>\n`,
    `      </div>\n\n`,
    `      <div class="assignment-grid">\n`,
    (plan.activities || []).map((activity, index) => {
      const mins = Number(activity.minutes) || 0;
      const start = elapsed;
      elapsed += mins;
      const taskText = cleanStudentText(activity.student_task || activity.instructions || '', true);
      const groupTag = activity.grouping ? ` [${e(activity.grouping)}]` : '';

      // Comprobar si la actividad trabaja un requisito pendiente
      const isPendingResource = (activity.requirement_id && unmetReqIds.has(activity.requirement_id)) ||
        (activity.music_request_id && unmetReqIds.size > 0 &&
          [...unmetReqIds].some(rid => {
            const rObj = (requirements || []).find(r => r.id === rid);
            return rObj?.ejecutor === 'partitura_obra' || rObj?.ejecutor === 'analisis_sobre_partitura';
          }));

      const pendingBadge = isPendingResource ? [
        `\n          <div class="activity-resource-pending">\n`,
        `            <span>⚠️ Material que te entregará el profesor</span>\n`,
        `          </div>\n`
      ].join('') : '';

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
        pendingBadge,
        `        </div>\n`
      ].join('');
    }).join(''),
    `\n      </div>\n    </section>\n\n`
  ].join('');

  // --- 6. FUENTES Y BIBLIOGRAFÍA DE CONSULTA ---
  sectionIndex += 1;
  const sourcesSecNum = String(sectionIndex).padStart(2, '0');
  const sourcesHtml = [
    `    <!-- FUENTES Y BIBLIOGRAFÍA DE CONSULTA -->\n`,
    `    <section class="student-section section-sources">\n`,
    `      <div class="student-section-header">\n`,
    `        <span class="student-section-number">${e(sourcesSecNum)}</span>\n`,
    `        <div>\n`,
    `          <h2>Para saber más</h2>\n`,
    `          <p class="student-section-intro">Libros y antologías con los que se ha preparado este material.</p>\n`,
    `        </div>\n`,
    `      </div>\n`,
    `      <div class="sources-pills-list">\n`,
    studentSources.map(meta => [
      `\n        <div class="source-pill-card">\n          <span class="source-pill-icon">📖</span>\n`,
      `          <div>\n            <strong>${e(meta.title || 'Fuente documental')}</strong>\n`,
      `            <small>${e(normalizeAuthorsDisplay(meta.authors).join(', ') || 'Biblioteca Arkhé')}`,
      `${meta.year ? ` · ${e(meta.year)}` : ''}</small>\n          </div>\n        </div>\n`
    ].join('')).join(''),
    `\n      </div>\n    </section>\n  </article>`
  ].join('');

  return headerHtml + introHtml + sectionsHtml + listeningsHtml + assignmentsHtml + sourcesHtml;
}

export async function printStudentDocument(run) {
  const targetRun = run || store.currentStudentRun || store.currentRun;
  const fulfillment = targetRun?.result?.fulfillment || [];
  const unmet = fulfillment.filter(f => f.estado === 'pendiente_profesor' || f.estado === 'sin_fuentes');

  if (unmet.length > 0) {
    const listStr = unmet.map(u => `• ${u.requirement_id}: ${u.falta || 'Pendiente'}`).join('\n');
    const confirmed = window.confirm(
      'Esta propuesta no cumple todos los requisitos del profesor:\n\n' +
      listStr + '\n\n' +
      'El material del alumnado omite las secciones no resueltas.\n' +
      '¿Deseas imprimir de todos modos?'
    );
    if (!confirmed) return;
  }

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

  const clone = handout.cloneNode(true);
  clone.querySelectorAll('.egypt-sheet-tabs').forEach(el => el.remove());
  clone.querySelectorAll('.egypt-sheet').forEach(el => {
    el.style.display = 'block';
  });
  clone.querySelectorAll('.button, button, [data-action], .score-loading').forEach(el => el.remove());

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
  store.currentStudentRun = run;
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
  printStudentDocument(store.currentStudentRun || store.currentRun);
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
