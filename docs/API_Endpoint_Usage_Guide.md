# LibraryOfBabel API Endpoint Usage Guide

**Production API**: `https://api.ashortstayinhell.com:5562`  
**Status**: ✅ **LIVE & OPERATIONAL**  
**SSL**: ✅ **Enabled with Let's Encrypt certificates**  
**Last Updated**: August 19, 2025

---

## 🚀 Quick Start

### Base URL
```
https://api.ashortstayinhell.com:5562
```

### Authentication
 **IMPORTANT**: Never hardcode API keys in documentation or source code!

**Environment Variable Setup**:
```bash
# Set your API key as an environment variable
export API_KEY="<your-babel-api-key>"

# Or add to your shell profile
echo 'export API_KEY="<your-babel-api-key>"' >> ~/.bashrc
source ~/.bashrc
```

**Usage in Requests**:
```bash
# Use environment variable (recommended)
curl -k "https://api.ashortstayinhell.com:5562/health"

# Or pass as parameter (less secure)
curl -k "https://api.ashortstayinhell.com:5562/api/books?action=list&api_key=$API_KEY"
```

### Test the API
```bash
# Health check
curl -k "https://api.ashortstayinhell.com:5562/health"

# Books list with sorting (using env var)
curl -k "https://api.ashortstayinhell.com:5562/api/books?action=list&limit=3&sort=title&api_key=$API_KEY"
```

---

## 📚 Books API (`/api/books`)

### Available Actions: 7
- `list` - Get paginated list of books with sorting
- `summary` - Get book summary
- `toc` - Get table of contents
- `random_page` - Get random page content
- `page` - Get specific page content
- `construct` - Build book from chunks
- `info` - Get book metadata

### List Books with Sorting

**Endpoint**: `GET /api/books?action=list`

**Parameters**:
- `limit` (optional): Number of results per page (default: 10, max: 100)
- `page` (optional): Page number (default: 1)
- `sort` (optional): Sort field - `book_id`, `author`, `title`, `publication_date`, `word_count`

**Default Behavior**:
- **Default Sort**: `title` (alphabetical by title)
- **Default Limit**: 10 items per page
- **Default Page**: 1
- **Consistency**: Same sort order maintained across pagination

**Examples**:

```bash
# Sort by title (alphabetical) - DEFAULT
curl -k "https://api.ashortstayinhell.com:5562/api/books?action=list&limit=5&api_key=$API_KEY"

# Sort by author
curl -k "https://api.ashortstayinhell.com:5562/api/books?action=list&limit=5&sort=author&api_key=$API_KEY"

# Sort by word count (largest first)
curl -k "https://api.ashortstayinhell.com:5562/api/books?action=list&limit=5&sort=word_count&api_key=$API_KEY"

# Sort by publication date (newest first)
curl -k "https://api.ashortstayinhell.com:5562/api/books?action=list&limit=5&sort=publication_date&api_key=$API_KEY"
```

**Response Format**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "book_id": 4463,
        "title": "\"I Give You My Body . . .\"",
        "author": "Diana Gabaldon",
        "genre": "Unknown",
        "publication_date": "2025-07-25 02:50:30.066637",
        "word_count": 36416,
        "processed_date": "2025-08-14T02:50:30.066689"
      }
    ],
    "pagination": {
      "limit": 5,
      "page": 1,
      "total_count": 5,
      "total_pages": 1
    },
    "sorting": {
      "sort_by": "title",
      "sort_options": ["book_id", "author", "title", "publication_date", "word_count"]
    }
  },
  "meta": {
    "request_id": "fcd2660d-05c2-4717-8f57-c8887a67bbfa",
    "response_time_ms": 0.0,
    "timestamp": "2025-08-14T07:40:47.503661+00:00"
  }
}
```

---

## 🔍 Search API (`/api/search`)

### Available Actions: 10
- `search` - General semantic search (vector similarity)
- `passage` - Semantic passage search (embedding-based)
- `highlighted` - Exact text matching (GIN trigram)
- `chapter` - Chapter-level search
- `fullbook` - Full book content search
- `metadata` - Search book metadata
- `genre` - Genre-based search
- `author` - Author-specific search
- `title` - Title-based search
- `advanced` - Multi-criteria search

### Search with Sorting

**Endpoint**: `GET /api/search`

**Parameters**:
- `q` (required): Search query
- `action` (required): Search type
- `limit` (optional): Results per page (default: 10, max: 100)
- `page` (optional): Page number (default 1 **IMPORTANT**: Always specify page for consistency)
- `sort` (optional): Sort field - `relevance`, `title`, `author`, `word_count`, `publication_date`

**Default Behavior**:
- **Default Sort**: `relevance` (search relevance score)
- **Default Limit**: 10 items per page
- **Default Page**: 1
- **Consistency**: Same sort order maintained across pagination

**Examples**:

```bash
# Semantic search sorted by relevance (DEFAULT)
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=philosophy&action=search&limit=3&api_key=$API_KEY"

