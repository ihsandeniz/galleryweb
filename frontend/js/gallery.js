// ========== Mode & API Base URL ==========
const MODE = localStorage.getItem('galleryMode') || 'yerel';
const API_BASE = MODE === 'yerel'
    ? `${window.location.origin}/yerel/api`
    : `${window.location.origin}/api`;

// ========== Global State ==========
let state = {
    currentDirectory: null,
    currentDirectories: [],   // Faz 5.2: all active dirs
    images: [],
    currentPage: 1,
    perPage: 50,
    totalPages: 1,
    totalImages: 0,
    searchQuery: '',
    includeSubfolders: true,
    currentImageIndex: -1,
    sortBy: 'name',
    sortDir: 'asc',
    favorites: new Set(),
    activeTags: [],
    allTags: [],
    viewMode: localStorage.getItem('galleryViewMode') || 'thumbnail',
    showOnlyFavs: localStorage.getItem('galleryFavsOnly') === 'true',
    selectMode: false,
    selectedPaths: new Set(),
    activeFileTypes: [],
    videoAutoplay: localStorage.getItem('galleryAutoplay') === 'true',
    ratings: new Map(),
    bookmarks: [],
    slideshowInterval: parseInt(localStorage.getItem('slideshowInterval') || '3000'),
    kioskMode: false,
    statsOpen: false,
    albums: [],
    activeAlbum: null,
    imageMtimes: {},
    // Bulut modu
    cloudPhotos: [],
    cloudGalleries: [],
    activeGalleryId: null,
};

// ========== DOM Elements ==========
const elements = {
    selectDirBtn:      document.getElementById('selectDirBtn'),
    addDirBtn:         document.getElementById('addDirBtn'),
    clearDirBtn:       document.getElementById('clearDirBtn'),
    dirChipsRow:       document.getElementById('dirChipsRow'),
    searchInput:       document.getElementById('searchInput'),
    subFoldersCheck:   document.getElementById('subFoldersCheck'),
    sortSelect:        document.getElementById('sortSelect'),
    sortDirBtn:        document.getElementById('sortDirBtn'),
    gallery:           document.getElementById('gallery'),
    loading:           document.getElementById('loading'),
    emptyState:        document.getElementById('emptyState'),
    lightbox:          document.getElementById('lightbox'),
    lightboxImage:     document.getElementById('lightboxImage'),
    lightboxVideo:     document.getElementById('lightboxVideo'),
    closeLightbox:     document.getElementById('closeLightbox'),
    deleteLightboxBtn: document.getElementById('deleteLightboxBtn'),
    prevImage:         document.getElementById('prevImage'),
    nextImage:         document.getElementById('nextImage'),
    imageCounter:      document.getElementById('imageCounter'),
    imageName:         document.getElementById('imageName'),
    // Pagination
    pagination:        document.getElementById('pagination'),
    prevPage:          document.getElementById('prevPage'),
    nextPage:          document.getElementById('nextPage'),
    firstPage:         document.getElementById('firstPage'),
    lastPage:          document.getElementById('lastPage'),
    pageNumbers:       document.getElementById('pageNumbers'),
    pageInfo:          document.getElementById('pageInfo'),
    jumpInput:         document.getElementById('jumpInput'),
    jumpBtn:           document.getElementById('jumpBtn'),
    perPageSelect:     document.getElementById('perPageSelect'),
    // Controls
    refreshBtn:        document.getElementById('refreshBtn'),
    tagBarToggle:      document.getElementById('tagBarToggle'),
    tagBar:            document.getElementById('tagBar'),
    tagChips:          document.getElementById('tagChips'),
    clearTagsBtn:      document.getElementById('clearTagsBtn'),
    trashBtn:          document.getElementById('trashBtn'),
    trashCount:        document.getElementById('trashCount'),
    trashModal:        document.getElementById('trashModal'),
    trashList:         document.getElementById('trashList'),
    trashEmptyHint:    document.getElementById('trashEmptyHint'),
    closeTrashBtn:     document.getElementById('closeTrashBtn'),
    // Browser Modal
    browserModal:      document.getElementById('browserModal'),
    browserPath:       document.getElementById('browserPath'),
    browserList:       document.getElementById('browserList'),
    browserHistory:    document.getElementById('browserHistory'),
    closeBrowserBtn:   document.getElementById('closeBrowserBtn'),
    selectCurrentBtn:  document.getElementById('selectCurrentBtn'),
    // EXIF Panel
    closeExifBtn:      document.getElementById('closeExifBtn'),
    // View Mode
    viewModeSelect:    document.getElementById('viewModeSelect'),
    // Fav Filter
    favsFilterBtn:     document.getElementById('favsFilterBtn'),
    // Duplicates
    duplicatesBtn:     document.getElementById('duplicatesBtn'),
    duplicateModal:    document.getElementById('duplicateModal'),
    closeDuplicateBtn: document.getElementById('closeDuplicateBtn'),
    duplicateContent:  document.getElementById('duplicateContent'),
    duplicateSummary:  document.getElementById('duplicateSummary'),
    // Theme
    themeToggleBtn:    document.getElementById('themeToggleBtn'),
    // Help
    helpBtn:           document.getElementById('helpBtn'),
    helpModal:         document.getElementById('helpModal'),
    closeHelpBtn:      document.getElementById('closeHelpBtn'),
    // Select Mode
    selectModeBtn:     document.getElementById('selectModeBtn'),
    batchBar:          document.getElementById('batchBar'),
    batchCount:        document.getElementById('batchCount'),
    batchSelectAll:    document.getElementById('batchSelectAll'),
    batchFavAdd:       document.getElementById('batchFavAdd'),
    batchFavRemove:    document.getElementById('batchFavRemove'),
    batchTagBtn:       document.getElementById('batchTagBtn'),
    batchCopyBtn:      document.getElementById('batchCopyBtn'),
    batchMoveBtn:      document.getElementById('batchMoveBtn'),
    batchExportBtn:    document.getElementById('batchExportBtn'),
    batchDeleteBtn:    document.getElementById('batchDeleteBtn'),
    // Folder picker
    folderPickerModal:      document.getElementById('folderPickerModal'),
    folderPickerBackdrop:   document.getElementById('folderPickerBackdrop'),
    folderPickerTitle:      document.getElementById('folderPickerTitle'),
    closeFolderPickerBtn:   document.getElementById('closeFolderPickerBtn'),
    folderPickerCurrent:    document.getElementById('folderPickerCurrent'),
    folderPickerList:       document.getElementById('folderPickerList'),
    folderPickerSelectedPath: document.getElementById('folderPickerSelectedPath'),
    folderPickerConfirm:    document.getElementById('folderPickerConfirm'),
    batchCancel:       document.getElementById('batchCancel'),
    batchTagModal:     document.getElementById('batchTagModal'),
    batchTagInput:     document.getElementById('batchTagInput'),
    batchTagConfirm:   document.getElementById('batchTagConfirm'),
    closeBatchTagBtn:  document.getElementById('closeBatchTagBtn'),
    // File Type Filter
    fileTypeToggle:    document.getElementById('fileTypeToggle'),
    fileTypeBar:       document.getElementById('fileTypeBar'),
    clearFileTypesBtn: document.getElementById('clearFileTypesBtn'),
    autoplayToggleBtn: document.getElementById('autoplayToggleBtn'),
    // Faz 1 — New features
    statsBtn:              document.getElementById('statsBtn'),
    statsPanel:            document.getElementById('statsPanel'),
    statsContent:          document.getElementById('statsContent'),
    closeStatsBtn:         document.getElementById('closeStatsBtn'),
    statsBackdrop:         document.getElementById('statsBackdrop'),
    kioskBtn:              document.getElementById('kioskBtn'),
    bookmarkAddBtn:        document.getElementById('bookmarkAddBtn'),
    bookmarkDropdown:      document.getElementById('bookmarkDropdown'),
    ratingPicker:          document.getElementById('ratingPicker'),
    clearRatingBtn:        document.getElementById('clearRatingBtn'),
    slideshowIntervalBtn:  document.getElementById('slideshowIntervalBtn'),
    slideshowIntervalPopover: document.getElementById('slideshowIntervalPopover'),
    // Faz 3.1 — Albums
    albumsBtn:          document.getElementById('albumsBtn'),
    albumsPanel:        document.getElementById('albumsPanel'),
    albumsBackdrop:     document.getElementById('albumsBackdrop'),
    closeAlbumsBtn:     document.getElementById('closeAlbumsBtn'),
    albumsList:         document.getElementById('albumsList'),
    createAlbumBtn:     document.getElementById('createAlbumBtn'),
    albumModal:         document.getElementById('albumModal'),
    albumModalBackdrop: document.getElementById('albumModalBackdrop'),
    albumModalTitle:    document.getElementById('albumModalTitle'),
    closeAlbumModalBtn: document.getElementById('closeAlbumModalBtn'),
    albumNameInput:     document.getElementById('albumNameInput'),
    albumDescInput:     document.getElementById('albumDescInput'),
    albumModalConfirm:  document.getElementById('albumModalConfirm'),
    batchAddToAlbumBtn: document.getElementById('batchAddToAlbumBtn'),
    // Faz 2 — QR
    qrBtn:       document.getElementById('qrBtn'),
    qrModal:     document.getElementById('qrModal'),
    qrImage:     document.getElementById('qrImage'),
    qrUrlText:   document.getElementById('qrUrlText'),
    closeQrBtn:  document.getElementById('closeQrBtn'),
    qrBackdrop:  document.getElementById('qrBackdrop'),
    copyQrUrlBtn: document.getElementById('copyQrUrlBtn'),
    // Faz 3.3 — Compare
    batchCompareBtn:    document.getElementById('batchCompareBtn'),
    compareModal:       document.getElementById('compareModal'),
    compareBackdrop:    document.getElementById('compareBackdrop'),
    closeCompareBtn:    document.getElementById('closeCompareBtn'),
    compareImgLeft:     document.getElementById('compareImgLeft'),
    compareImgRight:    document.getElementById('compareImgRight'),
    compareLabelLeft:   document.getElementById('compareLabelLeft'),
    compareLabelRight:  document.getElementById('compareLabelRight'),
    compareResetBtn:    document.getElementById('compareResetBtn'),
    compareSyncZoomBtn: document.getElementById('compareSyncZoomBtn'),
    // Faz 4.2 — Map
    mapBtn:         document.getElementById('mapBtn'),
    mapModal:       document.getElementById('mapModal'),
    mapBackdrop:    document.getElementById('mapBackdrop'),
    closeMapBtn:    document.getElementById('closeMapBtn'),
    mapImageCount:  document.getElementById('mapImageCount'),
    // Faz 5.3 — Batch EXIF
    batchExifBtn:      document.getElementById('batchExifBtn'),
    batchExifModal:    document.getElementById('batchExifModal'),
    batchExifBackdrop: document.getElementById('batchExifBackdrop'),
    closeBatchExifBtn: document.getElementById('closeBatchExifBtn'),
    batchExifConfirm:  document.getElementById('batchExifConfirm'),
    // Faz 5.4 — Watermark/Export Modal
    watermarkModal:          document.getElementById('watermarkModal'),
    watermarkBackdrop:       document.getElementById('watermarkBackdrop'),
    closeWatermarkModalBtn:  document.getElementById('closeWatermarkModalBtn'),
    wmEnable:                document.getElementById('wmEnable'),
    wmOptions:               document.getElementById('wmOptions'),
    wmText:                  document.getElementById('wmText'),
    wmPosition:              document.getElementById('wmPosition'),
    wmOpacity:               document.getElementById('wmOpacity'),
    wmOpacityVal:            document.getElementById('wmOpacityVal'),
    wmSize:                  document.getElementById('wmSize'),
    wmSizeVal:               document.getElementById('wmSizeVal'),
    wmExportBtn:             document.getElementById('wmExportBtn'),
    wmExportStatus:          document.getElementById('wmExportStatus')
};

// ========== Toast ==========
function showToast(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
}

function showUndoToast(message, trashId) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast warning toast-undo';
    toast.innerHTML = `<span>${message}</span><button class="undo-btn">Geri Al</button>`;
    container.appendChild(toast);

    toast.querySelector('.undo-btn').addEventListener('click', async () => {
        try {
            const res = await fetch(`${API_BASE}/restore/${trashId}`, { method: 'POST' });
            if (res.ok) {
                const d = await res.json();
                toast.remove();
                showToast(`"${d.filename}" geri alındı`, 'success');
                refreshGallery();
                updateTrashCount();
            } else {
                showToast('Geri alma başarısız', 'error');
            }
        } catch { showToast('Bağlantı hatası', 'error'); }
    });

    setTimeout(() => toast.remove(), 8000);
}

