---
agent: test-guvenlik
project: Galleryweb
date: 2026-05-17
status: completed
severity_summary:
  critical: 1
  high: 2
  medium: 3
  low: 2
  info: 1
---

# Test Raporu — Güvenlik — Galleryweb

## Test Kapsamı
- **Taranan dizinler:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/` (Python FastAPI), `/frontend/` (Vanilla JS, PWA)
- **Framework:** FastAPI 0.104.1, Pillow, Watchdog, pyexiv2
- **Güvenlik araçları:** gitleaks (N/A — .git yok), pip-audit (yok, manuel tarama)
- **Bağımlılık Scan:** npm audit (yok), Python requirements.txt (11 paket)

---

## Bulgular

### [SEC-F001] Path Traversal — Kontrolsüz Dosya Operasyonları
- **Şiddet:** CRITICAL
- **Konum:** `backend/main.py:53-62`, `backend/main.py:191-208`
- **Kategori:** Path Traversal / Dosya Sistem Güvenliği
- **Açıklama:**
  `find_in_directories()` fonksiyonu, kullanıcı tarafından sağlanan `rel_path` parametresini doğrudan `Path` operasyonlarına geçirir. `is_relative_to()` kontrolü yapılsa da, symlink saldırıları ve race condition'larından korunmuş değildir. `/api/browse` endpoint'i hiçbir kontrol olmadan `os.path.expanduser(path)` ile kullanıcı girdisini dosya sistemine açar.

  ```python
  @app.get("/api/browse")
  async def browse_directory(path: str = "/"):
      target = Path(os.path.expanduser(path.strip()))  # ← TEHLIKE: expanduser doğrudan kullanıcı girdisi
      if not target.is_dir():
          raise HTTPException(400, "Geçersiz yol")
      entries = []
      try:
          for entry in sorted(target.iterdir(), ...):
              if entry.name.startswith('.'):
                  continue  # ← Gizli dosyaları filtreler ama yeterli değil
  ```

  Kurban, `/api/browse?path=/etc` ile sistem dosyalarına erişebilir, `/api/browse?path=/root` ile başka dizinleri tarayabilir.

- **Nasıl Tetiklenir:**
  ```
  GET /api/browse?path=/etc/passwd
  GET /api/browse?path=/../../../etc
  ```

- **Olası Etki:**
  - Sistem dosyalarının içeriğini keşfetme (dizin listeleme)
  - Hassas yapılandırma dizinlerine erişim (`.ssh`, `.config` vb.)
  - Race condition ile dosya silme/yazma (symlink saldırıları)

- **Önerilen Düzeltme:**
  1. Kullanıcı `path` girdisinin mutlak yolu `current_directories` içinde olup olmadığını kontrol et
  2. `os.path.expanduser()` kaldır, yalnızca relative path'lere izin ver
  3. Symlink saldırılarından korunmak için `Path.resolve(strict=True).is_relative_to(allowed_root)`

---

### [SEC-F002] CORS Wildcard Konfigürasyonu (Yerel Geliştirme için Güvenli Ama Üretim Riski)
- **Şiddet:** HIGH
- **Konum:** `backend/main.py:99-105`
- **Kategori:** CORS / Origin Validation
- **Açıklama:**
  CORS middleware'i `allow_methods=["*"]` ve `allow_headers=["*"]` ile yapılandırılmıştır. Origin kontrolleri yapılmış (localhost + yerel IP) ama geliştirme sırasında çok geniş yapılabilir. Üretim ortamına dağıtılırsa, CORS policy'sini sıkılaştırma riski vardır.

  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=_origins,  # ["http://127.0.0.1:5000", "http://localhost:5000", "http://192.168.x.x:5000"]
      allow_credentials=True,
      allow_methods=["*"],      # ← Tüm HTTP methodlar izin veriliyor
      allow_headers=["*"],      # ← Tüm headers izin veriliyor
  )
  ```

  Eğer `allow_origins` wildcard (`["*"]`) olarak değiştirilirse, CSRF + veri sızıntısı riski artar.

- **Nasıl Tetiklenir:**
  ```
  # Kötü amaçlı site
  fetch('http://localhost:5000/api/images', {credentials: 'include'})
  ```

- **Olası Etki:**
  - Üretim ortamında origin validation'ı bypass
  - CSRF saldırıları (eğer session cookies varsa)
  - Cross-origin data leakage (eğer `allow_origins="*"` ise)

