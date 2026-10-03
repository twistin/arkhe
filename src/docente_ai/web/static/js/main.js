// Registro de módulos, delegación de eventos y coordinación de la navegación.
import {store, view} from './state.js';
import {$, dialog, e, fail, icon, main, render} from './ui.js';
import {dailyAgenda} from './componentes/agenda.js';
import {checkStatus, monitor, refresh} from './componentes/trabajos.js';
import * as biblioteca from './vistas/biblioteca.js';
import * as diario from './vistas/diario.js';
import * as ajustes from './vistas/ajustes.js';
import * as asistente from './vistas/asistente.js';
import * as propuestas from './vistas/propuestas.js';
import * as consentimiento from './componentes/consentimiento.js';
import * as agenda from './componentes/agenda.js';
import * as documentos from './componentes/documentos.js';
import * as configuracion from './componentes/configuracion.js';
import * as trabajos from './componentes/trabajos.js';
import * as material_alumnado from './componentes/material-alumnado.js';
import * as audiciones from './componentes/audiciones.js';
import * as dialogo from './componentes/dialogo.js';

const modules = [
  biblioteca,
  diario,
  ajustes,
  asistente,
  propuestas,
  consentimiento,
  agenda,
  documentos,
  configuracion,
  trabajos,
  material_alumnado,
  audiciones,
  dialogo,
];
const actions = new Map(), forms = new Map();
function register(target, entries, label) {
  for (const [name, handler] of Object.entries(entries || {})) {
    if (target.has(name)) throw new Error(`Registro duplicado de ${label}: ${name}`);
    target.set(name, handler);
  }
}
for (const module of modules) {
  register(actions, module.actions, 'acción');
  register(forms, module.forms, 'formulario');
}
const bindings = modules.flatMap(module => module.clickBindings || []).sort((a, b) => a.priority - b.priority);
function findHandler(map, name) {
  const handler = map.get(name);
  if (!handler) throw new Error(`No hay manejador registrado: ${name}`);
  return handler;
}
const {library} = biblioteca, {assistant} = asistente, {proposals} = propuestas;
const {diary} = diario, {settings} = ajustes;

export function renderPage() {
  if (store.isClosed) {
    main.innerHTML =
      '<section class="empty-library"><h2>Tu espacio está cerrado.</h2><p>Todo queda ' +
        'guardado. Abre Arkhe.app para volver a trabajar.</p></section>';
    return;
  }
  const focused = document.activeElement,
    focusId = main.contains(focused) ? focused.id : null,
    selectionStart = focused?.selectionStart,
    selectionEnd = focused?.selectionEnd;
  const active = view();
  const indicators = [store.state.provider_info?.indicator, store.state.pedagogy_provider_info?.indicator]
    .filter(Boolean);
  $('#generation-indicator').textContent = [...new Set(indicators)].join(' · ') || 'Proveedor sin configurar';
  document.querySelectorAll('[data-nav]').forEach(link => {
    link.classList.toggle('active', link.dataset.nav === active);
    if (link.dataset.nav === active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  $('#section-name').textContent = ({
    biblioteca: 'Biblioteca',
    asistente: 'Asistente',
    propuestas: 'Propuestas',
    diario: 'Diario docente',
    ajustes: 'Ajustes'
  })[active];
  document.title = `Arkhé · ${$('#section-name').textContent}`;
  main.className = 'content-enter';
  main.innerHTML = dailyAgenda() + ({
    biblioteca: library,
    asistente: assistant,
    propuestas: proposals,
    diario: diary,
    ajustes: settings
  })[active]();
  if (store.state.server_mode) {
    document.querySelectorAll('[data-action="reveal"], [data-action="reveal-diary"], ' +
      '[data-action="shutdown"], [data-action="shutdown-dialog"], ' +
      '[data-action="delete-api-key"]').forEach(node => node.remove());
    document.querySelectorAll('[data-reveal-record]').forEach(node => {
      node.textContent = 'Descargar sesión';
    });
    document.querySelector('.local-note').textContent = 'Biblioteca privada · Servidor UE';
    document.querySelectorAll('input[name="api_key"]').forEach(node => {
      node.disabled = true;
      node.placeholder = 'Clave administrada en el servidor';
    });
    document.querySelectorAll('select[name="provider"] option').forEach(node => {
      if (node.value !== 'mistral') node.remove();
    });
    document.querySelectorAll('.path').forEach(node => { node.textContent = 'Biblioteca privada del servidor'; });
  }
  if (focusId) {
    const field = document.getElementById(focusId);
    field?.focus({
      preventScroll: true
    });
    if (typeof selectionStart === 'number' && field?.setSelectionRange) field.setSelectionRange(
      selectionStart, selectionEnd);
  }
}

document.querySelectorAll('[data-icon]').forEach(el => el.innerHTML = icon(el.dataset.icon));
document.addEventListener('enjambre:render', renderPage);
document.addEventListener('enjambre:navigate', event => {
  location.hash = event.detail;
});
document.addEventListener('click', async event => {
  if (event.target.closest('.skip')) {
    event.preventDefault();
    main.focus();
    return;
  }
  const target = event.target.closest('button,a[data-nav]');
  if (!target) return;
  const name = bindings.find(binding => binding.matches(target))?.action || target.dataset.action;
  if (!name) return;
  try {
    await findHandler(actions, name)({target, event});
  } catch (error) {
    fail(error);
    target.disabled = false;
  }
});
for (const module of modules) {
  for (const [type, selectors] of Object.entries(module.events || {})) {
    document.addEventListener(type, event => {
      for (const [selector, handler] of Object.entries(selectors)) {
        if (event.target.closest(selector)) handler(event);
      }
    });
  }
  for (const [type, handler] of Object.entries(module.windowEvents || {})) window.addEventListener(type, handler);
}
document.addEventListener('input', event => {
  const form = event.target.closest('form');
  if (form?.id && event.target.name) {
    store.drafts[form.id] ??= {};
    store.drafts[form.id][event.target.name] = event.target.value;
  }
});
document.addEventListener('submit', async event => {
  const form = event.target.closest('[data-form]');
  if (!form) return;
  event.preventDefault();
  const button = $('[type="submit"]', form) || $('button:not([type="button"])', form);
  const data = Object.fromEntries(new FormData(form));
  const buttonLabel = button?.innerHTML;
  if (button) button.disabled = true;
  const errorNode = $('.form-error', dialog.open ? dialog : form);
  if (errorNode) errorNode.textContent = '';
  try {
    await findHandler(forms, form.dataset.form)({form, data, button, event});
  } catch (error) {
    fail(error);
  } finally {
    if (button?.isConnected) {
      button.disabled = false;
      button.innerHTML = buttonLabel;
    }
  }
});
window.addEventListener('hashchange', () => {
  if (store.state) {
    render();
    window.scrollTo(0, 0);
  }
});
export async function boot() {
  try {
    await refresh();
    store.state.jobs.forEach(j => store.knownJobs.set(j.id, j.status));
    await monitor();
    checkStatus().catch(fail);
    store.monitorTimer = setInterval(monitor, 3000);
  } catch (error) {
    main.innerHTML = [
      `<section class="error-state"><h2>No se pudo abrir el espacio.</h2><p>${e(error.message)}`,
      `</p><button class="button" data-action="reload">Volver a intentar</button></section>`
    ].join('');
  }
}
boot();