// ========== Initialize ==========
async function init() {
    elements.selectDirBtn.addEventListener('click', openBrowserModal);
    if (elements.addDirBtn) elements.addDirBtn.addEventListener('click', openAddDirModal);
    elements.clearDirBtn.addEventListener('click', clearDirectory);
    elements.searchInput.addEventListener('input', debounce(handleSearch, 300));
    elements.subFoldersCheck.checked = state.includeSubfolders;
    elements.subFoldersCheck.addEventListener('change', handleSubfoldersToggle);
    elements.closeLightbox.addEventListener('click', closeLightbox);
    elements.prevImage.addEventListener('click', showPrevImage);
    elements.nextImage.addEventListener('click', showNextImage);
    elements.refreshBtn.addEventListener('click', refreshGallery);

    // Sort
    elements.sortSelect.addEventListener('change', e => {
        state.sortBy = e.target.value;
        state.currentPage = 1;
        loadImages();
    });
    elements.sortDirBtn.addEventListener('click', () => {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        elements.sortDirBtn.textContent = state.sortDir === 'asc' ? '↑' : '↓';
        state.currentPage = 1;
        loadImages();
    });

    // Pagination
    elements.firstPage.addEventListener('click', () => goToPage(1));
    elements.lastPage.addEventListener('click', () => goToPage(state.totalPages));
    elements.prevPage.addEventListener('click', () => changePage(-1));
    elements.nextPage.addEventListener('click', () => changePage(1));
    elements.jumpBtn.addEventListener('click', handleJump);
    elements.jumpInput.addEventListener('keydown', e => { if (e.key === 'Enter') handleJump(); });
    elements.perPageSelect.addEventListener('change', e => {
        state.perPage = parseInt(e.target.value);
        state.currentPage = 1;
        loadImages();
    });

    // Tag bar
    elements.tagBarToggle.addEventListener('click', toggleTagBar);
    elements.clearTagsBtn.addEventListener('click', clearTagFilter);

    // File type filter bar
    elements.fileTypeToggle.addEventListener('click', toggleFileTypeBar);
    elements.clearFileTypesBtn.addEventListener('click', clearFileTypeFilter);
    // Event delegation on the entire bar (chips are in two groups now)
    elements.fileTypeBar.addEventListener('click', e => {
        const chip = e.target.closest('.ft-chip');
        if (!chip) return;
        const exts = chip.dataset.ext.split(',');
        chip.classList.toggle('active');
        if (chip.classList.contains('active')) {
            exts.forEach(ext => { if (!state.activeFileTypes.includes(ext)) state.activeFileTypes.push(ext); });
        } else {
            state.activeFileTypes = state.activeFileTypes.filter(ext => !exts.includes(ext));
        }
        elements.clearFileTypesBtn.classList.toggle('hidden', state.activeFileTypes.length === 0);
        state.currentPage = 1;
        loadImages();
    });

    // Delete
    elements.deleteLightboxBtn.addEventListener('click', deleteCurrentImage);

    // Trash modal
    elements.trashBtn.addEventListener('click', openTrashModal);
    elements.closeTrashBtn.addEventListener('click', closeTrashModal);
    elements.trashModal.querySelector('.modal-backdrop').addEventListener('click', closeTrashModal);

    // Lightbox dışına tıkla
    elements.lightbox.addEventListener('click', e => {
        if (e.target === elements.lightbox) closeLightbox();
    });

    // Browser Modal
    elements.closeBrowserBtn.addEventListener('click', closeBrowserModal);
    elements.browserModal.querySelector('.modal-backdrop').addEventListener('click', closeBrowserModal);
    elements.selectCurrentBtn.addEventListener('click', selectCurrentBrowsedDir);

    // View mode
    elements.viewModeSelect.value = state.viewMode;
    elements.viewModeSelect.addEventListener('change', e => {
        state.viewMode = e.target.value;
        localStorage.setItem('galleryViewMode', state.viewMode);
        renderGallery();
    });

    // Fav filter
    applyFavsFilterUI();
    elements.favsFilterBtn.addEventListener('click', toggleFavsFilter);

    // Theme
    applyTheme(localStorage.getItem('galleryTheme') || 'dark');
    elements.themeToggleBtn.addEventListener('click', () => {
        const next = document.body.classList.contains('light') ? 'dark' : 'light';
        applyTheme(next);
        localStorage.setItem('galleryTheme', next);
    });

    // Help modal
    elements.helpBtn.addEventListener('click', () => elements.helpModal.classList.remove('hidden'));
    elements.closeHelpBtn.addEventListener('click', () => elements.helpModal.classList.add('hidden'));
    elements.helpModal.querySelector('.modal-backdrop').addEventListener('click', () => elements.helpModal.classList.add('hidden'));

    // Duplicates modal
    elements.duplicatesBtn.addEventListener('click', openDuplicateModal);
    elements.closeDuplicateBtn.addEventListener('click', () => elements.duplicateModal.classList.add('hidden'));
    elements.duplicateModal.querySelector('.modal-backdrop').addEventListener('click', () => elements.duplicateModal.classList.add('hidden'));

    // Select mode
    elements.selectModeBtn.addEventListener('click', toggleSelectMode);
    elements.batchCancel.addEventListener('click', exitSelectMode);
    elements.batchSelectAll.addEventListener('click', selectAllCurrentPage);
    elements.batchExportBtn.addEventListener('click', openWatermarkModal);
    elements.batchDeleteBtn.addEventListener('click', batchDelete);
    elements.batchFavAdd.addEventListener('click', () => batchFavorite('add'));
    elements.batchFavRemove.addEventListener('click', () => batchFavorite('remove'));
    elements.batchCopyBtn.addEventListener('click', () => openFolderPicker('copy'));
    elements.batchMoveBtn.addEventListener('click', () => openFolderPicker('move'));
    elements.closeFolderPickerBtn.addEventListener('click', closeFolderPicker);
    elements.folderPickerBackdrop.addEventListener('click', closeFolderPicker);
    elements.folderPickerConfirm.addEventListener('click', executeFolderPickerAction);
    elements.batchTagBtn.addEventListener('click', () => elements.batchTagModal.classList.remove('hidden'));
    elements.closeBatchTagBtn.addEventListener('click', () => elements.batchTagModal.classList.add('hidden'));
    elements.batchTagModal.querySelector('.modal-backdrop').addEventListener('click', () => elements.batchTagModal.classList.add('hidden'));
    elements.batchTagConfirm.addEventListener('click', batchTag);
    elements.batchTagInput.addEventListener('keydown', e => { if (e.key === 'Enter') batchTag(); });

    // EXIF Panel
    elements.closeExifBtn.addEventListener('click', toggleExifPanel);

    // Rating picker
    elements.ratingPicker.querySelectorAll('.star').forEach(star => {
        star.addEventListener('click', () => setRating(parseInt(star.dataset.star)));
        star.addEventListener('mouseenter', () => previewRating(parseInt(star.dataset.star)));
        star.addEventListener('mouseleave', () => renderRatingStars());
    });
    elements.clearRatingBtn.addEventListener('click', clearRating);

    // Stats panel
    elements.statsBtn.addEventListener('click', toggleStatsPanel);
    elements.closeStatsBtn.addEventListener('click', closeStatsPanel);
    elements.statsBackdrop.addEventListener('click', closeStatsPanel);

    // Albums panel
    elements.albumsBtn.addEventListener('click', toggleAlbumsPanel);
    elements.closeAlbumsBtn.addEventListener('click', closeAlbumsPanel);
    elements.albumsBackdrop.addEventListener('click', closeAlbumsPanel);
    elements.createAlbumBtn.addEventListener('click', () => openAlbumModal());
    elements.closeAlbumModalBtn.addEventListener('click', closeAlbumModal);
    elements.albumModalBackdrop.addEventListener('click', closeAlbumModal);
    elements.albumModalConfirm.addEventListener('click', confirmAlbumModal);
    elements.albumNameInput.addEventListener('keydown', e => { if (e.key === 'Enter') confirmAlbumModal(); });
    elements.batchAddToAlbumBtn.addEventListener('click', openAddToAlbumPicker);

    // QR modal
    elements.qrBtn.addEventListener('click', showQRModal);
    elements.closeQrBtn.addEventListener('click', closeQRModal);
    elements.qrBackdrop.addEventListener('click', closeQRModal);
    elements.copyQrUrlBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(elements.qrUrlText.textContent)
            .then(() => showToast('URL kopyalandı!', 'success'))
            .catch(() => showToast('Kopyalama başarısız', 'error'));
    });

    // Compare modal
    elements.batchCompareBtn.addEventListener('click', openCompareMode);
    elements.closeCompareBtn.addEventListener('click', closeCompareMode);
    elements.compareBackdrop.addEventListener('click', closeCompareMode);
    elements.compareResetBtn.addEventListener('click', resetCompare);
    elements.compareSyncZoomBtn.addEventListener('click', () => {
        compareState.syncZoom = !compareState.syncZoom;
        elements.compareSyncZoomBtn.classList.toggle('active', compareState.syncZoom);
    });

    // Map modal
    elements.mapBtn.addEventListener('click', openMapView);
    elements.closeMapBtn.addEventListener('click', closeMapView);
    elements.mapBackdrop.addEventListener('click', closeMapView);

    // Kiosk mode
    elements.kioskBtn.addEventListener('click', toggleKioskMode);
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            state.kioskMode = false;
            document.body.classList.remove('kiosk');
        }
    });

    // Bookmarks
    elements.bookmarkAddBtn.addEventListener('click', e => {
        e.stopPropagation();
        toggleBookmarkDropdown();
    });
    document.addEventListener('click', e => {
        if (!e.target.closest('.bookmark-wrapper')) {
            elements.bookmarkDropdown.classList.add('hidden');
        }
    });

    // Slideshow interval popover
    elements.slideshowIntervalBtn.addEventListener('click', e => {
        e.stopPropagation();
        elements.slideshowIntervalPopover.classList.toggle('hidden');
        updateIntervalUI();
    });
    elements.slideshowIntervalPopover.querySelectorAll('.interval-opt').forEach(btn => {
        btn.addEventListener('click', () => {
            setSlideshowInterval(parseInt(btn.dataset.ms));
            elements.slideshowIntervalPopover.classList.add('hidden');
        });
    });
    document.addEventListener('click', e => {
        if (!e.target.closest('.slideshow-wrapper')) {
            elements.slideshowIntervalPopover.classList.add('hidden');
        }
    });

    // Video autoplay — guard against rapid-fire ended events
    // (flags declared at module level: _autoplayAdvancing, _videoActive)
    elements.lightboxVideo.addEventListener('ended', async () => {
        if (state.videoAutoplay && !_autoplayAdvancing && _videoActive) {
            _autoplayAdvancing = true;
            await showNextImage();
            _autoplayAdvancing = false;
        }
    });
    // Hatalı/yüklenemeyen videolarda sonrakine geç — SADECE _videoActive=true iken
    elements.lightboxVideo.addEventListener('error', async () => {
        if (state.videoAutoplay && !_autoplayAdvancing && _videoActive) {
            _autoplayAdvancing = true;
            showToast('Video yüklenemedi, sonrakine geçiliyor', 'warning');
            await showNextImage();
            _autoplayAdvancing = false;
        }
    });
    elements.autoplayToggleBtn.addEventListener('click', () => {
        state.videoAutoplay = !state.videoAutoplay;
        localStorage.setItem('galleryAutoplay', state.videoAutoplay);
        elements.autoplayToggleBtn.classList.toggle('active', state.videoAutoplay);
        const isVideo = /\.(mp4|webm|mov)$/i.test(state.images[state.currentImageIndex] || '');
        if (isVideo && state.videoAutoplay) {
            elements.lightboxVideo.play().catch(() => {});
        }
    });

    // Lightbox zoom
    elements.lightboxImage.addEventListener('wheel', handleLightboxZoom, { passive: false });
    elements.lightboxImage.addEventListener('touchstart', handlePinchStart, { passive: true });
    elements.lightboxImage.addEventListener('touchmove', handlePinchMove, { passive: false });

    // Lightbox swipe — telefon navigasyonu
    let _swipeStartX = 0, _swipeStartY = 0;
    elements.lightbox.addEventListener('touchstart', e => {
        if (e.touches.length === 1) {
            _swipeStartX = e.touches[0].clientX;
            _swipeStartY = e.touches[0].clientY;
        }
    }, { passive: true });
    elements.lightbox.addEventListener('touchend', e => {
        if (e.changedTouches.length !== 1 || zoomLevel > 1) return;
        const dx = e.changedTouches[0].clientX - _swipeStartX;
        const dy = e.changedTouches[0].clientY - _swipeStartY;
        if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy)) {
            if (dx < 0) showNextImage();
            else showPrevImage();
        }
    }, { passive: true });

    // Faz 5.3 — Batch EXIF
    elements.batchExifBtn.addEventListener('click', openBatchExifModal);
    elements.closeBatchExifBtn.addEventListener('click', closeBatchExifModal);
    elements.batchExifBackdrop.addEventListener('click', closeBatchExifModal);
    elements.batchExifConfirm.addEventListener('click', executeBatchExif);

    // Faz 5.4 — Watermark/Export Modal
    elements.closeWatermarkModalBtn.addEventListener('click', closeWatermarkModal);
    elements.watermarkBackdrop.addEventListener('click', closeWatermarkModal);
    elements.wmEnable.addEventListener('change', () => {
        elements.wmOptions.classList.toggle('hidden', !elements.wmEnable.checked);
    });
    elements.wmOpacity.addEventListener('input', () => {
        elements.wmOpacityVal.textContent = elements.wmOpacity.value + '%';
    });
    elements.wmSize.addEventListener('input', () => {
        elements.wmSizeVal.textContent = elements.wmSize.value + '%';
    });
    elements.wmExportBtn.addEventListener('click', executeWatermarkExport);

    // Faz 5.1 + Faz 9 — Edit mode (foto stüdyosu)
    document.getElementById('editModeBtn').addEventListener('click', toggleEditToolbar);
    document.getElementById('closeEditToolbarBtn').addEventListener('click', closeEditToolbar);
    document.getElementById('editRotateCCW').addEventListener('click', () => applyEdit('rotate', { degrees: -90 }));
    document.getElementById('editRotateCW').addEventListener('click', () => applyEdit('rotate', { degrees: 90 }));
    document.getElementById('editRotate180').addEventListener('click', () => applyEdit('rotate', { degrees: 180 }));
    document.getElementById('editFlipH').addEventListener('click', () => applyEdit('flip', { direction: 'horizontal' }));
    document.getElementById('editFlipV').addEventListener('click', () => applyEdit('flip', { direction: 'vertical' }));
    document.getElementById('editCropBtn').addEventListener('click', startCropMode);
    document.getElementById('editAdjustBtn').addEventListener('click', openAdjustPanel);
    document.getElementById('editFilterBtn').addEventListener('click', openFilterPanel);
    document.getElementById('editRevertBtn').addEventListener('click', revertEdit);
    document.getElementById('adjustApplyBtn').addEventListener('click', applyAdjust);
    document.getElementById('adjustResetBtn').addEventListener('click', resetAdjustSliders);
    document.getElementById('adjustCancelBtn').addEventListener('click', closeAdjustPanel);
    document.getElementById('filterCancelBtn').addEventListener('click', closeFilterPanel);
    document.querySelectorAll('.filter-preset').forEach(btn => {
        btn.addEventListener('click', () => applyFilterPreset(btn.dataset.preset));
    });

    // Faz 9 — Video edit (trim)
    document.getElementById('closeVideoEditBtn').addEventListener('click', closeVideoEditToolbar);
    document.getElementById('videoTrimBtn').addEventListener('click', openTrimPanel);
    document.getElementById('videoRevertBtn').addEventListener('click', revertVideoEdit);
    document.getElementById('trimApplyBtn').addEventListener('click', applyTrim);
    document.getElementById('trimCancelBtn').addEventListener('click', () => {
        document.getElementById('trimPanel').classList.add('hidden');
    });

    elements.emptyState.classList.remove('hidden');

    // Mode switch button
    const modeSwitchBtn = document.getElementById('modeSwitchBtn');
    if (modeSwitchBtn) {
        modeSwitchBtn.textContent = MODE === 'bulut' ? '☁' : '📂';
        modeSwitchBtn.title = MODE === 'bulut' ? 'Yerel moda geç' : 'Bulut moduna geç';
        modeSwitchBtn.addEventListener('click', () => {
            const next = MODE === 'yerel' ? 'bulut' : 'yerel';
            localStorage.setItem('galleryMode', next);
            window.location.reload();
        });
    }

    if (MODE === 'bulut') {
        // Bulut modu: galeri listesini yükle
        const cloudSection = document.getElementById('cloudSection');
        const yerelSection = document.getElementById('yerelSection');
        if (cloudSection) cloudSection.style.display = '';
        if (yerelSection) yerelSection.style.display = 'none';

        const cloudGallerySelect = document.getElementById('cloudGallerySelect');
        const cloudUploadBtn = document.getElementById('cloudUploadBtn');
        const cloudFileInput = document.getElementById('cloudFileInput');

        if (cloudGallerySelect) {
            cloudGallerySelect.addEventListener('change', () => {
                state.activeGalleryId = cloudGallerySelect.value || null;
                if (state.activeGalleryId) loadCloudPhotos();
                else { state.cloudPhotos = []; elements.gallery.innerHTML = ''; elements.emptyState.classList.remove('hidden'); }
            });
        }
        if (cloudUploadBtn && cloudFileInput) {
            cloudUploadBtn.addEventListener('click', () => cloudFileInput.click());
            cloudFileInput.addEventListener('change', () => {
                if (cloudFileInput.files.length > 0) uploadCloudFiles(cloudFileInput.files);
            });
        }

        loadCloudGalleries();
    } else {
        // Yerel modu
        const cloudSection = document.getElementById('cloudSection');
        const yerelSection = document.getElementById('yerelSection');
        if (cloudSection) cloudSection.style.display = 'none';
        if (yerelSection) yerelSection.style.display = '';

        const savedPath = localStorage.getItem('galleryPath');
        if (savedPath) {
            autoConnectDirectory(savedPath);
        } else {
            fetch(`${API_BASE}/current-directory`)
                .then(r => r.json())
                .then(d => {
                    if (d.directories && d.directories.length > 0) {
                        state.currentDirectories = d.directories;
                        state.currentDirectory = d.path;
                        renderDirChips();
                        elements.emptyState.classList.add('hidden');
                        loadFavorites().then(() => loadRatings()).then(() => loadBookmarks()).then(() => loadImages());
                        startWatcher();
                        updateTrashCount();
                        updateBookmarkBtnState();
                    } else if (d.path) {
                        autoConnectDirectory(d.path);
                    }
                })
                .catch(() => {});
        }
    }
}

