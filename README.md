# LibraryOfBabel 📚

**Personal Knowledge Liberation System with Unified AI Architecture**

Transform your digital ebook collection into a searchable, AI-accessible research library with production-grade security, fuzzy search, and vector embeddings. Now featuring advanced semantic search capabilities and comprehensive project organization.

## 🎯 **What It Does**

LibraryOfBabel turns your EPUB collection into a powerful, unified search API with your entire library instantly accessible through secure endpoints. Perfect for AI agents, research tools, and knowledge discovery with advanced fuzzy search and vector embeddings.

### **✨ Core Features**
- 🔍 **Lightning-Fast Search**: Query across 5,160+ books in <200ms (performance optimized)
- 🏛️ **PostgreSQL-First**: Optimized database functions for maximum performance  
- 🧠 **AI-Powered**: Semantic search using advanced vector embeddings
- 📖 **Smart Chunking**: Configurable text granularity (500/1500/5000 chars)
- 🔐 **Production Security**: API key authentication + HTTPS + QA Security Agent
- 🤖 **AI-Ready**: Structured JSON responses for agent consumption
- 📱 **Universal Access**: Works with iOS Shortcuts, web apps, curl
- 🎯 **Flexible Limits**: Control results (1-10,000) for any use case
- 📚 **In-Book Search**: Search within specific books for focused research
- 🔗 **MCP Integration**: Connect Claude Code directly to your library
- 🗂️ **Professional Organization**: Clean, maintainable codebase with 18 essential directories

## 🚀 **Quick Start - 4 Commands**

```bash
# 1. Check if system is running
curl https://api.example.com:5562/health

# 2. Search your library (replace YOUR_API_KEY)
curl "https://api.example.com:5562/books?api_key=YOUR_API_KEY&search=consciousness&page_size=5"

# 3. 🔥 PostgreSQL-optimized search with limit control (1-10,000 results!)
curl "https://api.example.com:5562/search?api_key=YOUR_API_KEY&q=artificial%20intelligence&limit=100"

# 4. NEW: Search within a specific book
curl "https://api.example.com:5562/books/1099/search?api_key=YOUR_API_KEY&q=discourse&page_size=3"
```

**That's it. Four commands. Bookmark this page!** 📌

## 📊 **Current Statistics**

- **📚 Total Books**: 5,160 (massive expansion complete)
- **📝 Total Chunks**: 165,206+ (searchable segments with optimized indexing)
- **👥 Unique Authors**: 3,000+ authors (diverse collection)
- **⚡ Response Time**: Mobile-optimized for iOS Shortcuts (<200ms)
- **🔒 Security**: 100% API key protected with QA Security Agent
- **📈 Uptime**: 99.9%+ with auto-restart daemon
- **🎯 API Type**: iOS Shortcuts API (mobile-first design)
- **🗂️ Project Structure**: 18 essential directories (54% reduction from cleanup)
- **🔗 Architecture Team**: Dr. Elena Rodriguez (IAV) + DBA Team (Dr. Thompson, Dr. Park)
- **🏛️ Philosophy**: "Information architecture makes complex knowledge feel simple"

## 🔗 **iOS Shortcuts Production API**

**Base URL**: `https://api.ashortstayinhell.com:5562/api/shortcuts/`  
**Architecture**: iOS Shortcuts API (mobile-first design)  
**Designer**: Dr. Elena Rodriguez (IAV) - Information Architecture Validator

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
- `GET /books/count` - Get total book count (5,160)
- `GET /books/title-list` - List all book titles
- `GET /books/author-list` - List all authors
- `GET /books/{id}/summary` - Individual book details
- `GET /books/{id}/construct` - Complete book structure
- `GET /books/{id}/page/{num}` - Page-by-page reading
- `GET /search/{term}/count` - Count matching books
- `GET /search/{term}/simple` - Simplified search results
- `GET /serendipity/random-passage` - Creative inspiration
- `GET /serendipity/story-starter` - Story starter packages

