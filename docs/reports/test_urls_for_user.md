# Test URLs for Ollama Integration - No API Key Required

## 🔍 Direct LibraryOfBabel Search URLs

Based on your observed behavioral patterns, here are direct search URLs you can test immediately:

### 1. **AI Consciousness + Philosophy**
```
https://api.ashortstayinhell.com/api/v3/search?q=AI+consciousness+philosophy&limit=10&search_type=semantic
```

### 2. **Octavia Butler Social Justice**
```
https://api.ashortstayinhell.com/api/v3/search?q=Octavia+Butler+social+justice&limit=10&search_type=author&author=Butler
```

### 3. **Digital Surveillance Theory**
```
https://api.ashortstayinhell.com/api/v3/search?q=digital+surveillance+theory&limit=10&search_type=semantic
```

### 4. **Climate Change Policy**
```
https://api.ashortstayinhell.com/api/v3/search?q=climate+change+policy&limit=10&search_type=topic
```

### 5. **Critical Race Theory Technology**
```
https://api.ashortstayinhell.com/api/v3/search?q=critical+race+theory+technology&limit=10&search_type=semantic
```

### 6. **Post-structuralist Analysis**
```
https://api.ashortstayinhell.com/api/v3/search?q=post-structuralist+analysis&limit=10&search_type=concept
```

## 🤖 Ollama Integration Test URLs (API Key Required)

### Health Check (No Auth)
```
https://api.ashortstayinhell.com/api/v3/health
```

### Ollama Query Endpoint (Requires API Key)
```
POST https://api.ashortstayinhell.com/api/v3/ollama/query
Content-Type: application/json
X-API-Key: YOUR_API_KEY_HERE

{
  "query": "Find books about AI consciousness through philosophical lens"
}
```

### Ollama Health Check (Requires API Key)
```
GET https://api.ashortstayinhell.com/api/v3/ollama/health
X-API-Key: YOUR_API_KEY_HERE
```

## 🧪 cURL Test Commands

### 1. Test Basic API Health
```bash
curl -X GET "https://api.ashortstayinhell.com/api/v3/health"
```

### 2. Test Direct Search
```bash
curl -X GET "https://api.ashortstayinhell.com/api/v3/search?q=AI+consciousness&limit=5"
```

### 3. Test Ollama Integration (with API key)
```bash
curl -X POST "https://api.ashortstayinhell.com/api/v3/ollama/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"query": "Find books about digital surveillance through critical theory"}'
```

## 📊 Expected Response Format

### Direct Search Response:
```json
{
  "success": true,
  "query": "AI consciousness",
  "results": [
    {
      "book_id": 123,
      "title": "Book Title",
      "author": "Author Name",
      "content": "Relevant excerpt...",
      "relevance_score": 0.85
    }
  ],
  "total_found": 25,
  "processing_time": 0.045
}
```

### Ollama Integration Response:
```json
{
  "success": true,
  "data": {
    "original_query": "Find books about AI consciousness",
    "structured_query": {
      "search_terms": ["AI", "consciousness", "philosophy"],
      "search_type": "semantic",
      "limit": 10
    },
    "search_urls": [
      {
        "url": "https://api.ashortstayinhell.com/api/v3/search?q=AI+consciousness...",
        "strategy": "semantic",
        "description": "Primary semantic search"
      }
    ],
    "explanation": "Converted natural language to structured search",
    "performance": {
      "processing_time": 0.032
    }
  }
}
```

## 🎯 Test Strategy Recommendations

### Phase 1: Basic API Testing
1. Test health endpoint first
2. Try direct search URLs with your favorite topics
3. Verify 360-book database is responding

### Phase 2: Ollama Integration (with API key)
1. Test Ollama health endpoint
2. Try simple natural language queries
3. Test complex multi-concept queries

### Phase 3: Advanced Testing
1. Test personalized recommendations from agents
2. Try experimental complexity queries
3. Validate cross-domain synthesis results

## 💡 Quick Browser Tests

Just paste these URLs directly into your browser:

1. **API Health**: https://api.ashortstayinhell.com/api/v3/health
2. **AI Search**: https://api.ashortstayinhell.com/api/v3/search?q=artificial+intelligence&limit=5
3. **Philosophy Search**: https://api.ashortstayinhell.com/api/v3/search?q=philosophy+consciousness&limit=5
4. **Butler Search**: https://api.ashortstayinhell.com/api/v3/search?q=Octavia+Butler&search_type=author&limit=5

## 🔒 API Key Information

For Ollama integration testing, you'll need an API key. The system supports multiple authentication methods:
- Header: `X-API-Key: your_key`
- Bearer token: `Authorization: Bearer your_key`
- Query parameter: `?api_key=your_key`

## 🚀 Ready to Test!

Start with the browser URLs above, then move to cURL commands, and finally test the Ollama integration when you have your API key ready!