#!/usr/bin/env python3
"""
📖 LibraryOfBabel Book-Specific Search API
Provides highlight search, page navigation, and book-specific functionality
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

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'knowledge_base'),
    'user': os.getenv('DB_USER', 'weixiangzhang'),
    'port': 5432
}

def get_db():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        return None

class BookSearchEngine:
    def __init__(self):
        self.db_config = DB_CONFIG
    
    def search_within_book(self, book_id: int, query: str, highlight: bool = True) -> Dict[str, Any]:
        """Search for text within a specific book with optional highlighting"""
        conn = get_db()
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
                
                # Find context around matches
                matches = self._find_matches_with_context(content, query)
                
                result = {
                    'chunk_id': chunk['chunk_id'],
                    'chunk_type': chunk['chunk_type'],
                    'chapter_number': chunk['chapter_number'],
                    'section_number': chunk['section_number'],
                    'word_count': chunk['word_count'],
                    'relevance_score': round(float(chunk['relevance']), 4),
                    'highlighted_content': highlighted_content,
                    'matches': matches,
                    'position_info': {
                        'start_position': chunk['start_position'],
                        'end_position': chunk['end_position']
                    }
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
    
    def get_book_outline(self, book_id: int) -> Dict[str, Any]:
        """Get book structure with chapters and sections"""
        conn = get_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get book info
            cursor.execute("""
                SELECT book_id, title, author, publication_year, word_count
                FROM books 
                WHERE book_id = %s
            """, (book_id,))
            
            book_info = cursor.fetchone()
            if not book_info:
                return {"error": f"Book with ID {book_id} not found"}
            
            # Get chapter structure
            cursor.execute("""
                SELECT 
                    chunk_id, chunk_type, chapter_number, section_number,
                    title, word_count, start_position, end_position,
                    LEFT(content, 200) as preview
                FROM chunks 
                WHERE book_id = %s 
                ORDER BY chapter_number, section_number
            """, (book_id,))
            
            chunks = cursor.fetchall()
            
            # Organize by chapters
            chapters = {}
            for chunk in chunks:
                chapter_num = chunk['chapter_number'] or 0
                
                if chapter_num not in chapters:
                    chapters[chapter_num] = {
                        'chapter_number': chapter_num,
                        'sections': [],
                        'total_words': 0
                    }
                
                chapters[chapter_num]['sections'].append({
                    'chunk_id': chunk['chunk_id'],
                    'chunk_type': chunk['chunk_type'],
                    'section_number': chunk['section_number'],
                    'title': chunk['title'],
                    'word_count': chunk['word_count'],
                    'preview': chunk['preview'],
                    'position': {
                        'start': chunk['start_position'],
                        'end': chunk['end_position']
                    }
                })
                chapters[chapter_num]['total_words'] += chunk['word_count'] or 0
            
            return {
                'book_info': dict(book_info),
                'chapters': list(chapters.values()),
                'total_chapters': len(chapters)
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            conn.close()
    
    def get_chapter_content(self, book_id: int, chapter_number: int) -> Dict[str, Any]:
        """Get full content of a specific chapter"""
        conn = get_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get book info
            cursor.execute("""
                SELECT title, author FROM books WHERE book_id = %s
            """, (book_id,))
            
            book_info = cursor.fetchone()
            if not book_info:
                return {"error": f"Book with ID {book_id} not found"}
            
            # Get chapter content
            cursor.execute("""
                SELECT 
                    chunk_id, chunk_type, section_number, title,
                    content, word_count, start_position, end_position
                FROM chunks 
                WHERE book_id = %s AND chapter_number = %s
                ORDER BY section_number
            """, (book_id, chapter_number))
            
            sections = cursor.fetchall()
            
            if not sections:
                return {"error": f"Chapter {chapter_number} not found in book {book_id}"}
            
            return {
                'book_info': dict(book_info),
                'chapter_number': chapter_number,
                'sections': [dict(section) for section in sections],
                'total_sections': len(sections),
                'total_words': sum(s['word_count'] or 0 for s in sections)
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            conn.close()
    
    def search_across_books(self, query: str, author_filter: str = None) -> Dict[str, Any]:
        """Search across multiple books with optional author filter"""
        conn = get_db()
        if not conn:
            return {"error": "Database connection failed"}
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Build query with optional author filter
            if author_filter:
                where_clause = """
                    WHERE c.search_vector @@ plainto_tsquery('english', %s)
                    AND b.author ILIKE %s
                """
                params = (query, f'%{author_filter}%')
            else:
                where_clause = """
                    WHERE c.search_vector @@ plainto_tsquery('english', %s)
                """
                params = (query,)
            
            cursor.execute(f"""
                SELECT 
                    b.book_id, b.title, b.author, b.publication_year,
                    c.chunk_id, c.chunk_type, c.chapter_number,
                    c.content, c.word_count,
                    ts_rank(c.search_vector, plainto_tsquery('english', %s)) as relevance,
                    COUNT(*) OVER (PARTITION BY b.book_id) as book_matches
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                {where_clause}
                ORDER BY relevance DESC, b.title, c.chapter_number
                LIMIT 50
            """, (query,) + params)
            
            results = cursor.fetchall()
            
            # Group by book
            books = {}
            for result in results:
                book_id = result['book_id']
                
                if book_id not in books:
                    books[book_id] = {
                        'book_info': {
                            'book_id': book_id,
                            'title': result['title'],
                            'author': result['author'],
                            'publication_year': result['publication_year']
                        },
                        'total_matches': result['book_matches'],
                        'best_matches': []
                    }
                
                # Add highlighted content
                highlighted_content = self._highlight_text(result['content'], query)
                
                books[book_id]['best_matches'].append({
                    'chunk_id': result['chunk_id'],
                    'chunk_type': result['chunk_type'],
                    'chapter_number': result['chapter_number'],
                    'relevance_score': round(float(result['relevance']), 4),
                    'highlighted_content': highlighted_content[:500] + "..." if len(highlighted_content) > 500 else highlighted_content
                })
            
            return {
                'query': query,
                'author_filter': author_filter,
                'total_books_found': len(books),
                'books': list(books.values())
            }
            
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            conn.close()
    
    def _highlight_text(self, text: str, query: str) -> str:
        """Add HTML highlighting to search matches"""
        # Split query into individual terms
        terms = query.lower().split()
        
        highlighted = text
        for term in terms:
            # Use regex for case-insensitive highlighting
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(lambda m: f'<mark>{m.group()}</mark>', highlighted)
        
        return highlighted
    
    def _find_matches_with_context(self, content: str, query: str, context_chars: int = 100) -> List[Dict[str, Any]]:
        """Find all matches with surrounding context"""
        terms = query.lower().split()
        matches = []
        
        for term in terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            for match in pattern.finditer(content):
                start_pos = max(0, match.start() - context_chars)
                end_pos = min(len(content), match.end() + context_chars)
                
                context = content[start_pos:end_pos]
                highlighted_context = self._highlight_text(context, term)
                
                matches.append({
                    'term': term,
                    'position': match.start(),
                    'context': highlighted_context,
                    'context_start': start_pos,
                    'context_end': end_pos
                })
        
        return matches

# Initialize search engine
search_engine = BookSearchEngine()

# API Routes
@app.route('/api/book/search/<int:book_id>')
def search_in_book(book_id):
    """Search within a specific book"""
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
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/book/outline/<int:book_id>')
def get_book_outline(book_id):
    """Get book structure and outline"""
    start_time = time.time()
    result = search_engine.get_book_outline(book_id)
    
    return jsonify({
        'success': 'error' not in result,
        'data': result,
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/book/chapter/<int:book_id>/<int:chapter_number>')
def get_chapter_content(book_id, chapter_number):
    """Get full content of a specific chapter"""
    start_time = time.time()
    result = search_engine.get_chapter_content(book_id, chapter_number)
    
    return jsonify({
        'success': 'error' not in result,
        'data': result,
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/book/search-across')
def search_across_books():
    """Search across multiple books"""
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
        'response_time_ms': round((time.time() - start_time) * 1000, 2),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/book/list')
def list_books():
    """List all available books"""
    conn = get_db()
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
            'timestamp': datetime.now().isoformat()
        })
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/book/docs')
def get_api_docs():
    """API documentation"""
    docs = {
        'title': 'LibraryOfBabel Book Search API',
        'version': '1.0',
        'description': 'Book-specific search with highlighting and navigation',
        'endpoints': {
            'list_books': {
                'path': '/api/book/list',
                'method': 'GET',
                'description': 'List all available books',
                'example': 'GET /api/book/list'
            },
            'book_outline': {
                'path': '/api/book/outline/<book_id>',
                'method': 'GET',
                'description': 'Get book structure and chapter outline',
                'example': 'GET /api/book/outline/123'
            },
            'search_in_book': {
                'path': '/api/book/search/<book_id>',
                'method': 'GET',
                'description': 'Search within a specific book with highlighting',
                'parameters': {
                    'q': 'Search query (required)',
                    'highlight': 'Enable highlighting (true/false, default: true)'
                },
                'example': 'GET /api/book/search/123?q=consciousness&highlight=true'
            },
            'chapter_content': {
                'path': '/api/book/chapter/<book_id>/<chapter_number>',
                'method': 'GET',
                'description': 'Get full content of specific chapter',
                'example': 'GET /api/book/chapter/123/5'
            },
            'search_across_books': {
                'path': '/api/book/search-across',
                'method': 'GET',
                'description': 'Search across multiple books with optional author filter',
                'parameters': {
                    'q': 'Search query (required)',
                    'author': 'Author filter (optional)'
                },
                'example': 'GET /api/book/search-across?q=power&author=Foucault'
            }
        }
    }
    
    return jsonify({
        'success': True,
        'data': docs,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("📖 Starting LibraryOfBabel Book Search API...")
    print("🔍 Features:")
    print("   • Highlight search within books")
    print("   • Chapter/page navigation")
    print("   • Cross-book search with author filtering")
    print("   • Book outlines and structure")
    print("")
    print("📚 API Endpoints:")
    print("   • GET /api/book/list - List all books")
    print("   • GET /api/book/outline/<book_id> - Book structure")
    print("   • GET /api/book/search/<book_id>?q=query - Search within book")
    print("   • GET /api/book/chapter/<book_id>/<chapter> - Chapter content")
    print("   • GET /api/book/search-across?q=query - Search across books")
    print("   • GET /api/book/docs - API documentation")
    print("")
    print("🌐 Starting server on http://localhost:5561")
    
    app.run(host='0.0.0.0', port=5561, debug=False)