---
agent: test-arayuz
project: Galleryweb
date: 2026-05-17
status: completed
severity_summary:
  critical: 0
  high: 1
  medium: 3
  low: 2
  info: 1
---

# Test Raporu — UI & Frontend — Galleryweb

## Test Kapsamı
- **Taranan frontend dizinleri:** `/frontend/js/` (3 JS dosyası), `/frontend/css/` (1 CSS dosyası), `/frontend/index.html`
- **Framework:** Vanilla JavaScript + HTML5 + CSS3
- **Toplam JS dosya:** 3 (gallery.js ~2892 satır, keybinds.js ~179 satır, slideshow.js ~95 satır)
- **Toplam bileşen dosyası:** 1 HTML
- **Test türü:** Runtime hatalar, event listener sızıntısı, loading/error state, localStorage güvenliği, CSS sorunları, erişilebilirlik

## Bulgular

### [UI-F001] Event Listener Sızıntısı — Dinamik Album Listesi (Tekrar-Bağlama)
- **Şiddet:** HIGH
- **Konum:** `frontend/js/gallery.js:1076-1096`
- **Kategori:** Event Listener Leak
- **Açıklama:** `renderAlbumsList()` fonksiyonu her çağrıldığında (loadImages, albüm seçimi değiştiğinde) tüm `.album-item` ve `.album-del-btn` elementlerine yeni event listener'ları ekler. Eski listener'lar temizlenmez. 100+ albüm case'inde bellek sızıntısına yol açabilir.
- **Kanıt:**
  ```javascript
  // Satır 1076-1096
  elements.albumsList.innerHTML = state.albums.map(a => `...`).join('');
  
  // Hemen sonra yeni listener'lar eklenir — eski listener'lar attached kalır
  elements.albumsList.querySelectorAll('.album-item').forEach(item => {
      item.addEventListener('click', e => { ... });
  });
  elements.albumsList.querySelectorAll('.album-del-btn').forEach(btn => {
      btn.addEventListener('click', async () => { ... });
  });
  ```
- **Nasıl Tetiklenir:** 1) İlk kez albüm yükle 2) Albümü seç (state değişir) 3) loadImages() → renderAlbumsList() tekrar çalışır → yeni listener'lar eklenir fakat eski listener'lar silinmez
- **Olası Etki:** Albüm seçimi her yapıldığında handler'lar çoğalır. 20 seçim sonrası single click 20x tetiklenebilir.
- **Önerilen Düzeltme:** Event delegation kullan veya innerHTML öncesi `removeEventListener()` ile eski listener'ları temizle. Alternatif: `.addEventListener()` yerine `.onclick` / data attribute tabanlı event handling.

---

### [UI-F002] Lighthouse — Boş Alt Metin (alt="")
- **Şiddet:** MEDIUM
- **Konum:** `frontend/index.html:234, 235, 457, 481, 482`
- **Kategori:** Erişilebilirlik (A11y)
- **Açıklama:** Dinamik resimleri gösteren `<img>` elementleri `alt=""` (boş) veya tamamen `alt` olmadan tanımlanmıştır. Resim yolları JavaScript'te set edilse bile, ekran okuyucular resim açıklaması alamaz.
- **Kanıt:**
  ```html
  <img id="lightboxImage" class="lightbox-image" src="" alt="">
  <video id="lightboxVideo" class="lightboxImage hidden" controls></video>
  <!-- Map popup içinde -->
  <img src="${API_BASE}/image/..." style="..." loading="lazy">
  <!-- Karşılaştırma paneli -->
  <img id="compareImgLeft" src="" alt="">
  <img id="compareImgRight" src="" alt="">
  <!-- QR Modal -->
  <img id="qrImage" src="" alt="QR Kod">
  ```
- **Nasıl Tetiklenir:** Ekran okuyucu (NVDA, JAWS) ile lightbox açılsa veya resimler yüklense
- **Olası Etki:** Engelli kullanıcılar resim içeriğini anlayamaz
- **Önerilen Düzeltme:** JavaScript'te `alt` attribute'ü dinamik olarak set et:
  ```javascript
  lightboxImage.alt = `Resim: ${imageName}`;
  ```

---

