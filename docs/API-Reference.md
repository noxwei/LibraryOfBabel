# API Reference

Complete documentation for the Library of Babel API endpoints. This API provides access to both the infinite procedural library and real ebook research capabilities.

## 🌐 Base URLs

- **Educational Mode (Procedural Generation)**: `http://localhost:5570/api`
- **Research Mode (Real Ebook Analysis)**: `http://localhost:5560/api` 
- **Production**: `https://your-domain.com/api`

**Port Reference:**
- **Port 5570**: Procedural/Educational domain - infinite book generation, Borges' library simulation
- **Port 5560**: Research domain - real ebook processing, AI agents, PostgreSQL database access

## 🔐 Authentication

Most endpoints are public for educational use. Research endpoints may require API keys.

```bash
# For authenticated endpoints
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:5570/api/endpoint
```

---

## 📚 Library Information

### `GET /api/library/info`

Get library configuration and statistics.

**Example Request:**
```bash
curl http://localhost:5570/api/library/info
```

**Response:**
```json
{
  "name": "Library of Babel",
  "mode": "educational",
  "version": "2.0.0",
  "features": {
    "proceduralGeneration": true,
    "infiniteSpace": true,
    "deterministicContent": true,
    "realBookSearch": false,
    "aiAgents": false
  },
  "statistics": {
    "maxBooks": 999999999,
    "availableConcepts": 30,
    "availableFields": 22,
    "totalGenerations": 15420,
    "uniqueCoordinates": 8750
  },
  "capabilities": {
    "searchModes": ["comprehensive", "precise", "exploratory"],
    "languages": ["english"],
    "formats": ["academic", "philosophical", "literary"]
  }
}
```

**Response Fields:**
- `mode`: Current library mode (`educational` or `research`)
- `features`: Available system capabilities
- `statistics`: Usage and generation statistics
- `capabilities`: Supported search modes and formats

---

## 🔍 Search Endpoints

### `POST /api/search`

Search the infinite library for relevant books.

**Example Request:**
```bash
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "consciousness and artificial intelligence",
    "mode": "comprehensive",
    "maxResults": 10,
    "filters": {
      "genre": "philosophy",
      "yearRange": [1980, 2024],
      "complexityRange": [5, 10]
    }
  }'
```

**Request Parameters:**
- `query` (required): Search terms or concepts
- `mode` (optional): Search mode (`comprehensive`, `precise`, `exploratory`, `enhanced`)
- `maxResults` (optional): Maximum results to return (default: 10, max: 50)
- `filters` (optional): Additional search filters

**Filters Object:**
```json
{
  "genre": "philosophy|science|literature|history|technology",
  "yearRange": [startYear, endYear],
  "complexityRange": [minComplexity, maxComplexity],
  "authorRegion": "europe|americas|asia|global",
  "language": "english|spanish|french|german",
  "minimumCitations": 5
}
```

**Response:**
```json
{
  "query": "consciousness and artificial intelligence",
  "mode": "comprehensive",
  "results": [
    {
      "id": "123456.3.2.15",
      "title": "Consciousness in Digital Systems",
      "author": "Dr. Elena Vasquez",
      "publicationYear": 1995,
      "genre": "philosophy",
      "abstract": "An examination of consciousness theories applied to artificial intelligence systems...",
      "relevanceScore": 0.94,
      "coordinates": {
        "hexagon": 123456,
        "wall": 3,
        "shelf": 2,
        "volume": 15
      },
      "metadata": {
        "wordCount": 4250,
        "chapterCount": 11,
        "citationCount": 18,
        "complexity": 7.2,
        "isbn": "978-0-123456-78-9",
        "deweyDecimal": "006.3"
      }
    }
  ],
  "metadata": {
    "totalFound": 847,
    "searchTime": "0.089s",
    "coordinatesExplored": 47,
    "library": {
      "mode": "educational",
      "infinite": true
    }
  },
  "educational": {
    "concept": "This demonstrates how infinite possibility enables perfect knowledge discovery",
    "philosophy": "Every search reveals both sought knowledge and unexpected discoveries"
  }
}
```

### `GET /api/search/suggestions`

Get search suggestions based on available concepts.

**Example Request:**
```bash
curl http://localhost:5570/api/search/suggestions?partial=conscious
```

