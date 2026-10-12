import { e, icon, render, toast } from '../ui.js';
import { store } from '../state.js';
import { api } from '../api.js';

// Módulo para renderizado de partituras con Verovio y resolución de ejemplos.

export function renderScoreVoiceItem(v, i, claves) {
  const isTenor = v.es_cantus_firmus || (v.nombre || '').toLowerCase().includes('tenor');
  const clef = (claves && claves[i]) || (i === 3 ? 'F4' : (i === 0 ? 'G2' : 'C3'));
  return [
    `<div class="score-voice-item ${isTenor ? 'is-tenor' : ''}">`,
    `  <span class="score-voice-name">${e(v.nombre || v.id)}</span>`,
    `  <span class="score-voice-clef">Clave: ${e(clef)}</span>`,
    isTenor ? `<span class="score-voice-note">★ cantus firmus</span>` : '',
    `</div>`,
  ].join('');
}

export function renderScorePreviewSvg(candidato, startMeasure = 1, endMeasure = 8) {
  const voces = candidato.voces || [
    { id: 'P1', nombre: 'Superius' },
    { id: 'P2', nombre: 'Altus' },
    { id: 'P3', nombre: 'Tenor' },
    { id: 'P4', nombre: 'Bassus' },
  ];
  const totalMeasures = candidato.compases || 8;
  const end = Math.min(totalMeasures, Math.max(startMeasure, endMeasure));
  const timeSig = candidato.mensuracion || '3/2';

  return [
    `<div class="verovio-score-preview">`,
    `  <div class="score-meta-bar">`,
    `    <span class="score-time-badge">Mensuración: ${e(timeSig)}</span>`,
    `    <span class="score-range-badge">Compases ${e(startMeasure)}–${e(end)} de ${e(totalMeasures)}</span>`,
    `  </div>`,
    `  <div class="score-voices-list">`,
    voces.map((v, i) => renderScoreVoiceItem(v, i, candidato.claves)).join(''),
    `  </div>`,
    `</div>`,
  ].join('');
}

export function renderScoreCandidateItem(cand, cIdx, runId, reqId) {
  const pathLabel = cand.path ?
    `<div class="score-path-label"><small class="muted">Origen: ${e(cand.path)}</small></div>` : '';

  return [
    `<div class="score-candidate-item" data-candidate-id="${e(cand.id)}" data-path="${e(cand.path || '')}">`,
    `  <div class="candidate-header">`,
    `    <div>`,
    `      <strong>Candidato ${e(cIdx + 1)}: ${e(cand.titulo)}</strong>`,
    `      <div class="score-meta">${e(cand.compositor)} · ${e(cand.fuente)} (${e(cand.licencia)})</div>`,
    pathLabel,
    `    </div>`,
    `    <div class="candidate-controls">`,
    `      <div class="score-mode-toggle">`,
    `        <button type="button" class="score-mode-btn active" data-mode="svg">🎼 Partitura</button>`,
    `        <button type="button" class="score-mode-btn" data-mode="pianoroll">🎹 Piano roll</button>`,
    `      </div>`,
    `      <label class="range-label">Compases: `,
    `        <input type="number" class="score-start-input" min="1" max="99" value="1"> a `,
    `        <input type="number" class="score-end-input" min="1" max="99" value="8">`,
    `      </label>`,
    `      <button class="button small ghost play-score-btn" data-candidate="${e(cand.id)}">`,
    `        ${icon('play')}▶ Reproducir`,
    `      </button>`,
    `      <button class="button small primary adopt-score-btn" data-run-id="${e(runId)}" `,
    `data-req-id="${e(reqId)}" data-candidate="${e(cand.id)}">`,
    `        ${icon('check')}Usar`,
    `      </button>`,
    `      <button class="button small ghost discard-score-btn" data-run-id="${e(runId)}" `,
    `data-req-id="${e(reqId)}" data-candidate="${e(cand.id)}">`,
    `        ${icon('close')}Descartar`,
    `      </button>`,
    `    </div>`,
    `  </div>`,
    `  <div class="score-preview-box" data-path="${e(cand.path || '')}" ` +
    `data-candidate-id="${e(cand.id)}" data-current-mode="svg">`,
    `    <div class="score-loading"><span class="spinner"></span> Renderizando partitura con Verovio…</div>`,
    `  </div>`,
    `</div>`,
  ].join('');
}

