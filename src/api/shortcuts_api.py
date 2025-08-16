#!/usr/bin/env python3
"""
🎯 Dr. Elena Rodriguez - Modern Query-Parameter Based iOS Shortcuts API v2.0
=========================================================================

MLS Specialization: Information Architecture & User Experience Design
Primary Role: Modern RESTful API design for iOS Shortcuts and Data Jar

Philosophy: "Information architecture makes complex knowledge feel simple"
Design Principle: Query parameters over path segments, flexible data combinations

Modernization: Complete elimination of forward slash navigation
User Feedback: "I don't like the forward slash as a way of url navigation"

Created: July 26, 2025 (v2.0 Modernization)
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

# Create modern shortcuts blueprint
shortcuts_v2_bp = Blueprint('shortcuts_v2', __name__, url_prefix='/api/shortcuts')

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
    """Decorator for API authentication (disabled for local testing)"""
    def decorated_function(*args, **kwargs):
        # Skip auth for local testing
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ================================
# MODERN QUERY-PARAMETER BASED ENDPOINTS
# ================================

@shortcuts_v2_bp.route('/books')
@require_auth
def books_endpoint():
    """
    Universal books endpoint with query parameters
    
    Examples:
    - /books?id=288&action=summary
    - /books?id=288&page=1
    - /books?id=288&action=toc&limit=all&include_word_counts=true
    - /books?id=288&action=construct
    """
    book_id = request.args.get('id', type=int)
    action = request.args.get('action', 'summary')
    page = request.args.get('page', type=int)
    
    if not book_id:
        return jsonify({"error": "Missing required parameter: id"}), 400
    
    try:
        if action == 'summary':
            return get_book_summary(book_id)
        elif action == 'construct':
            return get_book_construct(book_id)
        elif action == 'toc':
            return get_book_toc(book_id)
        elif page:
            return get_book_page(book_id, page)
        else:
            return jsonify({"error": "Invalid action or missing page parameter"}), 400
            
    except Exception as e:
        logger.error(f"Books endpoint error: {e}")
        return jsonify({"error": "Books endpoint unavailable"}), 500

def get_book_summary(book_id: int):
    """Get book summary with enhanced metadata"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, b.subject, b.publication_year,
                           b.word_count, b.genre,
                           COUNT(c.chunk_id) as chunk_count,
                           MIN(LENGTH(c.content)) as min_chunk_length,
                           MAX(LENGTH(c.content)) as max_chunk_length,
                           AVG(LENGTH(c.content)) as avg_chunk_length
                    FROM books b
                    LEFT JOIN chunks c ON b.book_id = c.book_id
                    WHERE b.book_id = %s
                    GROUP BY b.book_id, b.title, b.author, b.subject, b.publication_year, b.word_count, b.genre;
                """, (book_id,))
                
                result = cur.fetchone()
                
                if result:
                    return jsonify({
                        "book_id": book_id,
                        "title": result['title'],
                        "author": result['author'],
                        "subject": result['subject'] or "No subject assigned",
                        "publication_year": result['publication_year'],
                        "total_word_count": result['word_count'] or 0,
                        "genre": result['genre'],
                        "chunk_count": result['chunk_count'],
                        "avg_chunk_length": round(result['avg_chunk_length']) if result['avg_chunk_length'] else 0,
                        "has_content": result['chunk_count'] > 0,
                        "reading_time_minutes": round((result['word_count'] or 0) / 200) if result['word_count'] else 0,
                        "shortcuts_ready": True,
                        "api_version": "v2.0_query_parameters"
                    })
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

def get_book_construct(book_id: int):
    """Get book structure with total word count"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, b.subject, b.word_count,
                           COUNT(c.chunk_id) as total_pages,
                           SUM(c.word_count) as calculated_word_count
                    FROM books b
                    LEFT JOIN chunks c ON b.book_id = c.book_id
                    WHERE b.book_id = %s
                    GROUP BY b.book_id, b.title, b.author, b.subject, b.word_count;
                """, (book_id,))
                
                book_info = cur.fetchone()
                
                if not book_info:
                    return jsonify({"error": "Book not found"}), 404
                
                return jsonify({
                    "book_id": book_id,
                    "title": book_info['title'],
                    "author": book_info['author'],
                    "subject": book_info['subject'],
                    "total_pages": book_info['total_pages'],
                    "total_word_count": book_info['word_count'] or book_info['calculated_word_count'] or 0,
                    "reading_time_minutes": round((book_info['word_count'] or book_info['calculated_word_count'] or 0) / 200),
                    "navigation": {
                        "first_page": f"/api/shortcuts/books?id={book_id}&page=1",
                        "last_page": f"/api/shortcuts/books?id={book_id}&page={book_info['total_pages']}",
                        "random_page": f"/api/shortcuts/books?id={book_id}&page=random",
                        "table_of_contents": f"/api/shortcuts/books?id={book_id}&action=toc&limit=all"
                    },
                    "shortcuts_ready": True,
                    "designed_for": "Page-by-page reading with query parameters",
                    "api_version": "v2.0_query_parameters"
                })
                
    except Exception as e:
        logger.error(f"Book construction error: {e}")
        return jsonify({"error": "Construction failed", "book_id": book_id}), 500

def get_book_toc(book_id: int):
    """Get table of contents with word counts and no pagination limit"""
    try:
        limit_param = request.args.get('limit', 'all')
        include_word_counts = request.args.get('include_word_counts', 'false').lower() == 'true'
        
        # Remove pagination limit when requested
        limit = None if limit_param == 'all' else min(int(limit_param), 1000)
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                query = """
                    SELECT b.title, b.author,
                           c.chunk_id, c.word_count,
                           LEFT(c.content, 100) as preview
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id
                    WHERE b.book_id = %s
                    ORDER BY c.chunk_id
                """
                
                if limit:
                    query += f" LIMIT {limit};"
                else:
                    query += ";"
                
                cur.execute(query, (book_id,))
                results = cur.fetchall()
                
                if not results:
                    return jsonify({"error": "Book not found"}), 404
                
                chapters = []
                for i, row in enumerate(results, 1):
                    chapter = {
                        "chapter_number": i,
                        "page_number": row['chunk_id'],
                        "preview": row['preview'] + "...",
                        "page_url": f"/api/shortcuts/books?id={book_id}&page={i}"
                    }
                    if include_word_counts:
                        chapter["word_count"] = row['word_count'] or 0
                    chapters.append(chapter)
                
                toc_response = {
                    "book_id": book_id,
                    "title": results[0]['title'],
                    "author": results[0]['author'],
                    "chapters": chapters,
                    "total_chapters": len(results),
                    "showing_all_chapters": limit is None,
                    "includes_word_counts": include_word_counts,
                    "shortcuts_navigation_ready": True,
                    "api_version": "v2.0_query_parameters"
                }
                
                if include_word_counts:
                    total_words = sum(chapter.get('word_count', 0) for chapter in chapters)
                    toc_response["total_word_count"] = total_words
                
                return jsonify(toc_response)
                
    except Exception as e:
        logger.error(f"Book TOC error: {e}")
        return jsonify({"error": "Table of contents unavailable"}), 500

def get_book_page(book_id: int, page_num):
    """Get specific book page with modern query parameter structure"""
    try:
        # Handle random page
        if str(page_num) == 'random' or request.args.get('page') == 'random':
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT chunk_id FROM chunks 
                        WHERE book_id = %s 
                        ORDER BY RANDOM() LIMIT 1;
                    """, (book_id,))
                    result = cur.fetchone()
                    if result:
                        # Extract page number from chunk_id format
                        chunk_id = result[0]
                        if '_' in chunk_id:
                            page_num = int(chunk_id.split('_')[1])
                        else:
                            page_num = 1
                    else:
                        return jsonify({"error": "No pages found"}), 404
        
        # Convert page number to chunk_id format
        chunk_id = f"{book_id}_{int(page_num):04d}"
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT c.content, c.chunk_id, c.word_count, b.title, b.author,
                           (SELECT COUNT(*) FROM chunks WHERE book_id = %s) as max_page
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.book_id = %s AND c.chunk_id = %s;
                """, (book_id, book_id, chunk_id))
                
                page_data = cur.fetchone()
                
                if not page_data:
                    return jsonify({"error": "Page not found"}), 404
                
                current_page = int(page_num)
                prev_page = current_page - 1 if current_page > 1 else None
                next_page = current_page + 1 if current_page < page_data['max_page'] else None
                
                return jsonify({
                    "book_id": book_id,
                    "title": page_data['title'],
                    "author": page_data['author'],
                    "current_page": current_page,
                    "total_pages": page_data['max_page'],
                    "word_count": page_data['word_count'] or 0,
                    "reading_time_minutes": round((page_data['word_count'] or 0) / 200, 1),
                    "page_content": page_data['content'],
                    "navigation": {
                        "previous_page": f"/api/shortcuts/books?id={book_id}&page={prev_page}" if prev_page else None,
                        "next_page": f"/api/shortcuts/books?id={book_id}&page={next_page}" if next_page else None,
                        "random_page": f"/api/shortcuts/books?id={book_id}&page=random",
                        "book_overview": f"/api/shortcuts/books?id={book_id}&action=construct",
                        "first_page": f"/api/shortcuts/books?id={book_id}&page=1",
                        "last_page": f"/api/shortcuts/books?id={book_id}&page={page_data['max_page']}"
                    },
                    "shortcuts_optimized": True,
                    "api_version": "v2.0_query_parameters"
                })
                
    except Exception as e:
        logger.error(f"Book page error: {e}")
        return jsonify({"error": "Page unavailable"}), 500

@shortcuts_v2_bp.route('/search')
@require_auth
def search_endpoint():
    """
    Universal search endpoint with query parameters
    
    Examples:
    - /search?term=philosophy&action=count
    - /search?term=philosophy&format=enhanced&include_metadata=true
    - /search?term=philosophy&fields=title,author,subject&limit=50
    """
    term = request.args.get('term')
    action = request.args.get('action', 'results')
    format_type = request.args.get('format', 'simple')
    fields = request.args.get('fields', 'title,author').split(',')
    limit = min(int(request.args.get('limit', 10)), 1000)
    include_metadata = request.args.get('include_metadata', 'false').lower() == 'true'
    
    if not term:
        return jsonify({"error": "Missing required parameter: term"}), 400
    
    try:
        if action == 'count':
            return get_search_count(term)
        elif action == 'has_results':
            return get_search_has_results(term)
        else:
            return get_search_results(term, format_type, fields, limit, include_metadata)
            
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return jsonify({"error": "Search endpoint unavailable"}), 500

def get_search_count(term: str):
    """Get search count with performance optimization"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Optimized search with proper full-text search
                cur.execute("""
                    SELECT COUNT(DISTINCT c.book_id) 
                    FROM chunks c
                    WHERE c.search_vector @@ plainto_tsquery('english', %s)
                       OR c.content % %s;  -- TRIGRAM MATCH
                """, (term, term))
                count = cur.fetchone()[0]
                return str(count), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Search count error: {e}")
        return "0", 500, {'Content-Type': 'text/plain'}