# Semantic search sorted by title
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=philosophy&action=search&limit=3&sort=title&api_key=$API_KEY"

# Passage search (semantic/embedding-based) - DEFAULT sort by relevance
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=ADHD&action=passage&limit=3&api_key=$API_KEY"

# Highlighted search (exact text matching) - DEFAULT sort by relevance
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=ADHD&action=highlighted&limit=3&api_key=$API_KEY"
```

**Response Formats**:

**Search Results**:
```json
{
  "success": true,
  "data": {
    "data": {
      "query": "philosophy",
      "results": [
        {
          "title": "Dune: The Butlerian Jihad",
          "author": "Kevin J. Anderson",
          "book_id": 973,
          "chunk_id": "1527_chapter_92",
          "content_preview": "The darkness of humanity's past...",
          "relevance": 1.0,
          "word_count": 786
        }
      ],
      "search_method": "Vector similarity (ultra-fast)",
      "total_results": 3
    },
    "success": true
  },
  "meta": {
    "request_id": "e3a87e19-fecb-413d-a801-c12491fe6e4d",
    "response_time_ms": 0.0,
    "timestamp": "2025-08-14T07:43:08.537173+00:00"
  }
}
```

**Passage Results**:
```json
{
  "success": true,
  "data": [
    {
      "title": "Indefinite",
      "author": "Michael L. Walker",
      "chunk_id": "1793_chapter_13",
      "chunk_type": "chapter",
      "content": "Alone Time Scott was released...",
      "similarity_score": 1.0
    }
  ],
  "meta": {
    "pagination": {"total_count": 3},
    "request_id": "40886a15-c39f-4b11-9f8d-512c9557dd3b",
    "response_time_ms": 0.0,
    "timestamp": "2025-08-14T07:43:13.186541+00:00"
  }
}
```

---

## 📱 Mobile-Optimized Endpoints

### iOS Shortcuts Integration
- `/api/mobile/search` - Optimized search for mobile
- `/api/mobile/books` - Mobile-friendly book operations
- `/api/mobile/quick` - Quick access endpoints

---

## 📊 Pagination & Sorting Guidelines

### Pagination
- **Default**: 10 items per page
- **Maximum**: 100 items per page
- **Page Navigation**: Use `page` parameter
- **Total Count**: Always included in response
- **Consistency**: Same sort order maintained across all pages

### Sorting Options

**Books List**:
- `book_id` - Numeric order
- `author` - Alphabetical by author
- `title` - Alphabetical by title (DEFAULT)
- `publication_date` - Chronological (newest first)
- `word_count` - Numeric (largest first)

**Search Results**:
- `relevance` - Search relevance score (DEFAULT)
- `title` - Alphabetical by title
- `author` - Alphabetical by author
- `word_count` - Numeric by word count
- `publication_date` - Chronological order

### Default Behavior & Consistency
**Why Defaults Matter**:
- **Prevents Jumping**: Results stay in same order across pagination
- **User Experience**: Consistent sorting prevents confusion
- **Performance**: Default sorts are optimized for speed
- **Caching**: Client-side caching works reliably with consistent sorts

**Best Practices**:
- **Always specify `page`** for search results to maintain consistency
- Use `limit=20-50` for optimal performance
- Implement client-side caching for sorted results
- Use `page` parameter for large result sets
- Sort by `relevance` for best search results (DEFAULT)
- Sort by `title` for book browsing (DEFAULT)

---

## 🔧 Response Formats

### Standard Response Structure
```json
{
  "success": boolean,
  "data": object|array,
  "meta": {
    "request_id": "uuid",
    "response_time_ms": float,
    "timestamp": "ISO-8601"
  }
}
```

### List Response Structure
```json
{
  "success": true,
  "data": {
    "items": array,
    "pagination": {
      "limit": int,
      "page": int,
      "total_count": int,
      "total_pages": int
    },
    "sorting": {
      "sort_by": string,
      "sort_options": array
    }
  }
}
```

---

## ⚠️ Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found
- `500` - Internal Server Error

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error information"
  }
}
```

