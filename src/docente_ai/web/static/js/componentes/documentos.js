import { api, request, token } from '../api.js';
import { store, subjectName } from '../state.js';
import { toast, e, subjectStyle, formatMarkdown, icon, modal } from '../ui.js';
import {
  POLYPHONY_LISTENINGS,
  getRunListenings,
  is15thCenturyPolyphony,
  isAncientEgypt,
  renderEgyptListeningsHTML,
  renderListeningCardItem,
} from './audiciones.js';
import { renderEgyptInfographic } from '../infografias/egipto.js';
import { renderStudentInfographic } from '../infografias/musica.js';
// Módulo local: responsabilidad separada sin alterar el contenido.

export function resultHTML(run) {
  const isPedagogy = !!run.request.pedagogy;
  const review = run.review;
  const plan = run.result?.plan;
  const context = run.request.pedagogy;
  const claims = run.result?.claims || [];
  const visuals = run.result?.visualizations || [];
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : getRunListenings(run);
  const hasGraphic = isPolyphony || isEgypt || visuals.length > 0;
  const hasListenings = !!(listenings?.length || isEgypt);
  const reviewBadge = review ? [
      `<span class="badge ${review.action === 'approved' ? 'approved' : 'rejected'}">`,
      `${review.action === 'approved' ? 'Aprobada' : 'Rechazada'}</span>`
    ].join('') :
    (run.status === 'draft' && isPedagogy ? `<span class="badge pending">Por revisar</span>` : '');
  const studentControl = isPedagogy && run.status === 'draft' && run.result?.plan ? [
    `<button class="button small primary student-button" data-student-run="${e(run.id)}">`,
    `${icon('document')}Material para el alumnado</button>`
  ].join('') : '';
  const sourceControl = isPedagogy && run.evidence?.length ? [
    `<button class="button small ghost" data-sources-run="${e(run.id)}">${icon('document')}`,
    `Anexo documental</button>`
  ].join('') : '';
  const controls = [
    `<div class="result-action-group">${studentControl}${sourceControl}`,
    [
      `</div><div class="result-action-group"><button class="button small" data-download="${e(run.id)}">`
    ].join(''),
    [
      `${icon('download')}Guardar Markdown</button><button class="button small ghost" data-copy-markdown="`
    ].join(''),
    [
      `${e(run.id)}" title="Copiar texto en Markdown al portapapeles">${icon('document')}Copiar</button>`
    ].join(''),
    [
      `${
        isPedagogy ? [
          `<button class="button small ghost" data-expand-proposal="${e(run.id)}">${icon('spark')}`,
          `Ampliar</button>`
        ].join('') : ''
      }`
    ].join(''),
    `<button class="icon-button danger" data-delete-run="${e(run.id)}`,
    `" aria-label="Eliminar propuesta" title="Eliminar">${icon('trash')}</button></div>`
  ].join('');
  const totalMinutes = plan ? plan.activities.reduce((sum, item) => sum + Number(item.minutes || 0), 0) : (
    context?.duration_minutes || 0);
  const groupLabel = context?.group?.name || '';
  const levelLabel = context?.group?.level || '';
  const groupAndLevel = groupLabel && levelLabel && groupLabel.includes(levelLabel) ? groupLabel : [
    groupLabel, levelLabel
  ].filter(Boolean).join(' · ');

  const titleText = run.title || run.request.question || (isPedagogy ? 'Propuesta pedagógica' :
    'Consulta documental');
  const hasLongQuestion = run.title && run.title.trim() !== (run.request.question || '').trim();

  let content = [
    `<section class="panel result result-document"><header class="result-cover"><div `,
    [
      `class="result-cover-copy"><div class="result-kicker"><span class="subject-badge subject-tag" style="`
    ].join(''),
    `${e(subjectStyle(run.subject))}">`,
    [
      `${
        e(subjectName(run.subject) || (isPedagogy ? 'Propuesta docente' : 'Documentación'))
      }</span>`
    ].join(''),
    [
      `${reviewBadge}${
        groupAndLevel ? `<span class="result-meta-pill">${e(groupAndLevel)}</span>` : ''
      }`
    ].join(''),
    `${
      totalMinutes ? `<span class="result-meta-pill">${e(totalMinutes)} min</span>` : ''
    }`,
    [
      `${
        context?.session?.date ? `<span class="result-meta-pill">${e(context.session.date)}</span>` : ''
      }`
    ].join(''),
    `</div><h2 class="result-title">${e(titleText)}</h2>`,
    `${
      hasLongQuestion ? `<p class="result-subtitle">${e(run.request.question)}</p>` : ''
    }`,
    `</div><div class="result-actions">${controls}</div></header>`
  ].join('');

  if (['failed', 'cancelled', 'running'].includes(run.status)) return content + [
    `<div class="notice error">`,
    [
      `${
        e(run.error || 'Esta operación no ha terminado. Puedes volver a consultar su estado desde el historial.')
      }`
    ].join(''),
    `</div></section>`
  ].join('');
  if (run.status === 'abstained') {
    const sources = [...new Map((run.evidence || []).map(item => [item.document_id, item])).values()];
    const abstentionReason = run.result?.observations || run.result?.reason || '';
    return content + [
      `<div class="notice warning"><strong>Consulta completada · Sin respaldo `,
      `documental suficiente</strong><p>`,
      [
        `${
          abstentionReason ? e(abstentionReason) : (sources.length ?
            'Los fragmentos recuperados no aportan información suficiente para responder a ' +
              'esta pregunta con citas. Tener una fuente preparada no significa que cubra este ' +
              'tema.' :
            'No se recuperaron fragmentos utilizables de las fuentes seleccionadas.')
        }`
      ].join(''),
      `</p></div>`,
      [
        `${
          sources.length ? [
            `<details class="abstention-sources"><summary>Documentos recuperados para esta consulta (`,
            `${e(sources.length)})</summary><ul>`,
            [
              `${
          sources.map(item => `<li>${e(item.metadata?.title||item.citation)}</li>`).join('')
          }`
            ].join(''),
            `</ul></details>`
          ].join('') : ''
        }`
      ].join(''),
      [
        `${
          (run.warnings || []).map(w => `<div class="notice warning">${e(w)}</div>`).join('')
        }`
      ].join(''),
      [
        `<div class="review-actions"><button class="button primary" data-action="add-source">${icon('plus')}`
      ].join(''),
      `Añadir documentación</button><a class="button ghost" href="#biblioteca">Revisar `,
      `biblioteca</a></div></section>`
    ].join('');
  }
  for (const warning of run.warnings || []) content += `<div class="notice warning">${e(warning)}</div>`;
  if (review?.notes) content += [
    `<div class="notice"><strong>Notas del profesor:</strong> ${e(review.notes)}</div>`
  ].join('');

  if (plan) {
    let elapsed = 0;
    content += [
      `\n    <div class="proposal-outline" aria-label="Mapa de la propuesta">\n      `,
      `<span><strong>01</strong> Objetivos</span>\n      <span><strong>02</strong> `,
      `Secuencia de aula</span>\n      <span><strong>03</strong> Organización</span>\n  `,
      `    <span><strong>04</strong> Guía teórica</span>\n      `,
      `${hasGraphic ? '<span><strong>05</strong> Esquema gráfico</span>' : ''}\n      `,
      `${hasListenings ? '<span><strong>06</strong> Audiciones</span>' : ''}\n      `,
      [
        `${
          teacherWorkedExample(run) ? [
            `<span><strong>${hasListenings ? '07' : hasGraphic ? '06' : '05'}</strong> Ejemplo resuelto</span>`
          ].join('') : ''
        }`
      ].join(''),
      `\n    </div>`
    ].join('');

    if (context.teacher_criteria) {
      content += [
        `\n      <div class="teacher-criteria-card">\n        <span `,
        `class="criteria-badge">TUS INDICACIONES</span>\n        <p>${e(context.teacher_criteria)}`,
        `</p>\n      </div>`
      ].join('');
    }

    content += [
      `\n    <div class="pedagogy-block">\n      <div class="block-header">\n        `,
      `<span class="block-num">01</span>\n        <div>\n          <h3>Objetivos de `,
      `aprendizaje</h3>\n          <p class="block-desc">Lo que debería quedar claro al `,
      [
        `terminar la sesión.</p>\n        </div>\n      </div>\n      <div class="objectives-list">\n        `
      ].join(''),
      [
        `${
          plan.objectives.map((o, idx) => [
            `\n                  <div class="objective-item">\n                    <span class="obj-index">`,
            `${e(idx + 1)}</span>\n                    <p>${e(o)}</p>\n                  </div>\n                `
          ].join('')).join('')
        }`
      ].join(''),
      `\n      </div>\n    </div>\n\n    <div class="pedagogy-block">\n      <div `,
      `class="block-header">\n        <span class="block-num">02</span>\n        <div>`,
      `\n          <h3>Secuencia de aula</h3>\n          <p class="block-desc">Ritmo de `,
      `trabajo, dinámica y propósito de cada tramo.</p>\n        </div>\n      </div>\n `,
      `     <div class="timeline-stepper">\n        `,
      [
        `${
          plan.activities.map((a, idx) => {
            const start = elapsed;
            elapsed += a.minutes;
            const textToScan = (a.title + ' ' + a.instructions).toLowerCase();
            const isGroup = /grupo|pareja|equipo|colectiv|debate|coral|conjunto/i.test(textToScan);
            const isIndiv = /individual|personal|autónom|cada alumno/i.test(textToScan);
            const dynamicBadge = isGroup ? '<span class="step-pill-group">Práctica en Grupo / Parejas</span>' :
              isIndiv ? '<span class="step-pill-indiv">Ejercicio Individual</span>' :
              '<span class="step-pill-class">Práctica Colectiva</span>';
            return [
              `\n          <div class="timeline-step">\n            <div class="step-timing">\n `,
              `             <span class="timing-range">${start}–${elapsed}`,
              ` min</span>\n              <span class="timing-dur">${e(a.minutes)}`,
              ` min</span>\n            </div>\n            <div class="step-card">\n           `,
              `   <div class="step-card-header">\n                <div class="step-title-row">`,
              `\n                  <h4>${e(a.title)}</h4>\n                  ${dynamicBadge}`,
              [
                `\n                </div>\n                <span class="step-claims-badge">Fundamento: Contenidos `
              ].join(''),
              `${e(a.claim_ids.map(c => '#' + c).join(', '))}`,
              [
                `</span>\n              </div>\n              <p class="step-instructions">${e(a.instructions)}`
              ].join(''),
              `</p>\n            </div>\n          </div>`
            ].join('');
          }).join('')
        }`
      ].join(''),
      `\n      </div>\n    </div>\n\n    <div class="pedagogy-block">\n      <div `,
      `class="block-header">\n        <span class="block-num">03</span>\n        <div>`,
      `\n          <h3>Organización</h3>\n          <p class="block-desc">Recursos, `,
      `dificultad prevista y ajustes metodológicos.</p>\n        </div>\n      </div>\n `,
      `     <div class="pedagogy-details-grid">\n        <div class="detail-card">\n    `,
      [
        `      <h4>Recursos a preparar</h4>\n          <ul class="clean-bullet-list">\n            `
      ].join(''),
      `${plan.resources.map(r => `<li>${e(r)}</li>`).join('')}`,
      `\n          </ul>\n        </div>\n        <div class="detail-card">\n          `,
      `<h4>Nivel y dificultad</h4>\n          <p>${e(plan.difficulty)}`,
      `</p>\n        </div>\n        <div class="detail-card wide">\n          <h4>`,
      `Observaciones didácticas de IA</h4>\n          <p>${e(plan.observations)}`,
      `</p>\n        </div>\n      </div>\n    </div>`
    ].join('');
  }

  content += [
    [
      `\n  <div class="pedagogy-block">\n    <div class="block-header">\n      <span class="block-num">`
    ].join(''),
    `${plan ? '04' : '01'}</span>\n      <div>\n        <h3>`,
    `${plan ? 'Guía teórica para impartir la sesión' : 'Respuesta y Análisis'}`,
    `</h3>\n        <p class="block-desc">Contenido desarrollado para recordar los `,
    `conceptos clave sin salir de la app.</p>\n      </div>\n    </div>\n    <div `,
    `class="academic-article">`
  ].join('');

  for (const [index, claim] of claims.entries()) {
    const isInf = claim.kind === 'inference';
    const tag = plan ? [
      `CONTENIDO ${index + 1} · ${(isInf ? 'ANÁLISIS E INFERENCIA' : 'SÍNTESIS DOCUMENTAL')}`
    ].join('') : (isInf ? 'ANÁLISIS E INFERENCIA' : 'SÍNTESIS');
    content += [
      `\n    <div class="academic-section">\n      <div class="section-tag-bar">\n      `,
      `  <span class="academic-tag ${isInf ? 'tag-inf' : 'tag-syn'}">${e(tag)}`,
      `</span>\n      </div>\n      <div class="claim-body">${formatMarkdown(claim.text)}</div>\n    </div>`
    ].join('');
  }
  content += `</div></div>`;

  if (hasGraphic) {
    content += [
      `\n    <div class="pedagogy-block proposal-infographic-block">\n      <div `,
      `class="block-header">\n        <span class="block-num">05</span>\n        <div>`,
      [
        `\n          <h3>Esquema gráfico y modelos analíticos</h3>\n          <p class="block-desc">`
      ].join(''),
      [
        `${
          isEgypt ? 'Láminas didácticas de contexto, funciones sociales, organología y fuentes del Antiguo Egipto.' :
            isPolyphony ?
            'Modelos de misa (cantus firmus, paráfrasis, parodia) y recursos de unificación cíclica del siglo XV.' :
            'Modelos y esquemas estructurales para el aula.'
        }`
      ].join(''),
      [
        `</p>\n        </div>\n      </div>\n      <div class="proposal-infographic-wrap">\n        `
      ].join(''),
      [
        `${
          isEgypt ? renderEgyptInfographic(run) : (isPolyphony ? renderStudentInfographic(run) : (
            visuals.map(v => visualHTML(run, v)).join('')
          ))
        }`
      ].join(''),
      `\n      </div>\n    </div>`
    ].join('');
  }

  if (hasListenings) {
    content += [
      `\n    <div class="pedagogy-block proposal-listenings-block">\n      <div `,
      `class="block-header">\n        <span class="block-num">06</span>\n        <div>`,
      `\n          <h3>Repertorio de audiciones recomendadas con enlaces y `,
      `grabaciones</h3>\n          <p class="block-desc">`,
      [
        `${
          isPolyphony ?
            'Obras maestras con grabaciones de referencia, enlaces directos a YouTube y comentarios docentes.' :
            'Repertorio de audición activa y fuentes sonoras para la sesión.'
        }`
      ].join(''),
      `</p>\n        </div>\n      </div>\n      <div class="listening-grid `,
      `proposal-listening-grid">\n        `,
      [
        `${
          isPolyphony ? POLYPHONY_LISTENINGS.map(l => renderListeningCardItem(l, true)).join('') : isEgypt ?
            renderEgyptListeningsHTML(true) : listenings.map(l => renderListeningCardItem(l, true)).join('')
        }`
      ].join(''),
      `\n      </div>\n    </div>`
    ].join('');
  }

  const workedExample = teacherWorkedExample(run);
  if (plan && workedExample) {
    const num = hasListenings ? '07' : (hasGraphic ? '06' : '05');
    const links = (workedExample.claim_ids || []).map(id => `#${id}`).join(', ');
    content += [
      `<div class="pedagogy-block worked-example-block">\n      <div `,
      `class="block-header"><span class="block-num">${num}`,
      `</span><div><h3>Ejemplo resuelto completo</h3><p class="block-desc">Modelo listo `,
      `para utilizar en la explicación y proyectar en el aula.</p></div></div>\n      `,
      `<div class="worked-example"><div class="worked-example-head"><div><span class="eyebrow">`,
      `${e(workedExample.language||'ejemplo')}</span><h4>${e(workedExample.title)}`,
      [
        `</h4></div><button class="button small ghost" data-copy-code="${e(run.id)}">${icon('copy')}`
      ].join(''),
      `Copiar código</button></div><pre><code>${e(workedExample.code)}`,
      `</code></pre><div class="worked-example-notes"><strong>Cómo leer el ejemplo</strong><ol>`,
      `${(workedExample.explanation||[]).map(item=>`<li>${e(item)}</li>`).join('')}</ol>`,
      `${links?`<p>Base documental: contenidos ${e(links)}.</p>`:''}</div></div>\n    </div>`
    ].join('');
  }

  if (!hasGraphic) {
    for (const visual of visuals) content += visualHTML(run, visual);
  }
  if (run.status === 'draft' && isPedagogy && !review) {
    content += [
      [
        `<div class="review-actions"><button class="button primary" data-review-approve="${e(run.id)}">`
      ].join(''),
      [
        `${icon('check')}Aprobar propuesta</button><button class="button ghost" data-review-reject="`
      ].join(''),
      `${e(run.id)}">${icon('close')}Rechazar</button></div>`
    ].join('');
  }
  if (isPedagogy && review?.action === 'approved') {
    content += [
      [
        `<div class="review-actions"><button class="button" data-record-run="${e(run.id)}">${icon('record')}`
      ].join(''),
      `Registrar clase impartida</button></div>`
    ].join('');
  }
  return content + '</section>';
}