def get_search_has_results(term: str):
    """Check if search has results (boolean response)"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM chunks c
                        WHERE c.search_vector @@ plainto_tsquery('english', %s)
                           OR c.content % %s  -- TRIGRAM MATCH
                        LIMIT 1
                    );
                """, (term, term))
                has_results = cur.fetchone()[0]
                return str(has_results).lower(), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Search exists error: {e}")
        return "false", 500, {'Content-Type': 'text/plain'}

def get_search_results(term: str, format_type: str, fields: List[str], limit: int, include_metadata: bool):
    """Get search results with enhanced data"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Enhanced search query with proper ranking
                cur.execute("""
                    SELECT DISTINCT b.book_id, b.title, b.author, b.subject, b.publication_year,
                           b.word_count, b.genre,
                           ts_rank(c.search_vector, plainto_tsquery('english', %s)) as relevance_score
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id
                    WHERE c.search_vector @@ plainto_tsquery('english', %s)
                       OR c.content % %s  -- TRIGRAM MATCH
                    ORDER BY relevance_score DESC, b.title
                    LIMIT %s;
                """, (term, term, term, limit))
                
                results = cur.fetchall()
                
                if format_type == 'enhanced':
                    # Enhanced format with useful metadata
                    books = []
                    for row in results:
                        book = {
                            "book_id": row['book_id'],
                            "title": row['title'],
                            "author": row['author'],
                            "relevance_score": float(row['relevance_score']) if row['relevance_score'] else 0.0
                        }
                        
                        if include_metadata:
                            book.update({
                                "subject": row['subject'],
                                "publication_year": row['publication_year'],
                                "word_count": row['word_count'],
                                "genre": row['genre'],
                                "reading_time_minutes": round((row['word_count'] or 0) / 200)
                            })
                        
                        books.append(book)
                    
                    return jsonify({
                        "search_term": term,
                        "results_count": len(results),
                        "books": books,
                        "search_type": "enhanced",
                        "includes_metadata": include_metadata,
                        "shortcuts_optimized": True,
                        "api_version": "v2.0_query_parameters"
                    })
                else:
                    # Simple format - just what was requested
                    response = {
                        "search_term": term,
                        "count": len(results),
                        "has_results": len(results) > 0
                    }
                    
                    if 'title' in fields:
                        response["titles"] = [r['title'] for r in results]
                    if 'author' in fields:
                        response["authors"] = [r['author'] for r in results]
                    if 'book_id' in fields:
                        response["book_ids"] = [r['book_id'] for r in results]
                    if 'subject' in fields:
                        response["subjects"] = [r['subject'] for r in results]
                    
                    if results:
                        response.update({
                            "first_title": results[0]['title'],
                            "first_author": results[0]['author'],
                            "first_book_id": results[0]['book_id']
                        })
                    
                    response.update({
                        "shortcuts_optimized": True,
                        "api_version": "v2.0_query_parameters"
                    })
                    
                    return jsonify(response)
                
    except Exception as e:
        logger.error(f"Search results error: {e}")
        return jsonify({
            "search_term": term,
            "count": 0,
            "has_results": False,
            "error": "Search failed",
            "api_version": "v2.0_query_parameters"
        }), 500

@shortcuts_v2_bp.route('/lists')
@require_auth
def lists_endpoint():
    """
    Universal lists endpoint with query parameters
    
    Examples:
    - /lists?type=titles&limit=500&page=1
    - /lists?type=authors&limit=500&unique=true
    - /lists?type=subjects&limit=100&exclude_empty=true
    """
    list_type = request.args.get('type', 'titles')
    limit = min(int(request.args.get('limit', 50)), 1000)
    page = int(request.args.get('page', 1))
    unique = request.args.get('unique', 'false').lower() == 'true'
    exclude_empty = request.args.get('exclude_empty', 'true').lower() == 'true'
    format_type = request.args.get('format', 'array')
    
    offset = (page - 1) * limit
    
    try:
        if list_type == 'titles':
            return get_title_list(limit, offset, format_type)
        elif list_type == 'authors':
            return get_author_list(limit, offset, unique, exclude_empty, format_type)
        elif list_type == 'subjects':
            return get_subject_list(limit, offset, exclude_empty, format_type)
        else:
            return jsonify({"error": "Invalid list type. Use: titles, authors, subjects"}), 400
            
    except Exception as e:
        logger.error(f"Lists endpoint error: {e}")
        return jsonify({"error": "Lists endpoint unavailable"}), 500

def get_title_list(limit: int, offset: int, format_type: str):
    """Get list of book titles"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT title, author, book_id FROM books 
                    ORDER BY title 
                    LIMIT %s OFFSET %s;
                """, (limit, offset))
                results = cur.fetchall()
                
                if format_type == 'array':
                    return jsonify([row[0] for row in results])
                else:
                    return jsonify({
                        "titles": [{"title": row[0], "author": row[1], "book_id": row[2]} for row in results],
                        "count": len(results),
                        "page_info": {"limit": limit, "offset": offset},
                        "api_version": "v2.0_query_parameters"
                    })
    except Exception as e:
        logger.error(f"Title list error: {e}")
        return jsonify([])

def get_author_list(limit: int, offset: int, unique: bool, exclude_empty: bool, format_type: str):
    """Get list of authors"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                query = "SELECT "
                if unique:
                    query += "DISTINCT "
                query += "author FROM books"
                
                if exclude_empty:
                    query += " WHERE author IS NOT NULL AND author != ''"
                
                query += " ORDER BY author LIMIT %s OFFSET %s;"
                
                cur.execute(query, (limit, offset))
                results = cur.fetchall()
                
                if format_type == 'array':
                    return jsonify([row[0] for row in results])
                else:
                    return jsonify({
                        "authors": [row[0] for row in results],
                        "count": len(results),
                        "unique_only": unique,
                        "excludes_empty": exclude_empty,
                        "page_info": {"limit": limit, "offset": offset},
                        "api_version": "v2.0_query_parameters"
                    })
    except Exception as e:
        logger.error(f"Author list error: {e}")
        return jsonify([])

