#!/usr/bin/env python3
"""
🔐 LibraryOfBabel Consolidated Secure API v3.0
HTTPS + API Key + Vector Embeddings + AI Features + Book Navigation + EPUB Upload

This is the SINGLE PRODUCTION API consolidating all previous implementations:
- secure_enhanced_api.py (base security + vector embeddings)
- book_search_api.py (book navigation + highlighting)
- secure_book_api.py (EPUB upload + enhanced security)
- enhanced_search_api.py (AI discovery features)
- hybrid_search_api.py (chunk navigation)
- search_api.py (multi-type search)
"""

from flask import Flask, request, jsonify, g, send_file
import psycopg2
import psycopg2.extras
import logging
import time
import json
import os
import sys
import threading
import tempfile
import zipfile
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from werkzeug.utils import secure_filename
import re

# Add src directory to path for imports
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_dir)

# Import security and core components
try:
    from security_middleware import SecurityManager
    from vector_embeddings import VectorEmbeddingGenerator
    from epub_processor import EpubProcessor
    from text_chunker import TextChunker
except ImportError as e:
    print(f"Core import error: {e}")
    sys.exit(1)

# Import AI components (optional)
try:
    from genre_classifier import GenreClassifier
    from serendipity_engine import SerendipityEngine
    from enhanced_librarian_agent import EnhancedLibrarianAgent
except ImportError as e:
    print(f"AI components not available: {e}")
    GenreClassifier = None
    SerendipityEngine = None
    EnhancedLibrarianAgent = None

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consolidated_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize security manager
security_manager = SecurityManager()

# Initialize components
try:
    vector_generator = VectorEmbeddingGenerator()
    epub_processor = EpubProcessor()
    text_chunker = TextChunker()
    logger.info("✅ Core components initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize core components: {e}")
    vector_generator = None
    epub_processor = None
    text_chunker = None

# Initialize AI components (optional)
genre_classifier = GenreClassifier() if GenreClassifier else None
serendipity_engine = SerendipityEngine() if SerendipityEngine else None
librarian_agent = EnhancedLibrarianAgent() if EnhancedLibrarianAgent else None

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': int(os.getenv('DB_PORT', 5432))
}