export function teacherWorkedExample(run) {
  const supplied = run.result?.teacher_guide?.worked_example;
  if (supplied) return supplied;
  const corpus = [run.request?.question || '', ...(run.result?.claims || []).map(item => item.text || ''), ...
    (run.result?.visualizations || []).flatMap(item => (item.items || []).flatMap(part => [part.label || '',
      part.detail || ''
    ]))
  ].join(' ');
  const labels = new Set((run.result?.visualizations || []).flatMap(item => item.items || []).map(item => item
    .label));
  if (!/lilypond/i.test(corpus) || !labels.has('\\score')) return null;
  return {
    title: 'Archivo LilyPond completo y compilable',
    language: 'lilypond',
    claim_ids: [3, 4, 5].filter(id => id <= (run.result?.claims || []).length),
    code: [
      `\\version "2.23.82"\n\n\\header {\n  title = "Mi primera partitura"\n  composer `,
      `= "Nombre del alumno/a"\n}\n\n% VARIABLE MUSICAL: se declara sin barra `,
      `invertida.\n% Guarda este fragmento para poder reutilizarlo después.\nmelody = `,
      `\\relative {\n  c'4 a b c\n}\n\n\\score {\n  % LLAMADA A LA VARIABLE: \\melody `,
      `inserta aquí su contenido.\n  \\melody\n  \\layout { }\n  \\midi { }\n}`
    ].join(''),
    explanation: ['\\version declara la versión del lenguaje usada por el archivo.',
      '\\header reúne los metadatos visibles, como título y compositor.',
      'melody = ... declara una variable musical: se escribe sin barra invertida y conserva el bloque de notas.',
      '\\melody llama a la variable dentro de \\score: la barra invertida indica que debe insertarse su contenido.',
      '\\relative calcula cada altura con relación a la anterior y reduce la escritura de octavas.',
      '\\layout produce la partitura gráfica y \\midi genera la reproducción MIDI.'
    ]
  };
}

