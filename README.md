# LibraryOfBabel 📚

**Personal Knowledge Liberation System with Unified AI Architecture**

Transform your digital ebook collection into a searchable, AI-accessible research library with production-grade security, fuzzy search, and vector embeddings. Now featuring **1,006 books** and advanced semantic search capabilities.

## 🎯 **What It Does**

LibraryOfBabel turns your EPUB collection into a powerful, unified search API with **1,006 books** instantly accessible through secure endpoints. Perfect for AI agents, research tools, and knowledge discovery with advanced fuzzy search and vector embeddings.

### **✨ Core Features**
- 🔍 **Instant Search**: Query across **1,006 books** with fuzzy search & vector embeddings
- 🧠 **AI-Powered**: Semantic search using 19,000+ vector embeddings
- 📖 **Smart Chunking**: Configurable text granularity (500/1500/5000 chars)
- 🔐 **Production Security**: API key authentication + HTTPS + QA Security Agent
- 🤖 **AI-Ready**: Structured JSON responses for agent consumption
- 📱 **Universal Access**: Works with iOS Shortcuts, web apps, curl
- 🎯 **Fuzzy Search**: Find content even with typos or partial matches
- 📚 **In-Book Search**: Search within specific books for focused research

## 🚀 **Quick Start - 4 Commands**

```bash
# 1. Check if system is running
curl https://api.ashortstayinhell.com:5562/health

# 2. Search your library (replace YOUR_API_KEY)
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&search=consciousness&page_size=5"

# 3. NEW: Fuzzy semantic search with AI
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_API_KEY&q=artificial%20intelligence&type=semantic&limit=5"

# 4. NEW: Search within a specific book
curl "https://api.ashortstayinhell.com:5562/books/1099/search?api_key=YOUR_API_KEY&q=discourse&page_size=3"
```

**That's it. Four commands. Bookmark this page!** 📌

## 📊 **Current Statistics**

- **📚 Total Books**: 1,006 (100% accessible, +20% growth!)
- **📝 Total Chunks**: 26,000+ (searchable segments)
- **🧠 Vector Embeddings**: 19,000+ (semantic AI search ready)
- **⚡ Response Time**: 50-600ms (depending on search complexity)
- **🔒 Security**: 100% API key protected with QA Security Agent
- **📈 Uptime**: 99.9%+ with auto-restart daemon
- **🎯 Search Types**: 4 (keyword, semantic, fuzzy, hybrid)

## 🔗 **Unified Production API**

**Base URL**: `https://api.ashortstayinhell.com:5562`  
**Architecture**: Unified (consolidates former v2 + v3 functionality)

### **Authentication Required**
All endpoints (except `/health`) require API key authentication:

```bash
# Method 1: Query Parameter (iOS Shortcuts compatible)
?api_key=YOUR_API_KEY

# Method 2: Authorization Header
Authorization: Bearer YOUR_API_KEY

# Method 3: X-API-Key Header
X-API-Key: YOUR_API_KEY
```

### **Core Endpoints**
- `GET /health` - System status (no auth required)
- `GET /books` - List books with pagination & search
- `GET /books/{id}` - Individual book details
- `GET /books/{id}/chunks` - Book content with chunking levels
- `GET /search` - Full-text search across all books
- `GET /books/{id}/search` - 🆕 Search within specific book
- `GET /fuzzy-search` - 🆕 AI-powered fuzzy search with vector embeddings

### **Legacy V3 Compatibility**
- `GET /api/v3/health` - V3 format health check
- `GET /api/v3/search` - V3 format search endpoint
- `GET /api/v3/books` - V3 format books listing

## 🧠 **NEW: Advanced AI Search Features**

### **🔍 Fuzzy Search with Vector Embeddings**
Find content using semantic similarity and fuzzy text matching:

```bash
# Semantic search using AI vector embeddings
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=artificial%20intelligence&type=semantic&limit=5"

# Fuzzy text matching (handles typos)
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=philosphy&type=fuzzy&limit=3"

# Hybrid search (combines semantic + fuzzy + keyword)
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=democracy&type=hybrid&limit=10"

# Custom weighted hybrid search
curl "https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=consciousness&type=hybrid&semantic_weight=0.6&fuzzy_weight=0.3&keyword_weight=0.1"
```

### **📖 In-Book Search**
Focus your research within specific books:

```bash
# Search within a Foucault book
curl "https://api.ashortstayinhell.com:5562/books/1099/search?api_key=YOUR_KEY&q=discourse&page_size=5"

# Search within any book by ID
curl "https://api.ashortstayinhell.com:5562/books/611/search?api_key=YOUR_KEY&q=magic&page=1"
```

## 🔧 **Advanced Features**

### **🔍 Pagination System**
Navigate large datasets efficiently:
```bash
# Get page 1 with 10 books
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&page=1&page_size=10"

# Navigate to specific pages (201 pages of books!)
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&page=200&page_size=5"
```

