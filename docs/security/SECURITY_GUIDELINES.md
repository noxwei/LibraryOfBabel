# 🔒 Security Guidelines for Contributors

## 🚨 Critical Security Rules

### 1. **Never Commit Sensitive Data**
- ❌ **NEVER** commit API keys, passwords, or secrets
- ❌ **NEVER** commit SSL certificates or private keys
- ❌ **NEVER** commit environment files with real credentials
- ❌ **NEVER** commit personal data or user information

### 2. **Use Environment Variables**
- ✅ Store all secrets in environment variables
- ✅ Use `.env` files for local development (already in .gitignore)
- ✅ Use placeholder values in example files

### 3. **File Naming Conventions**
- ✅ Use descriptive names that don't contain sensitive terms
- ✅ Avoid files with names like `secret.json`, `password.txt`, etc.

## 📁 Protected File Types

The following file types are automatically ignored by `.gitignore`:

```
# Environment files
.env*
*.env

# SSL/TLS certificates
*.pem
*.key
*.crt
*.p12
*.pfx

# API keys and secrets
*api_key*
*API_KEY*
*secret*
*SECRET*
*password*
*PASSWORD*
*token*
*TOKEN*

# Personal data
*weixiangzhang*
*linda_zhang*
*personal*
*identity*
```

## 🛠️ Development Workflow

### Setting Up Environment Variables

1. **Create a local environment file:**
   ```bash
   cp .env.example .env.local
   ```

2. **Add your secrets to `.env.local`:**
   ```bash
   API_KEY=your_actual_api_key_here
   DB_PASSWORD=your_database_password
   ```

3. **Use environment variables in code:**
   ```python
   import os
   api_key = os.getenv('API_KEY')
   ```

### Testing Security

1. **Run the pre-commit hook manually:**
   ```bash
   .git/hooks/pre-commit
   ```

2. **Check for sensitive files:**
   ```bash
   find . -name "*.env*" -o -name "*.pem" -o -name "*.key"
   ```

3. **Scan for hardcoded secrets:**
   ```bash
   grep -r "babel_secure_" src/
   grep -r "API_KEY=" src/
   ```

## 🔍 Security Checklist

Before committing, ensure:

- [ ] No `.env` files are staged
- [ ] No SSL certificates are staged
- [ ] No hardcoded secrets in code
- [ ] No personal data in commits
- [ ] Pre-commit hook passes
- [ ] Environment variables are used for all secrets

## 🚨 Emergency Procedures

### If You Accidentally Commit Sensitive Data

1. **Immediately remove the file from git history:**
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch path/to/sensitive/file' \
   --prune-empty --tag-name-filter cat -- --all
   ```

2. **Force push to remove from remote:**
   ```bash
   git push origin --force --all
   ```

3. **Rotate any exposed credentials immediately**

4. **Notify the security team**

### If You Find Exposed Secrets

1. **Don't commit the fix with the secret still visible**
2. **Remove the secret from git history first**
3. **Then commit the fix**

## 📞 Security Contacts

- **Security Issues:** Create an issue with the `security` label
- **Emergency:** Contact the repository maintainer immediately
- **Questions:** Ask in the security channel or create a discussion

## 🔄 Regular Security Practices

### Monthly Security Review
- [ ] Review all environment files
- [ ] Check for new sensitive file types
- [ ] Update .gitignore if needed
- [ ] Rotate API keys and passwords
- [ ] Review access permissions

### Quarterly Security Audit
- [ ] Full repository scan for secrets
- [ ] Review git history for exposed data
- [ ] Update security guidelines
- [ ] Train team on security practices

## 📚 Additional Resources

- [GitHub Security Best Practices](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Environment Variable Best Practices](https://12factor.net/config)

---

**Remember:** Security is everyone's responsibility. When in doubt, ask before committing! 