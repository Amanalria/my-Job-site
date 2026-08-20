import supabase_client as supa
import os
import re
import json
import uuid
import vacancy_lifecycle_engine as lifecycle
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from flask import Flask, send_from_directory, request, Response, abort, jsonify, render_template, redirect

app = Flask(__name__)
app.secret_key = 'sarkari_official_secret_2026'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, 'pages')
WP_CONTENT_DIR = os.path.join(BASE_DIR, 'wp-content')
DATA_DIR = os.path.join(BASE_DIR, 'data')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')

TARGET_DOMAIN = "studytopper.in"

PRIMARY_CATEGORIES = [
    'latest-jobs', 'admit-card', 'result', 'admission', 'syllabus', 'answer-key',
    'certificate-verification', 'important', 'contact', 'disclaimer', 'privacy-policy'
]

MAIN_CSS_CACHE = ""
try:
    _main_css_file = os.path.join(WP_CONTENT_DIR, 'themes', 'generatepress', 'assets', 'css', 'main.min.css')
    if os.path.exists(_main_css_file):
        with open(_main_css_file, 'r', encoding='utf-8') as f:
            MAIN_CSS_CACHE = f.read()
except Exception as e:
    print("Notice: Could not load main.min.css cache:", e)

STYLE_32_CSS_CACHE = ""
try:
    _s32_file = os.path.join(WP_CONTENT_DIR, 'uploads', 'generateblocks', 'style-32.css')
    if os.path.exists(_s32_file):
        with open(_s32_file, 'r', encoding='utf-8') as f:
            STYLE_32_CSS_CACHE = f.read()
except Exception as e:
    print("Notice: Could not load style-32.css cache:", e)

# ==================== UNIFIED POST MANAGEMENT SYSTEM ====================

def get_deleted_post_slugs():
    settings = load_settings()
    return set(settings.get('deleted_posts', []))

def load_custom_posts():
    custom_posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
    return lifecycle.safe_read_json(custom_posts_file, [])

def save_custom_posts(posts_list):
    custom_posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
    lifecycle.safe_write_json(custom_posts_file, posts_list)

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
        from thumbnail_generator import generate_post_thumbnail
        thumb_filename = f"{slug}.webp"
        thumb_abs_path = os.path.join('/root/sarkari-result-portal/static/thumbnails', thumb_filename)
        posts_badge = post_item.get('total_posts') or (post_item.get('custom_badge') if any(c.isdigit() for c in str(post_item.get('custom_badge', ''))) else '')
        last_dt = post_item.get('application_last_date', '')
        generate_post_thumbnail(
            title=post_item.get('title', slug),
            total_posts=str(posts_badge) if posts_badge else '',
            last_date=str(last_dt),
            output_path=thumb_abs_path
        )
    except Exception as e:
        print("Thumbnail auto-generation error in save_single_post:", e)

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
    footer_cfg = settings.get('footer', {})
    wa_url = socials.get('whatsapp') or 'https://whatsapp.com/'
    tg_url = socials.get('telegram') or 'https://t.me/'
    ig_url = socials.get('instagram') or 'https://instagram.com/'
    yt_url = socials.get('youtube') or 'https://youtube.com/'
    fb_url = socials.get('facebook') or 'https://facebook.com/'
    tw_url = socials.get('twitter') or 'https://x.com/'

    for s in footer_cfg.get('social_links', []):
        s_name = s.get('name', '').lower()
        s_url = s.get('url', '')
        if s_url:
            if 'whatsapp' in s_name: wa_url = s_url
            elif 'telegram' in s_name: tg_url = s_url
            elif 'instagram' in s_name: ig_url = s_url
            elif 'youtube' in s_name: yt_url = s_url
            elif 'facebook' in s_name: fb_url = s_url
            elif 'x' in s_name or 'twitter' in s_name: tw_url = s_url

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
        cls_list = a_tag.get('class', [])
        cls_str = ' '.join(cls_list) if isinstance(cls_list, list) else str(cls_list or '')
        
        if 'whatsapp' in href.lower() or 'whatsapp' in text or 'whatsapp' in cls_str.lower():
            a_tag['href'] = wa_url
        elif 't.me' in href.lower() or 'telegram' in text or 'telegram' in cls_str.lower():
            a_tag['href'] = tg_url
        elif 'instagram' in href.lower() or 'instagram' in text or 'instagram' in cls_str.lower():
            a_tag['href'] = ig_url
        elif 'youtube' in href.lower() or 'youtube' in text or 'youtube' in cls_str.lower():
            a_tag['href'] = yt_url
        elif 'facebook' in href.lower() or 'facebook' in text or 'facebook' in cls_str.lower():
            a_tag['href'] = fb_url
        elif 'twitter' in href.lower() or text in ['@x', 'twitter'] or 'twitter' in cls_str.lower():
            a_tag['href'] = tw_url
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

def get_nav_search_styles_html():
    return """<style id="st-nav-search-styles">
.main-navigation {
    background-color: #0b213f !important;
    position: relative !important;
    z-index: 99999 !important;
    clear: both !important;
    width: 100% !important;
}
.main-navigation .inside-navigation {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 0 12px !important;
    min-height: 46px !important;
    position: relative !important;
    box-sizing: border-box !important;
}
.main-navigation .menu-toggle {
    display: none;
    background: transparent !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    padding: 10px 4px !important;
    align-items: center !important;
    gap: 8px !important;
    line-height: 1 !important;
    text-transform: capitalize !important;
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation !important;
    pointer-events: auto !important;
}
.main-navigation .menu-toggle:focus {
    outline: none;
}
.main-navigation .menu-toggle .gp-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.main-navigation .menu-toggle .gp-icon svg {
    width: 18px;
    height: 18px;
    fill: #ffffff;
}
.main-navigation .menu-toggle .icon-close {
    display: none;
}
.main-navigation.toggled .menu-toggle .icon-bars {
    display: none !important;
}
.main-navigation.toggled .menu-toggle .icon-close {
    display: inline-flex !important;
}

.main-navigation .main-nav {
    display: flex;
    flex: 1;
}
.main-navigation .main-nav ul.menu {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
}
.main-navigation .main-nav ul.menu > li {
    position: relative;
    margin: 0;
    padding: 0;
}
.main-navigation .main-nav ul.menu > li > a {
    color: #ffffff !important;
    display: block;
    padding: 12px 14px;
    font-size: 14px;
    font-weight: 700;
    text-decoration: none;
    transition: background 0.15s ease;
}
.main-navigation .main-nav ul.menu > li:hover > a,
.main-navigation .main-nav ul.menu > li.current-menu-item > a {
    background-color: #07162c;
}
.main-navigation .main-nav ul.menu > li.menu-item-has-children > a {
    display: flex;
    align-items: center;
    gap: 6px;
}
.main-navigation .dropdown-menu-toggle {
    display: inline-flex;
    align-items: center;
}
.main-navigation .dropdown-menu-toggle svg {
    width: 11px;
    height: 11px;
    fill: #ffffff;
    transition: transform 0.2s ease;
}

/* Sub-Menu (More Dropdown) */
.main-navigation ul.sub-menu {
    position: absolute;
    top: 100%;
    left: 0;
    background-color: #0b213f;
    min-width: 190px;
    list-style: none;
    margin: 0;
    padding: 6px 0;
    display: none;
    box-shadow: 0 6px 16px rgba(0,0,0,0.3);
    z-index: 100000;
    border-top: 2px solid #cd0808;
}
.main-navigation ul.sub-menu li {
    width: 100%;
    margin: 0;
    padding: 0;
}
.main-navigation ul.sub-menu li a {
    color: #ffffff !important;
    padding: 10px 16px;
    display: block;
    font-size: 13.5px;
    font-weight: 600;
    text-decoration: none;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.main-navigation ul.sub-menu li a:hover {
    background-color: #07162c;
    color: #ffd700 !important;
}
.main-navigation .main-nav ul.menu > li:hover > ul.sub-menu,
.main-navigation .main-nav ul.menu > li.sfHover > ul.sub-menu {
    display: block;
}

/* Menu Bar Items (Search Icon) */
.main-navigation .menu-bar-items {
    display: flex;
    align-items: center;
}
.main-navigation .menu-bar-item a {
    color: #ffffff !important;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    cursor: pointer;
}
.main-navigation .menu-bar-item a svg {
    width: 18px;
    height: 18px;
    fill: #ffffff;
}
.main-navigation .menu-bar-item a:hover {
    background-color: #07162c;
}

/* Mobile Responsive - Compact Original Sarkari Result Style */
@media (max-width: 768px) {
    .main-navigation .inside-navigation {
        flex-wrap: wrap !important;
        padding: 0 8px !important;
        min-height: 38px !important;
        height: auto !important;
    }
    .main-navigation .menu-toggle {
        display: flex !important;
        padding: 6px 4px !important;
        font-size: 14px !important;
        line-height: 1 !important;
        min-height: 38px !important;
        height: auto !important;
    }
    .main-navigation .menu-toggle .gp-icon svg {
        width: 16px !important;
        height: 16px !important;
    }
    .main-navigation .main-nav {
        display: none !important;
        width: 100% !important;
        order: 3 !important;
        background-color: #05055f !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main-navigation.toggled .main-nav {
        display: block !important;
    }
    .main-navigation .main-nav ul.menu {
        flex-direction: column !important;
        width: 100% !important;
        align-items: stretch !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .main-navigation .main-nav ul.menu > li {
        width: 100% !important;
        border-bottom: 1px solid rgba(255,255,255,0.05) !important;
        margin: 0 !important;
        padding: 0 !important;
        position: relative !important;
    }
    .main-navigation .main-nav ul.menu > li > a {
        padding: 7px 12px !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        line-height: 1.25 !important;
        min-height: unset !important;
        height: auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        text-decoration: none !important;
        color: #ffffff !important;
    }
    .main-navigation .main-nav ul.menu > li.current-menu-item > a {
        background-color: #070763 !important;
    }
    .main-navigation ul.sub-menu {
        position: static !important;
        box-shadow: none !important;
        background-color: #04044a !important;
        padding: 0 !important;
        margin: 0 !important;
        border-top: none !important;
        display: none !important;
        width: 100% !important;
    }
    .main-navigation .main-nav ul.menu > li.sfHover > ul.sub-menu,
    .main-navigation .main-nav ul.menu > li.sub-menu-open > ul.sub-menu,
    .main-navigation ul.sub-menu.sub-menu-open {
        display: block !important;
    }
    .main-navigation ul.sub-menu li {
        border-bottom: 1px solid rgba(255,255,255,0.04) !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }
    .main-navigation ul.sub-menu li a {
        padding: 6.5px 12px 6.5px 24px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        line-height: 1.25 !important;
        background: #04044a !important;
        min-height: unset !important;
        height: auto !important;
        display: block !important;
        color: #ffffff !important;
    }
}

/* Search Modal Popup */
.gp-modal.gp-search-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    -webkit-backdrop-filter: blur(4px);
    z-index: 9999999;
    display: none;
    align-items: flex-start;
    justify-content: center;
    padding-top: 70px;
    box-sizing: border-box;
}
.gp-modal.gp-search-modal.gp-modal--open {
    display: flex !important;
}
.gp-modal__overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    padding-top: 70px;
    box-sizing: border-box;
}
.gp-modal__container {
    width: 90%;
    max-width: 600px;
    background: #ffffff;
    border-radius: 6px;
    padding: 6px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.6);
    position: relative;
    z-index: 10;
    animation: gpModalSlideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    box-sizing: border-box;
}
@keyframes gpModalSlideDown {
    from { opacity: 0; transform: translateY(-20px); }
    to { opacity: 1; transform: translateY(0); }
}
.search-modal-form {
    margin: 0;
    padding: 0;
    width: 100%;
}
.search-modal-fields {
    display: flex;
    align-items: center;
    position: relative;
    width: 100%;
}
.search-modal-fields .search-field {
    width: 100%;
    border: none;
    padding: 12px 46px 12px 16px;
    font-size: 16px;
    font-family: inherit;
    color: #1e293b;
    outline: none;
    background: transparent;
    box-sizing: border-box;
}
.search-modal-fields button {
    position: absolute;
    right: 8px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 8px;
    color: #334155;
    display: flex;
    align-items: center;
    justify-content: center;
}
.search-modal-fields button svg {
    width: 20px;
    height: 20px;
    fill: #334155;
}
.search-modal-fields button:hover svg {
    fill: #000000;
}
</style>"""

