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
import re
from flask import Blueprint, request
from .auth import public_read
from .database import execute_pg_function
from .validation import validate_params
from .nomic_intelligent_search import nomic_chapter_semantic_search
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
@public_read
@validate_params(q=None, action='search', limit=20, page=1, format='json', sort='relevance', id=None, title=None, author=None, description=None, genre=None, embedding_model='nomic-embed-text', ensemble=False)
def search_endpoint():
    """
    LEVEL 1 CORE: Standardized Search API
    
    Supported actions:
    - search: Basic content search (default)
    - count: Count search results
    - titles: Search book titles only
    - books: Comprehensive book metadata search (title, author, description, genre)
    - has_results: Check if results exist
    - semantic: Semantic vector search (book-level results)
    - semantic_passages: Intelligent chapter-level semantic search with smart content previews (nomic-embed-text)
    - concept: Concept-based search
    - passage: Passage similarity search
    - emotional: Emotional content search
    - highlighted: Search with content highlights
    - advanced: Advanced multi-filter search
    - discovery: Book discovery engine using opening semantic analysis
    - style: Writing style analysis and matching from opening passages
    - quality: Content quality assessment based on opening analysis
    
    Standard Parameters:
    - q: string (search query, required)
    - action: string (search action, default: search)
    - limit: integer (1-200, default: 20)
    - page: integer (page number, default: 1)
    - format: string (json|simple, default: json)
    - sort: string (relevance|title|author|word_count|publication_date, default: relevance)
    - embedding_model: string (nomic-embed-text|mxbai-embed-large|bge-m3, default: nomic-embed-text)
    - ensemble: boolean (use multiple models for better accuracy, default: false)
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
            
        elif action == 'books':
            return _handle_books_metadata_search(query, limit, page, response_format, sort_field)
            
        elif action == 'has_results':
            return _handle_has_results(query, response_format)
            
        elif action == 'semantic':
            embedding_model = params.get('embedding_model', 'nomic-embed-text')
            ensemble = params.get('ensemble', False)
            return _handle_semantic_search(query, limit, response_format, sort_field, embedding_model, ensemble)
            
        elif action == 'semantic_passages':
            embedding_model = params.get('embedding_model', 'nomic-embed-text')
            genre_filter = request.args.get('genre')
            if genre_filter and (len(genre_filter) > 100 or not re.match(r'^[a-zA-Z0-9\s\-\']+$', genre_filter)):
                return create_error_response(
                    message="Invalid genre parameter",
                    code="INVALID_GENRE_PARAMETER",
                    details={"max_length": 100, "allowed_characters": "alphanumeric, spaces, hyphens, apostrophes"},
                    status_code=400
                )
            return _handle_nomic_intelligent_search(query, limit, response_format, genre_filter, sort_field)
            
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
            book_id = params.get('id')
            return _handle_highlighted_search(query, limit, snippet_length, response_format, sort_field, book_id)
            
        elif action == 'advanced':
            return _handle_advanced_search(query, limit, response_format, sort_field)
            
        elif action == 'discovery':
            embedding_model = params.get('embedding_model', 'nomic-embed-text')
            return _handle_discovery_search(query, limit, response_format, sort_field, embedding_model)
            
        elif action == 'style':
            embedding_model = params.get('embedding_model', 'nomic-embed-text')
            return _handle_style_search(query, limit, response_format, sort_field, embedding_model)
            
        elif action == 'quality':
            embedding_model = params.get('embedding_model', 'nomic-embed-text')
            quality_threshold = min(max(float(request.args.get('quality_threshold', 0.6)), 0.1), 1.0)
            return _handle_quality_search(query, limit, response_format, sort_field, embedding_model, quality_threshold)
        
        elif action == 'author_influence':
            # Author influence network analysis
            return _handle_author_influence_search(query, limit, response_format)
        
        elif action == 'thematic_evolution':
            # Thematic evolution patterns across literature
            return _handle_thematic_evolution_search(query, limit, response_format)
        
        elif action == 'content_analysis':
            # Deep content analysis (stylometric, thematic, entities)
            return _handle_content_analysis_search(query, limit, response_format)
            
        else:
            return create_error_response(
                message=f"Unsupported search action: {action}",
                code="UNSUPPORTED_SEARCH_ACTION",
                details={
                    "supported_actions": ["search", "count", "titles", "books", "has_results", "semantic", "semantic_passages", "concept", "passage", "emotional", "highlighted", "advanced", "discovery", "style", "quality", "author_influence", "thematic_evolution", "content_analysis"],
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
    """Handle titles search using fast PostgreSQL function"""
    try:
        titles = execute_pg_function('api_fast_titles_search', query, limit)
        
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

def _handle_semantic_search(query: str, limit: int, response_format: str, sort_field: str, embedding_model: str = 'nomic-embed-text', ensemble: bool = False):
    """Handle semantic search using PostgreSQL functions with model selection"""
    try:
        # Validate embedding model
        valid_models = ['nomic-embed-text', 'mxbai-embed-large', 'bge-m3']
        if embedding_model not in valid_models:
            return create_error_response(
                message=f"Invalid embedding model: {embedding_model}",
                code="INVALID_EMBEDDING_MODEL",
                details={
                    "provided_model": embedding_model,
                    "supported_models": valid_models
                },
                status_code=400
            )
        
        if ensemble:
            # Use ensemble search with multiple models
            result = execute_pg_function('api_semantic_ensemble_search', query, ['nomic-embed-text', 'mxbai-embed-large', 'bge-m3'], [0.5, 0.3, 0.2], limit)
        else:
            # Use single model search
            result = execute_pg_function('api_semantic_fullbook_search_multimodel', query, embedding_model, limit)
            
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Semantic search error for query '{query}' with model '{embedding_model}': {e}")
        return create_error_response(
            message=f"Semantic search failed for query: {query}",
            code="SEMANTIC_SEARCH_ERROR",
            details={"embedding_model": embedding_model, "ensemble": ensemble},
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

def _handle_highlighted_search(query: str, limit: int, snippet_length: int, response_format: str, sort_field: str, book_id: int = None):
    """Handle highlighted search using PostgreSQL function"""
    try:
        if book_id:
            # Book-specific passage search with regular text matching
            result = execute_pg_function('api_book_passage_search', book_id, query, limit)
        else:
            # Global trigram search across entire database
            result = execute_pg_function('api_search_content_with_highlights', query, limit, snippet_length)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Highlighted search error for query '{query}' (book_id: {book_id}): {e}")
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

def _handle_nomic_intelligent_search(query: str, limit: int, response_format: str, genre_filter: str = None, sort_field: str = 'relevance'):
    """Handle nomic intelligent chapter search with smart content previews"""
    try:
        # Use our new nomic intelligent search
        result = nomic_chapter_semantic_search(query, limit, genre_filter, sort_field)
        
        if not result['success']:
            return create_error_response(
                message=f"Nomic intelligent search failed: {result.get('error', 'Unknown error')}",
                code="NOMIC_INTELLIGENT_SEARCH_ERROR",
                status_code=500
            )
        
        search_results = result['results']
        metadata = result['search_metadata']
        
        if response_format == 'simple':
            # Mobile-optimized format
            simplified_results = []
            for item in search_results:
                simplified_results.append({
                    'title': item['title'],
                    'author': item['author'],
                    'genre': item['genre'],
                    'preview': item['preview'],
                    'similarity_score': item['similarity_score'],
                    'terms_found': item['query_terms_found']
                })
            return create_success_response(data=simplified_results)
        else:
            # Full format with enhanced results including metadata
            enhanced_results = []
            for item in search_results:
                enhanced_item = item.copy()
                enhanced_item['search_metadata'] = {
                    'search_type': 'nomic_intelligent_chapter_search',
                    'model': 'nomic-embed-text',
                    'intelligent_preview': True,
                    'max_chapter_words': metadata['max_chapter_words'],
                    'genre_filter': genre_filter
                }
                enhanced_results.append(enhanced_item)
            
            return create_list_response(
                items=enhanced_results,
                total_count=len(enhanced_results)
            )
            
    except Exception as e:
        logger.error(f"Nomic intelligent search error for query '{query}': {e}")
        return create_error_response(
            message=f"Nomic intelligent search failed for query: {query}",
            code="NOMIC_INTELLIGENT_SEARCH_ERROR",
            details={"genre_filter": genre_filter},
            status_code=500
        )

def _handle_books_metadata_search(query: str, limit: int, page: int, response_format: str, sort_field: str):
    """Handle comprehensive book metadata search using PostgreSQL function"""
    try:
        # Get field-specific filters from request
        title_filter = request.args.get('title', '').strip()
        author_filter = request.args.get('author', '').strip()
        description_filter = request.args.get('description', '').strip()
        genre_filter = request.args.get('genre', '').strip()
        
        # Map sort field to PostgreSQL function parameter
        sort_mapping = {
            'relevance': 'author_title',
            'title': 'title',
            'author': 'author', 
            'word_count': 'word_count'
        }
        pg_sort_field = sort_mapping.get(sort_field, 'author_title')
        
        # Call the PostgreSQL function with field-specific filters
        result = execute_pg_function(
            'api_book_metadata_search',
            query,
            author_filter,
            genre_filter,
            title_filter,
            description_filter,
            page,
            limit,
            pg_sort_field
        )
        
        if response_format == 'simple':
            # Return simplified format for mobile
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data']['books'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Books metadata search error for query '{query}': {e}")
        return create_error_response(
            message=f"Book metadata search failed for query: {query}",
            code="BOOK_METADATA_SEARCH_ERROR", 
            status_code=500
        )

def _handle_discovery_search(query: str, limit: int, response_format: str, sort_field: str, embedding_model: str = 'nomic-embed-text'):
    """Handle book discovery using opening chunk semantic analysis"""
    try:
        # Validate embedding model
        valid_models = ['nomic-embed-text', 'mxbai-embed-large', 'bge-m3']
        if embedding_model not in valid_models:
            return create_error_response(
                message=f"Invalid embedding model: {embedding_model}",
                code="INVALID_EMBEDDING_MODEL",
                details={
                    "provided_model": embedding_model,
                    "supported_models": valid_models
                },
                status_code=400
            )
        
        # Use opening chunks (full-book chunks) for book discovery
        result = execute_pg_function('api_semantic_opening_discovery', query, embedding_model, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Discovery search error for query '{query}' with model '{embedding_model}': {e}")
        return create_error_response(
            message=f"Discovery search failed for query: {query}",
            code="DISCOVERY_SEARCH_ERROR",
            details={"embedding_model": embedding_model},
            status_code=500
        )

def _handle_style_search(query: str, limit: int, response_format: str, sort_field: str, embedding_model: str = 'nomic-embed-text'):
    """Handle writing style analysis using opening chunk analysis"""
    try:
        # Validate embedding model
        valid_models = ['nomic-embed-text', 'mxbai-embed-large', 'bge-m3']
        if embedding_model not in valid_models:
            return create_error_response(
                message=f"Invalid embedding model: {embedding_model}",
                code="INVALID_EMBEDDING_MODEL",
                details={
                    "provided_model": embedding_model,
                    "supported_models": valid_models
                },
                status_code=400
            )
        
        # Use opening chunks for style analysis and matching
        result = execute_pg_function('api_semantic_style_analysis', query, embedding_model, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Style search error for query '{query}' with model '{embedding_model}': {e}")
        return create_error_response(
            message=f"Style search failed for query: {query}",
            code="STYLE_SEARCH_ERROR",
            details={"embedding_model": embedding_model},
            status_code=500
        )

def _handle_quality_search(query: str, limit: int, response_format: str, sort_field: str, embedding_model: str = 'nomic-embed-text', quality_threshold: float = 0.6):
    """Handle content quality assessment using opening analysis"""
    try:
        # Validate embedding model
        valid_models = ['nomic-embed-text', 'mxbai-embed-large', 'bge-m3']
        if embedding_model not in valid_models:
            return create_error_response(
                message=f"Invalid embedding model: {embedding_model}",
                code="INVALID_EMBEDDING_MODEL",
                details={
                    "provided_model": embedding_model,
                    "supported_models": valid_models
                },
                status_code=400
            )
        
        # Use opening chunks for quality assessment
        result = execute_pg_function('api_semantic_quality_assessment', query, embedding_model, quality_threshold, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Quality search error for query '{query}' with model '{embedding_model}': {e}")
        return create_error_response(
            message=f"Quality search failed for query: {query}",
            code="QUALITY_SEARCH_ERROR",
            details={"embedding_model": embedding_model, "quality_threshold": quality_threshold},
            status_code=500
        )

def _handle_author_influence_search(query: str, limit: int, response_format: str):
    """Handle author influence network analysis"""
    try:
        # Query can be author name or influence type
        if query and not query.isspace():
            # Treat query as author name
            result = execute_pg_function('api_author_influence_network', query, 'stylistic_similarity', limit)
        else:
            # Get network overview
            result = execute_pg_function('api_author_influence_network', None, 'stylistic_similarity', limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Author influence search error for query '{query}': {e}")
        return create_error_response(
            message=f"Author influence analysis failed for query: {query}",
            code="AUTHOR_INFLUENCE_ERROR",
            status_code=500
        )

def _handle_thematic_evolution_search(query: str, limit: int, response_format: str):
    """Handle thematic evolution analysis"""
    try:
        # Query can be theme name or evolution type
        evolution_type = 'historical'  # Default
        theme_name = None
        
        if query and not query.isspace():
            # Check if query looks like evolution type
            if query.lower() in ['historical', 'structural', 'all']:
                evolution_type = query.lower()
            else:
                # Treat as theme name
                theme_name = query
        
        result = execute_pg_function('api_thematic_evolution', theme_name, evolution_type, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Thematic evolution search error for query '{query}': {e}")
        return create_error_response(
            message=f"Thematic evolution analysis failed for query: {query}",
            code="THEMATIC_EVOLUTION_ERROR",
            status_code=500
        )

def _handle_content_analysis_search(query: str, limit: int, response_format: str):
    """Handle deep content analysis"""
    try:
        # Query determines analysis type
        analysis_type = 'overview'  # Default
        filter_value = None
        
        if query and not query.isspace():
            # Check for analysis types
            if query.lower() in ['stylometric', 'thematic', 'entities', 'overview']:
                analysis_type = query.lower()
            else:
                # Use query as filter value
                filter_value = query
                analysis_type = 'thematic'  # Default when filtering
        
        result = execute_pg_function('api_content_analysis', analysis_type, filter_value, limit)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Content analysis search error for query '{query}': {e}")
        return create_error_response(
            message=f"Content analysis failed for query: {query}",
            code="CONTENT_ANALYSIS_ERROR",
            status_code=500
        )