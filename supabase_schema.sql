-- =========================================================
-- SARKARI RESULT OFFICIAL PORTAL - SUPABASE DATABASE SCHEMA
-- Execute this SQL script in your Supabase Dashboard -> SQL Editor
-- =========================================================

-- 1. Create Posts Table
CREATE TABLE IF NOT EXISTS public.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('latest-jobs', 'admit-card', 'result', 'answer-key', 'syllabus', 'admission', 'certificate-verification', 'important')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    application_start_date DATE,
    application_last_date DATE,
    is_date_extended BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    custom_badge TEXT,
    short_desc TEXT,
    html_content TEXT,
    tables JSONB DEFAULT '[]'::jsonb,
    important_links JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_posts_category ON public.posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_created ON public.posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_last_date ON public.posts(application_last_date);

-- 2. Create Portal Settings Table
CREATE TABLE IF NOT EXISTS public.settings (
    id TEXT PRIMARY KEY DEFAULT 'site_config',
    site_name TEXT DEFAULT 'SARKARI RESULT',
    domain TEXT DEFAULT 'yourdomain.com',
    tagline TEXT,
    top_banner_text TEXT,
    adsense JSONB DEFAULT '{"enabled": false, "client_id": ""}'::jsonb,
    socials JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Row Level Security
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public Read All Posts" ON public.posts FOR SELECT USING (true);
CREATE POLICY "Public Read Settings" ON public.settings FOR SELECT USING (true);
CREATE POLICY "Admin All Posts" ON public.posts FOR ALL USING (auth.role() = 'authenticated');
CREATE POLICY "Admin All Settings" ON public.settings FOR ALL USING (auth.role() = 'authenticated');
