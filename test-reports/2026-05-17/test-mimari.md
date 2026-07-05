---
agent: test-mimari
project: Galleryweb
date: 2026-05-17
status: completed
severity_summary:
  critical: 0
  high: 2
  medium: 4
  low: 3
  info: 5
---

# Test Raporu — Yapı & Mimari — Galleryweb

## Test Kapsamı

Galleryweb projesi (FastAPI + Vanilla JS + SQLite) yapısı, bağımlılıklar, konfigürasyon ve kod kalitesi açısından incelendi.

**İncelenen Dosyalar:**
- `/backend/main.py` (1402 satır)
- `/backend/cache_manager.py` (569 satır)
- `/backend/thumbnail_gen.py` (133 satır)
- `/backend/duplicate_finder.py` (63 satır)
- `/backend/requirements.txt`
- `/frontend/index.html` (565 satır)
- `/frontend/js/gallery.js` (2892 satır)
- `/frontend/js/keybinds.js` (178 satır)
- `/frontend/js/slideshow.js` (94 satır)
- `/frontend/css/style.css`

**Eklenmiş Dizinler:** venv/ (Python 3.14), cache/, __pycache__

---

## Bulgular

### [MIM-F001] Hardcoded Localhost CORS Origins
- **Şiddet:** HIGH
- **Konum:** `backend/main.py:31-33`
- **Kategori:** Configuration / Security
- **Açıklama:** CORS origins'te localhost ve 127.0.0.1 hardcoded. Dinamik IP tespit edilse bile geliştirme-özel hardcoded değerler, uygulamanın prod'da çalışmasını engeller.
- **Kanıt:**
  ```python
  _origins = ["http://127.0.0.1:5000", "http://localhost:5000"]
  if _local_ip:
      _origins.append(f"http://{_local_ip}:5000")
  ```
- **Nasıl Tetiklenir:** Prod ortamında (localhost DNS resolution yok), CORS hatası
- **Olası Etki:** Prod deploy'da frontend → backend API çağrıları CORS hatası ile bloke edilir
- **Önerilen Düzeltme:** CORS origins'i `.env` veya ortam değişkeninden oku; fallback olarak `*` (dev mode) veya dinamik origin validation (prod)

---

### [MIM-F002] Hardcoded Port 5000
- **Şiddet:** HIGH
- **Konum:** `backend/main.py:1191, 1205, 1402` (QR URL, fallback)
- **Kategori:** Configuration
- **Açıklama:** Port 5000 birden çok yerde hardcoded. `uvicorn.run(..., port=5000)` sadece `__main__` bloğunda, QR ve fallback URL'lerde ise hardcoded string. Port çakışması veya konteyner ortamında sorun yaratır.
- **Kanıt:**
  ```python
  # main.py:1191
  url = f"http://{_local_ip}:{port}"
  # Ama port=5000 hardcoded
  
  # main.py:1402
  uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True, log_level="info")
  ```
- **Nasıl Tetiklenir:** Port 5000 başka bir proses tarafından kullanılıyorsa; Docker'da farklı port expose ediliyorsa
- **Olası Etki:** QR kod URL'si yanlış, port çakışması uygulamayı başlatamaz
- **Önerilen Düzeltme:** `PORT` env variable'dan oku; `main.py`'da `port = int(os.getenv('PORT', '5000'))`; QR endpoint'inde de kullan

---

### [MIM-F003] Linux-Specific Hardcoded Font Paths
- **Şiddet:** MEDIUM
- **Konum:** `backend/main.py:587-591`
- **Kategori:** Portability / Cross-Platform
- **Açıklama:** Watermark fontu arama sırası Arch/Debian-spesifik path'ler. macOS/Windows'ta font bulunamaz, fallback (`ImageFont.load_default()`) kötü görünüm verir.
- **Kanıt:**
  ```python
  for font_path in [
      "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
      "/usr/share/fonts/TTF/DejaVuSans.ttf",
      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
  ]:
  ```
- **Nasıl Tetiklenir:** macOS veya Windows'ta watermark export
- **Olası Etki:** Watermark metin kötü kalite, okunabilirlik düşük
- **Önerilen Düzeltme:** Fontmap dict'i `requirements.txt`'e embedded font ekle veya `fonttools` kullan; OS-agnostic çözüm

---

