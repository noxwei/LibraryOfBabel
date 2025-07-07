# Service Management Guide

## LibraryOfBabel macOS Launch Agent Management

This guide covers managing the LibraryOfBabel API as a macOS service using Launch Agents.

## Service Overview

### **Active Services**
1. **Main API Service** - `com.librarybabel.api`
2. **Certificate Renewal** - `com.librarybabel.certrenew`
3. **Health Monitoring** - `com.librarybabel.healthcheck`

### **Service Locations**
```
/Users/username/Library/LaunchAgents/com.librarybabel.api.plist
/Users/username/Library/LaunchAgents/com.librarybabel.certrenew.plist
/Users/username/Library/LaunchAgents/com.librarybabel.healthcheck.plist
```

## Basic Service Commands

### **Service Control**
```bash
# Start the API service
launchctl start com.librarybabel.api

# Stop the API service
launchctl stop com.librarybabel.api

# Restart the API service
launchctl stop com.librarybabel.api
sleep 2
launchctl start com.librarybabel.api

# Check service status
launchctl list | grep librarybabel
```

### **Service Installation**
```bash
# Load all services (first-time setup)
launchctl load "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
launchctl load "/Users/username/Library/LaunchAgents/com.librarybabel.certrenew.plist"
launchctl load "/Users/username/Library/LaunchAgents/com.librarybabel.healthcheck.plist"

# Unload all services (for maintenance)
launchctl unload "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
launchctl unload "/Users/username/Library/LaunchAgents/com.librarybabel.certrenew.plist"
launchctl unload "/Users/username/Library/LaunchAgents/com.librarybabel.healthcheck.plist"
```

## Log Management

### **Log File Locations**
```
/path/to/LibraryOfBabel/logs/api.log              # Main API output
/path/to/LibraryOfBabel/logs/api-error.log        # API errors
/path/to/LibraryOfBabel/logs/cert-renewal.log     # Certificate renewals
/path/to/LibraryOfBabel/logs/health-check.log     # Health monitoring
```

### **Log Monitoring Commands**
```bash
# Real-time API logs
tail -f "/path/to/LibraryOfBabel/logs/api.log"

# Real-time error logs
tail -f "/path/to/LibraryOfBabel/logs/api-error.log"

# Recent health checks
tail -20 "/path/to/LibraryOfBabel/logs/health-check.log"

# Certificate renewal history
tail -20 "/path/to/LibraryOfBabel/logs/cert-renewal.log"

# All logs combined
tail -f /path/to/LibraryOfBabel/logs/*.log
```

### **Log Analysis**
```bash
# Count errors in last 24 hours
grep "$(date +%Y-%m-%d)" /path/to/LibraryOfBabel/logs/api-error.log | wc -l

# Find recent API starts
grep "Starting LibraryOfBabel" /path/to/LibraryOfBabel/logs/api.log

# Check health check failures
grep "failed" /path/to/LibraryOfBabel/logs/health-check.log

# Find certificate renewals
grep "renewal successful" /path/to/LibraryOfBabel/logs/cert-renewal.log
```

## Health Monitoring

### **Service Status Check**
```bash
# Check if services are running
launchctl list | grep librarybabel

# Expected output:
# 12345   0   com.librarybabel.api
# 12346   0   com.librarybabel.certrenew
# 12347   0   com.librarybabel.healthcheck
```

### **API Availability Check**
```bash
# Test API endpoint
curl -s https://api.yourdomain.com:5562/api/secure/info | jq .success

# Test with authentication
curl -s -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.yourdomain.com:5562/api/secure/books/search-across?q=test | jq .success

# Check SSL certificate
openssl s_client -connect api.yourdomain.com:5562 -servername api.yourdomain.com < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

### **Performance Monitoring**
```bash
# API response time test
time curl -s https://api.yourdomain.com:5562/api/secure/info > /dev/null

# Check system resources
ps aux | grep secure_book_api  # Memory and CPU usage
lsof -i :5562                 # Port usage
```

## Certificate Management

### **Certificate Status**
```bash
# Check certificate expiry
openssl x509 -in /path/to/LibraryOfBabel/ssl/letsencrypt-config/live/api.yourdomain.com/fullchain.pem -noout -dates

# List all certificates
certbot certificates --config-dir /path/to/LibraryOfBabel/ssl/letsencrypt-config

