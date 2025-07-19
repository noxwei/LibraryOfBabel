# 🎯 iOS Shortcuts API - LLM Bot Instructions

**Created by:** Dr. Elena Rodriguez (Information Architecture Validator)  
**Philosophy:** "Information architecture makes complex knowledge feel simple"  
**Optimized for:** iOS Shortcuts, Data Jar, Mobile Workflows

## 📱 Quick Start for LLM Bots

This API is designed specifically for iOS Shortcuts with mobile-first architecture:
- **Single-value endpoints** (plain text, no JSON parsing needed)
- **Simple arrays** (easy for shortcuts loops)
- **Pre-formatted text** (ready for sharing/display)
- **Boolean responses** (perfect for if/then logic)
- **Data Jar optimized** (clean objects for persistence)

## 🔗 Base URL
```
https://api.ashortstayinhell.com:5562/api/shortcuts/
```

## 🔐 Authentication
- All endpoints require API key except `/health`
- **Authentication required** - API key must be provided by user
- Include as query parameter: `?api_key=YOUR_API_KEY`
- Or use header: `X-API-Key: YOUR_API_KEY`

## 📁 Documentation Structure
```
/endpoints/          # Individual endpoint YAML files
/authentication/     # Auth examples and troubleshooting
/examples/          # Complete iOS Shortcuts examples
/troubleshooting/   # Common issues and solutions
```

## 🎯 Endpoint Categories

### Single Values (Perfect for Shortcuts)
- `/books/count` → `2503` (plain text)
- `/random/title` → `"The Elegant Universe"` (plain text)
- `/search/{term}/has-results` → `true` (boolean)

### Simple Arrays (Easy Loops)
- `/books/title-list` → `["Title1", "Title2"]`
- `/books/author-list` → `["Author1", "Author2"]`

### Pre-formatted Text (Share Ready)
- `/random/share-text` → `"📚 Currently reading: Book by Author"`
- `/random/citation` → `"Author. Title (2023)"`

### Data Jar Ready
- `/stats/dashboard` → Clean JSON object for persistence
- `/user/reading-progress` → Reading tracker object

### Book Navigation
- `/books/{id}/construct` → Complete book structure
- `/books/{id}/page/{num}` → Single page with navigation

### Serendipity (ChatGPT Integration)
- `/serendipity/random-passage` → Random passage for prompts
- `/serendipity/story-starter` → Complete story starter package

## 🤖 LLM Bot Guidelines

1. **Always test endpoints** with `/health` first
2. **Check authentication** before reporting errors
3. **Use specific endpoint YAML** files for detailed parameters
4. **Provide iOS Shortcuts examples** when helping users
5. **Consider Data Jar integration** for persistence needs
6. **NEVER include actual API keys in documentation**

## 🔧 Common Parameters
- `limit`: Maximum results (default varies by endpoint)
- `api_key`: Authentication (required except health)
- Path parameters: `{term}`, `{id}`, `{page_num}`

## 🔍 URL Generator System

LLM bots can help users discover books and navigate the API using natural language:

### Step 1: Search for Books
Help users find books by using search endpoints:
- `/search/{term}` - General search
- `/books/title-list` - Browse available titles
- `/books/author-list` - Browse available authors

### Step 2: Generate Specific URLs
Once a book is found, help users create URLs for:
- **Reading**: `/books/{book_id}/page/{page_num}`
- **Book Info**: `/books/{book_id}/summary`
- **Full Text**: `/books/{book_id}/construct`

### Step 3: Teach Natural Navigation
Show users how to:
1. "Find me a book about physics" → Search → Get book_id
2. "Take me to page 5 of that book" → Generate page URL
3. "Show me the summary" → Generate summary URL

---
*Mobile-first API design by Dr. Elena Rodriguez - Making complex knowledge feel simple*