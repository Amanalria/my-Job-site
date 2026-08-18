-- ================================================================
-- SARKARI RESULT PRO PORTAL - SUPABASE SQL SCHEMA
-- Copy and run this in your Supabase Project -> SQL Editor -> Run
-- ================================================================

-- 1. Create Posts Table
CREATE TABLE IF NOT EXISTS public.posts (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'latest-jobs',
    short_desc TEXT,
    html_content TEXT,
    application_start_date TEXT,
    application_last_date TEXT,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_date_extended BOOLEAN DEFAULT FALSE,
    is_temporary BOOLEAN DEFAULT FALSE,
    custom_badge TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create Site Settings Table (Stores JSON configuration)
CREATE TABLE IF NOT EXISTS public.settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create Categories Table
CREATE TABLE IF NOT EXISTS public.categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    "desc" TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Enable Row Level Security (RLS) & Allow Anonymous Read
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;

-- Allow Public Read for Website Visitors
CREATE POLICY "Public Read Posts" ON public.posts FOR SELECT USING (true);
CREATE POLICY "Public Read Settings" ON public.settings FOR SELECT USING (true);
CREATE POLICY "Public Read Categories" ON public.categories FOR SELECT USING (true);

-- Allow Full Access via Anon/Service Key for Admin Operations
CREATE POLICY "Admin Insert Posts" ON public.posts FOR INSERT WITH CHECK (true);
CREATE POLICY "Admin Update Posts" ON public.posts FOR UPDATE USING (true);
CREATE POLICY "Admin Delete Posts" ON public.posts FOR DELETE USING (true);

CREATE POLICY "Admin Insert Settings" ON public.settings FOR INSERT WITH CHECK (true);
CREATE POLICY "Admin Update Settings" ON public.settings FOR UPDATE USING (true);
CREATE POLICY "Admin Delete Settings" ON public.settings FOR DELETE USING (true);

CREATE POLICY "Admin Insert Categories" ON public.categories FOR INSERT WITH CHECK (true);
CREATE POLICY "Admin Update Categories" ON public.categories FOR UPDATE USING (true);
CREATE POLICY "Admin Delete Categories" ON public.categories FOR DELETE USING (true);

-- Indices for Ultra-Fast Search & Category queries
CREATE INDEX IF NOT EXISTS idx_posts_slug ON public.posts(slug);
CREATE INDEX IF NOT EXISTS idx_posts_category ON public.posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_is_temporary ON public.posts(is_temporary);
