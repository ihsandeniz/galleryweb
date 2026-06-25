// GalleryWeb Auth Module — JWT management, login/signup/logout/refresh
(function () {
    'use strict';

    const AUTH_BASE = window.location.origin;
    const KEYS = {
        token:   'gw_access_token',
        refresh: 'gw_refresh_token',
        expiry:  'gw_token_expiry',
        user:    'gw_user',
    };

    function getToken()  { return localStorage.getItem(KEYS.token); }
    function getRefresh(){ return localStorage.getItem(KEYS.refresh); }

    function getUser() {
        try { return JSON.parse(localStorage.getItem(KEYS.user)); } catch { return null; }
    }

    function isTokenValid() {
        if (!getToken()) return false;
        const expiry = parseInt(localStorage.getItem(KEYS.expiry) || '0', 10);
        return expiry > Math.floor(Date.now() / 1000) + 60;
    }

    function authHeaders() {
        const t = getToken();
        return t ? { 'Authorization': `Bearer ${t}` } : {};
    }

    function clearAuth() {
        [KEYS.token, KEYS.refresh, KEYS.expiry, KEYS.user].forEach(k => localStorage.removeItem(k));
    }

    function storeAuth(data) {
        if (data.access_token)  localStorage.setItem(KEYS.token, data.access_token);
        if (data.refresh_token) localStorage.setItem(KEYS.refresh, data.refresh_token);
        const expiry = Math.floor(Date.now() / 1000) + (data.expires_in || 3600);
        localStorage.setItem(KEYS.expiry, String(expiry));
        if (data.user) localStorage.setItem(KEYS.user, JSON.stringify(data.user));
    }

    async function refreshToken() {
        const rt = getRefresh();
        if (!rt) return false;
        try {
            const res = await fetch(`${AUTH_BASE}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: rt }),
            });
            if (!res.ok) { clearAuth(); return false; }
            const data = await res.json();
            storeAuth(data);
            window.dispatchEvent(new CustomEvent('gw:token-refreshed', {
                detail: { token: data.access_token },
            }));
            return true;
        } catch { return false; }
    }

    async function requireAuth() {
        if (isTokenValid()) return true;
        if (getRefresh() && await refreshToken()) return true;
        // Demo bypass: doğrudan demo kullanıcıyla otomatik giriş yap
        try {
            const res = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: 'demo@gallery.local', password: 'demo1234' }),
            });
            if (res.ok) { storeAuth(await res.json()); return true; }
        } catch { /* ignore */ }
        window.location.href = '/login';
        return false;
    }

    async function login(email, password) {
        const res = await fetch(`${AUTH_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
            const d = await res.json().catch(() => ({}));
            throw new Error(d.detail || 'Giriş başarısız');
        }
        const data = await res.json();
        storeAuth(data);
        return data;
    }

    async function signup(email, password, fullName) {
        const res = await fetch(`${AUTH_BASE}/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, full_name: fullName || null }),
        });
        if (!res.ok) {
            const d = await res.json().catch(() => ({}));
            throw new Error(d.detail || 'Kayıt başarısız');
        }
        const data = await res.json();
        storeAuth(data);
        return data;
    }

    async function logout() {
        try {
            await fetch(`${AUTH_BASE}/auth/logout`, {
                method: 'POST',
                headers: { ...authHeaders(), 'Content-Type': 'application/json' },
            });
        } catch { /* non-fatal */ }
        clearAuth();
        window.location.href = '/login';
    }

    // Schedule proactive token refresh 5 min before expiry
    function scheduleRefresh() {
        const expiry = parseInt(localStorage.getItem(KEYS.expiry) || '0', 10);
        const delay  = Math.max(30, expiry - Math.floor(Date.now() / 1000) - 300) * 1000;
        if (delay < 86_400_000) {
            setTimeout(async () => {
                if (getRefresh()) { await refreshToken(); scheduleRefresh(); }
            }, delay);
        }
    }

    window.GW = { getToken, getUser, isTokenValid, authHeaders, clearAuth, storeAuth,
                  refreshToken, requireAuth, login, signup, logout };

    if (isTokenValid()) scheduleRefresh();
}());
