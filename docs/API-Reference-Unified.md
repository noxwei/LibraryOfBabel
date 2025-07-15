# 📚 LibraryOfBabel Unified API Reference

Complete documentation for the LibraryOfBabel Unified API. This consolidated API provides authenticated access to 838 real books with advanced pagination, chunking, search capabilities, and fuzzy search with vector embeddings.

**🎉 NEW: Single unified API - no more v2/v3 separation!**

## 🌐 Production Endpoint

**Base URL**: `https://api.ashortstayinhell.com:5562`  
**Version**: Unified (consolidates former v2 + v3 functionality)

## 🔐 Authentication

**All endpoints (except `/health`) require API key authentication.**

### Authentication Methods
1. **Query Parameter** (Recommended for testing):
   ```bash
   ?api_key=YOUR_API_KEY
   ```

2. **Authorization Header**:
   ```bash
   Authorization: Bearer YOUR_API_KEY
   ```

3. **X-API-Key Header**:
   ```bash
   X-API-Key: YOUR_API_KEY
   ```

### Rate Limiting
- **60 requests per minute** per API key
- Rate limit headers included in responses
- Security monitoring and request logging active

---

## 📊 System Health

### `GET /health`
**No authentication required** - Public health check endpoint.

**Example Request:**
```bash
curl https://api.ashortstayinhell.com:5562/health
```

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "api": "healthy",
    "database": "healthy"
  },
  "stats": {
    "books": 838,
    "chunks": 25067,
    "response_time_ms": 185.21
  },
  "timestamp": "2025-07-14T22:51:23.373861"
}
```

---

## 📚 Books Endpoints

### `GET /books`
**Authentication required** - List books with pagination and search.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)
- `search` (optional): Search in title/author
- `author` (optional): Filter by author
- `genre` (optional): Filter by genre

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page=1&page_size=5"
```

**Response:**
```json
{
  "results": [
    {
      "book_id": 1373,
      "title": "Sample Book Title",
      "author": "Author Name",
      "publisher": "Publisher",
      "publication_date": "2020-01-01T00:00:00+00:00",
      "language": "en",
      "genre": "non-fiction",
      "word_count": 50000,
      "processed_date": "2025-07-14T00:00:00+00:00",
      "links": {
        "self": "https://api.ashortstayinhell.com:5562/books/1373",
        "chunks": "https://api.ashortstayinhell.com:5562/books/1373/chunks",
        "search_in_book": "https://api.ashortstayinhell.com:5562/books/1373/search"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 5,
    "total_items": 838,
    "total_pages": 168,
    "has_next": true,
    "has_prev": false
  },
  "navigation": {
    "next": "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page=2&page_size=5",
    "first": "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page=1&page_size=5",
    "last": "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page=168&page_size=5"
  }
}
```

### `GET /books/{book_id}`
**Authentication required** - Get specific book details.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/books/1373?api_key=YOUR_API_KEY"
```

**Response:**
```json
{
  "book_id": 1373,
  "title": "Sample Book Title",
  "author": "Author Name",
  "publisher": "Publisher",
  "publication_date": "2020-01-01T00:00:00+00:00",
  "language": "en",
  "isbn": "9781234567890",
  "description": "Book description...",
  "genre": "non-fiction",
  "word_count": 50000,
  "file_path": "/processed/sample_book.epub",
  "processed_date": "2025-07-14T00:00:00+00:00",
  "chunks_available": 45,
  "embeddings_available": 42,
  "links": {
    "chunks": "https://api.ashortstayinhell.com:5562/books/1373/chunks",
    "search_in_book": "https://api.ashortstayinhell.com:5562/books/1373/search"
  },
  "meta": {
    "query_time_ms": 12.34
  }
}
```

### `GET /books/{book_id}/chunks`
**Authentication required** - Get book chunks with configurable chunking levels.

**Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Chunks per page (default: 10, max: 50)
- `chunk_level` (optional): Chunking granularity
  - `small`: 500 characters per chunk
  - `medium`: 1500 characters per chunk (default)
  - `large`: 5000 characters per chunk

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/books/1373/chunks?api_key=YOUR_API_KEY&chunk_level=medium&page=1"
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "1373_chapter_1",
      "title": "Chapter 1 Title",
      "chapter_number": 1,
      "original_word_count": 2000,
      "sub_chunks": [
        {
          "chunk_id": 1,
          "text": "Chapter content text...",
          "word_count": 300,
          "char_count": 1200,
          "chunk_level": "medium"
        }
      ],
      "total_sub_chunks": 3,
      "chunk_level": "medium"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_items": 45,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "query_time_ms": 18.67,
    "chunk_level": "medium",
    "available_levels": ["small", "medium", "large"]
  }
}
```

