# 🚀 LibraryOfBabel Unified API - Endpoint Summary

**Base URL**: `https://api.ashortstayinhell.com:5562`  
**Version**: Unified (consolidates former v2 + v3)

## 📋 Quick Reference - All Available Endpoints

### 🔧 System
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | ❌ | API health status and stats |

### 📚 Books & Content
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/books` | GET | ✅ | List all books with pagination |
| `/books/{book_id}` | GET | ✅ | Get specific book details |
| `/books/{book_id}/chunks` | GET | ✅ | Get book chunks with chunking levels |
| `/chunks/{chunk_id}` | GET | ✅ | Get full chunk content |

### 🔍 Search (Traditional)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/search` | GET | ✅ | Search across all books (keyword/semantic) |
| `/books/{book_id}/search` | GET | ✅ | 🆕 Search within specific book |

### 🧠 Fuzzy Search (NEW)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/fuzzy-search` | GET | ✅ | 🆕 Advanced fuzzy search with vector embeddings |

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
?api_key=YOUR_API_KEY

# Option 2: Authorization header
Authorization: Bearer YOUR_API_KEY

# Option 3: X-API-Key header
X-API-Key: YOUR_API_KEY
```

## 🧠 Fuzzy Search Types

The new `/fuzzy-search` endpoint supports multiple search algorithms:

- **`semantic`**: Vector similarity search using 18,363 embeddings
- **`fuzzy`**: Text similarity using Levenshtein distance and token matching
- **`hybrid`**: Combined semantic + fuzzy + keyword search with weights
- **`keyword`**: Traditional PostgreSQL full-text search

## 📊 Current Data

- **📚 Books**: 838 total
- **📝 Chunks**: 25,067 total
- **🧠 Embeddings**: 18,363 vector embeddings
- **⚡ Performance**: 50-600ms response times

## 🆕 What's New

### ✅ Unified API
- Single endpoint (port 5562) instead of separate v2/v3
- All functionality consolidated
- Backwards compatibility maintained

### ✅ New Search Features
- **In-book search**: `/books/{book_id}/search`
- **Fuzzy search**: `/fuzzy-search` with multiple algorithms
- **Vector embeddings**: Semantic similarity search
- **Hybrid search**: Weighted combination of multiple algorithms

### ✅ Enhanced Capabilities
- Configurable chunking levels (small/medium/large)
- Custom search weights in hybrid mode
- Performance optimizations
- Comprehensive error handling

## 🚀 Quick Examples

```bash
# Health check
curl "https://api.ashortstayinhell.com:5562/health"

# List books
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&page_size=5"

# Traditional search
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_KEY&q=Foucault"

# NEW: In-book search
curl "https://api.ashortstayinhell.com:5562/books/1099/search?api_key=YOUR_KEY&q=discourse"

# NEW: Semantic fuzzy search
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=artificial%20intelligence&type=semantic&limit=5"

# NEW: Hybrid search with custom weights
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=democracy&type=hybrid&semantic_weight=0.6&fuzzy_weight=0.3&keyword_weight=0.1"
```

---

**📖 For detailed documentation**: See [API-Reference-Unified.md](API-Reference-Unified.md)

**🎯 Ready for production use with enhanced search capabilities!**