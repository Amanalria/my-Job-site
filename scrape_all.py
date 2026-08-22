import sys
import json
import requests
from bs4 import BeautifulSoup
import re
import os
sys.path.append('/root/sarkari-result-portal')
import fact_checker_agent
import universal_design_agent

# 1. Load existing posts
with open('/root/sarkari-result-portal/data/all_posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)
existing_slugs = {p['slug'] for p in posts}

# 2. Get links
url = "https://www.sarkariresult.com/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, 'html.parser')

links = []
for a in soup.find_all('a'):
    href = a.get('href', '')
    if 'sarkariresult.com' in href and '2026/' in href:
        match = re.search(r'sarkariresult\.com/(.*?/.*?)/?$', href)
        if match:
            slug = match.group(1).strip('/').split('/')[-1]
            if slug and len(slug) > 5 and slug != 'latestjob':
                links.append((slug, href))

# Unique preservation
seen = set()
unique_links = []
for slug, href in links:
    if slug not in seen and slug not in existing_slugs:
        seen.add(slug)
        unique_links.append((slug, href))

print(f"Found {len(unique_links)} new jobs to scrape.")

uda = universal_design_agent.UniversalDesignAgent()
fca = fact_checker_agent.FactCheckerAgent()
count = 0

for slug, href in unique_links:
    try:
        print(f"Processing: {slug}")
        data = fca.fetch_live_source_data(slug, href)
        if data:
            data['slug'] = slug
            data['category'] = 'latest-jobs'
            data['organization'] = data.get('title', 'Govt Board').split()[0]
            data['title'] = data.get('title', slug.replace('-', ' ').title())
            data['short_desc'] = f"{data['organization']} has released {data['title']} for {data.get('total_posts', 'Various Posts')}."
            
            imp_dates = data.get('important_dates', {})
            last_d = "Soon"
            for k, v in imp_dates.items():
                if 'last date' in k.lower():
                    last_d = v
                    break
            if last_d == "Soon" and imp_dates:
                last_d = list(imp_dates.values())[-1]
            data['last_date'] = last_d
            
            uda.publish(data)
            count += 1
    except Exception as e:
        print(f"Error on {slug}: {e}")

print(f"Scraped {count} additional posts.")
import vacancy_lifecycle_engine
vacancy_lifecycle_engine.audit_and_execute_lifecycle()
os.system('cd /root/sarkari-result-portal && git add . && git commit -m "feat(scraper): automated scraping of all latest sarkariresult posts" && git push origin master')
