import { e } from '../ui.js';

// Módulo de infografía de Egipto: renderiza dinámicamente a partir de la ficha servida por la API.

export function switchEgyptTab(btn, tabId) {
  const poster = btn.closest('.egypt-infographic-poster');
  if (!poster) return;
  poster.querySelectorAll('.egypt-tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const p1 = poster.querySelector('#egypt-page-1');
  const p2 = poster.querySelector('#egypt-page-2');
  if (p1) p1.style.display = tabId === 'egypt-page-1' ? 'block' : 'none';
  if (p2) p2.style.display = tabId === 'egypt-page-2' ? 'block' : 'none';
}

export function renderEgyptInfographic(run) {
  const ficha = run?.ficha;
  const infog = ficha?.infografia;
  if (!infog) {
    return '<div class="infographic-empty"><p>Sin contenido infográfico disponible.</p></div>';
  }

  const marco = infog.marco_historico || [];
  const marcoList = Array.isArray(marco) ? marco : [marco];
  const funciones = infog.funciones_sociales || [];
  const organologia = infog.organologia || [];
  const fuentes = infog.fuentes_e_iconografia || [];

  return [
    '<div class="infographic-poster egypt-infographic-poster">',
    '  <div class="egypt-page-tabs">',
    '    <button type="button" class="egypt-tab-btn active" data-tab="egypt-page-1">',
    `      📜 ${e(infog.titulo || 'Lámina 1')}`,
    '    </button>',
    '    <button type="button" class="egypt-tab-btn" data-tab="egypt-page-2">',
    '      𓏢 Lámina 2: Instrumentos y fuentes',
    '    </button>',
    '  </div>',
    '  <div id="egypt-page-1" class="egypt-sheet">',
    '    <header class="egypt-sheet-header">',
    '      <div class="egypt-header-top">',
    '        <div class="egypt-header-icon">𓏢</div>',
    '        <div class="egypt-header-center">',
    `          <h1>${e(infog.titulo || 'ANTIGUO EGIPTO')}</h1>`,
    infog.subtitulo ? `          <span class="egypt-sheet-sub">${e(infog.subtitulo)}</span>` : '',
    '        </div>',
    '      </div>',
    '    </header>',
    marcoList.length ? [
      '    <section class="egypt-block block-historical">',
      '      <div class="egypt-block-title-row">',
      '        <span class="egypt-num-badge">1</span>',
      '        <div><h3>Marco contextual</h3></div>',
      '      </div>',
      '      <div class="egypt-hist-body">',
      marcoList.map(p => `        <p>${e(p)}</p>`).join('\n'),
      '      </div>',
      '    </section>'
    ].join('\n') : '',
    funciones.length ? [
      '    <section class="egypt-block block-functions">',
      '      <div class="egypt-block-title-row">',
      '        <span class="egypt-num-badge">2</span>',
      '        <div><h3>Funciones sociales y religiosas</h3></div>',
      '      </div>',
      '      <div class="egypt-functions-grid">',
      funciones.map(f => [
        '        <div class="egypt-fn-card">',
        `          <strong>${e(f.funcion || '')}</strong>`,
        f.contexto ? `          <p>${e(f.contexto)}</p>` : '',
        f.repertorio ? `          <small><em>${e(f.repertorio)}</em></small>` : '',
        '        </div>'
      ].join('\n')).join('\n'),
      '      </div>',
      '    </section>'
    ].join('\n') : '',
    '  </div>',
    '  <div id="egypt-page-2" class="egypt-sheet" style="display:none">',
    organologia.length ? [
      '    <section class="egypt-block block-organology">',
      '      <div class="egypt-block-title-row">',
      '        <span class="egypt-num-badge">3</span>',
      '        <div><h3>Organología</h3></div>',
      '      </div>',
      '      <div class="egypt-instruments-grid">',
      organologia.map(o => [
        '        <div class="egypt-inst-card">',
        `          <strong>${e(o.familia || '')}</strong>`,
        o.instrumentos ? `          <p><strong>Instrumentos:</strong> ${e(o.instrumentos)}</p>` : '',
        o.contexto ? `          <small>${e(o.contexto)}</small>` : '',
        '        </div>'
      ].join('\n')).join('\n'),
      '      </div>',
      '    </section>'
    ].join('\n') : '',
    fuentes.length ? [
      '    <section class="egypt-block block-sources">',
      '      <div class="egypt-block-title-row">',
      '        <span class="egypt-num-badge">4</span>',
      '        <div><h3>Fuentes e iconografía</h3></div>',
      '      </div>',
      '      <ul>',
      fuentes.map(fi => `        <li>${e(fi)}</li>`).join('\n'),
      '      </ul>',
      '    </section>'
    ].join('\n') : '',
    '  </div>',
    '</div>'
  ].join('\n');
}
