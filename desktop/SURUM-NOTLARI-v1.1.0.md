# GalleryWeb v1.1.0 — Windows masaüstü uygulaması

**v1.0.0'da eksik olan tek şey Windows paketiydi. Bu sürüm onu kapatıyor** — ve
yolda, Windows'ta sessizce yanlış çalışan altı davranış düzeltildi.

## 📥 İndir

| Platform | Dosya |
|---|---|
| **Windows 10 / 11** | `GalleryWeb_1.1.0_x64-setup.exe` |
| **Linux (taşınabilir)** | `GalleryWeb_1.1.0_amd64.AppImage` |
| **Linux (Debian/Ubuntu)** | `GalleryWeb_1.1.0_amd64.deb` |

> **Windows'ta “Windows bilgisayarınızı korudu” uyarısı çıkacak.** Paket imzasızdır —
> kod imzalama sertifikası yıllık $200-400 ve bu ücretsiz, açık kaynak bir proje.
> **Ek bilgi → Yine de çalıştır** deyin. Ne çalıştırdığınızı doğrulayabilirsiniz:
> paket bir geliştiricinin bilgisayarında değil, bu depodan **GitHub Actions'ta
> herkese açık şekilde** derleniyor.

## 🪟 Windows'ta düzeltilenler

Hepsi *"Linux'ta sorunsuz, Windows'ta hata vermeden yanlış"* sınıfından. Hiçbiri
istisna fırlatmıyordu — kullanıcı sadece işin **olmadığını** görüyordu.

- **Telefon “zaman aşımı” diyor, sebebi söylenmiyordu.** Windows'ta gelen bağlantılar
  varsayılan olarak engellidir ve izin penceresi görünmeyebilir. Uygulama artık güvenlik
  duvarını tespit edip **kopyalanabilir `netsh` komutunu** ve yönetici uyarısını gösteriyor.
- **Açık dosya silinince “silindi” deniyordu.** Windows açık dosyayı taşıtmaz. Video
  oynarken silme/kesme artık kısa süre yeniden deniyor, olmazsa *"dosya başka bir program
  tarafından kullanılıyor"* diyor. Geri yükleme aynı adlı dosyayı **artık ezmiyor**.
- **Derin klasörde düzenlemeler kayboluyordu.** 260 karakter (MAX_PATH) sınırını aşan
  yollarda düzenleme geçmişi sessizce yazılamıyordu.
- **Etiket/puan/çöp filtreleri boş gelebiliyordu.** Klasör yolu ile fotoğraf yolları
  farklı biçimlerde saklanıyordu (Windows'ta büyük-küçük harf, Linux'ta sembolik bağ).
- **ffmpeg yokken çıplak 500 hatası.** Video kesme artık ne eksik olduğunu ve nasıl
  kurulacağını söylüyor. Ayrıca ffmpeg çağrılarında **konsol penceresi yanıp sönmüyor**.
- **Küçük resimler yanlış MIME türüyle gidiyordu** (`.webp` Windows kayıt defterinde
  kayıtlı değil) — video akışını bozabilecek bir tutarsızlık.
- **Türkçe/emoji çıktı sunucuyu çökertiyordu.** Windows konsolu (cp1252) `ğ`/`ş`/emoji
  kodlayamıyor; telefon erişimi açıldığında yazılan uyarı satırı sunucuyu düşürüyordu.

## 📦 Paketleme değişiklikleri

- **Windows paketi klasör düzeninde (onedir).** Tek dosya paket her açılışta ~55 MB'ı
  `%TEMP%`'e açıyordu — Defender her seferinde baştan tarıyor, açılış uzuyordu.
- **WebView2 çevrimdışı kurucu gömüldü.** Kurulum artık internet istemiyor. (Varsayılan
  davranış indirmekti; internetsiz makinede uygulama hiç açılmıyordu.)
- **Paket artık CI'da üretiliyor.** Her push'ta testler gerçek Windows'ta koşuyor, paket
  derleniyor ve kurulum dosyası **açılıp içeriği doğrulanıyor**.

## 🧹 Yayınlanmamış bulut katmanı depodan kaldırıldı

Bu sürüm aynı zamanda **hiç yayınlanmamış** bir çok kullanıcılı "bulut modu"
iskeletini deponun dışına çıkarıyor (`3814181`, `024f94d` — 48 dosya, −3816 satır):

- **Arayüzdeki ☁ düğmesi gitti.** Düğme çalışmayan bir moda geçiriyordu; tercih
  tarayıcıda saklandığı için bir kez basan kullanıcı galeriyi **kapatıp açsa bile**
  bozuk modda kalıyordu. Sürüm, eski tercihi açılışta temizler — bir şey yapmanız
  gerekmez.
- **Sabit parolalı "demo giriş"** (`DEMO_USERS`, `/auth/*`) kaldırıldı. Açık kaynak
  bir depoda parola sabitlemek, kimse kullanmasa bile yanlıştı.
- Supabase CLI'ın bıraktığı `supabase/.temp/` klasörü depoya girmişti — silindi ve
  `.gitignore`'a eklendi.

Yerel modu (tek mod) kullanan hiçbir davranış değişmedi.

## 🧪 Bu sürüm nasıl doğrulandı

- **28 otomatik test — hem Linux hem Windows'ta.** Aynı takım iki işletim sisteminde
  koşar, platforma özgü olanlar diğerinde atlanır: Linux'ta 24 geçti / 4 atlandı,
  Windows'ta 27 geçti / 1 atlandı (CI koşusu `19acaf09`).
- Paket duman testi: derlenen exe gerçekten çalıştırılıp galeri, Türkçe dosya adları,
  küçük resim üretimi ve düzenleme zinciri sınanıyor
- NSIS kurulum paketi açılıp sunucunun içinde olduğu doğrulanıyor

<!-- W3 tamamlanınca buraya eklenecek:
- Gerçek Windows 10/11 makinesinde kurulum + kullanım turu (bkz. desktop/WINDOWS-TEST.md)
-->

## Bilinen sınırlar

- Paket **imzasız** — SmartScreen uyarısı çıkar (yukarıya bakın).
- **Video kesme için `ffmpeg` gerekir**; fotoğrafların hepsi ffmpeg'siz çalışır.
- macOS paketi yok (derlenmedi, planlanmadı).

**Tam değişiklik listesi:** https://github.com/ihsandeniz/galleryweb/compare/v1.0.0...v1.1.0
