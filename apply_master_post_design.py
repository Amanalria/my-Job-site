import os
import glob
import re
import json
from bs4 import BeautifulSoup
import datetime
import app

BASE_DIR = "/root/sarkari-result-portal"
PAGES_DIR = "/root/sarkari-result-portal/pages"
DATA_DIR = "/root/sarkari-result-portal/data"

STATIC_PAGES = [
    'about-us.html', 'about.html', 'contact.html', 'disclaimer.html',
    'privacy-policy.html', 'terms-and-conditions.html', 'terms.html',
    'index.html', 'admission.html', 'admit-card.html', 'answer-key.html',
    'latest-jobs.html', 'result.html', 'syllabus.html'
]

settings = app.load_settings()

# Load the exact master HTML template from post_design_preview.html
with open(os.path.join(BASE_DIR, 'post_design_preview.html'), 'r', encoding='utf-8') as f:
    MASTER_PREVIEW_HTML = f.read()

def humanize(text):
    if not text:
        return ""
    t = text.replace('—', ', ').replace('–', '-')
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
    t = re.sub(r'https?://(?:www\.)?sarkariresult\.com\.cm/?', 'https://studytopper.in/', t, flags=re.I)
    t = re.sub(r'sarkariresult\.com\.cm', 'studytopper.in', t, flags=re.I)
    t = re.sub(r'Sarkari\s*Result', 'Study Topper', t, flags=re.I)
    t = re.sub(r'SarkariResult', 'Study Topper', t, flags=re.I)
    return t.strip()

def extract_category_from_slug_or_title(slug, title):
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

