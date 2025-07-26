# 📚 LibraryOfBabel iOS Shortcuts API Reference

Complete documentation for the LibraryOfBabel iOS Shortcuts API. This mobile-first API provides authenticated access to 2,730 real books with iOS Shortcuts optimization, Data Jar integration, and mobile workflows.

**🎯 DESIGNED BY: Dr. Elena Rodriguez (IAV) - Information Architecture Validator**  
**🏛️ PHILOSOPHY: "Information architecture makes complex knowledge feel simple"**  
**📱 OPTIMIZED FOR: iOS Shortcuts, Data Jar, Mobile Workflows**

## 🌐 Production Endpoint

**Base URL**: `https://api.ashortstayinhell.com:5562/api/shortcuts/`  
**Version**: iOS Shortcuts API (mobile-first design)

## 🔐 Authentication

**All endpoints (except `/health`) require API key authentication.**

### Authentication Methods
1. **Query Parameter** (Recommended for testing):
   ```bash
   ?api_key=***REMOVED***
   ```

2. **Authorization Header**:
   ```bash
   Authorization: Bearer ***REMOVED***
   ```

3. **X-API-Key Header**:
   ```bash
   X-API-Key: ***REMOVED***
   ```

### Rate Limiting
- **60 requests per minute** per API key
- Rate limit headers included in responses
- Security monitoring and request logging active

---

## 📊 System Health

### `GET /api/shortcuts/health`
**No authentication required** - Public health check endpoint.

**Example Request:**
```bash
curl https://api.ashortstayinhell.com:5562/api/shortcuts/health
```

**Response:**
```json
{
  "status": "healthy",
  "namespace": "shortcuts",
  "designed_by": "Dr. Elena Rodriguez (IAV)",
  "optimized_for": ["iOS Shortcuts", "Data Jar", "Mobile Workflows"],
  "philosophy": "Information architecture makes complex knowledge feel simple",
  "endpoints_available": [
    "/books/count",
    "/random/title",
    "/random/author",
    "/search/{term}/count",
    "/search/{term}/has-results",
    "/books/title-list",
    "/books/author-list",
    "/search/{term}/titles",
    "/random/citation",
    "/random/share-text",
    "/search/{term}/summary",
    "/stats/dashboard",
    "/user/reading-progress",
    "/search/{term}/simple",
    "/books/{id}/summary"
  ],
  "timestamp": "2025-07-23T01:52:10.199804"
}
```

---

## 📚 Books Endpoints

### `GET /api/shortcuts/books/count`
**Authentication required** - Get total book count.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/count?api_key=***REMOVED***"
```

**Response:**
```
2730
```

### `GET /api/shortcuts/books/title-list`
**Authentication required** - Get list of all book titles.

**Parameters:**
- `limit` (optional): Maximum number of titles (default: all)
- `page` (optional): Page number for pagination
- `search` (optional): Filter titles by search term

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/title-list?api_key=***REMOVED***&limit=10"
```

**Response:**
```json
[
  "The Age of Surveillance Capitalism",
  "Being and Time",
  "Algorithms of Oppression",
  "Black Skin, White Masks",
  "How Emotions Are Made",
  "The Body Keeps the Score",
  "Discipline and Punish",
  "The Second Sex",
  "The Wretched of the Earth",
  "Pedagogy of the Oppressed"
]
```

### `GET /api/shortcuts/books/author-list`
**Authentication required** - Get list of all authors.

