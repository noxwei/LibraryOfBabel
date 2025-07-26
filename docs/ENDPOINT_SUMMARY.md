# 🚀 LibraryOfBabel iOS Shortcuts API - Endpoint Summary

**Base URL**: `https://api.ashortstayinhell.com:5562/api/shortcuts/`  
**Version**: iOS Shortcuts API (mobile-first design)  
**Designer**: Dr. Elena Rodriguez (IAV) - Information Architecture Validator

## 📋 Quick Reference - All Available Endpoints

### 🔧 System
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | ❌ | API health status and stats |

### 📚 Books & Content
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/books/count` | GET | ✅ | Get total book count (2,730) |
| `/books/title-list` | GET | ✅ | Get list of all book titles |
| `/books/author-list` | GET | ✅ | Get list of all authors |
| `/books/{book_id}/summary` | GET | ✅ | Get specific book details |
| `/books/{book_id}/construct` | GET | ✅ | Get complete book structure |
| `/books/{book_id}/page/{num}` | GET | ✅ | Get specific page content |
| `/books/{book_id}/toc` | GET | ✅ | Get table of contents |

### 🎲 Random Content
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/random/title` | GET | ✅ | Get random book title |
| `/random/author` | GET | ✅ | Get random author name |
| `/random/citation` | GET | ✅ | Get random book citation |
| `/random/share-text` | GET | ✅ | Get random shareable text |

### 🔍 Search Functions
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/search/{term}/count` | GET | ✅ | Get count of matching books |
| `/search/{term}/has-results` | GET | ✅ | Check if search has results |
| `/search/{term}/titles` | GET | ✅ | Get titles of matching books |
| `/search/{term}/summary` | GET | ✅ | Get search summary |
| `/search/{term}/simple` | GET | ✅ | Get simplified search results |

### 📊 Statistics & Dashboard
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/stats/dashboard` | GET | ✅ | Get comprehensive library stats |
| `/user/reading-progress` | GET | ✅ | Get user reading metrics |

### 🎭 Serendipity Features
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/serendipity/random-passage` | GET | ✅ | Get random passage for inspiration |
| `/serendipity/story-starter` | GET | ✅ | Get complete story starter package |

### 🔗 Legacy V3 Compatibility
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v3/health` | GET | ❌ | V3 format health check |
| `/api/v3/search` | GET | ✅ | V3 format search endpoint |
| `/api/v3/books` | GET | ✅ | V3 format books listing |

## 🔑 Authentication

**Required for all endpoints except `/health` and `/api/v3/health`**

```bash
# Option 1: Query parameter (recommended for testing)
?api_key=***REMOVED***

# Option 2: Authorization header
Authorization: Bearer ***REMOVED***

# Option 3: X-API-Key header
X-API-Key: ***REMOVED***
```

## 🧠 Fuzzy Search Types

The new `/fuzzy-search` endpoint supports multiple search algorithms:

- **`semantic`**: Vector similarity search using 18,363 embeddings
- **`fuzzy`**: Text similarity using Levenshtein distance and token matching
- **`hybrid`**: Combined semantic + fuzzy + keyword search with weights
- **`keyword`**: Traditional PostgreSQL full-text search

## 📊 Current Data

- **📚 Books**: 2,730 total (verified production count)
- **📝 Chunks**: 79,054 total
- **👥 Authors**: 2,152 unique authors
- **⚡ Performance**: Mobile-optimized response times
- **📱 Optimized For**: iOS Shortcuts, Data Jar, Mobile Workflows

## 🆕 What's New

### ✅ iOS Shortcuts API
- Mobile-first design by Dr. Elena Rodriguez (IAV)
- Single-value responses perfect for iOS Shortcuts
- Data Jar integration ready
- Mobile workflows streamlined

### ✅ Serendipity Features
- **Random passage generation**: `/serendipity/random-passage`
- **Story starter packages**: `/serendipity/story-starter`
- **Creative inspiration**: Theme blending across books
- **Mixed author combinations**: Diverse perspectives

### ✅ Enhanced Navigation
- **Book construction**: Complete structure with navigation
- **Page-by-page reading**: With next/prev links
- **Table of contents**: Easy chapter navigation
- **Reading progress**: User metrics tracking

## 🚀 Quick Examples

```bash
# Health check
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/health"

# Get book count
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/count?api_key=***REMOVED***"

# Get random title
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/random/title?api_key=***REMOVED***"

# Search for books
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/search/philosophy/count?api_key=***REMOVED***"

# Get book details
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/books/1099/summary?api_key=***REMOVED***"

# Get serendipity inspiration
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/serendipity/random-passage?api_key=***REMOVED***"

# Get story starter
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/serendipity/story-starter?api_key=***REMOVED***"
```

---

**📖 For detailed documentation**: See [API-Reference-Unified.md](API-Reference-Unified.md)

**🎯 Ready for production use with enhanced search capabilities!**