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


# iOS Shortcuts Search - STANDARDIZED PARAMETERS
@shortcuts_bp.route('/api/shortcuts/search')
@require_auth
def shortcuts_search():
    """iOS Shortcuts search with standardized parameters (q= and term= both supported)"""
    try:
        # Support both q= (standard) and term= (legacy) for backwards compatibility
        query = request.args.get('q', '').strip()
        term = request.args.get('term', '').strip()
        search_term = query or term  # Use q= if provided, fallback to term=
        
        action = request.args.get('action', 'simple')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term required',
                'usage': '/api/shortcuts/search?q=philosophy&action=simple (or use term= for legacy)',
                'supported_actions': ['simple', 'count', 'has_results', 'titles']
            }), 400
            
        if action == 'count':
            count = execute_pg_function('api_shortcuts_search_count', search_term)
            return jsonify(count)  # Return simple integer for iOS Shortcuts
            
        elif action == 'has_results':
            has_results = execute_pg_function('api_shortcuts_search_has_results', search_term)
            return jsonify(has_results)  # Return simple boolean
            
        elif action == 'titles':
            titles = execute_pg_function('api_shortcuts_search_titles', search_term, limit)
            return jsonify(titles)  # Return simple array
            
        else:  # simple search
            result = execute_pg_function('api_shortcuts_search_simple', search_term, limit)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Shortcuts search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Missing Shortcuts Routes - Add the endpoints that tests expect
@shortcuts_bp.route('/api/shortcuts/random')
@require_auth
def shortcuts_random_fallback():
    """Fallback for /api/shortcuts/random - redirect to random title"""
    try:
        # Default to random title if no specific type requested
        result = execute_pg_function('api_shortcuts_random_title')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Random fallback error: {e}")
        return jsonify({'error': 'Failed to get random content'}), 500


@shortcuts_bp.route('/api/shortcuts/stats')
@require_auth
def shortcuts_stats_fallback():
    """Fallback for /api/shortcuts/stats - redirect to collection health"""
    try:
        health = execute_pg_function('api_shortcuts_collection_health')
        return jsonify(health)
    except Exception as e:
        logger.error(f"Stats fallback error: {e}")
        return jsonify({'error': 'Failed to get stats'}), 500


@shortcuts_bp.route('/api/shortcuts/lists')
@require_auth
def shortcuts_lists_fallback():
    """Fallback for /api/shortcuts/lists - provide list options"""
    try:
        action = request.args.get('action', 'titles')
        limit = min(int(request.args.get('limit', 100)), 500)
        page = max(int(request.args.get('page', 1)), 1)
        
        if action == 'authors':
            authors = execute_pg_function('api_shortcuts_list_authors', limit, page)
            return jsonify(authors)
        else:  # default to titles
            titles = execute_pg_function('api_shortcuts_list_titles', limit, page)
            return jsonify(titles)
            
    except Exception as e:
        logger.error(f"Lists fallback error: {e}")
        return jsonify({'error': 'Failed to get lists'}), 500


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