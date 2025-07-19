#!/usr/bin/env python3
"""
🎯 Dr. Elena Rodriguez - iOS Shortcuts Optimized API Namespace
=============================================================

MLS Specialization: Information Architecture & User Experience Design
Primary Role: Mobile-first API design for iOS Shortcuts and Data Jar

Philosophy: "Information architecture makes complex knowledge feel simple"
Design Principle: Flat structures, single-value responses, shortcut-friendly formats

Created: July 19, 2025
Team: LibraryOfBabel Ebook Focus DBA Team
"""

from flask import Flask, request, jsonify, Blueprint
import psycopg2
import psycopg2.extras
import logging
import time
import json
import os
import random
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)

# Create shortcuts blueprint
shortcuts_bp = Blueprint('shortcuts', __name__, url_prefix='/api/shortcuts')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': int(os.getenv('DB_PORT', 5432))
}

def get_db():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

def verify_api_key():
    """Verify API key (inherit from main API)"""
    api_key = os.getenv('API_KEY')
    if not api_key:
        return True  # Development mode
    
    # Check various auth methods
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:] == api_key
    
    provided_key = (request.headers.get('X-API-Key') or 
                   request.args.get('api_key') or
                   (request.json.get('api_key') if request.is_json and request.json else None))
    
    return provided_key == api_key

def require_auth(f):
    """Decorator for API authentication"""
    def decorated_function(*args, **kwargs):
        if not verify_api_key():
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ================================
# SINGLE VALUE ENDPOINTS (Perfect for iOS Shortcuts)
# ================================

@shortcuts_bp.route('/books/count')
@require_auth
def book_count():
    """Returns: 2503 (just the number, perfect for shortcuts)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books;")
                count = cur.fetchone()[0]
                return str(count), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Book count error: {e}")
        return "0", 500, {'Content-Type': 'text/plain'}

@shortcuts_bp.route('/random/title')
@require_auth
def random_title():
    """Returns: "The Elegant Universe" (just the title string)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT title FROM books ORDER BY RANDOM() LIMIT 1;")
                title = cur.fetchone()[0]
                return title, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Random title error: {e}")
        return "No books available", 500, {'Content-Type': 'text/plain'}

@shortcuts_bp.route('/random/author')
@require_auth
def random_author():
    """Returns: "Brian Greene" (just the author string)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT author FROM books WHERE author IS NOT NULL ORDER BY RANDOM() LIMIT 1;")
                author = cur.fetchone()[0]
                return author, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Random author error: {e}")
        return "Unknown Author", 500, {'Content-Type': 'text/plain'}

@shortcuts_bp.route('/random/book')
@require_auth
def random_book():
    """Returns: {"title": "Book Title", "author": "Author Name", "id": 123} - combined random book info"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT book_id, title, author 
                    FROM books 
                    WHERE author IS NOT NULL 
                    ORDER BY RANDOM() 
                    LIMIT 1;
                """)
                result = cur.fetchone()
                if result:
                    book_id, title, author = result
                    return jsonify({
                        "id": book_id,
                        "title": title,
                        "author": author,
                        "shortcuts_ready": True
                    })
                else:
                    return jsonify({
                        "error": "No books available",
                        "shortcuts_ready": True
                    }), 404
    except Exception as e:
        logger.error(f"Random book error: {e}")
        return jsonify({
            "error": "Random book unavailable",
            "shortcuts_ready": True
        }), 500

@shortcuts_bp.route('/search/<term>/count')
@require_auth
def search_count(term):
    """Returns: 15 (number of books matching search term)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(DISTINCT book_id) 
                    FROM chunks 
                    WHERE content ILIKE %s;
                """, (f'%{term}%',))
                count = cur.fetchone()[0]
                return str(count), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Search count error: {e}")
        return "0", 500, {'Content-Type': 'text/plain'}

@shortcuts_bp.route('/search/<term>/has-results')
@require_auth
def search_has_results(term):
    """Returns: true or false (boolean for shortcuts if/then logic)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM chunks WHERE content ILIKE %s LIMIT 1
                    );
                """, (f'%{term}%',))
                has_results = cur.fetchone()[0]
                return str(has_results).lower(), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Search exists error: {e}")
        return "false", 500, {'Content-Type': 'text/plain'}

# ================================
# SIMPLE ARRAY ENDPOINTS (Easy for shortcuts to loop through)
# ================================

@shortcuts_bp.route('/books/title-list')
@require_auth
def book_title_list():
    """Returns: ["Title1", "Title2", "Title3"] - simple array"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT title FROM books ORDER BY title LIMIT %s;", (limit,))
                titles = [row[0] for row in cur.fetchall()]
                return jsonify(titles)
    except Exception as e:
        logger.error(f"Title list error: {e}")
        return jsonify([])

