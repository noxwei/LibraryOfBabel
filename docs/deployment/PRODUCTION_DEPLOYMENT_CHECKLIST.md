# 🚀 Production Deployment Checklist

## **🚨 CRITICAL SECURITY PROTOCOL: LOCAL TESTING MANDATORY**

### **🔴 GOLDEN RULE: DO NOT PUSH UNTIL LOCAL IS TESTED**

**MANDATORY PRE-DEPLOYMENT SEQUENCE:**
1. ✅ **LOCAL TESTING FIRST** - All changes MUST work locally before any deployment
2. ✅ **COMPREHENSIVE LOCAL VERIFICATION** - Test all endpoints on localhost
3. ✅ **DATABASE FIXES VERIFIED LOCALLY** - Run test suites locally
4. ✅ **PAGINATION CONFIRMED LOCALLY** - Verify Page 1 ≠ Page 2 locally
5. ✅ **ONLY THEN** → Proceed to production deployment

---

## **Step 0: LOCAL TESTING (MANDATORY)**
**⚠️ NEVER Deploy If Local Testing Not Completed ⚠️**

- [ ] **Start local API** on port 9002: `python3 scripts/test_api_endpoints.py`
- [ ] **Test local endpoints**: `curl http://localhost:9002/api/v4/health`
- [ ] **Verify 5000+ books loaded**: Check logs for "📚 Knowledge Base: 5000 books"
- [ ] **Test API key auth**: `curl -H "API-Key: [TEST_API_KEY]" http://localhost:9002/api/v4/vector/search`
- [ ] **Database connectivity**: Ensure PostgreSQL knowledge_base connected
- [ ] **SSL certificate paths exist**: `/ssl/letsencrypt-config/live/api.ashortstayinhell.com/`
- [ ] **Network configuration verified**: Mac Mini IP = 10.0.0.13 (static)
- [ ] **Port forwarding confirmed**: Router forwarding 5562 → 10.0.0.13:5562
- [ ] **Firewall allowlist**: Python added to macOS Application Firewall

**LOCAL TESTING FAILURES = DEPLOYMENT BLOCKED**
- ❌ Any endpoint failing locally
- ❌ Wrong book count (not 5000+)
- ❌ Database connection failures
- ❌ Missing SSL certificates
- ❌ Network configuration issues

## **Step 0.5: NETWORK INFRASTRUCTURE CHECK**
**⚠️ CRITICAL: Verify External Access Capability ⚠️**

- [ ] **Mac Mini IP Static**: `ifconfig | grep "inet " | grep -v 127.0.0.1` shows 10.0.0.13
- [ ] **External IP Confirmed**: `curl ifconfig.me` shows 73.161.54.75
- [ ] **DNS A Record**: api.ashortstayinhell.com → 73.161.54.75
- [ ] **Router Port Forward**: 5562 external → 10.0.0.13:5562 internal
- [ ] **Firewall Allowlist**: Python permitted for incoming connections
- [ ] **SSL Certificates Valid**: Not expired, correct domain
- [ ] **Test External Access**: `curl http://73.161.54.75:5562` connects (may error but connects)
- ❌ Pagination not working locally  
- ❌ Database errors in local testing
- ❌ Authentication issues locally
- ❌ Search functionality broken locally

---

## **Step 1: Code Preparation**
- [ ] Work on fixes in `Shortcuts` branch locally
- [ ] Test all endpoints locally on port 5001
- [ ] Commit changes to `Shortcuts` branch
- [ ] Push to remote `Shortcuts` branch

## **Step 2: Merge to Main**
- [ ] `git checkout main`
- [ ] `git merge Shortcuts`

## **Step 3: Update Production Configuration**
- [ ] Edit `/config/macos/com.librarybabel.api.plist`
- [ ] Set correct production API key: `[REDACTED - babel_prod_*****]`
- [ ] Ensure path points to: `/Users/weixiangzhang/Local_Dev/LibraryOfBabel/src/api/production_api.py`

## **Step 4: Deploy via macOS Launch Agent**
- [ ] Copy updated plist: `cp config/macos/com.librarybabel.api.plist ~/Library/LaunchAgents/`
- [ ] Stop service: `launchctl unload ~/Library/LaunchAgents/com.librarybabel.api.plist`
- [ ] Start service: `launchctl load ~/Library/LaunchAgents/com.librarybabel.api.plist`

## **Step 5: Verify Deployment**
- [ ] Test health endpoint: `curl -s "https://api.ashortstayinhell.com:5562/api/shortcuts/health?api_key=[PROD_API_KEY]"`
- [ ] Test pagination: `curl -s "https://api.ashortstayinhell.com:5562/api/shortcuts/books/author-list?page=1&limit=5&api_key=[PROD_API_KEY]"`
- [ ] Verify timestamp shows recent deployment

## **Key Details**
- **Production URL:** `https://api.ashortstayinhell.com:5562`
- **Port:** 5562
- **API Key:** `[REDACTED - babel_prod_*****]`
- **Method:** Self-hosted via macOS Launch Agent
- **No external services:** (No Render, Heroku, etc.)

## **Security Notes**
- **🚨 MANDATORY: Complete Step 0 Local Testing before any deployment**
- **NEVER deploy untested code** - All changes must work locally first
- Always use production API key for production deployments
- Verify health check returns recent timestamp after deployment
- Test pagination to ensure database fixes are deployed
- Monitor logs at `/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/api.err.log`
- **Local testing prevents production failures and security vulnerabilities**

## **Emergency Shutdown**
To turn off production API:
```bash
launchctl unload ~/Library/LaunchAgents/com.librarybabel.api.plist
```

To restart production API:
```bash
launchctl load ~/Library/LaunchAgents/com.librarybabel.api.plist
```

---
**Created:** 2025-07-19  
**Last Updated:** 2025-07-19  
**Version:** 2.0 - **CRITICAL SECURITY UPDATE: MANDATORY LOCAL TESTING**