export function bibliographyHTML(run) {
  const allCitations = [];
  const seen = new Set();
  for (const claim of (run.result?.claims || [])) {
    for (const c of (claim.evidence || [])) {
      const key = `${c.source_id}:::${c.quote}`;
      if (!seen.has(key)) {
        seen.add(key);
        allCitations.push(c);
      }
    }
  }
  for (const vis of (run.result?.visualizations || [])) {
    for (const c of (vis.evidence || [])) {
      const key = `${c.source_id}:::${c.quote}`;
      if (!seen.has(key)) {
        seen.add(key);
        allCitations.push(c);
      }
    }
  }
  if (!allCitations.length) return '';

  let html = [
    `\n  <section class="sources-bibliography">\n    <div class="bib-head">\n      `,
    `<span class="eyebrow">FUENTES Y PASAJES DE REFERENCIA</span>\n      <h3>Fuentes `,
    `y citas contrastadas</h3>\n      <p class="muted-small">Pasajes textuales `,
    `extraídos de tu biblioteca que fundamentan este análisis:</p>\n    </div>\n    `,
    `<div class="bibliography-grid">`
  ].join('');
  for (const citation of allCitations) {
    const source = run.evidence.find(s => s.source_id === citation.source_id);
    if (!source) continue;
    const m = source.metadata,
      l = source.locator;
    const location = locatorLabel(l);
    html += [
      `\n    <div class="bibliography-card">\n      <div class="bib-header">\n        `,
      [
        `<span class="bib-title">${e(m.title)}</span>\n        <span class="bib-loc">${e(location)}`
      ].join(''),
      `</span>\n      </div>\n      <blockquote class="bib-quote">«${e(citation.quote)}`,
      `»</blockquote>\n      <div class="bib-footer">\n        <span>`,
      `${e(m.authors?.join(', ') || 'Sin autor')}${m.year ? ' · ' + e(m.year) : ''} (`,
      `${source.category === 'profesor' ? 'Material propio' : 'Fuente documental'}`,
      [
        `)</span>\n        <button class="button ghost small" data-document="${e(source.document_id)}`
      ].join(''),
      `">Ver fuente ${icon('arrow')}</button>\n      </div>\n    </div>`
    ].join('');
  }
  html += `</div></section>`;
  return html;
}

