"""
Ultimate High-Fidelity Official Scraper & Category Reference HTML Builder
========================================================================
1. Scrapes exact official data from live sources (sarkariresult.com / sarkariresult.com.cm).
2. Captures 100% of Important Dates, Application Fees, Age Limits, Vacancy Matrix, Category Breakdown, and Links.
3. Strictly applies Humanizer rewriting to ONLY 3 sections:
   [1] Overview Paragraph (90-100 words prose, bold blue org, bold red title, dates, vacancies, eligibility)
   [2] How to Fill Form (Structured application steps incorporating source dates + indtool.in image resizer)
   [3] Frequently Asked Questions (FAQ) (5 structured tailored FAQs)
4. Accurately maps and builds every post to match the exact Category Reference HTML layout.
"""

import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple
import universal_design_agent

BASE_DIR = "/root/sarkari-result-portal"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_text(t: str) -> str:
    if not t: return ""
    return re.sub(r'\s+', ' ', str(t)).strip()

def extract_live_post_details(slug: str, cat: str, existing_title: str = "") -> Optional[Dict[str, Any]]:
    clean_slug = slug.strip('/')
    candidate_urls = [
        f"https://www.sarkariresult.com/2026/{clean_slug}/",
        f"https://www.sarkariresult.com/{clean_slug}/",
        f"https://www.sarkariresult.com/latestjob/{clean_slug}/",
        f"https://www.sarkariresult.com/result/{clean_slug}/",
        f"https://www.sarkariresult.com/admitcard/{clean_slug}/",
        f"https://www.sarkariresult.com/admission/{clean_slug}/",
        f"https://www.sarkariresult.com/syllabus/{clean_slug}/",
        f"https://www.sarkariresult.com/bihar/{clean_slug}/",
        f"https://www.sarkariresult.com/bank/{clean_slug}/",
        f"https://www.sarkariresult.com.cm/{clean_slug}/"
    ]
    
    if 'scholarship' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/2026/up-scholarship-postmatric-jul26/")
        candidate_urls.insert(1, "https://www.sarkariresult.com/up-scholarship/")
    if 'si-prohibition' in clean_slug or 'bpssc' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/bihar/bpssc-si-prohibition-03-2026/")
    if 'bijnor' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/2026/up-bijnor-ecce-educator-july26/")
    if 'patna' in clean_slug or 'phc' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/2026/patna-high-court-july26/")

    for url in candidate_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code != 200 or len(resp.text) < 1200:
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            tables = soup.find_all('table')
            if not tables:
                continue

            h1 = soup.find('h1')
            page_title = clean_text(h1.get_text()) if h1 else existing_title or clean_slug.replace('-', ' ').title()

            data: Dict[str, Any] = {
                "source_url": url,
                "title": page_title,
                "important_dates": {},
                "application_fee": {},
                "age_limits": {},
                "age_as_on": "",
                "total_posts": "",
                "post_matrix": [],
                "category_vacancies": {},
                "how_to_fill": [],
                "important_links": [],
                "apply_link": "",
                "notification_link": "",
                "official_website": ""
            }

            m = re.search(r'Total\s*:\s*([\d,]+\s*Posts?)', resp.text, re.I)
            if m:
                data["total_posts"] = clean_text(m.group(1))
            else:
                m2 = re.search(r'(\d+[\d,]*\s*Posts?)', resp.text, re.I)
                if m2:
                    data["total_posts"] = clean_text(m2.group(1))

            # 1. Important Links
            for tr in soup.find_all('tr'):
                tds = tr.find_all(['td', 'th'])
                if len(tds) >= 2:
                    label = clean_text(tds[0].get_text(separator=' '))
                    label_l = label.lower()
                    a_tags = tds[1].find_all('a', href=True)
                    for a in a_tags:
                        href = a['href'].strip()
                        anchor_text = clean_text(a.get_text()) or label
                        if href and not href.startswith('javascript:') and len(label) > 2:
                            is_apple = 'apple' in label_l or 'ios' in label_l
                            data["important_links"].append({
                                "title": label,
                                "anchor": anchor_text,
                                "url": href
                            })
                            if not is_apple and re.search(r'\bapply\b', label_l) and not data["apply_link"]:
                                data["apply_link"] = href
                            elif ('notification' in label_l or 'advt' in label_l or 'writeup' in label_l or 'brochure' in label_l) and not data["notification_link"]:
                                data["notification_link"] = href
                            elif 'official website' in label_l and not data["official_website"]:
                                data["official_website"] = href
                            elif ('admit card' in label_l or 'hall ticket' in label_l or 'result' in label_l or 'score' in label_l or 'answer key' in label_l or 'syllabus' in label_l) and not data["apply_link"]:
                                data["apply_link"] = href

            # 2. Text Cells (Dates, Fee, Age, How-to-Fill)
            for td in soup.find_all(['td', 'th']):
                txt = td.get_text(separator='\n', strip=True)
                raw_lines = [clean_text(l) for l in txt.split('\n') if clean_text(l)]

                # Dates
                if any('important dates' in l.lower() or 'schedule dates' in l.lower() or 'exam dates' in l.lower() for l in raw_lines[:2]):
                    curr_k = None
                    for l in raw_lines:
                        if any(x in l.lower() for x in ['important dates', 'exam dates', 'schedule dates']):
                            continue
                        if ':' in l:
                            p = l.split(':', 1)
                            k = clean_text(p[0])
                            v = clean_text(p[1])
                            if v:
                                data["important_dates"][k] = v
                                curr_k = None
                            else:
                                curr_k = k
                        elif curr_k:
                            data["important_dates"][curr_k] = l
                            curr_k = None
                        elif len(l) > 3:
                            data["important_dates"][l] = "Available"

                # Fee
                if any('application fee' in l.lower() or 'fee details' in l.lower() for l in raw_lines[:2]):
                    curr_k = None
                    for l in raw_lines:
                        if any(x in l.lower() for x in ['application fee', 'fee details']):
                            continue
                        if ':' in l:
                            p = l.split(':', 1)
                            k = clean_text(p[0])
                            v = clean_text(p[1])
                            if v:
                                data["application_fee"][k] = v
                                curr_k = None
                            else:
                                curr_k = k
                        elif curr_k:
                            data["application_fee"][curr_k] = l
                            curr_k = None
                        elif any(w in l.lower() for w in ['pay the exam fee', 'payment mode', 'through online', 'debit card', 'net banking', 'offline fee', 'exempted', 'no application fee', 'challan']):
                            data["application_fee"]["Payment Mode"] = l
                        elif len(l) > 3:
                            data["application_fee"][l] = "Applicable"

                # Age Limits
                if any('age limit' in l.lower() for l in raw_lines[:3]):
                    curr_k = None
                    for l in raw_lines:
                        if 'age limit as on' in l.lower() or 'age as on' in l.lower():
                            m_d = re.search(r'(\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})', l)
                            if m_d:
                                data["age_as_on"] = m_d.group(1)
                            else:
                                data["age_as_on"] = l.replace('Age Limit as on', '').replace('Age as on', '').replace(':', '').strip()
                        elif 'minimum age' in l.lower() or 'maximum age' in l.lower() or 'age limit' in l.lower():
                            if ':' in l:
                                p = l.split(':', 1)
                                k = clean_text(p[0])
                                v = clean_text(p[1])
                                if v:
                                    data["age_limits"][k] = v
                                    curr_k = None
                                else:
                                    curr_k = k
                            else:
                                curr_k = l
                        elif curr_k:
                            data["age_limits"][curr_k] = l
                            curr_k = None
                        elif 'age relaxation' in l.lower():
                            data["age_limits"]["Age Relaxation"] = l
                        elif len(l) > 4:
                            data["age_limits"][l] = "Applicable"

                # How to Fill
                if any('how to' in l.lower() or 'instructions' in l.lower() for l in raw_lines[:2]):
                    for l in raw_lines:
                        if any(w in l.lower() for w in ['how to', 'sarkari result', 'telegram', 'whatsapp', 'download app', 'visit website']) and len(l) < 35:
                            continue
                        if len(l) > 12 and l not in data["how_to_fill"] and not any(x in l.lower() for x in ['telegram', 'whatsapp', 'download app', 'visit website']):
                            data["how_to_fill"].append(l)

            # 3. Flexible Multi-Header Post Matrix Extraction
            col1_headers = ['post name', 'district name', 'class', 'trade name', 'discipline', 'department', 'course', 'branch', 'subject', 'exam name', 'cadre', 'designation', 'post']
            col2_headers = ['eligibility', 'total post', 'total seat', 'total vacancy', 'qualification', 'criteria', 'seat', 'posts', 'vacancies']

            for tbl in tables:
                rows = tbl.find_all('tr')
                for i, tr in enumerate(rows):
                    tds = tr.find_all(['td', 'th'])
                    row_txt = " | ".join([clean_text(t.get_text()) for t in tds]).lower()

                    # Post Matrix
                    if any(h in row_txt for h in col1_headers) and any(h in row_txt for h in col2_headers):
                        for d_tr in rows[i+1:]:
                            d_tds = d_tr.find_all(['td', 'th'])
                            d_txt = " | ".join([clean_text(t.get_text()) for t in d_tds]).lower()
                            if 'how to' in d_txt or 'category wise' in d_txt or 'download' in d_txt or 'exam district' in d_txt or len(d_tds) < 2:
                                break
                            p_name = clean_text(d_tds[0].get_text())
                            p_posts = clean_text(d_tds[1].get_text()) if len(d_tds) > 1 else ""
                            p_elig = clean_text(" ".join([t.get_text(separator=' ') for t in d_tds[2:]])) if len(d_tds) > 2 else ""
                            if p_name and not any(p_name.lower() == h for h in col1_headers) and not any(p['name'] == p_name for p in data["post_matrix"]):
                                data["post_matrix"].append({
                                    "name": p_name,
                                    "posts": p_posts,
                                    "eligibility": p_elig
                                })

                    # Category Matrix
                    if any(h in row_txt for h in ['ur', 'gen', 'sc', 'st', 'obc', 'ews', 'ebc']) and ('total' in row_txt or 'post name' in row_txt or 'category' in row_txt):
                        headers = [clean_text(t.get_text()) for t in tds]
                        for d_tr in rows[i+1:]:
                            d_tds = d_tr.find_all(['td', 'th'])
                            d_txt = " | ".join([clean_text(t.get_text()) for t in d_tds]).lower()
                            if 'how to' in d_txt or 'download' in d_txt or len(d_tds) != len(headers):
                                break
                            vals = [clean_text(t.get_text()) for t in d_tds]
                            for h, v in zip(headers, vals):
                                if h.lower() not in ['post name', 'state name', 'language', 'sl no']:
                                    data["category_vacancies"][h] = v

            return data
        except Exception:
            continue
    return None

