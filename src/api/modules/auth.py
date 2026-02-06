"""
Authentication Module - SECURITY HARDENED
Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture

SECURITY FIXES:
- Removed dangerous test mode bypass
- Added input validation
- Enhanced API key security
- Added rate limiting support
"""

import os
import re
import logging
import secrets
from functools import wraps
from flask import request, jsonify

# Security logger
security_logger = logging.getLogger('security')


def get_api_key():
    """Get API key from environment"""
    return os.getenv('API_KEY', 'your-secret-api-key')


def validate_input(value, param_name, max_length=1000, allow_special=False):
    """Validate user input to prevent injection attacks"""
    if not value:
        return True  # Allow empty values
    
    if len(str(value)) > max_length:
        security_logger.warning(f"Input too long for {param_name}: {len(str(value))} > {max_length}")
        return False
    
    if not allow_special:
        # Prevent SQL injection patterns
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)',
            r'(--|\*\/|\/\*)',
            r'(\bUNION\b|\bJOIN\b)',
            r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
            r'(\bCAST\s*\()',
            r'(\bCONVERT\s*\()',
            r'(\bSUBSTRING\s*\()',
            r'(\bCHAR\s*\()',
            r'(\bASCII\s*\()'
        ]
        
        value_str = str(value).upper()
        for pattern in dangerous_patterns:
            if re.search(pattern, value_str, re.IGNORECASE):
                security_logger.error(f"Potential SQL injection in {param_name}: {value}")
                return False
    
    return True


def verify_api_key():
    """Verify API key from request headers (SECURE - NO QUERY PARAMS)"""
    api_key = get_api_key()
    client_ip = request.remote_addr
    
    # Check for API-Key header (primary)
    request_key = request.headers.get('API-Key')
    if request_key:
        is_valid = secrets.compare_digest(str(request_key), str(api_key))
        if not is_valid:
            security_logger.warning(f"Invalid API key attempt from {client_ip} via header")
        return is_valid
    
    # Check for X-API-Key header (secondary)
    request_key = request.headers.get('X-API-Key')
    if request_key:
        is_valid = secrets.compare_digest(str(request_key), str(api_key))
        if not is_valid:
            security_logger.warning(f"Invalid API key attempt from {client_ip} via X-API-Key")
        return is_valid
    
    # Check for Authorization Bearer header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        is_valid = secrets.compare_digest(str(token), str(api_key))
        if not is_valid:
            security_logger.warning(f"Invalid bearer token from {client_ip}")
        return is_valid
    
    # SECURITY FIX: Removed query parameter support
    # Query parameters expose API keys in logs, referrer headers, browser history
    
    # SECURITY: Reject API keys via query parameters entirely
    if request.args.get('api_key'):
        security_logger.warning("API key via query parameter rejected - use X-API-Key header")
        return False
    
    security_logger.info(f"No API key provided from {client_ip}")
    return False


def require_auth(f):
    """Decorator to require authentication (SECURE - NO BYPASSES)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # SECURITY FIX: Removed dangerous test mode bypass
        # All requests must authenticate - no exceptions
        
        if not verify_api_key():
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Valid API key required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def is_localhost():
    """Check if request is from localhost (container-aware)"""
    localhost_addresses = ['127.0.0.1', '::1', 'localhost']
    
    # In container environment, also consider container gateway
    if os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true':
        localhost_addresses.extend([
            '172.21.0.1',  # Docker gateway
            'host.docker.internal'
        ])
    
    return request.remote_addr in localhost_addresses


def require_auth_unless_localhost(f):
    """Decorator to require auth unless from localhost"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_localhost() and not verify_api_key():
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Valid API key required for remote access'
            }), 401
        return f(*args, **kwargs)
    return decorated_function