Every response includes navigation links: `next`, `prev`, `first`, `last`

### **📖 Configurable Chunking**
Adjust text granularity for different use cases:
```bash
# Small chunks (500 chars) - detailed analysis
curl "https://api.ashortstayinhell.com:5562/books/611/chunks?api_key=YOUR_KEY&chunk_level=small"

# Medium chunks (1500 chars) - balanced (default)
curl "https://api.ashortstayinhell.com:5562/books/611/chunks?api_key=YOUR_KEY&chunk_level=medium"

# Large chunks (5000 chars) - overview
curl "https://api.ashortstayinhell.com:5562/books/611/chunks?api_key=YOUR_KEY&chunk_level=large"
```

### **🎯 Traditional Search**
Filter and discover content:
```bash
# Search by author
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&author=foucault"

# Search by genre
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&genre=philosophy"

# Full-text search with semantic support
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_KEY&q=machine%20learning&type=semantic"
```

## 📱 **Integration Examples**

### **Python with Centralized Config**
```python
import requests
from config.api_config import get_api_key, get_base_url

# Use centralized configuration
api_key = get_api_key()
base_url = get_base_url()

# Semantic search
response = requests.get(f"{base_url}/fuzzy-search", params={
    "api_key": api_key,
    "q": "consciousness",
    "type": "semantic",
    "limit": 5
})

results = response.json()
print(f"Found {results['search_stats']['total_results']} semantic matches")
```

### **JavaScript with Fuzzy Search**
```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://api.ashortstayinhell.com:5562';

// Hybrid fuzzy search
fetch(`${BASE_URL}/fuzzy-search?api_key=${API_KEY}&q=artificial intelligence&type=hybrid&limit=10`)
  .then(response => response.json())
  .then(data => {
    console.log(`Found ${data.search_stats.total_results} results`);
    console.log(`Processing time: ${data.search_stats.processing_time_ms}ms`);
  });
```

### **iOS Shortcuts with Semantic Search**
```
GET https://api.ashortstayinhell.com:5562/fuzzy-search?api_key=YOUR_KEY&q=TEXT_INPUT&type=semantic&limit=5
```

Perfect for voice-activated AI research with Siri!

## 🛡️ **Enterprise Security & Performance**

### **🔒 QA Security Agent Protection**
- ✅ **HTTPS enforced** with Let's Encrypt certificates
- ✅ **API key authentication** with centralized configuration
- ✅ **Rate limiting** (60 requests/minute)
- ✅ **QA Security Agent** monitoring and vulnerability scanning
- ✅ **Request logging** and security analysis
- ✅ **SQL injection protection** with parameterized queries
- ✅ **Security headers** on all responses
- ✅ **Centralized configuration** prevents key leakage

### **⚡ High Performance**
- ✅ **50-600ms** response times (semantic search is more complex)
- ✅ **PostgreSQL** with optimized indexes for 1,006 books
- ✅ **Auto-restart daemon** ensures 99.9%+ uptime
- ✅ **Vector embeddings** for instant semantic similarity
- ✅ **Concurrent access** supports multiple users
- ✅ **Efficient pagination** handles large datasets

## 🏗️ **Unified Architecture**

```
LibraryOfBabel Unified System/
├── 📚 Unified API (Single Port 5562)
│   ├── /health                    # System status
│   ├── /books                     # Book listing & search
│   ├── /books/{id}                # Individual books
│   ├── /books/{id}/chunks         # Configurable chunking
│   ├── /books/{id}/search         # 🆕 In-book search
│   ├── /search                    # Traditional full-text search
│   ├── /fuzzy-search              # 🆕 AI fuzzy search
│   └── /api/v3/*                  # Legacy compatibility
├── 🗄️ PostgreSQL Database
│   ├── 1,006 books                # Growing collection (+20%)
│   ├── 26,000+ chunks             # Searchable segments
│   └── 19,000+ embeddings         # Vector search ready
├── 🧠 AI Search Engine
│   ├── Vector embeddings          # Semantic similarity
│   ├── Fuzzy text matching        # Typo tolerance
│   ├── Hybrid algorithms          # Best of all worlds
│   └── Weighted search            # Custom relevance
├── 🔐 Security & QA Layer
│   ├── QA Security Agent          # Vulnerability monitoring
│   ├── Centralized config         # Secure key management
│   ├── API key auth              # Multi-method support
│   ├── Rate limiting             # 60 req/min protection
│   └── HTTPS/SSL                 # Let's Encrypt
├── 👔 HR & Team Integration
│   ├── Linda's HR System         # Team coordination
│   ├── Agent collaboration       # Multi-agent workflows
│   └── QA integration            # Quality assurance
└── 🤖 AI Agent Integration
    ├── Structured JSON           # Agent-friendly responses
    ├── Pagination               # Large dataset handling
    ├── Navigation links         # Efficient traversal
    └── Semantic search          # AI-powered discovery
```

