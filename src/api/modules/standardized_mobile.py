"""
LibraryOfBabel Standardized Mobile API
=====================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization  
LEVEL 3 MOBILE: /api/mobile/*

CONSOLIDATED FROM:
- /api/shortcuts/* (12 endpoints)

iOS SHORTCUTS OPTIMIZED - CLEAN RESPONSES, NO METADATA POLLUTION
"""

import logging
from flask import Blueprint, request
from .auth import require_auth_unless_localhost
from .database import execute_pg_function
from .validation import validate_params
from .response_helpers import (
    create_success_response, create_mobile_response, init_response_timing
)

logger = logging.getLogger(__name__)
standardized_mobile_bp = Blueprint('standardized_mobile', __name__)

@standardized_mobile_bp.before_request
def before_request():
    """Initialize response timing for mobile endpoints"""
    init_response_timing()

# MOBILE RANDOM CONTENT
@standardized_mobile_bp.route('/api/mobile/random')
@require_auth_unless_localhost
@validate_params(type='title')
def mobile_random():
    """
    Mobile random content endpoint
    
    Parameters:
    - type: string (title|author|citation|share, default: title)
    """
    try:
        params = request.validated_params
        content_type = params['type']
        
        # Route to appropriate PostgreSQL function
        if content_type == 'title':
            result = execute_pg_function('api_shortcuts_random_title')
        elif content_type == 'author':
            result = execute_pg_function('api_shortcuts_random_author')
        elif content_type == 'citation':
            result = execute_pg_function('api_shortcuts_random_citation')
        elif content_type == 'share':
            result = execute_pg_function('api_shortcuts_random_share_text')
        else:
            return create_mobile_response({"error": "Invalid type"}, simplified=False)
        
        # Return mobile-optimized response (simplified)
        return create_mobile_response(result, simplified=True)
        
    except Exception as e:
        logger.error(f"Mobile random error: {e}")
        return create_mobile_response({"error": "Failed to get random content"}, simplified=False)

# MOBILE SEARCH
@standardized_mobile_bp.route('/api/mobile/search')
@require_auth_unless_localhost
@validate_params('q', action='simple', limit=5)
def mobile_search():
    """
    Mobile search endpoint - optimized for iOS Shortcuts
    
    Parameters:
    - q: string (search query, required)
    - action: string (simple|count|titles|has_results, default: simple)
    - limit: integer (1-10, default: 5)
    """
    try:
        params = request.validated_params
        query = params['q']
        action = params['action']
        limit = min(params['limit'], 10)  # Mobile limit cap
        
        # Route to appropriate PostgreSQL function
        if action == 'simple':
            result = execute_pg_function('api_shortcuts_search_simple', query, limit)
        elif action == 'count':
            result = execute_pg_function('api_shortcuts_search_count', query)
        elif action == 'titles':
            result = execute_pg_function('api_shortcuts_search_titles', query, limit)
        elif action == 'has_results':
            result = execute_pg_function('api_shortcuts_search_has_results', query)
        else:
            return create_mobile_response({"error": "Invalid action"}, simplified=False)
        
        # Return mobile-optimized response (simplified for iOS)
        return create_mobile_response(result, simplified=True)
        
    except Exception as e:
        logger.error(f"Mobile search error: {e}")
        return create_mobile_response({"error": "Search failed"}, simplified=False)

# MOBILE BOOKS
@standardized_mobile_bp.route('/api/mobile/books')
@require_auth_unless_localhost
@validate_params(action='summary', id=5560)
def mobile_books():
    """
    Mobile books endpoint - optimized for iOS Shortcuts
    
    Parameters:
    - action: string (summary|toc|random_page|page, default: summary)
    - id: integer (book ID, default: 5560)
    - page_num: integer (for page action)
    """
    try:
        params = request.validated_params
        action = params['action']
        book_id = params['id']
        
        # Route to appropriate PostgreSQL function
        if action == 'summary':
            result = execute_pg_function('api_shortcuts_book_summary', book_id)
        elif action == 'toc':
            result = execute_pg_function('api_shortcuts_book_toc', book_id)
        elif action == 'random_page':
            result = execute_pg_function('api_shortcuts_book_random_page', book_id)
        elif action == 'page':
            page_num = request.args.get('page_num', 1, type=int)
            result = execute_pg_function('api_shortcuts_book_page', book_id, page_num)
        else:
            return create_mobile_response({"error": "Invalid action"}, simplified=False)
        
        # Return mobile-optimized response (simplified for iOS)
        return create_mobile_response(result, simplified=True)
        
    except Exception as e:
        logger.error(f"Mobile books error: {e}")
        return create_mobile_response({"error": "Books request failed"}, simplified=False)

# MOBILE STATS
@standardized_mobile_bp.route('/api/mobile/stats')
@require_auth_unless_localhost
@validate_params(type='count')
def mobile_stats():
    """
    Mobile stats endpoint - optimized for iOS Shortcuts
    
    Parameters:
    - type: string (count|health, default: count)
    """
    try:
        params = request.validated_params
        stats_type = params['type']
        
        # Route to appropriate PostgreSQL function
        if stats_type == 'count':
            result = execute_pg_function('api_shortcuts_book_count')
        elif stats_type == 'health':
            result = execute_pg_function('api_shortcuts_collection_health')
        else:
            return create_mobile_response({"error": "Invalid stats type"}, simplified=False)
        
        # Return mobile-optimized response (simplified for iOS)
        return create_mobile_response(result, simplified=True)
        
    except Exception as e:
        logger.error(f"Mobile stats error: {e}")
        return create_mobile_response({"error": "Stats request failed"}, simplified=False)

# MOBILE LISTS
@standardized_mobile_bp.route('/api/mobile/lists')
@require_auth_unless_localhost
@validate_params(type='titles', limit=10, page=1)
def mobile_lists():
    """
    Mobile lists endpoint - optimized for iOS Shortcuts
    
    Parameters:
    - type: string (titles|authors, default: titles)
    - limit: integer (1-50, default: 10)
    - page: integer (page number, default: 1)
    """
    try:
        params = request.validated_params
        list_type = params['type']
        limit = min(params['limit'], 50)  # Mobile limit cap
        page = params['page']
        
        # Route to appropriate PostgreSQL function
        if list_type == 'titles':
            result = execute_pg_function('api_shortcuts_list_titles', limit, page)
        elif list_type == 'authors':
            result = execute_pg_function('api_shortcuts_list_authors', limit, page)
        else:
            return create_mobile_response({"error": "Invalid list type"}, simplified=False)
        
        # Return mobile-optimized response (simplified for iOS)
        return create_mobile_response(result, simplified=True)
        
    except Exception as e:
        logger.error(f"Mobile lists error: {e}")
        return create_mobile_response({"error": "List request failed"}, simplified=False)

# MOBILE DASHBOARD
@standardized_mobile_bp.route('/api/mobile/dashboard')
@require_auth_unless_localhost
@validate_params(include_gaps='false')
def mobile_dashboard():
    """
    Mobile dashboard endpoint - optimized for iOS Shortcuts
    
    Parameters:
    - include_gaps: string (true|false, default: false)
    """
    try:
        params = request.validated_params
        include_gaps = params['include_gaps'].lower() == 'true'
        
        # Use PostgreSQL function
        result = execute_pg_function('api_shortcuts_dashboard', include_gaps)
        
        # Return mobile-optimized response (full data for dashboard)
        return create_mobile_response(result, simplified=False)
        
    except Exception as e:
        logger.error(f"Mobile dashboard error: {e}")
        return create_mobile_response({"error": "Dashboard request failed"}, simplified=False)