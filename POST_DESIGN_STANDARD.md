# StudyTopper™ Universal Post Design Standard

---

## ⚠️ MANDATORY RULE: EXACT OFFICIAL SOURCE DATA (ZERO TRUNCATION) + 3-SECTION HUMANIZER REWRITE

> **Core Content Rule**: 
> - **100% Exact Official Source Data (Zero Truncation / No Data Dropped)** for all factual recruitment sections:
>   1. **Important Dates**: Exact raw dates from official table (Application Start, Last Date, Fee Last Date, Correction Window, Re-open Dates, Pre Exam, Mains Exam, Admit Card, Result, etc. - NEVER truncate or drop lines).
>   2. **Application Fee**: Exact fee breakdown by category (Gen, OBC, EWS, SC, ST, PH, Female, Correction Charges, Late Fee, Payment Mode notes).
>   3. **Age Limits**: Exact Minimum Age, Maximum Age, Reference Cut-off Date, Post-wise age limits, and all category relaxations.
>   4. **Vacancy & Eligibility Matrix**: Exact table with post names, total vacancy counts, and educational criteria directly from official notice.
>   5. **Category-wise Vacancy Matrix**: Extracted as-is whenever available in official notice (cleanly omitted if not present; never show an empty box).
>   6. **Useful Important Links**: Exact real direct links (Apply Online, Notification PDF, Official Portal).
>
> - **Strictly ONLY 3 Sections are Rewritten by Humanizer**:
>   1. **Overview Paragraph**: Strictly 90–100 words in clean English, bold blue full authority name (`<strong style="color: #0000cd;">...</strong>`), bold red post title (`<strong style="color: #cd0808;">...</strong>`), exact dates, vacancies, and qualifications.
>   2. **How to Fill Form**: Structured humanized step-by-step application instructions incorporating source dates + `indtool.in` image resizer.
>   3. **Frequently Asked Questions (FAQ)**: 5 structured tailored FAQs with exact post numbers, dates, fees, and criteria.


> **Permanent Mandatory Rule for All Posts**: Every post published on StudyTopper™ (`studytopper.in`) must strictly adhere to this layout, typography, humanizer rewriting pipeline, custom WebP thumbnail specifications, and GeneratePress WordPress HTML skeleton. Never alter this design, never create partial `<article>` snippets, and always produce full ~150KB WordPress-style pages.

---

## 1. Complete Workflow & Quality Pipeline (Every Single Post)

1. **Ingest / Copy from Source Portal**:
   - Extract official notification data from government / official recruitment portals (e.g. SSC, UPSC, RRB, State PSCs, Sarkari Result).
   - Collect exact dates, fee breakdown, age limits, vacancy counts, category-wise distribution, post eligibility, and official links.

2. **Humanizer Agent Full Rewrite (`blader/humanizer` & `universal_design_agent.py`)**:
   - **Zero Duplicate Content**: 100% rewritten from scratch. Never copy-paste raw overview text from other websites.
   - **No Robotic AI Markers**: Enforce Wikipedia's 35 "Signs of AI Writing" rules (0 em-dashes `—`, 0 en-dashes `–`, no AI clichés like "beacon", "testament", "tapestry", "crucial role", etc.).
   - **Overview Word Count Requirement**: Strictly **90 to 100 words in clean English**.
   - **Entity Highlighting**:
     - Organization name in bold blue: `<strong style="color: #0000cd;">[Organization Name]</strong>`
     - Post title in bold: `<strong>[Post Title]</strong>`
     - Notice number in bold red: `<strong style="color: #cd0808;">([Advt No. / CEN No.])</strong>`
     - Zero Hindi text in the overview.

3. **Custom WebP Thumbnail Image Requirement**:
   - Every single post MUST have its own custom WebP thumbnail image saved at `/static/thumbnails/<slug>.webp`.
   - Generated with `thumbnail_generator.py` (640x330 or 1200x675, burgundy gradient header, gold stripe, bold text, max size < 10 KB).

4. **Universal Design Rendering (Full ~150KB GeneratePress HTML Skeleton)**:
   - Always clone the base structure from `/pages/rrb-je-2026.html` or `/pages/ssc-cgl-2026.html`.
   - Keep complete `<!DOCTYPE html>`, `<head>` meta tags, GeneratePress CSS style blocks, Google Analytics (`G-LZ32T0N2XE`), Schema.org JSON-LD, navbar, search modal, and scripts.
   - Replace `<main class="site-main" id="main">` with the universal layout components specified below.