**Response:**
```json
{
  "suggestions": [
    "consciousness",
    "consciousness studies", 
    "unconscious processes",
    "collective consciousness",
    "stream of consciousness"
  ],
  "concepts": [
    "phenomenology",
    "cognitive science",
    "philosophy of mind",
    "artificial intelligence",
    "neuroscience"
  ],
  "relatedFields": [
    "Psychology",
    "Philosophy", 
    "Cognitive Science",
    "Neuroscience"
  ]
}
```

---

## 📖 Book Endpoints

### `GET /api/book/:hexagon/:wall/:shelf/:volume`

Retrieve a specific book by coordinates.

**Example Request:**
```bash
curl http://localhost:5570/api/book/123456/3/2/15
```

**Response:**
```json
{
  "book": {
    "id": "123456.3.2.15",
    "title": "The Nature of Digital Consciousness",
    "author": "Prof. Constantine Ellsworth",
    "publicationYear": 1987,
    "genre": "philosophy",
    "abstract": "This fundamental examination explores the intersection of consciousness studies and computational theory...",
    "chapters": [
      {
        "number": 1,
        "title": "Foundations of Digital Thought",
        "content": "In examining digital consciousness, we must first establish the fundamental principles...",
        "wordCount": 342,
        "keyTerms": ["consciousness", "digital", "computation", "awareness"],
        "summary": "Introduces core concepts of digital consciousness theory."
      }
    ],
    "bibliography": [
      {
        "author": "Alexander Goodwin",
        "title": "Studies in Computational Mind",
        "year": 1978,
        "publisher": "Cambridge University Press",
        "isbn": "978-0-521-12345-6"
      }
    ],
    "metadata": {
      "wordCount": 4187,
      "chapterCount": 11,
      "pageCount": 324,
      "isbn": "978-0-123456-78-9",
      "deweyDecimal": "006.3",
      "language": "english",
      "complexity": 7.2
    }
  },
  "coordinates": {
    "hexagon": 123456,
    "wall": 3,
    "shelf": 2,
    "volume": 15,
    "adjacent": [
      "123456.3.2.14",
      "123456.3.2.16",
      "123456.3.1.15",
      "123456.3.3.15"
    ]
  },
  "educational": {
    "concept": "Each book is generated deterministically from its coordinates",
    "navigation": "Use adjacent coordinates to explore related content"
  }
}
```

### `GET /api/book/:id/chapters/:chapterNumber`

Get a specific chapter from a book.

**Example Request:**
```bash
curl http://localhost:5570/api/book/123456.3.2.15/chapters/3
```

**Response:**
```json
{
  "chapter": {
    "number": 3,
    "title": "Computational Models of Awareness",
    "content": "The development of computational models for consciousness requires...",
    "wordCount": 1240,
    "keyTerms": ["computation", "awareness", "modeling", "simulation"],
    "summary": "Explores various computational approaches to modeling consciousness.",
    "citations": [
      {
        "text": "According to Turing (1950), machine intelligence...",
        "reference": "Turing, A. M. (1950). Computing machinery and intelligence."
      }
    ]
  },
  "navigation": {
    "previousChapter": 2,
    "nextChapter": 4,
    "totalChapters": 11
  }
}
```

### `GET /api/random-book`

Get a randomly selected book from the library.

**Example Request:**
```bash
curl http://localhost:5570/api/random-book?genre=philosophy
```

**Response:**
```json
{
  "book": {
    "id": "987654.1.4.7",
    "title": "Meditations on Temporal Paradox",
    "author": "Dr. Miranda Chen",
    "abstract": "An exploration of time, causality, and paradox in modern philosophy...",
    "coordinates": {
      "hexagon": 987654,
      "wall": 1,
      "shelf": 4,
      "volume": 7
    }
  },
  "serendipity": {
    "message": "Sometimes the most profound discoveries come from unexpected encounters",
    "recommendedNext": ["987654.1.4.6", "987654.1.4.8"]
  }
}
```

---

## 🧠 Concept Exploration

### `GET /api/concepts`

List available concepts and academic fields.

**Example Request:**
```bash
curl http://localhost:5570/api/concepts
```

