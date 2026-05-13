/**
 * voz/sw.js — Service Worker para NosVers Voz.
 *
 * Responsabilidades:
 *   1. Cache de los assets estáticos (shell offline) — versión 'v1'.
 *   2. Background Sync con etiqueta 'notas-pendientes'.
 *   3. Fallback offline en navegaciones (sirve index.html del cache).
 *
 * El SW NO toca IndexedDB directamente — al recibir sync, postMessage al
 * cliente activo y deja que app.js corra `sync.flush()`. Si no hay cliente
 * abierto, el flush ocurre la próxima vez que abran la PWA.
 *
 * Para forzar update tras un deploy: bumpear CACHE_NAME.
 */

const CACHE_NAME = 'nosvers-voz-v2';

const PRECACHE = [
  '/',
  '/index.html',
  '/manifest.json',
  '/css/styles.css',
  '/js/app.js',
  '/js/db.js',
  '/js/auth.js',
  '/js/recorder.js',
  '/js/sync.js',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // No tocar llamadas a la API: la cola IndexedDB se encarga de offline.
  if (url.pathname.startsWith('/voz/api/')) return;
  if (url.host !== self.location.host) return;

  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) return cached;
      return fetch(req)
        .then(res => {
          // Cache opportunistic de assets propios
          if (res.ok && (url.pathname.startsWith('/css/') ||
                         url.pathname.startsWith('/js/')  ||
                         url.pathname.startsWith('/assets/'))) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then(c => c.put(req, copy));
          }
          return res;
        })
        .catch(() => {
          // Navegación offline → shell
          if (req.mode === 'navigate') {
            return caches.match('/index.html');
          }
          return new Response('offline', { status: 503 });
        });
    })
  );
});

self.addEventListener('sync', (event) => {
  if (event.tag !== 'notas-pendientes') return;
  event.waitUntil(notificarClientes('flush-please'));
});

async function notificarClientes(tipo) {
  const cs = await self.clients.matchAll({ includeUncontrolled: true, type: 'window' });
  for (const c of cs) c.postMessage({ tipo });
}
