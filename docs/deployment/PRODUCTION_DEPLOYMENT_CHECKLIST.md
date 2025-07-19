# 🚀 Production Deployment Checklist

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
- Always use production API key for production deployments
- Verify health check returns recent timestamp after deployment
- Test pagination to ensure database fixes are deployed
- Monitor logs at `/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/api.err.log`

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
**Version:** 1.0