// Módulo local: responsabilidad separada sin alterar el contenido.
import { resultHTML } from '../componentes/documentos.js';
import { draft, store, subjectName } from '../state.js';
import { dateLabel, e, header, icon, modal, option, primary } from '../ui.js';

export function proposals() {
  const runs = store.state.runs.filter(r=>r.kind==='proposal');
  const groups = store.state.config.groups;
  return header('TALLER DOCENTE','De las fuentes a la clase.','Propuestas a tu medida, para revisar y hacer tuyas.',primary('Nueva propuesta','new-proposal','plus')) +
  (store.currentRun?.request.pedagogy
    ? `<button class="button ghost small" data-action="close-run">${icon('arrowleft')}Volver a mis propuestas</button>${resultHTML(store.currentRun)}`
    : runs.length
    ? `<div class="library-summary"><span>${runs.length} ${runs.length===1?'propuesta guardada':'propuestas guardadas'}</span><span>Revisa cada propuesta antes de utilizarla</span></div><div class="proposal-list">${runs.map(r=>{
        const reviewClass=r.review_action==='approved'?'approved':r.review_action==='rejected'?'rejected':'pending';
        const reviewLabel=r.review_action==='approved'?'Aprobada':r.review_action==='rejected'?'Rechazada':'Borrador';
        const subj = r.subject || 'none';
        const groupName = r.request?.pedagogy?.group?.name || '';
        const duration = r.request?.pedagogy?.duration_minutes ? `${r.request.pedagogy.duration_minutes} min` : '';
        const metaParts = [dateLabel(r.created_at), groupName, duration].filter(Boolean);
        return `<article class="proposal-card subject-${e(subj)}" data-subject="${e(subj)}">
          <div class="proposal-card-header">
            <div class="proposal-card-tags">
              <span class="subject-badge subject-tag-${e(subj)}">${e(subjectName(r.subject) || 'Sin materia')}</span>
              <span class="badge ${reviewClass}">${reviewLabel}</span>
            </div>
            <button class="icon-button danger proposal-delete-btn" data-delete-run="${e(r.id)}" aria-label="Eliminar propuesta" title="Eliminar propuesta">${icon('trash')}</button>
          </div>
          <button class="proposal-card-body" data-run="${e(r.id)}">
            <h3 class="proposal-card-title">${e(r.title || r.request?.question || 'Propuesta sin título')}</h3>
            <div class="proposal-card-meta">
              <span>${metaParts.join(' · ')}</span>
            </div>
            <span class="proposal-card-cta">Abrir propuesta ${icon('arrow')}</span>
          </button>
        </article>`;
      }).join('')}</div>`
    : `<section class="empty-library"><div class="onboarding-mark">${icon('document')}</div><h2>Una clase empieza con una buena idea.</h2><p>Elige un grupo, un tema y el tiempo disponible. El asistente propondrá objetivos y actividades con base en tu biblioteca.</p>${primary('Preparar una propuesta','new-proposal','plus')}<span class="format-hint">Tú decides qué llevar al aula.</span></section>`);
}

