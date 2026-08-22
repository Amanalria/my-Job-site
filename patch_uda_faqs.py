import re

with open('/root/sarkari-result-portal/universal_design_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add generate_faqs method to UniversalDesignAgent
faqs_method = '''    def generate_faqs(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        title = data.get("title", "Recruitment 2026")
        org = data.get("organization") or extract_clean_organization(title)
        category = data.get("category", "latest-jobs").lower()
        last_date = data.get("last_date", "As per Official Notification")
        total_posts = data.get("total_posts", "Various Posts")
        
        # Determine last date text
        for k, v in data.get("important_dates", {}).items():
            if 'last date' in k.lower() or 'apply' in k.lower():
                last_date = v
                break
                
        # Determine age limit text
        age_text = "As per official notification rules. General age range is 18 to 40 years with relaxation extra per category rules."
        if data.get("age_limits"):
            age_parts = [f"{k}: {v}" for k, v in data["age_limits"].items() if len(k) > 1]
            if age_parts:
                age_text = "; ".join(age_parts[:3])
                
        # Determine fee text
        fee_text = "Check official notification for exact category-wise application fee."
        if data.get("application_fee"):
            fee_parts = [f"{k}: {v}" for k, v in data["application_fee"].items() if len(k) > 1]
            if fee_parts:
                fee_text = "; ".join(fee_parts[:3])

        faqs = [
            {
                "question": f"What is the last date to apply online for {title}?",
                "answer": f"The last date for submission of online application is {last_date}."
            },
            {
                "question": f"What is the eligibility criteria and age limit for {org} {title}?",
                "answer": f"{age_text} Candidates must hold the prescribed educational qualification from any recognized Board or University in India."
            },
            {
                "question": f"What is the application fee for {title}?",
                "answer": f"{fee_text} Fee can be paid through online Net Banking, Debit Card, Credit Card, or UPI modes."
            },
            {
                "question": f"How many total posts/vacancies are announced for {title}?",
                "answer": f"A total of {total_posts} have been officially announced by {org} under this recruitment notice."
            },
            {
                "question": f"How to apply online or download documents for {title}?",
                "answer": f"Eligible candidates can scroll down to the 'Important Links' section on StudyTopper.in, click on the direct link, complete registration, resize documents via indtool.in, and submit the form."
            }
        ]
        return faqs
'''

# Insert generate_faqs method right before build_post_html
code = code.replace("    def build_post_html(self, data: Dict[str, Any]) -> str:", faqs_method + "\n    def build_post_html(self, data: Dict[str, Any]) -> str:")

# 2. Insert FAQ section into main_content in build_post_html
find_links_insertion = '''<!-- SECTION 5: USEFUL IMPORTANT LINKS TABLE -->
<table style="border-collapse: collapse; width: 100%; border: 2px solid #5b032f; margin: 15px 0 20px 0; background-color: #fff37a;">
<tbody>
<tr style="background-color: #5b032f;">
<th colspan="2" style="padding: 12px 10px; color: #ffffff; font-size: 19px; font-weight: 800; text-align: center; font-family: '-apple-system, BlinkMacSystemFont, \\'Segoe UI\\', Roboto, \\'Helvetica Neue\\', Arial, sans-serif', Times, serif, Hind, sans-serif;">SOME USEFUL IMPORTANT LINKS</th>
</tr>
{links_rows_html}
</tbody>
</table>'''

replace_links_insertion = '''<!-- SECTION 5: USEFUL IMPORTANT LINKS TABLE -->
<table style="border-collapse: collapse; width: 100%; border: 2px solid #5b032f; margin: 15px 0 20px 0; background-color: #fff37a;">
<tbody>
<tr style="background-color: #5b032f;">
<th colspan="2" style="padding: 12px 10px; color: #ffffff; font-size: 19px; font-weight: 800; text-align: center; font-family: '-apple-system, BlinkMacSystemFont, \\'Segoe UI\\', Roboto, \\'Helvetica Neue\\', Arial, sans-serif', Times, serif, Hind, sans-serif;">SOME USEFUL IMPORTANT LINKS</th>
</tr>
{links_rows_html}
</tbody>
</table>
<p>&nbsp;</p>

<!-- SECTION 6: FREQUENTLY ASKED QUESTIONS (FAQ - EXACT REFERENCE STANDARD) -->
<div class="st-faq-section" style="margin: 25px 0 20px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <h3 style="color: #000080; font-size: 16.5px; font-weight: 700; border-bottom: 2px solid #000080; padding-bottom: 6px; margin: 0 0 16px 0;">
    {title} : Frequently Asked Questions (FAQ)
  </h3>
  <div style="font-size: 14.5px; line-height: 1.65; color: #222222;">
    {faq_items_html}
  </div>
</div>
<p>&nbsp;</p>'''

code = code.replace(find_links_insertion, replace_links_insertion)

# 3. Add faq_items_html builder inside build_post_html right before main_content assembly
find_assembly_start = '        links_rows_html = self.build_important_links_html(data, category, title)'
replace_assembly_start = '''        links_rows_html = self.build_important_links_html(data, category, title)

        # Generate 5 Tailored FAQs
        faqs_list = self.generate_faqs(data)
        faq_items_html = ""
        for i, q_item in enumerate(faqs_list, 1):
            q_txt = q_item.get("question", "")
            a_txt = q_item.get("answer", "")
            margin_b = "16px" if i < len(faqs_list) else "0"
            faq_items_html += f'<p style="margin: 0 0 4px 0;"><strong style="color: #000080;">Q{i}. {q_txt}</strong></p>\\n<p style="margin: 0 0 {margin_b} 0; color: #333333; line-height: 1.6;">Ans. {a_txt}</p>\\n'
'''

code = code.replace(find_assembly_start, replace_assembly_start)

with open('/root/sarkari-result-portal/universal_design_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated universal_design_agent.py with exact reference FAQ section!")
