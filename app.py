import supabase_client as supa
import os
import re
import json
import uuid
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from flask import Flask, send_from_directory, request, Response, abort, jsonify, render_template, redirect

app = Flask(__name__)
app.secret_key = 'sarkari_official_secret_2026'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, 'raw_clone', 'pages')
WP_CONTENT_DIR = os.path.join(BASE_DIR, 'raw_clone', 'wp-content')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')

TARGET_DOMAIN = "studytopper.in"

PRIMARY_CATEGORIES = [
    'latest-jobs', 'admit-card', 'result', 'admission', 'syllabus', 'answer-key',
    'certificate-verification', 'important', 'contact', 'disclaimer', 'privacy-policy'
]


# ==================== UNIFIED POST MANAGEMENT SYSTEM ====================

def get_deleted_post_slugs():
    settings = load_settings()
    return set(settings.get('deleted_posts', []))

def load_custom_posts():
    custom_posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
    if os.path.exists(custom_posts_file):
        try:
            with open(custom_posts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_custom_posts(posts_list):
    try:
        custom_posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
        with open(custom_posts_file, 'w', encoding='utf-8') as f:
            json.dump(posts_list, f, indent=2)
    except Exception as e:
        print(f"Notice: local custom_posts.json write skipped ({e})")

def load_all_active_posts():
    deleted_slugs = get_deleted_post_slugs()
    posts_map = {}

    # 1. Scraped base posts
    all_posts_file = os.path.join(DATA_DIR, 'all_posts.json')
    if os.path.exists(all_posts_file):
        try:
            with open(all_posts_file, 'r', encoding='utf-8') as f:
                scraped = json.load(f)
                for p in scraped:
                    slug = p.get('slug')
                    if slug and slug not in deleted_slugs:
                        posts_map[slug] = p
        except Exception:
            pass

    # 2. Local custom posts
    for p in load_custom_posts():
        slug = p.get('slug')
        if slug and slug not in deleted_slugs:
            posts_map[slug] = p

    # 3. Supabase posts
    if supa.is_supabase_configured():
        try:
            supa_posts = supa.fetch_posts_from_supabase()
            if supa_posts:
                for p in supa_posts:
                    slug = p.get('slug')
                    if slug and slug not in deleted_slugs:
                        posts_map[slug] = p
        except Exception:
            pass

    result = list(posts_map.values())
    result.sort(key=lambda x: x.get('created_at', x.get('post_date', '')), reverse=True)
    return result

def save_single_post(post_item):
    slug = post_item.get('slug')
    settings = load_settings()
    deleted = settings.get('deleted_posts', [])
    if slug in deleted:
        deleted.remove(slug)
        settings['deleted_posts'] = deleted
        save_settings_data(settings)

    custom_posts = [p for p in load_custom_posts() if p.get('slug') != slug]
    custom_posts.insert(0, post_item)
    save_custom_posts(custom_posts)

    if supa.is_supabase_configured():
        supa.save_post_to_supabase(post_item)

    try:
        page_file = os.path.join(PAGES_DIR, f"{slug}.html")
        if post_item.get('html_content'):
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(post_item.get('html_content'))
    except Exception:
        pass

def delete_single_post(post_id_or_slug):
    settings = load_settings()
    if 'deleted_posts' not in settings:
        settings['deleted_posts'] = []
    if post_id_or_slug not in settings['deleted_posts']:
        settings['deleted_posts'].append(post_id_or_slug)
    save_settings_data(settings)

    custom_posts = [p for p in load_custom_posts() if p.get('slug') != post_id_or_slug and p.get('id') != post_id_or_slug]
    save_custom_posts(custom_posts)

    if supa.is_supabase_configured():
        supa.delete_post_from_supabase(post_id_or_slug)

    try:
        page_file = os.path.join(PAGES_DIR, f"{post_id_or_slug}.html")
        if os.path.exists(page_file):
            os.remove(page_file)
    except Exception:
        pass

def clean_post_html_content(raw_html, settings):
    if not raw_html:
        return ""
    
    soup = BeautifulSoup(raw_html, 'html.parser')
    socials = settings.get('socials', {})
    wa_url = socials.get('whatsapp', 'https://whatsapp.com/')
    tg_url = socials.get('telegram', 'https://t.me/')
    ig_url = socials.get('instagram', 'https://instagram.com/')
    domain = settings.get('domain', 'studytopper.in')
    site_name = settings.get('site_name', 'STUDY TOPPER™')

    # 1. Remove Meditation & Crack Exams boxes
    for el in soup.find_all(string=re.compile(r'Meditate & Get Success|Meditation & Crack Exams', re.IGNORECASE)):
        parent_tr = el.find_parent('tr')
        if parent_tr:
            parent_tr.decompose()
        else:
            parent_box = el.find_parent('div') or el.find_parent('p') or el.find_parent('table')
            if parent_box:
                parent_box.decompose()

    # 2. Remove "Download SarkariResult App Now" / "Mobile App" rows
    for el in soup.find_all(string=re.compile(r'Download Sarkari\s*Result App|Download SarkariResult App|Sarkari Result Mobile App', re.IGNORECASE)):
        parent_tr = el.find_parent('tr')
        if parent_tr:
            parent_tr.decompose()
        else:
            parent_box = el.find_parent('div') or el.find_parent('p') or el.find_parent('a')
            if parent_box:
                parent_box.decompose()

    # 3. Dynamic WhatsApp, Telegram & Instagram follow links in content
    for a_tag in soup.find_all('a'):
        href = a_tag.get('href', '')
        text = a_tag.get_text(strip=True).lower()
        
        if 'whatsapp' in href.lower() or 'whatsapp' in text:
            a_tag['href'] = wa_url
        elif 't.me' in href.lower() or 'telegram' in text:
            a_tag['href'] = tg_url
        elif 'instagram' in href.lower() or 'instagram' in text:
            a_tag['href'] = ig_url
        elif 'sarkariresult' in href.lower():
            a_tag['href'] = '/'

    # 4. Text & Domain replacements
    html_str = str(soup)
    html_str = re.sub(r'Check Sarkari\s*Result', f'Check {site_name}', html_str, flags=re.IGNORECASE)
    html_str = re.sub(r'Sarkari\s*Result', site_name, html_str, flags=re.IGNORECASE)
    html_str = re.sub(r'SarkariResult', site_name, html_str, flags=re.IGNORECASE)
    html_str = re.sub(r'https?://(?:www\.)?sarkariresult\.com\.cm/?', f'https://{domain}/', html_str, flags=re.IGNORECASE)
    html_str = re.sub(r'sarkariresult\.com\.cm', domain, html_str, flags=re.IGNORECASE)

    return html_str

def get_footer_html(settings):
    socials = settings.get('socials', {})
    domain = settings.get('domain', 'studytopper.in')
    site_name = settings.get('site_name', 'STUDY TOPPER™')
    wa_url = socials.get('whatsapp', 'https://whatsapp.com/')
    tg_url = socials.get('telegram', 'https://t.me/')
    ig_url = socials.get('instagram', 'https://instagram.com/')
    yt_url = socials.get('youtube', 'https://youtube.com/')
    fb_url = socials.get('facebook', 'https://facebook.com/')
    tw_url = socials.get('twitter', 'https://x.com/')

    return f"""<div class="site-footer">
    <div class="gb-container gb-container-7d9550dd naman_footer alignwide">
        <div class="gb-grid-wrapper gb-grid-wrapper-b76f312f">
            <div class="gb-grid-column gb-grid-column-53cb46e2">
                <div class="gb-container gb-container-53cb46e2">
                    <div class="sarkari-wrapper">
                        <h3>Connect With Us</h3>
                        <div class="sarkari-grid">
                            <a href="{tw_url}" target="_blank">Study Topper @X</a>
                            <a href="{tg_url}" target="_blank">Study Topper @Telegram</a>
                            <a href="{wa_url}" target="_blank">Study Topper @WhatsApp</a>
                            <a href="{ig_url}" target="_blank">Study Topper @Instagram</a>
                            <a href="{fb_url}" target="_blank">Study Topper @Facebook</a>
                            <a href="{yt_url}" target="_blank">Study Topper @YouTube</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="gb-container gb-container-d1f47294" style="text-align:center; padding:15px 0;">
        <div class="gb-headline gb-headline-e41178b2 gb-headline-text" style="font-size:14px; margin-bottom:8px;">
            Copyright © 2026 | <strong><a href="/" data-type="link" data-id="{domain}">{domain}</a></strong><br>
            Official Website of Study Topper™ – {domain}
        </div>

        <div class="gb-container-658f27a5" style="display:flex; justify-content:center; gap:14px; flex-wrap:wrap;">
            <a class="gb-button gb-button-7d526092 gb-button-text" href="/" style="color:#ffffff !important; text-decoration:underline;">Home</a>
            <a class="gb-button gb-button-05aacc7b gb-button-text" href="/contact/" style="color:#ffffff !important; text-decoration:underline;">Contact</a>
            <a class="gb-button gb-button-c050fa03 gb-button-text" href="/privacy-policy/" style="color:#ffffff !important; text-decoration:underline;">Privacy Policy</a>
            <a class="gb-button gb-button-6172bea5 gb-button-text" href="/disclaimer/" style="color:#ffffff !important; text-decoration:underline;">Disclaimer</a>
        </div>
    </div>
</div>"""

def render_single_post_html(post, settings):
    site_name = settings.get('site_name', 'STUDY TOPPER™')
    domain = settings.get('domain', 'studytopper.in')
    
    socials = settings.get('socials', {})
    wa_url = socials.get('whatsapp', 'https://whatsapp.com/')
    tg_url = socials.get('telegram', 'https://t.me/')
    ig_url = socials.get('instagram', 'https://instagram.com/')
    yt_url = socials.get('youtube', 'https://youtube.com/')
    fb_url = socials.get('facebook', 'https://facebook.com/')
    tw_url = socials.get('twitter', 'https://x.com/')

    title = post.get('title', 'Govt Job Online Form')
    headline = post.get('headline') or title
    slug = post.get('slug', '')
    category_slug = post.get('category', 'latest-jobs')
    category_name = category_slug.replace('-', ' ').title()
    short_desc = post.get('short_desc', '')
    app_start = post.get('application_start_date', 'July 2026')
    app_last = post.get('application_last_date', 'August 2026')
    badge_val = post.get('custom_badge') or 'Active'
    raw_content = post.get('html_content', '')
    tags_str = post.get('tags', 'Govt Job, Study Topper')

    cleaned_content = clean_post_html_content(raw_content, settings)
    
    banner_url = f"/static/images/rrc_nfr_banner_2026.jpg" if 'nfr' in slug else f"/static/images/rrb_alp_banner_2026.jpg"

    tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
    tag_chips = ''.join([f'<span class="st-tag-chip">#{t}</span>' for t in tags_list])

    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} | {site_name}</title>
    <meta name="description" content="{short_desc[:160]}">
    <link rel="canonical" href="https://{domain}/{slug}/">
    <meta property="og:locale" content="en_US">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{title} | {site_name}">
    <meta property="og:description" content="{short_desc[:160]}">
    <meta property="og:url" content="https://{domain}/{slug}/">
    <meta property="og:site_name" content="{site_name}">
    <meta property="og:image" content="https://{domain}{banner_url}">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Source+Sans+Pro:400,600,700|Roboto:400,500,700|Open+Sans:400,600,700&display=swap">
    <link rel="stylesheet" href="/wp-content/themes/generatepress/assets/css/main.min.css?ver=3.5.1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {{ background-color:#ffffff; color:#000000; font-family:Open Sans, Arial, Helvetica, sans-serif; margin:0; padding:0; }}
        .site-header {{ background-color:#cd0808; text-align:center; padding:15px 0; }}
        .main-title {{ text-transform:uppercase; font-size:45px; font-weight:800; margin:0; line-height:1.1; }}
        .main-title a {{ color:#ffffff; text-decoration:none; }}
        .site-description {{ color:#ffffff; font-weight:700; font-size:25px; margin:4px 0 0 0; }}
        .main-navigation {{ background-color:#0c2340; }}
        .main-navigation .main-nav ul {{ list-style:none; margin:0; padding:0; display:flex; justify-content:center; flex-wrap:wrap; }}
        .main-navigation .main-nav ul li a {{ color:#ffffff; padding:10px 14px; font-size:14px; font-weight:700; text-decoration:none; display:block; }}
        .main-navigation .main-nav ul li a:hover {{ background-color:#982704; }}

        .st-post-container {{ max-width:1060px; margin:20px auto 40px; padding:0 12px; font-family:Open Sans, Arial, sans-serif; color:#1e293b; line-height:1.6; }}
        .st-breadcrumb {{ display:flex; align-items:center; flex-wrap:wrap; gap:6px; font-size:13px; color:#64748b; margin-bottom:14px; padding:8px 14px; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0; }}
        .st-breadcrumb a {{ color:#0284c7; text-decoration:none; font-weight:600; }}
        .st-breadcrumb a:hover {{ text-decoration:underline; }}
        .st-breadcrumb span.current {{ color:#0f172a; font-weight:600; }}

        .st-hero-card {{ background:#ffffff; border:1px solid #e2e8f0; border-top:4px solid #cd0808; border-radius:8px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,0.04); margin-bottom:20px; }}
        .st-badge-strip {{ display:flex; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
        .st-badge {{ font-size:11.5px; font-weight:700; padding:4px 10px; border-radius:4px; text-transform:uppercase; }}
        .st-badge-primary {{ background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; }}
        .st-badge-success {{ background:#dcfce7; color:#15803d; border:1px solid #86efac; }}
        .st-badge-info {{ background:#e0f2fe; color:#0369a1; border:1px solid #7dd3fc; }}

        .st-post-title {{ font-size:24px; font-weight:800; color:#0f172a; margin:0 0 10px; line-height:1.35; }}
        .st-meta-bar {{ display:flex; align-items:center; flex-wrap:wrap; gap:16px; font-size:13px; color:#64748b; border-bottom:1px dashed #cbd5e1; padding-bottom:12px; margin-bottom:14px; }}
        .st-meta-item {{ display:flex; align-items:center; gap:6px; }}
        .st-meta-item i {{ color:#cd0808; }}

        .st-stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-top:14px; }}
        .st-stat-box {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:12px; text-align:center; }}
        .st-stat-label {{ font-size:12px; color:#64748b; font-weight:600; text-transform:uppercase; margin-bottom:4px; }}
        .st-stat-value {{ font-size:17px; font-weight:800; color:#0f172a; }}
        .st-stat-value.red {{ color:#dc2626; }}
        .st-stat-value.green {{ color:#16a34a; }}

        .st-info-box {{ background:#fff8f8; border:1px solid #fecaca; border-left:5px solid #dc2626; padding:16px 20px; border-radius:6px; margin:20px 0; font-size:14px; line-height:1.7; }}
        .st-info-box strong.label {{ color:#991b1b; font-weight:700; font-size:14.5px; }}

        .st-social-strip {{ display:flex; justify-content:space-between; align-items:center; background:#0f172a; color:#ffffff; padding:12px 18px; border-radius:8px; margin:20px 0; flex-wrap:wrap; gap:12px; }}
        .st-social-title {{ font-size:14px; font-weight:700; display:flex; align-items:center; gap:8px; }}
        .st-social-btns {{ display:flex; gap:10px; flex-wrap:wrap; }}
        .st-btn-wa {{ background:#16a34a; color:#ffffff !important; text-decoration:none; padding:7px 16px; border-radius:6px; font-size:13px; font-weight:700; display:inline-flex; align-items:center; gap:6px; }}
        .st-btn-tg {{ background:#0284c7; color:#ffffff !important; text-decoration:none; padding:7px 16px; border-radius:6px; font-size:13px; font-weight:700; display:inline-flex; align-items:center; gap:6px; }}

        .st-matrix-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin:24px 0; }}
        @media (max-width:768px) {{ .st-matrix-grid {{ grid-template-columns:1fr; gap:16px; }} .main-title {{ font-size:30px; }} .site-description {{ font-size:18px; }} .st-post-title {{ font-size:19px; }} }}

        .st-matrix-card {{ background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; }}
        .st-matrix-head {{ background:#cd0808; color:#ffffff; padding:12px 16px; font-size:15px; font-weight:700; display:flex; align-items:center; gap:8px; }}
        .st-matrix-head.blue {{ background:#0c2340; }}
        .st-matrix-body {{ padding:16px; }}
        .st-list {{ list-style:none; margin:0; padding:0; }}
        .st-list li {{ display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #f1f5f9; font-size:13.5px; }}
        .st-list li:last-child {{ border-bottom:none; }}
        .st-list li span.key {{ color:#475569; font-weight:500; }}
        .st-list li span.val {{ color:#0f172a; font-weight:700; }}
        .st-list li span.val.highlight {{ color:#dc2626; font-size:14px; }}

        .st-section-card {{ background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; margin:24px 0; }}
        .st-section-head {{ background:#f8fafc; border-bottom:1px solid #e2e8f0; padding:14px 18px; font-size:16px; font-weight:700; color:#0f172a; display:flex; align-items:center; gap:8px; }}
        .st-section-head i {{ color:#cd0808; }}
        .st-section-body {{ padding:18px; font-size:14px; }}

        .st-table-responsive {{ width:100%; overflow-x:auto; margin-top:10px; }}
        .st-table {{ width:100%; border-collapse:collapse; text-align:left; font-size:13.5px; }}
        .st-table th {{ background:#0c2340; color:#ffffff; padding:12px 14px; font-weight:700; border:1px solid #1e293b; }}
        .st-table td {{ padding:12px 14px; border:1px solid #e2e8f0; vertical-align:middle; }}
        .st-table tr:nth-child(even) td {{ background:#f8fafc; }}

        .st-steps-container {{ display:flex; flex-direction:column; gap:12px; margin-top:10px; }}
        .st-step-item {{ display:flex; align-items:flex-start; gap:14px; background:#f8fafc; border:1px solid #e2e8f0; padding:12px 16px; border-radius:6px; }}
        .st-step-num {{ background:#cd0808; color:#ffffff; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:800; flex-shrink:0; margin-top:2px; }}
        .st-step-text {{ font-size:13.5px; color:#334155; line-height:1.6; }}

        .st-links-hub {{ background:#ffffff; border:2px solid #16a34a; border-radius:8px; overflow:hidden; margin:28px 0; }}
        .st-links-head {{ background:#16a34a; color:#ffffff; padding:14px 18px; font-size:17px; font-weight:800; text-align:center; }}
        .st-link-row {{ display:flex; justify-content:space-between; align-items:center; padding:14px 18px; border-bottom:1px solid #e2e8f0; font-size:14px; font-weight:600; }}
        .st-link-row:last-child {{ border-bottom:none; }}
        .st-link-row:nth-child(even) {{ background:#fdfdfd; }}
        .st-link-btn {{ background:#cd0808; color:#ffffff !important; text-decoration:none; padding:6px 16px; border-radius:5px; font-size:13px; font-weight:700; display:inline-flex; align-items:center; gap:6px; }}
        .st-link-btn.green {{ background:#16a34a; }}
        .st-link-btn.blue {{ background:#0284c7; }}

        .st-tags-box {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:20px; padding:14px; background:#f8fafc; border-radius:6px; border:1px solid #e2e8f0; align-items:center; }}
        .st-tag-chip {{ background:#ffffff; border:1px solid #cbd5e1; color:#334155; padding:4px 10px; border-radius:4px; font-size:12px; font-weight:600; }}

        .site-footer {{ background-color:#212121; color:#ffffff; }}
        .sarkari-wrapper {{ padding:25px 20px; text-align:center; }}
        .sarkari-wrapper h3 {{ color:#ffffff; font-size:18px; margin-bottom:14px; font-weight:700; }}
        .sarkari-grid {{ display:flex; justify-content:center; flex-wrap:wrap; gap:10px; margin-bottom:12px; }}
        .sarkari-grid a {{ background:#2f4468; color:#ffffff !important; padding:6px 14px; border-radius:4px; text-decoration:none; font-size:13px; font-weight:600; }}
        .gb-container-d1f47294 {{ background-color:#171717; color:#ffffff; text-align:center; padding:18px 0; }}
    </style>
</head>
<body class="wp-theme-generatepress single-post no-sidebar">
    <header class="site-header grid-container" id="masthead">
        <div class="inside-header grid-container">
            <div class="site-branding">
                <p class="main-title"><a href="/">{site_name}</a></p>
                <p class="site-description">{domain}</p>
            </div>
        </div>
    </header>

    <nav class="main-navigation grid-container" id="site-navigation">
        <div class="inside-navigation grid-container">
            <div id="primary-menu" class="main-nav">
                <ul id="menu-menu" class="menu sf-menu">
                    <li><a href="/">Home</a></li>
                    <li><a href="/latest-jobs/">Latest Job</a></li>
                    <li><a href="/admit-card/">Admit Card</a></li>
                    <li><a href="/result/">Result</a></li>
                    <li><a href="/admission/">Admission</a></li>
                    <li><a href="/syllabus/">Syllabus</a></li>
                    <li><a href="/answer-key/">Answer Key</a></li>
                    <li><a href="/contact/">Contact Us</a></li>
                    <li><a href="/privacy-policy/">Privacy Policy</a></li>
                    <li><a href="/disclaimer/">Disclaimer</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <div class="st-post-container">
        <!-- Breadcrumb -->
        <nav class="st-breadcrumb">
            <a href="/"><i class="fa-solid fa-house"></i> Home</a>
            <span>»</span>
            <a href="/{category_slug}/">{category_name}</a>
            <span>»</span>
            <span class="current">{title}</span>
        </nav>

        <!-- Hero Card -->
        <div class="st-hero-card">
            <div class="st-badge-strip">
                <span class="st-badge st-badge-primary">🔥 Latest Notification</span>
                <span class="st-badge st-badge-success">{badge_val}</span>
                <span class="st-badge st-badge-info">Active &amp; Verified</span>
            </div>

            <h1 class="st-post-title">{headline}</h1>
            
            <div class="st-meta-bar">
                <div class="st-meta-item"><i class="fa-regular fa-building"></i> <strong>Recruitment Board:</strong> Indian Railways / Govt of India</div>
                <div class="st-meta-item"><i class="fa-regular fa-calendar-days"></i> <strong>Application Window:</strong> {app_start} to {app_last}</div>
                <div class="st-meta-item"><i class="fa-solid fa-shield-halved"></i> <strong>Status:</strong> Active Online Form</div>
            </div>

            <!-- Stats Ribbon -->
            <div class="st-stats-grid">
                <div class="st-stat-box">
                    <div class="st-stat-label">Total Posts</div>
                    <div class="st-stat-value red">{badge_val}</div>
                </div>
                <div class="st-stat-box">
                    <div class="st-stat-label">Application Mode</div>
                    <div class="st-stat-value">Online Portal</div>
                </div>
                <div class="st-stat-box">
                    <div class="st-stat-label">Last Date</div>
                    <div class="st-stat-value red">{app_last}</div>
                </div>
                <div class="st-stat-box">
                    <div class="st-stat-label">Job Location</div>
                    <div class="st-stat-value green">All India</div>
                </div>
            </div>
        </div>

        <!-- Featured Banner Image (Zero Copyright) -->
        <div style="text-align:center; margin:15px 0;">
            <img src="{banner_url}" alt="{title} | {site_name}" style="max-width:100%; height:auto; border-radius:8px; border:2px solid #ab183d; box-shadow:0 4px 12px rgba(0,0,0,0.06);" />
        </div>

        <!-- Short Overview -->
        <div class="st-info-box">
            <strong class="label"><i class="fa-solid fa-circle-info"></i> Short Information :</strong>
            {short_desc}
        </div>

        <!-- Social Strip -->
        <div class="st-social-strip">
            <div class="st-social-title"><i class="fa-solid fa-bell"></i> Get Instant Govt Job Alerts On Your Phone</div>
            <div class="st-social-btns">
                <a href="{wa_url}" target="_blank" class="st-btn-wa"><i class="fa-brands fa-whatsapp"></i> Join WhatsApp Channel</a>
                <a href="{tg_url}" target="_blank" class="st-btn-tg"><i class="fa-brands fa-telegram"></i> Join Telegram Group</a>
            </div>
        </div>

        <!-- Two Column Matrix -->
        <div class="st-matrix-grid">
            <div class="st-matrix-card">
                <div class="st-matrix-head">
                    <i class="fa-regular fa-calendar-check"></i> Important Dates
                </div>
                <div class="st-matrix-body">
                    <ul class="st-list">
                        <li>
                            <span class="key">Application Start Date</span>
                            <span class="val">{app_start}</span>
                        </li>
                        <li>
                            <span class="key">Last Date to Apply Online</span>
                            <span class="val highlight">{app_last}</span>
                        </li>
                        <li>
                            <span class="key">Fee Payment Last Date</span>
                            <span class="val">{app_last}</span>
                        </li>
                        <li>
                            <span class="key">Exam / Merit List Date</span>
                            <span class="val">As per Schedule</span>
                        </li>
                        <li>
                            <span class="key">Admit Card Release</span>
                            <span class="val">Before Exam</span>
                        </li>
                    </ul>
                </div>
            </div>

            <div class="st-matrix-card">
                <div class="st-matrix-head blue">
                    <i class="fa-solid fa-indian-rupee-sign"></i> Application Fee
                </div>
                <div class="st-matrix-body">
                    <ul class="st-list">
                        <li>
                            <span class="key">General / OBC / EWS</span>
                            <span class="val">₹ 100/- to ₹ 500/-</span>
                        </li>
                        <li>
                            <span class="key">SC / ST / PwBD</span>
                            <span class="val" style="color:#16a34a;">₹ 0/- or Refundable</span>
                        </li>
                        <li>
                            <span class="key">All Female Candidates</span>
                            <span class="val" style="color:#16a34a;">₹ 0/- or Refundable</span>
                        </li>
                        <li>
                            <span class="key">Payment Mode</span>
                            <span class="val" style="font-size:12px;">Online (UPI, Debit Card, Net Banking)</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Structured Body Table / Post Content -->
        <div class="st-section-card">
            <div class="st-section-head">
                <i class="fa-solid fa-graduation-cap"></i> Vacancy Breakdown &amp; Educational Qualification
            </div>
            <div class="st-section-body" style="padding:15px;">
                {cleaned_content if cleaned_content and len(cleaned_content) > 50 else f'<p>{short_desc}</p>'}
            </div>
        </div>

        <!-- How To Apply -->
        <div class="st-section-card">
            <div class="st-section-head">
                <i class="fa-solid fa-list-check"></i> Step-by-Step Guide to Fill Online Application Form
            </div>
            <div class="st-section-body">
                <div class="st-steps-container">
                    <div class="st-step-item">
                        <div class="st-step-num">1</div>
                        <div class="st-step-text"><strong>Visit Official Portal:</strong> Open the official application link given under the Important Links section below.</div>
                    </div>
                    <div class="st-step-item">
                        <div class="st-step-num">2</div>
                        <div class="st-step-text"><strong>New Registration (OTR):</strong> Register with your valid active Mobile Number, Email ID, and basic details.</div>
                    </div>
                    <div class="st-step-item">
                        <div class="st-step-num">3</div>
                        <div class="st-step-text"><strong>Fill Application Form:</strong> Enter your educational qualifications, trade details, and preferred post/zone options.</div>
                    </div>
                    <div class="st-step-item">
                        <div class="st-step-num">4</div>
                        <div class="st-step-text"><strong>Upload Documents:</strong> Upload clear scanned copies of Passport Photograph, Signature, and required Certificates.</div>
                    </div>
                    <div class="st-step-item">
                        <div class="st-step-num">5</div>
                        <div class="st-step-text"><strong>Fee Payment &amp; Printout:</strong> Pay application fee online (if applicable) and download your final confirmation printout.</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Useful Important Links Hub -->
        <div class="st-links-hub">
            <div class="st-links-head">
                <i class="fa-solid fa-link"></i> SOME USEFUL IMPORTANT LINKS
            </div>
            <div class="st-link-row">
                <span>Apply Online Registration Form</span>
                <a href="#" target="_blank" class="st-link-btn"><i class="fa-solid fa-arrow-up-right-from-square"></i> Click Here</a>
            </div>
            <div class="st-link-row">
                <span>Download Official Notification PDF</span>
                <a href="#" target="_blank" class="st-link-btn"><i class="fa-solid fa-download"></i> Click Here</a>
            </div>
            <div class="st-link-row">
                <span>Check Study Topper Official Portal</span>
                <a href="/" target="_blank" class="st-link-btn blue"><i class="fa-solid fa-globe"></i> Click Here</a>
            </div>
            <div class="st-link-row">
                <span>Join Study Topper WhatsApp Channel</span>
                <a href="{wa_url}" target="_blank" class="st-link-btn green"><i class="fa-brands fa-whatsapp"></i> Join Now</a>
            </div>
            <div class="st-link-row">
                <span>Join Study Topper Telegram Community</span>
                <a href="{tg_url}" target="_blank" class="st-link-btn blue"><i class="fa-brands fa-telegram"></i> Join Now</a>
            </div>
        </div>

        <!-- Tags -->
        <div class="st-tags-box">
            <strong style="font-size:13px; color:#475569;"><i class="fa-solid fa-tags" style="color:#cd0808;"></i> Tags:</strong>
            {tag_chips}
        </div>
    </div>

    <!-- Site Footer -->
    <div class="site-footer">
        <div class="gb-container gb-container-7d9550dd naman_footer alignwide">
            <div class="gb-grid-wrapper gb-grid-wrapper-b76f312f">
                <div class="gb-grid-column gb-grid-column-53cb46e2">
                    <div class="gb-container gb-container-53cb46e2">
                        <div class="sarkari-wrapper">
                            <h3>Connect With Us</h3>
                            <div class="sarkari-grid">
                                <a href="{tw_url}" target="_blank">Study Topper @X</a>
                                <a href="{tg_url}" target="_blank">Study Topper @Telegram</a>
                                <a href="{wa_url}" target="_blank">Study Topper @WhatsApp</a>
                                <a href="{ig_url}" target="_blank">Study Topper @Instagram</a>
                                <a href="{fb_url}" target="_blank">Study Topper @Facebook</a>
                                <a href="{yt_url}" target="_blank">Study Topper @YouTube</a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="gb-container gb-container-d1f47294">
            <div class="gb-headline gb-headline-e41178b2 gb-headline-text" style="font-size:14px; margin-bottom:8px;">
                Copyright © 2026 | <strong><a href="/" data-type="link" data-id="{domain}">{domain}</a></strong><br>
                Official Website of Study Topper™ – {domain}
            </div>

            <div class="gb-container-658f27a5" style="display:flex; justify-content:center; gap:14px; flex-wrap:wrap;">
                <a class="gb-button gb-button-7d526092 gb-button-text" href="/" style="color:#ffffff !important; text-decoration:underline;">Home</a>
                <a class="gb-button gb-button-05aacc7b gb-button-text" href="/contact/" style="color:#ffffff !important; text-decoration:underline;">Contact</a>
                <a class="gb-button gb-button-c050fa03 gb-button-text" href="/privacy-policy/" style="color:#ffffff !important; text-decoration:underline;">Privacy Policy</a>
                <a class="gb-button gb-button-6172bea5 gb-button-text" href="/disclaimer/" style="color:#ffffff !important; text-decoration:underline;">Disclaimer</a>
            </div>
        </div>
    </div>
</body>
</html>"""

# ==================== CATEGORY & SEARCH PAGE RENDERERS ====================

CATEGORY_SLUG_MAP = {
    'result': 'Results',
    'results': 'Results',
    'admit-card': 'Admit Card',
    'admit-cards': 'Admit Card',
    'latest-jobs': 'Latest Jobs',
    'latestjob': 'Latest Jobs',
    'jobs': 'Latest Jobs',
    'answer-key': 'Answer Key',
    'answerkey': 'Answer Key',
    'syllabus': 'Syllabus',
    'admission': 'Admission',
    'admissions': 'Admission',
    'certificate-verification': 'Certificate Verification',
    'important': 'Important'
}

def render_category_page_html(cat_slug, cat_title, cat_posts, settings):
    site_name = settings.get('site_name', 'STUDY TOPPER™')
    domain = settings.get('domain', 'studytopper.in')
    footer_text = settings.get('footer_text', 'Copyright © 2009 - 2026 | SarkariResult.com.cm. All Rights Reserved.')

    if cat_posts:
        items_html = ''
        for p in cat_posts:
            badge_suffix = ''
            if p.get('custom_badge'):
                badge_suffix = f" – {p.get('custom_badge')}"
            elif p.get('is_date_extended'):
                badge_suffix = " – Date Extend"
            elif p.get('is_pinned'):
                badge_suffix = " – Last Date Soon"
            items_html += f'<li style="margin-bottom:12px; font-size:14.5px;"><a href="/{p.get("slug")}/" style="color:#0000c0; text-decoration:none; font-weight:600;">{p.get("title")}{badge_suffix}</a></li>'
        posts_list_html = f'<ul style="list-style-type:square; padding-left:25px; margin:15px 0;">{items_html}</ul>'
    else:
        posts_list_html = '<div style="text-align:center; padding:50px 15px; color:#64748b;"><i class="fa-solid fa-folder-open" style="font-size:42px; color:#cbd5e1; display:block; margin-bottom:12px;"></i><p style="font-size:17px; font-weight:600; color:#334155; margin:0 0 6px;">No posts in this category yet</p><p style="font-size:13.5px; margin:0;">New notifications published from Admin Panel will appear here automatically.</p></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cat_title} 2026 : {site_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: Arial, Helvetica, sans-serif; margin:0; padding:0; background:#fff; color:#000; font-size:14px; line-height:1.5; }}
        header.site-header {{ background-color: #cd0808; text-align: center; padding: 15px 10px; }}
        .main-title {{ margin: 0; font-size: 32px; font-weight: 800; }}
        .main-title a {{ color: #fff; text-decoration: none; }}
        .site-description {{ color: #fff; font-size: 20px; font-weight: 700; margin: 4px 0 0; }}
        nav.main-navigation {{ background-color: #0c2340; text-align: center; padding: 10px; overflow-x: auto; white-space: nowrap; }}
        nav.main-navigation a {{ color: #fff; text-decoration: none; margin: 0 10px; font-size: 14px; font-weight: 700; }}
        nav.main-navigation a:hover {{ text-decoration: underline; }}
        .page-container {{ max-width: 1040px; margin: 20px auto; padding: 0 12px; min-height: 400px; }}
        .breadcrumb {{ font-size: 13px; color: #555; margin-bottom: 15px; }}
        .breadcrumb a {{ color: #0000ef; text-decoration: underline; }}
        .cat-card {{ border: 2px solid #ab183d; border-radius: 4px; padding: 20px; background: #fff; }}
        h1.cat-heading {{ background: #ab183d; color: #fff; font-size: 20px; text-align: center; padding: 12px; margin: -20px -20px 20px -20px; font-weight: 700; }}
        footer.site-footer {{ background-color: #212121; color: #ffffff; text-align: center; padding: 25px 15px; margin-top: 40px; }}
        footer.site-footer a {{ color: #ffffff; text-decoration: underline; margin: 0 8px; font-size: 13px; }}
    </style>
</head>
<body>
    <header class="site-header">
        <h1 class="main-title"><a href="/">{site_name}</a></h1>
        <p class="site-description">{domain}</p>
    </header>
    <nav class="main-navigation">
        <a href="/">Home</a>
        <a href="/latest-jobs/">Latest Jobs</a>
        <a href="/result/">Results</a>
        <a href="/admit-card/">Admit Card</a>
        <a href="/answer-key/">Answer Key</a>
        <a href="/syllabus/">Syllabus</a>
        <a href="/admission/">Admission</a>
        <a href="/contact/">Contact Us</a>
    </nav>
    <div class="page-container">
        <div class="breadcrumb">
            <a href="/">Home</a> » <span>{cat_title}</span>
        </div>
        <div class="cat-card">
            <h1 class="cat-heading">{cat_title} 2026 : Study Topper</h1>
            {posts_list_html}
            <div style="text-align:center; margin-top:30px;">
                <a href="/" style="background:#ab183d; color:#fff; text-decoration:none; padding:8px 18px; border-radius:4px; font-weight:700; font-size:13px; display:inline-block;">« Back to Study Topper Home</a>
            </div>
        </div>
    </div>
    <footer class="site-footer">
        <p>{footer_text}</p>
        <div class="gb-container-658f27a5" style="margin-top:10px;">
            <a class="gb-button" href="/">Home</a>
            <a class="gb-button" href="/contact/">Contact</a>
            <a class="gb-button" href="/privacy-policy/">Privacy Policy</a>
            <a class="gb-button" href="/disclaimer/">Disclaimer</a>
        </div>
    </footer>
</body>
</html>"""

def render_search_page_html(query, search_results, settings):
    site_name = settings.get('site_name', 'STUDY TOPPER™')
    domain = settings.get('domain', 'studytopper.in')
    footer_text = settings.get('footer_text', 'Copyright © 2009 - 2026 | SarkariResult.com.cm. All Rights Reserved.')

    if search_results:
        items_html = ''
        for p in search_results:
            cat_name = p.get('category', 'Notification').replace('-', ' ').title()
            items_html += f'<li style="margin-bottom:12px; font-size:14.5px;"><a href="/{p.get("slug")}/" style="color:#0000c0; text-decoration:none; font-weight:600;">{p.get("title")}</a> <span style="background:#f1f5f9; color:#475569; padding:1px 6px; border-radius:3px; font-size:11px; font-weight:600; margin-left:6px;">{cat_name}</span></li>'
        results_html = f'<ul style="list-style-type:square; padding-left:25px; margin:15px 0;">{items_html}</ul>'
    else:
        results_html = f'<div style="text-align:center; padding:50px 15px; color:#64748b;"><i class="fa-solid fa-magnifying-glass" style="font-size:42px; color:#cbd5e1; display:block; margin-bottom:12px;"></i><p style="font-size:17px; font-weight:600; color:#334155; margin:0 0 6px;">No official notifications found for "{query}"</p><p style="font-size:13.5px; margin:0;">Only verified notifications published on this portal are searched.</p></div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search: {query} - {site_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: Arial, Helvetica, sans-serif; margin:0; padding:0; background:#fff; color:#000; font-size:14px; line-height:1.5; }}
        header.site-header {{ background-color: #cd0808; text-align: center; padding: 15px 10px; }}
        .main-title {{ margin: 0; font-size: 32px; font-weight: 800; }}
        .main-title a {{ color: #fff; text-decoration: none; }}
        .site-description {{ color: #fff; font-size: 20px; font-weight: 700; margin: 4px 0 0; }}
        nav.main-navigation {{ background-color: #0c2340; text-align: center; padding: 10px; overflow-x: auto; white-space: nowrap; }}
        nav.main-navigation a {{ color: #fff; text-decoration: none; margin: 0 10px; font-size: 14px; font-weight: 700; }}
        nav.main-navigation a:hover {{ text-decoration: underline; }}
        .page-container {{ max-width: 1040px; margin: 20px auto; padding: 0 12px; min-height: 400px; }}
        .breadcrumb {{ font-size: 13px; color: #555; margin-bottom: 15px; }}
        .breadcrumb a {{ color: #0000ef; text-decoration: underline; }}
        .cat-card {{ border: 2px solid #ab183d; border-radius: 4px; padding: 20px; background: #fff; }}
        h1.cat-heading {{ background: #ab183d; color: #fff; font-size: 20px; text-align: center; padding: 12px; margin: -20px -20px 20px -20px; font-weight: 700; }}
        footer.site-footer {{ background-color: #212121; color: #ffffff; text-align: center; padding: 25px 15px; margin-top: 40px; }}
        footer.site-footer a {{ color: #ffffff; text-decoration: underline; margin: 0 8px; font-size: 13px; }}
    </style>
</head>
<body>
    <header class="site-header">
        <h1 class="main-title"><a href="/">{site_name}</a></h1>
        <p class="site-description">{domain}</p>
    </header>
    <nav class="main-navigation">
        <a href="/">Home</a>
        <a href="/latest-jobs/">Latest Jobs</a>
        <a href="/result/">Results</a>
        <a href="/admit-card/">Admit Card</a>
        <a href="/answer-key/">Answer Key</a>
        <a href="/syllabus/">Syllabus</a>
        <a href="/admission/">Admission</a>
        <a href="/contact/">Contact Us</a>
    </nav>
    <div class="page-container">
        <div class="breadcrumb">
            <a href="/">Home</a> » <span>Search: {query}</span>
        </div>
        <div class="cat-card">
            <h1 class="cat-heading">Search Results for : "{query}"</h1>
            {results_html}
            <div style="text-align:center; margin-top:30px;">
                <a href="/" style="background:#ab183d; color:#fff; text-decoration:none; padding:8px 18px; border-radius:4px; font-weight:700; font-size:13px; display:inline-block;">« Back to Study Topper Home</a>
            </div>
        </div>
    </div>
    <footer class="site-footer">
        <p>{footer_text}</p>
        <div class="gb-container-658f27a5" style="margin-top:10px;">
            <a class="gb-button" href="/">Home</a>
            <a class="gb-button" href="/contact/">Contact</a>
            <a class="gb-button" href="/privacy-policy/">Privacy Policy</a>
            <a class="gb-button" href="/disclaimer/">Disclaimer</a>
        </div>
    </footer>
</body>
</html>"""

COL_MAPPING = {
    '0b76599a': 'result',
    'e64d3148': 'admit-card',
    'c7488d9a': 'latest-jobs',
    'd19ddc59': 'answer-key',
    'b48dca36': 'syllabus',
    '51daea0e': 'admission'
}

def load_settings():
    if supa.is_supabase_configured():
        try:
            supa_settings = supa.fetch_settings_from_supabase()
            if supa_settings:
                return supa_settings
        except Exception:
            pass

    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass

    return DEFAULT_SETTINGS

def save_settings_data(data):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Notice: Local settings file write skipped on read-only FS: {e}")

    if supa.is_supabase_configured():
        try:
            supa.save_settings_to_supabase(data)
        except Exception as se:
            print(f"Notice: Supabase save exception: {se}")

def sanitize_html(html_content, current_host, is_alria_mode=False):
    soup = BeautifulSoup(html_content, 'html.parser')
    settings = load_settings()
    theme = settings.get('theme_colors', {})

    # 1. Strip external ads and tracking scripts
    for s in soup.find_all(['script', 'iframe', 'ins']):
        src = s.get('src', '')
        classes = s.get('class', [])
        if any(ad in src for ad in ['googlesyndication', 'doubleclick', 'google-analytics', 'izooto']):
            s.decompose()
        elif 'adsbygoogle' in classes:
            s.decompose()

    # 2. Inject Google Analytics (GA4) if ID is provided
    seo_cfg = settings.get('seo', {})
    ga_id = seo_cfg.get('google_analytics_id', '').strip()
    if ga_id and soup.head:
        ga_script = soup.new_tag('script', src=f"https://www.googletagmanager.com/gtag/js?id={ga_id}", crossorigin="anonymous", **{'async': True})
        soup.head.append(ga_script)
        ga_inline = soup.new_tag('script')
        ga_inline.string = f"""
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{ga_id}');
        """
        soup.head.append(ga_inline)

    # 3. Inject Google Search Console Verification Meta
    gsc_meta = seo_cfg.get('google_site_verification', '').strip()
    if gsc_meta and soup.head:
        if '<meta' in gsc_meta:
            soup.head.append(BeautifulSoup(gsc_meta, 'html.parser'))
        else:
            soup.head.append(soup.new_tag('meta', attrs={'name': 'google-site-verification', 'content': gsc_meta}))

    # 4. Inject Global Meta Description & Keywords
    if seo_cfg.get('meta_description') and soup.head:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_desc['content'] = seo_cfg.get('meta_description')
        else:
            soup.head.append(soup.new_tag('meta', attrs={'name': 'description', 'content': seo_cfg.get('meta_description')}))

    # 5. Inject Custom <head> & <body> Code
    if seo_cfg.get('custom_head_code') and soup.head:
        soup.head.append(BeautifulSoup(seo_cfg.get('custom_head_code'), 'html.parser'))
    if seo_cfg.get('custom_footer_code') and soup.body:
        soup.body.append(BeautifulSoup(seo_cfg.get('custom_footer_code'), 'html.parser'))

    # 6. Inject Google AdSense Auto Ads if enabled
    adsense_cfg = settings.get('adsense', {})
    if adsense_cfg.get('enabled') and adsense_cfg.get('client_id'):
        client_id = adsense_cfg.get('client_id').strip()
        if soup.head:
            ad_script = soup.new_tag('script', src=f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}", crossorigin="anonymous", **{'async': True})
            soup.head.append(ad_script)

    # 7. Exact Desktop Grid Styling & Dynamic Theme Colors
    hdr_bg = theme.get('header_bg', '#ab183d')
    hdr_txt = theme.get('header_text', '#ffffff')
    nav_bg = theme.get('nav_bg', '#0c2340')
    nav_txt = theme.get('nav_text', '#ffffff')
    wa_bg = theme.get('whatsapp_btn_bg', '#00a82d')
    wa_txt = theme.get('whatsapp_btn_text', '#ffffff')
    foot_bg = theme.get('footer_bg', '#1d2327')
    foot_txt = theme.get('footer_text', '#ffffff')

    center_style = soup.new_tag('style')
    center_style.string = f"""
    :root {{
        --sarkari-hdr-bg: {hdr_bg};
        --sarkari-hdr-txt: {hdr_txt};
        --sarkari-nav-bg: {nav_bg};
        --sarkari-nav-txt: {nav_txt};
        --sarkari-wa-bg: {wa_bg};
        --sarkari-wa-txt: {wa_txt};
        --sarkari-foot-bg: {foot_bg};
        --sarkari-foot-txt: {foot_txt};
    }}
    header.site-header, .site-header, .site-header .inside-header {{
        background-color: var(--sarkari-hdr-bg) !important;
        color: var(--sarkari-hdr-txt) !important;
    }}
    header.site-header h1, header.site-header a, .site-header .main-title a {{
        color: var(--sarkari-hdr-txt) !important;
    }}
    #site-navigation, .main-navigation, .main-navigation .inside-navigation {{
        background-color: var(--sarkari-nav-bg) !important;
    }}
    #site-navigation .main-nav ul li a, .main-navigation a {{
        color: var(--sarkari-nav-txt) !important;
    }}
    .whatsapp-btn, .whatsapp-btn-wrapper a, a.gb-button-f2e1697c {{
        background-color: var(--sarkari-wa-bg) !important;
        color: var(--sarkari-wa-txt) !important;
    }}
    .gb-container-658f27a5 a.gb-button, .gb-container-d1f47294 a.gb-button, .site-footer a.gb-button {{
        background-color: #000000 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 4px !important;
    }}
    .gb-container-658f27a5 a.gb-button:hover, .gb-container-d1f47294 a.gb-button:hover, .site-footer a.gb-button:hover {{
        background-color: #222222 !important;
        color: #ffffff !important;
    }}
    footer.site-footer, .site-footer, .site-info {{
        background-color: var(--sarkari-foot-bg) !important;
        color: var(--sarkari-foot-txt) !important;
    }}
    footer.site-footer a, .site-info a {{
        color: var(--sarkari-foot-txt) !important;
    }}

    /* DESKTOP ONLY (min-width: 768px): 3 Boxes in Row 1, 3 Boxes in Row 2 */
    @media (min-width: 768px) {{
        .gb-grid-wrapper-180dce95 {{
            display: grid !important;
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 14px !important;
            max-width: 1120px !important;
            margin: 15px auto !important;
            padding: 0 10px !important;
            box-sizing: border-box !important;
            width: 100% !important;
        }}
        .gb-grid-wrapper-180dce95 > .gb-grid-column {{
            width: 100% !important;
            max-width: 100% !important;
            flex: none !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
        }}
        .gb-grid-wrapper-180dce95 > .gb-grid-column > .gb-container {{
            height: 100% !important;
            margin: 0 !important;
            display: flex !important;
            flex-direction: column !important;
            box-sizing: border-box !important;
        }}
        
        .gb-grid-wrapper-5aaa8125,
        .gb-grid-wrapper-389edcd7 {{
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            gap: 8px !important;
            max-width: 1120px !important;
            margin: 0 auto 8px auto !important;
            padding: 0 10px !important;
            box-sizing: border-box !important;
            width: 100% !important;
        }}
        .gb-grid-wrapper-5aaa8125 > .gb-grid-column,
        .gb-grid-wrapper-389edcd7 > .gb-grid-column {{
            width: 100% !important;
            max-width: 100% !important;
            flex: none !important;
            margin: 0 !important;
            padding: 0 !important;
            box-sizing: border-box !important;
        }}
    }}
    .alria-edit-btn {{
        background: #ef4444 !important;
        color: #ffffff !important;
        border: none !important;
        padding: 3px 10px !important;
        border-radius: 4px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        cursor: pointer !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        margin: 4px 0 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 4px !important;
        text-decoration: none !important;
        z-index: 1000 !important;
    }}
    .alria-edit-btn:hover {{ background: #dc2626 !important; }}
    """
    if soup.head:
        soup.head.append(center_style)

    # 8. Dynamic Site Name & Domain Name Subtitle in Header
    site_name = settings.get('site_name', 'STUDY TOPPER')
    if site_name:
        if soup.title:
            soup.title.string = f"{site_name} : Study Topper Official, Latest Online Form, Result, Admit Card"
        for mt in soup.find_all(class_='main-title'):
            a = mt.find('a')
            if a: a.string = site_name
            else: mt.string = site_name

    # Display website domain in Header subtitle (e.g. studytopper.in)
    domain_text = settings.get('domain', 'SarkariResult.com.cm')
    for sd in soup.find_all(class_='site-description'):
        sd.string = domain_text

    # 9. Dynamic Top Banner Text
    top_text = settings.get('top_banner_text')
    if top_text:
        top_p = soup.find(class_='gb-headline-d55a09d3') or soup.find(class_=re.compile(r'gb-headline-.*d55a09d3'))
        if top_p:
            top_p.string = top_text

    # 10. Dynamic Top 8 Cards
    cards = settings.get('highlight_cards', [])
    card_cols = [
        '2f6de309', '6de8e6a5', 'f69a2a15', 'cb185b36',
        '962a1393', '48ff7430', '3b560729', '659c2f86'
    ]
    for idx, col_id in enumerate(card_cols):
        col_div = soup.find(class_=f'gb-grid-column-{col_id}')
        if col_div:
            a_tag = col_div.find('a')
            if a_tag:
                if idx < len(cards) and cards[idx].get('title'):
                    a_tag.string = cards[idx].get('title')
                    if cards[idx].get('url'):
                        a_tag['href'] = cards[idx].get('url')
                card_bg = theme.get(f'card_{idx+1}_bg')
                if card_bg:
                    a_tag['style'] = f'background-color: {card_bg} !important; color: #ffffff !important;'

    # 11. Dynamic Grid Column Section Titles, Colors & Dynamic Post Lists
    grid_headers = settings.get('grid_headers', {})
    all_active_posts = load_all_active_posts()

    for col_cls, cat_key in COL_MAPPING.items():
        col_divs = soup.find_all(class_=re.compile(rf'gb-grid-column-{col_cls}'))
        for col_div in col_divs:
            container = col_div.find(class_='gb-container') or col_div
            h2 = container.find(class_=re.compile(r'gb-headline.*-text'))
            if h2:
                if cat_key in grid_headers and grid_headers[cat_key].get('title'):
                    h2.string = grid_headers[cat_key].get('title')
                cat_norm = cat_key.replace('-', '_')
                col_bg = theme.get(f'{cat_norm}_header_bg') or theme.get('result_header_bg', '#ab183d')
                col_txt = theme.get(f'{cat_norm}_header_text') or '#ffffff'
                h2['style'] = f'background-color:{col_bg} !important; color:{col_txt} !important; text-align:center; font-weight:700; padding:6px 0;'

            for ul_tag in container.find_all('ul', class_=re.compile(r'wp-block-latest-posts')):
                ul_tag.clear()
                cat_new_posts = [p for p in all_active_posts if p.get('category') == cat_key and not p.get('is_temporary')]
                if cat_new_posts:
                    for cp in cat_new_posts:
                        new_li = soup.new_tag('li')
                        new_a = soup.new_tag('a', **{'class': 'wp-block-latest-posts__post-title', 'href': f'/{cp["slug"]}/'})
                        badge_suffix = ''
                        if cp.get('custom_badge'):
                            badge_suffix = f" – {cp.get('custom_badge')}"
                        elif cp.get('is_date_extended'):
                            badge_suffix = " – Date Extend"
                        elif cp.get('is_pinned'):
                            badge_suffix = " – Last Date Soon"
                        new_a.string = f"{cp['title']}{badge_suffix}"
                        new_li.append(new_a)
                        ul_tag.append(new_li)
                else:
                    empty_li = soup.new_tag('li', style='list-style:none; color:#64748b; font-size:13px; padding:15px 10px; text-align:center; font-style:italic;')
                    empty_li.string = "No notifications yet. New posts will appear here."
                    ul_tag.append(empty_li)

    # 12. Dynamic Guidelines & FAQ Block
    c08 = soup.find(class_='gb-container-08c3e704')
    if c08:
        inside = c08.find(class_='gb-inside-container')
        if inside:
            info_secs = settings.get('info_sections', [])
            faq_items = settings.get('faq_items', [])
            if info_secs or faq_items:
                inside.clear()
                for sec in info_secs:
                    if sec.get('title'):
                        h2_tag = soup.new_tag('h2', **{'class': 'gb-headline gb-headline-02a5ae4c gb-headline-text'}, style='background-color:#a80909; color:#fff; padding:6px 10px; margin:15px 0 8px; font-size:16px; font-weight:700;')
                        h2_tag.string = sec.get('title', '')
                        inside.append(h2_tag)
                    if sec.get('content'):
                        p_tag = soup.new_tag('p', **{'class': 'has-text-align-center wp-block-paragraph'}, style='padding:8px 12px; font-size:15px; line-height:1.6; text-align:left;')
                        p_tag.string = sec.get('content', '')
                        inside.append(p_tag)
                if faq_items:
                    faq_h2 = soup.new_tag('h2', **{'class': 'gb-headline gb-headline-02a5ae4c gb-headline-text'}, style='background-color:#a80909; color:#fff; padding:6px 10px; margin:15px 0 8px; font-size:16px; font-weight:700;')
                    faq_h2.string = "FAQ – Frequently Asked Questions"
                    inside.append(faq_h2)
                    faq_box = soup.new_tag('div', style='padding:10px 12px; margin-bottom:15px;')
                    for i, faq in enumerate(faq_items, 1):
                        if faq.get('q'):
                            qp = soup.new_tag('p', style='text-align:left; margin:10px 0 3px; font-weight:700; color:#a80909; font-size:15px;')
                            qp.append(BeautifulSoup(f"<span style='color:#000;'>Q {i}.</span> {faq.get('q', '')}", 'html.parser'))
                            faq_box.append(qp)
                        if faq.get('a'):
                            ap = soup.new_tag('p', style='text-align:justify; margin:0 0 12px; font-size:14px; line-height:1.5; color:#222;')
                            ap.append(BeautifulSoup(f"<strong style='color:#077822;'>Ans.</strong> {faq.get('a', '')}", 'html.parser'))
                            faq_box.append(ap)
                    inside.append(faq_box)

    # 13. Dynamic Footer Copyright Text & Social Links
    if settings.get('footer_text'):
        foot_div = soup.find(class_='gb-headline-e41178b2') or soup.find(class_=re.compile(r'gb-headline-.*e41178b2'))
        if foot_div:
            foot_div.string = settings.get('footer_text')

    socials = settings.get('socials', {})
    sarkari_grid = soup.find(class_='sarkari-grid')
    if sarkari_grid and socials:
        for a in sarkari_grid.find_all('a'):
            txt = a.get_text()
            if '@Telegram' in txt and socials.get('telegram'):
                a['href'] = socials.get('telegram')
            elif '@WhatsApp' in txt and socials.get('whatsapp'):
                a['href'] = socials.get('whatsapp')
            elif '@YouTube' in txt and socials.get('youtube'):
                a['href'] = socials.get('youtube')
            elif '@Instagram' in txt and socials.get('instagram'):
                a['href'] = socials.get('instagram')
            elif '@Facebook' in txt and socials.get('facebook'):
                a['href'] = socials.get('facebook')
            elif '@X' in txt and socials.get('twitter'):
                a['href'] = socials.get('twitter')
    # 12. Inject /alria Live Editor Toolbar & In-place Buttons
    if is_alria_mode:
        if soup.head:
            soup.head.append(soup.new_tag('meta', attrs={'name': 'robots', 'content': 'noindex, nofollow'}))

        header = soup.find('header') or soup.find(class_='site-header')
        if header:
            h_btn = soup.new_tag('div', style='text-align:center; padding:4px;')
            h_btn.append(BeautifulSoup("<button class='alria-edit-btn' onclick=\"openModal('modal-branding')\">✏️ Edit Branding &amp; Banner</button>", 'html.parser'))
            header.insert(0, h_btn)

        grid_top = soup.find(class_='gb-grid-wrapper-5aaa8125')
        if grid_top:
            cards_btn = soup.new_tag('div', style='text-align:center; margin:8px 0;')
            cards_btn.append(BeautifulSoup("<button class='alria-edit-btn' onclick=\"openModal('modal-cards')\">✏️ Edit Top 8 Cards</button>", 'html.parser'))
            grid_top.insert_before(cards_btn)

        for col_cls, cat_key in COL_MAPPING.items():
            col_div = soup.find(class_=f'gb-grid-column-{col_cls}')
            if col_div:
                container = col_div.find(class_='gb-container')
                if container:
                    c_btn = soup.new_tag('div', style='text-align:center; margin:4px 0;')
                    c_btn.append(BeautifulSoup(f"<button class='alria-edit-btn' onclick=\"openModal('modal-grid-titles')\">✏️ Edit Titles</button>", 'html.parser'))
                    container.insert(0, c_btn)

        if c08:
            info_btn = soup.new_tag('div', style='text-align:center; margin:10px 0;')
            info_btn.append(BeautifulSoup("<button class='alria-edit-btn' onclick=\"openModal('modal-info-faq')\">✏️ Edit Guidelines &amp; FAQs</button>", 'html.parser'))
            c08.insert(0, info_btn)

        footer = soup.find('footer') or soup.find(class_='site-footer')
        if footer:
            foot_btn = soup.new_tag('div', style='text-align:center; margin:8px 0;')
            foot_btn.append(BeautifulSoup("<button class='alria-edit-btn' onclick=\"openModal('modal-footer-socials')\">✏️ Edit Footer &amp; Social Links</button>", 'html.parser'))
            footer.insert(0, foot_btn)

        info_secs_list = settings.get('info_sections', [])
        info_t1 = info_secs_list[0].get('title', '') if info_secs_list else ''
        info_c1 = info_secs_list[0].get('content', '') if info_secs_list else ''
        settings_json_escaped = json.dumps(settings)

        theme = settings.get('theme_colors', {})
        theme = settings.get('theme_colors', {})
        t_hdr_bg = theme.get('header_bg', '#ab183d')
        t_hdr_txt = theme.get('header_text', '#ffffff')
        t_nav_bg = theme.get('nav_bg', '#0c2340')
        t_nav_txt = theme.get('nav_text', '#ffffff')
        t_wa_bg = theme.get('whatsapp_btn_bg', '#00a82d')
        t_wa_txt = theme.get('whatsapp_btn_text', '#ffffff')
        t_foot_bg = theme.get('footer_bg', '#1d2327')
        t_foot_txt = theme.get('footer_text', '#ffffff')
        t_res_bg = theme.get('result_header_bg', '#ab183d')
        t_adm_bg = theme.get('admit_header_bg', '#ab183d')
        t_job_bg = theme.get('jobs_header_bg', '#ab183d')
        t_key_bg = theme.get('answer_header_bg', '#ab183d')
        t_syl_bg = theme.get('syllabus_header_bg', '#ab183d')
        t_adms_bg = theme.get('admission_header_bg', '#ab183d')

        s_site_name = settings.get('site_name', '')
        s_domain = settings.get('domain', '')
        s_tagline = settings.get('tagline', '')
        s_top_banner = settings.get('top_banner_text', '')
        s_footer_text = settings.get('footer_text', '')
        s_tg = settings.get('socials', {}).get('telegram', '')
        s_wa = settings.get('socials', {}).get('whatsapp', '')
        s_yt = settings.get('socials', {}).get('youtube', '')
        s_ig = settings.get('socials', {}).get('instagram', '')

        gt_res = grid_headers.get('result', {}).get('title', 'Result')
        gt_adm = grid_headers.get('admit-card', {}).get('title', 'Admit Card')
        gt_job = grid_headers.get('latest-jobs', {}).get('title', 'Latest Jobs')
        gt_key = grid_headers.get('answer-key', {}).get('title', 'Answer Key')
        gt_syl = grid_headers.get('syllabus', {}).get('title', 'Syllabus')
        gt_adms = grid_headers.get('admission', {}).get('title', 'Admission')

        alria_html = f'''
        <div id="alria-bar" style="position:fixed; top:0; left:0; right:0; z-index:999999; background:rgba(15,23,42,0.96); backdrop-filter:blur(10px); color:#fff; padding:10px 20px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 4px 20px rgba(0,0,0,0.4); border-bottom:2px solid #ef4444; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif; flex-wrap:wrap; gap:8px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="background:#ef4444; color:#fff; padding:3px 8px; border-radius:4px; font-weight:800; font-size:12px;">⚡ ALRIA LIVE EDITOR</span>
                <span style="font-size:13px; color:#cbd5e1;">Click any red ✏️ button on page or use top toolbar</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                <button onclick="openModal('modal-theme-colors')" style="background:#ec4899; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🎨 All Colors</button>
                <button onclick="openModal('modal-branding')" style="background:#2563eb; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🏷️ Branding</button>
                <button onclick="openModal('modal-cards')" style="background:#0891b2; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🃏 Top 8 Cards</button>
                <button onclick="openModal('modal-grid-titles')" style="background:#7c3aed; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">📊 6 Grid Titles</button>
                <button onclick="openModal('modal-info-faq')" style="background:#059669; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">❓ FAQs &amp; Info</button>
                <button onclick="openModal('modal-footer-socials')" style="background:#d97706; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🔗 Footer &amp; Socials</button>
                <a href="/admin/dashboard" style="background:#475569; color:#fff; text-decoration:none; padding:5px 12px; border-radius:4px; font-weight:700; font-size:12px;">Admin Panel</a>
                <a href="/" style="background:#ef4444; color:#fff; text-decoration:none; padding:5px 12px; border-radius:4px; font-weight:700; font-size:12px;">Exit Live</a>
            </div>
        </div>

        <style>
            .alria-modal-backdrop {{ display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.65); z-index: 1000000; align-items: center; justify-content: center; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            .alria-modal-card {{ background: #ffffff; border-radius: 8px; width: 94%; max-width: 680px; max-height: 88vh; overflow-y: auto; padding: 22px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); color: #1e293b; }}
            .alria-modal-card h3 {{ margin-top: 0; font-size: 18px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; color: #0f172a; display: flex; justify-content: space-between; align-items: center; }}
            .alria-input-group {{ margin-bottom: 12px; }}
            .alria-input-group label {{ display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #475569; }}
            .alria-modal-card input[type="text"], .alria-modal-card textarea {{ width: 100%; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 13px; box-sizing: border-box; }}
            .alria-color-row {{ display: flex; align-items: center; gap: 8px; margin-top: 4px; }}
            .alria-color-picker {{ width: 42px; height: 34px; padding: 2px; border: 1px solid #cbd5e1; border-radius: 4px; cursor: pointer; }}
            .alria-modal-actions {{ display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
            .alria-btn-cancel {{ padding: 8px 16px; border: 1px solid #cbd5e1; background: #fff; border-radius: 4px; cursor: pointer; font-weight: 600; }}
            .alria-btn-save {{ padding: 8px 18px; background: #ef4444; color: #fff; border: none; border-radius: 4px; font-weight: 700; cursor: pointer; }}
        </style>

        <!-- 1. Dedicated Master Color Customizer Modal -->
        <div id="modal-theme-colors" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🎨 Master Homepage Theme &amp; Section Colors</h3>
                
                <h4 style="margin:12px 0 8px; color:#2563eb; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">1. Header &amp; Top Navigation</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="alria-input-group">
                        <label>Header Background</label>
                        <div class="alria-color-row"><input type="color" id="tc-hdr-bg" value="{t_hdr_bg}" class="alria-color-picker"><input type="text" id="tc-hdr-bg-txt" value="{t_hdr_bg}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Header Text Color</label>
                        <div class="alria-color-row"><input type="color" id="tc-hdr-txt" value="{t_hdr_txt}" class="alria-color-picker"><input type="text" id="tc-hdr-txt-txt" value="{t_hdr_txt}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Navigation Bar Background</label>
                        <div class="alria-color-row"><input type="color" id="tc-nav-bg" value="{t_nav_bg}" class="alria-color-picker"><input type="text" id="tc-nav-bg-txt" value="{t_nav_bg}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Navigation Link Color</label>
                        <div class="alria-color-row"><input type="color" id="tc-nav-txt" value="{t_nav_txt}" class="alria-color-picker"><input type="text" id="tc-nav-txt-txt" value="{t_nav_txt}"></div>
                    </div>
                </div>

                <h4 style="margin:16px 0 8px; color:#059669; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">2. WhatsApp / Main Action Button</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="alria-input-group">
                        <label>Button Background</label>
                        <div class="alria-color-row"><input type="color" id="tc-wa-bg" value="{t_wa_bg}" class="alria-color-picker"><input type="text" id="tc-wa-bg-txt" value="{t_wa_bg}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Button Text Color</label>
                        <div class="alria-color-row"><input type="color" id="tc-wa-txt" value="{t_wa_txt}" class="alria-color-picker"><input type="text" id="tc-wa-txt-txt" value="{t_wa_txt}"></div>
                    </div>
                </div>

                <h4 style="margin:16px 0 8px; color:#7c3aed; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">3. 6 Section Column Header Colors</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;">
                    <div class="alria-input-group"><label>Results Header</label><input type="color" id="tc-col-result" value="{t_res_bg}" class="alria-color-picker" style="width:100%;"></div>
                    <div class="alria-input-group"><label>Admit Card Header</label><input type="color" id="tc-col-admit" value="{t_adm_bg}" class="alria-color-picker" style="width:100%;"></div>
                    <div class="alria-input-group"><label>Latest Jobs Header</label><input type="color" id="tc-col-jobs" value="{t_job_bg}" class="alria-color-picker" style="width:100%;"></div>
                    <div class="alria-input-group"><label>Answer Key Header</label><input type="color" id="tc-col-key" value="{t_key_bg}" class="alria-color-picker" style="width:100%;"></div>
                    <div class="alria-input-group"><label>Syllabus Header</label><input type="color" id="tc-col-syl" value="{t_syl_bg}" class="alria-color-picker" style="width:100%;"></div>
                    <div class="alria-input-group"><label>Admission Header</label><input type="color" id="tc-col-adm" value="{t_adms_bg}" class="alria-color-picker" style="width:100%;"></div>
                </div>

                <h4 style="margin:16px 0 8px; color:#d97706; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">4. Footer Colors</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="alria-input-group">
                        <label>Footer Background</label>
                        <div class="alria-color-row"><input type="color" id="tc-foot-bg" value="{t_foot_bg}" class="alria-color-picker"><input type="text" id="tc-foot-bg-txt" value="{t_foot_bg}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Footer Text Color</label>
                        <div class="alria-color-row"><input type="color" id="tc-foot-txt" value="{t_foot_txt}" class="alria-color-picker"><input type="text" id="tc-foot-txt-txt" value="{t_foot_txt}"></div>
                    </div>
                </div>

                <div class="alria-modal-actions">
                    <button class="alria-btn-cancel" onclick="closeModal('modal-theme-colors')">Cancel</button>
                    <button class="alria-btn-save" onclick="saveMasterThemeColors()">Save Theme Colors</button>
                </div>
            </div>
        </div>

        <!-- 2. Branding Modal with Color Controls -->
        <div id="modal-branding" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🏷️ Edit Portal Branding, Header URL &amp; Header Color</h3>
                <div class="alria-input-group"><label>Site Title (Shown at Top in Header, e.g. STUDY TOPPER)</label><input type="text" id="b-site-name" value="{s_site_name}"></div>
                <div class="alria-input-group"><label>Website URL (Shown below Site Title, e.g. SarkariResult.com.cm)</label><input type="text" id="b-domain" value="{s_domain}"></div>
                <div class="alria-input-group"><label>Top Red Headline Banner Text</label><textarea id="b-top-banner" rows="3">{s_top_banner}</textarea></div>
                
                <h4 style="margin-top:14px; font-size:13px;">Header Background &amp; Text Color</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                    <div class="alria-input-group">
                        <label>Header Color</label>
                        <div class="alria-color-row"><input type="color" id="b-hdr-bg" value="{t_hdr_bg}" class="alria-color-picker"><input type="text" id="b-hdr-bg-txt" value="{t_hdr_bg}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Header Text Color</label>
                        <div class="alria-color-row"><input type="color" id="b-hdr-txt" value="{t_hdr_txt}" class="alria-color-picker"><input type="text" id="b-hdr-txt-txt" value="{t_hdr_txt}"></div>
                    </div>
                </div>

                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-branding')">Cancel</button><button class="alria-btn-save" onclick="saveBranding()">Save Changes</button></div>
            </div>
        </div>

        <!-- 3. Cards Modal with Color Controls -->
        <div id="modal-cards" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🃏 Edit Top 8 Highlight Cards (Titles, Links &amp; Colors)</h3>
                <div id="cards-container"></div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-cards')">Cancel</button><button class="alria-btn-save" onclick="saveCards()">Save All 8 Cards</button></div>
            </div>
        </div>

        <!-- 4. 6 Grid Titles & Colors Modal -->
        <div id="modal-grid-titles" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>📊 Edit 6 Grid Column Titles &amp; Header Colors</h3>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="alria-input-group">
                        <label>Col 1 (Results)</label>
                        <input type="text" id="gt-result" value="{gt_res}">
                        <div class="alria-color-row" style="margin-top:4px;"><input type="color" id="gc-result" value="{t_res_bg}" class="alria-color-picker"><span style="font-size:11px; color:#64748b;">Header Color</span></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Col 2 (Admit Card)</label>
                        <input type="text" id="gt-admit" value="{gt_adm}">
                        <div class="alria-color-row" style="margin-top:4px;"><input type="color" id="gc-admit" value="{t_adm_bg}" class="alria-color-picker"><span style="font-size:11px; color:#64748b;">Header Color</span></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Col 3 (Latest Jobs)</label>
                        <input type="text" id="gt-jobs" value="{gt_job}">
                        <div class="alria-color-row" style="margin-top:4px;"><input type="color" id="gc-jobs" value="{t_job_bg}" class="alria-color-picker"><span style="font-size:11px; color:#64748b;">Header Color</span></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Col 4 (Answer Key)</label>
                        <input type="text" id="gt-key" value="{gt_key}">
                        <div class="alria-color-row" style="margin-top:4px;"><input type="color" id="gc-key" value="{t_key_bg}" class="alria-color-picker"><span style="font-size:11px; color:#64748b;">Header Color</span></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Col 5 (Syllabus)</label>
                        <input type="text" id="gt-syl" value="{gt_syl}">
                        <div class="alria-color-row" style="margin-top:4px;"><input type="color" id="gc-syl" value="{t_syl_bg}" class="alria-color-picker"><span style="font-size:11px; color:#64748b;">Header Color</span></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Col 6 (Admission)</label>
                        <input type="text" id="gt-adm" value="{gt_adms}">
                        <div class="alria-color-row" style="margin-top:4px;"><input type="color" id="gc-adm" value="{t_adms_bg}" class="alria-color-picker"><span style="font-size:11px; color:#64748b;">Header Color</span></div>
                    </div>
                </div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-grid-titles')">Cancel</button><button class="alria-btn-save" onclick="saveGridTitles()">Save Titles &amp; Colors</button></div>
            </div>
        </div>

        <!-- 5. Guidelines & FAQ Modal -->
        <div id="modal-info-faq" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>❓ Edit Guidelines &amp; FAQs</h3>
                <h4>Guidelines Block 1</h4>
                <div class="alria-input-group">
                    <label>Title</label><input type="text" id="info-t1" value="{info_t1}">
                    <label style="margin-top:6px;">Content</label><textarea id="info-c1" rows="3">{info_c1}</textarea>
                </div>
                <h4 style="margin-top:16px;">FAQ Q&amp;A Items</h4>
                <div id="faq-list-container"></div>
                <button onclick="addNewFaqItem()" style="background:#0891b2; color:#fff; border:none; padding:4px 10px; border-radius:4px; font-size:12px; cursor:pointer;">+ Add New FAQ Question</button>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-info-faq')">Cancel</button><button class="alria-btn-save" onclick="saveInfoFaq()">Save Info &amp; FAQs</button></div>
            </div>
        </div>

        <!-- 6. Footer & Socials Modal with Color Controls -->
        <div id="modal-footer-socials" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🔗 Edit Footer, Socials &amp; Footer Color</h3>
                <div class="alria-input-group"><label>Footer Copyright Text</label><textarea id="f-text" rows="2">{s_footer_text}</textarea></div>
                
                <h4 style="margin-top:10px;">Footer Colors</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:12px;">
                    <div class="alria-input-group">
                        <label>Footer Background</label>
                        <div class="alria-color-row"><input type="color" id="f-bg" value="{t_foot_bg}" class="alria-color-picker"><input type="text" id="f-bg-txt" value="{t_foot_bg}"></div>
                    </div>
                    <div class="alria-input-group">
                        <label>Footer Text Color</label>
                        <div class="alria-color-row"><input type="color" id="f-txt" value="{t_foot_txt}" class="alria-color-picker"><input type="text" id="f-txt-txt" value="{t_foot_txt}"></div>
                    </div>
                </div>

                <h4>Official Social Channels</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                    <div class="alria-input-group"><label>Telegram Link</label><input type="text" id="soc-tg" value="{s_tg}"></div>
                    <div class="alria-input-group"><label>WhatsApp Link</label><input type="text" id="soc-wa" value="{s_wa}"></div>
                    <div class="alria-input-group"><label>YouTube Link</label><input type="text" id="soc-yt" value="{s_yt}"></div>
                    <div class="alria-input-group"><label>Instagram Link</label><input type="text" id="soc-ig" value="{s_ig}"></div>
                </div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-footer-socials')">Cancel</button><button class="alria-btn-save" onclick="saveFooterSocials()">Save Footer &amp; Socials</button></div>
            </div>
        </div>

        <script>
            let siteSettings = {settings_json_escaped};
            let themeColors = siteSettings.theme_colors || {{}};

            function openModal(id) {{ document.getElementById(id).style.display = 'flex'; }}
            function closeModal(id) {{ document.getElementById(id).style.display = 'none'; }}

            function linkColorInputs(colorId, textId) {{
                const cEl = document.getElementById(colorId);
                const tEl = document.getElementById(textId);
                if(cEl && tEl) {{
                    cEl.addEventListener('input', () => {{ tEl.value = cEl.value; }});
                    tEl.addEventListener('input', () => {{ if(tEl.value.match(/^#[0-9A-Fa-f]{{6}}$/)) cEl.value = tEl.value; }});
                }}
            }}
            linkColorInputs('tc-hdr-bg', 'tc-hdr-bg-txt');
            linkColorInputs('tc-hdr-txt', 'tc-hdr-txt-txt');
            linkColorInputs('tc-nav-bg', 'tc-nav-bg-txt');
            linkColorInputs('tc-nav-txt', 'tc-nav-txt-txt');
            linkColorInputs('tc-wa-bg', 'tc-wa-bg-txt');
            linkColorInputs('tc-wa-txt', 'tc-wa-txt-txt');
            linkColorInputs('tc-foot-bg', 'tc-foot-bg-txt');
            linkColorInputs('tc-foot-txt', 'tc-foot-txt-txt');
            linkColorInputs('b-hdr-bg', 'b-hdr-bg-txt');
            linkColorInputs('b-hdr-txt', 'b-hdr-txt-txt');
            linkColorInputs('f-bg', 'f-bg-txt');
            linkColorInputs('f-txt', 'f-txt-txt');

            function renderCardsInputs() {{
                const cont = document.getElementById('cards-container'); if(!cont) return; cont.innerHTML = '';
                const cards = siteSettings.highlight_cards || [];
                const defaultCardBgs = ['#ff2a00', '#ff6600', '#db2777', '#0052cc', '#708238', '#0080ff', '#800000', '#00802b'];
                for(let i=0; i<8; i++) {{
                    const c = cards[i] || {{title: '', url: '#'}};
                    const curBg = themeColors['card_' + (i+1) + '_bg'] || defaultCardBgs[i] || '#ff2a00';
                    cont.innerHTML += `
                    <div style="display:grid; grid-template-columns:1fr 1fr 90px; gap:8px; margin-bottom:8px; background:#f8fafc; padding:6px 10px; border-radius:4px; align-items:center;">
                        <div><label style="font-size:11px; font-weight:700;">Card ${{i+1}} Title</label><input type="text" id="card-title-${{i}}" value="${{c.title || ''}}"></div>
                        <div><label style="font-size:11px; font-weight:700;">Card ${{i+1}} Link</label><input type="text" id="card-url-${{i}}" value="${{c.url || '#'}}"></div>
                        <div><label style="font-size:11px; font-weight:700;">Color</label><input type="color" id="card-color-${{i}}" value="${{curBg}}" class="alria-color-picker" style="width:100%;"></div>
                    </div>`;
                }}
            }}
            renderCardsInputs();

            function renderFaqInputs() {{
                const cont = document.getElementById('faq-list-container'); if(!cont) return; cont.innerHTML = '';
                const faqs = siteSettings.faq_items || [];
                faqs.forEach((faq, idx) => {{
                    cont.innerHTML += `<div style="border:1px solid #e2e8f0; padding:8px 10px; border-radius:4px; margin-bottom:10px; background:#f8fafc;"><label style="font-size:12px; font-weight:700;">Question ${{idx+1}}</label><input type="text" id="faq-q-${{idx}}" value="${{faq.q || ''}}" style="margin-bottom:6px;"><label style="font-size:12px; font-weight:700;">Answer</label><textarea id="faq-a-${{idx}}" rows="2">${{faq.a || ''}}</textarea></div>`;
                }});
            }}
            renderFaqInputs();

            function addNewFaqItem() {{
                if(!siteSettings.faq_items) siteSettings.faq_items = [];
                siteSettings.faq_items.push({{q: "New Question Title", a: "Answer text goes here..."}});
                renderFaqInputs();
            }}

            async function saveSettingsPayload(payload) {{
                const res = await fetch('/api/admin/save-settings', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
                if(res.ok) {{ alert('Section & Colors updated successfully!'); location.reload(); }} else {{ alert('Error updating settings'); }}
            }}

            function saveMasterThemeColors() {{
                const colors = {{
                    header_bg: document.getElementById('tc-hdr-bg').value,
                    header_text: document.getElementById('tc-hdr-txt').value,
                    nav_bg: document.getElementById('tc-nav-bg').value,
                    nav_text: document.getElementById('tc-nav-txt').value,
                    whatsapp_btn_bg: document.getElementById('tc-wa-bg').value,
                    whatsapp_btn_text: document.getElementById('tc-wa-txt').value,
                    result_header_bg: document.getElementById('tc-col-result').value,
                    admit_header_bg: document.getElementById('tc-col-admit').value,
                    jobs_header_bg: document.getElementById('tc-col-jobs').value,
                    answer_header_bg: document.getElementById('tc-col-key').value,
                    syllabus_header_bg: document.getElementById('tc-col-syl').value,
                    admission_header_bg: document.getElementById('tc-col-adm').value,
                    footer_bg: document.getElementById('tc-foot-bg').value,
                    footer_text: document.getElementById('tc-foot-txt').value
                }};
                saveSettingsPayload({{ theme_colors: colors }});
            }}

            function saveBranding() {{
                const siteNameEl = document.getElementById('b-site-name');
                const domainEl = document.getElementById('b-domain');
                const bannerEl = document.getElementById('b-top-banner');
                const hdrBgEl = document.getElementById('b-hdr-bg');
                const hdrTxtEl = document.getElementById('b-hdr-txt');

                const payload = {{
                    site_name: siteNameEl ? siteNameEl.value : '',
                    domain: domainEl ? domainEl.value : '',
                    top_banner_text: bannerEl ? bannerEl.value : ''
                }};

                if (hdrBgEl || hdrTxtEl) {{
                    payload.theme_colors = {{
                        header_bg: hdrBgEl ? hdrBgEl.value : '#cd0808',
                        header_text: hdrTxtEl ? hdrTxtEl.value : '#ffffff'
                    }};
                }}

                saveSettingsPayload(payload);
            }}

            function saveCards() {{
                const cards = [];
                const cardColors = {{}};
                for(let i=0; i<8; i++) {{
                    cards.push({{ title: document.getElementById('card-title-' + i).value, url: document.getElementById('card-url-' + i).value }});
                    cardColors['card_' + (i+1) + '_bg'] = document.getElementById('card-color-' + i).value;
                }}
                saveSettingsPayload({{ highlight_cards: cards, theme_colors: cardColors }});
            }}

            function saveGridTitles() {{
                saveSettingsPayload({{
                    grid_headers: {{
                        'result': {{ title: document.getElementById('gt-result').value, more_url: '/result/' }},
                        'admit-card': {{ title: document.getElementById('gt-admit').value, more_url: '/admit-card/' }},
                        'latest-jobs': {{ title: document.getElementById('gt-jobs').value, more_url: '/latest-jobs/' }},
                        'answer-key': {{ title: document.getElementById('gt-key').value, more_url: '/answer-key/' }},
                        'syllabus': {{ title: document.getElementById('gt-syl').value, more_url: '/syllabus/' }},
                        'admission': {{ title: document.getElementById('gt-adm').value, more_url: '/admission/' }}
                    }},
                    theme_colors: {{
                        result_header_bg: document.getElementById('gc-result').value,
                        admit_header_bg: document.getElementById('gc-admit').value,
                        jobs_header_bg: document.getElementById('gc-jobs').value,
                        answer_header_bg: document.getElementById('gc-key').value,
                        syllabus_header_bg: document.getElementById('gc-syl').value,
                        admission_header_bg: document.getElementById('gc-adm').value
                    }}
                }});
            }}

            function saveInfoFaq() {{
                const info_secs = [{{ title: document.getElementById('info-t1').value, content: document.getElementById('info-c1').value }}];
                const faqs = []; const len = siteSettings.faq_items ? siteSettings.faq_items.length : 0;
                for(let i=0; i<len; i++) {{ const qEl = document.getElementById('faq-q-' + i); const aEl = document.getElementById('faq-a-' + i); if(qEl && aEl) faqs.push({{ q: qEl.value, a: aEl.value }}); }}
                saveSettingsPayload({{ info_sections: info_secs, faq_items: faqs }});
            }}

            function saveFooterSocials() {{
                saveSettingsPayload({{
                    footer_text: document.getElementById('f-text').value,
                    theme_colors: {{
                        footer_bg: document.getElementById('f-bg').value,
                        footer_text: document.getElementById('f-txt').value
                    }},
                    socials: {{
                        telegram: document.getElementById('soc-tg').value,
                        whatsapp: document.getElementById('soc-wa').value,
                        youtube: document.getElementById('soc-yt').value,
                        instagram: document.getElementById('soc-ig').value
                    }}
                }});
            }}
        </script>
        '''
        if soup.body:
            soup.body['style'] = 'padding-top: 55px !important;'
            soup.body.insert(0, BeautifulSoup(alria_html, 'html.parser'))

    # 13. Domain Rewrite for All Links
    for a in soup.find_all('a'):
        href = a.get('href', '')
        if 'studytopper.in' in href:
            path = href.replace('https://studytopper.in', '').replace('http://studytopper.in', '')
            a['href'] = path if path else '/'

        # Rewrite search forms to internal /search
    for s_form in soup.find_all('form', class_=re.compile(r'search-modal-form|search-form')):
        s_form['action'] = '/search'
    rendered = str(soup)
    # Global domain & branding sanitize
    rendered = re.sub(r'https?://(?:www\.)?sarkariresult\.com\.cm/?', '/', rendered, flags=re.IGNORECASE)
    rendered = re.sub(r'sarkariresult\.com\.cm', settings.get('domain', 'studytopper.in'), rendered, flags=re.IGNORECASE)
    rendered = re.sub(r'SarkariResult\.Com\.Cm', settings.get('domain', 'studytopper.in'), rendered)
    return rendered

# Static Asset Handler
@app.route('/wp-content/<path:filepath>')
def serve_wp_content(filepath):
    full_dir = os.path.dirname(os.path.join(WP_CONTENT_DIR, filepath))
    filename = os.path.basename(filepath)
    if os.path.exists(os.path.join(full_dir, filename)):
        return send_from_directory(full_dir, filename)
    abort(404)

# ==================== SEO & CRAWLER PROTECTION ROUTES ====================

@app.route('/ads.txt')
def ads_txt():
    settings = load_settings()
    content = settings.get('ads_txt', 'google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0')
    return Response(content, mimetype='text/plain')

@app.route('/robots.txt')
def robots_txt():
    settings = load_settings()
    host = request.host
    scheme = 'https' if request.is_secure else 'http'
    default_robots = f"""User-agent: *
Disallow: /admin/
Disallow: /admin
Disallow: /alria
Disallow: /alria/
Disallow: /api/
Allow: /

Sitemap: {scheme}://{host}/sitemap.xml
"""
    content = settings.get('robots_txt') or default_robots
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def dynamic_sitemap():
    host = request.host
    scheme = 'https' if request.is_secure else 'http'
    today = datetime.now().strftime('%Y-%m-%d')
    settings = load_settings()

    pages = []
    # 1. Homepage
    pages.append({'loc': f"{scheme}://{host}/", 'priority': '1.0', 'changefreq': 'always'})

    # 2. Categories
    for cat in settings.get('categories', []):
        slug = cat.get('slug')
        if slug:
            pages.append({'loc': f"{scheme}://{host}/{slug}/", 'priority': '0.9', 'changefreq': 'hourly'})

    # 3. All Local Posts
    if os.path.exists(PAGES_DIR):
        for fname in os.listdir(PAGES_DIR):
            if fname.endswith('.html') and fname not in ['index.html'] and fname[:-5] not in PRIMARY_CATEGORIES:
                slug = fname[:-5]
                pages.append({'loc': f"{scheme}://{host}/{slug}/", 'priority': '0.8', 'changefreq': 'daily'})

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for p in pages:
        xml_lines.append('  <url>')
        xml_lines.append(f"    <loc>{p['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{today}</lastmod>")
        xml_lines.append(f"    <changefreq>{p['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{p['priority']}</priority>")
        xml_lines.append('  </url>')
    xml_lines.append('</urlset>')

    return Response('\n'.join(xml_lines), mimetype='application/xml')

# ==================== CORE HOMEPAGE & /ALRIA ROUTE ====================

@app.route('/')
@app.route('/alria')
@app.route('/alria/')
def home():
    search_q = request.args.get('s') or request.args.get('q')
    if search_q:
        return redirect(f'/search?q={search_q}')

    is_alria = (request.path in ['/alria', '/alria/']) or (request.args.get('alria') == '1')
    index_file = os.path.join(PAGES_DIR, 'index.html')
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        sanitized = sanitize_html(content, request.host, is_alria_mode=is_alria)
        return Response(sanitized, mimetype='text/html')
    abort(404)

@app.route('/search')
@app.route('/search/')
def search_page():
    query = (request.args.get('q') or request.args.get('s') or '').strip()
    settings = load_settings()
    all_posts = load_all_active_posts()
    
    results = []
    if query:
        q_lower = query.lower()
        for p in all_posts:
            title = (p.get('title') or '').lower()
            tags = (p.get('tags') or '').lower()
            desc = (p.get('short_desc') or '').lower()
            cat = (p.get('category') or '').lower()
            if q_lower in title or q_lower in tags or q_lower in desc or q_lower in cat:
                results.append(p)
                
    return Response(render_search_page_html(query, results, settings), mimetype='text/html')

# ==================== CLEAN TOP-LEVEL SLUG ROUTING ====================

@app.route('/<path:slug>/')
@app.route('/<path:slug>')
def dynamic_page_router(slug):
    clean_slug = slug.strip('/')
    if clean_slug in ['favicon.ico', 'robots.txt', 'sitemap.xml', 'ads.txt', 'alria', 'admin', 'search']:
        abort(404)

    settings = load_settings()
    all_posts = load_all_active_posts()

    # 1. Category Page Routing (e.g. /result/, /latest-jobs/, /admit-card/)
    norm_slug = clean_slug.lower()
    if norm_slug in CATEGORY_SLUG_MAP:
        cat_title = CATEGORY_SLUG_MAP[norm_slug]
        cat_key = 'latest-jobs' if norm_slug in ['jobs', 'latestjob'] else ('result' if norm_slug == 'results' else ('admit-card' if norm_slug == 'admit-cards' else ('answer-key' if norm_slug == 'answerkey' else ('admission' if norm_slug == 'admissions' else norm_slug))))
        cat_posts = [p for p in all_posts if p.get('category') == cat_key and not p.get('is_temporary')]
        cat_html = render_category_page_html(clean_slug, cat_title, cat_posts, settings)
        return Response(sanitize_html(cat_html, request.host), mimetype='text/html')

    # 2. Exact Scraped / Static Post Page in PAGES_DIR (100% Exact HTML Design)
    page_file = os.path.join(PAGES_DIR, f"{clean_slug}.html")
    if os.path.exists(page_file) and clean_slug != 'index':
        with open(page_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(sanitize_html(content, request.host), mimetype='text/html')

    # 3. Dynamic User-Created Single Post Routing
    for p in all_posts:
        if p.get('slug') == clean_slug or p.get('id') == clean_slug:
            post_html = render_single_post_html(p, settings)
            return Response(sanitize_html(post_html, request.host), mimetype='text/html')

    # Zero external scraper fallback! Only show clean 404
    abort(404)

# Candidate Tools
@app.route('/tools/<tool_name>')
@app.route('/tools/<tool_name>/')
def candidate_tools(tool_name):
    clean_tool = tool_name.strip('/').replace('-', '_')
    tpl_path = os.path.join(BASE_DIR, 'templates', 'tools', f'{clean_tool}.html')
    if os.path.exists(tpl_path):
        return render_template(f'tools/{clean_tool}.html', settings=load_settings())
    abort(404)

# ==================== ADMIN PANEL ROUTES ====================

@app.route('/admin')
@app.route('/admin/')
@app.route('/admin/dashboard')
def admin_dashboard():
    settings = load_settings()
    post_count = 0
    if os.path.exists(PAGES_DIR):
        post_count = len([f for f in os.listdir(PAGES_DIR) if f.endswith('.html')])
    
    return render_template(
        'admin/dashboard.html',
        settings=settings,
        total_posts=post_count,
        active_posts=post_count,
        soon_posts=3,
        expired_posts=0,
        recent_posts=[]
    )

@app.route('/admin/posts')
def admin_posts():
    settings = load_settings()
    posts = load_all_active_posts()
    return render_template('admin/posts.html', settings=settings, posts=posts)

@app.route('/admin/posts/new')
def admin_post_new():
    settings = load_settings()
    return render_template('admin/post_form.html', settings=settings, post=None)

@app.route('/admin/posts/edit/<post_id>')
def admin_post_edit(post_id):
    settings = load_settings()
    all_posts = load_all_active_posts()
    target_post = None
    for p in all_posts:
        if p.get('id') == post_id or p.get('slug') == post_id:
            target_post = p
            break
    
    if not target_post:
        target_post = {
            'id': post_id,
            'title': post_id.replace('-', ' ').title(),
            'slug': post_id,
            'category': 'latest-jobs',
            'application_start_date': '2026-08-01',
            'application_last_date': '2026-09-30',
            'is_date_extended': False,
            'is_pinned': False,
            'custom_badge': '',
            'short_desc': '',
            'tags': '',
            'html_content': ''
        }
        page_file = os.path.join(PAGES_DIR, f"{post_id}.html")
        if os.path.exists(page_file):
            try:
                with open(page_file, 'r', encoding='utf-8') as f:
                    target_post['html_content'] = f.read()
            except Exception:
                pass
    return render_template('admin/post_form.html', settings=settings, post=target_post)

@app.route('/admin/categories')
def admin_categories():
    settings = load_settings()
    return render_template('admin/categories.html', settings=settings)

@app.route('/admin/settings')
def admin_settings():
    settings = load_settings()
    return render_template('admin/settings.html', settings=settings)

# ==================== API ADMIN ENDPOINTS ====================

@app.route('/api/admin/save-settings', methods=['GET', 'POST'])
@app.route('/api/admin/save-settings/', methods=['GET', 'POST'])
def api_save_settings():
    if request.method == 'GET':
        return redirect('/admin/settings')

    try:
        settings = load_settings()
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form.to_dict()

        for k, v in data.items():
            if k.startswith('social_'):
                soc_k = k.replace('social_', '')
                if 'socials' not in settings: settings['socials'] = {}
                settings['socials'][soc_k] = v
            elif k in ['telegram', 'whatsapp', 'youtube', 'instagram', 'facebook', 'twitter']:
                if 'socials' not in settings: settings['socials'] = {}
                settings['socials'][k] = v
            elif k in ['google_analytics_id', 'google_site_verification', 'meta_description', 'meta_keywords', 'custom_head_code', 'custom_footer_code']:
                if 'seo' not in settings: settings['seo'] = {}
                settings['seo'][k] = v
            elif k == 'theme_colors' and isinstance(v, dict):
                if 'theme_colors' not in settings: settings['theme_colors'] = {}
                settings['theme_colors'].update(v)
            elif k.startswith('theme_'):
                col_k = k.replace('theme_', '')
                if 'theme_colors' not in settings: settings['theme_colors'] = {}
                settings['theme_colors'][col_k] = v
            elif k in ['adsense_id', 'adsense_client']:
                if 'adsense' not in settings: settings['adsense'] = {}
                settings['adsense']['client_id'] = v
                settings['adsense']['enabled'] = bool(v)
            elif k in ['adsense_enabled']:
                if 'adsense' not in settings: settings['adsense'] = {}
                settings['adsense']['enabled'] = bool(v)
            elif k in ['supabase_url', 'supabase_key']:
                if 'supabase' not in settings: settings['supabase'] = {}
                sub_k = 'url' if k == 'supabase_url' else 'key'
                settings['supabase'][sub_k] = v
            else:
                settings[k] = v

        save_settings_data(settings)
        if request.is_json:
            return jsonify({'status': 'success', 'settings': settings})
        return redirect('/admin/settings')
    except Exception as e:
        import traceback
        traceback.print_exc()
        if request.is_json:
            return jsonify({'status': 'error', 'message': str(e)}), 500
        return f"<h3>Settings Saved</h3><p>{str(e)}</p><a href='/admin/settings'>Go Back</a>"

@app.route('/api/admin/save-post', methods=['POST'])
def api_save_post():
    data = request.get_json(silent=True) or request.form
    title = data.get('title', '').strip()
    slug = data.get('slug') or title.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')[:80]
    slug = re.sub(r'[^a-zA-Z0-9_-]', '', slug)
    html_content = data.get('html_content', '')
    category = data.get('category', 'latest-jobs')
    app_start = data.get('application_start_date', '')
    app_last = data.get('application_last_date', '')
    short_desc = data.get('short_desc', '')
    tags = data.get('tags', '')
    is_pinned = bool(data.get('is_pinned'))
    is_date_extended = bool(data.get('is_date_extended'))
    custom_badge = data.get('custom_badge', '')

    post_item = {
        'id': data.get('id') or f"post_{uuid.uuid4().hex[:8]}",
        'slug': slug,
        'title': title,
        'category': category,
        'short_desc': short_desc,
        'tags': tags,
        'html_content': html_content,
        'application_start_date': app_start,
        'application_last_date': app_last,
        'is_pinned': is_pinned,
        'is_date_extended': is_date_extended,
        'is_temporary': False,
        'custom_badge': custom_badge,
        'created_at': datetime.now().isoformat()
    }

    save_single_post(post_item)
    return redirect('/admin/posts')

@app.route('/api/admin/posts/bulk-delete', methods=['POST'])
def api_bulk_delete_posts():
    try:
        data = request.get_json(silent=True) or {}
        post_ids = data.get('post_ids', [])
        deleted_count = 0
        for pid in post_ids:
            if pid:
                delete_single_post(pid)
                deleted_count += 1
        return jsonify({'status': 'success', 'deleted_count': deleted_count})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/admin/posts/delete/<post_id>', methods=['POST'])
def api_delete_post(post_id):
    delete_single_post(post_id)
    return jsonify({'status': 'success', 'deleted': post_id})

# ==================== SUPABASE CLOUD MANAGEMENT ENDPOINTS ====================

@app.route('/api/admin/supabase/test')
def api_supabase_test():
    return jsonify(supa.test_supabase_connection())

@app.route('/api/admin/supabase/sync', methods=['POST'])
def api_supabase_sync():
    settings = load_settings()
    if not supa.is_supabase_configured():
        return jsonify({'status': 'error', 'message': 'Supabase is not configured yet. Please enter Project URL and Key.'})
    
    # 1. Sync settings
    supa.save_settings_to_supabase(settings)
    
    # 2. Sync all local post pages
    post_count = 0
    if os.path.exists(PAGES_DIR):
        for f in os.listdir(PAGES_DIR):
            if f.endswith('.html') and f not in ['index.html']:
                slug = f[:-5]
                with open(os.path.join(PAGES_DIR, f), 'r', encoding='utf-8') as hf:
                    html_c = hf.read()
                
                post_data = {
                    'id': f"post_{slug}",
                    'slug': slug,
                    'title': slug.replace('-', ' ').title(),
                    'category': 'latest-jobs',
                    'html_content': html_c,
                    'is_temporary': True
                }
                supa.save_post_to_supabase(post_data)
                post_count += 1
                
    return jsonify({'status': 'success', 'message': f'Synced settings and {post_count} posts to Supabase successfully!'})

@app.route('/api/admin/supabase/wipe-temporary', methods=['POST'])
def api_supabase_wipe_temporary():
    if supa.is_supabase_configured():
        supa.wipe_temporary_posts_from_supabase()
    
    deleted_count = 0
    if os.path.exists(PAGES_DIR):
        for f in os.listdir(PAGES_DIR):
            if f.endswith('.html') and f not in ['index.html']:
                os.remove(os.path.join(PAGES_DIR, f))
                deleted_count += 1
                
    return jsonify({'status': 'success', 'message': f'Wiped {deleted_count} temporary sample posts cleanly. Ready for real posts!'})

@app.route('/api/admin/categories/save', methods=['POST'])
def api_save_category():
    settings = load_settings()
    data = request.get_json(silent=True) or request.form
    name = data.get('name', '').strip()
    slug = data.get('slug', '').strip().lower().replace(' ', '-')
    desc = data.get('desc', '').strip()

    if not name or not slug:
        return redirect('/admin/categories')

    cats = settings.get('categories', [])
    existing = next((c for c in cats if c.get('slug') == slug), None)
    if existing:
        existing['name'] = name
        existing['desc'] = desc
    else:
        cats.append({'id': f"cat_{uuid.uuid4().hex[:6]}", 'name': name, 'slug': slug, 'desc': desc})

    settings['categories'] = cats
    save_settings_data(settings)
    return redirect('/admin/categories')

@app.route('/api/admin/categories/delete/<cat_id>', methods=['POST'])
def api_delete_category(cat_id):
    settings = load_settings()
    cats = settings.get('categories', [])
    filtered = [c for c in cats if c.get('id') != cat_id and c.get('slug') != cat_id]
    settings['categories'] = filtered
    save_settings_data(settings)
    return jsonify({'status': 'success', 'deleted': cat_id})

if __name__ == '__main__':
    print("===================================================================")
    print("Starting STUDY TOPPER PRO PORTAL (PORT 9093)")
    print(" - Official Homepage:     http://127.0.0.1:9093")
    print(" - /alria Visual Editor:  http://127.0.0.1:9093/alria")
    print(" - ads.txt:               http://127.0.0.1:9093/ads.txt")
    print(" - robots.txt:            http://127.0.0.1:9093/robots.txt")
    print(" - sitemap.xml:           http://127.0.0.1:9093/sitemap.xml")
    print(" - Admin Dashboard:       http://127.0.0.1:9093/admin/dashboard")
    print(" - Category Manager:      http://127.0.0.1:9093/admin/categories")
    print(" - SEO & Settings:        http://127.0.0.1:9093/admin/settings")
    print("===================================================================")
    app.run(host='0.0.0.0', port=9093, debug=False)
