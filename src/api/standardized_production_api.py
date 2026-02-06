#!/usr/bin/env python3
"""
LibraryOfBabel Standardized Production API
==========================================

Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
Dr. Elena Rodriguez (IAV) UX-Optimized Design

PRODUCTION-READY STANDARDIZED API v4.1
- 12 endpoints (down from 25)
- Zero parameter inconsistencies
- Zero version pollution
- PostgreSQL-First ONLY
- REST-compliant hierarchy
- CI/CD Pipeline Integration
"""

import os
import sys
import logging
from flask import Flask, jsonify, send_from_directory

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import standardized modules
from modules.database import test_connection
from modules.standardized_health import standardized_health_bp
from modules.standardized_books import standardized_books_bp
from modules.standardized_search import standardized_search_bp
from modules.standardized_mobile import standardized_mobile_bp
from modules.standardized_upload import standardized_upload_bp

# Configure container-aware logging
def get_log_path():
    """Get container-aware log file path"""
    if os.getenv('RUNNING_IN_CONTAINER') == 'true':
        log_dir = '/app/logs'
    else:
        log_dir = os.getenv('LOG_PATH', './logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'standardized_api.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_path()),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Static frontend directory (Next.js static export)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'frontend', 'out')
FRONTEND_DIR = os.path.normpath(FRONTEND_DIR)

# Create Flask app (static files served via custom routes, not Flask static_folder)
app = Flask(__name__, static_folder=None)
app.config['JSON_SORT_KEYS'] = False

# Container-aware CORS configuration
from flask_cors import CORS

def get_cors_origins():
    """Get CORS origins from environment with container defaults"""
    env_origins = os.getenv('CORS_ORIGINS', '')
    if env_origins:
        return env_origins.split(',')
    
    # Default origins for different environments
    default_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://api.ashortstayinhell.com",
        "https://api.ashortstayinhell.com:5562",
    ]
    
    # Add container-specific origins if running in container
    if os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true':
        container_origins = [
            "http://localhost:5565",
            "http://127.0.0.1:5565", 
            "http://host.docker.internal:5565"
        ]
        default_origins.extend(container_origins)
    
    return default_origins

# Enable CORS for frontend integration
CORS(app, origins=get_cors_origins())

# Security headers for all responses (no CSP to avoid breaking frontend)
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Register standardized blueprints (CLEAN HIERARCHY)
app.register_blueprint(standardized_health_bp)    # Level 4: Utilities
app.register_blueprint(standardized_books_bp)     # Level 1: Core Resources
app.register_blueprint(standardized_search_bp)    # Level 1: Core Resources
app.register_blueprint(standardized_mobile_bp)    # Level 3: Mobile Optimized
app.register_blueprint(standardized_upload_bp)    # Level 2: Upload & Processing

def initialize_app():
    """Initialize application and test database connection"""
    logger.info("🚀 Starting LibraryOfBabel Standardized Production API")
    logger.info("📐 Architecture: PostgreSQL-First with REST Standardization")
    logger.info("🔥 ZERO inconsistencies, ZERO version pollution")
    
    # Container environment detection
    if os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true':
        logger.info("🐳 Container environment detected")
        logger.info(f"📁 Log path: {os.getenv('LOG_PATH', '/app/logs')}")
    else:
        logger.info("💻 Local development environment")
    
    # Test database connection
    if test_connection():
        logger.info("✅ PostgreSQL connection successful")
    else:
        logger.error("❌ PostgreSQL connection failed")

@app.errorhandler(404)
def not_found(error):
    """Handle 404 - serve frontend 404 page or API error"""
    from flask import request
    if request.path.startswith('/api/') or request.path == '/health':
        return jsonify({
            'success': False,
            'error': {
                'code': 'ENDPOINT_NOT_FOUND',
                'message': 'The requested API endpoint does not exist'
            }
        }), 404
    # For non-API routes, serve frontend 404
    fallback_path = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(fallback_path):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with clean response"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred'
        }
    }), 500

@app.route('/')
def root():
    """Serve frontend landing page"""
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    # Fallback to API info if no frontend build
    return jsonify({
        'api_name': 'LibraryOfBabel Production API',
        'status': 'operational',
        'frontend': 'not built - run npm run build in frontend/'
    })

@app.route('/<path:path>')
def serve_frontend(path):
    """Serve static frontend files for Next.js static export"""
    # Don't intercept API or health routes (let Flask blueprints handle them)
    if path.startswith('api/') or path == 'health':
        return jsonify({'error': 'Not found'}), 404

    # Strip trailing slash for consistent lookup
    clean_path = path.rstrip('/')

    # Try path/index.html for Next.js static export routes (e.g., demo/ -> demo/index.html)
    index_path = os.path.join(FRONTEND_DIR, clean_path, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(os.path.join(FRONTEND_DIR, clean_path), 'index.html')

    # Try exact file (e.g., _next/static/*, images, etc.)
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)

    # Fallback to 404.html
    fallback_path = os.path.join(FRONTEND_DIR, '404.html')
    if os.path.exists(fallback_path):
        return send_from_directory(FRONTEND_DIR, '404.html'), 404
    return jsonify({'error': 'Not found'}), 404

