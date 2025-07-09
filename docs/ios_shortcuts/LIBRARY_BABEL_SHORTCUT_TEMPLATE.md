# 📱 LibraryOfBabel iOS Shortcuts Integration

## 🚀 **"Hey Siri, Ask LibraryOfBabel"** - Mobile Research Revolution

Transform your iPhone into a powerful research assistant with instant access to 363 books and 34+ million words through Ollama Llama3 7B powered natural language processing!

---

## 🎯 **Quick Setup Guide**

### **Step 1: Get Your API Key**
1. Contact your LibraryOfBabel admin for your personal API key
2. Save it securely (you'll need it for the shortcut)

### **Step 2: Create the iOS Shortcut**

#### **Basic Shortcut Configuration**
1. **Open Shortcuts app** on your iPhone
2. **Tap "+" to create new shortcut**
3. **Add these actions in order:**

#### **Action 1: Get Text Input**
- **Action**: "Ask for Input"
- **Input Type**: Text
- **Prompt**: "What would you like to research?"
- **Allow Multiple Lines**: ON
- **Default Answer**: (leave empty)

#### **Action 2: Create Request Body**
- **Action**: "Get Contents of URL"
- **URL**: `https://your-api-domain.com/api/v3/ollama/ios/chat`
- **Method**: POST
- **Headers**:
  - `Content-Type`: `application/json`
  - `Authorization`: `Bearer YOUR_API_KEY_HERE`
- **Request Body** (JSON):
```json
{
  "query": "[Insert Ask for Input result here]",
  "context": "mobile_ios_shortcuts",
  "session_id": "ios_[current_time]"
}
```

#### **Action 3: Parse Response**
- **Action**: "Get Dictionary from Input"
- **Input**: [Result from URL request]

#### **Action 4: Display Results**
- **Action**: "Show Result"
- **Text**: 
```
📚 LibraryOfBabel Response:

🤖 Agent: [Dictionary Value: agent_name]

💬 Response: [Dictionary Value: response]

📊 Found: [Dictionary Value: total_books_found] books

⏱️ Response Time: [Dictionary Value: performance.response_time]s

🔗 Powered by Ollama Llama3 7B
```

---

## 🎤 **Voice Activation Setup**

### **Enable "Hey Siri" Integration**
1. **In Shortcuts app**, tap your new shortcut
2. **Tap "Add to Siri"**
3. **Record phrase**: "Ask LibraryOfBabel" or "Research question"
4. **Test**: "Hey Siri, Ask LibraryOfBabel"

### **Suggested Voice Commands**
- "Hey Siri, Ask LibraryOfBabel about AI consciousness"
- "Hey Siri, Research question about philosophy"
- "Hey Siri, LibraryOfBabel search"

---

## 🔧 **Advanced Configuration**

### **Complete Shortcut Template (Copy-Paste Ready)**

```
Shortcut Name: LibraryOfBabel Research
Description: AI-powered research across 363 books with Ollama Llama3 7B

Actions:
1. Ask for Input
   - Prompt: "What would you like to research in our 363-book library?"
   - Input Type: Text
   - Allow Multiple Lines: ON

2. Text Action
   - Text: {
     "query": "[Provided Input]",
     "context": "mobile_ios_shortcuts",
     "session_id": "ios_[Current Date]"
   }

3. Get Contents of URL
   - URL: https://your-domain.com/api/v3/ollama/ios/chat
   - Method: POST
   - Headers:
     - Content-Type: application/json
     - Authorization: Bearer YOUR_API_KEY
   - Request Body: [Text from Action 2]

4. Get Dictionary from Input
   - Input: [Contents of URL]

5. Get Dictionary Value
   - Dictionary: [Dictionary from previous action]
   - Key: response

6. Get Dictionary Value
   - Dictionary: [Dictionary from action 4]
   - Key: total_books_found

7. Get Dictionary Value
   - Dictionary: [Dictionary from action 4]
   - Key: performance.response_time

8. Text Action
   - Text: 📚 LibraryOfBabel Research Results

🤖 u/DataScientistBookworm says:
[Dictionary Value from Action 5]

📊 Found [Dictionary Value from Action 6] books
⏱️ Response: [Dictionary Value from Action 7] seconds

🧠 Powered by Ollama Llama3 7B
🔍 Searching 363 books with 34M+ words

9. Show Result
   - Text: [Text from Action 8]

10. Copy to Clipboard (Optional)
    - Text: [Text from Action 8]
```

---

## 🌟 **Example Queries**

### **Philosophy & AI**
- "Books about artificial intelligence and consciousness"
- "What does Foucault say about surveillance?"
- "Find connections between Buddhism and modern technology"

### **Social Theory**
- "Show me books about social justice movements"
- "Critical race theory and technology intersections"
- "Climate change policy solutions"

### **Literature & Culture**
- "Octavia Butler's approach to social change"
- "Science fiction that explores identity"
- "Books that bridge science and spirituality"

### **Research & Academic**
- "Find citations for digital surveillance theory"
- "Compare different authors on post-structuralism"
- "Books for interdisciplinary research methods"

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **"Network Error" or "Request Failed"**
- Check your internet connection
- Verify API key is correctly formatted
- Ensure URL is correct (no extra spaces)

#### **"Unauthorized" Error**
- Check API key in Authorization header
- Verify Bearer token format: `Bearer YOUR_API_KEY`
- Contact admin for API key validation

#### **"Query Too Long" Error**
- Limit queries to 500 characters
- Break complex questions into smaller parts
- Try more specific search terms

#### **Slow Response Times**
- Normal: 2-3 seconds for complex queries
- Network dependent: Check WiFi/cellular
- Ollama processing: May take longer for complex analysis

### **Performance Tips**
1. **Specific queries** get better results than general ones
2. **Author names** trigger specialized search strategies
3. **Concept combinations** work well (e.g., "AI + ethics")
4. **Follow-up questions** leverage session memory

---

## 🔒 **Security & Privacy**

### **Data Protection**
- All queries processed locally via Ollama
- No data sent to external AI services
- Session data stored temporarily
- API key encrypted in iOS keychain

### **Best Practices**
- Keep API key secure
- Don't share shortcuts with embedded keys
- Use specific device authentication
- Monitor API usage in logs

---

## 📊 **Response Format**

### **Typical iOS Response Structure**
```json
{
  "success": true,
  "agent": "reddit_bibliophile",
  "agent_name": "u/DataScientistBookworm",
  "response": "yo! found 5 solid books for 'AI consciousness' 🔥 quality > quantity, and these are all bangers! 📖",
  "query": "AI consciousness",
  "session_id": "ios_session_1720507200",
  "mobile_optimized": true,
  "ios_shortcuts_compatible": true,
  "search_results": [...],
  "total_books_found": 5,
  "memory_updated": true,
  "ollama_powered": true,
  "performance": {
    "response_time": 2.45,
    "target_met": true
  },
  "timestamp": "2025-07-09T09:00:00Z",
  "next_actions": [
    "📖 Tap a book title to read more details",
    "🔍 Ask follow-up questions about specific concepts",
    "📚 Request book recommendations based on these results"
  ]
}
```

---

## 🎉 **Advanced Features**

### **Session Continuity**
- Shortcut remembers context across queries
- Follow-up questions work naturally
- Agent personality maintained throughout session

### **Multiple Search Strategies**
- Semantic search for concepts
- Author-focused searches
- Topic-based exploration
- Cross-reference discovery

### **Mobile Optimization**
- Responses formatted for mobile screens
- Highlighted text for key passages
- Emoji indicators for better readability
- Quick action suggestions

---

## 🚀 **What's Next?**

### **Upcoming Features**
- Voice-to-text query optimization
- Offline caching for frequently accessed books
- Custom agent personality selection
- Integration with Notes app for research saving

### **Advanced Shortcuts**
- Book recommendation shortcut
- Citation generator
- Research note compiler
- Reading list manager

---

## 🤝 **Support & Community**

### **Getting Help**
- Check logs at `/api/v3/logs` for troubleshooting
- Contact your LibraryOfBabel administrator
- Join the researcher community for tips

### **Contributing**
- Share successful shortcut configurations
- Report bugs and suggest improvements
- Help test new features

---

**🎯 Transform your iPhone into a mobile research powerhouse! Access 363 books with 34+ million words through natural language queries powered by Ollama Llama3 7B - all through simple voice commands!**

*Built with ❤️ by the LibraryOfBabel team*  
*Coordinated by Linda Zhang (张丽娜) - HR Manager*  
*Powered by Reddit Bibliophile agent & Ollama Llama3 7B*