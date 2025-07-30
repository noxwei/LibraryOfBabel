#!/usr/bin/env python3
"""
LibraryOfBabel Modular Production API
====================================

Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
Dr. Elena Rodriguez (IAV) UX-Optimized Design

Modular, maintainable, PostgreSQL-First API with zero hardcoded SQL.
All business logic implemented as PostgreSQL functions.

Key Features:
- Modular architecture (separate modules for auth, books, search, etc.)
- PostgreSQL-First design (zero hardcoded SQL in application code)
- Extended semantic search (10-word compound queries)
- iOS Shortcuts optimization
- Proper limit parameter handling
- Authentication middleware
- Comprehensive error handling
"""

import os
import sys
import logging
import ssl
import time
import json
from collections import defaultdict, deque
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modular components
from modules.database import test_connection
from modules.health import health_bp
from modules.auth import require_auth
from modules.books import books_bp
from modules.search import search_bp
from modules.shortcuts import shortcuts_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/modular_api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Security logger for monitoring
security_logger = logging.getLogger('security')
security_handler = logging.FileHandler('/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/security.log')
security_handler.setFormatter(logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s'))
security_logger.addHandler(security_handler)

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Override Flask's JSON encoder to always pretty-print
class PrettyJSONEncoder(json.JSONEncoder):
    def encode(self, obj):
        return json.dumps(obj, indent=2, ensure_ascii=False, separators=(',', ': '))

app.json_encoder = PrettyJSONEncoder

# Monkey patch Flask's jsonify to always use pretty printing
original_jsonify = jsonify

def pretty_jsonify(*args, **kwargs):
    """Pretty-print JSON responses"""
    response = original_jsonify(*args, **kwargs)
    # Re-encode with pretty formatting
    data = response.get_json()
    response.data = json.dumps(data, indent=2, ensure_ascii=False, separators=(',', ': '))
    return response

# Replace Flask's jsonify globally
import flask
flask.jsonify = pretty_jsonify

# Custom JSON formatter for pretty output
def pretty_json_response(data, status_code=200):
    """Return pretty-formatted JSON response"""
    json_str = json.dumps(data, indent=2, ensure_ascii=False, separators=(',', ': '))
    response = Response(
        json_str,
        mimetype='application/json',
        status=status_code
    )
    return response

# Enable CORS for frontend integration (HTTPS ONLY)
CORS(app, origins=["https://localhost:3000", "https://api.ashortstayinhell.com"])

# Simple in-memory rate limiting with IP blocking
class SimpleRateLimiter:
    def __init__(self):
        self.requests = defaultdict(lambda: {'minute': deque(), 'hour': deque()})
        # Block suspicious IPs (add IPs here that are attacking)
        self.blocked_ips = set([
            # Add attacking IPs here, e.g.:
            # '192.168.1.100',
            # '10.0.0.50'
        ])
        # Block entire country ranges if needed (example)
        self.blocked_ip_ranges = [
            # Add CIDR blocks here if needed, e.g.:
            # '192.168.1.0/24'
        ]
    
    def is_blocked(self, client_ip):
        """Check if IP is blocked"""
        return client_ip in self.blocked_ips
    
    def is_allowed(self, client_ip, requests_per_minute=50, requests_per_hour=200):
        now = time.time()
        
        # Check if IP is blocked
        if self.is_blocked(client_ip):
            return False, 'blocked', 'IP_BLOCKED'
        
        client_data = self.requests[client_ip]
        
        # Clean old requests (older than 1 hour)
        while client_data['hour'] and now - client_data['hour'][0] > 3600:
            client_data['hour'].popleft()
        
        # Clean old requests (older than 1 minute)  
        while client_data['minute'] and now - client_data['minute'][0] > 60:
            client_data['minute'].popleft()
        
        # Check limits
        if len(client_data['minute']) >= requests_per_minute:
            return False, 'minute', requests_per_minute
        if len(client_data['hour']) >= requests_per_hour:
            return False, 'hour', requests_per_hour
            
        # Add current request
        client_data['minute'].append(now)
        client_data['hour'].append(now)
        
        return True, None, None

# Initialize rate limiter
rate_limiter = SimpleRateLimiter()

# Register blueprints (modular components)
app.register_blueprint(health_bp)
app.register_blueprint(books_bp)
app.register_blueprint(search_bp)
app.register_blueprint(shortcuts_bp)


def initialize_app():
    """Initialize application and test database connection"""
    logger.info("🚀 Starting LibraryOfBabel Modular API")
    logger.info("🔧 Architecture: PostgreSQL-First with Modular Design")
    logger.info("👩‍💻 Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture")
    logger.info("🎨 Dr. Elena Rodriguez (IAV) - UX-Optimized Design")
    logger.info("🛡️ Security: Rate limiting and headers enabled")
    
    # Test database connection
    if test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")


@app.after_request
def add_security_headers(response):
    """Add comprehensive security headers to all responses"""
    # Prevent XSS attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Force HTTPS and prevent protocol downgrade attacks
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Content Security Policy - restrict resource loading
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
    
    # Prevent referrer information leakage
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Feature policy restrictions
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), speaker=()'
    
    # Additional security headers
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
    
    return response


