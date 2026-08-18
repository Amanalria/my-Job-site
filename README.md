# 🚀 SARKARI RESULT OFFICIAL PORTAL – Full Production Stack

A complete 1:1 replica of the official Sarkari Result portal with 133+ scraped notifications, configured for **Vercel Serverless + Supabase Cloud + GitHub Sync + Google AdSense Ready**.

---

## 🌟 Key Architecture & Features

1. **🔗 Clean & Flat URL Structure**:
   - `https://yourdomain.com/<custom-url-slug>/`
   - Flat top-level routing for all posts (e.g. `domain.com/bpsc-school-teacher-tre-4-0-2026/`, `domain.com/latest-jobs/`).
   - Domain-agnostic: Automatically adapts to localhost, Vercel domain, and any custom domain connected.

2. **⚡ `/alria` Visual In-Place Live Homepage Editor**:
   - Open `https://yourdomain.com/alria` to enter the live in-place editor.
   - Edit Portal Name, Taglines, Google AdSense Client ID, and Supabase credentials directly from the homepage.

3. **🔍 Full SEO & Search Engine Optimization**:
   - **Dynamic XML Sitemap**: `https://yourdomain.com/sitemap.xml` (all 133+ posts & categories automatically indexed with `lastmod`, `priority`, `changefreq`).
   - **Robots.txt**: `https://yourdomain.com/robots.txt` (proper crawler directives).
   - **Meta Tags & OpenGraph**: Auto-injected social preview cards for Google and WhatsApp sharing.

4. **💰 Google AdSense Ready**:
   - Paste your AdSense Publisher ID (`ca-pub-XXXXXXXXXXXXXXXX`) in `/admin/settings` or `/alria`.
   - AdSense auto-ads script will automatically inject into all pages without breaking layouts.

5. **🗄️ Supabase Cloud Database Ready**:
   - SQL schema ready in [`supabase_schema.sql`](./supabase_schema.sql) for 1-click cloud synchronization.

---

## 🚀 How to Deploy on GitHub & Vercel

### Step 1: Push Project to GitHub
```bash
git init
git add .
git commit -m "Initial release: Sarkari Result Official Portal"
git remote add origin https://github.com/your-username/sarkari-result-portal.git
git branch -M main
git push -u origin main
```

### Step 2: 1-Click Deploy on Vercel
1. Open [Vercel.com](https://vercel.com) and click **"Add New..." -> Project**.
2. Import your GitHub repository `sarkari-result-portal`.
3. Vercel automatically detects `vercel.json` and configures serverless Python.
4. Click **Deploy**.

### Step 3: Add Custom Domain on Vercel
1. In Vercel Project Settings -> **Domains**.
2. Add your custom domain (e.g. `sarkariresult.com`, `myjobportal.in`).
3. Add the DNS records (A record / CNAME) as instructed by Vercel.
4. The site and all internal URLs immediately work seamlessly on your custom domain!

---

## 🗄️ Supabase Setup
1. Create a project at [Supabase.com](https://supabase.com).
2. Go to **SQL Editor** -> Click **New Query**.
3. Paste the contents of [`supabase_schema.sql`](./supabase_schema.sql) and click **Run**.
4. Go to **Project Settings -> API** -> Copy **Project URL** & **Anon Public Key**.
5. Open `https://yourdomain.com/admin/settings` and paste your Supabase keys.

---

## 💻 Localhost Development
```bash
python3 app.py
```
- **Homepage**: `http://localhost:9093`
- **Visual Live Editor**: `http://localhost:9093/alria`
- **Dynamic Sitemap**: `http://localhost:9093/sitemap.xml`
- **Admin Dashboard**: `http://localhost:9093/admin/dashboard`
