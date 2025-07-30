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

# Create Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Enable CORS for frontend integration
CORS(app, origins=["http://localhost:3000", "https://api.ashortstayinhell.com"])

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
    
    # Development server settings
    port = int(os.getenv('PORT', 5564))  # Different port to avoid conflicts
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Enable test mode for local development
    os.environ['TEST_MODE'] = 'true'
    
    logger.info(f"🌟 Starting modular API on port {port}")
    logger.info("🧪 DEVELOPMENT MODE - Local testing only")
    logger.info("🔓 TEST MODE ENABLED - No API key required for localhost")
    
    try:
        app.run(
            host='127.0.0.1',
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 API server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start API server: {e}")
        sys.exit(1)