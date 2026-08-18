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

TARGET_DOMAIN = "sarkariresult.com.cm"

PRIMARY_CATEGORIES = [
    'latest-jobs', 'admit-card', 'result', 'admission', 'syllabus', 'answer-key',
    'certificate-verification', 'important', 'contact', 'disclaimer', 'privacy-policy'
]

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

    # 8. Dynamic Site Name & Tagline
    site_name = settings.get('site_name')
    if site_name:
        if soup.title:
            soup.title.string = f"{site_name} : Sarkari Result Official, Latest Online Form, Result, Admit Card"
        for mt in soup.find_all(class_='main-title'):
            a = mt.find('a')
            if a: a.string = site_name
            else: mt.string = site_name

    tagline = settings.get('tagline')
    if tagline:
        for sd in soup.find_all(class_='site-description'):
            sd.string = tagline

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

    # 11. Dynamic Grid Column Section Titles & Colors
    grid_headers = settings.get('grid_headers', {})
    for col_cls, cat_key in COL_MAPPING.items():
        col_div = soup.find(class_=f'gb-grid-column-{col_cls}')
        if col_div:
            container = col_div.find(class_='gb-container')
            if container:
                h2 = container.find(class_=re.compile(r'gb-headline.*-text'))
                if h2:
                    if cat_key in grid_headers and grid_headers[cat_key].get('title'):
                        h2.string = grid_headers[cat_key].get('title')
                    cat_norm = cat_key.replace('-', '_')
                    col_bg = theme.get(f'{cat_norm}_header_bg') or theme.get('result_header_bg', '#ab183d')
                    col_txt = theme.get(f'{cat_norm}_header_text') or '#ffffff'
                    h2['style'] = f'background-color:{col_bg} !important; color:{col_txt} !important; text-align:center; font-weight:700; padding:6px 0;'

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
                <h3>🏷️ Edit Portal Branding, Banner &amp; Header Color</h3>
                <div class="alria-input-group"><label>Portal Site Name</label><input type="text" id="b-site-name" value="{s_site_name}"></div>
                <div class="alria-input-group"><label>Domain Name</label><input type="text" id="b-domain" value="{s_domain}"></div>
                <div class="alria-input-group"><label>Site Tagline</label><input type="text" id="b-tagline" value="{s_tagline}"></div>
                <div class="alria-input-group"><label>Top Headline Banner Text</label><textarea id="b-top-banner" rows="3">{s_top_banner}</textarea></div>
                
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
                saveSettingsPayload({{
                    site_name: document.getElementById('b-site-name').value,
                    domain: document.getElementById('b-domain').value,
                    tagline: document.getElementById('b-tagline').value,
                    top_banner_text: document.getElementById('b-top-banner').value,
                    theme_colors: {{
                        header_bg: document.getElementById('b-hdr-bg').value,
                        header_text: document.getElementById('b-hdr-txt').value
                    }}
                }});
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
        if 'sarkariresult.com.cm' in href:
            path = href.replace('https://sarkariresult.com.cm', '').replace('http://sarkariresult.com.cm', '')
            a['href'] = path if path else '/'

    return str(soup)

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
    is_alria = (request.path in ['/alria', '/alria/']) or (request.args.get('alria') == '1')
    index_file = os.path.join(PAGES_DIR, 'index.html')
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
        sanitized = sanitize_html(content, request.host, is_alria_mode=is_alria)
        return Response(sanitized, mimetype='text/html')
    abort(404)

# ==================== CLEAN TOP-LEVEL SLUG ROUTING ====================

@app.route('/<path:slug>/')
@app.route('/<path:slug>')
def dynamic_page_router(slug):
    clean_slug = slug.strip('/')
    if clean_slug in ['favicon.ico', 'robots.txt', 'sitemap.xml', 'ads.txt', 'alria', 'admin']:
        abort(404)

    page_file = os.path.join(PAGES_DIR, f"{clean_slug}.html")
    if os.path.exists(page_file):
        with open(page_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(sanitize_html(content, request.host), mimetype='text/html')

    # Live scraper fallback
    try:
        url = f"https://{TARGET_DOMAIN}/{clean_slug}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            cleaned = sanitize_html(res.text, request.host)
            with open(page_file, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            return Response(cleaned, mimetype='text/html')
    except Exception:
        pass

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
    posts = []
    if os.path.exists(PAGES_DIR):
        for fname in os.listdir(PAGES_DIR):
            if fname.endswith('.html') and fname != 'index.html' and fname[:-5] not in PRIMARY_CATEGORIES:
                slug = fname[:-5]
                title = slug.replace('-', ' ').title()
                posts.append({
                    'id': slug,
                    'title': title,
                    'slug': slug,
                    'category': 'latest-jobs',
                    'application_last_date': '2026-09-30',
                    'is_soon': False
                })
    return render_template('admin/posts.html', settings=settings, posts=posts)

@app.route('/admin/posts/new')
def admin_post_new():
    settings = load_settings()
    return render_template('admin/post_form.html', settings=settings, post=None)

@app.route('/admin/posts/edit/<post_id>')
def admin_post_edit(post_id):
    settings = load_settings()
    post_obj = {
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
        'html_content': ''
    }
    page_file = os.path.join(PAGES_DIR, f"{post_id}.html")
    if os.path.exists(page_file):
        with open(page_file, 'r', encoding='utf-8') as f:
            post_obj['html_content'] = f.read()
    return render_template('admin/post_form.html', settings=settings, post=post_obj)

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
            if k in ['google_analytics_id', 'google_site_verification', 'meta_description', 'meta_keywords', 'custom_head_code', 'custom_footer_code']:
                if 'seo' not in settings: settings['seo'] = {}
                settings['seo'][k] = v
            elif k in ['telegram', 'whatsapp', 'youtube', 'instagram', 'facebook', 'twitter']:
                if 'socials' not in settings: settings['socials'] = {}
                settings['socials'][k] = v
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
    html_content = data.get('html_content', '')
    category = data.get('category', 'latest-jobs')
    app_start = data.get('application_start_date', '')
    app_last = data.get('application_last_date', '')
    short_desc = data.get('short_desc', '')
    is_pinned = bool(data.get('is_pinned'))
    is_date_extended = bool(data.get('is_date_extended'))
    custom_badge = data.get('custom_badge', '')

    try:
        page_file = os.path.join(PAGES_DIR, f"{slug}.html")
        with open(page_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        print(f"Notice: Local HTML page write skipped ({e}) - persisting to Supabase.")

    post_item = {
        'id': data.get('id') or f"post_{uuid.uuid4().hex[:8]}",
        'slug': slug,
        'title': title,
        'category': category,
        'short_desc': short_desc,
        'html_content': html_content,
        'application_start_date': app_start,
        'application_last_date': app_last,
        'is_pinned': is_pinned,
        'is_date_extended': is_date_extended,
        'is_temporary': False,
        'custom_badge': custom_badge
    }

    if supa.is_supabase_configured():
        supa.save_post_to_supabase(post_item)

    return redirect('/admin/posts')

@app.route('/api/admin/posts/delete/<post_id>', methods=['POST'])
def api_delete_post(post_id):
    page_file = os.path.join(PAGES_DIR, f"{post_id}.html")
    if os.path.exists(page_file):
        os.remove(page_file)
    
    if supa.is_supabase_configured():
        supa.delete_post_from_supabase(post_id)

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
    print("Starting SARKARI RESULT PRO PORTAL (PORT 9093)")
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
