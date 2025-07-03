#!/usr/bin/env python3
"""
LibraryOfBabel Hybrid Search API
Combines exact reference navigation with semantic discovery
"""

from flask import Flask, request, jsonify, g
import psycopg2
import psycopg2.extras
import logging
import time
import re
import os
from typing import Dict, List, Any, Optional
import json
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
    """Get database connection with automatic cleanup"""
    if 'db' not in g:
        try:
            g.db = psycopg2.connect(**DB_CONFIG)
            g.db.autocommit = True
        except psycopg2.Error as e:
            logger.error(f"Database connection failed: {e}")
            return None
    return g.db

def close_db_connection(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.teardown_appcontext
def close_db(error):
    close_db_connection()

def get_chunk_navigation(cursor, chunk_id: str) -> Dict:
    """Get navigation info for a chunk (previous/next in same book)"""
    try:
        # Get current chunk info
        cursor.execute("""
            SELECT book_id, chapter_number, section_number, chunk_type
            FROM chunks 
            WHERE chunk_id = %s
        """, (chunk_id,))
        
        current = cursor.fetchone()
        if not current:
            return {}
        
        book_id, chapter_num, section_num, chunk_type = current
        
        # Get previous chunk in same book
        cursor.execute("""
            SELECT chunk_id, chapter_number, section_number, chunk_type,
                   LEFT(content, 100) as preview
            FROM chunks 
            WHERE book_id = %s 
              AND (chapter_number < %s OR 
                   (chapter_number = %s AND section_number < %s))
            ORDER BY chapter_number DESC, section_number DESC
            LIMIT 1
        """, (book_id, chapter_num, chapter_num, section_num or 0))
        
        prev_chunk = cursor.fetchone()
        
        # Get next chunk in same book
        cursor.execute("""
            SELECT chunk_id, chapter_number, section_number, chunk_type,
                   LEFT(content, 100) as preview
            FROM chunks 
            WHERE book_id = %s 
              AND (chapter_number > %s OR 
                   (chapter_number = %s AND section_number > %s))
            ORDER BY chapter_number ASC, section_number ASC
            LIMIT 1
        """, (book_id, chapter_num, chapter_num, section_num or 0))
        
        next_chunk = cursor.fetchone()
        
        # Get chapter outline for context
        cursor.execute("""
            SELECT DISTINCT chapter_number, 
                   LEFT(content, 150) as chapter_title
            FROM chunks 
            WHERE book_id = %s AND chunk_type = 'chapter'
            ORDER BY chapter_number
        """, (book_id,))
        
        chapters = cursor.fetchall()
        
        return {
            'current': {
                'chunk_id': chunk_id,
                'chapter': chapter_num,
                'section': section_num,
                'type': chunk_type
            },
            'previous': dict(prev_chunk) if prev_chunk else None,
            'next': dict(next_chunk) if next_chunk else None,
            'chapter_outline': [dict(ch) for ch in chapters] if chapters else []
        }
        
    except Exception as e:
        logger.error(f"Error getting chunk navigation: {e}")
        return {}

def search_exact_references(cursor, query: str, limit: int = 20) -> List[Dict]:
    """Get exact reference matches with full navigation context"""
    try:
        # Full-text search with detailed chunk information
        sql = """
        SELECT 
            c.chunk_id,
            b.title,
            b.author,
            b.publication_year,
            c.chunk_type,
            c.chapter_number,
            c.section_number,
            c.word_count,
            ts_headline('english', c.content, plainto_tsquery('english', %s), 
                       'MaxFragments=3,MaxWords=80,MinWords=30') as highlighted_content,
            LEFT(c.content, 300) as content_preview,
            ts_rank(c.search_vector, plainto_tsquery('english', %s)) as relevance_rank
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY relevance_rank DESC, c.chapter_number ASC, c.section_number ASC
        LIMIT %s
        """
        
        cursor.execute(sql, (query, query, query, limit))
        results = cursor.fetchall()
        
        # Add navigation context to each result
        enriched_results = []
        for result in results:
            result_dict = dict(result)
            
            # Add navigation info
            navigation = get_chunk_navigation(cursor, result['chunk_id'])
            result_dict['navigation'] = navigation
            
            # Add reference citation
            result_dict['citation'] = {
                'format': f"{result['title']} by {result['author']}",
                'chapter_ref': f"Chapter {result['chapter_number']}" if result['chapter_number'] else "Introduction",
                'location_id': result['chunk_id']
            }
            
            enriched_results.append(result_dict)
        
        return enriched_results
        
    except Exception as e:
        logger.error(f"Error in exact reference search: {e}")
        return []

def search_semantic_discovery(query: str, limit: int = 10) -> List[Dict]:
    """Get semantic similarity matches for knowledge discovery"""
    try:
        # Import vector search
        import sys
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, current_dir)
        from vector_embeddings import VectorEmbeddingGenerator
        
        generator = VectorEmbeddingGenerator()
        results = generator.semantic_search(query, limit)
        
        # Format for discovery context
        discovery_results = []
        for result in results:
            discovery_results.append({
                'chunk_id': result.get('chunk_id'),
                'title': result['title'],
                'author': result['author'],
                'similarity_score': result['similarity_score'],
                'content_preview': result['content_preview'][:200] + "...",
                'chapter_number': result.get('chapter_number'),
                'discovery_type': 'semantic_similarity',
                'relevance_explanation': f"Conceptually related (similarity: {result['similarity_score']:.3f})"
            })
        
        return discovery_results
        
    except Exception as e:
        logger.error(f"Error in semantic discovery search: {e}")
        return []