### **🔥 NEW: iOS Shortcuts Optimization**
- **Single-value responses**: Perfect for iOS Shortcuts (no JSON parsing needed)
- **Simple arrays**: Easy for shortcuts loops
- **Pre-formatted text**: Ready for sharing/display
- **Boolean responses**: Perfect for if/then logic
- **Data Jar optimized**: Clean objects for persistence

### **Legacy V3 Compatibility**
- `GET /api/v3/health` - V3 format health check
- `GET /api/v3/search` - V3 format search endpoint
- `GET /api/v3/books` - V3 format books listing

## 🧠 **NEW: Advanced AI Search Features**

### **🔍 Fuzzy Search with Vector Embeddings**
Find content using semantic similarity and fuzzy text matching:

```bash
# Semantic search using AI vector embeddings
curl "https://api.example.com:5562/fuzzy-search?api_key=YOUR_KEY&q=artificial%20intelligence&type=semantic&limit=5"

# Fuzzy text matching (handles typos)
curl "https://api.example.com:5562/fuzzy-search?api_key=YOUR_KEY&q=philosphy&type=fuzzy&limit=3"

# Hybrid search (combines semantic + fuzzy + keyword)
curl "https://api.example.com:5562/fuzzy-search?api_key=YOUR_KEY&q=democracy&type=hybrid&limit=10"

# Custom weighted hybrid search
curl "https://api.example.com:5562/fuzzy-search?api_key=YOUR_KEY&q=consciousness&type=hybrid&semantic_weight=0.6&fuzzy_weight=0.3&keyword_weight=0.1"
```

### **📖 In-Book Search**
Focus your research within specific books:

```bash
# Search within a Foucault book
curl "https://api.example.com:5562/books/1099/search?api_key=YOUR_KEY&q=discourse&page_size=5"

# Search within any book by ID
curl "https://api.example.com:5562/books/611/search?api_key=YOUR_KEY&q=magic&page=1"
```

## 🔧 **Advanced Features**

### **🔍 Pagination System**
Navigate large datasets efficiently:
```bash
# Get page 1 with 10 books
curl "https://api.example.com:5562/books?api_key=YOUR_KEY&page=1&page_size=10"

# Navigate to specific pages with pagination
curl "https://api.example.com:5562/books?api_key=YOUR_KEY&page=200&page_size=5"
```

Every response includes navigation links: `next`, `prev`, `first`, `last`

### **🔗 MCP Integration (Claude Code)**
Connect Claude directly to your library for intelligent research:

**MCP Endpoints**:
- `GET /mcp/health` - Server health check
- `GET /mcp/tools` - Available tools
- `POST /mcp/call` - Execute tools

**Configure Claude Code**:
```json
{
  "mcpServers": {
    "library-of-babel": {
      "url": "https://api.example.com:5562/mcp",
      "env": {
        "LIBRARY_API_KEY": "YOUR_API_KEY"
      }
    }
  }
}
```

**Use with Claude**:
- *"What books about AI do I have?"*
- *"Give me insights on consciousness from my library"*
- *"What are my current library statistics?"*

**Available Tools**:
- `search_books` - Search across your collection
- `get_library_stats` - Real-time library statistics
- `semantic_search` - AI-powered concept search
- `get_book_content` - Full book content retrieval
- `get_topic_insights` - Comprehensive topic analysis

### **📖 Configurable Chunking**
Adjust text granularity for different use cases:
```bash
# Small chunks (500 chars) - detailed analysis
curl "https://api.example.com:5562/books/611/chunks?api_key=YOUR_KEY&chunk_level=small"

# Medium chunks (1500 chars) - balanced (default)
curl "https://api.example.com:5562/books/611/chunks?api_key=YOUR_KEY&chunk_level=medium"

# Large chunks (5000 chars) - overview
curl "https://api.example.com:5562/books/611/chunks?api_key=YOUR_KEY&chunk_level=large"
```

