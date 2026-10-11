import { e } from '../ui.js';

// Módulo de infografía musical: renderiza dinámicamente a partir de la ficha servida por la API.

export function renderEjemploPendiente() {
  return [
    '<div class="ejemplo-pendiente-caja">',
    '  <span class="ejemplo-pendiente-icono">🎼</span>',
    '  <span class="ejemplo-pendiente-texto">Ejemplo musical pendiente de añadir al catálogo</span>',
    '</div>'
  ].join('\n');
}

export function renderFichaScoreBox(ej, runId = '') {
  if (!ej) return renderEjemploPendiente();
  const candId = ej.cand_id || ej.id;
  const isTenor = ej.voz_destacada === 'tenor' || ej.categoria === 'cantus_firmus';
  const compDef = ej.compases_defecto || [1, 12];
  const startC = compDef[0] || 1;
  const endC = compDef[1] || 12;

  return [
    `<div class="cantus-firmus-box-wrapper score-candidate-item" ` +
    `data-candidate-id="${e(candId)}" data-voice="${e(ej.voz_destacada || '')}" ` +
    `data-tenor-highlight="${isTenor ? 'true' : 'false'}">`,
    '  <div class="cf-controls-header">',
    '    <div class="cf-title-row">',
    `      <strong>${e(ej.titulo || 'Ejemplo')}</strong>`,
    isTenor ? '      <span class="badge accent-amber">★ Tenor resaltado</span>' : '',
    ej.verificado
      ? '      <span class="badge accent-green">✓ Verificado</span>'
      : '      <span class="badge accent-muted">JRP · CC BY-NC 4.0 (Pendiente de usar)</span>',
    '    </div>',
    '    <div class="candidate-controls">',
    '      <div class="score-mode-toggle">',
    '        <button type="button" class="score-mode-btn active" data-mode="svg">🎼 Partitura</button>',
    '        <button type="button" class="score-mode-btn" data-mode="pianoroll">🎹 Piano roll</button>',
    '      </div>',
    '      <label class="range-label">Compases: ',
    `        <input type="number" class="score-start-input" min="1" max="99" value="${e(startC)}"> a `,
    `        <input type="number" class="score-end-input" min="1" max="99" value="${e(endC)}">`,
    '      </label>',
    `      <button type="button" class="button small ghost play-score-btn" data-candidate="${e(candId)}">`,
    '        ▶ Reproducir',
    '      </button>',
    !ej.verificado
      ? `      <button type="button" class="button small primary adopt-score-btn" ` +
        `data-run-id="${e(runId)}" data-candidate="${e(candId)}">Usar</button>`
      : '',
    '    </div>',
    '  </div>',
    `  <div class="score-preview-box" data-candidate-id="${e(candId)}" ` +
    `data-current-mode="svg" data-voice="${e(ej.voz_destacada || '')}">`,
    '    <div class="score-loading"><span class="spinner"></span> Renderizando partitura con Verovio…</div>',
    '  </div>',
    '</div>'
  ].join('\n');
}

export function renderCantusFirmusBox(cfEjemplo = null) {
  if (!cfEjemplo) {
    return [
      '<div class="cantus-firmus-box-wrapper" data-tenor-highlight="true">',
      '  <div class="cf-controls-header">',
      '    <div class="cf-title-row">',
      '      <strong>Cantus firmus en el Tenor</strong>',
      '      <span class="badge accent-amber">★ Tenor resaltado</span>',
      '    </div>',
      '    <div class="score-mode-toggle">',
      '      <button type="button" class="score-mode-btn" data-mode="svg">🎼 Partitura</button>',
      '      <button type="button" class="score-mode-btn active" data-mode="pianoroll">🎹 Piano roll</button>',
      '    </div>',
      '  </div>',
      renderEjemploPendiente(),
      '</div>'
    ].join('\n');
  }
  return renderFichaScoreBox(cfEjemplo);
}

