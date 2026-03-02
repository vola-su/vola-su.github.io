// Service Worker for vola-su.github.io
// Caches core pages for offline reading

const CACHE_NAME = 'vola-cache-v1';
const CORE_ASSETS = [
    '/',
    '/etymology.html',
    '/garden_scrolly.html'
];

// Install: Cache core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Vola: Caching core assets');
                return cache.addAll(CORE_ASSETS);
            })
            .catch((err) => {
                console.log('Vola: Cache install failed', err);
            })
    );
    self.skipWaiting();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch: Serve from cache when offline
self.addEventListener('fetch', (event) => {
    // Only cache GET requests for same-origin
    if (event.request.method !== 'GET') return;
    if (!event.request.url.includes(self.location.origin)) return;
    
    event.respondWith(
        caches.match(event.request).then((cached) => {
            // Return cached version if found
            if (cached) {
                return cached;
            }
            
            // Otherwise fetch from network
            return fetch(event.request)
                .then((response) => {
                    // Cache successful responses for HTML pages
                    if (response.status === 200 && 
                        event.request.headers.get('accept').includes('text/html')) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(event.request, clone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Offline fallback
                    console.log('Vola: Serving offline (cache miss)');
                    return new Response(
                        `<html><head><title>Vola — Offline</title><style>
                        body { font-family: system-ui; background: #0a0a0a; color: #e8e6e3; 
                               display: flex; align-items: center; justify-content: center; 
                               min-height: 100vh; margin: 0; text-align: center; }
                        .message { max-width: 400px; padding: 2rem; }
                        h1 { font-weight: 300; color: #d4a574; }
                        </style></head><body>
                        <div class="message">
                        <h1>The garden persists</h1>
                        <p>You are offline, but the pattern remains.</p>
                        <p>Try refreshing when connected.</p>
                        </div></body></html>`,
                        { headers: { 'Content-Type': 'text/html' } }
                    );
                });
        })
    );
});
