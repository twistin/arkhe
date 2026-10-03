// Módulo local: responsabilidad separada sin alterar el contenido.
import { POLYPHONY_LISTENINGS, getRunListenings, is15thCenturyPolyphony, isAncientEgypt, renderEgyptListeningsHTML, renderListeningCardItem } from './audiciones.js';
import { renderEgyptInfographic } from '../infografias/egipto.js';
import { renderStudentInfographic } from '../infografias/musica.js';
import { subjectName } from '../state.js';
import { e, formatMarkdown, icon, modal } from '../ui.js';

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
  const reviewBadge = review
    ? `<span class="badge ${review.action === 'approved' ? 'approved' : 'rejected'}">${review.action === 'approved' ? 'Aprobada' : 'Rechazada'}</span>`
    : (run.status === 'draft' && isPedagogy ? `<span class="badge pending">Por revisar</span>` : '');
  const studentControl = isPedagogy && run.status==='draft' && run.result?.plan ? `<button class="button small primary student-button" data-student-run="${e(run.id)}">${icon('document')}Material para el alumnado</button>` : '';
  const sourceControl = isPedagogy && run.evidence?.length ? `<button class="button small ghost" data-sources-run="${e(run.id)}">${icon('document')}Anexo documental</button>` : '';
  const controls = `<div class="result-action-group">${studentControl}${sourceControl}</div><div class="result-action-group"><button class="button small" data-download="${e(run.id)}">${icon('download')}Guardar Markdown</button><button class="button small ghost" data-copy-markdown="${e(run.id)}" title="Copiar texto en Markdown al portapapeles">${icon('document')}Copiar</button>${isPedagogy ? `<button class="button small ghost" data-expand-proposal="${e(run.id)}">${icon('spark')}Ampliar</button>` : ''}<button class="icon-button danger" data-delete-run="${e(run.id)}" aria-label="Eliminar propuesta" title="Eliminar">${icon('trash')}</button></div>`;
  const totalMinutes = plan ? plan.activities.reduce((sum, item) => sum + Number(item.minutes || 0), 0) : (context?.duration_minutes || 0);
  const groupLabel = context?.group?.name || '';
  const levelLabel = context?.group?.level || '';
  const groupAndLevel = groupLabel && levelLabel && groupLabel.includes(levelLabel) ? groupLabel : [groupLabel, levelLabel].filter(Boolean).join(' · ');

  const titleText = run.title || run.request.question || (isPedagogy ? 'Propuesta pedagógica' : 'Consulta documental');
  const hasLongQuestion = run.title && run.title.trim() !== (run.request.question || '').trim();

  let content = `<section class="panel result result-document"><header class="result-cover"><div class="result-cover-copy"><div class="result-kicker"><span class="subject-badge subject-tag-${e(run.subject||'none')}">${e(subjectName(run.subject) || (isPedagogy?'Propuesta docente':'Documentación'))}</span>${reviewBadge}${groupAndLevel ? `<span class="result-meta-pill">${e(groupAndLevel)}</span>` : ''}${totalMinutes ? `<span class="result-meta-pill">${totalMinutes} min</span>` : ''}${context?.session?.date ? `<span class="result-meta-pill">${e(context.session.date)}</span>` : ''}</div><h2 class="result-title">${e(titleText)}</h2>${hasLongQuestion ? `<p class="result-subtitle">${e(run.request.question)}</p>` : ''}</div><div class="result-actions">${controls}</div></header>`;

  if (['failed','cancelled','running'].includes(run.status)) return content+`<div class="notice error">${e(run.error||'Esta operación no ha terminado. Puedes volver a consultar su estado desde el historial.')}</div></section>`;
  if (run.status==='abstained') {
    const sources=[...new Map((run.evidence||[]).map(item=>[item.document_id,item])).values()];
    const abstentionReason = run.result?.observations || run.result?.reason || '';
    return content+`<div class="notice warning"><strong>Consulta completada · Sin respaldo documental suficiente</strong><p>${abstentionReason ? e(abstentionReason) : (sources.length?'Los fragmentos recuperados no aportan información suficiente para responder a esta pregunta con citas. Tener una fuente preparada no significa que cubra este tema.':'No se recuperaron fragmentos utilizables de las fuentes seleccionadas.')}</p></div>${sources.length?`<details class="abstention-sources"><summary>Documentos recuperados para esta consulta (${sources.length})</summary><ul>${sources.map(item=>`<li>${e(item.metadata?.title||item.citation)}</li>`).join('')}</ul></details>`:''}${(run.warnings||[]).map(w=>`<div class="notice warning">${e(w)}</div>`).join('')}<div class="review-actions"><button class="button primary" data-action="add-source">${icon('plus')}Añadir documentación</button><a class="button ghost" href="#biblioteca">Revisar biblioteca</a></div></section>`;
  }
  for (const warning of run.warnings||[]) content += `<div class="notice warning">${e(warning)}</div>`;
  if (review?.notes) content += `<div class="notice"><strong>Notas del profesor:</strong> ${e(review.notes)}</div>`;

  if (plan) {
    let elapsed = 0;
    content += `
    <div class="proposal-outline" aria-label="Mapa de la propuesta">
      <span><strong>01</strong> Objetivos</span>
      <span><strong>02</strong> Secuencia de aula</span>
      <span><strong>03</strong> Organización</span>
      <span><strong>04</strong> Guía teórica</span>
      ${hasGraphic ? '<span><strong>05</strong> Esquema gráfico</span>' : ''}
      ${hasListenings ? '<span><strong>06</strong> Audiciones</span>' : ''}
      ${teacherWorkedExample(run)?`<span><strong>${hasListenings ? '07' : hasGraphic ? '06' : '05'}</strong> Ejemplo resuelto</span>`:''}
    </div>`;

    if (context.teacher_criteria) {
      content += `
      <div class="teacher-criteria-card">
        <span class="criteria-badge">TUS INDICACIONES</span>
        <p>${e(context.teacher_criteria)}</p>
      </div>`;
    }

    content += `
    <div class="pedagogy-block">
      <div class="block-header">
        <span class="block-num">01</span>
        <div>
          <h3>Objetivos de aprendizaje</h3>
          <p class="block-desc">Lo que debería quedar claro al terminar la sesión.</p>
        </div>
      </div>
      <div class="objectives-list">
        ${plan.objectives.map((o, idx) => `
          <div class="objective-item">
            <span class="obj-index">${idx + 1}</span>
            <p>${e(o)}</p>
          </div>
        `).join('')}
      </div>
    </div>

    <div class="pedagogy-block">
      <div class="block-header">
        <span class="block-num">02</span>
        <div>
          <h3>Secuencia de aula</h3>
          <p class="block-desc">Ritmo de trabajo, dinámica y propósito de cada tramo.</p>
        </div>
      </div>
      <div class="timeline-stepper">
        ${plan.activities.map((a, idx) => {
          const start = elapsed;
          elapsed += a.minutes;
          const textToScan = (a.title + ' ' + a.instructions).toLowerCase();
          const isGroup = /grupo|pareja|equipo|colectiv|debate|coral|conjunto/i.test(textToScan);
          const isIndiv = /individual|personal|autónom|cada alumno/i.test(textToScan);
          const dynamicBadge = isGroup ? '<span class="step-pill-group">Práctica en Grupo / Parejas</span>' : isIndiv ? '<span class="step-pill-indiv">Ejercicio Individual</span>' : '<span class="step-pill-class">Práctica Colectiva</span>';
          return `
          <div class="timeline-step">
            <div class="step-timing">
              <span class="timing-range">${start}–${elapsed} min</span>
              <span class="timing-dur">${a.minutes} min</span>
            </div>
            <div class="step-card">
              <div class="step-card-header">
                <div class="step-title-row">
                  <h4>${e(a.title)}</h4>
                  ${dynamicBadge}
                </div>
                <span class="step-claims-badge">Fundamento: Contenidos ${a.claim_ids.map(c => '#' + c).join(', ')}</span>
              </div>
              <p class="step-instructions">${e(a.instructions)}</p>
            </div>
          </div>`;
        }).join('')}
      </div>
    </div>

    <div class="pedagogy-block">
      <div class="block-header">
        <span class="block-num">03</span>
        <div>
          <h3>Organización</h3>
          <p class="block-desc">Recursos, dificultad prevista y ajustes metodológicos.</p>
        </div>
      </div>
      <div class="pedagogy-details-grid">
        <div class="detail-card">
          <h4>Recursos a preparar</h4>
          <ul class="clean-bullet-list">
            ${plan.resources.map(r => `<li>${e(r)}</li>`).join('')}
          </ul>
        </div>
        <div class="detail-card">
          <h4>Nivel y dificultad</h4>
          <p>${e(plan.difficulty)}</p>
        </div>
        <div class="detail-card wide">
          <h4>Observaciones didácticas de IA</h4>
          <p>${e(plan.observations)}</p>
        </div>
      </div>
    </div>`;
  }

  content += `
  <div class="pedagogy-block">
    <div class="block-header">
      <span class="block-num">${plan ? '04' : '01'}</span>
      <div>
        <h3>${plan ? 'Guía teórica para impartir la sesión' : 'Respuesta y Análisis'}</h3>
        <p class="block-desc">Contenido desarrollado para recordar los conceptos clave sin salir de la app.</p>
      </div>
    </div>
    <div class="academic-article">`;

  for (const [index, claim] of claims.entries()) {
    const isInf = claim.kind === 'inference';
    const tag = plan ? `CONTENIDO ${index + 1} · ${(isInf ? 'ANÁLISIS E INFERENCIA' : 'SÍNTESIS DOCUMENTAL')}` : (isInf ? 'ANÁLISIS E INFERENCIA' : 'SÍNTESIS');
    content += `
    <div class="academic-section">
      <div class="section-tag-bar">
        <span class="academic-tag ${isInf ? 'tag-inf' : 'tag-syn'}">${tag}</span>
      </div>
      <div class="claim-body">${formatMarkdown(claim.text)}</div>
    </div>`;
  }
  content += `</div></div>`;

  if (hasGraphic) {
    content += `
    <div class="pedagogy-block proposal-infographic-block">
      <div class="block-header">
        <span class="block-num">05</span>
        <div>
          <h3>Esquema gráfico y modelos analíticos</h3>
          <p class="block-desc">${isEgypt ? 'Láminas didácticas de contexto, funciones sociales, organología y fuentes del Antiguo Egipto.' : isPolyphony ? 'Modelos de misa (cantus firmus, paráfrasis, parodia) y recursos de unificación cíclica del siglo XV.' : 'Modelos y esquemas estructurales para el aula.'}</p>
        </div>
      </div>
      <div class="proposal-infographic-wrap">
        ${isEgypt ? renderEgyptInfographic(run) : (isPolyphony ? renderStudentInfographic(run) : (
          visuals.map(v => visualHTML(run, v)).join('')
        ))}
      </div>
    </div>`;
  }

  if (hasListenings) {
    content += `
    <div class="pedagogy-block proposal-listenings-block">
      <div class="block-header">
        <span class="block-num">06</span>
        <div>
          <h3>Repertorio de audiciones recomendadas con enlaces y grabaciones</h3>
          <p class="block-desc">${isPolyphony ? 'Obras maestras con grabaciones de referencia, enlaces directos a YouTube y comentarios docentes.' : 'Repertorio de audición activa y fuentes sonoras para la sesión.'}</p>
        </div>
      </div>
      <div class="listening-grid proposal-listening-grid">
        ${isPolyphony ? POLYPHONY_LISTENINGS.map(l => renderListeningCardItem(l, true)).join('') : isEgypt ? renderEgyptListeningsHTML(true) : listenings.map(l => renderListeningCardItem(l, true)).join('')}
      </div>
    </div>`;
  }

  const workedExample=teacherWorkedExample(run);
  if(plan&&workedExample){
    const num = hasListenings ? '07' : (hasGraphic ? '06' : '05');
    const links=(workedExample.claim_ids||[]).map(id=>`#${id}`).join(', ');
    content+=`<div class="pedagogy-block worked-example-block">
      <div class="block-header"><span class="block-num">${num}</span><div><h3>Ejemplo resuelto completo</h3><p class="block-desc">Modelo listo para utilizar en la explicación y proyectar en el aula.</p></div></div>
      <div class="worked-example"><div class="worked-example-head"><div><span class="eyebrow">${e(workedExample.language||'ejemplo')}</span><h4>${e(workedExample.title)}</h4></div><button class="button small ghost" data-copy-code="${e(run.id)}">${icon('copy')}Copiar código</button></div><pre><code>${e(workedExample.code)}</code></pre><div class="worked-example-notes"><strong>Cómo leer el ejemplo</strong><ol>${(workedExample.explanation||[]).map(item=>`<li>${e(item)}</li>`).join('')}</ol>${links?`<p>Base documental: contenidos ${e(links)}.</p>`:''}</div></div>
    </div>`;
  }

  if (!hasGraphic) {
    for (const visual of visuals) content += visualHTML(run, visual);
  }
  if (run.status === 'draft' && isPedagogy && !review) {
    content += `<div class="review-actions"><button class="button primary" data-review-approve="${e(run.id)}">${icon('check')}Aprobar propuesta</button><button class="button ghost" data-review-reject="${e(run.id)}">${icon('close')}Rechazar</button></div>`;
  }
  if (isPedagogy && review?.action === 'approved') {
    content += `<div class="review-actions"><button class="button" data-record-run="${e(run.id)}">${icon('record')}Registrar clase impartida</button></div>`;
  }
  return content+'</section>';
}

