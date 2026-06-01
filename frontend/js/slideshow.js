// ========== Slideshow Mode ==========

let slideshowInterval = null;

const slideshowBtn = document.getElementById('slideshowBtn');
slideshowBtn.addEventListener('click', toggleSlideshow);

function startSlideshow() {
    if (state.images.length === 0) {
        showToast('Önce resim yükleyin.', 'warning');
        return;
    }

    // İlk resimden başla
    if (state.currentImageIndex === -1) {
        openLightbox(0);
    }

    const speed = state.slideshowInterval || 3000;
    slideshowInterval = setInterval(() => {
        if (state.currentImageIndex < state.images.length - 1) {
            showNextImage();
        } else {
            // Son resme gelince döngüye al
            openLightbox(0);
        }
    }, speed);

    slideshowBtn.textContent = '⏸️';
    slideshowBtn.title = 'Duraklat (S)';
    state.slideshowActive = true;

    // Lightbox'ta slideshow göstergesi
    showSlideshowIndicator();
}

function stopSlideshow() {
    if (slideshowInterval) {
        clearInterval(slideshowInterval);
        slideshowInterval = null;
        slideshowBtn.textContent = '▶️';
        slideshowBtn.title = 'Slideshow (S)';
        state.slideshowActive = false;
        hideSlideshowIndicator();
    }
}

function restartSlideshow() {
    if (slideshowInterval) {
        stopSlideshow();
        startSlideshow();
    }
}

function toggleSlideshow() {
    if (slideshowInterval) {
        stopSlideshow();
    } else {
        startSlideshow();
    }
}

function showSlideshowIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'slideshowIndicator';
    indicator.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.2);
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        color: #fff;
        z-index: 1001;
    `;
    indicator.textContent = '▶️ Slideshow Aktif';
    document.body.appendChild(indicator);
}

function hideSlideshowIndicator() {
    const indicator = document.getElementById('slideshowIndicator');
    if (indicator) indicator.remove();
}

// Lightbox kapanınca slideshow'u durdur
const originalCloseLightbox = window.closeLightbox;
window.closeLightbox = function() {
    stopSlideshow();
    originalCloseLightbox();
};

// S tuşu keybinds.js tarafından yönetilir — burada tekrar dinleme