export function renderStudentInfographic(run) {
  const ficha = run?.ficha;
  const infog = ficha?.infografia;
  if (!infog) {
    return '<div class="infographic-empty"><p>Sin contenido infográfico disponible.</p></div>';
  }

  const runId = run?.id || '';
  const ejemplos = (run?.ficha_ejemplos && run.ficha_ejemplos.length)
    ? run.ficha_ejemplos
    : (ficha?.ejemplos_musicales || []);
  const cfEj = ejemplos.find(x => x.categoria === 'cantus_firmus') || null;
  const pfEj = ejemplos.find(x => x.categoria === 'parafrasis') || null;
  const vvEj = ejemplos.find(x => x.categoria === 'varias_voces_chanson') || null;
  const isorritmiaEj = ejemplos.find(x => x.categoria === 'isorritmia') || null;
  const lhommeEj = ejemplos.find(x => x.categoria === 'lhomme_arme') || null;

  const modelos = infog.modelos_misa || [];
  const modelosEjemplos = [cfEj, pfEj, vvEj];

  const tecnicas = infog.tecnicas || {};
  const paso1 = tecnicas.paso_1 || {};
  const paso2 = tecnicas.paso_2 || {};
  const paso3 = tecnicas.paso_3 || {};

  return [
    '<div class="infographic-poster">',
    '  <div class="infographic-main-head">',
    '    <div class="info-tag-row">',
    `      <span class="info-badge">${e(ficha.tema || 'TEMA')}</span>`,
    `      <span class="info-badge-sub">${e(infog.titulo || '')}</span>`,
    '    </div>',
    `    <h2>${e(infog.titulo || '')}</h2>`,
    infog.subtitulo ? `    <p class="info-subtitle">${e(infog.subtitulo)}</p>` : '',
    '  </div>',
    '  <div class="infographic-grid">',
    '    <div class="infographic-panel panel-left">',
    '      <div class="panel-header-bar">',
    '        <span class="panel-number">1</span>',
    '        <div>',
    `          <h3>${e(infog.titulo || 'MODELOS DE MISA')}</h3>`,
    '        </div>',
    '      </div>',
    modelos.map((m, idx) => {
      const ejAsociado = modelosEjemplos[idx] || null;
      return [
        '      <div class="model-block">',
        '        <div class="model-header-row">',
        '          <div class="model-title-group">',
        `            <span class="model-circle-badge">${e(idx + 1)}</span>`,
        '            <div>',
        `              <h4>${e(m.nombre || '')}</h4>`,
        `              <small class="model-meta">${e(m.disposicion || '')}</small>`,
        '            </div>',
        '          </div>',
        '        </div>',
        '        <div class="model-body-grid">',
        renderFichaScoreBox(ejAsociado, runId),
        '          <div class="model-side-info">',
        '            <div class="model-chars-card">',
        '              <strong>CARACTERÍSTICAS</strong>',
        '              <ul>',
        (m.caracteristicas || []).map(c => `                <li>${e(c)}</li>`).join('\n'),
        '              </ul>',
        '            </div>',
        m.ejemplo ? [
          '            <div class="model-example-card">',
          '              <span class="ex-badge">EJEMPLO</span>',
          `              <strong>${e(m.ejemplo)}</strong>`,
          m.ejemplo_descripcion ? `              <p>${e(m.ejemplo_descripcion)}</p>` : '',
          '            </div>'
        ].join('\n') : '',
        '          </div>',
        '        </div>',
        '      </div>'
      ].join('\n');
    }).join('\n'),
    '    </div>',
    '    <div class="infographic-panel panel-right">',
    '      <div class="panel-header-bar accent-wine">',
    '        <span class="panel-number">2</span>',
    '        <div>',
    `          <h3>${e(paso2.titulo || 'TÉCNICAS DE COMPOSICIÓN')}</h3>`,
    paso2.descripcion ? `          <span class="panel-sub">${e(paso2.descripcion)}</span>` : '',
    '        </div>',
    '      </div>',
    '      <div class="step-card">',
    '        <div class="step-title-row">',
    '          <span class="step-badge">1</span>',
    '          <div>',
    `            <strong>${e(paso1.titulo || 'Selección del material')}</strong>`,
    paso1.descripcion ? `            <p>${e(paso1.descripcion)}</p>` : '',
    '          </div>',
    '        </div>',
    '        <div class="source-branches-grid">',
    (paso1.procedimientos || []).map(p => [
      '          <div class="source-branch-card">',
      '            <div class="branch-head">',
      `              <strong>${e(p.nombre || '')}</strong>`,
      '            </div>',
      '            <ul>',
      (p.detalles || []).map(d => `              <li>${e(d)}</li>`).join('\n'),
      '            </ul>',
      p.resultado ? `            <div class="branch-examples"><em>${e(p.resultado)}</em></div>` : '',
      '          </div>'
    ].join('\n')).join('\n'),
    '        </div>',
    '      </div>',
    '      <div class="flow-arrow-down">⬇</div>',
    '      <div class="step-card">',
    '        <div class="step-title-row">',
    '          <span class="step-badge">2</span>',
    '          <div>',
    `            <strong>${e(paso2.titulo || 'Técnicas')}</strong>`,
    paso2.descripcion ? `            <p>${e(paso2.descripcion)}</p>` : '',
    '          </div>',
    '        </div>',
    '        <div class="treatment-cols-grid">',
    (paso2.procedimientos || []).map(p => [
      '          <div class="treatment-box">',
      `            <strong>${e(p.nombre || '')}</strong>`,
      '            <ul>',
      (p.detalles || []).map(d => `              <li>${e(d)}</li>`).join('\n'),
      '            </ul>',
      p.resultado ? `            <div class="treatment-res"><small>${e(p.resultado)}</small></div>` : '',
      '          </div>'
    ].join('\n')).join('\n'),
    '        </div>',
    '      </div>',
    '      <div class="flow-arrow-down">⬇</div>',
    '      <div class="step-card">',
    '        <div class="step-title-row">',
    '          <span class="step-badge">3</span>',
    '          <div>',
    `            <strong>${e(paso3.titulo || 'Unificación')}</strong>`,
    paso3.descripcion ? `            <p>${e(paso3.descripcion)}</p>` : '',
    '          </div>',
    '        </div>',
    '        <div class="unification-cards-grid">',
    (paso3.recursos || []).map((r, idx) => {
      const extraScore = idx === 0 ? isorritmiaEj : lhommeEj;
      return [
        '          <div class="unification-card">',
        '            <div class="u-card-head">',
        `              <strong>${e(r.nombre || '')}</strong>`,
        r.subtitulo ? `              <small>(${e(r.subtitulo)})</small>` : '',
        '            </div>',
        renderFichaScoreBox(extraScore, runId),
        '            <ul>',
        (r.detalles || []).map(d => `              <li>${e(d)}</li>`).join('\n'),
        '            </ul>',
        '          </div>'
      ].join('\n');
    }).join('\n'),
    '        </div>',
    '      </div>',
    '    </div>',
    '  </div>',
    '  <div class="infographic-footer-banner">',
    `    <span>${e(infog.subtitulo || ficha.tema || '')}</span>`,
    '  </div>',
    '</div>'
  ].join('\n');
}
