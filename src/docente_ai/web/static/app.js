const $ = (s, root = document) => root.querySelector(s);
const token = $('meta[name="docente-token"]').content;
const e = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths = {
 library:'<path d="M4 4h4v16H4zM10 4h4v16h-4zM16 5l4-1 4 15-4 1z"/>',
 spark:'<path d="m12 3 2.8 6.2L21 12l-6.2 2.8L12 21l-2.8-6.2L3 12l6.2-2.8L12 3Z"/><path d="m20 2 .8 1.7L22.5 4l-1.7.8L20 6.5l-.8-1.7L17.5 4l1.7-.3Z"/>',
 document:'<path d="M5 3h9l5 5v13H5zM14 3v6h5M8 13h8M8 17h6"/>',
 settings:'<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="15" cy="17" r="3"/>',
 folder:'<path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10H3z"/>',
 plus:'<path d="M12 5v14M5 12h14"/>', search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
 arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>', up:'<path d="M12 16V3m-5 5 5-5 5 5M4 15v6h16v-6"/>',
 close:'<path d="m6 6 12 12M6 18 18 6"/>', check:'<path d="m5 12 4 4L19 6"/>',
 shield:'<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
 external:'<path d="M13 4h7v7m0-7L10 14M9 4H4v16h16v-5"/>',
 download:'<path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4"/>',
 refresh:'<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>', edit:'<path d="m15 4 5 5M4 20l5-1L21 7l-5-5L4 14z"/>',
 arrowleft:'<path d="M19 12H5m5-5-5 5 5 5"/>', copy:'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8V3H3v13h5"/>',
 record:'<path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M9 7h6M7 12h10M7 17h7"/>',
 trash:'<path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M10 11v6M14 11v6"/>'
};
const icon = name => `<svg class="icon" viewBox="0 0 25 25" aria-hidden="true">${paths[name] || paths.document}</svg>`;
document.querySelectorAll('[data-icon]').forEach(el => el.innerHTML = icon(el.dataset.icon));
let state, modelStatus, selected = localStorage.getItem('enjambre-subject') || '', selectedPeriod = '', tab = 'all', query = '', currentRun = null;
const periodLabels = {
  '00 Xeral e Tratados': 'Xeral e Tratados',
  '01 Antiguedade': 'Antigüidade',
  '02 Idade Media': 'Idade Media',
  '03 Renacemento': 'Renacemento',
  '01 Barroco e Preclasicismo': 'Barroco e Preclasicismo',
  '02 Clasicismo': 'Clasicismo',
  '03 Romanticismo': 'Romanticismo',
  '04 Seculo XX e Contemporanea': 'Século XX e Contemporánea',
};
const formatPeriod = p => periodLabels[p] || (p ? p.replace(/^\d+\s*/, '') : '');
let drafts = {}, chosenFiles = [], knownJobs = new Map(), polling = false, toastTimer, monitorTimer, connectionLost = false, isClosed = false;
const main = $('#main'), dialog = $('#dialog');
const view = () => ['biblioteca','asistente','propuestas','diario','ajustes'].includes(location.hash.slice(1)) ? location.hash.slice(1) : 'biblioteca';
const subjectName = id => state.config.subjects.find(s => s.id === id)?.name || 'Sin materia';
const readyDocs = subject => state.documents.filter(d => d.enabled && d.indexed && (!subject || d.shared || d.subjects.includes(subject)));
const draft = (form, key, fallback = '') => drafts[form]?.[key] ?? fallback;
const option = (value, text, selectedValue) => `<option value="${e(value)}" ${value === selectedValue ? 'selected' : ''}>${e(text)}</option>`;
const subjectOptions = (value, blank = false) => (blank ? option('', 'Elige una materia', value) : '') + state.config.subjects.map(s => option(s.id, s.name, value)).join('');
const statusBadge = doc => doc.enabled ? doc.indexed ? '<span class="badge">Preparada</span>' : '<span class="badge pending">Por preparar</span>' : '<span class="badge off">Por revisar</span>';
const dateLabel = value => new Intl.DateTimeFormat('es', {day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'}).format(new Date(value));
const runStatus = value => ({draft:'Borrador',abstained:'Sin respaldo suficiente',failed:'No completado',running:'En curso',cancelled:'Cancelado'}[value] || value);
async function api(path, data, options = {}) {
  const response = await fetch('/api' + path, {method: data === undefined ? 'GET' : 'POST', headers:{'X-Docente-Token':token, ...(data === undefined ? {} : {'Content-Type':'application/json'}), ...options.headers}, ...(data === undefined ? {} : {body:JSON.stringify(data)}), ...options});
  if (!response.ok) { let message = 'No se pudo completar la operación.'; try {message = (await response.json()).error || message;} catch {} throw new Error(message); }
  return response.json();
}
function toast(message, error = false) {const element = $('#toast'); element.textContent = message; element.className = error ? 'error' : ''; element.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => element.hidden = true, error ? 12000 : 5500);}
function fail(error) {const target = dialog.open ? $('.form-error', dialog) : null; if (target) target.textContent = error.message; else toast(error.message, true);}
async function refresh(renderPage = true) {state = await api('/state'); if (!state.config.subjects.some(s => s.id === selected)) selected = ''; if (renderPage) render(); $('#source-count').textContent = state.documents.length; return state;}
function header(eyebrow, title, description, actions = '') {return `<section class="page-head"><div><span class="eyebrow">${eyebrow}</span><h1>${title}</h1><p>${description}</p></div>${actions ? `<div class="head-actions">${actions}</div>` : ''}</section>`;}
function primary(text, action, name='plus') {return `<button class="button primary" data-action="${action}">${icon(name)}${text}</button>`;}
function dailyAgenda() {
  const agenda=state.agenda, sessions=agenda?.sessions||[];
  const feedbackMode=view()==='diario';
  const day=new Date(`${agenda?.date||new Date().toISOString().slice(0,10)}T12:00:00`);
  const label=new Intl.DateTimeFormat('es',{weekday:'long',day:'numeric',month:'long'}).format(day);
  const cards=sessions.map(session=>{
    const start=new Date(session.start), end=new Date(session.end), now=new Date();
    const status=now>=start&&now<end?'Ahora':now<start?'Próxima':'Finalizada';
    const time=new Intl.DateTimeFormat('es',{hour:'2-digit',minute:'2-digit'}).format(start);
    const subjId = session.subject_id || 'none';
    return `<button class="agenda-session subject-${e(subjId)}" data-subject="${e(subjId)}" ${feedbackMode?`data-feedback-session="${e(session.id)}"`:`data-prepare-session="${e(session.id)}"`} aria-label="${feedbackMode?'Registrar feedback de':'Preparar'} ${e(session.subject)} a las ${e(time)}"><span class="agenda-time">${e(time)}</span><span class="agenda-copy"><strong title="${e(session.subject)}">${e(session.subject)}</strong><small title="${e(session.group)}${session.room?' · '+e(session.room):''}">${e(session.group)}${session.room?' · '+e(session.room):''}</small></span><span class="agenda-status ${status.toLowerCase()}">${status}</span><span class="agenda-action">${feedbackMode?'Dar feedback':'Preparar'} ${icon('arrow')}</span></button>`;
  }).join('');
  return `<section class="daily-agenda" aria-label="Clases de hoy"><div class="agenda-heading"><div><span class="eyebrow">HOY · ${e(label.toLocaleUpperCase('es'))}</span><h2>${sessions.length?`${sessions.length} ${sessions.length===1?'clase':'clases'} en tu agenda`:'Hoy no tienes clases programadas'}</h2></div><span class="agenda-note">${sessions.length?(feedbackMode?'Selecciona una clase para dejar tu valoración.':'Selecciona una clase para preparar su propuesta.'):'Tu horario está al día.'}</span></div>${sessions.length?`<div class="agenda-track">${cards}</div>`:''}</section>`;
}
function formatMarkdown(text) {
  if (!text) return '';
  let out = e(text);

  // Generic code blocks remain escaped; generated text is never executable markup.
  out = out.replace(/```([a-z0-9_-]*)\s*([\s\S]*?)```/gi, (_, lang, code) => `<pre><code>${code.trim()}</code></pre>`);

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
        htmlTable += '<thead><tr>' + cells.map(c => `<th>${c}</th>`).join('') + '</tr></thead><tbody>';
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
      const items = trimmed.split('\n').filter(l => l.trim().startsWith('-')).map(l => `<li>${l.trim().replace(/^-\s+/, '')}</li>`).join('');
      return `<ul>${items}</ul>`;
    }
    return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
  }).join('');
}

