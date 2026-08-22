import json, os, time
import post_audit_engine
import universal_design_agent

uda = universal_design_agent.UniversalDesignAgent()

with open('/root/sarkari-result-portal/data/all_posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)

print(f"Force healing all {len(posts)} posts with exact official data + 3 Humanizer sections...")

count = 0
for idx, p in enumerate(posts):
    slug = p.get('slug')
    print(f"[{idx+1}/{len(posts)}] Rebuilding: {slug}...")
    try:
        ok = post_audit_engine.heal_post(p, uda)
        if ok:
            count += 1
    except Exception as e:
        print(f"Error on {slug}: {e}")
    time.sleep(0.05)

print(f"Successfully rebuilt {count}/{len(posts)} posts!")
