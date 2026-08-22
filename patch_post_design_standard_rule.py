with open('/root/sarkari-result-portal/POST_DESIGN_STANDARD.md', 'r', encoding='utf-8') as f:
    content = f.read()

rule_addition = """
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

"""

if "MANDATORY RULE: EXACT OFFICIAL SOURCE DATA (ZERO TRUNCATION)" not in content:
    content = content.replace("# StudyTopper™ Universal Post Design Standard\n", "# StudyTopper™ Universal Post Design Standard\n" + rule_addition)
    with open('/root/sarkari-result-portal/POST_DESIGN_STANDARD.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated POST_DESIGN_STANDARD.md with zero-truncation & 3-section Humanizer rule!")
else:
    print("POST_DESIGN_STANDARD.md already updated.")
