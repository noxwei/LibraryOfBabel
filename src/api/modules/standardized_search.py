"""
LibraryOfBabel Standardized Search API
=====================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization
LEVEL 1 CORE RESOURCE: /api/search

CONSOLIDATED FROM:
- /api/v4/search (10 actions)
- /api/v4/search/semantic (semantic search)
- /api/v4/search/advanced (advanced filters)
- /api/v4/search/passage (passage search)
- /api/shortcuts/search (4 actions)

POSTGRESQL-FIRST ONLY - ZERO HARDCODED SQL
"""

import logging
from flask import Blueprint, request
from .auth import require_auth_unless_localhost
from .database import execute_pg_function
from .validation import validate_params
from .response_helpers import (
    create_success_response, create_error_response, create_list_response,
    create_single_item_response, create_count_response, create_boolean_response,
    init_response_timing
)

logger = logging.getLogger(__name__)
standardized_search_bp = Blueprint('standardized_search', __name__)

@standardized_search_bp.before_request
def before_request():
    """Initialize response timing for all search endpoints"""
    init_response_timing()

@standardized_search_bp.route('/api/search')
@require_auth_unless_localhost
@validate_params('q', action='search', limit=20, page=1, format='json', sort='relevance')
def search_endpoint():
    """
    LEVEL 1 CORE: Standardized Search API
    
    Supported actions:
    - search: Basic content search (default)
    - count: Count search results
    - titles: Search book titles only
    - has_results: Check if results exist
    - semantic: Semantic vector search (book-level results)
    - semantic_passages: Semantic vector search (passage/chunk-level results)
    - concept: Concept-based search
    - passage: Passage similarity search
    - emotional: Emotional content search
    - highlighted: Search with content highlights
    - advanced: Advanced multi-filter search
    
    Standard Parameters:
    - q: string (search query, required)
    - action: string (search action, default: search)
    - limit: integer (1-200, default: 20)
    - page: integer (page number, default: 1)
    - format: string (json|simple, default: json)
    - sort: string (relevance|title|author|word_count|publication_date, default: relevance)
    """
    try:
        params = request.validated_params
        query = params['q']
        action = params['action']
        limit = params['limit']
        page = params['page']
        response_format = params['format']
        sort_field = params.get('sort', 'relevance')
        
        # ACTION ROUTING - All PostgreSQL functions
        if action == 'search':
            return _handle_basic_search(query, limit, response_format, sort_field)
            
        elif action == 'count':
            return _handle_search_count(query, response_format)
            
        elif action == 'titles':
            return _handle_titles_search(query, limit, response_format, sort_field)
            
        elif action == 'has_results':
            return _handle_has_results(query, response_format)
            
        elif action == 'semantic':
            return _handle_semantic_search(query, limit, response_format, sort_field)
            
        elif action == 'semantic_passages':
            return _handle_semantic_passages_search(query, limit, response_format, sort_field)
            
        elif action == 'concept':
            threshold = min(max(float(request.args.get('threshold', 0.4)), 0.1), 1.0)
            return _handle_concept_search(query, threshold, limit, response_format, sort_field)
            
        elif action == 'passage':
            return _handle_passage_search(query, limit, response_format, sort_field)
            
        elif action == 'emotional':
            book_filter = request.args.get('book_id', type=int)
            return _handle_emotional_search(query, book_filter, limit, response_format, sort_field)
            
        elif action == 'highlighted':
            snippet_length = min(int(request.args.get('snippet_length', 200)), 500)
            return _handle_highlighted_search(query, limit, snippet_length, response_format, sort_field)
            
        elif action == 'advanced':
            return _handle_advanced_search(query, limit, response_format, sort_field)
            
        else:
            return create_error_response(
                message=f"Unsupported search action: {action}",
                code="UNSUPPORTED_SEARCH_ACTION",
                details={
                    "supported_actions": ["search", "count", "titles", "has_results", "semantic", "semantic_passages", "concept", "passage", "emotional", "highlighted", "advanced"],
                    "provided_action": action
                },
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return create_error_response(
            message="Failed to process search request",
            code="SEARCH_API_ERROR",
            status_code=500
        )

def _handle_basic_search(query: str, limit: int, response_format: str, sort_field: str):
    """Handle basic search using PostgreSQL function"""
    try:
        result = execute_pg_function('api_shortcuts_search_simple', query, limit)
        
        if response_format == 'simple':
            # Mobile-optimized response
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Basic search error for query '{query}': {e}")
        return create_error_response(
            message=f"Basic search failed for query: {query}",
            code="BASIC_SEARCH_ERROR",
            status_code=500
        )

def _handle_search_count(query: str, response_format: str):
    """Handle search count using PostgreSQL function"""
    try:
        count = execute_pg_function('api_shortcuts_search_count', query)
        
        if response_format == 'simple':
            # Return just the number for mobile
            return create_success_response(data=count)
        else:
            return create_count_response(count)
            
    except Exception as e:
        logger.error(f"Search count error for query '{query}': {e}")
        return create_error_response(
            message=f"Search count failed for query: {query}",
            code="SEARCH_COUNT_ERROR",
            status_code=500
        )

def _handle_titles_search(query: str, limit: int, response_format: str, sort_field: str):
    """Handle titles search using PostgreSQL function"""
    try:
        titles = execute_pg_function('api_shortcuts_search_titles', query, limit)
        
        if response_format == 'simple':
            # Return just the titles array for mobile
            return create_success_response(data=titles)
        else:
            return create_list_response(items=titles)
            
    except Exception as e:
        logger.error(f"Titles search error for query '{query}': {e}")
        return create_error_response(
            message=f"Titles search failed for query: {query}",
            code="TITLES_SEARCH_ERROR",
            status_code=500
        )

def _handle_has_results(query: str, response_format: str):
    """Handle has_results check using PostgreSQL function"""
    try:
        has_results = execute_pg_function('api_shortcuts_search_has_results', query)
        
        if response_format == 'simple':
            # Return just the boolean for mobile
            return create_success_response(data=has_results)
        else:
            return create_boolean_response(has_results)
            
    except Exception as e:
        logger.error(f"Has results error for query '{query}': {e}")
        return create_error_response(
            message=f"Has results check failed for query: {query}",
            code="HAS_RESULTS_ERROR",
            status_code=500
        )

def _handle_semantic_search(query: str, limit: int, response_format: str, sort_field: str):
    """Handle semantic search using PostgreSQL functions"""
    try:
        # Use the new fullbook semantic search with actual nomic embeddings
        result = execute_pg_function('api_semantic_fullbook_search', query, limit)
            
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Semantic search error for query '{query}': {e}")
        return create_error_response(
            message=f"Semantic search failed for query: {query}",
            code="SEMANTIC_SEARCH_ERROR",
            status_code=500
        )

def _handle_concept_search(query: str, threshold: float, limit: int, response_format: str, sort_field: str):
    """Handle concept search using PostgreSQL function"""
    try:
        result = execute_pg_function('api_semantic_concept_search', query, threshold, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Concept search error for query '{query}': {e}")
        return create_error_response(
            message=f"Concept search failed for query: {query}",
            code="CONCEPT_SEARCH_ERROR",
            status_code=500
        )

def _handle_passage_search(query: str, limit: int, response_format: str, sort_field: str):
    """Handle passage search using PostgreSQL functions"""
    try:
        # Use the correct, existing PostgreSQL function
        # The previous functions api_fullbook_fts_passage_search and api_chapter_fts_passage_search don't exist
        result = execute_pg_function('api_passage_similarity_search', query, limit)
        search_method = "Vector-Passage-Similarity"
        
        # Format results consistently
        formatted_results = []
        if isinstance(result, dict) and 'results' in result:
            # Handle JSON response from PostgreSQL function
            for row in result['results'][:limit]:
                if isinstance(row, dict):
                    formatted_results.append({
                        'title': row.get('title'),
                        'author': row.get('author'),
                        'content': row.get('content'),
                        'chunk_id': row.get('chunk_id'),
                        'similarity_score': row.get('similarity_score'),
                        'chunk_type': row.get('chunk_type')
                    })
        elif isinstance(result, list):
            # Handle table response from PostgreSQL function
            for row in result[:limit]:
                if isinstance(row, dict):
                    formatted_results.append({
                        'title': row.get('title'),
                        'author': row.get('author'),
                        'content': row.get('content'),
                        'chunk_id': row.get('chunk_id'),
                        'similarity_score': row.get('similarity_score'),
                        'chunk_type': row.get('chunk_type')
                    })
        
        if response_format == 'simple':
            return create_success_response(data=formatted_results)
        else:
            return create_list_response(
                items=formatted_results,
                total_count=len(formatted_results)
            )
            
    except Exception as e:
        logger.error(f"Passage search error for query '{query}': {e}")
        return create_error_response(
            message=f"Passage search failed for query: {query}",
            code="PASSAGE_SEARCH_ERROR",
            status_code=500
        )

def _handle_emotional_search(query: str, book_filter: int, limit: int, response_format: str, sort_field: str):
    """Handle emotional content search using PostgreSQL function"""
    try:
        result = execute_pg_function('api_emotional_content_search', query, book_filter, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Emotional search error for query '{query}': {e}")
        return create_error_response(
            message=f"Emotional search failed for query: {query}",
            code="EMOTIONAL_SEARCH_ERROR",
            status_code=500
        )

def _handle_highlighted_search(query: str, limit: int, snippet_length: int, response_format: str, sort_field: str):
    """Handle highlighted search using PostgreSQL function"""
    try:
        result = execute_pg_function('api_search_content_with_highlights', query, limit, snippet_length)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Highlighted search error for query '{query}': {e}")
        return create_error_response(
            message=f"Highlighted search failed for query: {query}",
            code="HIGHLIGHTED_SEARCH_ERROR",
            status_code=500
        )

def _handle_advanced_search(query: str, limit: int, response_format: str, sort_field: str):
    """Handle advanced search using PostgreSQL functions"""
    try:
        # Get additional filters from request
        author = request.args.get('author', '').strip()
        genre = request.args.get('genre', '').strip()
        year_min = request.args.get('year_min', type=int)
        year_max = request.args.get('year_max', type=int)
        
        # Use existing fast trigram search as base
        if query:
            result = execute_pg_function('api_fast_trigram_phonetic_search', query, limit)
        else:
            # If no query, use book listing with filters
            result = execute_pg_function('api_list_books', 1, limit, None, author, genre)
        
        # Apply additional filters if needed (handled by PostgreSQL functions)
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Advanced search error for query '{query}': {e}")
        return create_error_response(
            message=f"Advanced search failed for query: {query}",
            code="ADVANCED_SEARCH_ERROR",
            status_code=500
        )

def _handle_semantic_passages_search(query: str, limit: int, response_format: str, sort_field: str):
    """Handle semantic passages search using PostgreSQL functions"""
    try:
        # Use the new passages semantic search with actual nomic embeddings
        result = execute_pg_function('api_semantic_passages_search', query, limit)
            
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Semantic passages search error for query '{query}': {e}")
        return create_error_response(
            message=f"Semantic passages search failed for query: {query}",
            code="SEMANTIC_PASSAGES_SEARCH_ERROR",
            status_code=500
        )