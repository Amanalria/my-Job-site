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
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'service_account.json')
INDEXING_LOGS_FILE = os.path.join(BASE_DIR, 'data', 'indexing_logs.json')
SCOPES = ["https://www.googleapis.com/auth/indexing"]
INDEXING_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications:publish"
METADATA_ENDPOINT = "https://indexing.googleapis.com/v3/urlNotifications/metadata"

def load_indexing_logs():
    if os.path.exists(INDEXING_LOGS_FILE):
        try:
            with open(INDEXING_LOGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_indexing_logs(logs):
    os.makedirs(os.path.dirname(INDEXING_LOGS_FILE), exist_ok=True)
    try:
        with open(INDEXING_LOGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("[Indexing] Error saving logs:", e)

def get_access_token():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        return None, "service_account.json key file not found. Please upload or save your Google Service Account JSON."
    
    if not GOOGLE_AUTH_AVAILABLE:
        # Fallback to pure python jwt if google-auth not installed
        return None, "google-auth package required. Install with pip install google-auth requests."
        
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        creds.refresh(Request())
        return creds.token, None
    except Exception as e:
        return None, f"Failed to authenticate with Google: {str(e)}"

def submit_url_to_google(url, action_type="URL_UPDATED"):
    token, err = get_access_token()
    if err:
        return {"success": False, "url": url, "error": err}
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "type": action_type
    }
    
    try:
        res = requests.post(INDEXING_ENDPOINT, headers=headers, json=payload, timeout=15)
        log_entry = {
            "url": url,
            "type": action_type,
            "timestamp": datetime.now().isoformat(),
            "status_code": res.status_code,
            "response": res.json() if res.headers.get('content-type', '').startswith('application/json') else res.text
        }
        
        # Save to local logs
        logs = load_indexing_logs()
        logs.insert(0, log_entry)
        save_indexing_logs(logs[:500]) # Keep last 500
        
        if res.status_code == 200:
            return {"success": True, "url": url, "response": log_entry["response"]}
        else:
            return {"success": False, "url": url, "status_code": res.status_code, "error": log_entry["response"]}
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}

def bulk_submit_urls(url_list, action_type="URL_UPDATED", delay=0.5):
    results = []
    for url in url_list:
        res = submit_url_to_google(url, action_type)
        results.append(res)
        time.sleep(delay)
    return results
