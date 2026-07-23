// ========== Vim-Style Keybindings ==========

// UI-F001: modül iki kez yüklenirse (dinamik reload / tekrar enjeksiyon) listener
// çiftlenmesin — eski kaydı iptal edip tek AbortController ile bağla.
if (window._keybindController) window._keybindController.abort();
window._keybindController = new AbortController();

document.addEventListener('keydown', (e) => {
    // Eğer input alanındaysa keybinding'leri devre dışı bırak
    if (e.target.tagName === 'INPUT') {
        // Sadece Escape'e izin ver
        if (e.key === 'Escape') {
            e.target.blur();
        }
        return;
    }
    
    // Lightbox açıkken
    if (!elements.lightbox.classList.contains('hidden')) {
        handleLightboxKeys(e);
        return;
    }
    
    // Normal modda
    handleGalleryKeys(e);
}, { signal: window._keybindController.signal });

function handleGalleryKeys(e) {
    switch(e.key.toLowerCase()) {
        case 'j':
        case 'arrowdown':
            e.preventDefault();
            window.scrollBy({ top: 200, behavior: 'smooth' });
            break;

        case 'arrowup':
            e.preventDefault();
            window.scrollBy({ top: -200, behavior: 'smooth' });
            break;
            
        case 'g':
            if (e.shiftKey) {
                // Shift+G: En alta git
                e.preventDefault();
                window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            } else {
                // gg: En üste git (iki kez g)
                if (lastKeyWasG) {
                    e.preventDefault();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    lastKeyWasG = false;
                } else {
                    lastKeyWasG = true;
                    setTimeout(() => lastKeyWasG = false, 500);
                }
            }
            break;
            
        case 'h':
        case 'arrowleft':
            // Önceki sayfa
            if (state.currentPage > 1) {
                changePage(-1);
            }
            break;
            
        case 'l':
        case 'arrowright':
            // Sonraki sayfa
            if (state.currentPage < state.totalPages) {
                changePage(1);
            }
            break;
            
        case '/':
            // Arama moduna gir
            e.preventDefault();
            elements.searchInput.focus();
            break;
            
        case 'r':
            // Yenile
            e.preventDefault();
            refreshGallery();
            break;
            
        case 's':
            // Slideshow toggle (slideshow.js ayrıca dinlediği için toggleSlideshow kullan)
            e.preventDefault();
            if (typeof toggleSlideshow === 'function') toggleSlideshow();
            break;
            
        case 'f':
            if (e.ctrlKey) {
                e.preventDefault();
                elements.searchInput.focus();
            } else {
                e.preventDefault();
                if (typeof window.toggleFavsFilter === 'function') window.toggleFavsFilter();
            }
            break;

        case '?':
            e.preventDefault();
            if (elements.helpModal) elements.helpModal.classList.remove('hidden');
            break;

        case 'k':
            if (e.ctrlKey) {
                e.preventDefault();
                if (typeof toggleKioskMode === 'function') toggleKioskMode();
            } else {
                e.preventDefault();
                window.scrollBy({ top: -200, behavior: 'smooth' });
            }
            break;
    }
}

function handleLightboxKeys(e) {
    switch(e.key.toLowerCase()) {
        case 'escape':
        case 'q':
            e.preventDefault();
            closeLightbox();
            break;
            
        case 'h':
        case 'arrowleft':
            e.preventDefault();
            showPrevImage();
            break;
            
        case 'l':
        case 'arrowright':
            e.preventDefault();
            showNextImage();
            break;
            
        case 'j': {
            e.preventDefault();
            // 10 resim ileri
            const newIndex = Math.min(state.currentImageIndex + 10, state.images.length - 1);
            openLightbox(newIndex);
            break;
        }
        case 'k': {
            e.preventDefault();
            // 10 resim geri
            const prevIndex = Math.max(state.currentImageIndex - 10, 0);
            openLightbox(prevIndex);
            break;
        }

        case 'i':
            e.preventDefault();
            if (typeof window.toggleExifPanel === 'function') window.toggleExifPanel();
            break;

        case '+':
        case '=':
            e.preventDefault();
            if (typeof window.zoomIn === 'function') window.zoomIn();
            break;

        case '-':
            e.preventDefault();
            if (typeof window.zoomOut === 'function') window.zoomOut();
            break;

        case 'delete':
            e.preventDefault();
            if (typeof deleteCurrentImage === 'function') deleteCurrentImage();
            break;

        case 'e':
            e.preventDefault();
            if (typeof toggleEditToolbar === 'function') toggleEditToolbar();
            break;
    }
}

let lastKeyWasG = false;
