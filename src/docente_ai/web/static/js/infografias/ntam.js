import { e } from '../ui.js';

// Módulo de infografía de NTAM: renderiza dinámicamente a partir de la ficha servida por la API.

export function renderNtamInfographic(run) {
  const ficha = run?.ficha;
  const infog = ficha?.infografia;
  if (!infog) {
    return '<div class="infographic-empty"><p>Sin contenido infográfico disponible.</p></div>';
  }

  const bloques = infog.bloques || [];

  return [
    '<div class="infographic-poster ntam-infographic-poster">',
    '  <div class="infographic-main-head">',
    '    <div class="info-tag-row">',
    `      <span class="info-badge">${e(ficha.tema || 'NTAM')}</span>`,
    `      <span class="info-badge-sub">${e(infog.titulo || '')}</span>`,
    '    </div>',
    `    <h2>${e(infog.titulo || 'NUEVAS TECNOLOGÍAS APLICADAS A LA MÚSICA')}</h2>`,
    infog.subtitulo ? `    <p class="info-subtitle">${e(infog.subtitulo)}</p>` : '',
    '  </div>',
    '  <div class="ntam-blocks-grid">',
    bloques.map((b, idx) => [
      '    <div class="ntam-block-card">',
      '      <div class="ntam-block-head">',
      `        <span class="ntam-num-badge">${e(idx + 1)}</span>`,
      `        <h3>${e(b.nombre || '')}</h3>`,
      '      </div>',
      b.descripcion ? `      <p>${e(b.descripcion)}</p>` : '',
      b.elementos && b.elementos.length ? [
        '      <ul>',
        b.elementos.map(el => `        <li>${e(el)}</li>`).join('\n'),
        '      </ul>'
      ].join('\n') : '',
      '    </div>'
    ].join('\n')).join('\n'),
    '  </div>',
    '</div>'
  ].join('\n');
}