// ========== Clear Directory ==========
function clearDirectory() {
    stopWatcher();
    state.currentDirectory = null;
    state.currentDirectories = [];
    state.images = [];
    state.currentPage = 1;
    state.totalPages = 1;
    state.favorites = new Set();
    state.activeTags = [];
    renderDirChips();
    elements.gallery.innerHTML = '';
    elements.emptyState.classList.remove('hidden');
    elements.emptyState.innerHTML = '<p>📁 Klasör seçmek için yukarıdaki butona tıklayın</p>';
    localStorage.removeItem('galleryPath');
    fetch(`${API_BASE}/clear-directory`, { method: 'POST' }).catch(() => {});
    updatePagination();
}

// ========== Multi-Directory Chips ==========
function renderDirChips() {
    if (!elements.dirChipsRow) return;
    elements.dirChipsRow.innerHTML = '';
    state.currentDirectories.forEach(dirPath => {
        const chip = document.createElement('div');
        chip.className = 'dir-chip';
        const label = dirPath.split('/').pop() || dirPath;
        chip.innerHTML = `<span class="dir-chip-label" title="${dirPath}">📁 ${label}</span>` +
                         `<span class="dir-chip-remove" title="Kaldır">✕</span>`;
        chip.querySelector('.dir-chip-remove').addEventListener('click', (e) => {
            e.stopPropagation();
            removeDirectory(dirPath);
        });
        elements.dirChipsRow.appendChild(chip);
    });
}

async function addDirectory(path) {
    try {
        const res = await fetch(`${API_BASE}/add-directory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        if (!res.ok) { showToast('Klasör eklenemedi', 'error'); return; }
        const data = await res.json();
        if (!state.currentDirectories.includes(data.path)) {
            state.currentDirectories.push(data.path);
        }
        if (!state.currentDirectory) state.currentDirectory = data.path;
        renderDirChips();
        state.currentPage = 1;
        await loadFavorites();
        await loadRatings();
        await loadImages();
        startWatcher();
        updateBookmarkBtnState();
        showToast(`Eklendi: ${data.path.split('/').pop()}`, 'success');
    } catch { showToast('Bağlantı hatası', 'error'); }
}

async function removeDirectory(path) {
    try {
        const res = await fetch(`${API_BASE}/directory?path=${encodeURIComponent(path)}`, {
            method: 'DELETE'
        });
        if (!res.ok) return;
        state.currentDirectories = state.currentDirectories.filter(d => d !== path);
        if (state.currentDirectory === path) {
            state.currentDirectory = state.currentDirectories[0] || null;
        }
        renderDirChips();
        state.currentPage = 1;
        if (state.currentDirectories.length === 0) {
            clearDirectory();
        } else {
            await loadImages();
        }
    } catch { showToast('Bağlantı hatası', 'error'); }
}

// ========== Auto Connect ==========
async function autoConnectDirectory(path) {
    try {
        const res = await fetch(`${API_BASE}/set-directory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        if (!res.ok) { localStorage.removeItem('galleryPath'); return; }
        const data = await res.json();
        if (data.status === 'fallback') {
            localStorage.removeItem('galleryPath');
            showToast(`'${path}' taşınmış veya silinmiş — ana dizine geçildi`, 'warning');
        }
        state.currentDirectory = data.path;
        state.currentDirectories = [data.path];
        renderDirChips();
        elements.emptyState.classList.add('hidden');
        await loadFavorites();
        await loadRatings();
        await loadBookmarks();
        await loadImages();
        generateThumbnails();
        startWatcher();
        updateTrashCount();
        updateBookmarkBtnState();
    } catch { localStorage.removeItem('galleryPath'); }
}

// ========== Browser Modal ==========
let currentBrowsePath = '/';
let _browserMode = 'set'; // 'set' | 'add'

async function _resolveStartPath() {
    const saved = state.currentDirectory || localStorage.getItem('galleryPath');
    if (!saved) return '/home';
    // Saved path'in hâlâ geçerli olup olmadığını backend'den doğrula
    try {
        const check = await fetch(`${API_BASE}/browse?path=${encodeURIComponent(saved)}`);
        if (check.ok) return saved;
    } catch { /* ignore */ }
    // Geçersiz → temizle ve home'a dön
    localStorage.removeItem('galleryPath');
    localStorage.removeItem('galleryHistory');
    state.currentDirectory = null;
    state.currentDirectories = [];
    return '/home';
}

async function openBrowserModal() {
    _browserMode = 'set';
    const startPath = await _resolveStartPath();
    currentBrowsePath = startPath;
    elements.browserModal.classList.remove('hidden');
    renderHistory();
    await navigateBrowser(startPath);
}

async function openAddDirModal() {
    _browserMode = 'add';
    const startPath = await _resolveStartPath();
    currentBrowsePath = startPath;
    elements.browserModal.classList.remove('hidden');
    renderHistory();
    await navigateBrowser(startPath);
}

function closeBrowserModal() { elements.browserModal.classList.add('hidden'); }

async function navigateBrowser(path) {
    try {
        let res = await fetch(`${API_BASE}/browse?path=${encodeURIComponent(path)}`);
        // Geçersiz path → home'a düş
        if (!res.ok) {
            res = await fetch(`${API_BASE}/browse?path=${encodeURIComponent('/home')}`);
            if (!res.ok) { showToast('Klasör açılamadı', 'error'); return; }
        }
        const data = await res.json();
        currentBrowsePath = data.current;
        elements.browserPath.textContent = data.current;
        elements.browserList.innerHTML = '';

        if (data.parent) {
            const li = document.createElement('li');
            li.className = 'parent-item';
            li.innerHTML = '<span>📁</span> ..';
            li.addEventListener('click', () => navigateBrowser(data.parent));
            elements.browserList.appendChild(li);
        }

        data.entries.filter(e => e.is_dir).forEach(entry => {
            const li = document.createElement('li');
            li.innerHTML = `<span class="dir-icon">📁</span> ${entry.name}`;
            li.addEventListener('click', () => navigateBrowser(entry.path));
            elements.browserList.appendChild(li);
        });
    } catch { showToast('Bağlantı hatası', 'error'); }
}

async function selectCurrentBrowsedDir() {
    if (_browserMode === 'add') {
        closeBrowserModal();
        await addDirectory(currentBrowsePath);
        return;
    }
    try {
        const res = await fetch(`${API_BASE}/set-directory`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentBrowsePath })
        });
        if (!res.ok) { showToast('Klasör ayarlanamadı', 'error'); return; }
        const data = await res.json();
        state.currentDirectory = data.path;
        state.currentDirectories = [data.path];
        renderDirChips();
        localStorage.setItem('galleryPath', data.path);
        addToHistory(data.path);
        closeBrowserModal();
        state.currentPage = 1;
        state.favorites = new Set();
        state.activeTags = [];
        await loadFavorites();
        await loadRatings();
        await loadBookmarks();
        await loadImages();
        generateThumbnails();
        startWatcher();
        updateTrashCount();
        updateBookmarkBtnState();
        if (!elements.tagBar.classList.contains('hidden')) loadAllTags();
    } catch { showToast('Hata oluştu', 'error'); }
}

function renderHistory() {
    const history = getHistory();
    if (!history.length) { elements.browserHistory.classList.add('hidden'); return; }
    elements.browserHistory.classList.remove('hidden');
    elements.browserHistory.innerHTML = '<span>Son:</span>' +
        history.map(p => `<button class="history-item" data-path="${p}">${p.split('/').pop() || p}</button>`).join('');
    elements.browserHistory.querySelectorAll('.history-item').forEach(el =>
        el.addEventListener('click', () => navigateBrowser(el.dataset.path))
    );
}

function addToHistory(path) {
    let h = JSON.parse(localStorage.getItem('galleryHistory') || '[]');
    h = [path, ...h.filter(p => p !== path)].slice(0, 5);
    localStorage.setItem('galleryHistory', JSON.stringify(h));
}

function getHistory() {
    return JSON.parse(localStorage.getItem('galleryHistory') || '[]');
}

// ========== Load Images ==========
async function loadImages() {
    if (MODE === 'bulut') { await loadCloudPhotos(); return; }
    if (!state.currentDirectory) return;
    try {
        showLoading();
        elements.emptyState.classList.add('hidden');

        const params = new URLSearchParams({
            page: state.currentPage,
            per_page: state.perPage,
            search: state.searchQuery,
            include_subfolders: state.includeSubfolders,
            sort_by: state.sortBy,
            sort_dir: state.sortDir,
            favorites_only: state.showOnlyFavs
        });
        if (state.activeTags.length) params.set('tags', state.activeTags.join(','));
        if (state.activeFileTypes.length) params.set('file_types', state.activeFileTypes.join(','));
        if (state.activeAlbum) params.set('album_id', state.activeAlbum);

        const res = await fetch(`${API_BASE}/images?${params}`);
        if (!res.ok) throw new Error('Resimler yüklenemedi');

        const data = await res.json();
        state.images = data.images;
        state.imageMtimes = data.mtimes || {};
        state.totalPages = data.total_pages;
        state.totalImages = data.total;

        renderGallery();
        updatePagination();
    } catch (err) {
        console.error(err);
        showToast('Resimler yüklenirken hata oluştu', 'error');
    } finally {
        hideLoading();
    }
}

// ========== BULUT MODU FONKSİYONLARI ==========

function getCloudThumbUrl(photoId, size) {
    const token = window.GW && window.GW.getToken ? window.GW.getToken() : '';
    return `${window.location.origin}/api/photos/${photoId}/thumb?size=${size}&token=${encodeURIComponent(token)}`;
}

async function loadCloudGalleries() {
    if (!window.GW || !window.GW.isTokenValid()) {
        window.location.href = '/login';
        return;
    }
    try {
        const res = await fetch(`${window.location.origin}/api/galleries`, {
            headers: window.GW.authHeaders(),
        });
        if (!res.ok) { if (res.status === 401) { window.location.href = '/login'; } return; }
        const data = await res.json();
        state.cloudGalleries = data;
        const sel = document.getElementById('cloudGallerySelect');
        if (!sel) return;
        sel.innerHTML = '<option value="">Galeri seçin...</option>';
        data.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = g.name;
            sel.appendChild(opt);
        });
        if (data.length > 0) {
            sel.value = data[0].id;
            state.activeGalleryId = data[0].id;
            loadCloudPhotos();
        } else {
            elements.emptyState.classList.remove('hidden');
            elements.emptyState.innerHTML = '<p>☁ Henüz galeri yok. Önce bir galeri oluşturun.</p>';
        }
    } catch (err) {
        console.error(err);
        showToast('Galeriler yüklenemedi', 'error');
    }
}

async function loadCloudPhotos() {
    if (!state.activeGalleryId) return;
    if (!window.GW || !window.GW.isTokenValid()) { window.location.href = '/login'; return; }
    try {
        showLoading();
        elements.emptyState.classList.add('hidden');
        const res = await fetch(`${window.location.origin}/api/photos?gallery_id=${state.activeGalleryId}`, {
            headers: window.GW.authHeaders(),
        });
        if (!res.ok) throw new Error('Fotoğraflar yüklenemedi');
        const data = await res.json();
        state.cloudPhotos = Array.isArray(data) ? data : (data.photos || []);
        renderCloudGallery();
    } catch (err) {
        console.error(err);
        showToast('Fotoğraflar yüklenirken hata oluştu', 'error');
    } finally {
        hideLoading();
    }
}

function buildCloudItem(photo, index) {
    const item = document.createElement('div');
    item.className = 'gallery-item';
    item.dataset.index = index;
    const img = document.createElement('img');
    img.src = getCloudThumbUrl(photo.id, 'md');
    img.alt = photo.filename || '';
    img.loading = 'lazy';
    img.onerror = () => { img.src = ''; img.style.background = '#333'; };
    item.appendChild(img);
    const label = document.createElement('div');
    label.className = 'item-label';
    label.textContent = photo.filename || '';
    item.appendChild(label);
    item.addEventListener('click', () => openCloudLightbox(index));
    return item;
}

function renderCloudGallery() {
    elements.gallery.innerHTML = '';
    if (!state.cloudPhotos.length) {
        elements.emptyState.classList.remove('hidden');
        elements.emptyState.innerHTML = '<p>☁ Bu galeride henüz fotoğraf yok.</p>';
        return;
    }
    elements.emptyState.classList.add('hidden');
    const frag = document.createDocumentFragment();
    state.cloudPhotos.forEach((photo, i) => frag.appendChild(buildCloudItem(photo, i)));
    elements.gallery.appendChild(frag);
}