---

## 🔍 Search Endpoints

### `GET /search`
**Authentication required** - Search across all books with pagination.

**Parameters:**
- `q` (required): Search query
- `type` (optional): Search type (`keyword`, `semantic`)
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 20, max: 100)

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_API_KEY&q=Foucault&type=semantic&page=1&page_size=3"
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "1099_chapter_3",
      "book_id": 1099,
      "content": "Text containing search term...",
      "chapter_number": 3,
      "word_count": 500,
      "title": "Book Title",
      "author": "Author Name",
      "relevance_score": 0.85
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 3,
    "total_items": 156,
    "total_pages": 52,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "search_query": "Foucault",
    "search_type": "semantic",
    "query_time_ms": 101.01
  }
}
```

### `GET /books/{book_id}/search` 🆕
**Authentication required** - Search within a specific book.

**Parameters:**
- `q` (required): Search query
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 20, max: 100)

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/books/1099/search?api_key=YOUR_API_KEY&q=discourse&page=1&page_size=3"
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "1099_chapter_5",
      "book_id": 1099,
      "content": "Text about discourse...",
      "chapter_number": 5,
      "word_count": 400,
      "relevance_score": 0.92
    }
  ],
  "book_info": {
    "book_id": 1099,
    "title": "Book Title",
    "author": "Author Name"
  },
  "pagination": {
    "page": 1,
    "page_size": 3,
    "total_items": 23,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "search_query": "discourse",
    "query_time_ms": 374.53
  }
}
```

---

## 🧠 Fuzzy Search Endpoints 🆕

### `GET /fuzzy-search`
**Authentication required** - Advanced fuzzy search with vector embeddings and multiple algorithms.

**Parameters:**
- `q` (required): Search query
- `type` (required): Search type
  - `semantic`: Pure vector similarity search
  - `fuzzy`: Pure fuzzy text matching
  - `hybrid`: Combined semantic + fuzzy + keyword search
  - `keyword`: Traditional keyword search
- `limit` (optional): Maximum results (default: 20, max: 50)
- `semantic_weight` (optional): Weight for semantic search in hybrid mode (0.0-1.0, default: 0.5)
- `fuzzy_weight` (optional): Weight for fuzzy search in hybrid mode (0.0-1.0, default: 0.3)
- `keyword_weight` (optional): Weight for keyword search in hybrid mode (0.0-1.0, default: 0.2)

**Example Requests:**

#### Semantic Search
```bash
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_API_KEY&q=artificial%20intelligence&type=semantic&limit=3"
```

#### Fuzzy Text Search
```bash
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_API_KEY&q=philosophy&type=fuzzy&limit=3"
```

#### Hybrid Search with Custom Weights
```bash
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_API_KEY&q=democracy&type=hybrid&semantic_weight=0.6&fuzzy_weight=0.3&keyword_weight=0.1&limit=5"
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "795_chapter_8",
      "book_id": 795,
      "content": "Text content with search matches...",
      "chapter_number": 8,
      "word_count": 450,
      "title": "Book Title",
      "author": "Author Name",
      "semantic_similarity": 0.85,
      "fuzzy_score": 0.72,
      "combined_score": 0.79,
      "search_type": "hybrid"
    }
  ],
  "search_stats": {
    "total_results": 5,
    "semantic_count": 3,
    "fuzzy_count": 4,
    "keyword_count": 2,
    "processing_time_ms": 578.51,
    "search_weights": {
      "semantic": 0.6,
      "fuzzy": 0.3,
      "keyword": 0.1
    },
    "query": "democracy"
  }
}
```

---

## 🔗 Legacy V3 Compatibility Endpoints

