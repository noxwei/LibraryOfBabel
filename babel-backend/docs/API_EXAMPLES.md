# Library of Babel API Examples

## Quick Test Commands

### 1. Check Library Status
```bash
curl -s http://localhost:5570/api/library/info | jq '.'
```

Expected response shows library configuration, available concepts, and educational features.

### 2. Search for Books
```bash
# Search for books about infinity
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "infinity and paradox", "maxResults": 5}' | jq '.'

# Search for philosophy books
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "metaphysics consciousness", "mode": "comprehensive"}' | jq '.'
```

### 3. Get Specific Book
```bash
# Get book at specific coordinates
curl -s http://localhost:5570/api/book/123456/3/2/15 | jq '.'

# Get book metadata only (no content)
curl -s "http://localhost:5570/api/book/123456/3/2/15?includeContent=false" | jq '.'
```

### 4. Random Book Discovery
```bash
# Get a random book with full content
curl -s http://localhost:5570/api/random-book | jq '.'

# Get random book metadata only
curl -s "http://localhost:5570/api/random-book?includeContent=false" | jq '.'
```

### 5. Explore Concepts
```bash
# List all available concepts
curl -s http://localhost:5570/api/concepts | jq '.'

# Explore books about recursion
curl -s http://localhost:5570/api/explore/recursion?limit=3 | jq '.'

# Explore books about consciousness
curl -s http://localhost:5570/api/explore/consciousness?limit=5 | jq '.'
```

### 6. Health Check
```bash
curl -s http://localhost:5570/api/health | jq '.'
```

## Example Responses

### Search Response
```json
{
  "query": "infinity and paradox",
  "results": [
    {
      "id": "234567.4.1.8",
      "title": "Meditations on Infinity",
      "author": "Dr. Helena Blackwood", 
      "abstract": "An exploration of infinite concepts...",
      "relevanceScore": 0.89,
      "coordinates": {"hexagon": 234567, "wall": 4, "shelf": 1, "volume": 8},
      "genre": "Philosophy",
      "publicationYear": 1987
    }
  ],
  "educational": {
    "concept": "This demonstrates Borges' Library of Babel concept",
    "philosophy": "Every search reveals both sought knowledge and unexpected discoveries"
  }
}
```

### Book Response
```json
{
  "book": {
    "id": "123456.3.2.15",
    "title": "The Essential Nature of Being",
    "author": "Prof. Constantine Ellsworth",
    "chapters": [
      {
        "number": 1,
        "title": "The Concept of Existence", 
        "content": "In examining existence, we must consider...",
        "wordCount": 342
      }
    ],
    "bibliography": [
      {
        "author": "Alexander Goodwin",
        "title": "Studies in Metaphysics",
        "year": 1978
      }
    ]
  },
  "educational": {
    "concept": "Each book is generated deterministically from its coordinates"
  }
}
```

## Testing Different Search Modes

### Comprehensive Search (Default)
```bash
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "logic and reason", "mode": "comprehensive", "maxResults": 8}'
```

### Precise Search
```bash
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "ethics", "mode": "precise", "maxResults": 10}'
```

### Exploratory Search
```bash
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "time eternity", "mode": "exploratory", "maxResults": 6}'
```

## Educational Demonstrations

### Deterministic Generation
```bash
# These commands will always return the same book:
curl -s http://localhost:5570/api/book/42/0/0/0 | jq '.book.title'
curl -s http://localhost:5570/api/book/42/0/0/0 | jq '.book.title'
curl -s http://localhost:5570/api/book/42/0/0/0 | jq '.book.title'
```

### Infinite Space Exploration
```bash
# Explore different regions of the infinite library:
curl -s http://localhost:5570/api/book/1000000/5/4/31 | jq '.book.title'
curl -s http://localhost:5570/api/book/999999/2/1/16 | jq '.book.title' 
curl -s http://localhost:5570/api/book/500000/3/3/8 | jq '.book.title'
```

### Concept Mapping
```bash
# Search for the same concept multiple times to see consistent regions:
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "infinity", "maxResults": 3}' | jq '.results[].coordinates'
```

## Enhanced Mode Testing (If Enabled)

### Enable Enhanced Mode
```bash
# Set environment variable and restart server
export ENHANCED_MODE=true
export REAL_SEARCH_API=http://localhost:5560
```

### Enhanced Search
```bash
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "philosophy", "mode": "enhanced", "maxResults": 5}'
```

### Compare Modes
```bash
# Educational mode
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "consciousness", "mode": "comprehensive"}' | jq '.metadata.library.mode'

# Enhanced mode  
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "consciousness", "mode": "enhanced"}' | jq '.metadata.library.mode'
```

## Performance Testing

### Load Testing
```bash
# Generate multiple concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:5570/api/search \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"test $i\", \"maxResults\": 5}" &
done
wait
```

### Memory Usage
```bash
# Check server health and memory usage
curl -s http://localhost:5570/api/health | jq '.server.memory'
```

## Error Handling Examples

### Invalid Coordinates
```bash
# Test invalid coordinates (should return 400 error)
curl -s http://localhost:5570/api/book/123/7/0/0  # wall > 5
curl -s http://localhost:5570/api/book/123/0/6/0  # shelf > 4  
curl -s http://localhost:5570/api/book/123/0/0/35 # volume > 31
```

### Empty Search
```bash
# Test empty search query (should return 400 error)
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": ""}'
```

### Unknown Concept
```bash
# Test unknown concept (should return 400 error)
curl -s http://localhost:5570/api/explore/unknownconcept
```

## Batch Operations

### Multiple Book Retrieval
```bash
# Get multiple books in sequence
for coord in "1/0/0/0" "1/0/0/1" "1/0/0/2"; do
  echo "Book at $coord:"
  curl -s "http://localhost:5570/api/book/$coord?includeContent=false" | jq '.book.title'
done
```

### Concept Exploration
```bash
# Explore multiple concepts
for concept in "infinity" "paradox" "logic"; do
  echo "Books about $concept:"
  curl -s "http://localhost:5570/api/explore/$concept?limit=2" | jq '.books[].title'
done
```

## Frontend Integration Testing

### CORS Test
```bash
# Test CORS headers (should include Access-Control-Allow-Origin)
curl -v http://localhost:5570/api/library/info 2>&1 | grep -i "access-control"
```

### JSON Response Validation
```bash
# Validate all responses are valid JSON
curl -s http://localhost:5570/api/library/info | jq empty && echo "Valid JSON"
curl -s http://localhost:5570/api/health | jq empty && echo "Valid JSON"
```

---

## Educational Use Cases

### Philosophy Class
```bash
# Find books about existentialism
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "existence being reality", "maxResults": 5}'
```

### Computer Science Class  
```bash
# Explore algorithmic concepts
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "recursion algorithms", "maxResults": 5}'
```

### Literature Class
```bash
# Study narrative and meaning
curl -X POST http://localhost:5570/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "narrative meaning interpretation", "maxResults": 5}'
```

These examples demonstrate the full capabilities of the Library of Babel backend, from basic functionality to advanced educational applications.