def get_nav_html():
    return """<nav aria-label="Primary" class="main-navigation grid-container has-menu-bar-items sub-menu-right" id="site-navigation" itemscope="" itemtype="https://schema.org/SiteNavigationElement">
<div class="inside-navigation grid-container">
<button aria-controls="primary-menu" aria-expanded="false" class="menu-toggle" type="button" aria-label="Toggle navigation">
<span class="gp-icon icon-menu-bars">
    <svg class="icon-bars" aria-hidden="true" height="1em" viewbox="0 0 512 512" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M0 96c0-13.255 10.745-24 24-24h464c13.255 0 24 10.745 24 24s-10.745 24-24 24H24c-13.255 0-24-10.745-24-24zm0 160c0-13.255 10.745-24 24-24h464c13.255 0 24 10.745 24 24s-10.745 24-24 24H24c-13.255 0-24-10.745-24-24zm0 160c0-13.255 10.745-24 24-24h464c13.255 0 24 10.745 24 24s-10.745 24-24 24H24c-13.255 0-24-10.745-24-24z"></path></svg>
    <svg class="icon-close" aria-hidden="true" height="1em" viewbox="0 0 512 512" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M71.029 71.029c9.373-9.372 24.569-9.372 33.942 0L256 222.059l151.029-151.03c9.373-9.372 24.569-9.372 33.942 0 9.372 9.373 9.372 24.569 0 33.942L289.941 256l151.03 151.029c9.372 9.373 9.372 24.569 0 33.942-9.373 9.372-24.569 9.372-33.942 0L256 289.941l-151.029 151.03c-9.373 9.372-24.569 9.372-33.942 0-9.372-9.373-9.372-24.569 0-33.942L222.059 256 71.029 104.971c-9.372-9.373-9.372-24.569 0-33.942z"></path></svg>
</span>
<span class="mobile-menu">Menu</span>
</button>
<div class="main-nav" id="primary-menu">
<ul class="menu sf-menu" id="menu-menu">
    <li class="menu-item current-menu-item"><a href="/" aria-current="page">Home</a></li>
    <li class="menu-item"><a href="/latest-jobs/">Latest Job</a></li>
    <li class="menu-item"><a href="/admit-card/">Admit Card</a></li>
    <li class="menu-item"><a href="/result/">Result</a></li>
    <li class="menu-item"><a href="/admission/">Admission</a></li>
    <li class="menu-item"><a href="/syllabus/">Syllabus</a></li>
    <li class="menu-item"><a href="/answer-key/">Answer Key</a></li>
    <li class="menu-item menu-item-has-children">
        <a href="javascript:void(0);" role="button" aria-expanded="false">More<span class="dropdown-menu-toggle" role="presentation"><span class="gp-icon icon-arrow"><svg aria-hidden="true" height="1em" viewbox="0 0 330 512" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M305.913 197.085c0 2.266-1.133 4.815-2.833 6.514L171.087 335.593c-1.7 1.7-4.249 2.832-6.515 2.832s-4.815-1.133-6.515-2.832L26.064 203.599c-1.7-1.7-2.832-4.248-2.832-6.514s1.132-4.816 2.832-6.515l14.162-14.163c1.7-1.699 3.966-2.832 6.515-2.832 2.266 0 4.815 1.133 6.515 2.832l111.316 111.317 111.316-111.317c1.7-1.699 4.249-2.832 6.515-2.832s4.815 1.133 6.515 2.832l14.162 14.163c1.7 1.7 2.833 4.249 2.833 6.515z"></path></svg></span></span></a>
        <ul class="sub-menu">
            <li class="menu-item"><a href="/important/">Important</a></li>
            <li class="menu-item"><a href="/certificate-verification/">Certificate Verification</a></li>
            <li class="menu-item"><a href="/contact/">Contact Us</a></li>
            <li class="menu-item"><a href="/privacy-policy/">Privacy Policy</a></li>
            <li class="menu-item"><a href="/terms-and-conditions/">Terms &amp; Conditions</a></li>
            <li class="menu-item"><a href="/about-us/">About Us</a></li>
            <li class="menu-item"><a href="/disclaimer/">Disclaimer</a></li>
        </ul>
    </li>
</ul>
</div>
<div class="menu-bar-items">
    <span class="menu-bar-item">
        <a aria-controls="gp-search" aria-haspopup="dialog" aria-label="Open search" data-gpmodal-trigger="gp-search" href="javascript:void(0);" role="button">
            <span class="gp-icon icon-search"><svg aria-hidden="true" height="1em" viewbox="0 0 512 512" width="1em" xmlns="http://www.w3.org/2000/svg"><path clip-rule="evenodd" d="M208 48c-88.366 0-160 71.634-160 160s71.634 160 160 160 160-71.634 160-160S296.366 48 208 48zM0 208C0 93.125 93.125 0 208 0s208 93.125 208 208c0 48.741-16.765 93.566-44.843 129.024l133.826 134.018c9.366 9.379 9.355 24.575-.025 33.941-9.379 9.366-24.575 9.355-33.941-.025L337.238 370.987C301.747 399.167 256.839 416 208 416 93.125 416 0 322.875 0 208z" fill-rule="evenodd"></path></svg></span>
        </a>
    </span>
</div>
</div>
</nav>"""

def get_search_modal_html():
    return """<div aria-label="Search" aria-modal="true" class="gp-modal gp-search-modal" id="gp-search" role="dialog">
<div class="gp-modal__overlay" data-gpmodal-close="" tabindex="-1">
<div class="gp-modal__container">
<form action="/search" class="search-modal-form" method="get" role="search">
<label class="screen-reader-text" for="search-modal-input">Search for:</label>
<div class="search-modal-fields">
<input class="search-field" id="search-modal-input" name="q" placeholder="Search …" type="search" value="" autocomplete="off" />
<button aria-label="Search" type="submit"><span class="gp-icon icon-search"><svg aria-hidden="true" height="1em" viewbox="0 0 512 512" width="1em" xmlns="http://www.w3.org/2000/svg"><path clip-rule="evenodd" d="M208 48c-88.366 0-160 71.634-160 160s71.634 160 160 160 160-71.634 160-160S296.366 48 208 48zM0 208C0 93.125 93.125 0 208 0s208 93.125 208 208c0 48.741-16.765 93.566-44.843 129.024l133.826 134.018c9.366 9.379 9.355 24.575-.025 33.941-9.379 9.366-24.575 9.355-33.941-.025L337.238 370.987C301.747 399.167 256.839 416 208 416 93.125 416 0 322.875 0 208z" fill-rule="evenodd"></path></svg></span></button>
</div>
</form>
</div>
</div>
</div>"""

