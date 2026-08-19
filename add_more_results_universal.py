import os
import glob
import re
import json
import datetime
from bs4 import BeautifulSoup

BASE_DIR = "/root/sarkari-result-portal"
PAGES_DIR = os.path.join(BASE_DIR, "pages")
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_CLONE_DIR = os.path.join(BASE_DIR, "raw_clone/pages")

# Load master blueprint
with open(os.path.join(BASE_DIR, 'post_design_preview.html'), 'r', encoding='utf-8') as f:
    MASTER_BLUEPRINT = f.read()

# Additional high-impact Result posts
new_results = [
    {
        "slug": "bihar-police-constable-result-2024",
        "title": "Bihar Police Constable Written Exam Result 2024-2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "03:30 pm",
        "short_desc": "Central Selection Board of Constable (CSBC Bihar) announces the written examination results and physical standard / efficiency test (PET) shortlisted candidate roll numbers for 21,391 Constable vacancies in Bihar Police.",
        "start_date": "Written Exam: July-August 2024",
        "last_date": "Result Declared: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "PET Exam: Sept-Oct 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "25 Years",
        "total_posts": "21,391 Posts",
        "vacancy_rows": [
            ("Bihar Police Constable (GD)", "21,391", "Candidates shortlisted for Physical Efficiency Test (PET), 1.6 km run, high jump, shot put.")
        ],
        "how_to_apply": [
            "Visit the official portal of CSBC Bihar at csbc.bih.nic.in.",
            "Click on Bihar Police tab on the navigation bar.",
            "Download the Written Examination Result PDF for Advt 01/2023.",
            "Search your Roll Number in the PDF file.",
            "Save the qualified result page for PET admit card verification."
        ],
        "links": [
            ("Download Written Result PDF", "https://csbc.bih.nic.in/", "Click Here"),
            ("Check Cutoff Marks Notice", "https://csbc.bih.nic.in/", "Click Here"),
            ("CSBC Official Website", "https://csbc.bih.nic.in/", "Click Here")
        ],
        "faqs": [
            ("How to find roll number in Bihar Police Constable result PDF?", "Open the downloaded PDF and press Ctrl+F (or tap search icon on mobile) and type your roll number.")
        ]
    },
    {
        "slug": "up-police-constable-result-2024",
        "title": "UP Police Constable Written Exam Result & Scorecard 2024-2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "04:15 pm",
        "short_desc": "Uttar Pradesh Police Recruitment and Promotion Board (UPPRPB) issues the normalized scorecards, cutoff marks, and candidate shortlist for Document Verification & Physical Standards Test (DV/PST) for 60,244 Constable posts.",
        "start_date": "Written Exam: August 2024",
        "last_date": "Result Declared: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "DV/PST: September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "25 Years (Male) / 28 Years (Female)",
        "total_posts": "60,244 Posts",
        "vacancy_rows": [
            ("Constable Civil Police (Male & Female)", "60,244", "Candidates qualified for Document Verification and Physical Standard Test (DV/PST).")
        ],
        "how_to_apply": [
            "Open the official UPPRPB website at uppbpb.gov.in.",
            "Click on Candidate Scorecard Login link.",
            "Enter your Registration Number and Date of Birth.",
            "View normalized score and DV/PST qualification status.",
            "Download and print the scorecard for document verification."
        ],
        "links": [
            ("Download UP Police Scorecard", "https://uppbpb.gov.in/", "Click Here"),
            ("Check Category Cutoff PDF", "https://uppbpb.gov.in/", "Click Here"),
            ("UPPRPB Official Website", "https://uppbpb.gov.in/", "Click Here")
        ],
        "faqs": [
            ("What is the next stage for candidates who cleared UP Police written exam?", "Qualified candidates must attend Document Verification and Physical Standard Test (DV/PST).")
        ]
    },
    {
        "slug": "ssc-cgl-tier-1-result-2026",
        "title": "SSC CGL Tier 1 Result, Scorecard & Cutoff Marks 2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "05:00 pm",
        "short_desc": "Staff Selection Commission (SSC) declares the Computer Based Examination (Tier-I) results, normalized cutoff marks, and merit lists of candidates shortlisted for Tier-II descriptive/online examination.",
        "start_date": "Tier-1 Exam: July 2026",
        "last_date": "Result Declared: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Tier-2 Exam: October 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18-20 Years",
        "age_max": "30-32 Years",
        "total_posts": "17,727 Posts",
        "vacancy_rows": [
            ("Assistant Audit Officer (AAO) List-1", "Merit List 1", "Shortlisted for Tier-2 Paper 1 and Paper 2."),
            ("Junior Statistical Officer (JSO) List-2", "Merit List 2", "Shortlisted for Tier-2 Paper 1 and Paper 2 (Statistics)."),
            ("All Other Posts (List-3)", "Merit List 3", "Shortlisted for Tier-2 Paper 1 (Compulsory).")
        ],
        "how_to_apply": [
            "Visit the official SSC portal at ssc.gov.in.",
            "Navigate to Results section and click on CGL tab.",
            "Download List 1, List 2, and List 3 PDF documents.",
            "Search candidate Roll Number and Name in the appropriate list."
        ],
        "links": [
            ("Download Tier-1 Result (List 1)", "https://ssc.gov.in/", "Click Here"),
            ("Download Tier-1 Result (List 2)", "https://ssc.gov.in/", "Click Here"),
            ("Download Tier-1 Result (List 3)", "https://ssc.gov.in/", "Click Here"),
            ("SSC Official Website", "https://ssc.gov.in/", "Click Here")
        ],
        "faqs": [
            ("When will SSC CGL Tier 2 examination be held?", "SSC CGL Tier 2 is scheduled for October 2026.")
        ]
    },
    {
        "slug": "ssc-chsl-tier-1-result-2026",
        "title": "SSC CHSL (10+2) Tier 1 Result & Merit List 2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "05:30 pm",
        "short_desc": "Staff Selection Commission publishes Tier-1 Computer Based Examination results and cutoff marks for Combined Higher Secondary Level (10+2) Lower Division Clerk (LDC), Junior Secretariat Assistant (JSA), and Data Entry Operator (DEO) recruitments.",
        "start_date": "Tier-1 Exam: July 2026",
        "last_date": "Result Declared: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Tier-2 Exam: November 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "18 Years",
        "age_max": "27 Years",
        "total_posts": "3,712 Posts",
        "vacancy_rows": [
            ("LDC, JSA & DEO Posts", "3,712", "Candidates shortlisted for Tier-2 objective and skill/typing test.")
        ],
        "how_to_apply": [
            "Open the official SSC web portal at ssc.gov.in.",
            "Click on Result tab and choose CHSL section.",
            "Download the List of Shortlisted Candidates PDF.",
            "Search roll number in the document."
        ],
        "links": [
            ("Download CHSL Tier-1 Result PDF", "https://ssc.gov.in/", "Click Here"),
            ("Check Category-wise Cutoff", "https://ssc.gov.in/", "Click Here"),
            ("SSC Official Website", "https://ssc.gov.in/", "Click Here")
        ],
        "faqs": [
            ("Where to check SSC CHSL Tier-1 marks?", "Marks and scorecards are released on candidate dashboards at ssc.gov.in.")
        ]
    },
    {
        "slug": "rpsc-1st-grade-teacher-result-2025",
        "title": "RPSC 1st Grade School Lecturer Result & Cutoff 2025-2026",
        "category": "result",
        "post_date": "August 19, 2026",
        "post_time": "06:00 pm",
        "short_desc": "Rajasthan Public Service Commission (RPSC Ajmer) releases subject-wise provisional selection lists and cutoff scores for School Lecturer (School Education Department) examination.",
        "start_date": "Exam Date: 2025",
        "last_date": "Result: August 2026",
        "fee_last_date": "N/A",
        "exam_date": "Counselling: September 2026",
        "fee_gen": "Nil",
        "fee_res": "Nil",
        "age_min": "21 Years",
        "age_max": "40 Years",
        "total_posts": "6,000 Posts",
        "vacancy_rows": [
            ("School Lecturer (Various Subjects)", "6,000", "Provisional selection list for Document Verification and Counselling.")
        ],
        "how_to_apply": [
            "Visit rpsc.rajasthan.gov.in.",
            "Navigate to News and Events section.",
            "Click on Result Preamble and Cutoff Marks for School Lecturer.",
            "Download your subject specific result PDF."
        ],
        "links": [
            ("Download RPSC Result PDF", "https://rpsc.rajasthan.gov.in/", "Click Here"),
            ("RPSC Official Website", "https://rpsc.rajasthan.gov.in/", "Click Here")
        ],
        "faqs": [
            ("Where will RPSC document verification take place?", "Document counselling will be conducted at RPSC Commission office in Ajmer.")
        ]
    }
]

