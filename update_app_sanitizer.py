import os
import json
import re

BASE_DIR = '/root/sarkari-result-portal'
DATA_DIR = os.path.join(BASE_DIR, 'data')

# ==================== 1. UPDATE APP.PY ====================
app_file = os.path.join(BASE_DIR, 'app.py')
with open(app_file, 'r', encoding='utf-8') as f:
    app_code = f.read()

# Add clean_post_html_content & get_footer_html functions in app.py
helpers_code = '''
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

    return f"""<footer class="site-footer" style="background-color:#212121; color:#ffffff; text-align:center; padding:30px 15px; margin-top:40px;">
    <div style="max-width:1040px; margin:0 auto; padding:0 12px;">
        <h3 style="color:#ffffff; font-size:18px; margin-bottom:14px; font-weight:700;">Connect With Us</h3>
        <div style="display:flex; justify-content:center; flex-wrap:wrap; gap:10px; margin-bottom:22px;">
            <a href="{tw_url}" target="_blank" style="color:#fff; text-decoration:none; background:#1e293b; padding:7px 14px; border-radius:4px; font-size:13px; font-weight:600;"><i class="fa-brands fa-x-twitter"></i> Study Topper @X</a>
            <a href="{tg_url}" target="_blank" style="color:#fff; text-decoration:none; background:#0284c7; padding:7px 14px; border-radius:4px; font-size:13px; font-weight:600;"><i class="fa-brands fa-telegram"></i> Study Topper @Telegram</a>
            <a href="{wa_url}" target="_blank" style="color:#fff; text-decoration:none; background:#16a34a; padding:7px 14px; border-radius:4px; font-size:13px; font-weight:600;"><i class="fa-brands fa-whatsapp"></i> Study Topper @WhatsApp</a>
            <a href="{ig_url}" target="_blank" style="color:#fff; text-decoration:none; background:#db2777; padding:7px 14px; border-radius:4px; font-size:13px; font-weight:600;"><i class="fa-brands fa-instagram"></i> Study Topper @Instagram</a>
            <a href="{fb_url}" target="_blank" style="color:#fff; text-decoration:none; background:#2563eb; padding:7px 14px; border-radius:4px; font-size:13px; font-weight:600;"><i class="fa-brands fa-facebook"></i> Study Topper @Facebook</a>
            <a href="{yt_url}" target="_blank" style="color:#fff; text-decoration:none; background:#dc2626; padding:7px 14px; border-radius:4px; font-size:13px; font-weight:600;"><i class="fa-brands fa-youtube"></i> Study Topper @YouTube</a>
        </div>
        
        <p style="font-size:13px; color:#cbd5e1; margin:10px 0; line-height:1.6;">Official Website of Study Topper™ – {domain} | All educational and government recruitment notifications published for student guidance.</p>
        <p style="font-size:12px; color:#94a3b8; margin:6px 0;">Copyright © 2026 | {domain}. All Rights Reserved. Not affiliated with any government agency.</p>
        
        <div class="gb-container-658f27a5" style="margin-top:14px;">
            <a class="gb-button" href="/" style="background:transparent !important; color:#ffffff !important; text-decoration:underline !important; margin:0 8px; font-size:13px;">Home</a>
            <a class="gb-button" href="/contact/" style="background:transparent !important; color:#ffffff !important; text-decoration:underline !important; margin:0 8px; font-size:13px;">Contact</a>
            <a class="gb-button" href="/privacy-policy/" style="background:transparent !important; color:#ffffff !important; text-decoration:underline !important; margin:0 8px; font-size:13px;">Privacy Policy</a>
            <a class="gb-button" href="/disclaimer/" style="background:transparent !important; color:#ffffff !important; text-decoration:underline !important; margin:0 8px; font-size:13px;">Disclaimer</a>
        </div>
    </div>
</footer>"""
'''