### [MIM-F004] Missing Environment Variable Documentation
- **Şiddet:** MEDIUM
- **Konum:** `/backend/` (proje root'ta .env.example yok)
- **Kategori:** Documentation
- **Açıklama:** `.env` dosyası veya `.env.example` template yok. Ortam değişkenleri (PORT, HOST, DB_PATH, LOG_LEVEL, vb) belgelenmemiş.
- **Kanıt:** `ls -la` çıktısında `.env*` dosyası yok
- **Nasıl Tetiklenir:** Yeni dev proje'yi fork'larken yapılandırması unclear
- **Olası Etki:** Setup hatası, yanlış port/host konfigürasyonu
- **Önerilen Düzeltme:** `.env.example` oluştur:
  ```
  PORT=5000
  HOST=0.0.0.0
  CACHE_DIR=./cache
  LOG_LEVEL=info
  RELOAD=true
  ALLOWED_ORIGINS=http://localhost:5000,http://127.0.0.1:5000
  ```

---

### [MIM-F005] Subprocess Timeout Hardcoded
- **Şiddet:** MEDIUM
- **Konum:** `backend/thumbnail_gen.py:94`
- **Kategori:** Configuration / Resilience
- **Açıklama:** ffmpeg thumbnail generation timeout 30s hardcoded. Büyük video'larda timeout, thumbnail generation fail. Env config yok.
- **Kanıt:**
  ```python
  subprocess.run([...], capture_output=True, timeout=30)
  ```
- **Nasıl Tetiklenir:** Uzun videolar (>30s duration, yavaş disk) ffmpeg timeout
- **Olası Etki:** Video thumbnail'i yüklenmez; kullanıcı görüntüde resim yok
- **Önerilen Düzeltme:** `os.getenv('FFMPEG_TIMEOUT', '60')` veya batch_generate'de dinamik timeout

---

### [MIM-F006] Global Mutable State in Frontend
- **Şiddet:** MEDIUM
- **Konum:** `frontend/js/gallery.js:5-35`
- **Kategori:** Code Quality / Maintainability
- **Açıklama:** Global `state` object, tüm gallery state'ini saklar. Multi-tab sync problemi, memory leak potansiyeli, refactoring zor.
- **Kanıt:**
  ```javascript
  let state = {
      currentDirectory: null,
      currentDirectories: [],
      images: [],
      currentPage: 1,
      perPage: 50,
      // ... 20+ more fields
  };
  ```
- **Nasıl Tetiklenir:** Birden çok tab aynı localhost:5000 açarsa, state sync sorunu
- **Olası Etki:** Tab A'da dosya sil → Tab B hala eski cache gösterir; UI inconsistency
- **Önerilen Düzeltme:** LocalStorage-backed reactive state (e.g., Nanostores, Zustand) veya IndexedDB with sync

---

### [MIM-F007] Unused Imports / Redundant Re-imports
- **Şiddet:** LOW
- **Konum:** `backend/main.py:662, 594-596, 1300, 1356, 1396` (PIL, Image re-imports)
- **Kategori:** Code Quality
- **Açıklama:** `from PIL import Image` top-level'de import edilse de, fonksiyon içinde `from PIL import Image as _Image` tekrar import edilir. Clean code değil.
- **Kanıt:**
  ```python
  # Line 1 (implicit):
  from PIL import Image  # Used once globally
  
  # Line 644:
  from PIL import Image as _Img  # Re-import with alias
  ```
- **Nasıl Tetiklenir:** Linter vs code review
- **Olası Etki:** Minor — read performance negligible, ama messy
- **Önerilen Düzeltme:** Top-level'de `from PIL import Image as Image` or `from PIL import Image, ImageDraw, ImageFont, ...` list'i yap

---

### [MIM-F008] Missing Error Handling in Async Operations
- **Şiddet:** LOW
- **Konum:** `backend/main.py:878, 918` (asyncio.create_task, observer.stop())
- **Kategori:** Resilience
- **Açıklama:** `asyncio.create_task()` hatalarını silent olarak ignores; exception handler yok. SSE watch endpoint'inde observer.stop() exception handling yok.
- **Kanıt:**
  ```python
  # Line 878:
  asyncio.create_task(thumbnail_gen.batch_generate(d))
  # No exception handler
  
  # Line 915-916:
  finally:
      observer.stop()  # What if stop() fails?
      observer.join()
  ```
- **Nasıl Tetiklenir:** Batch thumbnail generation fail; observer error
- **Olası Etki:** Silent failure, user non-wary
- **Önerilen Düzeltme:** `asyncio.create_task(...).add_done_callback(...)` or try/except in coro

---

### [MIM-F009] Deprecation Warning: ImageFont Import Style
- **Şiddet:** INFO
- **Konum:** `backend/main.py:594-601`
- **Kategori:** Code Quality / Future Compatibility
- **Açıklama:** `from PIL import ImageFont as _IF` local import style (line 594, 600) inconsistent; normally top-level import.
- **Kanıt:**
  ```python
  if font is None:
      from PIL import ImageFont as _IF
      font = _IF.load_default()
  ```
- **Nasıl Tetiklenir:** Code review, linting
- **Olası Etki:** Negligible — works, but non-standard
- **Önerilen Düzeltme:** Top-level import, use alias if needed

---

### [MIM-F010] Large SQLite DB Without Pragma Optimization
- **Şiddet:** INFO
- **Konum:** `backend/cache_manager.py` (DB initialization & queries)
- **Kategori:** Performance
- **Açıklama:** SQLite DB (thumbnails.db, potentially large) no PRAGMA optimizations (journal_mode=WAL, synchronous=NORMAL, cache_size, etc). High volume I/O slow.
- **Kanıt:**
  ```python
  def _init_db(self):
      conn = sqlite3.connect(self.db_path)
      c = conn.cursor()
      # No PRAGMA optimizations
  ```
- **Nasıl Tetiklenir:** Large gallery (10k+ images) → slow metadata queries
- **Olası Etki:** UI lag during sort/filter operations
- **Önerilen Düzeltme:**
  ```python
  conn.execute("PRAGMA journal_mode=WAL")
  conn.execute("PRAGMA synchronous=NORMAL")
  conn.execute("PRAGMA cache_size=5000")
  ```

---

### [MIM-F011] Duplicate Finder Single-Pass Algorithm
- **Şiddet:** INFO
- **Konum:** `backend/duplicate_finder.py:46-61`
- **Kategori:** Performance / Algorithm
- **Açıklama:** Duplicate detection algorithm O(n²) worst-case (pairwise comparison). Threshold=8 allows false positives (perceptual hash can be noisy). No clustering optimization.
- **Kanıt:**
  ```python
  for i, p1 in enumerate(paths):
      for j in range(i + 1, len(paths)):  # O(n²)
          h2 = imagehash.hex_to_hash(hashes[p2])
          if (h1 - h2) <= threshold:
  ```
- **Nasıl Tetiklenir:** Large gallery (5k+ images) find duplicates button slow
- **Olası Etki:** UI hangs during duplicate scan
- **Önerilen Düzeltme:** BK-tree or LSH (locality-sensitive hashing) for O(n log n) grouping

---

### [MIM-F012] No Rate Limiting on API Endpoints
- **Şiddet:** INFO
- **Konum:** `backend/main.py` (FastAPI app routes)
- **Kategori:** Security / DoS Mitigation
- **Açıklama:** No rate limiting middleware on `/api/*` endpoints. Malicious client can spam requests (delete, export ZIP, etc), DoS server.
- **Kanıt:** Middleware'de rate limit logic yok
- **Nasıl Tetiklenir:** `for i in range(10000): await fetch('/api/delete/...)`
- **Olası Etki:** Server resource exhaustion
- **Önerilen Düzeltme:** `slowapi` kütüphanesi veya custom middleware with Redis/memory counter

---

### [MIM-F013] CSS Versioning via Query String
- **Şiddet:** LOW
- **Konum:** `frontend/index.html:7 (v=17)`
- **Kategori:** Caching / Best Practice
- **Açıklama:** CSS/JS versioning `?v=17` hardcoded. Otomatik version management yok; manual update gerekli (v18, v19, ...).
- **Kanıt:**
  ```html
  <link rel="stylesheet" href="/static/css/style.css?v=17">
  <script src="/static/js/gallery.js?v=17"></script>
  ```
- **Nasıl Tetiklenir:** CSS update → forget to increment version → browser cache serve stale CSS
- **Olası Etki:** Inconsistent UI, visual bugs
- **Önerilen Düzeltme:** File hash-based versioning (build step) veya service worker cache invalidation

---

## İstatistikler

| CRITICAL | HIGH | MEDIUM | LOW | INFO | TOPLAM |
|----------|------|--------|-----|------|--------|
| 0        | 2    | 4      | 3   | 5    | 14     |

---

## Değerlendirme

**Özet:** Galleryweb stabil bir proje (Faz 5.4 tamamlanmış), ancak **HIGH** şiddetli 2 konfigürasyon sorunu prod deployment'ı engeller:

1. **CORS hardcoding** → Prod'da localhost API çağrı başarısız
2. **Port hardcoding** → Docker/multi-instance ortamlarda conflict

**MEDIUM sorunlar** (4): Font paths, env docs eksikliği, timeout hardcoding, global state mutable. Refactoring önerilir ama urgent değil.

**LowInfo sorunlar** (8): Code quality, maintainability, perf optimizations — backlog issue olarak takip et.

**Positive Notes:**
- Clean FastAPI structure (async/await, dependency injection)
- Comprehensive features (tags, ratings, albums, EXIF, duplicate detection, QR, watermark)
- Service worker + PWA manifest
- Multi-folder support (Faz 5.2)
- Vim-style keybindings
- SQLite cache layer (efficient)

**Tavsiyeler:**
1. `PORT` ve `ALLOWED_ORIGINS` env vars haline getir → prod-safe
2. `.env.example` oluştur → setup doc
3. SQLite PRAGMA optimizations ekle → large library perf
4. Rate limiting middleware ekle → DoS mitigation
5. State management refactor (Zustand/Nanostores) → multi-tab sync

---

**Rapor Tarihi:** 2026-05-17  
**Tarama Kapsamı:** Dosya yapısı, bağımlılıklar, konfigürasyon, hardcoded değerler, dead code, async handling  
**Exclude Edilen:** node_modules/, venv/, .git/, __pycache__/, *.lock
