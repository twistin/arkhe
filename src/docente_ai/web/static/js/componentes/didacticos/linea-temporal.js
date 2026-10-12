import { e } from '../../ui.js';

export function renderLineaTemporal(data) {
  const svgContent = data?.svg_alumnado || data?.svg || '';

  return [
    `<div class="didactic-component-card didactic-timeline-card" data-component-type="linea_temporal">`,
    `  <div class="didactic-head">`,
    `    <div>`,
    `      <span class="badge">Eje histórico y fuentes</span>`,
    `      <h4>${e(data?.titulo || 'Línea Temporal de Tratadistas de la Música Griega')}</h4>`,
    `      <p class="didactic-desc">` +
    `${e(data?.descripcion || 'Eje cronológico real de siglos (a. C. / d. C.) con autores y tratados.')}</p>`,
    `    </div>`,
    `  </div>`,
    `  <div class="didactic-visual-container">`,
    svgContent ? `    <div class="didactic-svg-wrapper">${svgContent}</div>` : '',
    `  </div>`,
    `</div>`,
  ].join('');
}
