# 📚 LibraryOfBabel API Reference v2.0

**Complete documentation for the LibraryOfBabel API with 5,832 books, field-specific search, and comprehensive pagination.**

**🎯 Production Ready**: Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture  
**📱 Mobile Optimized**: Dr. Elena Rodriguez (IAV) Information Architecture  
**🔍 Field-Specific Search**: Advanced filtering by title, author, description, genre  

---

## 🌐 Base URLs

| Environment | URL | Port | Usage |
|-------------|-----|------|-------|
| **Production** | `https://api.ashortstayinhell.com:5562` | 5562 | Live API |
| **Staging** | `https://staging.ashortstayinhell.com:5568` | 5568 | Testing |

---

## 🔐 Authentication

**All endpoints require API key authentication.**

### Authentication Methods
```bash
# Query Parameter (Recommended)
?api_key=YOUR_API_KEY

# Authorization Header
Authorization: Bearer YOUR_API_KEY

# X-API-Key Header
X-API-Key: YOUR_API_KEY
```

### Rate Limiting
- **60 requests per minute** per API key
- Rate limit headers included in responses
- Security monitoring active

---

## 📊 Core Endpoints

### 1. Books API (`/api/books`)

**Base URL**: `/api/books`  
**Description**: Access book metadata, content, and pagination with 5,832 total books

#### Supported Actions

| Action | Description | Required Parameters | Optional Parameters |
|--------|-------------|-------------------|-------------------|
| `list` | List books with pagination and sorting | None | `limit`, `page`, `sort`, `format` |
| `summary` | Get book summary | `id` | `format` |
| `toc` | Get table of contents | `id` | `format` |
| `random_page` | Get random page from book | `id` | `format` |
| `construct` | Get book construction info | `id` | `format` |
| `page` | Get specific page | `id`, `page_num` | `words_per_page`, `format` |

#### Parameters

| Parameter | Type | Default | Validation | Description |
|-----------|------|---------|------------|-------------|
| `action` | string | `list` | See actions above | Action to perform |
| `id` | integer | `5560` | 1-999999 | Book ID |
| `limit` | integer | `20` | 1-200 | Results per page |
| `page` | integer | `1` | 1-10000 | Page number |
| `sort` | string | `title` | book_id, author, title, publication_date, word_count | Sort field |
| `format` | string | `json` | json, simple | Response format |
| `words_per_page` | integer | `1000` | 100-2000 | Words per page for dynamic pagination |
| `page_num` | integer | - | 1+ | Specific page number for `page` action |

#### Sorting Options

| Sort Field | Description | Order |
|------------|-------------|-------|
| `book_id` | Sort by book ID | Ascending (1, 2, 3...) |
| `author` | Sort by author name | Alphabetical |
| `title` | Sort by book title | Alphabetical (default) |
| `publication_date` | Sort by publication date | Descending (newest first) |
| `word_count` | Sort by book length | Descending (longest first) |

#### Pagination Response

```json
{
  "data": {
    "items": [...],
    "pagination": {
      "limit": 20,
      "page": 1,
      "total_count": 5832,
      "total_pages": 292
    },
    "sorting": {
      "sort_by": "title",
      "sort_options": ["book_id", "author", "title", "publication_date", "word_count"]
    }
  },
  "success": true,
  "meta": {
    "request_id": "...",
    "response_time_ms": 45.2,
    "timestamp": "2025-01-17T10:30:00Z"
  }
}
```

#### Examples

**List Books (Default)**
```bash
curl "https://api.ashortstayinhell.com:5562/api/books?api_key=YOUR_KEY"
```

**List Books with Custom Pagination and Sorting**
```bash
curl "https://api.ashortstayinhell.com:5562/api/books?action=list&limit=10&page=5&sort=word_count&api_key=YOUR_KEY"
```

**Get Book Summary**
```bash
curl "https://api.ashortstayinhell.com:5562/api/books?action=summary&id=4297&api_key=YOUR_KEY"
```

