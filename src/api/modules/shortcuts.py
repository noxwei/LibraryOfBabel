"""
iOS Shortcuts Module - PostgreSQL-First Architecture
Dr. Elena Rodriguez (IAV) UX Design + Dr. Sarah Chen (陈雪芳) PostgreSQL-First
"""

import logging
from flask import Blueprint, request, jsonify
from .auth import require_auth
from .database import execute_pg_function

logger = logging.getLogger(__name__)
shortcuts_bp = Blueprint('shortcuts', __name__)


@shortcuts_bp.route('/api/shortcuts/random/title')
@require_auth
def random_title():
    """Get random book title with ID - iOS Shortcuts optimized"""
    try:
        result = execute_pg_function('api_shortcuts_random_title')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Random title error: {e}")
        return jsonify({'error': 'Failed to get random title'}), 500


@shortcuts_bp.route('/api/shortcuts/random/author')
@require_auth
def random_author():
    """Get random author with book info - iOS Shortcuts optimized"""
    try:
        result = execute_pg_function('api_shortcuts_random_author')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Random author error: {e}")
        return jsonify({'error': 'Failed to get random author'}), 500


@shortcuts_bp.route('/api/shortcuts/random/citation')
@require_auth
def random_citation():
    """Get random book citation - iOS Shortcuts optimized"""
    try:
        result = execute_pg_function('api_shortcuts_random_citation')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Random citation error: {e}")
        return jsonify({'error': 'Failed to get random citation'}), 500


@shortcuts_bp.route('/api/shortcuts/random/share')
@require_auth
def random_share_text():
    """Get random shareable book text - iOS Shortcuts optimized"""
    try:
        result = execute_pg_function('api_shortcuts_random_share_text')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Random share text error: {e}")
        return jsonify({'error': 'Failed to get random share text'}), 500


@shortcuts_bp.route('/api/shortcuts/list/titles')
@require_auth
def list_titles():
    """List book titles - iOS Shortcuts optimized"""
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        page = max(int(request.args.get('page', 1)), 1)
        
        titles = execute_pg_function('api_shortcuts_list_titles', limit, page)
        return jsonify(titles)  # Return simple array for iOS Shortcuts
        
    except Exception as e:
        logger.error(f"List titles error: {e}")
        return jsonify({'error': 'Failed to list titles'}), 500


@shortcuts_bp.route('/api/shortcuts/list/authors')
@require_auth
def list_authors():
    """List authors - iOS Shortcuts optimized"""
    try:
        limit = min(int(request.args.get('limit', 100)), 500)
        page = max(int(request.args.get('page', 1)), 1)
        
        authors = execute_pg_function('api_shortcuts_list_authors', limit, page)
        return jsonify(authors)  # Return simple array for iOS Shortcuts
        
    except Exception as e:
        logger.error(f"List authors error: {e}")
        return jsonify({'error': 'Failed to list authors'}), 500


@shortcuts_bp.route('/api/shortcuts/stats/count')
@require_auth
def book_count():
    """Get total book count - iOS Shortcuts optimized"""
    try:
        count = execute_pg_function('api_shortcuts_book_count')
        return jsonify(count)  # Return simple integer for iOS Shortcuts
    except Exception as e:
        logger.error(f"Book count error: {e}")
        return jsonify({'error': 'Failed to get book count'}), 500


@shortcuts_bp.route('/api/shortcuts/stats/health')
@require_auth
def collection_health():
    """Get collection health metrics - iOS Shortcuts optimized"""
    try:
        health = execute_pg_function('api_shortcuts_collection_health')
        return jsonify(health)
    except Exception as e:
        logger.error(f"Collection health error: {e}")
        return jsonify({'error': 'Failed to get collection health'}), 500


@shortcuts_bp.route('/api/shortcuts/dashboard')
@require_auth
def dashboard():
    """Get dashboard statistics - iOS Shortcuts optimized"""
    try:
        include_gaps = request.args.get('include_gaps', 'false').lower() == 'true'
        dashboard_data = execute_pg_function('api_shortcuts_dashboard', include_gaps)
        return jsonify(dashboard_data)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return jsonify({'error': 'Failed to get dashboard data'}), 500


# Legacy V3 shortcuts endpoints for backwards compatibility
@shortcuts_bp.route('/api/v3/search')
@require_auth
def v3_search():
    """V3 Legacy search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('search_type', 'content')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query:
            return jsonify({
                'results': [],
                'pagination': {
                    'page': 1,
                    'page_size': limit,
                    'total_items': 0,
                    'total_pages': 0
                }
            })
            
        result = execute_pg_function('api_v3_search', query, search_type, limit)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"V3 search error: {e}")
        return jsonify({'error': 'Search failed'}), 500