def get_subject_list(limit: int, offset: int, exclude_empty: bool, format_type: str):
    """Get list of subjects with book counts"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT subject, COUNT(*) as book_count 
                    FROM books
                """
                if exclude_empty:
                    query += " WHERE subject IS NOT NULL AND subject != ''"
                
                query += " GROUP BY subject ORDER BY book_count DESC, subject LIMIT %s OFFSET %s;"
                
                cur.execute(query, (limit, offset))
                results = cur.fetchall()
                
                if format_type == 'array':
                    return jsonify([row[0] for row in results])
                else:
                    return jsonify({
                        "subjects": [{"subject": row[0], "book_count": row[1]} for row in results],
                        "count": len(results),
                        "excludes_empty": exclude_empty,
                        "page_info": {"limit": limit, "offset": offset},
                        "api_version": "v2.0_query_parameters"
                    })
    except Exception as e:
        logger.error(f"Subject list error: {e}")
        return jsonify([])

@shortcuts_v2_bp.route('/random')
@require_auth
def random_endpoint():
    """
    Universal random content endpoint with query parameters
    
    Examples:
    - /random?type=book&include_metadata=true
    - /random?type=title&format=plain_text
    - /random?type=author&exclude_null=true
    """
    content_type = request.args.get('type', 'book')
    include_metadata = request.args.get('include_metadata', 'false').lower() == 'true'
    format_type = request.args.get('format', 'json')
    exclude_null = request.args.get('exclude_null', 'true').lower() == 'true'
    
    try:
        if content_type == 'book':
            return get_random_book(include_metadata)
        elif content_type == 'title':
            return get_random_title(format_type)
        elif content_type == 'author':
            return get_random_author(format_type, exclude_null)
        else:
            return jsonify({"error": "Invalid type. Use: book, title, author"}), 400
            
    except Exception as e:
        logger.error(f"Random endpoint error: {e}")
        return jsonify({"error": "Random endpoint unavailable"}), 500

