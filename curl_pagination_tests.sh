#!/bin/bash
# 🧪 Comprehensive iOS Shortcuts API Curl Pagination Tests
# ========================================================

BASE_URL="http://localhost:5001/api/shortcuts"
echo "🧪 iOS Shortcuts API Curl Pagination Tests"
echo "=========================================="
echo "Testing: $BASE_URL"
echo ""

# Function to test endpoint
test_endpoint() {
    local endpoint="$1"
    local description="$2"
    echo "🔍 Testing: $description"
    echo "   Endpoint: $endpoint"
    
    response=$(curl -s "$BASE_URL$endpoint" 2>/dev/null)
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null)
    
    if [ "$http_code" = "200" ]; then
        echo "   ✅ Status: $http_code"
        echo "   📋 Response: ${response:0:100}..."
        echo ""
        return 0
    else
        echo "   ❌ Status: $http_code"
        echo "   📋 Error: $response"
        echo ""
        return 1
    fi
}

# Function to test pagination
test_pagination() {
    local endpoint="$1"
    local description="$2"
    echo "📄 Testing Pagination: $description"
    
    # Test page 1
    echo "   🔸 Page 1:"
    page1=$(curl -s "$BASE_URL$endpoint?page=1&limit=3" 2>/dev/null)
    code1=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint?page=1&limit=3" 2>/dev/null)
    echo "      Status: $code1"
    echo "      Response: ${page1:0:80}..."
    
    # Test page 2
    echo "   🔸 Page 2:"
    page2=$(curl -s "$BASE_URL$endpoint?page=2&limit=3" 2>/dev/null)
    code2=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint?page=2&limit=3" 2>/dev/null)
    echo "      Status: $code2"
    echo "      Response: ${page2:0:80}..."
    
    # Check if pagination works
    if [ "$code1" = "200" ] && [ "$code2" = "200" ] && [ "$page1" != "$page2" ]; then
        echo "   ✅ Pagination: WORKING (Page 1 ≠ Page 2)"
    elif [ "$page1" = "$page2" ]; then
        echo "   ❌ Pagination: FAILED (Page 1 = Page 2)"
    else
        echo "   ⚠️  Pagination: ERROR (HTTP errors)"
    fi
    echo ""
}

echo "📊 SINGLE VALUE ENDPOINTS"
echo "========================"
test_endpoint "/books/count" "Book Count"
test_endpoint "/random/title" "Random Title"
test_endpoint "/random/author" "Random Author"
test_endpoint "/random/book" "Random Book (JSON)"

echo "🔍 SEARCH ENDPOINTS"
echo "=================="
test_endpoint "/search/love/count" "Search Count for 'love'"
test_endpoint "/search/love/has-results" "Search Boolean for 'love'"

echo "📋 ARRAY ENDPOINTS WITH PAGINATION"
echo "================================="
test_pagination "/books/author-list" "Author List"
test_pagination "/books/title-list" "Title List"
test_pagination "/search/love/titles" "Search Titles for 'love'"

echo "💬 FORMATTED TEXT ENDPOINTS"
echo "=========================="
test_endpoint "/random/citation" "Random Citation"
test_endpoint "/random/share-text" "Random Share Text"
test_endpoint "/search/love/summary" "Search Summary for 'love'"

echo "📊 DATA JAR ENDPOINTS"
echo "==================="
test_endpoint "/stats/dashboard" "Stats Dashboard"
test_endpoint "/user/reading-progress" "Reading Progress"

echo "🔍 ADVANCED SEARCH"
echo "================="
test_endpoint "/search/love/simple" "Simple Search for 'love'"

echo "📖 BOOK-SPECIFIC ENDPOINTS (Olivia Laing - Book ID 2238)"
echo "========================================================"
test_endpoint "/books/2238/summary" "Book Summary"
test_endpoint "/books/2238/construct" "Book Construction"
test_endpoint "/books/2238/page/1" "Book Page 1"
test_endpoint "/books/2238/toc" "Table of Contents"

echo "🎲 SERENDIPITY ENDPOINTS"
echo "======================="
test_endpoint "/serendipity/random-passage" "Random Passage"
test_endpoint "/serendipity/mixed-authors" "Mixed Authors"
test_endpoint "/serendipity/theme-blend/love" "Theme Blend: Love"
test_endpoint "/serendipity/story-starter" "Story Starter"

echo "🏥 UTILITY"
echo "========="
test_endpoint "/health" "Health Check"

echo "🎯 OLIVIA LAING ACCESSIBILITY TEST"
echo "================================="
echo "Testing if Olivia Laing is accessible on page 4..."
olivia_test=$(curl -s "$BASE_URL/books/author-list?page=4&limit=500" 2>/dev/null | grep -i "olivia")
if [ -n "$olivia_test" ]; then
    echo "✅ Olivia Laing found on page 4: $olivia_test"
else
    echo "❌ Olivia Laing NOT found on page 4"
fi

echo ""
echo "📊 TEST COMPLETE"
echo "================"