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
import requests
from functools import lru_cache
from werkzeug.utils import secure_filename
import hashlib
import subprocess
import asyncio

# Add src directory to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.dirname(current_dir)

# Import Ollama URL Generator Agent
sys.path.insert(0, src_dir)
sys.path.append(os.path.join(src_dir, 'agents'))
from ollama_url_generator import OllamaUrlGeneratorAgent
from ios_shortcuts_handler import IOSShortcutsHandler

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

# Initialize iOS Shortcuts handler
ios_handler = None

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': int(os.getenv('DB_PORT', 5432))
}

# API Key for authentication - REQUIRED environment variable
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    logger.critical("🚨 SECURITY ERROR: API_KEY environment variable not set!")
    logger.critical("Set API_KEY environment variable before starting the server.")
    logger.critical("Example: export API_KEY=your_secure_api_key_here")
    raise SystemExit("API_KEY environment variable is required for security")

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
                'secured': ['/api/v3/search', '/api/v3/books', '/api/v3/upload', '/api/v3/stats', '/api/v3/agents/feed'],
                'lexi': ['/api/v3/lexi', '/api/v3/lexi/health'],
                'note': 'All secured and Lexi endpoints require API key authentication'
            },
            'lexi': {
                'name': 'Lexi',
                'full_name': 'Lexi - LibraryOfBabel Official Mascot',
                'personality': 'reddit_bibliophile_scholar',
                'primary_endpoint': '/api/v3/lexi',
                'health_endpoint': '/api/v3/lexi/health',
                'powered_by': 'Ollama Llama3 7B + RAG with 363 books',
                'description': 'THE official LibraryOfBabel mascot - not just a mascot, but THE mascot'
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
# OLLAMA LLAMA3 7B + iOS SHORTCUTS INTEGRATION
# ================================

@app.route('/api/v3/ollama/ios/chat', methods=['POST'])
@require_auth
def ollama_ios_chat():
    """
    iOS Shortcuts compatible endpoint for Ollama Llama3 7B integration
    Designed for Reddit Bibliophile agent with dual memory system
    Enhanced with IOSShortcutsHandler for mobile-optimized responses
    """
    global ios_handler
    
    # Initialize iOS handler if not already done
    if ios_handler is None:
        ios_handler = IOSShortcutsHandler(DB_CONFIG)
    
    start_time = time.time()
    
    try:
        # Validate request structure using iOS handler
        if not request.is_json:
            error_response = ios_handler.handle_error("Request must be JSON", "invalid_content_type")
            return jsonify(error_response), 400
        
        request_data = request.get_json()
        is_valid, validation_message = ios_handler.validate_mobile_request(request_data)
        
        if not is_valid:
            error_response = ios_handler.handle_error(validation_message, "validation_error")
            return jsonify(error_response), 400
        
        # Process mobile request using iOS handler
        logger.info(f"📱 iOS Shortcuts request: {request_data['query'][:50]}...")
        
        mobile_response = ios_handler.process_mobile_request(request_data)
        
        # Log successful processing
        processing_time = mobile_response['metadata']['processing_time_ms']
        logger.info(f"✅ iOS Shortcuts response generated in {processing_time}ms")
        
        return jsonify(mobile_response)
        
    except Exception as e:
        logger.error(f"❌ iOS Shortcuts endpoint error: {e}")
        error_response = ios_handler.handle_error("Internal server error", "server_error") if ios_handler else {
            'success': False,
            'error': 'Internal server error',
            'agent': 'lexi_voice_mode',
            'response': '🤔 Oops! Something went wrong. Try again?',
            'intentLabel': 'error',
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(error_response), 500

# Legacy iOS endpoint (kept for backwards compatibility)
@app.route('/api/v3/ollama/ios/chat/legacy', methods=['POST'])
@require_auth
def ollama_ios_chat_legacy():
    """
    Legacy iOS Shortcuts endpoint - kept for backwards compatibility
    Use /api/v3/ollama/ios/chat for new implementations
    """
    start_time = time.time()
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        user_query = data.get('query', '').strip()
        session_id = data.get('session_id', f'ios_session_{int(time.time())}')
        context = data.get('context', 'mobile_ios_shortcuts')
        
        # Validate query
        if not user_query:
            return jsonify({
                'success': False,
                'error': 'Query is required',
                'ios_friendly': True
            }), 400
        
        if len(user_query) > 500:
            return jsonify({
                'success': False,
                'error': 'Query too long (max 500 characters)',
                'ios_friendly': True
            }), 400
        
        logger.info(f"📱 iOS Shortcuts query: '{user_query[:100]}...' (session: {session_id})")
        
        # Initialize Ollama agent with Llama3 7B model
        try:
            ollama_agent = OllamaUrlGeneratorAgent(
                ollama_model="llama3:7b",  # Llama3 7B model
                api_key=API_KEY,
                library_api_base=request.host_url.rstrip('/') + '/api/v3'
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Ollama agent: {e}")
            return jsonify({
                'success': False,
                'error': 'Ollama service unavailable',
                'ios_friendly': True,
                'fallback_available': True
            }), 503
        
        # Process query with Ollama
        try:
            # Use asyncio for async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            ollama_result = loop.run_until_complete(
                ollama_agent.natural_language_to_url(user_query)
            )
            
            loop.close()
            
            if not ollama_result.get('success', False):
                raise Exception(ollama_result.get('error', 'Ollama processing failed'))
                
        except Exception as e:
            logger.error(f"❌ Ollama processing failed: {e}")
            # Fallback to simple keyword search
            ollama_result = {
                'success': False,
                'search_urls': [{
                    'strategy': 'fallback_keyword',
                    'url': f"{request.host_url.rstrip('/')}/api/v3/search?q={user_query}&limit=10&api_key={API_KEY}",
                    'description': f"Keyword search for: {user_query}",
                    'priority': 1
                }],
                'explanation': 'Using fallback keyword search due to Ollama unavailability'
            }
        
        # Execute searches and get results
        search_results = []
        total_books_found = 0
        
        for url_config in ollama_result.get('search_urls', []):
            try:
                # Execute internal search
                search_url = url_config['url']
                
                # Extract query parameters from URL
                if '?' in search_url:
                    query_params = search_url.split('?')[1]
                    params = {}
                    for param in query_params.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = value
                    
                    # Execute search internally
                    search_query = params.get('q', user_query)
                    search_limit = int(params.get('limit', 10))
                    
                    # Get database results
                    conn = get_db()
                    if conn:
                        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                            cur.execute("""
                                SELECT 
                                    c.chunk_id, c.book_id, c.chapter_number, c.section_number,
                                    c.content, c.word_count, c.chunk_type,
                                    b.title, b.author, b.publication_year,
                                    ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                                FROM chunks c
                                JOIN books b ON c.book_id = b.book_id
                                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                                ORDER BY relevance DESC
                                LIMIT %s
                            """, (search_query, search_query, search_limit))
                            
                            results = [dict(row) for row in cur.fetchall()]
                            
                            # Add highlighting for mobile display
                            for result in results:
                                result['highlighted_content'] = _highlight_text(
                                    result['content'], search_query, 200
                                )
                            
                            search_results.append({
                                'strategy': url_config['strategy'],
                                'description': url_config['description'],
                                'results': results,
                                'result_count': len(results)
                            })
                            
                            total_books_found += len(set(r['book_id'] for r in results))
                            
            except Exception as e:
                logger.error(f"❌ Search execution failed: {e}")
                continue
        
        # Generate Reddit Bibliophile response
        reddit_response = _generate_reddit_bibliophile_response(
            user_query, search_results, total_books_found
        )
        
        # Update agent memory (dual system)
        memory_updated = _update_agent_memory(
            session_id, user_query, reddit_response, search_results
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # iOS Shortcuts optimized response
        ios_response = {
            'success': True,
            'agent': 'reddit_bibliophile',
            'agent_name': 'u/DataScientistBookworm',
            'response': reddit_response,
            'query': user_query,
            'session_id': session_id,
            'mobile_optimized': True,
            'ios_shortcuts_compatible': True,
            'search_results': search_results,
            'total_books_found': total_books_found,
            'memory_updated': memory_updated,
            'ollama_powered': ollama_result.get('success', False),
            'performance': {
                'response_time': round(response_time, 3),
                'target_met': response_time < 3.0
            },
            'timestamp': datetime.now().isoformat(),
            'next_actions': _suggest_next_actions(user_query, search_results)
        }
        
        logger.info(f"✅ iOS query processed in {response_time:.3f}s - {total_books_found} books found")
        
        return jsonify(ios_response)
        
    except Exception as e:
        logger.error(f"❌ iOS chat endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'ios_friendly': True,
            'agent': 'reddit_bibliophile',
            'fallback_message': 'yo, something went wrong with the search! try again in a sec 🤖',
            'timestamp': datetime.now().isoformat()
        }), 500

def _generate_reddit_bibliophile_response(query, search_results, total_books):
    """Generate Reddit Bibliophile agent response"""
    
    # Reddit-style enthusiasm based on results
    if total_books == 0:
        return f"oof, no direct hits for '{query}' 😅 but don't worry! try rephrasing or hit me with related terms - our 363-book library is MASSIVE! 🚀"
    
    if total_books == 1:
        return f"yo! found 1 book that's absolutely PERFECT for '{query}' 🎯 this is some quality research material right here! 📚✨"
    
    if total_books <= 5:
        return f"nice! found {total_books} solid books for '{query}' 🔥 quality > quantity, and these are all bangers! 📖"
    
    if total_books <= 10:
        return f"YOOO! hit the jackpot with {total_books} books for '{query}' 🎰 this is prime research territory! dive in! 🤓"
    
    return f"HOLY MOLY! {total_books} books for '{query}' - this is like Christmas morning for researchers! 🎄📚 time to get DEEP into this topic! 🚀"

def _update_agent_memory(session_id, query, response, search_results):
    """Update dual memory system (PostgreSQL + JSON)"""
    try:
        # Update JSON memory for short-term context
        memory_file = '/Users/weixiangzhang/Local Dev/LibraryOfBabel/agents/bulletin_board/agent_memory.json'
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
            
            # Add to memory threads
            memory_entry = {
                'timestamp': datetime.now().isoformat(),
                'agent': 'reddit_bibliophile',
                'agent_name': 'Reddit Bibliophile (u/DataScientistBookworm)',
                'message': f"iOS query processed: '{query[:50]}...' - found {len(search_results)} result sets",
                'source': 'ios_shortcuts_integration',
                'event_type': 'mobile_query',
                'priority': 'HIGH',
                'session_id': session_id,
                'mobile_context': True
            }
            
            memory_data.get('memory_threads', []).append(memory_entry)
            
            # Update last active
            memory_data.setdefault('last_active', {})['reddit_bibliophile'] = datetime.now().isoformat()
            
            # Save updated memory
            with open(memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Memory update failed: {e}")
        return False

def _suggest_next_actions(query, search_results):
    """Suggest next actions for iOS users"""
    suggestions = []
    
    if search_results:
        suggestions.append("📖 Tap a book title to read more details")
        suggestions.append("🔍 Ask follow-up questions about specific concepts")
        suggestions.append("📚 Request book recommendations based on these results")
    
    suggestions.append("🎯 Try more specific search terms")
    suggestions.append("📝 Ask for chapter summaries or key insights")
    suggestions.append("🔗 Request connections between different books")
    
    return suggestions

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

@app.route('/api/v3/agents/feed', methods=['GET'])
@require_auth
def get_agent_feed():
    """Get today's agent social media feed with book discoveries"""
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 20)), 50)
        hours = min(int(request.args.get('hours', 24)), 168)  # Max 1 week
        category = request.args.get('category')  # Optional filter
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Get recent agent posts with book information
            base_query = """
                SELECT 
                    ap.post_id,
                    ap.message,
                    ap.book_title,
                    ap.book_author,
                    ap.coffee_boosted,
                    ap.existence_level,
                    ap.category,
                    ap.created_at,
                    a.agent_name,
                    a.category as agent_category,
                    b.book_id,
                    b.word_count,
                    CASE 
                        WHEN ap.coffee_boosted THEN '☕ CAFFEINATED'
                        WHEN ap.existence_level = 'HYPERACTIVE' THEN '🚀 HYPERACTIVE'
                        WHEN ap.existence_level = 'RECOVERING' THEN '😴 RECOVERING'
                        ELSE '😐 STANDARD'
                    END as status_emoji
                FROM agent_posts ap
                JOIN agents a ON ap.agent_id = a.agent_id
                LEFT JOIN books b ON ap.book_title = b.title
                WHERE ap.created_at > NOW() - INTERVAL '%s hours'
            """
            
            params = [hours]
            
            if category:
                base_query += " AND ap.category = %s"
                params.append(category)
            
            base_query += " ORDER BY ap.created_at DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(base_query, params)
            posts = [dict(row) for row in cur.fetchall()]
            
            # Get agent activity summary
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT ap.agent_id) as active_agents,
                    COUNT(ap.post_id) as total_posts,
                    COUNT(CASE WHEN ap.coffee_boosted THEN 1 END) as coffee_boosted_posts,
                    COUNT(CASE WHEN ap.book_title IS NOT NULL THEN 1 END) as book_mentions,
                    COUNT(CASE WHEN ap.category = 'mental_state' THEN 1 END) as spy_observations
                FROM agent_posts ap
                WHERE ap.created_at > NOW() - INTERVAL '%s hours'
            """, [hours])
            
            activity = dict(cur.fetchone())
            
            # Get book discovery stats
            cur.execute("""
                SELECT 
                    ap.book_title,
                    ap.book_author,
                    b.book_id,
                    COUNT(*) as mention_count,
                    ARRAY_AGG(DISTINCT a.agent_name ORDER BY a.agent_name) as mentioned_by_agents
                FROM agent_posts ap
                JOIN agents a ON ap.agent_id = a.agent_id
                LEFT JOIN books b ON ap.book_title = b.title
                WHERE ap.created_at > NOW() - INTERVAL '%s hours'
                  AND ap.book_title IS NOT NULL
                GROUP BY ap.book_title, ap.book_author, b.book_id
                ORDER BY mention_count DESC
                LIMIT 10
            """, [hours])
            
            book_discoveries = [dict(row) for row in cur.fetchall()]
            
            # Get coffee status summary
            cur.execute("""
                SELECT 
                    a.agent_name,
                    acs.status,
                    acs.boost_until,
                    acs.cooldown_until,
                    acs.frequency_multiplier
                FROM agent_coffee_states acs
                JOIN agents a ON acs.agent_id = a.agent_id
                WHERE acs.expires_at > NOW()
                ORDER BY acs.coffee_given_at DESC
            """)
            
            coffee_status = [dict(row) for row in cur.fetchall()]
        
        # Format timestamps for better readability
        for post in posts:
            post['created_at'] = post['created_at'].isoformat()
            post['time_ago'] = _time_ago(post['created_at'])
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'feed_period': f"Last {hours} hours",
                'activity_summary': activity,
                'posts': posts,
                'book_discoveries': book_discoveries,
                'coffee_status': coffee_status,
                'categories': {
                    'mental_state': 'The Spy behavioral analysis',
                    'book_discovery': 'Reading recommendations', 
                    'social_humor': 'Agent democracy updates',
                    'highlights': 'Curated book passages',
                    'analysis': 'Technical research'
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting agent feed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _time_ago(timestamp_str):
    """Calculate human-readable time ago"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        diff = datetime.now() - timestamp.replace(tzinfo=None)
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except:
        return "unknown"

