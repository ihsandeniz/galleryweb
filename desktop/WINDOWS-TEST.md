# 🪟 Windows Gerçek Makine Kontrol Listesi (FAZ W3)

**Süre:** ~30 dakika · **Gereken:** Windows 10 veya 11, internet (ilk indirme için)

CI (GitHub Actions) paketi derliyor, testleri gerçek Windows'ta koşuyor ve kurulum
paketinin içeriğini doğruluyor. Ama CI'nın **yapamadığı** altı şey var — hepsi
"kurulum makinesinde ne oluyor" sorusuna bakar, kod doğruluğuna değil:

| CI yapabiliyor | CI yapamıyor (bu liste) |
|---|---|
| Testleri Windows'ta koşmak | SmartScreen uyarısı |
| exe + NSIS üretmek | Gerçek virüs tarayıcısı davranışı |
| Kurulum içeriğini açıp doğrulamak | Controlled Folder Access |
| Sunucuyu başlatıp HTTP sınamak | WebView2'siz makinede kurulum |
| — | Pencerenin gerçekten açılması |
| — | Telefon + güvenlik duvarı akışı |

---

## Paketi indir

> ✅ **2026-08-07 17:04 — taslak paketler TAZELENDİ.** Bir süre bayattılar (07-28
> sürümü, bugün silinen SaaS katmanını içeriyordu); üçü de değiştirildi.
> Windows paketi `19acaf09` koşusunun CI çıktısıdır, Linux paketleri aynı ağaçtan
> yerelde derlendi. Doğrulandı: kurulum paketi açıldı, içindeki
> `_internal/frontend/js/gallery.js` **`MODE='yerel'`** taşıyor, bulut fonksiyonu
> 0, `auth.js`/`saas-api.js`/`realtime.js`/`login.html` pakette **yok**.
> **Ders kayda geçti** → `WIKI/ledger.md` §
> `release/taslak-varlik-koddan-sonra-tazelenmez-bayat-paket-test-edilir`

