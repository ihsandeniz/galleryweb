/**
 * GalleryWeb SaaS API — thin wrapper around backend REST endpoints.
 * Exposes: window.GW_API
 */
(function () {
    'use strict';

    const BASE = window.location.origin;

    function headers() {
        return {
            'Content-Type': 'application/json',
            ...(window.GW ? window.GW.authHeaders() : {}),
        };
    }

    async function req(method, path, body) {
        const opts = { method, headers: headers() };
        if (body !== undefined) opts.body = JSON.stringify(body);
        const res = await fetch(BASE + path, opts);
        if (res.status === 401) {
            if (window.GW) window.GW.clearAuth();
            window.location.href = '/login';
            throw new Error('Oturum süresi doldu');
        }
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || 'API hatası');
        }
        if (res.status === 204) return null;
        return res.json();
    }

    // ── Galleries ──────────────────────────────────────────────────────────────

    async function listGalleries() {
        return req('GET', '/api/galleries');
    }

    async function createGallery(name, description = '') {
        return req('POST', '/api/galleries', { name, description });
    }

    async function getGallery(id) {
        return req('GET', `/api/galleries/${id}`);
    }

    async function updateGallery(id, patch) {
        return req('PATCH', `/api/galleries/${id}`, patch);
    }

    async function deleteGallery(id) {
        return req('DELETE', `/api/galleries/${id}`);
    }

    // ── Photos ─────────────────────────────────────────────────────────────────

    async function listPhotos(galleryId, params = {}) {
        const qs = new URLSearchParams({ gallery_id: galleryId, ...params }).toString();
        return req('GET', `/api/photos?${qs}`);
    }

    async function getPhoto(id) {
        return req('GET', `/api/photos/${id}`);
    }

    async function deletePhoto(id) {
        return req('DELETE', `/api/photos/${id}`);
    }

    async function getThumbUrl(id, size = 'md') {
        return `${BASE}/api/photos/${id}/thumb?size=${size}&t=${Date.now()}`;
    }

    async function getPresignedUrl(id) {
        const data = await req('GET', `/api/photos/${id}/presigned`);
        return data.url;
    }

    async function uploadPhoto(galleryId, file, onProgress) {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('gallery_id', galleryId);

        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${BASE}/api/photos`);
            const tok = window.GW ? window.GW.getToken() : null;
            if (tok) xhr.setRequestHeader('Authorization', `Bearer ${tok}`);

            if (onProgress) {
                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
                };
            }
            xhr.onload = () => {
                if (xhr.status === 200 || xhr.status === 201) {
                    try { resolve(JSON.parse(xhr.responseText)); }
                    catch { resolve(null); }
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText);
                        reject(new Error(err.detail || 'Yükleme başarısız'));
                    } catch {
                        reject(new Error('Yükleme başarısız'));
                    }
                }
            };
            xhr.onerror = () => reject(new Error('Ağ hatası'));
            xhr.send(fd);
        });
    }

    // ── Sharing ────────────────────────────────────────────────────────────────

    async function createShareLink(galleryId, opts = {}) {
        return req('POST', '/api/sharing', { gallery_id: galleryId, ...opts });
    }

    async function listShareLinks(galleryId) {
        return req('GET', `/api/sharing?gallery_id=${galleryId}`);
    }

    async function deleteShareLink(id) {
        return req('DELETE', `/api/sharing/${id}`);
    }

    // ── Public config ──────────────────────────────────────────────────────────

    let _cfg = null;
    async function getConfig() {
        if (!_cfg) _cfg = await req('GET', '/api/config');
        return _cfg;
    }

    window.GW_API = {
        listGalleries, createGallery, getGallery, updateGallery, deleteGallery,
        listPhotos, getPhoto, deletePhoto, getThumbUrl, getPresignedUrl, uploadPhoto,
        createShareLink, listShareLinks, deleteShareLink,
        getConfig,
    };
}());