function openCloudLightbox(index) {
    const photo = state.cloudPhotos[index];
    if (!photo) return;
    state.currentImageIndex = index;
    const isVideo = /\.(mp4|webm|mov)$/i.test(photo.filename || '');
    resetZoom();
    if (isVideo) {
        _videoActive = true;
        elements.lightboxImage.classList.add('hidden');
        elements.lightboxVideo.classList.remove('hidden');
        const token = window.GW && window.GW.getToken ? window.GW.getToken() : '';
        elements.lightboxVideo.src = `${window.location.origin}/api/photos/${photo.id}/file?token=${encodeURIComponent(token)}`;
        if (state.videoAutoplay) elements.lightboxVideo.play().catch(() => {});
    } else {
        _videoActive = false;
        elements.lightboxVideo.pause();
        elements.lightboxVideo.removeAttribute('src');
        elements.lightboxVideo.load();
        elements.lightboxImage.classList.remove('hidden');
        elements.lightboxVideo.classList.add('hidden');
        elements.lightboxImage.src = getCloudThumbUrl(photo.id, 'lg');
    }
    elements.autoplayToggleBtn.classList.toggle('active', state.videoAutoplay);
    elements.imageName.textContent = photo.filename || '';
    elements.imageCounter.textContent = `${index + 1} / ${state.cloudPhotos.length}`;
    elements.lightbox.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

async function uploadCloudFiles(files) {
    if (!state.activeGalleryId) { showToast('Önce bir galeri seçin', 'warning'); return; }
    if (!window.GW || !window.GW.isTokenValid()) { window.location.href = '/login'; return; }
    const total = files.length;
    let done = 0;
    showToast(`${total} fotoğraf yükleniyor...`, 'info');
    for (const file of files) {
        try {
            const form = new FormData();
            form.append('file', file);
            form.append('gallery_id', state.activeGalleryId);
            const res = await fetch(`${window.location.origin}/api/photos`, {
                method: 'POST',
                headers: window.GW.authHeaders(),
                body: form,
            });
            if (res.ok) done++;
        } catch (err) {
            console.error(err);
        }
    }
    showToast(`${done}/${total} fotoğraf yüklendi`, done === total ? 'success' : 'warning');
    await loadCloudPhotos();
    document.getElementById('cloudFileInput').value = '';
}

// ========== Favorites ==========
async function loadFavorites() {
    try {
        const res = await fetch(`${API_BASE}/favorites`);
        if (!res.ok) return;
        const data = await res.json();
        state.favorites = new Set(data.favorites);
    } catch { /* sessizce geç */ }
}

// ========== Ratings ==========
async function loadRatings() {
    try {
        const res = await fetch(`${API_BASE}/ratings`);
        if (!res.ok) return;
        const data = await res.json();
        state.ratings = new Map(Object.entries(data.ratings));
    } catch { /* sessiz */ }
}

function renderRatingStars(hoverStars = null) {
    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;
    const currentStars = state.ratings.get(imagePath) || 0;
    const display = hoverStars !== null ? hoverStars : currentStars;
    elements.ratingPicker.querySelectorAll('.star').forEach((star, i) => {
        star.classList.toggle('active', i < display);
    });
}

function previewRating(stars) {
    elements.ratingPicker.querySelectorAll('.star').forEach((star, i) => {
        star.classList.toggle('active', i < stars);
    });
}

async function setRating(stars) {
    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;
    try {
        const res = await fetch(`${API_BASE}/rating/${encodeURIComponent(imagePath)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stars })
        });
        if (!res.ok) throw new Error();
        state.ratings.set(imagePath, stars);
        renderRatingStars();
        // Update gallery item star overlay if visible
        updateGalleryItemRating(imagePath, stars);
    } catch { showToast('Puan kaydedilemedi', 'error'); }
}

async function clearRating() {
    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;
    try {
        await fetch(`${API_BASE}/rating/${encodeURIComponent(imagePath)}`, { method: 'DELETE' });
        state.ratings.delete(imagePath);
        renderRatingStars();
        updateGalleryItemRating(imagePath, 0);
    } catch { showToast('Puan silinemedi', 'error'); }
}

function updateGalleryItemRating(imagePath, stars) {
    const items = elements.gallery.querySelectorAll('.gallery-item');
    items.forEach(item => {
        if (item.dataset.path === imagePath) {
            let overlay = item.querySelector('.item-stars');
            if (stars > 0) {
                if (!overlay) {
                    overlay = document.createElement('span');
                    overlay.className = 'item-stars';
                    item.appendChild(overlay);
                }
                overlay.textContent = '★'.repeat(stars);
            } else if (overlay) {
                overlay.remove();
            }
        }
    });
}

// ========== Bookmarks ==========
async function loadBookmarks() {
    try {
        const res = await fetch(`${API_BASE}/bookmarks`);
        if (!res.ok) return;
        const data = await res.json();
        state.bookmarks = data.bookmarks;
        renderBookmarkDropdown();
    } catch { /* sessiz */ }
}

function renderBookmarkDropdown() {
    const dd = elements.bookmarkDropdown;
    dd.innerHTML = '';

    if (!state.currentDirectory) {
        const hint = document.createElement('div');
        hint.className = 'bookmark-hint';
        hint.textContent = 'Önce bir klasör seçin';
        dd.appendChild(hint);
        return;
    }

    // "Add current" button at top
    const addBtn = document.createElement('button');
    addBtn.className = 'bookmark-add-current';
    const isAlreadyBookmarked = state.bookmarks.some(b => b.path === state.currentDirectory);
    addBtn.textContent = isAlreadyBookmarked ? '✓ Zaten eklendi' : '+ Mevcut klasörü ekle';
    addBtn.disabled = isAlreadyBookmarked;
    addBtn.addEventListener('click', async () => {
        if (isAlreadyBookmarked) return;
        try {
            const res = await fetch(`${API_BASE}/bookmark`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: state.currentDirectory, label: state.currentDirectory.split('/').pop() })
            });
            const d = await res.json();
            if (d.ok) {
                await loadBookmarks();
                elements.bookmarkDropdown.classList.remove('hidden');
                updateBookmarkBtnState();
                showToast('Yer imi eklendi', 'success');
            }
        } catch { showToast('Yer imi eklenemedi', 'error'); }
    });
    dd.appendChild(addBtn);

    if (state.bookmarks.length > 0) {
        const divider = document.createElement('hr');
        divider.className = 'bookmark-divider';
        dd.appendChild(divider);
    }

    state.bookmarks.forEach(bm => {
        const item = document.createElement('div');
        item.className = 'bookmark-item';
        const label = document.createElement('span');
        label.className = 'bookmark-label';
        label.textContent = bm.label || bm.path;
        label.title = bm.path;
        label.addEventListener('click', () => {
            autoConnectDirectory(bm.path);
            localStorage.setItem('galleryPath', bm.path);
            elements.bookmarkDropdown.classList.add('hidden');
        });
        const del = document.createElement('button');
        del.className = 'bookmark-del-btn';
        del.textContent = '✕';
        del.title = 'Kaldır';
        del.addEventListener('click', async e => {
            e.stopPropagation();
            try {
                await fetch(`${API_BASE}/bookmark/${bm.id}`, { method: 'DELETE' });
                await loadBookmarks();
                elements.bookmarkDropdown.classList.remove('hidden');
                updateBookmarkBtnState();
            } catch { showToast('Silinemedi', 'error'); }
        });
        item.appendChild(label);
        item.appendChild(del);
        dd.appendChild(item);
    });
}

function toggleBookmarkDropdown() {
    if (elements.bookmarkDropdown.classList.contains('hidden')) {
        renderBookmarkDropdown();
        elements.bookmarkDropdown.classList.remove('hidden');
    } else {
        elements.bookmarkDropdown.classList.add('hidden');
    }
}

function updateBookmarkBtnState() {
    if (!state.currentDirectory) return;
    const isBookmarked = state.bookmarks.some(b => b.path === state.currentDirectory);
    elements.bookmarkAddBtn.classList.toggle('active', isBookmarked);
}

// ========== Stats Panel ==========
async function toggleStatsPanel() {
    if (state.statsOpen) { closeStatsPanel(); return; }
    state.statsOpen = true;
    elements.statsPanel.classList.add('open');
    elements.statsBackdrop.classList.remove('hidden');
    elements.statsContent.innerHTML = '<div class="spinner"></div>';
    try {
        const res = await fetch(`${API_BASE}/stats`);
        if (!res.ok) throw new Error();
        const d = await res.json();
        renderStats(d);
    } catch { elements.statsContent.innerHTML = '<p style="padding:16px">Veri alınamadı.</p>'; }
}

function closeStatsPanel() {
    state.statsOpen = false;
    elements.statsPanel.classList.remove('open');
    elements.statsBackdrop.classList.add('hidden');
}

function renderStats(d) {
    const stars = d.rating_distribution;
    const starsHtml = [5, 4, 3, 2, 1].map(n => {
        const count = stars[n] || 0;
        return `<div class="stat-bar-row"><span>${'★'.repeat(n)}</span><div class="stat-bar"><div class="stat-bar-fill" style="width:${count > 0 ? Math.min(100, count * 10) : 0}%"></div></div><span>${count}</span></div>`;
    }).join('');

    const tagsHtml = (d.top_tags || []).slice(0, 8).map(t =>
        `<span class="stat-tag">#${t.name} <small>(${t.count})</small></span>`
    ).join('');

    elements.statsContent.innerHTML = `
        <div class="stat-group">
            <div class="stat-item"><span class="stat-label">🖼 Resim</span><span class="stat-val">${d.images_count}</span></div>
            <div class="stat-item"><span class="stat-label">🎬 Video</span><span class="stat-val">${d.videos_count}</span></div>
            <div class="stat-item"><span class="stat-label">💾 Boyut</span><span class="stat-val">${d.storage_gb} GB</span></div>
            <div class="stat-item"><span class="stat-label">♥ Favori</span><span class="stat-val">${d.favorite_count}</span></div>
            <div class="stat-item"><span class="stat-label"># Etiketli</span><span class="stat-val">${d.tagged_count}</span></div>
            <div class="stat-item"><span class="stat-label">⭐ Ort. Puan</span><span class="stat-val">${d.avg_rating ? d.avg_rating.toFixed(1) : '—'}</span></div>
            <div class="stat-item"><span class="stat-label">📅 En Eski</span><span class="stat-val">${d.oldest_file || '—'}</span></div>
            <div class="stat-item"><span class="stat-label">📅 En Yeni</span><span class="stat-val">${d.newest_file || '—'}</span></div>
        </div>
        <div class="stat-section-title">Puan Dağılımı</div>
        <div class="stat-bars">${starsHtml}</div>
        ${tagsHtml ? `<div class="stat-section-title">Popüler Etiketler</div><div class="stat-tags">${tagsHtml}</div>` : ''}
    `;
}

// ========== Albums ==========
async function loadAlbums() {
    try {
        const data = await fetch(`${API_BASE}/albums`).then(r => r.json());
        state.albums = data.albums || [];
        if (elements.albumsList) renderAlbumsList();
    } catch { /* silent */ }
}

function renderAlbumsList() {
    if (state.albums.length === 0) {
        elements.albumsList.innerHTML = '<p class="albums-empty">Henüz albüm yok.<br>＋ butonuyla oluşturun.</p>';
        return;
    }
    elements.albumsList.innerHTML = state.albums.map(a => `
        <div class="album-item ${state.activeAlbum === a.id ? 'active' : ''}" data-id="${a.id}">
            <div class="album-item-info">
                <span class="album-item-name">${a.name}</span>
                <span class="album-item-count">${a.count} dosya</span>
            </div>
            <button class="album-del-btn btn-icon" data-id="${a.id}" title="Albümü sil">🗑</button>
        </div>
    `).join('');

    if (!elements.albumsList._delegated) {
        elements.albumsList._delegated = true;
        elements.albumsList.addEventListener('click', async e => {
            const delBtn = e.target.closest('.album-del-btn');
            if (delBtn) {
                if (!confirm('Albümü silmek istiyor musunuz? Dosyalar silinmez.')) return;
                await fetch(`${API_BASE}/albums/${delBtn.dataset.id}`, {method: 'DELETE'});
                if (state.activeAlbum === parseInt(delBtn.dataset.id)) {
                    state.activeAlbum = null;
                    loadImages();
                }
                loadAlbums();
                return;
            }
            const item = e.target.closest('.album-item');
            if (item) {
                const id = parseInt(item.dataset.id);
                state.activeAlbum = state.activeAlbum === id ? null : id;
                renderAlbumsList();
                loadImages();
            }
        });
    }
}

async function toggleAlbumsPanel() {
    if (elements.albumsPanel.classList.contains('open')) {
        closeAlbumsPanel();
    } else {
        await loadAlbums();
        elements.albumsPanel.classList.add('open');
        elements.albumsBackdrop.classList.remove('hidden');
    }
}

function closeAlbumsPanel() {
    elements.albumsPanel.classList.remove('open');
    elements.albumsBackdrop.classList.add('hidden');
}

let _albumModalEditId = null;

function openAlbumModal(albumId = null, name = '', desc = '') {
    _albumModalEditId = albumId;
    elements.albumModalTitle.textContent = albumId ? 'Albümü Düzenle' : 'Yeni Albüm';
    elements.albumModalConfirm.textContent = albumId ? 'Kaydet' : 'Oluştur';
    elements.albumNameInput.value = name;
    elements.albumDescInput.value = desc;
    elements.albumModal.classList.remove('hidden');
    elements.albumNameInput.focus();
}

function closeAlbumModal() {
    elements.albumModal.classList.add('hidden');
    _albumModalEditId = null;
}

async function confirmAlbumModal() {
    const name = elements.albumNameInput.value.trim();
    if (!name) { showToast('Albüm adı gerekli', 'warning'); return; }
    const desc = elements.albumDescInput.value.trim();
    try {
        if (_albumModalEditId) {
            await fetch(`${API_BASE}/albums/${_albumModalEditId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, description: desc})
            });
            showToast('Albüm güncellendi', 'success');
        } else {
            const res = await fetch(`${API_BASE}/albums`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, description: desc})
            }).then(r => r.json());
            if (res.id) showToast(`"${name}" albümü oluşturuldu`, 'success');
        }
        closeAlbumModal();
        loadAlbums();
    } catch {
        showToast('İşlem başarısız', 'error');
    }
}

async function openAddToAlbumPicker() {
    if (state.selectedPaths.size === 0) { showToast('Önce dosya seçin', 'warning'); return; }
    await loadAlbums();
    if (state.albums.length === 0) {
        showToast('Önce bir albüm oluşturun', 'warning');
        return;
    }
    // Simple prompt: list albums, pick one
    const names = state.albums.map(a => `${a.name} (${a.count})`).join('\n');
    const choice = prompt(`Eklenecek albümü seçin (isim yazın):\n${names}`);
    if (!choice) return;
    const album = state.albums.find(a => a.name.toLowerCase() === choice.trim().toLowerCase());
    if (!album) { showToast('Albüm bulunamadı', 'error'); return; }
    const paths = Array.from(state.selectedPaths);
    const res = await fetch(`${API_BASE}/albums/${album.id}/images`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({paths})
    }).then(r => r.json());
    showToast(`${res.added} dosya "${album.name}" albümüne eklendi`, 'success');
    loadAlbums();
}

// ========== Batch Copy / Move ==========
let _folderPickerMode = null;  // 'copy' | 'move'
let _folderPickerSelected = null;
let _folderPickerBrowsePath = null;

async function openFolderPicker(mode) {
    if (state.selectedPaths.size === 0) {
        showToast('Önce dosya seçin', 'warning');
        return;
    }
    _folderPickerMode = mode;
    _folderPickerSelected = null;
    elements.folderPickerTitle.textContent = mode === 'copy' ? '📋 Kopyala — Hedef Klasör' : '✂️ Taşı — Hedef Klasör';
    elements.folderPickerSelectedPath.textContent = '';
    elements.folderPickerConfirm.disabled = true;
    elements.folderPickerModal.classList.remove('hidden');
    const startPath = state.currentDirectory || '/';
    await browseFolderPicker(startPath);
}

function closeFolderPicker() {
    elements.folderPickerModal.classList.add('hidden');
    _folderPickerMode = null;
    _folderPickerSelected = null;
}

async function browseFolderPicker(path) {
    _folderPickerBrowsePath = path;
    elements.folderPickerCurrent.textContent = path;
    elements.folderPickerList.innerHTML = '<div class="spinner" style="margin:16px auto"></div>';
    try {
        const data = await fetch(`${API_BASE}/browse?path=${encodeURIComponent(path)}`).then(r => r.json());
        const items = [];
        if (data.parent) {
            items.push(`<button class="folder-picker-item folder-picker-up" data-path="${data.parent}">⬆ ..</button>`);
        }
        data.entries.filter(e => e.is_dir).forEach(e => {
            items.push(`<button class="folder-picker-item" data-path="${e.path}">📁 ${e.name}</button>`);
        });
        if (items.length === 0) {
            elements.folderPickerList.innerHTML = '<p style="padding:12px;color:var(--text-secondary)">Alt klasör yok</p>';
        } else {
            elements.folderPickerList.innerHTML = items.join('');
            elements.folderPickerList.querySelectorAll('.folder-picker-item').forEach(btn => {
                btn.addEventListener('click', async () => {
                    if (btn.classList.contains('folder-picker-up')) {
                        await browseFolderPicker(btn.dataset.path);
                    } else {
                        // Single click = select, double click = browse into
                        if (_folderPickerSelected === btn.dataset.path) {
                            await browseFolderPicker(btn.dataset.path);
                        } else {
                            elements.folderPickerList.querySelectorAll('.folder-picker-item').forEach(b => b.classList.remove('selected'));
                            btn.classList.add('selected');
                            _folderPickerSelected = btn.dataset.path;
                            elements.folderPickerSelectedPath.textContent = btn.dataset.path;
                            elements.folderPickerConfirm.disabled = false;
                        }
                    }
                });
            });
        }
        // Also allow selecting the current browsed dir
        elements.folderPickerCurrent.onclick = () => {
            _folderPickerSelected = path;
            elements.folderPickerSelectedPath.textContent = path;
            elements.folderPickerConfirm.disabled = false;
        };
    } catch {
        elements.folderPickerList.innerHTML = '<p style="padding:12px;color:var(--text-secondary)">Klasör listelenemedi</p>';
    }
}

async function executeFolderPickerAction() {
    if (!_folderPickerSelected || !_folderPickerMode) return;
    const paths = Array.from(state.selectedPaths);
    const endpoint = _folderPickerMode === 'copy' ? '/batch/copy' : '/batch/move';
    closeFolderPicker();
    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({paths, destination: _folderPickerSelected})
        }).then(r => r.json());
        const verb = _folderPickerMode === 'copy' ? 'kopyalandı' : 'taşındı';
        showToast(`${res.success_count}/${paths.length} dosya ${verb}`, res.success_count === paths.length ? 'success' : 'warning');
        if (_folderPickerMode === 'move') {
            exitSelectMode();
            loadImages();
        }
    } catch {
        showToast('İşlem başarısız', 'error');
    }
}

// ========== QR Code ==========
async function showQRModal() {
    elements.qrModal.classList.remove('hidden');
    elements.qrImage.src = '';
    elements.qrUrlText.textContent = '';
    try {
        const data = await fetch(`${API_BASE}/qr-url`).then(r => r.json());
        elements.qrUrlText.textContent = data.url;
        elements.qrImage.src = `${API_BASE}/qr?t=${Date.now()}`;
    } catch {
        elements.qrUrlText.textContent = window.location.origin;
        elements.qrImage.src = `${API_BASE}/qr?t=${Date.now()}`;
    }
}

function closeQRModal() {
    elements.qrModal.classList.add('hidden');
}

// ========== Compare Mode ==========
const compareState = {
    paths: [],
    zoom: 1,
    panX: 0, panY: 0,
    syncZoom: true,
    dragging: null  // { pane, startX, startY, startPanX, startPanY }
};

const COMPARE_ZOOM_MIN = 0.2;
const COMPARE_ZOOM_MAX = 10;

function openCompareMode() {
    const paths = [...state.selectedPaths];
    if (paths.length !== 2) { showToast('Tam 2 resim seçin', 'error'); return; }
    compareState.paths = paths;
    compareState.zoom = 1; compareState.panX = 0; compareState.panY = 0;

    elements.compareImgLeft.src = `${API_BASE}/image/${encodeURIComponent(paths[0])}`;
    elements.compareImgRight.src = `${API_BASE}/image/${encodeURIComponent(paths[1])}`;
    elements.compareLabelLeft.textContent = paths[0].split('/').pop();
    elements.compareLabelRight.textContent = paths[1].split('/').pop();
    elements.compareModal.classList.remove('hidden');
    applyCompareTransform();
    setupCompareInteractions();
}

function closeCompareMode() {
    elements.compareModal.classList.add('hidden');
    cleanupCompareInteractions();
}

function resetCompare() {
    compareState.zoom = 1; compareState.panX = 0; compareState.panY = 0;
    applyCompareTransform();
}

function applyCompareTransform() {
    const t = `translate(calc(-50% + ${compareState.panX}px), calc(-50% + ${compareState.panY}px)) scale(${compareState.zoom})`;
    elements.compareImgLeft.style.transform = t;
    elements.compareImgRight.style.transform = t;
}

function _onCompareWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    compareState.zoom = Math.max(COMPARE_ZOOM_MIN, Math.min(COMPARE_ZOOM_MAX, compareState.zoom * delta));
    applyCompareTransform();
}

function _onCompareMousedown(e) {
    compareState.dragging = {
        startX: e.clientX, startY: e.clientY,
        startPanX: compareState.panX, startPanY: compareState.panY
    };
}

function _onCompareMousemove(e) {
    if (!compareState.dragging) return;
    compareState.panX = compareState.dragging.startPanX + (e.clientX - compareState.dragging.startX);
    compareState.panY = compareState.dragging.startPanY + (e.clientY - compareState.dragging.startY);
    applyCompareTransform();
}

function _onCompareMouseup() { compareState.dragging = null; }

function setupCompareInteractions() {
    const split = document.getElementById('compareSplit');
    split.addEventListener('wheel', _onCompareWheel, { passive: false });
    split.addEventListener('mousedown', _onCompareMousedown);
    window.addEventListener('mousemove', _onCompareMousemove);
    window.addEventListener('mouseup', _onCompareMouseup);
}

function cleanupCompareInteractions() {
    const split = document.getElementById('compareSplit');
    split.removeEventListener('wheel', _onCompareWheel);
    split.removeEventListener('mousedown', _onCompareMousedown);
    window.removeEventListener('mousemove', _onCompareMousemove);
    window.removeEventListener('mouseup', _onCompareMouseup);
}

// ========== Map View ==========
let _mapInstance = null;
let _mapMarkersLayer = null;

async function openMapView() {
    if (elements.mapModal._loading) return;
    elements.mapModal._loading = true;
    elements.mapModal.classList.remove('hidden');

    // Init map once
    if (!_mapInstance) {
        _mapInstance = L.map('mapContainer').setView([39.9, 32.8], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19
        }).addTo(_mapInstance);
        _mapMarkersLayer = L.layerGroup().addTo(_mapInstance);
    } else {
        _mapMarkersLayer.clearLayers();
        setTimeout(() => _mapInstance.invalidateSize(), 100);
    }

    elements.mapImageCount.textContent = 'Yükleniyor...';

    try {
        const res = await fetch(`${API_BASE}/images/map`);
        if (!res.ok) throw new Error('Harita verileri alınamadı');
        const data = await res.json();

        if (!data.images.length) {
            elements.mapImageCount.textContent = 'GPS verisi bulunamadı';
            return;
        }

        elements.mapImageCount.textContent = `${data.images.length} fotoğraf`;
        const bounds = [];

        data.images.forEach(img => {
            const marker = L.marker([img.lat, img.lng]);
            marker.bindPopup(`
                <div style="text-align:center">
                    <img src="${API_BASE}/image/${encodeURIComponent(img.path)}?thumb=true&w=160"
                         style="max-width:160px;max-height:120px;border-radius:4px;" loading="lazy">
                    <div style="margin-top:4px;font-size:0.75rem;word-break:break-all">${img.path.split('/').pop()}</div>
                </div>
            `);
            _mapMarkersLayer.addLayer(marker);
            bounds.push([img.lat, img.lng]);
        });

        if (bounds.length) {
            _mapInstance.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 });
        }
        setTimeout(() => _mapInstance.invalidateSize(), 200);
    } catch (err) {
        elements.mapImageCount.textContent = 'Hata oluştu';
        showToast(err.message, 'error');
    } finally {
        elements.mapModal._loading = false;
    }
}

function closeMapView() {
    elements.mapModal.classList.add('hidden');
}

// ========== Kiosk Mode ==========
function toggleKioskMode() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {
            showToast('Tam ekran desteklenmiyor', 'error');
        });
        state.kioskMode = true;
        document.body.classList.add('kiosk');
    } else {
        document.exitFullscreen();
        state.kioskMode = false;
        document.body.classList.remove('kiosk');
    }
}

// ========== Slideshow Interval ==========
function setSlideshowInterval(ms) {
    state.slideshowInterval = ms;
    localStorage.setItem('slideshowInterval', ms);
    updateIntervalUI();
    // restart slideshow if running (slideshow.js exposes restartSlideshow)
    if (typeof restartSlideshow === 'function' && state.slideshowActive) {
        restartSlideshow();
    }
}

function updateIntervalUI() {
    const ms = state.slideshowInterval;
    elements.slideshowIntervalPopover.querySelectorAll('.interval-opt').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.ms) === ms);
    });
}

// ========== Timeline Helpers ==========
function formatMonthLabel(ym) {
    return new Intl.DateTimeFormat('tr-TR', { year: 'numeric', month: 'long' })
        .format(new Date(ym + '-01'));
}

function groupByDate(images) {
    const groups = {};
    images.forEach((imagePath, index) => {
        const mtime = state.imageMtimes[imagePath];
        let key;
        if (mtime) {
            const d = new Date(mtime * 1000);
            key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
        } else {
            key = 'unknown';
        }
        if (!groups[key]) groups[key] = { label: key === 'unknown' ? 'Tarih Bilinmiyor' : formatMonthLabel(key), items: [] };
        groups[key].items.push({ imagePath, index });
    });
    return Object.entries(groups).sort(([a], [b]) => b.localeCompare(a)); // en yeni önce
}

// ========== Render Gallery ==========
function renderGallery() {
    elements.gallery.innerHTML = '';
    elements.gallery.dataset.view = state.viewMode;

    if (state.images.length === 0) {
        elements.emptyState.classList.remove('hidden');
        elements.emptyState.innerHTML = '<p>🔍 Hiç resim bulunamadı</p>';
        return;
    }

    // Timeline modu: aya göre gruplandır
    if (state.viewMode === 'timeline') {
        elements.gallery.dataset.view = 'thumbnail'; // galeri ızgarası thumbnail layout kullanır
        const groups = groupByDate(state.images);
        groups.forEach(([key, { label, items }]) => {
            const header = document.createElement('h3');
            header.className = 'timeline-group-header';
            header.textContent = `${label} (${items.length})`;
            elements.gallery.appendChild(header);

            const groupWrap = document.createElement('div');
            groupWrap.className = 'timeline-group-grid';
            items.forEach(({ imagePath, index }) => {
                groupWrap.appendChild(buildGalleryItem(imagePath, index));
            });
            elements.gallery.appendChild(groupWrap);
        });
        lazyLoadImages();
        return;
    }

    state.images.forEach((imagePath, index) => {
        elements.gallery.appendChild(buildGalleryItem(imagePath, index));
    });

    lazyLoadImages();
}

function buildGalleryItem(imagePath, index) {
    const item = document.createElement('div');
    const isVideo = /\.(mp4|webm|mov)$/i.test(imagePath);
    item.className = 'gallery-item' + (isVideo ? ' video-item' : '');
    item.dataset.name = imagePath.split('/').pop();
    item.dataset.path = imagePath;

    const img = document.createElement('img');
    img.className = 'loading';
    const encPath = encodeURIComponent(imagePath);
    img.dataset.src = `${API_BASE}/image/${encPath}?thumb=true&w=500`;
    img.dataset.srcset = `${API_BASE}/image/${encPath}?thumb=true&w=500 1x, ${API_BASE}/image/${encPath}?thumb=true&w=800 2x`;
    img.alt = imagePath.split('/').pop();

    img.addEventListener('load', () => img.classList.remove('loading'));
    item.addEventListener('click', () => {
        if (state.selectMode) { toggleItemSelection(item, imagePath); return; }
        openLightbox(index);
    });

    // Favori butonu
    const heart = document.createElement('button');
    heart.className = 'fav-btn' + (state.favorites.has(imagePath) ? ' active' : '');
    heart.textContent = '♥';
    heart.title = 'Favori';
    heart.addEventListener('click', async e => {
        e.stopPropagation();
        try {
            const res = await fetch(`${API_BASE}/favorite/${encodeURIComponent(imagePath)}`, { method: 'POST' });
            const d = await res.json();
            if (d.is_favorite) { state.favorites.add(imagePath); heart.classList.add('active'); }
            else { state.favorites.delete(imagePath); heart.classList.remove('active'); }
        } catch { showToast('Favori güncellenemedi', 'error'); }
    });

    item.appendChild(img);
    item.appendChild(heart);

    // Star rating overlay
    const stars = state.ratings.get(imagePath);
    if (stars) {
        const starOverlay = document.createElement('span');
        starOverlay.className = 'item-stars';
        starOverlay.textContent = '★'.repeat(stars);
        item.appendChild(starOverlay);
    }

    const effectiveView = state.viewMode === 'timeline' ? 'thumbnail' : state.viewMode;
    if (effectiveView === 'extended') {
        const label = document.createElement('div');
        label.className = 'gallery-item-label';
        const fname = imagePath.split('/').pop();
        label.textContent = fname;
        label.title = fname;
        item.appendChild(label);
    }

    if (state.selectMode) {
        item.classList.add('selectable');
        if (state.selectedPaths.has(imagePath)) item.classList.add('selected');
    }

    return item;
}

// ========== Lazy Loading ==========
let imageObserver;

function lazyLoadImages() {
    if (imageObserver) imageObserver.disconnect();

    imageObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                if (img.dataset.srcset) img.srcset = img.dataset.srcset;
                imageObserver.unobserve(img);
            }
        });
    }, { rootMargin: '50px' });

    document.querySelectorAll('.gallery-item img').forEach(img => imageObserver.observe(img));
}

// ========== Pagination ==========
function getPageWindows(current, total) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

    const set = new Set([1, total]);
    for (let i = Math.max(2, current - 2); i <= Math.min(total - 1, current + 2); i++) set.add(i);

    const sorted = [...set].sort((a, b) => a - b);
    const result = [];
    let prev = 0;
    for (const p of sorted) {
        if (p - prev > 1) result.push('…');
        result.push(p);
        prev = p;
    }
    return result;
}

function updatePagination() {
    const cur = state.currentPage;
    const total = state.totalPages;

    elements.pageInfo.textContent = total > 0
        ? `${cur} / ${total}  ·  ${state.totalImages} dosya`
        : '';

    elements.prevPage.disabled = cur <= 1;
    elements.nextPage.disabled = cur >= total || total === 0;
    elements.firstPage.disabled = cur <= 1;
    elements.lastPage.disabled = cur >= total || total === 0;

    // Sliding window sayfa butonları
    elements.pageNumbers.innerHTML = '';
    if (total > 0) {
        getPageWindows(cur, total).forEach(p => {
            if (p === '…') {
                const span = document.createElement('span');
                span.className = 'page-ellipsis';
                span.textContent = '…';
                elements.pageNumbers.appendChild(span);
            } else {
                const btn = document.createElement('button');
                btn.className = 'btn-page-num' + (p === cur ? ' active' : '');
                btn.textContent = p;
                btn.addEventListener('click', () => goToPage(p));
                elements.pageNumbers.appendChild(btn);
            }
        });
    }

    if (elements.jumpInput) elements.jumpInput.max = total;
    elements.pagination.style.display = total === 0 && state.images.length === 0 ? 'none' : '';
}

function goToPage(page) {
    const p = Math.max(1, Math.min(state.totalPages, page));
    if (p !== state.currentPage) {
        state.currentPage = p;
        loadImages();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function changePage(delta) { goToPage(state.currentPage + delta); }

function handleJump() {
    const val = parseInt(elements.jumpInput.value);
    if (val >= 1 && val <= state.totalPages) {
        goToPage(val);
        elements.jumpInput.value = '';
    }
}

// ========== Lightbox ==========
let zoomLevel = 1;
const MIN_ZOOM = 0.5, MAX_ZOOM = 6;

function resetZoom() {
    zoomLevel = 1;
    elements.lightboxImage.style.transform = 'scale(1)';
    elements.lightboxImage.style.cursor = 'zoom-in';
}

function handleLightboxZoom(e) {
    e.preventDefault();
    zoomLevel = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoomLevel * (e.deltaY < 0 ? 1.1 : 0.9)));
    elements.lightboxImage.style.transform = `scale(${zoomLevel})`;
    elements.lightboxImage.style.cursor = zoomLevel > 1 ? 'grab' : 'zoom-in';
}

let lastPinchDist = 0;
function handlePinchStart(e) {
    if (e.touches.length === 2)
        lastPinchDist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
}
function handlePinchMove(e) {
    if (e.touches.length !== 2) return;
    e.preventDefault();
    const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
    );
    zoomLevel = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoomLevel * (dist / lastPinchDist)));
    elements.lightboxImage.style.transform = `scale(${zoomLevel})`;
    lastPinchDist = dist;
}

window.zoomIn = function () {
    zoomLevel = Math.min(MAX_ZOOM, zoomLevel * 1.2);
    elements.lightboxImage.style.transform = `scale(${zoomLevel})`;
    elements.lightboxImage.style.cursor = zoomLevel > 1 ? 'grab' : 'zoom-in';
};
window.zoomOut = function () {
    zoomLevel = Math.max(MIN_ZOOM, zoomLevel / 1.2);
    elements.lightboxImage.style.transform = `scale(${zoomLevel})`;
    elements.lightboxImage.style.cursor = zoomLevel > 1 ? 'grab' : 'zoom-in';
};

// ========== Lightbox Navigation Flags ==========
let _videoActive = false;        // gerçek video oynatılıyor mu?
let _autoplayAdvancing = false;  // ended/error handler aktif mi?
let _navigating = false;         // showNextImage/showPrevImage kilit

function openLightbox(index) {
    if (MODE === 'bulut') { openCloudLightbox(index); return; }
    state.currentImageIndex = index;
    const imagePath = state.images[index];
    const isVideo = /\.(mp4|webm|mov)$/i.test(imagePath);

    resetZoom();

    if (isVideo) {
        _videoActive = true;
        elements.lightboxImage.classList.add('hidden');
        elements.lightboxVideo.classList.remove('hidden');
        elements.lightboxVideo.src = `${API_BASE}/image/${encodeURIComponent(imagePath)}`;
        if (state.videoAutoplay) {
            elements.lightboxVideo.play().catch(() => {});
        }
    } else {
        _videoActive = false;
        elements.lightboxVideo.pause();
        elements.lightboxVideo.removeAttribute('src');
        elements.lightboxVideo.load();
        elements.lightboxImage.classList.remove('hidden');
        elements.lightboxVideo.classList.add('hidden');
        elements.lightboxImage.src = `${API_BASE}/image/${encodeURIComponent(imagePath)}`;
    }

    elements.autoplayToggleBtn.classList.toggle('active', state.videoAutoplay);
    elements.imageName.textContent = imagePath.split('/').pop();
    elements.imageCounter.textContent = `${index + 1} / ${state.images.length}`;
    elements.lightbox.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    renderRatingStars();
}

function closeLightbox() {
    _videoActive = false;
    elements.lightbox.classList.add('hidden');
    document.body.style.overflow = '';
    document.getElementById('exifPanel').classList.add('hidden');
    elements.lightboxVideo.pause();
    elements.lightboxVideo.removeAttribute('src');
    elements.lightboxVideo.load();
    closeEditToolbar();
}

// ========== Faz 5.1 — Image Editing ==========

let _cropState = null; // { startX, startY, endX, endY, drawing }

function toggleEditToolbar() {
    const photoBar = document.getElementById('editToolbar');
    const videoBar = document.getElementById('videoEditToolbar');
    const isOpen = !photoBar.classList.contains('hidden') || !videoBar.classList.contains('hidden');
    if (isOpen) {
        closeEditToolbar();
        closeVideoEditToolbar();
        return;
    }
    const imagePath = state.images[state.currentImageIndex];
    const isVideo = /\.(mp4|webm|mov|mkv|m4v)$/i.test(imagePath || '');
    if (isVideo) {
        videoBar.classList.remove('hidden');
        document.getElementById('editModeBtn').classList.add('active');
        checkVideoBackup(imagePath);
    } else {
        photoBar.classList.remove('hidden');
        document.getElementById('editModeBtn').classList.add('active');
        checkEditBackup(imagePath);
    }
}

function closeEditToolbar() {
    document.getElementById('editToolbar').classList.add('hidden');
    closeAdjustPanel();
    closeFilterPanel();
    cancelCropMode();
    const btn = document.getElementById('editModeBtn');
    if (btn) btn.classList.remove('active');
}

function closeVideoEditToolbar() {
    document.getElementById('videoEditToolbar').classList.add('hidden');
    document.getElementById('trimPanel').classList.add('hidden');
    const btn = document.getElementById('editModeBtn');
    if (btn) btn.classList.remove('active');
}

async function checkEditBackup(imagePath) {
    try {
        const res = await fetch(`${API_BASE}/edit/${encodeURIComponent(imagePath)}/has-backup`);
        const d = await res.json();
        document.getElementById('editRevertBtn').disabled = !d.has_backup;
        document.getElementById('editRevertBtn').style.opacity = d.has_backup ? '1' : '0.4';
    } catch {}
}

async function applyEdit(operation, params) {
    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;
    try {
        const res = await fetch(`${API_BASE}/edit/${encodeURIComponent(imagePath)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ operation, params })
        });
        if (!res.ok) {
            const d = await res.json().catch(() => ({}));
            showToast(d.detail || 'Düzenleme hatası', 'error');
            return;
        }
        showToast('Düzenleme uygulandı', 'success', 2000);
        // Reload image with cache-bust; canlı önizleme filtresini temizle
        if (typeof _clearPreview === 'function') _clearPreview();
        elements.lightboxImage.src = `${API_BASE}/image/${encodeURIComponent(imagePath)}?t=${Date.now()}`;
        // Enable revert button
        document.getElementById('editRevertBtn').disabled = false;
        document.getElementById('editRevertBtn').style.opacity = '1';
    } catch (e) {
        showToast('Bağlantı hatası', 'error');
    }
}

async function revertEdit() {
    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;
    if (!confirm('Orijinal dosyaya dönülsün mü?')) return;
    try {
        const res = await fetch(`${API_BASE}/edit/${encodeURIComponent(imagePath)}/revert`, { method: 'POST' });
        const d = await res.json();
        if (d.reverted) {
            showToast('Orijinal dosya geri yüklendi', 'success');
            elements.lightboxImage.src = `${API_BASE}/image/${encodeURIComponent(imagePath)}?t=${Date.now()}`;
            document.getElementById('editRevertBtn').disabled = true;
            document.getElementById('editRevertBtn').style.opacity = '0.4';
        } else {
            showToast(d.reason || 'Yedek bulunamadı', 'warning');
        }
    } catch {
        showToast('Bağlantı hatası', 'error');
    }
}

// ── Video edit (Faz 9 — trim) ──

async function checkVideoBackup(path) {
    try {
        const res = await fetch(`${API_BASE}/edit/${encodeURIComponent(path)}/has-backup`);
        const d = await res.json();
        const btn = document.getElementById('videoRevertBtn');
        btn.disabled = !d.has_backup;
        btn.style.opacity = d.has_backup ? '1' : '0.4';
    } catch {}
}

function openTrimPanel() {
    const video = elements.lightboxVideo;
    const dur = video && isFinite(video.duration) ? video.duration : 0;
    if (!dur) { showToast('Video süresi okunamadı — önce oynatın', 'warning'); return; }
    const panel = document.getElementById('trimPanel');
    const startS = document.getElementById('trimStartSlider');
    const endS = document.getElementById('trimEndSlider');
    startS.value = 0;
    endS.value = 1000;
    const range = document.getElementById('trimRange');

    const updateLabels = () => {
        let s = parseInt(startS.value), e = parseInt(endS.value);
        if (s >= e) { if (document.activeElement === startS) s = e - 1; else e = s + 1; startS.value = s; endS.value = e; }
        const startSec = (s / 1000) * dur;
        const endSec = (e / 1000) * dur;
        document.getElementById('trimStartVal').textContent = startSec.toFixed(1);
        document.getElementById('trimEndVal').textContent = endSec.toFixed(1);
        range.style.left = (s / 10) + '%';
        range.style.right = (100 - e / 10) + '%';
        if (document.activeElement === startS) video.currentTime = startSec;
        else if (document.activeElement === endS) video.currentTime = Math.max(0, endSec - 0.1);
    };
    startS.oninput = updateLabels;
    endS.oninput = updateLabels;
    panel.dataset.duration = dur;
    updateLabels();
    panel.classList.remove('hidden');
}

async function applyTrim() {
    const path = state.images[state.currentImageIndex];
    const panel = document.getElementById('trimPanel');
    const dur = parseFloat(panel.dataset.duration || '0');
    if (!path || !dur) return;
    const startFrac = parseInt(document.getElementById('trimStartSlider').value) / 1000;
    const endFrac = parseInt(document.getElementById('trimEndSlider').value) / 1000;
    const start_ms = Math.round(startFrac * dur * 1000);
    const end_ms = Math.round(endFrac * dur * 1000);
    if (end_ms - start_ms < 200) { showToast('En az 0.2 saniye seçin', 'warning'); return; }

    const btn = document.getElementById('trimApplyBtn');
    btn.disabled = true; btn.textContent = 'Kesiliyor…';
    try {
        const res = await fetch(`${API_BASE}/edit/${encodeURIComponent(path)}/trim`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_ms, end_ms }),
        });
        if (!res.ok) {
            const d = await res.json().catch(() => ({}));
            showToast(d.detail || 'Video kesme hatası', 'error');
            return;
        }
        showToast('Video kesildi', 'success', 2500);
        panel.classList.add('hidden');
        elements.lightboxVideo.src = `${API_BASE}/image/${encodeURIComponent(path)}?t=${Date.now()}`;
        const rb = document.getElementById('videoRevertBtn');
        rb.disabled = false; rb.style.opacity = '1';
    } catch {
        showToast('Bağlantı hatası', 'error');
    } finally {
        btn.disabled = false; btn.textContent = 'Kes ve Kaydet';
    }
}