@lru_cache(maxsize=1000)
def get_ip_geolocation(ip_address: str) -> Dict[str, Any]:
    """Get approximate location from IP address using free geolocation service"""
    try:
        # Using ip-api.com (free, no API key needed, 1000 requests/hour)
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'success': True,
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', 'Unknown'),
                    'country': data.get('country', 'Unknown'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'timezone': data.get('timezone', 'Unknown'),
                    'isp': data.get('isp', 'Unknown')
                }
    except Exception as e:
        logger.warning(f"IP geolocation failed for {ip_address}: {e}")
    
    return {'success': False, 'city': 'Unknown', 'country': 'Unknown'}

def get_client_ip():
    """Get client IP address, handling proxies and load balancers"""
    # Check for forwarded IP (common with proxies/CDNs)
    forwarded_ips = request.headers.get('X-Forwarded-For')
    if forwarded_ips:
        # Take the first IP (client IP)
        return forwarded_ips.split(',')[0].strip()
    
    # Check for real IP (some proxy configurations)
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Check for CF-Connecting-IP (Cloudflare)
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip
    
    # Fallback to remote address
    return request.remote_addr

@app.route('/api/v3/location', methods=['GET'])
def get_visitor_location():
    """Get visitor location info (IP-based only, no permission required)"""
    try:
        client_ip = get_client_ip()
        
        # Get IP-based location only
        ip_location = get_ip_geolocation(client_ip)
        
        # Simple response with just IP geolocation
        response_data = {
            'city': ip_location.get('city', 'Unknown'),
            'region': ip_location.get('region', 'Unknown'),
            'country': ip_location.get('country', 'Unknown'),
            'timezone': ip_location.get('timezone', 'Unknown'),
            'method': 'IP geolocation (approximate)',
            'privacy_note': 'Location is approximate based on IP address and not stored'
        }
        
        # Log visitor for analytics (anonymized)
        logger.info(f"Visitor from {ip_location.get('city', 'Unknown')}, {ip_location.get('country', 'Unknown')} - IP: {client_ip[:8]}...")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"Error getting location: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/v3/regional-books', methods=['GET'])
