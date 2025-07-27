# 🤖 LibraryOfBabel Automated Testing Pipeline
## Preventing "External Access Crisis" Through Automation

**Created:** July 27, 2025 after resolving external access issues  
**Purpose:** Automate detection of network/deployment issues before they impact production

---

## 🎯 **AUTOMATION GOALS**

1. **Detect IP address changes** before they break external access
2. **Validate network configuration** automatically
3. **Test external connectivity** before deployment
4. **Monitor SSL certificate expiration**
5. **Verify database scaling** (5000+ books)

---

## 🔄 **AUTOMATED TESTING PIPELINE**

### **Stage 1: Infrastructure Health Check**
```bash
#!/bin/bash
# infrastructure_health_check.sh

echo "🔍 Infrastructure Health Check..."

# Check Mac Mini IP
CURRENT_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
EXPECTED_IP="10.0.0.13"

if [ "$CURRENT_IP" != "$EXPECTED_IP" ]; then
    echo "❌ CRITICAL: Mac Mini IP changed from $EXPECTED_IP to $CURRENT_IP"
    echo "🔧 Action Required: Update static IP or router port forwarding"
    exit 1
fi

# Check External IP
EXTERNAL_IP=$(curl -s ifconfig.me)
EXPECTED_EXTERNAL="73.161.54.75"

if [ "$EXTERNAL_IP" != "$EXPECTED_EXTERNAL" ]; then
    echo "⚠️ WARNING: External IP changed from $EXPECTED_EXTERNAL to $EXTERNAL_IP"
    echo "🔧 Action Required: Update DNS A record"
fi

# Check DNS Resolution
DNS_IP=$(nslookup api.ashortstayinhell.com | grep "Address:" | tail -1 | awk '{print $2}')
if [ "$DNS_IP" != "$EXPECTED_EXTERNAL" ]; then
    echo "❌ DNS mismatch: Expected $EXPECTED_EXTERNAL, got $DNS_IP"
    exit 1
fi

echo "✅ Infrastructure health check passed"
```

### **Stage 2: Local API Testing**
```bash
#!/bin/bash
# local_api_test.sh

echo "🧪 Local API Testing..."

# Start test server
python3 scripts/test_api_endpoints.py &
TEST_PID=$!
sleep 5

# Test health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:9002/api/v4/health)
if [[ ! "$HEALTH_RESPONSE" == *"healthy"* ]]; then
    echo "❌ Local health check failed"
    kill $TEST_PID
    exit 1
fi

# Test book count
INFO_RESPONSE=$(curl -s http://localhost:9002/api/v4/info)
if [[ ! "$INFO_RESPONSE" == *"5000"* ]]; then
    echo "❌ Book count verification failed (not 5000+)"
    kill $TEST_PID
    exit 1
fi

# Test API key authentication
AUTH_RESPONSE=$(curl -s -H "API-Key: babel_test_5000_books" http://localhost:9002/api/v4/vector/search -d '{"query":"test"}')
if [[ "$AUTH_RESPONSE" == *"error"* ]]; then
    echo "❌ API key authentication failed"
    kill $TEST_PID
    exit 1
fi

kill $TEST_PID
echo "✅ Local API tests passed"
```

### **Stage 3: Production Environment Test**
```bash
#!/bin/bash
# production_environment_test.sh

echo "🚀 Production Environment Testing..."

# Start production API
cd "/Users/weixiangzhang/Local_Dev/LibraryOfBabel"
python3 src/api/production_api.py &
PROD_PID=$!
sleep 10

# Test local HTTPS
LOCAL_HTTPS=$(curl -s -k https://localhost:5562/api/v4/health)
if [[ ! "$LOCAL_HTTPS" == *"healthy"* ]]; then
    echo "❌ Local HTTPS test failed"
    kill $PROD_PID
    exit 1
fi

# Test external HTTP (basic connectivity)
EXTERNAL_TEST=$(curl -s -m 10 http://73.161.54.75:5562 || echo "TIMEOUT")
if [[ "$EXTERNAL_TEST" == "TIMEOUT" ]]; then
    echo "❌ External connectivity failed - check router/firewall"
    kill $PROD_PID
    exit 1
fi

# Test external HTTPS with domain
DOMAIN_TEST=$(curl -s https://api.ashortstayinhell.com:5562/api/v4/health)
if [[ ! "$DOMAIN_TEST" == *"healthy"* ]]; then
    echo "❌ External domain access failed"
    kill $PROD_PID
    exit 1
fi

echo "✅ Production environment tests passed"
# Keep production API running
```