# Update render_single_post_html to use clean_post_html_content and get_footer_html
authentic_post_renderer = '''def render_single_post_html(post, settings):
    title = post.get('title', 'Study Topper Notification')
    headline = post.get('headline') or title
    category_slug = post.get('category', 'latest-jobs')
    category_name = category_slug.replace('-', ' ').title()
    short_desc = post.get('short_desc', '')
    html_content = post.get('html_content', '')
    app_start = post.get('application_start_date', 'August 2026')
    app_last = post.get('application_last_date', 'September 2026')
    tags = post.get('tags', '')
    site_name = settings.get('site_name', 'STUDY TOPPER™')
    domain = settings.get('domain', 'studytopper.in')
    socials = settings.get('socials', {})
    wa_url = socials.get('whatsapp', 'https://whatsapp.com/')
    tg_url = socials.get('telegram', 'https://t.me/')

    # Clean raw html content
    cleaned_content = clean_post_html_content(html_content, settings)

    tags_html = ''
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        tags_html = '<div style="margin:25px 0 15px; padding:12px 15px; background:#f8fafc; border-left:4px solid #ab183d; border-radius:3px; display:flex; flex-wrap:wrap; gap:8px; align-items:center;"><strong><i class="fa-solid fa-tags" style="color:#ab183d;"></i> Related Tags:</strong> ' + ''.join([f'<span style="background:#fff; border:1px solid #cbd5e1; padding:3px 10px; border-radius:3px; font-size:12px; font-weight:600; color:#1e293b;">#{t}</span>' for t in tag_list]) + '</div>'

    body_content_render = cleaned_content
    if not body_content_render or len(body_content_render.strip()) < 50:
        body_content_render = f"""
        <table style="width:100%; border-collapse:collapse; border:2px solid #ab183d; margin:15px 0;">
            <thead>
                <tr style="background:#ab183d; color:#ffffff;">
                    <th colspan="2" style="padding:12px; text-align:center; font-size:17px; font-weight:700;">{headline}</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="width:50%; vertical-align:top; padding:12px; border:1px solid #ccc; background:#fafafa;">
                        <h4 style="color:#008000; margin:0 0 8px; font-size:15px;">Important Dates</h4>
                        <ul style="margin:0 0 0 18px; padding:0; font-size:13.5px; line-height:1.8;">
                            <li>Application Begin : <strong>{app_start}</strong></li>
                            <li>Last Date for Apply : <strong style="color:#ab183d;">{app_last}</strong></li>
                            <li>Pay Exam Fee Last Date : <strong>{app_last}</strong></li>
                            <li>Exam Date : <strong>As per Schedule</strong></li>
                            <li>Admit Card Available : <strong>Before Exam</strong></li>
                        </ul>
                    </td>
                    <td style="width:50%; vertical-align:top; padding:12px; border:1px solid #ccc; background:#fafafa;">
                        <h4 style="color:#008000; margin:0 0 8px; font-size:15px;">Application Fee</h4>
                        <ul style="margin:0 0 0 18px; padding:0; font-size:13.5px; line-height:1.8;">
                            <li>General / OBC / EWS : <strong>Rs. 100/-</strong></li>
                            <li>SC / ST / PH : <strong>Rs. 0/- (Exempted)</strong></li>
                            <li>All Category Female : <strong>Rs. 0/-</strong></li>
                            <li>Pay Fee via Online Debit Card / Credit Card / Net Banking / UPI.</li>
                        </ul>
                    </td>
                </tr>
                <tr>
                    <td colspan="2" style="padding:12px; border:1px solid #ccc; background:#ffffff;">
                        <h4 style="color:#ab183d; margin:0 0 8px; font-size:15px;">Age Limit Criteria (as on {app_last})</h4>
                        <ul style="margin:0 0 0 18px; padding:0; font-size:13.5px; line-height:1.7;">
                            <li>Minimum Age : <strong>18 Years</strong></li>
                            <li>Maximum Age : <strong>30-35 Years (Post Wise)</strong></li>
                            <li>Age Relaxation Extra as per Official Recruitment Rules.</li>
                        </ul>
                    </td>
                </tr>
            </tbody>
        </table>
        """

    footer_render = get_footer_html(settings)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} : {site_name} Official Portal</title>
    <meta name="description" content="{short_desc or title}">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; padding: 0; background: #ffffff; color: #000000; line-height: 1.5; font-size: 14px; }}
        header.site-header {{ background-color: #cd0808; text-align: center; padding: 15px 10px; }}
        .main-title {{ margin: 0; font-size: 32px; font-weight: 800; }}
        .main-title a {{ color: #ffffff; text-decoration: none; }}
        .site-description {{ color: #ffffff; font-size: 20px; font-weight: 700; margin: 4px 0 0; }}
        nav.main-navigation {{ background-color: #0c2340; text-align: center; padding: 10px; overflow-x: auto; white-space: nowrap; }}
        nav.main-navigation a {{ color: #ffffff; text-decoration: none; margin: 0 10px; font-size: 14px; font-weight: 700; }}
        nav.main-navigation a:hover {{ text-decoration: underline; }}
        
        .whatsapp-banner {{ text-align: center; margin: 15px 0; }}
        .whatsapp-btn {{ background: #01aa03; color: #fff !important; text-decoration: none; font-size: 14px; font-weight: 700; padding: 10px 22px; border-radius: 8px; display: inline-block; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }}
        
        .post-wrapper {{ max-width: 1040px; margin: 15px auto; padding: 0 12px; }}
        .breadcrumb {{ font-size: 13px; color: #555; margin-bottom: 12px; }}
        .breadcrumb a {{ color: #0000ef; text-decoration: underline; }}
        
        .post-card {{ border: 2px solid #ab183d; padding: 18px 20px; background: #ffffff; margin-bottom: 25px; border-radius: 4px; }}
        h1.entry-title {{ color: #ab183d; font-size: 22px; font-weight: 700; text-align: center; margin: 0 0 12px 0; line-height: 1.4; }}
        .post-meta-line {{ text-align: center; font-size: 13px; color: #444; border-bottom: 1px dashed #ccc; padding-bottom: 10px; margin-bottom: 14px; }}
        .post-meta-line strong {{ color: #000; }}
        
        .short-info-box {{ background: #fff8f8; border: 1px solid #fca5a5; padding: 12px 15px; border-radius: 4px; margin: 15px 0; font-size: 13.5px; line-height: 1.6; text-align: justify; }}
        .short-info-box strong {{ color: #b91c1c; }}

        table {{ width: 100%; border-collapse: collapse; margin: 18px 0; }}
        th, td {{ border: 1px solid #000000; padding: 8px 10px; font-size: 13.5px; text-align: left; }}
        th {{ background-color: #ab183d; color: #ffffff; font-weight: 700; text-align: center; }}
        
        .important-links-table {{ width: 100%; border: 2px solid #0b7659; margin: 25px 0; }}
        .important-links-table th {{ background: #0b7659; color: #fff; font-size: 16px; padding: 10px; }}
        .important-links-table td {{ padding: 10px 12px; font-size: 14px; font-weight: 700; }}
        .important-links-table td a {{ color: #ab183d; font-weight: 700; text-decoration: underline; }}
        
        @media (max-width: 767px) {{
            .main-title {{ font-size: 24px; }}
            .site-description {{ font-size: 16px; }}
            h1.entry-title {{ font-size: 18px; }}
            .post-card {{ padding: 12px 8px; }}
            table, th, td {{ font-size: 12.5px; padding: 6px; }}
        }}
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
    
    <div class="whatsapp-banner">
        <a href="{wa_url}" target="_blank" class="whatsapp-btn">
            <i class="fa-brands fa-whatsapp"></i> Join WhatsApp Channel
        </a>
    </div>

    <div class="post-wrapper">
        <div class="breadcrumb">
            <a href="/">Home</a> » <a href="/{category_slug}/">{category_name}</a> » <span>{title}</span>
        </div>
        
        <article class="post-card">
            <h1 class="entry-title">{headline}</h1>
            <div class="post-meta-line">
                <span><strong>Post Date / Update:</strong> {app_start}</span> | 
                <span><strong>Category:</strong> {category_name}</span> | 
                <span><strong>Status:</strong> Active</span>
            </div>

            {f'<div class="short-info-box"><strong>Short Information : </strong>{short_desc}</div>' if short_desc else ''}

            <div class="entry-content">
                {body_content_render}
            </div>

            <table class="important-links-table">
                <thead>
                    <tr>
                        <th colspan="2">SOME USEFUL IMPORTANT LINKS</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="width:50%;">Apply Online Form</td>
                        <td><a href="#" target="_blank">Click Here</a></td>
                    </tr>
                    <tr>
                        <td>Download Official Notification</td>
                        <td><a href="#" target="_blank">Click Here</a></td>
                    </tr>
                    <tr>
                        <td>Check Study Topper Official Portal</td>
                        <td><a href="/" target="_blank">Click Here</a></td>
                    </tr>
                    <tr>
                        <td>Join Study Topper WhatsApp Channel</td>
                        <td><a href="{wa_url}" target="_blank" style="color:#01aa03;">Join Now</a></td>
                    </tr>
                    <tr>
                        <td>Join Study Topper Telegram Group</td>
                        <td><a href="{tg_url}" target="_blank" style="color:#0284c7;">Join Now</a></td>
                    </tr>
                </tbody>
            </table>

            {tags_html}
            
            <div style="text-align:center; margin-top:25px;">
                <a href="/" style="background:#ab183d; color:#fff; text-decoration:none; padding:8px 18px; border-radius:4px; font-weight:700; font-size:13px; display:inline-block;">« Back to Study Topper Home</a>
            </div>
        </article>
    </div>

    {footer_render}
</body>
</html>"""'''

# Update api_save_settings to parse all social links
old_save_settings = """    # Social Links
    socials = settings.get('socials', {})
    for soc in ['telegram', 'whatsapp', 'youtube', 'instagram']:
        if f'social_{soc}' in data:
            socials[soc] = data[f'social_{soc}'].strip()
    settings['socials'] = socials"""

new_save_settings = """    # Social Links
    socials = settings.get('socials', {})
    for soc in ['telegram', 'whatsapp', 'youtube', 'instagram', 'facebook', 'twitter']:
        if f'social_{soc}' in data:
            socials[soc] = data[f'social_{soc}'].strip()
    settings['socials'] = socials"""

app_code = app_code.replace(old_save_settings, new_save_settings)

# Replace render_single_post_html with new renderer + helper
app_code = re.sub(r'def render_single_post_html\(post, settings\):.*?(?=\n# ==================== CATEGORY & SEARCH PAGE RENDERERS ====================)', helpers_code + '\n' + authentic_post_renderer, app_code, flags=re.DOTALL)

with open(app_file, 'w', encoding='utf-8') as f:
    f.write(app_code)

print("Updated app.py with clean_post_html_content, get_footer_html and dynamic social link handlers!")
