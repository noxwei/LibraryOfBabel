# LibraryOfBabel Search API Documentation

## Overview

The LibraryOfBabel Search API provides RESTful endpoints for AI research agents to query the personal knowledge base. All responses are optimized for AI consumption with structured JSON format, relevance scoring, and contextual information.

## Base URL

```
http://localhost:5000/api
```

## Authentication

Currently no authentication required for local development. Production deployment should implement API key authentication.

## Response Format

All API responses follow this structure:

```json
{
  "query_metadata": {
    "timestamp": "2025-01-26T18:00:00.000Z",
    "response_time_ms": 15.34,
    "total_results": 25,
    "api_version": "1.0"
  },
  "results": [...],
  "search_suggestions": [...]
}
```

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check API and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected", 
  "books_indexed": 14,
  "chunks_indexed": 331,
  "response_time_ms": 5.23,
  "timestamp": "2025-01-26T18:00:00.000Z"
}
```

### 2. Search

**GET/POST** `/api/search`

Main search endpoint supporting multiple query types.

#### GET Parameters:
- `q` (required): Search query
- `type` (optional): Search type - `content`, `author`, `title`, `cross_reference`
- `limit` (optional): Number of results (default: 10)
- `highlight` (optional): Enable content highlighting (default: true)

#### POST Body:
```json
{
  "query": "artificial intelligence",
  "type": "content",
  "limit": 10,
  "highlight": true
}
```

#### Search Types:

##### Content Search (`type=content`)
Full-text search across all book content with relevance ranking.

**Example:**
```bash
GET /api/search?q=machine%20learning&type=content&limit=5
```

**Response:**
```json
{
  "query_metadata": {...},
  "results": [
    {
      "title": "A Human Algorithm",
      "author": "Flynn Coleman", 
      "publication_year": 2019,
      "chunk_type": "chapter",
      "chapter_number": 3,
      "word_count": 2847,
      "highlighted_content": "...discusses <b>machine learning</b> algorithms...",
      "relevance_rank": 0.876
    }
  ],
  "search_suggestions": [...]
}
```

##### Author Search (`type=author`)
Find all books by specific authors.

**Example:**
```bash
GET /api/search?q=Coleman&type=author
```

##### Title Search (`type=title`)
Search books by title.

**Example:**
```bash
GET /api/search?q=History&type=title
```

##### Cross-Reference Search (`type=cross_reference`)
Find books discussing multiple concepts simultaneously.

**Example:**
```bash
GET /api/search?q=democracy,technology&type=cross_reference
```

**Response:**
```json
{
  "query_metadata": {...},
  "results": [
    {
      "title": "The Age of Surveillance Capitalism",
      "author": "Shoshana Zuboff",
      "publication_year": 2019,
      "matching_chunks": 15,
      "chunk_types": "chapter, section",
      "avg_relevance": 0.654
    }
  ]
}
```

### 3. Statistics

**GET** `/api/stats`

Get comprehensive knowledge base statistics.

**Response:**
```json
{
  "knowledge_base_stats": {
    "total_books": {"count": 14},
    "total_chunks": {"count": 331},
    "total_words": {"count": 815891},
    "chunk_types": [
      {"chunk_type": "chapter", "count": 156},
      {"chunk_type": "section", "count": 175}
    ],
    "top_authors": [
      {
        "author": "Flynn Coleman",
        "book_count": 2,
        "total_words": 145230
      }
    ],
    "processing_stats": {
      "avg_words_per_book": 58277.93,
      "max_words_per_book": 127845,
      "min_words_per_book": 15432
    }
  },
  "timestamp": "2025-01-26T18:00:00.000Z"
}
```

### 4. Search Suggestions

**GET** `/api/suggest`

Get suggested search queries and popular content.

**Response:**
```json
{
  "suggestions": {
    "popular_authors": [
      "Flynn Coleman",
      "Yuval Noah Harari",
      "Shoshana Zuboff"
    ],
    "suggested_topics": [
      "artificial intelligence",
      "digital privacy", 
      "human rights"
    ],
    "recent_books": [
      "A Human Algorithm by Flynn Coleman",
      "The Age of Surveillance Capitalism by Shoshana Zuboff"
    ],
    "search_examples": [
      "Search by content: 'artificial intelligence'",
      "Search by author: 'type=author&q=Coleman'",
      "Cross-reference: 'type=cross_reference&q=democracy,technology'"
    ]
  },
  "timestamp": "2025-01-26T18:00:00.000Z"
}
```

## AI Agent Integration Examples

### Python Example

```python
import requests

# Initialize API client
api_base = "http://localhost:5000/api"

def search_knowledge_base(query, search_type="content", limit=10):
    """Search the knowledge base for AI research"""
    response = requests.get(f"{api_base}/search", params={
        'q': query,
        'type': search_type,
        'limit': limit,
        'highlight': True
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data['results'])} results in {data['query_metadata']['response_time_ms']}ms")
        return data['results']
    else:
        print(f"Search failed: {response.status_code}")
        return []

# Example usage
results = search_knowledge_base("machine learning ethics")
for result in results:
    print(f"📖 {result['title']} by {result['author']}")
    print(f"   {result.get('highlighted_content', result.get('content_preview', ''))}")
```

### JavaScript Example

```javascript
class LibraryOfBabelClient {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = baseUrl;
    }
    
    async search(query, options = {}) {
        const params = new URLSearchParams({
            q: query,
            type: options.type || 'content',
            limit: options.limit || 10,
            highlight: options.highlight !== false ? 'true' : 'false'
        });
        
        const response = await fetch(`${this.baseUrl}/search?${params}`);
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async crossReference(concepts) {
        return this.search(concepts.join(','), { type: 'cross_reference' });
    }
    
    async getStats() {
        const response = await fetch(`${this.baseUrl}/stats`);
        return await response.json();
    }
}

// Usage
const library = new LibraryOfBabelClient();

library.search('artificial intelligence')
    .then(data => {
        console.log(`Found ${data.results.length} results`);
        data.results.forEach(result => {
            console.log(`📚 ${result.title} - ${result.author}`);
        });
    });
```

## Performance Characteristics

- **Average response time**: 3-15ms for simple searches
- **Complex queries**: <50ms for cross-reference searches
- **Concurrent requests**: Supports multiple AI agents simultaneously
- **Database optimization**: Sub-second performance on 800K+ words

## Error Handling

All errors return JSON with appropriate HTTP status codes:

```json
{
  "error": "Query parameter required",
  "details": "Additional error context"
}
```

**Common Status Codes:**
- `200` - Success
- `400` - Bad Request (missing parameters)
- `404` - Endpoint not found
- `500` - Internal server error

## Deployment

### Development
```bash
pip install -r requirements.txt
python src/api/search_api.py
```

### Production
Consider using:
- **Gunicorn** for WSGI server
- **Nginx** for reverse proxy
- **Redis** for caching
- **API authentication** for security

## Rate Limiting

No rate limiting implemented for local development. Production deployment should implement appropriate rate limiting for AI agent access.

---

*Optimized for AI research agent consumption with millisecond response times*