### **Stage 4: SSL Certificate Monitoring**
```bash
#!/bin/bash
# ssl_certificate_check.sh

echo "🔒 SSL Certificate Check..."

CERT_PATH="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/ssl/letsencrypt-config/live/api.ashortstayinhell.com/cert.pem"

if [ ! -f "$CERT_PATH" ]; then
    echo "❌ SSL certificate not found at $CERT_PATH"
    exit 1
fi

# Check expiration (30 days warning)
EXPIRY_DATE=$(openssl x509 -in "$CERT_PATH" -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
CURRENT_EPOCH=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))

if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
    echo "⚠️ SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
    echo "🔧 Action Required: Renew SSL certificate"
    if [ $DAYS_UNTIL_EXPIRY -lt 7 ]; then
        exit 1
    fi
fi

echo "✅ SSL certificate valid for $DAYS_UNTIL_EXPIRY days"
```

---

## 📊 **MONITORING DASHBOARD**

### **Daily Automated Checks** (via cron)
```bash
# Add to crontab: crontab -e
# Run infrastructure check every hour
0 * * * * /Users/weixiangzhang/Local_Dev/LibraryOfBabel/scripts/infrastructure_health_check.sh

# Run full test suite daily at 6 AM
0 6 * * * /Users/weixiangzhang/Local_Dev/LibraryOfBabel/scripts/full_test_suite.sh

# Check SSL weekly
0 0 * * 0 /Users/weixiangzhang/Local_Dev/LibraryOfBabel/scripts/ssl_certificate_check.sh
```

### **Alert System**
```bash
#!/bin/bash
# alert_system.sh

send_alert() {
    local message="$1"
    echo "🚨 ALERT: $message" | mail -s "LibraryOfBabel Alert" admin@ashortstayinhell.com
    echo "$(date): $message" >> /var/log/librarybabel-alerts.log
}

# Example usage in tests:
if [ "$test_failed" = true ]; then
    send_alert "External access test failed - check network configuration"
fi
```

---

## 🔧 **INTEGRATION WITH EXISTING WORKFLOW**

### **Pre-Deployment Hook**
```bash
#!/bin/bash
# pre_deployment_hook.sh

echo "🔍 Running pre-deployment checks..."

./scripts/infrastructure_health_check.sh || exit 1
./scripts/local_api_test.sh || exit 1
./scripts/ssl_certificate_check.sh || exit 1

echo "✅ All pre-deployment checks passed - safe to deploy"
```

### **Post-Deployment Verification**
```bash
#!/bin/bash
# post_deployment_verification.sh

echo "🚀 Post-deployment verification..."

sleep 30  # Allow services to start

./scripts/production_environment_test.sh || {
    echo "❌ Post-deployment tests failed"
    echo "🔧 Rolling back..."
    # Add rollback logic here
    exit 1
}

echo "✅ Deployment successful and verified"
```

---

## 📈 **SUCCESS METRICS**

- **Zero external access failures** after implementing pipeline
- **Automated detection** of IP changes within 1 hour
- **SSL certificate renewal** alerts 30 days before expiry
- **99.9% uptime** through proactive monitoring
- **Faster issue resolution** through automated diagnostics

---

## 🎯 **IMPLEMENTATION CHECKLIST**

- [ ] Create monitoring scripts in `/scripts/monitoring/`
- [ ] Set up cron jobs for automated checks
- [ ] Configure alert system (email/Slack)
- [ ] Test all automation scripts manually
- [ ] Document alert response procedures
- [ ] Create monitoring dashboard (optional)
- [ ] Schedule weekly review of automation logs

**Last Updated:** July 27, 2025  
**Status:** 🎯 Ready for Implementation