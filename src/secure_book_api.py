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
import requests
import json
import numpy as np
import uuid
import threading
import subprocess
from pathlib import Path
from werkzeug.utils import secure_filename
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

# Upload configuration
UPLOAD_CONFIG = {
    'upload_folder': '/Users/weixiangzhang/Local Dev/LibraryOfBabel/ebooks/downloads',
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'allowed_extensions': {'.epub', '.mobi', '.azw3', '.azw'},
    'processing_script': '/Users/weixiangzhang/Local Dev/LibraryOfBabel/src/automated_ebook_processor.py'
}

class BookSearchEngine:
    def __init__(self):
        self.db_config = DB_CONFIG
        self.ollama_url = "http://localhost:11434/api/embeddings"
        self.model_name = "nomic-embed-text"
    
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
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Ollama's nomic-embed-text model"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding', [])
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Ollama failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm_vec1 = np.linalg.norm(vec1)
            norm_vec2 = np.linalg.norm(vec2)
            
            if norm_vec1 == 0 or norm_vec2 == 0:
                return 0.0
            
            return dot_product / (norm_vec1 * norm_vec2)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def search_across_books(self, query: str, author: str = None, limit: int = 10) -> Dict[str, Any]:
        """Perform semantic search across all books using vector embeddings"""
        # Generate embedding for query
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            logger.error("Failed to generate embedding for query")
            return {"error": "Failed to generate embedding for query"}
        
        # Get all chunks with embeddings
        conn = self.get_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Build query with optional author filter
            if author:
                cursor.execute("""
                    SELECT 
                        c.chunk_id, c.content, c.embedding_array, c.chunk_type, c.chapter_number,
                        b.book_id, b.title, b.author, b.publication_year
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.embedding_array IS NOT NULL
                    AND LOWER(b.author) LIKE LOWER(%s)
                """, (f'%{author}%',))
            else:
                cursor.execute("""
                    SELECT 
                        c.chunk_id, c.content, c.embedding_array, c.chunk_type, c.chapter_number,
                        b.book_id, b.title, b.author, b.publication_year
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.embedding_array IS NOT NULL
                """)
            
            chunks = cursor.fetchall()
            logger.info(f"Found {len(chunks)} chunks with embeddings")
            
            # Calculate similarities
            results = []
            for chunk in chunks:
                similarity = self.cosine_similarity(query_embedding, chunk['embedding_array'])
                
                if similarity >= 0.1:  # Minimum similarity threshold
                    result = {
                        'chunk_id': chunk['chunk_id'],
                        'book_id': chunk['book_id'],
                        'title': chunk['title'],
                        'author': chunk['author'],
                        'publication_year': chunk['publication_year'],
                        'chunk_type': chunk['chunk_type'],
                        'chapter_number': chunk['chapter_number'],
                        'content_preview': chunk['content'][:300] + "..." if len(chunk['content']) > 300 else chunk['content'],
                        'similarity_score': round(similarity, 4)
                    }
                    results.append(result)
            
            # Sort by similarity score (highest first)
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return {
                'query': query,
                'author_filter': author,
                'total_matches': len(results),
                'results': results[:limit]
            }
            
        except psycopg2.Error as e:
            logger.error(f"Error performing semantic search: {e}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            conn.close()

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
                    '/api/secure/books/search-across',
                    '/api/secure/upload-epub'
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
                },
                'upload_epub': {
                    'path': '/api/secure/upload-epub',
                    'method': 'POST',
                    'description': 'Upload EPUB file for automated processing and database ingestion',
                    'auth_required': True,
                    'content_type': 'multipart/form-data',
                    'parameters': {
                        'file': 'EPUB file to upload (required)'
                    },
                    'supported_formats': ['.epub', '.mobi', '.azw3', '.azw'],
                    'max_file_size': '100MB',
                    'example': 'POST /api/secure/upload-epub (with file in form data)'
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

@app.route('/api/secure/upload-epub', methods=['POST'])
@require_api_key
def secure_upload_epub():
    """Upload EPUB file for processing - SECURED"""
    start_time = time.time()
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file provided',
            'message': 'Please include an EPUB file in the "file" parameter'
        }), 400
    
    file = request.files['file']
    
    # Check if file was actually selected
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected',
            'message': 'Please select a file to upload'
        }), 400
    
    # Validate file extension
    filename = secure_filename(file.filename)
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in UPLOAD_CONFIG['allowed_extensions']:
        return jsonify({
            'success': False,
            'error': 'Invalid file type',
            'message': f'Only {", ".join(UPLOAD_CONFIG["allowed_extensions"])} files are supported',
            'allowed_types': list(UPLOAD_CONFIG['allowed_extensions'])
        }), 400
    
    # Generate unique filename to prevent conflicts
    upload_id = str(uuid.uuid4())[:8]
    safe_filename = f"{upload_id}_{filename}"
    upload_path = Path(UPLOAD_CONFIG['upload_folder']) / safe_filename
    
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_CONFIG['upload_folder'], exist_ok=True)
        
        # Save file
        file.save(str(upload_path))
        
        # Check file size after saving
        file_size = upload_path.stat().st_size
        if file_size > UPLOAD_CONFIG['max_file_size']:
            # Remove file if too large
            upload_path.unlink()
            return jsonify({
                'success': False,
                'error': 'File too large',
                'message': f'File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({UPLOAD_CONFIG["max_file_size"] / 1024 / 1024}MB)',
                'max_size_mb': UPLOAD_CONFIG['max_file_size'] / 1024 / 1024
            }), 413
        
        # Start background processing
        def process_epub_async():
            """Process EPUB in background thread"""
            try:
                logger.info(f"Starting background processing for {safe_filename}")
                
                # Use virtual environment python if it exists
                venv_python = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/venv/bin/python"
                python_cmd = venv_python if Path(venv_python).exists() else "python3"
                
                # Run automated processor
                result = subprocess.run([
                    python_cmd,
                    UPLOAD_CONFIG['processing_script'],
                    '--single-file', str(upload_path)
                ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
                
                if result.returncode == 0:
                    logger.info(f"Successfully processed {safe_filename}")
                    # Move to processed directory
                    processed_dir = Path(UPLOAD_CONFIG['upload_folder']).parent / 'processed'
                    processed_dir.mkdir(exist_ok=True)
                    processed_path = processed_dir / safe_filename
                    shutil.move(str(upload_path), str(processed_path))
                else:
                    logger.error(f"Failed to process {safe_filename}: {result.stderr}")
                    # Move to failed directory
                    failed_dir = Path(UPLOAD_CONFIG['upload_folder']).parent / 'failed'
                    failed_dir.mkdir(exist_ok=True)
                    failed_path = failed_dir / safe_filename
                    shutil.move(str(upload_path), str(failed_path))
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Processing timeout for {safe_filename}")
            except Exception as e:
                logger.error(f"Processing error for {safe_filename}: {str(e)}")
        
        # Start processing in background thread
        processing_thread = threading.Thread(target=process_epub_async, daemon=True)
        processing_thread.start()
        
        return jsonify({
            'success': True,
            'data': {
                'upload_id': upload_id,
                'filename': filename,
                'safe_filename': safe_filename,
                'file_size_mb': round(file_size / 1024 / 1024, 2),
                'file_type': file_ext,
                'upload_path': str(upload_path),
                'status': 'uploaded',
                'processing_status': 'queued',
                'message': 'File uploaded successfully and queued for processing'
            },
            'security': {'authenticated': True, 'api_key_valid': True},
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        
        # Clean up file if it exists
        if upload_path.exists():
            try:
                upload_path.unlink()
            except:
                pass
        
        return jsonify({
            'success': False,
            'error': 'Upload failed',
            'message': str(e),
            'security': {'authenticated': True, 'api_key_valid': True}
        }), 500

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
    print("   • POST /api/secure/upload-epub - Upload EPUB for processing (auth required)")
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