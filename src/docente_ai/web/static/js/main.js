// Módulo local: responsabilidad separada sin alterar el contenido.
import {
  api,
  request,
  token
} from './api.js';
import {
  dailyAgenda
} from './componentes/agenda.js';
import {
  groupModal,
  subjectModal
} from './componentes/configuracion.js';
import {
  ensureRemoteConsent
} from './componentes/consentimiento.js';
import {
  sourcesModal,
  teacherWorkedExample
} from './componentes/documentos.js';
import {
  printStudentDocument,
  studentMaterialModal
} from './componentes/material-alumnado.js';
import {
  checkStatus,
  monitor,
  openRun,
  queue,
  refresh
} from './componentes/trabajos.js';
import {
  switchEgyptTab
} from './infografias/egipto.js';
import {
  store,
  view
} from './state.js';
import {
  $,
  dateLabel,
  dialog,
  e,
  fail,
  icon,
  main,
  modal,
  render,
  runStatus,
  toast
} from './ui.js';
import {
  settings
} from './vistas/ajustes.js';
import {
  assistant
} from './vistas/asistente.js';
import {
  library,
  libraryResults,
  scanFolder,
  setFiles,
  showDocument,
  sourceModal
} from './vistas/biblioteca.js';
import {
  diary,
  existingFeedbackModal,
  feedbackModal,
  recordModal
} from './vistas/diario.js';
import {
  expandProposalModal,
  proposalModal,
  proposals,
  unitOptions
} from './vistas/propuestas.js';

