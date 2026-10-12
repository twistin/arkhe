import { e, icon } from '../../ui.js';
import { playFrequencySequence } from './audio.js';

export const TETRACORDOS_DATOS = {
  pitagorica: {
    nombre: 'Afinación pitagórica exacta (proporciones puras)',
    diatonico: {
      cents: '(204 + 204 + 90 = 498 cents)',
      notas: [
        { nombre: 'Mi4', hz: '330.0 Hz', val: 330.0 },
        { nombre: 'Re4', hz: '293.3 Hz', val: 293.33 },
        { nombre: 'Do4', hz: '260.7 Hz', val: 260.74 },
        { nombre: 'Si3', hz: '247.5 Hz', val: 247.5 },
      ],
    },
    cromatico: {
      cents: '(294 + 114 + 90 = 498 cents)',
      notas: [
        { nombre: 'Mi4', hz: '330.0 Hz', val: 330.0 },
        { nombre: 'Do♯4', hz: '278.4 Hz', val: 278.44 },
        { nombre: 'Do♮4', hz: '260.7 Hz', val: 260.74 },
        { nombre: 'Si3', hz: '247.5 Hz', val: 247.5 },
      ],
    },
    enarmonico: {
      cents: '(408 + 45 + 45 = 498 cents)',
      notas: [
        { nombre: 'Mi4', hz: '330.0 Hz', val: 330.0 },
        { nombre: 'Do4', hz: '260.7 Hz', val: 260.74 },
        { nombre: 'si ↑¼', hz: '254.0 Hz', val: 254.04 },
        { nombre: 'Si3', hz: '247.5 Hz', val: 247.5 },
      ],
    },
  },
  temperada: {
    nombre: 'Temperamento igual moderno (12-EDO)',
    diatonico: {
      cents: '(200 + 200 + 100 = 500 cents)',
      notas: [
        { nombre: 'Mi4', hz: '329.6 Hz', val: 329.63 },
        { nombre: 'Re4', hz: '293.7 Hz', val: 293.66 },
        { nombre: 'Do4', hz: '261.6 Hz', val: 261.63 },
        { nombre: 'Si3', hz: '246.9 Hz', val: 246.94 },
      ],
    },
    cromatico: {
      cents: '(300 + 100 + 100 = 500 cents)',
      notas: [
        { nombre: 'Mi4', hz: '329.6 Hz', val: 329.63 },
        { nombre: 'Do♯4', hz: '277.2 Hz', val: 277.18 },
        { nombre: 'Do♮4', hz: '261.6 Hz', val: 261.63 },
        { nombre: 'Si3', hz: '246.9 Hz', val: 246.94 },
      ],
    },
    enarmonico: {
      cents: '(400 + 50 + 50 = 500 cents)',
      notas: [
        { nombre: 'Mi4', hz: '329.6 Hz', val: 329.63 },
        { nombre: 'Do4', hz: '261.6 Hz', val: 261.63 },
        { nombre: 'si ↑¼', hz: '254.2 Hz', val: 254.18 },
        { nombre: 'Si3', hz: '246.9 Hz', val: 246.94 },
      ],
    },
  },
};

export const TETRACORDOS_FRECUENCIAS = {
  pitagorica: {
    diatonico: [330.0, 293.33, 260.74, 247.5],
    cromatico: [330.0, 278.44, 260.74, 247.5],
    enarmonico: [330.0, 260.74, 254.04, 247.5],
  },
  temperada: {
    diatonico: [329.63, 293.66, 261.63, 246.94],
    cromatico: [329.63, 277.18, 261.63, 246.94],
    enarmonico: [329.63, 261.63, 254.18, 246.94],
  },
};

function renderGenreCard(key, title, sub, centsFormula, notes, color) {
  return [
    '      <div class="tc-genre-card" data-genre="' + e(key) + '" ',
    'style="background:#fff; border:1.5px solid #e2e8f0; border-radius:8px; padding:14px; height:auto;">',
    `        <h5 style="margin:0 0 4px; font-size:14px; color:#0f172a;">${e(title)}</h5>`,
    `        <p style="margin:0 0 4px; font-size:11px; color:#64748b;">${e(sub)}</p>`,
    '        <p class="tc-cents-formula" data-genre="' + e(key) + '" ',
    `style="margin:0 0 12px; font-size:11px; color:${e(color)}; font-weight:600;">${e(centsFormula)}</p>`,
    '        <div class="tc-notes-row" style="display:flex; justify-content:space-between; gap:6px;">',
    notes.map((n, idx) => {
      const isQuarter = n.nombre.includes('↑');
      const nColor = isQuarter ? '#dc2626' : '#0f172a';
      const hzColor = isQuarter ? '#dc2626' : color;
      const weight = isQuarter ? '700' : '600';
      return [
        '          <div class="tc-note-col" style="text-align:center;">',
        `            <strong style="display:block; font-size:12px; color:${e(nColor)};">${e(n.nombre)}</strong>`,
        '            <span class="tc-hz-val" data-genre="' + e(key) + '" data-idx="' + e(idx) + '" ',
        `style="font-size:11px; color:${e(hzColor)}; font-weight:${e(weight)};">${e(n.hz)}</span>`,
        '          </div>',
      ].join('\n');
    }).join('\n'),
    '        </div>',
    '      </div>',
  ].join('\n');
}

