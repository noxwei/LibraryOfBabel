#\!/usr/bin/env python3
"""
🔍 COMPREHENSIVE UNIFIED API ENDPOINT TEST
==========================================

Test all available endpoints on the consolidated LibraryOfBabel API.
No more v2/v3 separation - single unified API documentation.
"""

import requests
import json
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = "babel_secure_8a52a0ad3a1fe3bf3ade37d04deef0054d8f58035a0e9d4760a9a08548d8cebf"
BASE_URL = "https://api.ashortstayinhell.com:5562"

def test_endpoint(name, url, description=""):
    """Test endpoint and return result info"""
    print(f"🧪 {name}")
    print(f"   URL: {url}")
    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            result_count = len(data.get('results', [])) if 'results' in data else 'N/A'
            print(f"   ✅ SUCCESS - Results: {result_count}")
            return True, data
        else:
            print(f"   ❌ FAILED - HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"   ❌ ERROR - {e}")
        return False, None

def main():
    print("🚀 UNIFIED LIBRARYOFBABEL API ENDPOINT DOCUMENTATION TEST")
    print("=" * 60)
    
    endpoints = []
    
    # Core API endpoints
    print("\n📊 CORE API ENDPOINTS")
    print("-" * 30)
    
    success, data = test_endpoint(
        "Health Check", 
        f"{BASE_URL}/health",
        "API health status and system stats"
    )
    if success:
        endpoints.append({
            "endpoint": "/health",
            "method": "GET",
            "auth_required": False,
            "description": "API health status and system stats",
            "example_response": {
                "status": data.get("status"),
                "stats": data.get("stats")
            }
        })
    
    success, data = test_endpoint(
        "List Books",
        f"{BASE_URL}/books?page=1&page_size=3&api_key={API_KEY}",
        "Paginated list of all books"
    )
    if success:
        endpoints.append({
            "endpoint": "/books",
            "method": "GET", 
            "auth_required": True,
            "parameters": "page, page_size, api_key",
            "description": "Paginated list of all books",
            "example_response": {
                "total_count": data.get("total_count"),
                "results_count": len(data.get("results", []))
            }
        })
    
    success, data = test_endpoint(
        "Book Details",
        f"{BASE_URL}/books/1373?api_key={API_KEY}",
        "Detailed information about a specific book"
    )
    if success:
        endpoints.append({
            "endpoint": "/books/<book_id>",
            "method": "GET",
            "auth_required": True, 
            "parameters": "api_key",
            "description": "Detailed information about a specific book",
            "example_response": {
                "title": data.get("title"),
                "author": data.get("author"),
                "chunks_available": data.get("chunks_available")
            }
        })
    
    success, data = test_endpoint(
        "Book Chunks",
        f"{BASE_URL}/books/1373/chunks?page=1&page_size=2&api_key={API_KEY}",
        "Paginated chunks of a specific book"
    )
    if success:
        endpoints.append({
            "endpoint": "/books/<book_id>/chunks",
            "method": "GET",
            "auth_required": True,
            "parameters": "page, page_size, chunk_level, api_key", 
            "description": "Paginated chunks of a specific book with chunking levels",
            "example_response": {
                "total_count": data.get("total_count"),
                "chunk_level": data.get("meta", {}).get("chunk_level")
            }
        })
    
    # Search endpoints
    print("\n🔍 SEARCH ENDPOINTS")
    print("-" * 20)
    
    success, data = test_endpoint(
        "Traditional Search",
        f"{BASE_URL}/search?q=Foucault&page=1&page_size=3&api_key={API_KEY}",
        "Traditional keyword search across all books"
    )
    if success:
        endpoints.append({
            "endpoint": "/search",
            "method": "GET",
            "auth_required": True,
            "parameters": "q, type, page, page_size, api_key",
            "description": "Search across all books (keyword, semantic types)",
            "search_types": "keyword, semantic",
            "example_response": {
                "total_count": data.get("total_count"),
                "results_count": len(data.get("results", []))
            }
        })
    
    success, data = test_endpoint(
        "In-Book Search",
        f"{BASE_URL}/books/1099/search?q=discourse&page=1&page_size=3&api_key={API_KEY}",
        "Search within a specific book"
    )
    if success:
        endpoints.append({
            "endpoint": "/books/<book_id>/search", 
            "method": "GET",
            "auth_required": True,
            "parameters": "q, page, page_size, api_key",
            "description": "Search within a specific book",
            "example_response": {
                "total_count": data.get("total_count"),
                "book_id": data.get("book_id")
            }
        })
    
    # Fuzzy search endpoints
    print("\n🧠 FUZZY SEARCH ENDPOINTS (NEW)")
    print("-" * 35)
    
    success, data = test_endpoint(
        "Fuzzy Semantic Search",
        f"{BASE_URL}/fuzzy-search?q=artificial%20intelligence&type=semantic&limit=3&api_key={API_KEY}",
        "Semantic vector similarity search"
    )
    if success:
        endpoints.append({
            "endpoint": "/fuzzy-search",
            "method": "GET", 
            "auth_required": True,
            "parameters": "q, type, limit, semantic_weight, fuzzy_weight, keyword_weight, api_key",
            "description": "Advanced fuzzy search with vector embeddings",
            "search_types": "semantic, fuzzy, hybrid, keyword",
            "example_response": {
                "total_results": data.get("search_stats", {}).get("total_results"),
                "search_type": "semantic/fuzzy/hybrid"
            }
        })
    
    # Legacy v3 compatibility (optional)
    print("\n🔗 LEGACY V3 COMPATIBILITY")
    print("-" * 30)
    
    success, data = test_endpoint(
        "V3 Health (Legacy)",
        f"{BASE_URL}/api/v3/health",
        "Legacy v3 health endpoint for backwards compatibility"
    )
    if success:
        endpoints.append({
            "endpoint": "/api/v3/health",
            "method": "GET",
            "auth_required": False,
            "description": "Legacy v3 health endpoint (backwards compatibility)",
            "note": "Returns same data as /health with v3 format"
        })
    
    success, data = test_endpoint(
        "V3 Search (Legacy)",
        f"{BASE_URL}/api/v3/search?q=Foucault&limit=2&api_key={API_KEY}",
        "Legacy v3 search endpoint for backwards compatibility"
    )
    if success:
        endpoints.append({
            "endpoint": "/api/v3/search",
            "method": "GET", 
            "auth_required": True,
            "parameters": "q, type, limit, api_key",
            "description": "Legacy v3 search endpoint (backwards compatibility)",
            "note": "Returns data in v3 format with api_version field"
        })
    
    # Generate documentation
    print(f"\n📋 ENDPOINT SUMMARY")
    print("-" * 20)
    print(f"Total endpoints tested: {len(endpoints)}")
    
    # Save endpoint documentation
    doc_data = {
        "api_name": "LibraryOfBabel Unified API",
        "description": "Consolidated API with search, fuzzy search, and vector embeddings",
        "base_url": BASE_URL,
        "version": "Unified (formerly v2 + v3)",
        "endpoints": endpoints,
        "authentication": {
            "method": "API Key",
            "parameter": "api_key", 
            "example": "api_key=YOUR_API_KEY"
        },
        "features": [
            "Paginated book listings",
            "Book content chunking (small/medium/large)",
            "Traditional keyword search",
            "Semantic vector search", 
            "Fuzzy text matching",
            "Hybrid search algorithms",
            "In-book search",
            "18,363+ vector embeddings"
        ]
    }
    
    with open("docs/api_endpoints_unified.json", "w") as f:
        json.dump(doc_data, f, indent=2)
    
    print(f"✅ Documentation saved to: docs/api_endpoints_unified.json")
    print(f"🎯 Ready to update documentation files\!")

if __name__ == "__main__":
    main()
EOF < /dev/null