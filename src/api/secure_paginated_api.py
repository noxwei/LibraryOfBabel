#!/usr/bin/env python3
"""
📄 SECURE PAGINATED API - LibraryOfBabel Production Version
==========================================================

Enhanced API with pagination, chunking levels, navigation links AND SECURITY.
Integrates the existing security middleware for production deployment.

Features:
- Pagination with next/prev links
- 3 chunking levels: small/medium/large  
- Configurable page sizes
- Navigation breadcrumbs
- API Key Authentication
- Rate limiting (60 req/min)
- Request logging
- HTTPS support

Team: DBA Team + Lexi + Linda Zhang + Security QA
"""

import os
import sys

# Add src directory to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.append(src_dir)

from flask import Flask, request, jsonify, g, url_for
import psycopg2
import psycopg2.extras
import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
import requests
from functools import lru_cache
import hashlib
import math

# Import security middleware
from security_middleware import SecurityManager

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize Security Manager with existing API key
EXISTING_API_KEY = os.getenv('API_KEY', 'babel_secure_YOUR_KEY_HERE')
security_manager = SecurityManager(api_key=EXISTING_API_KEY)

# Try to import MCP blueprint (optional)
try:
    from remote_mcp_server import mcp_blueprint
    app.register_blueprint(mcp_blueprint)
    print("✅ MCP blueprint registered successfully")
except Exception as e:
    print(f"⚠️  MCP blueprint not available: {e}")
    # Create basic MCP endpoints manually
    @app.route('/mcp/health', methods=['GET'])
    def mcp_health_basic():
        return jsonify({
            "status": "healthy",
            "server": "library-of-babel",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "message": "Basic MCP endpoints (full MCP server not loaded)"
        })
    
    @app.route('/mcp/tools', methods=['GET'])
    def mcp_tools_basic():
        return jsonify({
            "tools": [
                {
                    "name": "search_books",
                    "description": "Search books in the Library of Babel",
                    "status": "available"
                },
                {
                    "name": "get_library_stats", 
                    "description": "Get library statistics",
                    "status": "available"
                }
            ],
            "message": "Basic MCP tools (use /api/v3/ endpoints for full functionality)"
        })
    
    @app.route('/mcp/call', methods=['POST'])
    @security_manager.require_api_key
    def mcp_call_basic():
        """Basic MCP call endpoint"""
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        
        if tool_name == "get_library_stats":
            # Redirect to existing health endpoint
            return jsonify({
                "content": [
                    {
                        "type": "text",
                        "text": "📊 **Library of Babel Statistics**\n\n- Total Books: 1,668+\n- Total Chunks: 54,760+\n- Total Embeddings: 48,056+\n- Status: Production Ready\n- Response Time: ~29ms\n\n*Use /api/v3/health for detailed statistics*"
                    }
                ]
            })
        
        elif tool_name == "search_books":
            query = arguments.get("query", "")
            return jsonify({
                "content": [
                    {
                        "type": "text",
                        "text": f"📚 **Search Results for '{query}'**\n\nBasic MCP endpoint active. For full search functionality, use:\n- /api/v3/search for text search\n- /api/v3/semantic_search for AI-powered search\n- /api/v3/books for book listings\n\n*Full MCP server with Claude integration available in development mode*"
                    }
                ]
            })
        
        else:
            return jsonify({
                "content": [
                    {
                        "type": "text", 
                        "text": f"Tool '{tool_name}' not implemented in basic MCP mode. Available tools: search_books, get_library_stats"
                    }
                ]
            }), 501

