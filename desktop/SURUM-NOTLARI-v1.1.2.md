# GalleryWeb v1.1.2 — harita görünümü ilk kez gerçekten çalışıyor

**Harita görünümü bugüne kadar hiçbir fotoğrafı göstermedi.** Hata vermiyordu,
boş bir harita açıyordu — bu yüzden yıllarca fark edilmedi. v1.1.2 onu düzeltiyor.

## 📥 İndir

| Platform | Dosya |
|---|---|
| **Windows 10 / 11** | `GalleryWeb_1.1.2_x64-setup.exe` |
| **Linux — Debian 12+ / Ubuntu 22.04+** | `GalleryWeb_1.1.2_amd64.deb` |
| **Linux — kurulumsuz** | `GalleryWeb_1.1.2_amd64.AppImage` |

## 🗺 Ne düzeldi

Fotoğraflarının GPS koordinatını okuyup haritada gösteren özellik **iki ayrı
sebepten** kırıktı ve ikisi de sessizdi:

1. **Koordinat okuyucu kurulu değildi.** GPS'in tek kaynağı `pyexiv2` kütüphanesiydi;
   o da kurulum listesinde hiç yer almıyordu. Kütüphane bulunamayınca hata
   bastırılıyor, harita boş açılıyordu. Artık GPS, zaten kurulu olan **Pillow** ile
   de okunuyor — ek kurulum gerekmiyor.
2. **Okuyucu kurulu olsa bile ayrıştırma yanlıştı.** Koordinat metin olarak
   `38/1 25/1 201/25` biçiminde geliyor; kod bunun yerine üç ayrı parçadan oluşan
   bir liste bekliyordu, dolayısıyla her fotoğrafta sessizce başarısız oluyordu.
   Artık üç biçimi de kabul ediyor.

**Sonuç:** GPS bilgisi olan fotoğrafların çekildiği yerler haritada işaretleniyor.
Koordinatı olmayan fotoğraflar haritaya girmiyor (uydurma konum yok).

> **Gizliliğin değişmedi.** Harita altlığı (arka plandaki sokak haritası) hâlâ
> **varsayılan olarak kapalı** ve açık onay istiyor; onay vermeden koordinatların
> hiçbir yere bildirilmez. Bu sürümle birlikte bu güvence artık **her CI koşusunda
> otomatik ölçülüyor** (aşağıya bakın).

## 🔒 Gizlilik vaadi artık otomatik ölçülüyor

"Fotoğraflarınla ilgili hiçbir şey dışarı gitmez" cümlesi bu projenin ana vaadi.
Bugüne kadar bunu doğrulayan test vardı ama yalnızca elle çalıştırılıyordu — yani
bir gün bir dış bağlantı geri sızsa kimse fark etmeyecekti.

Artık her değişiklikte otomatik olarak: uygulama açılır, harita görünümüne girilir
ve **kendi bilgisayarın dışına giden her istek** kaydedilir. Onay verilmeden tek bir
dış bağlantı çıkarsa sürüm kırmızı yanar ve yayınlanamaz.

## Bilinen sınırlar

- Paket **imzasız** — Windows'ta SmartScreen uyarısı çıkar: **Ek bilgi → Yine de çalıştır**.
- **Video kesme için `ffmpeg` gerekir**; fotoğrafların hepsi ffmpeg'siz çalışır.
- macOS paketi yok (derlenmedi, planlanmadı).
- Paket doğrulaması **arayüz penceresini açmaz** — CI kabında ekran yok; sınanan şey
  bağımlılıkların çözülmesi ve sunucu katmanının koşmasıdır.
- Gerçek bir Windows makinesinde kurulum turu **hâlâ yapılmadı** (`desktop/WINDOWS-TEST.md`).
- **Debian 11 / Ubuntu 20.04 ve öncesi desteklenmiyor** — apt açıkça reddeder;
  o sistemlerde kaynaktan çalıştır (`run.sh`), glibc kısıtı yoktur.

**Tam değişiklik listesi:** https://github.com/ihsandeniz/galleryweb/compare/v1.1.1...v1.1.2
