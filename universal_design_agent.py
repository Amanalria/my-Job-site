#!/usr/bin/env python3
"""
StudyTopper™ Universal Design Publishing Agent (universal_design_agent.py)
Automates end-to-end recruitment post scraping, 100% humanizer rewriting,
WebP thumbnail generation, and multi-location publishing in strict Universal Design Standard.
"""

import os
import re
import sys
import json
import argparse
import datetime
from typing import Dict, Any, List, Optional
import urllib.request
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
THUMBNAILS_DIR = os.path.join(STATIC_DIR, "thumbnails")

sys.path.insert(0, BASE_DIR)
try:
    from thumbnail_generator import generate_post_thumbnail
except ImportError:
    generate_post_thumbnail = None


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def count_words(text: str) -> int:
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"[^\w\s]", " ", clean)
    return len(clean.split())


def clean_humanizer_text(text: str) -> str:
    """Enforces Wikipedia 35 Signs of AI Writing rules."""
    text = text.replace("—", " - ").replace("–", " - ")
    ai_cliches = [
        r"\bdelve\b", r"\btapestry\b", r"\btestament\b", r"\bbeacon\b",
        r"\bcrucial role\b", r"\bpivotal role\b", r"\bmultifaceted\b",
        r"\bcomprehensive guide\b", r"\bin conclusion\b", r"\blook no further\b"
    ]
    for pattern in ai_cliches:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