export function renderWavDownloadButton(ej) {
  const hasFluid = store.state?.music_capabilities?.fluidsynth;
  if (!hasFluid || !ej?.id) return '';
  return [
    `<a class="button small ghost download-wav-btn" href="/api/ejemplos/${e(ej.id)}/wav" `,
    `download="${e(ej.id)}.wav">`,
    `  ${icon('download')}Exportar audio (WAV)`,
    `</a>`,
  ].join('');
}

export function renderMusicRequestCard(item, result, run) {
  const req = item.request || (result.music_requests || []).find(r => r.id === item.request_id) || {};
  const isResolved = item.status === 'resuelto_catalogo' && item.ejemplo;
  const isVerified = isResolved && !!item.verificado;

  if (isVerified) {
    const ej = item.ejemplo;
    const wavButton = renderWavDownloadButton(ej);
    const isTheory = ej.calculado_teoria || ej.fuente === 'Calculado a partir de la teoría';
    const badgeText = isTheory ? '✓ Calculado a partir de la teoría' : '✓ Ejemplo verificado';
    const badgeClass = isTheory ? 'badge info' : 'badge success';
    const fuenteText = isTheory ? 'Calculado a partir de la teoría' : (ej.fuente || 'Catálogo');
    const freqsJson = JSON.stringify(ej.frecuencias_hz || []);

    return [
      `<div class="score-card score-card-verified score-candidate-item" data-candidate-id="${e(ej.id)}">`,
      `  <div class="score-card-head">`,
      `    <div>`,
      `      <span class="${badgeClass}">${badgeText}</span>`,
      `      <h4>${e(ej.titulo || req.work)} — ${e(ej.compositor || req.composer)}</h4>`,
      `      <small class="score-meta">${e(ej.seccion || req.section || '')} · `,
      `Compases ${e(ej.compases || '1-3')} · Fuente: ${e(fuenteText)}</small>`,
      `    </div>`,
      `    <div class="candidate-controls">`,
      `      <div class="score-mode-toggle">`,
      `        <button type="button" class="score-mode-btn active" data-mode="svg">🎼 Partitura</button>`,
      `        <button type="button" class="score-mode-btn" data-mode="pianoroll">🎹 Piano roll</button>`,
      `      </div>`,
      `      <button class="button small ghost play-score-btn" data-candidate="${e(ej.id)}" ` +
      `data-frequencies="${e(freqsJson)}">`,
      `        ${icon('play')}▶ Reproducir`,
      `      </button>`,
      wavButton ? `      ${wavButton}` : '',
      `    </div>`,
      `  </div>`,
      `  <div class="score-preview-container">`,
      `    <div class="score-preview-box" data-candidate-id="${e(ej.id)}" ` +
      `data-current-mode="svg" data-voice="Tetracordo">`,
      `      <div class="score-loading"><span class="spinner"></span> Renderizando partitura con Verovio…</div>`,
      `    </div>`,
      `  </div>`,
      `</div>`,
    ].join('');
  }

  const candidatos = item.candidatos || [];
  const reqId = req.id || item.request_id;
  const candidatesHtml = candidatos.length ?
    `<div class="score-candidates-list">` +
    candidatos.map((c, idx) => renderScoreCandidateItem(c, idx, run.id, reqId)).join('') +
    `</div>` :
    `<div class="score-no-candidates"><p>Sin candidatos automáticos en la carpeta local. ` +
    `Usa el botón para buscar en JRP, KernScores, CPDL y music21.</p></div>`;

  return [
    `<div class="score-card score-card-pending" data-request-id="${e(reqId)}">`,
    `  <div class="score-card-head">`,
    `    <div>`,
    `      <span class="badge warning">⚠️ Ejemplo pendiente de selección</span>`,
    `      <h4>${e(req.work || 'Obra requerida')} — ${e(req.composer || 'Compositor')}</h4>`,
    `      <p class="score-desc">${e(req.description || '')}</p>`,
    `      <small class="score-meta">Técnica: ${e(req.technique || 'General')} · `,
    `Actividad: ${e(req.activity_title || 'Clase')}</small>`,
    `    </div>`,
    `    <button class="button small open-repos-btn" data-run-id="${e(run.id)}" `,
    `data-req-id="${e(reqId)}">`,
    `      ${icon('spark')}Buscar en repositorios abiertos`,
    `    </button>`,
    `  </div>`,
    candidatesHtml,
    `</div>`,
  ].join('');
}