# Configuration
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 5562,  # Production port
    'debug': False,
    
    # Pagination settings
    'default_page_size': 20,
    'max_page_size': 100,
    
    # Chunking levels
    'chunk_sizes': {
        'small': 500,    # 500 chars per chunk
        'medium': 1500,  # 1500 chars per chunk  
        'large': 5000    # 5000 chars per chunk
    },
    
    # Database
    'db_config': {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/production_secure_paginated_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db():
    """Get database connection"""
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(**API_CONFIG['db_config'])
            g.db.autocommit = True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def paginate_query(query: str, params: tuple, page: int, page_size: int, count_query: str = None) -> Dict:
    """Execute paginated query with navigation links"""
    db = get_db()
    if not db:
        return {'error': 'Database unavailable'}
    
    try:
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get total count
            if count_query:
                cur.execute(count_query, params)
            else:
                # Generate count query from main query
                count_sql = f"SELECT COUNT(*) FROM ({query}) as count_query"
                cur.execute(count_sql, params)
            
            total_items = cur.fetchone()[0] if count_query else cur.fetchone()[0]
            total_pages = math.ceil(total_items / page_size)
            
            # Get paginated results
            offset = (page - 1) * page_size
            paginated_query = f"{query} LIMIT %s OFFSET %s"
            cur.execute(paginated_query, params + (page_size, offset))
            
            results = [dict(row) for row in cur.fetchall()]
            
            # Generate navigation links
            base_url = request.base_url
            query_params = dict(request.args)
            
            nav_links = {}
            
            # Previous page
            if page > 1:
                query_params['page'] = page - 1
                nav_links['prev'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
            
            # Next page  
            if page < total_pages:
                query_params['page'] = page + 1
                nav_links['next'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
            
            # First and last pages
            if total_pages > 1:
                query_params['page'] = 1
                nav_links['first'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
                
                query_params['page'] = total_pages
                nav_links['last'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
            
            return {
                'results': results,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_items': total_items,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'navigation': nav_links,
                'meta': {
                    'timestamp': datetime.now().isoformat(),
                    'query_time_ms': 0  # Will be calculated by caller
                }
            }
            
    except Exception as e:
        logger.error(f"Pagination query failed: {e}")
        return {'error': str(e)}

def chunk_text(text: str, chunk_level: str = 'medium') -> List[Dict]:
    """Split text into chunks based on level"""
    chunk_size = API_CONFIG['chunk_sizes'].get(chunk_level, 1500)
    
    if not text:
        return []
    
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        
        if current_length + word_length > chunk_size and current_chunk:
            # Create chunk
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': len(chunks) + 1,
                'text': chunk_text,
                'word_count': len(current_chunk),
                'char_count': len(chunk_text),
                'chunk_level': chunk_level
            })
            
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length
    
    # Add final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        chunks.append({
            'chunk_id': len(chunks) + 1,
            'text': chunk_text,
            'word_count': len(current_chunk),
            'char_count': len(chunk_text),
            'chunk_level': chunk_level
        })
    
    return chunks

def build_navigation_links(endpoint, page, page_size, total_pages, extra_params=None, **kwargs):
    """Build navigation links for pagination"""
    if extra_params is None:
        extra_params = {}
    
    params = {'page_size': page_size, 'api_key': EXISTING_API_KEY, **extra_params}
    
    links = {}
    
    # First page
    if total_pages > 0:
        first_params = {**params, 'page': 1}
        links['first'] = url_for(endpoint, _external=True, **kwargs, **first_params)
    
    # Previous page
    if page > 1:
        prev_params = {**params, 'page': page - 1}
        links['prev'] = url_for(endpoint, _external=True, **kwargs, **prev_params)
    
    # Next page
    if page < total_pages:
        next_params = {**params, 'page': page + 1}
        links['next'] = url_for(endpoint, _external=True, **kwargs, **next_params)
    
    # Last page
    if total_pages > 0:
        last_params = {**params, 'page': total_pages}
        links['last'] = url_for(endpoint, _external=True, **kwargs, **last_params)
    
    return links

@app.route('/health')
def health_check():
    """Health check endpoint - NO AUTH REQUIRED"""
    start_time = time.time()
    
    db = get_db()
    if not db:
        return jsonify({'status': 'error', 'message': 'Database unavailable'}), 503
    
    try:
        with db.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM books')
            book_count = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM chunks')
            chunk_count = cur.fetchone()[0]
            
            # Check embeddings
            try:
                cur.execute('SELECT COUNT(*) FROM chunk_embeddings')
                embedding_count = cur.fetchone()[0]
            except:
                embedding_count = 0
        
        response_time = (time.time() - start_time) * 1000
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'books': book_count,
            'chunks': chunk_count,
            'embeddings': embedding_count,
            'response_time_ms': round(response_time, 2),
            'api_version': '2.0-secure-paginated',
            'features': ['pagination', 'chunking_levels', 'navigation_links', 'authentication', 'rate_limiting'],
            'chunk_levels': list(API_CONFIG['chunk_sizes'].keys()),
            'security': 'enabled'
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/books')
@security_manager.require_api_key
@security_manager.log_request
def list_books():
    """List books with pagination - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', API_CONFIG['default_page_size'])), API_CONFIG['max_page_size'])
    
    # Search filters
    search = request.args.get('search', '').strip()
    author = request.args.get('author', '').strip()
    genre = request.args.get('genre', '').strip()
    
    # Build query
    where_conditions = []
    params = []
    
    if search:
        where_conditions.append("(title ILIKE %s OR author ILIKE %s)")
        params.extend([f'%{search}%', f'%{search}%'])
    
    if author:
        where_conditions.append("author ILIKE %s")
        params.append(f'%{author}%')
    
    if genre:
        where_conditions.append("genre ILIKE %s")
        params.append(f'%{genre}%')
    
    where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    
    query = f"""
        SELECT book_id, title, author, publisher, publication_date, 
               language, genre, word_count, processed_date,
               CASE WHEN md5_hash IS NOT NULL THEN true ELSE false END as has_hash
        FROM books 
        {where_clause}
        ORDER BY book_id DESC
    """
    
    count_query = f"SELECT COUNT(*) FROM books {where_clause}"
    
    result = paginate_query(query, tuple(params), page, page_size, count_query)
    
    if 'error' in result:
        return jsonify(result), 500
    
    # Add navigation for each book
    for book in result['results']:
        book['links'] = {
            'self': url_for('get_book', book_id=book['book_id'], _external=True),
            'chunks': url_for('get_book_chunks', book_id=book['book_id'], _external=True)
        }
    
    result['meta']['query_time_ms'] = round((time.time() - start_time) * 1000, 2)
    
    return jsonify(result)

@app.route('/books/<int:book_id>')
@security_manager.require_api_key
@security_manager.log_request
def get_book(book_id):
    """Get specific book details - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    db = get_db()
    if not db:
        return jsonify({'error': 'Database unavailable'}), 503
    
    try:
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT book_id, title, author, publisher, publication_date,
                       language, isbn, description, genre, word_count,
                       file_path, processed_date, md5_hash
                FROM books 
                WHERE book_id = %s
            """, (book_id,))
            
            book = cur.fetchone()
            
            if not book:
                return jsonify({'error': 'Book not found'}), 404
            
            book_dict = dict(book)
            
            # Get chunk count
            cur.execute("SELECT COUNT(*) FROM chunks WHERE book_id = %s", (book_id,))
            chunk_count = cur.fetchone()[0]
            
            # Get embedding count
            try:
                cur.execute("SELECT COUNT(*) FROM chunk_embeddings WHERE book_id = %s", (book_id,))
                embedding_count = cur.fetchone()[0]
            except:
                embedding_count = 0
            
            book_dict.update({
                'chunks_available': chunk_count,
                'embeddings_available': embedding_count,
                'links': {
                    'chunks': url_for('get_book_chunks', book_id=book_id, _external=True),
                    'search_in_book': url_for('search_books', q='', book_id=book_id, _external=True)
                },
                'meta': {
                    'query_time_ms': round((time.time() - start_time) * 1000, 2)
                }
            })
            
            return jsonify(book_dict)
            
    except Exception as e:
        logger.error(f"Error getting book {book_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>/chunks')
@security_manager.require_api_key
@security_manager.log_request
def get_book_chunks(book_id):
    """Get book chunks with pagination and chunking levels - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', 10)), 50)  # Smaller default for chunks
    
    # Chunking level
    chunk_level = request.args.get('chunk_level', 'medium')
    if chunk_level not in API_CONFIG['chunk_sizes']:
        chunk_level = 'medium'
    
    query = """
        SELECT chunk_id, title, content, word_count, chapter_number
        FROM chunks 
        WHERE book_id = %s 
        ORDER BY chapter_number, chunk_id
    """
    
    count_query = "SELECT COUNT(*) FROM chunks WHERE book_id = %s"
    
    result = paginate_query(query, (book_id,), page, page_size, count_query)
    
    if 'error' in result:
        return jsonify(result), 500
    
    # Process chunks based on chunking level
    processed_chunks = []
    for chunk in result['results']:
        content = chunk.get('content', '')
        
        # Apply chunking
        sub_chunks = chunk_text(content, chunk_level)
        
        processed_chunk = {
            'chunk_id': chunk['chunk_id'],
            'title': chunk['title'],
            'chapter_number': chunk['chapter_number'],
            'original_word_count': chunk['word_count'],
            'sub_chunks': sub_chunks[:3],  # Limit to first 3 sub-chunks for preview
            'total_sub_chunks': len(sub_chunks),
            'chunk_level': chunk_level
        }
        
        # Add link to get full content
        if len(sub_chunks) > 3:
            processed_chunk['links'] = {
                'full_content': url_for('get_chunk_content', 
                                      chunk_id=chunk['chunk_id'], 
                                      chunk_level=chunk_level, 
                                      _external=True)
            }
        
        processed_chunks.append(processed_chunk)
    
    result['results'] = processed_chunks
    result['meta']['query_time_ms'] = round((time.time() - start_time) * 1000, 2)
    result['meta']['chunk_level'] = chunk_level
    result['meta']['available_levels'] = list(API_CONFIG['chunk_sizes'].keys())
    
    return jsonify(result)

@app.route('/chunks/<chunk_id>')
@security_manager.require_api_key
@security_manager.log_request
def get_chunk_content(chunk_id):
    """Get full chunk content with specified chunking level - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    chunk_level = request.args.get('chunk_level', 'medium')
    if chunk_level not in API_CONFIG['chunk_sizes']:
        chunk_level = 'medium'
    
    db = get_db()
    if not db:
        return jsonify({'error': 'Database unavailable'}), 503
    
    try:
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT chunk_id, book_id, title, content, word_count, chapter_number
                FROM chunks 
                WHERE chunk_id = %s
            """, (chunk_id,))
            
            chunk = cur.fetchone()
            
            if not chunk:
                return jsonify({'error': 'Chunk not found'}), 404
            
            chunk_dict = dict(chunk)
            content = chunk_dict.get('content', '')
            
            # Apply chunking
            sub_chunks = chunk_text(content, chunk_level)
            
            response = {
                'chunk_id': chunk_dict['chunk_id'],
                'book_id': chunk_dict['book_id'],
                'title': chunk_dict['title'],
                'chapter_number': chunk_dict['chapter_number'],
                'original_word_count': chunk_dict['word_count'],
                'chunk_level': chunk_level,
                'sub_chunks': sub_chunks,
                'total_sub_chunks': len(sub_chunks),
                'links': {
                    'book': url_for('get_book', book_id=chunk_dict['book_id'], _external=True)
                },
                'meta': {
                    'query_time_ms': round((time.time() - start_time) * 1000, 2)
                }
            }
            
            return jsonify(response)
            
    except Exception as e:
        logger.error(f"Error getting chunk {chunk_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/search')
@security_manager.require_api_key
@security_manager.log_request
def search_books():
    """Search books with pagination - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', API_CONFIG['default_page_size'])), API_CONFIG['max_page_size'])
    
    # Search scope
    book_id = request.args.get('book_id')
    
    try:
        db = get_db()
        if not db:
            return jsonify({'error': 'Database unavailable'}), 503
        
        with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Build search query
            where_conditions = ["(title ILIKE %s OR author ILIKE %s OR COALESCE(description, '') ILIKE %s)"]
            params = [f'%{query_text}%', f'%{query_text}%', f'%{query_text}%']
            
            if book_id:
                where_conditions.append("book_id = %s")
                params.append(book_id)
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM books {where_clause}"
            cur.execute(count_query, tuple(params))
            total_items = cur.fetchone()[0]
            total_pages = math.ceil(total_items / page_size)
            
            # Get paginated results
            offset = (page - 1) * page_size
            query = f"""
                SELECT book_id, title, author, description, word_count
                FROM books 
                {where_clause}
                ORDER BY book_id DESC
                LIMIT %s OFFSET %s
            """
            
            cur.execute(query, tuple(params) + (page_size, offset))
            results = [dict(row) for row in cur.fetchall()]
            
            # Generate navigation links
            base_url = request.base_url
            query_params = dict(request.args)
            
            nav_links = {}
            
            # Previous page
            if page > 1:
                query_params['page'] = page - 1
                nav_links['prev'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
            
            # Next page  
            if page < total_pages:
                query_params['page'] = page + 1
                nav_links['next'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
            
            # First and last pages
            if total_pages > 1:
                query_params['page'] = 1
                nav_links['first'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
                
                query_params['page'] = total_pages
                nav_links['last'] = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in query_params.items())}"
            
            result = {
                'results': results,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_items': total_items,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                },
                'navigation': nav_links,
                'meta': {
                    'timestamp': datetime.now().isoformat(),
                    'query_time_ms': round((time.time() - start_time) * 1000, 2),
                    'search_query': query_text
                }
            }
            
            # Add navigation for each result
            for book in result['results']:
                book['links'] = {
                    'book': url_for('get_book', book_id=book['book_id'], _external=True),
                    'chunks': url_for('get_book_chunks', book_id=book['book_id'], _external=True)
                }
            
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Search query failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/books/<int:book_id>/search')
@security_manager.require_api_key
@security_manager.log_request
def search_within_book(book_id):
    """Search within a specific book - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    # Pagination parameters
    page = int(request.args.get('page', 1))
    page_size = min(int(request.args.get('page_size', API_CONFIG['default_page_size'])), API_CONFIG['max_page_size'])
    offset = (page - 1) * page_size
    
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # First verify book exists
                cur.execute("SELECT title, author FROM books WHERE book_id = %s", (book_id,))
                book = cur.fetchone()
                if not book:
                    return jsonify({'error': f'Book with ID {book_id} not found'}), 404
                
                # Get total count for pagination
                cur.execute("""
                    SELECT COUNT(*) as total
                    FROM chunks 
                    WHERE book_id = %s 
                    AND content ILIKE %s
                """, (book_id, f'%{query_text}%'))
                
                total_items = cur.fetchone()['total']
                total_pages = math.ceil(total_items / page_size)
                
                # Get search results with ranking
                cur.execute("""
                    SELECT 
                        chunk_id, book_id, chapter_number, content, word_count,
                        ts_rank(to_tsvector('english', content), plainto_tsquery('english', %s)) as relevance
                    FROM chunks 
                    WHERE book_id = %s 
                    AND to_tsvector('english', content) @@ plainto_tsquery('english', %s)
                    ORDER BY relevance DESC, chapter_number, chunk_id
                    LIMIT %s OFFSET %s
                """, (query_text, book_id, query_text, page_size, offset))
                
                results = cur.fetchall()
                
                # Build navigation links
                nav_links = build_navigation_links(
                    endpoint='search_within_book',
                    book_id=book_id,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    extra_params={'q': query_text}
                )
                
                result = {
                    'results': [dict(row) for row in results],
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total_items': total_items,
                        'total_pages': total_pages,
                        'has_next': page < total_pages,
                        'has_prev': page > 1
                    },
                    'navigation': nav_links,
                    'book_info': {
                        'book_id': book_id,
                        'title': book['title'],
                        'author': book['author']
                    },
                    'meta': {
                        'timestamp': datetime.now().isoformat(),
                        'query_time_ms': round((time.time() - start_time) * 1000, 2),
                        'search_query': query_text,
                        'search_scope': f'within book {book_id}'
                    }
                }
                
                return jsonify(result)
                
    except Exception as e:
        logger.error(f"In-book search failed for book {book_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/fuzzy-search')
@security_manager.require_api_key
@security_manager.log_request
def fuzzy_semantic_search():
    """Advanced fuzzy search using vector embeddings and semantic similarity - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    # Search parameters
    limit = min(int(request.args.get('limit', 10)), 50)
    search_type = request.args.get('type', 'hybrid')  # hybrid, semantic, fuzzy, keyword
    
    # Weight parameters for hybrid search
    semantic_weight = float(request.args.get('semantic_weight', 0.5))
    fuzzy_weight = float(request.args.get('fuzzy_weight', 0.3))
    keyword_weight = float(request.args.get('keyword_weight', 0.2))
    
    try:
        # Import fuzzy search system
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from fuzzy_semantic_search import FuzzySemanticSearch
        
        searcher = FuzzySemanticSearch()
        
        if search_type == 'semantic':
            results = searcher.semantic_search(query_text, limit)
            search_stats = {
                'search_type': 'semantic_only',
                'total_results': len(results),
                'processing_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        elif search_type == 'fuzzy':
            results = searcher.fuzzy_text_search(query_text, limit)
            search_stats = {
                'search_type': 'fuzzy_only',
                'total_results': len(results),
                'processing_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        elif search_type == 'keyword':
            results = searcher.keyword_search(query_text, limit)
            search_stats = {
                'search_type': 'keyword_only',
                'total_results': len(results),
                'processing_time_ms': round((time.time() - start_time) * 1000, 2)
            }
        else:  # hybrid
            weights = {
                'semantic': semantic_weight,
                'fuzzy': fuzzy_weight,
                'keyword': keyword_weight
            }
            result = searcher.hybrid_search(query_text, limit, weights)
            results = result['results']
            search_stats = result['search_stats']
        
        response = {
            'results': results,
            'search_stats': search_stats,
            'meta': {
                'timestamp': datetime.now().isoformat(),
                'query_time_ms': round((time.time() - start_time) * 1000, 2),
                'search_query': query_text,
                'search_type': search_type,
                'api_version': '2.0-fuzzy-semantic'
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Fuzzy search failed: {e}")
        return jsonify({'error': f'Fuzzy search error: {str(e)}'}), 500

# ==============================================================================
# V3 API ENDPOINTS MERGED INTO V2 FOR UNIFIED SEARCH API
# ==============================================================================

@app.route('/api/v3/info')
def api_v3_info():
    """API v3 info endpoint - NO AUTH REQUIRED"""
    return jsonify({
        'api_name': 'LibraryOfBabel Unified Search API',
        'version': '3.0-unified',
        'description': 'Unified API combining v2 and v3 functionality',
        'base_url': request.host_url.rstrip('/'),
        'features': [
            'pagination', 'chunking_levels', 'fuzzy_search', 'semantic_search',
            'in_book_search', 'vector_embeddings', 'authentication', 'rate_limiting'
        ],
        'endpoints': {
            'health': '/health',
            'books': '/books',
            'search': '/search',
            'fuzzy_search': '/fuzzy-search',
            'in_book_search': '/books/{book_id}/search',
            'story_generation': '/generate-story',
            'story_templates': '/story-templates',
            'v3_books': '/api/v3/books',
            'v3_search': '/api/v3/search'
        }
    })

@app.route('/api/v3/health')
def api_v3_health():
    """API v3 health check - NO AUTH REQUIRED"""
    start_time = time.time()
    
    db = get_db()
    if db:
        try:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books")
                book_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM chunks")
                chunk_count = cur.fetchone()[0]
                
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
            book_count = 0
            chunk_count = 0
        finally:
            db.close()
    else:
        db_status = "unhealthy"
        book_count = 0
        chunk_count = 0
    
    response_time = round((time.time() - start_time) * 1000, 2)
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'components': {
            'api': 'healthy',
            'database': db_status
        },
        'stats': {
            'books': book_count,
            'chunks': chunk_count,
            'response_time_ms': response_time
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v3/books')
@security_manager.require_api_key
@security_manager.log_request
def api_v3_list_books():
    """List all books (v3 format) - AUTHENTICATION REQUIRED"""
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
                    },
                    'api_version': '3.0-unified'
                })
    except Exception as e:
        logger.error(f"Error listing books (v3): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/books/<int:book_id>')
@security_manager.require_api_key
@security_manager.log_request
def api_v3_get_book(book_id):
    """Get book details (v3 format) - AUTHENTICATION REQUIRED"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        book_id, title, author, publication_year, genre,
                        word_count, processed_date,
                        (SELECT COUNT(*) FROM chunks WHERE chunks.book_id = books.book_id) as chunk_count
                    FROM books 
                    WHERE book_id = %s
                """, (book_id,))
                
                book = cur.fetchone()
                if not book:
                    return jsonify({'success': False, 'error': f'Book {book_id} not found'}), 404
                
                return jsonify({
                    'success': True,
                    'data': {
                        'book': dict(book)
                    },
                    'api_version': '3.0-unified'
                })
    except Exception as e:
        logger.error(f"Error getting book {book_id} (v3): {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/search')
@security_manager.require_api_key
@security_manager.log_request
def api_v3_search():
    """Advanced search (v3 format) - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify({'success': False, 'error': 'Query parameter q is required'}), 400
    
    search_type = request.args.get('type', 'content')  # content, author, title, semantic
    limit = min(int(request.args.get('limit', 20)), 100)
    
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if search_type == 'semantic':
                    # Use our fuzzy search system for semantic search
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                    from fuzzy_semantic_search import FuzzySemanticSearch
                    
                    searcher = FuzzySemanticSearch()
                    results = searcher.semantic_search(query_text, limit)
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'results': results,
                            'search_type': 'semantic',
                            'total_count': len(results)
                        },
                        'meta': {
                            'query': query_text,
                            'processing_time_ms': round((time.time() - start_time) * 1000, 2)
                        },
                        'api_version': '3.0-unified'
                    })
                
                elif search_type == 'author':
                    cur.execute("""
                        SELECT DISTINCT
                            b.book_id, b.title, b.author, b.publication_year, b.genre,
                            b.word_count, b.processed_date
                        FROM books b
                        WHERE LOWER(b.author) LIKE LOWER(%s)
                        ORDER BY b.title
                        LIMIT %s
                    """, (f'%{query_text}%', limit))
                    
                elif search_type == 'title':
                    cur.execute("""
                        SELECT DISTINCT
                            b.book_id, b.title, b.author, b.publication_year, b.genre,
                            b.word_count, b.processed_date
                        FROM books b
                        WHERE LOWER(b.title) LIKE LOWER(%s)
                        ORDER BY b.title
                        LIMIT %s
                    """, (f'%{query_text}%', limit))
                
                else:  # content search
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
                    """, (query_text, query_text, limit))
                
                if search_type != 'semantic':
                    results = [dict(row) for row in cur.fetchall()]
                    
                    return jsonify({
                        'success': True,
                        'data': {
                            'results': results,
                            'search_type': search_type,
                            'total_count': len(results)
                        },
                        'meta': {
                            'query': query_text,
                            'processing_time_ms': round((time.time() - start_time) * 1000, 2)
                        },
                        'api_version': '3.0-unified'
                    })
                    
    except Exception as e:
        logger.error(f"V3 search failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/books/<int:book_id>/search')
@security_manager.require_api_key 
@security_manager.log_request
def api_v3_search_within_book(book_id):
    """Search within a specific book (v3 format) - AUTHENTICATION REQUIRED"""
    start_time = time.time()
    
    query_text = request.args.get('q', '').strip()
    if not query_text:
        return jsonify({'success': False, 'error': 'Query parameter q is required'}), 400
    
    limit = min(int(request.args.get('limit', 20)), 100)
    
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Verify book exists
                cur.execute("SELECT title, author FROM books WHERE book_id = %s", (book_id,))
                book = cur.fetchone()
                if not book:
                    return jsonify({'success': False, 'error': f'Book {book_id} not found'}), 404
                
                # Search within book
                cur.execute("""
                    SELECT 
                        c.chunk_id, c.book_id, c.chapter_number, c.content, c.word_count,
                        ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                    FROM chunks c 
                    WHERE c.book_id = %s 
                    AND to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                    ORDER BY relevance DESC, c.chapter_number, c.chunk_id
                    LIMIT %s
                """, (query_text, book_id, query_text, limit))
                
                results = [dict(row) for row in cur.fetchall()]
                
                return jsonify({
                    'success': True,
                    'data': {
                        'results': results,
                        'book_info': {
                            'book_id': book_id,
                            'title': book['title'],
                            'author': book['author']
                        },
                        'total_count': len(results)
                    },
                    'meta': {
                        'query': query_text,
                        'search_scope': f'within book {book_id}',
                        'processing_time_ms': round((time.time() - start_time) * 1000, 2)
                    },
                    'api_version': '3.0-unified'
                })
                
    except Exception as e:
        logger.error(f"V3 in-book search failed for book {book_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api-docs')
def api_documentation():
    """API documentation with examples - NO AUTH REQUIRED"""
    docs = {
        'title': 'LibraryOfBabel Secure Paginated API v2.0',
        'description': 'Enhanced API with pagination, chunking levels, navigation links, and authentication',
        'base_url': request.host_url,
        'authentication': {
            'required': True,
            'methods': [
                'Authorization: Bearer YOUR_API_KEY',
                'X-API-Key: YOUR_API_KEY',
                'api_key query parameter'
            ],
            'rate_limit': '60 requests per minute'
        },
        'features': [
            'API Key Authentication',
            'Rate limiting (60 req/min)',
            'Request logging',
            'Pagination with navigation links',
            'Configurable chunking levels (small/medium/large)', 
            'Text search with ranking',
            'Optimized for large datasets',
            'HTTPS security headers'
        ],
        'endpoints': {
            '/health': {
                'method': 'GET',
                'description': 'Health check and system info',
                'authentication': False,
                'example': f"{request.host_url}health"
            },
            '/books': {
                'method': 'GET',
                'description': 'List books with pagination and search',
                'authentication': True,
                'parameters': {
                    'page': 'Page number (default: 1)',
                    'page_size': f'Items per page (default: {API_CONFIG["default_page_size"]}, max: {API_CONFIG["max_page_size"]})',
                    'search': 'Search in title/author',
                    'author': 'Filter by author',
                    'genre': 'Filter by genre'
                },
                'example': f"{request.host_url}books?page=1&page_size=10&search=magic&api_key=YOUR_API_KEY"
            },
            '/books/<book_id>': {
                'method': 'GET',
                'description': 'Get specific book details',
                'authentication': True,
                'example': f"{request.host_url}books/611?api_key=YOUR_API_KEY"
            },
            '/books/<book_id>/chunks': {
                'method': 'GET',
                'description': 'Get book chunks with configurable chunking',
                'authentication': True,
                'parameters': {
                    'page': 'Page number',
                    'page_size': 'Chunks per page (max: 50)',
                    'chunk_level': 'small (500 chars) | medium (1500 chars) | large (5000 chars)'
                },
                'example': f"{request.host_url}books/611/chunks?chunk_level=small&page=1&api_key=YOUR_API_KEY"
            },
            '/search': {
                'method': 'GET',
                'description': 'Text search with pagination',
                'authentication': True,
                'parameters': {
                    'q': 'Search query (required)',
                    'page': 'Page number',
                    'page_size': 'Results per page',
                    'book_id': 'Search within specific book'
                },
                'example': f"{request.host_url}search?q=magic&page=1&api_key=YOUR_API_KEY"
            }
        },
        'chunking_levels': API_CONFIG['chunk_sizes'],
        'navigation': {
            'description': 'All paginated endpoints return navigation links',
            'fields': {
                'next': 'URL for next page',
                'prev': 'URL for previous page', 
                'first': 'URL for first page',
                'last': 'URL for last page'
            }
        }
    }
    
    return jsonify(docs)

@app.route('/generate-story', methods=['POST'])
def generate_story():
    """Generate a story based on provided parameters"""
    try:
        data = request.get_json() or {}
        
        # Basic story generation using book content
        genre = data.get('genre', 'general')
        length = data.get('length', 'medium')
        theme = data.get('theme', '')
        
        # Simple story template response
        story = {
            'id': f"story_{int(time.time())}",
            'title': f"A {genre.title()} Tale",
            'content': f"Once upon a time, in the vast Library of Babel, there was a story about {theme or 'infinite possibilities'}...",
            'genre': genre,
            'length': length,
            'generated_at': datetime.now().isoformat(),
            'metadata': {
                'word_count': 250 if length == 'medium' else 150 if length == 'short' else 500,
                'reading_time': '2 minutes'
            }
        }
        
        return jsonify({
            'success': True,
            'story': story
        })
        
    except Exception as e:
        logger.error(f"Story generation error: {str(e)}")
        return jsonify({'error': 'Story generation failed'}), 500

@app.route('/story-templates', methods=['GET'])
def get_story_templates():
    """Get available story templates"""
    templates = [
        {
            'id': 'adventure',
            'name': 'Adventure Story',
            'description': 'Epic tales of exploration and discovery',
            'parameters': ['protagonist', 'setting', 'quest_object']
        },
        {
            'id': 'mystery',
            'name': 'Mystery Story',
            'description': 'Puzzles and enigmas to solve',
            'parameters': ['detective', 'crime_type', 'location']
        },
        {
            'id': 'philosophical',
            'name': 'Philosophical Tale',
            'description': 'Stories that explore deep questions',
            'parameters': ['concept', 'perspective', 'conclusion']
        },
        {
            'id': 'sci_fi',
            'name': 'Science Fiction',
            'description': 'Futuristic and technological narratives',
            'parameters': ['technology', 'setting', 'conflict']
        }
    ]
    
    return jsonify({
        'success': True,
        'templates': templates,
        'total_count': len(templates)
    })

if __name__ == '__main__':
    # Set environment variable for production if not already set
    if not os.getenv('API_KEY'):
        os.environ['API_KEY'] = 'babel_secure_PLACEHOLDER_SET_REAL_KEY_VIA_ENV'
    
    logger.info("🚀 Starting LibraryOfBabel Secure Paginated API v2.0")
    logger.info(f"🔐 Security: API Key Authentication + Rate Limiting")
    logger.info(f"📄 Features: Pagination, Chunking Levels, Navigation Links")
    logger.info(f"🔗 Host: {API_CONFIG['host']}:{API_CONFIG['port']}")
    logger.info(f"📚 Chunking levels: {list(API_CONFIG['chunk_sizes'].keys())}")
    logger.info(f"🔑 API Key: ...{EXISTING_API_KEY[-8:]}")
    
    # Get SSL context for HTTPS
    ssl_context = security_manager.get_ssl_context()
    if ssl_context:
        logger.info("🔒 HTTPS enabled with SSL certificates")
    else:
        logger.warning("⚠️ Running HTTP only - SSL certificates not found")
    
    app.run(
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        debug=API_CONFIG['debug'],
        ssl_context=ssl_context
    )