export function sourcesModal(run) {
  const appendix = bibliographyHTML(run);
  modal('Anexo documental', [
    `${
      appendix || '<p>No hay citas documentales disponibles para esta propuesta.</p>'
    }`,
    `<div class="dialog-actions"><button class="button" data-download-sources="${e(run.id)}">`,
    `${icon('download')}Descargar anexo</button><button class="button primary" type="button" `,
    `data-action="close-dialog">Volver a la propuesta</button></div>`
  ].join(''));
}

export function locatorLabel(locator) {
  let label;
  if (locator.kind === 'pdf_page') label = `Página ${locator.pdf_page_index} del PDF`;
  else if (locator.kind === 'docx_paragraph') label = `Párrafo ${locator.paragraph_index} del DOCX`;
  else if (locator.kind === 'docx_table') label = `Tabla ${locator.table_index} del DOCX`;
  else label = `Líneas ${locator.line_start}–${locator.line_end}`;
  if (locator.section) label += ' · ' + locator.section;
  if (locator.ocr_document || locator.text_origin === 'texto OCR') label +=
    ' · Texto OCR: posible error de reconocimiento';
  return label;
}

export function evidenceHTML(run, citations) {
  let content = '';
  for (const citation of citations || []) {
    const source = run.evidence.find(s => s.source_id === citation.source_id);
    if (!source) continue;
    const m = source.metadata,
      l = source.locator;
    const location = locatorLabel(l);
    content += [
      `<details class="evidence"><summary>`,
      `${source.category==='profesor'?'Material propio':'Fuente documental'} · ${e(m.title)} · `,
      `${e(location)}</summary><blockquote>${e(citation.quote)}</blockquote><p>`,
      `${e(m.authors?.join(', ') || 'Sin autor')}${m.year?' · '+e(m.year):''}`,
      [
        `</p><button class="button ghost small" data-document="${e(source.document_id)}">Ver fuente `
      ].join(''),
      `${icon('arrow')}</button></details>`
    ].join('');
  }
  return content;
}

