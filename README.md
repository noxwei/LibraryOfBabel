# LibraryOfBabel 📚

**Personal Knowledge Liberation System**

Transform your digital ebook collection into a searchable, AI-accessible research library with production-grade security and performance.

## 🎯 **What It Does**

LibraryOfBabel turns your EPUB collection into a powerful, searchable API with **838 books** instantly accessible through secure endpoints. Perfect for AI agents, research tools, and knowledge discovery.

### **✨ Core Features**
- 🔍 **Instant Search**: Query across **838 books** in under 30ms
- 📖 **Smart Chunking**: Configurable text granularity (500/1500/5000 chars)
- 🔐 **Production Security**: API key authentication + HTTPS
- 🤖 **AI-Ready**: Structured JSON responses for agent consumption
- 📱 **Universal Access**: Works with iOS Shortcuts, web apps, curl

## 🚀 **Quick Start - 4 Commands**

```bash
# 1. Check if system is running
curl https://api.ashortstayinhell.com:5562/health

# 2. Search your library (replace YOUR_API_KEY)
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_API_KEY&search=consciousness&page_size=5"

# 3. Get book details
curl "https://api.ashortstayinhell.com:5562/books/611?api_key=YOUR_API_KEY"

# 4. Search across all content
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_API_KEY&q=artificial%20intelligence"
```

**That's it. Four commands. Bookmark this page!** 📌

## 📊 **Current Statistics**

- **📚 Total Books**: 838 (100% accessible)
- **📝 Total Chunks**: 25,067 (searchable segments)
- **🧠 Total Embeddings**: 18,363 (vector search ready)
- **⚡ Response Time**: 12-30ms average
- **🔒 Security**: 100% API key protected
- **📈 Uptime**: 99.9%+ with auto-restart daemon

## 🔗 **Production API**

**Base URL**: `https://api.ashortstayinhell.com:5562`

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
- `GET /api-docs` - Interactive API documentation

## 🔧 **Advanced Features**

### **🔍 Pagination System**
Navigate large datasets efficiently:
```bash
# Get page 1 with 10 books
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&page=1&page_size=10"

# Navigate to specific pages
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&page=168&page_size=5"
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

### **🎯 Advanced Search**
Filter and discover content:
```bash
# Search by author
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&author=Rowling"

# Search by genre
curl "https://api.ashortstayinhell.com:5562/books?api_key=YOUR_KEY&genre=philosophy"

# Full-text search
curl "https://api.ashortstayinhell.com:5562/search?api_key=YOUR_KEY&q=machine%20learning"
```

## 📱 **Integration Examples**

### **Python**
```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://api.ashortstayinhell.com:5562"

# Search books
response = requests.get(f"{BASE_URL}/search", params={
    "api_key": API_KEY,
    "q": "consciousness"
})

results = response.json()
print(f"Found {results['pagination']['total_items']} results")
```

### **JavaScript**
```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://api.ashortstayinhell.com:5562';

// Get all books
fetch(`${BASE_URL}/books?api_key=${API_KEY}&page_size=20`)
  .then(response => response.json())
  .then(data => console.log(`${data.pagination.total_items} books available`));
```

### **iOS Shortcuts**
```
GET https://api.ashortstayinhell.com:5562/search?api_key=YOUR_KEY&q=TEXT_INPUT
```

Perfect for voice-activated research with Siri!

## 🛡️ **Security & Performance**

### **Enterprise-Grade Security**
- ✅ **HTTPS enforced** with Let's Encrypt certificates
- ✅ **API key authentication** on all data endpoints
- ✅ **Rate limiting** (60 requests/minute)
- ✅ **Request logging** and monitoring
- ✅ **SQL injection protection**
- ✅ **Security headers** on all responses

### **High Performance**
- ✅ **12-30ms** average response times
- ✅ **PostgreSQL** with optimized indexes
- ✅ **Auto-restart daemon** ensures 99.9%+ uptime
- ✅ **Concurrent access** supports multiple users
- ✅ **Efficient pagination** handles large datasets

## 🏗️ **Architecture**

```
LibraryOfBabel/
├── 📚 Secure Paginated API (Production)
│   ├── /health              # System status
│   ├── /books              # Book listing & search
│   ├── /books/{id}         # Individual books
│   ├── /books/{id}/chunks  # Configurable chunking
│   ├── /search             # Full-text search
│   └── /api-docs           # Documentation
├── 🗄️ PostgreSQL Database
│   ├── 838 books           # Complete collection
│   ├── 25,067 chunks       # Searchable segments
│   └── 18,363 embeddings   # Vector search ready
├── 🔐 Security Layer
│   ├── API key auth        # Multi-method support
│   ├── Rate limiting       # 60 req/min
│   └── HTTPS/SSL           # Let's Encrypt
└── 🤖 AI Agent Integration
    ├── Structured JSON     # Agent-friendly responses
    ├── Pagination          # Large dataset handling
    └── Navigation links    # Efficient traversal
```

## 📖 **Documentation**

- **[Complete API Reference](docs/API-Reference.md)** - Full endpoint documentation
- **[Simple Usage Guide](docs/SIMPLE_USAGE_GUIDE.md)** - Quick setup manual
- **[Installation Guide](docs/Installation-Guide.md)** - Deployment instructions
- **[Security Guide](docs/Security-Guide.md)** - Security best practices

## 🎯 **Use Cases**

### **🤖 AI Research Agents**
- Query entire library for literature reviews
- Extract relevant passages with context
- Navigate large datasets efficiently
- Structured responses for easy parsing

### **📱 Mobile Research**
- iOS Shortcuts for voice-activated search
- Quick book discovery on any device
- Offline-capable with local caching
- Universal browser compatibility

### **🔬 Academic Research**
- Cross-reference concepts across books
- Citation discovery and verification
- Topic exploration with semantic search
- Knowledge graph construction

### **⚡ Personal Knowledge Management**
- Instant access to your reading history
- Rediscover forgotten insights
- Build on previous research
- Accelerate learning and synthesis

## 🚀 **Performance Benchmarks**

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Health Check | < 50ms | ~15ms | ✅ |
| Book Listing | < 100ms | 12-30ms | ✅ |
| Individual Book | < 50ms | ~15ms | ✅ |
| Search Queries | < 200ms | 20-40ms | ✅ |
| Chunk Retrieval | < 100ms | 15-25ms | ✅ |

**Result**: All performance targets exceeded! 🎉

## 🔧 **Local Development**

```bash
# Clone repository
git clone https://github.com/noxwei/LibraryOfBabel.git
cd LibraryOfBabel

# Start local API (mirrors production port)
python src/api/secure_paginated_api.py

# Test locally
curl "http://localhost:5562/health"
```

For complete setup instructions, see [Installation Guide](docs/Installation-Guide.md).

## 🤝 **Connect**

- **GitHub**: [@noxwei](https://github.com/noxwei)
- **Threads**: [@maybe_foucault](https://threads.net/@maybe_foucault)

## 🎉 **Production Status**

**✅ FULLY OPERATIONAL**

The LibraryOfBabel API is production-ready and serving **838 books** with enterprise-grade security and performance. Perfect for researchers, developers, and AI agents seeking instant access to curated knowledge.

**🔗 Ready to explore?** Start with the [Simple Usage Guide](docs/SIMPLE_USAGE_GUIDE.md)

---

*Liberating knowledge through intelligent automation and searchable personal libraries.*

**Status**: Production-Ready ✅ | **Security**: Maximum ✅ | **Performance**: Optimized ✅