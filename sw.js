// Cache the app shell and local icons. News and articles come from the server.
const CACHE = 'liiga365-shell-v1';
const ASSETS = ['/manifest.webmanifest', '/static/icons/liiga365-180.png', '/static/icons/liiga365-192.png', '/static/icons/liiga365-512.png'];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(['/', ...ASSETS])).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(key => key.startsWith('liiga365-shell-') && key !== CACHE).map(key => caches.delete(key))
  )).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => caches.match('/')));
    return;
  }
  if (ASSETS.includes(url.pathname + url.search)) {
    event.respondWith(caches.match(event.request).then(response => response || fetch(event.request)));
  }
});
