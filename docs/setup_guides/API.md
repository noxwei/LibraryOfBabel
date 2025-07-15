# 📚 LibraryOfBabel API Setup Guide

## 🌐 Production API Overview

The LibraryOfBabel API provides secure, paginated access to **838 real books** with advanced chunking and search capabilities. The API is fully consolidated into a single secure endpoint.

## 🔗 API Endpoint

**Production URL**: `https://api.example.com:5562`

## 🔐 Authentication

**⚠️ REQUIRED**: All endpoints (except `/health`) require API key authentication.

### Authentication Methods
```bash
# Method 1: Query Parameter (Recommended for testing)
curl "https://api.example.com:5562/books?api_key=YOUR_API_KEY"

# Method 2: Authorization Header
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.example.com:5562/books"

# Method 3: X-API-Key Header
curl -H "X-API-Key: YOUR_API_KEY" \
     "https://api.example.com:5562/books"
```

### Rate Limiting
- **60 requests per minute** per API key
- Rate limit headers included in responses
- Automatic request logging and monitoring

## 📊 Health Check (No Auth Required)

```bash
curl https://api.example.com:5562/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected", 
  "books": 838,
  "chunks": 25067,
  "embeddings": 18363,
  "response_time_ms": 15.2,
  "api_version": "2.0-secure-paginated",
  "features": [
    "pagination",
    "chunking_levels",
    "navigation_links", 
    "authentication",
    "rate_limiting"
  ],
  "chunk_levels": ["small", "medium", "large"],
  "security": "enabled"
}
```

## 📚 Core Endpoints

### 1. List Books (Paginated)
```bash
# Get first 5 books
curl "https://api.example.com:5562/books?api_key=YOUR_API_KEY&page_size=5"

# Search for specific content
curl "https://api.example.com:5562/books?api_key=YOUR_API_KEY&search=artificial%20intelligence"

# Filter by author
curl "https://api.example.com:5562/books?api_key=YOUR_API_KEY&author=Rowling"
```

### 2. Get Specific Book
```bash
curl "https://api.example.com:5562/books/611?api_key=YOUR_API_KEY"
```

### 3. Get Book Chunks (Configurable Chunking)
```bash
# Small chunks (500 chars) for detailed analysis
curl "https://api.example.com:5562/books/611/chunks?api_key=YOUR_API_KEY&chunk_level=small"

# Medium chunks (1500 chars) - default
curl "https://api.example.com:5562/books/611/chunks?api_key=YOUR_API_KEY&chunk_level=medium"

# Large chunks (5000 chars) for overview
curl "https://api.example.com:5562/books/611/chunks?api_key=YOUR_API_KEY&chunk_level=large"
```

### 4. Search Books
```bash
curl "https://api.example.com:5562/search?api_key=YOUR_API_KEY&q=machine%20learning"
```

### 5. Get Full API Documentation
```bash
# Interactive API documentation (no auth required)
curl https://api.example.com:5562/api-docs
```

## 🚀 Quick Integration Examples

### Python
```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://api.example.com:5562"

# Get all books with pagination
response = requests.get(f"{BASE_URL}/books", params={
    "api_key": API_KEY,
    "page_size": 20
})

books = response.json()
print(f"Total books: {books['pagination']['total_items']}")  # 838
```

### JavaScript
```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://api.example.com:5562';

// Search for books
fetch(`${BASE_URL}/search?api_key=${API_KEY}&q=consciousness`)
  .then(response => response.json())
  .then(data => console.log(`Found ${data.pagination.total_items} results`));
```

### Bash/Shell
```bash
#!/bin/bash
API_KEY="your_api_key_here"
BASE_URL="https://api.example.com:5562"

# Get health status
curl "$BASE_URL/health"

# Get books with authentication  
curl "$BASE_URL/books?api_key=$API_KEY&page_size=10"
```

## 🔧 Local Development Setup

For local development, mirror the production port:

```bash
# Start local API on port 5562 to match production
python src/api/secure_paginated_api.py

# Test local endpoint
curl "http://localhost:5562/health"
```

## 📊 Current Statistics

- **📚 Total Books**: 838
- **📝 Total Chunks**: 25,067  
- **🧠 Total Embeddings**: 18,363
- **⚡ Average Response Time**: 12-30ms
- **🔒 Security**: 100% API key protected
- **📈 Uptime**: 99.9%+

## 🛡️ Security Features

- **HTTPS enforced** with Let's Encrypt certificates
- **API key authentication** required for all data endpoints
- **Rate limiting** (60 req/min) prevents abuse
- **Request logging** tracks all access
- **Security headers** on all responses
- **SQL injection protection** with parameterized queries

## ⚠️ Error Handling

**Common HTTP Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Book/chunk not found  
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Standard Error Response:**
```json
{
  "error": "Authentication required",
  "success": false
}
```

## 🤖 AI Agent Integration

Perfect for AI agents and automated analysis:

- **Pagination** handles large datasets efficiently
- **Chunking levels** optimize for different analysis needs
- **Search capabilities** enable topic-specific discovery
- **Structured JSON** responses for easy parsing
- **Rate limiting** prevents overload

## 📖 Additional Resources

- **Complete API Reference**: `/docs/API-Reference.md`
- **Agent Integration Guide**: `/docs/AI-Agents-Guide.md`
- **Frontend Integration**: `/docs/FRONTEND_INTEGRATION_GUIDE.md`

---

**Last Updated**: July 14, 2025 | **API Version**: 2.0-secure-paginated  
**Production Ready**: ✅ | **SSL Enabled**: ✅ | **Auto-restart Daemon**: ✅