@app.before_request
def security_and_rate_limit_check():
    """Check HTTPS, rate limits and log security-relevant information"""
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', 'Unknown')
    endpoint = request.endpoint or request.path
    method = request.method
    
    # Enforce HTTPS only
    if not request.is_secure:
        security_logger.warning(f"HTTP request blocked from {client_ip}: {method} {request.full_path}")
        return pretty_json_response({
            'success': False,
            'error': 'HTTPS Required',
            'message': 'This API only accepts HTTPS connections for security',
            'redirect_url': f'https://api.ashortstayinhell.com:5562{request.full_path}'
        }, 426)  # 426 Upgrade Required
    
    # Skip rate limiting for health checks
    if endpoint != 'health.health':
        # Check rate limits
        allowed, limit_type, limit_value = rate_limiter.is_allowed(client_ip)
        if not allowed:
            security_logger.warning(f"Rate limit exceeded from {client_ip}: {limit_value}/{limit_type}")
            return pretty_json_response({
                'success': False,
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Limit: {limit_value} per {limit_type}',
                'retry_after': 60 if limit_type == 'minute' else 3600
                # SECURITY: Removed client_ip to prevent information disclosure
            }, 429)
    
    # Log suspicious patterns
    if any(suspicious in request.full_path.lower() for suspicious in ['union', 'select', 'drop', 'insert', '--', '/*']):
        security_logger.warning(f"Suspicious request from {client_ip}: {method} {request.full_path}")
    
    # Log high-frequency endpoints for monitoring  
    if endpoint in ['health', 'search.v4_search', 'shortcuts.shortcuts_search']:
        security_logger.info(f"High-freq endpoint: {client_ip} -> {method} {endpoint}")


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    client_ip = request.remote_addr
    security_logger.info(f"404 error from {client_ip}: {request.path}")
    
    return pretty_json_response({
        'success': False,
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'available_endpoints': {
            'health': '/health',
            'books': '/api/v4/books',
            'search': '/api/v4/search',
            'semantic_search': '/api/v4/search/semantic',
            'shortcuts': '/api/shortcuts/*'
        }
    }, 404)


@app.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit exceeded errors"""
    client_ip = request.remote_addr
    security_logger.warning(f"Rate limit exceeded from {client_ip}: {error.description}")
    
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please slow down.',
        'retry_after': getattr(error, 'retry_after', 60),
        'limits': {
            'default': '200 per hour, 50 per minute',
            'search': '30 per minute',
            'books': '100 per hour'
        }
    }), 429


@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    client_ip = request.remote_addr
    security_logger.warning(f"Bad request from {client_ip}: {error}")
    
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': 'Invalid request parameters or format'
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access errors"""
    client_ip = request.remote_addr
    security_logger.warning(f"Unauthorized access attempt from {client_ip}")
    
    return jsonify({
        'success': False,
        'error': 'Authentication required',
        'message': 'Valid API key required in headers',
        'auth_methods': [
            'Header: API-Key: your-key-here',
            'Header: X-API-Key: your-key-here', 
            'Header: Authorization: Bearer your-key-here'
        ]
    }), 401


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    client_ip = request.remote_addr
    logger.error(f"Internal server error from {client_ip}: {error}")
    security_logger.error(f"Server error from {client_ip}: {str(error)[:200]}")
    
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


