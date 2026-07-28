from PIL import Image
import hashlib
from pathlib import Path
import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import os
import shutil
import subprocess

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False

VIDEO_FORMATS = {'.mp4', '.webm', '.mov', '.avi'}
HEIF_FORMATS = {'.heic', '.heif', '.avif'}

class ThumbnailGenerator:
    def __init__(self, cache_manager, thumb_size=(300, 300), cache_dir=None):
        self.cache_manager = cache_manager
        self.thumb_size = thumb_size
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent / "cache" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        isci = min(4, os.cpu_count() or 2)
        # Windows'ta süreç havuzu KULLANMA. Orada multiprocessing `fork` değil
        # `spawn` yapar: her işçi çalıştırılabilir dosyayı baştan başlatır —
        # paketlenmiş uygulamada bu, 55 MB'lık exe'nin dört kez yeniden açılması
        # ve her açılışta paketin geçici dizine çıkarılması demek (çok yavaş,
        # `freeze_support()` unutulursa süreç bombası). Pillow'un çöz/ölçekle
        # işlemleri GIL'i bıraktığı için iş parçacığı havuzu Windows'ta hem
        # güvenli hem yeterli. POSIX'te fork ucuz → gerçek paralellik korunur.
        if os.name == "nt":
            self.executor = ThreadPoolExecutor(max_workers=isci,
                                               thread_name_prefix="thumb")
        else:
            self.executor = ProcessPoolExecutor(max_workers=isci)

    def _generate_thumb_path(self, original_path: Path, size: int = 300) -> Path:
        file_hash = hashlib.md5(str(original_path).encode()).hexdigest()
        # 300px → eski format (backwards compat), diğer boyutlar → {hash}_{size}.webp
        if size == 300:
            return self.cache_dir / f"{file_hash}.webp"
        return self.cache_dir / f"{file_hash}_{size}.webp"

    def _cache_key(self, original_path: Path, size: int = 300) -> str:
        if size == 300:
            return str(original_path)
        return f"{original_path}:{size}"

    async def get_thumbnail(self, original_path: Path, size: int = 300) -> Path:
        thumb_path, _ = await self.get_thumbnail_ex(original_path, size)
        return thumb_path

    async def get_thumbnail_ex(self, original_path: Path, size: int = 300) -> tuple[Path, bool]:
        """Küçük resmi döndür. İkinci değer: dosya gerçekten okunabildi mi?

        Okunamayan dosya (0 bayt, bozuk, desteklenmeyen kodek) için hata FIRLATMAZ;
        yerine 'bozuk dosya' yer tutucusu üretir. Sebebi: tek bozuk dosya yüzünden
        istek 500 dönünce tarayıcıdaki kutucuk sonsuza kadar 'yükleniyor' durumunda
        kalıyor ve kullanıcı galeriyi bozuk sanıyordu. Yer tutucu da önbelleğe
        yazılır — 0 baytlık dosya her istekte yeniden çözülmeye çalışılmaz.
        """
        if original_path.suffix.lower() in VIDEO_FORMATS:
            return await self._get_video_thumbnail(original_path)

        thumb_path = self._generate_thumb_path(original_path, size)
        cache_key = self._cache_key(original_path, size)

        # Cache kontrolü — yer tutucu da önbelleğe girer, o yüzden "okunamadı"
        # bilgisini yanındaki işaret dosyasından okuyoruz (aksi halde ikinci
        # istekte durum yanlışlıkla "ok" görünüyordu).
        if thumb_path.exists():
            original_mtime = original_path.stat().st_mtime
            cached_mtime = self.cache_manager.get_mtime(cache_key)
            if cached_mtime and cached_mtime == original_mtime:
                return thumb_path, not self._bad_marker(thumb_path).exists()

        # Boş dosyayı çözmeye çalışmaya bile gerek yok
        if original_path.stat().st_size == 0:
            self._write_placeholder(thumb_path, (size, size))
            self.cache_manager.set_thumbnail(cache_key, str(thumb_path),
                                             original_path.stat().st_mtime)
            return thumb_path, False

        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(
            self.executor,
            ThumbnailGenerator._create_thumbnail,
            original_path,
            thumb_path,
            (size, size)
        )

        self.cache_manager.set_thumbnail(
            cache_key,
            str(thumb_path),
            original_path.stat().st_mtime
        )

        return thumb_path, bool(ok)

    async def _get_video_thumbnail(self, video_path: Path) -> tuple[Path, bool]:
        """Videonun poster karesi. ffmpeg yoksa veya kare alınamazsa yer tutucu.

        Eskiden ffmpeg bulunamayınca var olmayan dosya yolu döndürülüyordu ve
        istek 500 veriyordu — Windows'ta ffmpeg varsayılan kurulu OLMADIĞI için
        oradaki her video kutucuğu bozuk görünürdü.
        """
        thumb_path = self._generate_thumb_path(video_path)
        if thumb_path.exists():
            return thumb_path, not self._bad_marker(thumb_path).exists()

        if shutil.which('ffmpeg'):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                ThumbnailGenerator._ffmpeg_thumb,
                video_path,
                thumb_path
            )
        if not thumb_path.exists():
            self._write_placeholder(thumb_path, self.thumb_size, video=True)
            return thumb_path, False
        return thumb_path, True

    # Paketlenmiş Windows uygulamasında her ffmpeg çağrısı siyah bir konsol
    # penceresi açıp kapatır. 20 videoluk bir klasörde bu, kullanıcının önünde
    # 20 kez yanıp sönen pencere demek — uygulama virüs gibi görünür.
    _NO_WINDOW = 0x0800_0000 if os.name == "nt" else 0

    @staticmethod
    def _ffmpeg_thumb(video_path: Path, thumb_path: Path):
        try:
            subprocess.run([
                'ffmpeg', '-i', str(video_path),
                '-ss', '00:00:01', '-vframes', '1',
                '-vf', 'scale=300:300:force_original_aspect_ratio=decrease',
                '-y', str(thumb_path)
            ], capture_output=True, timeout=30,
                creationflags=ThumbnailGenerator._NO_WINDOW)
        except Exception as e:
            print(f"ffmpeg thumbnail hatası: {video_path} - {e}")

    @staticmethod
    def _bad_marker(thumb_path: Path) -> Path:
        """Yer tutucu üretilmiş küçük resmin yanındaki işaret dosyası."""
        return thumb_path.with_name(thumb_path.name + ".bad")

    @staticmethod
    def _write_placeholder(thumb_path: Path, thumb_size: tuple, video: bool = False):
        """Önizlemesi üretilemeyen dosya için yer tutucu görsel.

        `video=False` → uyarı üçgeni (bozuk/okunamayan dosya)
        `video=True`  → film şeridi + oynat üçgeni (poster karesi alınamadı;
                        genelde ffmpeg kurulu değil — Windows'ta varsayılan durum)

        Yazı tipi gerektirmez (paketlenmiş uygulamada font garantisi yok) — sadece
        geometrik şekiller.
        """
        from PIL import ImageDraw
        w = h = max(64, min(thumb_size[0], 512))
        img = Image.new("RGB", (w, h), (26, 26, 30))
        d = ImageDraw.Draw(img)
        if video:
            renk = (120, 160, 200)
            kalinlik = max(2, w // 90)
            d.rectangle([w * 0.18, h * 0.28, w * 0.82, h * 0.72], outline=renk, width=kalinlik)
            for i in range(4):  # film şeridi delikleri
                y = h * (0.34 + i * 0.11)
                d.rectangle([w * 0.21, y, w * 0.25, y + h * 0.05], outline=renk, width=1)
                d.rectangle([w * 0.75, y, w * 0.79, y + h * 0.05], outline=renk, width=1)
            d.polygon([(w * 0.44, h * 0.40), (w * 0.62, h * 0.50), (w * 0.44, h * 0.60)], fill=renk)
        else:
            m = w * 0.22
            d.polygon([(w / 2, m), (w - m, h - m), (m, h - m)], outline=(200, 90, 90), width=max(2, w // 90))
            d.line([(w / 2, h * 0.42), (w / 2, h * 0.62)], fill=(200, 90, 90), width=max(2, w // 70))
            d.ellipse([w / 2 - w * 0.018, h * 0.68, w / 2 + w * 0.018, h * 0.68 + w * 0.036],
                      fill=(200, 90, 90))
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(thumb_path, "WEBP", quality=80)
        try:
            ThumbnailGenerator._bad_marker(thumb_path).touch()
        except OSError:
            pass

    @staticmethod
    def _create_thumbnail(original_path: Path, thumb_path: Path, thumb_size: tuple) -> bool:
        try:
            with Image.open(original_path) as img:
                try:
                    from PIL import ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass

                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background

                img.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                img.save(thumb_path, 'WEBP', quality=85, method=6)
                # Dosya sonradan düzeldiyse eski "bozuk" işaretini kaldır
                marker = ThumbnailGenerator._bad_marker(thumb_path)
                if marker.exists():
                    try:
                        marker.unlink()
                    except OSError:
                        pass
                return True

        except Exception as e:
            # FIRLATMA. Tek bozuk dosya (0 bayt, yarım inmiş, desteklenmeyen kodek)
            # yüzünden istek 500 dönünce galeri kutucuğu sonsuza kadar 'yükleniyor'
            # kalıyordu. Yer tutucu üret, kullanıcı hangi dosyanın bozuk olduğunu
            # görsün ve galerinin geri kalanı çalışsın.
            print(f"Küçük resim üretilemedi (yer tutucu kondu): {original_path} - {e}")
            try:
                ThumbnailGenerator._write_placeholder(thumb_path, thumb_size)
            except Exception as ph_err:
                print(f"Yer tutucu da yazılamadı: {thumb_path} - {ph_err}")
            return False

    async def batch_generate(self, directory: Path):
        supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'} | VIDEO_FORMATS | HEIF_FORMATS
        images = [p for p in directory.rglob("*") if p.suffix.lower() in supported_formats]
        print(f"Toplam {len(images)} dosya için thumbnail oluşturuluyor...")

        sem = asyncio.Semaphore(min(4, os.cpu_count() or 2))

        async def limited(img):
            async with sem:
                return await self.get_thumbnail(img)

        results = await asyncio.gather(*[limited(img) for img in images], return_exceptions=True)
        errors = sum(1 for r in results if isinstance(r, Exception))
        print(f"Thumbnails: {len(images)-errors}/{len(images)} tamamlandı")
