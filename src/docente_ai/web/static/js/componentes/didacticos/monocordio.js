import { e, icon } from '../../ui.js';
import { playFrequency } from './audio.js';

export function renderMonocordio(data) {
  const svgContent = data?.svg || '';

  return [
    `<div class="didactic-component-card didactic-monocordio-card" data-component-type="monocordio">`,
    `  <div class="didactic-head">`,
    `    <div>`,
    `      <span class="badge info">✓ Calculado a partir de la teoría</span>`,
    `      <h4>${e(data?.titulo || 'Monocordio Pitagórico (Canon)')}</h4>`,
    `      <p class="didactic-desc">` +
    `${e(data?.descripcion || 'Cuerda dividida en 1/2 (octava), 2/3 (quinta) y 3/4 (cuarta).')}</p>`,
    `    </div>`,
    `    <div class="didactic-controls">`,
    `      <div class="tuning-selector" data-component="monocordio">`,
    `        <span class="tuning-label">Afinación:</span>`,
    `        <button type="button" class="button small tuning-btn active" data-tuning="pitagorica">` +
    `Pitagórica</button>`,
    `        <button type="button" class="button small tuning-btn" data-tuning="temperada">` +
    `Temperada</button>`,
    `      </div>`,
    `    </div>`,
    `  </div>`,
    `  <div class="didactic-visual-container">`,
    svgContent ? `    <div class="didactic-svg-wrapper">${svgContent}</div>` : '',
    `  </div>`,
    `  <div class="monocordio-buttons-row">`,
    (data?.divisiones || []).map(d => {
      const fPit = Number(d.freq_pitagorica || d.freq_hz || 220);
      const fTemp = Number(d.freq_temperada || d.freq_hz || 220);
      const nomProp = d.nombre_proporcion || d.proporcion || '';
      return [
        `    <button type="button" class="button small play-monocordio-btn" ` +
        `data-freq="${e(fPit)}" data-freq-pit="${e(fPit)}" data-freq-temp="${e(fTemp)}" ` +
        `data-frac="${e(d.fraccion)}">`,
        `      ${icon('play')}<strong>${e(d.fraccion)}</strong> · ` +
        `${e(d.intervalo_moderno)} — ${e(nomProp)} ` +
        `(<span class="mc-btn-hz">${e(fPit.toFixed(2))}</span> Hz)`,
        `    </button>`,
      ].join('');
    }).join(''),
    `  </div>`,
    `</div>`,
  ].join('');
}

export function initMonocordioEvents(container) {
  // Selector de afinación
  container.querySelectorAll('.tuning-selector[data-component="monocordio"] .tuning-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.didactic-monocordio-card');
      if (!card) return;
      card.querySelectorAll('.tuning-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tuning = btn.dataset.tuning;

      // Actualizar botones de división
      card.querySelectorAll('.play-monocordio-btn').forEach(b => {
        const f = tuning === 'temperada' ? b.dataset.freqTemp : b.dataset.freqPit;
        b.dataset.freq = f;
        const span = b.querySelector('.mc-btn-hz');
        if (span) span.textContent = parseFloat(f).toFixed(2);
      });

      // Actualizar etiquetas en el SVG
      card.querySelectorAll('.mc-bridge-mobile').forEach(bm => {
        const f = tuning === 'temperada' ? bm.dataset.freqTemp : bm.dataset.freqPit;
        const idx = bm.dataset.divIdx;
        const hzText = card.querySelector(`.mc-text-hz[data-mc-hz-idx="${idx}"]`);
        if (hzText && f) hzText.textContent = `${parseFloat(f).toFixed(2)} Hz`;
      });
    });
  });

  // Reproducción por botón
  container.querySelectorAll('.play-monocordio-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const f = parseFloat(btn.dataset.freq);
      if (f && !isNaN(f)) playFrequency(f, 0.7);
    });
  });

  // Clic directo sobre puentes en el SVG
  container.querySelectorAll('.mc-bridge-mobile').forEach(bm => {
    bm.addEventListener('click', () => {
      const card = bm.closest('.didactic-monocordio-card');
      const activeTuning = card?.querySelector('.tuning-btn.active')?.dataset.tuning || 'pitagorica';
      const fStr = activeTuning === 'temperada' ? bm.dataset.freqTemp : bm.dataset.freqPit;
      const f = parseFloat(fStr);
      if (f && !isNaN(f)) playFrequency(f, 0.7);
    });
  });
}
