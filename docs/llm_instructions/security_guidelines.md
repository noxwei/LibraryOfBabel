# 🔒 LLM Security Guidelines

## 🚨 Critical Security Rules

### ❌ NEVER Include in Documentation or Responses
- Actual API keys
- Production credentials
- Server URLs with embedded keys
- Environment variables with real values
- Database connection strings

### ✅ Always Use in Examples
- Placeholder text: `YOUR_API_KEY`
- Template URLs: `?api_key=YOUR_KEY`
- Generic examples: `api_key=your_production_key_here`
- Environment variables: `${API_KEY}` or `$API_KEY`

## 🔐 API Key Handling

### For Documentation
```markdown
# ✅ Correct Example
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/health?api_key=YOUR_API_KEY"

# ❌ NEVER Do This
curl "https://api.ashortstayinhell.com:5562/api/shortcuts/health?api_key=***REMOVED***"
```

### For User Interactions
```
User: "How do I use the API?"
LLM Response: "You'll need to include your API key like this: ?api_key=YOUR_API_KEY
Please replace YOUR_API_KEY with the actual key provided to you."
```

## 🛡️ LLM Training Security

### When Training Lexi or Reddit Bibliophile
1. **Use sanitized examples** - No real credentials
2. **Teach security awareness** - Explain why keys must be protected
3. **Provide templates** - Show proper placeholder usage
4. **Test with dummy data** - Never use production keys in training

### Response Patterns
```
# ✅ Secure Response Pattern
"Here's how to access the book list:
https://api.ashortstayinhell.com:5562/api/shortcuts/books/title-list?api_key=YOUR_API_KEY

Remember to replace YOUR_API_KEY with your actual key."

# ❌ Insecure Response Pattern  
"Here's the direct link: [URL with embedded production key]"
```

## 📚 Documentation Standards

### File Naming
- Use `.example` for templates with placeholders
- Keep actual config files out of documentation
- Use generic examples in public docs

### Content Guidelines
- Always explain security context
- Provide setup instructions without exposing secrets
- Use environment variable patterns
- Include security warnings

## 🎯 Training Verification

### Security Checklist for LLM Training
- [ ] No production API keys in training materials
- [ ] Placeholder usage demonstrated correctly
- [ ] Security awareness included in personality
- [ ] Proper template patterns taught
- [ ] Verification steps included in responses

### Response Quality Test
```
Test Question: "How do I get book data from the API?"
Expected Response Elements:
✅ Placeholder API key usage
✅ Clear security explanation  
✅ Template URL structure
✅ User instruction to replace placeholders
❌ No actual production credentials
```

## 🔄 Incident Response

### If API Keys Are Accidentally Exposed
1. **Immediate**: Remove/edit the content
2. **Rotate**: Change the exposed API key
3. **Review**: Check all documentation for similar issues
4. **Update**: Improve training to prevent recurrence

### Prevention Measures
- Regular security audits of documentation
- Automated scanning for credential patterns
- LLM response monitoring for accidental exposure
- Clear separation of training and production environments

---
*Security-first approach to LLM training and documentation*