/**
 * voz/js/recorder.js — Captura push-to-talk con MediaRecorder.
 *
 * Salida preferida: audio/webm;codecs=opus (Chrome Android nativo).
 * Fallback: audio/ogg;codecs=opus o el primer MIME soportado.
 *
 * Uso:
 *   const rec = new Recorder();
 *   await rec.start();
 *   ...
 *   const blob = await rec.stop();   // → Blob audio/* (opus)
 *
 * Si el usuario suelta el botón antes de stop(), llamamos cancel().
 */

const CANDIDATOS_MIME = [
  'audio/webm;codecs=opus',
  'audio/ogg;codecs=opus',
  'audio/webm',
  'audio/mp4',
];

function elegirMime() {
  if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return '';
  for (const m of CANDIDATOS_MIME) {
    if (MediaRecorder.isTypeSupported(m)) return m;
  }
  return '';
}

export class Recorder {
  constructor() {
    this.stream = null;
    this.mr = null;
    this.chunks = [];
    this.mime = '';
    this._resolve = null;
    this._reject = null;
    this._cancelled = false;
  }

  get mimeType() { return this.mime; }

  async start() {
    if (this.mr) throw new Error('ya grabando');

    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error('MediaDevices no disponible — usa Chrome reciente');
    }

    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 48000,
        echoCancellation: true,
        noiseSuppression: true,
      }
    });

    this.mime = elegirMime();
    const opts = this.mime ? { mimeType: this.mime, audioBitsPerSecond: 32000 } : {};

    this.mr = new MediaRecorder(this.stream, opts);
    this.chunks = [];
    this._cancelled = false;

    this.mr.addEventListener('dataavailable', (e) => {
      if (e.data && e.data.size > 0) this.chunks.push(e.data);
    });

    this.mr.addEventListener('stop', () => {
      this._tearDown();
      if (this._cancelled) {
        this._resolve && this._resolve(null);
      } else {
        const blob = new Blob(this.chunks, { type: this.mime || 'audio/webm' });
        this._resolve && this._resolve(blob);
      }
      this._resolve = null;
      this._reject = null;
    });

    this.mr.addEventListener('error', (e) => {
      this._tearDown();
      this._reject && this._reject(e.error || new Error('recorder error'));
    });

    this.mr.start();
  }

  stop() {
    if (!this.mr) return Promise.resolve(null);
    return new Promise((resolve, reject) => {
      this._resolve = resolve;
      this._reject = reject;
      try { this.mr.stop(); } catch (e) { reject(e); }
    });
  }

  cancel() {
    if (!this.mr) return;
    this._cancelled = true;
    try { this.mr.stop(); } catch {}
  }

  _tearDown() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    this.mr = null;
  }
}