### [UI-F003] Dinamik innerHTML + Event Listener Ek-Yükleme — Kitap Işaretleri
- **Şiddet:** MEDIUM
- **Konum:** `frontend/js/gallery.js:969-984`
- **Kategori:** Event Listener Leak + Performance
- **Açıklama:** `renderBookmarkDropdown()` her bookmark dropdown açılışında tüm `.bookmark-item`'lere click handler'ı ekler. Kapalı/açılan state'te sızıntı potansiyeli.
- **Kanıt:**
  ```javascript
  // renderBookmarkDropdown()
  dd.innerHTML = ''; // Önceki listener'lar detach edilir
  state.bookmarks.forEach(b => {
      const item = document.createElement('div');
      item.className = 'bookmark-item';
      item.innerHTML = `...`;
      item.addEventListener('click', () => { ... }); // Her açılışta yeniden
      dd.appendChild(item);
  });
  ```
- **Nasıl Tetiklenir:** Bookmark dropdown 10+ kez açılıp kapandığında
- **Olası Etki:** Sayfada uzun süre kalınan kullanıcılarda bellek tüketimi artabilir
- **Önerilen Düzeltme:** Event delegation kullan (`dd.addEventListener()`) veya listener'ları template ile yönet

---

### [UI-F004] Loading State Eksikliği — Map View
- **Şiddet:** MEDIUM
- **Konum:** `frontend/js/gallery.js:1390-1441`
- **Kategori:** Loading State
- **Açıklama:** `openMapView()` asenkron fetch yapılırken, map modal hemen açılıyor ama yükleme durumunda loading spinner veya UI lock yok. Kullanıcı map yüklenmeden modala tıklayabilir (aynı anda 2. fetch başlatabilir).
- **Kanıt:**
  ```javascript
  async function openMapView() {
      elements.mapModal.classList.remove('hidden'); // Hemen açılır
      // ... map init ...
      // RACE CONDITION: Bu sırada user başka harita butonuna tıklayabilir
      const res = await fetch(`${API_BASE}/images/map`);
  }
  ```
- **Nasıl Tetiklenir:** 1) Harita butonuna tıkla 2) Yüklenmesi bitmeden hızlıca tekrar tıkla
- **Olası Etki:** Duplicate fetch istekleri, eski data ile yeni data çakışması
- **Önerilen Düzeltme:** Modal açmadan önce loading state koy, fetch bitene kadar button disable et:
  ```javascript
  async function openMapView() {
      if (elements.mapModal.classList.contains('loading')) return; // Prevent duplicate
      elements.mapModal.classList.add('loading');
      // ... fetch ...
      elements.mapModal.classList.remove('loading');
  }
  ```

---

### [UI-F005] Keydown Listener — Kapanmaz
- **Şiddet:** LOW
- **Konum:** `frontend/js/keybinds.js:3-21`
- **Kategori:** Event Listener Management
- **Açıklama:** Global `document.addEventListener('keydown')` hiçbir cleanup mekanizması olmadan ekleniyor. HTML içinde tanımlanan 3 script dosyası loading order'ına bağlı olarak Multiple listener attach edebilir (çünkü inline script reload yapmıyor, duplicate binding).
- **Kanıt:**
  ```javascript
  // frontend/js/keybinds.js
  document.addEventListener('keydown', (e) => { ... });
  // Hiçbir cleanup yok. Sayfa hot-reload veya SPA gibi davranırsa duplicate listener
  ```
- **Nasıl Tetiklenir:** SPA-style component reload (varsa, örn. DevTools ile manual hotload)
- **Olası Etki:** Aynı key birden çok kez tetiklenebilir
- **Önerilen Düzeltme:** Conditional listener registration (var global flag check) veya removeEventListener

---

### [UI-F006] Z-Index Chaos Riski
- **Şiddet:** LOW
- **Konum:** `frontend/css/style.css`: 51, 259, 912, 932, 1001, 1039, 1313, 1332, 1351, 1847, 1891, 1936, 2018, 2074, 2084, 2173, 2212, 2222, 2351, 2468, 2495, 2512, 2618, 2654
- **Kategori:** CSS
- **Açıklama:** Z-index değerleri tutarsız: header=100, modal-backdrop=2000, slideshow-indicator=1001, lightbox kontrolü=1002 ama albums-panel arka planı hiç set edilmemiş (z-index yok).
- **Kanıt:**
  ```css
  .header { z-index: 100; }
  .modal-backdrop { z-index: 2000; } /* Çok yüksek */
  .lightbox-nav { z-index: 1002; }
  .albums-panel { /* z-index: none */ } /* Backdrop var ama panel'ın kendisinde yok */
  ```
