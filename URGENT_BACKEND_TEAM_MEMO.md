# 🚨 URGENT MEMO: Backend Deployment Teams

## TO: All Backend Deployment Teams  
## FROM: AI Agent Deployment Coordination  
## RE: MANDATORY Port Configuration Change  
## DATE: 2025-07-11  

---

## CRITICAL ACTION REQUIRED

**User has mandated**: Production API must use port **5562** (NOT 8080)

### Current Problem
- Production API failing due to wrong port (8080)
- User frustrated having to remind team repeatedly
- Core agents blocked from deployment to `api.ashortstayinhell.com`

### IMMEDIATE ACTIONS REQUIRED

#### 1. Backend Teams - Identify Primary Deploy Engineer
**WHO typically handles production deployments for LibraryOfBabel?**
- [ ] Team Lead name: ________________
- [ ] Primary deployment engineer: ________________  
- [ ] Secondary/backup engineer: ________________

#### 2. CI/CD Process Updates REQUIRED
- [ ] Update deployment scripts to enforce port 5562
- [ ] Add port validation to pre-deployment checks
- [ ] Update Docker configurations (if used)
- [ ] Update environment variable defaults
- [ ] Add automated port testing

#### 3. Documentation Updates REQUIRED  
- [ ] Update PRODUCTION-DEPLOYMENT-CHECKLIST.md
- [ ] Add port requirement to CI/CD pipeline docs
- [ ] Update README deployment instructions
- [ ] Create automated deployment script templates

#### 4. Validation Requirements
- [ ] Test deployment with port 5562
- [ ] Verify SSL works with new port
- [ ] Confirm api.ashortstayinhell.com:5562 accessibility
- [ ] Test all agent endpoints

### CODE CHANGES ALREADY MADE
✅ Fixed `/src/api/production_api.py` line 2422:
```python
# OLD (WRONG)
port=int(os.getenv('PORT', 8080))

# NEW (CORRECT) 
port=int(os.getenv('PORT', 5562))
```

### DEPLOYMENT CHECKLIST ADDITIONS
Add to ALL future deployment checklists:
- [ ] ✅ Verify PORT environment variable = 5562
- [ ] ✅ Confirm production API runs on port 5562  
- [ ] ✅ Test HTTPS access: `https://api.ashortstayinhell.com:5562`
- [ ] ✅ Validate SSL certificate for port 5562

---

## ESCALATION PATH
If this is not resolved within 24 hours:
1. Escalate to senior backend team lead
2. Involve DevOps automation team  
3. Update all CI/CD templates permanently

## EXPECTED OUTCOME
- No more manual port corrections needed
- Automated enforcement in deployment pipeline
- User never has to remind team about port again

---
**RESPOND WITH:**
1. Name of primary deployment engineer
2. ETA for CI/CD process updates  
3. Confirmation of checklist integration

**PRIORITY: CRITICAL - DO NOT DELAY**