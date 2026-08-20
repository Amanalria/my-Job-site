import os
import json
import requests

def get_supabase_credentials():
    """Retrieve Supabase URL and Key from env vars or settings.json"""
    url = os.environ.get('SUPABASE_URL', '').strip()
    key = os.environ.get('SUPABASE_KEY', '').strip()
    
    if not url or not key:
        settings_file = os.path.join(os.path.dirname(__file__), 'data', 'settings.json')
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    s = json.load(f)
                    supa = s.get('supabase', {})
                    if not url: url = supa.get('url', '').strip()
                    if not key: key = supa.get('key', '').strip()
            except Exception:
                pass

    if url and not url.startswith('http'):
        url = f"https://{url}"
    url = url.rstrip('/')
    return url, key

def is_supabase_configured():
    url, key = get_supabase_credentials()
    return bool(url and key and 'supabase.co' in url)

def get_headers(key):
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

def test_supabase_connection():
    url, key = get_supabase_credentials()
    if not url or not key:
        return {'connected': False, 'message': 'Supabase URL or Key is missing in Settings.'}
    
    try:
        req_url = f"{url}/rest/v1/settings?select=key&limit=1"
        res = requests.get(req_url, headers=get_headers(key), timeout=6)
        if res.status_code in [200, 201]:
            return {'connected': True, 'message': 'Connected to Supabase PostgreSQL successfully!'}
        elif res.status_code == 401 or res.status_code == 403:
            return {'connected': False, 'message': f'Authentication failed ({res.status_code}). Check your Anon/Service Key.'}
        elif res.status_code == 404:
            return {'connected': True, 'message': 'Connected to Supabase! (Note: Remember to run schema.sql in SQL Editor to create tables).'}
        else:
            return {'connected': False, 'message': f'Supabase response: HTTP {res.status_code} - {res.text}'}
    except Exception as e:
        return {'connected': False, 'message': f'Connection Error: {str(e)}'}

# ==================== POSTS OPERATIONS ====================

def fetch_posts_from_supabase():
    url, key = get_supabase_credentials()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/posts?select=*&order=created_at.desc"
        res = requests.get(req_url, headers=get_headers(key), timeout=6)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

def save_post_to_supabase(post_data):
    import uuid
    url, key = get_supabase_credentials()
    if not url or not key:
        return False
    try:
        allowed_cols = {'id', 'slug', 'title', 'category', 'short_desc', 'application_start_date', 'application_last_date', 'custom_badge', 'is_pinned', 'created_at', 'html_content'}
        filtered_payload = {k: v for k, v in post_data.items() if k in allowed_cols}
        slug = filtered_payload.get('slug', 'default')
        raw_id = filtered_payload.get('id', '')
        if not raw_id or len(raw_id) != 36:
            filtered_payload['id'] = str(uuid.uuid5(uuid.NAMESPACE_DNS, slug))
        headers = get_headers(key)
        headers['Prefer'] = 'resolution=merge-duplicates'
        req_url = f"{url}/rest/v1/posts"
        res = requests.post(req_url, headers=headers, json=filtered_payload, timeout=8)
        return res.status_code in [200, 201, 204]
    except Exception:
        return False

def delete_post_from_supabase(post_id_or_slug):
    url, key = get_supabase_credentials()
    if not url or not key:
        return False
    try:
        req_url = f"{url}/rest/v1/posts?or=(id.eq.{post_id_or_slug},slug.eq.{post_id_or_slug})"
        res = requests.delete(req_url, headers=get_headers(key), timeout=8)
        return res.status_code in [200, 204]
    except Exception:
        return False

def wipe_temporary_posts_from_supabase():
    """Wipe all posts flagged as is_temporary=True"""
    url, key = get_supabase_credentials()
    if not url or not key:
        return False
    try:
        req_url = f"{url}/rest/v1/posts?is_temporary=eq.true"
        res = requests.delete(req_url, headers=get_headers(key), timeout=8)
        return res.status_code in [200, 204]
    except Exception:
        return False

# ==================== SETTINGS OPERATIONS ====================

def fetch_settings_from_supabase():
    url, key = get_supabase_credentials()
    if not url or not key:
        return None
    try:
        req_url = f"{url}/rest/v1/settings?key=eq.portal_settings&select=value"
        res = requests.get(req_url, headers=get_headers(key), timeout=6)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                return data[0].get('value')
    except Exception:
        pass
    return None

def save_settings_to_supabase(settings_data):
    url, key = get_supabase_credentials()
    if not url or not key:
        return False
    try:
        headers = get_headers(key)
        headers['Prefer'] = 'resolution=merge-duplicates'
        req_url = f"{url}/rest/v1/settings"
        payload = {
            'key': 'portal_settings',
            'value': settings_data
        }
        res = requests.post(req_url, headers=headers, json=payload, timeout=8)
        return res.status_code in [200, 201, 204]
    except Exception:
        return False
