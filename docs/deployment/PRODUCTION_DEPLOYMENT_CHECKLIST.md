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

- [ ] **Start local API** on port 5001: `python src/api/production_api.py` (ensure PORT=5001 in local env)
- [ ] **Test all endpoints locally** - Verify basic functionality
- [ ] **Run pagination test script**: `./curl_pagination_tests.sh` (modify for localhost:5001)
- [ ] **Verify pagination works locally** - Confirm Page 1 ≠ Page 2 responses
- [ ] **Test database connectivity** - Ensure all queries work
- [ ] **Confirm 25/25 endpoints working locally** - All tests pass
- [ ] **Check for any local errors** - Review console output for issues
- [ ] **Verify authentication locally** - Test API key validation
- [ ] **Test search functionality locally** - Ensure vector search works

**LOCAL TESTING FAILURES = DEPLOYMENT BLOCKED**
- ❌ Any endpoint failing locally
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
- [ ] Set correct production API key: `***REMOVED***`
- [ ] Ensure path points to: `/Users/weixiangzhang/Local_Dev/LibraryOfBabel/src/api/production_api.py`

## **Step 4: Deploy via macOS Launch Agent**
- [ ] Copy updated plist: `cp config/macos/com.librarybabel.api.plist ~/Library/LaunchAgents/`
- [ ] Stop service: `launchctl unload ~/Library/LaunchAgents/com.librarybabel.api.plist`
- [ ] Start service: `launchctl load ~/Library/LaunchAgents/com.librarybabel.api.plist`

## **Step 5: Verify Deployment**
- [ ] Test health endpoint: `curl -s "https://api.ashortstayinhell.com:5562/api/shortcuts/health?api_key=***REMOVED***"`
- [ ] Test pagination: `curl -s "https://api.ashortstayinhell.com:5562/api/shortcuts/books/author-list?page=1&limit=5&api_key=***REMOVED***"`
- [ ] Verify timestamp shows recent deployment

## **Key Details**
- **Production URL:** `https://api.ashortstayinhell.com:5562`
- **Port:** 5562
- **API Key:** `***REMOVED***`
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