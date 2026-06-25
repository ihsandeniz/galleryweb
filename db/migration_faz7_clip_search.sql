-- GalleryWeb — Faz 7: CLIP Semantic Search
-- Apply: psql -h localhost -p 5436 -U postgres -d galleryweb -f migration_faz7_clip_search.sql

-- pgvector extension (requires postgresql-15+, pgvector apt package)
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to photos (512-dim: clip-ViT-B-32)
ALTER TABLE public.photos ADD COLUMN IF NOT EXISTS embedding vector(512);

-- IVFFlat approximate nearest-neighbor index (cosine distance)
-- lists = 100 is a safe default; re-create with larger lists after 50k+ rows
CREATE INDEX IF NOT EXISTS idx_photos_embedding
    ON public.photos USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Partial index only over rows that already have an embedding (skips NULLs)
CREATE INDEX IF NOT EXISTS idx_photos_embedding_notnull
    ON public.photos (id)
    WHERE embedding IS NOT NULL;