def get_random_book(include_metadata: bool):
    """Get random book with optional metadata"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                if include_metadata:
                    cur.execute("""
                        SELECT book_id, title, author, subject, publication_year, word_count, genre
                        FROM books 
                        WHERE author IS NOT NULL 
                        ORDER BY RANDOM() 
                        LIMIT 1;
                    """)
                    result = cur.fetchone()
                    if result:
                        return jsonify({
                            "book_id": result[0],
                            "title": result[1],
                            "author": result[2],
                            "subject": result[3],
                            "publication_year": result[4],
                            "word_count": result[5],
                            "genre": result[6],
                            "reading_time_minutes": round((result[5] or 0) / 200),
                            "shortcuts_ready": True,
                            "api_version": "v2.0_query_parameters"
                        })
                else:
                    cur.execute("""
                        SELECT book_id, title, author 
                        FROM books 
                        WHERE author IS NOT NULL 
                        ORDER BY RANDOM() 
                        LIMIT 1;
                    """)
                    result = cur.fetchone()
                    if result:
                        return jsonify({
                            "book_id": result[0],
                            "title": result[1],
                            "author": result[2],
                            "shortcuts_ready": True,
                            "api_version": "v2.0_query_parameters"
                        })
                
                return jsonify({"error": "No books available"}), 404
                
    except Exception as e:
        logger.error(f"Random book error: {e}")
        return jsonify({"error": "Random book unavailable"}), 500

def get_random_title(format_type: str):
    """Get random book title"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT title FROM books ORDER BY RANDOM() LIMIT 1;")
                result = cur.fetchone()
                if result:
                    title = result[0]
                    if format_type == 'plain_text':
                        return title, 200, {'Content-Type': 'text/plain'}
                    else:
                        return jsonify({
                            "title": title,
                            "api_version": "v2.0_query_parameters"
                        })
                return jsonify({"error": "No titles available"}), 404
    except Exception as e:
        logger.error(f"Random title error: {e}")
        return jsonify({"error": "Random title unavailable"}), 500

def get_random_author(format_type: str, exclude_null: bool):
    """Get random author"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                query = "SELECT author FROM books"
                if exclude_null:
                    query += " WHERE author IS NOT NULL"
                query += " ORDER BY RANDOM() LIMIT 1;"
                
                cur.execute(query)
                result = cur.fetchone()
                if result:
                    author = result[0]
                    if format_type == 'plain_text':
                        return author, 200, {'Content-Type': 'text/plain'}
                    else:
                        return jsonify({
                            "author": author,
                            "api_version": "v2.0_query_parameters"
                        })
                return jsonify({"error": "No authors available"}), 404
    except Exception as e:
        logger.error(f"Random author error: {e}")
        return jsonify({"error": "Random author unavailable"}), 500

@shortcuts_v2_bp.route('/serendipity')
@require_auth
def serendipity_endpoint():
    """
    Universal serendipity endpoint with query parameters
    
    Examples:
    - /serendipity?type=passage&book_id=288&include_book_info=true
    - /serendipity?type=theme_blend&theme=philosophy&speed=fast
    - /serendipity?type=story_starter&max_time=5s
    """
    serendipity_type = request.args.get('type', 'passage')
    book_id = request.args.get('book_id', type=int)
    theme = request.args.get('theme')
    speed = request.args.get('speed', 'normal')
    max_time = request.args.get('max_time', '10s')
    include_book_info = request.args.get('include_book_info', 'true').lower() == 'true'
    count = min(int(request.args.get('count', 3)), 10)
    
    try:
        if serendipity_type == 'passage':
            return get_random_passage(book_id, include_book_info)
        elif serendipity_type == 'theme_blend':
            if not theme:
                return jsonify({"error": "Missing required parameter: theme"}), 400
            return get_theme_blend(theme, count, speed)
        elif serendipity_type == 'story_starter':
            return get_story_starter(max_time)
        elif serendipity_type == 'mixed_authors':
            return get_mixed_authors(count, speed)
        else:
            return jsonify({"error": "Invalid type. Use: passage, theme_blend, story_starter, mixed_authors"}), 400
            
    except Exception as e:
        logger.error(f"Serendipity endpoint error: {e}")
        return jsonify({"error": "Serendipity endpoint unavailable"}), 500

def get_random_passage(book_id: Optional[int], include_book_info: bool):
    """Get random passage with optional book targeting"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                if book_id:
                    # Get passage from specific book
                    cur.execute("""
                        SELECT b.title, b.author, b.book_id, c.content, c.chunk_id, c.word_count
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE c.book_id = %s AND LENGTH(c.content) > 200
                        ORDER BY RANDOM()
                        LIMIT 1;
                    """, (book_id,))
                else:
                    # Get passage from any book
                    cur.execute("""
                        SELECT b.title, b.author, b.book_id, c.content, c.chunk_id, c.word_count
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE LENGTH(c.content) > 200
                        ORDER BY RANDOM()
                        LIMIT 1;
                    """)
                
                result = cur.fetchone()
                
                if result:
                    passage = {
                        "passage": result['content'],
                        "word_count": result['word_count'] or 0,
                        "reading_time_minutes": round((result['word_count'] or 0) / 200, 1),
                        "chatgpt_prompt_ready": True,
                        "story_seed": f"Based on this passage, write a story...",
                        "serendipity_type": "random_passage",
                        "api_version": "v2.0_query_parameters"
                    }
                    
                    if include_book_info:
                        passage.update({
                            "book_id": result['book_id'],
                            "title": result['title'],
                            "author": result['author'],
                            "page_number": result['chunk_id'],
                            "book_url": f"/api/shortcuts/books?id={result['book_id']}&action=summary"
                        })
                    
                    return jsonify(passage)
                else:
                    return jsonify({"error": "No passages available"}), 404
                    
    except Exception as e:
        logger.error(f"Random passage error: {e}")
        return jsonify({"error": "Random passage unavailable"}), 500

