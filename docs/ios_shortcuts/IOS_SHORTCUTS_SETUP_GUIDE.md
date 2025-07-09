# 📱 iOS Shortcuts Setup Guide for LibraryOfBabel

**Connect Lexi to Siri and iOS Shortcuts for voice-powered book research**

## 🎯 Quick Start

### **Step 1: Get Your API Key**
1. Contact your LibraryOfBabel administrator for an API key
2. Your API key provides secure access to 363 books and 34M+ words
3. Keep your API key secure - never share it publicly

### **Step 2: Create iOS Shortcut**

#### **Basic Shortcut Setup**
1. Open **Shortcuts** app on iPhone/iPad
2. Tap **+** to create new shortcut
3. Add the following actions:

#### **Action 1: Get Text from Input**
- Action: **Get Text from Input**
- Source: **Shortcut Input**
- Input Type: **Text**

#### **Action 2: Get Contents of URL**
- Action: **Get Contents of URL**
- URL: `https://your-domain.com/api/v3/ollama/ios/chat`
- Method: **POST**
- Headers:
  - `Content-Type`: `application/json`
  - `Authorization`: `Bearer YOUR_API_KEY_HERE`
- Request Body: 
```json
{
  "query": "[Text from previous action]",
  "context": "mobile_ios_shortcuts",
  "max_length": 280,
  "compact": true
}
```

#### **Action 3: Get Value from Dictionary**
- Action: **Get Value from Dictionary**
- Dictionary: **Contents of URL**
- Key: **response**

#### **Action 4: Speak Text**
- Action: **Speak Text**
- Text: **Dictionary Value**
- Voice: **Siri Voice**

### **Step 3: Configure Siri**
1. In Shortcut settings, tap **"Add to Siri"**
2. Record phrase: **"Hey Siri, ask LibraryOfBabel"**
3. Test with: *"Hey Siri, ask LibraryOfBabel about artificial intelligence"*

---

## 🔧 Advanced Configuration

### **Enhanced Shortcut with Intent Routing**

Add after **Get Contents of URL**:

#### **Get intentLabel for Conditional Actions**
- Action: **Get Value from Dictionary**
- Dictionary: **Contents of URL**
- Key: **shortcuts_data.intent**

#### **Conditional Actions by Intent**
- Action: **If**
- Input: **Dictionary Value**
- Condition: **is** `recommend`
- Then: **Speak Text**: "Here are my book recommendations: [response]"

### **Custom Response Lengths**

Modify Request Body for different scenarios:

#### **Brief Voice Response (Twitter-length)**
```json
{
  "query": "[Text]",
  "context": "siri_voice",
  "max_length": 140,
  "compact": true
}
```

#### **Detailed Research Response**
```json
{
  "query": "[Text]",
  "context": "detailed_research",
  "max_length": 500,
  "compact": false,
  "use_ollama": true
}
```

### **Multiple Shortcuts for Different Use Cases**

#### **"Quick Book Search"**
- Siri Phrase: *"Quick book search"*
- max_length: 180
- compact: true

#### **"Research Assistant"**
- Siri Phrase: *"Research assistant"*
- max_length: 400
- compact: false
- use_ollama: true

#### **"Book Recommendations"**
- Siri Phrase: *"Recommend books"*
- Prepend query with: "recommend books about"

---

## 📊 Response Format

### **Standard Response Structure**
```json
{
  "success": true,
  "agent": "lexi_voice_mode",
  "response": "📖 Found in \"AI Book\" by Author: content...",
  "intentLabel": "search",
  "metadata": {
    "processing_time_ms": 45,
    "results_count": 3,
    "knowledge_base_size": "363 books"
  },
  "shortcuts_data": {
    "intent": "search",
    "has_results": true,
    "can_follow_up": true,
    "voice_optimized": true
  }
}
```

### **Using intentLabel for Conditional Logic**

Intent types and suggested actions:

- **search**: Present results, offer follow-up
- **recommend**: List recommendations, ask for preferences
- **explain**: Provide definition, offer deeper exploration
- **summary**: Give brief overview, offer full details
- **compare**: Show differences, ask for more comparisons
- **quote**: Share passage, offer related quotes
- **help**: Provide instructions, show available commands
- **error**: Handle gracefully, suggest rephrasing

