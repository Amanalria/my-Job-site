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

def is_unwanted_line(t: str) -> bool:
    if not t:
        return True
    tl = str(t).lower()
    unwanted_tokens = [
        'question', 'answer', 'q.', 'ans.', 'you may also check',
        'related post', 'some useful', 'click here', 'whatsapp', 'telegram',
        'follow us', 'official website for', 'join group', 'what is the',
        'how to apply', 'frequently asked', 'contact us', 'disclaimer', 'privacy policy'
    ]
    return any(token in tl for token in unwanted_tokens)

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

    def get_reference_template(self, category: str = "latest-jobs") -> str:
        cat_file_map = {
            "latest-jobs": "reference_latest_jobs.html",
            "result": "reference_result.html",
            "admit-card": "reference_admit_card.html",
            "answer-key": "reference_answer_key.html",
            "syllabus": "reference_syllabus.html",
            "admission": "reference_admission.html"
        }
        ref_dir = os.path.join(self.base_dir, "templates", "reference")
        fname = cat_file_map.get(category.lower(), "reference_latest_jobs.html")
        fpath = os.path.join(ref_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                return f.read()

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

    def build_structured_faqs(self, data: Dict[str, Any], category: str, title: str) -> List[Tuple[str, str]]:
        org = data.get("organization", "Recruitment Board")
        last_date = data.get("last_date", "as per notification")
        total_posts = data.get("total_posts", "Various Posts")

        if category == "result":
            return [
                (f"How can I check the {title}?", f"Candidates can check their result by visiting the official portal or clicking the direct 'Download Result' link provided in the Important Links table above."),
                (f"What details are required to download {title} score card?", f"You will need your Application Number / Roll Number and Date of Birth / Password to access your scorecard."),
                (f"When was the {title} officially declared?", f"The result was officially declared on {data.get('important_dates', {}).get('Result Declared Date', 'August 2026')}."),
                (f"What is the next stage after {title} declaration?", f"Qualified candidates will be called for the next stage which may include Mains Exam, Physical Test, Skill Test, or Document Verification."),
                (f"Where can I find the cut-off marks for {title}?", f"Official category-wise cut-off marks are published along with the result write-up PDF on the official website.")
            ]
        elif category == "admit-card":
            return [
                (f"When will {title} be released?", f"The admit card is released 4 to 7 days before the exam date on the official website."),
                (f"How to download {title} online?", f"Click on 'Download Admit Card' link in the Useful Links section, enter your Registration Number and DOB, and download your call letter PDF."),
                (f"What documents are required along with {title} at the exam center?", f"Candidates must carry a clear printed copy of the Admit Card, original Photo ID proof (Aadhaar/PAN/Voter ID), and 2 passport photos."),
                (f"Is exam city slip and admit card the same for {org}?", f"No, exam city slip intimates your allotted test city in advance, while the admit card contains exact examination venue and reporting time."),
                (f"What should I do if there is an error in {title}?", f"Immediately contact the official {org} helpline email/phone number mentioned in the official notification before exam day.")
            ]
        elif category == "answer-key":
            return [
                (f"How to download {title}?", f"Candidates can download the answer key PDF directly from the links table above or through the official {org} portal."),
                (f"Can I challenge / raise objections on {title}?", f"Yes, candidates can submit online challenges against incorrect answer keys during the active objection window by paying the requisite challenge fee."),
                (f"What is the marking scheme for {title}?", f"Scores are calculated according to the official examination pattern (+1 or prescribed mark for correct answers, negative marking if applicable)."),
                (f"When will the final answer key be released?", f"The final answer key is released after reviewing all candidate objections submitted during the challenge period."),
                (f"Where can I check the objection challenge link?", f"The online objection link is provided in the Useful Important Links table on this page.")
            ]
        elif category == "syllabus":
            return [
                (f"What is the exam pattern for {title}?", f"The exam consists of Computer Based Tests / Written Exam covering relevant subjects, general studies, reasoning, and technical subjects as detailed above."),
                (f"Is there negative marking in {title}?", f"Yes, negative marking is applicable as per the official recruitment rules (typically 1/3rd or 1/4th mark deduction per wrong answer)."),
                (f"How to download {title} PDF in Hindi / English?", f"Click on the 'Download Syllabus PDF' link in the Important Links table to get the complete official syllabus booklet."),
                (f"What is the total duration of the examination for {org}?", f"Standard test duration ranges from 90 to 120 minutes depending on the paper scheme."),
                (f"What are the best preparation tips for {title}?", f"Focus on understanding the syllabus weightage, solving previous years' questions, and attempting regular mock tests.")
            ]
        elif category == "admission":
            return [
                (f"What is the eligibility criteria for {title}?", f"Candidates must hold the prescribed minimum qualifying educational degree from a recognized university as outlined in the matrix above."),
                (f"What is the last date to apply for {title}?", f"The last date for online registration and fee submission is {last_date}."),
                (f"How to fill {title} application form online?", f"Click on 'Apply Online' in the Useful Links section, complete registration, enter academic credentials, upload documents, and pay the admission fee."),
                (f"What is the selection process for {title}?", f"Selection is based on Entrance Examination scores, Written Ability Test / GD, Personal Interview, and composite merit rank."),
                (f"Where can I download the official information bulletin for {title}?", f"The official information bulletin PDF link is provided in the Important Links table above.")
            ]
        else: # latest-jobs
            return [
                (f"What is the last date to apply for {title}?", f"The last date for online submission of application is {last_date}."),
                (f"What is the age limit for {title}?", f"Candidate age should generally be between {data.get('min_age', '18 Years')} and {data.get('max_age', '40 Years')} as on {data.get('age_as_on', '01 August 2026')}. Age relaxation is applicable per rules."),
                (f"What is the application fee for {title}?", f"Application fee varies by category (e.g., General/OBC: {data.get('application_fee', {}).get('General / OBC / EWS', 'Rs. 100/-')}, SC/ST/PwD: {data.get('application_fee', {}).get('SC / ST / PwD', 'Exempted')})."),
                (f"How many total posts are available in {title}?", f"A total of {total_posts} have been officially announced for this recruitment drive."),
                (f"How can I apply online for {title}?", f"Eligible candidates can click the 'Apply Online' link in the Important Links table, register, fill details, resize photo/signature via indtool.in, and submit before {last_date}.")
            ]

    def build_bottom_sections_html(self, data: Dict[str, Any], category: str, title: str, slug: str) -> str:
        # Load app_cta settings if available
        settings = {}
        try:
            settings_file = "/root/sarkari-result-portal/data/settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as sf:
                    settings = json.load(sf)
        except Exception:
            pass

        app_cta = settings.get("app_cta", {})
        app_enabled = app_cta.get("enabled", True)
        app_title = app_cta.get("title", "StudyTopper.in")
        app_subtitle = app_cta.get("subtitle", "Fastest Government Job Updates, Results, Admit Cards & Exam Syllabus Portal")
        app_btn_text = app_cta.get("button_text", "📱 Download StudyTopper Mobile App & English Vocab")
        app_btn_url = app_cta.get("button_url", "https://play.google.com/store/apps/details?id=in.qmaths.blackbook")
        app_bg = app_cta.get("bg_color", "#fdfaf2")
        app_btn_bg = app_cta.get("button_color", "#046132")

        app_cta_html = ""
        if app_enabled and app_btn_text and app_btn_text.strip():
            app_cta_html = f'''<!-- SECTION 3: APP DOWNLOAD BANNER / CTA BOX -->
<div class="st-app-download-box gb-container gb-container-ce6e23c9" style="margin: 20px 0; text-align: center; background: {app_bg}; border: 1px solid #e2d7be; border-radius: 6px; padding: 16px;">
  <p class="gb-headline" style="margin: 0 0 6px 0;"><span style="font-size: 20px; font-weight: 800; color: #5b032f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{app_title}</span></p>
  <p style="margin: 6px 0 14px 0; font-size: 14.5px; color: #444444; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{app_subtitle}</p>
  <p style="margin: 0;">
    <a href="{app_btn_url}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: {app_btn_bg}; color: #ffffff; padding: 10px 22px; border-radius: 4px; text-decoration: none; font-size: 16px; font-weight: 700; box-shadow: 0 2px 6px rgba(0,0,0,0.15);">
      {app_btn_text}
    </a>
  </p>
</div>'''

        faqs = self.build_structured_faqs(data, category, title)
        faq_items_html = ""
        for idx, (q, a) in enumerate(faqs, 1):
            is_last = (idx == len(faqs))
            mb = "0" if is_last else "16px"
            faq_items_html += f'''<p style="margin: 0 0 4px 0;"><strong style="color: #000080;">Q{idx}. {q}</strong></p>
<p style="margin: 0 0 {mb} 0; color: #333333; line-height: 1.6;">Ans. {a}</p>'''

        latest_links = [
            ("IBPS Clerk 16th Recruitment 2026", "/ibps-clerk-16th-2026/"),
            ("Railway RRB Group D Admit Card 2026", "/railway-rrb-group-d-level-1-recruitment-2026-online/"),
            ("NTA SWAYAM Result 2026", "/nta-swayam-2026/"),
            ("RRB Junior Engineer JE Syllabus 2026", "/rrb-je-2026-syllabus/"),
            ("IIM CAT 2026 Admission Form", "/iim-cat-2026/")
        ]

        related_links = [
            ("UPSSSC PET Online Form 2026", "/upsssc-pet-2026/"),
            ("UPSSSC BCG Technician Answer Key 2026", "/upsssc-bcg-technician-2024/"),
            ("RPSC Rajasthan Police SI Telecom Result", "/rpsc-rajasthan-police-si-telecom-2025/"),
            ("SBI Junior Associates Clerk Recruitment", "/sbi-junior-associates-clerk-2026/"),
            ("SSC 10+2 CHSL 2025 FRTA Result", "/ssc-chsl-2026/")
        ]

        latest_html = "".join([f'<p style="margin: 6px 0; font-size: 14px;"><a href="{url}" style="color: #0056b3; text-decoration: none; font-weight: 600;">• {txt}</a></p>' for txt, url in latest_links])
        related_html = "".join([f'<p style="margin: 6px 0; font-size: 14px;"><a href="{url}" style="color: #0056b3; text-decoration: none; font-weight: 600;">• {txt}</a></p>' for txt, url in related_links])

        return f'''<!-- SECTION 1: FREQUENTLY ASKED QUESTIONS (FAQ - SIMPLE & CLEAN) -->
<div class="st-faq-section" style="margin: 25px 0 20px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <h3 style="color: #000080; font-size: 16.5px; font-weight: 700; border-bottom: 2px solid #000080; padding-bottom: 6px; margin: 0 0 16px 0;">
    {title} : Frequently Asked Questions (FAQ)
  </h3>
  <div style="font-size: 14.5px; line-height: 1.65; color: #222222;">
    {faq_items_html}
  </div>
</div>

<!-- SECTION 2: POST WEBP FEATURED IMAGE THUMBNAIL (OPTIMIZED FOR 100 PAGESPEED & 0 CLS) -->
<div class="st-post-thumbnail-box" style="text-align: center; margin: 25px 0 15px 0;">
  <img src="/static/thumbnails/{slug}.webp" alt="{title} StudyTopper" width="600" height="315" style="max-width: 100%; height: auto; border: 2px solid #ab183d; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.12); aspect-ratio: 1200/630;" loading="lazy" decoding="async" fetchpriority="low" />
</div>

{app_cta_html}

<!-- SECTION 4: LATEST POSTS & RELATED POSTS 2-COLUMN TABLE -->
<table style="width: 100%; border-collapse: collapse; margin: 20px 0; border: 1px solid #ddd; background: #ffffff;">
<tbody>
<tr>
  <td style="width: 50%; padding: 14px; vertical-align: top; border-right: 1px solid #ddd; background: #ffffff;">
    <h3 style="margin: 0 0 10px 0; color: #ef0303; font-size: 16px; font-weight: 700; border-bottom: 2px solid #ef0303; padding-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Latest Posts</h3>
    {latest_html}
  </td>
  <td style="width: 50%; padding: 14px; vertical-align: top; background: #ffffff;">
    <h3 style="margin: 0 0 10px 0; color: #000080; font-size: 16px; font-weight: 700; border-bottom: 2px solid #000080; padding-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Related Posts</h3>
    {related_html}
  </td>
</tr>
</tbody>
</table>

<!-- SECTION 5: SOCIAL CHANNELS BUTTONS -->
<div class="social-buttons" style="display: flex; gap: 12px; justify-content: flex-start; margin: 18px 0;">
  <a href="https://whatsapp.com/channel/0029Va9xyz" target="_blank" rel="noopener noreferrer" style="display: flex; align-items: center; padding: 9px 18px; border-radius: 5px; text-decoration: none; color: #ffffff; font-weight: 700; font-size: 14.5px; background-color: #25D366;">
    WhatsApp Channel
  </a>
  <a href="https://t.me/studytopperofficial" target="_blank" rel="noopener noreferrer" style="display: flex; align-items: center; padding: 9px 18px; border-radius: 5px; text-decoration: none; color: #ffffff; font-weight: 700; font-size: 14.5px; background-color: #0088cc;">
    Telegram Channel
  </a>
</div>

<!-- SECTION 6: OFFICIAL TRADEMARK & DISCLAIMER NOTICES -->
<p style="text-align: center; font-size: 13px; line-height: 1.5; color: #333333; margin: 15px 0 8px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <strong>Official Website of StudyTopper™ – StudyTopper.in | Since 2026 | Comprehensive Government Recruitment, Result, Admit Card & Syllabus Information Portal.</strong>
</p>
<p style="font-size: 11.5px; line-height: 1.5; color: #666666; text-align: justify; margin: 0 0 25px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <strong>Disclaimer:</strong> Information regarding examination forms, results, answer keys, admit cards, and syllabus published on StudyTopper.in is for immediate guidance and informational purposes only. While every attempt is made to ensure full accuracy with real verified destination links, StudyTopper does not claim legal liability for unintentional discrepancies. Candidates are requested to refer to the official gazette and official authority portal before taking action.
</p>'''

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
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{t}</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;"><a href="{u}" aria-label="{aria}" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" {target}>Click Here</a></span>
</td>
</tr>"""

        return rows_html

    def build_post_html(self, data: Dict[str, Any]) -> str:
        category = data.get("category", "latest-jobs").lower()
        template = self.get_reference_template(category)
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

        # 1. Clean Dates, Fee & Age Lists (Filter out any inline FAQs or questions)
        clean_dates = {k: v for k, v in data.get("important_dates", {}).items() if not is_unwanted_line(k) and not is_unwanted_line(v)}
        clean_fees = {k: v for k, v in data.get("application_fee", {}).items() if not is_unwanted_line(k) and not is_unwanted_line(v)}
        clean_ages = {k: v for k, v in data.get("age_limits", {}).items() if not is_unwanted_line(k) and not is_unwanted_line(v)}

        dates_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' if "Last Date" not in k else f'<li><span style="font-size: 14pt;">{k} : <span style="color: #ff0000;"><strong>{v}</strong></span></span></li>' for k, v in clean_dates.items()])
        fee_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' for k, v in clean_fees.items()])
        age_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' for k, v in clean_ages.items()])

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
        cat_table_html = ""
        if cat_rows:
            cat_table_html = f'''<table style="border-collapse: collapse; width: 100%; height: 150px;">
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
<p>&nbsp;</p>'''

        post_rows = ""
        for p_item in data.get("post_matrix", []):
            post_rows += f"""<tr>
<td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{p_item.get('name', '')}</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{p_item.get('posts', '')}</td>
<td style="padding: 8px; border: 1px solid #ddd;">{p_item.get('eligibility', '')}</td>
</tr>"""

        post_table_html = ""
        if post_rows:
            post_table_html = f'''<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th1}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th2}</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{tbl2_th3}</th>
</tr>
{post_rows}
</tbody>
</table>
<p>&nbsp;</p>'''

        how_to_steps = "".join([f'<li style="margin-bottom:6px; text-align: left !important;">{s}</li>' for s in data.get("how_to_fill", [])])
        if "indtool.in" not in how_to_steps and category in ["latest-jobs", "admission"]:
            how_to_steps += '<li style="margin-bottom:6px; text-align: left !important;">Resize candidate photograph and signature accurately using the <a href="https://indtool.in" rel="noopener" target="_blank"><strong>StudyTopper Tools</strong></a> image resizer at indtool.in.</li>'

        selection_li = "".join([f'<li style="text-align: left !important;"><span style="font-size: 14pt;"><strong>{s}</strong></span></li>' for s in data.get("selection_process", ["Computer Based Examination (CBE) / Written Exam", "Document Verification", "Medical Examination"])])

        bottom_sections = self.build_bottom_sections_html(data, category, title, slug)

        # Build Category-Tailored Useful Important Links
        important_links_rows = self.build_important_links_html(data, category, title)

        # Dynamic Extra Sections (Physical standards, Exam Centers, Additional Tables)
        extra_sections_html = data.get("extra_sections_html", "")

        main_content = f"""<main class="site-main" id="main">
<div class="gb-container gb-container-b39c368c">
<h1 class="gb-headline gb-headline-e52a0102 gb-headline-text" style="font-size: 22px; font-weight: 700; color: #0000cd; text-align: left; margin: 8px 0 4px 0; line-height: 1.3; width: 100%; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{title}</h1>
<div class="gb-container gb-container-659bd175"><p style="color: #cd0808; font-weight: 700; font-size: 15px; margin: 2px 0 7px 0; text-align: left; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">Post Date: {post_date}</p></div>
<p class="gb-headline gb-headline-550ae316 short_Details gb-headline-text" style="width: 100%; max-width: 100%; font-size: 16.8px; line-height: 1.55; color: #000000; text-align: justify; text-justify: inter-word; margin: 8px 0 14px 0; display: block; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{overview_html}</p>
<div class="gb-container gb-container-9849916c"><div class="social-buttons-compact" style="display: flex; justify-content: flex-start; align-items: center; gap: 10px; margin: 10px 0 16px 0; width: 100%;"><a class="social-btn-compact wa" href="https://whatsapp.com/channel/0029Va9xyz" rel="noopener" style="background-color: #00d084; color: #ffffff; padding: 10px 18px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 15.5px; display: inline-flex; align-items: center; justify-content: center; height: auto;" target="_blank">WhatsApp</a><a class="social-btn-compact tg" href="https://t.me/studytopperofficial" rel="noopener" style="background-color: #0088cc; color: #ffffff; padding: 10px 18px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 15.5px; display: inline-flex; align-items: center; justify-content: center; height: auto;" target="_blank">Telegram</a></div></div>
<div class="gb-container gb-container-f58e6ca1" style="border: 2px solid #5b032f; border-radius: 4px; overflow: hidden; margin: 15px 0 20px 0; background-color: #ffffff; width: 100%; box-sizing: border-box;">
<h2 class="gb-headline gb-headline-2ca5a791 gb-headline-text" style="font-size: 16px; font-weight: 700; text-align: center; color: #ef0303; line-height: 1.3; padding: 6px 4px; margin: 0; background: #ffffff; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{title} &ndash; Latest Details &amp; Updates</h2>
<h3 class="gb-headline gb-headline-7d5f86e8 gb-headline-text" style="font-size: 16px; font-weight: 600; text-align: center; color: #009703; line-height: 1.25; margin: 0; padding: 2px 4px 6px 4px; background: #ffffff; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{org} : Details &amp; Summary</h3>
<p class="gb-headline gb-headline-79adf169 gb-headline-text" style="margin: 0 0 6px 0; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif; text-align: center; font-size: 18px; font-weight: 700;"><a href="/" style="color: #0000ff; text-decoration: underline;">StudyTopper.in</a></p>

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
    <div style="background-color: #5b032f; color: #ffffff; padding: 8px 10px; font-size: 20px; font-weight: 700; text-align: center; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{box1_left_title}</div>
    <div style="padding: 12px 14px; background-color: #ffffff;">
      <ul style="padding-left: 20px; margin: 0; list-style-type: disc; text-align: left; font-size: 14pt; line-height: 1.6; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">
        {dates_li}
      </ul>
    </div>
  </div>
  <!-- Right Col: Application Fee -->
  <div class="st-col-half" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #5b032f; color: #ffffff; padding: 8px 10px; font-size: 20px; font-weight: 700; text-align: center; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{box1_right_title}</div>
    <div style="padding: 12px 14px; background-color: #ffffff;">
      <ul style="padding-left: 20px; margin: 0; list-style-type: disc; text-align: left; font-size: 14pt; line-height: 1.6; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">
        {fee_li}
      </ul>
      <div style="margin-top: 10px; font-size: 14pt; line-height: 1.5; color: #000000; border-top: 1px dashed #ccc; padding-top: 8px; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">
        <strong>Mode of Payment / Access:</strong> Online via Net Banking, Debit Card, Credit Card, UPI or Free Candidate Portal.
      </div>
    </div>
  </div>
</div>

<!-- RESPONSIVE 2-COL BOX 2: AGE LIMITS & TOTAL POST -->
<div class="st-grid-row" style="display: flex; flex-wrap: wrap; width: 100%; border-top: 2px solid #5b032f; margin: 0; padding: 0; box-sizing: border-box;">
  <!-- Left Col: Age Limits -->
  <div class="st-col-half st-col-border-right" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #046132; color: #ffffff; padding: 8px 10px; font-size: 17px; font-weight: 700; text-align: center; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{box2_left_title}</div>
    <div style="padding: 12px 14px; background-color: #ffffff;">
      <ul style="padding-left: 20px; margin: 0; list-style-type: disc; text-align: left; font-size: 14pt; line-height: 1.6; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">
        {age_li}
      </ul>
    </div>
  </div>
  <!-- Right Col: Total Post -->
  <div class="st-col-half" style="box-sizing: border-box; vertical-align: top;">
    <div style="background-color: #f53c00; color: #ffffff; padding: 8px 10px; font-size: 20px; font-weight: 700; text-align: center; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{box2_right_title}</div>
    <div style="padding: 24px 10px; background-color: #ffffff; text-align: center;">
      <span style="font-size: 28px; font-weight: 800; color: #000000; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{total_posts}</span>
    </div>
  </div>
</div>
</div>

<!-- Study Topper -->
<ins class="adsbygoogle" data-ad-client="ca-pub-9762662687323163" data-ad-format="auto" data-ad-slot="7596594071" data-full-width-responsive="true" style="display:block"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
<div class="gb-container gb-container-ec1f6e4c">
<h2 class="gb-headline gb-headline-c7683bda gb-headline-text" style="font-size: 24px; font-weight: 800; text-align: center; color: #ef0303; line-height: 1.35; margin: 20px 0 12px 0; padding: 6px 4px; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">{title} : Key Overview &amp; Matrix</h2>
<div class="gb-headline gb-headline-60ccea19 gb-headline-text">
{cat_table_html}
{post_table_html}
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

<!-- Study Topper -->
<ins class="adsbygoogle" data-ad-client="ca-pub-9762662687323163" data-ad-format="auto" data-ad-slot="7596594071" data-full-width-responsive="true" style="display:block"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
<div class="gb-container gb-container-761d9c16">
<table style="border-collapse: collapse; width: 100%; border: 1px solid #000000; margin-bottom: 20px;">
<tbody>
<tr style="border-bottom: 1px solid #000000; background-color: #ffffff;">
<td colspan="2" style="padding: 12px 14px; text-align: center;">
<h3 style="margin: 0; color: #ff0000; font-size: 20px; font-weight: 800; text-transform: uppercase; font-family: '-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif', Times, serif, Hind, sans-serif;">SOME USEFUL IMPORTANT LINKS</h3>
</td>
</tr>
{important_links_rows}
</tbody>
</table>
<p>&nbsp;</p>
{bottom_sections}
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
            import textwrap

            # 1. Load Real Base Image
            base_img_path = os.path.join(self.static_dir, "images", "studytopper_banner_base.webp")
            if not os.path.exists(base_img_path):
                base_img_path = os.path.join(self.static_dir, "images", "base_templates", "template_1_classic_crimson.webp")
            
            if os.path.exists(base_img_path):
                img = Image.open(base_img_path).convert('RGB')
            else:
                width, height = 640, 330
                img = Image.new('RGB', (width, height), color='#ffffff')

            draw = ImageDraw.Draw(img)
            width, height = img.size
            
            font_bold_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
            
            def get_f(size):
                try:
                    return ImageFont.truetype(font_bold_path, size)
                except Exception:
                    return ImageFont.load_default()

            # Title Wrap & Render on Base Image
            clean_title = data.get("title", "Govt Recruitment 2026").strip()
            lines = textwrap.wrap(clean_title, width=32)
            if len(lines) > 2:
                lines = lines[:2]
                lines[1] = lines[1][:28] + "..."

            if len(lines) == 1:
                title_font_size = 23
                title_y = 112
                line_spacing = 0
            else:
                title_font_size = 19
                title_y = 96
                line_spacing = 25

            title_font = get_f(title_font_size)
            for i, line in enumerate(lines):
                y = title_y + (i * line_spacing)
                draw.text((width // 2, y), line, fill='#0b213f', font=title_font, anchor='mm')

            # Meta Line (Posts & Last Date in Red/Crimson)
            meta_y = 162 if len(lines) == 1 else 170
            category = data.get("category", "latest-jobs").lower()
            
            meta_parts = []
            if category == "result":
                meta_parts.append("Result Declared")
                meta_parts.append("Score Card Available")
            elif category == "admit-card":
                meta_parts.append("Admit Card Active")
                meta_parts.append(f"Exam: {data.get('exam_date', 'Upcoming')}")
            elif category == "answer-key":
                meta_parts.append("Answer Key Released")
                meta_parts.append("Objection Active")
            elif category == "syllabus":
                meta_parts.append("Exam Syllabus PDF")
                meta_parts.append("Pattern & Marking")
            else: # latest-jobs / admission
                tot_p = data.get("total_posts", "")
                if tot_p:
                    posts_str = str(tot_p).strip()
                    if not posts_str.lower().endswith("posts") and not posts_str.lower().endswith("post") and not posts_str.lower().endswith("seats"):
                        posts_str += " Posts"
                    meta_parts.append(f"Total Posts: {posts_str}")
                else:
                    meta_parts.append("Official Notification")
                
                ld = data.get("last_date", "")
                if ld:
                    meta_parts.append(f"Last Date: {ld}")
                else:
                    meta_parts.append("Apply Online Active")

            meta_text = "   |   ".join(meta_parts)
            meta_font = get_f(15 if len(meta_text) < 45 else 13)
            draw.text((width // 2, meta_y), meta_text, fill='#b91c1c', font=meta_font, anchor='mm')

            # Subtitle / Organization Line
            sub_y = meta_y + 44
            sub_text = f"Organization: {data.get('organization', 'Govt Authority')[:40]} • 100% Real Updates"
            sub_font = get_f(12)
            draw.text((width // 2, sub_y), sub_text, fill='#475569', font=sub_font, anchor='mm')

            # Save WebP strictly < 15KB
            img.save(out_path, 'WEBP', quality=85, method=6)
            print(f"[Thumbnail] Generated on Base Image: {out_path} ({os.path.getsize(out_path)/1024.0:.1f} KB)")
        except Exception as e:
            print(f"[Thumbnail Error] {e}")
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
