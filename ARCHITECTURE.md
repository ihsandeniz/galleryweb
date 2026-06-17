# GalleryWeb SaaS — Architecture Decision Log

**Proje:** GalleryWeb cross-platform SaaS  
**Başlangıç:** 2026-06-17  
**Plan Referansı:** `WIKI/sources/projects/galleryweb-saas-plan.md`

---

## Mimari Özeti

```
┌─────────────────────────────────────────────────────────────┐
│  CLIENTS                                                     │
│  Web (Vanilla JS) │ Desktop (Tauri 2) │ Mobile (Capacitor)  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS / JWT
┌────────────────────────▼────────────────────────────────────┐
│  API GATEWAY (Railway)                                      │
│  FastAPI 0.104+ — Multi-tenant, JWT auth, RLS               │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
    ┌───────────▼───────────┐   ┌─────────▼──────────────┐
    │  Supabase (managed)   │   │  Cloudflare R2          │
    │  PostgreSQL + Auth    │   │  Object storage         │
    │  Realtime + RLS       │   │  Presigned URL uploads  │
    └───────────────────────┘   └────────────┬───────────┘
                                             │ S3 event
                                 ┌───────────▼───────────┐
                                 │  Lambda / Worker      │
                                 │  Thumbnail generation │
                                 │  (Sharp, WebP 3 size) │
                                 └───────────────────────┘
```

---

## Karar 1: Veritabanı — SQLite → PostgreSQL (Supabase)

| Seçenek | Neden Red |
|---------|-----------|
| SQLite (mevcut) | Single-file, multi-user isolation yok, concurrent write sınırlı |
| PlanetScale | MySQL syntax, RLS yok |
| Neon | Serverless cold start, Supabase Auth entegrasyonu daha zor |
| **Supabase (seçilen)** | PostgreSQL + Auth + RLS + Realtime tek pakette; RLS ile multi-tenant isolation built-in |

**Karar:** Supabase managed PostgreSQL. RLS politikaları her tablo için `user_id = auth.uid()`.

---

## Karar 2: Object Storage — Local disk → Cloudflare R2

| Seçenek | Neden Red |
|---------|-----------|
| Local disk (mevcut) | Single server, SaaS'ta ölçeklenmez |
| AWS S3 | Egress fee: ~$0.09/GB (1000 MAU × 10GB/ay = $900/ay sadece egress) |
| Backblaze B2 | Cloudflare ile egress anlaşması yok, direct CDN zor |
| **Cloudflare R2 (seçilen)** | **Zero egress fee**, S3-compatible API, Cloudflare CDN ile entegre, EMEA edge |

**Karar:** R2. boto3 ile presigned URL. Tarayıcı doğrudan R2'ye upload eder (backend'i bypass).

---

## Karar 3: Auth — Yok → Supabase Auth

| Seçenek | Neden Red |
|---------|-----------|
| Yok (mevcut) | CRITICAL security: herkes her şeye erişiyor |
| Auth0 | $23/ay 1k MAU, RLS entegrasyonu için custom work |
| Clerk | $25/ay 1k MAU, FastAPI JWT doğrulama için extra setup |
| **Supabase Auth (seçilen)** | Supabase DB ile sıkı entegre; `auth.uid()` RLS'de çalışıyor; Google/Apple OAuth hazır; ücretsiz 50k MAU |

**Karar:** Supabase Auth. JWT token → FastAPI `get_current_user()` dependency → RLS.

---

## Karar 4: Deployment — Local only → Railway

| Seçenek | Neden Red |
|---------|-----------|
| VPS (DigitalOcean) | Manuel yönetim, scale etmek için downtime |
| Render | Sleep policy agresif, cold start >30s |
| Heroku | Pahalı, yavaş |
| **Railway (seçilen)** | GitHub push → otomatik deploy; usage-based pricing; PostgreSQL addon; env management iyi |

**Karar:** Railway. FastAPI container → Railway. Supabase DB'ye uzaktan bağlanır.

---

## Karar 5: Desktop — Electron vs Tauri

| Seçenek | Neden Red |
|---------|-----------|
| Electron | 80-120MB paket boyutu, Chromium bundled |
| **Tauri 2.x (seçilen)** | **3-15MB** paket boyutu (sistem webview kullanır); Rust backend; PyInstaller sidecar ile FastAPI backend bundle edilebilir |

**Karar:** Tauri 2.x. Python FastAPI backend → PyInstaller sidecar → Tauri uygulama içinde.

---

## Karar 6: Mobile — Native vs Capacitor

| Seçenek | Neden Red |
|---------|-----------|
| React Native | Mevcut Vanilla JS'i yeniden yazma gerektirir |
| Flutter | Yeni dil + yeniden yazma |
| **Capacitor.js (seçilen)** | **Mevcut Vanilla JS'i sıfır yeniden yazma ile wrap eder**; iOS + Android; camera/file API native plugins |

**Karar:** Capacitor.js. Mevcut frontend sıfır değişiklikle iOS ve Android'e wrap edilir.

---

## Karar 7: Billing — Stripe vs Paddle

| Seçenek | Neden Red |
|---------|-----------|
| Stripe | Türkiye VAT/KDV manuel ekle; EU/UK VAT da manuel; vergi hesabı karmaşık |
| LemonSqueezy | Küçük ecosystem, limit olan ülkeler var |
| **Paddle (seçilen)** | **Merchant of Record** — Türkiye KDV, AB VAT, ABD sales tax otomatik; anlaşmazlıklarda Paddle sorumluluk alır |

**Karar:** Paddle. Tier: Free / VIP1 $4.99 / VIP2 $14.99 / VIP3 $49.99.

---

## Faz Yol Haritası (Özet)

| Faz | Başlık | Süre | Durum |
|-----|--------|------|-------|
| **0** | Hazırlık & Altyapı | 1 hafta | 🔄 Aktif |
| 1 | Core SaaS Backend | 2.5 hafta | ⏳ |
| 2 | DB Migration SQLite→PG | 1 hafta | ⏳ |
| 3 | Cloud Storage R2 | 2 hafta | ⏳ |
| 4 | Frontend Auth UI | 2 hafta | ⏳ |
| 5 | Cross-platform (Tauri+Cap) | 3 hafta | ⏳ |
| 6 | Sync & Realtime | 2 hafta | ⏳ |
| 7 | Müşteri Proofing Gallery | 2 hafta | ⏳ |
| 8 | CLIP Semantic Search | 2 hafta | ⏳ |
| 9 | Paddle Billing | 1.5 hafta | ⏳ |
| 10 | E2EE (ZK) | 2 hafta | ⏳ |
| 11 | RAW Support | 2 hafta | ⏳ |
| 12 | Launch Prep | 2 hafta | ⏳ |

**Toplam:** ~6-8 ay | **Breakeven:** Ay 5-6 (~17k MAU)

---

## Ortam Değişkenleri

Tüm credentials → `.env` (repo'ya commit edilmez!)  
Şablon → `.env.example`

---

## Değişim Geçmişi

| Tarih | Karar | Açıklama |
|-------|-------|----------|
| 2026-06-17 | Tüm kararlar | İlk mimari draft |