**Parameters:**
- `limit` (optional): Maximum number of authors (default: all)
- `page` (optional): Page number for pagination
- `search` (optional): Filter authors by search term

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/author-list?api_key=***REMOVED***&limit=10"
```

**Response:**
```json
[
  "Shoshana Zuboff",
  "Martin Heidegger",
  "Safiya Noble",
  "Frantz Fanon",
  "Lisa Feldman Barrett",
  "Bessel van der Kolk",
  "Michel Foucault",
  "Simone de Beauvoir",
  "Frantz Fanon",
  "Paulo Freire"
]
```

### `GET /api/shortcuts/books/{book_id}/summary`
**Authentication required** - Get specific book details and summary.

**Parameters:**
- `book_id` (required): Book ID

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/1099/summary?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "book_id": 1099,
    "title": "Discipline and Punish",
    "author": "Michel Foucault",
    "publication_year": 1975,
    "genre": "Philosophy",
    "word_count": 125000,
    "chunk_count": 45,
    "description": "Analysis of the development of the modern penal system...",
    "summary": "Foucault's seminal work on the history of punishment and surveillance..."
  }
}
```

### `GET /api/shortcuts/books/{book_id}/construct`
**Authentication required** - Get complete book structure and navigation.

**Parameters:**
- `book_id` (required): Book ID

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/1099/construct?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "book_id": 1099,
    "title": "Discipline and Punish",
    "author": "Michel Foucault",
    "structure": {
      "total_pages": 45,
      "chapters": [
        {"chapter": 1, "title": "The Body of the Condemned", "page_start": 1},
        {"chapter": 2, "title": "The Spectacle of the Scaffold", "page_start": 15},
        {"chapter": 3, "title": "Docile Bodies", "page_start": 30}
      ]
    },
    "navigation": {
      "first_page": "/api/shortcuts/books/1099/page/1",
      "last_page": "/api/shortcuts/books/1099/page/45"
    }
  }
}
```

### `GET /api/shortcuts/books/{book_id}/page/{page_num}`
**Authentication required** - Get specific page content with navigation.

**Parameters:**
- `book_id` (required): Book ID
- `page_num` (required): Page number

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/1099/page/1?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "book_id": 1099,
    "title": "Discipline and Punish",
    "page_number": 1,
    "content": "Page content text...",
    "word_count": 450,
    "navigation": {
      "previous_page": null,
      "next_page": "/api/shortcuts/books/1099/page/2",
      "first_page": "/api/shortcuts/books/1099/page/1",
      "last_page": "/api/shortcuts/books/1099/page/45"
    }
  }
}
```

### `GET /api/shortcuts/books/{book_id}/toc`
**Authentication required** - Get table of contents.

**Parameters:**
- `book_id` (required): Book ID

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/1099/toc?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "book_id": 1099,
    "title": "Discipline and Punish",
    "table_of_contents": [
      {"chapter": 1, "title": "The Body of the Condemned", "page": 1},
      {"chapter": 2, "title": "The Spectacle of the Scaffold", "page": 15},
      {"chapter": 3, "title": "Docile Bodies", "page": 30},
      {"chapter": 4, "title": "The Means of Correct Training", "page": 45}
    ]
  }
}
```

---

## 🎲 Random Content Endpoints

### `GET /api/shortcuts/random/title`
**Authentication required** - Get a random book title.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/title?api_key=***REMOVED***"
```

**Response:**
```
"The Elegant Universe"
```

### `GET /api/shortcuts/random/author`
**Authentication required** - Get a random author name.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/author?api_key=***REMOVED***"
```

**Response:**
```
"Andrew Rowe"
```

### `GET /api/shortcuts/random/citation`
**Authentication required** - Get a random book citation.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/citation?api_key=***REMOVED***"
```

**Response:**
```
"Ocean Vuong. On Earth We're Briefly Gorgeous (2019)"
```

### `GET /api/shortcuts/random/share-text`
**Authentication required** - Get a random shareable text.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/share-text?api_key=***REMOVED***"
```

**Response:**
```
"📚 Currently reading: Fevered Star by Rebecca Roanhorse"
```

---

## 🔍 Search Endpoints

### `GET /api/shortcuts/search/{term}/count`
**Authentication required** - Get count of books matching search term.

**Parameters:**
- `term` (required): Search term

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/philosophy/count?api_key=***REMOVED***"
```