### Common Error Codes
- `INVALID_API_KEY` - Authentication failed
- `INVALID_PARAMETERS` - Missing or invalid parameters
- `BOOK_NOT_FOUND` - Requested book doesn't exist
- `SEARCH_FAILED` - Search operation failed
- `DATABASE_ERROR` - Database connection issue

---

## 🧠 Intertextual Analysis API (`/api/search` - Advanced Literary Research)

**NEW**: Transform LibraryOfBabel from basic book search into a computational literary research platform with sophisticated NLP analysis capabilities.

### Available Advanced Actions: 6

#### 🌐 Author Influence Networks (`action=author_influence`)
**Purpose**: Analyze stylistic connections between authors through computational similarity  
**Method**: Vector embeddings of opening passages (first 8K words) using nomic-embed-text  
**Results**: 1035 relationships across 90 unique authors  
**Performance**: ~30ms response time  

**Examples**:
```bash
# Get network overview (top connected authors)
curl -k "https://api.ashortstayinhell.com:5562/api/search?action=author_influence&limit=5&api_key=$API_KEY"

# Find authors similar to Mark Fisher
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=Mark%20Fisher&action=author_influence&limit=3&api_key=$API_KEY"
```

**Response Structure**:
```json
{
  "data": {
    "data": {
      "network_statistics": {
        "total_relationships": 1035,
        "unique_authors": 90,
        "avg_influence_score": 0.992
      },
      "top_connected_authors": [
        {
          "author": "Mark Fisher",
          "connection_count": 45,
          "avg_score": 0.994
        }
      ]
    }
  }
}
```

#### 🔄 Thematic Evolution (`action=thematic_evolution`)
**Purpose**: Track how literary themes evolve across historical periods  
**Method**: Semantic clustering + historical period analysis  
**Results**: 3 primary themes, 6 evolution patterns across medieval/enlightenment periods  
**Performance**: ~25ms response time  

**Examples**:
```bash
# Get thematic evolution overview
curl -k "https://api.ashortstayinhell.com:5562/api/search?action=thematic_evolution&limit=5&api_key=$API_KEY"

# Track specific theme evolution
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=time_memory&action=thematic_evolution&limit=3&api_key=$API_KEY"
```

**Response Structure**:
```json
{
  "data": {
    "data": {
      "theme_rankings": [
        {
          "theme_name": "time_memory",
          "avg_prevalence": 3.629,
          "pattern_count": 2,
          "time_periods": ["period_enlightenment", "period_medieval"]
        }
      ],
      "evolution_statistics": {
        "total_themes": 3,
        "total_patterns": 6,
        "avg_theme_prevalence": 2.713
      }
    }
  }
}
```

#### 📊 Content Analysis (`action=content_analysis`)
**Purpose**: Deep NLP-powered stylometric and thematic analysis  
**Method**: spaCy pipeline + custom stylometric metrics  
**Results**: 50 books with comprehensive analysis including vocabulary richness, narrative structure  
**Performance**: ~40ms response time  