### **🎯 Traditional Search**
Filter and discover content:
```bash
# Search by author
curl "https://api.example.com:5562/books?api_key=YOUR_KEY&author=foucault"

# Search by genre
curl "https://api.example.com:5562/books?api_key=YOUR_KEY&genre=philosophy"

# Full-text search with semantic support
curl "https://api.example.com:5562/search?api_key=YOUR_KEY&q=machine%20learning&type=semantic"

# 🔥 NEW: Control result count with limit parameter
curl "https://api.example.com:5562/search?api_key=YOUR_KEY&q=philosophy&limit=1"     # Just 1 result
curl "https://api.example.com:5562/search?api_key=YOUR_KEY&q=philosophy&limit=100"   # 100 results  
curl "https://api.example.com:5562/search?api_key=YOUR_KEY&q=philosophy&limit=5000"  # 5000 results!
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
const API_KEY = 'YOUR_ACTUAL_API_KEY';
const BASE_URL = 'https://api.example.com:5562';

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
GET https://api.example.com:5562/fuzzy-search?api_key=YOUR_KEY&q=TEXT_INPUT&type=semantic&limit=5
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
- ✅ **PostgreSQL** with optimized indexes for your ebook catalog
- ✅ **Auto-restart daemon** ensures 99.9%+ uptime
- ✅ **Vector embeddings** for instant semantic similarity
- ✅ **Concurrent access** supports multiple users
- ✅ **Efficient pagination** handles large datasets

## 🏗️ **Project Architecture**

```
LibraryOfBabel Production System/
├── 📚 Core System (Essential Directories)
│   ├── .agents/                   # Active agent ecosystem (HR, DBA, Reddit Bibliophile)
│   ├── src/                       # Core application source (26 Python modules)
│   │   └── api/                   # Production APIs (3 essential endpoints)
│   ├── config/                    # System configuration & security
│   ├── database/                  # PostgreSQL schemas & optimization
│   └── ebooks/                    # 10GB library (5,160 books)
├── 🛠️ Development & Operations
│   ├── frontend/                  # Next.js application
│   ├── scripts/                   # Utility & automation (67 scripts)
│   ├── tests/                     # Test suites & validation
│   ├── tools/                     # System tools & utilities
│   ├── daemons/                   # Daemon control & state
│   └── ssl/                       # SSL certificate management
├── 📖 Documentation & Communication
│   ├── docs/                      # Current documentation (33 subdirectories)
│   ├── team/                      # Team communication
│   └── notifications/             # Agent notification system
├── 📊 Operational Data
│   ├── logs/                      # Current operational logs (66MB)
│   └── archive/                   # Organized historical data (21MB)
│       ├── 2025_Q3_cleanup/       # July 2025 cleanup efforts
│       ├── emergency_docs_consolidated/ # Critical documentation
│       ├── experimental_consolidated/   # Research & development
│       ├── historical_logs/            # Archived logging data
│       └── project_reports_consolidated/ # Project reporting
├── 🗄️ PostgreSQL Database
│   ├── 5,160 books                # Processed EPUB collection
│   ├── 165,206+ chunks            # Searchable segments
│   └── 3,000+ unique authors      # Author database
├── 🔐 Security & QA Layer
│   ├── QA Security Agent          # Vulnerability monitoring
│   ├── Centralized config         # Secure key management
│   ├── API key auth              # Multi-method support
│   ├── Rate limiting             # 60 req/min protection
│   └── HTTPS/SSL                 # Let's Encrypt
├── 👔 Agent & Team Integration
│   ├── Linda's HR System         # Team coordination
│   ├── DBA Team (3 specialists)  # Database management
│   ├── Reddit Bibliophile        # Content curation
│   └── QA integration            # Quality assurance
└── 🤖 AI Integration
    ├── Structured JSON           # Agent-friendly responses
    ├── Semantic search          # AI-powered discovery
    ├── MCP Server               # Claude Code integration
    └── Vector embeddings        # Advanced search capabilities
