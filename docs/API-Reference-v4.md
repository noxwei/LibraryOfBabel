# 📚 LibraryOfBabel API v4.0 - Official Reference

**🚀 MAJOR UPDATE**: Forward slash navigation **ELIMINATED** - Now using modern query parameters!

**Base URL**: `https://api.ashortstayinhell.com:5562`  
**Architecture**: Modern RESTful Query Parameter Navigation  
**Version**: v4.0 Query Parameter Edition  
**Status**: ✅ **PRODUCTION LIVE**

---

## 🎯 **Migration Summary - What Changed**

### ❌ **ELIMINATED (v3.0 and earlier)**
```bash
# OLD forward slash structure - NO LONGER WORKS
/api/shortcuts/books/288/summary
/api/shortcuts/search/philosophy/count
/api/shortcuts/books/count
```

### ✅ **NEW STRUCTURE (v4.0)**
```bash
# NEW query parameter structure - LIVE NOW
/api/shortcuts/books?id=288&action=summary
/api/shortcuts/search?term=philosophy&action=count
/api/shortcuts/stats?metric=book_count
```

**User Request**: _"I don't like the forward slash as a way of url navigation"_ ✅ **SOLVED**

---

## 🏗️ **Dual API Architecture**

### 📱 **iOS Shortcuts API v2.0** - `/api/shortcuts/`
- **Optimized for**: iOS Shortcuts, Data Jar, Mobile Workflows
- **Response Style**: Simple values, single responses, boolean-compatible
- **Best Use**: Quick mobile access, Siri integration

### 🚀 **Production API v4.0** - `/api/v4/`
- **Optimized for**: Full applications, complex queries, detailed analysis
- **Response Style**: Rich metadata, comprehensive data, flexible search
- **Best Use**: Web applications, research tools, data analysis

---

## 📚 **Books API - Query Parameter Examples**

### iOS Shortcuts Books (`/api/shortcuts/books`)
```bash
# Book summary
GET /api/shortcuts/books?id=288&action=summary&api_key=YOUR_KEY

# Book structure  
GET /api/shortcuts/books?id=288&action=construct&api_key=YOUR_KEY

# Table of contents
GET /api/shortcuts/books?id=288&action=toc&api_key=YOUR_KEY

# Specific page
GET /api/shortcuts/books?id=288&page=1&api_key=YOUR_KEY

# Random page
GET /api/shortcuts/books?id=288&page=random&api_key=YOUR_KEY
```

### Production Books (`/api/v4/books`)
```bash
# List all books
GET /api/v4/books?action=list&api_key=YOUR_KEY

# Detailed book info with structure
GET /api/v4/books?id=288&action=details&api_key=YOUR_KEY

# Chapter content
GET /api/v4/books?id=288&action=content&chapter=1&limit=5&api_key=YOUR_KEY

# Search within book
GET /api/v4/books?id=1099&action=search&q=discourse&limit=3&api_key=YOUR_KEY
```

---

## 🔍 **Search API - Query Parameter Examples**

### iOS Shortcuts Search (`/api/shortcuts/search`)
```bash
# Search count (returns single number)
GET /api/shortcuts/search?term=philosophy&action=count&api_key=YOUR_KEY

# Enhanced search results
GET /api/shortcuts/search?term=philosophy&format=enhanced&include_metadata=true&api_key=YOUR_KEY

# Titles only
GET /api/shortcuts/search?term=democracy&fields=title&limit=10&api_key=YOUR_KEY

# Authors only  
GET /api/shortcuts/search?term=Gibson&fields=author&limit=5&api_key=YOUR_KEY
```