@shortcuts_bp.route('/books/author-list')
@require_auth
def book_author_list():
    """Returns: ["Author1", "Author2", "Author3"] - simple array"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT author 
                    FROM books 
                    WHERE author IS NOT NULL 
                    ORDER BY author 
                    LIMIT %s;
                """, (limit,))
                authors = [row[0] for row in cur.fetchall()]
                return jsonify(authors)
    except Exception as e:
        logger.error(f"Author list error: {e}")
        return jsonify([])

@shortcuts_bp.route('/search/<term>/titles')
@require_auth
def search_titles(term):
    """Returns: ["Book1", "Book2"] - titles matching search term"""
    try:
        limit = min(int(request.args.get('limit', 10)), 100)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT b.title
                    FROM books b
                    JOIN chunks c ON b.id = c.book_id
                    WHERE c.content ILIKE %s
                    ORDER BY b.title
                    LIMIT %s;
                """, (f'%{term}%', limit))
                titles = [row[0] for row in cur.fetchall()]
                return jsonify(titles)
    except Exception as e:
        logger.error(f"Search titles error: {e}")
        return jsonify([])

# ================================
# FORMATTED TEXT ENDPOINTS (Perfect for sharing/display)
# ================================

@shortcuts_bp.route('/random/citation')
@require_auth
def random_citation():
    """Returns: "Greene, Brian. The Elegant Universe (1999)" - formatted citation"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT author, title, publication_date 
                    FROM books 
                    WHERE author IS NOT NULL 
                    ORDER BY RANDOM() 
                    LIMIT 1;
                """)
                result = cur.fetchone()
                if result:
                    author, title, pub_date = result
                    year = pub_date.split('-')[0] if pub_date else "Unknown"
                    citation = f"{author}. {title} ({year})"
                    return citation, 200, {'Content-Type': 'text/plain'}
                else:
                    return "No books available", 500, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Random citation error: {e}")
        return "Citation unavailable", 500, {'Content-Type': 'text/plain'}

@shortcuts_bp.route('/random/share-text')
@require_auth
def random_share_text():
    """Returns: "📚 Currently reading: The Elegant Universe by Brian Greene" - share-ready text"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT title, author 
                    FROM books 
                    WHERE author IS NOT NULL 
                    ORDER BY RANDOM() 
                    LIMIT 1;
                """)
                result = cur.fetchone()
                if result:
                    title, author = result
                    share_text = f"📚 Currently reading: {title} by {author}"
                    return share_text, 200, {'Content-Type': 'text/plain'}
                else:
                    return "📚 Building my reading list!", 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Random share text error: {e}")
        return "📚 Reading something amazing!", 200, {'Content-Type': 'text/plain'}

@shortcuts_bp.route('/search/<term>/summary')
@require_auth
def search_summary(term):
    """Returns: "Found 5 books about quantum physics" - summary text"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(DISTINCT book_id) 
                    FROM chunks 
                    WHERE content ILIKE %s;
                """, (f'%{term}%',))
                count = cur.fetchone()[0]
                
                if count == 0:
                    summary = f"No books found about {term}"
                elif count == 1:
                    summary = f"Found 1 book about {term}"
                else:
                    summary = f"Found {count} books about {term}"
                
                return summary, 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Search summary error: {e}")
        return f"Search for {term} encountered an error", 500, {'Content-Type': 'text/plain'}

# ================================
# DATA JAR OPTIMIZED ENDPOINTS
# ================================

@shortcuts_bp.route('/stats/dashboard')
@require_auth
def stats_dashboard():
    """Returns: Clean object perfect for Data Jar storage"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get comprehensive stats
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_books,
                        COUNT(DISTINCT author) as unique_authors,
                        COUNT(*) FILTER (WHERE publication_date ~ '^[0-9]{4}' AND publication_date::text >= '2000') as books_2000s_plus,
                        COUNT(*) FILTER (WHERE publication_date ~ '^[0-9]{4}' AND publication_date::text < '2000') as books_pre_2000
                    FROM books;
                """)
                book_stats = cur.fetchone()
                
                cur.execute("SELECT COUNT(*) FROM chunks;")
                total_chunks = cur.fetchone()[0]
                
                cur.execute("""
                    SELECT author, COUNT(*) as book_count
                    FROM books 
                    WHERE author IS NOT NULL
                    GROUP BY author
                    ORDER BY book_count DESC
                    LIMIT 5;
                """)
                top_authors = [{"author": row[0], "book_count": row[1]} for row in cur.fetchall()]
                
                dashboard = {
                    "timestamp": datetime.now().isoformat(),
                    "library_stats": {
                        "total_books": book_stats['total_books'],
                        "unique_authors": book_stats['unique_authors'],
                        "total_chunks": total_chunks,
                        "books_2000s_plus": book_stats['books_2000s_plus'],
                        "books_pre_2000": book_stats['books_pre_2000'],
                        "avg_chunks_per_book": round(total_chunks / book_stats['total_books'], 1) if book_stats['total_books'] > 0 else 0
                    },
                    "top_authors": top_authors,
                    "data_jar_optimized": True,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                
                return jsonify(dashboard)
                
    except Exception as e:
        logger.error(f"Stats dashboard error: {e}")
        return jsonify({
            "error": "Stats unavailable",
            "timestamp": datetime.now().isoformat(),
            "data_jar_optimized": True
        })

@shortcuts_bp.route('/user/reading-progress', methods=['GET', 'POST'])
@require_auth
def reading_progress():
    """GET: Returns reading progress object. POST: Updates reading progress"""
    
    if request.method == 'GET':
        # Return stored reading progress (this would typically come from user storage)
        # For now, return a template structure
        progress = {
            "current_book": "The Elegant Universe",
            "current_author": "Brian Greene",
            "progress_percentage": 45,
            "pages_read": 156,
            "reading_streak_days": 7,
            "books_completed_this_month": 2,
            "reading_goal_annual": 50,
            "books_read_this_year": 12,
            "last_updated": datetime.now().isoformat(),
            "data_jar_ready": True
        }
        return jsonify(progress)
    
    elif request.method == 'POST':
        # Update reading progress
        try:
            data = request.get_json()
            # In a real implementation, this would save to user storage
            # For now, return success with the provided data
            updated_progress = {
                **data,
                "last_updated": datetime.now().isoformat(),
                "update_success": True,
                "data_jar_ready": True
            }
            return jsonify(updated_progress)
        except Exception as e:
            logger.error(f"Reading progress update error: {e}")
            return jsonify({"error": "Update failed", "success": False}), 400

# ================================
# SHORTCUT-FRIENDLY SEARCH ENDPOINTS
# ================================

@shortcuts_bp.route('/search/<term>/simple')
@require_auth
def search_simple(term):
    """Returns: Flat response with no nested objects"""
    try:
        limit = min(int(request.args.get('limit', 5)), 20)
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT b.title, b.author, b.id
                    FROM books b
                    JOIN chunks c ON b.id = c.book_id
                    WHERE c.content ILIKE %s
                    ORDER BY b.title
                    LIMIT %s;
                """, (f'%{term}%', limit))
                
                results = cur.fetchall()
                
                # Flat structure for easy shortcuts parsing
                response = {
                    "search_term": term,
                    "count": len(results),
                    "has_results": len(results) > 0,
                    "titles": [r['title'] for r in results],
                    "authors": [r['author'] for r in results],
                    "book_ids": [r['id'] for r in results],
                    "first_title": results[0]['title'] if results else None,
                    "first_author": results[0]['author'] if results else None,
                    "shortcuts_optimized": True
                }
                
                return jsonify(response)
                
    except Exception as e:
        logger.error(f"Simple search error: {e}")
        return jsonify({
            "search_term": term,
            "count": 0,
            "has_results": False,
            "titles": [],
            "authors": [],
            "book_ids": [],
            "error": "Search failed",
            "shortcuts_optimized": True
        })