**Examples**:
```bash
# Get stylometric analysis results
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=stylometric&action=content_analysis&limit=2&api_key=$API_KEY"

# Get content analysis overview
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=overview&action=content_analysis&limit=3&api_key=$API_KEY"
```

**Response Structure**:
```json
{
  "data": {
    "data": {
      "analysis_type": "stylometric_features",
      "books": [
        {
          "book_id": 45,
          "title": "Capitalist Realism",
          "author": "Mark Fisher",
          "stylometric_profile": {
            "vocabulary_richness": 0.096,
            "avg_sentence_length": 25.4,
            "dialogue_ratio": 0.0,
            "narrative_structure": "odyssey"
          }
        }
      ]
    }
  }
}
```

#### 🔍 Semantic Discovery (`action=discovery`)
**Purpose**: Intelligent book discovery using opening passage semantic analysis  
**Method**: Vector similarity search on opening chunks (first 8K words)  
**Performance**: ~200-400ms response time  

**Examples**:
```bash
# Discover books similar to mystery/detective themes
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=mystery%20detective%20crime&action=discovery&limit=3&api_key=$API_KEY"

# Find science fiction recommendations
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=science%20fiction%20space&action=discovery&limit=3&api_key=$API_KEY"
```

#### ✍️ Writing Style Analysis (`action=style`)
**Purpose**: Analyze and match writing styles based on opening passages  
**Method**: Stylistic similarity scoring using vector embeddings  
**Performance**: ~30ms response time  

**Examples**:
```bash
# Find books with first-person narrative style
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=first%20person%20narrative&action=style&limit=3&api_key=$API_KEY"

# Find sparse, minimalist prose styles
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=hemingway%20sparse%20prose&action=style&limit=2&api_key=$API_KEY"
```

#### ⭐ Content Quality Assessment (`action=quality`)
**Purpose**: Assess content quality using computational metrics  
**Method**: Quality scoring based on opening passage analysis  
**Performance**: ~30ms response time  

**Examples**:
```bash
# Find high-quality literary works
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=well%20written%20literary&action=quality&limit=2&api_key=$API_KEY"

# Find complex literary prose
curl -k "https://api.ashortstayinhell.com:5562/api/search?q=complex%20literary%20prose&action=quality&limit=3&api_key=$API_KEY"
```

### 🎯 Research Use Cases

#### Academic Research
- **Literary Network Analysis**: Map influence patterns between authors
- **Thematic Studies**: Track evolution of themes across historical periods
- **Stylometric Research**: Quantitative analysis of writing styles
- **Comparative Literature**: Cross-author stylistic similarity analysis

#### Content Discovery
- **Smart Recommendations**: Semantic similarity beyond keyword matching
- **Quality Assessment**: Computational quality metrics for content curation
- **Style Matching**: Find books with similar narrative voices
- **Thematic Exploration**: Discover books exploring similar concepts

#### Computational Humanities
- **Digital Literary Criticism**: Data-driven literary analysis
- **Cultural Evolution**: Track thematic changes across time periods
- **Author Attribution**: Stylistic fingerprinting and similarity
- **Narrative Structure Analysis**: Classify story archetypes

### 🔬 Methodology & Validation

#### Author Influence Networks
- **Data Source**: Opening 8K words from each book (most stylistically distinctive)
- **Algorithm**: nomic-embed-text vector embeddings + cosine similarity
- **Threshold**: 0.99+ similarity score indicates strong stylistic connection
- **Validation**: 1035 relationships across 90 authors demonstrate meaningful connections

#### Thematic Evolution
- **Clustering**: MiniBatchKMeans semantic clustering (25 themes from 4,956 books)
- **Time Periods**: Historical period classification (medieval, enlightenment, modern)
- **Tracking**: Theme prevalence scores across different time periods
- **Results**: 3 primary themes with 6 distinct evolution patterns

