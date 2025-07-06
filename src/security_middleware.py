#!/usr/bin/env python3
"""
🔐 LibraryOfBabel Security Middleware
HTTPS + API Key Authentication for secure external access
"""

import os
import hashlib
import secrets
import time
from functools import wraps
from flask import request, jsonify, g
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, api_key: str = None):
        # Use provided API key or load from environment/file
        self.api_key = api_key or self._load_api_key()
        self.api_key_hash = hashlib.sha256(self.api_key.encode()).hexdigest()
        
        # Rate limiting (simple in-memory store)
        self.rate_limits = {}
        self.max_requests_per_minute = 60
        
        logger.info(f"🔐 Security Manager initialized")
        logger.info(f"🔑 API Key (last 8 chars): ...{self.api_key[-8:]}")
    
    def _load_api_key(self):
        """Load API key from environment variables (secure method)"""
        # Try environment variable first (SECURE METHOD)
        api_key = os.getenv('API_KEY') or os.getenv('LIBRARY_API_KEY')
        if api_key:
            return api_key
        
        # DEPRECATED: Try to load from api_key.txt file for backwards compatibility
        # This is being phased out for security reasons
        api_key_file = os.path.join(os.path.dirname(__file__), '..', 'api_key.txt')
        if os.path.exists(api_key_file):
            logger.warning("🚨 SECURITY WARNING: Using deprecated api_key.txt file. Please set API_KEY environment variable instead.")
            with open(api_key_file, 'r') as f:
                return f.read().strip()
        
        # Generate new key if none exists
        new_key = secrets.token_urlsafe(32)
        logger.warning(f"🔑 Generated new API key - save this to your .env file: API_KEY={new_key}")
        logger.warning("🔐 IMPORTANT: Set this as an environment variable instead of using api_key.txt")
        
        return new_key
    
    def require_api_key(self, f):
        """Decorator to require API key authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from various sources
            api_key = None
            
            # 1. Check Authorization header (Bearer token)
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # 2. Check X-API-Key header
            elif 'X-API-Key' in request.headers:
                api_key = request.headers.get('X-API-Key')
            
            # 3. Check query parameter (for Shortcuts app compatibility)
            elif 'api_key' in request.args:
                api_key = request.args.get('api_key')
            
            # 4. Check JSON body
            elif request.is_json and request.json and 'api_key' in request.json:
                api_key = request.json.get('api_key')
            
            # Validate API key
            if not api_key:
                logger.warning(f"🚫 Missing API key from {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': 'API key required',
                    'message': 'Provide API key via Authorization header, X-API-Key header, or api_key parameter'
                }), 401
            
            if not self._verify_api_key(api_key):
                logger.warning(f"🚫 Invalid API key from {request.remote_addr}: {api_key[:8]}...")
                return jsonify({
                    'success': False,
                    'error': 'Invalid API key'
                }), 403
            
            # Rate limiting
            if not self._check_rate_limit(request.remote_addr):
                logger.warning(f"🚫 Rate limit exceeded for {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'message': f'Max {self.max_requests_per_minute} requests per minute'
                }), 429
            
            # Store authenticated state
            g.authenticated = True
            g.api_key_valid = True
            
            logger.info(f"✅ Authenticated request from {request.remote_addr} to {request.endpoint}")
            return f(*args, **kwargs)
        
        return decorated_function
    
    def _verify_api_key(self, provided_key: str) -> bool:
        """Verify API key using constant-time comparison"""
        try:
            provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
            return secrets.compare_digest(self.api_key_hash, provided_hash)
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return False
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Simple rate limiting by IP address"""
        current_time = time.time()
        minute_key = int(current_time // 60)  # Current minute
        
        # Clean old entries (keep last 2 minutes)
        self.rate_limits = {
            key: count for key, count in self.rate_limits.items() 
            if key[1] >= minute_key - 1
        }
        
        # Count requests in current minute
        rate_key = (client_ip, minute_key)
        current_count = self.rate_limits.get(rate_key, 0)
        
        if current_count >= self.max_requests_per_minute:
            return False
        
        # Increment counter
        self.rate_limits[rate_key] = current_count + 1
        return True
    
    def log_request(self, f):
        """Decorator to log all requests for security monitoring"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Log request details
            logger.info(f"📝 {request.method} {request.path} from {request.remote_addr}")
            logger.info(f"   User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
            logger.info(f"   Authenticated: {getattr(g, 'authenticated', False)}")
            
            # Execute request
            result = f(*args, **kwargs)
            
            # Log response time
            duration = round((time.time() - start_time) * 1000, 2)
            logger.info(f"   Response time: {duration}ms")
            
            return result
        
        return decorated_function
    
    def get_ssl_context(self):
        """Get SSL context for HTTPS"""
        ssl_dir = os.path.join(os.path.dirname(__file__), '..', 'ssl')
        
        # Try Let's Encrypt certificate first (browser-trusted)
        letsencrypt_cert = os.path.join(ssl_dir, 'letsencrypt-config/live/api.ashortstayinhell.com/fullchain.pem')
        letsencrypt_key = os.path.join(ssl_dir, 'letsencrypt-config/live/api.ashortstayinhell.com/privkey.pem')
        
        if os.path.exists(letsencrypt_cert) and os.path.exists(letsencrypt_key):
            logger.info("🔒 Using Let's Encrypt certificate for api.ashortstayinhell.com")
            return (letsencrypt_cert, letsencrypt_key)
        
        # Try fresh iOS-compatible certificate (fallback)
        fresh_cert_file = os.path.join(ssl_dir, 'fresh-server-cert.pem')
        fresh_key_file = os.path.join(ssl_dir, 'fresh-server-key.pem')
        
        if os.path.exists(fresh_cert_file) and os.path.exists(fresh_key_file):
            logger.info("🆕 Using fresh iOS-compatible certificate with proper SAN")
            return (fresh_cert_file, fresh_key_file)
        
        # Try iOS-friendly certificate (previous generation)
        ios_cert_file = os.path.join(ssl_dir, 'ios-server-cert.pem')
        ios_key_file = os.path.join(ssl_dir, 'ios-server-key.pem')
        
        if os.path.exists(ios_cert_file) and os.path.exists(ios_key_file):
            logger.info("📱 Using iOS-friendly certificate for external access")
            return (ios_cert_file, ios_key_file)
        
        # Try CA-signed certificate (best for browsers)
        ca_cert_file = os.path.join(ssl_dir, 'server-cert.pem')
        ca_key_file = os.path.join(ssl_dir, 'server-key.pem')
        
        if os.path.exists(ca_cert_file) and os.path.exists(ca_key_file):
            logger.info("🔒 Using CA-signed certificate for maximum browser compatibility")
            return (ca_cert_file, ca_key_file)
        
        # Fallback to self-signed certificate
        cert_file = os.path.join(ssl_dir, 'cert.pem')
        key_file = os.path.join(ssl_dir, 'key.pem')
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            logger.info("🔒 Using self-signed certificate")
            return (cert_file, key_file)
        else:
            logger.error("SSL certificate files not found!")
            return None
    
    def get_ca_certificate_path(self):
        """Get path to CA certificate for browser installation"""
        ssl_dir = os.path.join(os.path.dirname(__file__), '..', 'ssl')
        
        # Try fresh CA certificate first
        fresh_ca_cert = os.path.join(ssl_dir, 'fresh-ca-cert.pem')
        if os.path.exists(fresh_ca_cert):
            return fresh_ca_cert
        
        # Fallback to original CA certificate
        ca_cert_file = os.path.join(ssl_dir, 'ca-cert.pem')
        if os.path.exists(ca_cert_file):
            return ca_cert_file
        return None

def create_public_endpoint(f):
    """Decorator for public endpoints that don't require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.authenticated = False
        g.public_endpoint = True
        return f(*args, **kwargs)
    
    return decorated_function

# Global security manager instance
security_manager = SecurityManager()

# Export decorators for easy use
require_api_key = security_manager.require_api_key
log_request = security_manager.log_request
get_ssl_context = security_manager.get_ssl_context

# API Key Management Functions
def generate_new_api_key() -> str:
    """Generate a new secure API key"""
    return secrets.token_urlsafe(32)

def rotate_api_key() -> str:
    """Rotate to a new API key"""
    new_key = generate_new_api_key()
    logger.info(f"🔄 API key rotated. New key: ...{new_key[-8:]}")
    return new_key

if __name__ == "__main__":
    # Test security functions
    print("🔐 LibraryOfBabel Security Test")
    print(f"✅ API Key: {security_manager.api_key}")
    print(f"🔑 API Key Hash: {security_manager.api_key_hash[:16]}...")
    print(f"📁 SSL Context: {get_ssl_context()}")
    
    # Test key verification
    test_key = security_manager.api_key
    print(f"🧪 Key verification test: {security_manager._verify_api_key(test_key)}")
    print(f"🧪 Wrong key test: {security_manager._verify_api_key('wrong_key')}")