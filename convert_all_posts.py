import os
import glob
import re
import json
from bs4 import BeautifulSoup
import datetime
import app

RAW_DIR = "/root/sarkari-result-portal/raw_clone/pages"
PAGES_DIR = "/root/sarkari-result-portal/pages"
DATA_DIR = "/root/sarkari-result-portal/data"

STATIC_PAGES = [
    'about-us.html', 'about.html', 'contact.html', 'disclaimer.html',
    'privacy-policy.html', 'terms-and-conditions.html', 'terms.html',
    'index.html', 'admission.html', 'admit-card.html', 'answer-key.html',
    'latest-jobs.html', 'result.html', 'syllabus.html'
]

settings = app.load_settings()

def humanize_text(text):
    if not text:
        return ""
    # Remove em-dashes / en-dashes
    t = text.replace('—', ', ').replace('–', '-')
    # Remove AI buzzwords & replace with direct words
    t = re.sub(r'\bdelve into\b', 'check', t, flags=re.I)
    t = re.sub(r'\bdelve\b', 'look', t, flags=re.I)
    t = re.sub(r'\btapestry\b', 'overview', t, flags=re.I)
    t = re.sub(r'\btestament\b', 'proof', t, flags=re.I)
    t = re.sub(r'\bpivotal\b', 'important', t, flags=re.I)
    t = re.sub(r'\bintricate\b', 'detailed', t, flags=re.I)
    t = re.sub(r'\bfostering\b', 'providing', t, flags=re.I)
    t = re.sub(r'\bfurthermore\b', 'Also', t, flags=re.I)
    t = re.sub(r'\bmoreover\b', 'Also', t, flags=re.I)
    t = re.sub(r'\bin conclusion\b', '', t, flags=re.I)
    t = re.sub(r'\bin this digital age\b', 'today', t, flags=re.I)
    # Replace domains & brand names
    t = re.sub(r'https?://(?:www\.)?sarkariresult\.com\.cm/?', 'https://studytopper.in/', t, flags=re.I)
    t = re.sub(r'sarkariresult\.com\.cm', 'studytopper.in', t, flags=re.I)
    t = re.sub(r'Sarkari\s*Result', 'Study Topper', t, flags=re.I)
    t = re.sub(r'SarkariResult', 'Study Topper', t, flags=re.I)
    return t.strip()

def extract_category_from_slug_or_content(slug, title):
    s = slug.lower()
    t = title.lower()
    
    if 'answer-key' in s or 'answer key' in t:
        return 'answer-key'
    if 'admit-card' in s or 'admit' in s or 'hall-ticket' in s or 'exam-city' in s or 'city details' in t or 'admit card' in t:
        return 'admit-card'
    if 'result' in s or 'scorecard' in s or 'cutoff' in s or 'final result' in t or 'result' in t:
        return 'result'
    if 'admission' in s or 'entrance' in s or 'jam' in s or 'gate' in s or 'stet' in s or 'deled' in s or 'cat' in s or 'clat' in s or 'neet' in s or 'pgat' in s:
        return 'admission'
    if 'calendar' in s or 'syllabus' in s or 'pattern' in s or 'yojana' in s or 'scholarship' in s or 'otr' in s or 'document' in s:
        return 'syllabus'
    if 'certificate' in s or 'voter' in s or 'pan' in s or 'aadhar' in s or 'rtps' in s or 'edistrict' in s:
        return 'certificate-verification'
    return 'latest-jobs'

