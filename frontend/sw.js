// GalleryWeb Service Worker — v2
// v1 index.html'i Cache-First sunuyordu → yeni ?v= sürümleri kullanıcıya hiç
// ulaşmıyordu. v2: HTML/navigasyon Network-First (online'da hep taze),
// statikler Stale-While-Revalidate (offline çalışır + arka planda güncellenir).
const STATIC_CACHE = 'gallery-static-v2';
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

    // HTML / navigasyon (index.html dahil) — Network First.
    // Cache-First idi → yeni ?v= sürümlerini işaret eden taze index.html asla
    // gelmiyordu. Artık online'da hep taze, offline'da cache'e düşer.
    if (event.request.mode === 'navigate' ||
        url.pathname === '/' ||
        (event.request.destination === 'document')) {
        event.respondWith(networkFirstDoc(event.request));
        return;
    }

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

    // Static assets (css/js) — Stale-While-Revalidate: anında cache'ten ver,
    // arka planda güncelle. ?v= bump zaten yeni URL = taze getirir; bu strateji
    // versiyonsuz istekleri de bir sonraki yüklemede tazeler (Cache-First'te
    // asla tazelenmiyordu).
    event.respondWith(staleWhileRevalidate(event.request, STATIC_CACHE));
});

// Doküman için Network-First: online taze HTML, çevrimdışı cache fallback.
async function networkFirstDoc(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch {
        const cached = await caches.match(request) || await caches.match('/');
        return cached || new Response('Çevrimdışı', { status: 503 });
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
