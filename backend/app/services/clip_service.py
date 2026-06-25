"""CLIP image/text embedding service — Faz 7.

Model: clip-ViT-B-32 (512-dim) via sentence-transformers.
Model is loaded lazily on first call and cached for the process lifetime.
"""

import asyncio
import io
import logging
from functools import lru_cache

logger = logging.getLogger("galleryweb.clip")


class CLIPService:
    def __init__(self):
        self._model = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("clip-ViT-B-32")
            logger.info("CLIP model yüklendi: clip-ViT-B-32 (512-dim)")
        return self._model

    # ── Sync helpers (run in executor) ────────────────────────────────────────

    def _encode_image_bytes_sync(self, image_bytes: bytes) -> list[float]:
        from PIL import Image
        model = self._load_model()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        emb = model.encode(img, convert_to_numpy=True)
        return emb.tolist()

    def _encode_image_path_sync(self, image_path: str) -> list[float]:
        from PIL import Image
        model = self._load_model()
        img = Image.open(image_path).convert("RGB")
        emb = model.encode(img, convert_to_numpy=True)
        return emb.tolist()

    def _encode_text_sync(self, text: str) -> list[float]:
        model = self._load_model()
        emb = model.encode(text, convert_to_numpy=True)
        return emb.tolist()

    # ── Async API ─────────────────────────────────────────────────────────────

    async def encode_image_from_bytes(self, image_bytes: bytes) -> list[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode_image_bytes_sync, image_bytes)

    async def encode_image_from_path(self, image_path: str) -> list[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode_image_path_sync, image_path)

    async def encode_text(self, text: str) -> list[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode_text_sync, text)


@lru_cache(maxsize=1)
def get_clip_service() -> CLIPService:
    return CLIPService()