def get_theme_blend(theme: str, count: int, speed: str):
    """Get theme-based content blend with performance optimization"""
    try:
        # Optimize for speed if requested
        if speed == 'fast':
            count = min(count, 5)
            content_limit = 200
        else:
            content_limit = 400
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, b.book_id, c.content, c.chunk_id
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.search_vector @@ plainto_tsquery('english', %s) 
                       OR c.content % %s  -- TRIGRAM MATCH
                    AND LENGTH(c.content) > 100
                    ORDER BY RANDOM()
                    LIMIT %s;
                """, (theme, theme, count))
                
                results = cur.fetchall()
                
                if results:
                    passages = []
                    for row in results:
                        content = row['content']
                        if len(content) > content_limit:
                            content = content[:content_limit] + "..."
                        
                        passages.append({
                            "book_id": row['book_id'],
                            "title": row['title'],
                            "author": row['author'],
                            "passage": content,
                            "page_number": row['chunk_id']
                        })
                    
                    return jsonify({
                        "theme": theme,
                        "passages": passages,
                        "source_count": len(results),
                        "unique_authors": list(set([row['author'] for row in results if row['author']])),
                        "chatgpt_story_prompt": f"Create an original story about '{theme}' inspired by these {len(results)} passages:",
                        "performance_mode": speed,
                        "serendipity_type": "theme_blend",
                        "api_version": "v2.0_query_parameters"
                    })
                else:
                    return jsonify({
                        "theme": theme,
                        "error": f"No passages found for theme '{theme}'",
                        "suggestion": "Try broader themes like 'love', 'technology', 'journey', 'mystery'",
                        "api_version": "v2.0_query_parameters"
                    }), 404
                    
    except Exception as e:
        logger.error(f"Theme blend error: {e}")
        return jsonify({"error": "Theme blend unavailable"}), 500

def get_story_starter(max_time: str):
    """Get story starter with time optimization"""
    try:
        # Parse max_time (5s, 10s, etc.)
        time_limit = int(max_time.replace('s', '')) if 's' in max_time else 10
        
        # Optimize query complexity based on time limit
        if time_limit <= 5:
            passage_count = 2
            author_count = 3
        else:
            passage_count = 3
            author_count = 5
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get story elements
                cur.execute("""
                    SELECT b.title, b.author, b.book_id, c.content
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE LENGTH(c.content) BETWEEN 200 AND 600
                    ORDER BY RANDOM()
                    LIMIT %s;
                """, (passage_count,))
                
                passages = cur.fetchall()
                
                cur.execute("""
                    SELECT DISTINCT author
                    FROM books
                    WHERE author IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT %s;
                """, (author_count,))
                authors = [row[0] for row in cur.fetchall()]
                
                if passages:
                    story_starter = {
                        "inspiration_passages": [
                            {
                                "book_id": passage['book_id'],
                                "source": f"{passage['title']} by {passage['author']}",
                                "text": passage['content'][:300] + "...",
                                "book_url": f"/api/shortcuts/books?id={passage['book_id']}&action=summary"
                            }
                            for passage in passages
                        ],
                        "author_styles_to_blend": authors[:3],
                        "performance_optimized_for": f"{time_limit} seconds",
                        "serendipity_type": "story_starter",
                        "ready_for_chatgpt": True,
                        "generated_at": datetime.now().isoformat(),
                        "api_version": "v2.0_query_parameters"
                    }
                    
                    # Create ChatGPT prompt
                    prompt_parts = []
                    for i, passage in enumerate(passages, 1):
                        prompt_parts.append(f'{i}. From "{passage["title"]}" by {passage["author"]}:\n{passage["content"][:200]}...\n')
                    
                    story_starter["chatgpt_complete_prompt"] = f"""Create an original short story that blends elements from these passages:

