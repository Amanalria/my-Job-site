# 🛠️ StudyTopper™ Settings & Special Edits Guide (GitHub Direct Edit)

Welcome to the **StudyTopper™ Website Configuration System**.
You can edit any aspect of the website directly from GitHub by modifying [`SITE_SETTINGS.json`](./SITE_SETTINGS.json) or [`data/settings.json`](./data/settings.json).

---

## 📑 Table of Contents
1. [Header Branding & Typography](#1-header-branding--typography)
2. [Top 8 Highlight Cards](#2-top-8-highlight-cards)
3. [6 Category Grid Titles & Header Colors](#3-6-category-grid-titles--header-colors)
4. [Top 15 Pages Quick Links Matrix](#4-top-15-pages-quick-links-matrix)
5. [5 Red Info Sections](#5-5-red-info-sections)
6. [Frequently Asked Questions (FAQs)](#6-frequently-asked-questions-faqs)
7. [Mobile App Download CTA Banner](#7-mobile-app-download-cta-banner)
8. [Footer & Social Links](#8-footer--social-links)

---

### 1. Header Branding & Typography
Edit these fields in `SITE_SETTINGS.json`:
```json
"site_name": "STUDY TOPPER™",
"domain": "studytopper.in",
"tagline": "Latest Jobs, Results, Etc.",
"top_banner_text": "Study Topper : studytopper.in",
"header_customizer": {
    "title_text": "STUDY TOPPER™",
    "title_size_desktop": 51.0,
    "title_size_mobile": 36.0,
    "desc_text": "Latest Jobs, Results, Etc.",
    "desc_size_desktop": 25.8,
    "desc_size_mobile": 18.8,
    "gap_spacing": 2.0,
    "header_bg": "#cd0808",
    "pad_top_desktop": 58,
    "pad_bot_desktop": 58,
    "pad_top_mobile": 43,
    "pad_bot_mobile": 40
}
```

---

### 2. Top 8 Highlight Cards
Control the top 8 colorful featured boxes below the navigation bar:
```json
"highlight_cards": [
    {"title": "Railway NFR Apprentice Online Form 2026", "url": "/railway-nfr-2026/"},
    {"title": "SAV Bihar Class 6 Entrance Exam 2027-28", "url": "/sav-bihar-class-6-2026/"},
    {"title": "IGCAR Trade Apprentice Online Form 2026", "url": "/igcar-apprentice-2026/"},
    {"title": "IBPS Clerk (CSA) 16th Online Form 2026", "url": "/ibps-clerk-16th-2026/"},
    {"title": "UPESSC Principal Online Form 2026", "url": "/upessc-principal-2026/"},
    {"title": "Bihar Secondary STET 2026", "url": "/bihar-stet-2026/"},
    {"title": "BPSC School Teacher TRE 4.0 2026", "url": "/bpsc-school-teacher-tre-4-0-2026/"},
    {"title": "RRB JE Online Form 2026 (3993 Posts)", "url": "/rrb-je-2026/"}
]
```

To customize card colors in `theme_colors`:
- `"card_1_bg"` to `"card_8_bg"`: Custom hex colors (e.g. `#fb0303`, `#0080ff`, `#077822`).

---

### 3. 6 Category Grid Titles & Header Colors
Change the headings and header background colors for the 6 homepage columns:
```json
"grid_headers": {
    "result": {"title": "Result", "more_url": "/result/"},
    "admit-card": {"title": "Admit Card", "more_url": "/admit-card/"},
    "latest-jobs": {"title": "Latest Jobs", "more_url": "/latest-jobs/"},
    "answer-key": {"title": "Answer Key", "more_url": "/answer-key/"},
    "syllabus": {"title": "Syllabus", "more_url": "/syllabus/"},
    "admission": {"title": "Admission", "more_url": "/admission/"}
}
```

Column Colors in `theme_colors`:
- `"result_header_bg"`: `#ab183d`
- `"admit_card_header_bg"`: `#ab183d`
- `"latest_jobs_header_bg"`: `#ab183d`
- `"answer_key_header_bg"`: `#ab183d`
- `"syllabus_header_bg"`: `#ab183d`
- `"admission_header_bg"`: `#ab183d`

---

### 4. Top 15 Pages Quick Links Matrix
Control the 15 cells in the top quick links matrix table:
```json
"top_pages_table": [
    {"text": "Bharat Result", "url": "/result/"},
    {"text": "UP Police Result", "url": "/up-police-constable-result-2024/"},
    {"text": "Bihar Police Result", "url": "/bihar-police-constable-result-2024/"},
    {"text": "Study Topper Exam", "url": "/latest-jobs/"},
    {"text": "Study Topper Hindi", "url": "/"},
    {"text": "Study Topper NTPC", "url": "/railway-rrb-alp-2026/"},
    {"text": "Study Topper 2026", "url": "/latest-jobs/"},
    {"text": "Study Topper", "url": "/"},
    {"text": "Study Topper Center", "url": "/"},
    {"text": "Sarkari Naukri", "url": "/latest-jobs/"},
    {"text": "Study Topper 10th", "url": "/latest-jobs/"},
    {"text": "Study Topper SSC", "url": "/ssc-chsl-2026/"},
    {"text": "Study Topper 10+2", "url": "/latest-jobs/"},
    {"text": "StudyTopper.in", "url": "/"},
    {"text": "Study Topper Railway", "url": "/railway-nfr-2026/"}
]
```

---

### 5. 5 Red Info Sections
Control the 5 descriptive red info boxes:
```json
"info_sections": [
    {
        "title": "Study Topper 10+2 & Graduate Latest Jobs 2026",
        "content": "Find verified updates for 10+2 Intermediate and graduate government vacancies across India. StudyTopper.in provides direct official application links, notification PDFs, eligibility criteria, age relaxation, syllabus downloads, and deadline alerts for Railway RRB, SSC CHSL, Defence, Police Bharti, and state recruitment boards updated daily."
    }
]
```

---

### 6. Frequently Asked Questions (FAQs)
Add, remove, or modify FAQ pairs:
```json
"faq_items": [
    {
        "q": "What is Study Topper (studytopper.in) and what updates does it provide?",
        "a": "Study Topper (studytopper.in) is a leading educational and employment alert portal providing real-time, verified notifications for online application forms, government exam results, admit cards, official answer keys, syllabus PDFs, and admission forms across all central and state recruitment boards."
    }
]
```

---

### 7. Mobile App Download CTA Banner
```json
"mobile_app_cta": {
    "enabled": true,
    "button_text": "📱 Download StudyTopper Mobile App & English Vocab",
    "button_url": "https://play.google.com/store/apps/details?id=in.qmaths.blackbook",
    "bg_color": "#fdfaf2",
    "button_color": "#046132"
}
```

---

### 8. Footer & Social Links
```json
"footer_text": "StudyTopper.in is an online educational news and employment information portal.",
"socials": {
    "telegram": "https://t.me/studytopper",
    "whatsapp": "https://whatsapp.com/channel/0029Va...",
    "youtube": "https://youtube.com/@studytopper",
    "instagram": "https://instagram.com/studytopper"
}
```

---

## 🚀 How to Apply Changes
1. Edit [`SITE_SETTINGS.json`](./SITE_SETTINGS.json) directly on GitHub.com.
2. Click **Commit changes**.
3. On localhost, run `git pull` or save in Admin Panel — your site updates instantly!