function render() {
  if(isClosed){main.innerHTML='<section class="empty-library"><h2>Tu espacio está cerrado.</h2><p>Todo queda guardado. Abre Enjambre.app para volver a trabajar.</p></section>';return;}
  const focused=document.activeElement, focusId=main.contains(focused)?focused.id:null, selectionStart=focused?.selectionStart, selectionEnd=focused?.selectionEnd;
  const active = view();
  document.querySelectorAll('[data-nav]').forEach(link => {link.classList.toggle('active', link.dataset.nav === active); if (link.dataset.nav === active) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');});
  $('#section-name').textContent = ({biblioteca:'Biblioteca',asistente:'Asistente',propuestas:'Propuestas',diario:'Diario docente',ajustes:'Ajustes'})[active];
  document.title = `Enjambre · ${$('#section-name').textContent}`;
  main.className = 'content-enter';
  main.innerHTML = dailyAgenda() + ({biblioteca:library, asistente:assistant, propuestas:proposals, diario:diary, ajustes:settings})[active]();
  if(focusId){const field=document.getElementById(focusId);field?.focus({preventScroll:true});if(typeof selectionStart==='number'&&field?.setSelectionRange)field.setSelectionRange(selectionStart,selectionEnd);}
}
function library() {
  const subjectPeriods = (selected ? state.subject_periods?.[selected] : []) || [];
  return header('BIBLIOTECA DE CONOCIMIENTO', 'Tus fuentes, en un solo lugar.', 'Elige el conocimiento con el que trabajará tu asistente.', primary('Añadir documentos','add-source')) +
  `<section class="folder-banner"><div class="folder-symbol">${icon('folder')}</div><div class="folder-copy"><h3>Una biblioteca que sigue siendo tuya</h3><p>Añade archivos aquí o cópialos a tu carpeta Conocimiento.</p></div><button class="button ghost" data-action="reveal">Abrir carpeta ${icon('external')}</button></section>
  <div class="library-toolbar"><div class="tabs" role="tablist" aria-label="Tipo de fuente">${[['all','Todas las fuentes'],['documental','Documentación'],['profesor','Mis materiales'],['pending','Por revisar']].map(([id,text]) => `<button class="tab ${tab===id?'active':''}" role="tab" aria-selected="${tab===id}" data-tab="${id}">${text}</button>`).join('')}</div><label class="search">${icon('search')}<input id="library-search" type="search" placeholder="Buscar en la biblioteca" aria-label="Buscar en la biblioteca" value="${e(query)}"></label></div>
  <div class="filter-row"><span class="filter-label">CURSO / MATERIA</span><button class="chip ${!selected?'active':''}" data-subject="">Todas</button>${state.config.subjects.map(s => `<button class="chip ${selected===s.id?'active':''}" data-subject="${e(s.id)}">${e(s.name)}</button>`).join('')}<button class="icon-button" data-action="new-subject" aria-label="Añadir materia" title="Añadir materia">${icon('plus')}</button></div>
  ${subjectPeriods.length ? `<div class="filter-row period-filter-row"><span class="filter-label">PERÍODO</span><button class="chip ${!selectedPeriod?'active':''}" data-period="">Todos os períodos</button>${subjectPeriods.map(p => {
    const pCount = state.documents.filter(d => (!selected || d.shared || d.subjects.includes(selected)) && d.period === p).length;
    return `<button class="chip ${selectedPeriod===p?'active':''}" data-period="${e(p)}">${e(formatPeriod(p))}${pCount ? ` <small>(${pCount})</small>` : ''}</button>`;
  }).join('')}</div>` : ''}
  <div id="library-results">${libraryResults()}</div>`;
}
function libraryResults() {
  const docs = state.documents.filter(d => (!selected || d.shared || d.subjects.includes(selected)) && (!selectedPeriod || d.period === selectedPeriod) && (tab==='all' || tab==='pending' && !d.enabled || d.category===tab) && `${d.metadata.title} ${(d.metadata.authors||[]).join(' ')} ${(d.metadata.tags||[]).join(' ')} ${d.period||''}`.toLocaleLowerCase().includes(query.toLocaleLowerCase()));
  if (!state.documents.length) return `<section class="empty-library"><div class="library-art" aria-hidden="true"><span class="book-spine"></span><span class="book-spine"></span><span class="book-spine"></span></div><h2>Empieza por tus fuentes.</h2><p>Libros, artículos y apuntes que conoces y en los que confías. Tú decides qué puede utilizar el asistente.</p>${primary('Añadir mi primer documento','add-source','plus')}<span class="format-hint">PDF con texto · Markdown · TXT</span></section><div class="steps"><div class="step"><span>01</span><div><h3>Incorpora tus fuentes</h3><p>Arrastra archivos o elígelos desde tu equipo.</p></div></div><div class="step"><span>02</span><div><h3>Organiza y revisa</h3><p>Asigna una materia y comprueba el contenido.</p></div></div><div class="step"><span>03</span><div><h3>Trabaja con el asistente</h3><p>Consulta y prepara con referencias a tus fuentes.</p></div></div></div><div class="form-footer"><span></span><button class="button ghost small" data-action="scan">${icon('refresh')}Revisar carpeta</button></div>`;
  const periodSub = selectedPeriod ? ` · ${formatPeriod(selectedPeriod)}` : '';
  return `<div class="library-summary"><span>${docs.length} ${docs.length===1?'documento':'documentos'}${selected?' · '+e(subjectName(selected)):''}${e(periodSub)}</span><button class="button ghost small" data-action="scan">${icon('refresh')}Revisar carpeta</button></div>` + (docs.length ? `<div class="source-list">${docs.map(d => {
    const firstSubj = d.subjects && d.subjects.length ? d.subjects[0] : 'none';
    const subjBadges = d.shared ? '<span class="subject-badge subject-tag-xeral">Compartido</span>' : (d.subjects && d.subjects.length ? d.subjects.map(s => `<span class="subject-badge subject-tag-${e(s)}">${e(subjectName(s))}</span>`).join(' ') : '<span class="subject-badge subject-tag-none">Sin materia</span>');
    return `<button class="source-row subject-${e(firstSubj)}" data-document="${e(d.id)}"><span class="file-icon ${d.category}">${e(d.format.toUpperCase())}</span><span><span class="source-title">${e(d.metadata.title)}</span><span class="source-subtitle">${e(d.metadata.authors?.join(', ') || (d.category==='profesor'?'Material propio':'Autor pendiente de indicar'))}${d.metadata.year?' · '+e(d.metadata.year):''}${d.period ? ` · <span class="period-tag">${e(formatPeriod(d.period))}</span>` : ''}</span></span><span class="source-area">${subjBadges}</span>${statusBadge(d)}${icon('arrow')}</button>`;
  }).join('')}</div>` : `<div class="empty-library"><h2>No hay coincidencias.</h2><p>Prueba otra materia, período o una búsqueda diferente.</p><button class="button" data-action="clear-filter">Limpiar filtros</button></div>`);
}
function assistant() {
  const subject = draft('ask-form','subject', selected || state.config.subjects[0]?.id || '');
  const count = readyDocs(subject).length;
  return header('ASISTENTE DOCUMENTAL','Piensa con tus fuentes.','Consulta, contrasta y desarrolla ideas a partir de tu biblioteca.') +
  `<div class="workspace-grid"><div><form id="ask-form" class="panel" data-form="ask"><div class="field"><label class="label" for="ask-subject">¿En qué materia estás trabajando?</label><select id="ask-subject" name="subject" required>${subjectOptions(subject,true)}</select></div><label class="label" for="question">Tu pregunta</label><textarea id="question" name="question" class="question-box" maxlength="4000" required placeholder="¿Qué te gustaría comprender o preparar?">${e(draft('ask-form','question'))}</textarea><div class="field"><label class="label" for="ask-category">Utilizar</label><select id="ask-category" name="category">${[['all','Fuentes y materiales propios'],['documental','Solo documentación'],['profesor','Solo mis materiales']].map(([v,t]) => option(v,t,draft('ask-form','category','all'))).join('')}</select></div><div class="form-error" role="alert"></div><div class="form-footer"><p>Respuestas con referencias.<br>Siempre bajo tu revisión.</p><button class="button primary" type="submit" ${!state.config.subjects.length?'disabled':''}>${icon('spark')}Consultar fuentes</button></div></form><div id="answer-result">${currentRun && !currentRun.request.pedagogy ? resultHTML(currentRun) : ''}</div></div><aside class="panel context-panel"><div class="aside-title">TU CONTEXTO</div><h3>${e(subjectName(subject))}</h3><div class="context-number">${count}</div><div class="context-label">${count===1?'fuente preparada':'fuentes preparadas'}</div><hr class="context-rule"><p class="muted-small">${count?'El asistente consultará solo las fuentes que has autorizado para esta materia.':'Añade y autoriza una fuente para que el asistente pueda trabajar con ella.'}</p><a href="#biblioteca" class="button ghost small">Ir a la biblioteca ${icon('arrow')}</a><hr class="context-rule"><div class="aside-title">CONSULTAS RECIENTES</div>${state.runs.filter(r=>r.kind==='answer').slice(0,5).map(r=>`<button class="recent-item" data-run="${e(r.id)}">${e(r.title)}<span>${dateLabel(r.created_at)} · ${runStatus(r.status)}</span></button>`).join('') || '<p class="muted-small">Tus consultas aparecerán aquí.</p>'}${state.runs.filter(r=>r.kind==='answer').length>5?'<button class="button ghost small" data-action="all-answers">Ver todas las consultas</button>':''}</aside></div>`;
}
function proposals() {
  const runs = state.runs.filter(r=>r.kind==='proposal');
  const groups = state.config.groups;
  return header('TALLER DOCENTE','De las fuentes a la clase.','Propuestas a tu medida, para revisar y hacer tuyas.',primary('Nueva propuesta','new-proposal','plus')) +
  (currentRun?.request.pedagogy
    ? `<button class="button ghost small" data-action="close-run">${icon('arrowleft')}Volver a mis propuestas</button>${resultHTML(currentRun)}`
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
function diary(){
  const records=state.records||[];
  const groupName=id=>state.config.groups.find(group=>group.id===id)?.name||id;
  return header('ESPACIO DEL PROFESOR','Diario docente.','Registra lo que ocurrió en el aula. Tu feedback orientará las próximas propuestas.',primary('Registrar otra sesión','new-feedback','record'))+
    `<section class="folder-banner diary-folder"><div class="folder-symbol">${icon('folder')}</div><div class="folder-copy"><h3>Material de sesiones ordenado por fecha</h3><p>Guías, material del alumnado, anexos y feedback se guardan en 03 Diario docente.</p></div><button class="button ghost" data-action="reveal-diary">Abrir carpeta ${icon('external')}</button></section>`+
    (records.length?`<div class="diary-list">${records.map(record=>{const fb=record.feedback||{};const complete=!!(fb.what_worked||fb.what_failed||fb.next_session_note);return `<article class="diary-entry"><div class="diary-date"><strong>${e(record.session_date.slice(8,10))}</strong><span>${e(new Intl.DateTimeFormat('es',{month:'short'}).format(new Date(record.session_date+'T12:00:00')))}</span></div><div class="diary-entry-copy"><span class="eyebrow">${e(groupName(record.group_id))} · ${record.duration_minutes} min</span><h3>${e(record.topic)}</h3><p>${complete?e(fb.next_session_note||fb.what_worked||'Feedback registrado'):'Feedback pendiente'}</p></div><span class="badge ${complete?'':'pending'}">${complete?'Registrado':'Pendiente'}</span><button class="button small" data-session-record="${e(record.id)}">${complete?'Revisar feedback':'Completar feedback'}</button><button class="icon-button" data-reveal-record="${e(record.id)}" aria-label="Abrir carpeta de la sesión" title="Abrir carpeta">${icon('folder')}</button></article>`;}).join('')}</div>`:`<section class="empty-library diary-empty"><div class="onboarding-mark">${icon('record')}</div><h2>Tu experiencia también forma parte del sistema.</h2><p>Después de cada clase, anota qué funcionó, qué cambiarías y por dónde continuar.</p>${primary('Registrar la primera sesión','new-feedback','record')}</section>`);
}
function settings() {
  return header('MI ESPACIO','A tu manera.','Organiza tus materias, grupos y entorno de trabajo local.') + `<div class="settings-grid">
  <section class="panel"><div class="panel-header"><h2>Materias</h2><button class="button small" data-action="new-subject">${icon('plus')}Añadir</button></div>${state.config.subjects.map(s=>`<div class="setting-row"><span>${e(s.name)}<small>${state.documents.filter(d=>d.subjects.includes(s.id)).length} documentos</small></span><button class="icon-button" data-edit-subject="${e(s.id)}" aria-label="Editar ${e(s.name)}">${icon('edit')}</button></div>`).join('') || '<p class="muted-small">Crea una materia para empezar a organizar tus fuentes.</p>'}</section>
  <section class="panel"><div class="panel-header"><h2>Grupos</h2><button class="button small" data-action="new-group">${icon('plus')}Añadir</button></div>${state.config.groups.map(g=>`<div class="setting-row"><span>${e(g.name)}<small>${e(subjectName(g.subject_id))} · ${e(g.level)}</small></span><button class="icon-button" data-edit-group="${e(g.id)}" aria-label="Editar ${e(g.name)}">${icon('edit')}</button></div>`).join('') || '<p class="muted-small">Añade tus grupos para preparar propuestas adaptadas a su nivel.</p>'}</section>
  <section class="panel"><div class="panel-header"><h2>Horario y Calendario</h2><button class="button primary small" data-action="download-calendar">${icon('download')}Descargar .ics</button></div><p class="muted-small">Sincroniza tus clases semanales con Apple Calendar, Google Calendar u Outlook, con recordatorios configurados 15 min antes.</p><div class="setting-row"><span>Historia 5 (5º GP)<small>Martes y Viernes · 18:30–19:30 · Aula Historia</small></span></div><div class="setting-row"><span>Historia 4 (4º GP)<small>Martes y Viernes · 19:30–20:30 · Aula Historia</small></span></div><div class="setting-row"><span>NNTT 3P B (3º GP)<small>Lunes 19:30–20:30 y Jueves 17:30–18:30 · Aula NNTT</small></span></div><div class="setting-row"><span>Conxuntos y Guitarra<small>Lunes a Viernes · Aula Guitarra 1</small></span></div></section>
  <section class="panel"><div class="panel-header"><h2>Tu carpeta de conocimiento</h2>${icon('folder')}</div><p class="muted-small">Los documentos permanecen en tu equipo. Fuentes documentales y materiales propios se guardan por separado.</p><p class="path">${e(state.knowledge_path)}</p><button class="button" data-action="reveal">${icon('external')}Abrir en Finder</button><button class="button ghost" data-action="scan">Revisar archivos</button></section>
  <section class="panel"><div class="panel-header"><h2>Motor de IA</h2><button class="icon-button" data-action="status" aria-label="Comprobar conexión">${icon('refresh')}</button></div>${(()=>{const provider=state.generation_provider||'ollama';const isDS=provider==='deepseek';const embedList=modelStatus?.embedding_models?.length?modelStatus.embedding_models:['bge-m3'];const currentEmbed=modelStatus?.embeddings||'bge-m3';const ollamaList=modelStatus?.ollama_models?.length?modelStatus.ollama_models:(modelStatus?.models?.length?modelStatus.models:['qwen3:14b']);const currentGen=modelStatus?.generation||(isDS?'deepseek-chat':'qwen3:14b');return`<div class="settings-model"><span>Proveedor activo</span><strong>${isDS?'DeepSeek (nube)':'Ollama (local)'}</strong></div><div class="settings-model"><span>Modelo generativo</span><strong>${e(currentGen)}</strong></div><div class="settings-model"><span>Búsqueda documental</span><strong>${e(currentEmbed)} · siempre local</strong></div><details class="metadata"><summary>Configurar</summary><form data-form="models" class="model-form"><div class="field"><label class="label" for="model-provider">Proveedor</label><select id="model-provider" name="provider"><option value="deepseek" ${isDS?'selected':''}>DeepSeek (API nube · rápido y potente)</option><option value="ollama" ${!isDS?'selected':''}>Ollama (100% local en este equipo)</option></select></div><div class="field ds-only" ${!isDS?'hidden':''}><label class="label" for="model-apikey">Clave API DeepSeek</label><input id="model-apikey" name="api_key" type="password" autocomplete="off" placeholder="sk-…" value=""><p class="field-note">Tu clave se guarda en tu equipo. Los documentos son locales; solo los fragmentos relevantes se envían.</p></div><div class="field ds-only" ${!isDS?'hidden':''}><label class="label" for="model-gen-ds">Modelo DeepSeek</label><select id="model-gen-ds" name="generation_ds">${[['deepseek-chat','DeepSeek-V3 — rápido y económico'],['deepseek-reasoner','DeepSeek-R1 — razonamiento profundo']].map(([v,t])=>option(v,t,currentGen)).join('')}</select></div><div class="field ollama-only" ${isDS?'hidden':''}><label class="label" for="model-generation">Modelo para respuestas (Ollama)</label><select id="model-generation" name="generation_ollama">${ollamaList.map(m=>option(m,m,currentGen)).join('')}</select></div><div class="field"><label class="label" for="model-embeddings">Modelo para búsqueda documental (local)</label><select id="model-embeddings" name="embeddings" required>${embedList.map(m=>option(m,m,currentEmbed)).join('')}</select><p class="field-note">Búsqueda siempre local en tu Mac.</p></div><div class="form-error" role="alert"></div><button class="button small" type="submit">Guardar</button></form></details>`})()}</section></div><div class="form-footer"><span></span><button class="button ghost small" data-action="shutdown-dialog">Cerrar Enjambre</button></div>`;
}

function is15thCenturyPolyphony(run) {
  const text = ((run.request?.question || '') + ' ' + (run.request?.pedagogy?.teacher_criteria || '') + ' ' + (run.result?.claims || []).map(c=>c.text).join(' ')).toLowerCase();
  return text.includes('xv') || text.includes('ockeghem') || text.includes('dufay') || text.includes('binchois') || text.includes('busnois') || text.includes('cantus firmus') || text.includes('formes fixes') || text.includes('chanson') || text.includes('misa');
}

function isAncientEgypt(run) {
  const q = (run.request?.question || '').toLowerCase();
  const criteria = (run.request?.pedagogy?.teacher_criteria || '').toLowerCase();
  const claims = (run.result?.claims || []).map(c => c.text).join(' ').toLowerCase();
  const unitTitle = (run.request?.pedagogy?.unit?.title || '').toLowerCase();
  const unitId = run.request?.pedagogy?.unit?.id || run.request?.pedagogy?.unit_id || '';
  const text = `${q} ${criteria} ${claims} ${unitTitle}`;
  return text.includes('egipt') || text.includes('nilo') || text.includes('hathor') || text.includes('sistro') || text.includes('menat') || text.includes('nebamun') || text.includes('mesopotamia') || text.includes('antigüedad') || text.includes('antiga') || unitId === 'unit-h1-1';
}

const POLYPHONY_LISTENINGS = [
  {
    index: 1,
    composer: 'Guillaume Du Fay',
    title: 'Missa Se la face ay pale',
    subtitle: 'Kyrie y Gloria · Misa de cantus firmus secular a 4 voces sobre su propia chanson balada',
    performer: 'Early Music Consort of London, dir. David Munrow',
    anthology: 'Allan Atlas (Antología Norton, nº 14) / Gustave Reese',
    links: [
      { label: 'Escuchar el Kyrie en YouTube', url: 'https://www.youtube.com/watch?v=izy4bDPp23k' },
      { label: 'Escuchar el Gloria en YouTube', url: 'https://www.youtube.com/watch?v=McyAlOZ4JjQ' }
    ],
    teacher_note: 'Son especialmente útiles porque pertenecen a la misma grabación y mantienen una interpretación homogénea.',
    points: [
      'Identificar la entrada del Tenor en valores aumentados (proporción 3:1 en el Gloria).',
      'Observar el contraste tímbrico entre las notas sostenidas del Tenor y el contrapunto ágil de Superius y Altus.',
      'Detectar la articulación cadencial Landini (salto melódico de sexta a octava).'
    ]
  },
  {
    index: 2,
    composer: 'Gilles Binchois',
    title: 'De plus en plus se renouvelle',
    subtitle: 'Chanson cortesana borgoñona a 3 voces (Forme Fixe: Rondeau)',
    performer: 'Ensemble Gilles Binchois, dir. Dominique Vellard',
    anthology: 'Allan Atlas (Antología Norton, nº 11) / Gustave Reese',
    links: [
      { label: 'Escuchar De plus en plus en YouTube', url: 'https://www.youtube.com/watch?v=cw_V53noTUg' }
    ],
    teacher_note: 'Esta versión me parece particularmente apropiada para apreciar el carácter lírico de la chanson y la claridad de las tres voces.',
    points: [
      'Seguir la melodía lírica y transparente del Superius en ritmo ternario suave.',
      'Apreciar la sonoridad dulce de terceras y sextas imperfectas (contenance angloise).',
      'Distinguir la claridad meridiana de las frases musicales delimitadas por cadencias nítidas.'
    ]
  },
  {
    index: 3,
    composer: 'Johannes Ockeghem',
    title: "Missa L'homme armé",
    subtitle: 'Kyrie y Agnus Dei · Misa de cantus firmus a 4 voces sobre la popular melodía borgoñona',
    performer: 'Oxford Camerata, dir. Jeremy Summerly',
    anthology: 'Manuscrito Chigi C.VIII.234 (Vaticano) / Gustave Reese',
    links: [
      { label: 'Escuchar el Kyrie en YouTube', url: 'https://www.youtube.com/watch?v=KgV3cxc1NEI' },
      { label: 'Escuchar el Agnus Dei en YouTube', url: 'https://www.youtube.com/watch?v=xDFKOKWzpI0' }
    ],
    teacher_note: 'También aquí tienes la ventaja de utilizar la misma interpretación para ambos movimientos.',
    points: [
      'Percibir el registro vocal más profundo y homogéneo (el Bassus desciende a graves inusuales en Du Fay).',
      'Comprobar cómo las frases se solapan en un flujo polifónico continuo sin pausas colectivas.',
      'Escuchar los apéndices ornamentales añadidos al cantus firmus en el Tenor.'
    ]
  },
  {
    index: 4,
    composer: 'Johannes Ockeghem',
    title: 'Mort, tu as navré (Déploration sur la mort de Binchois)',
    subtitle: 'Motete-chanson funerario bilingüe a 4 voces (1460)',
    performer: 'Graindelavoix, dir. Björn Schmelzer',
    anthology: 'Allan Atlas (Cap. XI-XII) / Gustave Reese',
    links: [
      { label: 'Escuchar Mort, tu as navré en YouTube', url: 'https://www.youtube.com/watch?v=R9tcg1VfKPs' }
    ],
    teacher_note: 'Esta grabación funciona muy bien para clase por el contraste con las audiciones anteriores y por el carácter expresivo y sombrío de la obra.',
    points: [
      'Reconocer la textura bilingüe: Superius canta en francés la balada y el Tenor canta en latín el Pie Jhesu Domine.',
      'Identificar la paráfrasis litúrgica del canto llano del Dies Irae en el Tenor.',
      'Sentir el austero diatonicismo modal y el clima sombrío de homenaje al maestro borgoñón.'
    ]
  }
];

const EGYPT_LISTENINGS = [
  {
    index: '1A',
    composer: 'Michael Levy',
    title: 'Ancient Harps of Kemet',
    subtitle: 'Arpa arqueada · Recreación tímbrica e improvisación moderna (2011)',
    performer: 'Michael Levy (arpa arqueada de tipo arcaico)',
    anthology: 'Reconstrucción organológica / Arqueomusicología experimental',
    links: [
      { label: 'Escuchar en YouTube (Levy – Ancient Harps of Kemet)', url: 'https://www.youtube.com/watch?v=mqxB34z4tyw' }
    ],
    teacher_note: 'No es una pieza transmitida desde el Egipto faraónico: es una improvisación moderna sobre un arpa arqueada de tipo arcaico. Resulta útil para que el alumnado escuche un modelo de sonoridad próximo a la iconografía y para plantear cómo se reconstruye un paisaje sonoro cuando faltan partituras.',
    points: [
      'El ataque de la cuerda pulsada y la resonancia corta del instrumento.',
      'La ausencia de progresiones armónicas funcionales propias de la tonalidad moderna.',
      'La repetición y variación de células breves como recurso para construir continuidad.',
      'La diferencia entre escuchar el timbre de un instrumento reconstruido y afirmar que conocemos la música original.'
    ]
  },
  {
    index: '1B',
    composer: 'Michael Levy',
    title: 'Reconstructed Ancient Egyptian Melody',
    subtitle: 'Arreglo para lira de propuesta reconstructiva vinculada a escena de banquete tebano',
    performer: 'Michael Levy (lira; melodía basada en De Organographia y flauta vertical)',
    anthology: 'Escena de banquete tebano / Ensemble De Organographia',
    links: [
      { label: 'Escuchar en YouTube (Levy – Reconstructed Melody)', url: 'https://www.youtube.com/watch?v=nBmWXmn11YE' }
    ],
    teacher_note: 'Levy explica que tomó la melodía de De Organographia y que la escala se relacionó con una flauta vertical egipcia conservada. La utilidad didáctica está en observar el procedimiento de reconstrucción, no en tomar el resultado como una transcripción segura de 1400 a. C.',
    points: [
      'El perfil melódico: movimiento conjunto, fórmulas breves y clara sensación modal.',
      'La repetición ornamental y la ausencia de una dirección armónica tonal fuerte.',
      'Cómo una fuente iconográfica puede convertirse en hipótesis sonora.',
      'Qué partes de lo que oímos son dato arqueológico y cuáles son decisión del intérprete moderno.'
    ]
  },
  {
    index: '2',
    composer: 'De Organographia',
    title: 'Isis Sistrum Rhythm, after Apuleius',
    subtitle: 'Reconstrucción breve de ritmo ritual de sistro (0:31) a partir de Apuleyo (época romana)',
    performer: 'Ensemble De Organographia (Music of the Ancient Sumerians, Egyptians & Greeks)',
    anthology: 'Apuleyo (Metamorfosis) / Culto de Isis y Hathor',
    links: [
      { label: 'Escuchar en YouTube (De Organographia – Isis Sistrum Rhythm)', url: 'https://www.youtube.com/watch?v=599YEae4DYA' }
    ],
    teacher_note: 'Sustitución más segura para el aula: reconstruye un ritmo de sistro asociado a Isis a partir de Apuleyo, permitiendo trabajar el instrumento y su función ritual sin presentar como auténtica una melodía no conservada.',
    points: [
      'El timbre metálico y brillante del sistro (sejem/sesheshet) producido por el movimiento de sus varillas móviles.',
      'La función del pulso y del gesto repetido más que el desarrollo de una melodía.',
      'La relación del sistro y el menat con el culto ritual y divinidades como Hathor e Isis.',
      'La diferencia entre un ritmo reconstruido desde una fuente literaria tardía y una música faraónica conservada.'
    ]
  },
  {
    index: '3',
    composer: 'Descarte metodológico razonado',
    title: 'Canto colectivo de labor (Descartada deliberadamente)',
    subtitle: 'Módulo de análisis crítico de fuentes iconográficas en lugar de audición especulativa',
    performer: 'Sin grabación musical: rigor epistemológico en el aula',
    anthology: 'Escenas parietales de trabajo agrícola y navegación (Tumbas del Reino Antiguo y Nuevo)',
    links: [],
    teacher_note: 'Descartada como audición: existen escenas y textos que sugieren canto durante el trabajo, pero no conservamos melodía ni ritmo que permitan identificar con rigor un ejemplo faraónico. Se trabaja en el aula como análisis crítico de fuentes iconográficas.',
    points: [
      'Observar una escena parietal de trabajo colectivo (siega, molienda o remeros en el Nilo).',
      'Describir qué información objetiva aporta la imagen y separar lo que sabemos de lo que inferimos.',
      'Comprender por qué la ausencia de notación exige cautela metodológica frente a audiciones especulativas.'
    ]
  },
  {
    index: '4',
    composer: 'Grabación histórica BBC (1939)',
    title: "King Tutankhamun's Trumpets (Trompetas de Tutankamón)",
    subtitle: 'Instrumentos originales (c. 1323 a. C.); interpretación de James Tappern (El Cairo)',
    performer: 'James Tappern (trompetista militar), retransmisión oficial BBC El Cairo (1939)',
    anthology: 'Tumba KV62 de Tutankamón / Museo de El Cairo / BBC & Society of Antiquaries',
    links: [
      { label: 'Escuchar en YouTube (King Tutankhamun\'s Trumpets – Grabación BBC 1939)', url: 'https://www.youtube.com/watch?v=Qt9AyV3hnlc' },
      { label: 'BBC Ghost Music (Documental sobre las trompetas)', url: 'https://www.bbc.co.uk/programmes/b010dp0s' }
    ],
    teacher_note: 'Audición más excepcional del conjunto: en 1939 se hicieron sonar dos trompetas auténticas de la tumba de Tutankamón. Documenta el sonido posible de esos objetos, pero con técnica militar moderna del siglo XX y boquilla adaptada.',
    points: [
      'El timbre directo, metálico y de gran proyección al aire libre.',
      'La limitada disponibilidad de alturas sonoras, propia de un tubo natural sin válvulas ni llaves.',
      'La emisión de sonidos relacionados con la serie de armónicos naturales.',
      'La diferencia crucial entre hacer sonar un instrumento antiguo y reconstruir su práctica musical original.'
    ]
  }
];

function getRunListenings(run) {
  if (is15thCenturyPolyphony(run)) {
    return POLYPHONY_LISTENINGS;
  }
  if (isAncientEgypt(run)) {
    return EGYPT_LISTENINGS;
  }
  const criteria = run.request?.pedagogy?.teacher_criteria || '';
  const ytRegex = /\[([^\]]+)\]\((https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)[\w\-_&?=]+)\)/gi;
  const matches = [...criteria.matchAll(ytRegex)];
  if (matches.length > 0) {
    return matches.map((m, idx) => ({
      index: idx + 1,
      composer: 'Referencia aportada por el profesor',
      title: m[1],
      subtitle: 'Grabación de apoyo indicada en los criterios docentes',
      anthology: 'Material audiovisual aportado por el profesor',
      links: [{ label: m[1], url: m[2] }],
      teacher_note: 'Enlace de audición suministrado directamente en los criterios docentes.',
      points: [
        'Audición atenta del fragmento musical seleccionado.',
        'Vinculación de los rasgos audibles con los contenidos de la sesión.'
      ]
    }));
  }
  return null;
}

function renderListeningCardItem(l, isProposal = false) {
  const linksHTML = (l.links || []).map(link => `
    <a href="${e(link.url)}" target="_blank" rel="noopener noreferrer" class="yt-link-btn" title="Abrir audición en YouTube">
      <svg class="icon yt-icon" viewBox="0 0 24 24" width="16" height="16" style="vertical-align:-3px;margin-right:4px;"><path fill="#dc2626" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.5 12 3.5 12 3.5s-7.505 0-9.377.55a3.016 3.016 0 0 0-2.122 2.136C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.55 9.376.55 9.376.55s7.505 0 9.377-.55a3.016 3.016 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
      <span>${e(link.label)}</span>
      <svg class="icon" viewBox="0 0 25 25" style="width:12px;height:12px;margin-left:4px;opacity:0.8"><path d="M13 4h7v7m0-7L10 14M9 4H4v16h16v-5" stroke="currentColor" fill="none" stroke-width="2"/></svg>
    </a>
  `).join(' ');

  return `
    <div class="listening-card ${isProposal ? 'proposal-listening-card' : ''}">
      <div class="listening-head">
        <span class="listening-badge">AUDICIÓN ${l.index}</span>
        <div>
          <strong>${e(l.composer ? l.composer + ' · ' : '')}${e(l.title)}</strong>
          ${l.subtitle ? `<small>${e(l.subtitle)}</small>` : ''}
        </div>
      </div>
      ${l.performer ? `<div class="listening-performer">🎙 <strong>Grabación de referencia:</strong> ${e(l.performer)}</div>` : ''}
      ${linksHTML ? `<div class="listening-links">${linksHTML}</div>` : ''}
      ${l.teacher_note ? `<div class="listening-teacher-note">💡 <strong>Criterio y comentario docente:</strong> ${e(l.teacher_note)}</div>` : ''}
      ${l.anthology ? `<div class="listening-anthology">📚 ${e(l.anthology)}</div>` : ''}
      <div class="listening-points">
        <strong>Puntos clave de escucha activa:</strong>
        <ul>
          ${(l.points || []).map(pt => `<li>${e(pt)}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;
}

function renderEgyptListeningsHTML(isProposal = false) {
  return EGYPT_LISTENINGS.map(l => renderListeningCardItem(l, isProposal)).join('');
}

function renderStudentDiscographySection(run) {
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : isEgypt ? EGYPT_LISTENINGS : getRunListenings(run);
  if (!listenings || !listenings.length) return '';
  return `
    <section class="student-section section-discography">
      <div class="student-section-header">
        <span class="student-section-number">07</span>
        <div>
          <h2>Discografía recomendada y enlaces directos de audición</h2>
          <p class="student-section-intro">Relación detallada de grabaciones de referencia con enlaces directos a YouTube y comentarios analíticos del profesor para el trabajo autónomo del alumnado.</p>
        </div>
      </div>
      <div class="table-wrapper">
        <table class="discography-table">
          <thead>
            <tr>
              <th style="width: 25%;">Obra y movimientos</th>
              <th style="width: 25%;">Grabación e intérpretes</th>
              <th style="width: 24%;">Enlaces a YouTube</th>
              <th style="width: 26%;">Comentario didáctico</th>
            </tr>
          </thead>
          <tbody>
            ${listenings.map(item => `
              <tr>
                <td><strong>${e(item.composer || '')}</strong><br><em>${e(item.title)}</em>${item.subtitle ? `<br><small class="muted-small">${e(item.subtitle)}</small>` : ''}</td>
                <td><span class="disco-performer">🎙 ${e(item.performer || 'Grabación recomendada')}</span></td>
                <td>
                  <div class="disco-links">
                    ${(item.links && item.links.length > 0) ? (item.links.map(l => `
                      <a href="${e(l.url)}" target="_blank" rel="noopener noreferrer" class="yt-link-btn yt-link-table">
                        <svg class="icon yt-icon" viewBox="0 0 24 24" width="14" height="14" style="vertical-align:-2px;margin-right:2px;"><path fill="#dc2626" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.5 12 3.5 12 3.5s-7.505 0-9.377.55a3.016 3.016 0 0 0-2.122 2.136C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.55 9.376.55 9.376.55s7.505 0 9.377-.55a3.016 3.016 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
                        <span>${e(l.label)}</span>
                      </a>
                    `).join('')) : '<span class="muted-small"><em>(Descarte deliberado · Análisis iconográfico)</em></span>'}
                  </div>
                </td>
                <td><small class="disco-note">${e(item.teacher_note || 'Audición de referencia para la unidad.')}</small></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function resultHTML(run) {
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
function teacherWorkedExample(run){
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
function bibliographyHTML(run) {
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
    const location = l.kind === 'pdf_page' ? `pág. ${l.pdf_page_index}` : `líneas ${l.line_start}–${l.line_end}`;
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
function sourcesModal(run){
  const appendix=bibliographyHTML(run);
  modal('Anexo documental',`${appendix||'<p>No hay citas documentales disponibles para esta propuesta.</p>'}<div class="dialog-actions"><button class="button" data-download-sources="${e(run.id)}">${icon('download')}Descargar anexo</button><button class="button primary" type="button" data-action="close-dialog">Volver a la propuesta</button></div>`);
}
function evidenceHTML(run,citations) {
  let content='';
  for (const citation of citations||[]) {const source=run.evidence.find(s=>s.source_id===citation.source_id);if(!source)continue;const m=source.metadata,l=source.locator;const location=l.kind==='pdf_page'?`pág. ${l.pdf_page_index}`:`líneas ${l.line_start}–${l.line_end}`;
    content+=`<details class="evidence"><summary>${source.category==='profesor'?'Material propio':'Fuente documental'} · ${e(m.title)} · ${e(location)}</summary><blockquote>${e(citation.quote)}</blockquote><p>${e(m.authors?.join(', ') || 'Sin autor')}${m.year?' · '+e(m.year):''}</p><button class="button ghost small" data-document="${e(source.document_id)}">Ver fuente ${icon('arrow')}</button></details>`;
  }
  return content;
}
function visualHTML(run,visual) {
  const type=['sequence','relationship','table'].includes(visual.type)?visual.type:'relationship';
  const items=(visual.items||[]).map(item=>`<div class="visual-node"><strong>${e(item.label)}</strong><span>${e(item.detail)}</span></div>`).join('');
  return `<section class="source-visual source-visual-${type}" aria-label="${e(visual.title)}"><span class="eyebrow">ESQUEMA DOCUMENTADO</span><h3>${e(visual.title)}</h3><div class="visual-canvas">${items}</div><p class="visual-caption">${e(visual.caption)}</p></section>`;
}
function recordModal(runId, run) {
  const ctx = run?.request?.pedagogy;
  const today = new Date().toISOString().slice(0,10);
  const groupOptions = (state.config.groups||[]).map(g=>option(g.id, g.name, ctx?.group?.id)).join('');
  modal('Registrar clase impartida',
    `<p class="muted-small">Anota qué se impartió de verdad. Esta información alimenta la memoria del asistente para las próximas sesiones.</p>
    <form data-form="record" ${runId?`data-run="${e(runId)}"`:''}>
      <div class="field"><label class="label" for="rec-group">Grupo</label><select id="rec-group" name="group_id" required>${groupOptions}</select></div>
      <div class="field"><label class="label" for="rec-date">Fecha de la sesión</label><input id="rec-date" name="session_date" type="date" value="${e(today)}" required></div>
      <div class="field"><label class="label" for="rec-duration">Duración real (minutos)</label><input id="rec-duration" name="duration_minutes" type="number" min="1" max="480" value="${e(ctx?.duration_minutes||50)}" required></div>
      <div class="field"><label class="label" for="rec-topic">Qué se impartió</label><textarea id="rec-topic" name="topic" maxlength="2000" rows="3" required placeholder="Tema o contenido impartido realmente en la sesión…">${e(run?.request?.question||'')}</textarea></div>
      <div class="field"><label class="label" for="rec-notes">Notas de la sesión (opcional)</label><textarea id="rec-notes" name="notes" maxlength="4000" rows="2" placeholder="Asistencia, incidencias o cambios sobre lo planificado…"></textarea></div>
      <div class="feedback-fields"><div class="field"><label class="label" for="rec-worked">Qué funcionó</label><textarea id="rec-worked" name="what_worked" maxlength="2000" rows="2" placeholder="Actividad, explicación o dinámica que dio buen resultado…"></textarea></div><div class="field"><label class="label" for="rec-failed">Qué conviene ajustar</label><textarea id="rec-failed" name="what_failed" maxlength="2000" rows="2" placeholder="Dificultades, ritmo, materiales o puntos que revisar…"></textarea></div><div class="field"><label class="label" for="rec-next">Para la próxima sesión</label><textarea id="rec-next" name="next_session_note" maxlength="2000" rows="2" placeholder="Por dónde continuar y qué conviene preparar…"></textarea></div></div>
      <div class="form-error" role="alert"></div>
      <div class="dialog-actions">
        <button class="button ghost" type="button" data-action="close-dialog">Cancelar</button>
        <button class="button primary" type="submit">${icon('record')}Guardar registro</button>
      </div>
    </form>`
  );
}
function feedbackModal(session=null){
  const today=state.agenda?.date||new Date().toISOString().slice(0,10),group=session?.group_id||state.config.groups[0]?.id||'';
  modal('Feedback de la clase',`<p class="muted-small">Tu valoración se guarda en el diario y se incorpora al contexto de las próximas propuestas del grupo.</p><form data-form="feedback"><div class="form-row"><div class="field"><label class="label" for="fb-group">Grupo</label><select id="fb-group" name="group_id" required>${state.config.groups.map(item=>option(item.id,item.name,group)).join('')}</select></div><div class="field"><label class="label" for="fb-date">Fecha</label><input class="input" id="fb-date" name="session_date" type="date" value="${e(today)}" required></div><div class="field"><label class="label" for="fb-duration">Duración real</label><input class="input" id="fb-duration" name="duration_minutes" type="number" min="1" max="480" value="${e(session?.duration_minutes||60)}" required></div></div><div class="field"><label class="label" for="fb-topic">Contenido impartido</label><input class="input" id="fb-topic" name="topic" maxlength="2000" required placeholder="Qué se trabajó realmente en el aula"></div><div class="field"><label class="label" for="fb-worked">Qué funcionó</label><textarea id="fb-worked" name="what_worked" maxlength="2000" rows="3" placeholder="Explicaciones, ejercicios o dinámicas eficaces…"></textarea></div><div class="field"><label class="label" for="fb-failed">Qué conviene ajustar</label><textarea id="fb-failed" name="what_failed" maxlength="2000" rows="3" placeholder="Dificultades, tiempo, nivel o materiales…"></textarea></div><div class="field"><label class="label" for="fb-next">Para la próxima sesión</label><textarea id="fb-next" name="next_session_note" maxlength="2000" rows="3" placeholder="Qué continuar, reforzar o preparar…"></textarea></div><div class="field"><label class="label" for="fb-notes">Otras notas (opcional)</label><textarea id="fb-notes" name="notes" maxlength="4000" rows="2"></textarea></div><div class="form-error" role="alert"></div><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button primary" type="submit">${icon('record')}Guardar en el diario</button></div></form>`);
}
async function existingFeedbackModal(id){
  const record=await api('/records/'+encodeURIComponent(id)),fb=record.feedback||{};
  modal('Feedback de la clase',`<div class="record-summary"><span>${e(record.session_date)} · ${record.duration_minutes} min</span><h3>${e(record.topic)}</h3></div><form data-form="feedback" data-record="${e(id)}"><div class="field"><label class="label" for="fb-worked">Qué funcionó</label><textarea id="fb-worked" name="what_worked" maxlength="2000" rows="3">${e(fb.what_worked||'')}</textarea></div><div class="field"><label class="label" for="fb-failed">Qué conviene ajustar</label><textarea id="fb-failed" name="what_failed" maxlength="2000" rows="3">${e(fb.what_failed||'')}</textarea></div><div class="field"><label class="label" for="fb-next">Para la próxima sesión</label><textarea id="fb-next" name="next_session_note" maxlength="2000" rows="3">${e(fb.next_session_note||'')}</textarea></div><div class="form-error" role="alert"></div><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button primary" type="submit">Guardar cambios</button></div></form>`);
}
function modal(title, content) {dialog.classList.remove('student-dialog');$('#dialog-content').innerHTML=`<div class="dialog-head"><h2 id="dialog-title">${title}</h2><button class="icon-button" data-action="close-dialog" aria-label="Cerrar">${icon('close')}</button></div><div class="dialog-body"><div class="form-error" role="alert"></div>${content}</div>`;if(!dialog.open)dialog.showModal();}

function renderStaffSvg(type) {
  const lines = [8, 14, 20, 26, 32].map(y => `<line x1="24" y1="${y}" x2="315" y2="${y}" stroke="#cbd5e1" stroke-width="1.2"/>`).join('');
  let content = '';
  switch(type) {
    case 'superius_cf':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#475569">𝄞</text>
        <ellipse cx="48" cy="20" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 48 20)"/><line x1="52" y1="20" x2="52" y2="6" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="78" cy="14" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 78 14)"/><line x1="82" y1="14" x2="82" y2="2" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="108" cy="17" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 108 17)"/><line x1="112" y1="17" x2="112" y2="4" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="138" cy="23" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 138 23)"/><line x1="142" y1="23" x2="142" y2="9" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="172" cy="20" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 172 20)"/><line x1="176" y1="20" x2="176" y2="6" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="206" cy="14" rx="4.5" ry="3.5" fill="#1e293b" transform="rotate(-15 206 14)"/><line x1="210" y1="14" x2="210" y2="2" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="240" cy="8" rx="5" ry="4" fill="#ffffff" stroke="#1e293b" stroke-width="1.8" transform="rotate(-15 240 8)"/><line x1="244" y1="8" x2="244" y2="-4" stroke="#1e293b" stroke-width="1.5"/>
        <ellipse cx="280" cy="14" rx="5.5" ry="4" fill="#ffffff" stroke="#1e293b" stroke-width="2"/>
      `;
      break;
    case 'altus_cf':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#475569">𝄡</text>
        <ellipse cx="54" cy="26" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 54 26)"/><line x1="58" y1="26" x2="58" y2="12" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="94" cy="20" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 94 20)"/><line x1="98" y1="20" x2="98" y2="6" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="134" cy="23" rx="4.5" ry="3.5" fill="#334155" transform="rotate(-15 134 23)"/><line x1="138" y1="23" x2="138" y2="9" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="180" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/>
        <ellipse cx="230" cy="20" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/>
        <ellipse cx="280" cy="23" rx="5.5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="2"/>
      `;
      break;
    case 'tenor_cf':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#b45309">𝄡</text>
        <rect x="55" y="16" width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="71" y1="16" x2="71" y2="35" stroke="#b45309" stroke-width="2.2"/>
        <rect x="135" y="13" width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="151" y1="13" x2="151" y2="32" stroke="#b45309" stroke-width="2.2"/>
        <rect x="215" y="19" width="16" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.2" rx="1.5"/><line x1="231" y1="19" x2="231" y2="38" stroke="#b45309" stroke-width="2.2"/>
        <rect x="280" y="16" width="20" height="8" fill="#ffffff" stroke="#b45309" stroke-width="2.5" rx="1.5"/><line x1="300" y1="16" x2="300" y2="35" stroke="#b45309" stroke-width="2.2"/>
      `;
      break;
    case 'bassus_cf':
      content = `
        <text x="6" y="24" font-size="18" font-family="serif" fill="#475569">𝄢</text>
        <ellipse cx="60" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="56" y1="26" x2="56" y2="40" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="120" cy="32" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="116" y1="32" x2="116" y2="44" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="180" cy="26" rx="5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="1.8"/><line x1="176" y1="26" x2="176" y2="40" stroke="#334155" stroke-width="1.5"/>
        <ellipse cx="250" cy="20" rx="5.5" ry="4" fill="#ffffff" stroke="#334155" stroke-width="2"/>
      `;
      break;
    case 'paraphrase_s':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#dc2626">𝄞</text>
        <rect x="42" y="3" width="76" height="30" fill="rgba(239, 68, 68, 0.12)" stroke="#ef4444" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="47" y="12" font-size="8" font-weight="bold" fill="#dc2626">Fragmento A</text>
        <ellipse cx="62" cy="20" rx="4" ry="3" fill="#dc2626"/><ellipse cx="82" cy="14" rx="4" ry="3" fill="#dc2626"/><ellipse cx="102" cy="17" rx="4" ry="3" fill="#dc2626"/>
        <ellipse cx="150" cy="14" rx="4" ry="3" fill="#334155"/><ellipse cx="180" cy="20" rx="4" ry="3" fill="#334155"/><ellipse cx="230" cy="26" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      `;
      break;
    case 'paraphrase_a':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#d97706">𝄡</text>
        <rect x="95" y="3" width="76" height="30" fill="rgba(245, 158, 11, 0.12)" stroke="#f59e0b" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="100" y="12" font-size="8" font-weight="bold" fill="#b45309">↳ Imitación</text>
        <ellipse cx="115" cy="26" rx="4" ry="3" fill="#d97706"/><ellipse cx="135" cy="20" rx="4" ry="3" fill="#d97706"/><ellipse cx="155" cy="23" rx="4" ry="3" fill="#d97706"/>
        <ellipse cx="200" cy="20" rx="4" ry="3" fill="#334155"/><ellipse cx="240" cy="14" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      `;
      break;
    case 'paraphrase_t':
      content = `
        <text x="6" y="25" font-size="18" font-family="serif" fill="#059669">𝄡</text>
        <rect x="145" y="3" width="76" height="30" fill="rgba(16, 185, 129, 0.12)" stroke="#10b981" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="150" y="12" font-size="8" font-weight="bold" fill="#047857">↳ Imitación</text>
        <ellipse cx="165" cy="20" rx="4" ry="3" fill="#059669"/><ellipse cx="185" cy="14" rx="4" ry="3" fill="#059669"/><ellipse cx="205" cy="17" rx="4" ry="3" fill="#059669"/>
        <ellipse cx="250" cy="20" rx="4.5" ry="3.5" fill="#ffffff" stroke="#334155" stroke-width="1.5"/>
      `;
      break;
    case 'paraphrase_b':
      content = `
        <text x="6" y="24" font-size="18" font-family="serif" fill="#2563eb">𝄢</text>
        <rect x="195" y="3" width="76" height="30" fill="rgba(37, 99, 235, 0.12)" stroke="#2563eb" stroke-width="1.2" stroke-dasharray="3,2" rx="4"/>
        <text x="200" y="12" font-size="8" font-weight="bold" fill="#1d4ed8">↳ Imitación</text>
        <ellipse cx="215" cy="26" rx="4" ry="3" fill="#2563eb"/><ellipse cx="235" cy="20" rx="4" ry="3" fill="#2563eb"/><ellipse cx="255" cy="23" rx="4" ry="3" fill="#2563eb"/>
      `;
      break;
    case 'motto':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#6366f1">𝄞</text>
        <circle cx="50" cy="20" r="4.2" fill="#6366f1"/><line x1="54" y1="20" x2="54" y2="7" stroke="#6366f1" stroke-width="1.5"/>
        <circle cx="85" cy="14" r="4.2" fill="#6366f1"/><line x1="89" y1="14" x2="89" y2="2" stroke="#6366f1" stroke-width="1.5"/>
        <circle cx="120" cy="17" r="4.2" fill="#6366f1"/><line x1="124" y1="17" x2="124" y2="4" stroke="#6366f1" stroke-width="1.5"/>
        <circle cx="155" cy="20" r="4.2" fill="#6366f1"/><line x1="159" y1="20" x2="159" y2="7" stroke="#6366f1" stroke-width="1.5"/>
        <text x="180" y="22" font-size="10" font-weight="bold" fill="#4338ca">Kyrie / Gloria / Credo...</text>
      `;
      break;
    case 'cadence':
      content = `
        <text x="6" y="27" font-size="22" font-family="serif" fill="#0f766e">𝄞</text>
        <ellipse cx="55" cy="23" rx="4" ry="3" fill="#0f766e"/><ellipse cx="55" cy="14" rx="4" ry="3" fill="#0f766e"/>
        <text x="80" y="21" font-size="9" fill="#64748b">➔ 6ª a 8ª (Landini) ➔</text>
        <ellipse cx="200" cy="26" rx="5.5" ry="4" fill="#ffffff" stroke="#0f766e" stroke-width="2"/>
        <ellipse cx="200" cy="8" rx="5.5" ry="4" fill="#ffffff" stroke="#0f766e" stroke-width="2"/>
        <text x="216" y="20" font-size="8.5" font-weight="bold" fill="#0f766e">8ª sin 3ª</text>
      `;
      break;
    default:
      content = `<text x="6" y="27" font-size="22" font-family="serif" fill="#64748b">𝄞</text>`;
  }
  return `<svg class="staff-svg" viewBox="0 0 320 38" preserveAspectRatio="none">${lines}${content}</svg>`;
}

function renderStudentInfographic(run) {
  return `
    <div class="infographic-poster">
      <div class="infographic-main-head">
        <div class="info-tag-row">
          <span class="info-badge">POLIFONÍA DEL SIGLO XV</span>
          <span class="info-badge-sub">MODELOS DE MISA Y TÉCNICAS COMPOSITIVAS</span>
        </div>
        <h2>ARTE, FE Y MÚSICA EN EL RENACIMIENTO</h2>
        <p class="info-subtitle">Del material preexistente a la misa cíclica · Dufay · Binchois · Ockeghem · Busnois · Josquin</p>
      </div>

      <div class="infographic-grid">
        <!-- PANEL 1: DISTRIBUCIÓN VOCÁLICA Y EJEMPLOS DE NOTACIÓN -->
        <div class="infographic-panel panel-left">
          <div class="panel-header-bar">
            <span class="panel-number">1</span>
            <div>
              <h3>DISTRIBUCIÓN VOCÁLICA Y EJEMPLOS DE NOTACIÓN</h3>
              <span class="panel-sub">Modelos de misa del siglo XV · Una melodía, tres caminos de creación</span>
            </div>
          </div>

          <!-- MODELO 1: MISA DE CANTUS FIRMUS -->
          <div class="model-block">
            <div class="model-header-row">
              <div class="model-title-group">
                <span class="model-circle-badge">1</span>
                <div>
                  <h4>MISA DE CANTUS FIRMUS</h4>
                  <small class="model-meta">Estructura rígida</small>
                </div>
              </div>
              <span class="model-quote">«La melodía permanece fija como eje de la misa»</span>
            </div>

            <div class="model-body-grid">
              <div class="voice-staves-box">
                <div class="voice-row"><span class="voice-tag">Superius (Soprano)</span>${renderStaffSvg('superius_cf')}</div>
                <div class="voice-row"><span class="voice-tag">Altus (Contralto)</span>${renderStaffSvg('altus_cf')}</div>
                <div class="voice-row voice-tenor-highlight">
                  <span class="voice-tag voice-tenor-badge">Tenor (Cantus Firmus)</span>
                  ${renderStaffSvg('tenor_cf')}
                </div>
                <div class="voice-row"><span class="voice-tag">Bassus (Bajo)</span>${renderStaffSvg('bassus_cf')}</div>
              </div>

              <div class="model-side-info">
                <div class="model-chars-card">
                  <strong>CARACTERÍSTICAS</strong>
                  <ul>
                    <li>La melodía preexistente se presenta en valores largos (aumentación).</li>
                    <li>Normalmente situada en el Tenor.</li>
                    <li>Las otras voces desarrollan contrapunto libre o imitativo.</li>
                    <li>Estructura solemne y estable.</li>
                  </ul>
                </div>
                <div class="model-example-card">
                  <span class="ex-badge">EJEMPLO</span>
                  <strong>L'homme armé</strong>
                  <p>Melodía del cantus firmus en el Tenor (en valores de longa y máxima).</p>
                </div>
              </div>
            </div>
          </div>

          <!-- MODELO 2: MISA DE PARÁFRASIS -->
          <div class="model-block">
            <div class="model-header-row">
              <div class="model-title-group">
                <span class="model-circle-badge accent-amber">2</span>
                <div>
                  <h4>MISA DE PARÁFRASIS</h4>
                  <small class="model-meta">Estructura fluida e imitativa</small>
                </div>
              </div>
              <span class="model-quote">«La melodía viaja, se adorna y se transforma»</span>
            </div>

            <div class="model-body-grid">
              <div class="voice-staves-box">
                <div class="voice-row"><span class="voice-tag">Superius (Soprano)</span>${renderStaffSvg('paraphrase_s')}</div>
                <div class="voice-row"><span class="voice-tag">Altus (Contralto)</span>${renderStaffSvg('paraphrase_a')}</div>
                <div class="voice-row"><span class="voice-tag">Tenor</span>${renderStaffSvg('paraphrase_t')}</div>
                <div class="voice-row"><span class="voice-tag">Bassus (Bajo)</span>${renderStaffSvg('paraphrase_b')}</div>
              </div>

              <div class="model-side-info">
                <div class="model-chars-card">
                  <strong>CARACTERÍSTICAS</strong>
                  <ul>
                    <li>La melodía original se mantiene reconocible, pero con adornos (glosas).</li>
                    <li>Se reparte entre todas las voces mediante imitación.</li>
                    <li>Hay mayor libertad rítmica y melódica.</li>
                    <li>Textura más dinámica y expresiva.</li>
                  </ul>
                </div>
                <div class="model-example-card">
                  <span class="ex-badge">EJEMPLO</span>
                  <strong>Pange Lingua</strong>
                  <p>Fragmento del himno gregoriano con ornamentos y tratamiento imitativo entre voces.</p>
                </div>
              </div>
            </div>
          </div>

          <!-- MODELO 3: MISA PARODIA / IMITACIÓN -->
          <div class="model-block">
            <div class="model-header-row">
              <div class="model-title-group">
                <span class="model-circle-badge accent-green">3</span>
                <div>
                  <h4>MISA PARODIA / IMITACIÓN</h4>
                  <small class="model-meta">Estructura en bloque</small>
                </div>
              </div>
              <span class="model-quote">«Se toma el tejido polifónico completo y se reelabora»</span>
            </div>

            <div class="model-body-grid">
              <div class="parody-diagram-box">
                <div class="parody-box-side original-piece">
                  <span class="parody-box-title">Obra original (Motete / Chanson a 4 voces)</span>
                  <div class="p-voice v1">Voz 1 (Superius)</div>
                  <div class="p-voice v2">Voz 2 (Altus)</div>
                  <div class="p-voice v3">Voz 3 (Tenor)</div>
                  <div class="p-voice v4">Voz 4 (Bassus)</div>
                </div>

                <div class="parody-arrow-center">
                  <span>↳ Se copia, se adapta y se transforma ➔</span>
                </div>

                <div class="parody-box-side new-mass">
                  <span class="parody-box-title">Misa nueva (Kyrie, Gloria, Credo...)</span>
                  <div class="p-voice v1">Superius</div>
                  <div class="p-voice v2">Altus</div>
                  <div class="p-voice v3">Tenor</div>
                  <div class="p-voice v4">Bassus</div>
                </div>
              </div>

              <div class="model-side-info">
                <div class="model-chars-card">
                  <strong>CARACTERÍSTICAS</strong>
                  <ul>
                    <li>Se toma la obra original completa (las cuatro voces).</li>
                    <li>Puede mantenerse el orden, invertirse o variar el ritmo.</li>
                    <li>Alternancia de texturas: contrapunto imitativo y pasajes más homofónicos.</li>
                    <li>Inserción de nuevos motivos y adaptaciones al texto litúrgico.</li>
                  </ul>
                </div>
                <div class="model-example-card">
                  <span class="ex-badge">EJEMPLO</span>
                  <strong>Je ne vis oncques la / Se la face ay pale</strong>
                  <p>Inicio en imitación de las cuatro voces de la chanson en el Kyrie de la misa.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- PANEL 2: TÉCNICAS DE COMPOSICIÓN DEL SIGLO XV -->
        <div class="infographic-panel panel-right">
          <div class="panel-header-bar accent-wine">
            <span class="panel-number">2</span>
            <div>
              <h3>TÉCNICAS DE COMPOSICIÓN DEL SIGLO XV</h3>
              <span class="panel-sub">Del material preexistente a la misa cíclica · Tradición · Invención · Unidad</span>
            </div>
          </div>

          <!-- PASO 1 -->
          <div class="step-card">
            <div class="step-title-row">
              <span class="step-badge">PASO 1</span>
              <div>
                <strong>SELECCIÓN DEL MATERIAL PREEXISTENTE</strong>
                <p>El compositor parte de una melodía o de una obra ya conocida.</p>
              </div>
            </div>

            <div class="source-branches-grid">
              <div class="source-branch-card sacred">
                <div class="branch-head">
                  <span class="branch-icon">📜</span>
                  <div>
                    <strong>ORIGEN SACRO</strong>
                    <small>Canto Llano / Gregoriano</small>
                  </div>
                </div>
                <ul>
                  <li>Himnos</li>
                  <li>Antífonas</li>
                  <li>Cantos litúrgicos</li>
                </ul>
                <div class="branch-examples">
                  <em>Ejemplos:</em> Ave Maris Stella, Pange Lingua, Veni Creator Spiritus
                </div>
              </div>

              <div class="source-branch-card secular">
                <div class="branch-head">
                  <span class="branch-icon">🪕</span>
                  <div>
                    <strong>ORIGEN PROFANO</strong>
                    <small>Chansons, canciones populares</small>
                  </div>
                </div>
                <ul>
                  <li>Chansons cortesanas</li>
                  <li>Canciones de tradición oral</li>
                  <li>Melodías de gran difusión</li>
                </ul>
                <div class="branch-examples">
                  <em>Ejemplos:</em> L'homme armé, Se la face ay pale, Belle, bonne, sage
                </div>
              </div>
            </div>
          </div>

          <div class="flow-arrow-down">⬇</div>

          <!-- PASO 2 -->
          <div class="step-card">
            <div class="step-title-row">
              <span class="step-badge">PASO 2</span>
              <div>
                <strong>ELECCIÓN DE LA TÉCNICA DE TRATAMIENTO</strong>
                <p>Diferentes maneras de integrar el material en la misa.</p>
              </div>
            </div>

            <div class="treatment-cols-grid">
              <div class="treatment-box col-cf">
                <div class="treatment-icon">𝄡</div>
                <strong>CANTUS FIRMUS</strong>
                <ul>
                  <li>Aislar la melodía.</li>
                  <li>Estirar las notas (aumentación).</li>
                  <li>Normalmente en el Tenor.</li>
                  <li>Otras voces en contrapunto libre.</li>
                  <li>Estructura solemne.</li>
                </ul>
                <div class="treatment-res">
                  <small>Resultado:</small>
                  <span>Melodía fija como columna vertebral de la obra.</span>
                </div>
              </div>

              <div class="treatment-box col-pf">
                <div class="treatment-icon">〰</div>
                <strong>PARÁFRASIS</strong>
                <ul>
                  <li>Alterar intervalos.</li>
                  <li>Añadir ornamentos (glosas).</li>
                  <li>Repartir la melodía entre todas las voces (imitación).</li>
                  <li>Mayor libertad rítmica y melódica.</li>
                  <li>Textura más fluida.</li>
                </ul>
                <div class="treatment-res">
                  <small>Resultado:</small>
                  <span>Melodía transformada y en constante movimiento.</span>
                </div>
              </div>

              <div class="treatment-box col-pd">
                <div class="treatment-icon">♫</div>
                <strong>PARODIA / IMITACIÓN</strong>
                <ul>
                  <li>Tomar el tejido polifónico completo.</li>
                  <li>Variar el orden, el ritmo o la textura.</li>
                  <li>Alternar contrapunto y pasajes homofónicos.</li>
                  <li>Inserción de nuevos motivos.</li>
                </ul>
                <div class="treatment-res">
                  <small>Resultado:</small>
                  <span>Una nueva obra a partir de todo el material original.</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flow-arrow-down">⬇</div>

          <!-- PASO 3 -->
          <div class="step-card">
            <div class="step-title-row">
              <span class="step-badge">PASO 3</span>
              <div>
                <strong>UNIFICACIÓN DE LA MISA CÍCLICA</strong>
                <p>Recursos para dar coherencia a toda la obra (Kyrie, Gloria, Credo, Sanctus, Agnus Dei).</p>
              </div>
            </div>

            <div class="unification-cards-grid">
              <div class="unification-card motto">
                <div class="u-card-head">
                  <strong>TÉCNICA DEL MOTTO</strong>
                  <small>(Motivo de cabeza)</small>
                </div>
                ${renderStaffSvg('motto')}
                <ul>
                  <li>Todas las partes de la misa comienzan con las mismas 3 o 4 notas o células.</li>
                  <li>Refuerza la unidad arquitectónica de la obra.</li>
                  <li>Muy utilizada por Dufay, Josquin y sus contemporáneos.</li>
                </ul>
              </div>

              <div class="unification-card cadence">
                <div class="u-card-head">
                  <strong>CADENCIAS RENACENTISTAS</strong>
                  <small>(Landini y borgoñonas)</small>
                </div>
                ${renderStaffSvg('cadence')}
                <ul>
                  <li>Uso de la cadencia de Landini o cadencias borgoñonas.</li>
                  <li>Caracterizadas por la octava sin tercera (conducción 6ª a 8ª).</li>
                  <li>Cierran secciones y articulan el texto litúrgico.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="infographic-footer-banner">
        <span>⚜ MISMA MÚSICA, NUEVOS SIGNIFICADOS: DEL MUNDO PROFANO AL ESPACIO SAGRADO ⚜</span>
        <span class="footer-composers">DUFAY · BINCHOIS · OCKEGHEM · BUSNOIS · JOSQUIN</span>
      </div>
    </div>
  `;
}

function switchEgyptTab(btn, tabId) {
  const poster = btn.closest('.egypt-infographic-poster');
  if (!poster) return;
  poster.querySelectorAll('.egypt-tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const p1 = poster.querySelector('#egypt-page-1');
  const p2 = poster.querySelector('#egypt-page-2');
  if (p1) p1.style.display = (tabId === 'egypt-page-1') ? 'block' : 'none';
  if (p2) p2.style.display = (tabId === 'egypt-page-2') ? 'block' : 'none';
}
window.switchEgyptTab = switchEgyptTab;

function renderEgyptInfographic(run) {
  return `
    <div class="infographic-poster egypt-infographic-poster">
      <!-- CONTROL DE PÁGINAS DE LÁMINAS -->
      <div class="egypt-page-tabs">
        <span class="egypt-tab-label">LÁMINAS DIDÁCTICAS · HISTORIA DA MÚSICA I:</span>
        <button type="button" class="egypt-tab-btn active" data-tab="egypt-page-1" onclick="switchEgyptTab(this, 'egypt-page-1')">
          📜 Lámina 1: Contexto, funciones y rasgos
        </button>
        <button type="button" class="egypt-tab-btn" data-tab="egypt-page-2" onclick="switchEgyptTab(this, 'egypt-page-2')">
          𓏢 Lámina 2: Instrumentos, práctica y fuentes
        </button>
      </div>

      <!-- ==================== PÁGINA 1 ==================== -->
      <div id="egypt-page-1" class="egypt-sheet">
        <header class="egypt-sheet-header">
          <div class="egypt-header-top">
            <div class="egypt-header-icon">𓏢</div>
            <div class="egypt-header-center">
              <h1>LA MÚSICA EN EL ANTIGUO EGIPTO</h1>
              <span class="egypt-sheet-sub">APUNTES PARA EL ALUMNADO</span>
              <span class="egypt-sheet-page-indicator">Página 1: contexto, funciones y rasgos generales</span>
            </div>
            <div class="egypt-header-side">
              <span>MÚSICA</span>
              <span>CULTURA</span>
              <span>MEMORIA</span>
              <span>SOCIEDAD</span>
            </div>
          </div>
        </header>

        <!-- SECCIÓN 1: MARCO HISTÓRICO -->
        <section class="egypt-block block-historical">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">1</span>
            <div>
              <h3>MARCO HISTÓRICO</h3>
              <small>Una civilización, un río, una música milenaria</small>
            </div>
          </div>
          <div class="egypt-hist-body">
            <div class="egypt-hist-text">
              <p>La civilización egipcia se desarrolló a lo largo del valle del Nilo, un entorno que favoreció la estabilidad, la agricultura y una gran continuidad cultural desde el Imperio Antiguo (hacia 2700 a. C.) hasta el período grecorromano (siglos IV a. C. – IV d. C.).</p>
              <p>La música está presente en tumbas, relieves, pinturas y textos, lo que demuestra su importancia en la vida religiosa, política, social y cotidiana. <strong>No se conservan partituras completas</strong> como en la tradición occidental, por lo que nuestro conocimiento procede principalmente de fuentes iconográficas (imágenes), textuales (inscripciones y textos) y arqueológicas (instrumentos, objetos y contextos materiales).</p>
            </div>
            <div class="egypt-nile-card">
              <div class="nile-illustration">
                <svg viewBox="0 0 200 80" class="nile-svg">
                  <path d="M0,60 Q50,45 100,55 T200,50 L200,80 L0,80 Z" fill="#38bdf8" opacity="0.35"/>
                  <path d="M0,65 Q50,55 100,62 T200,58 L200,80 L0,80 Z" fill="#0284c7" opacity="0.4"/>
                  <polygon points="120,48 145,15 170,48" fill="#e2b170"/>
                  <polygon points="145,15 170,48 185,48" fill="#c69251"/>
                  <polygon points="90,50 110,24 130,50" fill="#edd09b"/>
                  <path d="M30,58 Q32,35 34,22" stroke="#78350f" stroke-width="2" fill="none"/>
                  <circle cx="34" cy="22" r="8" fill="#15803d" opacity="0.8"/>
                  <path d="M22,59 Q25,40 26,28" stroke="#78350f" stroke-width="1.8" fill="none"/>
                  <circle cx="26" cy="28" r="7" fill="#166534" opacity="0.8"/>
                  <polygon points="65,56 75,56 80,52 60,52" fill="#78350f"/>
                  <polygon points="70,52 70,30 82,48" fill="#ffffff" stroke="#cbd5e1" stroke-width="0.8"/>
                </svg>
              </div>
              <p class="nile-quote">«El Nilo no solo dio vida a Egipto, también inspiró su música.»</p>
              <span class="nile-tag">EL NILO, UNA CIVILIZACIÓN DE MIL SONIDOS</span>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 2: FUNCIONES DE LA MÚSICA -->
        <section class="egypt-block block-functions">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">2</span>
            <div>
              <h3>FUNCIONES DE LA MÚSICA</h3>
              <small>Una misma música para los dioses, la muerte, la fiesta y la vida cotidiana</small>
            </div>
          </div>
          <div class="egypt-functions-grid">
            <!-- 1. RELIGIOSA Y RITUAL -->
            <div class="fn-card fn-religious">
              <div class="fn-header">
                <span class="fn-symbol">☥</span>
                <h4>RELIGIOSA Y RITUAL</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Templo y Ceremonia</div>
                <div class="scene-desc">Sacerdotisas con arpas e himnos sagrados</div>
              </div>
              <ul class="fn-points">
                <li>La música formaba parte del culto a los dioses, con himnos, cantos, procesiones y ceremonias en los templos.</li>
                <li>Divinidades como <strong>Hathor</strong> (alegría, música y danza) e <strong>Isis</strong> (magia y protección) estaban especialmente vinculadas a la música.</li>
                <li>Sacerdotisas y músicos del templo desempeñaban un papel fundamental en los rituales y ofrendas.</li>
              </ul>
              <div class="fn-footer">
                <span>𓆸 Hathor, señora de la música, la danza y la alegría.</span>
              </div>
            </div>

            <!-- 2. FUNERARIA -->
            <div class="fn-card fn-funerary">
              <div class="fn-header">
                <span class="fn-symbol">𓂀</span>
                <h4>FUNERARIA</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Viaje al Más Allá</div>
                <div class="scene-desc">Cortejo fúnebre, flautas y lamento ritual</div>
              </div>
              <ul class="fn-points">
                <li>La música estaba presente en los ritos funerarios, acompañando al difunto en su tránsito al Más Allá.</li>
                <li>Se interpretaban cantos y piezas instrumentales en ceremonias de enterramiento y ofrendas.</li>
                <li>Dimensión ritual y conmemorativa para honrar la memoria del difunto y desear su renacimiento eterno.</li>
              </ul>
              <div class="fn-footer">
                <span>𓂀 La música acompañaba al difunto en su viaje eterno.</span>
              </div>
            </div>

            <!-- 3. CORTESANA Y FESTIVA -->
            <div class="fn-card fn-court">
              <div class="fn-header">
                <span class="fn-symbol">🪷</span>
                <h4>CORTESANA Y FESTIVA</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Palacios y Banquetes</div>
                <div class="scene-desc">Arpistas, danzas y recepciones de la élite</div>
              </div>
              <ul class="fn-points">
                <li>La música sonaba en banquetes, recepciones y celebraciones de la élite y la familia real.</li>
                <li>Acompañaba la danza, el entretenimiento y la vida social en los palacios.</li>
                <li>Piezas instrumentales y canciones con una clara función lúdica y de prestigio cortesano.</li>
              </ul>
              <div class="fn-footer">
                <span>🪷 Música y danza en los jardines del palacio.</span>
              </div>
            </div>

            <!-- 4. POPULAR Y LABORAL -->
            <div class="fn-card fn-popular">
              <div class="fn-header">
                <span class="fn-symbol">🌾</span>
                <h4>POPULAR Y LABORAL</h4>
              </div>
              <div class="fn-scene">
                <div class="scene-badge">Campo y Talleres</div>
                <div class="scene-desc">Remeros, agricultores y canciones de faena</div>
              </div>
              <ul class="fn-points">
                <li>Canciones vinculadas al trabajo: agricultores, constructores o remeros en el río.</li>
                <li>Acompañaba las tareas colectivas, marcando el pulso rítmico y facilitando la coordinación.</li>
                <li>Presente en la vida cotidiana del pueblo: coplas de amor, juegos y celebraciones festivas.</li>
              </ul>
              <div class="fn-footer">
                <span>🌾 El ritmo también movía la vida diaria.</span>
              </div>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 3: RASGOS GENERALES -->
        <section class="egypt-block block-traits">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">3</span>
            <div>
              <h3>RASGOS GENERALES</h3>
              <small>Más que sonido: un lenguaje total</small>
            </div>
          </div>
          <div class="egypt-traits-body">
            <div class="traits-text">
              <p>En el Antiguo Egipto, <strong>la música, la poesía y la danza estaban estrechamente unidas</strong> y formaban parte de un mismo lenguaje artístico y simbólico. La música no se entendía solo como sonido acústico, sino como una experiencia integral que incluía gesto, movimiento corporal, palabra poética y contexto ceremonial.</p>
              <p>Se practicaba tanto el canto monódico como la interpretación instrumental. El ritmo y la expresividad gestual eran elementos esenciales. Las representaciones pictóricas muestran una <strong>participación femenina muy visible</strong>, tanto como cantantes, instrumentistas y bailarinas, como en roles rituales sacerdotales junto a músicos varones.</p>
            </div>
            <div class="traits-badge-card">
              <span class="traits-badge-title">ARTE TOTAL</span>
              <p>«Música, danza y palabra, unidas en armonía.»</p>
              <div class="traits-symbols">𓏢 · 𓀤 · 𓀥 · 𓀠</div>
            </div>
          </div>
        </section>

        <!-- SECCIONES 4 Y 5: IDEAS PARA ESTUDIAR Y VOCABULARIO BÁSICO -->
        <div class="egypt-dual-grid">
          <!-- SECCIÓN 4: IDEAS PARA ESTUDIAR -->
          <section class="egypt-block block-study-keys">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">4</span>
              <div>
                <h3>IDEAS PARA ESTUDIAR</h3>
                <small>Cinco claves para recordar</small>
              </div>
            </div>
            <ol class="study-keys-list">
              <li><span>1</span><div>Egipto tuvo una larga continuidad cultural desde el Imperio Antiguo hasta el período grecorromano.</div></li>
              <li><span>2</span><div>La música aparece en tumbas, relieves, pinturas y textos; no se conservan partituras completas.</div></li>
              <li><span>3</span><div>Cumplía cuatro funciones esenciales: religiosa, funeraria, cortesana y popular/laboral.</div></li>
              <li><span>4</span><div>Estaba unida a la poesía, la danza, el gesto ritual y el contexto ceremonial (arte total).</div></li>
              <li><span>5</span><div>Las mujeres tuvieron un papel protagonista y sumamente visible en la práctica musical.</div></li>
            </ol>
          </section>

          <!-- SECCIÓN 5: VOCABULARIO BÁSICO -->
          <section class="egypt-block block-vocabulary">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">5</span>
              <div>
                <h3>VOCABULARIO BÁSICO</h3>
                <small>Términos esenciales</small>
              </div>
            </div>
            <div class="vocab-table">
              <div class="vocab-row"><strong>Canto ritual</strong><span>Canto en contextos religiosos dirigido a los dioses, vinculado a ofrendas y liturgia.</span></div>
              <div class="vocab-row"><strong>Iconografía</strong><span>Representaciones visuales (pinturas, relieves) que documentan instrumentos y músicos.</span></div>
              <div class="vocab-row"><strong>Relieve</strong><span>Escultura mural en muros de templos o tumbas mostrando escenas musicales y rituales.</span></div>
              <div class="vocab-row"><strong>Aerófono</strong><span>Instrumento de viento por vibración de columna de aire (flauta, clarinete doble, trompeta).</span></div>
              <div class="vocab-row"><strong>Cordófono</strong><span>Instrumento de cuerda que suena al pulsar cuerdas tensadas (arpa arqueada, laúd, lira).</span></div>
              <div class="vocab-row"><strong>Idiófono</strong><span>Instrumento cuyo propio cuerpo vibra al agitarse o golpearse (sistro, menat, crótalos).</span></div>
            </div>
            <div class="egypt-remember-box">
              <span class="rem-icon">☥ 𓂀</span>
              <p><strong>Recuerda:</strong> en Egipto la música no era solo entretenimiento; también era religión, rito, memoria y representación social.</p>
            </div>
          </section>
        </div>

        <footer class="egypt-sheet-footer">
          <span>UN RÍO. UNA CIVILIZACIÓN. INFINITAS MELODÍAS.</span>
        </footer>
      </div>

      <!-- ==================== PÁGINA 2 ==================== -->
      <div id="egypt-page-2" class="egypt-sheet" style="display:none;">
        <header class="egypt-sheet-header">
          <div class="egypt-header-top">
            <div class="egypt-header-icon">𓏢</div>
            <div class="egypt-header-center">
              <h1>LA MÚSICA EN EL ANTIGUO EGIPTO</h1>
              <span class="egypt-sheet-sub">APUNTES PARA EL ALUMNADO</span>
              <span class="egypt-sheet-page-indicator">Página 2 de 2: instrumentos, práctica musical y fuentes</span>
            </div>
            <div class="egypt-header-side">
              <span>ORGANOLOGÍA</span>
              <span>PRÁCTICA</span>
              <span>FUENTES</span>
              <span>HISTORIA</span>
            </div>
          </div>
          <p class="egypt-banner-motto">La música, un legado sonoro de una gran civilización</p>
        </header>

        <!-- SECCIÓN 1: PRINCIPALES INSTRUMENTOS -->
        <section class="egypt-block block-instruments">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">1</span>
            <div>
              <h3>PRINCIPALES INSTRUMENTOS</h3>
              <small>Diversos timbres y funciones para la vida religiosa, social y cortesana</small>
            </div>
          </div>
          <div class="instruments-columns-grid">
            <!-- CORDÓFONOS -->
            <div class="inst-col inst-chordophones">
              <div class="inst-col-head">
                <h4>CORDÓFONOS</h4>
                <small>Cuerdas que se hacen sonar al ser pulsadas</small>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Arpa arqueada</strong><span class="inst-pill">Cortesano</span></div>
                <p>Muy representada en pinturas y relieves. Asociada a banquetes, templos y acompañamiento de cantos. Sonido claro y envolvente.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Laúd</strong><span class="inst-pill">Vida cotidiana</span></div>
                <p>Mástil largo y pequeña caja de resonancia. Común en escenas festivas del Imperio Nuevo. Timbre cálido y suave.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Lira</strong><span class="inst-pill">Religioso y profano</span></div>
                <p>Estructura en forma de U con cuerdas paralelas. Importada de Asia anterior y adoptada en ceremonias. Timbre brillante.</p>
              </div>
            </div>

            <!-- AERÓFONOS -->
            <div class="inst-col inst-aerophones">
              <div class="inst-col-head">
                <h4>AERÓFONOS</h4>
                <small>Viento que se transforma en sonido</small>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Flautas rectas</strong><span class="inst-pill">Caña / Madera</span></div>
                <p>Varios orificios tonales. Usadas en la corte, pastoreo y ritos religiosos. Producían sonoridades dulces y expresivas.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Clarinetes dobles</strong><span class="inst-pill">Lengüeta batiente</span></div>
                <p>Dos tubos de caña paralelos que sonaban simultáneamente. Sonido penetrante y nasal, empleado en procesiones y danzas.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Trompetas</strong><span class="inst-pill">Bronce / Plata</span></div>
                <p>Asociadas al ejército, audiencias del faraón y ritos solemnes (como las de Tutankamón). Toques sonoros para marcar momentos clave.</p>
              </div>
            </div>

            <!-- PERCUSIÓN E IDIÓFONOS -->
            <div class="inst-col inst-idiophones">
              <div class="inst-col-head">
                <h4>PERCUSIÓN E IDIÓFONOS</h4>
                <small>Golpeados, agitados o entrechocados</small>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Sistros</strong><span class="inst-pill">Sagrado (Hathor)</span></div>
                <p>Marco de metal con varillas y anillas sonajas. Al agitarse emitía un brillo metálico para ahuyentar el mal en procesiones.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Menat</strong><span class="inst-pill">Collar ritual</span></div>
                <p>Collar de cuentas con contrapeso tañido por sacerdotisas de Hathor. Producía un tintineo rítmico asociado a la fertilidad.</p>
              </div>
              <div class="inst-card">
                <div class="inst-name-row"><strong>Tambores y Crótalos</strong><span class="inst-pill">Pulso y Danza</span></div>
                <p>Tambores de mano o doble parche y palillos/crótalos entrechocados de madera o marfil para guiar el movimiento corporal.</p>
              </div>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 2: AGRUPACIONES Y PRÁCTICA MUSICAL -->
        <section class="egypt-block block-practice">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">2</span>
            <div>
              <h3>AGRUPACIONES Y PRÁCTICA MUSICAL</h3>
              <small>Música en solitario, en conjunto y en movimiento</small>
            </div>
          </div>
          <div class="practice-body-grid">
            <div class="practice-formats-list">
              <div class="pf-item"><strong>Solistas:</strong> Músicos y músicas actuando en solitario (arpistas y cantantes) en la corte y escenas íntimas.</div>
              <div class="pf-item"><strong>Pequeños conjuntos:</strong> Combinación habitual de cámara: arpa, flauta doble y percusión rítmica.</div>
              <div class="pf-item"><strong>Música y danza:</strong> La música guiaba la coreografía en banquetes y templos mediante sistros y tambores.</div>
              <div class="pf-item"><strong>Canto e instrumentos:</strong> Alternancia antifonal entre solista y coro, con instrumentos respondiendo a las frases.</div>
              <div class="pf-item"><strong>Coordinación y Quironimia:</strong> Gestualidad consciente de manos y miradas del director para marcar alturas y giros melódicos.</div>
            </div>
            <div class="practice-mural-card">
              <div class="mural-visual-box">
                <div class="mural-scene-tag">Fresco de la Tumba de Nebamun (c. 1350 a. C.)</div>
                <div class="mural-caption">Música, danza y coordinación entre intérpretes</div>
              </div>
              <div class="mural-quotes">
                <p>«La música acompaña la vida: en el templo, en la corte, en la fiesta y en el trabajo.»</p>
                <p>«Diferentes instrumentos, una misma finalidad: expresar, comunicar, celebrar y conectar con lo divino.»</p>
              </div>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 3: FUENTES PARA SU ESTUDIO -->
        <section class="egypt-block block-sources">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">3</span>
            <div>
              <h3>FUENTES PARA SU ESTUDIO</h3>
              <small>Un pasado que se reconstruye a través de sus huellas</small>
            </div>
          </div>
          <div class="egypt-sources-grid">
            <div class="src-card">
              <span class="src-icon">🎨</span>
              <strong>Iconografía</strong>
              <p>Pinturas murales, relieves en tumbas y templos, estatuas y cerámicas que revelan posturas, conjuntos y usos sociales.</p>
            </div>
            <div class="src-card">
              <span class="src-icon">📜</span>
              <strong>Textos</strong>
              <p>Himnos litúrgicos, inscripciones jeroglíficas, documentos administrativos y poemas que describen a los músicos.</p>
            </div>
            <div class="src-card">
              <span class="src-icon">🏺</span>
              <strong>Arqueología</strong>
              <p>Instrumentos conservados en ajuares funerarios secos (arpa, sistro, trompeta) que permiten analizar acústica y materiales.</p>
            </div>
            <div class="src-card">
              <span class="src-icon">⚖️</span>
              <strong>Comparación</strong>
              <p>Estudio etnomusicológico comparado con tradiciones del Próximo Oriente y monodia mediterránea posterior.</p>
            </div>
          </div>
        </section>

        <!-- SECCIÓN 4: COMENTARIO HISTÓRICO-MUSICAL -->
        <section class="egypt-block block-commentary">
          <div class="egypt-block-title-row">
            <span class="egypt-num-badge">4</span>
            <div>
              <h3>COMENTARIO HISTÓRICO-MUSICAL</h3>
              <small>Sonido, ritual y sociedad en perspectiva</small>
            </div>
          </div>
          <div class="commentary-content">
            <p>La música en el Antiguo Egipto es fundamental para comprender cómo el sonido actuaba como un <strong>puente entre lo humano y lo divino</strong>. Presente en la religión, la corte, el trabajo y las celebraciones fúnebres, reflejaba el orden cósmico (<em>Maat</em>) y la cohesión de la sociedad egipcia. Aunque no conservamos partituras completas con notación cifrada, la convergencia de la iconografía, los instrumentos conservados y los textos poéticos demuestra una sofisticada cultura musical con más de tres milenios de evolución ininterrumpida.</p>
          </div>
        </section>

        <!-- SECCIONES 5 Y 6: ACTIVIDADES DE REPASO Y GLOSARIO -->
        <div class="egypt-dual-grid">
          <!-- SECCIÓN 5: ACTIVIDADES DE REPASO -->
          <section class="egypt-block block-review-tasks">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">5</span>
              <div>
                <h3>ACTIVIDADES DE REPASO</h3>
                <small>Comprueba y aplica lo aprendido</small>
              </div>
            </div>
            <ol class="review-questions-list">
              <li><span>1</span><div>¿En qué se diferencian los usos rituales y los usos festivos de la música egipcia?</div></li>
              <li><span>2</span><div>Nombra al menos tres instrumentos de cada familia (cordófonos, aerófonos, percusión e idiófonos).</div></li>
              <li><span>3</span><div>¿Qué papel crees que tenía el sistrum en las ceremonias religiosas? ¿Por qué?</div></li>
              <li><span>4</span><div>¿Cómo sabemos que la música acompañaba a la danza en el Antiguo Egipto?</div></li>
              <li><span>5</span><div>¿Por qué no conservamos partituras completas de la música egipcia?</div></li>
              <li><span>6</span><div>¿Qué información nueva crees que podría aportar un hallazgo arqueológico de un instrumento musical? Razona tu respuesta.</div></li>
            </ol>
          </section>

          <!-- SECCIÓN 6: GLOSARIO COMPLEMENTARIO -->
          <section class="egypt-block block-glossary">
            <div class="egypt-block-title-row">
              <span class="egypt-num-badge">6</span>
              <div>
                <h3>GLOSARIO COMPLEMENTARIO</h3>
                <small>Términos clave para tu estudio</small>
              </div>
            </div>
            <div class="glossary-items-list">
              <div class="gl-item"><strong>Sistrum:</strong> Instrumento de metal con anillas sagrado de Hathor en contextos rituales.</div>
              <div class="gl-item"><strong>Menat:</strong> Collar ritual con cuentas y contrapeso que emitía un suave tintineo.</div>
              <div class="gl-item"><strong>Arqueología musical:</strong> Estudio material y acústico de restos de instrumentos antiguos.</div>
              <div class="gl-item"><strong>Organología:</strong> Disciplina que clasifica, construye y estudia los instrumentos musicales.</div>
              <div class="gl-item"><strong>Canto llano (comparación):</strong> Monodia vocal litúrgica sin acompañamiento instrumental.</div>
              <div class="gl-item"><strong>Reconstrucción histórica:</strong> Formulación de hipótesis sonoras a partir de las fuentes conservadas.</div>
            </div>
          </section>
        </div>

        <footer class="egypt-sheet-footer">
          <span class="egypt-key-idea">Idea clave: estudiamos la música egipcia a través de imágenes, objetos, textos y comparaciones, no a través de partituras completas.</span>
          <span class="egypt-final-motto">«EL PASADO TAMBIÉN SUENA CUANDO SABEMOS ESCUCHARLO.»</span>
        </footer>
      </div>
    </div>
  `;
}

function studentDocumentHTML(run) {
  const context = run.request?.pedagogy || {}, plan = run.result?.plan || {}, claims = run.result?.claims || [];
  const session = context.session;
  const sources = [...new Map((run.evidence || []).map(item => [item.document_id, item.metadata])).values()];
  const title = (run.request?.question || '').charAt(0).toLocaleUpperCase('es') + (run.request?.question || '').slice(1);
  const visuals = run.result?.visualizations || [];
  const isPolyphony = is15thCenturyPolyphony(run);
  const isEgypt = isAncientEgypt(run);
  const listenings = isPolyphony ? POLYPHONY_LISTENINGS : getRunListenings(run);
  let elapsed = 0;

  return `<article class="student-handout">
    <header class="student-cover">
      <div class="student-brand">
        <span class="student-pill">ENJAMBRE · MATERIAL DE CLASE</span>
        <span class="student-topic-tag">CUADERNO DIDÁCTICO DEL ALUMNADO</span>
      </div>
      <h1>${e(title)}</h1>
      <div class="student-meta">
        <strong>${e(context.group?.name || 'Grupo')}</strong>
        <span>${e(context.group?.level || 'Conservatorio')}</span>
        <span>⏱ ${context.duration_minutes || 60} minutos</span>
        ${session ? `<span>📅 ${e(session.date)}</span>` : ''}
      </div>
    </header>

    <!-- OBJETIVOS DIDÁCTICOS -->
    <section class="student-section section-intro">
      <div class="student-section-header">
        <span class="student-section-number">🎯</span>
        <div>
          <h2>Qué vamos a aprender</h2>
          <p class="student-section-intro">Objetivos y competencias formativas que desarrollaremos a lo largo de la sesión.</p>
        </div>
      </div>
      <ol class="student-objectives">
        ${(plan.objectives || []).map(item => `<li>${e(item)}</li>`).join('')}
      </ol>
    </section>

    <!-- SECCIÓN 01: CONTENIDO TEÓRICO DE LAS FUENTES -->
    <section class="student-section section-theory">
      <div class="student-section-header">
        <span class="student-section-number">01</span>
        <div>
          <h2>Contenido teórico de las fuentes</h2>
          <p class="student-section-intro">Análisis musicológico e histórico basado en las fuentes documentales autorizadas${isPolyphony ? ' (Allan Atlas, Gustave Reese y Ulrich Michels)' : isEgypt ? ' (Marcelle Duchesne-Guillemin, J. Peter Burkholder y Enrico Fubini)' : ''}.</p>
        </div>
      </div>
      <div class="theory-claims-list">
        ${claims.map((claim, index) => `
          <div class="student-content theory-claim-card">
            <span class="claim-index-badge">${String(index + 1).padStart(2, '0')}</span>
            <div class="claim-body">
              ${formatMarkdown(claim.text)}
              ${claim.evidence?.length ? `<div class="claim-source-badge"><span>📖 Fuente: ${e(claim.evidence[0].source_id)}</span></div>` : ''}
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    <!-- SECCIÓN 02: ESQUEMA GRÁFICO (MODELOS Y TÉCNICAS) -->
    <section class="student-section section-infographic">
      <div class="student-section-header">
        <span class="student-section-number">02</span>
        <div>
          <h2>Esquema gráfico: ${isEgypt ? 'Marco histórico, funciones y organología del Antiguo Egipto' : isPolyphony ? 'Modelos y técnicas de composición del siglo XV' : 'Modelos y estructuras técnicas'}</h2>
          <p class="student-section-intro">${isEgypt ? 'Láminas didácticas de contexto, funciones sociales, organología, quironimia y fuentes de estudio.' : isPolyphony ? 'Estructuras vocálicas, transformaciones del material y recursos de unificación cíclica.' : 'Estructuras formales y esquemas comparativos para el aula.'}</p>
        </div>
      </div>
      ${isEgypt ? renderEgyptInfographic(run) : (isPolyphony ? renderStudentInfographic(run) : (
        visuals.length ? `
          <div class="infographic-poster">
            <div class="infographic-main-head">
              <div class="info-tag-row">
                <span class="info-badge">${e(title.toUpperCase())}</span>
                <span class="info-badge-sub">ESQUEMAS TÉCNICOS Y ESTRUCTURAS FORMALES</span>
              </div>
              <h2>MODELOS Y ANÁLISIS DE TEXTURAS</h2>
              <p class="info-subtitle">Estructuras formales y esquemas comparativos para el aula</p>
            </div>
            <div class="visual-items">${visuals.map(v => `
              <div class="visual-card">
                <h3>${e(v.title)}</h3>
                ${v.caption ? `<p class="visual-caption">${e(v.caption)}</p>` : ''}
                <div class="visual-items">${v.items.map(it => `
                  <div class="visual-item">
                    <strong>${e(it.label)}</strong>
                    <span>${e(it.detail)}</span>
                  </div>
                `).join('')}</div>
              </div>
            `).join('')}</div>
          </div>
        ` : `
          <div class="infographic-poster">
            <div class="infographic-main-head">
              <div class="info-tag-row"><span class="info-badge">${e(title.toUpperCase())}</span></div>
              <h2>ESQUEMA CONCEPTUAL Y ESTRUCTURAL</h2>
            </div>
            <div class="visual-items">${claims.slice(0, 4).map((c, i) => `
              <div class="visual-item"><strong>Eje ${i + 1}</strong><span>${e(c.text.slice(0, 180))}…</span></div>
            `).join('')}</div>
          </div>
        `
      ))}
    </section>

    <!-- SECCIÓN 03: CONCEPTOS OBLIGATORIOS PARA APRENDER -->
    <section class="student-section section-concepts">
      <div class="student-section-header">
        <span class="student-section-number">03</span>
        <div>
          <h2>Conceptos obligatorios para aprender</h2>
          <p class="student-section-intro">Vocabulario técnico y conceptos analíticos indispensables del currículo de conservatorio.</p>
        </div>
      </div>
      <div class="concept-grid">
        ${isEgypt ? `
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-ritual">RITUAL</span><strong>Sistrum (Sistro)</strong></div>
            <p>Instrumento sagrado de percusión con marco metálico y varillas sonajas, consagrado al culto de Hathor para ahuyentar las fuerzas del caos.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-ritual">RITUAL</span><strong>Menat</strong></div>
            <p>Collar ceremonial con cuentas y contrapeso pectoral que las sacerdotisas de Hathor agitaban produciendo un suave tintineo purificador.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-gesto">DIRECCIÓN</span><strong>Quironimia</strong></div>
            <p>Sistema de dirección musical mediante gestos de manos, dedos y cuerpo que el cantor/director hacía a los instrumentistas para guiar melodía y ritmo.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-cordas">CORDÓFONO</span><strong>Arpa Arqueada</strong></div>
            <p>Principal cordófono del Antiguo Egipto, con cuerpo curvo de madera y cuerdas tensadas tañidas por solistas en la corte, banquetes y templos.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-vento">AERÓFONO</span><strong>Clarinete Doble</strong></div>
            <p>Aerófono compuesto por dos tubos paralelos de caña provistos de lengüetas batientes, con sonido penetrante usado en procesiones y danzas.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-liturxia">LITURGIA</span><strong>Canto Ritual</strong></div>
            <p>Monodia vocal entonada en templos y ritos funerarios, concebida como puente directo de comunicación entre el ser humano y las divinidades.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-fonte">ICONOGRAFÍA</span><strong>Iconografía Musical</strong></div>
            <p>Estudio sistemático de las fuentes visuales (frescos de tumbas como la de Nebamun y relieves en templos) para reconstruir la práctica musical.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge egypt-b-arqueo">MÉTODO</span><strong>Arqueología Musical</strong></div>
            <p>Análisis científico de los instrumentos materiales conservados en tumbas secas para deducir acústica histórica, materiales y afinaciones.</p>
          </div>
        ` : isPolyphony ? `
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">TÉCNICA</span><strong>Cantus Firmus</strong></div>
            <p>Melodía preexistente (canto gregoriano o canción profana) empleada como eje estructural de una nueva composición polifónica, asignada tradicionalmente al Tenor en notas de valores largos.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">RITMO</span><strong>Aumentación Rítmica</strong></div>
            <p>Procedimiento consistente en alargar proporcionalmente las duraciones de las figuras de la melodía original (duplicar o triplicar su valor), confiriendo al Tenor un ritmo lento y solemne.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">FORMA</span><strong>Misa Cíclica</strong></div>
            <p>Obra litúrgica polifónica monumental en la que los cinco movimientos del Ordinario (Kyrie, Gloria, Credo, Sanctus, Agnus Dei) comparten el mismo material temático unificador.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">RECURSO</span><strong>Técnica del Motto</strong></div>
            <p>Recurso de unificación que consiste en iniciar cada uno de los movimientos del Ordinario con la misma frase melódica o contrapuntística en las voces superiores (motivo de cabeza).</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">GÉNERO</span><strong>Formes Fixes</strong></div>
            <p>Estructuras poético-musicales cerradas del siglo XIV que dominaron la chanson cortesana del XV: rondeau (ABaAabAB), ballade (aabC) y virelai / bergerette (AbbaA).</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">ESTILO</span><strong>Flujo Continuo y Asimetría</strong></div>
            <p>Técnica polifónica característica de Johannes Ockeghem que evita deliberadamente las cesuras cadenciales simultáneas mediante la superposición y encabalgamiento de frases melódicas independientes.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">TÉCNICA</span><strong>Misa Parodia (Imitación)</strong></div>
            <p>Procedimiento compositivo renacentista que toma como modelo una obra polifónica preexistente completa a 3 o 4 voces, reelaborando y recombinando sus puntos de imitación y texturas.</p>
          </div>
          <div class="concept-card">
            <div class="concept-head"><span class="concept-badge">LENGUAJE</span><strong>Diatonicismo Modal</strong></div>
            <p>Conducción melódica y polifónica basada estrictamente en los modos eclesiásticos tradicionales, con reducción deliberada de alteraciones cromáticas fictas respecto a la complejidad del Ars Subtilior.</p>
          </div>
        ` : (
          visuals.flatMap(v => v.items || []).slice(0, 8).map((it, i) => `
            <div class="concept-card">
              <div class="concept-head"><span class="concept-badge">CONCEPTO ${i + 1}</span><strong>${e(it.label)}</strong></div>
              <p>${e(it.detail)}</p>
            </div>
          `).join('') || claims.slice(0, 6).map((c, i) => {
            const first = c.text.split('.')[0];
            return `
              <div class="concept-card">
                <div class="concept-head"><span class="concept-badge">CLAVE ${i + 1}</span><strong>${e(first.slice(0, 40))}…</strong></div>
                <p>${e(c.text)}</p>
              </div>
            `;
          }).join('')
        )}
      </div>
    </section>

    <!-- SECCIÓN 04: RELACIÓN DE 4 AUDICIONES COMENTADAS -->
    <section class="student-section section-listenings">
      <div class="student-section-header">
        <span class="student-section-number">04</span>
        <div>
          <h2>Relación de 4 audiciones comentadas</h2>
          <p class="student-section-intro">Obras maestras y repertorio de audición activa con análisis formal y antologías de referencia.</p>
        </div>
      </div>
      <div class="listening-grid">
        ${isEgypt ? renderEgyptListeningsHTML(false) : isPolyphony ? POLYPHONY_LISTENINGS.map(l => renderListeningCardItem(l, false)).join('') : (listenings?.length ? listenings.map(l => renderListeningCardItem(l, false)).join('') : (
          [1, 2, 3, 4].map(i => {
            const act = (plan.activities || [])[i - 1] || {};
            const actTitle = act.title || `Obra y audición ${i} de la sesión`;
            return `
              <div class="listening-card">
                <div class="listening-head">
                  <span class="listening-badge">AUDICIÓN ${i}</span>
                  <div>
                    <strong>${e(actTitle)}</strong>
                    <small>Ejemplo práctico y análisis para ${e(title)}</small>
                  </div>
                </div>
                <div class="listening-anthology">📚 Antología de partituras y fuentes de la materia</div>
                <div class="listening-points">
                  <strong>Puntos clave de escucha activa:</strong>
                  <ul>
                    <li>${e(act.instructions || 'Identificar la textura predominante y la articulación formal de las frases.')}</li>
                    <li>Seguir la conducción melódica y los puntos de tensión y reposo cadencial.</li>
                    <li>Relacionar los procedimientos técnicos escuchados con el marco histórico de la sesión.</li>
                  </ul>
                </div>
              </div>
            `;
          }).join('')
        ))}
      </div>
    </section>

    <!-- SECCIÓN 05: TRABAJOS PARA EL ALUMNADO -->
    <section class="student-section section-assignments">
      <div class="student-section-header">
        <span class="student-section-number">05</span>
        <div>
          <h2>Trabajos para el alumnado</h2>
          <p class="student-section-intro">Tareas prácticas individuales y en grupo de análisis sobre partituras, audición y comparación formal.</p>
        </div>
      </div>

      <div class="assignment-grid">
        ${isEgypt ? `
          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 1 · FUNCIONES</span>
              <strong>Diferenciación de usos rituales y festivos</strong>
            </div>
            <p><strong>Objetivo:</strong> Contrastar el papel de la música en el culto sagrado frente a los banquetes cortesanos.</p>
            <div class="assign-instructions">
              <ul>
                <li>Completar un cuadro analítico comparando los espacios (templo vs. palacio) y los instrumentos utilizados.</li>
                <li>Explicar qué significaba que una diosa como Hathor fuese señora de la música y la danza.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 2 · ORGANOLOGÍA</span>
              <strong>Clasificación de las tres familias de instrumentos</strong>
            </div>
            <p><strong>Objetivo:</strong> Dominar la organología instrumental del Antiguo Egipto.</p>
            <div class="assign-instructions">
              <ul>
                <li>Nombrar y describir tres instrumentos de cada familia: cordófonos, aerófonos, percusión e idiófonos.</li>
                <li>Indicar con qué materiales se construía cada uno y cuál era su contexto de uso habitual.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 3 · SIMBOLOGÍA</span>
              <strong>El sistrum y el culto sagrado en el templo</strong>
            </div>
            <p><strong>Objetivo:</strong> Comprender la relación entre timbre metálico, rito y protección divina.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Qué papel crees que tenía el sistrum en las ceremonias religiosas? ¿Por qué?</li>
                <li>Relacionar el sonido de las anillas sonajas con la protección contra el caos y las fuerzas malignas.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 4 · ICONOGRAFÍA</span>
              <strong>Análisis del Fresco de la Tumba de Nebamun (c. 1350 a. C.)</strong>
            </div>
            <p><strong>Objetivo:</strong> Extraer información musical a partir de representaciones pictóricas directas.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Cómo sabemos que la música acompañaba a la danza en el Antiguo Egipto a partir de las imágenes?</li>
                <li>Identificar los gestos de las manos de los músicos (quironimia) y la disposición de las bailarinas.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 5 · INVESTIGACIÓN</span>
              <strong>El enigma de la ausencia de partituras completas</strong>
            </div>
            <p><strong>Objetivo:</strong> Analizar el método histórico-musicológico de aproximación a civilizaciones antiguas.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Por qué no conservamos partituras completas de la música egipcia?</li>
                <li>Explicar cómo se combinan la iconografía, los textos, la arqueología y la comparación.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assignment-head">
              <span class="assign-tag egypt-tag">ACTIVIDAD 6 · ARQUEOLOGÍA</span>
              <strong>Hallazgos arqueológicos y reconstrucción sonora</strong>
            </div>
            <p><strong>Objetivo:</strong> Valorar qué aporta el descubrimiento material de instrumentos en tumbas.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Qué información nueva crees que podría aportar un hallazgo arqueológico de un instrumento musical? Razona tu respuesta.</li>
                <li>Mencionar posibles datos sobre maderas, afinación, orificios tonales y técnicas constructivas.</li>
              </ul>
            </div>
          </div>
        ` : isPolyphony ? `
          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 1 · PARTITURA</span>
              <strong>Rastreo auditivo y analítico del Cantus Firmus</strong>
            </div>
            <p><strong>Objetivo:</strong> Seguir en la partitura el Kyrie de la <em>Missa Se la face ay pale</em> de Du Fay e identificar con precisión el Tenor.</p>
            <div class="assign-instructions">
              <ul>
                <li>Subrayar con rotulador en la partitura los compases exactos de entrada del Tenor.</li>
                <li>Calcular cuántos compases dura cada nota del tenor en comparación con el ritmo activo de Superius y Altus.</li>
                <li>Verificar en qué secciones secundarias (como el Christe) calla el cantus firmus.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 2 · FORMA POÉTICA</span>
              <strong>Diagramación formal de la Chanson cortesana (Rondeau)</strong>
            </div>
            <p><strong>Objetivo:</strong> Comprender la arquitectura de las formes fixes a partir de <em>De plus en plus</em> de Binchois.</p>
            <div class="assign-instructions">
              <ul>
                <li>Esquematizar el desarrollo formal del rondeau aplicando el molde clásico <code>ABaAabAB</code>.</li>
                <li>Señalar qué secciones reproducen el estribillo completo (música y texto idénticos) y cuáles repiten solo la música con nuevas rimas poéticas.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 3 · ESTILO Y TEXTURA</span>
              <strong>Matriz comparativa de estilo: Du Fay vs. Ockeghem</strong>
            </div>
            <p><strong>Objetivo:</strong> Contrastar la estética y técnica de la primera y segunda generación franco-flamenca.</p>
            <div class="assign-instructions">
              <ul>
                <li>Completar una tabla comparativa analizando: 1) Formación de frases (claras vs. solapadas/flujo continuo), 2) Tesituras y registro de voces, 3) Cadencias simultáneas y 4) Imitación contrapuntística.</li>
                <li>Justificar por qué Reese califica el estilo de Ockeghem como «evitación deliberada de la articulación de frases».</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 4 · CONSOLIDACIÓN</span>
              <strong>Cuestionario de conceptos clave del siglo XV</strong>
            </div>
            <p><strong>Objetivo:</strong> Afianzar los conceptos teóricos obligatorios para el examen y el análisis.</p>
            <div class="assign-instructions">
              <ul>
                <li>¿Qué diferencia técnica distingue a una misa de cantus firmus de una misa parodia?</li>
                <li>¿Por qué los compositores evitaban emplear melodías del propio Kyrie como cantus firmus de la misa cíclica?</li>
                <li>¿Qué función estructural desempeñaba la técnica del <em>motto</em> o motivo de cabeza?</li>
              </ul>
            </div>
          </div>
        ` : `
          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 1 · PARTITURA</span>
              <strong>Análisis auditivo y sobre partitura</strong>
            </div>
            <p><strong>Objetivo:</strong> Localizar en la partitura los elementos constructivos y técnicos trabajados en la sesión de ${e(title)}.</p>
            <div class="assign-instructions">
              <ul>
                <li>Marcar las entradas motívicas, cesuras y cambios de textura musical.</li>
                <li>Identificar los puntos de articulación formal y las cadencias principales.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 2 · FORMA Y ESTRUCTURA</span>
              <strong>Diagramación formal y esquema estructural</strong>
            </div>
            <p><strong>Objetivo:</strong> Diseñar un mapa visual de la arquitectura formal de las obras estudiadas.</p>
            <div class="assign-instructions">
              <ul>
                <li>Esquematizar las secciones principales (exposición, desarrollo, reexposiciones o estribillos).</li>
                <li>Indicar la modulación o centros tonales/modales de cada sección.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 3 · ESTILO Y TEXTURA</span>
              <strong>Matriz comparativa de estilo</strong>
            </div>
            <p><strong>Objetivo:</strong> Contrastar dos pasajes o ejemplos musicales analizando sus rasgos diferenciales.</p>
            <div class="assign-instructions">
              <ul>
                <li>Elaborar una tabla analítica comparando textura (homofonía vs. contrapunto), ritmo armónico y perfil melódico.</li>
                <li>Justificar las conclusiones utilizando vocabulario técnico de conservatorio.</li>
              </ul>
            </div>
          </div>

          <div class="assignment-card">
            <div class="assign-head">
              <span class="assign-tag">TAREA 4 · CONSOLIDACIÓN</span>
              <strong>Cuestionario de conceptos clave</strong>
            </div>
            <p><strong>Objetivo:</strong> Afianzar el dominio de los conceptos obligatorios de la unidad.</p>
            <div class="assign-instructions">
              <ul>
                <li>Definir con precisión técnica los términos obligatorios de la sesión.</li>
                <li>Redactar una síntesis razonada ilustrando cada concepto con un ejemplo musical concreto.</li>
              </ul>
            </div>
          </div>
        `}
      </div>

      <!-- SECUENCIA DE TRABAJO EN EL AULA -->
      <div class="class-session-work">
        <h3 class="session-work-title">⏱ Secuencia de trabajo y actividades en el aula</h3>
        <div class="student-activities">
          ${(plan.activities || []).map((activity, index) => {
            const mins = Number(activity.minutes) || 0;
            const start = elapsed;
            elapsed += mins;
            return `
              <div class="student-activity">
                <span>${start}–${elapsed} min</span>
                <div>
                  <h3>${index + 1}. ${e(activity.title)}</h3>
                  <p>${e(activity.instructions)}</p>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    </section>

    <!-- SECCIÓN 06: FUENTES Y BIBLIOGRAFÍA DE CONSULTA -->
    <section class="student-section section-sources">
      <div class="student-section-header">
        <span class="student-section-number">06</span>
        <div>
          <h2>Fuentes y antologías de consulta</h2>
          <p class="student-section-intro">Bibliografía autorizada y ediciones de partituras utilizadas para elaborar este material.</p>
        </div>
      </div>
      <div class="sources-pills-list">
        ${isEgypt ? `
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Music in Ancient Mesopotamia and Egypt</strong>
              <small>Marcelle Duchesne-Guillemin · World of Music / Garland</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Norton Anthology of Western Music (Ancient to Baroque)</strong>
              <small>J. Peter Burkholder & Claude V. Palisca · W. W. Norton</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Historia de la estética musical: desde la Antigüedad hasta el siglo XX</strong>
              <small>Enrico Fubini · Alianza Música</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">🏺</span>
            <div>
              <strong>Iconografía y textos de las tumbas de Nebamun, Ti y Tutankamón</strong>
              <small>Museo Británico (Londres) / Museo de El Cairo</small>
            </div>
          </div>
        ` : isPolyphony ? `
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>La música del Renacimiento & Antología de la música del Renacimiento</strong>
              <small>Allan W. Atlas · Ediciones Akal / Norton</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>La música en el Renacimiento</strong>
              <small>Gustave Reese · Alianza Música</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">📖</span>
            <div>
              <strong>Atlas de la Música (Vol. 1)</strong>
              <small>Ulrich Michels · Alianza Editorial</small>
            </div>
          </div>
          <div class="source-pill-card">
            <span class="source-pill-icon">🎼</span>
            <div>
              <strong>Manuscrito Chigi C.VIII.234</strong>
              <small>Biblioteca Apostólica Vaticana · Misas y motetes de Johannes Ockeghem</small>
            </div>
          </div>
        ` : ''}
        ${sources.filter(s => s.title && !s.title.includes('Atlas') && !s.title.includes('Reese') && !s.title.includes('Duchesne')).map(meta => `
          <div class="source-pill-card">
            <span class="source-pill-icon">📄</span>
            <div>
              <strong>${e(meta.title)}</strong>
              <small>${e(meta.authors?.join(', ') || 'Biblioteca Enjambre')}${meta.year ? ` · ${meta.year}` : ''}</small>
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    ${renderStudentDiscographySection(run)}
  </article>`;
}

function printStudentDocument() {
  const handout = document.querySelector('.student-dialog .student-handout');
  if (!handout) {
    document.body.classList.add('student-printing');
    window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), { once: true });
    window.print();
    return;
  }

  // Clone handout content so the on-screen modal stays intact
  const clone = handout.cloneNode(true);

  // For Ancient Egypt sheets: remove interactive tabs and show both sheets sequentially
  clone.querySelectorAll('.egypt-sheet-tabs').forEach(el => el.remove());
  clone.querySelectorAll('.egypt-sheet').forEach(el => {
    el.style.display = 'block';
  });

  // Remove buttons and interactive elements
  clone.querySelectorAll('.button, button, [data-action]').forEach(el => el.remove());

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
  const docTitle = document.querySelector('.student-cover h1')?.textContent?.trim() || 'Material para el alumnado';

  doc.open();
  doc.write('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>' + docTitle + ' · Enjambre</title></head><body class="print-isolated-body"></body></html>');
  doc.close();

  // Copy all style elements and stylesheets so custom typography, colors, and layout apply
  document.querySelectorAll('link[rel="stylesheet"], style').forEach(node => {
    doc.head.appendChild(node.cloneNode(true));
  });

  doc.body.appendChild(clone);

  setTimeout(() => {
    try {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
    } catch (e) {
      document.body.classList.add('student-printing');
      window.addEventListener('afterprint', () => document.body.classList.remove('student-printing'), { once: true });
      window.print();
    }
  }, 250);
}

async function studentMaterialModal(id) {
  const run=await api('/runs/'+encodeURIComponent(id));
  if(!run.request?.pedagogy||!run.result?.plan)throw new Error('Esta propuesta todavía no tiene material válido para el alumnado.');
  modal('Material para el alumnado',`${studentDocumentHTML(run)}<div class="student-share-actions"><div><strong>Listo para compartir</strong><p>Copia el contenido en Google Classroom o guárdalo como PDF.</p></div><button class="button" data-copy-student="${e(id)}">${icon('copy')}Copiar para Classroom</button><button class="button" data-download-student="${e(id)}">${icon('download')}Descargar Markdown</button><button class="button primary" data-action="print-student">${icon('document')}Imprimir / Guardar PDF</button></div>`);
  dialog.classList.add('student-dialog');
}
function sourceModal() {
  if(!state.config.subjects.length){subjectModal();toast('Primero, crea la materia a la que pertenecen tus fuentes.');return;}
  chosenFiles=[];
  modal('Añadir a tu biblioteca',`<p>Incorpora documentos y revisa su contenido antes de permitir que los utilice el asistente.</p><form data-form="upload" id="upload-form"><label class="dropzone" id="dropzone" tabindex="0">${icon('up')}<strong>Arrastra tus archivos aquí</strong><small>o haz clic para elegirlos · PDF, TXT y Markdown</small><input class="file-input" type="file" id="files" multiple accept=".pdf,.txt,.md" aria-label="Elegir documentos"></label><div class="chosen-files" id="chosen-files">Hasta 300 MB por archivo</div><div class="form-row"><div class="field"><label class="label" for="upload-subject">Materia</label><select id="upload-subject" name="subject" required>${subjectOptions(selected,true)}</select></div><div class="field"><label class="label" for="upload-category">Tipo de contenido</label><select id="upload-category" name="category"><option value="documental">Fuente documental</option><option value="profesor">Material propio</option></select></div></div><p class="field-note">Libros y artículos van en documentación. Tus apuntes y ejercicios, en material propio.</p><div class="dialog-actions"><button class="button ghost" type="button" data-action="scan">Revisar carpeta</button><button class="button primary" type="submit">Añadir y revisar ${icon('arrow')}</button></div></form>`);
}
function setFiles(files){chosenFiles=Array.from(files);$('#chosen-files').textContent=chosenFiles.length?chosenFiles.map(f=>f.name).join(' · '):'Hasta 300 MB por archivo';}
function subjectModal(id) {const subject=state.config.subjects.find(s=>s.id===id);modal(subject?'Editar materia':'Nueva materia',`<p>Cada materia tendrá su propio ámbito de conocimiento y sus carpetas.</p><form data-form="subject"><input type="hidden" name="id" value="${e(subject?.id||'')}"><div class="field"><label class="label" for="subject-name">Nombre de la materia</label><input class="input" id="subject-name" name="name" required maxlength="200" placeholder="Por ejemplo, Historia de la Música I" value="${e(subject?.name||'')}"></div><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button primary" type="submit">Guardar materia</button></div></form>`);$('#subject-name').focus();}
function groupModal(id) {if(!state.config.subjects.length){subjectModal();return;}const current=state.config.groups.find(g=>g.id===id),now=new Date(), year=current?Number(state.config.academic_years.find(y=>y.id===current.academic_year_id).start_date.slice(0,4)):(now.getMonth()>=8?now.getFullYear():now.getFullYear()-1);modal(current?'Editar grupo':'Nuevo grupo',`<p>El asistente usará estos datos para ajustar el nivel y el idioma de las propuestas.</p><form data-form="group"><input type="hidden" name="id" value="${e(current?.id||'')}"><div class="form-row"><div class="field"><label class="label" for="group-name">Nombre del grupo</label><input class="input" id="group-name" name="name" required placeholder="Por ejemplo, 3º GP · Grupo A" value="${e(current?.name||'')}"></div><div class="field"><label class="label" for="group-level">Nivel</label><input class="input" id="group-level" name="level" required placeholder="Por ejemplo, 3º de Grado Profesional" value="${e(current?.level||'')}"></div></div><div class="field"><label class="label" for="group-subject">Materia</label><select id="group-subject" name="subject" required>${subjectOptions(current?.subject_id||selected,true)}</select></div><div class="form-row"><div class="field"><label class="label" for="group-center">Centro</label><input class="input" id="group-center" name="center" required value="${e((current?state.config.centers.find(c=>c.id===current.center_id):state.config.centers[0])?.name||'')}"></div><div class="field"><label class="label" for="group-teacher">Profesor</label><input class="input" id="group-teacher" name="teacher" required value="${e((current?state.config.teachers.find(t=>t.id===current.teacher_id):state.config.teachers[0])?.name||'')}"></div></div><div class="form-row"><div class="field"><label class="label" for="group-year">Año de inicio del curso</label><input class="input" id="group-year" name="year" type="number" min="2000" max="2100" value="${year}" required><p class="field-note">De septiembre a agosto del año siguiente.</p></div><div class="field"><label class="label" for="group-language">Idioma de las propuestas</label><select id="group-language" name="language">${[['es','Castellano'],['gl','Galego'],['ca','Català'],['eu','Euskara'],['en','English'],['pt','Português']].map(([v,t])=>option(v,t,current?.language||'es')).join('')}</select></div></div><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button primary">Guardar grupo</button></div></form>`);}
function proposalModal(session=null) {
  if(!state.config.groups.length){modal('Primero, tu grupo',`<p>Para preparar una propuesta útil necesitamos conocer el nivel y la materia del grupo.</p><div class="dialog-actions">${primary('Añadir un grupo','new-group')}</div>`);return;}
  const group = session?.group_id || draft('proposal-form','group',state.config.groups[0].id);
  const duration = session?.duration_minutes || draft('proposal-form','duration','60');
  const sessionDate = session ? state.agenda.date : draft('proposal-form','session_date','');
  modal('Preparar una propuesta',`<p>Un punto de partida con objetivos, actividades y tiempos. Tú tendrás la última palabra.</p><form data-form="proposal" id="proposal-form"><div class="form-row proposal-schedule"><div class="field"><label class="label" for="proposal-group">Grupo</label><select id="proposal-group" name="group" required>${state.config.groups.map(g=>option(g.id,`${g.name} · ${subjectName(g.subject_id)}`,group)).join('')}</select></div><div class="field"><label class="label" for="proposal-date">Fecha de la clase · opcional</label><input class="input" id="proposal-date" type="date" name="session_date" value="${e(sessionDate)}"></div><div class="field"><label class="label" for="proposal-duration">Duración</label><input class="input" id="proposal-duration" type="number" name="duration" min="5" max="240" required value="${e(duration)}"></div></div><div class="field"><label class="label" for="proposal-topic">Tema de la sesión</label><input class="input" id="proposal-topic" name="question" maxlength="4000" required placeholder="¿Qué quieres trabajar?" value="${e(draft('proposal-form','question'))}"></div><div class="field"><label class="label" for="proposal-unit">Unidad de la programación · opcional</label><select id="proposal-unit" name="unit">${unitOptions(group)}</select></div><div class="field"><label class="label" for="proposal-criteria">Tus indicaciones · opcional</label><textarea id="proposal-criteria" name="criteria" maxlength="2000" placeholder="Qué priorizar, qué materiales tienes, qué conviene evitar…">${e(draft('proposal-form','criteria'))}</textarea></div><p class="field-note">La propuesta combinará la programación didáctica de la materia con tus fuentes autorizadas.</p><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button primary">${icon('spark')}Preparar propuesta</button></div></form>`);
}
function expandProposalModal(run) {
  if (!run) return;
  const ctx = run.request?.pedagogy;
  const groups = state.config.groups || [];
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
function unitOptions(group) {const binding=state.config.group_curricula.find(b=>b.group_id===group);return '<option value="">Sin unidad seleccionada</option>'+state.config.curriculum_units.filter(u=>u.curriculum_id===binding?.curriculum_id).map(u=>option(u.id,u.title,draft('proposal-form','unit'))).join('');}

async function showDocument(id) {
  modal('Abriendo documento', '<div class="initial-loading"><span class="spinner"></span>Consultando la biblioteca…</div>');
  const doc=await api('/documents/'+encodeURIComponent(id));
  const version=doc.versions.find(v=>v.id===doc.selected_version_id), warnings=version?.warnings||[];
  modal(e(doc.metadata.title),`<div class="document-meta"><span class="file-icon ${doc.category}">${e(version?.format?.toUpperCase()||'DOC')}</span><span>${doc.category==='profesor'?'Material del profesor':'Fuente documental'}<br>${e(doc.subjects.map(subjectName).join(', ')||'Sin materia')}</span></div>${version?.error?`<div class="notice error">${e(version.error)}</div>`:''}${warnings.map(w=>`<div class="notice warning">${e(w)}</div>`).join('')}<details class="metadata"><summary>Editar título, autor y materia</summary><form data-form="metadata" data-id="${e(id)}"><div class="field"><label class="label" for="doc-title">Título</label><input class="input" id="doc-title" name="title" required value="${e(doc.metadata.title)}"></div><div class="form-row"><div class="field"><label class="label" for="doc-authors">Autores, separados por punto y coma</label><input class="input" id="doc-authors" name="authors" value="${e(doc.metadata.authors?.join('; ')||'')}"></div><div class="field"><label class="label" for="doc-year">Año · opcional</label><input class="input" id="doc-year" name="year" type="number" value="${e(doc.metadata.year||'')}"></div></div><div class="field"><label class="label" for="doc-subject">Materia</label><select id="doc-subject" name="subject" required>${subjectOptions(doc.subjects[0]||'',true)}</select></div><button class="button small" type="submit">Guardar cambios</button></form></details><div class="panel-header"><h3>Vista previa del contenido</h3><button class="button ghost small" data-original="${e(id)}">${icon('download')}Original</button></div><div class="text-preview">${doc.segments.map(s=>`<small>${s.locator.kind==='pdf_page'?'Página '+s.locator.pdf_page_index+' del PDF':'Líneas '+s.locator.line_start+'–'+s.locator.line_end}</small>${e(s.text)}`).join('')||'No se ha podido extraer texto utilizable.'}</div>${doc.preview_truncated?'<p class="field-note">Vista previa abreviada. El original completo se conserva en la biblioteca.</p>':''}<form data-form="authorize" data-id="${e(id)}">${warnings.length?'<label class="check"><input type="checkbox" name="accept_warnings" required>He revisado los avisos y acepto utilizar esta extracción.</label>':''}<div class="dialog-actions"><button type="button" class="button danger small" data-delete-document="${e(id)}">${icon('trash')}Eliminar de la biblioteca</button>${doc.enabled?`<button type="button" class="button ghost small" data-exclude="${e(id)}">Excluir del asistente</button>`:'<span class="field-note">Este archivo aún no puede utilizarse.</span>'}<button class="button primary" type="submit" ${version?.status==='failed'?'disabled':''}>${icon('check')}${doc.enabled?'Preparar de nuevo':'Permitir al asistente'}</button></div></form>`);
}
async function scanFolder() {
  modal('Archivos de tu carpeta', '<div class="initial-loading"><span class="spinner"></span>Revisando archivos locales…</div>');
  const data=await api('/inbox');
  const pending=data.files.filter(f=>!f.imported);
  modal('Archivos de tu carpeta',`<p>Incorpora los archivos nuevos o sus versiones actualizadas. Después podrás revisar y autorizar cada fuente.</p>${data.truncated?'<div class="notice warning">Se muestran los primeros 1000 archivos de la carpeta.</div>':''}${pending.length?pending.map(f=>`<form class="inbox-row" data-form="inbox" data-path="${e(f.path)}" data-document-id="${e(f.document_id||'')}"><div>${icon('document')}<span>${e(f.name)}${f.document_id?' <span class="pill">Nueva versión</span>':''}</span></div>${f.too_large?'<div class="notice error">Supera los 300 MB por archivo.</div>':`<div class="form-row"><select name="subject" aria-label="Materia de ${e(f.name)}" ${f.document_id?'disabled':'required'}>${subjectOptions(f.subject||selected,true)}</select><select name="category" aria-label="Tipo de ${e(f.name)}" ${f.document_id?'disabled':''}>${option('documental','Fuente documental',f.category)}${option('profesor','Material propio',f.category)}</select><button class="button small" type="submit">Incorporar</button></div>`}</form>`).join(''):`<div class="empty-compact"><h2>Todo al día.</h2><p>${data.files.length?'Los archivos de esta carpeta ya están incorporados.':'Copia tus documentos a Conocimiento o añádelos desde la aplicación.'}</p>${primary('Añadir documentos','add-source')}</div>`}<div class="dialog-actions"><button class="button ghost" data-action="reveal">Abrir carpeta ${icon('external')}</button><button class="button" data-action="close-dialog">Cerrar</button></div>`);
}
async function openRun(id) {
  currentRun=await api('/runs/'+encodeURIComponent(id));
  const route=currentRun.request.pedagogy?'propuestas':'asistente';
  if(view()!==route)location.hash=route;else render();
  setTimeout(()=>{
    $('.result')?.scrollIntoView({behavior:'smooth',block:'start'});
  },100);
}
async function checkStatus() {
  modelStatus=await api('/status');
  const isDS=(state?.generation_provider||modelStatus?.provider)==='deepseek';
  const label=isDS?(modelStatus.connected?'DeepSeek conectado':'DeepSeek sin clave'):(modelStatus.connected?'Ollama conectado':'Ollama sin conexión');
  $('#connection').innerHTML=`<span class="status-dot ${modelStatus.connected?'':'offline'}"></span><span>${label}</span>`;
  if(view()==='ajustes')render();
}
async function monitor() {
  if(polling)return;polling=true;
  try {
    if(isClosed)return;
    const jobs=await api('/jobs');connectionLost=false;const active=jobs.filter(j=>['queued','running'].includes(j.status));
    const completed=jobs.filter(j=>knownJobs.has(j.id)&&knownJobs.get(j.id)!==j.status&&['done','failed'].includes(j.status));
    jobs.forEach(j=>knownJobs.set(j.id,j.status));
    const tray=$('#job-tray');tray.hidden=!active.length;
    if(active.length){const running=active.find(j=>j.status==='running')||active[0];tray.innerHTML=`<span class="spinner"></span><div><strong>${e(running.title)}</strong><small>${running.progress?`${running.progress.done} de ${running.progress.total} fragmentos · ${Math.round(100*running.progress.done/running.progress.total)}% · `:''}${active.length>1?`${active.length-1} en espera · `:''}Puedes seguir trabajando en tu espacio.</small></div>`;}
    if(completed.length){await refresh();for(const job of completed){if(job.status==='failed')toast(job.error,true);else if(job.result?.run_id){const result=state.runs.find(r=>r.id===job.result.run_id),destination=result?.kind==='proposal'?'propuestas':'asistente';if(view()===destination&&!dialog.open)await openRun(job.result.run_id);else toast(destination==='propuestas'?'Tu propuesta está lista en Propuestas.':'La respuesta está lista en Asistente.');}else {toast(job.result?.status==='failed'?'No se pudo extraer el documento. Revisa su ficha.':'Biblioteca actualizada.',job.result?.status==='failed');}}}
  } catch(error) {if(state&&!connectionLost){toast('No hay conexión con Enjambre. Si lo has vuelto a abrir, recarga esta página.',true);connectionLost=true;}} finally{polling=false;}
}
async function queue(path,data){const response=await api(path,data);knownJobs.set(response.job_id,'new');await monitor();return response;}
document.addEventListener('click', async event=>{
  if(event.target.closest('.skip')){event.preventDefault();main.focus();return;}
  const target=event.target.closest('button,a[data-nav]');if(!target)return;
  try {
    if(target.dataset.document){await showDocument(target.dataset.document);return;}
    if(target.dataset.run){if(dialog.open)dialog.close();await openRun(target.dataset.run);return;}
    if(target.dataset.studentRun){await studentMaterialModal(target.dataset.studentRun);return;}
    if(target.dataset.sourcesRun){
      const run=currentRun&&currentRun.id===target.dataset.sourcesRun?currentRun:await api('/runs/'+encodeURIComponent(target.dataset.sourcesRun));
      sourcesModal(run);return;
    }
    if(target.dataset.copyStudent){
      const response=await fetch('/api/runs/'+encodeURIComponent(target.dataset.copyStudent)+'?student=1',{headers:{'X-Docente-Token':token}});
      if(!response.ok)throw new Error('No se pudo preparar el material para el alumnado.');
      await navigator.clipboard.writeText(await response.text());
      toast('Material copiado. Ya puedes pegarlo en Google Classroom.');
      return;
    }
    if(target.dataset.copyCode){
      const example=currentRun&&currentRun.id===target.dataset.copyCode?teacherWorkedExample(currentRun):null;
      if(!example)throw new Error('No se encontró el ejemplo resuelto.');
      await navigator.clipboard.writeText(example.code);
      toast('Código copiado. Ya puedes pegarlo en tu editor.');
      return;
    }
    if(target.dataset.downloadStudent){
      const identifier=target.dataset.downloadStudent;
      const response=await fetch('/api/runs/'+encodeURIComponent(identifier)+'?student=1',{headers:{'X-Docente-Token':token}});
      if(!response.ok)throw new Error('No se pudo descargar el material para el alumnado.');
      const url=URL.createObjectURL(await response.blob()),link=document.createElement('a');
      link.href=url;link.download='material-alumnado-'+identifier+'.md';document.body.appendChild(link);link.click();link.remove();
      setTimeout(()=>URL.revokeObjectURL(url),2000);toast('Material para el alumnado descargado.');return;
    }
    if(target.dataset.downloadSources){
      const identifier=target.dataset.downloadSources;
      const response=await fetch('/api/runs/'+encodeURIComponent(identifier)+'?sources=1',{headers:{'X-Docente-Token':token}});
      if(!response.ok)throw new Error('No se pudo descargar el anexo documental.');
      const url=URL.createObjectURL(await response.blob()),link=document.createElement('a');
      link.href=url;link.download='anexo-fuentes-'+identifier+'.md';document.body.appendChild(link);link.click();link.remove();
      setTimeout(()=>URL.revokeObjectURL(url),2000);toast('Anexo de fuentes y citas descargado.');return;
    }
    if(target.dataset.copyMarkdown){
      const identifier = target.dataset.copyMarkdown;
      target.disabled = true;
      try {
        const response = await fetch('/api/runs/' + encodeURIComponent(identifier) + '?download=1', {headers: {'X-Docente-Token': token}});
        if(!response.ok) throw new Error('No se pudo obtener el texto Markdown.');
        const mdText = await response.text();
        await navigator.clipboard.writeText(mdText);
        toast('¡Markdown copiado al portapapeles!');
      } catch(err) {
        toast('Error al copiar: ' + (err.message || err), true);
      } finally {
        target.disabled = false;
      }
      return;
    }
    if(target.dataset.download||target.dataset.original){
      const identifier = target.dataset.download || target.dataset.original;
      const isOrig = !!target.dataset.original;
      target.disabled = true;
      try {
        const response = await fetch('/api/' + (isOrig ? 'documents/' : 'runs/') + encodeURIComponent(identifier) + '?download=1', {headers: {'X-Docente-Token': token}});
        if(!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || 'No se pudo exportar el archivo.');
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const filename = isOrig
          ? (decodeURIComponent(response.headers.get('Content-Disposition')?.match(/filename\*=utf-8''([^;]+)/i)?.[1] || '') || response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || 'original')
          : 'enjambre-' + identifier + '.md';
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 2000);
        toast('Descargando archivo Markdown (.md)...');
      } catch(err) {
        toast(err.message || 'Error al exportar.', true);
      } finally {
        target.disabled = false;
      }
      return;
    }
    if(target.dataset.deleteRun){
      const runId=target.dataset.deleteRun;
      if(!confirm('¿Estás seguro de que deseas eliminar esta propuesta del historial?'))return;
      target.disabled=true;
      await api('/runs/'+encodeURIComponent(runId)+'/delete',{});
      if(currentRun&&currentRun.id===runId)currentRun=null;
      if(dialog.open)dialog.close();
      await refresh();
      toast('Propuesta eliminada.');
      return;
    }
    if(target.dataset.deleteDocument){
      const docId=target.dataset.deleteDocument;
      if(!confirm('¿Estás seguro de que deseas eliminar este documento de tu biblioteca? Se eliminarán todas sus versiones y fragmentos procesados.'))return;
      target.disabled=true;
      await api('/documents/'+encodeURIComponent(docId)+'/delete',{});
      if(dialog.open)dialog.close();
      await refresh();
      toast('Documento eliminado de la biblioteca.');
      return;
    }
    if(target.dataset.exclude){target.disabled=true;await api('/documents/'+target.dataset.exclude+'/exclude',{});dialog.close();await refresh();toast('Fuente excluida. El asistente ya no puede utilizarla.');return;}
    if(target.dataset.editGroup){groupModal(target.dataset.editGroup);return;}
    if(target.dataset.editSubject){subjectModal(target.dataset.editSubject);return;}
    if(target.dataset.reviewApprove){target.disabled=true;const result=await api('/runs/'+encodeURIComponent(target.dataset.reviewApprove)+'/review',{action:'approved'});currentRun={...currentRun,...result};render();toast('Propuesta aprobada. Puedes exportarla o guardar una copia.');return;}
    if(target.dataset.reviewReject){const runId=target.dataset.reviewReject;modal('Rechazar propuesta',`<p>Puedes añadir una nota para recordar el motivo.</p><form data-form="reject" data-id="${e(runId)}"><div class="field"><label class="label" for="reject-notes">Notas (opcional)</label><textarea id="reject-notes" name="notes" maxlength="2000" placeholder="Motivo del rechazo o qué mejorar…"></textarea></div><div class="form-error" role="alert"></div><div class="dialog-actions"><button class="button ghost" type="button" data-action="close-dialog">Cancelar</button><button class="button danger" type="submit">${icon('close')}Rechazar propuesta</button></div></form>`);return;}
    if(target.dataset.recordRun){recordModal(target.dataset.recordRun, currentRun);return;}
    if(target.dataset.feedbackSession){const session=state.agenda.sessions.find(item=>item.id===target.dataset.feedbackSession);feedbackModal(session);return;}
    if(target.dataset.sessionRecord){await existingFeedbackModal(target.dataset.sessionRecord);return;}
    if(target.dataset.revealRecord){await api('/records/'+encodeURIComponent(target.dataset.revealRecord)+'/reveal',{});return;}
    if(target.dataset.expandProposal){expandProposalModal(currentRun);return;}
    if(target.dataset.prepareSession){const session=state.agenda.sessions.find(item=>item.id===target.dataset.prepareSession);if(session)proposalModal(session);return;}
    if('period' in target.dataset){selectedPeriod=target.dataset.period;render();return;}
    if('subject' in target.dataset){selected=target.dataset.subject;selectedPeriod='';localStorage.setItem('enjambre-subject',selected);render();return;}

    if(target.dataset.tab){tab=target.dataset.tab;render();return;}
    switch(target.dataset.action){
      case 'all-answers':modal('Tus consultas',state.runs.filter(r=>r.kind==='answer').map(r=>`<button class="recent-item" data-run="${e(r.id)}">${e(r.title)}<span>${dateLabel(r.created_at)} · ${runStatus(r.status)}</span></button>`).join(''));break;
      case 'shutdown-dialog':modal('Cerrar tu espacio',`<p>Se cerrará el servidor local. Tus documentos y propuestas quedan guardados.</p><div class="dialog-actions"><button class="button ghost" data-action="close-dialog">Volver</button><button class="button primary" data-action="shutdown">Cerrar Enjambre</button></div>`);break;
      case 'shutdown':await api('/shutdown',{});isClosed=true;clearInterval(monitorTimer);dialog.close();$('#connection').disabled=true;$('#connection').innerHTML='Enjambre cerrado';render();break;
      case 'add-source':sourceModal();break;
      case 'download-calendar':{
        const res = await fetch('/api/calendar.ics', {headers: {'X-Docente-Token': token}});
        if (!res.ok) throw new Error('No se pudo descargar el calendario.');
        const blobUrl = URL.createObjectURL(await res.blob());
        const dlLink = document.createElement('a');
        dlLink.href = blobUrl;
        dlLink.setAttribute('download', 'horario-docente.ics');
        document.body.appendChild(dlLink);
        dlLink.click();
        document.body.removeChild(dlLink);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
        toast('Descargando calendario con avisos (.ics)...');
        break;
      }
      case 'new-subject':subjectModal();break;
      case 'new-group':groupModal();break;
      case 'new-proposal':proposalModal();break;
      case 'new-feedback':feedbackModal();break;
      case 'close-dialog':dialog.close();break;
      case 'reveal':await api('/reveal',{});break;
      case 'reveal-diary':await api('/reveal-diary',{});break;
      case 'scan':await scanFolder();break;
      case 'status':await checkStatus();if(view()!=='ajustes'){location.hash='ajustes';}break;
      case 'clear-filter':selected='';selectedPeriod='';tab='all';query='';render();break;
      case 'close-run':currentRun=null;render();break;
      case 'print-student':printStudentDocument();break;
      case 'reload':await refresh();break;
    }
  }catch(error){fail(error);target.disabled=false;}
});
document.addEventListener('input',event=>{
  if(event.target.id==='library-search'){query=event.target.value;$('#library-results').innerHTML=libraryResults();return;}
  const form=event.target.closest('form');if(form?.id&&event.target.name){drafts[form.id]??={};drafts[form.id][event.target.name]=event.target.value;}
});
document.addEventListener('change',event=>{
  if(event.target.id==='files')setFiles(event.target.files);
  if(event.target.id==='proposal-group'){$('#proposal-unit').innerHTML=unitOptions(event.target.value);if(drafts['proposal-form'])drafts['proposal-form'].unit='';}
  if(event.target.id==='ask-subject'){drafts['ask-form']??={};drafts['ask-form'].subject=event.target.value;render();}
  if(event.target.id==='model-provider'){
    const form=event.target.closest('form');
    const isDS=event.target.value==='deepseek';
    form.querySelectorAll('.ds-only').forEach(el=>el.hidden=!isDS);
    form.querySelectorAll('.ollama-only').forEach(el=>el.hidden=isDS);
  }
});
document.addEventListener('keydown',event=>{if(event.target.id==='dropzone'&&['Enter',' '].includes(event.key)){event.preventDefault();$('#files').click();}});
document.addEventListener('dragover',event=>{if(event.target.closest('#dropzone')){event.preventDefault();$('#dropzone').classList.add('dragging');}});
document.addEventListener('dragleave',event=>{event.target.closest('#dropzone')?.classList.remove('dragging');});
document.addEventListener('drop',event=>{if(event.target.closest('#dropzone')){event.preventDefault();setFiles(event.dataTransfer.files);$('#dropzone').classList.remove('dragging');}});
document.addEventListener('submit',async event=>{
  const form=event.target.closest('[data-form]');if(!form)return;event.preventDefault();
  const button=$('[type="submit"]',form)||$('button:not([type="button"])',form);const data=Object.fromEntries(new FormData(form));const buttonLabel=button?.innerHTML;if(button)button.disabled=true;
  const errorNode=$('.form-error',dialog.open?dialog:form);if(errorNode)errorNode.textContent='';
  try {
    switch(form.dataset.form){
      case 'models':{
        const provider=data.provider||'ollama';
        const generation=provider==='deepseek'?(data.generation_ds||data.generation):(data.generation_ollama||data.generation);
        await api('/models',{...data,provider,generation});
        await refresh();await checkStatus();
        toast('Configuración de motor actualizada.');
        break;
      }
      case 'subject':await api('/subjects',data);dialog.close();await refresh();toast('Materia guardada. Sus carpetas ya están disponibles.');break;
      case 'group':await api('/groups',{...data,year:Number(data.year)});dialog.close();await refresh();toast('Grupo guardado. Ya puedes preparar una propuesta.');break;
      case 'upload':{
        if(!chosenFiles.length)throw new Error('Elige al menos un archivo.');
        if(chosenFiles.length>8)throw new Error('Añade hasta ocho archivos cada vez.');
        for(const file of chosenFiles){if(!/\.(pdf|md|txt)$/i.test(file.name))throw new Error('Solo se admiten PDF, Markdown y TXT.');if(file.size>300*1024*1024)throw new Error(file.name+' supera los 300 MB.');}
        let uploaded=0;
        for(const file of chosenFiles){button.textContent=`Añadiendo ${++uploaded} de ${chosenFiles.length}…`;const response=await fetch('/api/upload?name='+encodeURIComponent(file.name),{method:'POST',headers:{'X-Docente-Token':token},body:file});const stored=await response.json();if(!response.ok)throw new Error(stored.error);await queue('/import',{...data,path:stored.path});}
        dialog.close();toast('Archivos añadidos. Revisa cada fuente para permitir su uso.');break;
      }
      case 'inbox':await queue('/import',{...data,path:form.dataset.path,document_id:form.dataset.documentId||undefined});form.innerHTML='<p class="inbox-status">'+icon('check')+' En proceso. Aparecerá en la biblioteca para su revisión.</p>';break;
      case 'authorize':await queue('/documents/'+form.dataset.id+'/authorize',{accept_warnings:!!data.accept_warnings});dialog.close();break;
      case 'metadata':await api('/documents/'+form.dataset.id+'/metadata',{...data,authors:data.authors.split(';').map(a=>a.trim()).filter(Boolean),year:data.year?Number(data.year):null});await refresh();await showDocument(form.dataset.id);toast('Metadatos actualizados.');break;
      case 'ask':await queue('/generate',{...data,mode:'ask'});toast('Consulta en marcha. Puedes seguir navegando.');break;
      case 'proposal':await queue('/generate',{...data,mode:'pedagogy',duration:Number(data.duration)});dialog.close();toast('Preparando el borrador con tus fuentes.');break;
      case 'reject':{const result=await api('/runs/'+encodeURIComponent(form.dataset.id)+'/review',{action:'rejected',notes:data.notes||''});if(currentRun&&currentRun.id===form.dataset.id)currentRun={...currentRun,...result};dialog.close();render();toast('Propuesta rechazada y anotada.');break;}
      case 'record':{const payload={...data,duration_minutes:Number(data.duration_minutes),run_id:form.dataset.run||undefined};const result=await api('/records',payload);dialog.close();toast(`Clase registrada: ${result.id}. El asistente tendrá en cuenta esta sesión en las próximas propuestas.`);break;}
      case 'feedback':{const result=form.dataset.record?await api('/records/'+encodeURIComponent(form.dataset.record)+'/feedback',data):await api('/records',{...data,duration_minutes:Number(data.duration_minutes)});dialog.close();await refresh();toast(`Feedback guardado en el diario de ${result.session_date}.`);break;}
    }
  }catch(error){fail(error);}finally{if(button?.isConnected){button.disabled=false;button.innerHTML=buttonLabel;}}
});
window.addEventListener('hashchange',()=>{if(state){render();window.scrollTo(0,0);}});
window.addEventListener('beforeprint', () => {
  if (dialog?.open && dialog?.classList.contains('student-dialog')) {
    document.body.classList.add('student-printing');
    dialog.querySelectorAll('.egypt-sheet').forEach(el => { el.style.display = 'block'; });
  }
});
window.addEventListener('afterprint', () => {
  document.body.classList.remove('student-printing');
});
async function boot(){try{await refresh();state.jobs.forEach(j=>knownJobs.set(j.id,j.status));await monitor();checkStatus().catch(fail);monitorTimer=setInterval(monitor,3000);}catch(error){main.innerHTML=`<section class="error-state"><h2>No se pudo abrir el espacio.</h2><p>${e(error.message)}</p><button class="button" data-action="reload">Volver a intentar</button></section>`;}}
boot();

// Complete keyboard navigation for the source-type tabs.
document.addEventListener('keydown', event => {
  if(event.target.getAttribute('role')!=='tab'||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
  event.preventDefault();const tabs=Array.from(document.querySelectorAll('[role="tab"]')),index=tabs.indexOf(event.target);
  const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
  tabs[next].click();document.querySelectorAll('[role="tab"]')[next].focus();
});