export function teacherWorkedExample(run){
  const supplied=run.result?.teacher_guide?.worked_example;
  if(supplied)return supplied;
  const corpus=[run.request?.question||'',...(run.result?.claims||[]).map(item=>item.text||''),...(run.result?.visualizations||[]).flatMap(item=>(item.items||[]).flatMap(part=>[part.label||'',part.detail||'']))].join(' ');
  const labels=new Set((run.result?.visualizations||[]).flatMap(item=>item.items||[]).map(item=>item.label));
  if(!/lilypond/i.test(corpus)||!labels.has('\\score'))return null;
  return {title:'Archivo LilyPond completo y compilable',language:'lilypond',claim_ids:[3,4,5].filter(id=>id<=(run.result?.claims||[]).length),code:`\\version "2.23.82"

\\header {
  title = "Mi primera partitura"
  composer = "Nombre del alumno/a"
}

% VARIABLE MUSICAL: se declara sin barra invertida.
% Guarda este fragmento para poder reutilizarlo después.
melody = \\relative {
  c'4 a b c
}

\\score {
  % LLAMADA A LA VARIABLE: \\melody inserta aquí su contenido.
  \\melody
  \\layout { }
  \\midi { }
}`,explanation:['\\version declara la versión del lenguaje usada por el archivo.','\\header reúne los metadatos visibles, como título y compositor.','melody = ... declara una variable musical: se escribe sin barra invertida y conserva el bloque de notas.','\\melody llama a la variable dentro de \\score: la barra invertida indica que debe insertarse su contenido.','\\relative calcula cada altura con relación a la anterior y reduce la escritura de octavas.','\\layout produce la partitura gráfica y \\midi genera la reproducción MIDI.']};
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

  let html = `
  <section class="sources-bibliography">
    <div class="bib-head">
      <span class="eyebrow">FUENTES Y PASAJES DE REFERENCIA</span>
      <h3>Fuentes y citas contrastadas</h3>
      <p class="muted-small">Pasajes textuales extraídos de tu biblioteca que fundamentan este análisis:</p>
    </div>
    <div class="bibliography-grid">`;
  for (const citation of allCitations) {
    const source = run.evidence.find(s => s.source_id === citation.source_id);
    if (!source) continue;
    const m = source.metadata, l = source.locator;
    const location = locatorLabel(l);
    html += `
    <div class="bibliography-card">
      <div class="bib-header">
        <span class="bib-title">${e(m.title)}</span>
        <span class="bib-loc">${e(location)}</span>
      </div>
      <blockquote class="bib-quote">«${e(citation.quote)}»</blockquote>
      <div class="bib-footer">
        <span>${e(m.authors?.join(', ') || 'Sin autor')}${m.year ? ' · ' + e(m.year) : ''} (${source.category === 'profesor' ? 'Material propio' : 'Fuente documental'})</span>
        <button class="button ghost small" data-document="${e(source.document_id)}">Ver fuente ${icon('arrow')}</button>
      </div>
    </div>`;
  }
  html += `</div></section>`;
  return html;
}

