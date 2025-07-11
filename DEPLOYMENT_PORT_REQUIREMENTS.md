# 🚨 CRITICAL DEPLOYMENT PORT REQUIREMENTS

## LibraryOfBabel Production API Port Configuration

**MANDATORY PORT**: `5562` (NOT 8080)

### Background
- User has specified: "the port should be 55 something something"
- Production domain: `api.ashortstayinhell.com:5562` 
- This is a CRITICAL requirement that must be enforced in ALL deployments

### CI/CD Integration Required
This port requirement MUST be:
1. ✅ Documented in deployment checklists
2. ✅ Enforced in automated deployment scripts
3. ✅ Validated in pre-deployment tests
4. ✅ Part of backend team processes

### Code Location
- File: `/src/api/production_api.py`
- Line: `port=int(os.getenv('PORT', 5562))`
- Environment Variable: `PORT=5562`

### Teams Responsible
- Backend deployment team
- DevOps automation
- QA validation team
- Security team (SSL cert validation)

---
**NEVER USE PORT 8080 FOR PRODUCTION**
**ALWAYS USE PORT 5562**

Last Updated: 2025-07-11
Created by: Deployment coordination team response to user requirement