### Production Search (`/api/v4/search`)
```bash
# Content search with highlighting
GET /api/v4/search?q=philosophy&type=content&limit=5&api_key=YOUR_KEY

# Author-based search
GET /api/v4/search?q=Gibson&type=author&limit=3&api_key=YOUR_KEY

# Title search
GET /api/v4/search?q=Democracy&type=title&limit=3&api_key=YOUR_KEY

# Cross-reference search
GET /api/v4/search?q=cybernetic&type=cross_reference&limit=5&api_key=YOUR_KEY

# Search count (production)
GET /api/v4/search?term=artificial&action=count&api_key=YOUR_KEY
```

---

## 📋 **Lists & Random - Query Parameter Examples**

### Lists (`/api/shortcuts/lists`)
```bash
# All book titles (limited)
GET /api/shortcuts/lists?type=titles&limit=100&api_key=YOUR_KEY

# All book titles (maximum 500)
GET /api/shortcuts/lists?type=titles&limit=500&api_key=YOUR_KEY

# All authors
GET /api/shortcuts/lists?type=authors&limit=500&api_key=YOUR_KEY
```

### Random Content (`/api/shortcuts/random`)
```bash
# Random title (returns string)
GET /api/shortcuts/random?type=title&api_key=YOUR_KEY

# Random author (returns string)
GET /api/shortcuts/random?type=author&api_key=YOUR_KEY

# Random book with metadata
GET /api/shortcuts/random?type=book&include_metadata=true&api_key=YOUR_KEY

# Random citation
GET /api/shortcuts/random?type=citation&api_key=YOUR_KEY
```

---

## 🎭 **Serendipity Features - Query Parameter Examples**

### Serendipity (`/api/shortcuts/serendipity`)
```bash
# Random quote
GET /api/shortcuts/serendipity?action=quote&limit=3&api_key=YOUR_KEY

# Random passage
GET /api/shortcuts/serendipity?action=passage&length=medium&api_key=YOUR_KEY

# Mixed authors blend
GET /api/shortcuts/serendipity?action=blend&style=mixed_authors&api_key=YOUR_KEY

# Story starter
GET /api/shortcuts/serendipity?action=story&inspiration=random&api_key=YOUR_KEY

# Theme-based content
GET /api/shortcuts/serendipity?action=theme&topic=philosophy&api_key=YOUR_KEY
```

---

## 📊 **Statistics & Health - Query Parameter Examples**

### Statistics
```bash
# Simple book count (returns number)
GET /api/shortcuts/stats?metric=book_count&api_key=YOUR_KEY

# Full statistics (production)
GET /api/v4/stats?api_key=YOUR_KEY
```

### Health Checks
```bash
# iOS Shortcuts health (no auth required)
GET /api/shortcuts/health

# Production health (no auth required)
GET /api/v4/health

# API info
GET /api/v4/info
```

---

## 🤖 **RedditBibliophile Optimized Workflows**

### Research Scenarios (All using query parameters)
```bash
# 1. Philosophy Research
GET /api/v4/search?q=existentialism&type=content&limit=5&api_key=YOUR_KEY

# 2. Author Deep Dive
GET /api/v4/search?q=Foucault&type=author&limit=10&api_key=YOUR_KEY

# 3. Book Recommendations
GET /api/v4/search?q=artificial%20intelligence&type=content&limit=8&api_key=YOUR_KEY

# 4. Collection Statistics
GET /api/v4/stats?api_key=YOUR_KEY

# 5. Book Analysis
GET /api/v4/books?id=1373&action=details&api_key=YOUR_KEY

# 6. Chapter Access
GET /api/v4/books?id=1373&action=content&chapter=2&limit=10&api_key=YOUR_KEY

# 7. Cross-Book Research
GET /api/v4/search?q=democracy&type=cross_reference&limit=10&api_key=YOUR_KEY

# 8. iOS Quick Count
GET /api/shortcuts/search?term=philosophy&action=count&api_key=YOUR_KEY
```

---

## 🔐 **Authentication Methods**

### API Key: `***REMOVED***`

**Three Authentication Options:**

