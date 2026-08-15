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

**https://github.com/ihsandeniz/galleryweb/releases → `v1.1.2` (Latest)**
→ **`GalleryWeb_1.1.2_x64-setup.exe`** (**247 MB**)

Sürüm **herkese açık** — VM'in içinden tarayıcıyla doğrudan indirebilirsin.

> 🔎 **İndirmeden önce 5 saniyelik kontrol:** dosya adında **1.1.2** yazmalı ve boyut
> **247 MB** olmalı. Başka bir sayı görüyorsan eski sürüme bakıyorsundur — indirme, haber ver.

> ⚠️ **VM'in İÇİNDEN, tarayıcıyla indir.** Paylaşılan klasörle kopyalarsan dosyaya
> *Mark of the Web* basılmaz, SmartScreen hiç çıkmaz ve aşağıdaki 1. madde **sahte geçer**.

> Bu paket **imzasız**. Aşağıdaki 1. madde tam olarak bunu sınıyor — beklenen davranıştır.

> 🐧 **Linux tarafı bu listeye girmiyor** — 2026-08-15'ten beri paketler CI'da derleniyor
> ve her koşuda `debian:12` kabında kurulup çalıştırılarak doğrulanıyor
> (`tests/linux_paket_dogrula.sh`). Windows'ta böyle bir otomatik kapı **kurulabilir
> değil**: SmartScreen, Defender ve Controlled Folder Access ancak gerçek bir makinede
> davranır. Bu listenin var olma sebebi budur.

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

### 8. `guncelle.bat` — hiç çalıştırılmadı (⭐ ikinci kritik madde)
Kaynaktan kurulum yolunu kullananlar için güncelleyici. **Bugüne kadar gerçek bir
Windows'ta hiç koşmadı** ve Wine'da sınanamıyor: Wine'ın sahte `powershell`'i hiçbir
şey yapmadan `0` döndürdüğü için betik **başarısız güncellemeye "[TAMAM]" der** —
yani yeşil çıktısı kanıt değil.

- [ ] Depoyu ZIP olarak indir → aç → `run.bat` ile bir kez çalıştır (galeri açılsın)
- [ ] `guncelle.bat`'a çift tıkla
- [ ] **Beklenen:** indirir, kodun üstüne kopyalar, `.venv` / `photos` / ayarlar **korunur**
- [ ] Sonra `run.bat` → galeri hâlâ açılıyor mu, fotoğrafların yerinde mi?
- [ ] Ekranda hata çıktıysa **ham metni** yaz (özetleme — sahte "[TAMAM]" avlıyoruz)

---

## Sonucu nasıl ilet

Listeyi kopyalayıp yanına yazman yeterli. Özellikle şunları belirt:

- **5. madde** (Controlled Folder Access) — açık mıydı, kaydetme çalıştı mı?
- **3. madde** açılış süresi — onedir kararının ölçüsü
- Beklenmedik her ekran görüntüsü

> ⚠️ **Bu liste bir yayın kapısıydı, artık değil — ve bu bir gerileme.** `v1.1.0`
> 2026-08-08'de, `v1.1.1` ve `v1.1.2` 08-15'te liste tamamlanmadan yayınlandı.
> Yani **şu an yayında olan Windows paketi hiçbir gerçek Windows makinesinde
> açılmamış durumda**; doğrulama CI koşusuna, paket duman testine ve Wine turuna
> dayanıyor. Üçü de "kurulum makinesinde ne oluyor" sorusuna cevap vermez.
> *"Kaynak yeşil ≠ ürün çalışıyor"* (Yuki v0.5.0 dersi).

---

## Liste geçtikten sonra (bende)

1. Sonuçlar `WIKI/sources/projects/2026-05-03-galleryweb.md` § FAZ W3'e, ham hâliyle işlenir
2. Çıkan her kusur için önce **başarısız bir test** yazılır, sonra düzeltilir
3. Düzeltme gerekiyorsa yeni yama sürümü (v1.1.3) CI'dan çıkar — paket elle derlenmez

> Eski 1. ve 2. adım (`release --draft=false` + site dalını merge) **artık geçersiz**:
> sürüm 08-08'de yayına girdi, site indirme bandı da 08-15'te doğrudan `main`'e
> uygulandı. ⛔ `ihsan-web-site`'taki `galleryweb-v1.1.0` dalını **merge etme** —
> main'in 29 commit gerisinde, `takip.html`/`takip.css` gibi canlı sayfaları geri siler.