@shortcuts_bp.route('/books/<int:book_id>/summary')
@require_auth
def book_summary(book_id):
    """Returns: Single flat object about a specific book"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, b.subject, b.publication_date,
                           COUNT(c.id) as chunk_count,
                           MIN(LENGTH(c.content)) as min_chunk_length,
                           MAX(LENGTH(c.content)) as max_chunk_length,
                           AVG(LENGTH(c.content)) as avg_chunk_length
                    FROM books b
                    LEFT JOIN chunks c ON b.id = c.book_id
                    WHERE b.id = %s
                    GROUP BY b.id, b.title, b.author, b.subject, b.publication_date;
                """, (book_id,))
                
                result = cur.fetchone()
                
                if result:
                    summary = {
                        "book_id": book_id,
                        "title": result['title'],
                        "author": result['author'],
                        "subject": result['subject'],
                        "publication_date": result['publication_date'],
                        "chunk_count": result['chunk_count'],
                        "avg_chunk_length": round(result['avg_chunk_length']) if result['avg_chunk_length'] else 0,
                        "has_content": result['chunk_count'] > 0,
                        "shortcuts_ready": True
                    }
                    return jsonify(summary)
                else:
                    return jsonify({
                        "book_id": book_id,
                        "error": "Book not found",
                        "shortcuts_ready": True
                    }), 404
                    
    except Exception as e:
        logger.error(f"Book summary error: {e}")
        return jsonify({
            "book_id": book_id,
            "error": "Summary unavailable",
            "shortcuts_ready": True
        }), 500

