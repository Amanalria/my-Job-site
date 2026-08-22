import re

with open('/root/sarkari-result-portal/universal_design_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update is_unwanted_line to never drop dates, fees, or age tokens
new_unwanted_func = '''def is_unwanted_line(t: str) -> bool:
    if not t:
        return True
    tl = str(t).lower().strip()
    unwanted_tokens = [
        'frequently asked questions', 'faq', 'disclaimer', 'privacy policy',
        'join telegram', 'join whatsapp', 'download mobile app', 'follow us on',
        'contact us', 'you may also check', 'related post', 'click here to join'
    ]
    return any(token in tl for token in unwanted_tokens)
'''

code = re.sub(r'def is_unwanted_line\(t: str\) -> bool:.*?(?=\nclass UniversalDesignAgent)', new_unwanted_func, code, flags=re.DOTALL)

# 2. Update clean_dates, clean_fees, clean_ages to preserve every single scraped entry
find_clean_block = '''        # 1. Clean Dates, Fee & Age Lists (Filter out any inline FAQs or questions)
        clean_dates = {k: v for k, v in data.get("important_dates", {}).items() if not is_unwanted_line(k) and not is_unwanted_line(v)}
        clean_fees = {k: v for k, v in data.get("application_fee", {}).items() if not is_unwanted_line(k) and not is_unwanted_line(v)}
        clean_ages = {k: v for k, v in data.get("age_limits", {}).items() if not is_unwanted_line(k) and not is_unwanted_line(v)}'''

replace_clean_block = '''        # 1. Full Complete Dates, Fee & Age Lists (Zero Truncation - 100% Real Official Data)
        clean_dates = {k: v for k, v in data.get("important_dates", {}).items() if not is_unwanted_line(k)}
        clean_fees = {k: v for k, v in data.get("application_fee", {}).items() if not is_unwanted_line(k)}
        clean_ages = {k: v for k, v in data.get("age_limits", {}).items() if not is_unwanted_line(k)}'''

code = code.replace(find_clean_block, replace_clean_block)

with open('/root/sarkari-result-portal/universal_design_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated universal_design_agent.py for zero truncation!")