def convert_file(filepath):
    filename = os.path.basename(filepath)
    slug = filename.replace('.html', '')
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # 1. Title
    h1 = soup.find('h1')
    title = h1.get_text().strip() if h1 else (soup.title.get_text().strip() if soup.title else slug.replace('-', ' ').title())
    title = humanize_text(title)

    # 2. Extract raw dates, fees, age, vacancies from content
    full_text = soup.get_text()
    category = extract_category_from_slug_or_content(slug, title)

    # Extract dates
    start_date = "Check Official Notification"
    last_date = "Check Official Notification"
    fee_date = "Check Official Notification"
    exam_date = "As per Official Schedule"

    date_matches = re.findall(r'(?:Application Begin|Start Date|Starting Date|Begin)\s*[:\-–]\s*([^\n<,]+)', html, re.I)
    if date_matches:
        start_date = date_matches[0].strip()
    last_date_matches = re.findall(r'(?:Last Date for Apply|Last Date|Registration Last Date)\s*[:\-–]\s*([^\n<,]+)', html, re.I)
    if last_date_matches:
        last_date = last_date_matches[0].strip()
    exam_matches = re.findall(r'(?:Exam Date|CBT Date|Examination Date|Date of Exam)\s*[:\-–]\s*([^\n<,]+)', html, re.I)
    if exam_matches:
        exam_date = exam_matches[0].strip()

    # Extract fees
    fee_gen = "Check Notification"
    fee_res = "Check Notification"
    fee_gen_match = re.findall(r'(?:General|Gen\s*/\s*OBC|UR\s*/\s*OBC|General\s*/\s*OBC\s*/\s*EWS)\s*[:\-–]\s*([^\n<]+)', html, re.I)
    if fee_gen_match:
        fee_gen = fee_gen_match[0].strip()
    fee_res_match = re.findall(r'(?:SC\s*/\s*ST|SC\s*/\s*ST\s*/\s*PH)\s*[:\-–]\s*([^\n<]+)', html, re.I)
    if fee_res_match:
        fee_res = fee_res_match[0].strip()

    # Extract age
    min_age = "18 Years"
    max_age = "As per Norms"
    min_age_match = re.findall(r'(?:Minimum Age|Min Age)\s*[:\-–]\s*([^\n<]+)', html, re.I)
    if min_age_match:
        min_age = min_age_match[0].strip()
    max_age_match = re.findall(r'(?:Maximum Age|Max Age)\s*[:\-–]\s*([^\n<]+)', html, re.I)
    if max_age_match:
        max_age = max_age_match[0].strip()

    # Extract vacancies
    total_posts = "As per Notification"
    total_posts_match = re.findall(r'(\d+[\d,]*\s*(?:Posts|Vacancies|Positions|Seats))', title + " " + full_text, re.I)
    if total_posts_match:
        total_posts = total_posts_match[0].strip()

    # Extract tables for vacancy and eligibility
    post_rows = []
    tables = soup.find_all('table')
    for tbl in tables:
        rows = tbl.find_all('tr')
        for r in rows:
            tds = r.find_all(['td', 'th'])
            if len(tds) >= 2:
                txts = [humanize_text(td.get_text(strip=True)) for td in tds]
                if any('post name' in t.lower() or 'eligibility' in t.lower() for t in txts):
                    continue
                if len(tds) == 3:
                    post_rows.append({"name": txts[0], "total": txts[1], "eligibility": txts[2]})
                elif len(tds) == 2:
                    post_rows.append({"name": txts[0], "total": total_posts, "eligibility": txts[1]})

    if not post_rows:
        post_rows.append({
            "name": title,
            "total": total_posts,
            "eligibility": "Candidates must meet the educational qualifications and experience required as per the official recruitment notification."
        })

    # Limit post rows to top 6 to prevent oversized tables
    post_rows = post_rows[:6]

    # Extract links
    imp_links = []
    for a in soup.find_all('a'):
        txt = a.get_text(strip=True)
        href = a.get('href', '')
        if href and href.startswith('http') and not any(x in href.lower() for x in ['sarkariresult', 'facebook', 'twitter', 'instagram', 'youtube']):
            txt_clean = humanize_text(txt)
            if len(txt_clean) > 2 and not any(l['url'] == href for l in imp_links):
                imp_links.append({"name": txt_clean if len(txt_clean) < 50 else "Official Link", "url": href, "action_text": "Click Here"})

    # Always ensure standard useful links
    imp_links.append({"name": "Join Official WhatsApp Channel", "url": "https://whatsapp.com/", "action_text": "Join Now"})
    imp_links.append({"name": "Join Official Telegram Channel", "url": "https://t.me/", "action_text": "Join Now"})
    imp_links.append({"name": "StudyTopper Official Home", "url": "/", "action_text": "Click Here"})

    # Extract FAQs or generate standard FAQ items
    faq_items = []
    faq_matches = re.findall(r'(?:Question|Q\.?)\s*[:\-–]\s*([^\n<]+)[\s\S]*?(?:Answer|Ans\.?)\s*[:\-–]\s*([^\n<]+)', html, re.I)
    for q, a in faq_matches[:3]:
        faq_items.append((humanize_text(q), humanize_text(a)))

    if not faq_items:
        faq_items.append((f"What is the last date to apply for {title}?", f"Please check the official dates table above ({last_date})."))
        faq_items.append((f"What is the official website for this notification?", "You can visit the direct official portal links listed in the Useful Important Links table above."))

    # Generate humanized short intro description
    short_desc = f"{title} details, eligibility criteria, application dates, fee structure, and direct official application links. Candidates can review complete requirements and fill out the online form directly."

    # Build post rows HTML
    post_rows_html = ""
    for r in post_rows:
        post_rows_html += f"""
        <tr>
            <td style="padding: 8px 10px; border: 1px solid #ab183d; text-align: left; font-weight: 600;">{r['name']}</td>
            <td style="padding: 8px 10px; border: 1px solid #ab183d; text-align: center; font-weight: bold; color: #cd0808;">{r['total']}</td>
            <td style="padding: 8px 10px; border: 1px solid #ab183d; text-align: left;">{r['eligibility']}</td>
        </tr>
        """

    # Build links HTML
    links_rows_html = ""
    for l in imp_links[:6]:
        color = "#00a82d" if "whatsapp" in l['name'].lower() else ("#0088cc" if "telegram" in l['name'].lower() else "#0000ef")
        links_rows_html += f"""
        <tr>
            <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: left; font-weight: bold; width: 60%;">{l['name']}</td>
            <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: center;">
                <a href="{l['url']}" target="_blank" rel="noopener noreferrer" style="color: {color}; font-weight: bold; text-decoration: underline;">{l['action_text']}</a>
            </td>
        </tr>
        """

    # Build FAQ HTML
    faq_html = ""
    for q, a in faq_items:
        faq_html += f"""
        <tr>
            <td style="padding: 8px 10px; border: 1px solid #ab183d; background-color: #f8fafc; font-weight: bold; color: #0b213f;">Question: {q}</td>
        </tr>
        <tr>
            <td style="padding: 8px 10px; border: 1px solid #ab183d; margin-bottom: 8px; line-height: 1.45;">Answer: {a}</td>
        </tr>
        """

    # Assemble Standard Body HTML
    body_html = f"""
    <div style="font-family: Arial, Helvetica, sans-serif; color: #000000; line-height: 1.5; font-size: 14px;">
        <p style="margin-bottom: 12px; font-size: 14.5px; line-height: 1.6;">
            <strong>{title} :</strong> {short_desc}
        </p>

        <!-- Important Dates & Application Fee Table -->
        <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
            <thead>
                <tr style="background-color: #ab183d; color: #ffffff;">
                    <th style="padding: 8px 10px; border: 1px solid #ab183d; font-size: 15px; width: 50%;">Important Dates</th>
                    <th style="padding: 8px 10px; border: 1px solid #ab183d; font-size: 15px; width: 50%;">Application Fee</th>
                </tr>
            </thead>
            <tbody>
                <tr style="vertical-align: top;">
                    <td style="padding: 10px 12px; border: 1px solid #ab183d; background-color: #ffffff;">
                        <ul style="margin: 0; padding-left: 18px; line-height: 1.6;">
                            <li>Application Start Date: <strong>{start_date}</strong></li>
                            <li>Application Last Date: <strong style="color: #cd0808;">{last_date}</strong></li>
                            <li>Fee Payment Last Date: <strong>{last_date}</strong></li>
                            <li>Exam / Result Schedule: <strong>{exam_date}</strong></li>
                        </ul>
                    </td>
                    <td style="padding: 10px 12px; border: 1px solid #ab183d; background-color: #ffffff;">
                        <ul style="margin: 0; padding-left: 18px; line-height: 1.6;">
                            <li>General / OBC / EWS: <strong>{fee_gen}</strong></li>
                            <li>SC / ST / PH: <strong>{fee_res}</strong></li>
                            <li>Payment Mode: <strong>Online Net Banking / Cards / UPI</strong></li>
                        </ul>
                    </td>
                </tr>
            </tbody>
        </table>

        <!-- Age Limit Table -->
        <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
            <thead>
                <tr style="background-color: #ab183d; color: #ffffff;">
                    <th colspan="2" style="padding: 8px 10px; text-align: center; font-size: 15px;">Age Limit Criteria & Relaxation</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 10px 12px; border: 1px solid #ab183d;" colspan="2">
                        <ul style="margin: 0; padding-left: 18px; line-height: 1.6;">
                            <li>Minimum Age: <strong>{min_age}</strong></li>
                            <li>Maximum Age: <strong>{max_age}</strong></li>
                            <li>Age Relaxation: Extra relaxation admissible for reserved categories as per recruitment rules.</li>
                        </ul>
                    </td>
                </tr>
            </tbody>
        </table>

        <!-- Vacancy Details Table -->
        <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
            <thead>
                <tr style="background-color: #ab183d; color: #ffffff;">
                    <th colspan="3" style="padding: 8px 10px; text-align: center; font-size: 15px;">Vacancy Details (Total: {total_posts})</th>
                </tr>
                <tr style="background-color: #f1f5f9; color: #0b213f;">
                    <th style="padding: 8px 10px; border: 1px solid #ab183d; text-align: left; font-size: 13.5px;">Post Name</th>
                    <th style="padding: 8px 10px; border: 1px solid #ab183d; text-align: center; font-size: 13.5px;">Total Post</th>
                    <th style="padding: 8px 10px; border: 1px solid #ab183d; text-align: left; font-size: 13.5px;">Eligibility Criteria</th>
                </tr>
            </thead>
            <tbody>
                {post_rows_html}
            </tbody>
        </table>

        <!-- How to Apply Step-by-Step Instructions -->
        <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
            <thead>
                <tr style="background-color: #ab183d; color: #ffffff;">
                    <th style="padding: 8px 10px; text-align: center; font-size: 15px;">Step-by-Step Instructions & How to Apply</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 10px 14px; border: 1px solid #ab183d; background-color: #ffffff;">
                        <ol style="margin: 0; padding-left: 20px; line-height: 1.6;">
                            <li>Visit the designated official portal and read the advertisement guidelines thoroughly.</li>
                            <li>Register your basic profile details and verify contact information via OTP.</li>
                            <li>Enter academic records, marks, and personal identification details accurately.</li>
                            <li>Upload scanned passport photograph, signature, and necessary certificates.</li>
                            <li>Pay the required processing fee online and download the submitted confirmation form.</li>
                        </ol>
                    </td>
                </tr>
            </tbody>
        </table>

        <!-- Useful Important Links Table -->
        <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
            <thead>
                <tr style="background-color: #ab183d; color: #ffffff;">
                    <th colspan="2" style="padding: 8px 10px; text-align: center; font-size: 15px;">Useful Important Links</th>
                </tr>
            </thead>
            <tbody>
                {links_rows_html}
            </tbody>
        </table>

        <!-- FAQ Table -->
        <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
            <thead>
                <tr style="background-color: #ab183d; color: #ffffff;">
                    <th style="padding: 8px 10px; text-align: center; font-size: 15px;">Frequently Asked Questions (FAQ)</th>
                </tr>
            </thead>
            <tbody>
                {faq_html}
            </tbody>
        </table>
    </div>
    """

    post_record = {
        "id": f"post_{slug.replace('-', '_')}",
        "slug": slug,
        "title": title,
        "category": category,
        "short_desc": short_desc,
        "application_start_date": start_date,
        "application_last_date": last_date,
        "custom_badge": "",
        "tags": f"{category}, Govt Job, Study Topper",
        "created_at": datetime.datetime.now().isoformat(),
        "html_content": body_html
    }

    # Render complete standalone page HTML using render_single_post_html
    full_html = app.render_single_post_html(post_record, settings)
    
    out_file = os.path.join(PAGES_DIR, f"{slug}.html")
    with open(out_file, 'w', encoding='utf-8') as out_f:
        out_f.write(full_html)

    return post_record