def process_and_publish_all_posts():
    uda = universal_design_agent.UniversalDesignAgent()
    posts_path = os.path.join(BASE_DIR, 'data/all_posts.json')
    with open(posts_path, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    print(f"==================================================")
    print(f"STARTING COMPREHENSIVE RE-SCRAPE & REFERENCE REBUILD FOR {len(posts)} POSTS")
    print(f"==================================================")

    start_time = time.time()
    results_map = {}

    def fetch_worker(p):
        slug = p.get('slug')
        cat = p.get('category', 'latest-jobs')
        title = p.get('title', slug)
        
        live_data = extract_live_post_details(slug, cat, existing_title=title)
        if not live_data:
            live_data = {
                "title": title,
                "total_posts": p.get("total_posts", "Various Posts"),
                "important_dates": p.get("important_dates", {}),
                "application_fee": p.get("application_fee", {}),
                "age_limits": p.get("age_limits", {}),
                "age_as_on": p.get("age_as_on", "01/08/2026"),
                "post_matrix": p.get("post_matrix", []),
                "category_vacancies": p.get("category_vacancies", {}),
                "how_to_fill": p.get("how_to_fill", []),
                "important_links": p.get("important_links", []),
                "apply_link": p.get("apply_online_url", ""),
                "notification_link": p.get("notification_url", ""),
                "official_website": p.get("official_website_url", "")
            }

        clean_org = universal_design_agent.extract_clean_organization(live_data.get("title", title))
        last_date = p.get("application_last_date", "")
        for k, v in live_data["important_dates"].items():
            if 'last date' in k.lower():
                last_date = v
                break
        if not last_date:
            last_date = "As per Official Notification"

        payload = {
            "slug": slug,
            "category": cat,
            "title": live_data.get("title") or title,
            "organization": clean_org,
            "short_desc": f"{clean_org} has officially announced {live_data.get('title') or title} for {live_data.get('total_posts') or 'Various Posts'}.",
            "advt_no": "Official Notification 2026",
            "total_posts": live_data.get("total_posts") or "Various Posts",
            "last_date": last_date,
            "important_dates": live_data.get("important_dates") or {},
            "application_fee": live_data.get("application_fee") or {},
            "age_limits": live_data.get("age_limits") or {},
            "age_as_on": live_data.get("age_as_on") or "01/08/2026",
            "post_matrix": live_data.get("post_matrix") or [],
            "category_vacancies": live_data.get("category_vacancies") or {},
            "how_to_fill": live_data.get("how_to_fill") or [],
            "important_links": live_data.get("important_links") or [],
            "apply_link": live_data.get("apply_link") or "",
            "notification_link": live_data.get("notification_link") or "",
            "official_website": live_data.get("official_website") or "https://studytopper.in"
        }

        # Render HTML using exact reference template
        html = uda.build_post_html(payload)
        out_file = os.path.join(BASE_DIR, 'pages', f"{slug}.html")
        with open(out_file, "w", encoding="utf-8") as f_out:
            f_out.write(html)

        return slug, payload

    # Concurrent Fetching & HTML Generation
    with ThreadPoolExecutor(max_workers=10) as executor:
        futs = [executor.submit(fetch_worker, p) for p in posts]
        for f in as_completed(futs):
            slug, payload = f.result()
            results_map[slug] = payload
            print(f"[Done] {slug}")

    # Sequential Safe Database Updates
    print(f"\nScraping complete ({time.time()-start_time:.1f}s). Updating master records...")
    final_post_list = []
    for p in posts:
        slug = p.get('slug')
        if slug in results_map:
            payload = results_map[slug]
            p["title"] = payload["title"]
            p["total_posts"] = payload["total_posts"]
            p["application_last_date"] = payload["last_date"]
            p["important_dates"] = payload["important_dates"]
            p["application_fee"] = payload["application_fee"]
            p["age_limits"] = payload["age_limits"]
            p["age_as_on"] = payload["age_as_on"]
            p["post_matrix"] = payload["post_matrix"]
            p["category_vacancies"] = payload["category_vacancies"]
            p["how_to_fill"] = payload["how_to_fill"]
            p["important_links"] = payload["important_links"]
            p["apply_online_url"] = payload["apply_link"]
            p["notification_url"] = payload["notification_link"]
            p["official_website_url"] = payload["official_website"]
        final_post_list.append(p)

    with open(posts_path, 'w', encoding='utf-8') as f:
        json.dump(final_post_list, f, indent=4)

    custom_path = os.path.join(BASE_DIR, 'data/custom_posts.json')
    if os.path.exists(custom_path):
        with open(custom_path, 'w', encoding='utf-8') as f:
            json.dump(final_post_list, f, indent=4)

    print(f"==================================================")
    print(f"ALL {len(posts)} POSTS FULLY REBUILT ACCORDING TO REFERENCE HTML STANDARDS!")
    print(f"==================================================")

    # Sync Homepage & Git
    try:
        import vacancy_lifecycle_engine as v_engine
        v_engine.audit_and_execute_lifecycle()
    except Exception as e:
        print(f"[Sync Warning] {e}")

if __name__ == "__main__":
    process_and_publish_all_posts()
