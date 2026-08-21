import os
import json
import time
import requests
from datetime import datetime

try:
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'service_account.json')
INDEXING_LOGS_FILE = os.path.join(DATA_DIR, 'indexing_logs.json')
ACTIVE_URLS_FILE = os.path.join(DATA_DIR, 'active_urls.txt')
DEINDEX_URLS_FILE = os.path.join(DATA_DIR, 'deindex_urls.txt')
EXPIRED_DELETED_FILE = os.path.join(DATA_DIR, 'expired_deleted_posts.json')

SCOPES = ["https://www.googleapis.com/auth/indexing"]
INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"

def load_indexing_logs():
    if os.path.exists(INDEXING_LOGS_FILE):
        try:
            with open(INDEXING_LOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_indexing_logs(logs):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(INDEXING_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("[Indexing] Error saving logs:", e)

def get_access_token():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return None, "service_account.json key file not found. Please upload your Google Service Account JSON."
    
    if not GOOGLE_AUTH_AVAILABLE:
        return None, "google-auth package not found. Run pip install google-auth."
        
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        creds.refresh(Request())
        return creds.token, None
    except Exception as e:
        return None, f"Google Auth Error: {str(e)}"

def submit_url_to_google(url, action_type="URL_UPDATED"):
    token, err = get_access_token()
    if err:
        return {"success": False, "url": url, "error": err}
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url.strip(),
        "type": action_type
    }
    
    try:
        res = requests.post(INDEXING_ENDPOINT, headers=headers, json=payload, timeout=15)
        resp_body = res.json() if res.headers.get('content-type', '').startswith('application/json') else res.text
        log_entry = {
            "url": url.strip(),
            "type": action_type,
            "timestamp": datetime.now().isoformat(),
            "status_code": res.status_code,
            "response": resp_body
        }
        
        logs = load_indexing_logs()
        logs.insert(0, log_entry)
        save_indexing_logs(logs[:1000])
        
        if res.status_code == 200:
            return {"success": True, "url": url, "response": resp_body}
        else:
            return {"success": False, "url": url, "status_code": res.status_code, "error": resp_body}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}

def load_active_urls():
    if os.path.exists(ACTIVE_URLS_FILE):
        try:
            with open(ACTIVE_URLS_FILE, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
                if lines:
                    return list(dict.fromkeys(lines))
        except Exception:
            pass

    # Fallback to posts.json
    posts_file = os.path.join(DATA_DIR, 'all_posts.json')
    if not os.path.exists(posts_file):
        posts_file = os.path.join(DATA_DIR, 'custom_posts.json')
    urls = ["https://studytopper.in/"]
    if os.path.exists(posts_file):
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                posts = json.load(f)
                for p in posts:
                    if p.get('slug'):
                        urls.append(f"https://studytopper.in/{p.get('slug')}/")
        except Exception:
            pass
    return list(dict.fromkeys(urls))

def load_deindex_urls():
    urls = []
    if os.path.exists(DEINDEX_URLS_FILE):
        try:
            with open(DEINDEX_URLS_FILE, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except Exception:
            pass

    if os.path.exists(EXPIRED_DELETED_FILE):
        try:
            with open(EXPIRED_DELETED_FILE, 'r', encoding='utf-8') as f:
                deleted = json.load(f)
                for d in deleted:
                    u = d.get('url') or f"https://studytopper.in/{d.get('slug')}/"
                    if u:
                        urls.append(u)
        except Exception:
            pass

    return list(dict.fromkeys(urls))

def bulk_submit_urls(url_list, action_type="URL_UPDATED", delay=0.4):
    results = []
    for url in url_list:
        if url:
            res = submit_url_to_google(url, action_type)
            results.append(res)
            time.sleep(delay)
    return results

if __name__ == '__main__':
    # Cloud CLI Runner: Indexes active and deindexes deleted
    print("=== Google Indexing Engine Standalone Run ===")
    active = load_active_urls()
    deindex = load_deindex_urls()
    print(f"Loaded {len(active)} active URLs and {len(deindex)} de-index URLs.")
    
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        print("Submitting active URLs to Google Indexing API...")
        bulk_submit_urls(active, action_type="URL_UPDATED")
        if deindex:
            print("Submitting de-index URLs to Google Indexing API...")
            bulk_submit_urls(deindex, action_type="URL_DELETED")
        print("Completed Google Indexing synchronization!")
    else:
        print("Notice: service_account.json not configured yet.")
