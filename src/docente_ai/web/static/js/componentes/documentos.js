import { api, request, token } from '../api.js';
import { store, subjectName } from '../state.js';
import { toast, e, subjectStyle, formatMarkdown, icon, modal, normalizeAuthorsDisplay } from '../ui.js';
import {
  POLYPHONY_LISTENINGS,
  getRunListenings,
  is15thCenturyPolyphony,
  isAncientEgypt,
  normalizeTopic,
  renderEgyptListeningsHTML,
  renderListeningCardItem,
} from './audiciones.js';
import { renderEgyptInfographic } from '../infografias/egipto.js';
import { renderStudentInfographic } from '../infografias/musica.js';
import { renderMusicRequestsBlock } from './partituras.js';
// Módulo local: responsabilidad separada sin alterar el contenido.

export function formatPedagogyResource(r) {
  if (!r) return '';
  if (typeof r === 'string') return e(r);
  const texto = String(r.recurso || r.texto || '').trim();
  const tipo = String(r.tipo || '').trim();
  const pendiente = Boolean(r.pendiente);
  const partes = [];
  if (pendiente) partes.push('pendiente');
  if (tipo) partes.push(tipo);
  const meta = partes.join(', ');
  if (texto && meta) return `${e(texto)} — ${e(meta)}`;
  return e(texto || meta);
}

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

  const rawQuestion = (run.original_topic || run.request?.original_topic || run.request?.question || '').trim();
  const normalizedQuestion = normalizeTopic(rawQuestion);
  const rawTitle = (run.display_title || run.title || run.request?.display_title || '').trim();
  const titleText = rawTitle || normalizedQuestion || (isPedagogy ? 'Propuesta pedagógica' :
    'Consulta documental');
  const subtitleText = (rawQuestion && rawQuestion.toLowerCase() !== titleText.toLowerCase()) ?
    `Tema original: ${rawQuestion}` : '';

  const currentSubj = run.subject || run.request?.subject || '';
  const subjDisplay = subjectName(currentSubj) || (isPedagogy ? 'Sin materia' : 'Documentación');
  const subjectBadgeHTML = isPedagogy ? [
    `<span class="subject-badge subject-tag editable-subject" data-action="edit-proposal-subject" `,
    `data-run="${e(run.id)}" title="Clic para asignar o cambiar la materia" `,
    `style="${e(subjectStyle(currentSubj))}; cursor:pointer; display:inline-flex; align-items:center; gap:0.35rem;">`,
    `${e(subjDisplay)} `,
    `<button class="button small ghost icon-button inline-edit-btn" data-action="edit-proposal-subject" `,
    `data-run="${e(run.id)}" aria-label="Cambiar materia" title="Cambiar materia">${icon('edit')}</button></span>`
  ].join('') : [
    `<span class="subject-badge subject-tag" style="${e(subjectStyle(run.subject))}">`,
    `${e(subjectName(run.subject) || 'Documentación')}</span>`
  ].join('');

  let content = [
    `<section class="panel result result-document"><header class="result-cover"><div `,
    `class="result-cover-copy"><div class="result-kicker">`,
    `${subjectBadgeHTML}`,
    `${reviewBadge}${
      groupAndLevel ? `<span class="result-meta-pill">${e(groupAndLevel)}</span>` : ''
    }`,
    `${
      totalMinutes ? `<span class="result-meta-pill">${e(totalMinutes)} min</span>` : ''
    }`,
    `${
      context?.session?.date ? `<span class="result-meta-pill">${e(context.session.date)}</span>` : ''
    }`,
    `</div><div class="result-title-container"><h2 class="result-title editable-title" ` +
    `data-action="edit-proposal-title" data-run="${e(run.id)}" title="Clic para editar el título" ` +
    `style="cursor:pointer; display:inline-flex; align-items:center; gap:0.5rem;">${e(titleText)} ` +
    `<button class="button small ghost icon-button inline-edit-btn" data-action="edit-proposal-title" ` +
    `data-run="${e(run.id)}" aria-label="Editar título" title="Editar título">${icon('edit')}</button></h2></div>`,
    `${
      subtitleText ? `<p class="result-subtitle">${e(subtitleText)}</p>` : ''
    }`,
    `</div><div class="result-actions">${controls}</div></header>`
  ].join('');

  if (['failed', 'cancelled', 'running'].includes(run.status)) {
    let errorMsg = run.error || '';
    if (errorMsg.includes('no tiene sesiones previstas')) {
      errorMsg = 'No tienes clases este día en el calendario.';
    } else if (/traceback|file |line \d+|sqlite|exception|syntaxerror/i.test(errorMsg)) {
      errorMsg = 'Ha ocurrido un problema al procesar la propuesta. Revisa tus fuentes o inténtalo de nuevo.';
    }
    return content + [
      `<div class="notice ${errorMsg.includes('No tienes clases') ? 'warning' : 'error'}">`,
      `${e(errorMsg || 'Esta operación no ha terminado. Puedes volver a consultar su estado desde el historial.')}`,
      `</div></section>`
    ].join('');
  }

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
  const runClaims = run.result?.claims || [];
  const hasUnbackedClaim = runClaims.some(claim => {
    const evs = claim.evidence || [];
    return !evs.some(ev => {
      const src = (run.evidence || []).find(s => s.source_id === ev.source_id);
      const orig = src?.metadata?.origin || (src?.category === 'profesor' ? 'notas_profesor' : 'bibliografia');
      return orig === 'bibliografia' || orig === 'fuente_primaria';
    });
  });
  if (hasUnbackedClaim && runClaims.length > 0) {
    content += [
      '<div class="notice warning"><strong>Aviso de fundamentación:</strong> ',
      'Algunos contenidos carecen de fuente bibliográfica en la biblioteca ',
      '(se apoyan en notas del profesor o deducción de IA).</div>'
    ].join('');
  }
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

    const requirements = context.requirements || run.request?.requirements || [];
    const coverage = run.result?.coverage || [];
    if (coverage.length || requirements.length) {
      const covMap = new Map(coverage.map(item => [item.requirement_id, item]));
      const reqMap = new Map(requirements.map(item => [item.id, item]));
      const allIds = [...new Set([...reqMap.keys(), ...covMap.keys()])];

      content += [
        `\n    <div class="pedagogy-block coverage-block">\n      <div class="block-header">\n        `,
        `<span class="block-num">🎯</span>\n        <div>\n          <h3>Cobertura de requisitos del profesor`,
        `</h3>\n          <p class="block-desc">Verificación de peticiones temáticas frente a la biblioteca.</p>\n`,
        `        </div>\n      </div>\n      <div class="table-container">\n        `,
        `<table class="coverage-table">\n          <thead>\n            <tr>\n              <th>ID</th>\n`,
        `              <th>Requisito</th>\n              <th>Tipo</th>\n              <th>Estado</th>\n`,
        `              <th>Contenidos</th>\n`,
        `              <th>Observaciones</th>\n            </tr>\n          </thead>\n`,
        `          <tbody>\n`,
        allIds.map(rid => {
          const req = reqMap.get(rid) || {};
          const cov = covMap.get(rid) || {};
          const desc = req.description || rid;
          const rtype = req.type || 'contenido';
          const st = cov.status || (req ? 'sin_fuentes' : 'cubierto');
          const badgeClass = st === 'cubierto' ? 'success' : st === 'parcial' ? 'warning' : 'danger';
          const badgeText = st === 'cubierto' ? 'Cubierto' : st === 'parcial' ? 'Parcial' : '⚠️ Sin fuentes';
          const claims = (cov.claim_ids || []).map(cid => '#' + String(cid)).join(', ') || '—';
          const note = cov.note || '—';
          return [
            `            <tr>\n              <td><strong>${e(rid)}</strong></td>\n              `,
            `<td>${e(desc)}</td>\n              <td>${e(rtype)}</td>\n              `,
            `<td><span class="status-badge ${badgeClass}">${e(badgeText)}</span></td>\n              `,
            `<td>${e(claims)}</td>\n              <td>${e(note)}</td>\n            </tr>\n`
          ].join('');
        }).join(''),
        `          </tbody>\n        </table>\n      </div>\n    </div>`
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
      `      <div class="timeline-stepper">\n        `,
      [
        `${
          plan.activities.map((a, idx) => {
            const start = elapsed;
            elapsed += a.minutes;
            let dynamicBadge = '';
            if (a.grouping === 'grupo') {
              dynamicBadge = '<span class="step-pill-group">Práctica en Grupo</span>';
            } else if (a.grouping === 'individual') {
              dynamicBadge = '<span class="step-pill-indiv">Ejercicio Individual</span>';
            } else if (a.grouping === 'colectivo') {
              dynamicBadge = '<span class="step-pill-class">Práctica Colectiva</span>';
            } else {
              const textToScan = (a.title + ' ' + (a.instructions || '') + ' ' + (a.teacher_notes || '')).toLowerCase();
              const isGroup = /grupo|pareja|equipo|colectiv|debate|coral|conjunto/i.test(textToScan);
              const isIndiv = /individual|personal|autónom|cada alumno/i.test(textToScan);
              dynamicBadge = isGroup ? '<span class="step-pill-group">Práctica en Grupo / Parejas</span>' :
                isIndiv ? '<span class="step-pill-indiv">Ejercicio Individual</span>' :
                '<span class="step-pill-class">Práctica Colectiva</span>';
            }
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
              a.teacher_notes ? [
                `              <p class="step-teacher-notes"><strong>Pautas docentes:</strong> `,
                `${e(a.teacher_notes)}</p>\n`
              ].join('') : '',
              a.instructions ? `              <p class="step-instructions">${e(a.instructions)}</p>\n` : '',
              a.student_task ? [
                `              <p class="step-student-task"><strong>Consigna del alumno:</strong> `,
                `${e(a.student_task)}</p>\n`
              ].join('') : '',
              a.deliverable ? [
                `              <p class="step-deliverable"><strong>Entregable:</strong> `,
                `${e(a.deliverable)}</p>\n`
              ].join('') : '',
              a.solution ? [
                `              <div class="step-solution"><strong>Solución / Criterios de corrección:</strong><br>`,
                `${formatMarkdown(a.solution)}</div>\n`
              ].join('') : '',
              `            </div>\n          </div>`
            ].join('');
          }).join('')
        }`
      ].join(''),
      `\n      </div>\n    </div>\n\n    <div class="pedagogy-block">\n      <div `,
      `class="block-header">\n        <span class="block-num">03</span>\n        <div>`,
      `\n          <h3>Organización y evaluación</h3>\n          <p class="block-desc">Recursos, `,
      `evaluación formativa, dificultad y observaciones.</p>\n        </div>\n      </div>\n `,
      `     <div class="pedagogy-details-grid">\n        <div class="detail-card">\n    `,
      [
        `      <h4>Recursos a preparar</h4>\n          <ul class="clean-bullet-list">\n            `
      ].join(''),
      `${plan.resources.map(r => `<li>${e(formatPedagogyResource(r))}</li>`).join('')}`,
      `\n          </ul>\n        </div>\n        <div class="detail-card">\n          `,
      `<h4>Nivel y dificultad</h4>\n          <p>${e(plan.difficulty)}`,
      `</p>\n        </div>\n`,
      plan.assessment ? [
        `        <div class="detail-card wide">\n          <h4>Evaluación de la sesión</h4>\n          <p>`,
        `${e(plan.assessment)}</p>\n        </div>\n`
      ].join('') : '',
      `        <div class="detail-card wide">\n          <h4>`,
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
    const evs = claim.evidence || [];
    let hasBib = false;
    let hasProf = false;
    for (const ev of evs) {
      const src = (run.evidence || []).find(s => s.source_id === ev.source_id);
      const orig = src?.metadata?.origin || (src?.category === 'profesor' ? 'notas_profesor' : 'bibliografia');
      if (orig === 'bibliografia' || orig === 'fuente_primaria') hasBib = true;
      else if (orig === 'notas_profesor') hasProf = true;
    }
    const label = isInf ? 'ANÁLISIS E INFERENCIA' :
      hasBib ? 'SÍNTESIS RESPALDADA POR BIBLIOGRAFÍA' :
      hasProf ? 'SÍNTESIS BASADA EN NOTAS DEL PROFESOR' :
      'CONTENIDO SIN RESPALDO BIBLIOGRÁFICO';
    const tag = plan ? `CONTENIDO ${index + 1} · ${label}` : label;
    const tagClass = isInf ? 'tag-inf' : (hasBib ? 'tag-syn' : 'tag-warn');

    let claimSourcesHTML = '';
    if (!evs.length) {
      claimSourcesHTML = [
        '<p class="claim-source-empty"><em>Sin fuente bibliográfica identificada ',
        '(deducción / notas).</em></p>'
      ].join('');
    } else {
      claimSourcesHTML = '<div class="claim-sources-list"><strong>Fuentes:</strong><ul>' + evs.map(ev => {
        const src = (run.evidence || []).find(s => s.source_id === ev.source_id);
        if (!src) return '';
        const m = src.metadata || {};
        const auth = normalizeAuthorsDisplay(m.authors).join('; ') || 'Sin autor identificado';
        const yr = m.year ? ` (${e(m.year)})` : '';
        const loc = locatorLabel(src.locator || {});
        const orig = m.origin || (src.category === 'profesor' ? 'notas_profesor' : 'bibliografia');
        const origLabel = orig === 'notas_profesor' ? ' [Notas profesor]' :
          (orig === 'fuente_primaria' ? ' [Fuente primaria]' : ' [Bibliografía]');
        return [
          `<li><strong>${e(auth)}</strong>${yr}. `,
          `<em>${e(m.title||'')}</em>, ${e(loc)}${e(origLabel)} — «${e(ev.quote||'')}»</li>`
        ].join('');
      }).join('') + '</ul></div>';
    }

    content += [
      `\n    <div class="academic-section">\n      <div class="section-tag-bar">\n      `,
      `  <span class="academic-tag ${tagClass}">${e(tag)}`,
      `</span>\n      </div>\n      <div class="claim-body">${formatMarkdown(claim.text)}</div>\n      `,
      `${claimSourcesHTML}\n    </div>`
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
      `</p>\n        </div>\n      </div>\n`,
      run?.ficha?.ejemplos_musicales?.length ? (
        '      <div class="ficha-ejemplos-actions" style="margin-bottom:12px">\n' +
        '        <button type="button" class="button small secondary descargar-ejemplos-ficha-btn" ' +
        `data-run-id="${e(run.id)}">` +
        '📥 Descargar ejemplos de esta ficha (JRP · CC BY-NC 4.0)</button>\n' +
        '      </div>\n'
      ) : '',
      `      <div class="proposal-infographic-wrap">\n        `,
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
  if (isPedagogy && (run.result?.music_requests?.length || run.result?.resolved_music_requests?.length)) {
    content += renderMusicRequestsBlock(run);
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
      `${e(normalizeAuthorsDisplay(m.authors).join(', ') || 'Sin autor')}${m.year ? ' · ' + e(m.year) : ''} (`,
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
  const headerFilename = response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1];
  link.download = headerFilename || ('anexo-fuentes-' + identifier + '.md');
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
    const headerFilename = response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1];
    const filename = isOrig ?
      (decodeURIComponent(response.headers.get('Content-Disposition')?.match(
          /filename\*=utf-8''([^;]+)/i)?.[1] || '') || headerFilename || 'original') :
      (headerFilename || ('arkhe-' + identifier + '.md'));
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

async function accionEditProposalTitle({target}) {
  const el = target.closest('[data-run]');
  const runId = el?.dataset.run || store.currentRun?.id;
  const currentTitle = (store.currentRun?.display_title || store.currentRun?.title || '').trim();
  modal('Editar título de la propuesta', [
    '<form data-form="edit-proposal-title-form" class="stack">',
    `<input type="hidden" name="run_id" value="${e(runId)}">`,
    '<div class="field">',
    '<label class="label" for="new-proposal-title">Título de la propuesta</label>',
    `<input class="input" id="new-proposal-title" name="title" maxlength="500" required ` +
    `value="${e(currentTitle)}" autofocus>`,
    '</div>',
    '<p class="field-hint">Este título se usará en la lista de propuestas, la guía docente, ' +
    'el material del alumnado y las descargas.</p>',
    '<div class="dialog-actions">',
    '<button class="button ghost" type="button" data-action="close-dialog">Cancelar</button>',
    '<button class="button primary" type="submit">Guardar título</button>',
    '</div>',
    '</form>'
  ].join(''));
}

async function formEditProposalTitle({form, data}) {
  const runId = data.run_id;
  const title = (data.title || '').trim();
  if (!title) throw new Error('El título no puede estar vacío.');
  const updated = await api('/runs/' + encodeURIComponent(runId) + '/title', {title});
  if (store.currentRun && store.currentRun.id === runId) {
    Object.assign(store.currentRun, updated);
  }
  if (store.state?.runs) {
    const found = store.state.runs.find(r => r.id === runId);
    if (found) {
      found.display_title = title;
      found.title = title;
    }
  }
  document.getElementById('dialog')?.close();
  document.dispatchEvent(new CustomEvent('enjambre:render'));
  toast('Título de la propuesta actualizado.');
}

async function accionEditProposalSubject({target}) {
  const el = target.closest('[data-run]');
  const runId = el?.dataset.run || store.currentRun?.id;
  const currentSubj = store.currentRun?.subject || store.currentRun?.request?.subject || '';
  const subjects = store.state?.config?.subjects || [];
  modal('Asignar materia a la propuesta', [
    '<form data-form="edit-proposal-subject-form" class="stack">',
    `<input type="hidden" name="run_id" value="${e(runId)}">`,
    '<div class="field">',
    '<label class="label" for="new-proposal-subject">Materia</label>',
    '<select class="select input" id="new-proposal-subject" name="subject">',
    `<option value="">Sin materia</option>`,
    subjects.map(s => [
      `<option value="${e(s.id)}" ${s.id === currentSubj ? 'selected' : ''}>`,
      `${e(s.name)}</option>`
    ].join('')).join(''),
    '</select>',
    '</div>',
    '<p class="field-hint">La materia clasifica la propuesta con su color identificativo y ',
    'organiza el trabajo de clase.</p>',
    '<div class="dialog-actions">',
    '<button class="button ghost" type="button" data-action="close-dialog">Cancelar</button>',
    '<button class="button primary" type="submit">Guardar materia</button>',
    '</div>',
    '</form>'
  ].join(''));
}

async function formEditProposalSubject({form, data}) {
  const runId = data.run_id;
  const subject = (data.subject || '').trim();
  const updated = await api('/runs/' + encodeURIComponent(runId) + '/subject', {subject});
  if (store.currentRun && store.currentRun.id === runId) {
    store.currentRun.subject = subject;
    if (store.currentRun.request) store.currentRun.request.subject = subject;
    Object.assign(store.currentRun, updated);
  }
  if (store.state?.runs) {
    const found = store.state.runs.find(r => r.id === runId);
    if (found) {
      found.subject = subject;
    }
  }
  document.getElementById('dialog')?.close();
  document.dispatchEvent(new CustomEvent('enjambre:render'));
  toast('Materia de la propuesta actualizada.');
}

export const actions = {
  'open-sources-run': accionOpenSourcesRun,
  'copy-code': accionOpenCopyCode,
  'download-sources': accionOpenDownloadSources,
  'copy-markdown': accionOpenCopyMarkdown,
  'download': accionOpenDownload,
  'edit-proposal-title': accionEditProposalTitle,
  'edit-proposal-subject': accionEditProposalSubject,
};

export const forms = {
  'edit-proposal-title-form': formEditProposalTitle,
  'edit-proposal-subject-form': formEditProposalSubject,
};

export const clickBindings = [
  {
    priority: 1,
    matches: target => target.dataset.action === 'edit-proposal-title' ||
      target.closest('[data-action="edit-proposal-title"]'),
    action: 'edit-proposal-title'
  },
  {
    priority: 1,
    matches: target => target.dataset.action === 'edit-proposal-subject' ||
      target.closest('[data-action="edit-proposal-subject"]'),
    action: 'edit-proposal-subject'
  },
  {priority: 4, matches: target => target.dataset.sourcesRun, action: 'open-sources-run'},
  {priority: 6, matches: target => target.dataset.copyCode, action: 'copy-code'},
  {priority: 8, matches: target => target.dataset.downloadSources, action: 'download-sources'},
  {priority: 9, matches: target => target.dataset.copyMarkdown, action: 'copy-markdown'},
  {priority: 10, matches: target => target.dataset.download || target.dataset.original ||
    target.dataset.ocrDocument, action: 'download'},

];