---

## 🎤 Voice Optimization Tips

### **Siri Phrase Examples**
- *"Hey Siri, ask LibraryOfBabel about [topic]"*
- *"Hey Siri, find books about [subject]"*
- *"Hey Siri, what does LibraryOfBabel say about [concept]"*
- *"Hey Siri, recommend books on [topic]"*

### **Query Optimization for Voice**
- Use natural language: "books about AI" vs "artificial intelligence books"
- Include context: "philosophy books about consciousness"
- Be specific: "modern science fiction novels"
- Ask follow-ups: "more books like that"

### **Response Length Guidelines**
- **Siri Voice**: 140-180 characters (Twitter-length)
- **Screen Display**: 280-350 characters (SMS-length)
- **Detailed Research**: 400-500 characters (paragraph)

---

## 🔒 Security Best Practices

### **API Key Protection**
- Never share your API key publicly
- Use environment variables in automation
- Rotate keys regularly
- Monitor usage in logs

### **Network Security**
- Always use HTTPS endpoints
- Validate SSL certificates
- Use latest iOS/Shortcuts versions
- Monitor for suspicious activity

### **Privacy Considerations**
- Queries are logged for improvement
- No personal data is stored
- All searches are academic/research focused
- Delete shortcut history if needed

---

## 🚀 Testing Your Setup

### **Test Queries**
1. **"find books about artificial intelligence"**
   - Expected: Search results with AI books
   - intentLabel: "search"

2. **"recommend philosophy books"**
   - Expected: Book recommendations
   - intentLabel: "recommend"

3. **"explain quantum physics"**
   - Expected: Educational content
   - intentLabel: "explain"

### **Troubleshooting**

#### **403 Forbidden Error**
- Check API key format: `Bearer YOUR_API_KEY`
- Verify API key is active
- Confirm URL is correct

#### **Empty Response**
- Check network connection
- Verify JSON request format
- Test with simpler query

#### **Siri Not Responding**
- Re-record Siri phrase
- Check Shortcuts permissions
- Restart Shortcuts app

---

## 📚 Example Shortcuts

### **Academic Research Shortcut**
```
Name: "Academic Research"
Siri Phrase: "Research [topic]"
```

1. **Ask for Input**: "What topic to research?"
2. **Get Contents of URL**: API call with research context
3. **Get Value**: Extract response
4. **Show Result**: Display full response
5. **Speak Text**: Read key findings

### **Quick Book Finder**
```
Name: "Quick Book Finder"
Siri Phrase: "Find books about [topic]"
```

1. **Text Input**: Topic from Siri
2. **API Call**: Quick search format
3. **Speak Response**: Voice-optimized result

### **Reading Recommendations**
```
Name: "Book Recommendations"
Siri Phrase: "Recommend books"
```

1. **Ask for Input**: "What genre or topic?"
2. **Text Processing**: Add "recommend" prefix
3. **API Call**: Recommendation context
4. **Conditional Response**: Handle different recommendation types

---

## 🔄 Updates and Maintenance

### **Regular Updates**
- Update API endpoint URL if changed
- Refresh API key when notified
- Update shortcuts when new features added
- Test functionality after iOS updates

### **Feature Requests**
- New intent types for specialized queries
- Enhanced voice optimization
- Multi-language support
- Advanced search filters

---

## 💡 Pro Tips

### **Advanced Usage**
- Chain multiple queries for research sessions
- Use variables to remember context
- Create topic-specific shortcuts
- Integrate with note-taking apps

### **Workflow Integration**
- Add to morning routine shortcuts
- Include in study session automations
- Connect to calendar for research reminders
- Link with reading list apps

### **Voice Command Optimization**
- Use consistent phrasing
- Practice natural speech patterns
- Set up multiple trigger phrases
- Test in different environments

---

**🎭 Powered by Lexi - Your AI Librarian**  
*363 books • 34M+ words • Instant voice access*

---

*Last updated: 2025-07-09*  
*Version: iOS Shortcuts v1.0*  
*Support: Check agent logs for troubleshooting*