# StudyTopper™ Official Post Page Design & Humanizer Publishing Standard

## Permanent Rule & Standard for All Posts (All Chats & Sessions)

Whenever the user mentions **"sarkari result universal design"**, **"universal post design"**, or asks to create, publish, scrape, or rewrite articles/posts for **StudyTopper™** (`studytopper.in`):
1. **Mandatory Post Design Template**: Every post MUST follow the exact layout structure defined in this specification.
2. **100% Humanizer Engine**: All article body copy, summaries, descriptions, and step-by-step guides must be rewritten in 100% original, natural human prose (zero duplicate content, zero AI stock clichés, short 2-3 sentence paragraphs, active voice).
3. **Exact Fact Accuracy**: Board names, dates, vacancy counts, eligibility qualifications, fees, and official links must remain 100% technically accurate.

---

## 1. Post Page Layout Structure

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Site Header & Logo (STUDY TOPPER™ - studytopper.in)                │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Compact GeneratePress Navigation Bar (Mobile Hamburger + More Menu) │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Post Title Header (Left-aligned, bold royal blue #0000cd, 24px)     │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Post Date Line (Left-aligned, red #cd0808 bold)                     │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Overview Paragraph (Rich formatted English, bold/blue keywords,     │
│    bold red Advt No, zero Hindi text)                                  │
├────────────────────────────────────────────────────────────────────────┤
│ 6. Social Buttons: [WhatsApp #00d084] [Telegram #0088cc] (Full width)  │
├────────────────────────────────────────────────────────────────────────┤
│ 7. 2-Column Table: Important Dates & Application Fee                   │
│    - Header: #ab183d background, #ffffff bold text                     │
│    - Left: Application Start, Last Date, Fee Last Date, Exam Date      │
│    - Right: Gen/OBC/EWS Fee, SC/ST/PH Fee, Payment Mode                │
├────────────────────────────────────────────────────────────────────────┤
│ 8. Age Limit & Relaxation Table (#ab183d header)                       │
│    - Min Age, Max Age, Reference Date, Category Relaxations            │
├────────────────────────────────────────────────────────────────────────┤
│ 9. Vacancy Details & Eligibility Table                                 │
│    - Header: #f53c00 vibrant orange, #ffffff bold white text           │
│    - Columns: Post Name | Total Posts | Eligibility Matrix             │
├────────────────────────────────────────────────────────────────────────┤
│ 10. Dynamic 3-Day Rotating "You May Also Check" Widget                 │
├────────────────────────────────────────────────────────────────────────┤
│ 11. Step-by-Step "How to Apply Online Form" Guide (Left-aligned list)  │
├────────────────────────────────────────────────────────────────────────┤
│ 12. Useful Important Links Table (Screenshot_20260820-194153.png)      │
│     - Header: Red bold text SOME USEFUL IMPORTANT LINKS on white bg    │
│     - Table Fill: Soft pastel yellow #fff37a, 1px solid black border   │
│     - Left: Bold black #000000 text                                    │
│     - Right: Bold blue #0000ef Click Here (centered)                   │
├────────────────────────────────────────────────────────────────────────┤
│ 13. Frequently Asked Questions (FAQ) Section                           │
├────────────────────────────────────────────────────────────────────────┤
│ 14. Custom WebP Post Thumbnail (/static/thumbnails/<slug>.webp)        │
├────────────────────────────────────────────────────────────────────────┤
│ 15. Official Footer (About, Policies, Disclaimer, Copyright Notice)    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Standard HTML Content Template

```html
<div class="st-post-container" style="font-family: Arial, Helvetica, sans-serif; color: #000000; line-height: 1.5; font-size: 14px;">
    <!-- Intro Paragraph -->
    <p style="margin-bottom: 12px; font-size: 14.5px; line-height: 1.6;">
        <strong>[Post Title] :</strong> [Humanized, natural 2-3 sentence overview of recruitment, eligibility, and key notification details.]
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
                        <li>Application Start Date: <strong>[Start Date]</strong></li>
                        <li>Application Last Date: <strong style="color: #cd0808;">[Last Date]</strong></li>
                        <li>Fee Payment Last Date: <strong>[Fee Last Date]</strong></li>
                        <li>Exam / Result Date: <strong>[Exam / Schedule]</strong></li>
                    </ul>
                </td>
                <td style="padding: 10px 12px; border: 1px solid #ab183d; background-color: #ffffff;">
                    <ul style="margin: 0; padding-left: 18px; line-height: 1.6;">
                        <li>General / OBC / EWS: <strong>[Fee Amount]</strong></li>
                        <li>SC / ST / PH: <strong>[Fee Amount]</strong></li>
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
                        <li>Minimum Age: <strong>[Min Age]</strong></li>
                        <li>Maximum Age: <strong>[Max Age]</strong></li>
                        <li>Age Calculation Date: As on [Reference Date]</li>
                        <li>Age Relaxation: Extra age relaxation applicable as per board recruitment rules.</li>
                    </ul>
                </td>
            </tr>
        </tbody>
    </table>

    <!-- Vacancy Details Table -->
    <table style="width: 100%; border-collapse: collapse; border: 2px solid #ab183d; margin-bottom: 16px;">
        <thead>
            <tr style="background-color: #ab183d; color: #ffffff;">
                <th colspan="3" style="padding: 8px 10px; text-align: center; font-size: 15px;">Vacancy Details (Total: [Total Vacancies])</th>
            </tr>
            <tr style="background-color: #f53c00; color: #ffffff;">
                <th style="padding: 8px 10px; border: 1px solid #d35400; text-align: left; font-size: 13.5px; color: #ffffff; background-color: #f53c00;">Post Name</th>
                <th style="padding: 8px 10px; border: 1px solid #d35400; text-align: center; font-size: 13.5px; color: #ffffff; background-color: #f53c00;">Total Post</th>
                <th style="padding: 8px 10px; border: 1px solid #d35400; text-align: left; font-size: 13.5px; color: #ffffff; background-color: #f53c00;">Eligibility Criteria</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding: 8px 10px; border: 1px solid #ab183d; text-align: left; font-weight: 600;">[Post Name]</td>
                <td style="padding: 8px 10px; border: 1px solid #ab183d; text-align: center; font-weight: bold; color: #cd0808;">[Count]</td>
                <td style="padding: 8px 10px; border: 1px solid #ab183d; text-align: left;">[Detailed educational qualifications, marks, diploma/degree needed]</td>
            </tr>
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
                        <li>Visit the official portal and read the full notification carefully.</li>
                        <li>Complete One Time Registration (OTR) if required by the recruiting authority.</li>
                        <li>Fill in personal, academic, and reservation category details accurately.</li>
                        <li>Upload passport photo, signature, and required certificates in prescribed sizes.</li>
                        <li>Submit application fee online and preserve a copy of confirmation page.</li>
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
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; font-weight: bold; width: 60%;">Apply Online Form</td>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: center;">
                    <a href="[Apply URL]" target="_blank" rel="noopener noreferrer" style="color: #0000ef; font-weight: bold; text-decoration: underline;">Click Here</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; font-weight: bold;">Download Official Notification</td>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: center;">
                    <a href="[Notification URL]" target="_blank" rel="noopener noreferrer" style="color: #0000ef; font-weight: bold; text-decoration: underline;">Click Here</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; font-weight: bold;">Join WhatsApp Channel</td>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: center;">
                    <a href="https://whatsapp.com/" target="_blank" rel="noopener noreferrer" style="color: #00a82d; font-weight: bold; text-decoration: underline;">Join Now</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; font-weight: bold;">Join Telegram Channel</td>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: center;">
                    <a href="https://t.me/" target="_blank" rel="noopener noreferrer" style="color: #0088cc; font-weight: bold; text-decoration: underline;">Join Now</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; font-weight: bold;">Official Website</td>
                <td style="padding: 8px 12px; border: 1px solid #ab183d; text-align: center;">
                    <a href="[Official Website URL]" target="_blank" rel="noopener noreferrer" style="color: #0000ef; font-weight: bold; text-decoration: underline;">Click Here</a>
                </td>
            </tr>
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
            <tr>
                <td style="padding: 8px 10px; border: 1px solid #ab183d; background-color: #f8fafc; font-weight: bold; color: #0b213f;">Q: [Question 1]</td>
            </tr>
            <tr>
                <td style="padding: 8px 10px; border: 1px solid #ab183d; line-height: 1.45;">Ans: [Clear, direct answer]</td>
            </tr>
        </tbody>
    </table>
</div>
```

---

## 3. Humanizer Rewriting Guidelines (35-Signs of AI Check)
- **Minimum Word Count**: Every post MUST strictly contain **700+ words** (in-depth coverage of overview, eligibility, syllabus, how to apply, and FAQs).
- **Mandatory 5 FAQs**: Every post MUST contain exactly **5 Frequently Asked Questions** with clear, direct answers.
- **Zero Em-Dashes/En-Dashes**: Never use `—` or `–` in body copy. Use commas, colons, or parentheses.
- **Banned AI Buzzwords**: `delve`, `tapestry`, `testament`, `pivotal`, `landscape`, `intricate`, `fostering`, `furthermore`, `moreover`, `in conclusion`, `in this digital age`.
- **Short Paragraphs**: 2–3 sentences max per paragraph for optimal readability on mobile phones.
- **Active Voice**: Clearly state who is conducting the recruitment, dates, and instructions directly.
