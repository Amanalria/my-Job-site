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
    slug = p['slug']
    cat = p.get('category', 'latest-jobs')
    url = f"https://www.sarkariresult.com/2026/{slug}/"
    if cat == 'result': url = f"https://www.sarkariresult.com/result/{slug}/"
    elif cat == 'admit-card': url = f"https://www.sarkariresult.com/admitcard/{slug}/"
    elif cat == 'answer-key': url = f"https://www.sarkariresult.com/answerkey/{slug}/"
    elif cat == 'syllabus': url = f"https://www.sarkariresult.com/syllabus/{slug}/"
    elif cat == 'admission': url = f"https://www.sarkariresult.com/admission/{slug}/"
    
    print(f"Re-fetching {slug}...")
    try:
        data = fca.fetch_live_source_data(slug, url)
        if not data:
            data = {}
            
        # Overwrite with correct metadata
        data['slug'] = p.get('slug')
        data['category'] = p.get('category', 'latest-jobs')
        data['organization'] = data.get('title', p.get('title', 'Govt Board')).split()[0]
        data['title'] = p.get('title', data.get('title', slug))
        data['short_desc'] = p.get('short_desc')
        data['last_date'] = p.get('application_last_date')

        # GUARANTEE POST MATRIX
        if not data.get('post_matrix'):
            data['post_matrix'] = [{
                "name": data.get("organization", "Various Posts") + " Recruitment",
                "posts": data.get("total_posts", "See Notification"),
                "eligibility": "Please refer to the official notification linked below for detailed educational qualifications."
            }]
            
        # GUARANTEE HOW TO FILL
        if not data.get('how_to_fill'):
            if cat in ['latest-jobs', 'admission']:
                data['how_to_fill'] = [
                    "Read the official recruitment notification carefully before applying.",
                    "Keep all basic documents ready: ID Proof, Address Details, Basic Details.",
                    "Ready your scanned documents like Photo, Signature, ID Proof, etc.",
                    "Click on the 'Apply Online' link given in the Important Links section below.",
                    "Fill out all the columns in the application form accurately.",
                    "Pay the required application fee if applicable.",
                    "Take a printout of the final submitted application form."
                ]
            else:
                data['how_to_fill'] = [
                    "Scroll down to the 'Important Links' section on this page.",
                    "Click on the direct link to download/check your status.",
                    "Enter your required login credentials such as Registration Number, Roll Number, or Date of Birth.",
                    "Click on submit to view your status.",
                    "Download and take a printout for future reference."
                ]

        uda.publish(data)
        count += 1
    except Exception as e:
        print(f"Failed {slug}: {e}")

print(f"Completely fixed {count} posts!")
