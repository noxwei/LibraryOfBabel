#!/usr/bin/env python3
"""
🔐 Secure LibraryOfBabel Book Search API
HTTPS + API Key Authentication + Rate Limiting
"""

from flask import Flask, request, jsonify, g
import psycopg2
import psycopg2.extras
import logging
import re
import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import our security middleware
sys.path.append(os.path.dirname(__file__))
from security_middleware import require_api_key, log_request, get_ssl_context, create_public_endpoint, security_manager

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

class BookSearchEngine:
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def get_db(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def search_within_book(self, book_id: int, query: str, highlight: bool = True) -> Dict[str, Any]:
        """Search for text within a specific book with optional highlighting"""
        conn = self.get_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get book information
            cursor.execute("""
                SELECT book_id, title, author, publication_year, word_count
                FROM books 
                WHERE book_id = %s
            """, (book_id,))
            
            book_info = cursor.fetchone()
            if not book_info:
                return {"error": f"Book with ID {book_id} not found"}
            
            # Search within book chunks
            cursor.execute("""
                SELECT 
                    chunk_id, chunk_type, chapter_number, section_number,
                    content, word_count, start_position, end_position,
                    ts_rank(search_vector, plainto_tsquery('english', %s)) as relevance
                FROM chunks 
                WHERE book_id = %s 
                AND search_vector @@ plainto_tsquery('english', %s)
                ORDER BY relevance DESC, chapter_number, section_number
            """, (query, book_id, query))
            
            chunks = cursor.fetchall()
            
            results = []
            for chunk in chunks:
                content = chunk['content']
                
                # Add highlighting if requested
                if highlight:
                    highlighted_content = self._highlight_text(content, query)
                else:
                    highlighted_content = content
                
                result = {
                    'chunk_id': chunk['chunk_id'],
                    'chunk_type': chunk['chunk_type'],
                    'chapter_number': chunk['chapter_number'],
                    'section_number': chunk['section_number'],
                    'word_count': chunk['word_count'],
                    'relevance_score': round(float(chunk['relevance']), 4),
                    'highlighted_content': highlighted_content
                }
                results.append(result)
            
            return {
                'book_info': dict(book_info),
                'query': query,
                'total_matches': len(results),
                'results': results
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            conn.close()
    
    def _highlight_text(self, text: str, query: str) -> str:
        """Add HTML highlighting to search matches"""
        import re
        # Split query into individual terms
        terms = query.lower().split()
        
        highlighted = text
        for term in terms:
            # Use regex for case-insensitive highlighting
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', highlighted)
        
        return highlighted

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize search engine
search_engine = BookSearchEngine()

# Apply logging to all requests
@app.before_request
@log_request
def before_request():
    pass

# Public endpoint (no auth required) - for basic info
@app.route('/api/secure/info')
@create_public_endpoint
def api_info():
    """Public endpoint showing API information"""
    return jsonify({
        'success': True,
        'data': {
            'name': 'LibraryOfBabel Secure Book Search API',
            'version': '1.0',
            'security': 'HTTPS + API Key Required',
            'authentication': 'Required for all endpoints except /info and /ca-cert',
            'endpoints': {
                'public': ['/api/secure/info', '/api/secure/ca-cert'],
                'authenticated': [
                    '/api/secure/books/list',
                    '/api/secure/books/search/<book_id>',
                    '/api/secure/books/outline/<book_id>',
                    '/api/secure/books/chapter/<book_id>/<chapter>',
                    '/api/secure/books/search-across'
                ]
            },
            'auth_methods': [
                'Authorization: Bearer <api_key>',
                'X-API-Key: <api_key>',
                'Query parameter: ?api_key=<api_key>'
            ],
            'certificate_info': {
                'ca_certificate': '/api/secure/ca-cert',
                'instructions': 'Download and install the CA certificate in your browser for zero SSL warnings'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/ca-cert')
@create_public_endpoint
def download_ca_cert():
    """Download CA certificate for browser installation - PUBLIC"""
    ca_cert_path = security_manager.get_ca_certificate_path()
    
    if ca_cert_path and os.path.exists(ca_cert_path):
        try:
            with open(ca_cert_path, 'r') as f:
                ca_cert_content = f.read()
            
            return app.response_class(
                ca_cert_content,
                mimetype='application/x-pem-file',
                headers={
                    'Content-Disposition': 'attachment; filename=libraryofbabel-ca.crt',
                    'Content-Type': 'application/x-x509-ca-cert'
                }
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to read CA certificate: {str(e)}'
            }), 500
    else:
        return jsonify({
            'success': False,
            'error': 'CA certificate not available',
            'message': 'Install instructions: For browsers to trust this API without warnings, download and install this CA certificate in your browser/system certificate store.'
        }), 404

# Secured endpoints
@app.route('/api/secure/books/list')
@require_api_key
def secure_list_books():
    """List all available books - SECURED"""
    conn = search_engine.get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT 
                book_id, title, author, publication_year, word_count,
                (SELECT COUNT(*) FROM chunks WHERE book_id = books.book_id) as total_chunks
            FROM books 
            WHERE book_id > 0
            ORDER BY title
        """)
        
        books = [dict(book) for book in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'data': {
                'books': books,
                'total_books': len(books)
            },
            'security': {'authenticated': True, 'api_key_valid': True},
            'timestamp': datetime.now().isoformat()
        })
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/secure/books/search/<int:book_id>')
@require_api_key
def secure_search_in_book(book_id):
    """Search within a specific book - SECURED"""
    query = request.args.get('q', '').strip()
    highlight = request.args.get('highlight', 'true').lower() == 'true'
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter "q" is required'
        }), 400
    
    start_time = time.time()
    result = search_engine.search_within_book(book_id, query, highlight)
    
    return jsonify({
        'success': 'error' not in result,
        'data': result,
        'security': {'authenticated': True, 'api_key_valid': True},
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/books/outline/<int:book_id>')
@require_api_key
def secure_get_book_outline(book_id):
    """Get book structure and outline - SECURED"""
    start_time = time.time()
    result = search_engine.get_book_outline(book_id)
    
    return jsonify({
        'success': 'error' not in result,
        'data': result,
        'security': {'authenticated': True, 'api_key_valid': True},
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/books/chapter/<int:book_id>/<int:chapter_number>')
@require_api_key
def secure_get_chapter_content(book_id, chapter_number):
    """Get full content of a specific chapter - SECURED"""
    start_time = time.time()
    result = search_engine.get_chapter_content(book_id, chapter_number)
    
    return jsonify({
        'success': 'error' not in result,
        'data': result,
        'security': {'authenticated': True, 'api_key_valid': True},
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/books/search-across')
@require_api_key
def secure_search_across_books():
    """Search across multiple books - SECURED"""
    query = request.args.get('q', '').strip()
    author = request.args.get('author', '').strip() or None
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Query parameter "q" is required'
        }), 400
    
    start_time = time.time()
    result = search_engine.search_across_books(query, author)
    
    return jsonify({
        'success': 'error' not in result,
        'data': result,
        'security': {'authenticated': True, 'api_key_valid': True},
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/secure/docs')
@require_api_key
def secure_get_api_docs():
    """Secure API documentation - SECURED"""
    docs = {
        'title': 'LibraryOfBabel Secure Book Search API',
        'version': '1.0',
        'security': {
            'https': True,
            'api_key_required': True,
            'rate_limit': '60 requests per minute per IP'
        },
        'authentication': {
            'methods': [
                'Authorization: Bearer <api_key>',
                'X-API-Key: <api_key>',
                'Query parameter: ?api_key=<api_key>'
            ],
            'example': 'curl -H "X-API-Key: YOUR_API_KEY" https://your-domain:5562/api/secure/books/list'
        },
        'endpoints': {
            'public': {
                'api_info': {
                    'path': '/api/secure/info',
                    'method': 'GET',
                    'description': 'API information (no auth required)',
                    'example': 'GET /api/secure/info'
                }
            },
            'authenticated': {
                'list_books': {
                    'path': '/api/secure/books/list',
                    'method': 'GET',
                    'description': 'List all available books',
                    'auth_required': True,
                    'example': 'GET /api/secure/books/list'
                },
                'search_in_book': {
                    'path': '/api/secure/books/search/<book_id>',
                    'method': 'GET',
                    'description': 'Search within a specific book with highlighting',
                    'auth_required': True,
                    'parameters': {
                        'q': 'Search query (required)',
                        'highlight': 'Enable highlighting (true/false, default: true)'
                    },
                    'example': 'GET /api/secure/books/search/123?q=consciousness&highlight=true'
                },
                'book_outline': {
                    'path': '/api/secure/books/outline/<book_id>',
                    'method': 'GET',
                    'description': 'Get book structure and chapter outline',
                    'auth_required': True,
                    'example': 'GET /api/secure/books/outline/123'
                },
                'chapter_content': {
                    'path': '/api/secure/books/chapter/<book_id>/<chapter_number>',
                    'method': 'GET',
                    'description': 'Get full content of specific chapter',
                    'auth_required': True,
                    'example': 'GET /api/secure/books/chapter/123/5'
                },
                'search_across_books': {
                    'path': '/api/secure/books/search-across',
                    'method': 'GET',
                    'description': 'Search across multiple books with optional author filter',
                    'auth_required': True,
                    'parameters': {
                        'q': 'Search query (required)',
                        'author': 'Author filter (optional)'
                    },
                    'example': 'GET /api/secure/books/search-across?q=power&author=Foucault'
                }
            }
        }
    }
    
    return jsonify({
        'success': True,
        'data': docs,
        'security': {'authenticated': True, 'api_key_valid': True},
        'timestamp': datetime.now().isoformat()
    })

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'message': 'Valid API key required',
        'security': {'authenticated': False}
    }), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': 'Forbidden',
        'message': 'Invalid API key',
        'security': {'authenticated': False}
    }), 403

@app.errorhandler(429)
def rate_limited(error):
    return jsonify({
        'success': False,
        'error': 'Rate Limit Exceeded',
        'message': 'Too many requests. Please slow down.',
        'security': {'rate_limited': True}
    }), 429

if __name__ == '__main__':
    print("🔐 Starting LibraryOfBabel Secure Book Search API...")
    print("🛡️  Security Features:")
    print("   • HTTPS/TLS encryption")
    print("   • API key authentication") 
    print("   • Rate limiting (60 req/min per IP)")
    print("   • Request logging & monitoring")
    print("")
    print("🔑 API Key: M39Gqz5e8D-_qkyuy37ar87_jNU0EPs_nO6_izPnGaU")
    print("")
    print("📚 Secure Endpoints:")
    print("   • GET /api/secure/info - API info (public)")
    print("   • GET /api/secure/books/list - List books (auth required)")
    print("   • GET /api/secure/books/search/<id>?q=query - Search book (auth required)")
    print("   • GET /api/secure/books/outline/<id> - Book outline (auth required)")
    print("   • GET /api/secure/books/chapter/<id>/<chapter> - Chapter content (auth required)")
    print("   • GET /api/secure/books/search-across?q=query - Cross-book search (auth required)")
    print("   • GET /api/secure/docs - API documentation (auth required)")
    print("")
    print("🌐 Starting secure server on https://localhost:5562")
    
    # Get SSL context
    ssl_context = get_ssl_context()
    
    if ssl_context:
        app.run(
            host='0.0.0.0', 
            port=5562, 
            debug=False,
            ssl_context=ssl_context
        )
    else:
        print("❌ SSL certificates not found! Starting without HTTPS...")
        app.run(host='0.0.0.0', port=5562, debug=False)