**Get Table of Contents**
```bash
curl "https://api.ashortstayinhell.com:5562/api/books?action=toc&id=4297&api_key=YOUR_KEY"
```

**Get Specific Page with Dynamic Word Count**
```bash
curl "https://api.ashortstayinhell.com:5562/api/books?action=page&id=4297&page_num=1&words_per_page=500&api_key=YOUR_KEY"
```

**Get Random Page**
```bash
curl "https://api.ashortstayinhell.com:5562/api/books?action=random_page&id=4297&api_key=YOUR_KEY"
```

---

### 2. Search API (`/api/search`)

**Base URL**: `/api/search`  
**Description**: Advanced search with field-specific filtering, semantic search, and compound queries

#### Supported Actions

| Action | Description | Search Type | Field-Specific |
|--------|-------------|-------------|----------------|
| `search` | Basic content search | Text/Keyword | ✅ |
| `count` | Count search results | Text/Keyword | ✅ |
| `titles` | Search book titles only | Text/Keyword | ✅ |
| `books` | Comprehensive book metadata search | Metadata | ✅ |
| `has_results` | Check if results exist | Text/Keyword | ✅ |
| `semantic` | Semantic vector search (book-level) | AI/Vector | ❌ |
| `semantic_passages` | Semantic search (passage-level) | AI/Vector | ❌ |
| `concept` | Concept-based search | AI/Conceptual | ❌ |
| `passage` | Passage similarity search | AI/Vector | ❌ |
| `emotional` | Emotional content search | AI/Sentiment | ❌ |
| `highlighted` | Search with highlighting | Text/Keyword | ✅ |
| `advanced` | Advanced multi-field search | Combined | ✅ |

#### Parameters

| Parameter | Type | Default | Validation | Description |
|-----------|------|---------|------------|-------------|
| `q` | string | None | 1-500 chars | Global search query (optional for field-specific) |
| `action` | string | `search` | See actions above | Search action |
| `limit` | integer | `20` | 1-200 | Results per page |
| `page` | integer | `1` | 1-10000 | Page number |
| `sort` | string | `relevance` | title, author, date, relevance, popularity | Sort order |
| `format` | string | `json` | json, simple | Response format |
| `id` | integer | None | 1-999999 | Specific book ID filter |
| **Field-Specific Parameters** |
| `title` | string | None | 1-500 chars | Filter by book title |
| `author` | string | None | 1-255 chars | Filter by author name |
| `description` | string | None | 1-500 chars | Filter by book description |
| `genre` | string | None | 1-100 chars | Filter by genre |

#### Field-Specific Search

**🔥 NEW FEATURE**: Search specific fields independently or in combination

**Single Field Search**
```bash
# Search only book titles
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&title=dystopian&api_key=YOUR_KEY"

# Search only authors
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&author=stephen%20king&api_key=YOUR_KEY"

# Search only genres
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&genre=science%20fiction&api_key=YOUR_KEY"

# Search only descriptions
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&description=love%20story&api_key=YOUR_KEY"
```

**Combined Field Search**
```bash
# Author + Genre combination
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&author=king&genre=horror&api_key=YOUR_KEY"

# Global search + field-specific filter
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&q=magic&author=tolkien&api_key=YOUR_KEY"
```

#### Field-Specific Response

```json
{
  "data": {
    "data": {
      "books": [
        {
          "author": "Shade Owens",
          "book_id": 4297,
          "chunk_count": 1,
          "description": "No description available",
          "genre": "Unknown Genre",
          "title": "Chosen: A Dystopian Novel (The Immortal Ones Book 1)",
          "word_count": 63392
        }
      ],
      "filters_applied": {
        "author_filter": "",
        "description_filter": "",
        "genre_filter": "",
        "search_query": "",
        "title_filter": "dystopian"
      },
      "pagination": {
        "books_per_page": 20,
        "current_page": 1,
        "has_next": false,
        "has_previous": false,
        "total_books": 1,
        "total_pages": 1
      },
      "sort_order": "author_title"
    },
    "success": true
  },
  "meta": {
    "request_id": "...",
    "response_time_ms": 15.3,
    "timestamp": "2025-01-17T10:30:00Z"
  },
  "success": true
}
```

