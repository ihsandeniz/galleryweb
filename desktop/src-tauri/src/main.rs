// GalleryWeb masaüstü kabuğu
//
// Tauri yalnızca bir pencere + süreç yöneticisidir: asıl uygulama, yanına
// paketlenmiş `galleryweb-server` (PyInstaller ile tek dosya yapılmış FastAPI
// yerel modu) tarafından servis edilir. Kabuk şunları yapar:
//   1. boş bir port seçer (sabit 5000 çakışmasın)
//   2. sunucuyu 127.0.0.1'e bağlı olarak başlatır (LAN'a AÇILMAZ — yerel modda
//      kimlik doğrulama yoktur)
//   3. sunucu yanıt verene kadar bekler, sonra pencereyi o adrese açar
//   4. uygulama kapanınca sunucuyu da öldürür (arkada zombi süreç kalmaz)
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::ErrorKind;
use std::net::{Ipv4Addr, SocketAddrV4, TcpListener, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use tauri::{Manager, RunEvent, WebviewUrl, WebviewWindowBuilder};

/// Sunucu sürecini uygulama ömrü boyunca tutar; Drop/Exit'te öldürülür.
struct ServerProcess(Mutex<Option<Child>>);

impl ServerProcess {
    fn kill(&self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(mut child) = guard.take() {
                // 1) Boruyu kapat → sunucu kendini düzgünce sonlandırır (iç Python
                //    süreci dahil). 2) Kısa bekle. 3) Hâlâ duruyorsa zorla öldür.
                drop(child.stdin.take());
                for _ in 0..20 {
                    match child.try_wait() {
                        Ok(Some(_)) => return,
                        Ok(None) => std::thread::sleep(Duration::from_millis(100)),
                        Err(_) => break,
                    }
                }
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

/// İşletim sisteminden boş bir port iste (0 = "sen seç"), sonra bırak.
/// Küçük bir yarış penceresi var ama sunucu hemen ardından bağlanıyor.
fn pick_free_port() -> u16 {
    TcpListener::bind(SocketAddrV4::new(Ipv4Addr::LOCALHOST, 0))
        .and_then(|l| l.local_addr())
        .map(|a| a.port())
        .unwrap_or(5000)
}

/// Sunucu binary'sinin yeri:
///  • paketlenmiş uygulamada → resources/
///  • geliştirmede           → desktop/dist/ (PyInstaller çıktısı)
///  • her ikisi de yoksa     → GALLERYWEB_SERVER_BIN ile elle gösterilebilir
fn resolve_server_binary(app: &tauri::AppHandle) -> Option<PathBuf> {
    let name = if cfg!(windows) { "galleryweb-server.exe" } else { "galleryweb-server" };

    if let Ok(custom) = std::env::var("GALLERYWEB_SERVER_BIN") {
        let p = PathBuf::from(custom);
        if p.is_file() {
            return Some(p);
        }
    }
    if let Ok(dir) = app.path().resource_dir() {
        // Düz ad (tauri.conf.json'daki eşleme) + Tauri'nin üst-dizin kaynakları için
        // ürettiği `_up_/…` düzeni. İkincisi olmadan, dist/ klasörü duran GELİŞTİRME
        // makinesinde sorun görünmüyor ama temiz kurulumda uygulama açılmıyordu.
        for aday in [dir.join(name), dir.join("_up_").join("dist").join(name)] {
            if aday.is_file() {
                return Some(aday);
            }
        }
    }
    // Geliştirme: src-tauri/target/... yerine repo içindeki dist/
    let dev = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .map(|d| d.join("dist").join(name));
    dev.filter(|p| p.is_file())
}

/// Sunucu ayağa kalkana kadar bekle (TCP bağlanabiliyor mu?).
fn wait_for_server(port: u16, timeout: Duration) -> bool {
    let addr = SocketAddrV4::new(Ipv4Addr::LOCALHOST, port);
    let deadline = Instant::now() + timeout;
    while Instant::now() < deadline {
        if TcpStream::connect_timeout(&addr.into(), Duration::from_millis(400)).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(150));
    }
    false
}

/// Linux'ta WebKitGTK'nın DMABUF render yolu, bazı sürücülerde (özellikle NVIDIA +
/// Wayland) tampon ayıramıyor — pencere açılıyor ama İÇİ BOŞ/SİYAH kalıyor. Log'da
/// `Failed to create GBM buffer of size WxH` satırı görünür.
///
/// Bu, uygulamanın kendi sorunu değil ama kullanıcıdan ortam değişkeni ayarlamasını
/// bekleyemeyiz; güvenli olan yazılımsal yolu varsayılan yapıyoruz. GPU yolunu
/// denemek isteyen `GALLERYWEB_GPU=1` ile bunu kapatabilir.
#[cfg(target_os = "linux")]
fn linux_render_gecici_cozumu() {
    if std::env::var_os("GALLERYWEB_GPU").is_some() {
        return;
    }
    if std::env::var_os("WEBKIT_DISABLE_DMABUF_RENDERER").is_none() {
        std::env::set_var("WEBKIT_DISABLE_DMABUF_RENDERER", "1");
    }
}

#[cfg(not(target_os = "linux"))]
fn linux_render_gecici_cozumu() {}

fn main() {
    // GTK/WebKit başlatılmadan ÖNCE ayarlanmalı.
    linux_render_gecici_cozumu();

    tauri::Builder::default()
        .manage(ServerProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();

            let server_bin = resolve_server_binary(&handle).ok_or_else(|| {
                "galleryweb-server bulunamadı. Geliştirmede önce şunu çalıştırın: \
                 cd desktop && ../.build-venv/bin/pyinstaller galleryweb-server.spec --noconfirm"
                    .to_string()
            })?;

            // Thumbnail cache + tercihler buraya yazılır (paket dizini salt-okunur).
            let data_dir = handle.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;

            let port = pick_free_port();
            let mut cmd = Command::new(&server_bin);
            // stdin'i boru yap ve UCUNU AÇIK TUT: sunucu bu borudan EOF okuduğu an
            // kendini kapatır. Kabuk çökse/SIGKILL yese bile boru kapanacağı için
            // arkada öksüz sunucu kalmaz. (Sinyal iletmek yetmiyordu: PyInstaller
            // tek-dosya paketinde asıl Python süreci bootloader'ın çocuğu.)
            cmd.stdin(Stdio::piped())
                .env("PORT", port.to_string())
                // Yerel modda kimlik doğrulama YOK → asla 0.0.0.0'a bağlama.
                .env("HOST", "127.0.0.1")
                .env("GALLERYWEB_DATA_DIR", &data_dir)
                .env("GALLERYWEB_DESKTOP", "1");
            #[cfg(windows)]
            {
                use std::os::windows::process::CommandExt;
                const CREATE_NO_WINDOW: u32 = 0x0800_0000;
                cmd.creation_flags(CREATE_NO_WINDOW); // konsol penceresi açılmasın
            }

            let child = cmd.spawn().map_err(|e| {
                if e.kind() == ErrorKind::PermissionDenied {
                    format!("{} çalıştırılamadı (izin yok): {e}", server_bin.display())
                } else {
                    format!("{} başlatılamadı: {e}", server_bin.display())
                }
            })?;
            app.state::<ServerProcess>().0.lock().unwrap().replace(child);

            if !wait_for_server(port, Duration::from_secs(30)) {
                app.state::<ServerProcess>().kill();
                return Err("Sunucu 30 saniyede yanıt vermedi.".into());
            }

            let url = format!("http://127.0.0.1:{port}");
            WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.parse()?))
                .title("GalleryWeb")
                .inner_size(1280.0, 860.0)
                .min_inner_size(900.0, 600.0)
                .resizable(true)
                .build()?;

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("Tauri uygulaması başlatılamadı")
        .run(|app, event| {
            // Pencere kapanınca / uygulama çıkınca sunucu da gitsin.
            if let RunEvent::ExitRequested { .. } | RunEvent::Exit = event {
                app.state::<ServerProcess>().kill();
            }
        });
}
