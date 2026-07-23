/**
 * GalleryWeb Realtime — Supabase Realtime + offline queue.
 * Depends on: saas-api.js (GW_API), auth.js (GW)
 * Supabase JS v2 loaded via CDN before this script.
 * Exposes: window.GW_RT
 */
(function () {
    'use strict';

    let _sb = null;
    let _channel = null;
    let _presenceChannel = null;
    const _handlers = { photoAdded: [], photoDeleted: [], presence: [], reconnect: [] };
    const OFFLINE_QUEUE_KEY = 'gw_offline_queue';

    // ── Offline queue ──────────────────────────────────────────────────────────

    // UI-F002: eski/bozuk şema localStorage'da takılı kalmasın — parse edilemeyen
    // kuyruğu güvenle sıfırla (JSON.parse zaten try/catch'te, ama bozuk veri kalıcıydı).
    function _readQueue() {
        const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
        if (!raw) return [];
        try {
            const q = JSON.parse(raw);
            return Array.isArray(q) ? q : [];
        } catch (e) {
            console.warn('Bozuk offline kuyruğu sıfırlanıyor:', e);
            localStorage.removeItem(OFFLINE_QUEUE_KEY);
            return [];
        }
    }

    function queueOp(op) {
        try {
            const q = _readQueue();
            q.push({ ...op, ts: Date.now() });
            localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(q.slice(-50))); // max 50
        } catch { /* ignore */ }
    }

    async function flushQueue() {
        try {
            const q = _readQueue();
            if (!q.length) return;

            const remaining = [];
            for (const op of q) {
                try {
                    if (op.type === 'delete_photo') {
                        await window.GW_API.deletePhoto(op.id);
                    } else if (op.type === 'create_gallery') {
                        await window.GW_API.createGallery(op.name, op.description);
                    }
                    // success — don't push to remaining
                } catch {
                    remaining.push(op);
                }
            }
            if (remaining.length) {
                localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
            } else {
                localStorage.removeItem(OFFLINE_QUEUE_KEY);
            }
            _handlers.reconnect.forEach(fn => fn({ flushed: q.length - remaining.length }));
        } catch { /* ignore */ }
    }

    function queueLength() {
        return _readQueue().length;
    }

    // ── Supabase init ──────────────────────────────────────────────────────────

    async function _initSupabase() {
        if (_sb) return _sb;
        if (!window.supabase) {
            console.warn('[GW_RT] Supabase JS not loaded — realtime disabled');
            return null;
        }
        try {
            const cfg = await window.GW_API.getConfig();
            _sb = window.supabase.createClient(cfg.supabase_url, cfg.supabase_anon_key, {
                auth: { persistSession: false, autoRefreshToken: false },
                realtime: { params: { eventsPerSecond: 10 } },
            });
            const token = window.GW ? window.GW.getToken() : null;
            if (token) _sb.realtime.setAuth(token);
        } catch (e) {
            console.warn('[GW_RT] Supabase init failed:', e);
            return null;
        }
        return _sb;
    }

    // ── Realtime channels ──────────────────────────────────────────────────────

    async function connect(galleryId) {
        const sb = await _initSupabase();
        if (!sb) return;

        disconnect();

        // Photos channel — Postgres Changes
        _channel = sb.channel(`gallery:${galleryId}`)
            .on('postgres_changes', {
                event: 'INSERT',
                schema: 'public',
                table: 'photos',
                filter: `gallery_id=eq.${galleryId}`,
            }, (payload) => {
                _handlers.photoAdded.forEach(fn => fn(payload.new));
            })
            .on('postgres_changes', {
                event: 'DELETE',
                schema: 'public',
                table: 'photos',
                filter: `gallery_id=eq.${galleryId}`,
            }, (payload) => {
                _handlers.photoDeleted.forEach(fn => fn(payload.old));
            })
            .subscribe((status) => {
                if (status === 'SUBSCRIBED') {
                    flushQueue();
                } else if (status === 'CHANNEL_ERROR') {
                    console.warn('[GW_RT] Channel error — will retry');
                }
            });

        // Presence channel
        _presenceChannel = sb.channel(`presence:${galleryId}`, {
            config: { presence: { key: _currentUserId() } },
        });

        _presenceChannel
            .on('presence', { event: 'sync' }, () => {
                const state = _presenceChannel.presenceState();
                const users = Object.values(state).flat().map(u => u.user_id).filter(Boolean);
                _handlers.presence.forEach(fn => fn(users));
            })
            .subscribe(async (status) => {
                if (status === 'SUBSCRIBED') {
                    await _presenceChannel.track({
                        user_id: _currentUserId(),
                        online_at: new Date().toISOString(),
                    });
                }
            });
    }

    function disconnect() {
        if (_channel) { _channel.unsubscribe(); _channel = null; }
        if (_presenceChannel) { _presenceChannel.unsubscribe(); _presenceChannel = null; }
    }

    function updateToken(token) {
        if (_sb) _sb.realtime.setAuth(token);
    }

    function _currentUserId() {
        const u = window.GW ? window.GW.getUser() : null;
        return u ? u.id : 'anonymous';
    }

    // ── Event registration ─────────────────────────────────────────────────────

    function onPhotoAdded(fn)    { _handlers.photoAdded.push(fn); }
    function onPhotoDeleted(fn)  { _handlers.photoDeleted.push(fn); }
    function onPresenceChange(fn){ _handlers.presence.push(fn); }
    function onReconnect(fn)     { _handlers.reconnect.push(fn); }

    // ── Online/offline bridge ──────────────────────────────────────────────────

    window.addEventListener('online', () => {
        flushQueue();
    });

    window.addEventListener('offline', () => {
        console.info('[GW_RT] Offline — operations will queue');
    });

    // ── Expose ─────────────────────────────────────────────────────────────────

    window.GW_RT = {
        connect,
        disconnect,
        updateToken,
        queueOp,
        flushQueue,
        queueLength,
        onPhotoAdded,
        onPhotoDeleted,
        onPresenceChange,
        onReconnect,
    };
}());