export function parseMidiEvents(data) {
  let pos = 0;
  function readStr(len) {
    let s = '';
    for (let i = 0; i < len; i++) s += String.fromCharCode(data[pos++]);
    return s;
  }
  function read32() {
    return (data[pos++] << 24) | (data[pos++] << 16) | (data[pos++] << 8) | data[pos++];
  }
  function read16() {
    return (data[pos++] << 8) | data[pos++];
  }
  function readVarLen() {
    let val = 0, b = 0;
    do {
      b = data[pos++];
      val = (val << 7) | (b & 0x7f);
    } while (b & 0x80);
    return val;
  }
  if (readStr(4) !== 'MThd') return [];
  pos += 4; // saltar longitud de cabecera
  pos += 2; // formato
  const ntracks = read16();
  const division = read16() || 120;
  let tempo = 500000;
  const allNotes = [];

  for (let t = 0; t < ntracks; t++) {
    if (pos >= data.length) break;
    const trackId = readStr(4);
    if (trackId !== 'MTrk') break;
    const trackLen = read32();
    const trackEnd = pos + trackLen;
    let runningStatus = 0, currentTick = 0;
    const active = {};

    while (pos < trackEnd) {
      currentTick += readVarLen();
      let status = data[pos];
      if (status >= 0x80) {
        runningStatus = status;
        pos++;
      } else {
        status = runningStatus;
      }
      const type = status >> 4;
      if (type === 0x9) {
        const note = data[pos++], vel = data[pos++];
        if (vel > 0) {
          active[note] = currentTick;
        } else {
          const st = active[note] ?? currentTick;
          delete active[note];
          allNotes.push({ note, st, et: currentTick });
        }
      } else if (type === 0x8) {
        const note = data[pos++];
        pos++;
        const st = active[note] ?? currentTick;
        delete active[note];
        allNotes.push({ note, st, et: currentTick });
      } else if (status === 0xFF) {
        const metaType = data[pos++];
        const metaLen = readVarLen();
        if (metaType === 0x51 && metaLen === 3) {
          tempo = (data[pos] << 16) | (data[pos + 1] << 8) | data[pos + 2];
        }
        pos += metaLen;
      } else if (type === 0xB || type === 0xC || type === 0xD || type === 0xE) {
        pos += (type === 0xC || type === 0xD) ? 1 : 2;
      }
    }
    pos = trackEnd;
  }
  const secPerTick = (tempo / 1000000) / division;
  return allNotes.map(n => ({
    note: n.note,
    start: n.st * secPerTick,
    duration: Math.max(0.08, (n.et - n.st) * secPerTick),
  }));
}

export function playMidiBase64(midiBase64, targetContainer = null) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const binary = atob(midiBase64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const notes = parseMidiEvents(bytes);
    if (!notes.length) {
      toast('No se encontraron notas en el MIDI generado.');
      return;
    }
    const ctx = new AudioCtx();
    const now = ctx.currentTime + 0.05;
    const totalDuration = Math.max(...notes.map(n => n.start + n.duration));

    notes.forEach(n => {
      const freq = 440 * Math.pow(2, (n.note - 69) / 12);
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      const startT = now + n.start;
      const dur = Math.max(0.08, n.duration);
      osc.frequency.setValueAtTime(freq, startT);
      gain.gain.setValueAtTime(0.12, startT);
      gain.gain.exponentialRampToValueAtTime(0.001, startT + dur);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(startT);
      osc.stop(startT + dur);
    });

    // Sincronización del cursor en el Piano Roll (playhead)
    const playheads = targetContainer
      ? targetContainer.querySelectorAll('.pianoroll-playhead')
      : document.querySelectorAll('.pianoroll-playhead');

    if (playheads.length) {
      playheads.forEach(ph => {
        ph.style.display = 'inline';
      });
      const startTime = ctx.currentTime;
      function animarCursor() {
        const elapsed = ctx.currentTime - startTime;
        if (elapsed > totalDuration + 0.1) {
          playheads.forEach(ph => {
            ph.style.display = 'none';
          });
          return;
        }
        const progress = Math.min(1.0, Math.max(0.0, elapsed / totalDuration));
        playheads.forEach(ph => {
          const left = parseFloat(ph.dataset.left || 64);
          const width = parseFloat(ph.dataset.width || 800);
          const curX = left + progress * width;
          ph.setAttribute('x1', curX.toFixed(2));
          ph.setAttribute('x2', curX.toFixed(2));
        });
        requestAnimationFrame(animarCursor);
      }
      requestAnimationFrame(animarCursor);
    }

    toast('Reproduciendo muestra polifónica con cursor sincronizado...');
  } catch (err) {
    toast(`Error de audio: ${err.message}`, 'error');
  }
}

