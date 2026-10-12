import { renderTetracordos, initTetracordosEvents } from './tetracordos.js';
import { renderGranSistemaPerfecto, initGranSistemaPerfectoEvents } from './gran-sistema-perfecto.js';
import { renderMonocordio, initMonocordioEvents } from './monocordio.js';
import { renderEscaleraIntervalos } from './escalera-intervalos.js';
import { renderLineaTemporal } from './linea-temporal.js';

export function renderDidacticComponent(comp) {
  if (!comp || !comp.tipo) return '';
  const tipo = String(comp.tipo).trim().toLowerCase();

  switch (tipo) {
    case 'tetracordos':
    case 'tetracordo':
      return renderTetracordos(comp);
    case 'gran_sistema_perfecto':
    case 'gsp':
    case 'sistema_perfecto':
      return renderGranSistemaPerfecto(comp);
    case 'monocordio':
    case 'monocordio_pitagorico':
    case 'canon':
      return renderMonocordio(comp);
    case 'escalera_intervalos':
    case 'escalera':
    case 'cents':
      return renderEscaleraIntervalos(comp);
    case 'linea_temporal':
    case 'cronologia':
    case 'timeline':
      return renderLineaTemporal(comp);
    default:
      return '';
  }
}

export function initDidacticInteractions(container) {
  if (!container) return;
  initTetracordosEvents(container);
  initGranSistemaPerfectoEvents(container);
  initMonocordioEvents(container);
}
