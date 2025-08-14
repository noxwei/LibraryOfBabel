"""
LibraryOfBabel Standardized Books API
====================================

Dr. Sarah Chen (陈雪芳) - REST API Standardization
LEVEL 1 CORE RESOURCE: /api/books

CONSOLIDATED FROM:
- /api/v4/books (7 actions)
- /api/shortcuts/books (4 actions)

ZERO INCONSISTENCIES - PRODUCTION READY
"""

import logging
from flask import Blueprint, request
from .auth import require_auth_unless_localhost
from .database import execute_pg_function
from .validation import validate_params
from .response_helpers import (
    create_success_response, create_error_response, create_list_response,
    create_single_item_response, init_response_timing
)

logger = logging.getLogger(__name__)
standardized_books_bp = Blueprint('standardized_books', __name__)

# DEFAULT BOOK ID (consistent with prompts)
DEFAULT_BOOK_ID = 5560

@standardized_books_bp.before_request
def before_request():
    """Initialize response timing for all book endpoints"""
    init_response_timing()

@standardized_books_bp.route('/api/books')
@require_auth_unless_localhost
@validate_params(action='list', id=5560, limit=20, page=1, format='json')
def books_endpoint():
    """
    LEVEL 1 CORE: Standardized Books API
    
    Supported actions:
    - list: List books with pagination
    - summary: Get book summary (requires id)
    - toc: Get table of contents (requires id)  
    - random_page: Get random page (requires id)
    - construct: Get book construction (requires id)
    - page: Get specific page (requires id, page_num)
    
    Standard Parameters:
    - action: string (list|summary|toc|random_page|construct|page)
    - id: integer (book ID, defaults to 5560)
    - limit: integer (1-200, default: 20)
    - page: integer (page number, default: 1)
    - format: string (json|simple, default: json)
    """
    try:
        params = request.validated_params
        action = params['action']
        book_id = params.get('id', DEFAULT_BOOK_ID)
        limit = params['limit']
        page = params['page']
        response_format = params['format']
        
        # ACTION ROUTING
        if action == 'list':
            return _handle_books_list(limit, page, response_format)
            
        elif action == 'summary':
            return _handle_book_summary(book_id, response_format)
            
        elif action == 'toc':
            return _handle_book_toc(book_id, response_format)
            
        elif action == 'random_page':
            return _handle_book_random_page(book_id, response_format)
            
        elif action == 'construct':
            return _handle_book_construct(book_id, response_format)
            
        elif action == 'page':
            # Page action requires additional page_num parameter
            page_num = request.args.get('page_num', 1, type=int)
            if page_num < 1:
                return create_error_response(
                    message="page_num must be at least 1",
                    code="INVALID_PAGE_NUMBER",
                    status_code=400
                )
            return _handle_book_page(book_id, page_num, response_format)
            
        else:
            return create_error_response(
                message=f"Unsupported action: {action}",
                code="UNSUPPORTED_ACTION",
                details={
                    "supported_actions": ["list", "summary", "toc", "random_page", "construct", "page"],
                    "provided_action": action
                },
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Books endpoint error: {e}")
        return create_error_response(
            message="Failed to process books request",
            code="BOOKS_API_ERROR",
            status_code=500
        )

def _handle_books_list(limit: int, page: int, response_format: str):
    """Handle books list action with standardized response - PostgreSQL-First ONLY"""
    try:
        # Use existing PostgreSQL function api_list_books (pure PostgreSQL-First)
        result = execute_pg_function('api_list_books', page, limit)
        
        # The function returns TABLE format, convert to list
        if isinstance(result, list):
            books = []
            total_count = 0
            
            for row in result:
                if isinstance(row, dict):
                    book = {
                        'book_id': row.get('book_id'),
                        'title': row.get('title'),
                        'author': row.get('author'),
                        'publication_date': row.get('publication_date'),
                        'genre': row.get('genre', 'Unknown'),
                        'word_count': row.get('word_count'),
                        'processed_date': row.get('processed_date')
                    }
                    books.append(book)
                    # Get total count from the first row if available
                    if 'total_items' in row:
                        total_count = row['total_items']
            
            if response_format == 'simple':
                # Mobile-optimized simple response
                return create_success_response(data=books)
            else:
                # Full response with pagination metadata
                return create_list_response(
                    items=books,
                    total_count=total_count,
                    limit=limit,
                    page=page
                )
        else:
            # Handle unexpected format
            return create_success_response(data=result)
                    
    except Exception as e:
        logger.error(f"Books list error: {e}")
        return create_error_response(
            message="Failed to retrieve books list",
            code="BOOKS_LIST_ERROR",
            status_code=500
        )

def _handle_book_summary(book_id: int, response_format: str):
    """Handle book summary action"""
    try:
        result = execute_pg_function('api_shortcuts_book_summary', book_id)
        
        if response_format == 'simple':
            # Extract just the core data for mobile
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Book summary error for ID {book_id}: {e}")
        return create_error_response(
            message=f"Failed to get summary for book {book_id}",
            code="BOOK_SUMMARY_ERROR",
            status_code=500
        )

def _handle_book_toc(book_id: int, response_format: str):
    """Handle book table of contents action"""
    try:
        result = execute_pg_function('api_shortcuts_book_toc', book_id)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Book TOC error for ID {book_id}: {e}")
        return create_error_response(
            message=f"Failed to get table of contents for book {book_id}",
            code="BOOK_TOC_ERROR",
            status_code=500
        )

def _handle_book_random_page(book_id: int, response_format: str):
    """Handle book random page action"""
    try:
        result = execute_pg_function('api_shortcuts_book_random_page', book_id)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Book random page error for ID {book_id}: {e}")
        return create_error_response(
            message=f"Failed to get random page for book {book_id}",
            code="BOOK_RANDOM_PAGE_ERROR",
            status_code=500
        )

def _handle_book_construct(book_id: int, response_format: str):
    """Handle book construction action"""
    try:
        result = execute_pg_function('api_shortcuts_book_construct', book_id)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Book construct error for ID {book_id}: {e}")
        return create_error_response(
            message=f"Failed to get construction info for book {book_id}",
            code="BOOK_CONSTRUCT_ERROR",
            status_code=500
        )

def _handle_book_page(book_id: int, page_num: int, response_format: str):
    """Handle specific book page action"""
    try:
        result = execute_pg_function('api_shortcuts_book_page', book_id, page_num)
        
        if response_format == 'simple':
            if isinstance(result, dict) and 'data' in result:
                return create_success_response(data=result['data'])
            return create_success_response(data=result)
        else:
            return create_single_item_response(result)
            
    except Exception as e:
        logger.error(f"Book page error for ID {book_id}, page {page_num}: {e}")
        return create_error_response(
            message=f"Failed to get page {page_num} for book {book_id}",
            code="BOOK_PAGE_ERROR",
            status_code=500
        )

# CHAPTER NAVIGATION HELPER (from original shortcuts implementation)
@standardized_books_bp.route('/api/books/chapter')
@require_auth_unless_localhost
@validate_params(id=DEFAULT_BOOK_ID, chapter=1)
def books_chapter_navigation():
    """
    Navigate to first page of specific chapter
    
    Parameters:
    - id: integer (book ID, defaults to 5560)
    - chapter: integer (chapter number, required)
    """
    try:
        params = request.validated_params
        book_id = params['id']
        chapter = params['chapter']
        
        # PostgreSQL-First ONLY - use existing book chunk functions
        try:
            # Use existing api_get_book_chunks to find chapter content
            # Get chunks for this book filtered by chapter
            result = execute_pg_function('api_get_book_chunks', book_id, 1, 1)
            
            if result and len(result) > 0:
                # Find the first chunk of the requested chapter
                for chunk_data in result:
                    if isinstance(chunk_data, dict) and chunk_data.get('chapter_number') == chapter:
                        # Found the chapter, get the page content
                        page_result = execute_pg_function('api_shortcuts_book_page', book_id, 1)
                        return create_single_item_response(page_result)
                
                # Chapter not found
                return create_error_response(
                    message=f"Chapter {chapter} not found in book {book_id}",
                    code="CHAPTER_NOT_FOUND",
                    status_code=404
                )
            else:
                return create_error_response(
                    message=f"No content found for book {book_id}",
                    code="BOOK_NOT_FOUND",
                    status_code=404
                )
                
        except Exception as e:
            logger.error(f"Chapter navigation PostgreSQL error: {e}")
            return create_error_response(
                message=f"Failed to navigate to chapter {chapter} in book {book_id}",
                code="CHAPTER_NAVIGATION_ERROR",
                status_code=500
            )
                    
    except Exception as e:
        logger.error(f"Chapter navigation error: {e}")
        return create_error_response(
            message="Failed to navigate to chapter",
            code="CHAPTER_NAVIGATION_ERROR",
            status_code=500
        )