5. **Multi-Location Publishing**:
   - Save full HTML file to `pages/<slug>.html`.
   - Add post link to Homepage (`pages/index.html`) Top Colorful Box 1 (`.gb-grid-column-2f6de309`) and Latest Jobs column.
   - Save entry to `data/all_posts.json` and `data/custom_posts.json`.

---

## 2. Universal Design Component Layout & Colors

### 2.1 Post Header Section
- **Global Font Family**: `Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;`
- **H1 Post Title**: `font-size: 22px; font-weight: 700; color: #0000cd; text-align: left; margin: 8px 0 4px 0; line-height: 1.3; width: 100%;`
- **Post Date**: `color: #cd0808; font-weight: 700; font-size: 15px; margin: 2px 0 7px 0; text-align: left;`
- **Overview Paragraph (90–100 Words)**: `font-size: 16.8px; line-height: 1.55; color: #000000; text-align: justify; text-justify: inter-word; width: 100%; margin: 8px 0 14px 0; display: block;`
- **Social Buttons (Compact, Left-Aligned)**:
  - Left Button: `WhatsApp` (`#00d084`, color `#ffffff`, `padding: 10px 18px; font-size: 15.5px; font-weight: 700; border-radius: 4px;`)
  - Right Button: `Telegram` (`#0088cc`, color `#ffffff`, `padding: 10px 18px; font-size: 15.5px; font-weight: 700; border-radius: 4px;`)
- **H2 Section Header**: `font-size: 15.5px; font-weight: 700; text-align: center; color: #ef0303; line-height: 1.3; margin: 3px 0 1px 0;`
- **H3 Section Header**: `font-size: 16px; font-weight: 600; text-align: center; color: #009703; line-height: 1.25; margin: 1px 0 2px 0;`
- **StudyTopper.in Link**: `margin-top: 0; margin-bottom: 2px; text-align: center; font-size: 19px; font-weight: 600; color: #0000ff;`

### 2.2 Table Specifications
- **Important Dates & Application Fee (2-Col Grid)**:
  - Header 1: `Important Dates` (Background `#5b032f`, color `#ffffff`, `font-size: 20px; font-weight: 700;`)
  - Header 2: `Application Fee` (Background `#5b032f`, color `#ffffff`, `font-size: 20px; font-weight: 700;`)
  - Last Date in bold red `#ff0000`.
- **Age Limits & Total Vacancy Row**:
  - Column 1: `Age Limits As On [Date]` (Background `#046132`, text `#ffffff`, `20px`)
  - Column 2: `Total Post` (Background `#f53c00`, text `#ffffff`, `20px`) with large bold count (`font-size: 25px; color: #000000;`)
- **Vacancy Details Matrix**:
  - Category-Wise Header: `[Organization] Recruitment 2026 : Category Wise Vacancy Details` (Background `#000080`, text `#ffffff`, `14pt`)
  - Post Matrix Headers (`Post Name`, `Total Posts`, `Eligibility Criteria`): Background `#f53c00`, text `#ffffff`, `15px`, bold, border `#d35400`.
- **How to Fill Form Guide**:
  - Header: `How to Fill [Organization] Online Application Form` (Background `#000080` / `#046132`, color `#ffffff`, `14pt`)
  - Must include link to `https://indtool.in` for candidate photo/sign resizing.
- **Mode of Selection**:
  - Header: `[Organization] Recruitment 2026 : Mode Of Selection` (Background `#000080`, color `#ffffff`)
- **Important Links Table (Screenshot Standard)**:
  - Header: `SOME USEFUL IMPORTANT LINKS` (bold red `#ff0000`, white background `#ffffff`, `font-size: 20px;`)
  - Table Rows: Pastel yellow background (`#fff37a`)
  - Border: `1px solid #000000`
  - Action Links: `Click Here` in bold blue (`#0000ef`, `font-size: 20px; font-weight: 800; text-decoration: none;`)
  - Rows: Apply Online, Official Notification, Photo/Sign Resizer Tool (`https://indtool.in`), Check Sarkari Result (`/`), Official Website.
- **FAQs Section**:
  - Minimum 5 structured FAQs per post (`Q1. ... Ans: ...`).
- **Thumbnail Image**:
  - Center aligned, max-width 100%, border `2px solid #ab183d`, border-radius `6px`.

---

## 3. Automation Agent (`universal_design_agent.py`)

Run the dedicated agent to automatically create, rewrite, and publish posts:
```bash
python3 /root/sarkari-result-portal/universal_design_agent.py --file post_data.json
# OR
python3 /root/sarkari-result-portal/universal_design_agent.py --title "UPSSSC Lekhpal Online Form 2026" --org "UPSSSC" --posts "8,085 Posts" --last-date "15 September 2026"
```