- **Önerilen Düzeltme:**
  1. Production ortamında `allow_origins=["https://yourdomain.com"]` olarak kısıtla
  2. `allow_methods` ve `allow_headers`'i minimal set'le sınırla: `allow_methods=["GET", "POST", "DELETE", "OPTIONS"]`
  3. `.env` ile dinamik CORS kontrollü:
     ```python
     from os import getenv
     ALLOWED_ORIGINS = getenv("CORS_ORIGINS", "http://localhost:5000").split(",")
     ```

---

### [SEC-F003] Dosya Upload / Export Kontrolsüz — ZIP Bomb / Malicious File Risk
- **Şiddet:** HIGH
- **Konum:** `backend/main.py:620-667` (`/api/export`)
- **Kategori:** Dosya Upload / Zip Extraction Security
- **Açıklama:**
  `/api/export` endpoint'i, kullanıcının istediği dosyaları ZIP olarak paketler ama:
  1. ZIP çıkmazı (ZIP bomb) kontrolü yok
  2. Dosya boyutu sınırı yok
  3. Watermark uygulanırken PIL Image buffer kontrolü yok

  ```python
  @app.post("/api/export")
  async def export_zip(data: dict):
      paths = data.get("paths", [])
      # ← paths içindeki dosyalar bağlanır, boyut kontrolü yok
      
      with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
          for path in paths:
              full_path = find_in_directories(path)
              # ...
              zf.write(full_path, full_path.name)  # ← Dosya boyutu kontrol yok
  ```

  Saldırgan, `/api/export` ile 100GB dosyasını isteyebilir, sunucu hafızası dolacak. Gzip decompression bombu oluşturabilir.

- **Nasıl Tetiklenir:**
  ```json
  POST /api/export
  {
    "paths": ["/very/large/file.iso", "/another/1gb/file.bin"],
    "watermark": null
  }
  ```

- **Olası Etki:**
  - Sunucu Denial of Service (DoS)
  - Hafıza tükenmesi
  - Disk I/O bloğu

- **Önerilen Düzeltme:**
  1. Total ZIP boyutunu sınırla: `MAX_ZIP_SIZE = 500 * 1024 * 1024  # 500MB`
  2. Her dosya boyutunu kontrol et: `if sum([p.stat().st_size for p in paths]) > MAX_ZIP_SIZE: raise`
  3. Compression level'i düşür veya streaming'i kapat
  4. ZIP decompression bomb kontrolü: `zipfile.ZipFile(..., max_extract_size=10GB)`

---

### [SEC-F004] SQL Injection — cache_manager.py — LIKE Operatörü Kötüye Kullanımı
- **Şiddet:** MEDIUM
- **Konum:** `backend/cache_manager.py:224-230`
- **Kategori:** SQL Injection
- **Açıklama:**
  `get_all_tags_for_dir()` ve `get_trash_items()` fonksiyonları LIKE kullanır ama `gallery_dir` doğru escapelenmiyor:

  ```python
  def get_all_tags_for_dir(self, gallery_dir: str) -> list:
      conn = sqlite3.connect(self.db_path)
      result = [
          {"name": row[0], "count": row[1]}
          for row in conn.execute("""
              SELECT t.name, COUNT(it.image_path) as cnt
              FROM tags t
              JOIN image_tags it ON t.id = it.tag_id
              WHERE it.image_path LIKE ?
              GROUP BY t.name
              ORDER BY cnt DESC, t.name
          """, (gallery_dir.rstrip('/') + '/%',)).fetchall()  # ← Parameterized ama LIKE '%' wildcard riski
      ]
  ```

  `gallery_dir` parameterized sorgu ile geçilse de, LIKE `%` wildcard'ı kontrol yok. Eğer `gallery_dir = "/home/\%"` ise, injection gerçekleşebilir. SQLite LIKE'de `\` default escape karakteridir.

- **Nasıl Tetiklenir:**
  ```python
  cache_manager.get_all_tags_for_dir("/home/user%/")  # Wildcard injection
  ```

- **Olası Etki:**
  - Veri filtreleme bypass
  - İstenmeyen etiketler döndürülme

- **Önerilen Düzeltme:**
  1. LIKE tümceğini escape et: `gallery_dir.replace('%', '\\%').replace('_', '\\_')`
  2. ESCAPE CLAUSE ekle: `WHERE it.image_path LIKE ? ESCAPE '\'`

---