export function visualHTML(run, visual) {
  const type = ['sequence', 'relationship', 'table'].includes(visual.type) ? visual.type : 'relationship';
  const items = (visual.items || []).map(item => [
    `<div class="visual-node"><strong>${e(item.label)}</strong><span>${e(item.detail)}</span></div>`
  ].join('')).join('');
  return [
    `<section class="source-visual source-visual-${e(type)}" aria-label="${e(visual.title)}`,
    `"><span class="eyebrow">ESQUEMA DOCUMENTADO</span><h3>${e(visual.title)}`,
    [
      `</h3><div class="visual-canvas">${items}</div><p class="visual-caption">${e(visual.caption)}`
    ].join(''),
    `</p></section>`
  ].join('');
}

// Acciones y formularios de este módulo; delegación central en main.js.
async function accionOpenSourcesRun({target}) {
  const run = store.currentRun && store.currentRun.id === target.dataset.sourcesRun ? store
    .currentRun : await api('/runs/' + encodeURIComponent(target.dataset.sourcesRun));
  sourcesModal(run);
}

async function accionOpenCopyCode({target}) {
  const example = store.currentRun && store.currentRun.id === target.dataset.copyCode ?
    teacherWorkedExample(store.currentRun) : null;
  if (!example) throw new Error('No se encontró el ejemplo resuelto.');
  await navigator.clipboard.writeText(example.code);
  toast('Código copiado. Ya puedes pegarlo en tu editor.');
}