```

## 📖 **Documentation**

### **📋 API Reference**
- **[Unified API Reference](docs/API-Reference-Unified.md)** - Complete endpoint documentation
- **[Endpoint Summary](docs/ENDPOINT_SUMMARY.md)** - Quick reference guide
- **[Story Generation API](docs/STORY_GENERATION_API.md)** - Advanced AI-powered narrative creation
- **[Simple Usage Guide](docs/SIMPLE_USAGE_GUIDE.md)** - Getting started quickly

### **🔧 Configuration & Setup**
- **[Installation Guide](docs/Installation-Guide.md)** - Complete setup instructions  
- **[Centralized Config Guide](docs/CENTRALIZED_CONFIG_GUIDE.md)** - Configuration management
- **[MCP Extension Plan](docs/MCP_EXTENSION_PLAN.md)** - Claude Code integration roadmap

### **🔒 Security & Operations**
- **[Security Guide](docs/Security-Guide.md)** - Security best practices
- **[Production Deployment Checklist](docs/PRODUCTION-DEPLOYMENT-CHECKLIST.md)** - Deployment guide
- **[Service Management](docs/maintenance/SERVICE-MANAGEMENT.md)** - Operations manual

### **🏗️ Architecture & Development**
- **[Database Schema](docs/project_docs/DATABASE_SCHEMA.md)** - Database structure
- **[Frontend Architecture Plan](docs/technical/FRONTEND_ARCHITECTURE_PLAN.md)** - UI/UX design
- **[Organization Cleanup Complete](docs/project_docs/ORGANIZATION_CLEANUP_COMPLETE.md)** - Project structure

## 🎯 **Use Cases**

### **🤖 AI Research Agents with Semantic Search**
- Query entire entire library with semantic understanding
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
- Instant access to your reading history
- Rediscover forgotten insights with fuzzy search
- Build on previous research with semantic connections
- Accelerate learning with AI-powered discovery

### **🔗 Claude Code Integration (MCP)**
- Ask Claude questions about your library directly
- Get insights across your entire 5,160+ book collection
- Real-time library statistics and analytics
- Semantic search through natural conversation
- Cross-reference concepts across multiple books

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

**Result**: All performance targets exceeded for the collection! 🎉

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

**✅ FULLY OPERATIONAL WITH COMPREHENSIVE ORGANIZATION**

The LibraryOfBabel Unified API is production-ready and serving **your 5,160+ book collection** with enterprise-grade security, advanced AI search capabilities, MCP integration for Claude Code, and professional project organization. Perfect for researchers, developers, and AI agents seeking instant access to curated knowledge with semantic understanding.

### **🆕 Recent Enhancements**
- ✅ **Professional Organization**: 54% directory reduction (39→18 essential directories)
- ✅ **Archive Consolidation**: 5 organized archive categories with timestamp-based structure
- ✅ **API Consolidation**: Single unified endpoint (no more v2/v3 separation)
- ✅ **Fuzzy Search**: AI-powered semantic search with vector embeddings
- ✅ **In-Book Search**: Focus research within specific books
- ✅ **MCP Integration**: Claude Code remote server for direct AI access
- ✅ **Centralized Configuration**: Secure, automated configuration management
- ✅ **QA Security Agent**: Enhanced security monitoring and protection
- ✅ **Collection Growth**: Massive expansion to 5,160 books
- 🆕 **Story Generation Suite**: Advanced AI-powered narrative creation system
- 🆕 **Lexi's Template Engine**: Seed-based reproducible story generation
- 🆕 **RAG Integration**: Ollama-powered creative writing assistance

**🔗 Ready to explore?** Start with the [Unified API Reference](docs/API-Reference-Unified.md)

---

*Liberating knowledge through intelligent automation, AI-powered search, and collaborative development.*

**Status**: Production-Ready ✅ | **AI Features**: Operational ✅ | **Security**: QA Enhanced ✅ | **Team**: Integrated ✅ | **MCP**: Claude Ready ✅

**Collection**: 5,160+ Books 📚 | **Search**: AI-Powered 🧠 | **Architecture**: Organized 🎯 | **Integration**: MCP Enabled 🔗
