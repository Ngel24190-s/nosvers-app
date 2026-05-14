/* Claudio PWA Service Worker (007) — offline-read + skipWaiting on demand. */
const CACHE_NAME = 'claudio-pwa-v1';
const SHELL = ['/', '/index.html', '/manifest.json', '/icon-192.svg', '/icon-512.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

function shouldCache(url) {
  if (!url.startsWith(self.location.origin)) return false;
  const path = new URL(url).pathname;
  if (path.startsWith('/tablero/api/')) return true;
  if (path.startsWith('/voz/api/')) return false; // POST/audio: nunca cache
  if (path.startsWith('/sw.js')) return false;
  if (path === '/manifest.json') return true;
  if (path.startsWith('/assets/')) return true;
  if (path === '/' || path.endsWith('.html')) return true;
  if (path.endsWith('.svg') || path.endsWith('.png')) return true;
  return false;
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  if (!shouldCache(req.url)) return;

  // Stale-while-revalidate
  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(req);
      const fetchPromise = fetch(req)
        .then((res) => {
          if (res && res.status === 200) {
            cache.put(req, res.clone()).catch(() => {});
          }
          return res;
        })
        .catch(() => cached);
      return cached || fetchPromise;
    })
  );
});