**Response:**
```
1512
```

### `GET /api/shortcuts/search/{term}/has-results`
**Authentication required** - Check if search term has results.

**Parameters:**
- `term` (required): Search term

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/philosophy/has-results?api_key=***REMOVED***"
```

**Response:**
```
true
```

### `GET /api/shortcuts/search/{term}/titles`
**Authentication required** - Get titles of books matching search term.

**Parameters:**
- `term` (required): Search term
- `limit` (optional): Maximum number of titles (default: all)

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/philosophy/titles?api_key=***REMOVED***&limit=5"
```

**Response:**
```json
[
  "Being and Time",
  "Discipline and Punish",
  "The Second Sex",
  "Black Skin, White Masks",
  "The Wretched of the Earth"
]
```

### `GET /api/shortcuts/search/{term}/summary`
**Authentication required** - Get summary of search results.

**Parameters:**
- `term` (required): Search term

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/artificial%20intelligence/summary?api_key=***REMOVED***"
```

**Response:**
```
"Found 359 books about artificial intelligence"
```

### `GET /api/shortcuts/search/{term}/simple`
**Authentication required** - Get simplified search results.

**Parameters:**
- `term` (required): Search term
- `limit` (optional): Maximum number of results (default: 10)

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/philosophy/simple?api_key=***REMOVED***&limit=3"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "philosophy",
    "total_results": 1512,
    "results": [
      {
        "book_id": 1099,
        "title": "Discipline and Punish",
        "author": "Michel Foucault",
        "match_type": "content",
        "relevance_score": 0.95
      },
      {
        "book_id": 1100,
        "title": "Being and Time",
        "author": "Martin Heidegger",
        "match_type": "title",
        "relevance_score": 0.92
      },
      {
        "book_id": 1101,
        "title": "The Second Sex",
        "author": "Simone de Beauvoir",
        "match_type": "content",
        "relevance_score": 0.88
      }
    ]
  }
}
```

---

## 📊 Statistics & Dashboard

### `GET /api/shortcuts/stats/dashboard`
**Authentication required** - Get comprehensive library statistics.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/stats/dashboard?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "library_stats": {
      "total_books": 2730,
      "total_chunks": 79054,
      "avg_chunks_per_book": 31.4,
      "unique_authors": 2152,
      "books_2000s_plus": 1843,
      "books_pre_2000": 166
    },
    "top_authors": [
      {"author": "Brandon Sanderson", "book_count": 18},
      {"author": "Lee Child", "book_count": 10},
      {"author": "Terry Pratchett", "book_count": 8},
      {"author": "Neal Shusterman", "book_count": 8},
      {"author": "Unknown Author", "book_count": 8}
    ],
    "genre_distribution": {
      "fiction": 1250,
      "non-fiction": 1480,
      "philosophy": 320,
      "science": 280,
      "history": 220
    }
  }
}
```

### `GET /api/shortcuts/user/reading-progress`
**Authentication required** - Get user reading metrics.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/user/reading-progress?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "books_read": 45,
    "pages_read": 1250,
    "reading_streak": 7,
    "favorite_genre": "Philosophy",
    "reading_goal": 50,
    "progress_percentage": 90
  }
}
```

---

## 🎭 Serendipity Features

### `GET /api/shortcuts/serendipity/random-passage`
**Authentication required** - Get a random passage for creative inspiration.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/serendipity/random-passage?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "passage": "The body is not a thing, it is a situation: it is our grasp on the world and our sketch of our project.",
    "source": {
      "book": "The Second Sex",
      "author": "Simone de Beauvoir",
      "chapter": "The Data of Biology"
    },
    "inspiration_type": "philosophical_reflection"
  }
}
```

### `GET /api/shortcuts/serendipity/story-starter`
**Authentication required** - Get a complete story starter package.

**Example Request:**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/serendipity/story-starter?api_key=***REMOVED***"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "theme": "surveillance",
    "opening_line": "In a world where every movement is tracked...",
    "character_prompt": "A whistleblower who discovers...",
    "setting_description": "A corporate headquarters where...",
    "conflict_hint": "The protagonist must choose between...",
    "inspiration_sources": [
      "The Age of Surveillance Capitalism - Shoshana Zuboff",
      "Discipline and Punish - Michel Foucault"
    ]
  }
}
```