def get_gp_scripts_html():
    return """<script id="st-nav-search-scripts">
(function() {
    function initStudyTopperNavigation() {
        var siteNav = document.getElementById('site-navigation');
        var menuBtn = document.querySelector('.menu-toggle');
        var mainNav = document.getElementById('primary-menu');
        var searchModal = document.getElementById('gp-search');

        if (!siteNav || !menuBtn) return;
        if (siteNav.dataset.stNavV2Initialized === 'true') return;
        siteNav.dataset.stNavV2Initialized = 'true';

        // 1. Mobile Hamburger Menu Toggle
        var lastMenuToggleTs = 0;
        function handleMenuToggle(e) {
            var now = Date.now();
            if (now - lastMenuToggleTs < 250) return;
            lastMenuToggleTs = now;
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            var isCurrentlyToggled = siteNav.classList.contains('toggled');
            if (isCurrentlyToggled) {
                siteNav.classList.remove('toggled');
                menuBtn.setAttribute('aria-expanded', 'false');
                if (mainNav) mainNav.style.display = 'none';
            } else {
                siteNav.classList.add('toggled');
                menuBtn.setAttribute('aria-expanded', 'true');
                if (mainNav) mainNav.style.display = 'block';
            }
        }

        menuBtn.addEventListener('click', handleMenuToggle);

        // 2. 'More' / Submenu Dropdown Controller
        var moreParents = document.querySelectorAll('.menu-item-has-children');
        moreParents.forEach(function(parentLi) {
            var toggleLink = parentLi.querySelector(':scope > a') || parentLi.querySelector('a');
            var subMenu = parentLi.querySelector(':scope > .sub-menu') || parentLi.querySelector('.sub-menu');
            var arrowSvg = parentLi.querySelector('.dropdown-menu-toggle svg') || parentLi.querySelector('.dropdown-menu-toggle');
            var lastToggleTs = 0;

            function toggleDropdown(e) {
                var now = Date.now();
                if (now - lastToggleTs < 250) return;
                lastToggleTs = now;
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                var isOpen = parentLi.classList.contains('sub-menu-open') || (subMenu && subMenu.classList.contains('sub-menu-open'));
                if (isOpen) {
                    parentLi.classList.remove('sub-menu-open', 'sfHover');
                    if (toggleLink) toggleLink.setAttribute('aria-expanded', 'false');
                    if (subMenu) {
                        subMenu.classList.remove('sub-menu-open');
                        subMenu.style.setProperty('display', 'none', 'important');
                    }
                    if (arrowSvg) arrowSvg.style.transform = 'rotate(0deg)';
                } else {
                    parentLi.classList.add('sub-menu-open', 'sfHover');
                    if (toggleLink) toggleLink.setAttribute('aria-expanded', 'true');
                    if (subMenu) {
                        subMenu.classList.add('sub-menu-open');
                        subMenu.style.setProperty('display', 'block', 'important');
                    }
                    if (arrowSvg) arrowSvg.style.transform = 'rotate(180deg)';
                }
            }

            if (toggleLink) {
                toggleLink.addEventListener('click', toggleDropdown);
            }
            var dropdownSpan = parentLi.querySelector('.dropdown-menu-toggle');
            if (dropdownSpan && dropdownSpan !== toggleLink) {
                dropdownSpan.addEventListener('click', toggleDropdown);
            }
        });

        // 3. Search Modal Controller
        function openSearch(e) {
            if (e) {
                e.preventDefault();
                e.stopPropagation();
            }
            if (searchModal) {
                searchModal.classList.add('gp-modal--open');
                searchModal.style.display = 'flex';
                var inp = searchModal.querySelector('input[name="q"], input[type="search"]');
                if (inp) {
                    setTimeout(function() { inp.focus(); }, 60);
                }
            }
        }

        function closeSearch(e) {
            if (searchModal) {
                searchModal.classList.remove('gp-modal--open');
                searchModal.style.display = 'none';
            }
        }

        var searchBtns = document.querySelectorAll('[data-gpmodal-trigger="gp-search"], .icon-search, a[aria-controls="gp-search"]');
        searchBtns.forEach(function(btn) {
            btn.addEventListener('click', openSearch);
        });

        if (searchModal) {
            searchModal.addEventListener('click', function(e) {
                if (e.target === searchModal || e.target.classList.contains('gp-modal__overlay') || e.target.hasAttribute('data-gpmodal-close')) {
                    closeSearch(e);
                }
            });

            var form = searchModal.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    var inp = form.querySelector('input[name="q"], input[type="search"]');
                    if (inp && inp.value.trim()) {
                        window.location.href = '/search?q=' + encodeURIComponent(inp.value.trim());
                        e.preventDefault();
                    }
                });
            }
        }

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' || e.keyCode === 27) {
                closeSearch();
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initStudyTopperNavigation);
    } else {
        initStudyTopperNavigation();
    }
})();
</script>"""

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
    
    # Dynamic WebP Post Thumbnail Generator (< 10KB)
    try:
        from thumbnail_generator import generate_post_thumbnail
        thumb_filename = f"{slug}.webp"
        thumb_abs_path = os.path.join('/root/sarkari-result-portal/static/thumbnails', thumb_filename)
        if not os.path.exists(thumb_abs_path) or os.path.getsize(thumb_abs_path) == 0:
            posts_badge = post.get('total_posts') or (badge_val if any(c.isdigit() for c in str(badge_val)) else '')
            last_dt = post.get('application_last_date', '')
            generate_post_thumbnail(
                title=title,
                total_posts=str(posts_badge) if posts_badge else '',
                last_date=str(last_dt),
                output_path=thumb_abs_path
            )
        banner_url = f"/static/thumbnails/{thumb_filename}"
    except Exception as e:
        print("Thumbnail gen error in render_single_post_html:", e)
        banner_url = "/static/images/studytopper_banner_base.webp"

    tags_list = [t.strip() for t in tags_str.split(',') if t.strip()]
    tag_chips = ''.join([f'<span class="st-tag-chip">#{t}</span>' for t in tags_list])

    clean_how_title = re.sub(r'\s*(?:Online Form|Recruitment|Vacancy)?\s*(?:202[4-9])?$', '', title, flags=re.IGNORECASE).strip()
    clean_cat_header = category_name if not category_name.lower().startswith('latest') else category_name.replace('Latest', '').strip()

    # Related Posts from same category
    all_active_posts = load_all_active_posts()
    rel_posts = [p for p in all_active_posts if p.get('slug') != slug and p.get('category') == category_slug][:6]
    if not rel_posts:
        rel_posts = [p for p in all_active_posts if p.get('slug') != slug][:6]

    rel_rows = ""
    for rp in rel_posts:
        rp_title = rp.get('title', '')
        rp_slug = rp.get('slug', '')
        rel_rows += f"""<tr>
            <td style="padding: 8px 12px; border: 1px solid #ab183d; background: #ffffff;">
                <a href="/{rp_slug}/" style="color: #0000ef; font-weight: 600; text-decoration: none; font-size: 13.5px;">• {rp_title}</a>
            </td>
        </tr>"""

    related_posts_table = f"""
    <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin: 16px 0;">
        <thead>
            <tr style="background-color: #ab183d; color: #ffffff;">
                <th style="padding: 8px 10px; text-align: center; font-size: 15px; font-weight: 700;">Latest {clean_cat_header} &amp; Related Recruitment Updates</th>
            </tr>
        </thead>
        <tbody>
            {rel_rows}
        </tbody>
    </table>
    """ if rel_rows else ""

    extra_content_html = ""
    if cleaned_content and len(cleaned_content.strip()) > 50:
        extra_content_html = f"""<div style="margin: 16px 0;">{cleaned_content}</div>"""

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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" media="print" onload="this.media='all'">
    <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap"></noscript>
    <style id="generatepress-main-css">{MAIN_CSS_CACHE}</style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" media="print" onload="this.media='all'">
    {get_nav_search_styles_html()}
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

    {get_nav_html()}

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

    {get_footer_html(settings)}
    {get_search_modal_html()}
    {get_gp_scripts_html()}
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
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Open+Sans:400,600,700&display=swap">
    <link rel="stylesheet" href="/wp-content/themes/generatepress/assets/css/main.min.css?ver=3.5.1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    {get_nav_search_styles_html()}
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: Open Sans, Arial, Helvetica, sans-serif; margin:0; padding:0; background:#fff; color:#000; font-size:14px; line-height:1.5; }}
        header.site-header {{ background-color: #ab183d; text-align: center; padding: 15px 10px; }}
        .main-title {{ margin: 0; font-size: 32px; font-weight: 800; text-transform:uppercase; }}
        .main-title a {{ color: #fff; text-decoration: none; }}
        .site-description {{ color: #fff; font-size: 16px; font-weight: 700; margin: 4px 0 0; text-transform:uppercase; }}
        .page-container {{ max-width: 1040px; margin: 20px auto; padding: 0 12px; min-height: 400px; }}
        .breadcrumb {{ font-size: 13px; color: #555; margin-bottom: 15px; }}
        .breadcrumb a {{ color: #0000ef; text-decoration: underline; }}
        .cat-card {{ border: 2px solid #ab183d; border-radius: 4px; padding: 20px; background: #fff; }}
        h1.cat-heading {{ background: #ab183d; color: #fff; font-size: 20px; text-align: center; padding: 12px; margin: -20px -20px 20px -20px; font-weight: 700; }}
        .sarkari-wrapper {{ max-width:600px; margin:0 auto; text-align:center; background:#1e1e1e; padding:20px; border-radius:6px; }}
        .sarkari-wrapper h3 {{ color:#fff; margin-bottom:15px; }}
        .sarkari-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
        .sarkari-grid a {{ background:#2a2a2a; color:#fff; padding:10px; text-decoration:none; border-radius:4px; font-size:14px; display:flex; align-items:center; justify-content:center; }}
        .sarkari-grid a:hover {{ background:#3a3a3a; }}
        .gb-container-7d9550dd {{ background:#212121; padding:25px 15px 15px; }}
        .gb-container-d1f47294 {{ background:#1d2327; color:#fff; text-align:center; padding:18px 10px; }}
        .gb-container-d1f47294 a {{ color:#fff; }}
        .gb-button {{ background:#000000 !important; color:#ffffff !important; padding:6px 14px; border-radius:4px; text-decoration:underline; font-size:13px; border:1px solid #333; }}
    </style>
</head>
<body class="wp-theme-generatepress">
    <header class="site-header">
        <h1 class="main-title"><a href="/">{site_name}</a></h1>
        <p class="site-description">{domain}</p>
    </header>
    {get_nav_html()}
    <div class="page-container">
        <div class="breadcrumb">
            <a href="/">Home</a> » <span>{cat_title}</span>
        </div>
        <div class="cat-card">
            <h1 class="cat-heading">{cat_title} 2026 : {site_name}</h1>
            {posts_list_html}
            <div style="text-align:center; margin-top:30px;">
                <a href="/" style="background:#ab183d; color:#fff; text-decoration:none; padding:8px 18px; border-radius:4px; font-weight:700; font-size:13px; display:inline-block;">« Back to Study Topper Home</a>
            </div>
        </div>
    </div>
    {get_footer_html(settings)}
    {get_search_modal_html()}
    {get_gp_scripts_html()}
</body>
</html>"""

def render_search_page_html(query, search_results, settings):
    site_name = settings.get('site_name', 'STUDY TOPPER™')
    domain = settings.get('domain', 'studytopper.in')

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
    <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Open+Sans:400,600,700&display=swap">
    <link rel="stylesheet" href="/wp-content/themes/generatepress/assets/css/main.min.css?ver=3.5.1">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    {get_nav_search_styles_html()}
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: Open Sans, Arial, Helvetica, sans-serif; margin:0; padding:0; background:#fff; color:#000; font-size:14px; line-height:1.5; }}
        header.site-header {{ background-color: #ab183d; text-align: center; padding: 15px 10px; }}
        .main-title {{ margin: 0; font-size: 32px; font-weight: 800; text-transform:uppercase; }}
        .main-title a {{ color: #fff; text-decoration: none; }}
        .site-description {{ color: #fff; font-size: 16px; font-weight: 700; margin: 4px 0 0; text-transform:uppercase; }}
        .page-container {{ max-width: 1040px; margin: 20px auto; padding: 0 12px; min-height: 400px; }}
        .breadcrumb {{ font-size: 13px; color: #555; margin-bottom: 15px; }}
        .breadcrumb a {{ color: #0000ef; text-decoration: underline; }}
        .cat-card {{ border: 2px solid #ab183d; border-radius: 4px; padding: 20px; background: #fff; }}
        h1.cat-heading {{ background: #ab183d; color: #fff; font-size: 20px; text-align: center; padding: 12px; margin: -20px -20px 20px -20px; font-weight: 700; }}
        .sarkari-wrapper {{ max-width:600px; margin:0 auto; text-align:center; background:#1e1e1e; padding:20px; border-radius:6px; }}
        .sarkari-wrapper h3 {{ color:#fff; margin-bottom:15px; }}
        .sarkari-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
        .sarkari-grid a {{ background:#2a2a2a; color:#fff; padding:10px; text-decoration:none; border-radius:4px; font-size:14px; display:flex; align-items:center; justify-content:center; }}
        .sarkari-grid a:hover {{ background:#3a3a3a; }}
        .gb-container-7d9550dd {{ background:#212121; padding:25px 15px 15px; }}
        .gb-container-d1f47294 {{ background:#1d2327; color:#fff; text-align:center; padding:18px 10px; }}
        .gb-container-d1f47294 a {{ color:#fff; }}
        .gb-button {{ background:#000000 !important; color:#ffffff !important; padding:6px 14px; border-radius:4px; text-decoration:underline; font-size:13px; border:1px solid #333; }}
    </style>
</head>
<body class="wp-theme-generatepress">
    <header class="site-header">
        <h1 class="main-title"><a href="/">{site_name}</a></h1>
        <p class="site-description">{domain}</p>
    </header>
    {get_nav_html()}
    <div class="page-container">
        <div class="breadcrumb">
            <a href="/">Home</a> » <span>Search Results</span>
        </div>
        <div class="cat-card">
            <h1 class="cat-heading">Search Results for : "{query}"</h1>
            {results_html}
            <div style="text-align:center; margin-top:30px;">
                <a href="/" style="background:#ab183d; color:#fff; text-decoration:none; padding:8px 18px; border-radius:4px; font-weight:700; font-size:13px; display:inline-block;">« Back to Study Topper Home</a>
            </div>
        </div>
    </div>
    {get_footer_html(settings)}
    {get_search_modal_html()}
    {get_gp_scripts_html()}
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
    lifecycle.safe_write_json(SETTINGS_FILE, data)

    if supa.is_supabase_configured():
        try:
            supa.save_settings_to_supabase(data)
        except Exception as se:
            print(f"Notice: Supabase save exception: {se}")

def sanitize_html(html_content, current_host, is_alria_mode=False):
    soup = BeautifulSoup(html_content, 'html.parser')
    settings = load_settings()
    theme = settings.get('theme_colors', {})
    seo_cfg = settings.get('seo', {})

    # 0. HTML Lang & Viewport & Canonical Absolute Optimization
    if soup.html:
        soup.html['lang'] = 'en-US'

    domain_name = 'studytopper.in'
    current_path = '/'
    try:
        from flask import request
        if request and request.path:
            current_path = request.path
    except Exception:
        pass
    
    canon_tag = soup.find('link', rel='canonical')
    if canon_tag and canon_tag.get('href'):
        old_href = canon_tag['href'].strip()
        if old_href.startswith('http'):
            old_path = re.sub(r'^https?://[^/]+', '', old_href)
            canon_tag['href'] = f"https://{domain_name}{old_path if old_path else '/'}"
        else:
            old_path = old_href if old_href.startswith('/') else f"/{old_href}"
            canon_tag['href'] = f"https://{domain_name}{old_path}"
    else:
        canonical_url = f"https://{domain_name}{current_path}"
        if soup.head:
            soup.head.append(soup.new_tag('link', rel='canonical', href=canonical_url))

    # 1. Strip ALL legacy external ads, foreign tracking scripts & duplicate GTM from templates
    for s in soup.find_all(['script', 'iframe', 'ins']):
        src = (s.get('src') or '').lower()
        content = (s.string or s.get_text() or '').lower()
        classes = s.get('class', [])
        if any(ad in src for ad in ['googlesyndication', 'doubleclick', 'google-analytics', 'googletagmanager', 'izooto', 'cloudflare-static']):
            s.decompose()
        elif any(bad in content for bad in ['g-bx9pepg50m', 'g-lz32t0n2xe', 'googletagmanager', 'gtag(\'config\'', 'izooto']):
            s.decompose()
        elif 'adsbygoogle' in classes:
            s.decompose()

    # 1a. Clean broken font links and dead /cf-fonts/ CSS
    for st in soup.find_all('style'):
        st_text = st.get_text()
        if '/cf-fonts/' in st_text or st.get('id') == 'generate-google-fonts-css':
            st.decompose()

    for link in soup.find_all('link', rel='stylesheet'):
        href = link.get('href', '')
        link_id = link.get('id', '')
        if 'fonts.googleapis.com' in href or link_id == 'generateblocks-google-fonts-css':
            if any(bad in href for bad in ['Helvetica', 'Arial', 'Lato:', 'Source+Sans+Pro', 'Open+Sans:200', 'generateblocks']) or link_id == 'generateblocks-google-fonts-css':
                link.decompose()
        elif 'main.min.css' in href:
            if MAIN_CSS_CACHE and soup.head:
                if not soup.find(id='generatepress-main-css'):
                    inline_css = soup.new_tag('style', id='generatepress-main-css')
                    inline_css.string = MAIN_CSS_CACHE
                    soup.head.append(inline_css)
                link.decompose()
            else:
                link['media'] = 'print'
                link['onload'] = "this.media='all'"
        elif 'style-32.css' in href:
            if STYLE_32_CSS_CACHE and soup.head:
                if not soup.find(id='generateblocks-style-32'):
                    s32_tag = soup.new_tag('style', id='generateblocks-style-32')
                    s32_tag.string = STYLE_32_CSS_CACHE
                    soup.head.append(s32_tag)
                link.decompose()
            else:
                link['media'] = 'print'
                link['onload'] = "this.media='all'"
        # Make secondary non-critical CSS non-blocking
        elif any(c in href for c in ['featured-images.min.css', 'all.min.css', 'comments.min.css']):
            link['media'] = 'print'
            link['onload'] = "this.media='all'"

    # 1b. Inject Fast Preconnect & Google Fonts
    if soup.head and not soup.find('link', href=re.compile(r'fonts\.googleapis\.com/css2\?family=Open\+Sans')):
        pconn1 = soup.new_tag('link', rel='preconnect', href='https://fonts.googleapis.com')
        pconn2 = soup.new_tag('link', rel='preconnect', href='https://fonts.gstatic.com', crossorigin=True)
        font_link = soup.new_tag('link', rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap', media='print', onload="this.media='all'")
        soup.head.append(pconn1)
        soup.head.append(pconn2)
        soup.head.append(font_link)

    # 1c. LCP Text Element Immediate Zero-Delay Render Optimization
    for p_tag in soup.find_all(class_=re.compile(r'gb-headline-d55a09d3')):
        curr_style = p_tag.get('style', '')
        p_tag['style'] = (curr_style + ' font-family: Arial, Helvetica, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; font-display: swap !important; text-rendering: optimizeSpeed !important; content-visibility: visible !important; contain-intrinsic-size: auto !important;').strip()

    # 1d. Defer all local JavaScript
    for s in soup.find_all('script'):
        if s.get('src') and not s.get('defer') and not s.get('async'):
            s['defer'] = True

    # 1e. Images Performance & 0 CLS (Explicit Dimensions)
    for img in soup.find_all('img'):
        src = (img.get('src') or '').lower()
        if 'live-gif' in src or 'live' in src:
            img['width'] = '62'
            img['height'] = '20'
            img['loading'] = 'eager'
            img['fetchpriority'] = 'high'
            img['decoding'] = 'async'
            img['style'] = 'width:62px !important; height:20px !important; aspect-ratio:62/20 !important; display:inline-block !important; vertical-align:middle !important;'
            if img.get('srcset'):
                del img['srcset']
            if img.get('sizes'):
                del img['sizes']
        elif 'sarkari-result-6' in src:
            img['width'] = '150'
            img['height'] = '150'
            img['style'] = 'width:150px !important; height:150px !important; aspect-ratio:1/1 !important;'
        elif '512px512px' in src:
            img['width'] = '300'
            img['height'] = '300'
            img['style'] = 'width:300px !important; height:300px !important; aspect-ratio:1/1 !important;'
        
        if not img.get('alt'):
            img['alt'] = settings.get('site_name', 'Study Topper')
        if not img.get('loading') and not img.get('fetchpriority'):
            img['loading'] = 'lazy'
            img['decoding'] = 'async'

    # 1e. Contrast Fixes for WCAG AA (Replace hardcoded light/bright reds & colors)
    for tag in soup.find_all(['span', 'font', 'a', 'p', 'strong']):
        style_attr = tag.get('style', '')
        if '#ff0000' in style_attr or 'rgb(255, 0, 0)' in style_attr:
            tag['style'] = re.sub(r'#ff0000|rgb\(255,\s*0,\s*0\)', '#b91c1c', style_attr)
        if tag.get('color') == '#ff0000' or tag.get('color') == 'red':
            tag['color'] = '#b91c1c'

    # 1f. Inject Blinking Animation CSS for Urgent & Extended Vacancies
    if not soup.find(id='agy-lifecycle-blink-css') and soup.head:
        soup.head.append(BeautifulSoup(lifecycle.BLINKING_CSS, 'html.parser'))

    # 2. Inject Zero-Latency High Performance Google Analytics (GA4)
    ga_id = seo_cfg.get('google_analytics_id', '').strip()
    if ga_id and soup.body:
        lazy_ga = soup.new_tag('script')
        lazy_ga.string = f"""
        (function() {{
            var gaLoaded = false;
            function initGA() {{
                if (gaLoaded) return;
                gaLoaded = true;
                var s = document.createElement('script');
                s.src = 'https://www.googletagmanager.com/gtag/js?id={ga_id}';
                s.async = true;
                document.head.appendChild(s);
                window.dataLayer = window.dataLayer || [];
                function gtag(){{dataLayer.push(arguments);}}
                gtag('js', new Date());
                gtag('config', '{ga_id}');
            }}
            window.addEventListener('scroll', initGA, {{once: true, passive: true}});
            window.addEventListener('touchstart', initGA, {{once: true, passive: true}});
            window.addEventListener('mousemove', initGA, {{once: true, passive: true}});
            if ('requestIdleCallback' in window) {{
                requestIdleCallback(function() {{ setTimeout(initGA, 3500); }});
            }} else {{
                setTimeout(initGA, 4000);
            }}
        }})();
        """
        soup.body.append(lazy_ga)

    # 3. Inject Google Search Console Verification Meta
    gsc_meta = seo_cfg.get('google_site_verification', '').strip()
    if gsc_meta and soup.head:
        if '<meta' in gsc_meta:
            soup.head.append(BeautifulSoup(gsc_meta, 'html.parser'))
        else:
            soup.head.append(soup.new_tag('meta', attrs={'name': 'google-site-verification', 'content': gsc_meta}))

    # 4. Inject Global Meta Description & Keywords
    meta_desc_val = seo_cfg.get('meta_description') or "Study Topper (studytopper.in) - Latest Sarkari Naukri, Online Forms, Results, Admit Card, Answer Key, Syllabus, and Educational Career Guidance."
    meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_desc_tag:
        meta_desc_tag['content'] = meta_desc_val
    elif soup.head:
        soup.head.append(soup.new_tag('meta', attrs={'name': 'description', 'content': meta_desc_val}))

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
    body {{
        background-color: #ffffff !important;
        font-family: Arial, Helvetica, sans-serif !important;
        font-size: 14px !important;
        color: #000000 !important;
    }}
    .grid-container, .wp-block-group__inner-container, .site-container {{
        max-width: 1070px !important;
        margin-left: auto !important;
        margin-right: auto !important;
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
        border-radius: 20px !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
    }}
    a.wp-block-button__link, .wp-block-button__link {{
        background-color: #0000b8 !important;
        color: #ffffff !important;
    }}
    p.gb-headline-d55a09d3, .gb-headline-d55a09d3, .gb-headline-text {{
        font-family: Arial, Helvetica, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-display: swap !important;
    }}

    /* === 8 HIGHLIGHT BOXES (SARKARI RESULT EXACT DESIGN) === */
    .gb-container-0d9861a2 {{
        max-width: 1070px !important;
        margin: 6px auto 10px auto !important;
        padding: 0 4px !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }}
    .gb-grid-wrapper-5aaa8125,
    .gb-grid-wrapper-389edcd7 {{
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 6px !important;
        margin: 0 auto 6px auto !important;
        padding: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
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
    .gb-grid-wrapper-5aaa8125 .gb-headline,
    .gb-grid-wrapper-389edcd7 .gb-headline,
    p.gb-headline-240edee9, p.gb-headline-8f95d922, p.gb-headline-37224a92, p.gb-headline-68cafa90,
    p.gb-headline-106fdfbe, p.gb-headline-19f08da4, p.gb-headline-053dc0a0, p.gb-headline-d128e870 {{
        min-height: 52px !important;
        height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        border-radius: 5px !important;
        padding: 4px 6px !important;
        margin: 0 !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }}
    p.gb-headline-240edee9 {{ background-color: #c90000 !important; }}
    p.gb-headline-8f95d922 {{ background-color: #b83e00 !important; }}
    p.gb-headline-37224a92 {{ background-color: #a20999 !important; }}
    p.gb-headline-68cafa90 {{ background-color: #0b109e !important; }}
    p.gb-headline-106fdfbe {{ background-color: #585a05 !important; }}
    p.gb-headline-19f08da4 {{ background-color: #005fa8 !important; }}
    p.gb-headline-053dc0a0 {{ background-color: #5f0000 !important; }}
    p.gb-headline-d128e870 {{ background-color: #066e1f !important; }}
    .gb-grid-wrapper-5aaa8125 .gb-headline a,
    .gb-grid-wrapper-389edcd7 .gb-headline a,
    .gb-container-0d9861a2 .gb-headline a {{
        color: #ffffff !important;
        font-size: 13.5px !important;
        font-weight: 700 !important;
        font-family: Arial, Helvetica, sans-serif !important;
        line-height: 1.25 !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
        height: 100% !important;
        text-transform: capitalize !important;
    }}
    .gb-grid-wrapper-5aaa8125 .gb-headline:hover,
    .gb-grid-wrapper-389edcd7 .gb-headline:hover {{
        filter: brightness(0.92) !important;
    }}

    @media (max-width: 767px) {{
        .gb-grid-wrapper-5aaa8125,
        .gb-grid-wrapper-389edcd7 {{
            grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
            gap: 4px !important;
            margin-bottom: 4px !important;
        }}
        .gb-grid-wrapper-5aaa8125 .gb-headline,
        .gb-grid-wrapper-389edcd7 .gb-headline {{
            min-height: 48px !important;
            height: 48px !important;
            padding: 2px 4px !important;
        }}
        .gb-grid-wrapper-5aaa8125 .gb-headline a,
        .gb-grid-wrapper-389edcd7 .gb-headline a {{
            font-size: 11.5px !important;
            line-height: 1.15 !important;
        }}
        .gb-grid-column-cb185b36, .gb-grid-column-659c2f86,
        .gb-container-cb185b36, .gb-container-659c2f86 {{
            display: none !important;
        }}
    }}

    /* === CATEGORY SECTIONS (EXACT SARKARI RESULT DESIGN: DESKTOP 3-COL, MOBILE 2-COL) === */
    .gb-grid-wrapper-180dce95 {{
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 10px !important;
        max-width: 1070px !important;
        margin: 12px auto !important;
        padding: 0 4px !important;
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
        border: 1.5px solid #ab183d !important;
        background-color: #ffffff !important;
        border-radius: 0px !important;
        overflow: hidden !important;
    }}
    .gb-grid-wrapper-180dce95 .gb-inside-container {{
        display: flex !important;
        flex-direction: column !important;
        height: 100% !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }}
    .gb-grid-wrapper-180dce95 p.gb-headline-text,
    .gb-grid-wrapper-180dce95 h2.gb-headline-text,
    .gb-grid-wrapper-180dce95 h2,
    .gb-grid-wrapper-180dce95 .gb-headline-text {{
        background-color: #ab183d !important;
        color: #ffffff !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        text-align: center !important;
        padding: 5px 0 6px 0 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
        font-family: Arial, Helvetica, sans-serif !important;
        border-radius: 0 !important;
        letter-spacing: 0.2px !important;
    }}
    .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts,
    ul.wp-block-latest-posts.wp-block-latest-posts__list {{
        padding: 6px 6px 8px 20px !important;
        margin: 0 !important;
        list-style-type: disc !important;
        flex: 1 !important;
        box-sizing: border-box !important;
    }}
    .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li,
    ul.wp-block-latest-posts.wp-block-latest-posts__list li {{
        padding: 3px 0 5px 0 !important;
        margin-bottom: 6px !important;
        line-height: 1.45 !important;
        font-size: 13.5px !important;
    }}
    .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li a,
    .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li a.wp-block-latest-posts__post-title,
    ul.wp-block-latest-posts a {{
        color: #0000ef !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
        font-family: Arial, Helvetica, sans-serif !important;
        text-decoration: underline !important;
        text-decoration-color: #0000ef !important;
        display: inline-block !important;
        padding: 2px 0 !important;
        min-height: 24px !important;
    }}
    .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li a:hover,
    ul.wp-block-latest-posts a:hover {{
        color: #ff0000 !important;
        text-decoration: underline !important;
        text-decoration-color: #ff0000 !important;
    }}

    /* Mobile Responsive - 2 Columns (Matching Screenshot_20260819-150619.png) */
    @media (max-width: 767px) {{
        .gb-grid-wrapper-180dce95 {{
            display: grid !important;
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            gap: 5px !important;
            max-width: 100% !important;
            margin: 6px auto !important;
            padding: 0 3px !important;
        }}
        .gb-grid-wrapper-180dce95 > .gb-grid-column {{
            width: 100% !important;
        }}
        .gb-grid-column-0b76599a {{ order: 1 !important; }}
        .gb-grid-column-c7488d9a {{ order: 2 !important; }}
        .gb-grid-column-e64d3148 {{ order: 3 !important; }}
        .gb-grid-column-d19ddc59 {{ order: 4 !important; }}
        .gb-grid-column-b48dca36 {{ order: 5 !important; }}
        .gb-grid-column-51daea0e {{ order: 6 !important; }}

        .gb-grid-wrapper-180dce95 p.gb-headline-text,
        .gb-grid-wrapper-180dce95 h2.gb-headline-text,
        .gb-grid-wrapper-180dce95 .gb-headline-text {{
            font-size: 15px !important;
            padding: 4px 0 !important;
        }}
        .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts,
        ul.wp-block-latest-posts.wp-block-latest-posts__list {{
            padding: 4px 4px 6px 15px !important;
        }}
        .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li,
        ul.wp-block-latest-posts.wp-block-latest-posts__list li {{
            padding: 3px 0 4px 0 !important;
            margin-bottom: 5px !important;
            font-size: 12.5px !important;
            line-height: 1.4 !important;
        }}
        .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li a,
        .gb-grid-wrapper-180dce95 ul.wp-block-latest-posts li a.wp-block-latest-posts__post-title {{
            font-size: 12.5px !important;
            line-height: 1.35 !important;
            font-weight: 600 !important;
            display: inline-block !important;
            padding: 2px 0 !important;
            min-height: 24px !important;
        }}
    }}

    footer.site-footer, .site-footer, .site-info {{
        background-color: var(--sarkari-foot-bg) !important;
        color: var(--sarkari-foot-txt) !important;
    }}
    footer.site-footer a, .site-info a {{
        color: var(--sarkari-foot-txt) !important;
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
    default_card_bgs = ['#fb0303', '#fb5e03', '#ed13e3', '#0d13b5', '#868a08', '#0080ff', '#5f0000', '#077822']
    fallback_cards = [
        {"title": "Railway NFR Apprentice Online Form 2026", "url": "/railway-nfr-2026/"},
        {"title": "SAV Bihar Class 6 Entrance Exam Online Form 2027-28", "url": "/sav-bihar-class-6-2026/"},
        {"title": "IGCAR Trade Apprentice Online Form 2026", "url": "/igcar-apprentice-2026/"},
        {"title": "IBPS Clerk (CSA) 16th Online Form 2026", "url": "/ibps-clerk-16th-2026/"},
        {"title": "UPESSC Principal Online Form 2026", "url": "/upessc-principal-2026/"},
        {"title": "Bihar Secondary Teachers Eligibility Test STET 2026", "url": "/bihar-stet-2026/"},
        {"title": "BPSC School Teacher TRE 4.0 Online Form 2026", "url": "/bpsc-school-teacher-tre-4-0-2026/"},
        {"title": "RRB JE Online Form 2026 (3993 Posts)", "url": "/rrb-je-2026/"}
    ]

    for idx, col_id in enumerate(card_cols):
        col_div = soup.find(class_=re.compile(rf'gb-grid-column-{col_id}'))
        if col_div:
            p_tag = col_div.find(class_=re.compile(r'gb-headline'))
            if p_tag:
                p_tag.clear()
                c_data = cards[idx] if (idx < len(cards) and cards[idx].get('title')) else fallback_cards[idx]
                c_title = c_data.get('title', '')
                c_url = c_data.get('url', '#')
                new_a = soup.new_tag('a', href=c_url, rel="noreferrer noopener", target="_blank")
                new_a.string = c_title
                new_a['style'] = 'color:#ffffff !important; text-decoration:none !important; font-weight:700 !important; font-size:13.5px !important; font-family:Arial,Helvetica,sans-serif !important; line-height:1.25 !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; width:100% !important; height:100% !important;'
                p_tag.append(new_a)
                
                card_bg = theme.get(f'card_{idx+1}_bg') or default_card_bgs[idx]
                p_tag['style'] = f'background-color:{card_bg} !important; color:#ffffff !important; border-radius:5px !important; min-height:52px !important; height:52px !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; padding:4px 6px !important; margin:0 !important; box-sizing:border-box !important; overflow:hidden !important; width:100% !important;'

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
                    today_date = datetime.now().date()
                    cfg_settings = lifecycle.load_lifecycle_settings()
                    pinned_set = set(cfg_settings.get('pinned_posts', []))
                    urgent_threshold = int(cfg_settings.get('urgent_days_threshold', 3))
                    
                    for cp in cat_new_posts:
                        slug = cp.get('slug')
                        is_pin = (slug in pinned_set)
                        cp['is_pinned'] = is_pin
                        last_date_str = cp.get('application_last_date', '')
                        title_str = cp.get('title', '')
                        is_ext = 'extend' in (last_date_str + title_str + str(cp.get('custom_badge', ''))).lower() or cp.get('is_date_extended', False)
                        parsed_d = lifecycle.parse_date_string(last_date_str)
                        days_rem = (parsed_d - today_date).days if parsed_d else None
                        
                        if is_pin:
                            badge_text = "Date Extended!" if is_ext else ("Last Date Today!" if days_rem == 0 else f"{days_rem} Days Left!" if days_rem is not None else "3 Days Left!")
                            badge_class = "agy-extended-blink" if is_ext else "agy-urgent-blink"
                            cp['badge_markup'] = f' - <span class="agy-blinking-badge {badge_class}">{badge_text}</span>'
                            cp['calc_priority'] = 100000 - min(days_rem or 10, 10)
                        elif days_rem is not None and 0 <= days_rem <= urgent_threshold:
                            badge_text = "Last Date Today!" if days_rem == 0 else f"{days_rem} Days Left!"
                            cp['badge_markup'] = f' - <span class="agy-blinking-badge agy-urgent-blink">{badge_text}</span>'
                            cp['calc_priority'] = 10000 - days_rem
                        elif is_ext:
                            cp['badge_markup'] = ' - <span class="agy-blinking-badge agy-extended-blink">Date Extended!</span>'
                            cp['calc_priority'] = 5000
                        else:
                            cp['badge_markup'] = ''
                            cp['calc_priority'] = 100 - min(days_rem or 90, 90)
                            
                    cat_new_posts.sort(key=lambda x: x.get('calc_priority', 0), reverse=True)
                    
                    for cp in cat_new_posts[:12]:
                        new_li = soup.new_tag('li')
                        link_html = f'<a class="wp-block-latest-posts__post-title" href="/{cp["slug"]}/">{cp["title"]}{cp.get("badge_markup", "")}</a>'
                        new_li.append(BeautifulSoup(link_html, 'html.parser'))
                        ul_tag.append(new_li)
                else:
                    empty_li = soup.new_tag('li', style='list-style:none; color:#64748b; font-size:13px; padding:15px 10px; text-align:center; font-style:italic;')
                    empty_li.string = "No notifications yet. New posts will appear here."
                    ul_tag.append(empty_li)

    # 12. Dynamic Top Study Topper Pages Table
    top_pages_table = settings.get('top_pages_table', [])
    if top_pages_table:
        matrix_tbl = soup.find('table', id='top-pages-matrix-table') or soup.find(class_='wp-block-table')
        if matrix_tbl:
            all_tds = matrix_tbl.find_all('td')
            for idx, td in enumerate(all_tds):
                if idx < len(top_pages_table):
                    item = top_pages_table[idx]
                    t_text = item.get('text', '').strip()
                    t_url = item.get('url', '').strip()
                    td.clear()
                    if t_url and t_url != '#':
                        a_node = soup.new_tag('a', href=t_url, rel="noopener", target="_blank")
                        a_node['style'] = 'color:#0000ef; font-weight:700; text-decoration:none;'
                        a_node.string = t_text
                        td.append(a_node)
                    else:
                        span_node = soup.new_tag('span')
                        span_node['style'] = 'color:#222; font-weight:600;'
                        span_node.string = t_text
                        td.append(span_node)

    # 12b. Dynamic 5 Red Info Sections
    info_sections = settings.get('info_sections', [])
    if info_sections:
        c08 = soup.find(class_='gb-container-08c3e704')
        if c08:
            info_h2s = [h for h in c08.find_all('h2') if 'FAQ' not in h.get_text() and 'Frequently' not in h.get_text()]
            for idx, h2_tag in enumerate(info_h2s):
                if idx < len(info_sections):
                    sec = info_sections[idx]
                    if sec.get('title'):
                        h2_tag.string = sec.get('title')
                    next_p = h2_tag.find_next_sibling('p')
                    if next_p and sec.get('content'):
                        next_p.string = sec.get('content')

    # 12c. Dynamic FAQ Items Rendering
    faq_items = settings.get('faq_items', [])
    if faq_items:
        faq_h2 = None
        for h2 in soup.find_all('h2'):
            if 'FAQ' in h2.get_text() or 'Frequently Asked' in h2.get_text():
                faq_h2 = h2
                break
        if faq_h2:
            faq_wrap = faq_h2.find_next_sibling('div')
            if faq_wrap:
                faq_wrap.clear()
                for q_idx, item in enumerate(faq_items):
                    q_p = soup.new_tag('p', style='margin:12px 0 4px; font-size:14.5px; font-weight:700; color:#a80909;')
                    q_num = soup.new_tag('span', style='color:#000;')
                    q_num.string = f"Q {q_idx+1}. "
                    q_p.append(q_num)
                    q_p.append(BeautifulSoup(item.get('q', ''), 'html.parser'))
                    
                    a_p = soup.new_tag('p', style='margin:0 0 14px; font-size:13.5px; line-height:1.6; color:#222; text-align:justify;')
                    a_label = soup.new_tag('strong', style='color:#077822;')
                    a_label.string = "Ans. "
                    a_p.append(a_label)
                    a_p.append(BeautifulSoup(item.get('a', ''), 'html.parser'))
                    
                    faq_wrap.append(q_p)
                    faq_wrap.append(a_p)

    # 13. Dynamic Full Footer Management (Connect With Us + Socials + Bottom Nav + Copyright)
    footer_cfg = settings.get('footer', {})
    socials = settings.get('socials', {})
    connect_title = footer_cfg.get('connect_title', 'Connect With Us')
    
    default_social_links = [
        {"name": "Study Topper @X", "url": socials.get('twitter', 'https://x.com/')},
        {"name": "Study Topper @Telegram", "url": socials.get('telegram', 'https://t.me/')},
        {"name": "Study Topper @WhatsApp", "url": socials.get('whatsapp', 'https://whatsapp.com/')},
        {"name": "Study Topper @Instagram", "url": socials.get('instagram', 'https://instagram.com/')},
        {"name": "Study Topper @Facebook", "url": socials.get('facebook', 'https://facebook.com/')},
        {"name": "Study Topper @YouTube", "url": socials.get('youtube', 'https://youtube.com/')}
    ]
    social_links = footer_cfg.get('social_links') or default_social_links

    default_nav_links = [
        {"label": "Home", "url": "/"},
        {"label": "Contact", "url": "/contact/"},
        {"label": "Privacy Policy", "url": "/privacy-policy/"},
        {"label": "Disclaimer", "url": "/disclaimer/"}
    ]
    footer_nav_links = footer_cfg.get('nav_links') or default_nav_links
    copyright_text = footer_cfg.get('copyright_text') or settings.get('footer_text', 'Copyright © 2026. All Rights Reserved. Not affiliated with any government agency. Information published for educational guidance.')

    # A. Connect With Us Box & Social Grid
    sarkari_wrapper = soup.find(class_='sarkari-wrapper')
    if sarkari_wrapper:
        h3 = sarkari_wrapper.find('h3') or sarkari_wrapper.find('h2')
        if h3:
            h3.string = connect_title
        grid = sarkari_wrapper.find(class_='sarkari-grid')
        if grid:
            grid.clear()
            for s in social_links:
                s_name = s.get('name', '').strip()
                s_url = s.get('url', '').strip()
                if s_name:
                    s_a = soup.new_tag('a', href=s_url or '#', target="_blank", rel="noopener noreferrer")
                    s_a.string = s_name
                    grid.append(s_a)

    # B. Bottom Copyright Headline
    foot_div = soup.find(class_='gb-headline-e41178b2') or soup.find(class_=re.compile(r'gb-headline-.*e41178b2'))
    if foot_div:
        foot_div.clear()
        foot_div.append(BeautifulSoup(copyright_text.replace('\n', '<br/>'), 'html.parser'))

    # C. Bottom Nav Links
    foot_nav = soup.find(class_='gb-container-658f27a5')
    if foot_nav:
        foot_nav.clear()
        for nl in footer_nav_links:
            lbl = nl.get('label', '').strip()
            url = nl.get('url', '').strip()
            if lbl:
                n_a = soup.new_tag('a', href=url or '#')
                n_a['class'] = 'gb-button gb-button-text'
                n_a.string = lbl
                foot_nav.append(n_a)

    # D. Apply Footer Theme Colors
    foot_bg = theme.get('footer_bg', '#1d2327')
    foot_txt = theme.get('footer_text', '#ffffff')
    for f_el in soup.find_all(class_=re.compile(r'site-footer|naman_footer|gb-container-d1f47294')):
        f_el['style'] = f"background-color:{foot_bg} !important; color:{foot_txt} !important;"

    # 14. Universal Post Page Dynamic Social Buttons & Follow Links
    wa_url = socials.get('whatsapp')
    tg_url = socials.get('telegram')
    ig_url = socials.get('instagram')
    yt_url = socials.get('youtube')
    fb_url = socials.get('facebook')
    tw_url = socials.get('twitter')

    if not wa_url:
        for s in footer_cfg.get('social_links', []):
            if 'whatsapp' in s.get('name', '').lower() and s.get('url'):
                wa_url = s.get('url')
                break
    if not tg_url:
        for s in footer_cfg.get('social_links', []):
            if 'telegram' in s.get('name', '').lower() and s.get('url'):
                tg_url = s.get('url')
                break
    if not ig_url:
        for s in footer_cfg.get('social_links', []):
            if 'instagram' in s.get('name', '').lower() and s.get('url'):
                ig_url = s.get('url')
                break
    if not yt_url:
        for s in footer_cfg.get('social_links', []):
            if 'youtube' in s.get('name', '').lower() and s.get('url'):
                yt_url = s.get('url')
                break
    if not fb_url:
        for s in footer_cfg.get('social_links', []):
            if 'facebook' in s.get('name', '').lower() and s.get('url'):
                fb_url = s.get('url')
                break
    if not tw_url:
        for s in footer_cfg.get('social_links', []):
            if ('@x' in s.get('name', '').lower() or 'twitter' in s.get('name', '').lower()) and s.get('url'):
                tw_url = s.get('url')
                break

    wa_url = wa_url or 'https://whatsapp.com/'
    tg_url = tg_url or 'https://t.me/'
    ig_url = ig_url or 'https://instagram.com/'
    yt_url = yt_url or 'https://youtube.com/'
    fb_url = fb_url or 'https://facebook.com/'
    tw_url = tw_url or 'https://x.com/'

    # A. Top & Bottom standalone social buttons
    for a_el in soup.find_all('a'):
        cls_list = a_el.get('class', [])
        cls_str = ' '.join(cls_list) if isinstance(cls_list, list) else str(cls_list or '')
        text_str = a_el.get_text().strip().lower()
        href_str = a_el.get('href', '').lower()

        if 'whatsapp' in cls_str.lower() or text_str == 'whatsapp' or 'whatsapp.com' in href_str:
            a_el['href'] = wa_url
        elif 'telegram' in cls_str.lower() or text_str == 'telegram' or 't.me' in href_str:
            a_el['href'] = tg_url
        elif 'instagram' in cls_str.lower() or text_str == 'instagram' or 'instagram.com' in href_str:
            a_el['href'] = ig_url
        elif 'youtube' in cls_str.lower() or text_str == 'youtube' or 'youtube.com' in href_str:
            a_el['href'] = yt_url
        elif 'facebook' in cls_str.lower() or text_str == 'facebook' or 'facebook.com' in href_str:
            a_el['href'] = fb_url
        elif 'twitter' in cls_str.lower() or text_str == 'twitter' or text_str == '@x' or 'x.com' in href_str:
            a_el['href'] = tw_url

    # B. Important Links table rows (Join Our WhatsApp Channel / Join Our Telegram Channel)
    for tr in soup.find_all('tr'):
        tr_text = tr.get_text().lower()
        if 'whatsapp channel' in tr_text or 'join our whatsapp' in tr_text:
            for a in tr.find_all('a'):
                a['href'] = wa_url
        elif 'telegram channel' in tr_text or 'join our telegram' in tr_text:
            for a in tr.find_all('a'):
                a['href'] = tg_url
        elif 'instagram channel' in tr_text or 'join our instagram' in tr_text:
            for a in tr.find_all('a'):
                a['href'] = ig_url
        elif 'youtube channel' in tr_text or 'join our youtube' in tr_text:
            for a in tr.find_all('a'):
                a['href'] = yt_url

    # 15. Universal Post Page Dynamic "Latest Posts" & "Related Posts" 2-Column Table
    if all_active_posts:
        latest_job_posts = [p for p in all_active_posts if p.get('category') == 'latest-jobs']
        if len(latest_job_posts) < 5:
            latest_job_posts = all_active_posts
            
        related_result_posts = [p for p in all_active_posts if p.get('category') in ['result', 'admit-card', 'answer-key', 'admission']]
        if len(related_result_posts) < 5:
            related_result_posts = [p for p in all_active_posts if p not in latest_job_posts[:6]]
            if len(related_result_posts) < 5:
                related_result_posts = all_active_posts

        for tbl in soup.find_all('table'):
            tbl_text = tbl.get_text()
            if 'Latest Posts' in tbl_text and 'Related Posts' in tbl_text:
                for td in tbl.find_all('td'):
                    h3_tag = td.find(['h3', 'h4', 'strong'])
                    if h3_tag and 'Latest Posts' in h3_tag.get_text():
                        for old_p in td.find_all('p'):
                            old_p.decompose()
                        for lp in latest_job_posts[:6]:
                            new_p = soup.new_tag('p')
                            p_a = soup.new_tag('a', href=f"/{lp['slug']}/")
                            p_a.string = lp.get('title', '')
                            new_p.append(p_a)
                            td.append(new_p)
                    elif h3_tag and 'Related Posts' in h3_tag.get_text():
                        for old_p in td.find_all('p'):
                            old_p.decompose()
                        for rp in related_result_posts[:6]:
                            new_p = soup.new_tag('p')
                            p_a = soup.new_tag('a', href=f"/{rp['slug']}/")
                            p_a.string = rp.get('title', '')
                            new_p.append(p_a)
                            td.append(new_p)
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

        c08 = soup.find(class_='gb-container-08c3e704')
        if c08:
            info_btn = soup.new_tag('div', style='text-align:center; margin:10px 0; display:flex; justify-content:center; gap:8px; flex-wrap:wrap;')
            info_btn.append(BeautifulSoup("<button class='alria-edit-btn' onclick=\"openModal('modal-top-pages')\">✏️ Edit Top Pages Table (15 Links)</button><button class='alria-edit-btn' onclick=\"openModal('modal-info-sections')\">✏️ Edit 5 Info Sections</button><button class='alria-edit-btn' onclick=\"openModal('modal-faq-items')\">✏️ Edit FAQs</button>", 'html.parser'))
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
                <button onclick="openModal('modal-top-pages')" style="background:#10b981; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">📑 Top Pages Table</button>
                <button onclick="openModal('modal-grid-titles')" style="background:#7c3aed; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">📊 6 Grid Titles</button>
                <button onclick="openModal('modal-info-sections')" style="background:#059669; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">ℹ️ 5 Info Sections</button>
                <button onclick="openModal('modal-faq-items')" style="background:#0284c7; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">❓ FAQs</button>
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

        <!-- 3b. Top Study Topper Pages Table Modal -->
        <div id="modal-top-pages" class="alria-modal-backdrop">
            <div class="alria-modal-card" style="max-width:800px;">
                <h3>📑 Edit Top Study Topper Pages Table (15 Links &amp; Texts)</h3>
                <p style="font-size:12px; color:#64748b; margin:4px 0 12px 0;">Manage text and hyperlinks for the 15 cells displayed in the 3x5 matrix below the star header.</p>
                <div id="top-pages-container" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;"></div>
                <div class="alria-modal-actions">
                    <button class="alria-btn-cancel" onclick="closeModal('modal-top-pages')">Cancel</button>
                    <button class="alria-btn-save" onclick="saveTopPages()">Save Top Pages Table</button>
                </div>
            </div>
        </div>

        <!-- 3c. 5 Red Info Sections Modal -->
        <div id="modal-info-sections" class="alria-modal-backdrop">
            <div class="alria-modal-card" style="max-width:780px;">
                <h3>ℹ️ Edit 5 Homepage Info Sections</h3>
                <p style="font-size:12px; color:#64748b; margin:4px 0 12px 0;">Customize titles and descriptive text paragraphs for the 5 red banner sections.</p>
                <div id="info-sections-container"></div>
                <div class="alria-modal-actions">
                    <button class="alria-btn-cancel" onclick="closeModal('modal-info-sections')">Cancel</button>
                    <button class="alria-btn-save" onclick="saveInfoSections()">Save Info Sections</button>
                </div>
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

        <!-- 5. FAQ Modal -->
        <div id="modal-faq-items" class="alria-modal-backdrop">
            <div class="alria-modal-card" style="max-width:750px;">
                <h3>❓ Edit Frequently Asked Questions (FAQs)</h3>
                <p style="font-size:12px; color:#64748b; margin:4px 0 12px 0;">Add, modify, or remove FAQ questions and answers.</p>
                <div id="faq-list-container"></div>
                <button onclick="addNewFaqItem()" style="background:#0891b2; color:#fff; border:none; padding:6px 12px; border-radius:4px; font-size:12px; font-weight:700; cursor:pointer; margin-top:8px;">+ Add New FAQ Question</button>
                <div class="alria-modal-actions">
                    <button class="alria-btn-cancel" onclick="closeModal('modal-faq-items')">Cancel</button>
                    <button class="alria-btn-save" onclick="saveFaqItems()">Save FAQs</button>
                </div>
            </div>
        </div>

        <!-- 6. Full Footer & Socials Modal -->
        <div id="modal-footer-socials" class="alria-modal-backdrop">
            <div class="alria-modal-card" style="max-width:780px;">
                <h3>🔗 Edit Full Website Footer &amp; Social Channels</h3>
                
                <!-- Section 1: Connect Box -->
                <h4 style="margin:14px 0 8px; color:#2563eb; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">1. Connect Section Heading &amp; Social Channels</h4>
                <div class="alria-input-group">
                    <label>Connect Box Title (e.g. Connect With Us)</label>
                    <input type="text" id="foot-connect-title" value="{settings.get('footer', {}).get('connect_title', 'Connect With Us')}">
                </div>
                
                <div style="margin-top:10px;">
                    <label style="font-size:12px; font-weight:700; color:#475569; margin-bottom:6px; display:block;">Social Channel Buttons (Button Label + URL)</label>
                    <div id="footer-socials-container"></div>
                    <button type="button" onclick="addNewSocialLink()" style="background:#0284c7; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-size:12px; font-weight:700; cursor:pointer; margin-top:6px;">+ Add Social Channel</button>
                </div>

                <!-- Section 2: Bottom Navigation Links -->
                <h4 style="margin:18px 0 8px; color:#059669; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">2. Bottom Navigation Links</h4>
                <div id="footer-nav-container"></div>
                <button type="button" onclick="addNewNavLink()" style="background:#059669; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-size:12px; font-weight:700; cursor:pointer; margin-top:6px;">+ Add Nav Link</button>

                <!-- Section 3: Copyright Text -->
                <h4 style="margin:18px 0 8px; color:#d97706; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">3. Copyright &amp; Disclaimer Notice</h4>
                <div class="alria-input-group">
                    <label>Copyright &amp; Guidance Paragraph Text</label>
                    <textarea id="f-copyright-text" rows="3">{settings.get('footer', {}).get('copyright_text') or s_footer_text}</textarea>
                </div>
                
                <!-- Section 4: Footer Colors -->
                <h4 style="margin:16px 0 8px; color:#7c3aed; font-size:14px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;">4. Footer Colors</h4>
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

                <div class="alria-modal-actions">
                    <button class="alria-btn-cancel" onclick="closeModal('modal-footer-socials')">Cancel</button>
                    <button class="alria-btn-save" onclick="saveFooterSocials()">Save Full Footer</button>
                </div>
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

            function renderTopPagesInputs() {{
                const cont = document.getElementById('top-pages-container'); if(!cont) return; cont.innerHTML = '';
                const pages = siteSettings.top_pages_table || [];
                const defaultPages = [
                    {{"text": "Bharat Result", "url": "/result/"}},
                    {{"text": "UP Police Result", "url": "/up-police-constable-result-2024/"}},
                    {{"text": "Bihar Police Result", "url": "/bihar-police-constable-result-2024/"}},
                    {{"text": "Study Topper Exam", "url": "/latest-jobs/"}},
                    {{"text": "Study Topper Hindi", "url": "/"}},
                    {{"text": "Study Topper NTPC", "url": "/railway-rrb-alp-2026/"}},
                    {{"text": "Study Topper 2026", "url": "/latest-jobs/"}},
                    {{"text": "Study Topper", "url": "/"}},
                    {{"text": "Study Topper Center", "url": "/"}},
                    {{"text": "Sarkari Naukri", "url": "/latest-jobs/"}},
                    {{"text": "Study Topper 10th", "url": "/latest-jobs/"}},
                    {{"text": "Study Topper SSC", "url": "/ssc-chsl-2026/"}},
                    {{"text": "Study Topper 10+2", "url": "/latest-jobs/"}},
                    {{"text": "StudyTopper.in", "url": "/"}},
                    {{"text": "Study Topper Railway", "url": "/railway-nfr-2026/"}}
                ];
                for(let i=0; i<15; i++) {{
                    const p = pages[i] || defaultPages[i] || {{text: '', url: ''}};
                    cont.innerHTML += `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:4px; padding:6px 8px;">
                        <label style="font-size:11px; font-weight:700; color:#334155;">Cell ${{i+1}}</label>
                        <input type="text" id="top-page-text-${{i}}" value="${{p.text || ''}}" placeholder="Link Text" style="margin-bottom:4px; font-size:12px;">
                        <input type="text" id="top-page-url-${{i}}" value="${{p.url || ''}}" placeholder="URL (e.g. /result/)" style="font-size:11px;">
                    </div>`;
                }}
            }}
            renderTopPagesInputs();

            function saveTopPages() {{
                const pages = [];
                for(let i=0; i<15; i++) {{
                    const tEl = document.getElementById('top-page-text-' + i);
                    const uEl = document.getElementById('top-page-url-' + i);
                    if(tEl) {{
                        pages.push({{ text: tEl.value.trim(), url: uEl ? uEl.value.trim() : '' }});
                    }}
                }}
                saveSettingsPayload({{ top_pages_table: pages }});
            }}

            function renderInfoSectionsInputs() {{
                const cont = document.getElementById('info-sections-container'); if(!cont) return; cont.innerHTML = '';
                const defaultSecs = [
                    {{ "title": "Study Topper 10+2 & Graduate Latest Jobs 2026", "content": "Find verified updates for 10+2 Intermediate and graduate government vacancies across India. StudyTopper.in provides direct official application links, notification PDFs, eligibility criteria, age relaxation, syllabus downloads, and deadline alerts for Railway RRB, SSC CHSL, Defence, Police Bharti, and state recruitment boards updated daily." }},
                    {{ "title": "Study Topper Results 2026", "content": "Study Topper Results: Study Topper (studytopper.in) delivers instant, verified alerts for central and state government examination results, provisional answer keys, scorecards, cutoff marks, and merit lists. Candidates across all states rely on our fast servers to check their selection status without delay." }},
                    {{ "title": "Study Topper Bihar & Northern State Vacancies", "content": "Get comprehensive recruitment coverage for Bihar and Northern states including BPSC TRE School Teacher, Bihar Police Constable, CSBC Operator, Bihar STET, BSSC Inter Level, OFSS Intermediate Admission, and High Court recruitment forms, exam schedules, and results updated in real-time." }},
                    {{ "title": "Study Topper Hindi & Regional Language Portal", "content": "Uttar Pradesh (UP Board, UPPSC, UPSSSC) and Hindi-medium aspirants receive clear, step-by-step guidance on online application procedures, eligibility rules, syllabus breakdowns, and exam dates in simple Hindi and English for maximum ease and accessibility." }},
                    {{ "title": "StudyTopper.in Official Information & Disclaimer", "content": "studytopper.in is the official portal of Study Topper™ (Since 2026), presenting all latest career notices, employment news, admit card releases, exam keys, and direct online application links for job aspirants across India." }}
                ];
                const secs = (siteSettings.info_sections && siteSettings.info_sections.length) ? siteSettings.info_sections : defaultSecs;
                secs.forEach((sec, idx) => {{
                    cont.innerHTML += `
                    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px; margin-bottom:10px;">
                        <label style="font-size:12px; font-weight:700; color:#a80909;">Section ${{idx+1}} Title</label>
                        <input type="text" id="info-title-${{idx}}" value="${{sec.title || ''}}" style="margin-bottom:6px; font-size:13px; font-weight:600;">
                        <label style="font-size:12px; font-weight:700; color:#334155;">Section ${{idx+1}} Content Paragraph</label>
                        <textarea id="info-content-${{idx}}" rows="3" style="font-size:12px;">${{sec.content || ''}}</textarea>
                    </div>`;
                }});
            }}
            renderInfoSectionsInputs();

            function saveInfoSections() {{
                const secs = [];
                for(let i=0; i<5; i++) {{
                    const tEl = document.getElementById('info-title-' + i);
                    const cEl = document.getElementById('info-content-' + i);
                    if(tEl) {{
                        secs.push({{ title: tEl.value.trim(), content: cEl ? cEl.value.trim() : '' }});
                    }}
                }}
                saveSettingsPayload({{ info_sections: secs }});
            }}

            function renderFaqInputs() {{
                const cont = document.getElementById('faq-list-container'); if(!cont) return; cont.innerHTML = '';
                const faqs = siteSettings.faq_items || [];
                faqs.forEach((faq, idx) => {{
                    cont.innerHTML += `
                    <div style="border:1px solid #e2e8f0; padding:10px; border-radius:6px; margin-bottom:10px; background:#f8fafc;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                            <label style="font-size:12px; font-weight:700; color:#a80909;">Question ${{idx+1}}</label>
                            <button type="button" onclick="removeFaqItem(${{idx}})" style="background:#ef4444; color:#fff; border:none; border-radius:3px; padding:2px 6px; font-size:11px; cursor:pointer;">🗑️ Remove</button>
                        </div>
                        <input type="text" id="faq-q-${{idx}}" value="${{faq.q || ''}}" style="margin-bottom:6px; font-size:13px;">
                        <label style="font-size:12px; font-weight:700; color:#077822;">Answer ${{idx+1}}</label>
                        <textarea id="faq-a-${{idx}}" rows="2" style="font-size:12px;">${{faq.a || ''}}</textarea>
                    </div>`;
                }});
            }}
            renderFaqInputs();

            function addNewFaqItem() {{
                if(!siteSettings.faq_items) siteSettings.faq_items = [];
                siteSettings.faq_items.push({{q: "New Question Title", a: "Answer text goes here..."}});
                renderFaqInputs();
            }}

            function removeFaqItem(idx) {{
                if(siteSettings.faq_items && siteSettings.faq_items.length > idx) {{
                    siteSettings.faq_items.splice(idx, 1);
                    renderFaqInputs();
                }}
            }}

            function saveFaqItems() {{
                const items = [];
                const faqs = siteSettings.faq_items || [];
                for(let i=0; i<faqs.length; i++) {{
                    const qEl = document.getElementById('faq-q-' + i);
                    const aEl = document.getElementById('faq-a-' + i);
                    if(qEl) {{
                        items.push({{ q: qEl.value.trim(), a: aEl ? aEl.value.trim() : '' }});
                    }}
                }}
                saveSettingsPayload({{ faq_items: items }});
            }}

            async function saveSettingsPayload(payload) {{
                const res = await fetch('/api/admin/save-settings', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
                if(res.ok) {{ alert('Saved successfully!'); location.reload(); }} else {{ alert('Error saving settings'); }}
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

            function renderFooterSocialsInputs() {{
                const cont = document.getElementById('footer-socials-container'); if(!cont) return; cont.innerHTML = '';
                const defaultSoc = [
                    {{ name: 'Study Topper @X', url: siteSettings.socials?.twitter || 'https://x.com/' }},
                    {{ name: 'Study Topper @Telegram', url: siteSettings.socials?.telegram || 'https://t.me/' }},
                    {{ name: 'Study Topper @WhatsApp', url: siteSettings.socials?.whatsapp || 'https://whatsapp.com/' }},
                    {{ name: 'Study Topper @Instagram', url: siteSettings.socials?.instagram || 'https://instagram.com/' }},
                    {{ name: 'Study Topper @Facebook', url: siteSettings.socials?.facebook || 'https://facebook.com/' }},
                    {{ name: 'Study Topper @YouTube', url: siteSettings.socials?.youtube || 'https://youtube.com/' }}
                ];
                const socList = (siteSettings.footer && siteSettings.footer.social_links && siteSettings.footer.social_links.length) ? siteSettings.footer.social_links : defaultSoc;
                socList.forEach((item, idx) => {{
                    cont.innerHTML += `
                    <div style="display:grid; grid-template-columns:1fr 1fr 60px; gap:8px; margin-bottom:6px; background:#f8fafc; padding:6px 8px; border-radius:4px; align-items:center;">
                        <input type="text" id="foot-soc-name-${{idx}}" value="${{item.name || ''}}" placeholder="Button Label (e.g. Study Topper @X)" style="font-size:12px;">
                        <input type="text" id="foot-soc-url-${{idx}}" value="${{item.url || ''}}" placeholder="URL (e.g. https://x.com/)" style="font-size:12px;">
                        <button type="button" onclick="removeSocialLink(${{idx}})" style="background:#ef4444; color:#fff; border:none; border-radius:3px; padding:4px 6px; font-size:11px; cursor:pointer;">🗑️</button>
                    </div>`;
                }});
            }}
            renderFooterSocialsInputs();

            function addNewSocialLink() {{
                if(!siteSettings.footer) siteSettings.footer = {{}};
                if(!siteSettings.footer.social_links) siteSettings.footer.social_links = [];
                siteSettings.footer.social_links.push({{ name: 'New Social Channel', url: 'https://' }});
                renderFooterSocialsInputs();
            }}

            function removeSocialLink(idx) {{
                if(!siteSettings.footer) siteSettings.footer = {{}};
                if(!siteSettings.footer.social_links) siteSettings.footer.social_links = [
                    {{ name: 'Study Topper @X', url: 'https://x.com/' }},
                    {{ name: 'Study Topper @Telegram', url: 'https://t.me/' }},
                    {{ name: 'Study Topper @WhatsApp', url: 'https://whatsapp.com/' }},
                    {{ name: 'Study Topper @Instagram', url: 'https://instagram.com/' }},
                    {{ name: 'Study Topper @Facebook', url: 'https://facebook.com/' }},
                    {{ name: 'Study Topper @YouTube', url: 'https://youtube.com/' }}
                ];
                siteSettings.footer.social_links.splice(idx, 1);
                renderFooterSocialsInputs();
            }}

            function renderFooterNavInputs() {{
                const cont = document.getElementById('footer-nav-container'); if(!cont) return; cont.innerHTML = '';
                const defaultNav = [
                    {{ label: 'Home', url: '/' }},
                    {{ label: 'Contact', url: '/contact/' }},
                    {{ label: 'Privacy Policy', url: '/privacy-policy/' }},
                    {{ label: 'Disclaimer', url: '/disclaimer/' }}
                ];
                const navList = (siteSettings.footer && siteSettings.footer.nav_links && siteSettings.footer.nav_links.length) ? siteSettings.footer.nav_links : defaultNav;
                navList.forEach((item, idx) => {{
                    cont.innerHTML += `
                    <div style="display:grid; grid-template-columns:1fr 1fr 60px; gap:8px; margin-bottom:6px; background:#f8fafc; padding:6px 8px; border-radius:4px; align-items:center;">
                        <input type="text" id="foot-nav-lbl-${{idx}}" value="${{item.label || ''}}" placeholder="Link Label" style="font-size:12px;">
                        <input type="text" id="foot-nav-url-${{idx}}" value="${{item.url || ''}}" placeholder="URL (e.g. /contact/)" style="font-size:12px;">
                        <button type="button" onclick="removeNavLink(${{idx}})" style="background:#ef4444; color:#fff; border:none; border-radius:3px; padding:4px 6px; font-size:11px; cursor:pointer;">🗑️</button>
                    </div>`;
                }});
            }}
            renderFooterNavInputs();

            function addNewNavLink() {{
                if(!siteSettings.footer) siteSettings.footer = {{}};
                if(!siteSettings.footer.nav_links) siteSettings.footer.nav_links = [];
                siteSettings.footer.nav_links.push({{ label: 'New Link', url: '/' }});
                renderFooterNavInputs();
            }}

            function removeNavLink(idx) {{
                if(!siteSettings.footer) siteSettings.footer = {{}};
                if(!siteSettings.footer.nav_links) siteSettings.footer.nav_links = [
                    {{ label: 'Home', url: '/' }},
                    {{ label: 'Contact', url: '/contact/' }},
                    {{ label: 'Privacy Policy', url: '/privacy-policy/' }},
                    {{ label: 'Disclaimer', url: '/disclaimer/' }}
                ];
                siteSettings.footer.nav_links.splice(idx, 1);
                renderFooterNavInputs();
            }}

            function saveFooterSocials() {{
                const connectTitle = document.getElementById('foot-connect-title').value.trim();
                const copyText = document.getElementById('f-copyright-text').value.trim();
                const socList = [];
                const socInputs = document.querySelectorAll('[id^="foot-soc-name-"]');
                socInputs.forEach((el, idx) => {{
                    const nEl = document.getElementById('foot-soc-name-' + idx);
                    const uEl = document.getElementById('foot-soc-url-' + idx);
                    if(nEl && uEl && nEl.value.trim()) {{
                        socList.push({{ name: nEl.value.trim(), url: uEl.value.trim() }});
                    }}
                }});

                const navList = [];
                const navInputs = document.querySelectorAll('[id^="foot-nav-lbl-"]');
                navInputs.forEach((el, idx) => {{
                    const lEl = document.getElementById('foot-nav-lbl-' + idx);
                    const uEl = document.getElementById('foot-nav-url-' + idx);
                    if(lEl && uEl && lEl.value.trim()) {{
                        navList.push({{ label: lEl.value.trim(), url: uEl.value.trim() }});
                    }}
                }});

                const footerPayload = {{
                    connect_title: connectTitle,
                    social_links: socList,
                    nav_links: navList,
                    copyright_text: copyText
                }};

                saveSettingsPayload({{
                    footer: footerPayload,
                    footer_text: copyText,
                    theme_colors: {{
                        footer_bg: document.getElementById('f-bg').value,
                        footer_text: document.getElementById('f-txt').value
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

# Favicon & Static Asset Handlers
@app.route('/favicon.ico')
@app.route('/favicon.png')
def serve_favicon():
    for f in [
        os.path.join(WP_CONTENT_DIR, 'uploads', '2025', '06', '512px512px-150x150.png'),
        os.path.join(BASE_DIR, 'raw_clone', 'wp-content', 'uploads', '2025', '06', '512px512px-150x150.png')
    ]:
        if os.path.exists(f):
            return send_from_directory(os.path.dirname(f), os.path.basename(f), mimetype='image/png')
    return Response(b'', mimetype='image/x-icon')

@app.route('/cdn-cgi/scripts/<path:filepath>')
def serve_cdn_cgi(filepath):
    return Response('/* cdn-cgi mock */', mimetype='application/javascript')

@app.route('/wp-content/<path:filepath>')
def serve_wp_content(filepath):
    clean_filepath = filepath.split('?')[0]
    for base in [WP_CONTENT_DIR, os.path.join(BASE_DIR, 'raw_clone', 'wp-content'), os.path.join(BASE_DIR, 'static')]:
        target = os.path.join(base, clean_filepath)
        if os.path.exists(target) and os.path.isfile(target):
            return send_from_directory(os.path.dirname(target), os.path.basename(target))
    if clean_filepath.endswith('.css'):
        return Response('/* fallback */', mimetype='text/css')
    elif clean_filepath.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico')):
        return Response(b'', mimetype='image/png')
    elif clean_filepath.endswith(('.js', '.mjs')):
        return Response('/* fallback js */', mimetype='application/javascript')
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

def render_dynamic_homepage_html(raw_html, host, is_alria_mode=False):
    soup = BeautifulSoup(raw_html, 'html.parser')
    all_posts = load_all_active_posts()
    
    today = datetime.now().date()
    config = lifecycle.load_lifecycle_settings()
    urgent_threshold = int(config.get('urgent_days_threshold', 3))
    pinned_set = set(config.get('pinned_posts', []))
    
    posts_by_category = {}
    for p in all_posts:
        cat = p.get('category', 'latest-jobs')
        slug = p.get('slug')
        last_date_str = p.get('application_last_date', '')
        title = p.get('title', '')
        is_pinned = (slug in pinned_set)
        p['is_pinned'] = is_pinned
        
        is_extended = 'extend' in last_date_str.lower() or 'extend' in title.lower() or p.get('custom_badge') == 'Date Extended'
        parsed_date = lifecycle.parse_date_string(last_date_str)
        
        days_remaining = (parsed_date - today).days if parsed_date else None
        
        if days_remaining is not None:
            if days_remaining < 0:
                p_state = 'EXPIRED'
                p_badge = ''
                p_priority = -1000 + days_remaining
            elif is_pinned:
                p_state = 'URGENT_PINNED'
                badge_text = "Date Extended!" if is_extended else ("Last Date Today!" if days_remaining == 0 else f"{days_remaining} Days Left!")
                p_badge = f' - <span class="agy-blinking-badge {"agy-extended-blink" if is_extended else "agy-urgent-blink"}">{badge_text}</span>'
                p_priority = 100000 - min(days_remaining, 10)
            elif days_remaining <= urgent_threshold:
                p_state = 'URGENT'
                txt = "Last Date Today!" if days_remaining == 0 else f"{days_remaining} Days Left!"
                p_badge = f' - <span class="agy-blinking-badge agy-urgent-blink">{txt}</span>'
                p_priority = 10000 - days_remaining
            else:
                p_state = 'ACTIVE'
                if is_extended:
                    p_badge = ' - <span class="agy-blinking-badge agy-extended-blink">Date Extended!</span>'
                    p_priority = 5000 - min(days_remaining, 30)
                else:
                    p_badge = ''
                    p_priority = 100 - min(days_remaining, 90)
        else:
            if is_pinned:
                p_state = 'URGENT_PINNED'
                p_badge = ' - <span class="agy-blinking-badge agy-urgent-blink">Important!</span>'
                p_priority = 100000
            elif is_extended:
                p_state = 'ACTIVE'
                p_badge = ' - <span class="agy-blinking-badge agy-extended-blink">Date Extended!</span>'
                p_priority = 4000
            else:
                p_state = 'ACTIVE'
                p_badge = ''
                p_priority = 50
                
        p['calculated_badge'] = p_badge
        p['calculated_priority'] = p_priority
        p['is_pinned'] = is_pinned
        
        if cat not in posts_by_category:
            posts_by_category[cat] = []
        posts_by_category[cat].append(p)
        
    for cat in posts_by_category:
        posts_by_category[cat].sort(key=lambda x: x.get('calculated_priority', 0), reverse=True)
        
    # Inject blinking CSS in head
    if not soup.find(id='agy-lifecycle-blink-css'):
        if soup.head:
            soup.head.append(BeautifulSoup(lifecycle.BLINKING_CSS, 'html.parser'))
            
    # Inject into the 6 category boxes
    category_column_map = {
        'gb-grid-column-0b76599a': 'result',
        'gb-grid-column-c7488d9a': 'latest-jobs',
        'gb-grid-column-e64d3148': 'admit-card',
        'gb-grid-column-d19ddc59': 'answer-key',
        'gb-grid-column-b48dca36': 'syllabus',
        'gb-grid-column-51daea0e': 'admission'
    }
    
    for col_cls, cat_key in category_column_map.items():
        col = soup.find(class_=col_cls)
        if col:
            ul = col.find('ul')
            if ul:
                ul.clear()
                cat_list = posts_by_category.get(cat_key, [])
                for item in cat_list[:12]:
                    li = soup.new_tag('li')
                    title_raw = item.get('title', '')
                    badge_html = item.get('calculated_badge', '')
                    markup = f'<a href="/{item.get("slug")}/" class="wp-block-latest-posts__post-title">{title_raw}{badge_html}</a>'
                    li.append(BeautifulSoup(markup, 'html.parser'))
                    ul.append(li)
    return sanitize_html(str(soup), host, is_alria_mode=is_alria_mode)

@app.route('/')
@app.route('/alria')
@app.route('/alria/')
def home():
    search_q = request.args.get('s') or request.args.get('q')
    if search_q:
        return redirect(f'/search?q={search_q}')

    is_alria = (request.path in ['/alria', '/alria/']) or (request.args.get('alria') == '1')
    index_file = os.path.join(PAGES_DIR, 'index.html')
    if not os.path.exists(index_file):
        index_file = os.path.join(BASE_DIR, 'original_index.html')
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        sanitized = render_dynamic_homepage_html(content, request.host, is_alria_mode=is_alria)
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
    if clean_slug.startswith('api/') or clean_slug.startswith('admin/') or clean_slug.startswith('tools/') or clean_slug in ['favicon.ico', 'robots.txt', 'sitemap.xml', 'ads.txt', 'alria', 'admin', 'search', 'post-preview', 'post-design-preview']:
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

    alias_map = {
        'terms': 'terms-and-conditions',
        'about': 'about-us'
    }
    target_slug = alias_map.get(clean_slug, clean_slug)

    # 2. Exact Scraped / Saved Post Page in PAGES_DIR, raw_clone, or templates
    for dir_path in [PAGES_DIR, os.path.join(BASE_DIR, 'raw_clone', 'pages'), os.path.join(BASE_DIR, 'templates')]:
        page_file = os.path.join(dir_path, f"{target_slug}.html")
        if os.path.exists(page_file) and target_slug != 'index':
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()
            return Response(sanitize_html(content, request.host), mimetype='text/html')

    # 3. Dynamic User-Created Single Post Routing
    for p in all_posts:
        if p.get('slug') == clean_slug or p.get('id') == clean_slug or p.get('slug') == target_slug:
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
            target_post = dict(p)
            break
    
    slug = target_post.get('slug', post_id) if target_post else post_id
    
    # Extract HTML body content from pages/{slug}.html
    html_content = ''
    for dir_path in [PAGES_DIR, os.path.join(BASE_DIR, 'raw_clone', 'pages'), os.path.join(BASE_DIR, 'templates')]:
        page_file = os.path.join(dir_path, f"{slug}.html")
        if os.path.exists(page_file):
            try:
                with open(page_file, 'r', encoding='utf-8') as f:
                    raw_html = f.read()
                soup = BeautifulSoup(raw_html, 'html.parser')
                main = soup.find('main') or soup.find(class_='entry-content') or soup.find('article')
                if main:
                    html_content = ''.join(str(c) for c in main.contents).strip()
                else:
                    html_content = raw_html
                break
            except Exception:
                pass

    if not target_post:
        target_post = {
            'id': post_id,
            'title': post_id.replace('-', ' ').title(),
            'slug': slug,
            'category': 'latest-jobs',
            'application_start_date': '01 August 2026',
            'application_last_date': '30 August 2026',
            'is_date_extended': False,
            'is_pinned': False,
            'custom_badge': '',
            'short_desc': '',
            'tags': '',
            'html_content': html_content
        }
    else:
        target_post['html_content'] = html_content or target_post.get('html_content', '')
        
    return render_template('admin/post_form.html', settings=settings, post=target_post)

@app.route('/admin/categories')
def admin_categories():
    settings = load_settings()
    return render_template('admin/categories.html', settings=settings)

@app.route('/admin/settings')
def admin_settings():
    settings = load_settings()
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/lifecycle')
def admin_lifecycle():
    settings = load_settings()
    config = lifecycle.load_lifecycle_settings()
    custom_posts = load_custom_posts()
    pinned_set = set(config.get('pinned_posts', []))
    urgent_threshold = int(config.get('urgent_days_threshold', 3))
    
    urgent_posts = []
    extended_posts = []
    pinned_posts_list = []
    
    for p in custom_posts:
        slug = p.get('slug')
        is_pin = slug in pinned_set or p.get('is_pinned', False)
        p['is_pinned'] = is_pin
        
        days_rem = p.get('days_remaining')
        is_ext = 'extend' in (p.get('application_last_date', '') + p.get('title', '') + str(p.get('custom_badge', ''))).lower()
        
        # Strict threshold check: Only posts <= urgent_threshold days left
        if days_rem is not None and 0 <= days_rem <= urgent_threshold:
            urgent_posts.append(p)
        if is_ext:
            extended_posts.append(p)
        if is_pin:
            pinned_posts_list.append(p)
            
    urgent_count = len(urgent_posts)
    expired_count = sum(1 for p in custom_posts if p.get('lifecycle_state') == 'EXPIRED_DEMOTED')
    
    return render_template(
        'admin/lifecycle.html',
        settings=settings,
        config=config,
        posts=custom_posts,
        urgent_posts=urgent_posts,
        extended_posts=extended_posts,
        pinned_posts=pinned_posts_list,
        pinned_slugs=list(pinned_set),
        total_posts=len(custom_posts),
        urgent_count=urgent_count,
        expired_count=expired_count
    )

@app.route('/api/admin/pin-post/<slug>', methods=['GET', 'POST'])
@app.route('/api/admin/pin-post/<slug>/', methods=['GET', 'POST'])
def api_pin_post(slug):
    try:
        lifecycle.pin_post(slug)
        return jsonify({"success": True, "slug": slug, "is_pinned": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/unpin-post/<slug>', methods=['GET', 'POST'])
@app.route('/api/admin/unpin-post/<slug>/', methods=['GET', 'POST'])
def api_unpin_post(slug):
    try:
        lifecycle.unpin_post(slug)
        return jsonify({"success": True, "slug": slug, "is_pinned": False})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/toggle-pin-post/<slug>', methods=['GET', 'POST'])
@app.route('/api/admin/toggle-pin-post/<slug>/', methods=['GET', 'POST'])
def api_toggle_pin_post(slug):
    try:
        is_pinned = lifecycle.toggle_pin_post(slug)
        return jsonify({"success": True, "slug": slug, "is_pinned": is_pinned})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/lifecycle-run', methods=['GET', 'POST'])
@app.route('/api/admin/lifecycle-run/', methods=['GET', 'POST'])
def api_lifecycle_run():
    try:
        res = lifecycle.audit_and_execute_lifecycle()
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/lifecycle-save-config', methods=['GET', 'POST'])
@app.route('/api/admin/lifecycle-save-config/', methods=['GET', 'POST'])
def api_lifecycle_save_config():
    if request.method == 'GET':
        return redirect('/admin/lifecycle')
    try:
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form.to_dict()
        
        config = lifecycle.load_lifecycle_settings()
        for k, v in data.items():
            if isinstance(v, str) and v.lower() == 'true':
                config[k] = True
            elif isinstance(v, str) and v.lower() == 'false':
                config[k] = False
            elif isinstance(v, str) and v.isdigit():
                config[k] = int(v)
            else:
                config[k] = v
        
        lifecycle.save_lifecycle_settings(config)
        res = lifecycle.audit_and_execute_lifecycle()
        return jsonify({"success": True, "config": config, "audit": res})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

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
            if k == 'socials' and isinstance(v, dict):
                if 'socials' not in settings: settings['socials'] = {}
                settings['socials'].update(v)
            elif k.startswith('social_'):
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

        # Parse form collections if submitted via regular HTML form
        if not request.is_json:
            # 1. top_pages_table
            form_top_pages = []
            has_top_pages = False
            for i in range(15):
                t_k = f'top_pages_text_{i}'
                u_k = f'top_pages_url_{i}'
                if t_k in data or u_k in data:
                    has_top_pages = True
                    form_top_pages.append({
                        'text': data.get(t_k, '').strip(),
                        'url': data.get(u_k, '').strip()
                    })
            if has_top_pages:
                settings['top_pages_table'] = form_top_pages

            # 2. info_sections
            form_info_secs = []
            has_info_secs = False
            for i in range(5):
                t_k = f'info_title_{i}'
                c_k = f'info_content_{i}'
                if t_k in data or c_k in data:
                    has_info_secs = True
                    form_info_secs.append({
                        'title': data.get(t_k, '').strip(),
                        'content': data.get(c_k, '').strip()
                    })
            # 4. footer form parsing
            if any(k.startswith('footer_') for k in data):
                footer_cfg = settings.get('footer', {})
                if 'footer_connect_title' in data:
                    footer_cfg['connect_title'] = data['footer_connect_title'].strip()
                if 'footer_copyright_text' in data:
                    footer_cfg['copyright_text'] = data['footer_copyright_text'].strip()
                    settings['footer_text'] = footer_cfg['copyright_text']
                
                soc_list = []
                for i in range(20):
                    n_k = f'footer_soc_name_{i}'
                    u_k = f'footer_soc_url_{i}'
                    if n_k in data and data[n_k].strip():
                        soc_list.append({'name': data[n_k].strip(), 'url': data.get(u_k, '').strip()})
                if soc_list:
                    footer_cfg['social_links'] = soc_list

                nav_list = []
                for i in range(10):
                    l_k = f'footer_nav_lbl_{i}'
                    u_k = f'footer_nav_url_{i}'
                    if l_k in data and data[l_k].strip():
                        nav_list.append({'label': data[l_k].strip(), 'url': data.get(u_k, '').strip()})
                if nav_list:
                    footer_cfg['nav_links'] = nav_list

                settings['footer'] = footer_cfg

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
@app.route('/post-preview')
@app.route('/post-preview/')
@app.route('/post-design-preview')
@app.route('/post-design-preview/')
def post_preview_page():
    preview_file = os.path.join(BASE_DIR, 'post_design_preview.html')
    if not os.path.exists(preview_file):
        preview_file = os.path.join(BASE_DIR, 'sample_post.html')
    if os.path.exists(preview_file):
        with open(preview_file, 'r', encoding='utf-8') as f:
            content = f.read()
        sanitized = sanitize_html(content, request.host)
        return Response(sanitized, mimetype='text/html')
    abort(404)

if __name__ == '__main__':
    print("===================================================================")
    print("Starting STUDY TOPPER PRO PORTAL (PORT 9093)")
    print(" - Official Homepage:     http://127.0.0.1:9093")
    print(" - /alria Visual Editor:  http://127.0.0.1:9093/alria")
    print(" - ads.txt:               http://127.0.0.1:9093/ads.txt")
    print(" - robots.txt:            http://127.0.0.1:9093/robots.txt")
    print(" - sitemap.xml:           http://127.0.0.1:9093/sitemap.xml")
    print(" - Admin Dashboard:       http://127.0.0.1:9093/admin/dashboard")
    print(" - Auto-Lifecycle Engine: http://127.0.0.1:9093/admin/lifecycle")
    print(" - Category Manager:      http://127.0.0.1:9093/admin/categories")
    print(" - SEO & Settings:        http://127.0.0.1:9093/admin/settings")
    print("===================================================================")
    
    # Initialize and start automated vacancy lifecycle background worker
    try:
        lifecycle.start_lifecycle_background_daemon(interval_minutes=60)
        lifecycle.audit_and_execute_lifecycle()
        print(" [OK] Automated Vacancy Lifecycle Background Daemon Started!")
    except Exception as e:
        print(f"Notice: Lifecycle startup warning ({e})")

    app.run(host='0.0.0.0', port=9093, debug=False)
