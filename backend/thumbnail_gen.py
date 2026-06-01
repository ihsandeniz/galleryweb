from PIL import Image
import hashlib
from pathlib import Path
import asyncio
from concurrent.futures import ProcessPoolExecutor
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
        self.executor = ProcessPoolExecutor(max_workers=min(4, os.cpu_count() or 2))

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
        if original_path.suffix.lower() in VIDEO_FORMATS:
            return await self._get_video_thumbnail(original_path)

        thumb_path = self._generate_thumb_path(original_path, size)
        cache_key = self._cache_key(original_path, size)

        # Cache kontrolü
        if thumb_path.exists():
            original_mtime = original_path.stat().st_mtime
            cached_mtime = self.cache_manager.get_mtime(cache_key)
            if cached_mtime and cached_mtime == original_mtime:
                return thumb_path

        # Thumbnail oluştur
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
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

        return thumb_path

    async def _get_video_thumbnail(self, video_path: Path) -> Path:
        thumb_path = self._generate_thumb_path(video_path)
        if thumb_path.exists():
            return thumb_path
        if shutil.which('ffmpeg'):
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                ThumbnailGenerator._ffmpeg_thumb,
                video_path,
                thumb_path
            )
        return thumb_path

    @staticmethod
    def _ffmpeg_thumb(video_path: Path, thumb_path: Path):
        try:
            subprocess.run([
                'ffmpeg', '-i', str(video_path),
                '-ss', '00:00:01', '-vframes', '1',
                '-vf', 'scale=300:300:force_original_aspect_ratio=decrease',
                '-y', str(thumb_path)
            ], capture_output=True, timeout=30)
        except Exception as e:
            print(f"ffmpeg thumbnail hatası: {video_path} - {e}")

    @staticmethod
    def _create_thumbnail(original_path: Path, thumb_path: Path, thumb_size: tuple):
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

        except Exception as e:
            print(f"Thumbnail oluşturma hatası: {original_path} - {e}")
            raise

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
