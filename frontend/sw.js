// GalleryWeb Service Worker — v1
const STATIC_CACHE = 'gallery-static-v1';
const THUMB_CACHE  = 'gallery-thumbs-v1';

const STATIC_ASSETS = [
    '/',
    '/static/js/gallery.js',
    '/static/js/keybinds.js',
    '/static/js/slideshow.js',
    '/static/css/style.css'
];

// ── Install: pre-cache static assets ──────────────────────────────────────────
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// ── Activate: remove old caches ───────────────────────────────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys
                .filter(k => k !== STATIC_CACHE && k !== THUMB_CACHE)
                .map(k => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// ── Fetch strategy ────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // API data — Network First (always fresh)
    if (url.pathname.startsWith('/api/') && !url.pathname.startsWith('/api/thumbnail') && !url.pathname.startsWith('/api/image')) {
        event.respondWith(networkFirst(event.request));
        return;
    }

    // Thumbnails / images — Stale-While-Revalidate
    if (url.pathname.startsWith('/api/image') || url.pathname.startsWith('/api/thumbnail')) {
        event.respondWith(staleWhileRevalidate(event.request, THUMB_CACHE));
        return;
    }

    // Static assets — Cache First
    event.respondWith(cacheFirst(event.request, STATIC_CACHE));
});

async function cacheFirst(request, cacheName) {
    const cached = await caches.match(request);
    if (cached) return cached;
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch {
        return new Response('Çevrimdışı — önbellekte yok', { status: 503 });
    }
}

async function networkFirst(request) {
    try {
        return await fetch(request);
    } catch {
        const cached = await caches.match(request);
        return cached || new Response(JSON.stringify({ error: 'offline' }), {
            status: 503, headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    const networkPromise = fetch(request).then(response => {
        if (response.ok) cache.put(request, response.clone());
        return response;
    }).catch(() => null);
    return cached || await networkPromise || new Response('', { status: 503 });
}