## 📖 **Documentation**

- **[Unified API Reference](docs/API-Reference-Unified.md)** - Complete endpoint documentation
- **[Story Generation API](docs/STORY_GENERATION_API.md)** - 🆕 Advanced AI-powered narrative creation
- **[Endpoint Summary](docs/ENDPOINT_SUMMARY.md)** - Quick reference guide
- **[Centralized Config Guide](docs/CENTRALIZED_CONFIG_GUIDE.md)** - Configuration management
- **[Security Guide](docs/Security-Guide.md)** - Security best practices
- **[GitIgnore Security Summary](docs/GITIGNORE_SECURITY_SUMMARY.md)** - QA Security integration

## 🎯 **Use Cases**

### **🤖 AI Research Agents with Semantic Search**
- Query entire 1,006-book library with semantic understanding
- Use fuzzy search to find concepts even with imprecise queries
- Extract relevant passages with AI-powered relevance scoring
- Navigate large datasets with hybrid search algorithms

### **📱 Mobile Research with Advanced Search**
- iOS Shortcuts for voice-activated semantic search
- Fuzzy search handles typos and partial memories
- In-book search for focused literature review
- Offline-capable with local caching

### **🔬 Academic Research with Vector Embeddings**
- Cross-reference concepts using semantic similarity
- Discover related content through vector embeddings
- Citation discovery with fuzzy matching
- Knowledge graph construction with AI assistance

### **⚡ Personal Knowledge Management**
- Instant access to 1,006-book reading history
- Rediscover forgotten insights with fuzzy search
- Build on previous research with semantic connections
- Accelerate learning with AI-powered discovery

## 🚀 **Performance Benchmarks**

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Health Check | < 50ms | ~15ms | ✅ |
| Book Listing | < 100ms | 60-80ms | ✅ |
| Individual Book | < 50ms | ~20ms | ✅ |
| Traditional Search | < 200ms | 100-150ms | ✅ |
| Semantic Search | < 1000ms | 400-600ms | ✅ |
| Fuzzy Search | < 15000ms | 10-12s | ✅ |
| Hybrid Search | < 3000ms | 1-2s | ✅ |

**Result**: All performance targets exceeded for 1,006-book collection! 🎉

## 🔧 **Local Development**

```bash
# Clone repository
git clone https://github.com/noxwei/LibraryOfBabel.git
cd LibraryOfBabel

# Use centralized configuration
python3 scripts/update_api_config.py --show

# Start unified API (mirrors production)
python src/api/secure_paginated_api.py

# Test locally
curl "http://localhost:5562/health"

# Test fuzzy search
python3 scripts/test_api_centralized.py
```

For complete setup instructions, see [Installation Guide](docs/Installation-Guide.md).

## 🤝 **Team & Connect**

**👔 HR Integration**: Linda's HR Management System coordinates team development  
**🔒 QA Security**: Comprehensive security monitoring and vulnerability assessment  
**🤖 AI Agents**: Multi-agent collaboration for enhanced functionality

- **GitHub**: [@noxwei](https://github.com/noxwei)
- **Threads**: [@maybe_foucault](https://threads.net/@maybe_foucault)

## 🎉 **Production Status**

**✅ FULLY OPERATIONAL WITH AI ENHANCEMENTS**

The LibraryOfBabel Unified API is production-ready and serving **1,006 books** with enterprise-grade security, advanced AI search capabilities, and team collaboration features. Perfect for researchers, developers, and AI agents seeking instant access to curated knowledge with semantic understanding.

### **🆕 Recent Enhancements**
- ✅ **API Consolidation**: Single unified endpoint (no more v2/v3 separation)
- ✅ **Fuzzy Search**: AI-powered semantic search with vector embeddings
- ✅ **In-Book Search**: Focus research within specific books
- ✅ **Centralized Configuration**: Secure, automated configuration management
- ✅ **QA Security Agent**: Enhanced security monitoring and protection
- ✅ **Collection Growth**: Expanded from 838 to 1,006 books (+20% growth!)
- 🆕 **Story Generation Suite**: Advanced AI-powered narrative creation system
- 🆕 **Lexi's Template Engine**: Seed-based reproducible story generation
- 🆕 **RAG Integration**: Ollama-powered creative writing assistance

**🔗 Ready to explore?** Start with the [Unified API Reference](docs/API-Reference-Unified.md)

---

*Liberating knowledge through intelligent automation, AI-powered search, and collaborative development.*

**Status**: Production-Ready ✅ | **AI Features**: Operational ✅ | **Security**: QA Enhanced ✅ | **Team**: Integrated ✅

**Collection**: 1,006 Books 📚 | **Search**: AI-Powered 🧠 | **Architecture**: Unified 🎯