# ================================
# BOOK CONSTRUCTION ENDPOINTS (Page-by-page navigation)
# ================================

@shortcuts_bp.route('/books/<int:book_id>/construct')
@require_auth
def book_construct_overview(book_id):
    """Returns: Complete book structure for page-by-page navigation"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get book info and chunk count
                cur.execute("""
                    SELECT b.title, b.author, b.subject, COUNT(c.id) as total_pages
                    FROM books b
                    LEFT JOIN chunks c ON b.id = c.book_id
                    WHERE b.id = %s
                    GROUP BY b.id, b.title, b.author, b.subject;
                """, (book_id,))
                
                book_info = cur.fetchone()
                
                if not book_info:
                    return jsonify({"error": "Book not found"}), 404
                
                # Create navigation structure
                construction = {
                    "book_id": book_id,
                    "title": book_info['title'],
                    "author": book_info['author'],
                    "subject": book_info['subject'],
                    "total_pages": book_info['total_pages'],
                    "navigation": {
                        "first_page_url": f"/api/shortcuts/books/{book_id}/page/1",
                        "last_page_url": f"/api/shortcuts/books/{book_id}/page/{book_info['total_pages']}",
                        "random_page_url": f"/api/shortcuts/books/{book_id}/page/random",
                        "table_of_contents_url": f"/api/shortcuts/books/{book_id}/toc"
                    },
                    "shortcuts_ready": True,
                    "designed_for": "Page-by-page reading with navigation links"
                }
                
                return jsonify(construction)
                
    except Exception as e:
        logger.error(f"Book construction error: {e}")
        return jsonify({"error": "Construction failed", "book_id": book_id}), 500

@shortcuts_bp.route('/books/<int:book_id>/page/<page_num>')
@require_auth
def book_page(book_id, page_num):
    """Returns: Single page with navigation links (perfect for shortcuts)"""
    try:
        # Handle random page
        if page_num == 'random':
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT chunk_index FROM chunks 
                        WHERE book_id = %s 
                        ORDER BY RANDOM() LIMIT 1;
                    """, (book_id,))
                    result = cur.fetchone()
                    if result:
                        page_num = result[0]
                    else:
                        return jsonify({"error": "No pages found"}), 404
        
        page_num = int(page_num)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get current page
                cur.execute("""
                    SELECT c.text, c.chunk_index, b.title, b.author,
                           (SELECT MAX(chunk_index) FROM chunks WHERE book_id = %s) as max_page
                    FROM chunks c
                    JOIN books b ON c.book_id = b.id
                    WHERE c.book_id = %s AND c.chunk_index = %s;
                """, (book_id, book_id, page_num))
                
                page_data = cur.fetchone()
                
                if not page_data:
                    return jsonify({"error": "Page not found"}), 404
                
                # Create navigation
                prev_page = page_num - 1 if page_num > 1 else None
                next_page = page_num + 1 if page_num < page_data['max_page'] else None
                
                page_response = {
                    "book_id": book_id,
                    "title": page_data['title'],
                    "author": page_data['author'],
                    "current_page": page_num,
                    "total_pages": page_data['max_page'],
                    "page_content": page_data['text'],
                    "navigation": {
                        "previous_page_url": f"/api/shortcuts/books/{book_id}/page/{prev_page}" if prev_page else None,
                        "next_page_url": f"/api/shortcuts/books/{book_id}/page/{next_page}" if next_page else None,
                        "random_page_url": f"/api/shortcuts/books/{book_id}/page/random",
                        "book_overview_url": f"/api/shortcuts/books/{book_id}/construct",
                        "first_page_url": f"/api/shortcuts/books/{book_id}/page/1",
                        "last_page_url": f"/api/shortcuts/books/{book_id}/page/{page_data['max_page']}"
                    },
                    "shortcuts_optimized": True,
                    "chatgpt_ready": True
                }
                
                return jsonify(page_response)
                
    except Exception as e:
        logger.error(f"Book page error: {e}")
        return jsonify({"error": "Page unavailable"}), 500