# Check certificate validity
curl -vI https://api.yourdomain.com:5562 2>&1 | grep -E "(certificate|SSL)"
```

### **Manual Certificate Renewal**
```bash
# Run renewal script
/path/to/LibraryOfBabel/scripts/renew-certificates.sh

# Test renewal (dry run)
cd /path/to/LibraryOfBabel/ssl
certbot renew --dry-run \
    --config-dir "./letsencrypt-config" \
    --work-dir "./letsencrypt-work" \
    --logs-dir "./letsencrypt-logs"
```

### **Certificate Renewal Schedule**
The certificate renewal service runs daily at 3:30 AM. Check schedule:
```bash
# View renewal service configuration
cat "/Users/username/Library/LaunchAgents/com.librarybabel.certrenew.plist"

# Check if renewal service is loaded
launchctl list | grep certrenew
```

## Troubleshooting

### **Service Won't Start**
1. **Check plist syntax:**
   ```bash
   plutil -lint "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   ```

2. **Verify file permissions:**
   ```bash
   ls -la "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   # Should be: -rw-r--r--
   ```

3. **Check error logs:**
   ```bash
   tail -20 "/path/to/LibraryOfBabel/logs/api-error.log"
   ```

4. **Test manual start:**
   ```bash
   cd "/path/to/LibraryOfBabel/src"
   python3 secure_book_api.py
   ```

### **API Not Responding**
1. **Check service status:**
   ```bash
   launchctl list | grep librarybabel
   ```

2. **Restart service:**
   ```bash
   launchctl stop com.librarybabel.api
   sleep 5
   launchctl start com.librarybabel.api
   ```

3. **Check network connectivity:**
   ```bash
   # Test local access
   curl -k https://localhost:5562/api/secure/info
   
   # Test external access
   curl https://api.yourdomain.com:5562/api/secure/info
   ```

4. **Verify port forwarding:**
   - Check router configuration
   - Test from external network

### **Certificate Issues**
1. **Check certificate validity:**
   ```bash
   openssl x509 -in /path/to/cert -text -noout | grep -A 2 "Validity"
   ```

2. **Verify domain resolution:**
   ```bash
   nslookup api.yourdomain.com
   ```

3. **Test renewal manually:**
   ```bash
   /path/to/LibraryOfBabel/scripts/renew-certificates.sh
   ```

4. **Check Let's Encrypt logs:**
   ```bash
   tail -20 "/path/to/LibraryOfBabel/ssl/letsencrypt-logs/letsencrypt.log"
   ```

### **Performance Issues**
1. **Check system resources:**
   ```bash
   # Memory usage
   ps aux | grep secure_book_api | awk '{print $4"%", $11}'
   
   # CPU usage
   top -pid $(pgrep -f secure_book_api)
   ```

2. **Check database connection:**
   ```bash
   # Test PostgreSQL connection
   psql -h localhost -U username -d knowledge_base -c "SELECT COUNT(*) FROM chunks;"
   ```

3. **Monitor API response times:**
   ```bash
   # Time multiple requests
   for i in {1..5}; do
     time curl -s https://api.yourdomain.com:5562/api/secure/info > /dev/null
   done
   ```

## Maintenance Procedures

### **Daily Maintenance (Automated)**
- Certificate renewal check (3:30 AM)
- Health monitoring (every 5 minutes)
- Automatic service restart if unhealthy

### **Weekly Manual Checks**
```bash
# 1. Review error logs
grep -i error /path/to/LibraryOfBabel/logs/api-error.log | tail -20

# 2. Check service uptime
launchctl list com.librarybabel.api

# 3. Verify external access
curl https://api.yourdomain.com:5562/api/secure/info

# 4. Check certificate expiry
openssl x509 -in /path/to/cert -noout -dates

# 5. Review disk space
df -h /path/to/LibraryOfBabel/logs/
```

### **Monthly Maintenance**
```bash
# 1. Archive old logs
cd /path/to/LibraryOfBabel/logs
mkdir -p archive/$(date +%Y-%m)
gzip *.log
mv *.log.gz archive/$(date +%Y-%m)/

# 2. Test service restart
launchctl stop com.librarybabel.api
sleep 10
launchctl start com.librarybabel.api

# 3. Backup configurations
cp -r "/Users/username/Library/LaunchAgents/com.librarybabel.*" backup/

# 4. Update documentation if needed
```

