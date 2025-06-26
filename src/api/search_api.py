#!/usr/bin/env python3
"""
LibraryOfBabel Search API
RESTful API for AI research agents to query the knowledge base
"""

from flask import Flask, request, jsonify, g
import psycopg2
import psycopg2.extras
import logging
import time
import re
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'postgres',
    'port': 5432
}

def get_db():
    """Get database connection with automatic cleanup"""
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(**DB_CONFIG)
            g.db.autocommit = True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return None
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def close_db(error):
    close_db()

def format_search_results(results: List[Dict], query_time: float, total_count: int = None) -> Dict:
    """Format search results for AI agent consumption"""
    return {
        "query_metadata": {
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(query_time * 1000, 2),
            "total_results": total_count or len(results),
            "api_version": "1.0"
        },
        "results": results,
        "search_suggestions": generate_search_suggestions(results)
    }

def generate_search_suggestions(results: List[Dict]) -> List[str]:
    """Generate related search suggestions based on results"""
    if not results:
        return []
    
    # Extract common themes from results for suggestions
    suggestions = []
    authors = set()
    topics = set()
    
    for result in results[:5]:  # Analyze top 5 results
        if 'author' in result:
            authors.add(result['author'])
        # Extract key terms from content for topic suggestions
        content = result.get('content', '').lower()
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b[a-z]{4,}\b', content)
        topics.update(words[:3])  # Top 3 words per result
    
    # Generate suggestions
    if authors:
        suggestions.extend([f"More books by {author}" for author in list(authors)[:2]])
    if topics:
        suggestions.extend([f"Related to {topic}" for topic in list(topics)[:2]])
    
    return suggestions[:4]  # Limit to 4 suggestions

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    start_time = time.time()
    
    try:
        db = get_db()
        if not db:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        
        response_time = (time.time() - start_time) * 1000
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "books_indexed": book_count,
            "chunks_indexed": chunk_count,
            "response_time_ms": round(response_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/search', methods=['GET', 'POST'])
def search():
    """Main search endpoint supporting multiple query types"""
    start_time = time.time()
    
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            search_type = data.get('type', 'content')
            limit = data.get('limit', 10)
            highlight = data.get('highlight', True)
        else:
            query = request.args.get('q', '')
            search_type = request.args.get('type', 'content')
            limit = int(request.args.get('limit', 10))
            highlight = request.args.get('highlight', 'true').lower() == 'true'
        
        if not query:
            return jsonify({"error": "Query parameter required"}), 400
        
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Route to appropriate search function
        if search_type == 'content':
            results = search_content(cursor, query, limit, highlight)
        elif search_type == 'author':
            results = search_by_author(cursor, query, limit)
        elif search_type == 'title':
            results = search_by_title(cursor, query, limit)
        elif search_type == 'cross_reference':
            # Expects comma-separated concepts
            concepts = [c.strip() for c in query.split(',')]
            if len(concepts) < 2:
                return jsonify({"error": "Cross-reference search requires at least 2 concepts"}), 400
            results = search_cross_reference(cursor, concepts, limit)
        else:
            return jsonify({"error": f"Unsupported search type: {search_type}"}), 400
        
        query_time = time.time() - start_time
        response = format_search_results(results, query_time)
        
        logger.info(f"Search completed: query='{query}', type={search_type}, results={len(results)}, time={query_time:.3f}s")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return jsonify({"error": "Search failed", "details": str(e)}), 500

def search_content(cursor, query: str, limit: int, highlight: bool = True) -> List[Dict]:
    """Full-text search across all content"""
    if highlight:
        sql = """
        SELECT 
            b.title,
            b.author,
            b.publication_year,
            c.chunk_type,
            c.chapter_number,
            c.word_count,
            ts_headline('english', c.content, plainto_tsquery('english', %s), 
                       'MaxFragments=2,MaxWords=50,MinWords=20') as highlighted_content,
            ts_rank(c.search_vector, plainto_tsquery('english', %s)) as relevance_rank
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY relevance_rank DESC
        LIMIT %s
        """
        cursor.execute(sql, (query, query, query, limit))
    else:
        sql = """
        SELECT 
            b.title,
            b.author,
            b.publication_year,
            c.chunk_type,
            c.chapter_number,
            c.word_count,
            LEFT(c.content, 200) as content_preview,
            ts_rank(c.search_vector, plainto_tsquery('english', %s)) as relevance_rank
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY relevance_rank DESC
        LIMIT %s
        """
        cursor.execute(sql, (query, query, limit))
    
    return [dict(row) for row in cursor.fetchall()]

def search_by_author(cursor, author_query: str, limit: int) -> List[Dict]:
    """Search for books by specific author"""
    sql = """
    SELECT DISTINCT
        b.title,
        b.author,
        b.publication_year,
        b.genre,
        b.word_count,
        COUNT(c.chunk_id) as total_chunks
    FROM books b
    LEFT JOIN chunks c ON b.book_id = c.book_id
    WHERE b.author ILIKE %s
    GROUP BY b.book_id, b.title, b.author, b.publication_year, b.genre, b.word_count
    ORDER BY b.publication_year DESC
    LIMIT %s
    """
    cursor.execute(sql, (f'%{author_query}%', limit))
    return [dict(row) for row in cursor.fetchall()]

def search_by_title(cursor, title_query: str, limit: int) -> List[Dict]:
    """Search for books by title"""
    sql = """
    SELECT 
        b.title,
        b.author,
        b.publication_year,
        b.genre,
        b.word_count,
        COUNT(c.chunk_id) as total_chunks
    FROM books b
    LEFT JOIN chunks c ON b.book_id = c.book_id
    WHERE b.title ILIKE %s
    GROUP BY b.book_id, b.title, b.author, b.publication_year, b.genre, b.word_count
    ORDER BY b.title
    LIMIT %s
    """
    cursor.execute(sql, (f'%{title_query}%', limit))
    return [dict(row) for row in cursor.fetchall()]

def search_cross_reference(cursor, concepts: List[str], limit: int) -> List[Dict]:
    """Find books that discuss multiple concepts"""
    # Build query for books containing all concepts
    conditions = []
    params = []
    
    for concept in concepts:
        conditions.append("c.search_vector @@ plainto_tsquery('english', %s)")
        params.append(concept)
    
    sql = f"""
    SELECT 
        b.title,
        b.author,
        b.publication_year,
        COUNT(DISTINCT c.chunk_id) as matching_chunks,
        STRING_AGG(DISTINCT c.chunk_type, ', ') as chunk_types,
        AVG(ts_rank(c.search_vector, plainto_tsquery('english', %s))) as avg_relevance
    FROM books b
    JOIN chunks c ON b.book_id = c.book_id
    WHERE {' AND '.join(conditions)}
    GROUP BY b.book_id, b.title, b.author, b.publication_year
    HAVING COUNT(DISTINCT c.chunk_id) > 0
    ORDER BY matching_chunks DESC, avg_relevance DESC
    LIMIT %s
    """
    
    # Add the first concept for relevance ranking and the limit
    params = [concepts[0]] + params + [limit]
    cursor.execute(sql, params)
    
    return [dict(row) for row in cursor.fetchall()]

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get knowledge base statistics"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get comprehensive statistics
        stats_queries = {
            'total_books': "SELECT COUNT(*) as count FROM books",
            'total_chunks': "SELECT COUNT(*) as count FROM chunks",
            'total_words': "SELECT SUM(word_count) as count FROM books",
            'chunk_types': """
                SELECT chunk_type, COUNT(*) as count 
                FROM chunks 
                GROUP BY chunk_type 
                ORDER BY count DESC
            """,
            'top_authors': """
                SELECT author, COUNT(*) as book_count, SUM(word_count) as total_words
                FROM books 
                WHERE author IS NOT NULL
                GROUP BY author 
                ORDER BY book_count DESC 
                LIMIT 5
            """,
            'processing_stats': """
                SELECT 
                    AVG(word_count) as avg_words_per_book,
                    MAX(word_count) as max_words_per_book,
                    MIN(word_count) as min_words_per_book
                FROM books
            """
        }
        
        stats = {}
        for stat_name, query in stats_queries.items():
            cursor.execute(query)
            if stat_name in ['chunk_types', 'top_authors']:
                stats[stat_name] = [dict(row) for row in cursor.fetchall()]
            else:
                result = cursor.fetchone()
                stats[stat_name] = dict(result) if result else {}
        
        return jsonify({
            "knowledge_base_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return jsonify({"error": "Failed to retrieve stats", "details": str(e)}), 500

@app.route('/api/suggest', methods=['GET'])
def suggest_queries():
    """Suggest search queries based on content analysis"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get popular terms and concepts for suggestions
        suggestions = {
            'popular_authors': [],
            'suggested_topics': [],
            'recent_books': []
        }
        
        # Popular authors
        cursor.execute("""
            SELECT author, COUNT(*) as book_count
            FROM books 
            WHERE author IS NOT NULL
            GROUP BY author 
            ORDER BY book_count DESC 
            LIMIT 5
        """)
        suggestions['popular_authors'] = [row['author'] for row in cursor.fetchall()]
        
        # Recent books (by publication year)
        cursor.execute("""
            SELECT title, author, publication_year
            FROM books 
            WHERE publication_year IS NOT NULL
            ORDER BY publication_year DESC 
            LIMIT 5
        """)
        suggestions['recent_books'] = [
            f"{row['title']} by {row['author']}" 
            for row in cursor.fetchall()
        ]
        
        # Suggested search patterns
        suggestions['search_examples'] = [
            "Search by content: 'artificial intelligence'",
            "Search by author: 'type=author&q=AuthorName'",
            "Cross-reference: 'type=cross_reference&q=democracy,technology'",
            "Find titles: 'type=title&q=history'"
        ]
        
        return jsonify({
            "suggestions": suggestions,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Suggestion generation failed: {e}")
        return jsonify({"error": "Failed to generate suggestions", "details": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🚀 LibraryOfBabel Search API Starting...")
    print("📚 Endpoints available:")
    print("   GET  /api/health - API health check")
    print("   GET  /api/search - Search knowledge base")
    print("   POST /api/search - Advanced search with JSON payload")
    print("   GET  /api/stats - Knowledge base statistics")
    print("   GET  /api/suggest - Search suggestions")
    print("🔍 Ready for AI research agent queries!")
    
    app.run(host='0.0.0.0', port=5000, debug=False)