export async function loadScoreContent(box, mode = 'svg') {
  const card = box.closest('.score-candidate-item, .score-card, .cantus-firmus-box-wrapper');
  const candidateId = box.dataset.candidateId || card?.dataset.candidateId || box.dataset.id;
  if (!candidateId) return;
  const runId = card?.querySelector('.adopt-score-btn')?.dataset.runId;
  const startInp = card?.querySelector('.score-start-input');
  const endInp = card?.querySelector('.score-end-input');
  const start = startInp ? parseInt(startInp.value, 10) || 1 : 1;
  const end = endInp ? parseInt(endInp.value, 10) || 8 : 8;
  const voice = box.dataset.voice || card?.dataset.voice || 'tenor';

  box.dataset.currentMode = mode;

  if (mode === 'pianoroll') {
    box.innerHTML = '<div class="score-loading"><span class="spinner"></span> Generando Piano Roll…</div>';
    try {
      const res = await api('/scores/render-pianoroll', { id: candidateId, run_id: runId, start, end, voice });
      if (res?.svg) {
        box.innerHTML = '<div class="pianoroll-score-svg"></div>';
        box.firstElementChild.innerHTML = res.svg;
      } else {
        box.innerHTML = '<p class="score-meta">No se pudo generar el Piano Roll.</p>';
      }
    } catch (err) {
      box.innerHTML = `<p class="score-meta">Error al renderizar piano roll: ${e(err.message)}</p>`;
    }
  } else {
    box.innerHTML = '<div class="score-loading"><span class="spinner"></span> ' +
      'Renderizando partitura con Verovio…</div>';
    try {
      const res = await api('/scores/render-svg', { id: candidateId, run_id: runId, start, end, voice });
      if (res?.svg) {
        box.innerHTML = '<div class="verovio-score-svg"></div>';
        box.firstElementChild.innerHTML = res.svg;
      } else {
        box.innerHTML = '<p class="score-meta">No se pudo obtener el SVG de Verovio.</p>';
      }
    } catch (err) {
      box.innerHTML = `<p class="score-meta">Error al renderizar partitura: ${e(err.message)}</p>`;
    }
  }
}

export async function loadScoreSvg(box) {
  return loadScoreContent(box, 'svg');
}

export async function loadScorePianoroll(box) {
  return loadScoreContent(box, 'pianoroll');
}

export function initScorePreviews() {
  const boxes = document.querySelectorAll('.score-preview-box[data-candidate-id]:not([data-rendered])');
  boxes.forEach(box => {
    box.dataset.rendered = 'true';
    const initialMode = box.dataset.currentMode || 'svg';
    loadScoreContent(box, initialMode);
    const card = box.closest('.score-candidate-item, .score-card, .cantus-firmus-box-wrapper');
    if (card) {
      const inputs = card.querySelectorAll('.score-start-input, .score-end-input');
      inputs.forEach(inp => {
        inp.addEventListener('change', () => {
          const curMode = box.dataset.currentMode || 'svg';
          loadScoreContent(box, curMode);
        });
      });
    }
  });
}

