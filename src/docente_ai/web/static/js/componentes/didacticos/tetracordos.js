import { e, icon } from '../../ui.js';
import { playFrequencySequence } from './audio.js';

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

export function renderTetracordos(data) {
  const svgContent = data?.svg || '';

  return [
    `<div class="didactic-component-card didactic-tetracordos-card" data-component-type="tetracordos">`,
    `  <div class="didactic-head">`,
    `    <div>`,
    `      <span class="badge info">✓ Calculado a partir de la teoría</span>`,
    `      <h4>${e(data?.titulo || 'Tetracordo descendente mi–si en los tres géneros')}</h4>`,
    `      <p class="didactic-desc">` +
    `${e(data?.descripcion || 'Subdivisión de la cuarta justa en géneros diatónico, cromático y enarmónico.')}</p>`,
    `    </div>`,
    `    <div class="didactic-controls">`,
    `      <div class="tuning-selector" data-component="tetracordos">`,
    `        <span class="tuning-label">Afinación:</span>`,
    `        <button type="button" class="button small tuning-btn active" data-tuning="pitagorica">` +
    `Pitagórica</button>`,
    `        <button type="button" class="button small tuning-btn" data-tuning="temperada">` +
    `Temperada</button>`,
    `      </div>`,
    `      <button type="button" class="button small play-genre-btn" data-genre="diatonico">`,
    `        ${icon('play')}Diatónico`,
    `      </button>`,
    `      <button type="button" class="button small play-genre-btn" data-genre="cromatico">`,
    `        ${icon('play')}Cromático`,
    `      </button>`,
    `      <button type="button" class="button small play-genre-btn" data-genre="enarmonico">`,
    `        ${icon('play')}Enarmónico (¼ tono)`,
    `      </button>`,
    `    </div>`,
    `  </div>`,
    `  <div class="didactic-visual-container">`,
    svgContent ? `    <div class="didactic-svg-wrapper">${svgContent}</div>` : '',
    `  </div>`,
    `</div>`,
  ].join('');
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
      const tuning = btn.dataset.tuning;

      // Actualizar etiquetas en el SVG
      card.querySelectorAll('.tc-hz-label').forEach(lbl => {
        const f = tuning === 'temperada' ? lbl.dataset.freqTemp : lbl.dataset.freqPit;
        if (f) lbl.textContent = f;
      });

      // Actualizar pie informativo
      card.querySelectorAll('.tc-badge').forEach(badge => {
        badge.textContent = tuning === 'temperada'
          ? 'Web Audio: temperamento igual (12-TET)'
          : 'Web Audio: afinación pitagórica exacta';
      });
    });
  });

  // Reproducir géneros
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
