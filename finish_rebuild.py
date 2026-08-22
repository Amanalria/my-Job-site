import sys
import json
import os
sys.path.append('/root/sarkari-result-portal')
import fact_checker_agent
import universal_design_agent

with open('/root/sarkari-result-portal/data/all_posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

uda = universal_design_agent.UniversalDesignAgent()
fca = fact_checker_agent.FactCheckerAgent()

# Find posts whose HTML doesn't have "Eligibility Criteria" properly formatted in a table, or just rebuild all 29
# To be safe, just rebuild the ones that might be missing it. Let's just rebuild the last 15 from the initial 29.
initial_29 = [p for p in posts if p.get('category') == 'latest-jobs'][:29]
for p in initial_29:
    slug = p['slug']
    filepath = f"/root/sarkari-result-portal/pages/{slug}.html"
    if os.path.exists(filepath):
        with open(filepath, 'r') as f_html:
            html = f_html.read()
        if "Eligibility Criteria" not in html or "Category Wise Vacancy" not in html:
            # Needs rebuild
            url = f"https://www.sarkariresult.com/2026/{slug}/"
            print(f"Re-fetching tables for {slug}...")
            data = fca.fetch_live_source_data(slug, url)
            if data:
                data['slug'] = p.get('slug')
                data['category'] = p.get('category', 'latest-jobs')
                data['organization'] = data.get('title', 'Govt Board').split()[0]
                data['title'] = p.get('title')
                data['short_desc'] = p.get('short_desc')
                data['last_date'] = p.get('application_last_date')
                try:
                    uda.publish(data)
                    print(f"Fixed {slug}")
                except Exception as e:
                    pass