export function playMicrotoneFrequencies(frequenciesHz, durationPerNote = 0.5, targetContainer = null) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const now = ctx.currentTime + 0.05;
    const totalDuration = frequenciesHz.length * durationPerNote;
    frequenciesHz.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      const startT = now + idx * durationPerNote;
      osc.frequency.setValueAtTime(freq, startT);
      gain.gain.setValueAtTime(0.18, startT);
      gain.gain.exponentialRampToValueAtTime(0.001, startT + durationPerNote);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(startT);
      osc.stop(startT + durationPerNote);
    });

    const playheads = targetContainer
      ? targetContainer.querySelectorAll('.pianoroll-playhead')
      : document.querySelectorAll('.pianoroll-playhead');

    if (playheads.length) {
      playheads.forEach(ph => ph.style.display = 'inline');
      const startTime = ctx.currentTime;
      function animarCursor() {
        const elapsed = ctx.currentTime - startTime;
        if (elapsed > totalDuration + 0.1) {
          playheads.forEach(ph => ph.style.display = 'none');
          return;
        }
        const progress = Math.min(1.0, Math.max(0.0, elapsed / totalDuration));
        playheads.forEach(ph => {
          const left = parseFloat(ph.dataset.left || 64);
          const width = parseFloat(ph.dataset.width || 800);
          const curX = left + progress * width;
          ph.setAttribute('x1', curX);
          ph.setAttribute('x2', curX);
        });
        requestAnimationFrame(animarCursor);
      }
      requestAnimationFrame(animarCursor);
    }
    toast('Reproduciendo tetracordos con frecuencias exactas (Web Audio)…');
  } catch (err) {
    // Si el navegador restringe audio
  }
}

export function renderMusicRequestsBlock(run) {
  const result = run.result || {};
  const reqs = result.resolved_music_requests || [];
  if (!reqs.length && !(result.music_requests || []).length) {
    return '';
  }

  const items = reqs.length ? reqs : (result.music_requests || []).map(r => ({
    request_id: r.id,
    status: 'sin_resolver',
    origen: null,
    ejemplo: null,
    verificado: false,
    candidatos: [],
    request: r,
  }));

  return [
    `<div class="pedagogy-block proposal-scores-block">`,
    `  <div class="block-header">`,
    `    <span class="block-num">🎼</span>`,
    `    <div>`,
    `      <h3>Ejemplos musicales y partituras de la sesión</h3>`,
    `      <p class="block-desc">Partituras requeridas con resolución automática desde catálogo, ` +
    `carpeta del profesor o repositorios abiertos.</p>`,
    `    </div>`,
    `  </div>`,
    `  <div class="scores-container">`,
    items.map(it => renderMusicRequestCard(it, result, run)).join(''),
    `  </div>`,
    `</div>`,
  ].join('');
}

