import { e, icon } from '../../ui.js';
import { playFrequency, playFrequencySequence } from './audio.js';

export function renderGranSistemaPerfecto(data) {
  const svgContent = data?.svg || '';
  const af = data?.afinados || {};
  const freqsPit = af.pitagorica || data?.frecuencias_hz || [];
  const freqsTemp = af.temperada || data?.frecuencias_hz || [];
  const subtitulo = data?.subtitulo || (
    'dos pares de tetracordos conjuntos separados por una disyunción, ' +
    'más el proslambanómenos; synemmenon como tetracordo conjunto alternativo'
  );

  return [
    `<div class="didactic-component-card didactic-gsp-card" data-component-type="gran_sistema_perfecto">`,
    `  <div class="didactic-head">`,
    `    <div>`,
    `      <span class="badge info">✓ Calculado a partir de la teoría</span>`,
    `      <h4>${e(data?.titulo || 'Gran Sistema Perfecto (Systema Teleion Meizon)')}</h4>`,
    `      <p class="didactic-desc">${e(subtitulo)}</p>`,
    `    </div>`,
    `    <div class="didactic-controls">`,
    `      <div class="tuning-selector" data-component="gsp">`,
    `        <span class="tuning-label">Afinación:</span>`,
    `        <button type="button" class="button small tuning-btn active" data-tuning="pitagorica">` +
    `Pitagórica</button>`,
    `        <button type="button" class="button small tuning-btn" data-tuning="temperada">` +
    `Temperada</button>`,
    `      </div>`,
    `      <button type="button" class="button small primary play-gsp-all-btn" ` +
    `data-freqs-pit="${e(JSON.stringify(freqsPit))}" data-freqs-temp="${e(JSON.stringify(freqsTemp))}">`,
    `        ${icon('play')}Reproducir 15 notas (La2 → La4)`,
    `      </button>`,
    `    </div>`,
    `  </div>`,
    `  <div class="didactic-visual-container">`,
    svgContent ? `    <div class="didactic-svg-wrapper">${svgContent}</div>` : '',
    `  </div>`,
    `  <div class="gsp-notes-grid">`,
    (data?.notas || []).map((n, i) => {
      const fPit = Number(n.freq_pitagorica || freqsPit[i] || 110);
      const fTemp = Number(n.freq_temperada || freqsTemp[i] || 110);
      return [
        `    <div class="gsp-note-card" data-note-idx="${e(i)}">`,
        `      <div class="gsp-note-head-row">`,
        `        <span class="gsp-card-modern">${e(n.nota_moderna)}</span>`,
        `        <button type="button" class="button small ghost gsp-note-play" ` +
        `data-freq="${e(fPit)}" data-freq-pit="${e(fPit)}" data-freq-temp="${e(fTemp)}">`,
        `          ${icon('play')}`,
        `        </button>`,
        `      </div>`,
        `      <div class="gsp-card-greek">${e(n.nombre_griego)}</div>`,
        `      <div class="gsp-card-hz"><span class="gsp-hz-val">${e(fPit.toFixed(1))}</span> Hz</div>`,
        `    </div>`,
      ].join('');
    }).join(''),
    `  </div>`,
    `</div>`,
  ].join('');
}

export function initGranSistemaPerfectoEvents(container) {
  // Selector de afinación
  container.querySelectorAll('.tuning-selector[data-component="gsp"] .tuning-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.didactic-gsp-card');
      if (!card) return;
      card.querySelectorAll('.tuning-selector[data-component="gsp"] .tuning-btn').forEach(b => {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      const tuning = btn.dataset.tuning;

      // Actualizar tarjetas de notas
      card.querySelectorAll('.gsp-note-card').forEach(nc => {
        const playBtn = nc.querySelector('.gsp-note-play');
        if (!playBtn) return;
        const f = tuning === 'temperada' ? playBtn.dataset.freqTemp : playBtn.dataset.freqPit;
        playBtn.dataset.freq = f;
        const hzSpan = nc.querySelector('.gsp-hz-val');
        if (hzSpan) hzSpan.textContent = parseFloat(f).toFixed(1);
      });

      // Actualizar frecuencias en el SVG
      card.querySelectorAll('.gsp-note-hz').forEach(th => {
        const idx = th.dataset.gspHzIdx;
        const circle = card.querySelector(`circle[data-index="${idx}"]`);
        if (circle) {
          const f = tuning === 'temperada' ? circle.dataset.freqTemp : circle.dataset.freqPit;
          if (f) th.textContent = `${parseFloat(f).toFixed(1)} Hz`;
        }
      });
    });
  });

  // Reproducir todas las notas
  container.querySelectorAll('.play-gsp-all-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.didactic-gsp-card');
      const tuning = card?.querySelector('.tuning-selector[data-component="gsp"] .tuning-btn.active')?.dataset.tuning;
      const raw = tuning === 'temperada' ? btn.dataset.freqsTemp : btn.dataset.freqsPit;
      try {
        const freqs = JSON.parse(raw || '[]');
        if (freqs.length) playFrequencySequence(freqs, 0.4, 0.05);
      } catch (err) {
        console.error('Error al reproducir GSP:', err);
      }
    });
  });

  // Botón individual de nota
  container.querySelectorAll('.gsp-note-play').forEach(btn => {
    btn.addEventListener('click', () => {
      const f = parseFloat(btn.dataset.freq);
      if (f && !isNaN(f)) playFrequency(f, 0.6);
    });
  });

  // Clic directo sobre nodos circulares en el SVG
  container.querySelectorAll('.didactic-gsp circle[data-index]').forEach(circle => {
    circle.addEventListener('click', () => {
      const card = circle.closest('.didactic-gsp-card');
      const tuning = card?.querySelector('.tuning-selector[data-component="gsp"] .tuning-btn.active')?.dataset.tuning;
      const fStr = tuning === 'temperada' ? circle.dataset.freqTemp : circle.dataset.freqPit;
      const f = parseFloat(fStr);
      if (f && !isNaN(f)) playFrequency(f, 0.6);
    });
  });
}