**En kolay yol —** https://github.com/ihsandeniz/galleryweb/releases → **`v1.1.1` (Latest)**
→ `GalleryWeb_1.1.0_x64-setup.exe` (**232 MB**, 07-08-2026 17:04'te yüklendi).
*Taslağı yalnız sen görürsün.*

Alternatif (aynı dosya): Actions → yeşil **CI** koşusu → **Artifacts** →
`galleryweb-windows` (30 gün durur).

> 🔎 **İndirmeden önce 5 saniyelik kontrol:** dosya boyutu **232 MB** olmalı.
> 226 MB görüyorsan bayat sürüme bakıyorsundur — indirme, haber ver.

> ⚠️ **VM'in İÇİNDEN, tarayıcıyla indir.** Paylaşılan klasörle kopyalarsan dosyaya
> *Mark of the Web* basılmaz, SmartScreen hiç çıkmaz ve aşağıdaki 1. madde **sahte geçer**.

> Bu paket **imzasız**. Aşağıdaki 1. madde tam olarak bunu sınıyor — beklenen davranıştır.

---

## Kontrol listesi

Her maddeye **✅ / ❌ + ne gördün** yaz. Kısa cümle yeter, ekran görüntüsü daha iyi.

### 1. SmartScreen — kurulum açılıyor mu?
- [ ] Kuruluma çift tıkla. **Beklenen:** mavi "Windows bilgisayarınızı korudu" ekranı
      → **Ek bilgi** → **Yine de çalıştır**.
- [ ] Not al: uyarı çıktı mı, metni ne, "Yine de çalıştır" bağlantısı görünüyor mu?
- ❗ **Uyarı ÇIKMAZSA da yaz** — beklediğimizin çıkmaması da bilgidir.

### 2. WebView2 — kurulum internetsiz de tamamlanıyor mu?
- [ ] Kurulum sırasında WebView2 için ayrı bir adım/ilerleme çubuğu gördün mü?
- [ ] **Mümkünse:** Wi-Fi'ı kapat, kurulumu öyle çalıştır. **Beklenen:** yine tamamlanır
      (paket çevrimdışı kurucuyu içeriyor).
- [ ] Kurulum ne kadar sürdü, paket boyutu neydi?

### 3. Pencere gerçekten açılıyor mu?
- [ ] Başlat menüsünden **GalleryWeb** → pencere açılıyor mu?
- [ ] İçi **boş/siyah** mı, yoksa galeri arayüzü mü geliyor? *(Linux'ta NVIDIA+Wayland'de
      siyah pencere sorunu yaşanmıştı; Windows'ta beklenmez ama bakılır.)*
- [ ] Açılış kaç saniye sürdü? *(onedir kararının ölçüsü bu — 30 sn'yi geçerse sorun var.)*
- [ ] Arkada **siyah konsol penceresi** yanıp sönüyor mu? **Beklenen: HAYIR.**

### 4. Virüs tarayıcısı ne yapıyor?
- [ ] Defender (veya kullandığın AV) kurulumu ya da `galleryweb-server.exe`'yi karantinaya aldı mı?
- [ ] Defender geçmişini kontrol et: **Windows Güvenliği → Virüs ve tehdit koruması →
      Koruma geçmişi**. Bir kayıt varsa metnini yaz.

### 5. Controlled Folder Access (⭐ en kritik madde)
Defender'ın "Denetimli klasör erişimi" özelliği, **Resimler/Belgeler/Masaüstü** klasörlerine
tanımadığı programların YAZMASINI engeller. Açıksa GalleryWeb düzenleme yapamaz —
ve büyük ihtimalle **hata bile vermez**, sadece kaydetmez.

- [ ] Açık mı bak: **Windows Güvenliği → Virüs ve tehdit koruması → Fidye yazılımı koruması**
- [ ] Durumu yaz: **açık / kapalı**
- [ ] **Açıksa:** `Resimler` klasöründeki bir fotoğrafı GalleryWeb'de döndür + kaydet.
      Kaydediliyor mu, yoksa sessizce mi geçiyor?
- [ ] Aynı testi `İndirilenler` gibi korumasız bir klasörde tekrarla — orada çalışıyorsa
      sorun kesin CFA'dır.

### 6. Telefon erişimi + güvenlik duvarı
- [ ] Uygulamada **telefon erişimi** anahtarını aç.
- [ ] İlk açılışta Windows'un **"ağ erişimine izin ver"** penceresi çıktı mı? *(Çıkmayabilir —
      sunucu konsolsuz başlatılıyor. Beklediğimiz de bu.)*
- [ ] Telefondan QR'ı okut. **Beklenen (izin verilmediyse):** telefonda *zaman aşımı*.
- [ ] Uygulama ekranında 🧱 güvenlik duvarı kutusu göründü mü? İçinde `netsh advfirewall …`
      komutu ve **"Yönetici olarak çalıştırın"** notu var mı?
- [ ] Komutu **yönetici** Komut İstemi'nde çalıştır → telefondan tekrar dene.
      **Beklenen:** galeri telefonda açılıyor.
- [ ] İşin bitince kuralı kaldır: `netsh advfirewall firewall delete rule name="GalleryWeb"`

### 7. Gündelik kullanım (5 dk serbest gezinti)
- [ ] Türkçe karakterli ve boşluklu klasör seç (ör. `C:\Users\<ad>\Resimler\Tatil Fotoğrafları`)
- [ ] Küçük resimler geliyor mu, kaç saniyede?
- [ ] Bir fotoğrafı döndür → geri al (Ctrl+Z) → ileri al. Geçmiş korunuyor mu?
- [ ] Bir fotoğrafı sil → çöp kutusundan geri yükle.
- [ ] **Video varsa:** oynat, sonra oynarken silmeyi dene.
      **Beklenen:** "Dosya başka bir program tarafından kullanılıyor" uyarısı
      (çıplak hata veya sahte "silindi" DEĞİL).

---

## Sonucu nasıl ilet

Listeyi kopyalayıp yanına yazman yeterli. Özellikle şunları belirt:

- **5. madde** (Controlled Folder Access) — açık mıydı, kaydetme çalıştı mı?
- **3. madde** açılış süresi — onedir kararının ölçüsü
- Beklenmedik her ekran görüntüsü

Bu liste tamamlanmadan `v1.1.0` yayınlanmayacak: paket imzasız ve gerçek bir Windows
makinesinde hiç açılmadı. *"Kaynak yeşil ≠ ürün çalışıyor"* (Yuki v0.5.0 dersi).

---

## Liste geçtikten sonra (bende — 3 adım, ~5 dk)

1. ~~`gh release edit v1.1.0 --draft=false`~~ → **yapıldı 2026-08-08**; güncel sürüm **v1.1.1** (2026-08-15)
2. ~~`ihsan-web-site` reposunda `galleryweb-v1.1.0` dalını main'e al + push~~ →
   ⛔ **BU DALI MERGE ETME.** Dal main'in 29 commit GERİSİNDE; merge edilirse
   `takip.html`/`takip.css` gibi canlı sayfaları geri siler. İçeriği zaten
   2026-08-15'te doğrudan main'e uygulandı (indirme bandı v1.1.1). Dal ölü.
   (indirme linkleri o an canlıya çıkar — release'den ÖNCE push edilirse 404 verir)
3. Sürüm notlarındaki yorum satırına gerçek makine doğrulaması eklenir
