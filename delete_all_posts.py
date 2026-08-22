import os
import json
import glob
from bs4 import BeautifulSoup

BASE_DIR = "/root/sarkari-result-portal"
PAGES_DIR = os.path.join(BASE_DIR, "pages")
DATA_DIR = os.path.join(BASE_DIR, "data")
THUMB_DIR = os.path.join(BASE_DIR, "static", "thumbnails")

STATIC_PAGES = [
    'about-us.html', 'about.html', 'contact.html', 'disclaimer.html',
    'privacy-policy.html', 'terms-and-conditions.html', 'terms.html',
    'index.html', 'admission.html', 'admit-card.html', 'answer-key.html',
    'latest-jobs.html', 'result.html', 'syllabus.html'
]

# 1. Delete all non-static pages
deleted_pages = 0
for f in os.listdir(PAGES_DIR):
    if f.endswith('.html') and f not in STATIC_PAGES:
        os.remove(os.path.join(PAGES_DIR, f))
        deleted_pages += 1

# 2. Delete all thumbnails (except .keep or placeholders if any, but webp files are generated)
deleted_thumbs = 0
for f in os.listdir(THUMB_DIR):
    if f.endswith('.webp') and f != 'placeholder.webp':
        os.remove(os.path.join(THUMB_DIR, f))
        deleted_thumbs += 1

# 3. Empty data files
with open(os.path.join(DATA_DIR, "all_posts.json"), "w") as f:
    json.dump([], f)
with open(os.path.join(DATA_DIR, "custom_posts.json"), "w") as f:
    json.dump([], f)
with open(os.path.join(DATA_DIR, "category_data.json"), "w") as f:
    json.dump({}, f)

# 4. Clear index.html lists
category_column_map = {
    'gb-grid-column-0b76599a': 'result',
    'gb-grid-column-c7488d9a': 'latest-jobs',
    'gb-grid-column-e64d3148': 'admit-card',
    'gb-grid-column-d19ddc59': 'answer-key',
    'gb-grid-column-b48dca36': 'syllabus',
    'gb-grid-column-51daea0e': 'admission'
}

def clear_index_lists(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    for col_cls, cat_key in category_column_map.items():
        col = soup.find(class_=col_cls)
        if col:
            ul = col.find('ul')
            if ul:
                ul.clear()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(str(soup))

clear_index_lists(os.path.join(PAGES_DIR, 'index.html'))
clear_index_lists(os.path.join(BASE_DIR, 'original_index.html'))

print(f"Deleted {deleted_pages} posts and {deleted_thumbs} thumbnails.")
print("Cleared JSON databases and index.html categories.")
