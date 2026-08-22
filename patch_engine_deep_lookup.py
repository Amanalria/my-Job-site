import re

with open('/root/sarkari-result-portal/post_audit_engine.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Enhance candidate_urls in scrape_deep_source
find_urls = '''    candidate_urls = [
        f"https://www.sarkariresult.com/2026/{slug}/",
        f"https://www.sarkariresult.com/{slug}/",
        f"https://www.sarkariresult.com/latestjob/{slug}/",
        f"https://www.sarkariresult.com/result/{slug}/",
        f"https://www.sarkariresult.com/admitcard/{slug}/",
        f"https://www.sarkariresult.com/admission/{slug}/",
        f"https://www.sarkariresult.com/syllabus/{slug}/",
        f"https://sarkariresult.com.cm/{slug}/"
    ]'''

replace_urls = '''    # Clean slug variants
    clean_slug = slug.strip('/')
    candidate_urls = [
        f"https://www.sarkariresult.com/2026/{clean_slug}/",
        f"https://www.sarkariresult.com/{clean_slug}/",
        f"https://www.sarkariresult.com/latestjob/{clean_slug}/",
        f"https://www.sarkariresult.com/result/{clean_slug}/",
        f"https://www.sarkariresult.com/admitcard/{clean_slug}/",
        f"https://www.sarkariresult.com/admission/{clean_slug}/",
        f"https://www.sarkariresult.com/syllabus/{clean_slug}/",
        f"https://www.sarkariresult.com/bihar/{clean_slug}/",
        f"https://www.sarkariresult.com/bank/{clean_slug}/",
        f"https://sarkariresult.com.cm/{clean_slug}/"
    ]
    
    # Keyword based search if known pattern
    if 'scholarship' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/2026/up-scholarship-postmatric-jul26/")
        candidate_urls.insert(1, "https://www.sarkariresult.com/up-scholarship/")
    if 'si-prohibition' in clean_slug or 'bpssc' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/bihar/bpssc-si-prohibition-03-2026/")
    if 'bijnor' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/2026/up-bijnor-ecce-educator-july26/")
    if 'patna' in clean_slug or 'phc' in clean_slug:
        candidate_urls.insert(0, "https://www.sarkariresult.com/2026/patna-high-court-july26/")'''

code = code.replace(find_urls, replace_urls)

with open('/root/sarkari-result-portal/post_audit_engine.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated post_audit_engine.py with deep URL search and keyword resolution!")
