# GalleryWeb v1.1.3 — kopya bulucu ve toplu taşıma gerçekten çalışıyor

**İki özellik sessizce kırıktı, ikisi de bu sürümde düzeldi.** Hiçbiri hata mesajı
göstermiyordu — biri Linux'ta hep boş dönüyordu, öbürü "başarısız" derken dosyaları
zaten taşımıştı.

## 📥 İndir

| Platform | Dosya |
|---|---|
| **Windows 10 / 11** | `GalleryWeb_1.1.3_x64-setup.exe` |
| **Linux — Debian 12+ / Ubuntu 22.04+** | `GalleryWeb_1.1.3_amd64.deb` |
| **Linux — kurulumsuz** | `GalleryWeb_1.1.3_amd64.AppImage` |

## 🔍 Kopya bulucu Linux'ta hiç çalışmamış

"Benzer fotoğrafları bul" özelliği **Linux ve macOS'ta her çağrıldığında hata
veriyordu** (HTTP 500). Windows'ta çalışıyordu — bu yüzden fark edilmesi zordu.

Sebep, işi arka plandaki işçi süreçlere gönderme biçimiydi: gönderilen görev
Windows'ta iş parçacığına, Linux'ta ayrı bir sürece gidiyor ve ayrı süreç
yalnızca "paketlenebilir" bir görev kabul ediyor. Gönderilen görev paketlenemeyen
türdendi → Linux'ta istek daha başlamadan düşüyordu.

**Sonuç:** kopya bulucu artık her üç platformda da çalışıyor.

## 📦 Toplu taşıma: "başarısız" diyordu ama dosyalar taşınmıştı

Birden çok fotoğrafı başka bir klasöre taşıdığında uygulama **hepsi için hata
gösteriyordu** — oysa dosyalar hedefe çoktan gitmişti. Kullanıcı açısından en kötü
hâli şuydu: hata görürsün, kaynak klasöre bakarsın, dosyalar yoktur.

Aynı hatanın ikinci bir sonucu daha vardı: **taşınan fotoğrafların etiketleri,
favorileri, puanları ve notları taşınmıyordu.** Dosya yeni yerine gidiyor, ona
verdiğin bilgiler eski yolda kalıyordu — yani sessizce kayboluyorlardı.

Kök neden küçük ve tekti: notların tutulduğu tablonun sütun adı kodda yanlış
yazılmıştı; bu, bilgi aktarımının **tamamını** ilk adımda durduruyordu.

**Ayrıca:** bilgi aktarımı bundan sonra başarısız olsa bile taşıma artık "başarısız"
diye raporlanmıyor — dosya gerçekten taşındıysa öyle yazılıyor, sorun ayrıca bildiriliyor.

## 🐍 Python 3.14 desteği

Kaynaktan çalıştıranlar için: `run.sh` / `run.bat` artık Python 3.14'ü de kabul
ediyor. Daha önce "bu sürüm çok yeni olabilir" uyarısı veriyordu; bu uyarı eskiydi
ve ölçüldü — 3.14 ile kurulum sorunsuz tamamlanıyor. Arch ve Fedora gibi 3.14'ün
varsayılan olduğu sistemlerde artık gereksiz uyarı çıkmaz.

## 🧹 Ölü kod temizliği

- Erişilebilir ama **bozuk** bir `/share` sayfası vardı: açılıyor, ama arkasındaki
  servis bu üründe hiç bulunmadığı için hiçbir veri gelmiyordu. Kaldırıldı.
- Her sayfa açılışında indirilen ama hiçbir zaman çalışmayan bir arama betiği
  kaldırıldı. **Galerideki normal arama kutusu bundan etkilenmez** — o ayrı bir
  koddur ve çalışmaya devam ediyor.

## 🧪 Test kapsamı büyütüldü

Bu sürümün asıl işi buydu: dosya **silen, taşıyan ve kopyalayan** uçların hiç testi
yoktu. Yukarıdaki iki hata da zaten bu testler yazılırken ortaya çıktı.

Otomatik test sayısı **36 → 57**. Yeni eklenenler özellikle şunları ölçüyor:
hedefte aynı adlı dosya varsa **üzerine yazılmıyor** · taşınan dosyanın etiketi
birlikte gidiyor · silinen dosya çöp kutusundan geri gelebiliyor · albüm işlemleri ·
kopya bulucunun hem doğru gruplaması hem farklı fotoğrafları ayırması.

## Bilinen sınırlar

- Paket **imzasız** — Windows'ta SmartScreen uyarısı çıkar: **Ek bilgi → Yine de çalıştır**.
- **Video kesme için `ffmpeg` gerekir**; fotoğrafların hepsi ffmpeg'siz çalışır.
- macOS paketi yok (derlenmedi, planlanmadı).
- Paket doğrulaması **arayüz penceresini açmaz** — CI kabında ekran yok; sınanan şey
  bağımlılıkların çözülmesi ve sunucu katmanının koşmasıdır.
- Gerçek bir Windows makinesinde kurulum turu **hâlâ yapılmadı** (`desktop/WINDOWS-TEST.md`).
- **Debian 11 / Ubuntu 20.04 ve öncesi desteklenmiyor** — apt açıkça reddeder;
  o sistemlerde kaynaktan çalıştır (`run.sh`), glibc kısıtı yoktur.
- Kopya bulucu, **detaysız düz renkli** görsellerde (tek renk arka planlar gibi)
  yanılabilir — kullanılan algılama yöntemi ayrıntıya dayanır. Gerçek fotoğraflarda
  bu sınır pratikte görünmez.

**Tam değişiklik listesi:** https://github.com/ihsandeniz/galleryweb/compare/v1.1.2...v1.1.3