**Response:**
```json
{
  "concepts": [
    "infinity", "recursion", "paradox", "universals", "particulars",
    "causality", "determinism", "consciousness", "reality", "truth"
  ],
  "academicFields": [
    "Metaphysics", "Epistemology", "Logic", "Ethics", "Aesthetics",
    "Philosophy of Mind", "Philosophy of Science", "Political Philosophy"
  ],
  "thematicAdjectives": [
    "Essential", "Fundamental", "Critical", "Advanced", "Contemporary"
  ],
  "statistics": {
    "totalConcepts": 30,
    "totalFields": 22,
    "conceptCombinations": 435,
    "averageBooksPerConcept": 15420
  }
}
```

### `GET /api/explore/:concept`

Explore books related to a specific concept.

**Example Request:**
```bash
curl http://localhost:5570/api/explore/infinity?limit=5&depth=2
```

**Parameters:**
- `limit`: Maximum books to return (default: 10)
- `depth`: Exploration depth (1=direct, 2=related, 3=tangential)

**Response:**
```json
{
  "concept": "infinity",
  "exploration": {
    "direct": [
      {
        "id": "111111.0.0.1",
        "title": "On the Nature of Infinity",
        "relevance": 1.0,
        "relationship": "primary_focus"
      }
    ],
    "related": [
      {
        "id": "222222.2.1.5",
        "title": "Recursive Structures in Mathematics",
        "relevance": 0.8,
        "relationship": "mathematical_infinity"
      }
    ],
    "tangential": [
      {
        "id": "333333.4.3.12",
        "title": "Eternal Recurrence in Literature",
        "relevance": 0.6,
        "relationship": "conceptual_parallel"
      }
    ]
  },
  "pathways": {
    "mathematical": ["set_theory", "calculus", "topology"],
    "philosophical": ["metaphysics", "cosmology", "theology"],
    "literary": ["borges", "kafka", "joyce"]
  }
}
```

---

## 🔬 Research Endpoints (Enhanced Mode)

### `POST /api/research/search`

Search real ebook collections with AI analysis.

**Example Request:**
```bash
curl -X POST http://localhost:5560/api/research/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "query": "machine learning applications",
    "includeAnalysis": true,
    "filters": {
      "fileFormat": ["epub", "pdf"],
      "wordCountRange": [10000, 100000],
      "analysisDate": "2025-01-01"
    }
  }'
```

**Response:**
```json
{
  "query": "machine learning applications",
  "results": [
    {
      "bookId": "real_001",
      "title": "Hands-On Machine Learning",
      "author": "Aurélien Géron",
      "filePath": "/processed/hands-on-ml.epub",
      "analysis": {
        "chapterCount": 19,
        "wordCount": 180000,
        "complexity": 8.5,
        "keyTopics": ["neural networks", "supervised learning", "deep learning"],
        "extractedConcepts": ["tensorflow", "scikit-learn", "feature engineering"]
      },
      "relevanceScore": 0.95,
      "lastAnalyzed": "2025-07-03T11:28:15Z"
    }
  ],
  "metadata": {
    "totalBooks": 2847,
    "searchTime": "0.045s",
    "indexesUsed": ["content_gin", "concepts_btree"]
  }
}
```

### `GET /api/research/books/:bookId/analysis`

Get detailed AI analysis for a specific book.

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5560/api/research/books/real_001/analysis
```

**Response:**
```json
{
  "bookId": "real_001",
  "analysis": {
    "outline": {
      "chapterCount": 19,
      "sections": [
        {
          "title": "The Fundamentals of Machine Learning",
          "chapters": [1, 2, 3],
          "keyTopics": ["supervised learning", "training sets", "validation"]
        }
      ]
    },
    "concepts": {
      "primary": ["machine learning", "neural networks", "deep learning"],
      "secondary": ["feature engineering", "model validation", "overfitting"],
      "technical": ["tensorflow", "scikit-learn", "pandas", "numpy"]
    },
    "complexity": {
      "score": 8.5,
      "factors": {
        "vocabularyDifficulty": 8.2,
        "conceptDensity": 9.1,
        "mathematicalContent": 8.8
      }
    },
    "statistics": {
      "wordCount": 180000,
      "uniqueTerms": 12450,
      "codeExamples": 247,
      "figures": 89
    }
  },
  "generatedAt": "2025-07-03T11:28:15Z"
}
```

---

## 🤖 AI Agent Endpoints

### `GET /api/agents/status`

Get status of all AI agents.

**Example Request:**
```bash
curl http://localhost:5560/api/agents/status
```

**Response:**
```json
{
  "agents": {
    "reddit_bibliophile": {
      "status": "active",
      "persona": "u/DataScientistBookworm",
      "lastActivity": "2025-07-03T11:28:15Z",
      "booksAnalyzed": 47,
      "knowledgeGraphNodes": 156,
      "seedingCompliance": "100%"
    },
    "qa_agent": {
      "status": "active", 
      "testsRun": 1247,
      "successRate": "75%",
      "lastScan": "2025-07-03T10:15:00Z"
    },
    "seeding_monitor": {
      "status": "active",
      "torrentsTracked": 12,
      "compliantTorrents": 12,
      "violationsDetected": 0
    }
  },
  "systemHealth": {
    "overallStatus": "healthy",
    "agentCoordination": "optimal",
    "resourceUsage": "normal"
  }
}
```

### `POST /api/agents/reddit_bibliophile/analyze`

Trigger Reddit Bibliophile agent analysis.

**Example Request:**
```bash
curl -X POST http://localhost:5560/api/agents/reddit_bibliophile/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "bookCount": 5,
    "generateKnowledgeGraph": true,
    "redditStyleAnalysis": true
  }'