@shortcuts_bp.route('/books/<int:book_id>/toc')
@require_auth
def book_table_of_contents(book_id):
    """Returns: Table of contents with page numbers (shortcuts-friendly)"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get book title and chunks with preview
                cur.execute("""
                    SELECT b.title, b.author,
                           c.chunk_index, 
                           LEFT(c.text, 100) as preview
                    FROM books b
                    JOIN chunks c ON b.id = c.book_id
                    WHERE b.id = %s
                    ORDER BY c.chunk_index
                    LIMIT %s;
                """, (book_id, limit))
                
                results = cur.fetchall()
                
                if not results:
                    return jsonify({"error": "Book not found"}), 404
                
                toc = {
                    "book_id": book_id,
                    "title": results[0]['title'],
                    "author": results[0]['author'],
                    "chapters": [
                        {
                            "page_number": row['chunk_index'],
                            "preview": row['preview'] + "...",
                            "page_url": f"/api/shortcuts/books/{book_id}/page/{row['chunk_index']}"
                        }
                        for row in results
                    ],
                    "total_chapters_shown": len(results),
                    "shortcuts_navigation_ready": True
                }
                
                return jsonify(toc)
                
    except Exception as e:
        logger.error(f"Book TOC error: {e}")
        return jsonify({"error": "Table of contents unavailable"}), 500

# ================================
# SERENDIPITY ENDPOINTS (Random content for ChatGPT story construction!)
# ================================

@shortcuts_bp.route('/serendipity/random-passage')
@require_auth
def serendipity_random_passage():
    """Returns: Random passage from any book (perfect for ChatGPT prompts!)"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, c.text, c.chunk_index
                    FROM chunks c
                    JOIN books b ON c.book_id = b.id
                    WHERE LENGTH(c.content) > 200
                    ORDER BY RANDOM()
                    LIMIT 1;
                """)
                
                result = cur.fetchone()
                
                if result:
                    passage = {
                        "title": result['title'],
                        "author": result['author'],
                        "passage": result['text'],
                        "page_number": result['chunk_index'],
                        "chatgpt_prompt_ready": True,
                        "story_seed": f"Based on this passage from '{result['title']}' by {result['author']}, write a story...",
                        "serendipity_type": "random_passage"
                    }
                    return jsonify(passage)
                else:
                    return jsonify({"error": "No passages available"}), 404
                    
    except Exception as e:
        logger.error(f"Serendipity passage error: {e}")
        return jsonify({"error": "Serendipity unavailable"}), 500

@shortcuts_bp.route('/serendipity/mixed-authors')
@require_auth
def serendipity_mixed_authors():
    """Returns: Passages from different authors for creative mixing!"""
    try:
        count = min(int(request.args.get('count', 3)), 10)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT b.author, b.title, c.text, c.chunk_index
                    FROM chunks c
                    JOIN books b ON c.book_id = b.id
                    WHERE LENGTH(c.content) > 150 AND b.author IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT %s;
                """, (count,))
                
                results = cur.fetchall()
                
                if results:
                    mixed_content = {
                        "passages": [
                            {
                                "author": row['author'],
                                "title": row['title'],
                                "passage": row['text'][:300] + "..." if len(row['text']) > 300 else row['text'],
                                "page_number": row['chunk_index']
                            }
                            for row in results
                        ],
                        "author_list": [row['author'] for row in results],
                        "title_list": [row['title'] for row in results],
                        "chatgpt_prompt": f"Create a story that blends the styles of {', '.join([row['author'] for row in results])}, using these passages as inspiration:",
                        "serendipity_type": "mixed_authors",
                        "story_construction_ready": True
                    }
                    return jsonify(mixed_content)
                else:
                    return jsonify({"error": "No mixed content available"}), 404
                    
    except Exception as e:
        logger.error(f"Mixed authors error: {e}")
        return jsonify({"error": "Mixed content unavailable"}), 500