# Run conversion on all raw posts
all_converted = []
raw_files = [p for p in glob.glob(os.path.join(RAW_DIR, '*.html')) if os.path.basename(p) not in STATIC_PAGES]
print(f"Converting {len(raw_files)} posts into standard post design...")

for rf in sorted(raw_files):
    try:
        rec = convert_file(rf)
        all_converted.append(rec)
        print(f" [OK] Converted: {rec['slug']} ({rec['category']})")
    except Exception as e:
        print(f" [ERR] Failed {rf}: {e}")

# Save to data stores
with open(os.path.join(DATA_DIR, 'custom_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(all_converted, f, indent=2)

with open(os.path.join(DATA_DIR, 'all_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(all_converted, f, indent=2)

# Update category_data.json
cat_data = {}
for p in all_converted:
    cat = p.get('category', 'latest-jobs')
    if cat not in cat_data:
        cat_data[cat] = []
    cat_data[cat].append({
        'title': p.get('title'),
        'url': f"/{p.get('slug')}/",
        'short_desc': p.get('short_desc', ''),
        'date': p.get('application_start_date', '')
    })

with open(os.path.join(DATA_DIR, 'category_data.json'), 'w', encoding='utf-8') as f:
    json.dump(cat_data, f, indent=2)

print(f"\nSuccessfully converted all {len(all_converted)} posts into the permanent standard design layout!")