{chr(10).join(prompt_parts)}
Write in a style that combines influences from {', '.join(authors[:3])}.
Make it approximately 500-800 words."""
                    
                    return jsonify(story_starter)
                else:
                    return jsonify({"error": "No story material available"}), 404
                    
    except Exception as e:
        logger.error(f"Story starter error: {e}")
        return jsonify({"error": "Story starter unavailable"}), 500

def get_mixed_authors(count: int, speed: str):
    """Get mixed author content with performance optimization"""
    try:
        # Optimize for speed
        if speed == 'fast':
            count = min(count, 5)
            content_limit = 200
        else:
            content_limit = 300
        
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT b.author, b.title, b.book_id, c.content, c.chunk_id
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE LENGTH(c.content) > 150 AND b.author IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT %s;
                """, (count,))
                
                results = cur.fetchall()
                
                if results:
                    passages = []
                    for row in results:
                        content = row['content']
                        if len(content) > content_limit:
                            content = content[:content_limit] + "..."
                        
                        passages.append({
                            "book_id": row['book_id'],
                            "author": row['author'],
                            "title": row['title'],
                            "passage": content,
                            "page_number": row['chunk_id'],
                            "book_url": f"/api/shortcuts/books?id={row['book_id']}&action=summary"
                        })
                    
                    return jsonify({
                        "passages": passages,
                        "author_list": [row['author'] for row in results],
                        "title_list": [row['title'] for row in results],
                        "book_ids": [row['book_id'] for row in results],
                        "chatgpt_prompt": f"Create a story that blends the styles of {', '.join([row['author'] for row in results])}, using these passages as inspiration:",
                        "performance_mode": speed,
                        "serendipity_type": "mixed_authors",
                        "story_construction_ready": True,
                        "api_version": "v2.0_query_parameters"
                    })
                else:
                    return jsonify({"error": "No mixed content available"}), 404
                    
    except Exception as e:
        logger.error(f"Mixed authors error: {e}")
        return jsonify({"error": "Mixed content unavailable"}), 500

@shortcuts_v2_bp.route('/stats')
@require_auth
def stats_endpoint():
    """
    Universal statistics endpoint with query parameters
    
    Examples:
    - /stats?metric=book_count
    - /stats?type=dashboard&include_gaps=true
    - /stats?metric=collection_health
    """
    metric = request.args.get('metric')
    stats_type = request.args.get('type', 'dashboard')
    include_gaps = request.args.get('include_gaps', 'false').lower() == 'true'
    
    try:
        if metric == 'book_count':
            return get_book_count_stat()
        elif stats_type == 'dashboard':
            return get_stats_dashboard(include_gaps)
        elif metric == 'collection_health':
            return get_collection_health()
        else:
            return get_stats_dashboard(include_gaps)
            
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        return jsonify({"error": "Stats endpoint unavailable"}), 500