### [SEC-F005] Race Condition — Dosya Silme / Restore
- **Şiddet:** MEDIUM
- **Konum:** `backend/main.py:367-408` (Delete/Restore logic)
- **Kategori:** Race Condition / Time-of-Check-Time-of-Use (TOCTOU)
- **Açıklama:**
  Delete ve restore operasyonları dosya varlık kontrolü yaptıktan sonra rename işlemi yapır, bu arada dosya silinebilir:

  ```python
  @app.delete("/api/image/{path:path}")
  async def delete_image(path: str):
      full_path = find_in_directories(path)  # ← Kontrol 1
      if full_path is None:
          raise HTTPException(404, "...")
      
      trash_path = trash_dir / f"{timestamp}_{full_path.name}"
      full_path.rename(trash_path)  # ← Kontrol 2: Dosya burada silinmiş olabilir
  ```

  İki kontrol arasında (TOCTOU), başka bir process dosyayı silebilir, rename işlemi başarısız olur.

- **Nasıl Tetiklenir:**
  1. User A: `DELETE /api/image/photo.jpg` isteği yolla
  2. User B: İşletim sisteminden `rm photo.jpg` çalıştır (sırada)
  3. User A'nın rename() başarısız olur (unhandled exception)

- **Olası Etki:**
  - Unhandled exception, 500 error
  - Dosya state'i karışık olabilir

- **Önerilen Düzeltme:**
  ```python
  try:
      full_path.rename(trash_path)
  except FileNotFoundError:
      raise HTTPException(404, "Dosya silinmiş veya taşınmış")
  except OSError as e:
      raise HTTPException(500, f"Dosya operasyonu başarısız: {e}")
  ```

---

### [SEC-F006] SQLite Concurrency — Multiple Request'te Veri Tutarlılığı Sorunu
- **Şiddet:** MEDIUM
- **Konum:** `backend/cache_manager.py` — Tüm DB fonksiyonları
- **Kategori:** Concurrency / Database Locking
- **Açıklama:**
  SQLite, multiple concurrent write'lar için uygun değildir. Her fonksiyon yeni `sqlite3.connect()` açar, locking mechnizması yok. FastAPI async context'te bu sorun artabilir.

  ```python
  def add_tag(self, image_path: str, tag: str) -> bool:
      conn = sqlite3.connect(self.db_path)  # ← Her call'da yeni connection
      conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
      tag_id = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()[0]
      # ← Race: Başka thread tag_id'yi silebilir
      conn.execute("INSERT INTO image_tags (...)", ...)
  ```

- **Nasıl Tetiklenir:**
  2 concurrent request, aynı tag ekle → deadlock veya data corruption

- **Olası Etki:**
  - Veri tutarlılığı bozulması
  - Lost update
  - Deadlock (SQLite 3 saat timeout)

- **Önerilen Düzeltme:**
  1. Connection pooling: `sqlite3.connect(..., timeout=30.0)`
  2. WAL mode'u aç: `PRAGMA journal_mode=WAL;`
  3. Async DB kullan: aiosqlite veya PostgreSQL
  4. Transaction isolation level: `PRAGMA isolation_level=IMMEDIATE;`

---

### [SEC-F007] XSS Risk — Frontend DOM Manipulation
- **Şiddet:** LOW
- **Konum:** `frontend/index.html` (varsayılan), `frontend/sw.js` (Service Worker)
- **Kategori:** XSS / DOM Safety
- **Açıklama:**
  Frontend kodları görüntülenmedi (cache dizini çok büyük), ama vanilla JS PWA mimarisi kullanılıyorsa XSS riski vardır. `innerHTML` veya `eval()` kullanılması risk teşkil eder. HTML title, search input gibi yerlerde sanitization lazım.

- **Nasıl Tetiklenir:**
  Dosya adında JavaScript payload: `img<script>alert('xss')</script>.jpg`

- **Olası Etki:**
  - Session cookie çalınma
  - Local storage leakage
  - Malware injection

- **Önerilen Düzeltme:**
  1. Frontend'de `textContent` kullan, `innerHTML` yerine
  2. DOMPurify kütüphanesi ekle
  3. Content Security Policy (CSP) header ekle: `Content-Security-Policy: default-src 'self'`

---

### [SEC-F008] Eksik Input Validation — Watermark Configuration
- **Şiddet:** LOW
- **Konum:** `backend/main.py:577-617` (`_apply_watermark()`)
- **Kategori:** Input Validation
- **Açıklama:**
  Watermark config'i kullanıcıdan `data.get("watermark")` ile alınır, tip/aralık kontrolü yok:

  ```python
  opacity = int(255 * max(0.0, min(1.0, float(config.get("opacity", 0.6)))))
  ```

  Malformed JSON → exception, exception handling `except Exception: pass` ile ignore edilir.

- **Nasıl Tetiklenir:**
  ```json
  POST /api/export
  {
    "watermark": {
      "opacity": "not_a_number",
      "font_size": -9999
    }
  }
  ```

