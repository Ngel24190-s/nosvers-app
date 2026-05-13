/**
 * voz/js/app.js — Orquesta la UI push-to-talk + lista pendientes.
 *
 * Flujo:
 *   1. Si no hay token → abrir modal de onboarding (bloqueante).
 *   2. Push-to-talk:
 *      - pointerdown → start Recorder, mostrar pulso + timer
 *      - pointerup / pointercancel → stop → blob → addNota({audio}) → flush
 *      - cancelación (mover fuera del botón) ↓ se ignora; soltar siempre confirma
 *   3. Texto rápido: input + submit → addNota({texto}) → flush
 *   4. Lista pendientes: render reactivo a eventos del bus de sync.
 *   5. Service Worker registrado y Background Sync programado al añadir nota.
 */

import * as db from './db.js';
import * as auth from './auth.js';
import { Recorder } from './recorder.js';
import * as sync from './sync.js';

const $ = (sel) => document.querySelector(sel);

const ptt        = $('#ptt');
const pttTimer   = $('#ptt-timer');
const pttHint    = $('#ptt-hint');
const textForm   = $('#text-form');
const textInput  = $('#text-input');
const pendingUl  = $('#pending-list');
const pendingCt  = $('#pending-count');
const banner     = $('#status-banner');
const apiHost    = $('#api-host');
const netInd     = $('#net-indicator');
const netText    = $('#net-text');
const btnToken   = $('#btn-token');
const btnFlush   = $('#btn-flush');
const tokenModal = $('#token-modal');
const tokenInput = $('#token-input');
const tokenSave  = $('#token-save');
const tokenCancel= $('#token-cancel');
const deviceModal      = $('#device-modal');
const deviceChoices    = document.querySelectorAll('.device-choice');
const tokenDeviceLabel = $('#token-device-label');
const tokenDeviceCmd   = $('#token-device-cmd');

let recorder = null;
let pttTimerId = null;
let pttStartMs = 0;

apiHost.textContent = (new URL(sync.API_BASE)).host;

// ---------- Status banner ----------

function banderaInfo(msg)    { mostrarBanner(msg, 'info', 2500); }
function banderaWarning(msg) { mostrarBanner(msg, 'warning', 4000); }
function banderaError(msg)   { mostrarBanner(msg, 'error',   5000); }

function mostrarBanner(msg, tipo, ms) {
  banner.textContent = msg;
  banner.className = `show ${tipo}`;
  if (ms) setTimeout(() => banner.classList.remove('show'), ms);
}

// ---------- Token modal ----------

function abrirTokenModal(motivo) {
  tokenInput.value = auth.getToken();
  const dev = auth.getDeviceLabel();
  if (tokenDeviceLabel) tokenDeviceLabel.textContent = dev;
  if (tokenDeviceCmd)   tokenDeviceCmd.textContent   = dev;
  tokenModal.classList.add('show');
  if (motivo) banderaWarning(motivo);
}

function cerrarTokenModal() {
  tokenModal.classList.remove('show');
}

// ---------- Device onboarding (multi-usuario) ----------

function abrirDeviceModal() {
  deviceModal.classList.add('show');
}

function cerrarDeviceModal() {
  deviceModal.classList.remove('show');
}

deviceChoices.forEach((btn) => {
  btn.addEventListener('click', () => {
    const dev = btn.dataset.device;
    if (!dev) return;
    auth.setDeviceLabel(dev);
    cerrarDeviceModal();
    banderaInfo(`Dispositivo: ${dev}.`);
    if (!auth.hasToken()) {
      abrirTokenModal('Pega el token Bearer emitido desde el VPS.');
    }
  });
});

tokenSave.addEventListener('click', () => {
  const t = tokenInput.value.trim();
  if (!t) {
    banderaError('Pega un token válido.');
    return;
  }
  const payload = auth.decodePayload(t);
  const device = payload?.device || 'movil-angel';
  auth.setToken(t, device);
  cerrarTokenModal();
  banderaInfo(`Token guardado para ${device}.`);
  habilitarPtt();
  sync.flush();
});

tokenCancel.addEventListener('click', cerrarTokenModal);
btnToken.addEventListener('click', () => abrirTokenModal());

// ---------- PTT ----------

function habilitarPtt() {
  if (auth.hasToken()) {
    ptt.disabled = false;
    pttHint.textContent = 'Mantén pulsado para dictar.';
  } else {
    ptt.disabled = true;
    pttHint.textContent = 'Configura el token para empezar.';
  }
}

async function pttDown(ev) {
  ev.preventDefault();
  if (ptt.disabled) return;
  if (recorder) return;
  try {
    recorder = new Recorder();
    await recorder.start();
    ptt.classList.add('recording');
    pttStartMs = Date.now();
    pttTimer.textContent = '0:00';
    pttHint.textContent = 'Grabando… suelta para enviar.';
    pttTimerId = setInterval(actualizarTimer, 250);
    try { ptt.setPointerCapture?.(ev.pointerId); } catch {}
  } catch (e) {
    recorder = null;
    banderaError('No se pudo acceder al micrófono: ' + e.message);
  }
}

function actualizarTimer() {
  const s = Math.floor((Date.now() - pttStartMs) / 1000);
  const mm = String(Math.floor(s / 60));
  const ss = String(s % 60).padStart(2, '0');
  pttTimer.textContent = `${mm}:${ss}`;
}