export function renderTetracordos(data) {
  const svgScore = data?.svg_partitura || data?.svg || '';

  const c1 = renderGenreCard(
    'diatonico',
    '1. Género Diatónico',
    'Tono – Tono – Semitono',
    '(204 + 204 + 90 = 498 cents)',
    TETRACORDOS_DATOS.pitagorica.diatonico.notas,
    '#0284c7'
  );

  const c2 = renderGenreCard(
    'cromatico',
    '2. Género Cromático',
    'Trihemitono – Semitono – Semitono',
    '(294 + 114 + 90 = 498 cents)',
    TETRACORDOS_DATOS.pitagorica.cromatico.notas,
    '#7c3aed'
  );

  const c3 = renderGenreCard(
    'enarmonico',
    '3. Género Enarmónico (cuartos de tono)',
    'Dítono – Díesis – Díesis',
    '(408 + 45 + 45 = 498 cents)',
    TETRACORDOS_DATOS.pitagorica.enarmonico.notas,
    '#be185d'
  );

  const scoreBox = svgScore
    ? [
        '    <div class="didactic-score-wrapper" ',
        'style="background:#fff; border-radius:6px; border:1.5px solid #e2e8f0; ',
        'padding:10px 14px; margin-bottom:14px; overflow-x:auto;">',
        svgScore,
        '    </div>',
      ].join('\n')
    : '';

  return [
    '<div class="didactic-component-card didactic-tetracordos-card" data-component-type="tetracordos">',
    '  <div class="didactic-head">',
    '    <div>',
    '      <span class="badge info">✓ Calculado a partir de la teoría</span>',
    `      <h4>${e(data?.titulo || 'Tetracordo descendente mi–si en los tres géneros')}</h4>`,
    '      <p class="didactic-desc">Subdivisión de la cuarta en géneros diatónico, cromático y enarmónico.</p>',
    '    </div>',
    '    <div class="didactic-controls">',
    '      <div class="tuning-selector" data-component="tetracordos">',
    '        <span class="tuning-label">Afinación:</span>',
    '        <button type="button" class="button small tuning-btn active" data-tuning="pitagorica">Pitagórica</button>',
    '        <button type="button" class="button small tuning-btn" data-tuning="temperada">Temperada</button>',
    '      </div>',
      '<button type="button" class="button small play-genre-btn" data-genre="diatonico">',
      `  ${icon('play')}Diatónico`,
      '</button>',
      '<button type="button" class="button small play-genre-btn" data-genre="cromatico">',
      `  ${icon('play')}Cromático`,
      '</button>',
      '<button type="button" class="button small play-genre-btn" data-genre="enarmonico">',
      `  ${icon('play')}Enarmónico (¼ tono)`,
      '</button>',
    '    </div>',
    '  </div>',
    '  <div class="didactic-visual-container">',
    scoreBox,
    '    <div class="tetracordos-cards-grid" ',
    'style="display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; height:auto;">',
    c1,
    c2,
    c3,
    '    </div>',
    '    <p class="tc-footer-badge" style="margin:10px 0 0; font-size:11px; color:#0284c7; font-weight:600;">',
    'Web Audio: afinación pitagórica exacta (proporciones puras)</p>',
    '  </div>',
    '</div>',
  ].join('\n');
}

export function initTetracordosEvents(container) {
  // Selector de afinación
  container.querySelectorAll('.tuning-selector[data-component="tetracordos"] .tuning-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.didactic-tetracordos-card');
      if (!card) return;
      card.querySelectorAll('.tuning-selector[data-component="tetracordos"] .tuning-btn').forEach(b => {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      const tuning = btn.dataset.tuning || 'pitagorica';
      const datos = TETRACORDOS_DATOS[tuning] || TETRACORDOS_DATOS.pitagorica;

      // Actualizar fórmulas de cents
      card.querySelectorAll('.tc-cents-formula').forEach(el => {
        const g = el.dataset.genre;
        if (g && datos[g]) el.textContent = datos[g].cents;
      });

      // Actualizar valores de frecuencias Hz
      card.querySelectorAll('.tc-hz-val').forEach(el => {
        const g = el.dataset.genre;
        const idx = Number(el.dataset.idx || 0);
        if (g && datos[g]?.notas?.[idx]) el.textContent = datos[g].notas[idx].hz;
      });

      // Actualizar pie informativo
      const badge = card.querySelector('.tc-footer-badge');
      if (badge) {
        badge.textContent = tuning === 'temperada'
          ? 'Web Audio: temperamento igual moderno (12-EDO)'
          : 'Web Audio: afinación pitagórica exacta (proporciones puras)';
      }
    });
  });

  // Reproducir géneros con Web Audio
  container.querySelectorAll('.play-genre-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.didactic-tetracordos-card');
      const tuning = card?.querySelector(
        '.tuning-selector[data-component="tetracordos"] .tuning-btn.active'
      )?.dataset.tuning || 'pitagorica';
      const g = btn.dataset.genre;
      const freqs = TETRACORDOS_FRECUENCIAS[tuning]?.[g] || TETRACORDOS_FRECUENCIAS.pitagorica[g];
      if (freqs) playFrequencySequence(freqs, 0.55, 0.08);
    });
  });
}