#### Content Analysis Pipeline
- **NLP Engine**: spaCy with en_core_web_sm model
- **Features**: Named entities, vocabulary richness, sentence patterns, dialogue ratios
- **Classification**: Narrative structures (traditional, odyssey, creation myth, fairy tale)
- **Processing**: 50 books analyzed with comprehensive stylometric profiling

### ⚡ Performance Characteristics

| Endpoint | Avg Response Time | Data Processing | Computational Complexity |
|----------|------------------|-----------------|-------------------------|
| Author Influence | 20-30ms | 1035 relationships | Vector similarity (fast) |
| Thematic Evolution | 20-25ms | 6 patterns, 3 themes | Clustering analysis (fast) |
| Content Analysis | 35-45ms | 50 books, full NLP | spaCy processing (medium) |
| Discovery | 200-400ms | Semantic search | Vector operations (acceptable) |
| Style Analysis | 25-35ms | Style matching | Embedding comparison (fast) |
| Quality Assessment | 25-35ms | Quality scoring | Computational metrics (fast) |

---

## 🚀 Performance Tips

### Optimization Strategies
1. **Use Appropriate Limits**: Keep `limit` under 50 for best performance
2. **Implement Caching**: Cache sorted results client-side
3. **Batch Requests**: Use pagination instead of large result sets
4. **Choose Right Search Type**: Use `passage` for semantic, `highlighted` for exact text

### Performance Metrics
- **Response Time**: Typically <1ms for most operations
- **Search Speed**: Vector similarity (ultra-fast), GIN trigram (instant)
- **Database**: PostgreSQL-First architecture with optimized functions

---

## 💡 Use Cases

### Content Discovery
- Browse books by author, title, or publication date
- Sort by word count to find comprehensive works
- Use pagination for large catalogs

### Research & Analysis
- Semantic search for concept exploration
- Exact text matching for quote verification
- Genre-based filtering for targeted research

### Mobile Applications
- iOS Shortcuts integration
- Quick book lookups
- Offline content preparation

---

## 🏗️ Architecture

### PostgreSQL-First Design
- Business logic in database functions
- Optimized vector similarity search
- GIN trigram indexing for text search
- Efficient pagination and sorting

### API Structure
- RESTful endpoints with consistent patterns
- Comprehensive error handling
- Request/response logging
- SSL encryption for security

---

## 📝 Best Practices

### API Usage
1. **Always include API key** in requests
2. **Use HTTPS** for all production calls
3. **Implement proper error handling**
4. **Cache responses** when appropriate
5. **Respect rate limits** (if implemented)

### Development
1. **Test with small limits** first
2. **Validate response formats**
3. **Handle pagination properly**
4. **Use appropriate search types**
5. **Monitor response times**

---

## 📋 Changelog

### August 14, 2025 - Production Release ✅
- **API Status**: Now live on `https://api.ashortstayinhell.com:5562`
- **SSL**: Enabled with Let's Encrypt certificates
- **Sorting**: Full sorting support for books and search endpoints
- **Performance**: Sub-millisecond response times
- **Documentation**: Comprehensive usage guide
- **Security**: Environment variables for API keys (no hardcoded secrets)

### Recent Updates
- Added sorting capabilities to all list and search endpoints
- Fixed passage search functionality
- Improved error handling and response formats
- Enhanced pagination metadata
- Optimized database queries
- **Added default sorts and pagination for consistency**

---

## 🆘 Support

### Testing
- **Health Check**: `GET /health`
- **API Info**: `GET /api/info`
- **Status**: `GET /api/health`

### Development
- **Local Testing**: Use `http://localhost:5562` (HTTP)
- **Production**: Use `https://api.ashortstayinhell.com:5562` (HTTPS)
- **SSL**: Use `-k` flag with curl for self-signed certificates in testing

---

**🎯 Ready for Production Use!**  
All endpoints tested and verified on the live external domain with SSL encryption.

**🔒 Security Note**: This documentation uses environment variables for API keys. Never hardcode secrets in your code or documentation!