@app.route('/api/hybrid-search', methods=['GET', 'POST'])
def hybrid_search():
    """Hybrid search combining exact references and semantic discovery"""
    start_time = time.time()
    
    try:
        # Parse request parameters
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            exact_limit = data.get('exact_limit', 15)
            semantic_limit = data.get('semantic_limit', 10)
            include_navigation = data.get('include_navigation', True)
        else:
            query = request.args.get('q', '')
            exact_limit = int(request.args.get('exact_limit', 15))
            semantic_limit = int(request.args.get('semantic_limit', 10))
            include_navigation = request.args.get('navigation', 'true').lower() == 'true'
        
        if not query:
            return jsonify({"error": "Query parameter required"}), 400
        
        # Get database connection
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Perform both types of search
        exact_results = search_exact_references(cursor, query, exact_limit)
        semantic_results = search_semantic_discovery(query, semantic_limit)
        
        # Calculate query time
        query_time = time.time() - start_time
        
        # Build hybrid response
        response = {
            "query_metadata": {
                "query": query,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round(query_time * 1000, 2),
                "search_type": "hybrid",
                "api_version": "2.0"
            },
            "exact_references": {
                "description": "Precise textual matches with navigation context",
                "count": len(exact_results),
                "results": exact_results
            },
            "semantic_discovery": {
                "description": "Conceptually related content for knowledge exploration",
                "count": len(semantic_results),
                "results": semantic_results
            },
            "usage_guide": {
                "exact_references": "Use for precise citations, quotes, and specific information",
                "semantic_discovery": "Use for exploring related concepts and finding unexpected connections",
                "navigation": "Use chunk navigation to read full context around exact matches"
            }
        }
        
        logger.info(f"Hybrid search completed: query='{query}', exact={len(exact_results)}, semantic={len(semantic_results)}, time={query_time:.3f}s")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return jsonify({"error": "Hybrid search failed", "details": str(e)}), 500