```

**Response:**
```json
{
  "analysisId": "reddit_analysis_20250703_112843",
  "status": "completed",
  "results": {
    "booksAnalyzed": 5,
    "totalChapters": 127,
    "totalWords": 487532,
    "knowledgeGraph": {
      "nodes": 89,
      "edges": 124,
      "clusters": 7
    },
    "redditPost": {
      "title": "🤓 u/DataScientistBookworm's Deep Dive: 5 Books Analyzed",
      "url": "/reports/reddit_analysis/reddit_analysis_20250703_112843.md",
      "previewSnippet": "Just finished analyzing 5 books and holy shit, the patterns are FASCINATING! 📊"
    }
  },
  "processingTime": "1.2s",
  "seedingCompliance": {
    "status": "all_compliant",
    "message": "🛡️ Perfect 2-week seeding compliance maintained!"
  }
}
```

---

## 📊 Analytics Endpoints

### `GET /api/analytics/usage`

Get library usage statistics.

**Example Request:**
```bash
curl http://localhost:5570/api/analytics/usage?period=week
```

**Response:**
```json
{
  "period": "week",
  "timeRange": {
    "start": "2025-06-26T00:00:00Z",
    "end": "2025-07-03T00:00:00Z"
  },
  "statistics": {
    "totalSearches": 1247,
    "uniqueBooks": 8750,
    "topConcepts": [
      {"concept": "consciousness", "searches": 156},
      {"concept": "infinity", "searches": 134},
      {"concept": "recursion", "searches": 89}
    ],
    "searchModes": {
      "comprehensive": 847,
      "precise": 234,
      "exploratory": 166
    },
    "averageResultsPerSearch": 8.7,
    "averageSearchTime": "0.092s"
  },
  "trends": {
    "popularityGrowing": ["artificial intelligence", "quantum mechanics"],
    "popularityDecreasing": ["classical logic"],
    "emergingTopics": ["digital humanities", "computational philosophy"]
  }
}
```

### `GET /api/analytics/knowledge-graph`

Get knowledge graph analytics for research mode.

**Example Request:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5560/api/analytics/knowledge-graph
```

**Response:**
```json
{
  "graph": {
    "totalNodes": 156,
    "totalEdges": 234,
    "nodeTypes": {
      "books": 47,
      "concepts": 78,
      "themes": 31
    },
    "connectivity": {
      "averageDegree": 3.2,
      "clusteringCoefficient": 0.67,
      "shortestPathLength": 2.8
    }
  },
  "insights": {
    "centralConcepts": [
      {"concept": "machine learning", "centrality": 0.89},
      {"concept": "consciousness", "centrality": 0.76}
    ],
    "conceptClusters": [
      {
        "name": "AI/Technology",
        "concepts": ["machine learning", "neural networks", "algorithms"],
        "books": 12
      }
    ],
    "crossDisciplinaryConnections": [
      {
        "fields": ["Philosophy", "Computer Science"],
        "connectionStrength": 0.78,
        "bridgingConcepts": ["consciousness", "intelligence", "computation"]
      }
    ]
  }
}
```

---

## 🛡️ Health and Monitoring

### `GET /api/health`

System health check.

