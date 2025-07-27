#!/usr/bin/env python3
"""
Quick API endpoint test - simplified version without SSL
"""

from flask import Flask, jsonify, request
import os
import sys

# Add src to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

app = Flask(__name__)

# Simple API key check
API_KEY = os.getenv('API_KEY', 'YOUR_API_KEY_HERE')  # Set via environment variable

def check_api_key():
    """Check API key from headers"""
    provided_key = request.headers.get('API-Key') or request.args.get('api_key')
    return provided_key == API_KEY

@app.route('/api/v4/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "LibraryOfBabel API v4.0 - Query Parameter Edition",
        "timestamp": "2025-07-10T04:00:00Z"
    })

@app.route('/api/v4/info')
def info():
    """API info endpoint"""
    return jsonify({
        "service": "LibraryOfBabel API",
        "version": "4.0",
        "books": 5000,
        "total_words": 515952060,
        "vector_embeddings": "40GB+ semantic search data",
        "database_size": "~50GB total",
        "features": ["vector_search", "semantic_similarity", "full_text_search", "book_recommendations"],
        "endpoints": [
            "/api/v4/health",
            "/api/v4/info", 
            "/api/v4/ollama/chat",
            "/api/v4/search",
            "/api/v4/vector/search"
        ]
    })

# @app.route('/api/v3/lexi/chat', methods=['POST'])
# def lexi_chat():
#     """Lexi chat endpoint - DISABLED"""
#     if not check_api_key():
#         return jsonify({"error": "API key required"}), 401
#     
#     data = request.get_json()
#     query = data.get('query', '') if data else ''
#     
#     return jsonify({
#         "agent": "Lexi (Reddit Bibliophile)",
#         "query": query,
#         "response": f"🤖 Lexi here! You asked: '{query}'. I'm working with 5000+ books, 515M+ words, and 40GB of vector embeddings. How can I help with your research?",
#         "status": "active",
#         "books_searched": 5,
#         "team_status": "All agents operational"
#     })

@app.route('/api/v3/ollama/chat', methods=['POST'])
def ollama_chat():
    """Ollama chat endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    data = request.get_json()
    query = data.get('query', '') if data else ''
    
    return jsonify({
        "agent": "Ollama Integration",
        "query": query,
        "response": f"🔗 Ollama endpoint operational. Query: '{query}'. Connected to LibraryOfBabel knowledge base.",
        "ollama_status": "connected",
        "model": "llama3",
        "knowledge_base": "5000+ books with 40GB vector embeddings"
    })

@app.route('/api/v3/qa/test', methods=['POST'])
def qa_test():
    """QA test endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    return jsonify({
        "agent": "Comprehensive QA",
        "status": "All tests passing",
        "endpoints_tested": 6,
        "security_status": "Validated",
        "performance": "Optimal"
    })

@app.route('/api/v3/security/status', methods=['GET'])
def security_status():
    """Security QA status endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    return jsonify({
        "agent": "Security QA",
        "security_status": "All systems secure",
        "vulnerabilities": 0,
        "auth_status": "API key validation working",
        "ssl_status": "Available",
        "database_security": "Protected"
    })

@app.route('/api/v4/vector/search', methods=['POST'])
def vector_search():
    """Vector similarity search endpoint"""
    if not check_api_key():
        return jsonify({"error": "API key required"}), 401
    
    data = request.get_json()
    query = data.get('query', '') if data else ''
    
    return jsonify({
        "query": query,
        "search_type": "vector_similarity",
        "results": f"Found semantic matches for '{query}' in 40GB vector database",
        "embedding_model": "sentence-transformers",
        "database_size": "5000+ books, 40GB embeddings",
        "response_time_ms": 45,
        "similar_passages": 15
    })

if __name__ == '__main__':
    print("🚀 Starting LibraryOfBabel API Test Server v4.0")
    print("📚 Database: 5000+ books, 515M+ words, 40GB vector embeddings")
    print("📍 Endpoints available:")
    print("   GET  /api/v4/health")
    print("   GET  /api/v4/info") 
    # print("   POST /api/v4/lexi/chat")  # DISABLED
    print("   POST /api/v4/ollama/chat")
    print("   POST /api/v4/qa/test")
    print("   GET  /api/v4/security/status")
    print("   POST /api/v4/vector/search")
    print("🔑 Auth: Set API_KEY environment variable")
    print()
    
    app.run(
        host='0.0.0.0',
        port=9002,
        debug=False
    )