async function revertVideoEdit() {
    const path = state.images[state.currentImageIndex];
    if (!path) return;
    if (!confirm('Orijinal videoya dönülsün mü?')) return;
    try {
        const res = await fetch(`${API_BASE}/edit/${encodeURIComponent(path)}/revert`, { method: 'POST' });
        const d = await res.json();
        if (d.reverted) {
            showToast('Orijinal video geri yüklendi', 'success');
            elements.lightboxVideo.src = `${API_BASE}/image/${encodeURIComponent(path)}?t=${Date.now()}`;
            const rb = document.getElementById('videoRevertBtn');
            rb.disabled = true; rb.style.opacity = '0.4';
        } else {
            showToast(d.reason || 'Yedek bulunamadı', 'warning');
        }
    } catch {
        showToast('Bağlantı hatası', 'error');
    }
}

// ── Adjust (Faz 9 — ışık/renk/keskinlik + canlı önizleme) ──

const _ADJUST_SLIDERS = [
    { id: 'brightness', def: 1.0, dec: 2 },
    { id: 'contrast',   def: 1.0, dec: 2 },
    { id: 'saturation', def: 1.0, dec: 2 },
    { id: 'sharpness',  def: 1.0, dec: 2 },
    { id: 'temperature', def: 0,  dec: 0 },
    { id: 'gamma',      def: 1.0, dec: 2 },
];

