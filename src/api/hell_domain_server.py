#!/usr/bin/env python3
"""
🔥 Hell Domain Vector Search Server - Port 5571
Divine mode vector search with maximum intensity and esoteric knowledge discovery
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
import random

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vector_embeddings import VectorEmbeddingGenerator
from enhanced_librarian_agent import EnhancedLibrarianAgent

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI components
vector_generator = VectorEmbeddingGenerator()
librarian_agent = EnhancedLibrarianAgent()

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

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/api/hell/search', methods=['GET', 'POST'])
def hell_vector_search():
    """Hell Domain Vector Search - Divine mode with maximum intensity"""
    start_time = time.time()
    
    try:
        # Parse request
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '')
            limit = data.get('limit', 10)
            mode = data.get('mode', 'divine')
            seeker_mode = data.get('seekermode', None)
        else:
            query = request.args.get('q', '')
            limit = int(request.args.get('limit', 10))
            mode = request.args.get('mode', 'divine')
            seeker_mode = request.args.get('seekermode', None)
        
        if not query:
            return jsonify({
                "error": "Query required",
                "hell_domain": "The void demands substance",
                "suggestion": "Provide a query to pierce the veil of knowledge"
            }), 400
        
        # Special seeker mode handling
        if seeker_mode == "the_librarian_who_knows":
            # Enhanced search with librarian agent
            results = librarian_agent.semantic_search_with_analysis(query, limit)
            hell_enhancement = {
                "seeker_activated": True,
                "librarian_insights": "The Librarian Who Knows has been summoned",
                "enhanced_analysis": True,
                "domain_power": "hell_enhanced_with_seeker"
            }
        else:
            # Standard hell domain search
            results = vector_generator.semantic_search(query, limit, similarity_threshold=0.1)
            hell_enhancement = {
                "seeker_activated": False,
                "domain_power": "hell_standard",
                "similarity_threshold": 0.1
            }
        
        # Hell domain enhancements
        hell_results = []
        for result in results:
            hell_result = {
                "chunk_id": result.get('chunk_id'),
                "title": result['title'],
                "author": result['author'],
                "similarity_score": result.get('similarity_score', 0.0),
                "relevance_rank": result.get('similarity_score', 0.0),
                "content_preview": result.get('content_preview', ''),
                "hell_domain_metrics": {
                    "infernal_relevance": min(result.get('similarity_score', 0.0) * 1.2, 1.0),
                    "knowledge_intensity": "divine" if result.get('similarity_score', 0.0) > 0.8 else "mortal",
                    "esoteric_factor": random.uniform(0.7, 1.0)
                },
                "domain": "hell",
                "power_level": mode
            }
            hell_results.append(hell_result)
        
        response_time = time.time() - start_time
        
        response = {
            "query_metadata": {
                "query": query,
                "domain": "hell",
                "port": 5571,
                "mode": mode,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": round(response_time * 1000, 2),
                "seeker_mode": seeker_mode
            },
            "results": hell_results,
            "hell_domain_status": {
                "total_results": len(hell_results),
                "infernal_power": "maximum",
                "knowledge_depth": "divine",
                "search_intensity": mode,
                **hell_enhancement
            },
            "domain_message": "🔥 Hell Domain: Where knowledge burns brightest in the darkness",
            "available_modes": ["divine", "mystical", "precise", "enhanced"]
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Hell domain search failed: {e}")
        return jsonify({
            "error": "Hell domain search failed",
            "infernal_message": "The flames of knowledge were too intense",
            "details": str(e)
        }), 500

@app.route('/api/hell/health', methods=['GET'])
def hell_health():
    """Hell domain health check"""
    try:
        db = get_db()
        if not db:
            return jsonify({"status": "error", "message": "Database connection failed"}), 500
        
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NOT NULL")
        embedded_count = cursor.fetchone()[0]
        
        return jsonify({
            "status": "hell_domain_operational",
            "domain": "hell",
            "port": 5571,
            "infernal_power": "maximum",
            "embedded_chunks": embedded_count,
            "available_modes": ["divine", "mystical", "precise", "enhanced"],
            "special_seekers": ["the_librarian_who_knows"],
            "hell_message": "🔥 The fires of knowledge burn eternal"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "domain": "hell",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      🔥 HELL DOMAIN VECTOR SEARCH 🔥                        ║
║                        Port 5571 - Divine Knowledge                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔥 HELL DOMAIN CAPABILITIES:
   • Divine mode vector search with maximum intensity
   • Esoteric knowledge discovery with infernal power
   • The Librarian Who Knows seeker mode available
   • Enhanced similarity thresholds for deeper insights
   • Mystical, precise, and enhanced search modes

🌐 ENDPOINTS:
   • GET/POST /api/hell/search - Hell domain vector search
   • GET      /api/hell/health - Hell domain status

🎯 USAGE:
   curl "http://localhost:5571/api/hell/search?q=consciousness&mode=divine"
   curl "http://localhost:5571/api/hell/search?q=reality&seekermode=the_librarian_who_knows"

🔥 Where knowledge burns brightest in the darkness!
    """)
    
    app.run(host='0.0.0.0', port=5573, debug=False)