import os
import re
import json
import subprocess
import threading
import time
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, 'pages')
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_CLONE_DIR = os.path.join(BASE_DIR, 'raw_clone/pages')
SETTINGS_FILE = os.path.join(DATA_DIR, 'settings.json')

MONTH_MAP = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'september': 9, 'sept': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

def parse_date_string(date_str):
    if not date_str or not isinstance(date_str, str):
        return None

    s = date_str.strip().lower()

    # Look for extended date first if present (e.g. "28 August 2026 (Extended)")
    extended_match = re.search(r'(\d{1,2})\s+([a-z]+)\s+(\d{4})', s)
    if extended_match:
        d = int(extended_match.group(1))
        m_str = extended_match.group(2)
        y = int(extended_match.group(3))
        if m_str in MONTH_MAP:
            try:
                return date(y, MONTH_MAP[m_str], d)
            except Exception:
                pass

    # Match DD-MM-YYYY or DD/MM/YYYY or DD.MM.YYYY
    dmy_match = re.search(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})', s)
    if dmy_match:
        try:
            d = int(dmy_match.group(1))
            m = int(dmy_match.group(2))
            y = int(dmy_match.group(3))
            return date(y, m, d)
        except Exception:
            pass

    # Match YYYY-MM-DD
    ymd_match = re.search(r'(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})', s)
    if ymd_match:
        try:
            y = int(ymd_match.group(1))
            m = int(ymd_match.group(2))
            d = int(ymd_match.group(3))
            return date(y, m, d)
        except Exception:
            pass

    return None