- **Nasıl Tetiklenir:** Modal + albums panel + header overlap
- **Olası Etki:** Albums panel modal arkasında kaybolabilir
- **Önerilen Düzeltme:** Z-index stratejisi: header=10, modals=100, dropdowns=50 (relative context içinde)

---

### [UI-F007] localStorage — Sensitif Veri Değil Ama Bias Riski
- **Şiddet:** INFO
- **Konum:** `frontend/js/gallery.js` satırlar 21-29, 332, 345, 487, 752, 784, 976, 1466, 2394, 2734, 2748, 2855
- **Kategori:** Storage Management
- **Açıklama:** localStorage'da şu değerler kaydediliyor: `galleryViewMode`, `galleryTheme`, `galleryPath`, `galleryFavsOnly`, `galleryAutoplay`, `slideshowInterval`. Güvenlik sorunu yok (sensitif veri yok) ancak cross-site data leakage mümkün (XSS varsa).
- **Kanıt:**
  ```javascript
  localStorage.setItem('galleryPath', data.path); // User file paths
  localStorage.setItem('galleryFavsOnly', state.showOnlyFavs);
  state.viewMode = localStorage.getItem('galleryViewMode') || 'thumbnail';
  ```
- **Olası Etki:** Minimal — UI preference sadece
- **Tavsiye:** XSS filtreleme devam et, localStorage verileri sanitize etme ihtiyacı yok

---

### [UI-F008] !important Kötüye Kullanımı
- **Şiddet:** INFO
- **Konum:** `frontend/css/style.css:30`
- **Kategori:** CSS
- **Açıklama:** `.hidden { display: none !important; }` — tek !important kullanımı, genellikle kabul görebilir pattern. CSS specificity konuşu düşük risk.
- **Kanıt:**
  ```css
  .hidden { display: none !important; }
  ```
- **Tavsiye:** Kabul edilebilir kalıp, risk yok

---

## İstatistikler
| CRITICAL | HIGH | MEDIUM | LOW | INFO | TOPLAM |
|----------|------|--------|-----|------|--------|
| 0 | 1 | 3 | 2 | 1 | 7 |

---

## Değerlendirme

**Galleryweb** frontend kodu temiz ve çoğunlukla iyi yönetilmiş olsa da, **HIGH severity event listener sızıntısı** albüm listesi rendering'inde kritik bulgutur. Dinamik HTML + event binding pattern'ı yinelenmiş innerHTML bağlamında listener'ları çoğaltuyor.

**Orta seviye sorunlar:**
1. A11y — img alt metinleri eksik (erişilebilirlik)
2. Loading state — Map view'da race condition riski
3. Bookmark dropdown — similar listener leak (hafif)

**Düşük seviye sorunlar:**
- Global keydown listener cleanup
- Z-index organization

**Tespit edilen sorunların çoğu "long-running session" senaryolarında ortaya çıkar** (100+ folder/album, sık-sık interaksiyon). Kısa session'larda sorunlar sezdirilemez.

---

## Önerilen İlk Adımlar (Öncelik Sırasına Göre)
1. **HIGH:** `renderAlbumsList()` → event delegation'a geçiş veya listener cache yönetimi
2. **MEDIUM:** Lightbox + map + QR img → dynamic alt text assignment
3. **MEDIUM:** `openMapView()` → loading state guard
4. **LOW:** keybinds global listener → cleanup pattern
5. **INFO:** Z-index strategy review (opsiyonel)

---

## Kaynak
- `frontend/js/gallery.js` (~2892 satır)
- `frontend/js/keybinds.js` (~179 satır)
- `frontend/js/slideshow.js` (~95 satır)
- `frontend/css/style.css` (~2654 satır)
- `frontend/index.html` (565 satır)

**Raporlama Tarihi:** 2026-05-17
**Ajan:** test-arayuz (UI & Frontend)