def get_book_count_stat():
    """Get simple book count"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books;")
                count = cur.fetchone()[0]
                return str(count), 200, {'Content-Type': 'text/plain'}
    except Exception as e:
        logger.error(f"Book count error: {e}")
        return "0", 500, {'Content-Type': 'text/plain'}

def get_stats_dashboard(include_gaps: bool):
    """Get comprehensive dashboard statistics"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Get comprehensive stats
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_books,
                        COUNT(DISTINCT author) as unique_authors,
                        COUNT(CASE WHEN subject IS NOT NULL AND subject != '' THEN 1 END) as books_with_subjects,
                        COUNT(CASE WHEN publication_year IS NOT NULL THEN 1 END) as books_with_years,
                        AVG(word_count) as avg_word_count,
                        SUM(word_count) as total_word_count
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
                        "total_word_count": int(book_stats['total_word_count'] or 0),
                        "avg_word_count": round(book_stats['avg_word_count'] or 0),
                        "avg_chunks_per_book": round(total_chunks / book_stats['total_books'], 1) if book_stats['total_books'] > 0 else 0,
                        "estimated_reading_hours": round((book_stats['total_word_count'] or 0) / 12000)  # 200 words/min * 60 min
                    },
                    "top_authors": top_authors,
                    "api_version": "v2.0_query_parameters"
                }
                
                if include_gaps:
                    total = book_stats['total_books']
                    dashboard["metadata_gaps"] = {
                        "missing_subjects": total - book_stats['books_with_subjects'],
                        "missing_years": total - book_stats['books_with_years'],
                        "subject_completeness_percent": round((book_stats['books_with_subjects'] / total) * 100, 1),
                        "year_completeness_percent": round((book_stats['books_with_years'] / total) * 100, 1)
                    }
                
                dashboard.update({
                    "data_jar_optimized": True,
                    "shortcuts_ready": True,
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                
                return jsonify(dashboard)
                
    except Exception as e:
        logger.error(f"Stats dashboard error: {e}")
        return jsonify({
            "error": "Stats unavailable",
            "timestamp": datetime.now().isoformat(),
            "api_version": "v2.0_query_parameters"
        }), 500

def get_collection_health():
    """Get collection health metrics"""
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_books,
                        COUNT(CASE WHEN author IS NOT NULL AND author != '' THEN 1 END) as has_author,
                        COUNT(CASE WHEN subject IS NOT NULL AND subject != '' THEN 1 END) as has_subject,
                        COUNT(CASE WHEN word_count > 0 THEN 1 END) as has_word_count
                    FROM books;
                """)
                stats = cur.fetchone()
                
                cur.execute("""
                    SELECT COUNT(*) as books_with_content
                    FROM books b
                    WHERE EXISTS (SELECT 1 FROM chunks c WHERE c.book_id = b.book_id);
                """)
                content_stats = cur.fetchone()
                
                total = stats['total_books']
                health_score = 0
                
                if total > 0:
                    author_score = (stats['has_author'] / total) * 25
                    subject_score = (stats['has_subject'] / total) * 25
                    content_score = (content_stats['books_with_content'] / total) * 30
                    word_count_score = (stats['has_word_count'] / total) * 20
                    health_score = author_score + subject_score + content_score + word_count_score
                
                return jsonify({
                    "collection_health_score": round(health_score, 1),
                    "total_books": total,
                    "completeness": {
                        "author_completeness": round((stats['has_author'] / total) * 100, 1) if total > 0 else 0,
                        "subject_completeness": round((stats['has_subject'] / total) * 100, 1) if total > 0 else 0,
                        "content_completeness": round((content_stats['books_with_content'] / total) * 100, 1) if total > 0 else 0,
                        "word_count_completeness": round((stats['has_word_count'] / total) * 100, 1) if total > 0 else 0
                    },
                    "health_grade": "A" if health_score >= 90 else "B" if health_score >= 80 else "C" if health_score >= 70 else "D",
                    "api_version": "v2.0_query_parameters",
                    "calculated_at": datetime.now().isoformat()
                })
                
    except Exception as e:
        logger.error(f"Collection health error: {e}")
        return jsonify({"error": "Collection health unavailable"}), 500

# ================================
# POSTGRESQL-FIRST SHORTCUTS ENDPOINTS
# ================================

@shortcuts_v2_bp.route('/search_pg')
@require_auth
def search_postgresql_endpoint():
    """
    PostgreSQL-First search endpoint
    
    Examples:
    - /search_pg?term=philosophy&action=count
    - /search_pg?term=philosophy&action=has_results
    - /search_pg?term=philosophy&fields=title&limit=10
    - /search_pg?term=philosophy&format=simple&limit=20
    """
    term = request.args.get('term', '').strip()
    action = request.args.get('action')
    fields = request.args.get('fields')
    format_type = request.args.get('format', 'simple')
    limit = min(int(request.args.get('limit', 10)), 100)
    
    if not term:
        return jsonify({"error": "Missing required parameter: term"}), 400
    
    try:
        conn = get_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if action == 'count':
                cur.execute("SELECT api_shortcuts_search_count(%s) as count", (term,))
                result = cur.fetchone()['count']
                return str(result), 200, {'Content-Type': 'text/plain'}
            
            elif action == 'has_results':
                cur.execute("SELECT api_shortcuts_search_has_results(%s) as has_results", (term,))
                result = cur.fetchone()['has_results']
                return str(1 if result else 0), 200, {'Content-Type': 'text/plain'}
            
            elif fields == 'title':
                cur.execute("SELECT api_shortcuts_search_titles(%s, %s) as titles", (term, limit))
                result = cur.fetchone()['titles']
                return jsonify(result or [])
            
            elif fields == 'author':
                # Use books search for authors
                cur.execute("""
                    SELECT DISTINCT author 
                    FROM books 
                    WHERE LOWER(author) LIKE LOWER(%s) 
                    LIMIT %s
                """, (f'%{term}%', limit))
                results = [row['author'] for row in cur.fetchall()]
                return jsonify(results)
            
            else:
                cur.execute("SELECT * FROM api_shortcuts_search_simple(%s, %s)", (term, limit))
                result = dict(cur.fetchone())
                return jsonify(result)
                
    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        return jsonify({"error": "Search endpoint unavailable"}), 500

@shortcuts_v2_bp.route('/lists_pg')
@require_auth
def lists_postgresql_endpoint():
    """
    Lists endpoint with PostgreSQL functions
    
    Examples:
    - /lists_pg?type=titles&limit=100
    - /lists_pg?type=authors&limit=500
    """
    list_type = request.args.get('type', 'titles')
    limit = min(int(request.args.get('limit', 100)), 500)
    page = int(request.args.get('page', 1))
    
    try:
        conn = get_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if list_type == 'titles':
                cur.execute("SELECT api_shortcuts_list_titles(%s, %s) as titles", (limit, page))
                result = cur.fetchone()['titles']
                return jsonify(result or [])
            
            elif list_type == 'authors':
                cur.execute("SELECT api_shortcuts_list_authors(%s, %s) as authors", (limit, page))
                result = cur.fetchone()['authors']
                return jsonify(result or [])
            
            else:
                return jsonify({"error": f"Invalid list type: {list_type}"}), 400
                
    except Exception as e:
        logger.error(f"Lists endpoint error: {e}")
        return jsonify({"error": "Lists endpoint unavailable"}), 500

@shortcuts_v2_bp.route('/random_pg')
@require_auth
def random_postgresql_endpoint():
    """
    Random content endpoint with PostgreSQL functions
    
    Examples:
    - /random_pg?type=title
    - /random_pg?type=author
    - /random_pg?type=citation
    - /random_pg?type=share_text
    """
    random_type = request.args.get('type', 'title')
    include_metadata = request.args.get('include_metadata', 'false').lower() == 'true'
    
    try:
        conn = get_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if random_type == 'title':
                cur.execute("SELECT api_shortcuts_random_title() as data")
                result = cur.fetchone()['data']
                if include_metadata:
                    return jsonify(result)
                return result['title'], 200, {'Content-Type': 'text/plain'}
            
            elif random_type == 'author':
                cur.execute("SELECT api_shortcuts_random_author() as data")
                result = cur.fetchone()['data']
                if include_metadata:
                    return jsonify(result)
                return result['author'], 200, {'Content-Type': 'text/plain'}
            
            elif random_type == 'citation':
                cur.execute("SELECT api_shortcuts_random_citation() as data")
                result = cur.fetchone()['data']
                if include_metadata:
                    return jsonify(result)
                return result['citation'], 200, {'Content-Type': 'text/plain'}
            
            elif random_type == 'share_text':
                cur.execute("SELECT api_shortcuts_random_share_text() as data")
                result = cur.fetchone()['data']
                if include_metadata:
                    return jsonify(result)
                return result['share_text'], 200, {'Content-Type': 'text/plain'}
                
            else:
                return jsonify({"error": f"Invalid random type: {random_type}"}), 400
                
    except Exception as e:
        logger.error(f"Random endpoint error: {e}")
        return jsonify({"error": "Random endpoint unavailable"}), 500

# Update books endpoint to use PostgreSQL functions
@shortcuts_v2_bp.route('/books_pg')
@require_auth
def books_postgresql_endpoint():
    """
    Books endpoint using PostgreSQL functions
    
    Examples:
    - /books_pg?id=288&action=summary
    - /books_pg?id=288&action=construct
    - /books_pg?id=288&action=toc
    - /books_pg?id=288&page=1
    - /books_pg?id=288&page=random
    """
    book_id = request.args.get('id', type=int)
    action = request.args.get('action', 'summary')
    page = request.args.get('page')
    
    if not book_id:
        return jsonify({"error": "Missing required parameter: id"}), 400
    
    try:
        conn = get_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if action == 'summary':
                cur.execute("SELECT * FROM api_shortcuts_book_summary(%s)", (book_id,))
                result = dict(cur.fetchone())
                return jsonify(result)
            
            elif action == 'construct':
                cur.execute("SELECT * FROM api_shortcuts_book_construct(%s)", (book_id,))
                result = dict(cur.fetchone())
                return jsonify(result)
            
            elif action == 'toc':
                cur.execute("SELECT * FROM api_shortcuts_book_toc(%s)", (book_id,))
                result = dict(cur.fetchone())
                return jsonify(result)
            
            elif page:
                if page == 'random':
                    cur.execute("SELECT * FROM api_shortcuts_book_random_page(%s)", (book_id,))
                else:
                    page_num = int(page)
                    cur.execute("SELECT * FROM api_shortcuts_book_page(%s, %s)", (book_id, page_num))
                
                result = dict(cur.fetchone())
                return jsonify(result)
            
            else:
                return jsonify({"error": "Invalid action or missing page parameter"}), 400
                
    except Exception as e:
        logger.error(f"Books PostgreSQL endpoint error: {e}")
        return jsonify({"error": "Books endpoint unavailable"}), 500

# Update stats endpoint to use PostgreSQL functions
@shortcuts_v2_bp.route('/stats_pg')
@require_auth
def stats_postgresql_endpoint():
    """
    Stats endpoint using PostgreSQL functions
    
    Examples:
    - /stats_pg?metric=book_count
    - /stats_pg?metric=collection_health
    - /stats_pg?type=dashboard&include_gaps=true
    """
    metric = request.args.get('metric')
    stats_type = request.args.get('type', 'dashboard')
    include_gaps = request.args.get('include_gaps', 'false').lower() == 'true'
    
    try:
        conn = get_db()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if metric == 'book_count':
                cur.execute("SELECT api_shortcuts_book_count() as count")
                result = cur.fetchone()['count']
                return str(result), 200, {'Content-Type': 'text/plain'}
            
            elif metric == 'collection_health':
                cur.execute("SELECT * FROM api_shortcuts_collection_health()")
                result = dict(cur.fetchone())
                return jsonify(result)
            
            elif stats_type == 'dashboard':
                cur.execute("SELECT * FROM api_shortcuts_dashboard(%s)", (include_gaps,))
                result = dict(cur.fetchone())
                return jsonify(result)
            
            else:
                return jsonify({"error": f"Invalid metric or type"}), 400
                
    except Exception as e:
        logger.error(f"Stats PostgreSQL endpoint error: {e}")
        return jsonify({"error": "Stats endpoint unavailable"}), 500

# ================================
# HEALTH CHECK AND DEPRECATION NOTICES
# ================================

@shortcuts_v2_bp.route('/health')
def shortcuts_health_v2():
    """Health check for modern shortcuts namespace"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books LIMIT 1;")
                cur.fetchone()
                
        return jsonify({
            "status": "healthy",
            "namespace": "shortcuts_v2",
            "api_version": "v2.0_query_parameters",
            "endpoints_available": [
                "/books?id={id}&action={summary|construct|toc}",
                "/books?id={id}&page={number|random}",
                "/search?term={term}&action={count|has_results}",
                "/search?term={term}&format={simple|enhanced}&include_metadata={true|false}",
                "/lists?type={titles|authors|subjects}&limit={num}&page={num}",
                "/random?type={book|title|author}&include_metadata={true|false}",
                "/serendipity?type={passage|theme_blend|story_starter|mixed_authors}",
                "/stats?metric={book_count|collection_health}",
                "/stats?type=dashboard&include_gaps={true|false}"
            ],
            "designed_by": "Dr. Elena Rodriguez (IAV)",
            "philosophy": "Information architecture makes complex knowledge feel simple",
            "modernization": "Complete elimination of forward slash navigation",
            "user_feedback_addressed": "No more forward slash URL navigation",
            "optimized_for": ["iOS Shortcuts", "Data Jar", "Modern RESTful APIs"],
            "deprecated_endpoints": [
                "Legacy /search/{term}/* endpoints",
                "Legacy /books/{id}/page/{num} endpoints",
                "Legacy /serendipity/* path-based endpoints"
            ],
            "migration_guide": "Replace path segments with query parameters",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Shortcuts health check error: {e}")
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "namespace": "shortcuts_v2"
        }), 500

# Register the blueprint with the main app
def register_shortcuts_v2_blueprint(app):
    """Register modern shortcuts blueprint with Flask app"""
    app.register_blueprint(shortcuts_v2_bp)
    logger.info("🎯 Dr. Elena Rodriguez's Modern Query-Parameter iOS Shortcuts API v2.0 registered!")
    logger.info("📱 Available at /api/shortcuts/* - No more forward slash navigation!")
    logger.info("🚀 User feedback addressed: Complete query-parameter based structure!")

if __name__ == "__main__":
    # For testing purposes
    import os
    app = Flask(__name__)
    register_shortcuts_v2_blueprint(app)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port)