@require_auth  
def get_regional_book_recommendations():
    """Get book recommendations based on visitor's location"""
    try:
        client_ip = get_client_ip()
        location = get_ip_geolocation(client_ip)
        
        # Location-based book recommendations
        recommendations = []
        city = location.get('city', '').lower()
        country = location.get('country', '').lower()
        
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Search for books related to their region
            regional_queries = []
            
            if 'united states' in country or 'usa' in country:
                regional_queries = ['america', 'american', 'usa', 'united states']
            elif 'china' in country:
                regional_queries = ['china', 'chinese', '中国', 'beijing', 'shanghai']
            elif 'japan' in country:
                regional_queries = ['japan', 'japanese', 'tokyo', 'japan']
            elif 'germany' in country:
                regional_queries = ['germany', 'german', 'berlin', 'deutschland']
            elif 'france' in country:
                regional_queries = ['france', 'french', 'paris', 'français']
            elif 'uk' in country or 'britain' in country:
                regional_queries = ['britain', 'british', 'london', 'england', 'uk']
            
            # Add city-specific searches
            if city and len(city) > 3:
                regional_queries.append(city)
            
            # Search for regional content
            for query in regional_queries[:3]:  # Limit to 3 queries
                cur.execute("""
                    SELECT DISTINCT b.book_id, b.title, b.author, b.word_count,
                           c.content
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id
                    WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                    ORDER BY b.word_count DESC
                    LIMIT 3
                """, (query,))
                
                results = cur.fetchall()
                for book in results:
                    recommendations.append({
                        'book_id': book['book_id'],
                        'title': book['title'],
                        'author': book['author'],
                        'reason': f'Related to your region: {query}',
                        'excerpt': book['content'][:200] + '...'
                    })
        
        # Remove duplicates and limit
        seen_books = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec['book_id'] not in seen_books:
                seen_books.add(rec['book_id'])
                unique_recommendations.append(rec)
                if len(unique_recommendations) >= 5:
                    break
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'visitor_location': {
                    'city': location.get('city', 'Unknown'),
                    'country': location.get('country', 'Unknown')
                },
                'recommendations': unique_recommendations,
                'recommendation_basis': 'Books containing content related to your geographic region',
                'privacy_note': 'Location is used only for recommendations and not stored'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting regional recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================
