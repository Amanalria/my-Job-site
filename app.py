import os
import re
import json
import urllib.parse
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

TARGET_DOMAIN = "sarkariresult.com.cm"

PRIMARY_CATEGORIES = [
    'latest-jobs', 'admit-card', 'result', 'admission', 'syllabus', 'answer-key',
    'certificate-verification', 'important', 'contact', 'disclaimer', 'privacy-policy'
]

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
        'adsense': {'enabled': False, 'client_id': ''}
    }

def save_settings_data(data):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def sanitize_html(html_content, current_host, is_alria_mode=False):
    soup = BeautifulSoup(html_content, 'html.parser')
    settings = load_settings()

    # 1. Strip external ad scripts, iframes, push notifications
    for s in soup.find_all(['script', 'iframe', 'ins']):
        src = s.get('src', '')
        txt = s.get_text()
        classes = s.get('class', [])
        if any(ad in src.lower() for ad in ['pagead2', 'googlesyndication', 'izooto', 'googletagmanager', 'cloudflare']):
            s.decompose()
        elif 'adsbygoogle' in classes:
            s.decompose()

    # 2. Inject Google AdSense Auto Ads if enabled
    adsense_cfg = settings.get('adsense', {})
    if adsense_cfg.get('enabled') and adsense_cfg.get('client_id'):
        client_id = adsense_cfg.get('client_id')
        if soup.head:
            ad_script = soup.new_tag('script', src=f"https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={client_id}", crossorigin="anonymous", **{'async': True})
            soup.head.append(ad_script)

    # 3. Clean desktop centered alignment styling
    center_style = soup.new_tag('style')
    center_style.string = """
    @media (min-width: 1025px) {
        .gb-grid-wrapper-180dce95 {
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: center !important;
            margin-left: auto !important;
            margin-right: auto !important;
            max-width: 1100px !important;
        }
        .gb-grid-wrapper-180dce95 > .gb-grid-column {
            flex: 0 0 32% !important;
            max-width: 32% !important;
            margin: 0.6% !important;
        }
    }
    """
    if soup.head:
        soup.head.append(center_style)

    # 4. Inject /alria Live Editor Toolbar if in edit mode
    if is_alria_mode:
        alria_html = f'''
        <div id="alria-bar" style="position:fixed; top:0; left:0; right:0; z-index:999999; background:rgba(15,23,42,0.95); backdrop-filter:blur(10px); color:#fff; padding:10px 20px; display:flex; align-items:center; justify-content:space-between; box-shadow:0 4px 20px rgba(0,0,0,0.3); border-bottom:2px solid #ef4444; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            <div style="display:flex; align-items:center; gap:12px;">
                <span style="background:#ef4444; color:#fff; padding:3px 8px; border-radius:4px; font-weight:800; font-size:12px;">⚡ ALRIA LIVE EDITOR</span>
                <span style="font-size:13px; color:#cbd5e1;">Live visual editing on Official Clone</span>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <button onclick="openModal('modal-edit-settings')" style="background:#3b82f6; color:#fff; border:none; padding:6px 14px; border-radius:4px; font-weight:700; cursor:pointer; font-size:13px;">⚙️ Edit Branding &amp; Ads</button>
                <a href="/admin/dashboard" style="background:#475569; color:#fff; text-decoration:none; padding:6px 14px; border-radius:4px; font-weight:700; font-size:13px;">Admin Dashboard</a>
                <a href="/" style="background:#64748b; color:#fff; text-decoration:none; padding:6px 14px; border-radius:4px; font-weight:700; font-size:13px;">Exit Live Mode</a>
            </div>
        </div>

        <!-- Modals -->
        <div id="modal-edit-settings" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.6); z-index:1000000; align-items:center; justify-content:center; font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;">
            <div style="background:#fff; border-radius:8px; width:90%; max-width:550px; padding:24px; box-shadow:0 20px 25px -5px rgba(0,0,0,0.2);">
                <h3 style="margin-top:0; font-size:18px; color:#0f172a; border-bottom:1px solid #e2e8f0; padding-bottom:10px;">Edit Portal Branding &amp; AdSense</h3>
                <label style="display:block; font-weight:600; font-size:13px; margin:10px 0 4px;">Site Name</label>
                <input type="text" id="alria-site-name" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:4px; box-sizing:border-box;" value="{settings.get('site_name', '')}">
                <label style="display:block; font-weight:600; font-size:13px; margin:10px 0 4px;">Domain Name</label>
                <input type="text" id="alria-domain" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:4px; box-sizing:border-box;" value="{settings.get('domain', '')}">
                <label style="display:block; font-weight:600; font-size:13px; margin:10px 0 4px;">Google AdSense Publisher ID</label>
                <input type="text" id="alria-adsense-id" style="width:100%; padding:8px; border:1px solid #cbd5e1; border-radius:4px; box-sizing:border-box;" value="{adsense_cfg.get('client_id', '')}" placeholder="ca-pub-1234567890123456">
                <label style="display:flex; align-items:center; gap:8px; font-size:13px; font-weight:600; cursor:pointer; margin:10px 0;">
                    <input type="checkbox" id="alria-adsense-enabled" {'checked' if adsense_cfg.get('enabled') else ''}> Enable AdSense Auto Ads
                </label>
                <div style="display:flex; justify-content:flex-end; gap:10px; margin-top:15px;">
                    <button onclick="closeModal('modal-edit-settings')" style="padding:8px 16px; border:1px solid #cbd5e1; background:#fff; border-radius:4px; cursor:pointer;">Cancel</button>
                    <button onclick="saveSiteSettings()" style="padding:8px 16px; background:#ef4444; color:#fff; border:none; border-radius:4px; font-weight:700; cursor:pointer;">Save Changes</button>
                </div>
            </div>
        </div>

        <script>
            function openModal(id) {{ document.getElementById(id).style.display = 'flex'; }}
            function closeModal(id) {{ document.getElementById(id).style.display = 'none'; }}
            async function saveSiteSettings() {{
                const payload = {{
                    site_name: document.getElementById('alria-site-name').value,
                    domain: document.getElementById('alria-domain').value,
                    adsense_id: document.getElementById('alria-adsense-id').value,
                    adsense_enabled: document.getElementById('alria-adsense-enabled').checked
                }};
                const res = await fetch('/api/admin/save-settings', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(payload)
                }});
                if(res.ok) {{ alert('Settings saved successfully!'); location.reload(); }}
                else {{ alert('Error saving'); }}
            }}
        </script>
        '''
        if soup.body:
            soup.body['style'] = 'padding-top: 55px !important;'
            soup.body.insert(0, BeautifulSoup(alria_html, 'html.parser'))

    # 5. Domain Rewrite for All Links
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

