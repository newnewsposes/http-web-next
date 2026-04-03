"""
Rate limiting middleware and security utilities.
"""
from flask import request, jsonify
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib

# In-memory rate limit storage (use Redis in production)
rate_limit_storage = defaultdict(list)

class RateLimiter:
    """Simple rate limiter using sliding window."""
    
    @staticmethod
    def get_identifier():
        """Get unique identifier for the requester (IP-based)."""
        return request.remote_addr
    
    @staticmethod
    def is_rate_limited(key, max_requests, window_seconds):
        """Check if request should be rate limited."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Get requests for this key
        requests = rate_limit_storage[key]
        
        # Remove old requests
        rate_limit_storage[key] = [req_time for req_time in requests if req_time > window_start]
        
        # Check if limit exceeded
        if len(rate_limit_storage[key]) >= max_requests:
            return True
        
        # Add current request
        rate_limit_storage[key].append(now)
        return False

def rate_limit(max_requests=10, window_seconds=60):
    """Decorator for rate limiting endpoints."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            identifier = RateLimiter.get_identifier()
            key = f"{identifier}:{request.endpoint}"
            
            if RateLimiter.is_rate_limited(key, max_requests, window_seconds):
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per {window_seconds} seconds'
                }), 429
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def hash_password(password):
    """Hash a password using SHA256 (Werkzeug's method is better, this is backup)."""
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_filename(filename):
    """Sanitize filename to prevent directory traversal."""
    # Remove path components
    filename = filename.replace('/', '').replace('\\', '')
    # Remove hidden file prefix
    filename = filename.lstrip('.')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + (f'.{ext}' if ext else '')
    return filename

def validate_file_type(mimetype, allowed_types=None):
    """Validate file mimetype against allowed list."""
    if allowed_types is None:
        # Default: allow common file types
        allowed_types = [
            'image/', 'video/', 'audio/', 'application/pdf',
            'application/zip', 'application/x-rar', 'text/',
            'application/msword', 'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument'
        ]
    
    if not mimetype:
        return True  # Allow if no mimetype specified
    
    for allowed in allowed_types:
        if mimetype.startswith(allowed):
            return True
    
    return False

def get_client_ip():
    """Get real client IP (handles proxies)."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr
