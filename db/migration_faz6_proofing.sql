-- Migration: Faz 6 — Müşteri Proofing Gallery tables
-- Run: psql $DATABASE_URL -f migration_faz6_proofing.sql

CREATE TABLE IF NOT EXISTS public.gallery_comments (
    id          BIGSERIAL PRIMARY KEY,
    link_id     UUID NOT NULL REFERENCES public.sharing_links(id) ON DELETE CASCADE,
    photo_id    BIGINT REFERENCES public.photos(id) ON DELETE CASCADE,
    guest_name  VARCHAR(100) DEFAULT 'Ziyaretçi',
    body        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.gallery_votes (
    id                  BIGSERIAL PRIMARY KEY,
    link_id             UUID NOT NULL REFERENCES public.sharing_links(id) ON DELETE CASCADE,
    photo_id            BIGINT NOT NULL REFERENCES public.photos(id) ON DELETE CASCADE,
    guest_fingerprint   VARCHAR(64),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (link_id, photo_id, guest_fingerprint)
);

CREATE TABLE IF NOT EXISTS public.photo_selections (
    id          BIGSERIAL PRIMARY KEY,
    link_id     UUID NOT NULL REFERENCES public.sharing_links(id) ON DELETE CASCADE,
    photo_id    BIGINT NOT NULL REFERENCES public.photos(id) ON DELETE CASCADE,
    guest_name  VARCHAR(100) DEFAULT 'Ziyaretçi',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (link_id, photo_id)
);

CREATE TABLE IF NOT EXISTS public.photo_markings (
    id          BIGSERIAL PRIMARY KEY,
    photo_id    BIGINT NOT NULL UNIQUE REFERENCES public.photos(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    mark        VARCHAR(20) DEFAULT 'none',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gallery_comments_link ON public.gallery_comments(link_id);
CREATE INDEX IF NOT EXISTS idx_gallery_votes_link_photo ON public.gallery_votes(link_id, photo_id);
CREATE INDEX IF NOT EXISTS idx_photo_selections_link ON public.photo_selections(link_id);
CREATE INDEX IF NOT EXISTS idx_photo_markings_user ON public.photo_markings(user_id);