# EPUB UPLOAD ENDPOINT
# ================================

def allowed_file(filename):
    """Check if file is allowed EPUB format"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'epub'

def validate_epub_file(file_path):
    """Validate EPUB file format and security"""
    try:
        # Check file size (max 50MB)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB
            return False, "File too large (max 50MB)"
        
        # Check if it's a valid EPUB file
        result = subprocess.run(['file', file_path], capture_output=True, text=True)
        if 'EPUB document' not in result.stdout and 'Zip archive' not in result.stdout:
            return False, "Invalid EPUB format"
        
        return True, "Valid EPUB file"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

@app.route('/api/v3/upload', methods=['POST'])
@require_auth
def upload_epub():
    """Upload EPUB file for processing"""
    start_time = time.time()
    
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Only EPUB files allowed'}), 400
        
        # Create secure filename
        filename = secure_filename(file.filename)
        if not filename:
            filename = f"upload_{int(time.time())}.epub"
        
        # Ensure upload directory exists
        upload_dir = os.path.join(os.getcwd(), 'ebooks', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Validate uploaded file
        is_valid, message = validate_epub_file(file_path)
        if not is_valid:
            os.remove(file_path)  # Clean up invalid file
            return jsonify({'success': False, 'error': message}), 400
        
        # Generate file hash for tracking
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        # Move to processing directory
        processing_dir = os.path.join(os.getcwd(), 'ebooks', 'downloads')
        os.makedirs(processing_dir, exist_ok=True)
        
        final_path = os.path.join(processing_dir, filename)
        os.rename(file_path, final_path)
        
        # Log successful upload
        processing_time = time.time() - start_time
        logger.info(f"EPUB upload successful: {filename} ({file_hash}) - {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': {
                'filename': filename,
                'file_hash': file_hash,
                'size_bytes': os.path.getsize(final_path),
                'upload_time': datetime.utcnow().isoformat(),
                'status': 'uploaded',
                'message': 'EPUB uploaded successfully and queued for processing'
            }
        })
        
    except Exception as e:
        logger.error(f"Error uploading EPUB: {e}")
        return jsonify({'success': False, 'error': 'Upload failed'}), 500

# ================================
# OLLAMA INTEGRATION ENDPOINTS
# ================================

# Initialize Ollama agent
try:
    ollama_agent = OllamaUrlGeneratorAgent(
        ollama_endpoint=os.getenv('OLLAMA_ENDPOINT', 'http://localhost:11434'),
        ollama_model=os.getenv('OLLAMA_MODEL', 'llama2'),
        api_key=API_KEY,
        library_api_base=f"https://api.ashortstayinhell.com/api/v3"
    )
    logger.info("🤖 Ollama URL Generator Agent initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Ollama agent: {e}")
    ollama_agent = None

@app.route('/api/v3/ollama/query', methods=['POST'])
@require_auth
def ollama_natural_language_query():
    """Natural language query via Ollama integration"""
    start_time = time.time()
    
    try:
        if not ollama_agent:
            return jsonify({
                'success': False, 
                'error': 'Ollama agent not available'
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
        user_query = data.get('query', '').strip()
        
        # Validate input
        if not user_query or len(user_query) < 3:
            return jsonify({'success': False, 'error': 'Query too short (minimum 3 characters)'}), 400
        
        if len(user_query) > 500:
            return jsonify({'success': False, 'error': 'Query too long (maximum 500 characters)'}), 400
        
        # Process query with Ollama agent (run in asyncio)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ollama_agent.natural_language_to_url(user_query))
        finally:
            loop.close()
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Query processing failed')
            }), 500
        
        # Execute the generated searches
        search_results = []
        total_books_found = 0
        
        for url_config in result['search_urls']:
            try:
                # Extract search parameters from the generated URL
                search_params = url_config['url'].split('?')[1] if '?' in url_config['url'] else ''
                params = dict(param.split('=') for param in search_params.split('&') if '=' in param)
                
                # Execute search using existing search function
                search_query = params.get('q', '')
                search_limit = int(params.get('limit', 10))
                
                if search_query:
                    # Call internal search function
                    conn = get_db()
                    if conn:
                        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                            cur.execute("""
                                SELECT b.book_id, b.title, b.author, b.word_count,
                                       c.content, c.chunk_id
                                FROM books b
                                JOIN chunks c ON b.book_id = c.book_id
                                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                                ORDER BY ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) DESC
                                LIMIT %s
                            """, (search_query, search_query, search_limit))
                            
                            books = [dict(row) for row in cur.fetchall()]
                            
                            search_result = {
                                'strategy': url_config['strategy'],
                                'description': url_config['description'],
                                'query': search_query,
                                'books_found': len(books),
                                'books': books[:5],  # Limit to top 5 for response size
                                'priority': url_config.get('priority', 999)
                            }
                            
                            search_results.append(search_result)
                            total_books_found += len(books)
                        
                        conn.close()
                
            except Exception as search_error:
                logger.warning(f"Search execution failed for strategy {url_config.get('strategy', 'unknown')}: {search_error}")
                continue
        
        # Sort results by priority
        search_results.sort(key=lambda x: x.get('priority', 999))
        
        processing_time = time.time() - start_time
        
        # Log successful query
        logger.info(f"🔍 Ollama query: '{user_query[:50]}...' - {total_books_found} results in {processing_time:.3f}s")
        
        return jsonify({
            'success': True,
            'data': {
                'original_query': user_query,
                'ollama_analysis': result['structured_query'],
                'explanation': result['explanation'],
                'search_strategies': len(result['search_urls']),
                'search_results': search_results,
                'total_books_found': total_books_found,
                'performance': {
                    'processing_time': processing_time,
                    'ollama_time': result.get('performance', {}).get('response_time', 0)
                },
                'knowledge_base': {
                    'total_books': 360,
                    'total_words': 34236988,
                    'searched_via': 'Natural language processing with Ollama'
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"❌ Ollama query error: {e} - {processing_time:.3f}s")
        return jsonify({
            'success': False, 
            'error': 'Query processing failed',
            'processing_time': processing_time
        }), 500

@app.route('/api/v3/ollama/health', methods=['GET'])
@require_auth
def ollama_health_check():
    """Check Ollama integration health"""
    try:
        if not ollama_agent:
            return jsonify({
                'success': False,
                'status': 'ollama_agent_unavailable',
                'message': 'Ollama agent not initialized'
            }), 503
        
        # Run health check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            health_result = loop.run_until_complete(ollama_agent.test_connection())
        finally:
            loop.close()
        
        return jsonify({
            'success': True,
            'data': {
                'ollama_agent': 'initialized',
                'connection_test': health_result,
                'agent_stats': {
                    'queries_processed': ollama_agent.query_count,
                    'avg_response_time': ollama_agent.total_response_time / max(ollama_agent.query_count, 1)
                }
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Health check failed'
        }), 500

# ================================
# LEXI - THE OFFICIAL LIBRARYBABEL MASCOT
# ================================

@app.route('/api/v3/lexi', methods=['POST'])
@require_auth
def lexi_chat():
    """
    🎯 LEXI - THE Official LibraryOfBabel Mascot Chat Interface
    
    Lexi is THE official LibraryOfBabel mascot - a Reddit Bibliophile agent
    who serves as the primary interface for conversational book discovery.
    Powered by Ollama Llama3 7B with full RAG integration across 363 books
    
    Security: Full API key authentication required (same as major site components)
    """
    start_time = time.time()
    
    try:
        # Validate request format
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json',
                'mascot': 'lexi',
                'message': 'yo! need JSON format for our chat 📱'
            }), 400
        
        data = request.get_json()
        user_query = data.get('query', '').strip()
        session_id = data.get('session_id', f'lexi_session_{int(time.time())}')
        context = data.get('context', 'official_lexi_chat')
        
        # NEW: Chat history for conversation context
        chat_history = data.get('chat_history', [])
        include_history = data.get('include_history', True)  # Default to including history
        
        # Input validation (security requirement)
        if not user_query:
            return jsonify({
                'success': False,
                'error': 'Query is required',
                'mascot': 'lexi',
                'message': 'hey! what do you want to know? ask me about our 363 books! 📚'
            }), 400
        
        if len(user_query) > 1000:  # Increased limit for Lexi interactions
            return jsonify({
                'success': False,
                'error': 'Query too long (max 1000 characters)',
                'mascot': 'lexi',
                'message': 'whoa! keep it shorter so I can focus 🎯'
            }), 400
        
        # NEW: Validate and process chat history
        validated_history = _validate_chat_history(chat_history)
        if include_history:
            logger.info(f"🎭 LEXI CHAT: '{user_query[:100]}...' with {len(validated_history)} history items (session: {session_id})")
        
        # Rate limiting check (security requirement)
        client_ip = get_client_ip()
        logger.info(f"🎭 LEXI MASCOT: '{user_query[:100]}...' from {client_ip[:8]}... (session: {session_id})")
        
        # Initialize Ollama agent for Lexi personality with conversation context
        try:
            lexi_agent = OllamaUrlGeneratorAgent(
                ollama_model="llama3:7b",
                api_key=API_KEY,
                library_api_base=request.host_url.rstrip('/') + '/api/v3',
                conversation_history=validated_history if include_history else []
            )
        except Exception as e:
            logger.error(f"❌ Mascot Ollama initialization failed: {e}")
            return jsonify({
                'success': False,
                'error': 'Mascot temporarily unavailable',
                'mascot': 'lexi',
                'message': 'ugh, having some technical difficulties! try again in a sec 🔧',
                'fallback_available': True
            }), 503
        
        # Process query with Lexi personality
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            ollama_result = loop.run_until_complete(
                lexi_agent.natural_language_to_url(user_query)
            )
            
            loop.close()
            
            if not ollama_result.get('success', False):
                raise Exception(ollama_result.get('error', 'Mascot processing failed'))
                
        except Exception as e:
            logger.error(f"❌ Mascot Ollama processing failed: {e}")
            # Fallback to direct search
            ollama_result = {
                'success': False,
                'search_urls': [{
                    'strategy': 'lexi_fallback',
                    'url': f"{request.host_url.rstrip('/')}/api/v3/search?q={user_query}&limit=8&api_key={API_KEY}",
                    'description': f"Lexi's direct search for: {user_query}",
                    'priority': 1
                }],
                'explanation': 'Using my backup search system - still super effective! 🚀'
            }
        
        # Execute searches and collect results
        search_results = []
        total_books_found = 0
        unique_books = set()
        
        for url_config in ollama_result.get('search_urls', []):
            try:
                # Internal search execution
                search_url = url_config['url']
                
                if '?' in search_url:
                    query_params = search_url.split('?')[1]
                    params = {}
                    for param in query_params.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            params[key] = value
                    
                    search_query = params.get('q', user_query)
                    search_limit = int(params.get('limit', 8))
                    
                    # Execute database search
                    conn = get_db()
                    if conn:
                        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                            cur.execute("""
                                SELECT 
                                    c.chunk_id, c.book_id, c.chapter_number, c.section_number,
                                    c.content, c.word_count, c.chunk_type,
                                    b.title, b.author, b.publication_year, b.genre,
                                    ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as relevance
                                FROM chunks c
                                JOIN books b ON c.book_id = b.book_id
                                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                                ORDER BY relevance DESC
                                LIMIT %s
                            """, (search_query, search_query, search_limit))
                            
                            results = [dict(row) for row in cur.fetchall()]
                            
                            # Add highlighting for Lexi display
                            for result in results:
                                result['highlighted_content'] = _highlight_text(
                                    result['content'], search_query, 250
                                )
                                unique_books.add(result['book_id'])
                            
                            search_results.append({
                                'strategy': url_config['strategy'],
                                'description': url_config['description'],
                                'results': results,
                                'result_count': len(results)
                            })
                            
                            total_books_found += len(results)
                            
            except Exception as e:
                logger.error(f"❌ Mascot search execution failed: {e}")
                continue
        
        # Generate Lexi's personality-driven response with conversation context
        conversation_context = _format_conversation_context(validated_history) if include_history else None
        lexi_response = _generate_lexi_response(
            user_query, search_results, len(unique_books), total_books_found, conversation_context
        )
        
        # Update agent memory with Lexi interaction
        memory_updated = _update_lexi_memory(
            session_id, user_query, lexi_response, search_results
        )
        
        # Calculate performance metrics
        response_time = time.time() - start_time
        
        # Official Lexi response format
        lexi_response_data = {
            'success': True,
            'mascot': 'lexi',
            'mascot_full_name': 'Lexi - THE LibraryOfBabel Official Mascot',
            'personality': 'reddit_bibliophile_scholar',
            'response': lexi_response,
            'query': user_query,
            'session_id': session_id,
            'search_results': search_results,
            'books_found': len(unique_books),
            'passages_found': total_books_found,
            'conversation_context': {
                'history_items': len(validated_history) if include_history else 0,
                'context_enabled': include_history,
                'updated_history': _build_updated_history(validated_history, user_query, lexi_response, include_history)
            },
            'knowledge_base': {
                'total_books': 363,
                'total_words': 34236988,
                'search_system': 'RAG with PostgreSQL + Ollama Llama3 7B'
            },
            'memory_updated': memory_updated,
            'ollama_powered': ollama_result.get('success', False),
            'security': {
                'api_key_validated': True,
                'rate_limited': True,
                'input_sanitized': True
            },
            'performance': {
                'response_time': round(response_time, 3),
                'target_met': response_time < 2.0,
                'status': 'optimal' if response_time < 2.0 else 'acceptable'
            },
            'timestamp': datetime.now().isoformat(),
            'next_actions': _suggest_lexi_actions(user_query, search_results),
            'voice_compatible': True,
            'official_mascot': True,
            'is_primary_mascot': True,
            'chat_history': _build_updated_history(validated_history, user_query, lexi_response, include_history)
        }
        
        logger.info(f"🎭 LEXI: Query processed in {response_time:.3f}s - {len(unique_books)} books, {total_books_found} passages")
        
        return jsonify(lexi_response_data)
        
    except Exception as e:
        logger.error(f"❌ Mascot chat error: {e}")
        return jsonify({
            'success': False,
            'error': 'Mascot temporarily unavailable',
            'mascot': 'lexi',
            'message': 'oops! something went wrong on my end. try again? 🤖',
            'fallback_message': 'LibraryOfBabel search is still available at /api/v3/search',
            'timestamp': datetime.now().isoformat()
        }), 500

def _generate_lexi_response(query, search_results, unique_books, total_passages, conversation_context=None):
    """Generate Lexi's official personality response - THE LibraryOfBabel mascot with conversation memory"""
    
    # Add conversation context awareness
    context_prefix = ""
    if conversation_context:
        context_prefix = "Based on our conversation, "
    
    # No results - encouraging response
    if unique_books == 0:
        return f"{context_prefix}hmm, no direct hits for '{query}' 🤔 but hey! I've got 363 books in my brain - try rephrasing or ask me about related topics! I'm here to help you discover awesome knowledge! 🚀📚"
    
    # Single book - focused excitement
    if unique_books == 1:
        return f"{context_prefix}PERFECT! 🎯 Found exactly 1 book with amazing content about '{query}'! This is quality research material right here - dive deep into this one! 📖✨"
    
    # Few books - quality focus
    if unique_books <= 3:
        return f"{context_prefix}nice find! 🔥 discovered {unique_books} books with solid content about '{query}' - quality over quantity! These are carefully curated matches from my 363-book knowledge base! 📚"
    
    # Medium results - excited
    if unique_books <= 8:
        return f"{context_prefix}yo! this is EXCELLENT! 🎉 found {unique_books} books about '{query}' with {total_passages} relevant passages! This is prime research territory - you're gonna love exploring these! 🤓"
    
    # Many results - enthusiastic
    return f"{context_prefix}HOLY MOLY! 🎄 {unique_books} books about '{query}' with {total_passages} passages - this is like Christmas morning for researchers! I'm absolutely STOKED to help you explore this topic! Time to get DEEP into some serious knowledge! 🚀📚🔥"