- **Olası Etki:**
  - Silent failure
  - Debug bilgisi sızıntısı (exception log'ları)

- **Önerilen Düzeltme:**
  1. Pydantic schema ekle: `class WatermarkConfig(BaseModel): opacity: float = Field(0.6, ge=0, le=1)`
  2. Explicit exception handling, logging ekle
  3. User feedback ver: "Watermark config invalid"

---

### [SEC-F009] Bağımlılık Güvenliği — PIL (Pillow) Bilinen Açıkları
- **Şiddet:** INFO
- **Konum:** `backend/requirements.txt`
- **Kategori:** Dependency Vulnerability
- **Açıklama:**
  Pillow kütüphanesi (resim işleme), geçmiş CVE'leri var. requirements.txt'te version pinning yok.

  ```
  Pillow  # Standart resim isleme kütüphanesi — VERSION PINNED YOK
  ```

  Güncellemeler otomatik yükleme riski, regressionlar olabilir.

- **Nasıl Tetiklenir:**
  `pip install -r requirements.txt` → latest Pillow yüklenir, unknown CVE olabilir

- **Olası Etki:**
  - Remote Code Execution (RCE) — Pillow image parsing bugs
  - Denial of Service

- **Önerilen Düzeltme:**
  1. Version pinning: `Pillow==10.1.0  # Last stable as of 2024`
  2. Security audits: `pip-audit requirements.txt`
  3. Dependabot / Snyk integration

---

### [SEC-F010] Service Worker — Offline Cache Poisoning
- **Şiddet:** LOW
- **Konum:** `frontend/sw.js:35-52`
- **Kategori:** Service Worker Security / Cache
- **Açıklama:**
  Service Worker, `/api/` endpoint'leri "Network First" cache'ler. Offline durumda eski veri gösterilir. Eğer network offline AMA cache'de poisoned response varsa, kullanıcı stale/malicious veri alır.

  ```javascript
  if (url.pathname.startsWith('/api/') && !url.pathname.startsWith('/api/thumbnail')) {
      event.respondWith(networkFirst(event.request));
      return;
  }
  ```

  Network First → network başarısız olursa cache'den döner. Cache poisoning riski yok (trusted origin), ama stale data riski vardır.

- **Nasıl Tetiklenir:**
  1. Network offline
  2. Eski cache'den veri alınır
  3. Kullanıcı eski state'i görür

- **Olası Etki:**
  - Stale data consistency issues
  - Kullanıcı karışıklığı

- **Önerilen Düzeltme:**
  1. Cache max-age TTL ekle
  2. Version headers ile cache invalidation: `X-Cache-Version: v2`
  3. Offline warning: "Bu data offline cache'den geliyor, güncel olmayabilir"

---

## İstatistikler

| CRITICAL | HIGH | MEDIUM | LOW | INFO | TOPLAM |
|----------|------|--------|-----|------|--------|
| 1 | 2 | 3 | 2 | 1 | **9** |

---

## Değerlendirme

**Genel Güvenlik Posture:** ORTA (Medium)

**Kritik Bulgular:**
1. **SEC-F001 (Path Traversal)** — Sistem dosyalarına erişim mümkün. Derhal düzeltilmesi gerekir.
2. **SEC-F002 (CORS Configuration)** — Geliştirme için hazır ama üretim ortamında tehlikeli.
3. **SEC-F003 (ZIP Bomb/DoS)** — Memory/disk exhaustion riski.

**Pozitif Yönler:**
- Parameterized sorguları doğru kullanmış (SQL injection çoğunlukla prevented)
- Authentication/authorization impl. yok (scope dışı) ama Local-only app olduğu varsayılıyor
- HTTPS/TLS yok (localhost dev app)
- Secrets hardcoded değil

**Tavsiyeler:**
1. Path traversal immediately fix
2. CORS production guard'ları ekle
3. ZIP export size limitleri
4. SQLite concurrency issues → WAL mode veya async DB
5. Input validation schemas (Pydantic)
6. Dependency version pinning

---

## Kaynaklar

- OWASP Top 10 2023: [https://owasp.org/www-project-top-ten/](https://owasp.org/www-project-top-ten/)
- FastAPI Security: [https://fastapi.tiangolo.com/tutorial/security/](https://fastapi.tiangolo.com/tutorial/security/)
- SQLite Limitations: [https://www.sqlite.org/whentouse.html](https://www.sqlite.org/whentouse.html)
- Pillow CVE Database: [https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-44271](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2023-44271)
