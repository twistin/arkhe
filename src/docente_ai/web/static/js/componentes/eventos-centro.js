import {request, token} from '../api.js';
import {e, toast} from '../ui.js';
import {store} from '../state.js';

function fechaEvento(evento) {
  return new Intl.DateTimeFormat('es', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Madrid'
  }).format(new Date(evento.inicio));
}

function filaEventoCentro(evento) {
  return `<li class="evento-centro ${evento.prioritario ? 'evento-prioritario' : ''}">` +
    `<div><strong>${e(evento.titulo)}</strong><span>${e(fechaEvento(evento))}</span></div>` +
    `<span>${e(evento.lugar || 'Lugar sin indicar en el documento')}</span></li>`;
}

export function panelEventosCentro() {
  const eventos = store.state.eventos_centro || [];
  if (!eventos.length) return '';
  const ahora = new Date();
  const pendientes = eventos.filter(evento => new Date(evento.inicio) >= ahora);
  const proximo = pendientes.find(evento => evento.prioritario) || pendientes[0];
  const aviso = proximo ? `<div class="evento-destacado"><span class="eyebrow">` +
    `${proximo.prioritario ? 'TU PRÓXIMA AUDICIÓN PRIORITARIA' : 'PRÓXIMO EVENTO DEL CENTRO'}</span>` +
    `<h2>${e(proximo.titulo)}</h2><p>${e(fechaEvento(proximo))} · ${e(proximo.lugar)}</p></div>` :
    '<p>El calendario del centro ha finalizado.</p>';
  return '<section class="panel eventos-centro" aria-label="Audiciones y conciertos del centro">' + aviso +
    '<details><summary>Ver todas las audiciones y conciertos</summary>' +
    `<ul class="eventos-centro-lista">${eventos.map(filaEventoCentro).join('')}</ul></details>` +
    '<div class="dialog-actions"><button class="button small" data-action="download-center-events">' +
    'Añadir todo a mi calendario</button><button class="button small primary" ' +
    'data-action="download-priority-events">Añadir solo las prioritarias</button></div>' +
    '<p class="field-note">El archivo de calendario incluye avisos un día y una hora antes. ' +
    'Impórtalo en tu calendario y activa sus notificaciones para recibirlos con Arkhé cerrada.</p></section>';
}

async function descargarEventos(soloPrioritarios) {
  const respuesta = await request('/api/eventos-centro.ics' + (soloPrioritarios ? '?prioritarios=1' : ''), {
    headers: {'X-Docente-Token': token}
  });
  if (!respuesta.ok) throw new Error('No se pudo descargar el calendario del centro.');
  const url = URL.createObjectURL(await respuesta.blob());
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = soloPrioritarios ? 'audiciones-prioritarias.ics' : 'audiciones-centro.ics';
  enlace.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
  toast('Importa el archivo en tu calendario para activar los recordatorios.');
}

async function accionDescargarEventosCentro() {
  await descargarEventos(false);
}

async function accionDescargarEventosPrioritarios() {
  await descargarEventos(true);
}

export const actions = {
  'download-center-events': accionDescargarEventosCentro,
  'download-priority-events': accionDescargarEventosPrioritarios,
};