# ==================== SEO & SITEMAP ROUTES ====================

@app.route('/sitemap.xml')
def dynamic_sitemap():
    host = request.host
    scheme = 'https' if request.is_secure else 'http'
    today = datetime.now().strftime('%Y-%m-%d')

    pages = []
    # 1. Homepage
    pages.append({'loc': f"{scheme}://{host}/", 'priority': '1.0', 'changefreq': 'always'})

    # 2. Categories
    for cat in PRIMARY_CATEGORIES:
        pages.append({'loc': f"{scheme}://{host}/{cat}/", 'priority': '0.9', 'changefreq': 'hourly'})

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

@app.route('/robots.txt')
def robots_txt():
    host = request.host
    scheme = 'https' if request.is_secure else 'http'
    content = f"""User-agent: *
Allow: /

Sitemap: {scheme}://{host}/sitemap.xml
"""
    return Response(content, mimetype='text/plain')

# ==================== CORE HOMEPAGE & /ALRIA ROUTE ====================

@app.route('/')
@app.route('/alria')
def home():
    is_alria = (request.path == '/alria') or (request.args.get('alria') == '1')
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
    if clean_slug in ['favicon.ico', 'robots.txt', 'sitemap.xml']:
        abort(404)

    # Check local page
    page_file = os.path.join(PAGES_DIR, f"{clean_slug}.html")
    if os.path.exists(page_file):
        with open(page_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return Response(sanitize_html(content, request.host), mimetype='text/html')

    # On-demand live fetch fallback for uncached post URL
    try:
        url = f"https://{TARGET_DOMAIN}/{clean_slug}/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            cleaned = sanitize_html(res.text, request.host)
            # Cache locally
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
@app.route('/admin/dashboard')
def admin_dashboard():
    settings = load_settings()
    # Count local posts
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

@app.route('/admin/settings')
def admin_settings():
    settings = load_settings()
    return render_template('admin/settings.html', settings=settings)

@app.route('/api/admin/save-settings', methods=['POST'])
def api_save_settings():
    settings = load_settings()
    data = request.get_json(silent=True) or request.form

    if 'site_name' in data: settings['site_name'] = data['site_name']
    if 'domain' in data: settings['domain'] = data['domain']
    if 'adsense_id' in data: settings['adsense']['client_id'] = data['adsense_id']
    if 'adsense_enabled' in data: settings['adsense']['enabled'] = bool(data['adsense_enabled'])
    if 'supabase_url' in data: settings['supabase']['url'] = data['supabase_url']
    if 'supabase_key' in data: settings['supabase']['key'] = data['supabase_key']
    if 'supabase_enabled' in data: settings['supabase']['enabled'] = bool(data['supabase_enabled'])

    save_settings_data(settings)
    if request.is_json:
        return jsonify({'status': 'success', 'settings': settings})
    return redirect('/admin/settings')

if __name__ == '__main__':
    print("===================================================================")
    print("Starting SARKARI RESULT OFFICIAL PRO PORTAL (PORT 9093)")
    print(" - Official Homepage:     http://127.0.0.1:9093")
    print(" - /alria Visual Editor:  http://127.0.0.1:9093/alria")
    print(" - Dynamic Sitemap:       http://127.0.0.1:9093/sitemap.xml")
    print(" - Robots.txt:            http://127.0.0.1:9093/robots.txt")
    print(" - Full Admin Dashboard:  http://127.0.0.1:9093/admin/dashboard")
    print("===================================================================")
    app.run(host='0.0.0.0', port=9093, debug=False)