For backwards compatibility with existing integrations, the following v3 endpoints are available:

### `GET /api/v3/health`
**No authentication required** - V3 format health check.

```bash
curl "https://api.ashortstayinhell.com:5562/api/v3/health"
```

### `GET /api/v3/search`
**Authentication required** - V3 format search endpoint.

**Parameters:**
- `q` (required): Search query
- `type` (optional): Search type
- `limit` (optional): Maximum results

```bash
curl "https://api.ashortstayinhell.com:5562/api/v3/search?api_key=YOUR_API_KEY&q=Foucault&limit=2"
```

**Response includes `api_version: "3.0-unified"` for compatibility tracking.**

---

## 🛡️ Security Features

### HTTPS/SSL
- **Let's Encrypt certificates** for api.ashortstayinhell.com
- **HTTPS enforced** for all connections
- **Security headers** on all responses

### Authentication & Authorization
- **API key required** for all data endpoints
- **Rate limiting** prevents abuse (60 req/min)
- **Request logging** tracks all access
- **IP-based monitoring** for security analysis

### Database Security
- **PostgreSQL** with optimized indexes
- **Parameterized queries** prevent SQL injection
- **Connection pooling** with proper cleanup

---

## 📊 Current Statistics

- **📚 Total Books**: 838
- **📝 Total Chunks**: 25,067
- **🧠 Total Vector Embeddings**: 18,363
- **⚡ Average Response Time**: 50-600ms (depending on search complexity)
- **🔒 Security**: 100% API key protected
- **📈 Uptime**: 99.9%+

---

## 🚀 Quick Start Examples

### Basic Book Discovery
```bash
# Get first 5 books
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page_size=5"
```

### Traditional Search
```bash
# Search for books about Foucault
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_API_KEY&q=Foucault"
```

### Semantic Vector Search
```bash
# Find books similar to "artificial intelligence" using vector embeddings
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_API_KEY&q=artificial%20intelligence&type=semantic&limit=5"
```

### Search Within a Book
```bash
# Search for "discourse" within a specific Foucault book
curl "https://api.ashortstayinhell.com:5562/books/1099/search?api_key=YOUR_API_KEY&q=discourse"
```

### Hybrid Fuzzy Search
```bash
# Use hybrid search combining multiple algorithms
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_API_KEY&q=democracy&type=hybrid&limit=10"
```

---

## ⚠️ Error Handling

**Standard Error Response:**
```json
{
  "error": "Authentication required",
  "success": false
}
```

**Common HTTP Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Book/chunk not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## 🆕 What's New in the Unified API

### ✅ Consolidated Features
- **Single endpoint** (port 5562) - no more v2/v3 separation
- **All functionality** combined in one API
- **Backwards compatibility** with v3 format endpoints

### ✅ New Search Capabilities
- **In-book search**: Search within specific books
- **Fuzzy search**: Advanced text similarity matching
- **Semantic search**: Vector embedding similarity with 18,363 embeddings
- **Hybrid search**: Combines multiple search algorithms with custom weights

### ✅ Enhanced Performance
- **Vector embeddings**: 18,363+ pre-computed embeddings for semantic search
- **Multiple algorithms**: Cosine similarity, Levenshtein distance, token matching
- **Weighted results**: Customizable algorithm weights in hybrid mode

---

## 🤖 Agent Integration Notes

**For AI Agents and Integrations:**
- Use `/fuzzy-search?type=hybrid` for best search results
- Leverage `semantic_weight` parameters to tune search behavior
- Monitor `processing_time_ms` in responses for performance optimization
- Use in-book search for focused research within specific texts
- Check `/health` endpoint for system status monitoring

**Production Deployment:**
- **Single unified service** on port 5562
- **SSL/HTTPS**: Let's Encrypt certificates auto-renewed
- **Logging**: Production logs at `/logs/production_secure_paginated_api.log`
- **Auto-restart**: Managed by system daemon

---

*🎯 This unified API provides secure, paginated access to 838 real books with advanced search capabilities including fuzzy search and vector embeddings. Perfect for AI agents, research tools, and knowledge discovery applications.*

**Last Updated**: July 14, 2025 | **API Version**: Unified (formerly v2 + v3)