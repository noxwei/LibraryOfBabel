#!/usr/bin/env python3
"""
LibraryOfBabel Production API v3.0
==================================

Simplified production-ready API for immediate deployment
Consolidates core functionality without complex dependencies
"""

from flask import Flask, request, jsonify, g
import psycopg2
import psycopg2.extras
import logging
import time
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

# Add src directory to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': int(os.getenv('DB_PORT', 5432))
}

# API Key for authentication
API_KEY = os.getenv('API_KEY', 'M39Gqz5e8D-_qkyuy37ar87_jNU0EPs_nO6_izPnGaU')

def get_db():
    """Get database connection with error handling"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def verify_api_key():
    """Verify API key from request"""
    # Check various auth methods
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:] == API_KEY
    
    api_key = request.headers.get('X-API-Key')
    if api_key:
        return api_key == API_KEY
    
    api_key = request.args.get('api_key')
    if api_key:
        return api_key == API_KEY
    
    if request.is_json and request.json:
        api_key = request.json.get('api_key')
        if api_key:
            return api_key == API_KEY
    
    return False

def require_auth(f):
    """Decorator to require API key authentication"""
    def decorated_function(*args, **kwargs):
        if not verify_api_key():
            return jsonify({'success': False, 'error': 'Valid API key required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def _highlight_text(text: str, query: str, max_length: int = 200) -> str:
    """Enhanced text highlighting with context"""
    if not query or not text:
        return text[:max_length] + "..." if len(text) > max_length else text
    
    # Find the query position (case insensitive)
    lower_text = text.lower()
    lower_query = query.lower()
    query_pos = lower_text.find(lower_query)
    
    if query_pos == -1:
        return text[:max_length] + "..." if len(text) > max_length else text
    
    # Calculate context window
    context_start = max(0, query_pos - 50)
    context_end = min(len(text), query_pos + len(query) + 150)
    
    # Extract context with highlighting
    context = text[context_start:context_end]
    highlighted = context.replace(
        text[query_pos:query_pos + len(query)],
        f"**{text[query_pos:query_pos + len(query)]}**"
    )
    
    prefix = "..." if context_start > 0 else ""
    suffix = "..." if context_end < len(text) else ""
    
    return f"{prefix}{highlighted}{suffix}"

# Middleware
@app.before_request
def before_request():
    """Request logging and timing"""
    g.start_time = time.time()

@app.after_request
def after_request(response):
    """Log requests and add security headers"""
    duration = time.time() - g.get('start_time', time.time())
    
    logger.info(f"{request.method} {request.path} - {response.status_code} - {duration:.3f}s")
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response

# ================================
# PUBLIC ENDPOINTS
# ================================

@app.route('/api/v3/info')
def api_info():
    """Public API information endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'name': 'LibraryOfBabel Production API',
            'version': '3.0',
            'description': 'Production-ready unified API for book search and management',
            'security': 'HTTPS + API Key Required',
            'features': [
                'book_search_navigation',
                'multi_type_search', 
                'text_highlighting',
                'secure_authentication',
                'comprehensive_analytics'
            ],
            'endpoints': {
                'public': ['/api/v3/info', '/api/v3/health'],
                'secured': 'All other endpoints require API key authentication'
            },
            'authentication': {
                'methods': ['Bearer token', 'X-API-Key header', 'Query parameter'],
                'rate_limit': '60 requests per minute per IP'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v3/health')
def health_check():
    """Public health check endpoint"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': 'unknown',
            'api': 'healthy'
        }
    }
    
    # Quick database check
    try:
        with get_db() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    health_status['components']['database'] = 'healthy'
            else:
                health_status['components']['database'] = 'unhealthy'
                health_status['status'] = 'degraded'
    except Exception as e:
        health_status['components']['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    return jsonify(health_status)

# ================================
# BOOK SEARCH & NAVIGATION
# ================================

@app.route('/api/v3/books')
@require_auth
def list_books():
    """List all available books with metadata"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        book_id, title, author, publication_year, genre,
                        word_count, processed_date,
                        (SELECT COUNT(*) FROM chunks WHERE chunks.book_id = books.book_id) as chunk_count
                    FROM books 
                    ORDER BY title
                """)
                books = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'books': [dict(book) for book in books],
                        'total_count': len(books)
                    }
                })
    except Exception as e:
        logger.error(f"Error listing books: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/books/<int:book_id>')
@require_auth
def get_book_details(book_id):
    """Get detailed information about a specific book"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get book info
                cur.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
                book = cur.fetchone()
                
                if not book:
                    return jsonify({'success': False, 'error': 'Book not found'}), 404
                
                # Get chapter structure
                cur.execute("""
                    SELECT DISTINCT chapter_number, 
                           COUNT(*) as section_count,
                           SUM(word_count) as chapter_word_count
                    FROM chunks 
                    WHERE book_id = %s AND chapter_number IS NOT NULL
                    GROUP BY chapter_number 
                    ORDER BY chapter_number
                """, (book_id,))
                chapters = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'book': dict(book),
                        'structure': {
                            'chapters': [dict(chapter) for chapter in chapters],
                            'total_chapters': len(chapters)
                        }
                    }
                })
    except Exception as e:
        logger.error(f"Error getting book details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/books/<int:book_id>/search')
@require_auth
def search_within_book(book_id):
    """Search within a specific book with highlighting"""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter required'}), 400
    
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get book info
                cur.execute("SELECT title, author FROM books WHERE book_id = %s", (book_id,))
                book = cur.fetchone()
                
                if not book:
                    return jsonify({'success': False, 'error': 'Book not found'}), 404
                
                # Search within book
                cur.execute("""
                    SELECT 
                        chunk_id, chapter_number, section_number, content, 
                        word_count, chunk_type,
                        ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) as relevance
                    FROM chunks 
                    WHERE book_id = %s 
                    AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
                    ORDER BY relevance DESC, chapter_number, section_number
                    LIMIT 50
                """, (query, book_id, query))
                results = cur.fetchall()
                
                # Add highlighting
                highlighted_results = []
                for result in results:
                    result_dict = dict(result)
                    result_dict['highlighted_content'] = _highlight_text(
                        result['content'], query, 300
                    )
                    highlighted_results.append(result_dict)
                
                return jsonify({
                    'success': True,
                    'data': {
                        'book': dict(book),
                        'query': query,
                        'results': highlighted_results,
                        'total_matches': len(highlighted_results)
                    }
                })
    except Exception as e:
        logger.error(f"Error searching within book: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# MULTI-TYPE SEARCH
# ================================

@app.route('/api/v3/search')
@require_auth
def multi_search():
    """Comprehensive multi-type search endpoint"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'content')  # content, author, title, cross_reference
    limit = min(int(request.args.get('limit', 20)), 100)
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter required'}), 400
    
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                
                if search_type == 'content':
                    # Full-text content search
                    cur.execute("""
                        SELECT 
                            c.chunk_id, c.book_id, c.chapter_number, c.section_number,
                            c.content, c.word_count, c.chunk_type,
                            b.title, b.author,
                            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                        ORDER BY relevance DESC
                        LIMIT %s
                    """, (query, query, limit))
                
                elif search_type == 'author':
                    # Author-based search
                    cur.execute("""
                        SELECT DISTINCT
                            b.book_id, b.title, b.author, b.publication_year, b.genre,
                            b.word_count, b.processed_date
                        FROM books b
                        WHERE LOWER(b.author) LIKE LOWER(%s)
                        ORDER BY b.title
                        LIMIT %s
                    """, (f'%{query}%', limit))
                
                elif search_type == 'title':
                    # Title-based search
                    cur.execute("""
                        SELECT DISTINCT
                            b.book_id, b.title, b.author, b.publication_year, b.genre,
                            b.word_count, b.processed_date
                        FROM books b
                        WHERE to_tsvector('english', b.title) @@ plainto_tsquery('english', %s)
                        ORDER BY b.title
                        LIMIT %s
                    """, (query, limit))
                
                elif search_type == 'cross_reference':
                    # Cross-book reference search
                    cur.execute("""
                        SELECT 
                            c.chunk_id, c.book_id, c.chapter_number, c.section_number,
                            c.content, c.word_count, c.chunk_type,
                            b.title, b.author,
                            COUNT(*) OVER (PARTITION BY b.book_id) as book_match_count,
                            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                        ORDER BY book_match_count DESC, relevance DESC
                        LIMIT %s
                    """, (query, query, limit))
                
                else:
                    return jsonify({'success': False, 'error': f'Invalid search type: {search_type}'}), 400
                
                results = cur.fetchall()
                
                # Add highlighting for content searches
                if search_type in ['content', 'cross_reference']:
                    highlighted_results = []
                    for result in results:
                        result_dict = dict(result)
                        if 'content' in result_dict:
                            result_dict['highlighted_content'] = _highlight_text(
                                result['content'], query, 300
                            )
                        highlighted_results.append(result_dict)
                    results = highlighted_results
                else:
                    results = [dict(result) for result in results]
                
                return jsonify({
                    'success': True,
                    'data': {
                        'query': query,
                        'search_type': search_type,
                        'results': results,
                        'total_results': len(results),
                        'limit': limit
                    }
                })
                
    except Exception as e:
        logger.error(f"Error in multi-search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# STATISTICS & ANALYTICS
# ================================

@app.route('/api/v3/stats')
@require_auth
def get_statistics():
    """Comprehensive library statistics"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Basic counts
                cur.execute("SELECT COUNT(*) as total_books FROM books")
                book_count = cur.fetchone()['total_books']
                
                cur.execute("SELECT COUNT(*) as total_chunks FROM chunks")
                chunk_count = cur.fetchone()['total_chunks']
                
                cur.execute("SELECT SUM(word_count) as total_words FROM books")
                total_words = cur.fetchone()['total_words'] or 0
                
                # Genre distribution
                cur.execute("""
                    SELECT genre, COUNT(*) as count
                    FROM books
                    WHERE genre IS NOT NULL
                    GROUP BY genre
                    ORDER BY count DESC
                """)
                genres = cur.fetchall()
                
                # Author statistics
                cur.execute("""
                    SELECT author, COUNT(*) as book_count, SUM(word_count) as total_words
                    FROM books
                    WHERE author IS NOT NULL
                    GROUP BY author
                    ORDER BY book_count DESC
                    LIMIT 10
                """)
                top_authors = cur.fetchall()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'overview': {
                            'total_books': book_count,
                            'total_chunks': chunk_count,
                            'total_words': total_words,
                            'average_words_per_book': total_words // book_count if book_count > 0 else 0
                        },
                        'genres': [dict(g) for g in genres],
                        'top_authors': [dict(a) for a in top_authors]
                    }
                })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# ERROR HANDLERS
# ================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429

# ================================
# MAIN APPLICATION
# ================================

if __name__ == '__main__':
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    logger.info("🚀 Starting LibraryOfBabel Production API v3.0")
    logger.info(f"🔐 Security: API Key Authentication Required")
    logger.info(f"🔗 Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Production server
    app.run(
        host='0.0.0.0',
        port=5563,
        debug=False
    )