class UniversalDesignAgent:
    def __init__(self, base_dir: str = BASE_DIR):
        self.base_dir = base_dir
        self.pages_dir = os.path.join(base_dir, "pages")
        self.data_dir = os.path.join(base_dir, "data")
        self.thumbnails_dir = os.path.join(base_dir, "static", "thumbnails")
        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

    def get_reference_template(self) -> str:
        ref_candidates = [
            os.path.join(self.pages_dir, "rrb-je-2026.html"),
            os.path.join(self.pages_dir, "ssc-cgl-2026.html"),
            os.path.join(self.pages_dir, "railway-nfr-2026.html"),
            os.path.join(self.pages_dir, "index.html"),
            os.path.join(self.base_dir, "original_index.html"),
            os.path.join(self.base_dir, "raw_clone", "pages", "index.html")
        ]
        for ref in ref_candidates:
            if os.path.exists(ref):
                with open(ref, "r", encoding="utf-8") as f:
                    return f.read()
        raise FileNotFoundError("No reference GeneratePress template found!")

    def humanize_overview(self, data: Dict[str, Any]) -> str:
        """
        Generates 90-100 word overview in 100% human prose.
        Zero em-dashes, zero AI clichés, entity highlighting in bold blue/red.
        """
        org = data.get("organization", "Recruitment Board")
        title = data.get("title", "Recruitment 2026")
        advt = data.get("advt_no", "Advt No. 2026")
        total_posts = data.get("total_posts", "Various Posts")
        start_date = data.get("start_date", "Recently")
        last_date = data.get("last_date", "Upcoming")
        min_age = data.get("min_age", "18 Years")
        max_age = data.get("max_age", "30 Years")
        as_on_date = data.get("age_as_on", "01 August 2026")
        qualification = data.get("qualification_short", "prescribed educational qualification")

        p = (
            f'<strong style="color: #0000cd;">{org}</strong> has released the official recruitment '
            f'notification for <strong>{title}</strong> on its official web portal. '
            f'This recruitment drive offers <strong>{total_posts}</strong> across multiple zones and departments. '
            f'The online application process began on <strong>{start_date}</strong> and eligible candidates can submit '
            f'their applications before <strong>{last_date}</strong>. Applicants must be aged between '
            f'<strong>{min_age} and {max_age}</strong> as on <strong>{as_on_date}</strong> and hold {qualification}. '
            f'Candidates are advised to review eligibility conditions, syllabus, and application steps given below. '
            f'<strong style="color: #cd0808;">({advt})</strong>'
        )

        words = count_words(p)
        if words < 90:
            extra = f' Ensure all scanned certificates, photograph, and signature are verified before final form submission.'
            p = p.replace(f'<strong style="color: #cd0808;">({advt})</strong>', f'{extra} <strong style="color: #cd0808;">({advt})</strong>')
        elif words > 100:
            p = p.replace('across multiple zones and departments. ', '')
            p = p.replace('syllabus, and application steps ', 'and application steps ')

        return p

    def build_post_html(self, data: Dict[str, Any]) -> str:
        template = self.get_reference_template()
        slug = data.get("slug", slugify(data.get("title", "recruitment-2026")))
        title = data.get("title", "Govt Job Recruitment 2026")
        total_posts = data.get("total_posts", "Various Posts")
        last_date = data.get("last_date", "")
        post_date = data.get("post_date", datetime.datetime.now().strftime("%B %d, %Y %I:%M %p"))
        overview_html = self.humanize_overview(data)

        # Meta replacements
        template = re.sub(r'<title>.*?</title>', f'<title>{title} - StudyTopper™</title>', template, flags=re.DOTALL)
        template = re.sub(
            r'<meta content=".*?" name="description"/>',
            f'<meta content="{title}. Apply online for {total_posts} vacancies before {last_date} on StudyTopper." name="description"/>',
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

        # Build Main Section
        dates_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' if "Last Date" not in k else f'<li><span style="font-size: 14pt;">{k} : <span style="color: #ff0000;"><strong>{v}</strong></span></span></li>' for k, v in data.get("important_dates", {}).items()])
        fee_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' for k, v in data.get("application_fee", {}).items()])
        age_li = "".join([f'<li><span style="font-size: 14pt;">{k} : <strong>{v}</strong></span></li>' for k, v in data.get("age_limits", {}).items()])

        cat_rows = "".join([f'<tr><td style="text-align: center;">{k}</td><td style="text-align: center; font-weight: {"bold" if "Total" in k else "normal"}; color: {"#ff0000" if "Total" in k else "inherit"};">{v}</td></tr>' for k, v in data.get("category_vacancies", {}).items()])

        post_rows = ""
        for p_item in data.get("post_matrix", []):
            post_rows += f"""<tr>
<td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">{p_item.get('name', '')}</td>
<td style="padding: 8px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{p_item.get('posts', '')}</td>
<td style="padding: 8px; border: 1px solid #ddd;">{p_item.get('eligibility', '')}</td>
</tr>"""

        how_to_steps = "".join([f'<li style="margin-bottom:6px; text-align: left !important;">{s}</li>' for s in data.get("how_to_fill", [])])
        if "indtool.in" not in how_to_steps:
            how_to_steps += '<li style="margin-bottom:6px; text-align: left !important;">Resize candidate photograph and signature accurately using the <a href="https://indtool.in" rel="noopener" target="_blank"><strong>StudyTopper Tools</strong></a> image resizer at indtool.in.</li>'

        selection_li = "".join([f'<li style="text-align: left !important;"><span style="font-size: 14pt;"><strong>{s}</strong></span></li>' for s in data.get("selection_process", ["Computer Based Examination (CBE)", "Document Verification", "Medical Examination"])])

        faq_rows = ""
        for i, faq in enumerate(data.get("faqs", []), start=1):
            faq_rows += f"""<tr><td colspan="2"><strong>Q{i}. {faq.get('q', '')}</strong><br/><span style="color:#333333;">Ans: {faq.get('a', '')}</span></td></tr>"""

        important_links_rows = f"""
<tr style="border-bottom: 1px solid #000000; background-color: #fff37a;">
<td style="width: 50%; padding: 14px 16px; border-right: 1px solid #000000; text-align: center;">
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Apply Online Link</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"><a href="{data.get('apply_link', 'https://studytopper.in')}" aria-label="Click Here to Apply Online for {title}" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" target="_blank">Click Here</a></span>
</td>
</tr>
<tr style="border-bottom: 1px solid #000000; background-color: #fff37a;">
<td style="width: 50%; padding: 14px 16px; border-right: 1px solid #000000; text-align: center;">
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Check Official Notification</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"><a href="{data.get('notification_link', data.get('official_website', 'https://studytopper.in'))}" aria-label="Click Here to Download Official Notification for {title}" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" target="_blank">Click Here</a></span>
</td>
</tr>
<tr style="border-bottom: 1px solid #000000; background-color: #fff37a;">
<td style="width: 50%; padding: 14px 16px; border-right: 1px solid #000000; text-align: center;">
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Photo / Sign Resizer Tool</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"><a href="https://indtool.in" aria-label="Click Here for Photo and Signature Resizer Tool at IndTool" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" target="_blank">Click Here</a></span>
</td>
</tr>
<tr style="border-bottom: 1px solid #000000; background-color: #fff37a;">
<td style="width: 50%; padding: 14px 16px; border-right: 1px solid #000000; text-align: center;">
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Check Sarkari Result</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"><a href="/" aria-label="Click Here to Visit StudyTopper Home Page for Latest Jobs and Results" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" target="_blank">Click Here</a></span>
</td>
</tr>
<tr style="background-color: #fff37a;">
<td style="width: 50%; padding: 14px 16px; border-right: 1px solid #000000; text-align: center;">
<span style="font-size: 19px; font-weight: 800; color: #000000; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Official Website</span>
</td>
<td style="width: 50%; padding: 14px 16px; text-align: center;">
<span style="font-size: 20px; font-weight: 800; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;"><a href="{data.get('official_website', 'https://studytopper.in')}" aria-label="Click Here to Visit Official Website of {data.get('organization', 'Exam Board')}" rel="noopener noreferrer" style="color: #0000ef; font-weight: 800; text-decoration: none;" target="_blank">Click Here</a></span>
</td>
</tr>
"""

        main_content = f"""<main class="site-main" id="main">
<div class="gb-container gb-container-b39c368c">
<h1 class="gb-headline gb-headline-e52a0102 gb-headline-text" style="font-size: 22px; font-weight: 700; color: #0000cd; text-align: left; margin: 8px 0 4px 0; line-height: 1.3; width: 100%; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{title}</h1>
<div class="gb-container gb-container-659bd175"><p style="color: #cd0808; font-weight: 700; font-size: 15px; margin: 2px 0 7px 0; text-align: left; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Post Date: {post_date}</p></div>
<p class="gb-headline gb-headline-550ae316 short_Details gb-headline-text" style="width: 100%; max-width: 100%; font-size: 16.8px; line-height: 1.55; color: #000000; text-align: justify; text-justify: inter-word; margin: 8px 0 14px 0; display: block; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{overview_html}</p>
<div class="gb-container gb-container-9849916c"><div class="social-buttons-compact" style="display: flex; justify-content: flex-start; align-items: center; gap: 10px; margin: 10px 0 16px 0; width: 100%;"><a class="social-btn-compact wa" href="https://whatsapp.com/channel/0029Va9xyz" rel="noopener" style="background-color: #00d084; color: #ffffff; padding: 10px 18px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 15.5px; display: inline-flex; align-items: center; justify-content: center; height: auto;" target="_blank">WhatsApp</a><a class="social-btn-compact tg" href="https://t.me/studytopperofficial" rel="noopener" style="background-color: #0088cc; color: #ffffff; padding: 10px 18px; border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 15.5px; display: inline-flex; align-items: center; justify-content: center; height: auto;" target="_blank">Telegram</a></div></div>
<div class="gb-container gb-container-f58e6ca1">
<h2 class="gb-headline gb-headline-2ca5a791 gb-headline-text" style="font-size: 15.5px; font-weight: 700; text-align: center; color: #ef0303; line-height: 1.3; padding: 2px 2px; margin: 3px 0 1px 0; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{title} – Latest Details &amp; Updates</h2>
<h3 class="gb-headline gb-headline-7d5f86e8 gb-headline-text" style="font-size: 16px; font-weight: 600; text-align: center; color: #009703; line-height: 1.25; margin: 1px 0 2px 0; padding: 0; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">{data.get('organization', 'Recruitment')} Examination 2026 : Short Details</h3>
<p class="gb-headline gb-headline-79adf169 gb-headline-text" style="margin-top: 0; margin-bottom: 2px; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; text-align: center;"><a href="/">StudyTopper.in</a></p>
<div class="gb-grid-wrapper gb-grid-wrapper-303102a8">
<div class="gb-grid-column gb-grid-column-d96c68be"><div class="gb-container gb-container-d96c68be">
<div class="gb-container gb-container-16a90584">
<h4 class="gb-headline gb-headline-22b2e02b gb-headline-text"><strong>Important Dates</strong></h4>
<div class="gb-headline gb-headline-3b2f0e17 gb-headline-text"><ul style="text-align: left !important; list-style-position: outside !important">{dates_li}</ul></div>
</div>
</div></div>
<div class="gb-grid-column gb-grid-column-fcbb81ff"><div class="gb-container gb-container-fcbb81ff">
<h4 class="gb-headline gb-headline-4ddaf9ee gb-headline-text"><strong>Application Fee</strong></h4>
<div class="gb-headline gb-headline-989f3ffd gb-headline-text"><ul style="text-align: left !important; list-style-position: outside !important">{fee_li}</ul>
<ul style="text-align: left !important; list-style-position: outside !important">
<li style="text-align: left !important"><span style="font-size: 14pt;"><strong>Payment Mode (Online):</strong> Payment can be made using Debit Card, Credit Card, Net Banking, or UPI.</span></li>
</ul></div>
</div></div>
</div>
</div>
<div class="gb-container gb-container-6b6fbcac">
<div class="gb-grid-wrapper gb-grid-wrapper-8aa46b64">
<div class="gb-grid-column gb-grid-column-0f18d865"><div class="gb-container gb-container-0f18d865">
<h5 class="gb-headline gb-headline-0b3ada47 gb-headline-text">{data.get('organization', 'Recruitment')} : Age Limits As On {data.get('age_as_on', '01 August 2026')}</h5>
<div class="gb-headline gb-headline-28dede61 gb-headline-text"><ul style="text-align: left !important; list-style-position: outside !important">{age_li}</ul></div>
</div></div>
<div class="gb-grid-column gb-grid-column-860b2712"><div class="gb-container gb-container-860b2712">
<h5 class="gb-headline gb-headline-f2184b83 gb-headline-text"><strong>Total Post</strong></h5>
<div class="gb-headline gb-headline-4259c0c2 gb-headline-text">{total_posts}</div>
</div></div>
</div>
<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9762662687323163"></script>
<!-- Study Topper -->
<ins class="adsbygoogle" data-ad-client="ca-pub-9762662687323163" data-ad-format="auto" data-ad-slot="7596594071" data-full-width-responsive="true" style="display:block"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>
<div class="gb-container gb-container-ec1f6e4c">
<h6 class="gb-headline gb-headline-c7683bda gb-headline-text">{title} : Vacancy Details</h6>
<div class="gb-headline gb-headline-60ccea19 gb-headline-text">
<table style="border-collapse: collapse; width: 100%; height: 150px;">
<tbody>
<tr style="height: 25px;">
<td colspan="2" style="width: 50%; text-align: center; height: 25px;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt;"><strong> {data.get('organization', 'Recruitment')} : Category Wise Vacancy Details </strong></span></td>
</tr>
<tr style="height: 25px;">
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>Category</strong></span></td>
<td style="width: 50%; height: 25px; text-align: center;"><span style="font-size: 14pt;"><strong>No. Of Post</strong></span></td>
</tr>
{cat_rows}
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Post Name</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Total Posts</th>
<th style="background-color: #f53c00; color: #ffffff; padding: 6px 10px; text-align: center; border: 1px solid #d35400; font-size: 15px; font-weight: 700; font-family: Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">Eligibility Criteria</th>
</tr>
{post_rows}
</tbody>
</table>
<p>&nbsp;</p>
<table style="border-collapse: collapse; width: 100%;">
<tbody>
<tr>
<td style="width: 100%; text-align: center;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt; font-weight: bold; display: block; padding: 6px;"> How to Fill {data.get('organization', 'Recruitment')} Online Application Form </span></td>
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
<td style="width: 100%; text-align: center;"><span style="background-color: #000080; color: #ffffff; font-size: 14pt;"><strong><span style="color: #ffffff;"> {data.get('organization', 'Recruitment')} Recruitment 2026 : </span>Mode Of Selection </strong></span></td>
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
<tr><td colspan="2"><strong style="font-size:15px; color:#0b213f;">{title} : Frequently Asked Questions (FAQ)</strong></td></tr>
{faq_rows}
</table>
<p>&nbsp;</p>
<p><img alt="{title} | STUDY TOPPER™" class="aligncenter" src="/static/thumbnails/{slug}.webp" style="max-width:100%; height:auto; border-radius:6px; border:2px solid #ab183d; margin:15px auto; display:block;"/></p>
</div>
<div class="gb-container gb-container-ce6e23c9">
<p class="gb-headline gb-headline-a1cd0fe1"><span class="gb-headline-text">StudyTopper.in</span></p>
<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9762662687323163"></script>
<!-- Study Topper -->
<ins class="adsbygoogle" data-ad-client="ca-pub-9762662687323163" data-ad-format="auto" data-ad-slot="7596594071" data-full-width-responsive="true" style="display:block"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
<table style="width:100%; border-collapse: collapse;"><tr><td style="width:50%; padding: 10px; vertical-align: top; border: 1px solid #ddd;"><h3>Latest Posts</h3><p><a href="/ssc-cgl-2026/">SSC Combined Graduate Level CGL Online Form 2026</a></p><p><a href="/rrb-je-2026/">Railway RRB Junior Engineer JE Online Form 2026</a></p><p><a href="/railway-nfr-2026/">Railway NFR Apprentice Online Form 2026</a></p><p><a href="/ssc-gd-constable-2026/">SSC GD Constable Recruitment 2026</a></p></td><td style="width:50%; padding: 10px; vertical-align: top; border: 1px solid #ddd;"><h3>Related Posts</h3><p><a href="/latest-jobs/">Check More Sarkari Jobs</a></p><p><a href="/result/">Check Latest Exam Results</a></p><p><a href="/admit-card/">Download Admit Cards</a></p></td></tr></table>
<p>&nbsp;</p>
<div class="social-buttons" style="display: flex; gap: 10px; margin: 12px 0 16px 0;"><a class="social-button whatsapp" href="https://whatsapp.com/channel/0029Va9xyz" rel="noopener" style="background-color: #25D366; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; justify-content: center; font-size: 15px;" target="_blank">WhatsApp</a><a class="social-button telegram" href="https://t.me/studytopperofficial" rel="noopener" style="background-color: #0088cc; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; display: inline-flex; align-items: center; justify-content: center; font-size: 15px;" target="_blank">Telegram</a></div>
<p class="official_site wp-block-paragraph"><strong>Official Website of Study Topper™ – StudyTopper.in | Since 2009 | Trademark Applications for “Study Topper” Accepted and Advertised by the Controller General of Patents, Designs and Trade Marks, Government of India, under Application Nos. 6921399 (Class 35) and 6921398 (Class 41).</strong></p>
<p class="has-small-font-size wp-block-paragraph"><strong>Disclaimer:</strong> Information regarding any exam form , results/marks, answer key are published on this website are provided just for the immediate information of the examinees and should not be considered as a legal document. While every effort has been made by studytopper team to ensure the accuracy of the information provided which includes official links, we are not responsible for any inadvertent errors that may appear in the examination results/marks, answer key or time table/admission dates. Additionally, we disclaim any liability for any loss or damage caused by any shortcomings, defects, or inaccuracies in the information available on this website. In case of any correction is needed feel free to contact us through contact us page.</p>
</div>
</div>
</div>
<p class="wp-block-paragraph">&nbsp;</p>
</main>"""

        main_start = template.find('<main class="site-main" id="main">')
        main_end = template.find('</main>')
        if main_start != -1 and main_end != -1:
            return template[:main_start] + main_content + template[main_end + len('</main>'):]
        return template

    def generate_thumbnail(self, data: Dict[str, Any], slug: str) -> str:
        out_path = os.path.join(self.thumbnails_dir, f"{slug}.webp")
        if generate_post_thumbnail:
            try:
                generate_post_thumbnail(
                    title=data.get("title", "Govt Job Online Form 2026"),
                    total_posts=data.get("total_posts", ""),
                    last_date=data.get("last_date", ""),
                    qualification=data.get("qualification_short", "10th / 12th / Graduate"),
                    output_path=out_path
                )
                print(f"[Thumbnail] Generated: {out_path}")
                return out_path
            except Exception as e:
                print(f"[Thumbnail] Warning: generation error: {e}")
        return out_path

    def publish(self, data: Dict[str, Any]) -> str:
        slug = data.get("slug", slugify(data.get("title", "recruitment-2026")))
        data["slug"] = slug
        title = data.get("title", "Govt Job Recruitment 2026")

        # 1. Generate WebP Thumbnail
        self.generate_thumbnail(data, slug)

        # 2. Build full HTML
        html_code = self.build_post_html(data)
        out_file = os.path.join(self.pages_dir, f"{slug}.html")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_code)
        print(f"[Post] Saved HTML: {out_file} ({len(html_code)} bytes)")

        # 3. Update Database (all_posts.json & custom_posts.json)
        entry = {
            "id": f"post_{slug.replace('-', '_')}",
            "slug": slug,
            "title": title,
            "category": data.get("category", "latest-jobs"),
            "short_desc": f"{data.get('organization', 'Govt Board')} invites online applications for {title} for {data.get('total_posts', 'various posts')}.",
            "application_start_date": data.get("start_date", ""),
            "application_last_date": data.get("last_date", ""),
            "custom_badge": data.get("total_posts", ""),
            "tags": f"{data.get('category', 'latest-jobs')}, {data.get('organization', 'Govt Job')}, Study Topper",
            "created_at": datetime.datetime.now().isoformat(),
            "lifecycle_state": "ACTIVE",
            "is_pinned": True
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
                    print(f"[Data] Updated: {fpath}")
                except Exception as e:
                    print(f"[Data] Error updating {fname}: {e}")

        # 4. Update Homepage (pages/index.html)
        index_file = os.path.join(self.pages_dir, "index.html")
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    idx = f.read()

                # Add to Latest Jobs column if not already there
                if f'href="/{slug}/"' not in idx:
                    search_str = '<p class="gb-headline gb-headline-5badebdf gb-headline-text">Latest Jobs</p>\n<ul class="wp-block-latest-posts__list 6colm_box wp-block-latest-posts"><li>'
                    if search_str in idx:
                        idx = idx.replace(search_str, f'{search_str}<a class="wp-block-latest-posts__post-title" href="/{slug}/">{title}</a></li><li>', 1)
                        with open(index_file, "w", encoding="utf-8") as f:
                            f.write(idx)
                        print(f"[Homepage] Updated Latest Jobs list on index.html")
            except Exception as e:
                print(f"[Homepage] Error updating index.html: {e}")

        return out_file


def main():
    parser = argparse.ArgumentParser(description="StudyTopper Universal Design Agent")
    parser.add_argument("--slug", help="Slug for the post")
    parser.add_argument("--title", help="Title of the post")
    parser.add_argument("--org", help="Organization name")
    parser.add_argument("--posts", help="Total vacancy count")
    parser.add_argument("--last-date", help="Application last date")
    parser.add_argument("--file", help="JSON data file for complete vacancy details")
    args = parser.parse_args()

    agent = UniversalDesignAgent()

    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
        agent.publish(data)
    elif args.title:
        data = {
            "title": args.title,
            "slug": args.slug or slugify(args.title),
            "organization": args.org or "Staff Selection Commission",
            "total_posts": args.posts or "Various Posts",
            "last_date": args.last_date or "Upcoming",
            "start_date": "Recently",
            "advt_no": "Advt No. 2026",
            "min_age": "18 Years",
            "max_age": "30 Years",
            "age_as_on": "01 August 2026",
            "qualification_short": "Graduation Degree",
            "important_dates": {
                "Online Apply Start Date": "Recently",
                "Online Apply Last Date": args.last_date or "Upcoming",
                "Last Date For Fee Payment": args.last_date or "Upcoming",
                "Exam Date": "Announced Soon"
            },
            "application_fee": {
                "For General / OBC / EWS": "₹ 100/-",
                "For SC / ST / PwBD / Female": "₹ 0/- (Exempted)"
            },
            "age_limits": {
                "Minimum Age": "18 Years",
                "Maximum Age": "30 Years",
                "Age Relaxation": "As per Recruitment Rules"
            },
            "category_vacancies": {
                "General (UR)": "Available in Notification",
                "OBC / EWS": "Available in Notification",
                "SC / ST": "Available in Notification",
                "Total Vacancies": args.posts or "Various Posts"
            },
            "post_matrix": [
                {
                    "name": args.title,
                    "posts": args.posts or "Various Posts",
                    "eligibility": "Bachelor Degree or relevant qualification from recognized university."
                }
            ],
            "how_to_fill": [
                "Visit the official portal and complete One Time Registration (OTR).",
                "Fill in educational qualifications, contact information, and post preference.",
                "Upload required photograph and signature.",
                "Pay examination fee online if applicable and submit final application."
            ],
            "selection_process": [
                "Written Examination (CBE / OMR)",
                "Skill Test / Typing Test (if applicable)",
                "Document Verification & Medical Examination"
            ],
            "faqs": [
                {"q": f"What is the last date to apply for {args.title}?", "a": f"The last date is {args.last_date or 'as mentioned in official notification'}."},
                {"q": "What is the application fee?", "a": "General/OBC is ₹100/-, SC/ST/Female candidates are exempted."},
                {"q": "What is the eligibility criteria?", "a": "Candidate must hold required educational qualifications as specified in the notification."}
            ]
        }
        agent.publish(data)
    else:
        print("Usage: python3 universal_design_agent.py --file <data.json> OR python3 universal_design_agent.py --title <Title> --posts <Count> --last-date <Date>")

if __name__ == "__main__":
    main()
