-- Migration: Faz 8 — Video Proofing (timestamp yorum + kare üzerine çizim)
-- Run: psql -h localhost -p 5436 -U postgres -d galleryweb -f migration_faz8_video_proofing.sql

-- Video süresi (ffprobe ile upload'ta doldurulur)
ALTER TABLE public.photos
    ADD COLUMN IF NOT EXISTS duration_ms INTEGER;

-- Timestamp'li yorum: video için milisaniye konumu (NULL = normal yorum / fotoğraf)
ALTER TABLE public.gallery_comments
    ADD COLUMN IF NOT EXISTS timestamp_ms INTEGER;

-- Kare/fotoğraf üzerine çizim annotation'ları (misafir proofing)
CREATE TABLE IF NOT EXISTS public.media_annotations (
    id           BIGSERIAL PRIMARY KEY,
    link_id      UUID NOT NULL REFERENCES public.sharing_links(id) ON DELETE CASCADE,
    photo_id     BIGINT NOT NULL REFERENCES public.photos(id) ON DELETE CASCADE,
    guest_name   VARCHAR(100) DEFAULT 'Ziyaretçi',
    timestamp_ms INTEGER,             -- video karesi; foto için NULL
    drawing      JSONB NOT NULL,      -- {strokes:[{color,width,points:[[x,y],..]}]} — 0-1 normalize
    note         TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_annotations_link_photo
    ON public.media_annotations(link_id, photo_id);
