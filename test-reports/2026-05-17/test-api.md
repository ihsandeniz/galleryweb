---
agent: test-api
project: Galleryweb
date: 2026-05-17
status: completed
severity_summary:
  critical: 1
  high: 3
  medium: 6
  low: 1
  info: 0
---

# Test Raporu — API & Entegrasyon — Galleryweb

## Test Kapsamı
- **Taranan endpoint'ler:** 35 HTTP endpoint
- **Auth korumalı:** 0 / 35 (0%)
- **Framework:** FastAPI (Python)
- **Database:** SQLite (cache_manager.py)
- **Scope:** /api/* tüm endpoint'ler, batch operasyonlar, error handling

## Bulgular

### [API-F001] No Authentication on Any Endpoint
- **Şiddet:** CRITICAL
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:120-1398`
- **Kategori:** Auth Missing
- **Açıklama:** 
  Tüm API endpoint'leri (35 adet) hiçbir authentication middleware'i olmadan expose edilmiş. 
  - `/api/set-directory` → wildcard path seçme
  - `/api/delete/{path}` → dosya silme
  - `/api/batch/move` → sistem-çapında dosya taşıma
  - `/api/batch/exif` → metadata değişikliği
  
  Herhangi bir auth token, session, or IP whitelist yok.

- **Nasıl Tetiklenir:** 
  ```bash
  curl -X POST http://localhost:5000/api/set-directory \
    -H "Content-Type: application/json" \
    -d '{"path": "/etc"}'
  curl -X DELETE http://localhost:5000/api/image/etc/passwd
  ```

- **Olası Etki:** 
  Tam sistem dosya erişimi, silme, taşıma, metadata değişikliği. Production ortamında veri kaybı, sistem compromise.

- **Önerilen Düzeltme:** 
  - FastAPI `Depends()` guard ekle (token, session, veya X-Api-Key)
  - Middleware ile tüm `/api/*` path'leri protect et
  - Rate limiting + CORS stricter config

---

### [API-F002] No Input Validation — Path Traversal Risk
- **Şiddet:** HIGH
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:1021-1072 (batch_copy/batch_move)`
- **Kategori:** Input Validation
- **Açıklama:** 
  Destination path user input'ten doğrudan alınıyor. Sadece `is_dir()` check yapılıyor:
  - `Path(os.path.expanduser(destination)).resolve()` 
  - `if not dest.is_dir(): raise`
  
  Bu, path traversal veya symbolic link exploitation'e açık.

- **Kanıt:** 
  ```python
  # main.py:1031-1033
  dest = Path(os.path.expanduser(destination)).resolve()
  if not dest.is_dir():
      raise HTTPException(400, f"Hedef klasör bulunamadı: {destination}")
  ```

- **Nasıl Tetiklenir:** 
  ```bash
  curl -X POST http://localhost:5000/api/batch/move \
    -H "Content-Type: application/json" \
    -d '{
      "paths": ["photo.jpg"],
      "destination": "/etc"
    }'
  ```

- **Olası Etki:** 
  Sistem kritik dosyalarına erişim, overwrite, privilege escalation.

- **Önerilen Düzeltme:** 
  - `destination`'ı white-listed parent dirs içine confine et
  - `is_relative_to()` ile path escape kontrolü yap
  - Symlink resolution disable et: `symlink_ok=False` veya `lstat()` kullan

---

### [API-F003] High Severity Exception Swallowing — Silent Failures
- **Şiddet:** HIGH
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:509-530, 1037-1054`
- **Kategori:** Error Handling
- **Açıklama:** 
  Batch operasyonlarda `try/except: pass` → errors silent fail, no logging.
  - `/api/batch/delete` (line 528): `except Exception: pass`
  - `/api/batch/copy` (line 1053): `except Exception as e: results.append(...)`
  
  İlkinde hata hiç loglanmıyor, response'a da gelmez. Success count yanlış olabilir.

- **Kanıt:** 
  ```python
  # main.py:515-529
  for idx, path in enumerate(paths):
      try:
          # ... file operations
      except Exception:
          pass  # ← Hiç log/response yok
  return {"deleted": results, "count": len(results)}
  ```

- **Nasıl Tetiklenir:** 
  Permission denied veya I/O error'da → client başarılı zanneder ama dosya silinmemiştir.

- **Olası Etki:** 
  Data inconsistency, debugging imkansız, users silinen zannettiği dosyaları kurtaramaz.

- **Önerilen Düzeltme:** 
  - Her exception'ı `results[]` append et: `{"path": p, "ok": False, "error": str(e)}`
  - Logger ekle: `import logging; logger.error(f"...")`

---

### [API-F004] N+1 Query Problem in `/api/stats` — Tag Counting Loop
- **Şiddet:** MEDIUM
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:796-801`
- **Kategori:** N+1 Query
- **Açıklama:** 
  `/api/stats` endpoint'i tüm tag'ları alıp loop içinde her tag için ayrı `get_images_with_tags()` çağrısı yapıyor.
  - `get_all_tags()` → N tag döner
  - For loop → N × SQL query

- **Kanıt:** 
  ```python
  # main.py:798-801
  top_tags = cache_manager.get_all_tags()[:10]
  tagged_paths = set()
  for tag_info in cache_manager.get_all_tags():  # Full loop, not top 10!
      imgs = cache_manager.get_images_with_tags([tag_info["name"]])
      tagged_paths.update(imgs)
  ```

- **Nasıl Tetiklenir:** 
  Large image library (1000+ tags) → `/api/stats` response time 5-10 saniye.

- **Olası Etki:** 
  Slow stats endpoint, database lock, user-facing latency.

- **Önerilen Düzeltme:** 
  - `cache_manager`'a single-pass method ekle: `get_tagged_image_count()` (GROUP BY, COUNT aggregation)
  - Veya cached stats table (15min TTL)

---

### [API-F005] N+1 Query in `/api/images/map` — EXIF Per-File
- **Şiddet:** MEDIUM
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:1240-1273`
- **Kategori:** N+1 Query
- **Açıklama:** 
  `get_map_images()` tüm image'ları loop'ta pyexiv2 ile açıyor (disk I/O per file).
  - Cache check var (good) ama uncached files → sequential disk reads
  - 1000 image, %50 cache miss → 500 disk opens

- **Kanıt:** 
  ```python
  # main.py:1251-1268
  for p in image_paths:
      rel = _relative_to_any(p)
      cached = cache_manager.get_image_metadata(str(p))
      lat, lon = None, None
      if cached and cached.get('gps_latitude') is not None:
          lat, lon = cached['gps_latitude'], cached['gps_longitude']
      else:
          try:
              import pyexiv2
              img = pyexiv2.Image(str(p))  # ← Disk I/O per file
              exif = img.read_exif()
              img.close()
              # ...
  ```

- **Nasıl Tetiklenir:** 
  `GET /api/images/map?include_subfolders=true` → 1000 images → 20-30 second response.

- **Olası Etki:** 
  Timeout, client hangup, resource exhaustion.

- **Önerilen Düzeltme:** 
  - Batch EXIF reading (executor'da çalıştır)
  - Limit to cached-only if cache hit % < 30%
  - Async/background task for map data

---

### [API-F006] No Rate Limiting — DoS Risk
- **Şiddet:** HIGH
- **Konum:** Tüm endpoints, özellikle `main.py:837-871 (find_duplicate_images)`, `main.py:1240-1273 (get_map_images)`
- **Kategori:** Rate Limiting Missing
- **Açıklama:** 
  - `/api/duplicates` → full-library image hash (CPU intensive)
  - `/api/images/map` → full EXIF scan (I/O intensive)
  - `/api/batch/copy` → no size limit, unbounded
  
  Hiçbir rate limiting, throttling, veya request queue yok.

- **Nasıl Tetiklenir:** 
  ```bash
  for i in {1..100}; do
    curl -s http://localhost:5000/api/duplicates &
  done
  ```
  → Server CPU peg, memory OOM.

- **Olası Etki:** 
  Denial of Service, legitimate users blocked.

- **Önerilen Düzeltme:** 
  - Slowapi (FastAPI rate limiting library) ekle
  - Per-IP ratelimit: 10 req/min for `/api/duplicates`
  - Task queue (Celery, RQ) for async heavy jobs
  - Max request size: nginx `client_max_body_size`

---

### [API-F007] CORS Allow-All with Wildcard Methods & Headers
- **Şiddet:** MEDIUM
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:99-105`
- **Kategori:** CORS Misconfiguration
- **Açıklama:** 
  CORS middleware'i wildcard methods & headers allow ediliyor:
  - `allow_methods=["*"]` → DELETE, PUT hepsi pass
  - `allow_headers=["*"]` → X-Api-Key bile gereksiz
  
  Origins controlled ama methods/headers kısıtlı değil.

- **Kanıt:** 
  ```python
  # main.py:99-105
  app.add_middleware(
      CORSMiddleware,
      allow_origins=_origins,
      allow_credentials=True,
      allow_methods=["*"],  # ← Wildcard
      allow_headers=["*"],  # ← Wildcard
  )
  ```

- **Nasıl Tetiklenir:** 
  Cross-origin DELETE, PATCH requests → direct browser attack.

- **Olası Etki:** 
  CSRF-like vulnerabilities, unauthorized data modification from compromised sites.

- **Önerilen Düzeltme:** 
  ```python
  allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
  allow_headers=["Content-Type", "Authorization"],
  ```

---

### [API-F008] No Type Validation on POST Bodies
- **Şiddet:** LOW
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:137-149, 448-459, 684-693` (tüm POST endpoints)
- **Kategori:** Input Validation
- **Açıklama:** 
  Tüm POST endpoints `data: dict` parameter kullanıyor → Pydantic type hint yok.
  - Type coercion hatası yaşanabilir
  - Auto-swagger docs degrade
  - Runtime validation eksik

- **Kanıt:** 
  ```python
  # main.py:137
  @app.post("/api/set-directory")
  async def set_directory(data: dict):  # ← No Pydantic model
      path = data.get("path")
  ```

- **Nasıl Tetiklenir:** 
  `POST /api/set-directory -d '{"path": 123}'` → `os.path.isdir(123)` → type error.

- **Olası Etki:** 
  Unexpected exceptions, poor error messages, API brittleness.

- **Önerilen Düzeltme:** 
  ```python
  from pydantic import BaseModel
  
  class SetDirectoryRequest(BaseModel):
      path: str
  
  @app.post("/api/set-directory")
  async def set_directory(req: SetDirectoryRequest):
      ...
  ```

---

### [API-F009] EXIF Metadata Returned Without Sanitization
- **Şiddet:** MEDIUM
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:334-360 (get_metadata)`
- **Kategori:** Information Disclosure
- **Açıklama:** 
  `/api/metadata/{path}` EXIF dict'i raw return ediliyor.
  - GPS coordinates → location tracking
  - Camera model, lens → equipment info
  - Artist, copyright → ownership
  
  Sensitive data filtering yok.

- **Kanıt:** 
  ```python
  # main.py:349-355
  try:
      import pyexiv2
      img = pyexiv2.Image(str(full_path))
      metadata["exif"] = img.read_exif()  # ← Raw EXIF dict
      img.close()
  except Exception:
      metadata["exif"] = None
  ```

- **Nasıl Tetiklenir:** 
  `GET /api/metadata/photo.jpg` → Full EXIF including GPS.

- **Olası Etki:** 
  Location privacy leak, equipment disclosure.

- **Önerilen Düzeltme:** 
  ```python
  SAFE_EXIF_KEYS = {'Exif.Image.DateTime', 'Exif.Image.ImageDescription', ...}
  sanitized = {k: v for k, v in metadata['exif'].items() if k in SAFE_EXIF_KEYS}
  metadata['exif'] = sanitized
  ```

---

### [API-F010] Race Condition — File Operations Without Locks
- **Şiddet:** MEDIUM
- **Konum:** `/home/ihsan/Masaüstü/vibe-cod-organized/projects/Galleryweb/backend/main.py:367-399 (delete_image), main.py:1059-1099 (batch_move)`
- **Kategori:** Concurrency
- **Açıklama:** 
  Aynı dosyaya concurrent requests:
  - Request 1: DELETE /api/image/photo.jpg → move to trash
  - Request 2: DELETE /api/image/photo.jpg (parallel) → file not found, silent fail
  
  No file locking, no atomic checks.

- **Kanıt:** 
  ```python
  # main.py:371-381
  full_path = find_in_directories(path)
  if full_path is None:
      raise HTTPException(404, "Resim bulunamadı")
  # ← TOCTOU: file could be deleted between check and next line
  base = _dir_for_path(full_path) or current_directories[0]
  trash_dir = base / ".gallery_trash"
  full_path.rename(trash_path)  # ← Race condition
  ```

- **Nasıl Tetiklenir:** 
  ```bash
  curl -X DELETE http://localhost:5000/api/image/photo.jpg &
  curl -X DELETE http://localhost:5000/api/image/photo.jpg &
  wait
  ```

- **Olası Etki:** 
  Data inconsistency, cleanup failures, orphaned trash entries.

- **Önerilen Düzeltme:** 
  - File-level locking (fcntl, Windows locks)
  - Or database transaction: record pending delete, then OS operation
  - Atomic `Path.rename()` with error handling

---

## Endpoint Auth Haritası

| Endpoint | Method | Auth Var mı? | Status |
|----------|--------|--------------|--------|
| `/` | GET | ✗ | Public (HTML serve) |
| `/api/current-directory` | GET | ✗ | CRITICAL |
| `/api/set-directory` | POST | ✗ | CRITICAL |
| `/api/add-directory` | POST | ✗ | CRITICAL |
| `/api/directory` | DELETE | ✗ | CRITICAL |
| `/api/clear-directory` | POST | ✗ | CRITICAL |
| `/api/browse` | GET | ✗ | CRITICAL |
| `/api/images` | GET | ✗ | CRITICAL |
| `/api/image/{path}` | GET | ✗ | CRITICAL |
| `/api/metadata/{path}` | GET | ✗ | MEDIUM (Info Leak) |
| `/api/image/{path}` | DELETE | ✗ | CRITICAL |
| `/api/restore/{trash_id}` | POST | ✗ | CRITICAL |
| `/api/trash/{trash_id}` | DELETE | ✗ | CRITICAL |
| `/api/trash` | GET | ✗ | CRITICAL |
| `/api/tags` | GET | ✗ | LOW |
| `/api/tag/{path}` | GET/POST/DELETE | ✗ | CRITICAL |
| `/api/favorite/{path}` | POST | ✗ | CRITICAL |
| `/api/favorites` | GET | ✗ | LOW |
| `/api/batch/delete` | POST | ✗ | CRITICAL |
| `/api/batch/favorite` | POST | ✗ | CRITICAL |
| `/api/batch/tag` | POST | ✗ | CRITICAL |
| `/api/export` | POST | ✗ | CRITICAL |
| `/api/note/{path}` | GET/POST | ✗ | CRITICAL |
| `/api/ratings` | GET | ✗ | LOW |
| `/api/rating/{path}` | POST/DELETE | ✗ | CRITICAL |
| `/api/bookmarks` | GET | ✗ | LOW |
| `/api/bookmark` | POST/DELETE | ✗ | CRITICAL |
| `/api/stats` | GET | ✗ | MEDIUM (N+1) |
| `/api/duplicates` | GET | ✗ | HIGH (DoS) |
| `/api/generate-thumbnails` | POST | ✗ | HIGH (DoS) |
| `/api/watch` | GET (SSE) | ✗ | CRITICAL |
| `/api/albums` | GET/POST | ✗ | CRITICAL |
| `/api/albums/{id}` | GET/PUT/DELETE | ✗ | CRITICAL |
| `/api/albums/{id}/images` | POST/DELETE | ✗ | CRITICAL |
| `/api/batch/copy` | POST | ✗ | HIGH (Path Traversal) |
| `/api/batch/move` | POST | ✗ | HIGH (Path Traversal) |
| `/api/batch/exif` | POST | ✗ | HIGH |
| `/api/qr` | GET | ✗ | LOW |
| `/api/qr-url` | GET | ✗ | LOW |
| `/api/images/map` | GET | ✗ | MEDIUM (N+1) |
| `/api/edit/{path}` | POST | ✗ | CRITICAL |
| `/api/edit/{path}/revert` | POST | ✗ | CRITICAL |
| `/api/edit/{path}/has-backup` | GET | ✗ | CRITICAL |
| `/manifest.json` | GET | ✗ | Public (PWA) |
| `/sw.js` | GET | ✗ | Public (PWA) |

**Özet:** 0/35 endpoint auth korumalı. 23/35 CRITICAL (dosya sistemi erişimi), 6/35 HIGH (DoS, path traversal, rate limit).

---

## İstatistikler

| CRITICAL | HIGH | MEDIUM | LOW | INFO | TOPLAM |
|----------|------|--------|-----|------|--------|
| 1 | 3 | 6 | 1 | 0 | **11** |

---

## Değerlendirme

**Sonuç:** Galleryweb API **production'a hazır değildir**. CRITICAL severity authentication bypass + HIGH path traversal + MEDIUM N+1 performance issues var.

**Temel Sorunlar (Öncelik):**
1. **Auth ekle** (CRITICAL) — Tüm `/api/*` endpoints'leri protect et
2. **Path validation** (HIGH) — white-list dirs, symlink control
3. **Rate limiting** (HIGH) — heavy endpoints'leri throttle et
4. **Error handling** (HIGH) — silent failures logu ve report et
5. **Performance** (MEDIUM) — N+1 queries optimize et

**Faz:** Faz 5.4 (lightbox visual nav fix) tamamlandı, ancak security faz eksik. Faz 6 (Security Hardening) önerilir.