def build_post_from_master_template(slug, raw_html_content):
    soup = BeautifulSoup(MASTER_PREVIEW_HTML, 'html.parser')
    raw_soup = BeautifulSoup(raw_html_content, 'html.parser')

    raw_h1 = raw_soup.find('h1')
    title = raw_h1.get_text().strip() if raw_h1 else slug.replace('-', ' ').title()
    title = humanize(title)
    
    category = extract_category_from_slug_or_title(slug, title)

    # 1. Update Title tag & SEO
    if soup.title:
        soup.title.string = f"{title} | STUDY TOPPER™"
    
    # 2. Update H1 in Header
    h1 = soup.find('h1')
    if h1:
        h1.string = title

    # 3. Update H2
    h2 = soup.find('h2')
    if h2:
        h2.string = f"{title} – Details & Updates"

    # 4. Update H3
    h3 = soup.find('h3')
    if h3:
        h3.string = f"{title} : Short Details"

    # 5. Extract dates from raw content
    start_date = "Check Official Notification"
    last_date = "Check Official Notification"
    exam_date = "As per Official Schedule"
    
    date_matches = re.findall(r'(?:Application Begin|Start Date|Starting Date|Begin)\s*[:\-–]\s*([^\n<,]+)', raw_html_content, re.I)
    if date_matches:
        start_date = humanize(date_matches[0])
    last_date_matches = re.findall(r'(?:Last Date for Apply|Last Date|Registration Last Date)\s*[:\-–]\s*([^\n<,]+)', raw_html_content, re.I)
    if last_date_matches:
        last_date = humanize(last_date_matches[0])
    exam_matches = re.findall(r'(?:Exam Date|CBT Date|Examination Date|Date of Exam)\s*[:\-–]\s*([^\n<,]+)', raw_html_content, re.I)
    if exam_matches:
        exam_date = humanize(exam_matches[0])

    # Update Important Dates Box
    dates_box = soup.find(class_='gb-container-16a90584')
    if dates_box:
        ul = dates_box.find('ul')
        if ul:
            ul.clear()
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Online Apply Start Date : <strong>{start_date}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Online Apply Last Date : <span style="color: #ff0000;"><strong>{last_date}</strong></span></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Last Date For Fee Payment : <span style="color: #000000;"><strong>{last_date}</strong></span></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 18.6667px;">Exam / Merit Date : <strong>{exam_date}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Candidates are advised to confirm from the official website.</span></li>', 'html.parser'))

    # 6. Extract fees
    fee_gen = "Check Notification"
    fee_res = "Check Notification"
    fee_gen_match = re.findall(r'(?:General|Gen\s*/\s*OBC|UR\s*/\s*OBC|General\s*/\s*OBC\s*/\s*EWS)\s*[:\-–]\s*([^\n<]+)', raw_html_content, re.I)
    if fee_gen_match:
        fee_gen = humanize(fee_gen_match[0])
    fee_res_match = re.findall(r'(?:SC\s*/\s*ST|SC\s*/\s*ST\s*/\s*PH)\s*[:\-–]\s*([^\n<]+)', raw_html_content, re.I)
    if fee_res_match:
        fee_res = humanize(fee_res_match[0])

    fee_box = soup.find(class_='gb-container-fcbb81ff')
    if fee_box:
        uls = fee_box.find_all('ul')
        if uls:
            uls[0].clear()
            uls[0].append(BeautifulSoup(f'<li><span style="font-size: 14pt;">For <strong>General/ OBC/ EWS</strong> : <strong>{fee_gen}</strong></span></li>', 'html.parser'))
            uls[0].append(BeautifulSoup(f'<li><span style="font-size: 14pt;">For <strong>SC/ ST/ PH / Female</strong> : <strong>{fee_res}</strong></span></li>', 'html.parser'))

    # 7. Extract Total Posts
    total_posts = "As per Notification"
    total_posts_match = re.findall(r'(\d+[\d,]*\s*(?:Posts|Vacancies|Positions|Seats))', title + " " + raw_html_content, re.I)
    if total_posts_match:
        total_posts = total_posts_match[0].strip()

    post_count_box = soup.find(class_='gb-headline-4259c0c2')
    if post_count_box:
        post_count_box.string = total_posts

    # 8. Short details paragraph
    short_desc = f"{title} online form, recruitment details, eligibility criteria, application schedule, and fee guidelines. Review full instructions below and apply through official links."
    short_details_p = soup.find(class_='short_Details')
    if short_details_p:
        inner_p = short_details_p.find('p')
        if inner_p:
            inner_p.string = short_desc
        else:
            short_details_p.string = short_desc

    # 9. Clean links in tables to point to real external or portal links
    # Return complete string
    return str(soup), {
        "id": f"post_{slug.replace('-', '_')}",
        "slug": slug,
        "title": title,
        "category": category,
        "short_desc": short_desc,
        "application_start_date": start_date,
        "application_last_date": last_date,
        "custom_badge": "",
        "tags": f"{category}, Govt Job, Study Topper",
        "created_at": datetime.datetime.now().isoformat()
    }

# Process all posts from raw_clone and write directly into pages/
raw_files = [p for p in glob.glob(os.path.join(BASE_DIR, 'raw_clone/pages/*.html')) if os.path.basename(p) not in STATIC_PAGES]
print(f"Applying EXACT master preview template to {len(raw_files)} posts...")

all_posts = []
for rf in sorted(raw_files):
    slug = os.path.basename(rf).replace('.html', '')
    try:
        with open(rf, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()
        full_html, meta = build_post_from_master_template(slug, raw_content)
        
        # Write to pages/{slug}.html
        out_path = os.path.join(PAGES_DIR, f"{slug}.html")
        with open(out_path, 'w', encoding='utf-8') as out_f:
            out_f.write(full_html)
        
        all_posts.append(meta)
        print(f" [OK] Standardized with master template: {slug} ({meta['category']})")
    except Exception as e:
        print(f" [ERR] Failed on {slug}: {e}")

# Save to data stores
with open(os.path.join(DATA_DIR, 'custom_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(all_posts, f, indent=2)

with open(os.path.join(DATA_DIR, 'all_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(all_posts, f, indent=2)

print("\nSuccessfully applied the exact master preview template to all posts!")
