# GalleryWeb — Masaüstü Uygulaması

Aynı GalleryWeb, tarayıcı yerine kendi penceresinde. Kullanıcının bilgisayarında
**Python kurulu olması gerekmez** — sunucu tek dosya binary olarak uygulamanın
içinde gelir.

```
┌──────────────────────────────────────────────┐
│  Tauri kabuğu (Rust, ~5 MB)                  │
│   • boş port seçer                           │
│   • sunucuyu başlatır (127.0.0.1)            │
│   • hazır olunca pencereyi o adrese açar     │
│   • kapanınca sunucuyu da kapatır            │
└───────────────┬──────────────────────────────┘
                │ spawn + stdin borusu
┌───────────────▼──────────────────────────────┐
│  galleryweb-server (PyInstaller, ~55 MB)     │
│   backend/main.py — yerel mod, login yok     │
│   frontend/ varlıkları binary'nin içinde     │
└──────────────────────────────────────────────┘
```

## Derleme

```bash
cd desktop
./yap.sh              # sunucu binary'si + kurulabilir paketler
./yap.sh sunucu       # sadece sunucu binary'si
./yap.sh calistir     # geliştirme: derle + uygulamayı aç
```

Çıktılar: `desktop/src-tauri/target/release/bundle/` (AppImage · deb · Windows'ta NSIS).

**Gereksinimler:** Python 3.10–3.13 · Rust (`cargo`) · `cargo install tauri-cli --version "^2.0"` ·
Linux'ta `webkit2gtk-4.1` · video kırpma için `ffmpeg` (opsiyonel).

## Windows 10 / 11

**Paket Windows üzerinde derlenmelidir.** PyInstaller çapraz derleme yapmaz;
Linux'ta üretilen sunucu binary'si Windows'ta çalışmaz. Kod hazır, derleme betiği
hazır — tek gereken bir Windows makinesi.

```powershell
cd desktop
.\yap.ps1              # galleryweb-server.exe + NSIS kurulum paketi
.\yap.ps1 sunucu       # sadece sunucu exe'si
.\yap.ps1 calistir     # geliştirme: derle + uygulamayı aç
```

Gereksinimler: Python 3.10–3.13 (python.org, "Add Python to PATH" işaretli —
**Microsoft Store kısayolu gerçek Python değildir**) · Rust · `cargo install
tauri-cli --version "^2.0"` · WebView2 (Win 10/11'de genelde kurulu).

Windows için özel olarak yapılanlar:

| Konu | Neden gerekti |
|---|---|
| Küçük resim havuzu Windows'ta **iş parçacığı** havuzu | Orada multiprocessing `spawn` yapar → her işçi 55 MB'lık exe'yi baştan açardı; `freeze_support()` olmadan süreç bombası |
| `multiprocessing.freeze_support()` | PyInstaller + spawn için zorunlu |
| Kaynak eşlemesi platforma özel (`tauri.windows.conf.json`) | Sunucu dosyası Windows'ta `.exe` uzantılı; tek yapılandırma paketlemeyi düşürürdü |
| ffmpeg yoksa video yer tutucusu | Windows'ta ffmpeg varsayılan kurulu değil — eskiden her video kutucuğu 500 veriyordu |
| Veri dizini `%LOCALAPPDATA%` | Program dizini salt-okunur |
| Sunucu penceresi gizli (`CREATE_NO_WINDOW`) | Arkada siyah konsol açılmasın |

Doğrulama (Linux'tan yapılabildiği kadarıyla): Rust'ın Windows hedefiyle tip
kontrolü geçti (`cargo check --target x86_64-pc-windows-msvc`) — `#[cfg(windows)]`
dalları derleniyor. Python tarafında Windows'a giden dallar zorlanarak test edildi
(9/9): iş parçacığı havuzu seçimi, o havuzla gerçek küçük resim üretimi, bozuk
dosyanın yer tutucuya düşmesi, iki yer tutucu biçimi, `freeze_support` sırası,
`killpg`'nin POSIX'e kapatılması.

⚠️ **Gerçek Windows'ta hâlâ denenmedi:** exe üretimi, NSIS kurulumu, pencerenin
açılması, WebView2 davranışı. Bunlar ancak Windows makinede koşularak kapanır.
Ayrıca kurulum paketi **imzasız** olacağı için SmartScreen uyarısı çıkar
("Daha fazla bilgi" → "Yine de çalıştır").

## Tasarım kararları

**Neden gömülü sunucu, neden tam yeniden yazım değil?**
`backend/main.py` zaten tamamen bağımsız (Supabase/DB import etmez). Masaüstü sürümü
onu olduğu gibi kullanır — web ve masaüstü **tek kod tabanı**, davranış farkı yok.
Aynı test paketi hem kaynaktan hem paketlenmiş binary'ye karşı koşuyor.

**Neden dinamik port?**
Sabit 5000 kullanıcının başka bir uygulamasıyla (veya GalleryWeb'in Docker kopyasıyla)
çakışırdı. Kabuk her açılışta işletim sisteminden boş port ister.

**Neden yalnız 127.0.0.1?**
Yerel modda kimlik doğrulama **yoktur**. `0.0.0.0` dinlemek galeriyi tüm yerel ağa
açardı. Masaüstü sürümü bilinçli olarak yalnızca bu makineye bağlanır. (Telefondan
erişmek isteyenler için terminalden `python main.py` yolu duruyor.)

**Sunucu arkada kalır mı?**
Kalmaz. Kabuk sunucuyu, ucunu açık tuttuğu bir stdin borusuyla başlatır; kabuk hangi
sebeple olursa olsun sonlanınca (kapatma, çökme, `kill -9`) boru kapanır ve sunucu
kendini sonlandırır. Sinyal iletmeye kıyasla üstünlüğü: PyInstaller tek-dosya
paketinde asıl Python süreci bootloader'ın çocuğudur ve sinyalle temizlik onu
ıskalıyordu. Bu yöntem Windows/macOS/Linux'ta aynı çalışır.

**Veriler nereye yazılıyor?**
Program dosyaları salt-okunur geçici bir dizinde açıldığı için önbellek oraya
yazılamaz. Thumbnail veritabanı ve önbellek platform standardı kullanıcı veri
dizinine gider (Linux `~/.local/share/…`, Windows `%LOCALAPPDATA%`,
macOS `~/Library/Application Support`). `GALLERYWEB_DATA_DIR` ile değiştirilebilir.
**Fotoğraflarınız hiçbir zaman kopyalanmaz** — galeri onları bulundukları yerde okur.

**Paket neden 55 MB?**
Yerel mod yalnızca hafif bağımlılıkları (`requirements-selfhost.txt`) kullanır.
Bulut modunun ağır paketleri (torch, transformers, supabase, sqlalchemy…) derleme
sırasında bilinçle dışlanır; onlarla paket ~2.5 GB olurdu.

## Doğrulama

Sanal ekranda (Xvfb) uçtan uca test — senin masaüstünü etkilemez:

| Kontrol | Durum |
|---|---|
| Uygulama açılıyor, sunucu sidecar'ı başlıyor | ✅ |
| Yalnız `127.0.0.1`'e bağlı (LAN'a açık değil) | ✅ |
| Dinamik port seçiliyor (sabit 5000 değil) | ✅ |
| Sunucu HTTP 200 veriyor | ✅ |
| Webview uygulamayı yüklüyor (index + tüm JS/CSS/font/sw) | ✅ |
| Önbellek kullanıcı veri dizinine yazılıyor | ✅ |
| `kill -9` sonrası arkada sunucu kalmıyor | ✅ |
| Paketlenmiş binary, kaynak sürümle aynı davranıyor | ✅ 36/36 test |

Üretilen AppImage, son kullanıcı gibi (kurulum yapmadan, temiz veri dizeniyle) ayrıca denendi:
çalıştı · gömülü sunucu kalktı · HTTP 200 · webview galeriyi yükledi · gerçek klasörden 7 dosya
listeledi · önbellek doğru dizine yazıldı · `kill -9` sonrası zombi kalmadı.

> **Testin kendisinde bulunan tuzak:** paket testleri geliştirme makinesinde koşarken
> `desktop/dist/` klasörü de duruyor. Kod önce paket içindeki kaynağa, bulamazsa bu
> geliştirme yoluna düşüyordu — yani paketleme bozuk olsa bile test GEÇİYORDU. Artık
> doğrulama, `dist/` klasörü geçici olarak saklanarak yapılıyor; çalışan sürecin yolu
> `/tmp/.mount_…/usr/lib/GalleryWeb/galleryweb-server` olarak teyit ediliyor.

> **Not:** Doğrulamalar başsız (headless) sanal ekranda yapıldı; pencere içeriğinin
> piksel görüntüsü alınamadı (X sunucusunda pencere yöneticisi yok). Arayüzün kendisi
> aynı sürümle Chromium'da görsel olarak doğrulanmıştır (Faz 9/10 testleri).

## Paket boyutları

| Paket | Boyut | Not |
|---|---|---|
| `.deb` | 54 MB | Sistem GTK/WebKit'ini kullanır |
| `.AppImage` | 147 MB | GTK/WebKit'i de içine alır — hiçbir bağımlılık istemez |

## Video oynatma (AppImage)

WebKit videoları GStreamer ile oynatır. AppImage varsayılan olarak yalnızca
GStreamer'ın **çekirdek kütüphanelerini** alıyor, **eklentilerini** almıyordu →
`GStreamer element appsink/autoaudiosink not found` + ardından NULL işaretçi
kritiği ile WebProcess çöküyor, yani pencere komple gidiyordu.

`bundleMediaFramework` açıldı; pakette artık 194 GStreamer eklentisi var
(`libgstapp.so`, `libgstautodetect.so` dahil). Bu eklentiyi çalıştıran
linuxdeploy betiği **`patchelf` ister** — yoksa AppImage adımı tümden çöker,
`yap.sh` bunu baştan söyler.

Video **poster kareleri** ayrı bir yoldur (sunucu tarafında `ffmpeg`), her
zaman çalışır; ffmpeg pakete gömülmez, sistemden kullanılır.

## Ölçek

600 üretilmiş fotoğrafla sunucu stres testi (1800 küçük resim isteği, 48'e kadar
eşzamanlı): **600/600 başarılı, tek hata yok**, sunucu ayakta, ~850 MB tepe RSS.
9.549 fotoğrafluk gerçek arşivde listeleme: sayfa başına 50 kayıt, 6.5 KB yanıt,
0.76 s, 76 MB RSS. Ön yüz 9.549 fotoğrafta sayfa sayfa gezildi ve `per_page=500`
zorlandı: JS yığını 10 MB'de sabit, kart sayısı sayfa başına sınırlı, çökme yok.
Yani "çok resim" tek başına çökme sebebi değil — çökmenin kaynağı yukarıdaki
GStreamer eksikliğiydi.

## Bilinen tuzak

AppImage adımı `linuxdeploy` içindeki eski `strip` yüzünden modern dağıtımlarda
(`.relr.dyn` bölümü) çöküyor. `yap.sh` bunu `NO_STRIP=true` ile aşar; elle
derliyorsan aynı değişkeni geçmelisin.