#### Search Examples

**Basic Text Search**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=philosophy&action=search&limit=10&api_key=YOUR_KEY"
```
*Response includes books matching in title, author, or content with trigram-optimized search.*

**Count Results**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=artificial%20intelligence&action=count&api_key=YOUR_KEY"
```
*Fast counting using trigram indexes on book titles and authors.*

**Title-Only Search**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=game%20of%20thrones&action=titles&api_key=YOUR_KEY"
```

**Check If Results Exist**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=quantum%20physics&action=has_results&api_key=YOUR_KEY"
```

**Semantic Search (AI-Powered)**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=coming%20of%20age%20stories&action=semantic&limit=5&api_key=YOUR_KEY"
```

**Semantic Passage Search**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=existential%20crisis&action=semantic_passages&limit=10&api_key=YOUR_KEY"
```

**Emotional Content Search**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?q=melancholy%20and%20nostalgia&action=emotional&api_key=YOUR_KEY"
```

**Advanced Multi-Field Search**
```bash
curl "https://api.ashortstayinhell.com:5562/api/search?action=advanced&title=war&author=tolstoy&genre=historical%20fiction&api_key=YOUR_KEY"
```

---

## 📊 Pagination Deep Dive

### Pagination Metadata

All paginated endpoints return consistent pagination information:

```json
{
  "pagination": {
    "limit": 20,           // Results per page (1-200)
    "page": 1,             // Current page (1-10000)
    "total_count": 5832,   // Total items available
    "total_pages": 292     // Total pages available
  }
}
```

### Pagination Examples

**Navigate Through Large Dataset**
```bash
# Page 1 (books 1-20)
curl "https://api.ashortstayinhell.com:5562/api/books?page=1&limit=20&api_key=YOUR_KEY"

# Page 10 (books 181-200)
curl "https://api.ashortstayinhell.com:5562/api/books?page=10&limit=20&api_key=YOUR_KEY"

# Page 100 (books 1981-2000)
curl "https://api.ashortstayinhell.com:5562/api/books?page=100&limit=20&api_key=YOUR_KEY"

# Custom page size (books 1-50)
curl "https://api.ashortstayinhell.com:5562/api/books?page=1&limit=50&api_key=YOUR_KEY"
```

**Large Page Sizes**
```bash
# Maximum page size (200 books per page)
curl "https://api.ashortstayinhell.com:5562/api/books?limit=200&api_key=YOUR_KEY"

# Small mobile-friendly size (5 books per page)
curl "https://api.ashortstayinhell.com:5562/api/books?limit=5&api_key=YOUR_KEY"
```

---

## 🔧 Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Parameter 'limit' must be between 1 and 200"
  },
  "success": false,
  "meta": {
    "request_id": "...",
    "response_time_ms": 2.1,
    "timestamp": "2025-01-17T10:30:00Z"
  }
}
```

### Common Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| `MISSING_REQUIRED` | Required parameter missing | Add required parameter |
| `INVALID_TYPE` | Wrong parameter type | Check parameter type |
| `INVALID_VALUE` | Parameter value not allowed | Use valid value from enum |
| `TOO_LARGE` | Parameter value too large | Reduce parameter value |
| `TOO_SMALL` | Parameter value too small | Increase parameter value |
| `UNEXPECTED_PARAMETERS` | Unknown parameters provided | Remove invalid parameters |
| `AUTHENTICATION_REQUIRED` | Missing or invalid API key | Provide valid API key |

---

## 📱 Response Formats

### JSON Format (Default)

Full response with metadata, pagination, and structured data.

### Simple Format

Minimal response for mobile applications:

```bash
curl "https://api.ashortstayinhell.com:5562/api/books?format=simple&api_key=YOUR_KEY"
```

Returns simplified structure without metadata wrapper.

---

## 📱 Mobile-Optimized Endpoints (`/api/mobile/*`)

