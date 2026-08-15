# GalleryWeb v1.1.1 — Linux paketleri artık gerçekten dağıtılabilir

**v1.1.0'ın Linux paketi bozuktu ve bu sürüm onu kapatıyor.** Uygulamanın kendisinde
davranış değişikliği yok — değişen şey paketlerin **nerede derlendiği**. Bir Linux
paketi, derlendiği makinenin glibc'sini taban alır ve daha eskisinde açılmaz;
v1.1.0'a kadar paketler geliştiricinin Arch kurulumunda (glibc 2.44) üretiliyordu.

## 📥 İndir

| Platform | Dosya |
|---|---|
| **Windows 10 / 11** | `GalleryWeb_1.1.1_x64-setup.exe` |
| **Linux — Debian 12+ / Ubuntu 22.04+** | `GalleryWeb_1.1.1_amd64.deb` |
| **Linux — kurulumsuz** | `GalleryWeb_1.1.1_amd64.AppImage` (**geri döndü**) |

> **Windows'ta “Windows bilgisayarınızı korudu” uyarısı çıkacak.** Paket imzasızdır —
> kod imzalama sertifikası yıllık $200-400 ve bu ücretsiz, açık kaynak bir proje.
> **Ek bilgi → Yine de çalıştır** deyin. Paket bir geliştiricinin bilgisayarında değil,
> bu depodan **GitHub Actions'ta herkese açık şekilde** derleniyor.

## 🐧 Ne düzeldi

### AppImage geri geldi
v1.0.0'ın AppImage'ı derleyen makinenin sistem kütüphanelerini paketlediği için
Debian 13 ve Ubuntu 24.04 dahil **hiçbir LTS'te açılmıyordu** (`GLIBC_2.43 not found`);
v1.1.0'da bu yüzden bilerek yayınlanmamıştı. Artık `ubuntu-22.04` üzerinde üretiliyor
ve `debian:12` kabında gömülü kütüphanelerinin tamamı çözülüyor.

### deb artık Debian 12 ve Ubuntu 22.04'te de çalışıyor
v1.1.0'ın deb'i `GLIBC_2.39` istiyordu → bu dağıtımlarda açılmıyordu. Yeni taban **2.35**.

### deb sessizce kurulup sonra ölmüyor
Daha sinsi olan kusur buydu: paket `libc6` alt sınırını **beyan etmiyordu**, dolayısıyla
`apt` onu eski bir dağıtıma da sorunsuzca kuruyor, kullanıcı ancak uygulamayı açmayı
deneyince başlamadığını görüyordu. Paket artık `libc6 (>= 2.35)` beyan ediyor — uymayan
sistemde apt **kurmayı reddediyor**. Ölçüldü (`debian:11`):
`Depends: libc6 (>= 2.35) but 2.31-13+deb11u14 is to be installed`.

### Uygulama artık kendi sürümünü söylüyor
Paketler `1.1.0` derken çalışan uygulama kendini API'de `0.1.0` diye tanıtıyordu.
Sürüm dört yüzeyde de aynı ve bir test bunu her CI koşusunda ölçüyor
(`tests/test_surum_tutarliligi.py`) — bir daha ayrışamaz.

## 🔒 Bir daha olmaması için ne eklendi

Paketler yayınlanmadan önce **vaat ettiğimiz en eski dağıtımın içinde açılıyor.**
`tests/linux_paket_dogrula.sh` her CI koşusunda `debian:12` kabında:

- deb'i `apt install` ile **gerçekten kurar** (bağımlılıklar çözülüyor mu)
- kurulan arayüz ikilisinin bağımlılıklarını dener (`not found` var mı)
- deb'in ve AppImage'ın **içindeki sunucuyu çalıştırır** — sunucu kalkıyor mu, galeri
  listeleniyor mu, küçük resim üretiliyor mu, süreç temiz kapanıyor mu
- AppImage'ın gömülü kütüphanelerini **AppRun'ın yükleme sırasıyla** çözer
- tüm ELF'lerin istediği en yüksek glibc sürümünü sınırla karşılaştırır

> Neden çalıştırarak ölçüyoruz: PyInstaller tek-dosya arşivi kütüphaneleri **sıkıştırılmış**
> taşır, dışarıdan bakan hiçbir ELF aracı içeriğini göremez. v1.1.0'da paket "glibc 2.14
> yeter" diyor ve yanlış söylüyordu.

Doğrulama betiği ayrıca **bilinen-bozuk v1.1.0 paketine karşı** sınandı: ilk kapıda
kırmızı verdi (`GLIBC_2.39 not found`). Kırmızı verdiği görülmeden yeşiline güvenilmedi.

## Bilinen sınırlar

- Paket **imzasız** — SmartScreen uyarısı çıkar (yukarıya bakın).
- **Video kesme için `ffmpeg` gerekir**; fotoğrafların hepsi ffmpeg'siz çalışır.
- macOS paketi yok (derlenmedi, planlanmadı).
- Doğrulama **arayüz penceresini açmaz** — CI kabında ekran sunucusu yok. Sınanan şey
  bağımlılıkların çözülmesi ve sunucu katmanının koşmasıdır; pencerenin görsel testi
  ayrı yapılır.
- Gerçek bir Windows makinesinde kurulum turu **hâlâ yapılmadı** — Windows doğrulaması
  CI koşusuna ve paket duman testine dayanıyor (`desktop/WINDOWS-TEST.md`).
- **Debian 11 / Ubuntu 20.04 ve öncesi desteklenmiyor** — apt açıkça reddeder.
  O sistemlerde kaynaktan çalıştırın (`run.sh`), glibc kısıtı yoktur.

**Tam değişiklik listesi:** https://github.com/ihsandeniz/galleryweb/compare/v1.1.0...v1.1.1
