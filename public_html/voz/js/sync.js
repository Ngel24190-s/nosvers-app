/**
 * voz/js/sync.js — Envío de notas pendientes al MCP server.
 *
 * Estrategia:
 *   - Pasada secuencial sobre listarPendientes()
 *   - Por nota: POST multipart (audio) o POST JSON (texto)
 *   - Backoff exponencial intra-nota: 1, 2, 4, 8, 16s (max 5 intentos)
 *   - Tras 5 fallos, status='error' (queda visible para reintentar manual)
 *   - Si recibe 401 → emite evento 'auth-invalido' y aborta
 *
 * El timestamp original (ts_iso) se preserva — el backend lo respeta.
 */

import * as db from './db.js';
import { getToken, getDeviceLabel } from './auth.js';

export const API_BASE = window.NOSVERS_API_BASE
  || 'https://nosvers-mcp.72.61.160.108.nip.io';

const MAX_INTENTOS = 5;
const BACKOFFS_MS = [1000, 2000, 4000, 8000, 16000];

class SyncBus extends EventTarget {}
export const bus = new SyncBus();

let _enCurso = false;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function enviarNota(nota) {
  const token = getToken();
  if (!token) {
    const err = new Error('sin_token');
    err.code = 'sin_token';
    throw err;
  }
  const deviceLabel = getDeviceLabel();

  const url = `${API_BASE}/voz/api/capturar`;
  const headers = { 'Authorization': `Bearer ${token}` };

  let res;
  if (nota.tipo === 'audio' && nota.audio_blob) {
    const fd = new FormData();
    fd.append('meta', JSON.stringify({
      texto: nota.texto || '',
      ts_iso: nota.ts_iso,
      etiqueta: nota.etiqueta || 'auto',
      origen: nota.origen || 'voz_movil',
      device_label: deviceLabel,
      client_uuid: nota.id,
    }));
    fd.append('audio', nota.audio_blob, 'nota.opus');
    res = await fetch(url, { method: 'POST', headers, body: fd });
  } else {
    headers['Content-Type'] = 'application/json';
    res = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        texto: nota.texto,
        ts_iso: nota.ts_iso,
        etiqueta: nota.etiqueta || 'auto',
        origen: nota.origen || 'voz_movil',
        device_label: deviceLabel,
        client_uuid: nota.id,
      }),
    });
  }

  if (res.status === 401) {
    const err = new Error('auth_invalido');
    err.code = 'auth_invalido';
    throw err;
  }

  let body = null;
  try { body = await res.json(); } catch { /* ignore */ }

  if (!res.ok || !body?.ok) {
    const err = new Error(body?.error || `http_${res.status}`);
    err.status = res.status;
    err.body = body;
    throw err;
  }
  return body;
}

/**
 * Procesa una sola nota con reintentos y backoff intra-nota.
 * Retorna true si quedó enviada.
 */
async function procesarNota(nota) {
  await db.actualizar(nota.id, { status: 'enviando' });
  bus.dispatchEvent(new CustomEvent('progress'));

  for (let i = nota.intentos; i < MAX_INTENTOS; i++) {
    try {
      const resultado = await enviarNota(nota);
      await db.marcarEnviada(nota.id, resultado);
      bus.dispatchEvent(new CustomEvent('progress'));
      return true;
    } catch (err) {
      if (err.code === 'auth_invalido' || err.code === 'sin_token') {
        await db.actualizar(nota.id, {
          status: 'pendiente',
          ultimo_error: err.message,
        });
        bus.dispatchEvent(new CustomEvent('auth-invalido'));
        return false;
      }
      const intentos = i + 1;
      const restantes = MAX_INTENTOS - intentos;
      await db.actualizar(nota.id, {
        intentos,
        status: restantes > 0 ? 'pendiente' : 'error',
        ultimo_error: err.message || 'error',
      });
      bus.dispatchEvent(new CustomEvent('progress'));
      if (restantes === 0) return false;
      const espera = BACKOFFS_MS[i] || 16000;
      if (!navigator.onLine) return false;  // si nos quedamos sin red, salimos
      await sleep(espera);
    }
  }
  return false;
}

export async function flush() {
  if (_enCurso) return { skipped: true };
  _enCurso = true;
  let enviadas = 0;
  let fallidas = 0;
  try {
    if (!navigator.onLine) {
      bus.dispatchEvent(new CustomEvent('offline'));
      return { enviadas, fallidas, offline: true };
    }
    const pendientes = (await db.listarPendientes())
      .filter(n => n.status === 'pendiente' && n.intentos < MAX_INTENTOS);
    for (const n of pendientes) {
      const ok = await procesarNota(n);
      ok ? enviadas++ : fallidas++;
      if (!navigator.onLine) break;
    }
  } finally {
    _enCurso = false;
    bus.dispatchEvent(new CustomEvent('flush-done', { detail: { enviadas, fallidas } }));
  }
  return { enviadas, fallidas };
}

/**
 * Registra una sync etiqueta para Background Sync (cuando el SW lo soporta).
 * Si no hay SW o no soporta SyncManager, fallback a flush() directo.
 */
export async function programarSync() {
  if ('serviceWorker' in navigator && 'SyncManager' in window) {
    try {
      const reg = await navigator.serviceWorker.ready;
      await reg.sync.register('notas-pendientes');
      return { backgroundSync: true };
    } catch {
      // sigue al fallback
    }
  }
  // Fallback: intenta ya mismo si hay red
  if (navigator.onLine) flush();
  return { backgroundSync: false };
}

export function arrancarAutoFlush() {
  window.addEventListener('online', () => flush());
  // Periódico ligero — cada 60s mientras la PWA esté abierta
  setInterval(() => { if (navigator.onLine) flush(); }, 60_000);
}
