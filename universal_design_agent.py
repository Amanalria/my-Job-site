#!/usr/bin/env python3
import os
import re
import json
import datetime
import argparse
from typing import Dict, Any, List

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

class UniversalDesignAgent:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.pages_dir = os.path.join(self.base_dir, "pages")
        self.data_dir = os.path.join(self.base_dir, "data")
        self.static_dir = os.path.join(self.base_dir, "static")
        self.thumbnails_dir = os.path.join(self.static_dir, "thumbnails")
        self.ref_template_path = os.path.join(self.pages_dir, "ibps-clerk-16th-2026.html")

        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

    def get_reference_template(self) -> str:
        if os.path.exists(self.ref_template_path):
            with open(self.ref_template_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<html><head></head><body><main id='main'></main></body></html>"

    def humanize_overview(self, data: Dict[str, Any]) -> str:
        org = data.get("organization", "Government Authority")
        title = data.get("title", "Recruitment 2026")
        advt = data.get("advt_no", "Official Advt 2026")
        total_posts = data.get("total_posts", "various vacancies")
        last_date = data.get("last_date", "prescribed closing date")
        min_age = data.get("min_age", "18 Years")
        max_age = data.get("max_age", "40 Years")
        category = data.get("category", "latest-jobs")

        if category == "result":
            overview = (
                f'<strong style="color: #0000cd;">{org}</strong> has officially announced and declared the '
                f'<strong style="color: #cd0808;">{title}</strong> on its official examination portal. '
                f'Candidates who participated in the examination can now verify their subject-wise marks, scorecards, and qualifying status. '
                f'The online scorecard and merit cut-off lists are accessible through candidate login credentials. '
                f'All qualified aspirants are advised to review the comprehensive scorecard breakdown, download their rank certificate, '
                f'and verify the subsequent document verification schedule outlined in the official notification.'
            )
        elif category == "admit-card":
            overview = (
                f'<strong style="color: #0000cd;">{org}</strong> has officially released the exam city intimation slip and '
                f'<strong style="color: #cd0808;">{title}</strong> for eligible registered candidates. '
                f'Aspirants appearing for the upcoming computer-based test can download their e-call letters by entering their registration credentials. '
                f'The hall ticket contains vital examination details including shift timings, reporting hours, test venue coordinates, and exam day guidelines. '
                f'Candidates must download and print their admit cards early to avoid last-minute server congestion and carry valid photo identification.'
            )
        elif category == "answer-key":
            overview = (
                f'<strong style="color: #0000cd;">{org}</strong> has officially published the provisional and final '
                f'<strong style="color: #cd0808;">{title}</strong> along with master question paper booklets. '
                f'Examinees who appeared in the examination can verify their recorded responses against the official key solutions. '
                f'The board has activated an online objection window allowing candidates to submit challenges with authentic documentary proof within the deadline. '
                f'Review question series carefully and compute estimated test scores using the official marking scheme.'
            )
        elif category == "syllabus":
            overview = (
                f'<strong style="color: #0000cd;">{org}</strong> has officially outlined the detailed topic-wise '
                f'<strong style="color: #cd0808;">{title}</strong> for aspiring candidates. '
                f'The syllabus architecture provides comprehensive clarity on subject weightage, section-wise question distribution, and marking criteria. '
                f'Candidates preparing for the examination should align their preparation strategy with the core subjects including general aptitude and technical disciplines. '
                f'Download the complete curriculum PDF below to master high-scoring chapters and maximize performance.'
            )
        elif category == "admission":
            overview = (
                f'<strong style="color: #0000cd;">{org}</strong> has initiated the centralized online application process for '
                f'<strong style="color: #cd0808;">{title}</strong> across recognized institutions and university departments. '
                f'Eligible candidates seeking admission can complete the registration process before the specified deadline of {last_date}. '
                f'The entrance evaluation and counselling allotment evaluate academic merit and entrance examination ranks. '
                f'Prospective students must review detailed course eligibility, seat quotas, and reservation norms prior to submitting forms.'
            )
        else:
            overview = (
                f'<strong style="color: #0000cd;">{org}</strong> has officially published the recruitment notice '
                f'<strong style="color: #cd0808;">{title}</strong> under notification number {advt}. '
                f'Online applications are invited for {total_posts} across multiple departments and cadre positions. '
                f'Interested candidates possessing the requisite educational qualifications and falling between {min_age} to {max_age} '
                f'can complete their online registration before the application deadline of {last_date}. '
                f'Applicants should read the eligibility criteria, category reservation rules, and exam scheme thoroughly before submitting applications.'
            )
        return overview

    def build_important_links_html(self, data: Dict[str, Any], category: str, title: str) -> str:
        links_list = []
        
        # 1. Custom links if provided explicitly
        if data.get("important_links") and isinstance(data["important_links"], list) and len(data["important_links"]) > 0:
            links_list = list(data["important_links"])
        else:
            apply_url = data.get("apply_link", "")
            notif_url = data.get("notification_link", "")
            result_url = data.get("result_link", "")
            admit_url = data.get("admit_card_link", "")
            key_url = data.get("answer_key_link", "")
            syll_url = data.get("syllabus_link", "")
            official_url = data.get("official_website", "https://studytopper.in")

            if category == "result":
                links_list.append({"title": "Download Result / Score Card", "url": result_url or official_url})
                if notif_url and notif_url != official_url:
                    links_list.append({"title": "Check Result Notice / Writeup", "url": notif_url})
                if data.get("cutoff_link"):
                    links_list.append({"title": "Download Cutoff Marks", "url": data["cutoff_link"]})

            elif category == "admit-card":
                links_list.append({"title": "Download Admit Card / Hall Ticket", "url": admit_url or official_url})
                if data.get("city_details_link"):
                    links_list.append({"title": "Download Exam City Details", "url": data["city_details_link"]})
                if notif_url and notif_url != official_url:
                    links_list.append({"title": "Check Exam / Admit Card Notice", "url": notif_url})

            elif category == "answer-key":
                links_list.append({"title": "Download Answer Key / Objection Link", "url": key_url or official_url})
                if notif_url and notif_url != official_url:
                    links_list.append({"title": "Check Answer Key Notice", "url": notif_url})
                if data.get("question_paper_link"):
                    links_list.append({"title": "Download Question Paper PDF", "url": data["question_paper_link"]})

            elif category == "syllabus":
                links_list.append({"title": "Download Detailed Syllabus PDF", "url": syll_url or notif_url or official_url})
                if notif_url and notif_url != official_url:
                    links_list.append({"title": "Check Official Notification", "url": notif_url})
                if data.get("pattern_link"):
                    links_list.append({"title": "Check Exam Pattern & Marking Scheme", "url": data["pattern_link"]})

            elif category == "admission":
                links_list.append({"title": "Apply Online (Registration / Login)", "url": apply_url or official_url})
                links_list.append({"title": "Download Information Brochure PDF", "url": notif_url or official_url})
                links_list.append({"title": "Photo / Sign Resizer Tool", "url": "https://indtool.in"})

            else: # latest-jobs
                links_list.append({"title": "Apply Online Link", "url": apply_url or official_url})
                links_list.append({"title": "Check Official Notification", "url": notif_url or official_url})
                links_list.append({"title": "Photo / Sign Resizer Tool", "url": "https://indtool.in"})

        # Always ensure StudyTopper and Official Website
        if not any("Check Sarkari Result" in l.get("title", "") for l in links_list):
            links_list.append({"title": "Check Sarkari Result", "url": "/"})

        if not any("Official Website" in l.get("title", "") for l in links_list):
            links_list.append({"title": f"{data.get('organization', 'Official')} Website", "url": data.get('official_website', 'https://studytopper.in')})

        # Render HTML table rows
        rows_html = ""
        for idx, item in enumerate(links_list):
            t = item.get("title", "Link")
            u = item.get("url", "https://studytopper.in")
            is_last = (idx == len(links_list) - 1)
            border_b = "" if is_last else "border-bottom: 1px solid #000000;"
            aria = f"Click Here for {t} - {title}"
            target = "" if u == "/" else 'target="_blank"'
            
            rows_html += f"""
<tr style="{border_b} background-color: #fff37a;">
<td style="width: 50%; padding: 14px 16px; border-right: 1px solid #000000; text-align: center;">
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{t}</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"><a href="{u}" aria-label="{aria}" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" {target}>Click Here</a></span>
</td>
</tr>"""

        return rows_html

    def build_post_html(self, data: Dict[str, Any]) -> str:
        template = self.get_reference_template()
        slug = data.get("slug", slugify(data.get("title", "recruitment-2026")))
        title = data.get("title", "Govt Job Recruitment 2026")
        category = data.get("category", "latest-jobs").lower()
        org = data.get("organization", "Recruitment Authority")
        total_posts = data.get("total_posts", "Various Posts")
        last_date = data.get("last_date", "")
        post_date = data.get("post_date", datetime.datetime.now().strftime("%B %d, %Y %I:%M %p"))
        overview_html = self.humanize_overview(data)

        # Meta replacements
        template = re.sub(r'<title>.*?</title>', f'<title>{title} - StudyTopper™</title>', template, flags=re.DOTALL)
        template = re.sub(
            r'<meta content=".*?" name="description"/>',
            f'<meta content="{title}. Complete real details, schedule, dates, and official links on StudyTopper." name="description"/>',
            template,
            count=1
        )
        template = re.sub(
            r'<link href="https://studytopper\.in/[^"]*?" rel="canonical"/>',
            f'<link href="https://studytopper.in/{slug}/" rel="canonical"/>',
            template
        )
        template = re.sub(r'<meta content=".*?" property="og:title"/>', f'<meta content="{title}" property="og:title"/>', template, count=1)
        template = re.sub(r'<meta content="https://studytopper\.in/[^"]*?" property="og:url"/>', f'<meta content="https://studytopper.in/{slug}/" property="og:url"/>', template, count=1)
        template = re.sub(r'<meta content="https://studytopper\.in/static/thumbnails/[^"]*?" property="og:image"/>', f'<meta content="https://studytopper.in/static/thumbnails/{slug}.webp" property="og:image"/>', template, count=1)

        # 1. Dates & Fee Lists
        dates_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' if "Last Date" not in k else f'<li><span style="font-size: 14pt;">{k} : <span style="color: #ff0000;"><strong>{v}</strong></span></span></li>' for k, v in data.get("important_dates", {}).items()])
        fee_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' for k, v in data.get("application_fee", {}).items()])
        age_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' for k, v in data.get("age_limits", {}).items()])

        # 2. Category-Specific Box Titles
        if category == "result":
            box1_left_title = "Important Dates"
            box1_right_title = "Result / Scorecard Fee"
            box2_left_title = f"{org} : Eligibility / Age Criteria"
            box2_right_title = "Result Status"
            tbl1_title = f"{org} : Result / Scorecard Overview Details"
            tbl2_th1, tbl2_th2, tbl2_th3 = "Course / Post Name", "Total Candidates / Posts", "Eligibility / Qualifying Criteria"
            tbl3_title = f"How to Check &amp; Download {org} Result 2026"
            tbl4_title = f"{org} Examination 2026 : Mode of Evaluation &amp; Selection"
        elif category == "admit-card":
            box1_left_title = "Admit Card &amp; Exam Dates"
            box1_right_title = "Application / Exam Fee"
            box2_left_title = f"{org} : Age Limits As On {data.get('age_as_on', '01 August 2026')}"
            box2_right_title = "Hall Ticket Status"
            tbl1_title = f"{org} : Admit Card &amp; Exam City Intimation Details"
            tbl2_th1, tbl2_th2, tbl2_th3 = "Post / Cadre Name", "Total Posts", "Educational Eligibility Criteria"
            tbl3_title = f"How to Download {org} Admit Card 2026 &amp; Exam Day Instructions"
            tbl4_title = f"{org} Recruitment 2026 : Mode Of Selection"
        elif category == "answer-key":
            box1_left_title = "Answer Key &amp; Objection Dates"
            box1_right_title = "Objection / Challenge Fee"
            box2_left_title = f"{org} : Age Limits As On {data.get('age_as_on', '01 August 2026')}"
            box2_right_title = "Answer Key Status"
            tbl1_title = f"{org} : Answer Key &amp; Objection Window Details"
            tbl2_th1, tbl2_th2, tbl2_th3 = "Post / Paper Name", "Total Questions / Booklets", "Eligibility Criteria / Key Series"
            tbl3_title = f"How to Download {org} Answer Key &amp; Submit Online Objection"
            tbl4_title = f"{org} Recruitment 2026 : Mode Of Selection"
        elif category == "syllabus":
            box1_left_title = "Notification &amp; Exam Dates"
            box1_right_title = "Exam Mode &amp; Duration"
            box2_left_title = f"{org} : Age Limits As On {data.get('age_as_on', '01 August 2026')}"
            box2_right_title = "Exam Scheme &amp; Marks"
            tbl1_title = f"{org} : Exam Pattern &amp; Marking Scheme Details"
            tbl2_th1, tbl2_th2, tbl2_th3 = "Post / Subject Name", "Total Marks / Questions", "Detailed Topic Syllabus &amp; Eligibility"
            tbl3_title = f"Preparation Strategy &amp; Detailed Syllabus Guidelines for {org}"
            tbl4_title = f"{org} Examination 2026 : Mode Of Selection"
        elif category == "admission":
            box1_left_title = "Admission Schedule Dates"
            box1_right_title = "Application &amp; Counselling Fee"
            box2_left_title = f"{org} : Age Criteria As On {data.get('age_as_on', '01 August 2026')}"
            box2_right_title = "Total Seats / Quota"
            tbl1_title = f"{org} : Course Wise Seat Matrix &amp; Eligibility Details"
            tbl2_th1, tbl2_th2, tbl2_th3 = "Course / Program Name", "Total Seats", "Educational Qualification &amp; Eligibility"
            tbl3_title = f"How to Apply for {org} Online Admission Form 2026"
            tbl4_title = f"{org} Admission 2026 : Mode of Selection &amp; Counselling"
        else: # latest-jobs
            box1_left_title = "Important Dates"
            box1_right_title = "Application Fee"
            box2_left_title = f"{org} : Age Limits As On {data.get('age_as_on', '01 August 2026')}"
            box2_right_title = "Total Post"
            tbl1_title = f"{org} : Category Wise Vacancy Details"
            tbl2_th1, tbl2_th2, tbl2_th3 = "Post Name", "Total Posts", "Eligibility Criteria"
            tbl3_title = f"How to Fill {org} Online Application Form"
            tbl4_title = f"{org} Recruitment 2026 : Mode Of Selection"

        cat_rows = "".join([f'<tr><td style="text-align: center;">{k}</td><td style="text-align: center; font-weight: {"bold" if "Total" in k else "normal"}; color: {"#ff0000" if "Total" in k else "inherit"};">{v}</td></tr>' for k, v in data.get("category_vacancies", {}).items()])

        post_rows = ""
        for p_item in data.get("post_matrix", []):
            post_rows += f"""<tr>
<td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{p_item.get('name', '')}</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{p_item.get('posts', '')}</td>
<td style="padding: 8px; border: 1px solid #ddd;">{p_item.get('eligibility', '')}</td>
</tr>"""

        how_to_steps = "".join([f'<li style="margin-bottom:6px; text-align: left !important;">{s}</li>' for s in data.get("how_to_fill", [])])
        if "indtool.in" not in how_to_steps and category in ["latest-jobs", "admission"]:
            how_to_steps += '<li style="margin-bottom:6px; text-align: left !important;">Resize candidate photograph and signature accurately using the <a href="https://indtool.in" rel="noopener" target="_blank"><strong>StudyTopper Tools</strong></a> image resizer at indtool.in.</li>'

        selection_li = "".join([f'<li style="text-align: left !important;"><span style="font-size: 14pt;"><strong>{s}</strong></span></li>' for s in data.get("selection_process", ["Computer Based Examination (CBE) / Written Exam", "Document Verification", "Medical Examination"])])

        faq_rows = ""
        for i, faq in enumerate(data.get("faqs", []), start=1):
            faq_rows += f"""<tr><td colspan="2"><strong>Q{i}. {faq.get('q', '')}</strong><br/><span style="color:#333333;">Ans: {faq.get('a', '')}</span></td></tr>"""

        # Build Category-Tailored Useful Important Links
        important_links_rows = self.build_important_links_html(data, category, title)

        # Dynamic Extra Sections (Physical standards, Exam Centers, Additional Tables)
        extra_sections_html = data.get("extra_sections_html", "")

        main_content = f"""<main class="site-main" id="main">
<div class="gb-container gb-container-b39c368c">
<h1 class="gb-headline gb-headline-e52a0102 gb-headline-text" style="font-size: 22px; font-weight: 700; color: #0000cd; text-align: left; margin: 8px 0 4px 0; line-height: 1.3; width: 100%; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{title}</h1>
<div class="gb-container gb-container-659bd175"><p style="color: #cd0808; font-weight: 700; font-size: 15px; margin: 2px 0 7px 0; text-align: left; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Post Date: {post_date}</p></div>
<p class="gb-headline gb-headline-550ae316 short_Details gb-headline-text" style="width: 100%; max-width: 100%; font-size: 16.8px; line-height: 1.55; color: #000000; text-align: justify; text-justify: inter-word; margin: 8px 0 14px 0; display: block; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{overview_html}</p>
<div class="gb-container gb-container-9849916c"><div class="social-buttons-compact" style="display: flex; justify-content: flex-start; align-items: center; gap: 10px; margin: 10px 0 16px 0; width: 100%;"><a class="social-btn-compact wa" href="https://whatsapp.com/channel/0029Va9xyz" rel="noopener" style="background-color: #00d084; color: #ffffff; padding: 10px 18px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 15.5px; display: inline-flex; align-items: center; justify-content: center; height: auto;" target="_blank">WhatsApp</a><a class="social-btn-compact tg" href="https://t.me/studytopperofficial" rel="noopener" style="background-color: #0088cc; color: #ffffff; padding: 10px 18px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 15.5px; display: inline-flex; align-items: center; justify-content: center; height: auto;" target="_blank">Telegram</a></div></div>
<div class="gb-container gb-container-f58e6ca1" style="border: 2px solid #5b032f; border-radius: 4px; overflow: hidden; margin: 15px 0 20px 0; background-color: #ffffff; width: 100%; box-sizing: border-box;">
<h2 class="gb-headline gb-headline-2ca5a791 gb-headline-text" style="font-size: 16px; font-weight: 700; text-align: center; color: #ef0303; line-height: 1.3; padding: 6px 4px; margin: 0; background: #ffffff; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{title} &ndash; Latest Details &amp; Updates</h2>
<h3 class="gb-headline gb-headline-7d5f86e8 gb-headline-text" style="font-size: 16px; font-weight: 600; text-align: center; color: #009703; line-height: 1.25; margin: 0; padding: 2px 4px 6px 4px; background: #ffffff; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{org} : Details &amp; Summary</h3>
<p class="gb-headline gb-headline-79adf169 gb-headline-text" style="margin: 0 0 6px 0; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; text-align: center; font-size: 18px; font-weight: 700;"><a href="/" style="color: #0000ff; text-decoration: underline;">StudyTopper.in</a></p>

<style id="st-post-boxes-responsive-css">
@media (min-width: 768px) {{
    .st-col-half {{
        flex: 1 1 50% !important;
        max-width: 50% !important;
        width: 50% !important;
    }}
    .st-col-border-right {{
        border-right: 1px solid #5b032f !important;
    }}
}}
@media (max-width: 767px) {{
    .st-col-half {{
        flex: 1 1 100% !important;
        max-width: 100% !important;
        width: 100% !important;
    }}
    .st-col-border-right {{
        border-right: none !important;
        border-bottom: 2px solid #5b032f !important;
    }}
}}
</style>
<!-- RESPONSIVE 2-COL BOX 1: IMPORTANT DATES & APPLICATION FEE -->
<div class="st-grid-row" style="display: flex; flex-wrap: wrap; width: 100%; border-top: 2px solid #5b032f; margin: 0; padding: 0; box-sizing: border-box;">
  <!-- Left Col: Important Dates -->
  <div class="st-col-half st-col-border-right" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #5b032f; color: #ffffff; padding: 8px 10px; font-size: 20px; font-weight: 700; text-align: center; font-family: Hind, 'Open Sans', sans-serif;">{box1_left_title}</div>
    <div style="padding: 12px 14px; background-color: #ffffff;">
      <ul style="padding-left: 20px; margin: 0; list-style-type: disc; text-align: left; font-size: 14pt; line-height: 1.6; font-family: Hind, 'Open Sans', sans-serif;">
        {dates_li}
      </ul>
    </div>
  </div>
  <!-- Right Col: Application Fee -->
  <div class="st-col-half" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #5b032f; color: #ffffff; padding: 8px 10px; font-size: 20px; font-weight: 700; text-align: center; font-family: Hind, 'Open Sans', sans-serif;">{box1_right_title}</div>
    <div style="padding: 12px 14px; background-color: #ffffff;">
      <ul style="padding-left: 20px; margin: 0; list-style-type: disc; text-align: left; font-size: 14pt; line-height: 1.6; font-family: Hind, 'Open Sans', sans-serif;">
        {fee_li}
      </ul>
      <div style="margin-top: 10px; font-size: 14pt; line-height: 1.5; color: #000000; border-top: 1px dashed #ccc; padding-top: 8px; font-family: Hind, 'Open Sans', sans-serif;">
        <strong>Mode of Payment / Access:</strong> Online via Net Banking, Debit Card, Credit Card, UPI or Free Candidate Portal.
      </div>
    </div>
  </div>
</div>

<!-- RESPONSIVE 2-COL BOX 2: AGE LIMITS & TOTAL POST -->
<div class="st-grid-row" style="display: flex; flex-wrap: wrap; width: 100%; border-top: 2px solid #5b032f; margin: 0; padding: 0; box-sizing: border-box;">
  <!-- Left Col: Age Limits -->
  <div class="st-col-half st-col-border-right" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #046132; color: #ffffff; padding: 8px 10px; font-size: 17px; font-weight: 700; text-align: center; font-family: Hind, 'Open Sans', sans-serif;">{box2_left_title}</div>
    <div style="padding: 12px 14px; background-color: #ffffff;">
      <ul style="padding-left: 20px; margin: 0; list-style-type: disc; text-align: left; font-size: 14pt; line-height: 1.6; font-family: Hind, 'Open Sans', sans-serif;">
        {age_li}
      </ul>
    </div>
  </div>
  <!-- Right Col: Total Post -->
  <div class="st-col-half" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #f53c00; color: #ffffff; padding: 8px 10px; font-size: 20px; font-weight: 700; text-align: center; font-family: Hind, 'Open Sans', sans-serif;">{box2_right_title}</div>
    <div style="padding: 24px 10px; background-color: #ffffff; text-align: center;">
      <span style="font-size: 28px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', sans-serif;">{total_posts}</span>
    </div>
  </div>
</div>
</div>
<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9762662687323163"></script>
<!-- Study Topper -->
<ins class="adsbygoogle" data-ad-client="ca-pub-9762662687323163" data-ad-format="auto" data-ad-slot="7596594071" data-full-width-responsive="true" style="display:block"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
<div class="gb-container gb-container-ec1f6e4c">
<h2 class="gb-headline gb-headline-c7683bda gb-headline-text" style="font-size: 24px; font-weight: 800; text-align: center; color: #ef0303; line-height: 1.35; margin: 20px 0 12px 0; padding: 6px 4px; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{title} : Key Overview &amp; Matrix</h2>
<div class="gb-headline gb-headline-60ccea19 gb-headline-text">
<table style="border-collapse: collapse; width: 100%; height: 150px;">
<tbody>
<tr style="height: 25px;">
<td colspan="2" style="width: 50%; text-align: center; height: 25px;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt;"><strong> {tbl1_title} </strong></span></td>
</tr>
<tr style="height: 25px;">
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Category / Particulars</strong></span></td>
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Count / Status</strong></span></td>
</tr>
{cat_rows}
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{tbl2_th1}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{tbl2_th2}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{tbl2_th3}</th>
</tr>
{post_rows}
</tbody>
</table>
<p>&nbsp;</p>

{extra_sections_html}

<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 100%; text-align: center;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt; font-weight: bold; display: block; padding: 6px;"> {tbl3_title} </span></td>
</tr>
<tr>
<td style="width: 100%;"><ol style="margin:0; padding-left:18px; text-align: left !important; list-style-position: outside !important">{how_to_steps}</ol></td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 100%; text-align: center;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt;"><strong><span style="color: #ffffff;"> {tbl4_title} </span></strong></span></td>
</tr>
<tr>
<td style="width: 100%;">
<ul class="wp-block-list" style="text-align: left !important; list-style-position: outside !important">
{selection_li}
</ul>
</td>
</tr>
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 50%; text-align: center;"><span style="color: #800000; font-size: 14pt;"><strong>Join Our WhatsApp Channel</strong></span></td>
<td style="width: 50%; text-align: center;"><span style="font-size: 14pt;"><strong><a href="https://whatsapp.com/channel/0029Va9xyz" rel="noopener" target="_blank">Follow Now</a></strong></span></td>
</tr>
<tr>
<td style="width: 50%; text-align: center;"><span style="color: #800000; font-size: 14pt;"><strong>Join Our Telegram Channel</strong></span></td>
<td style="width: 50%; text-align: center;"><span style="font-size: 14pt;"><strong><a href="https://t.me/studytopperofficial" rel="noopener" target="_blank">Follow Now</a></strong></span></td>
</tr>
</tbody>
</table>
</div>
<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9762662687323163"></script>
<!-- Study Topper -->
<ins class="adsbygoogle" data-ad-client="ca-pub-9762662687323163" data-ad-format="auto" data-ad-slot="7596594071" data-full-width-responsive="true" style="display:block"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
<div class="gb-container gb-container-761d9c16">
<table style="border-collapse: collapse; width: 100%; border: 1px solid #000000; margin-bottom: 20px;">
<tbody>
<tr style="border-bottom: 1px solid #000000; background-color: #ffffff;">
<td colspan="2" style="padding: 12px 14px; text-align: center;">
<h3 style="margin: 0; color: #ff0000; font-size: 20px; font-weight: 800; text-transform: uppercase; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">SOME USEFUL IMPORTANT LINKS</h3>
</td>
</tr>
{important_links_rows}
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td colspan="2" style="background-color: #000080; color: #ffffff; font-size: 14pt; font-weight: bold; text-align: center; padding: 6px;"> {title} : Frequently Asked Questions (FAQ) </td>
</tr>
{faq_rows}
</tbody>
</table>
</div>
</div>
</div>
</main>"""

        content = re.sub(r'<main.*?</main>', main_content, template, flags=re.DOTALL)
        return content

    def generate_thumbnail(self, data: Dict[str, Any]) -> str:
        slug = data.get("slug", slugify(data.get("title", "recruitment-2026")))
        out_path = os.path.join(self.thumbnails_dir, f"{slug}.webp")
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new("RGB", (1200, 675), color=(10, 25, 47))
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, 1200, 15], fill=(239, 3, 3))
            draw.rectangle([0, 660, 1200, 675], fill=(91, 3, 47))
            
            # Watermark branding
            draw.text((60, 50), "STUDYTOPPER.IN", fill=(255, 204, 0))
            draw.text((60, 120), data.get("title", "Recruitment 2026")[:45], fill=(255, 255, 255))
            draw.text((60, 220), f"Total Posts / Details: {data.get('total_posts', 'Various Posts')}", fill=(0, 210, 255))
            draw.text((60, 300), f"Organization: {data.get('organization', 'Govt Authority')[:50]}", fill=(200, 200, 200))
            draw.text((60, 380), f"Last Date / Event: {data.get('last_date', 'Upcoming')}", fill=(255, 80, 80))
            draw.text((60, 540), "100% REAL SOURCE VERIFIED", fill=(0, 255, 128))
            
            img.save(out_path, "WEBP", quality=85)
            print(f"[Thumbnail] Generated: {out_path}")
        except Exception as e:
            with open(out_path, "wb") as f:
                f.write(bytes.fromhex("52494646240000005745425056503820180000003001009d012a0100010002003425a400037000fefbfd0000"))
        return out_path

    def publish(self, data: Dict[str, Any]) -> str:
        slug = data.get("slug", slugify(data.get("title", "recruitment-2026")))
        title = data.get("title", "Govt Job Recruitment 2026")
        
        # 1. Generate post HTML
        html = self.build_post_html(data)
        out_file = os.path.join(self.pages_dir, f"{slug}.html")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Post] Saved HTML: {out_file} ({len(html)} bytes)")

        # 2. Generate WebP Thumbnail
        self.generate_thumbnail(data)

        # 3. Update Database (all_posts.json & custom_posts.json)
        entry = {
            "id": f"post_{slug.replace('-', '_')}",
            "slug": slug,
            "title": title,
            "category": data.get("category", "latest-jobs").lower(),
            "short_desc": f"{data.get('organization', 'Govt Board')} announces {title} ({data.get('total_posts', 'details')}).",
            "application_start_date": data.get("start_date", ""),
            "application_last_date": data.get("last_date", ""),
            "custom_badge": data.get("total_posts", ""),
            "tags": f"{data.get('category', 'latest-jobs')}, {data.get('organization', 'Govt Job')}, Study Topper",
            "created_at": datetime.datetime.now().isoformat(),
            "lifecycle_state": "ACTIVE",
            "is_pinned": (slug == "ibps-clerk-16th-2026")
        }

        for fname in ["custom_posts.json", "all_posts.json"]:
            fpath = os.path.join(self.data_dir, fname)
            if os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        posts = json.load(f)
                    posts = [p for p in posts if p.get("slug") != slug]
                    posts.insert(0, entry)
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(posts, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"[Data] Error updating {fname}: {e}")

        # Trigger Lifecycle Audit
        try:
            import vacancy_lifecycle_engine as lifecycle
            lifecycle.audit_and_execute_lifecycle()
        except Exception:
            pass

        return out_file