1. **Query Parameter** (Recommended)
```bash
GET /api/shortcuts/books?id=288&action=summary&api_key=***REMOVED***
```

2. **Header Authentication**
```bash
curl -H "X-API-Key: ***REMOVED***" \
  https://api.ashortstayinhell.com:5562/api/shortcuts/books?id=288&action=summary
```

3. **Bearer Token**
```bash
curl -H "Authorization: Bearer ***REMOVED***" \
  https://api.ashortstayinhell.com:5562/api/shortcuts/books?id=288&action=summary
```

---

## 🎯 **Parameter Reference**

### Common Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `id` | integer | Book ID | `?id=288` |
| `action` | string | Action to perform | `?action=summary` |
| `term` | string | Search term | `?term=philosophy` |
| `type` | string | Search type | `?type=content` |
| `limit` | integer | Result limit | `?limit=10` |
| `page` | integer/string | Page number or 'random' | `?page=1` |
| `format` | string | Response format | `?format=enhanced` |
| `fields` | string | Comma-separated fields | `?fields=title,author` |

### Special Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `include_metadata` | boolean | Include extra data | `?include_metadata=true` |
| `chapter` | integer | Chapter number | `?chapter=1` |
| `length` | string | Content length | `?length=medium` |
| `topic` | string | Theme topic | `?topic=philosophy` |
| `metric` | string | Statistics metric | `?metric=book_count` |

---

## ✅ **Response Formats**

### iOS Shortcuts Optimized
```json
// Simple count (perfect for variables)
2930

// Simple title (perfect for text)
"The Elegant Universe"

// Simple array (perfect for loops)
["Title1", "Title2", "Title3"]

// Boolean compatible (perfect for conditions)
0  // No results
15 // Has results
```

### Production API Rich Data
```json
{
  "success": true,
  "data": {
    "book": {
      "book_id": 288,
      "title": "Dying Of Whiteness",
      "author": "Jonathan M. Metzl",
      "word_count": 111794,
      "publication_year": 2019
    },
    "structure": {
      "chapters": [...],
      "total_chapters": 33
    }
  }
}
```

---

## 🚀 **Version History**

### v4.0 (July 26, 2025) - **CURRENT**
- ✅ **ELIMINATED**: Forward slash navigation completely
- ✅ **IMPLEMENTED**: Query parameter architecture
- ✅ **ENHANCED**: iOS Shortcuts compatibility
- ✅ **OPTIMIZED**: RedditBibliophile scenarios
- ✅ **MODERNIZED**: RESTful design principles

### v3.0 and earlier - **DEPRECATED**
- ❌ Forward slash navigation (eliminated)
- ❌ Path-based parameters (replaced)

---

## 📱 **iOS Shortcuts Integration Guide**

### Getting Started
1. **Health Check**: Test `/api/shortcuts/health` (no auth needed)
2. **Get Count**: `/api/shortcuts/stats?metric=book_count&api_key=YOUR_KEY`
3. **Search**: `/api/shortcuts/search?term=philosophy&action=count&api_key=YOUR_KEY`
4. **Get Book**: `/api/shortcuts/books?id=288&action=summary&api_key=YOUR_KEY`

### Best Practices
- Use simple endpoints for variables: `/search?term=X&action=count`
- Use enhanced endpoints for rich data: `/search?term=X&format=enhanced`
- Cache book IDs for repeated access
- Use Data Jar for persistence of book metadata

---

## 🔧 **Troubleshooting**

### Common Issues

**Q: Getting 404 errors?**  
A: Check that you're using query parameters, not forward slashes:
- ❌ `/books/288/summary`
- ✅ `/books?id=288&action=summary`

**Q: Slow search responses?**  
A: Database optimization in progress. Use specific searches when possible.

---

**Documentation Version**: v4.0  
**API Status**: ✅ **PRODUCTION LIVE**  
**Last Updated**: July 26, 2025  
**Architecture**: 100% Query Parameter Based