**Base URL**: `/api/mobile/*`  
**Description**: Lightweight endpoints optimized for mobile apps with simplified responses

### Mobile Random Content (`/api/mobile/random`)

**Purpose**: Get random content for mobile apps and iOS shortcuts

#### Parameters

| Parameter | Type | Default | Options | Description |
|-----------|------|---------|---------|-------------|
| `type` | string | `title` | title, author, citation, share | Type of random content |

#### Examples

**Random Book Title**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/random?type=title&api_key=YOUR_KEY"
```

**Random Author**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/random?type=author&api_key=YOUR_KEY"
```

**Random Citation**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/random?type=citation&api_key=YOUR_KEY"
```

**Random Share Text**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/random?type=share&api_key=YOUR_KEY"
```

---

### Mobile Search (`/api/mobile/search`)

**Purpose**: Lightweight search optimized for mobile with limited results

#### Parameters

| Parameter | Type | Default | Validation | Description |
|-----------|------|---------|------------|-------------|
| `q` | string | Required | 1-500 chars | Search query |
| `action` | string | `simple` | simple, count, titles, has_results | Search action |
| `limit` | integer | `5` | 1-10 | Maximum results (mobile-optimized) |

#### Examples

**Simple Mobile Search**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/search?q=philosophy&api_key=YOUR_KEY"
```

**Count Results (Mobile)**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/search?q=science&action=count&api_key=YOUR_KEY"
```

**Titles Only (Mobile)**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/search?q=mystery&action=titles&limit=3&api_key=YOUR_KEY"
```

---

### Mobile Books (`/api/mobile/books`)

**Purpose**: Simplified book information for mobile apps

#### Parameters

| Parameter | Type | Default | Options | Description |
|-----------|------|---------|---------|-------------|
| `action` | string | `summary` | summary, toc, random_page, page | Book action |
| `id` | integer | `5560` | 1-999999 | Book ID |

#### Examples

**Book Summary (Mobile)**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/books?action=summary&id=4297&api_key=YOUR_KEY"
```

**Table of Contents (Mobile)**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/books?action=toc&id=4297&api_key=YOUR_KEY"
```

---

### Mobile Stats (`/api/mobile/stats`)

**Purpose**: System statistics in mobile-friendly format

#### Examples

**Get Mobile Stats**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/stats?api_key=YOUR_KEY"
```

---

### Mobile Lists (`/api/mobile/lists`)

**Purpose**: Curated lists for mobile apps

#### Examples

**Get Mobile Lists**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/lists?api_key=YOUR_KEY"
```

---

### Mobile Dashboard (`/api/mobile/dashboard`)

**Purpose**: Dashboard data optimized for mobile interfaces

#### Examples

**Get Mobile Dashboard**
```bash
curl "https://api.ashortstayinhell.com:5562/api/mobile/dashboard?api_key=YOUR_KEY"
```

---

## 🏥 System Endpoints

### Health Check (`/api/health`)

**Authentication**: Not required  
**Purpose**: Public health check for monitoring

```bash
curl "https://api.ashortstayinhell.com:5562/api/health"
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-17T10:30:00Z",
  "version": "2.0",
  "database": "connected",
  "services": {
    "books": "operational",
    "search": "operational",
    "mobile": "operational"
  }
}
```

---

### System Information (`/api/info`)

**Authentication**: Required  
**Purpose**: Detailed system information

```bash
curl "https://api.ashortstayinhell.com:5562/api/info?api_key=YOUR_KEY"
```

**Response**:
```json
{
  "system": {
    "name": "LibraryOfBabel API",
    "version": "2.0",
    "total_books": 5832,
    "total_chunks": 450000,
    "last_updated": "2025-01-17T10:30:00Z"
  },
  "endpoints": {
    "core": ["/api/books", "/api/search"],
    "mobile": ["/api/mobile/*"],
    "system": ["/api/health", "/api/info"]
  },
  "features": {
    "field_specific_search": true,
    "semantic_search": true,
    "pagination": true,
    "mobile_optimized": true
  }
}
```

---

## 🔌 Advanced Features

### MCP Integration

**Status**: Available via dedicated MCP server (separate from REST API)  
**Location**: `/mcp_server/` directory in codebase  
**Purpose**: Model Context Protocol integration for LLM tools

**Features**:
- Book tool integration
- Search tool integration  
- Browse tool integration
- LLM-optimized responses

**Note**: MCP tools are accessed through dedicated MCP server, not the REST API.

---

## 🎯 Use Cases & Examples

### Common Workflow Examples

**1. Find Books by Specific Author**
```bash
# Step 1: Search for author
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&author=tolkien&api_key=YOUR_KEY"