async function pttUp(ev) {
  ev.preventDefault();
  if (!recorder) return;
  ptt.classList.remove('recording');
  clearInterval(pttTimerId);
  pttTimerId = null;
  const segundos = Math.floor((Date.now() - pttStartMs) / 1000);
  try {
    const blob = await recorder.stop();
    recorder = null;
    pttTimer.textContent = '';
    if (!blob || blob.size < 1024 || segundos < 1) {
      pttHint.textContent = 'Mantén pulsado para dictar.';
      banderaWarning('Audio demasiado corto.');
      return;
    }
    const nota = await db.addNota({
      tipo: 'audio',
      audio_blob: blob,
      ts_iso: new Date().toISOString(),
      origen: 'voz_movil',
    });
    pttHint.textContent = `Encolada (${segundos}s).`;
    await renderPendientes();
    sync.programarSync();
  } catch (e) {
    banderaError('Error al guardar audio: ' + e.message);
    recorder = null;
    pttTimer.textContent = '';
  }
}

ptt.addEventListener('pointerdown', pttDown);
ptt.addEventListener('pointerup', pttUp);
ptt.addEventListener('pointercancel', pttUp);
ptt.addEventListener('contextmenu', e => e.preventDefault());

// Tecla espacio en desktop como bonus
window.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && !e.repeat && document.activeElement !== textInput && !ptt.disabled && !recorder) {
    e.preventDefault();
    pttDown({ preventDefault: () => {}, pointerId: -1 });
  }
});
window.addEventListener('keyup', (e) => {
  if (e.code === 'Space' && recorder) {
    e.preventDefault();
    pttUp({ preventDefault: () => {} });
  }
});

// ---------- Texto rápido ----------

textForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const txt = textInput.value.trim();
  if (!txt) return;
  if (!auth.hasToken()) {
    abrirTokenModal('Configura el token antes.');
    return;
  }
  await db.addNota({
    tipo: 'texto',
    texto: txt,
    ts_iso: new Date().toISOString(),
    origen: 'voz_movil',
  });
  textInput.value = '';
  banderaInfo('Encolada.');
  await renderPendientes();
  sync.programarSync();
});

// ---------- Lista pendientes ----------

function fmtHora(ts) {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

function previewNota(n) {
  if (n.tipo === 'texto') return n.texto || '(sin texto)';
  if (n.audio_blob) {
    const kb = (n.audio_blob.size / 1024).toFixed(0);
    return `🎙 audio · ${kb} KB`;
  }
  return '(audio)';
}

async function renderPendientes() {
  const pend = await db.listarPendientes();
  pendingCt.textContent = String(pend.length);
  if (pend.length === 0) {
    pendingUl.innerHTML = '<li class="empty">Sin notas en cola.</li>';
    return;
  }
  pendingUl.innerHTML = '';
  for (const n of pend) {
    const li = document.createElement('li');
    li.className = 'pending-item';
    const status = n.status || 'pendiente';
    const reintento = (n.intentos > 0 && n.status === 'pendiente')
      ? ` · reintentos ${n.intentos}/${5}` : '';
    li.innerHTML = `
      <div class="meta">
        <span>${fmtHora(n.ts_iso)}</span>
        <span class="status ${status}">${status}${reintento}</span>
      </div>
      <div class="preview"></div>
    `;
    li.querySelector('.preview').textContent = previewNota(n);
    pendingUl.appendChild(li);
  }
}

// ---------- Red & sync bus ----------

function refrescarRed() {
  if (navigator.onLine) {
    netInd.className = 'net-indicator online';
    netText.textContent = 'online';
  } else {
    netInd.className = 'net-indicator offline';
    netText.textContent = 'offline · sincronizará al reconectar';
  }
}

window.addEventListener('online', () => { refrescarRed(); sync.flush(); });
window.addEventListener('offline', refrescarRed);

sync.bus.addEventListener('progress', renderPendientes);
sync.bus.addEventListener('flush-done', (e) => {
  renderPendientes();
  const { enviadas, fallidas } = e.detail || {};
  if (enviadas) banderaInfo(`${enviadas} enviada${enviadas === 1 ? '' : 's'}.`);
  if (fallidas) banderaWarning(`${fallidas} en error — reintenta más tarde.`);
});
sync.bus.addEventListener('auth-invalido', () => {
  abrirTokenModal('Token inválido o revocado. Pega uno nuevo.');
});

btnFlush.addEventListener('click', () => {
  if (!auth.hasToken()) { abrirTokenModal('Configura el token antes.'); return; }
  sync.flush();
});

// ---------- Service Worker ----------

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('[voz] SW registrado:', reg.scope))
    .catch(err => console.warn('[voz] SW falló:', err));

  navigator.serviceWorker.addEventListener('message', (e) => {
    if (e.data?.tipo === 'flush-please' && navigator.onLine && auth.hasToken()) {
      sync.flush();
    }
  });
}

// ---------- Init ----------

(async function init() {
  refrescarRed();
  habilitarPtt();
  await db.purgarMasDe7Dias().catch(() => 0);
  await renderPendientes();
  sync.arrancarAutoFlush();
  if (!auth.hasDeviceLabel()) {
    abrirDeviceModal();
  } else if (!auth.hasToken()) {
    abrirTokenModal('Pega el token Bearer emitido desde el VPS.');
  } else if (navigator.onLine) {
    sync.flush();
  }
})();