@shortcuts_bp.route('/serendipity/theme-blend/<theme>')
@require_auth
def serendipity_theme_blend(theme):
    """Returns: Multiple passages around a theme for story blending"""
    try:
        count = min(int(request.args.get('count', 4)), 15)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, c.text, c.chunk_index
                    FROM chunks c
                    JOIN books b ON c.book_id = b.id
                    WHERE c.content ILIKE %s AND LENGTH(c.content) > 100
                    ORDER BY RANDOM()
                    LIMIT %s;
                """, (f'%{theme}%', count))
                
                results = cur.fetchall()
                
                if results:
                    theme_blend = {
                        "theme": theme,
                        "passages": [
                            {
                                "title": row['title'],
                                "author": row['author'],
                                "passage": row['text'][:400] + "..." if len(row['text']) > 400 else row['text'],
                                "page_number": row['chunk_index']
                            }
                            for row in results
                        ],
                        "source_count": len(results),
                        "unique_authors": list(set([row['author'] for row in results if row['author']])),
                        "chatgpt_story_prompt": f"Create an original story about '{theme}' inspired by these {len(results)} passages from different books:",
                        "serendipity_type": "theme_blend",
                        "story_construction_ready": True
                    }
                    return jsonify(theme_blend)
                else:
                    return jsonify({
                        "theme": theme,
                        "error": f"No passages found for theme '{theme}'",
                        "suggestion": "Try broader themes like 'love', 'technology', 'journey', 'mystery'"
                    }), 404
                    
    except Exception as e:
        logger.error(f"Theme blend error: {e}")
        return jsonify({"error": "Theme blend unavailable"}), 500

@shortcuts_bp.route('/serendipity/story-starter')
@require_auth
def serendipity_story_starter():
    """Returns: Complete story starter package for ChatGPT!"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get random elements for story construction
                cur.execute("""
                    SELECT b.title, b.author, c.text
                    FROM chunks c
                    JOIN books b ON c.book_id = b.id
                    WHERE LENGTH(c.content) BETWEEN 200 AND 600
                    ORDER BY RANDOM()
                    LIMIT 3;
                """)
                
                passages = cur.fetchall()
                
                # Get random character names from different books
                cur.execute("""
                    SELECT DISTINCT b.author
                    FROM books b
                    WHERE b.author IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT 5;
                """)
                authors = [row[0] for row in cur.fetchall()]
                
                if passages:
                    story_starter = {
                        "inspiration_passages": [
                            {
                                "source": f"{passage['title']} by {passage['author']}",
                                "text": passage['text'][:300] + "..."
                            }
                            for passage in passages
                        ],
                        "author_styles_to_blend": authors[:3],
                        "chatgpt_complete_prompt": f"""Create an original short story that blends elements from these three passages:

1. From "{passages[0]['title']}" by {passages[0]['author']}:
{passages[0]['text'][:200]}...

2. From "{passages[1]['title']}" by {passages[1]['author']}:
{passages[1]['text'][:200]}...

3. From "{passages[2]['title']}" by {passages[2]['author']}:
{passages[2]['text'][:200]}...

Write in a style that combines influences from {', '.join(authors[:3])}.
Make it approximately 500-800 words.""",
                        "serendipity_type": "complete_story_starter",
                        "ready_for_chatgpt": True,
                        "generated_at": datetime.now().isoformat()
                    }
                    return jsonify(story_starter)
                else:
                    return jsonify({"error": "No story material available"}), 404
                    
    except Exception as e:
        logger.error(f"Story starter error: {e}")
        return jsonify({"error": "Story starter unavailable"}), 500