def load_lifecycle_settings():
    default_settings = {
        "lifecycle_enabled": True,
        "urgent_days_threshold": 3,
        "expired_grace_period_days": 1,
        "auto_git_sync": True,
        "auto_detect_date_extension": True,
        "last_run_timestamp": None,
        "last_purged_posts": []
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                lifecycle_config = saved.get('lifecycle_config', {})
                default_settings.update(lifecycle_config)
        except Exception:
            pass
    return default_settings

def save_lifecycle_settings(config):
    try:
        saved = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
        saved['lifecycle_config'] = config
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(saved, f, indent=2)
    except Exception as e:
        print(f"Error saving lifecycle settings: {e}")

def run_git_sync(commit_msg):
    try:
        subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = subprocess.run(["git", "push", "origin", "master"], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
        return res.returncode == 0
    except Exception as e:
        print(f"Git sync notice: {e}")
        return False

def audit_and_execute_lifecycle():
    """
    Core automated execution:
    1. Evaluates all posts against today's date.
    2. Identifies:
       - Urgent Posts (<= 3 days remaining) -> Pins to top of categories and homepage.
       - Active Posts (> 3 days remaining or no fixed end date).
       - Expired Posts (< 0 days) -> Demotes to bottom.
       - Purge Posts (expired > grace_period_days) -> Deletes from website, JSON DB, and GitHub.
    3. Detects date extensions in post HTML/text and auto-updates last dates.
    4. Rewrites homepage category boxes to reflect real-time priorities.
    """
    config = load_lifecycle_settings()
    if not config.get('lifecycle_enabled', True):
        return {"status": "disabled", "message": "Lifecycle automation is currently disabled."}

    urgent_threshold = int(config.get('urgent_days_threshold', 3))
    grace_period = int(config.get('expired_grace_period_days', 1))
    auto_git = config.get('auto_git_sync', True)
    today = date.today()

    custom_posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
    all_posts_file = os.path.join(DATA_DIR, 'all_posts.json')
    category_data_file = os.path.join(DATA_DIR, 'category_data.json')

    if not os.path.exists(custom_posts_file):
        return {"status": "no_posts", "message": "No posts found."}

    with open(custom_posts_file, 'r', encoding='utf-8') as f:
        posts = json.load(f)

    purged_slugs = []
    updated_posts = []
    active_posts_by_category = {}

    for post in posts:
        slug = post.get('slug')
        title = post.get('title', '')
        category = post.get('category', 'latest-jobs')
        last_date_str = post.get('application_last_date', '')
        html_file = os.path.join(PAGES_DIR, f"{slug}.html")

        # 1. Check for date extension in HTML content if enabled
        if config.get('auto_detect_date_extension', True) and os.path.exists(html_file):
            try:
                with open(html_file, 'r', encoding='utf-8') as hf:
                    html_text = hf.read()
                ext_match = re.search(r'(?:extended\s+(?:to|till|upto)?|new\s+last\s+date)\s*[:\-–]?\s*([0-9]{1,2}\s+[a-zA-Z]+\s+[0-9]{4})', html_text, re.I)
                if ext_match:
                    new_extended_date = ext_match.group(1).strip()
                    if new_extended_date and new_extended_date != last_date_str:
                        post['application_last_date'] = new_extended_date
                        last_date_str = new_extended_date
                        post['custom_badge'] = "Date Extended"
            except Exception:
                pass

        parsed_date = parse_date_string(last_date_str)
        days_remaining = None
        if parsed_date:
            days_remaining = (parsed_date - today).days

        # Classify state
        if days_remaining is not None:
            if days_remaining < -grace_period:
                # Expired past grace period -> Auto-Delete
                purged_slugs.append({
                    "slug": slug,
                    "title": title,
                    "expired_on": parsed_date.isoformat(),
                    "days_ago": abs(days_remaining)
                })

                # Remove HTML files
                if os.path.exists(html_file):
                    try:
                        os.remove(html_file)
                    except Exception:
                        pass
                raw_file = os.path.join(RAW_CLONE_DIR, f"{slug}.html")
                if os.path.exists(raw_file):
                    try:
                        os.remove(raw_file)
                    except Exception:
                        pass
                continue

            elif days_remaining < 0:
                # Expired within grace period -> Demote to bottom
                post['lifecycle_state'] = 'EXPIRED_DEMOTED'
                post['days_remaining'] = days_remaining
                post['lifecycle_badge'] = 'Closed / Expired'
                post['sort_priority'] = -100 + days_remaining # Negative priority so it goes to bottom
            elif days_remaining <= urgent_threshold:
                # Urgent: Closing Soon (<= 3 days) -> Pin to top
                post['lifecycle_state'] = 'URGENT_PINNED'
                post['days_remaining'] = days_remaining
                badge_text = "Last Date Today!" if days_remaining == 0 else f"{days_remaining} Days Left!"
                post['lifecycle_badge'] = badge_text
                post['sort_priority'] = 1000 - days_remaining # Highest priority at top
            else:
                # Active
                post['lifecycle_state'] = 'ACTIVE'
                post['days_remaining'] = days_remaining
                post['lifecycle_badge'] = ''
                post['sort_priority'] = 100 - min(days_remaining, 90)
        else:
            # No specific end date (e.g. Schemes, Calendars, Certificate verification)
            post['lifecycle_state'] = 'ACTIVE'
            post['days_remaining'] = None
            post['lifecycle_badge'] = ''
            post['sort_priority'] = 50

        updated_posts.append(post)

        if category not in active_posts_by_category:
            active_posts_by_category[category] = []
        active_posts_by_category[category].append(post)

    # Sort each category: Urgent Pinned (top) -> Active -> Expired Demoted (bottom)
    for cat in active_posts_by_category:
        active_posts_by_category[cat].sort(key=lambda x: x.get('sort_priority', 0), reverse=True)

    # Reassemble global custom_posts list with top urgent posts first
    sorted_all_posts = []
    for cat in active_posts_by_category:
        sorted_all_posts.extend(active_posts_by_category[cat])
    sorted_all_posts.sort(key=lambda x: x.get('sort_priority', 0), reverse=True)

    # Save to custom_posts.json and all_posts.json
    with open(custom_posts_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_all_posts, f, indent=2)

    with open(all_posts_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_all_posts, f, indent=2)

    # Save category_data.json
    cat_data = {}
    for cat, p_list in active_posts_by_category.items():
        cat_data[cat] = []
        for p in p_list:
            badge_suffix = f" [{p.get('lifecycle_badge')}]" if p.get('lifecycle_badge') else ""
            cat_data[cat].append({
                'title': f"{p.get('title')}{badge_suffix}",
                'url': f"/{p.get('slug')}/",
                'short_desc': p.get('short_desc', ''),
                'date': p.get('application_last_date', p.get('application_start_date', '')),
                'lifecycle_state': p.get('lifecycle_state', 'ACTIVE')
            })

    with open(category_data_file, 'w', encoding='utf-8') as f:
        json.dump(cat_data, f, indent=2)

    # Update Homepage Category Boxes
    category_column_map = {
        'gb-grid-column-0b76599a': 'result',
        'gb-grid-column-c7488d9a': 'latest-jobs',
        'gb-grid-column-e64d3148': 'admit-card',
        'gb-grid-column-d19ddc59': 'answer-key',
        'gb-grid-column-b48dca36': 'syllabus',
        'gb-grid-column-51daea0e': 'admission'
    }

    def sync_homepage_boxes(filepath):
        if not os.path.exists(filepath):
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')

            for col_cls, cat_key in category_column_map.items():
                col = soup.find(class_=col_cls)
                if col:
                    ul = col.find('ul')
                    if ul:
                        ul.clear()
                        cat_posts = cat_data.get(cat_key, [])
                        for item in cat_posts[:10]:
                            li = soup.new_tag('li')
                            a = soup.new_tag('a', href=item['url'], class_='wp-block-latest-posts__post-title')
                            a.string = item['title']
                            li.append(a)
                            ul.append(li)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
        except Exception as e:
            print(f"Error updating {filepath}: {e}")

    sync_homepage_boxes(os.path.join(PAGES_DIR, 'index.html'))
    sync_homepage_boxes(os.path.join(BASE_DIR, 'original_index.html'))

    # Update config run record
    config['last_run_timestamp'] = datetime.now().isoformat()
    if purged_slugs:
        config['last_purged_posts'] = purged_slugs
    save_lifecycle_settings(config)

    # Auto Git push if posts were purged and auto_git is enabled
    git_synced = False
    if purged_slugs and auto_git:
        commit_msg = f"chore(lifecycle): auto-purge {len(purged_slugs)} expired vacancies past grace period"
        git_synced = run_git_sync(commit_msg)

    return {
        "status": "success",
        "timestamp": config['last_run_timestamp'],
        "total_active_posts": len(sorted_all_posts),
        "purged_count": len(purged_slugs),
        "purged_posts": purged_slugs,
        "git_synced": git_synced
    }

# Background Daemon Worker Thread
def start_lifecycle_background_daemon(interval_minutes=60):
    def daemon_loop():
        time.sleep(10) # Initial startup buffer
        while True:
            try:
                audit_and_execute_lifecycle()
            except Exception as e:
                print(f"Lifecycle daemon exception: {e}")
            time.sleep(interval_minutes * 60)

    t = threading.Thread(target=daemon_loop, daemon=True)
    t.start()
    return t

if __name__ == '__main__':
    result = audit_and_execute_lifecycle()
    print("Lifecycle Execution Summary:")
    print(json.dumps(result, indent=2))