function _livePreview() {
    // CSS filter ile yaklaşık canlı önizleme (sharpness/gamma CSS'te yok → yaklaşık)
    const b = parseFloat(document.getElementById('brightnessSlider').value);
    const c = parseFloat(document.getElementById('contrastSlider').value);
    const s = parseFloat(document.getElementById('saturationSlider').value);
    const t = parseFloat(document.getElementById('temperatureSlider').value);
    const g = parseFloat(document.getElementById('gammaSlider').value);
    // sıcaklık → sepia + hue-rotate yaklaşımı; gamma → brightness çarpanıyla kaba yaklaşım
    const warmSepia = t > 0 ? (t / 100 * 0.4).toFixed(2) : 0;
    const coolHue = t < 0 ? Math.round(t / 100 * 40) : 0; // negatif derece = maviye
    const gammaApprox = (b * (g >= 1 ? 1 + (g - 1) * 0.25 : g)).toFixed(3);
    elements.lightboxImage.style.filter =
        `brightness(${gammaApprox}) contrast(${c}) saturate(${s}) sepia(${warmSepia}) hue-rotate(${coolHue}deg)`;
}

function _clearPreview() {
    elements.lightboxImage.style.filter = '';
}

function resetAdjustSliders() {
    _ADJUST_SLIDERS.forEach(({ id, def, dec }) => {
        document.getElementById(id + 'Slider').value = def;
        document.getElementById(id + 'Val').textContent = dec ? def.toFixed(dec) : String(def);
    });
    _clearPreview();
}

function openAdjustPanel() {
    document.getElementById('filterPanel').classList.add('hidden');
    resetAdjustSliders();
    document.getElementById('adjustPanel').classList.remove('hidden');
    _ADJUST_SLIDERS.forEach(({ id, dec }) => {
        const slider = document.getElementById(id + 'Slider');
        slider.oninput = e => {
            const v = parseFloat(e.target.value);
            document.getElementById(id + 'Val').textContent = dec ? v.toFixed(dec) : String(v);
            _livePreview();
        };
    });
}

function closeAdjustPanel() {
    document.getElementById('adjustPanel').classList.add('hidden');
    _clearPreview();
}

async function applyAdjust() {
    const params = {
        brightness: parseFloat(document.getElementById('brightnessSlider').value),
        contrast: parseFloat(document.getElementById('contrastSlider').value),
        saturation: parseFloat(document.getElementById('saturationSlider').value),
        sharpness: parseFloat(document.getElementById('sharpnessSlider').value),
        temperature: parseFloat(document.getElementById('temperatureSlider').value),
        gamma: parseFloat(document.getElementById('gammaSlider').value),
    };
    closeAdjustPanel();
    await applyEdit('adjust', params);
}

// ── Filter presets (Faz 9) ──

function openFilterPanel() {
    document.getElementById('adjustPanel').classList.add('hidden');
    _clearPreview();
    document.getElementById('filterPanel').classList.remove('hidden');
}

function closeFilterPanel() {
    document.getElementById('filterPanel').classList.add('hidden');
}

async function applyFilterPreset(preset) {
    closeFilterPanel();
    await applyEdit('filter', { preset });
}

// ── Crop ──

function startCropMode() {
    const canvas = document.getElementById('cropCanvas');
    const img = elements.lightboxImage;
    if (!img || img.classList.contains('hidden')) {
        showToast('Kırpmak için önce bir resim açın', 'warning');
        return;
    }
    canvas.width = img.naturalWidth || img.clientWidth;
    canvas.height = img.naturalHeight || img.clientHeight;
    canvas.style.width = img.clientWidth + 'px';
    canvas.style.height = img.clientHeight + 'px';
    canvas.style.left = img.offsetLeft + 'px';
    canvas.style.top = img.offsetTop + 'px';
    canvas.classList.remove('hidden');
    _cropState = { startX: 0, startY: 0, endX: 0, endY: 0, drawing: false };

    const getPos = (e) => {
        const rect = canvas.getBoundingClientRect();
        const scaleX = (img.naturalWidth || img.clientWidth) / rect.width;
        const scaleY = (img.naturalHeight || img.clientHeight) / rect.height;
        const cx = ((e.clientX || e.touches[0].clientX) - rect.left) * scaleX;
        const cy = ((e.clientY || e.touches[0].clientY) - rect.top) * scaleY;
        return { x: Math.round(cx), y: Math.round(cy) };
    };

    const drawRect = () => {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(0,0,0,0.4)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        const x = Math.min(_cropState.startX, _cropState.endX);
        const y = Math.min(_cropState.startY, _cropState.endY);
        const w = Math.abs(_cropState.endX - _cropState.startX);
        const h = Math.abs(_cropState.endY - _cropState.startY);
        ctx.clearRect(x, y, w, h);
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);
    };

    canvas._onmousedown = (e) => {
        const p = getPos(e);
        _cropState = { startX: p.x, startY: p.y, endX: p.x, endY: p.y, drawing: true };
        e.preventDefault();
    };
    canvas._onmousemove = (e) => {
        if (!_cropState.drawing) return;
        const p = getPos(e);
        _cropState.endX = p.x; _cropState.endY = p.y;
        drawRect();
    };
    canvas._onmouseup = async (e) => {
        if (!_cropState.drawing) return;
        _cropState.drawing = false;
        const x = Math.min(_cropState.startX, _cropState.endX);
        const y = Math.min(_cropState.startY, _cropState.endY);
        const w = Math.abs(_cropState.endX - _cropState.startX);
        const h = Math.abs(_cropState.endY - _cropState.startY);
        if (w < 10 || h < 10) { cancelCropMode(); return; }
        cancelCropMode();
        await applyEdit('crop', { x, y, w, h });
    };

    canvas.addEventListener('mousedown', canvas._onmousedown);
    canvas.addEventListener('mousemove', canvas._onmousemove);
    canvas.addEventListener('mouseup', canvas._onmouseup);
}