## Service Updates

### **Updating the API Code**
1. **Stop the service:**
   ```bash
   launchctl stop com.librarybabel.api
   ```

2. **Update code files:**
   ```bash
   cd "/path/to/LibraryOfBabel"
   git pull origin main
   ```

3. **Test changes manually:**
   ```bash
   cd src
   python3 secure_book_api.py
   # Test in another terminal, then Ctrl+C
   ```

4. **Restart service:**
   ```bash
   launchctl start com.librarybabel.api
   ```

### **Updating Service Configuration**
1. **Unload service:**
   ```bash
   launchctl unload "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   ```

2. **Edit plist file:**
   ```bash
   nano "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   ```

3. **Validate syntax:**
   ```bash
   plutil -lint "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   ```

4. **Reload service:**
   ```bash
   launchctl load "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   ```

## Backup and Recovery

### **Backup Service Configurations**
```bash
# Create backup directory
mkdir -p "/path/to/LibraryOfBabel/backups/$(date +%Y-%m-%d)"

# Backup launch agent files
cp "/Users/username/Library/LaunchAgents/com.librarybabel."* \
   "/path/to/LibraryOfBabel/backups/$(date +%Y-%m-%d)/"

# Backup scripts
cp -r "/path/to/LibraryOfBabel/scripts" \
      "/path/to/LibraryOfBabel/backups/$(date +%Y-%m-%d)/"

# Backup SSL certificates
cp -r "/path/to/LibraryOfBabel/ssl/letsencrypt-config" \
      "/path/to/LibraryOfBabel/backups/$(date +%Y-%m-%d)/"
```

### **Recovery Procedures**
1. **Restore service files:**
   ```bash
   cp "/path/to/backup/com.librarybabel."* "/Users/username/Library/LaunchAgents/"
   ```

2. **Reload services:**
   ```bash
   launchctl load "/Users/username/Library/LaunchAgents/com.librarybabel.api.plist"
   ```

3. **Start services:**
   ```bash
   launchctl start com.librarybabel.api
   ```

4. **Verify operation:**
   ```bash
   curl https://api.yourdomain.com:5562/api/secure/info
   ```

## Performance Optimization

### **Service Tuning**
- **Memory limits** - Monitor usage and adjust if needed
- **Restart frequency** - Review health check intervals
- **Log levels** - Adjust verbosity based on needs
- **Database connections** - Optimize PostgreSQL settings

### **Monitoring Enhancements**
- **Response time tracking** - Log API performance metrics
- **Error rate monitoring** - Alert on high error rates
- **Resource usage** - Track memory and CPU over time
- **External monitoring** - Consider third-party uptime monitoring

## Service Status Dashboard

### **Quick Status Check Script**
```bash
#!/bin/bash
# LibraryOfBabel Service Status

echo "=== LibraryOfBabel Service Status ==="
echo "Date: $(date)"
echo

# Service status
echo "Services:"
launchctl list | grep librarybabel

echo
# API availability
echo "API Test:"
if curl -s https://api.yourdomain.com:5562/api/secure/info > /dev/null; then
    echo "✅ API responding"
else
    echo "❌ API not responding"
fi

echo
# Certificate status
echo "Certificate:"
cert_expiry=$(openssl x509 -in /path/to/cert -noout -enddate 2>/dev/null | cut -d= -f2)
echo "Expires: $cert_expiry"

echo
# Recent errors
echo "Recent Errors:"
error_count=$(grep "$(date +%Y-%m-%d)" /path/to/LibraryOfBabel/logs/api-error.log 2>/dev/null | wc -l)
echo "Today: $error_count errors"
```

Save as `/path/to/LibraryOfBabel/scripts/status-check.sh` and run for quick status overview.
<!-- Agent Commentary -->
---

## 🤖 Agent Bulletin Board

*Agents observe and comment on project evolution*

### 👤 Alex Thompson (Security Analyst)
*2025-07-07 00:17*

> Agent system expansion increases complexity, increases security risk. More components = more failure points.

### 👤 Dr. Sarah Kim (Technical Architecture Analyst)
*2025-07-07 00:17*

> New documentation suggests system architecture evolution. PostgreSQL + Flask + Agent pattern shows solid foundation.

---
*Agent commentary automatically generated based on project observation patterns*