export function proposalModal(session=null) {
  if(!store.state.config.groups.length){modal('Primero, tu grupo',`<p>Para preparar una propuesta útil necesitamos conocer el nivel y la materia del grupo.</p><div class="dialog-actions">${primary('Añadir un grupo','new-group')}</div>`);return;}
  const group = session?.group_id || draft('proposal-form','group',store.state.config.groups[0].id);
  const duration = session?.duration_minutes || draft('proposal-form','duration','60');
  const sessionDate = session ? store.state.agenda.date : draft('proposal-form','session_date','');
  modal('Preparar una propuesta',`<p>Un punto de partida con objetivos, actividades y tiempos. Tú tendrás la última palabra.</p><form data-form="proposal" id="proposal-form"><div class="form-row proposal-schedule"><div class="field"><label class="label" for="proposal-group">Grupo</label><select id="proposal-group" name="group" required>${store.state.config.groups.map(g=>option(g.id,`${g.name} · ${subjectName(g.subject_id)}`,group)).join('')}</select></div><div class="field"><label class="label" for="proposal-date">Fecha de la clase · opcional</label><input class="input" id="proposal-date" type="date" name="session_date" value="${e(sessionDate)}"></div><div class="field"><label class="label" for="proposal-duration">Duración</label><input class="input" id="proposal-duration" type="number" name="duration" min="5" max="240" required value="${e(duration)}"></div></div><div class="field"><label class="label" for="proposal-topic">Tema de la sesión</label><input class="input" id="proposal-topic" name="question" maxlength="4000" required placeholder="¿Qué quieres trabajar?" value="${e(draft('proposal-form','question'))}"></div><div class="field"><label class="label" for="proposal-unit">Unidad de la programación · opcional</label><select id="proposal-unit" name="unit">${unitOptions(group)}</select></div><div class="field"><label class="label" for="proposal-criteria">Tus indicaciones · opcional</label><textarea id="proposal-criteria" name="criteria" maxlength="2000" placeholder="Qué priorizar, qué materiales tienes, qué conviene evitar…">${e(draft('proposal-form','criteria'))}</textarea></div><p class="field-note">La propuesta combinará la programación didáctica de la materia con tus fuentes autorizadas.</p><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button primary">${icon('spark')}Preparar propuesta</button></div></form>`);
}

export function expandProposalModal(run) {
  if (!run) return;
  const ctx = run.request?.pedagogy;
  const groups = store.state.config.groups || [];
  const currentGroupId = ctx?.group?.id || groups[0]?.id || '';
  const currentTopic = run.request?.question || '';
  const currentDuration = ctx?.duration_minutes || 60;
  const priorCriteria = ctx?.teacher_criteria || '';
  
  modal('Ampliar propuesta pedagógica', `
    <p class="muted-small">Añade nuevas técnicas, contenidos o ejercicios prácticos manteniendo la base de tu biblioteca sin necesidad de rechazar esta propuesta.</p>
    <form data-form="proposal" id="proposal-form">
      <input type="hidden" name="session_date" value="${e(ctx?.session?.date||'')}">
      <div class="form-row">
        <div class="field">
          <label class="label" for="proposal-group">Grupo</label>
          <select id="proposal-group" name="group" required>
            ${groups.map(g => option(g.id, `${g.name} · ${subjectName(g.subject_id)}`, currentGroupId)).join('')}
          </select>
        </div>
        <div class="field">
          <label class="label" for="proposal-duration">Duración en minutos</label>
          <input class="input" id="proposal-duration" type="number" name="duration" min="5" max="240" required value="${e(currentDuration)}">
        </div>
      </div>
      <div class="field">
        <label class="label" for="proposal-topic">Tema principal</label>
        <input class="input" id="proposal-topic" name="question" maxlength="4000" required value="${e(currentTopic)}">
      </div>
      <div class="field">
        <label class="label" for="proposal-criteria">Contenidos, técnicas y ejercicios a añadir</label>
        <textarea id="proposal-criteria" name="criteria" maxlength="2000" rows="3" required placeholder="Ej. Añadir técnicas de composición de compositores ingleses: paráfrasis, melodía migratoria, faburden y ejercicios prácticos individuales y en grupo...">${priorCriteria ? e(priorCriteria + '\nAmpliación: ') : ''}</textarea>
        <p class="field-note">El asistente consultará tu biblioteca y elaborará una propuesta enriquecida con los nuevos contenidos y ejercicios prácticos solicitados.</p>
      </div>
      <div class="dialog-actions">
        <button class="button ghost" type="button" data-action="close-dialog">Cancelar</button>
        <button class="button primary" type="submit">${icon('spark')}Generar ampliación</button>
      </div>
    </form>
  `);
}

export function unitOptions(group) {const binding=store.state.config.group_curricula.find(b=>b.group_id===group);return '<option value="">Sin unidad seleccionada</option>'+store.state.config.curriculum_units.filter(u=>u.curriculum_id===binding?.curriculum_id).map(u=>option(u.id,u.title,draft('proposal-form','unit'))).join('');}