function cancelCropMode() {
    const canvas = document.getElementById('cropCanvas');
    if (!canvas) return;
    canvas.classList.add('hidden');
    if (canvas._onmousedown) canvas.removeEventListener('mousedown', canvas._onmousedown);
    if (canvas._onmousemove) canvas.removeEventListener('mousemove', canvas._onmousemove);
    if (canvas._onmouseup) canvas.removeEventListener('mouseup', canvas._onmouseup);
    _cropState = null;
}

function getVisualAdjacentIndex(currentIndex, direction) {
    const items = [...elements.gallery.querySelectorAll('.gallery-item')];
    if (!items.length) return -1;
    const currentItem = items[currentIndex];
    if (!currentItem) return -1;
    const currentRect = currentItem.getBoundingClientRect();
    const tolerance = currentRect.height * 0.5;
    const rows = [];
    items.forEach((item, idx) => {
        const rect = item.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        let row = rows.find(r => Math.abs(r.midY - mid) < tolerance);
        if (!row) { row = { midY: mid, items: [] }; rows.push(row); }
        row.items.push({ index: idx, rect });
    });
    rows.sort((a, b) => a.midY - b.midY);
    rows.forEach(r => r.items.sort((a, b) => a.rect.left - b.rect.left));
    const rowIdx = rows.findIndex(r => r.items.some(i => i.index === currentIndex));
    if (rowIdx === -1) return -1;
    const row = rows[rowIdx];
    const posInRow = row.items.findIndex(i => i.index === currentIndex);
    if (direction === 'next') {
        if (posInRow < row.items.length - 1) return row.items[posInRow + 1].index;
        if (rowIdx < rows.length - 1) return rows[rowIdx + 1].items[0].index;
        return -1;
    } else {
        if (posInRow > 0) return row.items[posInRow - 1].index;
        if (rowIdx > 0) { const pr = rows[rowIdx - 1]; return pr.items[pr.items.length - 1].index; }
        return -1;
    }
}
async function showPrevImage() {
    if (_navigating) return;
    _navigating = true;
    try {
        if (MODE === 'bulut') {
            const prevIdx = state.currentImageIndex - 1;
            if (prevIdx >= 0) openCloudLightbox(prevIdx);
            return;
        }
        const prevIdx = state.currentImageIndex - 1;
        if (prevIdx >= 0) {
            openLightbox(prevIdx);
        } else if (state.currentPage > 1) {
            state.currentPage--;
            await loadImages();
            if (state.images.length > 0) openLightbox(state.images.length - 1);
        }
    } finally {
        _navigating = false;
    }
}
async function showNextImage() {
    if (_navigating) return;
    _navigating = true;
    try {
        if (MODE === 'bulut') {
            const nextIdx = state.currentImageIndex + 1;
            if (nextIdx < state.cloudPhotos.length) openCloudLightbox(nextIdx);
            return;
        }
        const nextIdx = state.currentImageIndex + 1;
        if (nextIdx < state.images.length) {
            openLightbox(nextIdx);
        } else if (state.currentPage < state.totalPages) {
            state.currentPage++;
            await loadImages();
            if (state.images.length > 0) openLightbox(0);
        } else if (state.totalPages > 1) {
            // Son sayfa son öğe → başa dön
            state.currentPage = 1;
            await loadImages();
            if (state.images.length > 0) openLightbox(0);
        } else if (state.images.length > 0) {
            // Tek sayfa son öğe → başa dön
            openLightbox(0);
        }
    } finally {
        _navigating = false;
    }
}

// ========== Delete / Trash ==========
async function deleteCurrentImage() {
    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;

    try {
        const res = await fetch(`${API_BASE}/image/${encodeURIComponent(imagePath)}`, { method: 'DELETE' });
        if (!res.ok) { showToast('Silme başarısız', 'error'); return; }
        const data = await res.json();

        state.images.splice(state.currentImageIndex, 1);
        state.totalImages = Math.max(0, state.totalImages - 1);
        closeLightbox();
        renderGallery();
        updatePagination();
        updateTrashCount();
        showUndoToast(`"${data.filename}" silindi`, data.trash_id);
    } catch { showToast('Hata oluştu', 'error'); }
}

async function updateTrashCount() {
    try {
        const res = await fetch(`${API_BASE}/trash`);
        if (!res.ok) return;
        const data = await res.json();
        const count = data.items.filter(i => i.exists).length;
        elements.trashCount.textContent = count;
        elements.trashCount.classList.toggle('hidden', count === 0);
    } catch { /* sessiz */ }
}

async function openTrashModal() {
    elements.trashModal.classList.remove('hidden');
    await renderTrashList();
}

function closeTrashModal() { elements.trashModal.classList.add('hidden'); }

async function renderTrashList() {
    try {
        const res = await fetch(`${API_BASE}/trash`);
        if (!res.ok) return;
        const data = await res.json();
        const items = data.items.filter(i => i.exists);

        elements.trashList.innerHTML = '';
        elements.trashEmptyHint.style.display = items.length === 0 ? '' : 'none';

        items.forEach(item => {
            const li = document.createElement('li');
            li.className = 'trash-item';
            li.innerHTML = `
                <span class="trash-item-name" title="${item.original}">${item.filename}</span>
                <div class="trash-item-actions">
                    <button class="btn-restore" data-id="${item.id}">Geri Al</button>
                    <button class="btn-permdelete" data-id="${item.id}">Kalıcı Sil</button>
                </div>
            `;
            li.querySelector('.btn-restore').addEventListener('click', async () => {
                const r = await fetch(`${API_BASE}/restore/${item.id}`, { method: 'POST' });
                if (r.ok) {
                    showToast(`"${item.filename}" geri alındı`, 'success');
                    await renderTrashList();
                    updateTrashCount();
                    refreshGallery();
                } else showToast('Geri alma başarısız', 'error');
            });
            li.querySelector('.btn-permdelete').addEventListener('click', async () => {
                if (!confirm(`"${item.filename}" kalıcı olarak silinecek. Emin misiniz?`)) return;
                const r = await fetch(`${API_BASE}/trash/${item.id}`, { method: 'DELETE' });
                if (r.ok) {
                    showToast(`"${item.filename}" kalıcı silindi`, 'warning');
                    await renderTrashList();
                    updateTrashCount();
                }
            });
            elements.trashList.appendChild(li);
        });
    } catch { showToast('Çöp kutusu yüklenemedi', 'error'); }
}

// ========== Tags ==========
async function loadAllTags() {
    try {
        const res = await fetch(`${API_BASE}/tags`);
        if (!res.ok) return;
        const data = await res.json();
        state.allTags = data.tags;
        renderTagChips();
    } catch { /* sessiz */ }
}

function renderTagChips() {
    elements.tagChips.innerHTML = '';
    if (state.allTags.length === 0) {
        elements.tagChips.innerHTML = '<span class="tag-empty-hint">Henüz etiket yok.</span>';
        return;
    }
    state.allTags.forEach(tag => {
        const chip = document.createElement('button');
        chip.className = 'tag-chip' + (state.activeTags.includes(tag.name) ? ' active' : '');
        chip.textContent = `${tag.name} (${tag.count})`;
        chip.addEventListener('click', () => toggleTagFilter(tag.name));
        elements.tagChips.appendChild(chip);
    });
}

function toggleTagFilter(tagName) {
    const idx = state.activeTags.indexOf(tagName);
    if (idx >= 0) state.activeTags.splice(idx, 1);
    else state.activeTags.push(tagName);
    state.currentPage = 1;
    elements.clearTagsBtn.classList.toggle('hidden', state.activeTags.length === 0);
    renderTagChips();
    loadImages();
}

function clearTagFilter() {
    state.activeTags = [];
    state.currentPage = 1;
    elements.clearTagsBtn.classList.add('hidden');
    renderTagChips();
    loadImages();
}

function toggleTagBar() {
    elements.tagBar.classList.toggle('hidden');
    if (!elements.tagBar.classList.contains('hidden')) loadAllTags();
}

// ========== File Type Filter ==========
function toggleFileTypeBar() {
    elements.fileTypeBar.classList.toggle('hidden');
}

function clearFileTypeFilter() {
    state.activeFileTypes = [];
    state.currentPage = 1;
    elements.clearFileTypesBtn.classList.add('hidden');
    elements.fileTypeBar.querySelectorAll('.ft-chip').forEach(c => c.classList.remove('active'));
    loadImages();
}

// ========== EXIF Panel ==========
async function toggleExifPanel() {
    const panel = document.getElementById('exifPanel');
    if (!panel.classList.contains('hidden')) { panel.classList.add('hidden'); return; }

    const imagePath = state.images[state.currentImageIndex];
    if (!imagePath) return;

    try {
        const res = await fetch(`${API_BASE}/metadata/${encodeURIComponent(imagePath)}`);
        const data = await res.json();
        const content = document.getElementById('exifContent');

        const rows = [
            ['Dosya', data.filename],
            ['Boyut', formatBytes(data.size)],
            ['Değiştirilme', new Date(data.modified * 1000).toLocaleString('tr-TR')],
        ];

        if (data.exif) {
            const exifMap = {
                'Exif.Photo.FocalLength': 'Odak',
                'Exif.Photo.FNumber': 'Diyafram',
                'Exif.Photo.ISOSpeedRatings': 'ISO',
                'Exif.Photo.ExposureTime': 'Perde',
                'Exif.Image.Make': 'Marka',
                'Exif.Image.Model': 'Model',
            };
            for (const [key, label] of Object.entries(exifMap)) {
                if (data.exif[key]) rows.push([label, data.exif[key]]);
            }
        }

        content.innerHTML = rows.map(([k, v]) =>
            `<div class="exif-row"><span class="exif-label">${k}</span><span class="exif-value">${v ?? '—'}</span></div>`
        ).join('');

        // Etiket bölümü
        const tagsSection = document.createElement('div');
        tagsSection.className = 'exif-tags-section';
        tagsSection.innerHTML = `
            <div class="exif-tags-label">Etiketler</div>
            <div class="exif-tag-chips" id="exifTagChips"></div>
            <div class="exif-tag-input-row">
                <input class="exif-tag-input" id="exifTagInput" placeholder="Etiket ekle..." maxlength="32">
                <button class="exif-tag-add-btn" id="exifTagAddBtn">+ Ekle</button>
            </div>
        `;
        content.appendChild(tagsSection);

        renderExifTags(data.tags || [], imagePath);

        document.getElementById('exifTagAddBtn').addEventListener('click', () => addExifTag(imagePath));
        document.getElementById('exifTagInput').addEventListener('keydown', e => {
            if (e.key === 'Enter') addExifTag(imagePath);
        });

        // Note bölümü
        const noteTextarea = document.getElementById('noteTextarea');
        const saveNoteBtn = document.getElementById('saveNoteBtn');
        noteTextarea.value = '';
        try {
            const noteRes = await fetch(`${API_BASE}/note/${encodeURIComponent(imagePath)}`);
            const noteData = await noteRes.json();
            noteTextarea.value = noteData.note || '';
        } catch { /* not yüklenemedi */ }

        // Önceki event listener'ı temizle
        const newSaveBtn = saveNoteBtn.cloneNode(true);
        saveNoteBtn.parentNode.replaceChild(newSaveBtn, saveNoteBtn);
        newSaveBtn.addEventListener('click', async () => {
            try {
                await fetch(`${API_BASE}/note/${encodeURIComponent(imagePath)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: noteTextarea.value })
                });
                showToast('Not kaydedildi', 'success');
            } catch { showToast('Not kaydedilemedi', 'error'); }
        });

        panel.classList.remove('hidden');
    } catch { showToast('Metadata alınamadı', 'error'); }
}

function renderExifTags(tags, imagePath) {
    const container = document.getElementById('exifTagChips');
    if (!container) return;
    container.innerHTML = tags.length === 0
        ? '<span class="tag-empty-hint" style="font-size:11px">Etiket yok</span>'
        : '';
    tags.forEach(tag => {
        const chip = document.createElement('span');
        chip.className = 'exif-tag';
        chip.innerHTML = `${tag} <button class="exif-tag-remove" data-tag="${tag}">✕</button>`;
        chip.querySelector('.exif-tag-remove').addEventListener('click', async () => {
            await fetch(`${API_BASE}/tag/${encodeURIComponent(imagePath)}/${encodeURIComponent(tag)}`, { method: 'DELETE' });
            const updatedTags = tags.filter(t => t !== tag);
            renderExifTags(updatedTags, imagePath);
            if (!elements.tagBar.classList.contains('hidden')) loadAllTags();
        });
        container.appendChild(chip);
    });
}

async function addExifTag(imagePath) {
    const input = document.getElementById('exifTagInput');
    const tag = input.value.trim();
    if (!tag) return;
    try {
        const res = await fetch(`${API_BASE}/tag/${encodeURIComponent(imagePath)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tag })
        });
        if (!res.ok) { showToast('Etiket eklenemedi', 'error'); return; }
        const d = await res.json();
        input.value = '';
        // Mevcut chip listesini güncelle
        const container = document.getElementById('exifTagChips');
        const currentTags = [...container.querySelectorAll('.exif-tag')].map(el =>
            el.textContent.replace('✕', '').trim()
        );
        if (!currentTags.includes(d.tag)) {
            renderExifTags([...currentTags, d.tag], imagePath);
        }
        if (!elements.tagBar.classList.contains('hidden')) loadAllTags();
    } catch { showToast('Hata oluştu', 'error'); }
}

window.toggleExifPanel = toggleExifPanel;

// ========== Watchdog SSE ==========
let watchEventSource = null;

function startWatcher() {
    if (watchEventSource) watchEventSource.close();
    watchEventSource = new EventSource(`${API_BASE}/watch`);
    watchEventSource.onmessage = debounce(e => {
        const ev = JSON.parse(e.data);
        if (ev.type !== 'ping' && ev.type !== 'no_directory') {
            showToast('Klasör değişti, yenileniyor...', 'info', 2000);
            refreshGallery();
        }
    }, 1000);
}

function stopWatcher() {
    if (watchEventSource) { watchEventSource.close(); watchEventSource = null; }
}

// ========== Search & Filters ==========
function handleSearch(event) {
    state.searchQuery = event.target.value;
    state.currentPage = 1;
    loadImages();
}

function handleSubfoldersToggle(event) {
    state.includeSubfolders = event.target.checked;
    state.currentPage = 1;
    loadImages();
}

// ========== Thumbnail Generation ==========
async function generateThumbnails() {
    try { await fetch(`${API_BASE}/generate-thumbnails`, { method: 'POST' }); }
    catch (e) { console.error('Thumbnail oluşturma hatası:', e); }
}

// ========== Refresh ==========
function refreshGallery() { loadImages(); }

// ========== Utilities ==========
function showLoading() { elements.loading.classList.remove('hidden'); }
function hideLoading() { elements.loading.classList.add('hidden'); }

function formatBytes(b) {
    if (b < 1024) return b + ' B';
    if (b < 1048576) return (b / 1024).toFixed(1) + ' KB';
    return (b / 1048576).toFixed(1) + ' MB';
}

function debounce(func, delay) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}

// ========== Fav Filter ==========
function toggleFavsFilter() {
    state.showOnlyFavs = !state.showOnlyFavs;
    localStorage.setItem('galleryFavsOnly', state.showOnlyFavs);
    state.currentPage = 1;
    applyFavsFilterUI();
    loadImages();
}

