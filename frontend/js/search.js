/* GalleryWeb — CLIP Semantic Search UI (Faz 7)
 * Attaches to existing #searchInput and adds an AI toggle button.
 * VIP2+ only — shows upgrade banner for other tiers.
 */
(function () {
    'use strict';

    let _aiMode = false;
    let _debounceTimer = null;
    const DEBOUNCE_MS = 400;

    // ── Bootstrap (after DOM ready) ────────────────────────────────────────────
    function init() {
        const searchWrap = document.querySelector('.topbar-search');
        const searchInput = document.getElementById('searchInput');
        if (!searchWrap || !searchInput) return;

        // AI toggle button
        const aiBtn = document.createElement('button');
        aiBtn.id = 'aiSearchBtn';
        aiBtn.className = 'topbar-btn ai-search-btn';
        aiBtn.title = 'AI Semantic Arama (VIP2+)';
        aiBtn.textContent = '✦ AI';
        searchWrap.appendChild(aiBtn);

        // Results overlay
        const overlay = document.createElement('div');
        overlay.id = 'aiSearchOverlay';
        overlay.className = 'ai-search-overlay hidden';
        overlay.innerHTML = `
            <div class="aso-header">
                <span class="aso-title">✦ AI Arama Sonuçları</span>
                <span id="asoQueryLabel" class="aso-query"></span>
                <button id="asoCloseBtn" class="btn-icon">✕</button>
            </div>
            <div id="asoBody" class="aso-body">
                <div id="asoLoading" class="aso-loading hidden">
                    <div class="spinner"></div><span>Aranıyor…</span>
                </div>
                <div id="asoGrid" class="aso-grid"></div>
                <div id="asoUpgrade" class="aso-upgrade hidden">
                    <p>✦ AI Semantik Arama <strong>VIP2</strong> ve üzeri planlarında kullanılabilir.</p>
                    <a href="/upgrade" class="btn-primary aso-upgrade-btn">Planı Yükselt</a>
                </div>
                <div id="asoEmpty" class="aso-empty hidden">Sonuç bulunamadı.</div>
            </div>
        `;
        document.body.appendChild(overlay);

        // Events
        aiBtn.addEventListener('click', toggleAiMode);
        document.getElementById('asoCloseBtn').addEventListener('click', closeOverlay);
        searchInput.addEventListener('input', onSearchInput);
        overlay.addEventListener('click', function (e) {
            if (e.target === overlay) closeOverlay();
        });
    }

    function toggleAiMode() {
        _aiMode = !_aiMode;
        const btn = document.getElementById('aiSearchBtn');
        const input = document.getElementById('searchInput');
        if (_aiMode) {
            btn.classList.add('ai-active');
            input.placeholder = 'AI ara: "sahilde gün batımı köpek"…';
            input.focus();
        } else {
            btn.classList.remove('ai-active');
            input.placeholder = 'Ara... (Ctrl+F)';
            closeOverlay();
        }
    }

    function onSearchInput(e) {
        if (!_aiMode) return;
        const q = e.target.value.trim();
        if (!q) { closeOverlay(); return; }
        clearTimeout(_debounceTimer);
        _debounceTimer = setTimeout(() => runSearch(q), DEBOUNCE_MS);
    }

    async function runSearch(q) {
        showOverlay(q);
        setLoading(true);

        try {
            const token = window.GW && window.GW.getToken ? window.GW.getToken() : null;
            const headers = token ? { Authorization: `Bearer ${token}` } : {};
            const url = `/api/search?q=${encodeURIComponent(q)}&limit=40`;
            const res = await fetch(url, { headers });

            if (res.status === 403) {
                const body = await res.json().catch(() => ({}));
                if (body.detail && body.detail.code === 'upgrade_required') {
                    showUpgradeBanner();
                    return;
                }
            }

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();
            renderResults(data.results || [], q);
        } catch (err) {
            renderError(err.message);
        } finally {
            setLoading(false);
        }
    }

    function showOverlay(q) {
        const overlay = document.getElementById('aiSearchOverlay');
        const label = document.getElementById('asoQueryLabel');
        overlay.classList.remove('hidden');
        if (label) label.textContent = `"${q}"`;
    }

    function closeOverlay() {
        const overlay = document.getElementById('aiSearchOverlay');
        if (overlay) overlay.classList.add('hidden');
    }

    function setLoading(on) {
        const el = document.getElementById('asoLoading');
        const grid = document.getElementById('asoGrid');
        if (!el) return;
        el.classList.toggle('hidden', !on);
        if (grid) grid.innerHTML = '';
        hide('asoUpgrade');
        hide('asoEmpty');
    }

    function renderResults(results, q) {
        const grid = document.getElementById('asoGrid');
        const empty = document.getElementById('asoEmpty');
        if (!grid) return;

        if (!results.length) {
            empty && empty.classList.remove('hidden');
            return;
        }

        grid.innerHTML = results.map(photo => {
            const thumbUrl = `/api/photos/${photo.id}/thumb?size=md`;
            const sim = photo.similarity != null
                ? `<span class="aso-sim">${(photo.similarity * 100).toFixed(0)}%</span>`
                : '';
            return `
                <div class="aso-card" data-id="${photo.id}" title="${escHtml(photo.filename)}">
                    <img class="aso-thumb" src="${thumbUrl}" alt="${escHtml(photo.filename)}"
                         onerror="this.style.display='none'">
                    <div class="aso-card-footer">
                        <span class="aso-fname">${escHtml(photo.filename)}</span>
                        ${sim}
                    </div>
                </div>`;
        }).join('');

        // Click → open in main gallery lightbox if available
        grid.querySelectorAll('.aso-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = parseInt(card.dataset.id, 10);
                if (window._galleryOpenById) window._galleryOpenById(id);
            });
        });
    }

    function showUpgradeBanner() {
        const grid = document.getElementById('asoGrid');
        if (grid) grid.innerHTML = '';
        show('asoUpgrade');
    }

    function renderError(msg) {
        const grid = document.getElementById('asoGrid');
        if (grid) grid.innerHTML = `<p class="aso-error">Hata: ${escHtml(msg)}</p>`;
    }

    function show(id) { const el = document.getElementById(id); if (el) el.classList.remove('hidden'); }
    function hide(id) { const el = document.getElementById(id); if (el) el.classList.add('hidden'); }
    function escHtml(s) {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    // ── Styles (injected) ─────────────────────────────────────────────────────
    const css = `
        .ai-search-btn { font-size: 11px; letter-spacing: .5px; opacity: .7; transition: opacity .2s, color .2s; }
        .ai-search-btn:hover, .ai-search-btn.ai-active { opacity: 1; color: var(--accent, #00d2ff); }
        .ai-search-overlay {
            position: fixed; inset: 0; z-index: 9000;
            background: rgba(0,0,0,.55); backdrop-filter: blur(4px);
            display: flex; align-items: flex-start; justify-content: center;
            padding-top: 60px;
        }
        .ai-search-overlay.hidden { display: none; }
        .ai-search-overlay > * { pointer-events: auto; }
        .aso-header {
            position: absolute; top: 60px; left: 50%; transform: translateX(-50%);
            width: min(860px, 96vw);
            display: flex; align-items: center; gap: 8px;
            background: var(--bg-panel, #10141a); border-bottom: 1px solid var(--border, #222a35);
            padding: 10px 14px; border-radius: 8px 8px 0 0;
        }
        .aso-title { font-size: 13px; font-weight: 600; color: var(--accent, #00d2ff); }
        .aso-query { font-size: 12px; color: var(--fg-dim, #677); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .aso-body {
            position: absolute; top: calc(60px + 41px); left: 50%; transform: translateX(-50%);
            width: min(860px, 96vw); max-height: 72vh; overflow-y: auto;
            background: var(--bg-panel, #10141a); border-radius: 0 0 8px 8px;
            padding: 14px;
        }
        .aso-loading { display: flex; align-items: center; gap: 8px; color: var(--fg-dim, #677); font-size: 13px; padding: 24px; }
        .aso-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px; }
        .aso-card { position: relative; cursor: pointer; border-radius: 6px; overflow: hidden;
            background: var(--bg-card, #181f27); border: 1px solid var(--border, #222a35);
            transition: border-color .15s, transform .15s; }
        .aso-card:hover { border-color: var(--accent, #00d2ff); transform: translateY(-2px); }
        .aso-thumb { width: 100%; aspect-ratio: 1; object-fit: cover; display: block; }
        .aso-card-footer { padding: 4px 6px; font-size: 10px; display: flex; justify-content: space-between; align-items: center; }
        .aso-fname { color: var(--fg-dim, #677); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 80%; }
        .aso-sim { color: var(--accent, #00d2ff); font-weight: 600; flex-shrink: 0; }
        .aso-upgrade { text-align: center; padding: 32px 16px; }
        .aso-upgrade p { margin-bottom: 16px; font-size: 14px; }
        .aso-upgrade-btn { display: inline-block; padding: 8px 20px; border-radius: 6px; background: var(--accent, #00d2ff); color: #000; font-weight: 600; text-decoration: none; }
        .aso-empty { text-align: center; padding: 32px; color: var(--fg-dim, #677); font-size: 13px; }
        .aso-error { color: #e55; font-size: 12px; padding: 16px; }
    `;
    const styleEl = document.createElement('style');
    styleEl.textContent = css;
    document.head.appendChild(styleEl);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