export function renderPage() {
  if (store.isClosed) {
    main.innerHTML =
      '<section class="empty-library"><h2>Tu espacio está cerrado.</h2><p>Todo queda ' +
        'guardado. Abre Enjambre.app para volver a trabajar.</p></section>';
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
  document.title = `Enjambre · ${$('#section-name').textContent}`;
  main.className = 'content-enter';
  main.innerHTML = dailyAgenda() + ({
    biblioteca: library,
    asistente: assistant,
    propuestas: proposals,
    diario: diary,
    ajustes: settings
  })[active]();
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
  try {
    if (target.matches('.egypt-tab-btn')) switchEgyptTab(target, target.dataset.tab);
    if (target.dataset.document) {
      await showDocument(target.dataset.document);
      return;
    }
    if (target.dataset.run) {
      if (dialog.open) dialog.close();
      await openRun(target.dataset.run);
      return;
    }
    if (target.dataset.studentRun) {
      await studentMaterialModal(target.dataset.studentRun);
      return;
    }
    if (target.dataset.sourcesRun) {
      const run = store.currentRun && store.currentRun.id === target.dataset.sourcesRun ? store
        .currentRun : await api('/runs/' + encodeURIComponent(target.dataset.sourcesRun));
      sourcesModal(run);
      return;
    }
    if (target.dataset.copyStudent) {
      const response = await request('/api/runs/' + encodeURIComponent(target.dataset.copyStudent) +
        '?student=1', {
          headers: {
            'X-Docente-Token': token
          }
        });
      if (!response.ok) throw new Error('No se pudo preparar el material para el alumnado.');
      await navigator.clipboard.writeText(await response.text());
      toast('Material copiado. Ya puedes pegarlo en Google Classroom.');
      return;
    }
    if (target.dataset.copyCode) {
      const example = store.currentRun && store.currentRun.id === target.dataset.copyCode ?
        teacherWorkedExample(store.currentRun) : null;
      if (!example) throw new Error('No se encontró el ejemplo resuelto.');
      await navigator.clipboard.writeText(example.code);
      toast('Código copiado. Ya puedes pegarlo en tu editor.');
      return;
    }
    if (target.dataset.downloadStudent) {
      const identifier = target.dataset.downloadStudent;
      const response = await request('/api/runs/' + encodeURIComponent(identifier) + '?student=1', {
        headers: {
          'X-Docente-Token': token
        }
      });
      if (!response.ok) throw new Error('No se pudo descargar el material para el alumnado.');
      const url = URL.createObjectURL(await response.blob()),
        link = document.createElement('a');
      link.href = url;
      link.download = 'material-alumnado-' + identifier + '.md';
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      toast('Material para el alumnado descargado.');
      return;
    }
    if (target.dataset.downloadSources) {
      const identifier = target.dataset.downloadSources;
      const response = await request('/api/runs/' + encodeURIComponent(identifier) + '?sources=1', {
        headers: {
          'X-Docente-Token': token
        }
      });
      if (!response.ok) throw new Error('No se pudo descargar el anexo documental.');
      const url = URL.createObjectURL(await response.blob()),
        link = document.createElement('a');
      link.href = url;
      link.download = 'anexo-fuentes-' + identifier + '.md';
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 2000);
      toast('Anexo de fuentes y citas descargado.');
      return;
    }
    if (target.dataset.copyMarkdown) {
      const identifier = target.dataset.copyMarkdown;
      target.disabled = true;
      try {
        const response = await request('/api/runs/' + encodeURIComponent(identifier) + '?download=1', {
          headers: {
            'X-Docente-Token': token
          }
        });
        if (!response.ok) throw new Error('No se pudo obtener el texto Markdown.');
        const mdText = await response.text();
        await navigator.clipboard.writeText(mdText);
        toast('¡Markdown copiado al portapapeles!');
      } catch (err) {
        toast('Error al copiar: ' + (err.message || err), true);
      } finally {
        target.disabled = false;
      }
      return;
    }
    if (target.dataset.download || target.dataset.original || target.dataset.ocrDocument) {
      const identifier = target.dataset.download || target.dataset.original || target.dataset
        .ocrDocument;
      const isOrig = !!(target.dataset.original || target.dataset.ocrDocument);
      target.disabled = true;
      try {
        const response = await request('/api/' + (isOrig ? 'documents/' : 'runs/') + encodeURIComponent(
          identifier) + '?download=1' + (target.dataset.ocrDocument ? '&derived=1' : ''), {
          headers: {
            'X-Docente-Token': token
          }
        });
        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.error || 'No se pudo exportar el archivo.');
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const filename = isOrig ?
          (decodeURIComponent(response.headers.get('Content-Disposition')?.match(
              /filename\*=utf-8''([^;]+)/i)?.[1] || '') || response.headers.get('Content-Disposition')
            ?.match(/filename="([^"]+)"/)?.[1] || 'original') :
          'enjambre-' + identifier + '.md';
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(() => URL.revokeObjectURL(url), 2000);
        toast(isOrig ? 'Descargando documento…' : 'Descargando archivo Markdown (.md)…');
      } catch (err) {
        toast(err.message || 'Error al exportar.', true);
      } finally {
        target.disabled = false;
      }
      return;
    }
    if (target.dataset.deleteRun) {
      const runId = target.dataset.deleteRun;
      if (!confirm('¿Estás seguro de que deseas eliminar esta propuesta del historial?')) return;
      target.disabled = true;
      await api('/runs/' + encodeURIComponent(runId) + '/delete', {});
      if (store.currentRun && store.currentRun.id === runId) store.currentRun = null;
      if (dialog.open) dialog.close();
      await refresh();
      toast('Propuesta eliminada.');
      return;
    }
    if (target.dataset.deleteDocument) {
      const docId = target.dataset.deleteDocument;
      if (!confirm(
          '¿Estás seguro de que deseas eliminar este documento de tu biblioteca? Se ' +
            'eliminarán todas sus versiones y fragmentos procesados.'
        )) return;
      target.disabled = true;
      await api('/documents/' + encodeURIComponent(docId) + '/delete', {});
      if (dialog.open) dialog.close();
      await refresh();
      toast('Documento eliminado de la biblioteca.');
      return;
    }
    if (target.dataset.exclude) {
      target.disabled = true;
      await api('/documents/' + target.dataset.exclude + '/exclude', {});
      dialog.close();
      await refresh();
      toast('Fuente excluida. El asistente ya no puede utilizarla.');
      return;
    }
    if (target.dataset.editGroup) {
      groupModal(target.dataset.editGroup);
      return;
    }
    if (target.dataset.editSubject) {
      subjectModal(target.dataset.editSubject);
      return;
    }
    if (target.dataset.reviewApprove) {
      target.disabled = true;
      const result = await api('/runs/' + encodeURIComponent(target.dataset.reviewApprove) +
        '/review', {
          action: 'approved'
        });
      store.currentRun = {
        ...store.currentRun,
        ...result
      };
      render();
      toast('Propuesta aprobada. Puedes exportarla o guardar una copia.');
      return;
    }
    if (target.dataset.reviewReject) {
      const runId = target.dataset.reviewReject;
      modal('Rechazar propuesta', [
        [
          `<p>Puedes añadir una nota para recordar el motivo.</p><form data-form="reject" data-id="${e(runId)}`
        ].join(''),
        `"><div class="field"><label class="label" for="reject-notes">Notas `,
        `(opcional)</label><textarea id="reject-notes" name="notes" maxlength="2000" `,
        `placeholder="Motivo del rechazo o qué mejorar…"></textarea></div><div `,
        `class="form-error" role="alert"></div><div class="dialog-actions"><button `,
        `class="button ghost" type="button" data-action="close-dialog">Cancelar</button>`,
        [
          `<button class="button danger" type="submit">${icon('close')}Rechazar propuesta</button></div></form>`
        ].join('')
      ].join(''));
      return;
    }
    if (target.dataset.recordRun) {
      recordModal(target.dataset.recordRun, store.currentRun);
      return;
    }
    if (target.dataset.feedbackSession) {
      const session = store.state.agenda.sessions.find(item => item.id === target.dataset
        .feedbackSession);
      feedbackModal(session);
      return;
    }
    if (target.dataset.sessionRecord) {
      await existingFeedbackModal(target.dataset.sessionRecord);
      return;
    }
    if (target.dataset.revealRecord) {
      await api('/records/' + encodeURIComponent(target.dataset.revealRecord) + '/reveal', {});
      return;
    }
    if (target.dataset.expandProposal) {
      expandProposalModal(store.currentRun);
      return;
    }
    if (target.dataset.prepareSession) {
      const session = store.state.agenda.sessions.find(item => item.id === target.dataset
        .prepareSession);
      if (session) proposalModal(session);
      return;
    }
    if ('period' in target.dataset) {
      store.selectedPeriod = target.dataset.period;
      render();
      return;
    }
    if ('subject' in target.dataset) {
      store.selected = target.dataset.subject;
      store.selectedPeriod = '';
      localStorage.setItem('enjambre-subject', store.selected);
      render();
      return;
    }

    if (target.dataset.tab) {
      store.tab = target.dataset.tab;
      render();
      return;
    }
    switch (target.dataset.action) {
      case 'all-answers':
        modal('Tus consultas', store.state.runs.filter(r => r.kind === 'answer').map(r => [
          [
            `<button class="recent-item" data-run="${e(r.id)}">${e(r.title)}<span>${dateLabel(r.created_at)} · `
          ].join(''),
          `${runStatus(r.status)}</span></button>`
        ].join('')).join(''));
        break;
      case 'shutdown-dialog':
        modal('Cerrar tu espacio', [
          `<p>Se cerrará el servidor local. Tus documentos y propuestas quedan `,
          `guardados.</p><div class="dialog-actions"><button class="button ghost" `,
          `data-action="close-dialog">Volver</button><button class="button primary" `,
          `data-action="shutdown">Cerrar Enjambre</button></div>`
        ].join(''));
        break;
      case 'shutdown':
        await api('/shutdown', {});
        store.isClosed = true;
        clearInterval(store.monitorTimer);
        dialog.close();
        $('#connection').disabled = true;
        $('#connection').innerHTML = 'Enjambre cerrado';
        render();
        break;
      case 'add-source':
        sourceModal();
        break;
      case 'download-calendar': {
        const res = await request('/api/calendar.ics', {
          headers: {
            'X-Docente-Token': token
          }
        });
        if (!res.ok) throw new Error('No se pudo descargar el calendario.');
        const blobUrl = URL.createObjectURL(await res.blob());
        const dlLink = document.createElement('a');
        dlLink.href = blobUrl;
        dlLink.setAttribute('download', 'horario-docente.ics');
        document.body.appendChild(dlLink);
        dlLink.click();
        document.body.removeChild(dlLink);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
        toast('Descargando calendario con avisos (.ics)...');
        break;
      }
      case 'new-subject':
        subjectModal();
        break;
      case 'new-group':
        groupModal();
        break;
      case 'new-proposal':
        proposalModal();
        break;
      case 'new-feedback':
        feedbackModal();
        break;
      case 'close-dialog':
        dialog.close();
        break;
      case 'reveal':
        await api('/reveal', {});
        break;
      case 'reveal-diary':
        await api('/reveal-diary', {});
        break;
      case 'scan':
        await scanFolder();
        break;
      case 'confirm-provider':
        await ensureRemoteConsent();
        await refresh();
        break;
      case 'delete-api-key':
        await api('/secrets/provider', undefined, {
          method: 'DELETE'
        });
        await refresh();
        await checkStatus();
        toast(store.state.api_key_configured ? 'Entrada borrada; sigue configurada desde el entorno.' :
          'Clave borrada del Llavero.');
        break;
      case 'status':
        await checkStatus();
        if (view() !== 'ajustes') {
          location.hash = 'ajustes';
        }
        break;
      case 'clear-filter':
        store.selected = '';
        store.selectedPeriod = '';
        store.tab = 'all';
        store.query = '';
        render();
        break;
      case 'close-run':
        store.currentRun = null;
        render();
        break;
      case 'print-student':
        printStudentDocument();
        break;
      case 'reload':
        await refresh();
        break;
    }
  } catch (error) {
    fail(error);
    target.disabled = false;
  }
});
document.addEventListener('input', event => {
  if (event.target.id === 'library-search') {
    store.query = event.target.value;
    $('#library-results').innerHTML = libraryResults();
    return;
  }
  const form = event.target.closest('form');
  if (form?.id && event.target.name) {
    store.drafts[form.id] ??= {};
    store.drafts[form.id][event.target.name] = event.target.value;
  }
});
document.addEventListener('change', event => {
  if (event.target.id === 'files') setFiles(event.target.files);
  if (event.target.id === 'proposal-group') {
    $('#proposal-unit').innerHTML = unitOptions(event.target.value);
    if (store.drafts['proposal-form']) store.drafts['proposal-form'].unit = '';
  }
  if (event.target.id === 'ask-subject') {
    store.drafts['ask-form'] ??= {};
    store.drafts['ask-form'].subject = event.target.value;
    render();
  }
  if (event.target.id === 'model-provider') {
    const form = event.target.closest('form');
    const preset = store.state.provider_presets[event.target.value];
    const isDS = preset.transport !== 'ollama';
    form.elements.generation.value = Object.keys(preset.models)[0] || '';
    form.elements.base_url.value = preset.base_url;
    form.querySelectorAll('.custom-only').forEach(el => el.hidden = event.target.value !== 'custom');
    form.querySelectorAll('.remote-only').forEach(el => el.hidden = !isDS);
    form.querySelectorAll('.ollama-only').forEach(el => el.hidden = isDS);
  }
});
document.addEventListener('keydown', event => {
  if (event.target.id === 'dropzone' && ['Enter', ' '].includes(event.key)) {
    event.preventDefault();
    $('#files').click();
  }
});
document.addEventListener('dragover', event => {
  if (event.target.closest('#dropzone')) {
    event.preventDefault();
    $('#dropzone').classList.add('dragging');
  }
});
document.addEventListener('dragleave', event => {
  event.target.closest('#dropzone')?.classList.remove('dragging');
});
document.addEventListener('drop', event => {
  if (event.target.closest('#dropzone')) {
    event.preventDefault();
    setFiles(event.dataTransfer.files);
    $('#dropzone').classList.remove('dragging');
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
    switch (form.dataset.form) {
      case 'run-stats':
        store.selectedRunStats = await api('/runs/stats?limit=' + encodeURIComponent(data.limit));
        render();
        break;
      case 'models': {
        const provider = data.provider || 'ollama';
        const generation = data.generation;
        await api('/models', {
          ...data,
          provider,
          generation
        });
        if (form.elements.api_key) form.elements.api_key.value = '';
        await refresh();
        await checkStatus();
        toast('Configuración de motor actualizada.');
        break;
      }
      case 'subject':
        await api('/subjects', data);
        dialog.close();
        await refresh();
        toast('Materia guardada. Sus carpetas ya están disponibles.');
        break;
      case 'group':
        await api('/groups', {
          ...data,
          year: Number(data.year)
        });
        dialog.close();
        await refresh();
        toast('Grupo guardado. Ya puedes preparar una propuesta.');
        break;
      case 'upload': {
        if (!store.chosenFiles.length) throw new Error('Elige al menos un archivo.');
        if (store.chosenFiles.length > 8) throw new Error('Añade hasta ocho archivos cada vez.');
        for (const file of store.chosenFiles) {
          if (!/\.(pdf|docx|md|txt)$/i.test(file.name)) throw new Error(
            'Solo se admiten PDF, DOCX, Markdown y TXT.');
          if (file.size > 300 * 1024 * 1024) throw new Error(file.name + ' supera los 300 MB.');
        }
        let uploaded = 0;
        for (const file of store.chosenFiles) {
          button.textContent = `Añadiendo ${++uploaded} de ${store.chosenFiles.length}…`;
          const response = await request('/api/upload?name=' + encodeURIComponent(file.name), {
            method: 'POST',
            headers: {
              'X-Docente-Token': token
            },
            body: file
          });
          const stored = await response.json();
          if (!response.ok) throw new Error(stored.error);
          await queue('/import', {
            ...data,
            path: stored.path
          });
        }
        dialog.close();
        toast('Archivos añadidos. Revisa cada fuente para permitir su uso.');
        break;
      }
      case 'inbox':
        await queue('/import', {
          ...data,
          path: form.dataset.path,
          document_id: form.dataset.documentId || undefined
        });
        form.innerHTML = '<p class="inbox-status">' + icon('check') +
          ' En proceso. Aparecerá en la biblioteca para su revisión.</p>';
        break;
      case 'authorize':
        await queue('/documents/' + form.dataset.id + '/authorize', {
          accept_warnings: !!data.accept_warnings
        });
        dialog.close();
        break;
      case 'metadata':
        await api('/documents/' + form.dataset.id + '/metadata', {
          ...data,
          authors: data.authors.split(';').map(a => a.trim()).filter(Boolean),
          year: data.year ? Number(data.year) : null
        });
        await refresh();
        await showDocument(form.dataset.id);
        toast('Metadatos actualizados.');
        break;
      case 'ask':
        if (!await ensureRemoteConsent('ask')) break;
        await queue('/generate', {
          ...data,
          mode: 'ask'
        });
        toast('Consulta en marcha. Puedes seguir navegando.');
        break;
      case 'proposal':
        if (!await ensureRemoteConsent('pedagogy')) break;
        await queue('/generate', {
          ...data,
          mode: 'pedagogy',
          duration: Number(data.duration)
        });
        dialog.close();
        toast('Preparando el borrador con tus fuentes.');
        break;
      case 'reject': {
        const result = await api('/runs/' + encodeURIComponent(form.dataset.id) + '/review', {
          action: 'rejected',
          notes: data.notes || ''
        });
        if (store.currentRun && store.currentRun.id === form.dataset.id) store.currentRun = {
          ...store.currentRun,
          ...result
        };
        dialog.close();
        render();
        toast('Propuesta rechazada y anotada.');
        break;
      }
      case 'record': {
        const payload = {
          ...data,
          duration_minutes: Number(data.duration_minutes),
          run_id: form.dataset.run || undefined
        };
        const result = await api('/records', payload);
        dialog.close();
        toast([
          `Clase registrada: ${result.id}`,
          `. El asistente tendrá en cuenta esta sesión en las próximas propuestas.`
        ].join(''));
        break;
      }
      case 'feedback': {
        const result = form.dataset.record ? await api('/records/' + encodeURIComponent(form.dataset
          .record) + '/feedback', data) : await api('/records', {
          ...data,
          duration_minutes: Number(data.duration_minutes)
        });
        dialog.close();
        await refresh();
        toast(`Feedback guardado en el diario de ${result.session_date}.`);
        break;
      }
    }
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
window.addEventListener('beforeprint', () => {
  if (dialog?.open && dialog?.classList.contains('student-dialog')) {
    document.body.classList.add('student-printing');
    dialog.querySelectorAll('.egypt-sheet').forEach(el => {
      el.style.display = 'block';
    });
  }
});
window.addEventListener('afterprint', () => {
  document.body.classList.remove('student-printing');
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

// Complete keyboard navigation for the source-type tabs.
document.addEventListener('keydown', event => {
  if (event.target.getAttribute('role') !== 'tab' || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(
      event.key)) return;
  event.preventDefault();
  const tabs = Array.from(document.querySelectorAll('[role="tab"]')),
    index = tabs.indexOf(event.target);
  const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key ===
    'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
  tabs[next].click();
  document.querySelectorAll('[role="tab"]')[next].focus();
});