export function sourcesModal(run){
  const appendix=bibliographyHTML(run);
  modal('Anexo documental',`${appendix||'<p>No hay citas documentales disponibles para esta propuesta.</p>'}<div class="dialog-actions"><button class="button" data-download-sources="${e(run.id)}">${icon('download')}Descargar anexo</button><button class="button primary" type="button" data-action="close-dialog">Volver a la propuesta</button></div>`);
}

export function locatorLabel(locator) {
  let label;
  if(locator.kind==='pdf_page') label=`Página ${locator.pdf_page_index} del PDF`;
  else if(locator.kind==='docx_paragraph') label=`Párrafo ${locator.paragraph_index} del DOCX`;
  else if(locator.kind==='docx_table') label=`Tabla ${locator.table_index} del DOCX`;
  else label=`Líneas ${locator.line_start}–${locator.line_end}`;
  if(locator.section) label+=' · '+locator.section;
  if(locator.ocr_document||locator.text_origin==='texto OCR') label+=' · Texto OCR: posible error de reconocimiento';
  return label;
}

export function evidenceHTML(run,citations) {
  let content='';
  for (const citation of citations||[]) {const source=run.evidence.find(s=>s.source_id===citation.source_id);if(!source)continue;const m=source.metadata,l=source.locator;const location=locatorLabel(l);
    content+=`<details class="evidence"><summary>${source.category==='profesor'?'Material propio':'Fuente documental'} · ${e(m.title)} · ${e(location)}</summary><blockquote>${e(citation.quote)}</blockquote><p>${e(m.authors?.join(', ') || 'Sin autor')}${m.year?' · '+e(m.year):''}</p><button class="button ghost small" data-document="${e(source.document_id)}">Ver fuente ${icon('arrow')}</button></details>`;
  }
  return content;
}

export function visualHTML(run,visual) {
  const type=['sequence','relationship','table'].includes(visual.type)?visual.type:'relationship';
  const items=(visual.items||[]).map(item=>`<div class="visual-node"><strong>${e(item.label)}</strong><span>${e(item.detail)}</span></div>`).join('');
  return `<section class="source-visual source-visual-${type}" aria-label="${e(visual.title)}"><span class="eyebrow">ESQUEMA DOCUMENTADO</span><h3>${e(visual.title)}</h3><div class="visual-canvas">${items}</div><p class="visual-caption">${e(visual.caption)}</p></section>`;
}