# Step 2: Get book details
curl "https://api.ashortstayinhell.com:5562/api/books?action=summary&id=BOOK_ID&api_key=YOUR_KEY"
```

**2. Browse Books by Genre**
```bash
# Step 1: Filter by genre
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&genre=science%20fiction&limit=20&api_key=YOUR_KEY"

# Step 2: Sort by word count (longest first)
curl "https://api.ashortstayinhell.com:5562/api/books?action=list&sort=word_count&limit=20&api_key=YOUR_KEY"
```

**3. Mobile App Integration**
```bash
# Get random content for home screen
curl "https://api.ashortstayinhell.com:5562/api/mobile/random?type=title&api_key=YOUR_KEY"

# Quick mobile search
curl "https://api.ashortstayinhell.com:5562/api/mobile/search?q=mystery&limit=3&api_key=YOUR_KEY"
```

**4. Advanced Field Combinations**
```bash
# Complex filter: Horror books by King
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&author=king&genre=horror&api_key=YOUR_KEY"

# Global + field search: Magic books by fantasy authors
curl "https://api.ashortstayinhell.com:5562/api/search?action=books&q=magic&genre=fantasy&api_key=YOUR_KEY"
```

**5. Pagination Navigation**
```bash
# Navigate through large datasets
curl "https://api.ashortstayinhell.com:5562/api/books?page=1&limit=50&api_key=YOUR_KEY"     # First 50
curl "https://api.ashortstayinhell.com:5562/api/books?page=2&limit=50&api_key=YOUR_KEY"     # Next 50
curl "https://api.ashortstayinhell.com:5562/api/books?page=100&limit=50&api_key=YOUR_KEY"   # Books 4951-5000
```

---

## 📊 Performance & Limits

### Response Times
- **Books List**: ~45ms average  
- **Field-Specific Search**: ~15ms average (working in production)
- **Basic Search**: ~1.5s average (now working with trigram optimization)
- **Search Count**: ~100ms average (fast trigram-based counting)
- **Mobile Endpoints**: ~20ms average

### Data Limits
- **Total Books**: 5,832
- **Total Pages**: 1,167 (with default 20 per page)
- **Maximum Page Size**: 200 books per request
- **Mobile Page Size**: 1-10 results (optimized)

### Rate Limits
- **Standard**: 60 requests per minute per API key
- **Burst**: Up to 120 requests in 30 seconds
- **Daily**: 10,000 requests per day per API key

---

## 🚀 API Features Summary

✅ **Complete Coverage**: All 5,832 books with full metadata  
🔍 **Field-Specific Search**: title, author, description, genre filtering  
📊 **Accurate Pagination**: Real book counts with proper page calculation  
🎯 **Multiple Sort Options**: 5 different sorting methods  
📱 **Mobile Optimized**: Dedicated lightweight endpoints  
🤖 **AI Integration**: Semantic search and MCP protocol support  
⚡ **High Performance**: Optimized PostgreSQL-first architecture  
🔒 **Secure**: API key authentication with rate limiting  
📝 **Comprehensive**: 12 search actions, 6 book actions  
🔄 **Backward Compatible**: Support for legacy endpoints  

---

**📚 LibraryOfBabel API v2.0** - Complete access to 5,832 books with field-specific search, accurate pagination, and mobile optimization.

*Generated: 2025-01-17 | Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture*