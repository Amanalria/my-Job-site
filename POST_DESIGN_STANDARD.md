# StudyTopper™ Universal Post Design Standard

> **Mandatory Rule for All Posts**: Every post published on StudyTopper™ (`studytopper.in`) must strictly adhere to this layout, typography, humanizer rewriting pipeline, and custom thumbnail specifications.

---

## 1. Complete Workflow & Quality Pipeline (Every Single Post)

1. **Ingest / Scrape**: Extract official notification data from government / official recruitment portals.
2. **Humanizer Agent Full Rewrite (`blader/humanizer`)**:
   - **Zero Duplicate Content**: 100% rewritten from scratch. Never copy-paste text directly from other websites.
   - **No Robotic AI Markers**: Enforce Wikipedia's 35 "Signs of AI Writing" rules (0 em-dashes `—`, no AI clichés like "beacon", "testament", "tapestry", "crucial role", etc.).
   - **Overview Word Count Requirement**: Strictly **90 to 100 words in clean English**. If source details are short, expand autonomously with comprehensive key details (organization name in blue, notice number in red, start/end dates, total vacancy count, age limits, and eligibility). Zero Hindi text.
3. **Custom Thumbnail Image Requirement**:
   - Every single post MUST have its own custom WebP thumbnail image saved at `/static/thumbnails/<slug>.webp` (generated with 1200x675 / 16:9 or 1:1 aspect ratio, bold typography, official badges).
4. **Universal Design Rendering**: Render HTML strictly conforming to the component specifications below.
5. **Multi-Location Publishing**:
   - Add post to Homepage (`pages/index.html`) Colorful Box 1 and Latest Jobs column.
   - Add post to appropriate Category page (`/latest-jobs/`, etc.).
   - Add post URL to `sitemap.xml` with current ISO timestamp.
   - Save to `data/all_posts.json` and sync with Supabase database.

---

## 2. Typography & Color Specifications

- **Global Font Family**: `Hind, 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;` (Clean Category Wise Vacancy Details font stack across all elements).
- **H1 Post Title**:
  - `font-size: 22px; font-weight: 700; color: #0000cd; text-align: left; margin: 8px 0 4px 0; line-height: 1.3; width: 100%;`
- **Post Date**:
  - `color: #cd0808; font-weight: 700; font-size: 15px; margin: 2px 0 7px 0; text-align: left;`
  - Example: `Post Date: August 20, 2026 10:13 Am`
- **Overview Paragraph (90–100 Words)**:
  - `font-size: 16.8px; line-height: 1.55; color: #000000; text-align: justify; text-justify: inter-word; width: 100%; margin: 8px 0 14px 0; display: block;`
  - Key highlights: Organization in blue (`<strong style="color: #0000cd;">...</strong>`), keywords in bold, and Notice number in red (`<strong style="color: #cd0808;">(CEN No. ... / Advt No. ...)</strong>`). Zero Hindi text.
- **Social Buttons (Compact, Left-Aligned)**:
  - Container: `display: flex; justify-content: flex-start; align-items: center; gap: 10px; margin: 10px 0 16px 0; width: 100%;`
  - Left Button: `WhatsApp` (solid green `#00d084`, color `#ffffff`, `padding: 10px 18px; font-size: 15.5px; font-weight: 700; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; height: auto; text-decoration: none;`).
  - Right Button: `Telegram` (solid blue `#0088cc`, color `#ffffff`, `padding: 10px 18px; font-size: 15.5px; font-weight: 700; border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; height: auto; text-decoration: none;`).
  - Text inside buttons MUST ALWAYS remain strictly `WhatsApp` and `Telegram` (never replace with post titles).
- **H2 Section Header**:
  - `font-size: 15.5px; font-weight: 700; text-align: center; color: #ef0303; line-height: 1.3; padding: 2px 2px; margin: 3px 0 1px 0;`
- **H3 Section Header**:
  - `font-size: 16px; font-weight: 600; text-align: center; color: #009703; line-height: 1.25; margin: 1px 0 2px 0; padding: 0;`
- **StudyTopper.in Link**:
  - `margin-top: 0; margin-bottom: 2px; text-align: center; font-size: 19px; font-weight: 600; color: #0000ff;`

---

## 3. Table Standards

### 3.1 Important Dates & Application Fee Matrix (2-Column Grid)
- Column 1 Header: `Important Dates` (Background `#5b032f`, text `#ffffff`, 20px).
- Column 2 Header: `Application Fee` (Background `#5b032f`, text `#ffffff`, 20px).
- Highlighted last dates in bold red `#ff0000`.

### 3.2 Age Limits & Total Vacancy Row
- Column 1: `Age Limits As On [Date]` (Background `#046132`, text `#ffffff`, 20px).
- Column 2: `Total Post` (Background `#f53c00`, text `#ffffff`, 20px) with large bold count below (`25px`, `#000000`).

### 3.3 Vacancy Details Matrix & Category-Wise Breakdown
- Category Wise Header: `Railway RRB JE Recruitment 2026 : Category Wise Vacancy Details` (Background `#000080`, text `#ffffff`, `14pt`).
- Matrix Headers (`Post Name`, `Total Posts`, `Eligibility Criteria`): Background `#f53c00`, text `#ffffff`, `15px`, bold, `padding: 6px 10px; border: 1px solid #d35400;`.

### 3.4 Important Links Table (Screenshot_20260820-194153.png Standard)
- Main Header: `SOME USEFUL IMPORTANT LINKS` (bold red `#cd0808` text, white background, `font-size: 20px; text-align: center; padding: 8px 4px;`).
- Table Rows Fill: Pastel yellow background (`#fff37a`).
- Grid lines: `1px solid #000000`.
- Left Column: Bold black link label (`font-size: 17px; font-weight: 700; color: #000000; text-align: left; padding: 8px 12px;`).
- Right Column: Bold blue action text (`Click Here` in `#0000ef`, `font-size: 17px; font-weight: 700; text-align: center; padding: 8px 12px;`).

---

## 4. FAQs Section
- Minimum 5 relevant FAQs per post in clean structured format.
- Questions bold, answers clear and human-written.
