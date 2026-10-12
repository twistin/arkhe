// Motor de síntesis Web Audio para componentes didácticos musicales.
// Garantiza frecuencias microtonales exactas en Hz (incluyendo cuartos de tono).

let audioCtx = null;

export function getAudioContext() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

export function playFrequency(freqHz, duration = 0.55, startTimeOffset = 0) {
  const ctx = getAudioContext();
  if (!ctx) return;

  const now = ctx.currentTime + startTimeOffset;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();

  osc.type = 'sine';
  osc.frequency.setValueAtTime(freqHz, now);

  // Envolvente suave para evitar chasquidos (ataque 15ms, decaimiento suave)
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(0.3, now + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.2, now + duration * 0.7);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

  osc.connect(gain);
  gain.connect(ctx.destination);

  osc.start(now);
  osc.stop(now + duration + 0.05);
}

export function playFrequencySequence(frequencies, noteDuration = 0.5, gap = 0.08) {
  const ctx = getAudioContext();
  if (!ctx || !Array.isArray(frequencies) || frequencies.length === 0) return;

  frequencies.forEach((freq, index) => {
    const offset = index * (noteDuration + gap);
    playFrequency(freq, noteDuration, offset);
  });
}
