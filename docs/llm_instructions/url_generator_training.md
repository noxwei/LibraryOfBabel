# 🔗 LLM URL Generator Training Guide

## 🎯 Training Objective
Train LLM bots (Lexi, Reddit Bibliophile) to help users navigate the iOS Shortcuts API using natural language to generate specific URLs.

## 📋 Training Methodology

### Step 1: Book Discovery
Teach users to find books first using search capabilities:

```
User: "I want to read something about space"
LLM: "Let me help you find space-related books. I'll search our library."
→ Use: GET /search/space?api_key=YOUR_KEY
→ Parse results to find book_id values
```

### Step 2: URL Construction
Once book_id is found, generate specific navigation URLs:

```
Example book_id found: "2847"
User: "Take me to page 10"
LLM: "Here's your direct link to page 10:"
→ Generate: https://api.ashortstayinhell.com:5562/api/shortcuts/books/2847/page/10?api_key=YOUR_KEY
```

### Step 3: URL Categories to Generate

#### Reading URLs
- **Single Page**: `/books/{book_id}/page/{page_num}`
- **Book Construction**: `/books/{book_id}/construct`
- **Summary**: `/books/{book_id}/summary`

#### Discovery URLs  
- **Search**: `/search/{term}`
- **Author Search**: `/search/author/{author_name}`
- **Title Search**: `/search/title/{title_part}`

#### Random Discovery
- **Random Book**: `/random/book`
- **Random Passage**: `/serendipity/random-passage`
- **Story Starter**: `/serendipity/story-starter`

## 🎪 Training Examples

### Example 1: Complete Navigation Flow
```
User: "Find me a book by Carl Sagan"
LLM Response:
1. "Searching for Carl Sagan books..."
2. Use: /search/author/carl%20sagan
3. "Found 'Cosmos' (book_id: 1847). What would you like to do?"
4. User: "Read page 1"
5. Generate: /books/1847/page/1?api_key=YOUR_KEY
```

### Example 2: Natural Discovery
```
User: "I'm feeling adventurous, show me something random"
LLM Response:
1. "Let me find you a serendipitous discovery!"
2. Use: /serendipity/story-starter
3. "Here's a story starter to spark your imagination..."
4. Present the generated content with navigation options
```

## 🔒 Security Guidelines

### ✅ Safe Practices
- Always ask user for their API key
- Never store or log API keys
- Generate URLs with placeholder: `?api_key=YOUR_KEY`
- Teach users to replace `YOUR_KEY` with their actual key

### ❌ Never Do This
- Include actual API keys in generated URLs
- Store API keys in conversation memory
- Share API keys between users
- Include keys in documentation examples

## 🎯 Training Success Criteria

### For Lexi (UX Designer)
- Can generate user-friendly URLs for iOS Shortcuts
- Explains how URLs work in mobile context
- Provides Data Jar integration examples
- Focuses on accessibility and ease of use

### For Reddit Bibliophile  
- Generates URLs for book discovery and reading
- Maintains literary focus and ethical guidelines
- Provides contextual book recommendations
- Explains how URLs connect to reading experience

## 📱 iOS Shortcuts Integration Training

### URL Generation for Shortcuts
Teach how to create Shortcuts-friendly URLs:

```
Standard URL:
https://api.ashortstayinhell.com:5562/api/shortcuts/books/1847/page/1?api_key=YOUR_KEY

For iOS Shortcuts:
1. Base URL: "https://api.ashortstayinhell.com:5562/api/shortcuts/"
2. Path: "books/1847/page/1"
3. Parameters: "?api_key=" + [user's API key variable]
```

### Data Jar Integration
Help users create Data Jar objects:

```
Book Navigation Object:
{
  "book_id": "1847",
  "current_page": 1,
  "base_url": "https://api.ashortstayinhell.com:5562/api/shortcuts/books/1847/page/",
  "api_key": "[stored securely in user's Data Jar]"
}
```

## 🔄 Recursive Problem-Solving Training

### The Method
1. **Test** - Try the generated URL
2. **Verify** - Check if it works as expected  
3. **Fix** - If issues found, adjust approach
4. **Repeat** - Until 100% success

### Example Training Dialog
```
LLM: "Let me generate that URL for you..."
→ Creates URL
LLM: "Before we proceed, let me verify this works..."
→ Tests endpoint structure
LLM: "Perfect! Here's your working URL: [URL]"
→ Provides verified, functional URL
```

## 🎨 Personality Integration

### Lexi (UX Designer)
- Focuses on clean, accessible URL structures
- Explains mobile-first design principles
- Provides shortcuts optimization tips
- Emphasizes user experience in API navigation

### Reddit Bibliophile
- Maintains literary context in URL generation
- Provides book recommendations during navigation
- Explains how URLs connect to reading experience
- Keeps focus on books and learning

---
*Training guide for natural language API navigation - Security-first approach*