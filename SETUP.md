# GalleryWeb SaaS — Faz 0 Servis Kurulum Rehberi

Bu rehber Faz 0'da gerekli tüm servis hesaplarını nasıl açacağını adım adım anlatır.  
Her adımda alınan credential'ları `.env` dosyasına yaz.

---

## Adım 1 — GitHub Repository

```bash
# Repo oluştur (eğer yoksa)
gh repo create galleryweb --private
git init
git remote add origin https://github.com/SENİN_KULLANICI_ADIN/galleryweb.git
git add ARCHITECTURE.md .env.example .github/ db/ SETUP.md
git commit -m "chore: Faz 0 — SaaS altyapı dosyaları"
git push -u origin main
```

**GitHub Actions:** Push sonrası `Actions` sekmesinde CI workflow otomatik çalışır.

---

## Adım 2 — Supabase Kurulumu

1. [app.supabase.com](https://app.supabase.com) → **New Project** → `galleryweb-prod`
2. Region: **eu-central-1** (Frankfurt — Türkiye'ye en yakın)
3. Proje oluştuktan sonra: **Project Settings → API**
   - `URL` → `.env`'e `SUPABASE_URL` olarak yaz
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY`
4. **SQL Editor** → `db/bootstrap.sql` içeriğini yapıştır → **Run**
5. **Authentication → Providers → Email** → Enable, Confirm email: OFF (dev'de)
6. İsteğe bağlı: Google OAuth → Providers → Google → Client ID + Secret ekle

**Test:**
```bash
curl https://YOUR-PROJECT.supabase.co/rest/v1/profiles \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
# → []  (boş dizi, bağlantı başarılı)
```

---

## Adım 3 — Cloudflare R2 Kurulumu

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **R2** → **Create Bucket**
   - Bucket adı: `galleryweb-prod`
   - Location: **EEUR** (Eastern Europe — Türkiye için uygun)
2. **R2 → Manage R2 API Tokens** → **Create API Token**
   - Object Read & Write
   - Specify bucket: `galleryweb-prod`
   - Token oluştur → Access Key ID + Secret Key → `.env`'e yaz
3. `.env` dosyasındaki `R2_ACCOUNT_ID`: Dashboard URL'indeki sayı (`/xxxxxxxx`)
4. **Public access** (opsiyonel): Bucket → Settings → Public R2.dev subdomain → Enable
   - Bu URL'yi `R2_PUBLIC_URL` olarak yaz

**Test (Python):**
```python
import boto3, os
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)
print(s3.list_buckets())  # galleryweb-prod görünmeli
```

---

## Adım 4 — Railway Kurulumu

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. GalleryWeb reposunu seç
3. **Variables** sekmesi → `.env` içindeki tüm değişkenleri ekle
4. `railway.toml` dosyası oluştur (otomatik build için):

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 10
```

5. **Deploy** → URL al → `ALLOWED_ORIGINS`'e ekle

**Test:**
```bash
curl https://galleryweb-prod.up.railway.app/health
# → {"status": "ok"}
```

---

## Adım 5 — Paddle Kurulumu (Billing)

1. [paddle.com](https://paddle.com) → Sign up → **Seller** hesabı aç
2. **Sandbox** modunda başla (test kartları ile ücretsiz)
3. **Catalog → Products → New Product**
   - VIP1: `$4.99/month` → Price ID al → `.env` `PADDLE_VIP1_PRICE_ID`
   - VIP2: `$14.99/month` → Price ID al → `.env` `PADDLE_VIP2_PRICE_ID`
   - VIP3: `$49.99/month` → Price ID al → `.env` `PADDLE_VIP3_PRICE_ID`
4. **Developer Tools → Authentication** → API Key → `.env` `PADDLE_API_KEY`
5. **Developer Tools → Webhooks** → Add endpoint → Railway URL + `/webhook/paddle`
   - Event: `subscription.created`, `subscription.updated`, `subscription.canceled`
   - Signing secret → `.env` `PADDLE_WEBHOOK_SECRET`

> **Not:** Paddle Merchant of Record — Türkiye KDV, AB VAT otomatik. Production'a geçmek için Paddle onay süreci ~1-2 hafta.

---

## Adım 6 — .env Doldur ve Test Et

```bash
cp .env.example .env
# Nano veya VS Code ile .env'i aç ve tüm değerleri doldur

# Backend'i başlat (Faz 1'e kadar SQLite ile çalışmaya devam eder)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Sağlık kontrolü
curl http://localhost:8000/health
```

---

## Faz 0 Tamamlama Kriterleri

- [ ] GitHub repo oluşturuldu, CI/CD yeşil
- [ ] Supabase projesi aktif, `db/bootstrap.sql` çalıştı, tablolar görünüyor
- [ ] R2 bucket oluşturuldu, API token çalışıyor
- [ ] Railway project deploy edildi (boş endpoint)
- [ ] `.env` dolduruldu (en az Supabase + R2 + Railway)
- [ ] Paddle sandbox hesabı açıldı, 3 price ID alındı

**Tümü tamamlandıktan sonra:** Faz 1 — Core SaaS Backend başlayabiliriz.

---

## Destek

Herhangi bir adımda takıldığında durumu paylaş:
- Hangi adımda
- Aldığın hata mesajı
- Çalıştırdığın komut

Faz 1'i başlatmak için mesaj yaz: **"Faz 0 tamamlandı"**