# Legacy endpoint redirect helpers
@app.route('/api/v4/<path:path>')
def legacy_v4_redirect(path):
    """Redirect legacy v4 endpoints to standardized equivalents"""
    logger.warning(f"Legacy v4 endpoint accessed: /api/v4/{path}")
    
    redirect_map = {
        'books': '/api/books',
        'search': '/api/search',
        'health': '/api/health',
        'info': '/api/info'
    }
    
    base_path = path.split('?')[0].split('/')[0]
    new_endpoint = redirect_map.get(base_path)
    
    if new_endpoint:
        return jsonify({
            'success': False,
            'error': {
                'code': 'DEPRECATED_ENDPOINT',
                'message': f'Legacy endpoint /api/v4/{path} is deprecated'
            },
            'migration': {
                'new_endpoint': new_endpoint,
                'note': 'Please update to use standardized endpoints'
            }
        }), 410  # 410 Gone
    else:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ENDPOINT_NOT_FOUND',
                'message': f'Legacy endpoint /api/v4/{path} not found'
            }
        }), 404

@app.route('/api/shortcuts/<path:path>')
def legacy_shortcuts_redirect(path):
    """Redirect legacy shortcuts endpoints to mobile equivalents"""
    logger.warning(f"Legacy shortcuts endpoint accessed: /api/shortcuts/{path}")
    
    redirect_map = {
        'random': '/api/mobile/random',
        'search': '/api/mobile/search',
        'books': '/api/mobile/books',
        'stats': '/api/mobile/stats',
        'dashboard': '/api/mobile/dashboard',
        'list': '/api/mobile/lists'
    }
    
    base_path = path.split('?')[0].split('/')[0]
    new_endpoint = redirect_map.get(base_path)
    
    if new_endpoint:
        return jsonify({
            'success': False,
            'error': {
                'code': 'DEPRECATED_ENDPOINT',
                'message': f'Legacy endpoint /api/shortcuts/{path} is deprecated'
            },
            'migration': {
                'new_endpoint': new_endpoint,
                'note': 'Please update to use /api/mobile/* endpoints'
            }
        }), 410  # 410 Gone
    else:
        return jsonify({
            'success': False,
            'error': {
                'code': 'ENDPOINT_NOT_FOUND',
                'message': f'Legacy endpoint /api/shortcuts/{path} not found'
            }
        }), 404

if __name__ == '__main__':
    # Initialize app before starting
    initialize_app()
    
    # Container-aware server configuration
    is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
    port = int(os.getenv('API_PORT', os.getenv('PORT', 5565 if is_container else 5564)))
    host = os.getenv('API_HOST', '0.0.0.0' if is_container else '127.0.0.1')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configure test mode based on environment
    if not is_container:
        os.environ['TEST_MODE'] = 'true'
        logger.info("🧪 DEVELOPMENT MODE - Local testing only")
        logger.info("🔓 TEST MODE ENABLED - Simplified auth for localhost")
    else:
        logger.info("🐳 CONTAINER MODE - Production-ready configuration")
        logger.info("🔐 SECURITY ENABLED - Full API key validation active")
    
    logger.info(f"🌟 Starting standardized API on {host}:{port}")
    logger.info("📊 API SUMMARY:")
    logger.info("   📚 /api/books - All book operations (7 actions)")
    logger.info("   🔍 /api/search - All search functionality (10 actions)")
    logger.info("   📱 /api/mobile/* - iOS Shortcuts optimized (6 endpoints)")
    logger.info("   ❤️ /health, /api/info, /api/health - System utilities (3 endpoints)")
    logger.info("   🎯 TOTAL: 12 clean endpoints (down from 25)")
    
    # SSL configuration for staging/production
    ssl_cert = os.getenv('SSL_CERT_PATH')
    ssl_key = os.getenv('SSL_KEY_PATH')
    
    if ssl_cert and ssl_key and os.path.exists(ssl_cert) and os.path.exists(ssl_key):
        logger.info(f"🔒 SSL enabled with certificates: {ssl_cert}")
        ssl_context = (ssl_cert, ssl_key)
    else:
        logger.info("🔓 SSL not configured - running HTTP only")
        ssl_context = None
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            ssl_context=ssl_context
        )
    except KeyboardInterrupt:
        logger.info("🛑 Standardized API server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start standardized API server: {e}")
        sys.exit(1)