import { e } from '../../ui.js';

export function renderEscaleraIntervalos(data) {
  const svgContent = data?.svg || '';

  return [
    `<div class="didactic-component-card didactic-escalera-card" data-component-type="escalera_intervalos">`,
    `  <div class="didactic-head">`,
    `    <div>`,
    `      <span class="badge info">✓ Calculado a partir de la teoría</span>`,
    `      <h4>${e(data?.titulo || 'Escalera de Intervalos en Cents')}</h4>`,
    `      <p class="didactic-desc">` +
    `${e(data?.descripcion || 'Comparativa de las dimensiones interválicas en cents de los tres géneros.')}</p>`,
    `    </div>`,
    `  </div>`,
    `  <div class="didactic-visual-container">`,
    svgContent ? `    <div class="didactic-svg-wrapper">${svgContent}</div>` : '',
    `  </div>`,
    `</div>`,
  ].join('');
}