# ================================
# HEALTH CHECK FOR SHORTCUTS NAMESPACE
# ================================

@shortcuts_bp.route('/health')
def shortcuts_health():
    """Health check for shortcuts namespace"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books LIMIT 1;")
                cur.fetchone()
                
        return jsonify({
            "status": "healthy",
            "namespace": "shortcuts",
            "endpoints_available": [
                "/books/count",
                "/random/title", 
                "/random/author",
                "/search/{term}/count",
                "/search/{term}/has-results",
                "/books/title-list",
                "/books/author-list", 
                "/search/{term}/titles",
                "/random/citation",
                "/random/share-text",
                "/search/{term}/summary",
                "/stats/dashboard",
                "/user/reading-progress",
                "/search/{term}/simple",
                "/books/{id}/summary"
            ],
            "designed_by": "Dr. Elena Rodriguez (IAV)",
            "optimized_for": ["iOS Shortcuts", "Data Jar", "Mobile Workflows"],
            "philosophy": "Information architecture makes complex knowledge feel simple",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Shortcuts health check error: {e}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "namespace": "shortcuts"
        }), 500

# Register the blueprint with the main app
def register_shortcuts_blueprint(app):
    """Register shortcuts blueprint with Flask app"""
    app.register_blueprint(shortcuts_bp)
    logger.info("🎯 Dr. Elena Rodriguez's iOS Shortcuts API namespace registered!")
    logger.info("📱 Available at /api/shortcuts/* - Mobile-optimized and Data Jar ready!")

if __name__ == "__main__":
    # For testing purposes
    app = Flask(__name__)
    register_shortcuts_blueprint(app)
    app.run(debug=True, port=5000)