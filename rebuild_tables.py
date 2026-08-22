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

count = 0
for p in posts:
    if p.get('category') == 'latest-jobs':
        slug = p['slug']
        # Try to re-fetch data
        url = f"https://www.sarkariresult.com/2026/{slug}/"
        print(f"Re-fetching tables for {slug}...")
        data = fca.fetch_live_source_data(slug, url)
        if data:
            # We want to keep the old humanizer properties (slug, title, short_desc, last_date)
            # but inject the new tables.
            data['slug'] = p.get('slug')
            data['category'] = p.get('category', 'latest-jobs')
            data['organization'] = data.get('title', 'Govt Board').split()[0]
            data['title'] = p.get('title')
            data['short_desc'] = p.get('short_desc')
            data['last_date'] = p.get('application_last_date')
            
            # Use UniversalDesignAgent to rebuild the HTML
            try:
                uda.publish(data)
                print(f"Rebuilt HTML for {slug} with tables.")
                count += 1
            except Exception as e:
                print(f"Failed to rebuild {slug}: {e}")

print(f"Rebuilt {count} posts.")
