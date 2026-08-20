import os
import time
import hmac
import hashlib
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, request, redirect, jsonify, render_template, Response

# Master Credentials (Hashed with PBKDF2:SHA256)
ADMIN_USERNAME = "bittu07"
ADMIN_PASSWORD_HASH = generate_password_hash("bittu@2003", method="pbkdf2:sha256")

# In-Memory Brute Force Defense System
FAILED_ATTEMPTS = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes
SESSION_MAX_AGE_SECONDS = 86400 * 7  # 7 days

def get_client_ip():
    """Extract real client IP considering proxies and headers securely"""
    if request.headers.get('CF-Connecting-IP'):
        return request.headers.get('CF-Connecting-IP').strip()
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'

def is_ip_locked(ip: str):
    """Check if an IP is temporarily locked due to brute-force attempts"""
    now = time.time()
    info = FAILED_ATTEMPTS.get(ip)
    if not info:
        return False, 0
    locked_until = info.get('locked_until', 0)
    if now < locked_until:
        return True, int(locked_until - now)
    return False, 0

def record_failed_attempt(ip: str):
    """Record a failed login attempt and apply lockouts"""
    now = time.time()
    info = FAILED_ATTEMPTS.get(ip, {'count': 0, 'first_attempt': now, 'locked_until': 0})
    if (now - info.get('first_attempt', now)) > 900:
        info = {'count': 0, 'first_attempt': now, 'locked_until': 0}
    info['count'] += 1
    if info['count'] >= MAX_FAILED_ATTEMPTS:
        info['locked_until'] = now + LOCKOUT_DURATION_SECONDS
    FAILED_ATTEMPTS[ip] = info

def reset_failed_attempts(ip: str):
    """Clear failed attempts on successful login"""
    if ip in FAILED_ATTEMPTS:
        del FAILED_ATTEMPTS[ip]

def verify_credentials(username: str, password: str, ip: str):
    """Strict constant-time credential check with brute-force protection"""
    locked, remaining = is_ip_locked(ip)
    if locked:
        return False, f"Too many failed login attempts. Security lockout active for {remaining} seconds."

    # Constant-time comparison
    is_user_valid = hmac.compare_digest(username.strip(), ADMIN_USERNAME)
    is_pass_valid = check_password_hash(ADMIN_PASSWORD_HASH, password)

    if is_user_valid and is_pass_valid:
        reset_failed_attempts(ip)
        return True, "Login successful."
    
    record_failed_attempt(ip)
    locked_now, rem_now = is_ip_locked(ip)
    if locked_now:
        return False, f"Too many failed attempts. Security lockout active for {rem_now} seconds."
    
    return False, "Invalid username or password. Access denied."

def login_user(username: str):
    """Initialize secure authenticated session"""
    session.permanent = True
    session['user_id'] = username
    session['auth_token'] = hashlib.sha256(f"{username}:{ADMIN_PASSWORD_HASH}".encode()).hexdigest()
    session['logged_in_at'] = int(time.time())
    session['ip'] = get_client_ip()

def logout_user():
    """Clear authenticated session"""
    session.clear()

def is_authenticated():
    """Validate authenticated session with token and timeout checks"""
    if not session.get('user_id'):
        return False
    if session.get('user_id') != ADMIN_USERNAME:
        return False
    
    logged_in_at = session.get('logged_in_at', 0)
    if (time.time() - logged_in_at) > SESSION_MAX_AGE_SECONDS:
        logout_user()
        return False
        
    expected_token = hashlib.sha256(f"{ADMIN_USERNAME}:{ADMIN_PASSWORD_HASH}".encode()).hexdigest()
    return hmac.compare_digest(session.get('auth_token', ''), expected_token)

def admin_required(f):
    """Decorator protecting routes against unauthorized access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            if request.path.startswith('/api/') or request.is_json or request.method == 'POST':
                return jsonify({'error': 'Unauthorized: Admin authentication required', 'status': 401}), 401
            next_url = request.full_path if request.query_string else request.path
            return redirect(f'/admin/login?next={next_url}')
        return f(*args, **kwargs)
    return decorated_function
