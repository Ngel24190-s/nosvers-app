/**
 * voz/js/db.js — Wrapper IndexedDB.
 *
 * Store `notas_pendientes` (keyPath: id, autoincrement: false).
 *
 * Schema:
 *   id           string  uuid v4 generado en cliente — sirve de client_uuid
 *   tipo         'texto' | 'audio'
 *   texto        string  (vacío si tipo=audio)
 *   audio_blob   Blob    (null si tipo=texto)
 *   ts_iso       string  ISO con offset, captura local
 *   etiqueta     string  'auto' por defecto
 *   origen       string  'voz_movil'
 *   intentos     number  0..5
 *   status       'pendiente' | 'enviando' | 'enviada' | 'error'
 *   ultimo_error string  (opcional)
 *   created_at   number  Date.now()
 *
 * Las entradas con status === 'enviada' se purgan a los 7 días.
 */

const DB_NAME = 'nosvers-voz';
const DB_VERSION = 1;
const STORE = 'notas_pendientes';
const TTL_MS = 7 * 24 * 60 * 60 * 1000;

let _dbPromise = null;

function openDb() {
  if (_dbPromise) return _dbPromise;
  _dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id' });
        store.createIndex('status', 'status', { unique: false });
        store.createIndex('created_at', 'created_at', { unique: false });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return _dbPromise;
}

function tx(mode) {
  return openDb().then(db => db.transaction(STORE, mode).objectStore(STORE));
}

function reqAsPromise(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

export function nuevoId() {
  // crypto.randomUUID() en navegadores modernos (Chrome 92+, todos los Android target)
  if (crypto.randomUUID) return crypto.randomUUID();
  // Fallback
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export async function addNota(nota) {
  const store = await tx('readwrite');
  const completa = {
    id: nota.id || nuevoId(),
    tipo: nota.tipo,
    texto: nota.texto || '',
    audio_blob: nota.audio_blob || null,
    ts_iso: nota.ts_iso || new Date().toISOString(),
    etiqueta: nota.etiqueta || 'auto',
    origen: nota.origen || 'voz_movil',
    intentos: 0,
    status: 'pendiente',
    ultimo_error: '',
    created_at: Date.now(),
  };
  await reqAsPromise(store.add(completa));
  return completa;
}

export async function listarPendientes() {
  const store = await tx('readonly');
  const all = await reqAsPromise(store.getAll());
  return all
    .filter(n => n.status !== 'enviada')
    .sort((a, b) => a.created_at - b.created_at);
}

export async function listarTodas() {
  const store = await tx('readonly');
  return await reqAsPromise(store.getAll());
}

export async function obtener(id) {
  const store = await tx('readonly');
  return await reqAsPromise(store.get(id));
}

export async function actualizar(id, patch) {
  const store = await tx('readwrite');
  const actual = await reqAsPromise(store.get(id));
  if (!actual) return null;
  const nueva = { ...actual, ...patch };
  await reqAsPromise(store.put(nueva));
  return nueva;
}

export async function marcarEnviada(id, resultado) {
  return actualizar(id, {
    status: 'enviada',
    enviada_at: Date.now(),
    resultado: resultado || null,
  });
}

export async function eliminar(id) {
  const store = await tx('readwrite');
  await reqAsPromise(store.delete(id));
}

export async function purgarMasDe7Dias() {
  const store = await tx('readwrite');
  const corte = Date.now() - TTL_MS;
  const all = await reqAsPromise(store.getAll());
  let borradas = 0;
  for (const n of all) {
    if (n.status === 'enviada' && (n.enviada_at || n.created_at) < corte) {
      await reqAsPromise(store.delete(n.id));
      borradas++;
    }
  }
  return borradas;
}
