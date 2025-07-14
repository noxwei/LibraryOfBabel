# 📚 LibraryOfBabel API Reference v2.0

Complete documentation for the LibraryOfBabel Secure Paginated API. This API provides authenticated access to 838 real books with advanced pagination, chunking, and search capabilities.

## 🌐 Production Endpoint

**Base URL**: `https://api.ashortstayinhell.com:5562`

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
curl "https://api.ashorystayinhell.com:5562/books?api_key=YOUR_API_KEY&page=1&page_size=5&search=magic"
```

**Response:**
```json
{
  "results": [
    {
      "book_id": 611,
      "title": "Harry Potter and the Philosopher's Stone",
      "author": "J.K. Rowling",
      "publisher": "Bloomsbury",
      "publication_date": "1997-06-26T00:00:00+00:00",
      "language": "en-GB",
      "genre": "fantasy",
      "word_count": 77325,
      "processed_date": "Sun, 06 Jul 2025 00:49:50 GMT",
      "has_hash": true,
      "links": {
        "self": "https://api.ashortstayinhell.com:5562/books/611",
        "chunks": "https://api.ashortstayinhell.com:5562/books/611/chunks"
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
  },
  "meta": {
    "timestamp": "2025-07-14T13:35:25.089000",
    "query_time_ms": 30.01
  }
}
```

### `GET /books/{book_id}`
**Authentication required** - Get specific book details.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/books/611?api_key=YOUR_API_KEY"
```

**Response:**
```json
{
  "book_id": 611,
  "title": "Harry Potter and the Philosopher's Stone",
  "author": "J.K. Rowling",
  "publisher": "Bloomsbury",
  "publication_date": "1997-06-26T00:00:00+00:00",
  "language": "en-GB",
  "isbn": "9780747532699",
  "description": "The first book in the Harry Potter series...",
  "genre": "fantasy",
  "word_count": 77325,
  "file_path": "/processed/harry_potter_1.epub",
  "processed_date": "Sun, 06 Jul 2025 00:49:50 GMT",
  "md5_hash": "abc123def456...",
  "chunks_available": 45,
  "embeddings_available": 42,
  "links": {
    "chunks": "https://api.ashortstayinhell.com:5562/books/611/chunks",
    "search_in_book": "https://api.ashortstayinhell.com:5562/search?q=&book_id=611"
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
curl "https://api.ashortstayinhell.com:5562/books/611/chunks?api_key=YOUR_API_KEY&chunk_level=small&page=1"
```

**Response:**
```json
{
  "results": [
    {
      "chunk_id": 1234,
      "title": "Chapter 1: The Boy Who Lived",
      "chapter_number": 1,
      "original_word_count": 2847,
      "sub_chunks": [
        {
          "chunk_id": 1,
          "text": "Mr. and Mrs. Dursley of number four, Privet Drive...",
          "word_count": 125,
          "char_count": 487,
          "chunk_level": "small"
        }
      ],
      "total_sub_chunks": 6,
      "chunk_level": "small",
      "links": {
        "full_content": "https://api.ashortstayinhell.com:5562/chunks/1234?chunk_level=small"
      }
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
    "chunk_level": "small",
    "available_levels": ["small", "medium", "large"]
  }
}
```

### `GET /chunks/{chunk_id}`
**Authentication required** - Get full chunk content with specified chunking level.

**Parameters:**
- `chunk_level` (optional): Chunking granularity (small/medium/large)

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/chunks/1234?api_key=YOUR_API_KEY&chunk_level=medium"
```

**Response:**
```json
{
  "chunk_id": 1234,
  "book_id": 611,
  "title": "Chapter 1: The Boy Who Lived",
  "chapter_number": 1,
  "original_word_count": 2847,
  "chunk_level": "medium",
  "sub_chunks": [
    {
      "chunk_id": 1,
      "text": "Mr. and Mrs. Dursley of number four, Privet Drive, were proud to say that they were perfectly normal, thank you very much...",
      "word_count": 378,
      "char_count": 1456,
      "chunk_level": "medium"
    }
  ],
  "total_sub_chunks": 2,
  "links": {
    "book": "https://api.ashortstayinhell.com:5562/books/611"
  },
  "meta": {
    "query_time_ms": 8.92
  }
}
```

---

## 🔍 Search Endpoint

### `GET /search`
**Authentication required** - Search books with pagination.

**Parameters:**
- `q` (required): Search query
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 20, max: 100)
- `book_id` (optional): Search within specific book

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_API_KEY&q=magic&page=1"
```

**Response:**
```json
{
  "results": [
    {
      "book_id": 611,
      "title": "Harry Potter and the Philosopher's Stone",
      "author": "J.K. Rowling",
      "description": "The first book in the Harry Potter series about a young wizard...",
      "word_count": 77325,
      "links": {
        "book": "https://api.ashortstayinhell.com:5562/books/611",
        "chunks": "https://api.ashortstayinhell.com:5562/books/611/chunks"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 47,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "navigation": {
    "next": "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_API_KEY&q=magic&page=2"
  },
  "meta": {
    "timestamp": "2025-07-14T13:35:25.089000",
    "query_time_ms": 25.43,
    "search_query": "magic"
  }
}
```

---

## 📖 API Documentation Endpoint

### `GET /api-docs`
**No authentication required** - Interactive API documentation with examples.

**Example Request:**
```bash
curl https://api.ashortstayinhell.com:5562/api-docs
```

**Response:**
```json
{
  "title": "LibraryOfBabel Secure Paginated API v2.0",
  "description": "Enhanced API with pagination, chunking levels, navigation links, and authentication",
  "base_url": "https://api.ashortstayinhell.com:5562",
  "authentication": {
    "required": true,
    "methods": [
      "Authorization: Bearer YOUR_API_KEY",
      "X-API-Key: YOUR_API_KEY", 
      "api_key query parameter"
    ],
    "rate_limit": "60 requests per minute"
  },
  "features": [
    "API Key Authentication",
    "Rate limiting (60 req/min)",
    "Request logging",
    "Pagination with navigation links",
    "Configurable chunking levels (small/medium/large)",
    "Text search with ranking",
    "Optimized for large datasets",
    "HTTPS security headers"
  ],
  "endpoints": {
    "/health": {
      "method": "GET",
      "description": "Health check and system info",
      "authentication": false,
      "example": "https://api.ashortstayinhell.com:5562/health"
    },
    "/books": {
      "method": "GET", 
      "description": "List books with pagination and search",
      "authentication": true,
      "parameters": {
        "page": "Page number (default: 1)",
        "page_size": "Items per page (default: 20, max: 100)",
        "search": "Search in title/author",
        "author": "Filter by author",
        "genre": "Filter by genre"
      },
      "example": "https://api.ashortstayinhell.com:5562/books?page=1&page_size=10&search=magic&api_key=YOUR_API_KEY"
    }
  },
  "chunking_levels": {
    "small": 500,
    "medium": 1500,
    "large": 5000
  },
  "navigation": {
    "description": "All paginated endpoints return navigation links",
    "fields": {
      "next": "URL for next page",
      "prev": "URL for previous page",
      "first": "URL for first page", 
      "last": "URL for last page"
    }
  }
}
```

---

## 🛡️ Security Features

### HTTPS/SSL
- **Let's Encrypt certificates** for api.ashortstayinhell.com
- **HTTPS enforced** for all connections
- **Security headers** on all responses:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Authentication & Authorization
- **API key required** for all data endpoints
- **Rate limiting** prevents abuse (60 req/min)
- **Request logging** tracks all access
- **IP-based monitoring** for security analysis

### Database Security
- **PostgreSQL** with optimized indexes
- **Parameterized queries** prevent SQL injection
- **Connection pooling** with proper cleanup
- **Auto-commit transactions** for data integrity

---

## 📊 Current Statistics

- **📚 Total Books**: 838
- **📝 Total Chunks**: 25,067
- **🧠 Total Embeddings**: 18,363
- **⚡ Average Response Time**: 12-30ms
- **🔒 Security**: 100% API key protected
- **📈 Uptime**: 99.9%+

---

## 🚀 Quick Start Examples

### Basic Book Listing
```bash
# Get first 5 books
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page_size=5"
```

### Search for Specific Content
```bash
# Search for books about artificial intelligence
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_API_KEY&q=artificial%20intelligence"
```

### Navigate to Last Page
```bash
# Jump to the last page to see newest books
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&page=168&page_size=5"
```

### Get Book Chunks with Small Chunking
```bash
# Get small chunks for detailed analysis
curl "https://api.ashortstayinhell.com:5562/books/611/chunks?api_key=YOUR_API_KEY&chunk_level=small"
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

## 🤖 Agent Integration Notes

**For Lexi (Reddit Bibliophile Agent):**
- Use `/books?page=random` pattern for diverse content discovery
- Leverage `chunk_level=small` for detailed text analysis
- Monitor `total_items` in pagination for collection growth tracking
- Use search endpoint for topic-specific book discovery
- Check `/health` endpoint for system status monitoring

**Production Deployment:**
- **Auto-restart daemon** active: `com.librarybabel.api`
- **Port**: 5562 (managed by launchd)
- **SSL/HTTPS**: Let's Encrypt certificates auto-renewed
- **Logging**: Production logs at `/logs/production_secure_paginated_api.log`

---

*🎯 This API provides secure, paginated access to 838 real books with advanced chunking capabilities. Perfect for AI agents, research tools, and knowledge discovery applications.*

**Last Updated**: July 14, 2025 | **API Version**: 2.0-secure-paginated