def get_db():
    """Get database connection with automatic cleanup"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

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
    """Security and logging middleware"""
    g.start_time = time.time()
    
    # Skip security for public endpoints
    public_endpoints = ['/api/v3/info', '/api/v3/health']
    if request.endpoint and any(request.path.startswith(ep) for ep in public_endpoints):
        return
    
    # Apply security to all other endpoints
    return security_manager.require_api_key(lambda: None)()

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
            'name': 'LibraryOfBabel Consolidated Secure API',
            'version': '3.0',
            'description': 'Unified API combining all search, AI, and navigation features',
            'security': 'HTTPS + API Key Required',
            'features': {
                'core': [
                    'book_search_navigation',
                    'chapter_content_access',
                    'epub_upload_processing',
                    'multi_type_search',
                    'text_highlighting'
                ],
                'ai_powered': [
                    'vector_embeddings',
                    'semantic_search',
                    'serendipity_discovery' if serendipity_engine else 'serendipity_discovery (unavailable)',
                    'genre_classification' if genre_classifier else 'genre_classification (unavailable)',
                    'reading_recommendations' if librarian_agent else 'reading_recommendations (unavailable)'
                ],
                'security': [
                    'https_encryption',
                    'api_key_authentication',
                    'rate_limiting',
                    'input_validation',
                    'secure_file_upload'
                ]
            },
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
            'vector_embeddings': bool(vector_generator),
            'epub_processor': bool(epub_processor),
            'ai_components': {
                'genre_classifier': bool(genre_classifier),
                'serendipity_engine': bool(serendipity_engine),
                'librarian_agent': bool(librarian_agent)
            }
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

@app.route('/api/v3/books/<int:book_id>/outline')
def get_book_outline(book_id):
    """Get comprehensive book outline with chapter summaries"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get book basic info
                cur.execute("SELECT title, author FROM books WHERE book_id = %s", (book_id,))
                book = cur.fetchone()
                
                if not book:
                    return jsonify({'success': False, 'error': 'Book not found'}), 404
                
                # Get chapter outlines with first chunk as summary
                cur.execute("""
                    SELECT 
                        chapter_number,
                        MIN(chunk_id) as first_chunk_id,
                        COUNT(*) as section_count,
                        SUM(word_count) as total_words,
                        STRING_AGG(
                            CASE WHEN section_number = 1 
                            THEN LEFT(content, 200) || '...'
                            END, ''
                        ) as chapter_preview
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
                        'outline': [dict(chapter) for chapter in chapters]
                    }
                })
    except Exception as e:
        logger.error(f"Error getting book outline: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/books/<int:book_id>/chapters/<int:chapter_number>')
def get_chapter_content(book_id, chapter_number):
    """Get full content for a specific chapter"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        chunk_id, section_number, content, word_count,
                        chunk_type
                    FROM chunks 
                    WHERE book_id = %s AND chapter_number = %s
                    ORDER BY section_number
                """, (book_id, chapter_number))
                chunks = cur.fetchall()
                
                if not chunks:
                    return jsonify({'success': False, 'error': 'Chapter not found'}), 404
                
                # Combine content
                full_content = "\n\n".join([chunk['content'] for chunk in chunks])
                
                return jsonify({
                    'success': True,
                    'data': {
                        'book_id': book_id,
                        'chapter_number': chapter_number,
                        'content': full_content,
                        'chunks': [dict(chunk) for chunk in chunks],
                        'total_words': sum(chunk['word_count'] for chunk in chunks)
                    }
                })
    except Exception as e:
        logger.error(f"Error getting chapter content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/books/<int:book_id>/search')
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
def multi_search():
    """Comprehensive multi-type search endpoint"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'content')  # content, author, title, semantic, cross_reference
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
                
                elif search_type == 'semantic' and vector_generator:
                    # Vector semantic search
                    try:
                        embedding = vector_generator.generate_embedding(query)
                        if embedding:
                            cur.execute("""
                                SELECT 
                                    c.chunk_id, c.book_id, c.chapter_number, c.section_number,
                                    c.content, c.word_count, c.chunk_type,
                                    b.title, b.author,
                                    (c.embedding_array <=> %s::vector) as similarity
                                FROM chunks c
                                JOIN books b ON c.book_id = b.book_id
                                WHERE c.embedding_array IS NOT NULL
                                ORDER BY similarity
                                LIMIT %s
                            """, (embedding, limit))
                        else:
                            return jsonify({'success': False, 'error': 'Failed to generate embedding'}), 500
                    except Exception as e:
                        logger.error(f"Semantic search error: {e}")
                        return jsonify({'success': False, 'error': 'Semantic search unavailable'}), 500
                
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
# CHUNK NAVIGATION
# ================================

@app.route('/api/v3/chunks/<int:chunk_id>')
def get_chunk_details(chunk_id):
    """Get detailed chunk information with navigation"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Get current chunk
                cur.execute("""
                    SELECT 
                        c.*, b.title, b.author
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.chunk_id = %s
                """, (chunk_id,))
                chunk = cur.fetchone()
                
                if not chunk:
                    return jsonify({'success': False, 'error': 'Chunk not found'}), 404
                
                # Get navigation info (previous/next chunks)
                cur.execute("""
                    SELECT chunk_id, chapter_number, section_number
                    FROM chunks
                    WHERE book_id = %s
                    AND (
                        (chapter_number = %s AND section_number < %s) OR
                        (chapter_number < %s)
                    )
                    ORDER BY chapter_number DESC, section_number DESC
                    LIMIT 1
                """, (chunk['book_id'], chunk['chapter_number'], chunk['section_number'], chunk['chapter_number']))
                prev_chunk = cur.fetchone()
                
                cur.execute("""
                    SELECT chunk_id, chapter_number, section_number
                    FROM chunks
                    WHERE book_id = %s
                    AND (
                        (chapter_number = %s AND section_number > %s) OR
                        (chapter_number > %s)
                    )
                    ORDER BY chapter_number ASC, section_number ASC
                    LIMIT 1
                """, (chunk['book_id'], chunk['chapter_number'], chunk['section_number'], chunk['chapter_number']))
                next_chunk = cur.fetchone()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'chunk': dict(chunk),
                        'navigation': {
                            'previous': dict(prev_chunk) if prev_chunk else None,
                            'next': dict(next_chunk) if next_chunk else None
                        }
                    }
                })
    except Exception as e:
        logger.error(f"Error getting chunk details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# EPUB UPLOAD & PROCESSING
# ================================

@app.route('/api/v3/upload/epub', methods=['POST'])
def upload_epub():
    """Secure EPUB file upload with background processing"""
    if 'epub_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['epub_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.epub'):
        return jsonify({'success': False, 'error': 'File must be an EPUB'}), 400
    
    try:
        # Save file securely
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        # Validate EPUB file
        if not zipfile.is_zipfile(file_path):
            return jsonify({'success': False, 'error': 'Invalid EPUB file format'}), 400
        
        # Generate processing job ID
        job_id = f"epub_{int(time.time())}_{filename.replace('.epub', '')}"
        
        # Start background processing
        processing_thread = threading.Thread(
            target=_process_epub_background,
            args=(file_path, filename, job_id)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
        return jsonify({
            'success': True,
            'data': {
                'job_id': job_id,
                'filename': filename,
                'status': 'processing',
                'message': 'EPUB upload successful, processing in background'
            }
        })
    
    except Exception as e:
        logger.error(f"Error uploading EPUB: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _process_epub_background(file_path: str, filename: str, job_id: str):
    """Background EPUB processing function"""
    try:
        logger.info(f"Starting background processing for {filename} (Job: {job_id})")
        
        if not epub_processor:
            logger.error("EPUB processor not available")
            return
        
        # Process EPUB
        result = epub_processor.process_epub(file_path)
        
        if result.get('success'):
            logger.info(f"Successfully processed {filename}")
            
            # Store in database
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO books (title, author, word_count, processed_date)
                        VALUES (%s, %s, %s, %s)
                        RETURNING book_id
                    """, (
                        result.get('title', filename),
                        result.get('author', 'Unknown'),
                        result.get('word_count', 0),
                        datetime.now()
                    ))
                    book_id = cur.fetchone()[0]
                    
                    # Store chunks
                    for chunk in result.get('chunks', []):
                        cur.execute("""
                            INSERT INTO chunks (book_id, chapter_number, section_number, content, word_count, chunk_type)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            book_id,
                            chunk.get('chapter_number'),
                            chunk.get('section_number'),
                            chunk.get('content'),
                            chunk.get('word_count'),
                            chunk.get('chunk_type')
                        ))
                    
                    conn.commit()
                    logger.info(f"Stored {filename} as book_id {book_id}")
        else:
            logger.error(f"Failed to process {filename}: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"Background processing error for {filename}: {e}")
    
    finally:
        # Clean up temporary file
        try:
            os.remove(file_path)
            os.rmdir(os.path.dirname(file_path))
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {e}")

# ================================
# AI-POWERED DISCOVERY
# ================================

@app.route('/api/v3/discovery/serendipity')
def serendipity_discovery():
    """AI-powered serendipitous discovery"""
    if not serendipity_engine:
        return jsonify({'success': False, 'error': 'Serendipity engine not available'}), 503
    
    theme = request.args.get('theme')
    mood = request.args.get('mood')
    limit = min(int(request.args.get('limit', 10)), 50)
    
    try:
        discoveries = serendipity_engine.discover_serendipitous_connections(
            theme=theme, mood=mood, limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': {
                'discoveries': discoveries,
                'parameters': {'theme': theme, 'mood': mood, 'limit': limit}
            }
        })
    except Exception as e:
        logger.error(f"Serendipity discovery error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/discovery/recommendations')
def reading_recommendations():
    """AI-powered reading recommendations"""
    if not librarian_agent:
        return jsonify({'success': False, 'error': 'Librarian agent not available'}), 503
    
    interests = request.args.get('interests', '')
    previous_books = request.args.getlist('previous_books')
    
    try:
        recommendations = librarian_agent.generate_reading_recommendations(
            interests=interests,
            previous_books=previous_books
        )
        
        return jsonify({
            'success': True,
            'data': {
                'recommendations': recommendations,
                'parameters': {'interests': interests, 'previous_books': previous_books}
            }
        })
    except Exception as e:
        logger.error(f"Reading recommendations error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# STATISTICS & ANALYTICS
# ================================

@app.route('/api/v3/stats')
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
# SYSTEM MANAGEMENT
# ================================

@app.route('/api/v3/system/detailed-health')
def detailed_system_health():
    """Comprehensive system health check with performance metrics"""
    start_time = time.time()
    
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {},
        'performance': {},
        'ai_services': {}
    }
    
    try:
        # Database health
        with get_db() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM books")
                    book_count = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM chunks")
                    chunk_count = cur.fetchone()[0]
                    
                    health_data['components']['database'] = {
                        'status': 'healthy',
                        'books': book_count,
                        'chunks': chunk_count
                    }
            else:
                health_data['components']['database'] = {'status': 'unhealthy'}
                health_data['status'] = 'degraded'
        
        # Vector embeddings health
        if vector_generator:
            embedding_stats = vector_generator.get_embedding_stats()
            health_data['components']['vector_embeddings'] = {
                'status': 'available',
                'stats': embedding_stats
            }
        else:
            health_data['components']['vector_embeddings'] = {'status': 'unavailable'}
        
        # AI services health
        health_data['ai_services'] = {
            'genre_classifier': 'available' if genre_classifier else 'unavailable',
            'serendipity_engine': 'available' if serendipity_engine else 'unavailable',
            'librarian_agent': 'available' if librarian_agent else 'unavailable'
        }
        
        # Performance metrics
        health_data['performance'] = {
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'memory_usage': 'not_implemented',
            'active_connections': 'not_implemented'
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        health_data['status'] = 'error'
        health_data['error'] = str(e)
    
    return jsonify(health_data)

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
    
    logger.info("🚀 Starting LibraryOfBabel Consolidated Secure API v3.0")
    logger.info(f"🔐 Security: HTTPS + API Key Authentication")
    logger.info(f"🤖 AI Components: {sum([bool(genre_classifier), bool(serendipity_engine), bool(librarian_agent)])}/3 available")
    logger.info(f"🔗 Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    
    # Production HTTPS server
    app.run(
        host='0.0.0.0',
        port=5563,
        debug=False,
        ssl_context='adhoc'  # Use Flask's adhoc SSL for development
    )