@app.route('/')
def root():
    """Root endpoint with API information"""
    return jsonify({
        'name': 'LibraryOfBabel Modular API',
        'version': '4.0-modular-postgresql-first',
        'architecture': 'PostgreSQL-First with Modular Design',
        'designers': [
            'Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture',
            'Dr. Elena Rodriguez (IAV) - UX-Optimized Design'
        ],
        'features': [
            'Modular architecture for maintainability',
            'PostgreSQL-First design (zero hardcoded SQL)',
            'Extended semantic search (10-word capability)',
            'iOS Shortcuts optimization',
            'Proper limit parameter handling',
            'Authentication middleware',
            'Rate limiting protection (200/hour, 50/minute)',
            'Comprehensive security headers',
            'SQL injection protection',
            'Security logging and monitoring',
            'SSL/HTTPS encryption support',
            'Comprehensive error handling'
        ],
        'endpoints': {
            'health': '/health',
            'books': '/api/v4/books?action=list&limit=10',
            'search': '/api/v4/search?q=philosophy',
            'semantic_search': '/api/v4/search/semantic?q=artificial intelligence machine learning',
            'shortcuts_random': '/api/shortcuts/random/title',
            'shortcuts_search': '/api/shortcuts/search?term=democracy'
        },
        'documentation': 'https://github.com/your-repo/api-docs'
    })


@app.route('/api/v4/info')
def api_info():
    """API information endpoint"""
    return jsonify({
        'api_name': 'LibraryOfBabel Modular API',
        'version': '4.0-modular-postgresql-first',
        'architecture': 'PostgreSQL-First with Modular Design',
        'principles': [
            'Zero hardcoded SQL in application code',
            'All business logic in PostgreSQL functions',
            'Modular design for maintainability',
            'iOS Shortcuts optimization',
            'Proper parameter handling'
        ],
        'modules': [
            'auth - Authentication and authorization',
            'database - PostgreSQL connection management',
            'books - Book-related endpoints',
            'search - Search functionality',
            'health - Health check endpoints',
            'shortcuts - iOS Shortcuts optimization'
        ],
        'database_functions': [
            'api_shortcuts_book_summary',
            'api_shortcuts_search_simple',
            'api_extended_semantic_search',
            'api_semantic_phrase_search_optimized',
            'api_shortcuts_collection_health'
        ]
    })


if __name__ == '__main__':
    # Initialize app before starting
    initialize_app()
    
    # Production server settings
    port = int(os.getenv('PORT', 5562))  # Production port
    debug = False  # Disable debug in production
    
    # SSL Configuration
    ssl_enabled = os.getenv('SSL_ENABLED', 'true').lower() == 'true'
    ssl_cert_path = '/Users/weixiangzhang/Local_Dev/LibraryOfBabel/ssl/letsencrypt-config/live/api.ashortstayinhell.com/fullchain.pem'
    ssl_key_path = '/Users/weixiangzhang/Local_Dev/LibraryOfBabel/ssl/letsencrypt-config/live/api.ashortstayinhell.com/privkey.pem'
    
    # Disable test mode for production
    # os.environ['TEST_MODE'] = 'true'  # Disabled for production
    
    logger.info(f"🌟 Starting modular API on port {port}")
    logger.info("🚀 PRODUCTION MODE - Public API server")
    logger.info("🔐 AUTHENTICATION REQUIRED - API key validation enabled")
    
    if ssl_enabled and os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        logger.info("🔒 SSL ENABLED - HTTPS support active")
        logger.info(f"📜 Certificate: {ssl_cert_path}")
        
        # Create SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(ssl_cert_path, ssl_key_path)
        
        try:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=debug,
                threaded=True,
                ssl_context=context
            )
        except KeyboardInterrupt:
            logger.info("🛑 API server stopped by user")
        except Exception as e:
            logger.error(f"❌ Failed to start HTTPS API server: {e}")
            sys.exit(1)
    else:
        logger.info("🔓 HTTP MODE - SSL disabled or certificates not found")
        if ssl_enabled:
            logger.warning(f"⚠️ SSL requested but certificates not found at {ssl_cert_path}")
        
        try:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=debug,
                threaded=True
            )
        except KeyboardInterrupt:
            logger.info("🛑 API server stopped by user")
        except Exception as e:
            logger.error(f"❌ Failed to start HTTP API server: {e}")
            sys.exit(1)