def generate_post_page(p):
    soup = BeautifulSoup(MASTER_BLUEPRINT, 'html.parser')

    title = p["title"]
    slug = p["slug"]
    category = p["category"]

    if soup.title:
        soup.title.string = f"{title} | STUDY TOPPER™"

    h1 = soup.find('h1')
    if h1:
        h1.string = title

    h2 = soup.find('h2')
    if h2:
        h2.string = f"{title} – Latest Details & Updates"

    h3 = soup.find('h3')
    if h3:
        h3.string = f"{title} : Short Details"

    time_tag = soup.find('time', class_='entry-date')
    if time_tag:
        time_tag.string = p["post_date"]
    
    post_time_span = soup.find(class_='custom-post-time')
    if post_time_span:
        post_time_span.string = p["post_time"]

    short_details_p = soup.find(class_='short_Details')
    if short_details_p:
        inner_p = short_details_p.find('p')
        if inner_p:
            inner_p.string = p["short_desc"]
        else:
            short_details_p.string = p["short_desc"]

    dates_box = soup.find(class_='gb-container-16a90584')
    if dates_box:
        ul = dates_box.find('ul')
        if ul:
            ul.clear()
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Online Apply Start Date : <strong>{p["start_date"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Online Apply Last Date : <span style="color: #ff0000;"><strong>{p["last_date"]}</strong></span></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Last Date For Fee Payment : <span style="color: #000000;"><strong>{p["fee_last_date"]}</strong></span></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 18.6667px;">Exam / Merit Date : <strong>{p["exam_date"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Candidates are advised to confirm from the official website.</span></li>', 'html.parser'))

    fee_box = soup.find(class_='gb-container-fcbb81ff')
    if fee_box:
        uls = fee_box.find_all('ul')
        if uls:
            uls[0].clear()
            uls[0].append(BeautifulSoup(f'<li><span style="font-size: 14pt;">For <strong>General/ OBC/ EWS</strong> : <strong>{p["fee_gen"]}</strong></span></li>', 'html.parser'))
            uls[0].append(BeautifulSoup(f'<li><span style="font-size: 14pt;">For <strong>SC/ ST/ PH / Female</strong> : <strong>{p["fee_res"]}</strong></span></li>', 'html.parser'))

    age_box = soup.find(class_='gb-container-0f18d865')
    if age_box:
        ul = age_box.find('ul')
        if ul:
            ul.clear()
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Minimum Age : <strong>{p["age_min"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Maximum Age : <strong>{p["age_max"]}</strong></span></li>', 'html.parser'))
            ul.append(BeautifulSoup(f'<li><span style="font-size: 14pt;">Age relaxation provided for reserved categories as per official regulations.</span></li>', 'html.parser'))

    total_post_badge = soup.find(class_='gb-headline-4259c0c2')
    if total_post_badge:
        total_post_badge.string = p["total_posts"]

    tables = soup.find_all('table')
    if len(tables) >= 2:
        elig_tbl = tables[1]
        elig_tbl.clear()
        
        tr_head = soup.new_tag('tr')
        th1 = soup.new_tag('th')
        th1.string = "Post Name"
        th2 = soup.new_tag('th')
        th2.string = "Total Posts"
        th3 = soup.new_tag('th')
        th3.string = "Eligibility Criteria"
        tr_head.append(th1)
        tr_head.append(th2)
        tr_head.append(th3)
        elig_tbl.append(tr_head)

        for name, count, reqs in p["vacancy_rows"]:
            tr = soup.new_tag('tr')
            td1 = soup.new_tag('td')
            td1.string = name
            td2 = soup.new_tag('td')
            td2.string = count
            td3 = soup.new_tag('td')
            td3.string = reqs
            tr.append(td1)
            tr.append(td2)
            tr.append(td3)
            elig_tbl.append(tr)

    if len(tables) >= 4:
        how_tbl = tables[3]
        tbody = how_tbl.find('tbody') or how_tbl
        rows = tbody.find_all('tr')
        if len(rows) >= 2:
            step_td = rows[1].find('td')
            if step_td:
                ol_steps = "".join([f"<li style='margin-bottom:6px;'>{s}</li>" for s in p["how_to_apply"]])
                step_td.clear()
                step_td.append(BeautifulSoup(f"<ol style='margin:0; padding-left:18px;'>{ol_steps}</ol>", 'html.parser'))

    if len(tables) >= 7:
        links_tbl = tables[6]
        links_tbl.clear()
        for lname, lurl, laction in p["links"]:
            color = "#00a82d" if "whatsapp" in lname.lower() else ("#0088cc" if "telegram" in lname.lower() else "#0000ef")
            tr = soup.new_tag('tr')
            td1 = soup.new_tag('td')
            td1.append(BeautifulSoup(f"<h5 style='margin:4px 0; font-weight:bold;'>{lname}</h5>", 'html.parser'))
            td2 = soup.new_tag('td')
            td2.append(BeautifulSoup(f"<h5 style='margin:4px 0;'><a href='{lurl}' target='_blank' rel='noopener noreferrer' style='color:{color}; font-weight:bold; text-decoration:underline;'>{laction}</a></h5>", 'html.parser'))
            tr.append(td1)
            tr.append(td2)
            links_tbl.append(tr)

    if len(tables) >= 8:
        faq_tbl = tables[7]
        faq_tbl.clear()
        tr_head = soup.new_tag('tr')
        td_head = soup.new_tag('td', colspan="2")
        td_head.append(BeautifulSoup(f"<strong style='font-size:15px; color:#0b213f;'>{title} : Frequently Asked Questions (FAQ)</strong>", 'html.parser'))
        tr_head.append(td_head)
        faq_tbl.append(tr_head)

        for q, a in p["faqs"]:
            tr_q = soup.new_tag('tr')
            td_q = soup.new_tag('td', colspan="2")
            td_q.append(BeautifulSoup(f"<strong>Q. {q}</strong><br><span style='color:#333333;'>Ans: {a}</span>", 'html.parser'))
            tr_q.append(td_q)
            faq_tbl.append(tr_q)

    # Save to pages/
    out_file = os.path.join(PAGES_DIR, f"{slug}.html")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    # Also save to raw_clone/pages/
    raw_file = os.path.join(RAW_CLONE_DIR, f"{slug}.html")
    with open(raw_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    print(f" [OK] Generated New Result Post: pages/{slug}.html")

    return {
        "id": f"post_{slug.replace('-', '_')}",
        "slug": slug,
        "title": title,
        "category": category,
        "short_desc": p["short_desc"],
        "application_start_date": p["start_date"],
        "application_last_date": p["last_date"],
        "custom_badge": "Result Declared",
        "tags": "Result, Govt Job Result, Study Topper",
        "created_at": datetime.datetime.now().isoformat()
    }

# Read existing posts
with open(os.path.join(DATA_DIR, 'custom_posts.json'), 'r', encoding='utf-8') as f:
    custom_posts = json.load(f)

# Generate and append new results
for nr in new_results:
    meta = generate_post_page(nr)
    # Insert at top of custom_posts
    custom_posts.insert(0, meta)

# Save updated json stores
with open(os.path.join(DATA_DIR, 'custom_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(custom_posts, f, indent=2)

with open(os.path.join(DATA_DIR, 'all_posts.json'), 'w', encoding='utf-8') as f:
    json.dump(custom_posts, f, indent=2)

# Update category_data.json
with open(os.path.join(DATA_DIR, 'category_data.json'), 'r', encoding='utf-8') as f:
    cat_data = json.load(f)

if 'result' not in cat_data:
    cat_data['result'] = []

for nr in reversed(new_results):
    cat_data['result'].insert(0, {
        'title': nr['title'],
        'url': f"/{nr['slug']}/",
        'short_desc': nr['short_desc'],
        'date': nr['start_date']
    })

with open(os.path.join(DATA_DIR, 'category_data.json'), 'w', encoding='utf-8') as f:
    json.dump(cat_data, f, indent=2)

# Update Homepage Result Column in pages/index.html & original_index.html
def update_index_results(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    result_col = soup.find(class_='gb-grid-column-0b76599a')
    if result_col:
        ul = result_col.find('ul')
        if ul:
            ul.clear()
            for item in cat_data['result'][:10]:
                li = soup.new_tag('li')
                a = soup.new_tag('a', href=item['url'], class_='wp-block-latest-posts__post-title')
                a.string = item['title']
                li.append(a)
                ul.append(li)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print(f" [OK] Updated Results column on {filepath}")

update_index_results(os.path.join(PAGES_DIR, 'index.html'))
update_index_results(os.path.join(BASE_DIR, 'original_index.html'))

print("All new Result posts added successfully!")