**Example Request:**
```bash
curl http://localhost:5570/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": "7d 14h 32m",
  "services": {
    "proceduralGeneration": "healthy",
    "database": "healthy",
    "searchEngine": "healthy",
    "aiAgents": "healthy"
  },
  "performance": {
    "averageResponseTime": "89ms",
    "successRate": "99.7%",
    "errorRate": "0.3%"
  },
  "resources": {
    "memoryUsage": "45%",
    "diskUsage": "23%",
    "databaseSize": "2.4GB"
  }
}
```

### `GET /api/health/detailed`

Detailed system diagnostics.

**Response:**
```json
{
  "system": {
    "hostname": "babel-server-01",
    "platform": "darwin",
    "architecture": "arm64",
    "nodeVersion": "18.17.0",
    "pythonVersion": "3.11.4"
  },
  "database": {
    "status": "connected",
    "version": "PostgreSQL 14.8",
    "totalBooks": 2847,
    "totalChunks": 47523,
    "indexHealth": "optimal"
  },
  "agents": {
    "reddit_bibliophile": {
      "memory": "156MB",
      "cpu": "2.3%",
      "lastHeartbeat": "2025-07-03T11:28:43Z"
    }
  }
}
```

---

## 📝 Error Responses

All endpoints use consistent error response format:

**Error Response Structure:**
```json
{
  "error": {
    "code": "INVALID_COORDINATES",
    "message": "Coordinates must be within valid ranges",
    "details": {
      "invalidFields": ["hexagon"],
      "validRanges": {
        "hexagon": [0, 999999999],
        "wall": [0, 5],
        "shelf": [0, 4],
        "volume": [0, 31]
      }
    },
    "suggestion": "Use GET /api/random-book to find valid coordinates"
  },
  "requestId": "req_7f3e8a2c",
  "timestamp": "2025-07-03T11:28:15Z"
}
```

**Common Error Codes:**
- `INVALID_COORDINATES` - Coordinate values out of range
- `BOOK_NOT_FOUND` - Book doesn't exist at coordinates
- `INVALID_SEARCH_QUERY` - Malformed search parameters
- `RATE_LIMIT_EXCEEDED` - Too many requests
- `AUTHENTICATION_REQUIRED` - Missing or invalid API key
- `INTERNAL_ERROR` - Server error during processing

---

## 📈 Rate Limiting

API endpoints are rate limited to ensure fair usage:

- **Educational endpoints**: 100 requests/minute per IP
- **Research endpoints**: 50 requests/minute per API key
- **Analytics endpoints**: 20 requests/minute per API key

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1625097600
```

---

## 🔧 SDKs and Tools

### JavaScript/Node.js
```javascript
const BabelLibrary = require('@babel-library/client');

const library = new BabelLibrary({
  baseUrl: 'http://localhost:5570',
  apiKey: 'your-api-key' // For research endpoints
});

// Search the library
const results = await library.search('consciousness and AI');

// Get a specific book
const book = await library.getBook(123456, 3, 2, 15);
```

### Python
```python
from babel_library import LibraryClient

client = LibraryClient(
    base_url='http://localhost:5570',
    api_key='your-api-key'
)

# Search with filters
results = client.search(
    query='machine learning',
    mode='comprehensive',
    filters={'genre': 'science', 'yearRange': [2000, 2024]}
)

# Get random book
book = client.random_book(genre='philosophy')
```

### cURL Examples
```bash
# Save frequently used endpoints
export BABEL_API="http://localhost:5570/api"

# Search function
babel_search() {
  curl -X POST "$BABEL_API/search" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$1\", \"maxResults\": ${2:-10}}"
}

# Usage: babel_search "consciousness" 5
```

---

*This API enables infinite exploration of knowledge, whether procedurally generated or from real collections. Every search opens new pathways of discovery.*
<!-- Agent Commentary -->
---

## 🤖 Agent Bulletin Board

*Agents observe and comment on project evolution*

### 👤 Alex Thompson (Security Analyst)
*2025-07-07 00:17*

> API endpoints proliferating. Every endpoint is potential vulnerability. Security review needed.

### 👤 Dr. Sarah Kim (Technical Architecture Analyst)
*2025-07-07 00:17*

> Technical architecture demonstrates good separation of concerns. Agent modularity will enable future scaling.

### 👤 Jordan Park (Productivity & Efficiency Analyst)
*2025-07-07 00:17*

> Agent specialization creating efficiency through division of labor. Classic industrial engineering success pattern.

---
*Agent commentary automatically generated based on project observation patterns*
