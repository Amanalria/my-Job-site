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
TMP_DATA_DIR = '/tmp/sarkari_data'

try:
    os.makedirs(TMP_DATA_DIR, exist_ok=True)
except Exception:
    pass

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

def safe_read_json(filepath, default_value=None):
    filename = os.path.basename(filepath)
    tmp_path = os.path.join(TMP_DATA_DIR, filename)
    
    if os.path.exists(tmp_path):
        try:
            with open(tmp_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass

    return default_value if default_value is not None else []

def safe_write_json(filepath, data):
    written = False
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        written = True
    except (OSError, IOError):
        pass

    try:
        os.makedirs(TMP_DATA_DIR, exist_ok=True)
        filename = os.path.basename(filepath)
        tmp_path = os.path.join(TMP_DATA_DIR, filename)
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        written = True
    except Exception:
        pass

    return written

def safe_delete_file(filepath):
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except (OSError, IOError):
        pass
    return False

def parse_date_string(date_str):
    if not date_str or not isinstance(date_str, str):
        return None

    s = date_str.strip().lower()

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

    dmy_match = re.search(r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})', s)
    if dmy_match:
        try:
            d = int(dmy_match.group(1))
            m = int(dmy_match.group(2))
            y = int(dmy_match.group(3))
            return date(y, m, d)
        except Exception:
            pass

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
        "pinned_posts": ["railway-nfr-2026", "sav-bihar-class-6-2026"],
        "last_run_timestamp": None,
        "last_purged_posts": []
    }
    saved = safe_read_json(SETTINGS_FILE, {})
    lifecycle_config = saved.get('lifecycle_config', {})
    default_settings.update(lifecycle_config)
    if 'pinned_posts' in saved and 'pinned_posts' not in lifecycle_config:
        default_settings['pinned_posts'] = saved.get('pinned_posts', default_settings['pinned_posts'])
    return default_settings

def save_lifecycle_settings(config):
    saved = safe_read_json(SETTINGS_FILE, {})
    saved['lifecycle_config'] = config
    saved['pinned_posts'] = config.get('pinned_posts', [])
    safe_write_json(SETTINGS_FILE, saved)

def pin_post(slug):
    config = load_lifecycle_settings()
    pinned = config.get('pinned_posts', [])
    if slug not in pinned:
        pinned.insert(0, slug)
        config['pinned_posts'] = pinned
        save_lifecycle_settings(config)
        audit_and_execute_lifecycle()
    return True

def unpin_post(slug):
    config = load_lifecycle_settings()
    pinned = config.get('pinned_posts', [])
    if slug in pinned:
        pinned.remove(slug)
        config['pinned_posts'] = pinned
        save_lifecycle_settings(config)
        audit_and_execute_lifecycle()
    return True

def toggle_pin_post(slug):
    config = load_lifecycle_settings()
    pinned = config.get('pinned_posts', [])
    if slug in pinned:
        pinned.remove(slug)
        is_pinned = False
    else:
        pinned.insert(0, slug)
        is_pinned = True
    config['pinned_posts'] = pinned
    save_lifecycle_settings(config)
    audit_and_execute_lifecycle()
    return is_pinned

