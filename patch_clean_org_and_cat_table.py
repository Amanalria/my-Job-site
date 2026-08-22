import re

with open('/root/sarkari-result-portal/universal_design_agent.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add clean_org_name helper in universal_design_agent.py
clean_org_func = '''
def extract_clean_organization(title: str, default: str = "Government Authority") -> str:
    if not title:
        return default
    tl = title.lower()
    mappings = [
        (r'\\b(sbi|state bank of india)\\b', 'State Bank of India (SBI)'),
        (r'\\b(ibps)\\b', 'Institute of Banking Personnel Selection (IBPS)'),
        (r'\\b(upsssc)\\b', 'Uttar Pradesh Subordinate Services Selection Commission (UPSSSC)'),
        (r'\\b(uppsc)\\b', 'Uttar Pradesh Public Service Commission (UPPSC)'),
        (r'\\b(bpsc)\\b', 'Bihar Public Service Commission (BPSC)'),
        (r'\\b(bpssc|bihar police)\\b', 'Bihar Police Subordinate Services Commission (BPSSC)'),
        (r'\\b(csbc)\\b', 'Central Selection Board of Constable (CSBC)'),
        (r'\\b(rpsc)\\b', 'Rajasthan Public Service Commission (RPSC)'),
        (r'\\b(rsmssb|rssb)\\b', 'Rajasthan Staff Selection Board (RSSB)'),
        (r'\\b(mpesb|mp peb|peb)\\b', 'Madhya Pradesh Employees Selection Board (MPESB)'),
        (r'\\b(upsrtc)\\b', 'Uttar Pradesh State Road Transport Corporation (UPSRTC)'),
        (r'\\b(ecce educator|basic education|rojgar sangam|sewayojan)\\b', 'UP Basic Education & Sewayojan Vibhag'),
        (r'\\b(patan|patna high court|phc)\\b', 'Patna High Court (PHC)'),
        (r'\\b(allahabad high court|ahc)\\b', 'Allahabad High Court (AHC)'),
        (r'\\b(delhi high court|dhc)\\b', 'Delhi High Court (DHC)'),
        (r'\\b(mp high court|mphc)\\b', 'Madhya Pradesh High Court (MPHC)'),
        (r'\\b(railway|rrb|rrc)\\b', 'Railway Recruitment Board (RRB)'),
        (r'\\b(ssc|staff selection)\\b', 'Staff Selection Commission (SSC)'),
        (r'\\b(upsc)\\b', 'Union Public Service Commission (UPSC)'),
        (r'\\b(nta|neet|cuet|ugc net|csir)\\b', 'National Testing Agency (NTA)'),
        (r'\\b(drdo)\\b', 'Defence Research and Development Organisation (DRDO)'),
        (r'\\b(isro)\\b', 'Indian Space Research Organisation (ISRO)'),
        (r'\\b(nielit|ccc)\\b', 'National Institute of Electronics and Information Technology (NIELIT)'),
        (r'\\b(up scholarship|scholarship)\\b', 'Uttar Pradesh Social Welfare Department (UP Scholarship)'),
        (r'\\b(atal awasiya)\\b', 'UP Atal Awasiya Vidyalaya'),
        (r'\\b(kgbv|kasturba gandhi)\\b', 'KGBV (Kasturba Gandhi Balika Vidyalaya)'),
        (r'\\b(rvunl|rrvunl)\\b', 'Rajasthan Rajya Vidyut Utpadan Nigam Limited (RVUNL)')
    ]
    for pattern, name in mappings:
        if re.search(pattern, tl):
            return name
    clean = re.sub(r'(online form|recruitment|vacancy|apply online|admit card|result|answer key|syllabus|202\\d|201\\d|various post|\\bpost\\b|advt\\b.*)', '', title, flags=re.I).strip()
    clean = re.sub(r'[\\s\\-:,/]+$', '', clean).strip()
    if len(clean) < 4:
        return default
    return clean
'''

if "def extract_clean_organization" not in code:
    code = clean_org_func + "\n" + code

# 2. Fix how org is extracted in build_post_html
find_org = 'org = data.get("organization", "Recruitment Authority")'
replace_org = '''org = data.get("organization")
        if not org or org in ["Govt Board", "Recruitment Authority", "Government Authority"] or len(org) <= 5 or org in ["Uttar", "Bihar", "State", "Madhya", "Rajasthan"]:
            org = extract_clean_organization(title, default="Recruitment Authority")'''

code = code.replace(find_org, replace_org)

# 3. Ensure Category Vacancy Table ONLY renders when there are meaningful breakdown rows (UR, OBC, SC, ST, EWS, etc.)
find_cat_table = '''        cat_rows = "".join([f'<tr><td style="text-align: center;">{k}</td><td style="text-align: center; font-weight: {"bold" if "Total" in k else "normal"}; color: {"#ff0000" if "Total" in k else "inherit"};">{v}</td></tr>' for k, v in data.get("category_vacancies", {}).items()])
        cat_table_html = ""
        if cat_rows:'''

replace_cat_table = '''        cat_dict = data.get("category_vacancies", {})
        # Only render category table if it contains more than just a single Total Post row
        valid_cats = {k: v for k, v in cat_dict.items() if k.lower() not in ['state name', 'language', 'sl no'] and len(k) > 1}
        has_real_breakdown = any(c in [k.lower() for k in valid_cats.keys()] for c in ['ur', 'gen', 'sc', 'st', 'obc', 'ebc', 'ews', 'female']) or len(valid_cats) >= 3
        
        cat_rows = ""
        if has_real_breakdown:
            cat_rows = "".join([f'<tr><td style="text-align: center;">{k}</td><td style="text-align: center; font-weight: {"bold" if "Total" in k else "normal"}; color: {"#ff0000" if "Total" in k else "inherit"};">{v}</td></tr>' for k, v in valid_cats.items()])

        cat_table_html = ""
        if cat_rows and has_real_breakdown:'''

code = code.replace(find_cat_table, replace_cat_table)

with open('/root/sarkari-result-portal/universal_design_agent.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated universal_design_agent.py with clean org naming and strict category table validation!")