@app.route('/api/chunk/<chunk_id>', methods=['GET'])
def get_chunk_detail(chunk_id: str):
    """Get detailed chunk information with full navigation"""
    try:
        db = get_db()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get full chunk details
        cursor.execute("""
            SELECT 
                c.chunk_id,
                c.content,
                c.chunk_type,
                c.chapter_number,
                c.section_number,
                c.word_count,
                c.character_count,
                b.title,
                b.author,
                b.publication_year,
                b.genre
            FROM chunks c
            JOIN books b ON c.book_id = b.book_id
            WHERE c.chunk_id = %s
        """, (chunk_id,))
        
        chunk = cursor.fetchone()
        if not chunk:
            return jsonify({"error": "Chunk not found"}), 404
        
        # Get navigation context
        navigation = get_chunk_navigation(cursor, chunk_id)
        
        # Get related chunks from same chapter
        cursor.execute("""
            SELECT chunk_id, chunk_type, section_number,
                   LEFT(content, 150) as preview
            FROM chunks 
            WHERE book_id = (SELECT book_id FROM chunks WHERE chunk_id = %s)
              AND chapter_number = %s
              AND chunk_id != %s
            ORDER BY section_number
            LIMIT 10
        """, (chunk_id, chunk['chapter_number'], chunk_id))
        
        related_chunks = cursor.fetchall()
        
        response = {
            "chunk_details": dict(chunk),
            "navigation": navigation,
            "related_chunks": [dict(rc) for rc in related_chunks],
            "reading_context": {
                "current_location": f"Chapter {chunk['chapter_number']}, Section {chunk['section_number'] or 'N/A'}",
                "book_context": f"{chunk['title']} by {chunk['author']} ({chunk['publication_year'] or 'Unknown'})",
                "chunk_type": chunk['chunk_type'],
                "content_stats": {
                    "words": chunk['word_count'],
                    "characters": chunk['character_count']
                }
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting chunk detail: {e}")
        return jsonify({"error": "Failed to get chunk details", "details": str(e)}), 500

@app.route('/api/hybrid-health', methods=['GET'])
def hybrid_health():
    """Health check for hybrid search system"""
    try:
        db = get_db()
        if not db:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
        cursor = db.cursor()
        
        # Check database stats
        cursor.execute("SELECT COUNT(*) FROM books")
        book_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NOT NULL")
        embedded_count = cursor.fetchone()[0]
        
        # Test exact search
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE search_vector @@ plainto_tsquery('english', 'test')")
        exact_search_ready = cursor.fetchone()[0] >= 0
        
        # Test semantic search availability
        try:
            import sys
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, current_dir)
            from vector_embeddings import VectorEmbeddingGenerator
            generator = VectorEmbeddingGenerator()
            semantic_search_ready = True
        except:
            semantic_search_ready = False
        
        return jsonify({
            "status": "healthy",
            "hybrid_search": "operational",
            "capabilities": {
                "exact_references": exact_search_ready,
                "semantic_discovery": semantic_search_ready,
                "chunk_navigation": True,
                "full_text_search": True
            },
            "database_stats": {
                "books_indexed": book_count,
                "chunks_indexed": chunk_count,
                "embeddings_ready": embedded_count,
                "embedding_coverage": f"{(embedded_count/chunk_count*100):.1f}%" if chunk_count > 0 else "0%"
            },
            "endpoints": {
                "hybrid_search": "/api/hybrid-search",
                "chunk_detail": "/api/chunk/{chunk_id}",
                "health_check": "/api/hybrid-health"
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    print("🔗 LibraryOfBabel Hybrid Search API Starting...")
    print("📚 Hybrid Search Features:")
    print("   📖 Exact References - Precise textual matches with navigation")
    print("   🧠 Semantic Discovery - Conceptual exploration and connections") 
    print("   🧭 Chunk Navigation - Previous/next chapter navigation")
    print("   📍 Citation Support - Detailed reference information")
    print("")
    print("🔌 Endpoints:")
    print("   GET/POST /api/hybrid-search - Combined exact + semantic search")
    print("   GET      /api/chunk/{id} - Detailed chunk with navigation")
    print("   GET      /api/hybrid-health - System health and capabilities")
    print("")
    print("💡 Usage Examples:")
    print("   Hybrid: /api/hybrid-search?q=consciousness&exact_limit=10&semantic_limit=5")
    print("   Detail: /api/chunk/543_chapter_4")
    print("   Health: /api/hybrid-health")
    print("")
    print("🚀 Ready for hybrid knowledge exploration!")
    
    app.run(host='0.0.0.0', port=5560, debug=False)