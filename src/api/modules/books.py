"""
Books Module - PostgreSQL-First Architecture
Dr. Sarah Chen (陈雪芳) Design
"""

import logging
from flask import Blueprint, request, jsonify
from .auth import require_auth
from .database import execute_pg_function

logger = logging.getLogger(__name__)
books_bp = Blueprint('books', __name__)


@books_bp.route('/api/v4/books')
@require_auth
def v4_books():
    """V4 Books endpoint with PostgreSQL-First architecture"""
    try:
        # Get parameters
        action = request.args.get('action', 'list')
        book_id = request.args.get('id', type=int)
        limit = min(request.args.get('limit', 50, type=int), 200)
        page = request.args.get('page', 1, type=int)
        
        # Route to appropriate PostgreSQL function
        if action == 'list':
            # Use custom query with proper limit handling
            from .database import get_db
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT json_build_object(
                            'success', true,
                            'data', json_build_object(
                                'books', json_agg(
                                    json_build_object(
                                        'book_id', book_id,
                                        'title', title,
                                        'author', author,
                                        'publication_year', publication_year,
                                        'genre', genre,
                                        'word_count', word_count
                                    ) ORDER BY title
                                ),
                                'total_count', COUNT(*),
                                'limit', %s,
                                'page', %s
                            )
                        )
                        FROM (
                            SELECT book_id, title, author, publication_year, genre, word_count
                            FROM books 
                            ORDER BY title
                            LIMIT %s OFFSET %s
                        ) limited_books
                    """, (limit, page, limit, (page - 1) * limit))
                    result = cur.fetchone()[0]
                    return jsonify(result)
                    
        elif action == 'summary' and book_id:
            result = execute_pg_function('api_shortcuts_book_summary', book_id)
            return jsonify(result)
            
        elif action == 'toc' and book_id:
            result = execute_pg_function('api_shortcuts_book_toc', book_id)
            return jsonify(result)
            
        elif action == 'random_page' and book_id:
            result = execute_pg_function('api_shortcuts_book_random_page', book_id)
            return jsonify(result)
            
        elif action == 'construct' and book_id:
            result = execute_pg_function('api_shortcuts_book_construct', book_id)
            return jsonify(result)
            
        elif action == 'page' and book_id:
            page_num = request.args.get('page_num', 1, type=int)
            result = execute_pg_function('api_shortcuts_book_page', book_id, page_num)
            return jsonify(result)
            
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action or missing parameters',
                'valid_actions': ['list', 'summary', 'toc', 'random_page', 'construct', 'page'],
                'parameters': {
                    'list': 'limit, page',
                    'summary': 'id (required)',
                    'toc': 'id (required)',
                    'random_page': 'id (required)',
                    'construct': 'id (required)',
                    'page': 'id (required), page_num'
                }
            }), 400
            
    except Exception as e:
        logger.error(f"V4 Books error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@books_bp.route('/api/shortcuts/books')
@require_auth  
def shortcuts_books():
    """iOS Shortcuts optimized books endpoint"""
    try:
        book_id = request.args.get('id', type=int)
        action = request.args.get('action', 'summary')
        chapter = request.args.get('chapter', type=int)
        page = request.args.get('page', type=int)
        
        if not book_id:
            return jsonify({
                'success': False,
                'error': 'Book ID required',
                'usage': '/api/shortcuts/books?id=123&action=summary'
            }), 400
        
        # Handle chapter navigation (navigate to first page of chapter)
        if chapter:
            # Get the page number for the first chunk of the specified chapter
            from .database import get_db
            with get_db() as conn:
                with conn.cursor() as cur:
                    # Find the page number of the first chunk in this chapter
                    cur.execute("""
                        WITH numbered_chunks AS (
                            SELECT chunk_id, chapter_number, 
                                   ROW_NUMBER() OVER (ORDER BY chunk_id) as page_num
                            FROM chunks 
                            WHERE book_id = %s
                        )
                        SELECT page_num 
                        FROM numbered_chunks
                        WHERE chapter_number = %s
                        ORDER BY page_num
                        LIMIT 1
                    """, (book_id, chapter))
                    row = cur.fetchone()
                    if row:
                        page_num = row[0]
                        result = execute_pg_function('api_shortcuts_book_page', book_id, page_num)
                        return jsonify(result)
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Chapter {chapter} not found in book {book_id}'
                        }), 404
        
        # Handle page navigation
        elif page:
            result = execute_pg_function('api_shortcuts_book_page', book_id, page)
            return jsonify(result)
            
        # Route to PostgreSQL functions
        elif action == 'summary':
            result = execute_pg_function('api_shortcuts_book_summary', book_id)
        elif action == 'toc':
            result = execute_pg_function('api_shortcuts_book_toc', book_id)
        elif action == 'random_page':
            result = execute_pg_function('api_shortcuts_book_random_page', book_id)
        elif action == 'construct':
            result = execute_pg_function('api_shortcuts_book_construct', book_id)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid action',
                'valid_actions': ['summary', 'toc', 'random_page', 'construct'],
                'parameters': {
                    'chapter': 'Navigate to first page of chapter N',
                    'page': 'Navigate to specific page N'
                }
            }), 400
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Shortcuts books error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500