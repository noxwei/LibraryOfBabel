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