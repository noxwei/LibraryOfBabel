#!/usr/bin/env python3
"""
🚀 REDIRECTING TO STANDARDIZED API
=================================

This API has been upgraded to the new standardized version.
All requests are now handled by standardized_production_api.py
"""

import subprocess
import sys
import os

print("🔄 Redirecting to new standardized API...")
os.execvp('python3', ['python3', 'src/api/standardized_production_api.py'])

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
from flask import Flask, jsonify
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

# Configure logging with container-aware path resolution
def get_log_path():
    """Get container-aware log file path"""
    log_dir = os.getenv('LOG_PATH', '/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'modular_api.log')

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

# Register blueprints (modular components)
app.register_blueprint(health_bp)
app.register_blueprint(books_bp)
app.register_blueprint(search_bp)
app.register_blueprint(shortcuts_bp)


def initialize_app():
    """Initialize application and test database connection with container awareness"""
    logger.info("🚀 Starting LibraryOfBabel Modular API")
    logger.info("🔧 Architecture: PostgreSQL-First with Modular Design")
    logger.info("👩‍💻 Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture")
    logger.info("🎨 Dr. Elena Rodriguez (IAV) - UX-Optimized Design")
    
    # Container environment detection
    if os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true':
        logger.info("🐳 Container environment detected")
        logger.info(f"📁 Log path: {os.getenv('LOG_PATH', '/app/logs')}")
        logger.info(f"🌐 CORS origins: {get_cors_origins()}")
    else:
        logger.info("💻 Local development environment")
    
    # Test database connection
    if test_connection():
        logger.info("✅ Database connection successful")
    else:
        logger.error("❌ Database connection failed")


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
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
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
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
    
    # Container-aware server configuration
    is_container = os.getenv('RUNNING_IN_CONTAINER', '').lower() == 'true'
    port = int(os.getenv('API_PORT', os.getenv('PORT', 5565 if is_container else 5564)))
    host = os.getenv('API_HOST', '0.0.0.0' if is_container else '127.0.0.1')
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configure test mode based on environment
    if not is_container:
        os.environ['TEST_MODE'] = 'true'
        logger.info("🧪 DEVELOPMENT MODE - Local testing only")
        logger.info("🔓 TEST MODE ENABLED - No API key required for localhost")
    else:
        logger.info("🐳 CONTAINER MODE - Production-ready configuration")
        logger.info("🔐 SECURITY ENABLED - API key validation active")
    
    logger.info(f"🌟 Starting modular API on {host}:{port}")
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 API server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        sys.exit(1)