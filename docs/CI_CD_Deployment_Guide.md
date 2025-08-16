# LibraryOfBabel CI/CD Deployment Guide

## 🎯 Overview

Complete CI/CD pipeline using GitHub Actions self-hosted runner with LaunchAgent daemon management for zero-downtime blue-green deployments.

## 🏗️ Architecture

```
Local Dev → Staging (5568) → Production (5562)
     ↓          ↓                ↓
  Direct    Wildcard SSL   Production SSL  
   Test      Testing       Live Traffic
```

## 🔧 Components

### 1. **GitHub Actions Self-Hosted Runner**
- Runs directly on your Mac
- Access to real database, SSL certificates, Ollama
- No Docker complexity - matches production exactly

### 2. **Environment Setup**
- **Local**: `localhost:5561` (development)
- **Staging**: `staging.ashortstayinhell.com:5568` (QA testing)
- **Production**: `api.ashortstayinhell.com:5562` (live API)

### 3. **SSL Configuration**
- **Wildcard cert**: `*.ashortstayinhell.com` (staging + future subdomains)
- **Production cert**: `api.ashortstayinhell.com` (existing, unchanged)

### 4. **Database Migrations**
- **Flyway**: Automated SQL migration system
- **Function backup**: Automatic backup before deployments
- **Rollback capability**: Restore functions if needed

## 🚀 Workflows

### 1. **Staging Deployment** (`staging-deployment.yml`)
**Triggers:** Push to main/dev/staging branches
**Steps:**
1. Security pre-checks
2. Database migrations with Flyway
3. Stop existing staging server
4. Start staging with wildcard SSL
5. Health checks and validation
6. JIRA status update

### 2. **Production Deployment** (`production-deployment.yml`)
**Triggers:** Manual dispatch only
**Steps:**
1. Pre-production validation
2. Staging health verification
3. Graceful production shutdown (LaunchAgent)
4. Configuration backup
5. Start production daemon
6. Health checks and API validation
7. Rollback capability if failed

### 3. **QA Validation** (`qa-validation.yml`)
**Triggers:** Manual dispatch or after staging deployment
**Test Suites:**
- **Smoke Tests**: Critical endpoints (80% success required)
- **Comprehensive Tests**: All endpoints (90% success required)
- **Performance Tests**: Response time validation (<2000ms target)
- **Security Tests**: Auth, injection protection, HTTPS

## 📋 Setup Instructions

### 1. **Install GitHub Actions Runner**
```bash
cd /Users/weixiangzhang/Local_Dev/LibraryOfBabel
./setup_github_runner.sh
```

### 2. **Configure Runner**
1. Go to GitHub repo → Settings → Actions → Runners
2. Click "New self-hosted runner"
3. Copy and run the config command
4. Start runner: `cd /Users/weixiangzhang/actions-runner && ./run.sh`

### 3. **LaunchAgent Setup**
**Production:**
```bash
# Enable production daemon
cp ~/Library/LaunchAgents/com.librarybabel.api.plist.disabled \
   ~/Library/LaunchAgents/com.librarybabel.api.plist
launchctl load ~/Library/LaunchAgents/com.librarybabel.api.plist
```

**Staging:** (Already configured)
```bash
# Staging daemon ready to use
ls ~/Library/LaunchAgents/com.librarybabel.staging.plist
```

### 4. **Database Migration Setup**
```bash
# Apply function backup migration
cd flyway
flyway -configFiles=conf/flyway.conf migrate
```

## 🔄 Deployment Flow

### **Standard Deployment Process:**

1. **Code Push** → Triggers staging deployment
2. **Staging Validation** → Runs automated QA tests
3. **Manual Review** → Verify staging environment
4. **Production Deployment** → Manual trigger with approval
5. **Post-deployment** → Monitor and validate

### **Emergency Rollback:**

1. **Stop Production**: `launchctl stop com.librarybabel.api`
2. **Restore Functions**: Use Flyway rollback or function backup
3. **Restart**: `launchctl start com.librarybabel.api`

## 🛡️ Safety Features

### **Pre-deployment Checks:**
- Security scans for hardcoded secrets
- Database connectivity validation
- SSL certificate verification
- Function dependency checks

### **Deployment Safety:**
- Graceful shutdown with process monitoring
- Configuration backups before changes
- Health checks with retry logic
- Automatic rollback on failure

### **Quality Gates:**
- 80% success rate for smoke tests
- 90% success rate for comprehensive tests
- 2000ms response time limits
- Security validation requirements

## 📊 Monitoring

### **JIRA Integration:**
- Automatic status updates for SCRUM-109
- Deployment reports with metrics
- QA validation results
- Rollback notifications

### **Log Locations:**
- **Production**: `logs/api.out.log`, `logs/api.err.log`
- **Staging**: `logs/staging.out.log`, `logs/staging.err.log`
- **Runner**: `/Users/weixiangzhang/actions-runner/_diag/`

## 🔍 Troubleshooting

### **Common Issues:**

**Runner Not Starting:**
```bash
cd /Users/weixiangzhang/actions-runner
./config.sh remove  # Remove old config
# Re-run setup from GitHub
```

**Staging SSL Issues:**
```bash
# Check wildcard certificate
openssl x509 -in ssl/letsencrypt-config/live/wildcard-ashortstayinhell/fullchain.pem -text -noout
```

**Production Daemon Issues:**
```bash
# Check daemon status
launchctl list | grep librarybabel

# View logs
tail -f logs/api.err.log
```

**Database Migration Failures:**
```bash
# Check migration status
psql -d knowledge_base -c "SELECT * FROM flyway_schema_history ORDER BY installed_on DESC LIMIT 5;"

# Restore functions if needed
psql -d knowledge_base -c "SELECT function_backups.restore_functions_from_backup(1);"
```

## 🎯 Next Steps

1. **Setup Runner**: Install and configure GitHub Actions runner
2. **Test Staging**: Trigger staging deployment workflow
3. **Run QA**: Execute QA validation suite
4. **Deploy Production**: Manual production deployment
5. **Monitor**: Watch logs and metrics

## 📞 Support

- **Logs**: Check respective log files
- **JIRA**: SCRUM-109 for deployment tracking
- **Rollback**: Use backup functions or LaunchAgent restart

---

**CI/CD Pipeline Status**: ✅ Ready for deployment
**Last Updated**: August 16, 2025
**Pipeline Version**: v1.0 (LaunchAgent + Self-hosted runner)