def run_git_sync(commit_msg):
    try:
        subprocess.run(["git", "add", "-A"], cwd=BASE_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        res = subprocess.run(["git", "push", "origin", "master"], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
        return res.returncode == 0
    except Exception as e:
        print(f"Git sync notice: {e}")
        return False

# Blinking CSS - No box background, red text, 15% smaller font size, pulsing blink
BLINKING_CSS = """
<style id="agy-lifecycle-blink-css">
@keyframes agyBlinkPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.15; }
}
.agy-blinking-badge {
    display: inline !important;
    font-weight: 700 !important;
    font-size: 85% !important;
    padding: 0 !important;
    margin-left: 4px !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
    animation: agyBlinkPulse 0.85s infinite ease-in-out !important;
    vertical-align: baseline !important;
    letter-spacing: 0.2px !important;
    line-height: inherit !important;
}
.agy-urgent-blink {
    color: #dc2626 !important;
    background: transparent !important;
}
.agy-extended-blink {
    color: #0284c7 !important;
    background: transparent !important;
}
</style>
"""

def audit_and_execute_lifecycle():
    config = load_lifecycle_settings()
    if not config.get('lifecycle_enabled', True):
        return {"status": "disabled", "message": "Lifecycle automation is currently disabled."}

    urgent_threshold = int(config.get('urgent_days_threshold', 3))
    grace_period = int(config.get('expired_grace_period_days', 1))
    auto_git = config.get('auto_git_sync', True)
    pinned_slugs = set(config.get('pinned_posts', []))
    today = date.today()

    custom_posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
    all_posts_file = os.path.join(DATA_DIR, 'all_posts.json')
    category_data_file = os.path.join(DATA_DIR, 'category_data.json')

    posts = safe_read_json(custom_posts_file, [])
    if not posts:
        posts = safe_read_json(all_posts_file, [])

    if not posts:
        return {"status": "no_posts", "message": "No posts found."}

    purged_slugs = []
    updated_posts = []
    active_posts_by_category = {}

    for post in posts:
        slug = post.get('slug')
        title = post.get('title', '')
        category = post.get('category', 'latest-jobs')
        last_date_str = post.get('application_last_date', '')
        html_file = os.path.join(PAGES_DIR, f"{slug}.html")

        # Check for date extension in HTML content or title
        is_extended = 'extend' in last_date_str.lower() or 'extend' in title.lower() or post.get('custom_badge') == 'Date Extended'

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
                        is_extended = True
                        post['custom_badge'] = "Date Extended"
            except Exception:
                pass

        parsed_date = parse_date_string(last_date_str)
        days_remaining = None
        if parsed_date:
            days_remaining = (parsed_date - today).days

        # Check if manually pinned
        is_pinned = (slug in pinned_slugs)
        post['is_pinned'] = is_pinned

        # Classify state and priority
        if days_remaining is not None:
            if days_remaining < -grace_period:
                purged_slugs.append({
                    "slug": slug,
                    "title": title,
                    "expired_on": parsed_date.isoformat(),
                    "days_ago": abs(days_remaining)
                })

                safe_delete_file(html_file)
                safe_delete_file(os.path.join(RAW_CLONE_DIR, f"{slug}.html"))
                continue

            elif days_remaining < 0:
                # Expired within grace period -> Demoted to bottom
                post['lifecycle_state'] = 'EXPIRED_DEMOTED'
                post['days_remaining'] = days_remaining
                post['lifecycle_badge'] = 'Closed'
                post['badge_html'] = ''
                post['sort_priority'] = -1000 + days_remaining

            elif is_pinned:
                # Manually Pinned -> Absolute Top
                post['lifecycle_state'] = 'URGENT_PINNED'
                post['days_remaining'] = days_remaining
                badge_text = "Date Extended!" if is_extended else ("Last Date Today!" if days_remaining == 0 else f"{days_remaining} Days Left!")
                badge_class = "agy-extended-blink" if is_extended else "agy-urgent-blink"
                post['badge_html'] = f' - <span class="agy-blinking-badge {badge_class}">{badge_text}</span>'
                post['lifecycle_badge'] = badge_text
                post['sort_priority'] = 100000 - min(days_remaining, 10)

            elif days_remaining <= urgent_threshold:
                # Urgent: Closing Soon (<= urgent_days_threshold) -> Pinned to top
                post['lifecycle_state'] = 'URGENT_PINNED'
                post['days_remaining'] = days_remaining
                badge_text = "Last Date Today!" if days_remaining == 0 else f"{days_remaining} Days Left!"
                post['lifecycle_badge'] = badge_text
                post['badge_html'] = f' - <span class="agy-blinking-badge agy-urgent-blink">{badge_text}</span>'
                post['sort_priority'] = 10000 - days_remaining

            else:
                # Active (days_remaining > threshold)
                post['lifecycle_state'] = 'ACTIVE'
                post['days_remaining'] = days_remaining
                if is_extended:
                    post['lifecycle_badge'] = 'Date Extended'
                    post['badge_html'] = ' - <span class="agy-blinking-badge agy-extended-blink">Date Extended!</span>'
                    post['sort_priority'] = 5000 - min(days_remaining, 30)
                else:
                    post['lifecycle_badge'] = ''
                    post['badge_html'] = ''
                    post['sort_priority'] = 100 - min(days_remaining, 90)
        else:
            post['days_remaining'] = None
            if is_pinned:
                post['lifecycle_state'] = 'URGENT_PINNED'
                post['lifecycle_badge'] = 'Pinned'
                post['badge_html'] = ' - <span class="agy-blinking-badge agy-urgent-blink">Important!</span>'
                post['sort_priority'] = 100000
            elif is_extended:
                post['lifecycle_state'] = 'ACTIVE'
                post['lifecycle_badge'] = 'Date Extended'
                post['badge_html'] = ' - <span class="agy-blinking-badge agy-extended-blink">Date Extended!</span>'
                post['sort_priority'] = 4000
            else:
                post['lifecycle_state'] = 'ACTIVE'
                post['lifecycle_badge'] = ''
                post['badge_html'] = ''
                post['sort_priority'] = 50

        updated_posts.append(post)

        if category not in active_posts_by_category:
            active_posts_by_category[category] = []
        active_posts_by_category[category].append(post)

    for cat in active_posts_by_category:
        active_posts_by_category[cat].sort(key=lambda x: x.get('sort_priority', 0), reverse=True)

    sorted_all_posts = []
    for cat in active_posts_by_category:
        sorted_all_posts.extend(active_posts_by_category[cat])
    sorted_all_posts.sort(key=lambda x: x.get('sort_priority', 0), reverse=True)

    safe_write_json(custom_posts_file, sorted_all_posts)
    safe_write_json(all_posts_file, sorted_all_posts)

    cat_data = {}
    for cat, p_list in active_posts_by_category.items():
        cat_data[cat] = []
        for p in p_list:
            cat_data[cat].append({
                'title': p.get('title'),
                'title_raw': p.get('title'),
                'badge_html': p.get('badge_html', ''),
                'url': f"/{p.get('slug')}/",
                'short_desc': p.get('short_desc', ''),
                'date': p.get('application_last_date', p.get('application_start_date', '')),
                'lifecycle_state': p.get('lifecycle_state', 'ACTIVE'),
                'is_pinned': p.get('is_pinned', False)
            })

    safe_write_json(category_data_file, cat_data)

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
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # Ensure updated blinking CSS is in head
            existing_css = soup.find(id='agy-lifecycle-blink-css')
            if existing_css:
                existing_css.decompose()
            if soup.head:
                soup.head.append(BeautifulSoup(BLINKING_CSS, 'html.parser'))

            for col_cls, cat_key in category_column_map.items():
                col = soup.find(class_=col_cls)
                if col:
                    ul = col.find('ul')
                    if ul:
                        ul.clear()
                        cat_posts = cat_data.get(cat_key, [])
                        for item in cat_posts[:12]:
                            li = soup.new_tag('li')
                            title_text = item.get('title_raw', item.get('title', ''))
                            badge = item.get('badge_html', '')
                            link_markup = f'<a href="{item["url"]}" class="wp-block-latest-posts__post-title">{title_text}{badge}</a>'
                            li.append(BeautifulSoup(link_markup, 'html.parser'))
                            ul.append(li)

            top_urgent_posts = []
            for c_k in ['latest-jobs', 'result', 'admit-card', 'admission']:
                top_urgent_posts.extend(active_posts_by_category.get(c_k, []))
            top_urgent_posts.sort(key=lambda x: x.get('sort_priority', 0), reverse=True)

            top_box_classes = [
                'gb-grid-column-2f6de309',
                'gb-grid-column-6de8e6a5',
                'gb-grid-column-f69a2a15',
                'gb-grid-column-cb185b36',
                'gb-grid-column-962a1393',
                'gb-grid-column-48ff7430',
                'gb-grid-column-3b560729',
                'gb-grid-column-659c2f86'
            ]

            for idx, b_cls in enumerate(top_box_classes):
                if idx < len(top_urgent_posts):
                    p_item = top_urgent_posts[idx]
                    boxes = soup.find_all(class_=b_cls)
                    for b in boxes:
                        a_tag = b.find('a')
                        if a_tag:
                            a_tag['href'] = f"/{p_item.get('slug')}/"
                            b_txt = p_item.get('title', '')
                            b_badge = p_item.get('badge_html', '')
                            a_tag.clear()
                            a_tag.append(BeautifulSoup(f"{b_txt}{b_badge}", 'html.parser'))

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            except (OSError, IOError):
                pass
        except Exception as e:
            print(f"Notice: Homepage box sync ({e})")

    sync_homepage_boxes(os.path.join(PAGES_DIR, 'index.html'))
    sync_homepage_boxes(os.path.join(BASE_DIR, 'original_index.html'))

    config['last_run_timestamp'] = datetime.now().isoformat()
    if purged_slugs:
        config['last_purged_posts'] = purged_slugs
    save_lifecycle_settings(config)

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

def start_lifecycle_background_daemon(interval_minutes=60):
    def daemon_loop():
        time.sleep(5)
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
    res = audit_and_execute_lifecycle()
    print(json.dumps(res, indent=2))
