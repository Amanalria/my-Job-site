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
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'site_name': 'SARKARI RESULT',
        'domain': 'yourdomain.com',
        'tagline': 'Sarkari Result ™ 2026 : Sarkari Naukri, Latest Online Form & Govt Exam Results',
        'top_banner_text': 'Sarkari Result ™ 2026 : find latest Sarkari job vacancies, admit cards, exam dates and Sarkari exam results in one place.',
        'seo': {'google_analytics_id': '', 'google_site_verification': '', 'meta_description': '', 'meta_keywords': '', 'custom_head_code': '', 'custom_footer_code': ''},
        'ads_txt': 'google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0',
        'robots_txt': 'User-agent: *\nDisallow: /admin/\nDisallow: /admin\nDisallow: /alria\nDisallow: /api/\nAllow: /\n\nSitemap: https://yourdomain.com/sitemap.xml',
        'categories': [],
        'marquee_items': [],
        'highlight_cards': [],
        'grid_headers': {},
        'info_sections': [],
        'faq_items': [],
        'footer_text': 'Copyright © 2026. All Rights Reserved.',
        'adsense': {'enabled': False, 'client_id': ''}
    }

def save_settings_data(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def sanitize_html(html_content, current_host, is_alria_mode=False):
    soup = BeautifulSoup(html_content, 'html.parser')
    settings = load_settings()

    # 1. Strip external ads and tracking scripts
    for s in soup.find_all(['script', 'iframe', 'ins']):
        src = s.get('src', '')
        classes = s.get('class', [])
        if any(ad in src.lower() for ad in ['pagead2', 'googlesyndication', 'izooto', 'googletagmanager', 'cloudflare']):
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

    # 7. Exact 3x2 Grid Layout (3 in Row 1, 3 in Row 2)
    center_style = soup.new_tag('style')
    center_style.string = """
    /* 3 Boxes in Row 1, 3 Boxes in Row 2 (100% Exact to Original) */
    .gb-grid-wrapper-180dce95 {
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        gap: 14px !important;
        max-width: 1120px !important;
        margin: 15px auto !important;
        padding: 0 10px !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }
    .gb-grid-wrapper-180dce95 > .gb-grid-column {
        width: 100% !important;
        max-width: 100% !important;
        flex: none !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    .gb-grid-wrapper-180dce95 > .gb-grid-column > .gb-container {
        height: 100% !important;
        margin: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        box-sizing: border-box !important;
    }
    
    /* Top 8 Cards (4 in Row 1, 4 in Row 2) */
    .gb-grid-wrapper-5aaa8125,
    .gb-grid-wrapper-389edcd7 {
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 8px !important;
        max-width: 1120px !important;
        margin: 0 auto 8px auto !important;
        padding: 0 10px !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }
    .gb-grid-wrapper-5aaa8125 > .gb-grid-column,
    .gb-grid-wrapper-389edcd7 > .gb-grid-column {
        width: 100% !important;
        max-width: 100% !important;
        flex: none !important;
        margin: 0 !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }

    @media (max-width: 680px) {
        .gb-grid-wrapper-180dce95 {
            grid-template-columns: 1fr !important;
        }
        .gb-grid-wrapper-5aaa8125,
        .gb-grid-wrapper-389edcd7 {
            grid-template-columns: repeat(2, 1fr) !important;
        }
    }
    .alria-edit-btn {
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
    }
    .alria-edit-btn:hover { background: #dc2626 !important; }
    """
    if soup.head:
        soup.head.append(center_style)

    # 8. Dynamic Banner Text
    top_p = soup.find(class_='gb-headline-d55a09d3')
    if top_p and settings.get('top_banner_text'):
        top_p.string = settings.get('top_banner_text')

    # 9. Dynamic Top 8 Cards
    cards = settings.get('highlight_cards', [])
    if cards:
        card_containers = soup.find_all(class_=re.compile(r'gb-grid-column-(81c81cf2|c2e36bcf|1838ae6f|eef7c02b|62b661d9|2ad1104e|04597b83|a25e1b9b)'))
        for idx, col in enumerate(card_containers[:len(cards)]):
            a_tag = col.find('a')
            if a_tag:
                a_tag['href'] = cards[idx].get('url', '#')
                a_tag.string = cards[idx].get('title', '')

    # 10. Dynamic Grid Column Section Titles
    grid_headers = settings.get('grid_headers', {})
    for col_cls, cat_key in COL_MAPPING.items():
        col_div = soup.find(class_=f'gb-grid-column-{col_cls}')
        if col_div:
            container = col_div.find(class_='gb-container')
            if container:
                h2 = container.find(class_=re.compile(r'gb-headline.*-text'))
                if h2 and cat_key in grid_headers:
                    h2.string = grid_headers[cat_key].get('title', h2.get_text())

    # 11. Dynamic Guidelines & FAQ Block
    c08 = soup.find(class_='gb-container-08c3e704')
    if c08:
        inside = c08.find(class_='gb-inside-container')
        if inside:
            info_secs = settings.get('info_sections', [])
            faq_items = settings.get('faq_items', [])
            if info_secs or faq_items:
                inside.clear()
                for sec in info_secs:
                    h2_tag = soup.new_tag('h2', **{'class': 'gb-headline gb-headline-02a5ae4c gb-headline-text'}, style='background-color:#a80909; color:#fff; padding:6px 10px; margin:15px 0 8px; font-size:16px;')
                    h2_tag.string = sec.get('title', '')
                    inside.append(h2_tag)
                    p_tag = soup.new_tag('p', **{'class': 'has-text-align-center wp-block-paragraph'}, style='padding:8px 12px; font-size:15px; line-height:1.6; text-align:left;')
                    p_tag.string = sec.get('content', '')
                    inside.append(p_tag)
                if faq_items:
                    faq_h2 = soup.new_tag('h2', **{'class': 'gb-headline gb-headline-02a5ae4c gb-headline-text'}, style='background-color:#a80909; color:#fff; padding:6px 10px; margin:15px 0 8px; font-size:16px;')
                    faq_h2.string = "FAQ – Frequently Asked Questions"
                    inside.append(faq_h2)
                    faq_box = soup.new_tag('div', style='padding:10px 12px; margin-bottom:15px;')
                    for i, faq in enumerate(faq_items, 1):
                        qp = soup.new_tag('p', style='text-align:left; margin:10px 0 3px; font-weight:700; color:#a80909; font-size:15px;')
                        qp.append(BeautifulSoup(f"<span style='color:#000;'>Q {i}.</span> {faq.get('q', '')}", 'html.parser'))
                        faq_box.append(qp)
                        ap = soup.new_tag('p', style='text-align:justify; margin:0 0 12px; font-size:14px; line-height:1.5; color:#222;')
                        ap.append(BeautifulSoup(f"<strong style='color:#077822;'>Ans.</strong> {faq.get('a', '')}", 'html.parser'))
                        faq_box.append(ap)
                    inside.append(faq_box)

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

        alria_html = f'''
        <div id="alria-bar" style="position:fixed; top:0; left:0; right:0; z-index:999999; background:rgba(15,23,42,0.96); backdrop-filter:blur(10px); color:#fff; padding:10px 20px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 4px 20px rgba(0,0,0,0.4); border-bottom:2px solid #ef4444; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="background:#ef4444; color:#fff; padding:3px 8px; border-radius:4px; font-weight:800; font-size:12px;">⚡ ALRIA LIVE EDITOR</span>
                <span style="font-size:13px; color:#cbd5e1;">Click any red ✏️ button on the page to edit that section</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <button onclick="openModal('modal-branding')" style="background:#2563eb; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🏷️ Branding</button>
                <button onclick="openModal('modal-cards')" style="background:#0891b2; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🃏 Top 8 Cards</button>
                <button onclick="openModal('modal-grid-titles')" style="background:#7c3aed; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">📊 6 Grid Titles</button>
                <button onclick="openModal('modal-info-faq')" style="background:#059669; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">❓ FAQs &amp; Info</button>
                <button onclick="openModal('modal-footer-socials')" style="background:#d97706; color:#fff; border:none; padding:5px 12px; border-radius:4px; font-weight:700; cursor:pointer; font-size:12px;">🔗 Footer &amp; Socials</button>
                <a href="/admin/dashboard" style="background:#475569; color:#fff; text-decoration:none; padding:5px 12px; border-radius:4px; font-weight:700; font-size:12px;">Admin Panel</a>
                <a href="/" style="background:#ef4444; color:#fff; text-decoration:none; padding:5px 12px; border-radius:4px; font-weight:700; font-size:12px;">Exit Live Mode</a>
            </div>
        </div>

        <style>
            .alria-modal-backdrop {{ display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.65); z-index: 1000000; align-items: center; justify-content: center; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            .alria-modal-card {{ background: #ffffff; border-radius: 8px; width: 92%; max-width: 650px; max-height: 88vh; overflow-y: auto; padding: 24px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25); color: #1e293b; }}
            .alria-modal-card h3 {{ margin-top: 0; font-size: 18px; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; color: #0f172a; }}
            .alria-input-group {{ margin-bottom: 12px; }}
            .alria-input-group label {{ display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #475569; }}
            .alria-modal-card input[type="text"], .alria-modal-card textarea {{ width: 100%; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; box-sizing: border-box; }}
            .alria-modal-actions {{ display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
            .alria-btn-cancel {{ padding: 8px 16px; border: 1px solid #cbd5e1; background: #fff; border-radius: 4px; cursor: pointer; font-weight: 600; }}
            .alria-btn-save {{ padding: 8px 18px; background: #ef4444; color: #fff; border: none; border-radius: 4px; font-weight: 700; cursor: pointer; }}
        </style>

        <div id="modal-branding" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🏷️ Edit Portal Branding &amp; Banner</h3>
                <div class="alria-input-group"><label>Portal Site Name</label><input type="text" id="b-site-name" value="{settings.get('site_name', '')}"></div>
                <div class="alria-input-group"><label>Domain Name</label><input type="text" id="b-domain" value="{settings.get('domain', '')}"></div>
                <div class="alria-input-group"><label>Site Tagline</label><input type="text" id="b-tagline" value="{settings.get('tagline', '')}"></div>
                <div class="alria-input-group"><label>Top Red Headline Banner Text</label><textarea id="b-top-banner" rows="3">{settings.get('top_banner_text', '')}</textarea></div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-branding')">Cancel</button><button class="alria-btn-save" onclick="saveBranding()">Save Changes</button></div>
            </div>
        </div>

        <div id="modal-cards" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🃏 Edit Top 8 Colored Highlight Cards</h3>
                <div id="cards-container"></div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-cards')">Cancel</button><button class="alria-btn-save" onclick="saveCards()">Save All 8 Cards</button></div>
            </div>
        </div>

        <div id="modal-grid-titles" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>📊 Edit 6 Grid Column Section Titles</h3>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                    <div class="alria-input-group"><label>Column 1 (Results)</label><input type="text" id="gt-result" value="{grid_headers.get('result', {}).get('title', 'Result')}"></div>
                    <div class="alria-input-group"><label>Column 2 (Admit Card)</label><input type="text" id="gt-admit" value="{grid_headers.get('admit-card', {}).get('title', 'Admit Card')}"></div>
                    <div class="alria-input-group"><label>Column 3 (Latest Jobs)</label><input type="text" id="gt-jobs" value="{grid_headers.get('latest-jobs', {}).get('title', 'Latest Jobs')}"></div>
                    <div class="alria-input-group"><label>Column 4 (Answer Key)</label><input type="text" id="gt-key" value="{grid_headers.get('answer-key', {}).get('title', 'Answer Key')}"></div>
                    <div class="alria-input-group"><label>Column 5 (Syllabus)</label><input type="text" id="gt-syl" value="{grid_headers.get('syllabus', {}).get('title', 'Syllabus')}"></div>
                    <div class="alria-input-group"><label>Column 6 (Admission)</label><input type="text" id="gt-adm" value="{grid_headers.get('admission', {}).get('title', 'Admission')}"></div>
                </div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-grid-titles')">Cancel</button><button class="alria-btn-save" onclick="saveGridTitles()">Save Titles</button></div>
            </div>
        </div>

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

        <div id="modal-footer-socials" class="alria-modal-backdrop">
            <div class="alria-modal-card">
                <h3>🔗 Edit Footer &amp; Social Links</h3>
                <div class="alria-input-group"><label>Footer Copyright Text</label><textarea id="f-text" rows="2">{settings.get('footer_text', '')}</textarea></div>
                <h4>Official Social Channels</h4>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                    <div class="alria-input-group"><label>Telegram Link</label><input type="text" id="soc-tg" value="{settings.get('socials', {}).get('telegram', '')}"></div>
                    <div class="alria-input-group"><label>WhatsApp Link</label><input type="text" id="soc-wa" value="{settings.get('socials', {}).get('whatsapp', '')}"></div>
                    <div class="alria-input-group"><label>YouTube Link</label><input type="text" id="soc-yt" value="{settings.get('socials', {}).get('youtube', '')}"></div>
                    <div class="alria-input-group"><label>Instagram Link</label><input type="text" id="soc-ig" value="{settings.get('socials', {}).get('instagram', '')}"></div>
                </div>
                <div class="alria-modal-actions"><button class="alria-btn-cancel" onclick="closeModal('modal-footer-socials')">Cancel</button><button class="alria-btn-save" onclick="saveFooterSocials()">Save Footer &amp; Socials</button></div>
            </div>
        </div>

        <script>
            let siteSettings = {settings_json_escaped};
            function openModal(id) {{ document.getElementById(id).style.display = 'flex'; }}
            function closeModal(id) {{ document.getElementById(id).style.display = 'none'; }}
            function renderCardsInputs() {{
                const cont = document.getElementById('cards-container'); if(!cont) return; cont.innerHTML = '';
                const cards = siteSettings.highlight_cards || [];
                for(let i=0; i<8; i++) {{
                    const c = cards[i] || {{title: '', url: '#'}};
                    cont.innerHTML += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; background:#f8fafc; padding:6px 10px; border-radius:4px;"><div><label style="font-size:11px; font-weight:700;">Card ${{i+1}} Title</label><input type="text" id="card-title-${{i}}" value="${{c.title || ''}}"></div><div><label style="font-size:11px; font-weight:700;">Card ${{i+1}} Link</label><input type="text" id="card-url-${{i}}" value="${{c.url || '#'}}"></div></div>`;
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
                if(res.ok) {{ alert('Section updated!'); location.reload(); }} else {{ alert('Error updating'); }}
            }}
            function saveBranding() {{ saveSettingsPayload({{ site_name: document.getElementById('b-site-name').value, domain: document.getElementById('b-domain').value, tagline: document.getElementById('b-tagline').value, top_banner_text: document.getElementById('b-top-banner').value }}); }}
            function saveCards() {{
                const cards = []; for(let i=0; i<8; i++) {{ cards.push({{ title: document.getElementById(`card-title-${{i}}`).value, url: document.getElementById(`card-url-${{i}}`).value }}); }}
                saveSettingsPayload({{ highlight_cards: cards }});
            }}
            function saveGridTitles() {{
                saveSettingsPayload({{ grid_headers: {{ 'result': {{ title: document.getElementById('gt-result').value, more_url: '/result/' }}, 'admit-card': {{ title: document.getElementById('gt-admit').value, more_url: '/admit-card/' }}, 'latest-jobs': {{ title: document.getElementById('gt-jobs').value, more_url: '/latest-jobs/' }}, 'answer-key': {{ title: document.getElementById('gt-key').value, more_url: '/answer-key/' }}, 'syllabus': {{ title: document.getElementById('gt-syl').value, more_url: '/syllabus/' }}, 'admission': {{ title: document.getElementById('gt-adm').value, more_url: '/admission/' }} }} }});
            }}
            function saveInfoFaq() {{
                const info_secs = [{{ title: document.getElementById('info-t1').value, content: document.getElementById('info-c1').value }}];
                const faqs = []; const len = siteSettings.faq_items ? siteSettings.faq_items.length : 0;
                for(let i=0; i<len; i++) {{ const qEl = document.getElementById(`faq-q-${{i}}`); const aEl = document.getElementById(`faq-a-${{i}}`); if(qEl && aEl) faqs.push({{ q: qEl.value, a: aEl.value }}); }}
                saveSettingsPayload({{ info_sections: info_secs, faq_items: faqs }});
            }}
            function saveFooterSocials() {{
                saveSettingsPayload({{ footer_text: document.getElementById('f-text').value, socials: {{ telegram: document.getElementById('soc-tg').value, whatsapp: document.getElementById('soc-wa').value, youtube: document.getElementById('soc-yt').value, instagram: document.getElementById('soc-ig').value }} }});
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

@app.route('/api/admin/save-settings', methods=['POST'])
def api_save_settings():
    settings = load_settings()
    data = request.get_json(silent=True) or request.form

    for k, v in data.items():
        if k in ['google_analytics_id', 'google_site_verification', 'meta_description', 'meta_keywords', 'custom_head_code', 'custom_footer_code']:
            if 'seo' not in settings: settings['seo'] = {}
            settings['seo'][k] = v
        elif k in ['adsense_id']:
            if 'adsense' not in settings: settings['adsense'] = {}
            settings['adsense']['client_id'] = v
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

@app.route('/api/admin/save-post', methods=['POST'])
def api_save_post():
    data = request.get_json(silent=True) or request.form
    title = data.get('title', '').strip()
    slug = data.get('slug') or title.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')[:80]
    html_content = data.get('html_content', '')

    page_file = os.path.join(PAGES_DIR, f"{slug}.html")
    with open(page_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return redirect('/admin/posts')

@app.route('/api/admin/posts/delete/<post_id>', methods=['POST'])
def api_delete_post(post_id):
    page_file = os.path.join(PAGES_DIR, f"{post_id}.html")
    if os.path.exists(page_file):
        os.remove(page_file)
    return jsonify({'status': 'success', 'deleted': post_id})

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