function applyFavsFilterUI() {
    if (state.showOnlyFavs) {
        elements.favsFilterBtn.classList.add('active');
        elements.favsFilterBtn.title = 'Tüm Resimler (F)';
    } else {
        elements.favsFilterBtn.classList.remove('active');
        elements.favsFilterBtn.title = 'Sadece Favoriler (F)';
    }
}

window.toggleFavsFilter = toggleFavsFilter;

// ========== Theme ==========
function applyTheme(theme) {
    document.body.classList.toggle('light', theme === 'light');
    elements.themeToggleBtn.textContent = theme === 'light' ? '🌙' : '☀️';
}

// ========== Select Mode ==========
function toggleSelectMode() {
    if (state.selectMode) { exitSelectMode(); return; }
    state.selectMode = true;
    state.selectedPaths = new Set();
    elements.selectModeBtn.classList.add('active');
    elements.batchBar.classList.remove('hidden');
    renderGallery();
}

function exitSelectMode() {
    state.selectMode = false;
    state.selectedPaths = new Set();
    elements.selectModeBtn.classList.remove('active');
    elements.batchBar.classList.add('hidden');
    renderGallery();
}

function toggleItemSelection(item, imagePath) {
    if (state.selectedPaths.has(imagePath)) {
        state.selectedPaths.delete(imagePath);
        item.classList.remove('selected');
    } else {
        state.selectedPaths.add(imagePath);
        item.classList.add('selected');
    }
    elements.batchCount.textContent = `${state.selectedPaths.size} seçili`;
    elements.batchCompareBtn.disabled = state.selectedPaths.size !== 2;
}

function selectAllCurrentPage() {
    state.images.forEach(p => state.selectedPaths.add(p));
    elements.batchCount.textContent = `${state.selectedPaths.size} seçili`;
    elements.batchCompareBtn.disabled = state.selectedPaths.size !== 2;
    document.querySelectorAll('.gallery-item.selectable').forEach(el => el.classList.add('selected'));
}

async function batchDelete() {
    if (!state.selectedPaths.size) return;
    if (!confirm(`${state.selectedPaths.size} resim çöp kutusuna taşınsın mı?`)) return;
    try {
        const res = await fetch(`${API_BASE}/batch/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths: [...state.selectedPaths] })
        });
        const d = await res.json();
        showToast(`${d.count} resim silindi`, 'success');
        exitSelectMode();
        await loadImages();
        updateTrashCount();
    } catch { showToast('Toplu silme hatası', 'error'); }
}

async function batchFavorite(action) {
    if (!state.selectedPaths.size) return;
    try {
        const res = await fetch(`${API_BASE}/batch/favorite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths: [...state.selectedPaths], action })
        });
        const d = await res.json();
        showToast(`${d.count} resim ${action === 'add' ? 'favorilere eklendi' : 'favorilerden çıkarıldı'}`, 'success');
        await loadFavorites();
        renderGallery();
    } catch { showToast('Hata oluştu', 'error'); }
}

async function batchTag() {
    const tag = elements.batchTagInput.value.trim();
    if (!tag || !state.selectedPaths.size) return;
    try {
        const res = await fetch(`${API_BASE}/batch/tag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths: [...state.selectedPaths], tag })
        });
        const d = await res.json();
        elements.batchTagInput.value = '';
        elements.batchTagModal.classList.add('hidden');
        showToast(`${d.count} resime "${d.tag}" etiketi eklendi`, 'success');
        if (!elements.tagBar.classList.contains('hidden')) loadAllTags();
    } catch { showToast('Hata oluştu', 'error'); }
}

// ========== Duplicate Detection ==========
async function openDuplicateModal() {
    elements.duplicateModal.classList.remove('hidden');
    elements.duplicateContent.innerHTML = `<div class="duplicate-scanning"><div class="spinner"></div><p>Taranıyor...</p></div>`;
    elements.duplicateSummary.textContent = '';

    try {
        const res = await fetch(`${API_BASE}/duplicates`);
        const data = await res.json();

        if (!data.groups || data.groups.length === 0) {
            elements.duplicateContent.innerHTML = '<p style="padding:24px;text-align:center;color:var(--text-secondary)">Benzer resim bulunamadı.</p>';
            elements.duplicateSummary.textContent = 'Temiz!';
            return;
        }

        elements.duplicateSummary.textContent = `${data.groups.length} grup, toplam ${data.count} resim`;

        elements.duplicateContent.innerHTML = '';
        data.groups.forEach((group, gi) => {
            const groupEl = document.createElement('div');
            groupEl.className = 'dup-group';
            groupEl.innerHTML = `<div class="dup-group-header">Grup ${gi + 1} — ${group.length} benzer resim</div>`;
            const grid = document.createElement('div');
            grid.className = 'dup-grid';
            group.forEach(item => {
                const card = document.createElement('div');
                card.className = 'dup-card';
                card.innerHTML = `
                    <img src="${API_BASE}/image/${encodeURIComponent(item.path)}?thumb=true&w=160" loading="lazy" alt="">
                    <div class="dup-name" title="${item.path}">${item.path.split('/').pop()}</div>
                    <div class="dup-size">${formatBytes(item.size)}</div>
                    <button class="btn-icon btn-danger dup-del-btn" data-path="${item.path}">🗑️ Sil</button>
                `;
                card.querySelector('.dup-del-btn').addEventListener('click', async (e) => {
                    const path = e.currentTarget.dataset.path;
                    await fetch(`${API_BASE}/image/${encodeURIComponent(path)}`, { method: 'DELETE' });
                    card.style.opacity = '0.3';
                    card.style.pointerEvents = 'none';
                    showToast('Çöp kutusuna taşındı', 'success');
                    updateTrashCount();
                });
                grid.appendChild(card);
            });
            groupEl.appendChild(grid);
            elements.duplicateContent.appendChild(groupEl);
        });
    } catch (err) {
        elements.duplicateContent.innerHTML = `<p style="padding:24px;text-align:center;color:#f85149">Hata: ${err.message}</p>`;
    }
}

// ========== Faz 5.4 — Watermark / Export ==========

function openWatermarkModal() {
    if (!state.selectedPaths.size) return;
    // Reset state
    elements.wmEnable.checked = false;
    elements.wmOptions.classList.add('hidden');
    elements.wmText.value = 'GalleryWeb';
    elements.wmPosition.value = 'bottom-right';
    elements.wmOpacity.value = 60;
    elements.wmOpacityVal.textContent = '60%';
    elements.wmSize.value = 4;
    elements.wmSizeVal.textContent = '4%';
    elements.wmExportStatus.textContent = '';
    elements.wmExportBtn.disabled = false;
    elements.watermarkModal.classList.remove('hidden');
}

function closeWatermarkModal() {
    elements.watermarkModal.classList.add('hidden');
}

async function executeWatermarkExport() {
    if (!state.selectedPaths.size) return;
    const watermarkConfig = elements.wmEnable.checked ? {
        text:     elements.wmText.value.trim() || 'GalleryWeb',
        position: elements.wmPosition.value,
        opacity:  parseFloat(elements.wmOpacity.value) / 100,
        size:     parseFloat(elements.wmSize.value) / 100
    } : null;

    elements.wmExportBtn.disabled = true;
    elements.wmExportStatus.textContent = 'Zip hazırlanıyor...';

    try {
        const body = { paths: [...state.selectedPaths] };
        if (watermarkConfig) body.watermark = watermarkConfig;

        const res = await fetch(`${API_BASE}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) {
            elements.wmExportStatus.textContent = 'Hata oluştu';
            elements.wmExportBtn.disabled = false;
            return;
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'gallery-export.zip';
        a.click();
        URL.revokeObjectURL(url);
        closeWatermarkModal();
        showToast(`${state.selectedPaths.size} dosya indirildi`, 'success');
    } catch {
        elements.wmExportStatus.textContent = 'Hata oluştu';
        elements.wmExportBtn.disabled = false;
    }
}

// ========== PWA ==========
let _pwaInstallPrompt = null;

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => {
        console.warn('SW registration failed:', err);
    });
}

window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    _pwaInstallPrompt = e;
    const btn = document.getElementById('pwaInstallBtn');
    if (btn) btn.classList.remove('hidden');
});

window.addEventListener('appinstalled', () => {
    const btn = document.getElementById('pwaInstallBtn');
    if (btn) btn.classList.add('hidden');
    _pwaInstallPrompt = null;
    showToast('Uygulama yüklendi!', 'success');
});

document.getElementById('pwaInstallBtn')?.addEventListener('click', async () => {
    if (!_pwaInstallPrompt) return;
    _pwaInstallPrompt.prompt();
    const { outcome } = await _pwaInstallPrompt.userChoice;
    if (outcome === 'accepted') _pwaInstallPrompt = null;
});

// ========== Faz 5.3 — Batch EXIF Editing ==========

function openBatchExifModal() {
    if (state.selectedPaths.size === 0) {
        showToast('Önce resim seçin', 'warning');
        return;
    }
    // Clear inputs
    ['exifArtist', 'exifCopyright', 'exifDescription', 'exifDatetime'].forEach(id => {
        document.getElementById(id).value = '';
    });
    document.getElementById('exifEditStatus').textContent =
        `${state.selectedPaths.size} resim seçili`;
    elements.batchExifModal.classList.remove('hidden');
}

function closeBatchExifModal() {
    elements.batchExifModal.classList.add('hidden');
}

async function executeBatchExif() {
    const fields = {};
    const artist      = document.getElementById('exifArtist').value.trim();
    const copyright   = document.getElementById('exifCopyright').value.trim();
    const description = document.getElementById('exifDescription').value.trim();
    const datetime    = document.getElementById('exifDatetime').value.trim();

    if (artist)      fields.artist      = artist;
    if (copyright)   fields.copyright   = copyright;
    if (description) fields.description = description;
    if (datetime)    fields.datetime    = datetime;

    if (Object.keys(fields).length === 0) {
        showToast('En az bir alan doldurun', 'warning');
        return;
    }

    const paths = [...state.selectedPaths];
    const statusEl = document.getElementById('exifEditStatus');
    statusEl.textContent = 'İşleniyor...';
    elements.batchExifConfirm.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/batch/exif`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ paths, fields })
        });
        const data = await res.json();

        if (!res.ok) {
            showToast(data.detail || 'EXIF yazma hatası', 'error');
            statusEl.textContent = 'Hata oluştu';
            return;
        }

        const failed = data.results.filter(r => !r.ok);
        if (failed.length === 0) {
            showToast(`${data.success_count} resme EXIF yazıldı`, 'success');
            closeBatchExifModal();
        } else {
            showToast(`${data.success_count}/${data.total} başarılı, ${failed.length} hata`, 'warning', 5000);
            statusEl.textContent = `Hatalar: ${failed.map(f => f.path.split('/').pop()).join(', ')}`;
        }
    } catch {
        showToast('Bağlantı hatası', 'error');
        statusEl.textContent = 'Bağlantı hatası';
    } finally {
        elements.batchExifConfirm.disabled = false;
    }
}

// ========== Tree Panel ==========
(function () {
    const panel     = document.getElementById('treePanel');
    const root      = document.getElementById('treeRoot');
    const toggleBtn = document.getElementById('treeToggleBtn');
    const closeBtn  = document.getElementById('treePanelClose');

    let treeLoaded = false;

    function openTree() {
        panel.classList.add('open');
        document.body.classList.add('tree-open');
        toggleBtn.classList.add('active');
        localStorage.setItem('galleryTree', '1');
        if (!treeLoaded) {
            treeLoaded = true;
            const startPath = state.currentDirectory
                ? state.currentDirectory.split('/').slice(0, -1).join('/') || '/'
                : '~';
            loadTreeChildren(startPath, root, 0);
        }
    }

    function closeTree() {
        panel.classList.remove('open');
        document.body.classList.remove('tree-open');
        toggleBtn.classList.remove('active');
        localStorage.setItem('galleryTree', '0');
    }

    function toggleTree() {
        panel.classList.contains('open') ? closeTree() : openTree();
    }

    async function loadTreeChildren(path, container, depth) {
        container.innerHTML = '<div class="tree-loading">Yükleniyor...</div>';
        try {
            const res = await fetch(`${API_BASE}/browse?path=${encodeURIComponent(path)}`);
            if (!res.ok) { container.innerHTML = ''; return; }
            const data = await res.json();
            container.innerHTML = '';
            const dirs = data.entries.filter(e => e.is_dir);
            if (dirs.length === 0) {
                container.innerHTML = '<div class="tree-loading">Klasör yok</div>';
                return;
            }
            for (const entry of dirs) {
                container.appendChild(buildTreeNode(entry, depth));
            }
        } catch {
            container.innerHTML = '';
        }
    }

    function buildTreeNode(entry, depth) {
        const node = document.createElement('div');
        node.className = 'tree-node';

        const row = document.createElement('div');
        row.className = 'tree-row';
        row.style.paddingLeft = (6 + depth * 14) + 'px';

        // Mark active if this dir is currently selected
        const isActive = state.currentDirectories.includes(entry.path);
        if (isActive) row.classList.add('active');

        const arrow = document.createElement('span');
        arrow.className = 'tree-arrow';
        arrow.textContent = '›';

        const icon = document.createElement('span');
        icon.className = 'tree-icon';
        icon.textContent = isActive ? '📂' : '📁';

        const name = document.createElement('span');
        name.className = 'tree-name';
        name.textContent = entry.name;
        name.title = entry.path;

        row.appendChild(arrow);
        row.appendChild(icon);
        row.appendChild(name);
        node.appendChild(row);

        const children = document.createElement('div');
        children.className = 'tree-children';
        node.appendChild(children);

        let loaded = false;
        let expanded = false;

        function doExpand() {
            expanded = true;
            arrow.classList.add('expanded');
            children.classList.add('open');
            if (!loaded) {
                loaded = true;
                loadTreeChildren(entry.path, children, depth + 1);
            }
        }

        function doCollapse() {
            expanded = false;
            arrow.classList.remove('expanded');
            children.classList.remove('open');
        }

        arrow.addEventListener('click', e => {
            e.stopPropagation();
            expanded ? doCollapse() : doExpand();
        });

        name.addEventListener('click', async e => {
            e.stopPropagation();
            // Set as gallery directory
            await treeSetDir(entry.path, row, icon);
            if (!expanded) doExpand();
        });

        return node;
    }

    async function treeSetDir(path, row, icon) {
        try {
            const res = await fetch(`${API_BASE}/set-directory`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path })
            });
            if (!res.ok) { showToast('Klasör açılamadı', 'error'); return; }
            const data = await res.json();
            state.currentDirectory = data.path;
            state.currentDirectories = data.directories || [data.path];
            state.currentPage = 1;
            localStorage.setItem('galleryPath', data.path);
            renderDirChips();
            // Update active highlights across the tree
            panel.querySelectorAll('.tree-row.active').forEach(r => {
                r.classList.remove('active');
                r.querySelector('.tree-icon').textContent = '📁';
            });
            row.classList.add('active');
            icon.textContent = '📂';
            await loadFavorites();
            await loadRatings();
            await loadImages();
            startWatcher();
            updateTrashCount();
            updateBookmarkBtnState();
        } catch { showToast('Bağlantı hatası', 'error'); }
    }

    // Keyboard shortcut T
    document.addEventListener('keydown', e => {
        if (e.key === 't' || e.key === 'T') {
            const tag = document.activeElement.tagName;
            if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
            toggleTree();
        }
    });

    toggleBtn.addEventListener('click', toggleTree);
    closeBtn.addEventListener('click', closeTree);

    // Restore state from localStorage
    if (localStorage.getItem('galleryTree') === '1') {
        openTree();
    }
})();

// ========== Start ==========
init();