---

## 🔗 Legacy V3 API Endpoints

For backwards compatibility, the following v3 endpoints are also available:

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
curl "https://api.ashortstayinhell.com:5562/api/v3/search?api_key=***REMOVED***&q=Foucault&limit=2"
```

---

## 🛡️ Security Features

### HTTPS/SSL
- **Let's Encrypt certificates** for api.ashortstayinhell.com
- **HTTPS enforced** for all connections
- **SSL/TLS 1.3** encryption

### Authentication
- **API key required** for all data endpoints
- **Multiple auth methods** supported
- **Rate limiting** (60 requests/minute)
- **Request logging** and monitoring

### Error Handling
**Common HTTP Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid API key
- `404 Not Found` - Book/endpoint not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "error": "Authentication required",
  "success": false
}
```

---

## 🎯 iOS Shortcuts Integration

### **Perfect for iOS Shortcuts**
- **Single-value responses** (no JSON parsing needed)
- **Simple arrays** (easy for shortcuts loops)
- **Pre-formatted text** (ready for sharing/display)
- **Boolean responses** (perfect for if/then logic)
- **Data Jar optimized** (clean objects for persistence)

### **Quick Start Examples**

#### **Get Random Book Title**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/title?api_key=***REMOVED***"
# Returns: "The Elegant Universe"
```

#### **Check if Topic Has Books**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/quantum/has-results?api_key=***REMOVED***"
# Returns: true
```

#### **Get Shareable Text**
```bash
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/share-text?api_key=***REMOVED***"
# Returns: "📚 Currently reading: Fevered Star by Rebecca Roanhorse"
```

---

## 🆕 What's New in the iOS Shortcuts API

### ✅ Mobile-First Design
- **iOS Shortcuts optimized** responses
- **Data Jar integration** ready
- **Mobile workflows** streamlined
- **Single-value endpoints** for easy parsing

### ✅ Serendipity Features
- **Random passage generation** for creative inspiration
- **Story starter packages** for writing prompts
- **Theme blending** across multiple books
- **Mixed author combinations** for diverse perspectives

### ✅ Enhanced Navigation
- **Book construction** with complete structure
- **Page-by-page navigation** with links
- **Table of contents** access
- **Reading progress** tracking

### ✅ Statistics & Analytics
- **Comprehensive dashboard** with library stats
- **User reading metrics** and progress tracking
- **Genre distribution** analysis
- **Top authors** and book counts

---

## 🤖 Agent Integration Notes

**For AI Agents and Integrations:**
- Use `/api/shortcuts/search/{term}/simple` for structured search results
- Leverage `/api/shortcuts/stats/dashboard` for system monitoring
- Use `/api/shortcuts/serendipity/*` endpoints for creative content generation
- Check `/api/shortcuts/health` endpoint for system status monitoring

**Production Deployment:**
- **Single unified service** on port 5562
- **SSL/HTTPS**: Let's Encrypt certificates auto-renewed
- **Logging**: Production logs at `/logs/production_api.log`
- **Auto-restart**: Managed by system daemon

---

*🎯 This iOS Shortcuts API provides mobile-optimized access to 2,730 real books with serendipity features and creative content generation. Perfect for iOS Shortcuts, Data Jar, mobile workflows, and AI agents.*

**Last Updated**: July 23, 2025 | **API Version**: iOS Shortcuts API | **Designer**: Dr. Elena Rodriguez (IAV)