"""Storage service: local disk (Faz 1-2) → Cloudflare R2 (Faz 3+).

Usage:
    svc = get_storage()
    result = await svc.put(content, key, content_type)
    url = svc.url(key)
    thumb_result = await svc.put_thumbnail(content, key)
"""

from pathlib import Path
from .config import get_settings
import aiofiles
import io
import asyncio
from functools import lru_cache

_LOCAL_DIR = Path(__file__).parent.parent.parent / "cache" / "uploads"
_LOCAL_DIR.mkdir(parents=True, exist_ok=True)


class StorageResult:
    def __init__(self, key: str, url: str, backend: str):
        self.key = key
        self.url = url
        self.backend = backend  # "local" | "r2"


class LocalStorage:
    """Local disk fallback — used when R2 creds are not configured."""

    async def put(self, content: bytes, key: str, content_type: str = "") -> StorageResult:
        path = _LOCAL_DIR / key
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, "wb") as f:
            await f.write(content)
        return StorageResult(key=key, url=str(path), backend="local")

    def url(self, key: str) -> str | None:
        p = _LOCAL_DIR / key
        return str(p) if p.exists() else None

    async def delete(self, key: str) -> None:
        p = _LOCAL_DIR / key
        if p.exists():
            p.unlink()

    @property
    def is_r2(self) -> bool:
        return False


class R2Storage:
    """Cloudflare R2 via boto3 (S3-compatible)."""

    def __init__(self):
        import boto3
        s = get_settings()
        self._bucket = s.r2_bucket_name
        self._public_url = s.r2_public_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=s.r2_endpoint,
            aws_access_key_id=s.r2_access_key_id,
            aws_secret_access_key=s.r2_secret_access_key,
            region_name="auto",
        )

    async def put(self, content: bytes, key: str, content_type: str = "application/octet-stream") -> StorageResult:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        )
        return StorageResult(key=key, url=self.url(key), backend="r2")

    def url(self, key: str) -> str:
        return f"{self._public_url}/{key}"

    def presigned_put_url(self, key: str, content_type: str = "image/jpeg", expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expires,
        )

    def presigned_get_url(self, key: str, expires: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires,
        )

    async def delete(self, key: str) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self._client.delete_object(Bucket=self._bucket, Key=key)
        )

    @property
    def is_r2(self) -> bool:
        return True


@lru_cache
def get_storage() -> LocalStorage | R2Storage:
    s = get_settings()
    has_r2 = all([
        s.r2_access_key_id and not s.r2_access_key_id.startswith("BURAYA"),
        s.r2_secret_access_key and not s.r2_secret_access_key.startswith("BURAYA"),
        s.r2_endpoint and not s.r2_endpoint.startswith("https://BURAYA"),
    ])
    if has_r2:
        return R2Storage()
    return LocalStorage()
