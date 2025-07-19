#!/usr/bin/env python3
"""
🧪 iOS Shortcuts API Comprehensive Test Suite
===========================================
Tests ALL 25 shortcuts endpoints for pagination, limits, and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:5000/api/shortcuts"
RESULTS = []

def log_test(endpoint: str, status: str, details: str = ""):
    """Log test results"""
    result = {
        "endpoint": endpoint,
        "status": status,
        "details": details,
        "timestamp": time.time()
    }
    RESULTS.append(result)
    status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{status_emoji} {endpoint:<40} {status:<8} {details}")

def test_endpoint(endpoint: str, description: str = "") -> Dict[str, Any]:
    """Test a single endpoint"""
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        if response.status_code == 200:
            try:
                data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                return {"status": "PASS", "data": data, "code": 200}
            except:
                return {"status": "PASS", "data": response.text, "code": 200}
        else:
            return {"status": "FAIL", "error": f"HTTP {response.status_code}", "code": response.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "FAIL", "error": str(e), "code": 0}

def test_pagination(endpoint: str, param_name: str = "page") -> Dict[str, Any]:
    """Test pagination on an endpoint"""
    results = {}
    
    # Test page 1
    page1 = test_endpoint(f"{endpoint}?{param_name}=1&limit=5")
    results["page1"] = page1
    
    # Test page 2  
    page2 = test_endpoint(f"{endpoint}?{param_name}=2&limit=5")
    results["page2"] = page2
    
    # Check if pagination works (different results)
    if page1["status"] == "PASS" and page2["status"] == "PASS":
        page1_data = str(page1["data"])
        page2_data = str(page2["data"])
        if page1_data != page2_data:
            results["pagination_works"] = True
        else:
            results["pagination_works"] = False
    else:
        results["pagination_works"] = False
        
    return results

def main():
    """Run comprehensive test suite"""
    print("🧪 iOS Shortcuts API Comprehensive Test Suite")
    print("=" * 60)
    print(f"Testing: {BASE_URL}")
    print()
    
    # Wait for server to be ready
    print("⏳ Waiting for server...")
    time.sleep(3)
    
    print("📊 SINGLE VALUE ENDPOINTS")
    print("-" * 40)
    
    # 1. Basic endpoints
    result = test_endpoint("/books/count")
    log_test("/books/count", result["status"], f"Response: {str(result.get('data', ''))[:50]}")
    
    result = test_endpoint("/random/title")
    log_test("/random/title", result["status"], f"Response: {str(result.get('data', ''))[:50]}")
    
    result = test_endpoint("/random/author")
    log_test("/random/author", result["status"], f"Response: {str(result.get('data', ''))[:50]}")
    
    result = test_endpoint("/random/book")
    log_test("/random/book", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    # 2. Search endpoints
    result = test_endpoint("/search/love/count")
    log_test("/search/love/count", result["status"], f"Count: {result.get('data', '')}")
    
    result = test_endpoint("/search/love/has-results")
    log_test("/search/love/has-results", result["status"], f"Has results: {result.get('data', '')}")
    
    print("\n📋 ARRAY ENDPOINTS (Testing Pagination)")
    print("-" * 40)
    
    # 3. List endpoints with pagination
    pagination_result = test_pagination("/books/title-list")
    status = "PASS" if pagination_result["pagination_works"] else "FAIL"
    details = f"Page1≠Page2: {pagination_result['pagination_works']}"
    log_test("/books/title-list (pagination)", status, details)
    
    pagination_result = test_pagination("/books/author-list")
    status = "PASS" if pagination_result["pagination_works"] else "FAIL"
    details = f"Page1≠Page2: {pagination_result['pagination_works']}"
    log_test("/books/author-list (pagination)", status, details)
    
    pagination_result = test_pagination("/search/love/titles")
    status = "PASS" if pagination_result["pagination_works"] else "FAIL"
    details = f"Page1≠Page2: {pagination_result['pagination_works']}"
    log_test("/search/love/titles (pagination)", status, details)
    
    print("\n💬 FORMATTED TEXT ENDPOINTS")
    print("-" * 40)
    
    result = test_endpoint("/random/citation")
    log_test("/random/citation", result["status"], f"Response: {str(result.get('data', ''))[:50]}")
    
    result = test_endpoint("/random/share-text")
    log_test("/random/share-text", result["status"], f"Response: {str(result.get('data', ''))[:50]}")
    
    result = test_endpoint("/search/love/summary")
    log_test("/search/love/summary", result["status"], f"Response: {str(result.get('data', ''))[:50]}")
    
    print("\n📊 DATA JAR ENDPOINTS")
    print("-" * 40)
    
    result = test_endpoint("/stats/dashboard")
    log_test("/stats/dashboard", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint("/user/reading-progress")
    log_test("/user/reading-progress (GET)", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    print("\n🔍 ADVANCED SEARCH ENDPOINTS")
    print("-" * 40)
    
    result = test_endpoint("/search/love/simple")
    log_test("/search/love/simple", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    print("\n📖 BOOK-SPECIFIC ENDPOINTS")
    print("-" * 40)
    
    # Test with Olivia Laing's book ID
    book_id = 2238
    
    result = test_endpoint(f"/books/{book_id}/summary")
    log_test(f"/books/{book_id}/summary", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint(f"/books/{book_id}/construct")
    log_test(f"/books/{book_id}/construct", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint(f"/books/{book_id}/page/1")
    log_test(f"/books/{book_id}/page/1", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint(f"/books/{book_id}/toc")
    log_test(f"/books/{book_id}/toc", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    print("\n🎲 SERENDIPITY ENDPOINTS")
    print("-" * 40)
    
    result = test_endpoint("/serendipity/random-passage")
    log_test("/serendipity/random-passage", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint("/serendipity/mixed-authors")
    log_test("/serendipity/mixed-authors", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint("/serendipity/theme-blend/love")
    log_test("/serendipity/theme-blend/love", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    result = test_endpoint("/serendipity/story-starter")
    log_test("/serendipity/story-starter", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    print("\n🏥 UTILITY ENDPOINTS")
    print("-" * 40)
    
    result = test_endpoint("/health")
    log_test("/health", result["status"], f"Keys: {list(result.get('data', {}).keys()) if isinstance(result.get('data'), dict) else 'Not JSON'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(RESULTS)
    passed = len([r for r in RESULTS if r["status"] == "PASS"])
    failed = len([r for r in RESULTS if r["status"] == "FAIL"])
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
    
    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in RESULTS:
            if result["status"] == "FAIL":
                print(f"  - {result['endpoint']}: {result['details']}")
    
    print("\n🎯 PAGINATION TESTS:")
    pagination_endpoints = [
        "/books/title-list (pagination)",
        "/books/author-list (pagination)", 
        "/search/love/titles (pagination)"
    ]
    
    pagination_results = [r for r in RESULTS if r["endpoint"] in pagination_endpoints]
    pagination_passed = len([r for r in pagination_results if r["status"] == "PASS"])
    
    print(f"Pagination endpoints working: {pagination_passed}/{len(pagination_results)}")
    
    # Save detailed results
    with open("shortcuts_api_test_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: shortcuts_api_test_results.json")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)