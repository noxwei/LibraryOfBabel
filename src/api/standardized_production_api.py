#!/usr/bin/env python3
"""
LibraryOfBabel Standardized Production API
==========================================

Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
Dr. Elena Rodriguez (IAV) UX-Optimized Design

PRODUCTION-READY STANDARDIZED API
- 12 endpoints (down from 25)
- Zero parameter inconsistencies
- Zero version pollution
- PostgreSQL-First ONLY
- REST-compliant hierarchy
"""

import os
import sys
import logging
from flask import Flask, jsonify

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import standardized modules
from modules.database import test_connection
from modules.standardized_health import standardized_health_bp
from modules.standardized_books import standardized_books_bp
from modules.standardized_search import standardized_search_bp
from modules.standardized_mobile import standardized_mobile_bp

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

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Container-aware CORS configuration
from flask_cors import CORS

def get_cors_origins():
    """Get CORS origins from environment with container defaults"""
    env_origins = os.getenv('CORS_ORIGINS', '')
    if env_origins:
        return env_origins.split(',')
    
    # Default origins for different environments
    default_origins = ["http://localhost:3000", "https://api.ashortstayinhell.com"]
    
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

# Register standardized blueprints (CLEAN HIERARCHY)
app.register_blueprint(standardized_health_bp)    # Level 4: Utilities
app.register_blueprint(standardized_books_bp)     # Level 1: Core Resources
app.register_blueprint(standardized_search_bp)    # Level 1: Core Resources  
app.register_blueprint(standardized_mobile_bp)    # Level 3: Mobile Optimized

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
    """Handle 404 errors with clean response"""
    return jsonify({
        'success': False,
        'error': {
            'code': 'ENDPOINT_NOT_FOUND',
            'message': 'The requested API endpoint does not exist'
        },
        'available_endpoints': {
            'core_resources': [
                '/api/books - Book management and navigation',
                '/api/search - All search functionality'
            ],
            'mobile_optimized': [
                '/api/mobile/random - Random content for iOS',
                '/api/mobile/search - Mobile search',
                '/api/mobile/books - Mobile books',
                '/api/mobile/stats - Mobile statistics',
                '/api/mobile/lists - Mobile lists',
                '/api/mobile/dashboard - Mobile dashboard'
            ],
            'utilities': [
                '/health - Public health check',
                '/api/info - System information',
                '/api/health - Detailed health check'
            ]
        }
    }), 404

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
    """
    Root endpoint - CLEAN response with no version pollution
    Only essential information, no designer metadata
    """
    return jsonify({
        'api_name': 'LibraryOfBabel Production API',
        'status': 'operational',
        'architecture': 'PostgreSQL-First with REST Standardization',
        'endpoints': {
            'books': '/api/books?action=list',
            'search': '/api/search?q=your_query',
            'mobile_random': '/api/mobile/random?type=title',
            'mobile_search': '/api/mobile/search?q=your_query',
            'health': '/health',
            'system_info': '/api/info'
        },
        'features': [
            'Standardized parameter naming',
            'Unified response schema',
            'PostgreSQL-First architecture',
            'Mobile-optimized endpoints',
            'Zero version pollution'
        ]
    })

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
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Standardized API server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start standardized API server: {e}")
        sys.exit(1)