async function accionAdoptScore({target}) {
  const btn = target.closest('.adopt-score-btn');
  if (!btn) return;
  const runId = btn.dataset.runId;
  const reqId = btn.dataset.reqId;
  const candId = btn.dataset.candidate;
  const card = btn.closest('.score-candidate-item');
  const startInp = card?.querySelector('.score-start-input');
  const endInp = card?.querySelector('.score-end-input');
  const start = startInp ? parseInt(startInp.value, 10) || 1 : 1;
  const end = endInp ? parseInt(endInp.value, 10) || 8 : 8;
  const rango = `${start}-${end}`;

  btn.disabled = true;
  try {
    const updated = await api(
      `/runs/${encodeURIComponent(runId)}/music_requests/${encodeURIComponent(reqId)}/adopt`,
      { candidate_id: candId, compases: rango }
    );
    if (store.currentRun && store.currentRun.id === runId) {
      store.currentRun = updated;
    }
    render();
    toast('Ejemplo musical guardado en el catálogo como verificado.');
  } catch (err) {
    toast(`Error al adoptar partitura: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function accionDiscardScore({target}) {
  const btn = target.closest('.discard-score-btn');
  if (!btn) return;
  const runId = btn.dataset.runId;
  const reqId = btn.dataset.reqId;
  const candId = btn.dataset.candidate;

  btn.disabled = true;
  try {
    const updated = await api(
      `/runs/${encodeURIComponent(runId)}/music_requests/${encodeURIComponent(reqId)}/discard`,
      { candidate_id: candId }
    );
    if (store.currentRun && store.currentRun.id === runId) {
      store.currentRun = updated;
    }
    render();
    toast('Candidato descartado para esta propuesta.');
  } catch (err) {
    toast(`Error al descartar partitura: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function accionSearchOpenRepos({target}) {
  const btn = target.closest('.open-repos-btn');
  if (!btn) return;
  const runId = btn.dataset.runId;
  const reqId = btn.dataset.reqId;

  btn.disabled = true;
  try {
    const updated = await api(
      `/runs/${encodeURIComponent(runId)}/music_requests/${encodeURIComponent(reqId)}/search_open_repos`,
      {}
    );
    if (store.currentRun && store.currentRun.id === runId) {
      store.currentRun = updated;
    }
    render();
    toast('Búsqueda en repositorios abiertos completada.');
  } catch (err) {
    toast(`Error al buscar en repositorios: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function accionPlayScoreSample({target}) {
  const btn = target.closest('.play-score-btn');
  if (!btn) return;
  const candidateId = btn.dataset.candidate;
  const card = btn.closest('.score-candidate-item, .cantus-firmus-box-wrapper');
  const runId = card?.querySelector('.adopt-score-btn')?.dataset.runId;
  const startInp = card?.querySelector('.score-start-input');
  const endInp = card?.querySelector('.score-end-input');
  const start = startInp ? parseInt(startInp.value, 10) || 1 : 1;
  const end = endInp ? parseInt(endInp.value, 10) || 12 : 12;

  if (!candidateId) {
    toast('No hay identificador de partitura para reproducir.');
    return;
  }

  const freqsStr = btn.dataset.frequencies;
  if (freqsStr) {
    try {
      const freqs = JSON.parse(freqsStr);
      if (Array.isArray(freqs) && freqs.length) {
        playMicrotoneFrequencies(freqs, 0.6, card);
        return;
      }
    } catch (e) {
      // Continuar con fallback a MIDI
    }
  }

  btn.disabled = true;
  try {
    toast('Generando MIDI con Verovio...');
    const res = await api('/scores/render-midi', { id: candidateId, run_id: runId, start, end });
    if (res?.midi) {
      playMidiBase64(res.midi, card);
    } else {
      toast('No se pudo generar MIDI para este ejemplo.', 'error');
    }
  } catch (err) {
    toast(`Error al reproducir partitura: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

async function accionToggleScoreMode({target}) {
  const btn = target.closest('.score-mode-btn');
  if (!btn) return;
  const container = btn.closest('.score-candidate-item, .score-card, .cantus-firmus-box-wrapper');
  if (!container) return;
  const mode = btn.dataset.mode;
  const box = container.querySelector('.score-preview-box');
  if (!box) return;

  container.querySelectorAll('.score-mode-btn').forEach(b => b.classList.toggle('active', b === btn));
  box.dataset.currentMode = mode;
  await loadScoreContent(box, mode);
}

async function accionDescargarEjemplosFicha({target}) {
  const btn = target.closest('.descargar-ejemplos-ficha-btn');
  if (!btn) return;
  const runId = btn.dataset.runId;
  btn.disabled = true;
  btn.textContent = 'Descargando partituras del JRP…';
  try {
    const res = await api(`/runs/${encodeURIComponent(runId)}/descargar-ejemplos-ficha`, {}, { method: 'POST' });
    if (store.currentRun && store.currentRun.id === runId) {
      store.currentRun.ficha_ejemplos = res.ejemplos;
    }
    render();
    toast(`Se han preparado ${res.total || 9} ejemplos del JRP.`);
  } catch (err) {
    toast(`Error al descargar partituras: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

export const actions = {
  'adopt-score': accionAdoptScore,
  'discard-score': accionDiscardScore,
  'search-open-repos': accionSearchOpenRepos,
  'play-score-sample': accionPlayScoreSample,
  'toggle-score-mode': accionToggleScoreMode,
  'descargar-ejemplos-ficha': accionDescargarEjemplosFicha,
};

export const clickBindings = [
  { priority: 2, matches: target => !!target.closest('.adopt-score-btn'), action: 'adopt-score' },
  { priority: 2, matches: target => !!target.closest('.discard-score-btn'), action: 'discard-score' },
  { priority: 2, matches: target => !!target.closest('.open-repos-btn'), action: 'search-open-repos' },
  { priority: 2, matches: target => !!target.closest('.play-score-btn'), action: 'play-score-sample' },
  { priority: 2, matches: target => !!target.closest('.score-mode-btn'), action: 'toggle-score-mode' },
  {
    priority: 2,
    matches: target => !!target.closest('.descargar-ejemplos-ficha-btn'),
    action: 'descargar-ejemplos-ficha'
  },
];