async function accionOpenDownloadSources({target}) {
  const identifier = target.dataset.downloadSources;
  const response = await request('/api/runs/' + encodeURIComponent(identifier) + '?sources=1', {
    headers: {
      'X-Docente-Token': token
    }
  });
  if (!response.ok) throw new Error('No se pudo descargar el anexo documental.');
  const url = URL.createObjectURL(await response.blob()),
    link = document.createElement('a');
  link.href = url;
  link.download = 'anexo-fuentes-' + identifier + '.md';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast('Anexo de fuentes y citas descargado.');
}

async function accionOpenCopyMarkdown({target}) {
  const identifier = target.dataset.copyMarkdown;
  target.disabled = true;
  try {
    const response = await request('/api/runs/' + encodeURIComponent(identifier) + '?download=1', {
      headers: {
        'X-Docente-Token': token
      }
    });
    if (!response.ok) throw new Error('No se pudo obtener el texto Markdown.');
    const mdText = await response.text();
    await navigator.clipboard.writeText(mdText);
    toast('¡Markdown copiado al portapapeles!');
  } catch (err) {
    toast('Error al copiar: ' + (err.message || err), true);
  } finally {
    target.disabled = false;
  }
}

async function accionOpenDownload({target}) {
  const identifier = target.dataset.download || target.dataset.original || target.dataset
    .ocrDocument;
  const isOrig = !!(target.dataset.original || target.dataset.ocrDocument);
  target.disabled = true;
  try {
    const response = await request('/api/' + (isOrig ? 'documents/' : 'runs/') + encodeURIComponent(
      identifier) + '?download=1' + (target.dataset.ocrDocument ? '&derived=1' : ''), {
      headers: {
        'X-Docente-Token': token
      }
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.error || 'No se pudo exportar el archivo.');
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const filename = isOrig ?
      (decodeURIComponent(response.headers.get('Content-Disposition')?.match(
          /filename\*=utf-8''([^;]+)/i)?.[1] || '') || response.headers.get('Content-Disposition')
        ?.match(/filename="([^"]+)"/)?.[1] || 'original') :
      'arkhe-' + identifier + '.md';
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    toast(isOrig ? 'Descargando documento…' : 'Descargando archivo Markdown (.md)…');
  } catch (err) {
    toast(err.message || 'Error al exportar.', true);
  } finally {
    target.disabled = false;
  }
}

export const actions = {
  'open-sources-run': accionOpenSourcesRun,
  'copy-code': accionOpenCopyCode,
  'download-sources': accionOpenDownloadSources,
  'copy-markdown': accionOpenCopyMarkdown,
  'download': accionOpenDownload,
};

export const clickBindings = [
  {priority: 4, matches: target => target.dataset.sourcesRun, action: 'open-sources-run'},
  {priority: 6, matches: target => target.dataset.copyCode, action: 'copy-code'},
  {priority: 8, matches: target => target.dataset.downloadSources, action: 'download-sources'},
  {priority: 9, matches: target => target.dataset.copyMarkdown, action: 'copy-markdown'},
  {priority: 10, matches: target => target.dataset.download || target.dataset.original ||
    target.dataset.ocrDocument, action: 'download'},
];