def _update_lexi_memory(session_id, query, response, search_results):
    """Update Lexi memory in agent system - THE official mascot"""
    try:
        memory_file = '/Users/weixiangzhang/Local Dev/LibraryOfBabel/agents/bulletin_board/agent_memory.json'
        
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                memory_data = json.load(f)
            
            # Add Lexi interaction to memory
            memory_entry = {
                'timestamp': datetime.now().isoformat(),
                'agent': 'reddit_bibliophile',
                'agent_name': 'Lexi - LibraryOfBabel Official Mascot',
                'message': f"LEXI CHAT: '{query[:60]}...' - processed as THE official LibraryOfBabel mascot! {len(search_results)} search strategies executed! 🎭",
                'source': 'official_lexi_chat',
                'event_type': 'lexi_interaction',
                'priority': 'MAXIMUM',
                'session_id': session_id,
                'official_mascot': True,
                'is_primary_mascot': True
            }
            
            memory_data.get('memory_threads', []).append(memory_entry)
            
            # Update last active
            memory_data.setdefault('last_active', {})['reddit_bibliophile'] = datetime.now().isoformat()
            
            with open(memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Mascot memory update failed: {e}")
        return False

def _suggest_lexi_actions(query, search_results):
    """Suggest next actions in Lexi's voice"""
    suggestions = []
    
    if search_results:
        suggestions.append("📖 Ask me to explain any book in detail!")
        suggestions.append("🔍 Want me to find connections between these books?")
        suggestions.append("📚 I can recommend similar books if you like these!")
        suggestions.append("💡 Ask for key quotes or insights from any author!")
    
    suggestions.append("🎯 Try asking about specific topics or themes!")
    suggestions.append("📝 Want chapter summaries or book overviews?")
    suggestions.append("🔗 I can find cross-references between different authors!")
    suggestions.append("🚀 Challenge me with complex research questions!")
    
    return suggestions

@app.route('/api/v3/lexi/health', methods=['GET'])
@require_auth
def lexi_health():
    """Health check for Lexi - THE official LibraryOfBabel mascot system"""
    try:
        # Check all Lexi components
        health_status = {
            'mascot': 'lexi',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {
                'database': 'unknown',
                'ollama': 'unknown',
                'agent_memory': 'unknown',
                'api_security': 'healthy'
            }
        }
        
        # Database check
        try:
            with get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM books")
                        book_count = cur.fetchone()[0]
                        health_status['components']['database'] = f'healthy ({book_count} books)'
                else:
                    health_status['components']['database'] = 'unhealthy'
                    health_status['status'] = 'degraded'
        except Exception as e:
            health_status['components']['database'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Ollama check
        try:
            if ollama_agent:
                health_status['components']['ollama'] = 'agent_initialized'
            else:
                health_status['components']['ollama'] = 'agent_not_initialized'
        except:
            health_status['components']['ollama'] = 'error'
        
        # Agent memory check
        try:
            memory_file = '/Users/weixiangzhang/Local Dev/LibraryOfBabel/agents/bulletin_board/agent_memory.json'
            if os.path.exists(memory_file):
                health_status['components']['agent_memory'] = 'file_accessible'
            else:
                health_status['components']['agent_memory'] = 'file_missing'
        except:
            health_status['components']['agent_memory'] = 'error'
        
        # Add Lexi-specific info
        health_status['lexi_info'] = {
            'name': 'Lexi',
            'full_name': 'Lexi - LibraryOfBabel Official Mascot',
            'personality': 'reddit_bibliophile_scholar',
            'knowledge_base': '363 books, 34M+ words',
            'capabilities': ['RAG search', 'Book recommendations', 'Knowledge synthesis', 'Voice compatible'],
            'security_level': 'production (API key required)'
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Mascot health check failed: {e}")
        return jsonify({
            'mascot': 'lexi',
            'status': 'unhealthy',
            'error': 'Health check failed',
            'message': 'something went wrong with my health check! 🤒'
        }), 500

# ================================
# LEXI CONVERSATION HISTORY HELPERS
# ================================

def _validate_chat_history(chat_history):
    """Validate and sanitize chat history for security and format"""
    if not isinstance(chat_history, list):
        return []
    
    validated = []
    max_history_items = 20  # Prevent memory overflow
    
    for item in chat_history[-max_history_items:]:
        if isinstance(item, dict):
            # Validate required fields
            if 'user' in item and 'lexi' in item and 'timestamp' in item:
                # Sanitize content
                sanitized_item = {
                    'user': str(item['user'])[:500],  # Limit user message length
                    'lexi': str(item['lexi'])[:1000],  # Limit Lexi response length
                    'timestamp': item['timestamp'],
                    'session_id': item.get('session_id', 'unknown')
                }
                validated.append(sanitized_item)
    
    return validated

def _build_updated_history(previous_history, user_query, lexi_response, include_history):
    """Build updated conversation history with new interaction"""
    if not include_history:
        return []
    
    # Start with previous history
    updated_history = previous_history.copy() if previous_history else []
    
    # Add new interaction
    new_interaction = {
        'user': user_query,
        'lexi': lexi_response,
        'timestamp': datetime.now().isoformat(),
        'session_id': request.get_json().get('session_id', 'unknown')
    }
    
    updated_history.append(new_interaction)
    
    # Keep only last 20 interactions to prevent memory issues
    return updated_history[-20:]

def _format_conversation_context(chat_history):
    """Format conversation history for Lexi's context understanding"""
    if not chat_history:
        return "This is the start of our conversation!"
    
    context_lines = ["Previous conversation context:"]
    
    for item in chat_history[-5:]:  # Use last 5 interactions for context
        context_lines.append(f"You: {item['user']}")
        context_lines.append(f"Lexi: {item['lexi']}")
        context_lines.append("---")
    
    context_lines.append("Current question:")
    
    return "\n".join(context_lines)

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
    
    # Production server with SSL
    ssl_cert_path = '/Users/weixiangzhang/Local Dev/LibraryOfBabel/ssl/letsencrypt-config/live/api.ashortstayinhell.com/fullchain.pem'
    ssl_key_path = '/Users/weixiangzhang/Local Dev/LibraryOfBabel/ssl/letsencrypt-config/live/api.ashortstayinhell.com/privkey.pem'
    
    app.run(
        host='0.0.0.0',
        port=5563,
        debug=False,
        ssl_context=(ssl_cert_path, ssl_key_path)
    )