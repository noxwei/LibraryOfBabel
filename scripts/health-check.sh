#!/bin/bash
# LibraryOfBabel Health Check Script - Updated for Production

API_URL="https://localhost:5563/api/v3/health"
DOMAIN_HTTPS_URL="https://api.ashortstayinhell.com:5563/api/v3/health"
DOMAIN_HTTP_URL="http://api.ashortstayinhell.com:8080/api/v3/health"
LOG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/health-check.log"
CONFIG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/config/key_rotation_config.json"

# Load API key from config
API_KEY=$(python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
    print(config['current_key']['key'])
")

# Test local API availability
local_response=$(curl -k -s -o /dev/null -w "%{http_code}" "$API_URL")

# Test domain HTTPS availability
domain_https_response=$(curl -k -s -o /dev/null -w "%{http_code}" "$DOMAIN_HTTPS_URL")

# Test domain HTTP proxy availability
domain_http_response=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN_HTTP_URL")

if [ "$local_response" = "200" ] && [ "$domain_https_response" = "200" ]; then
    echo "$(date): ✅ All health checks passed - Local: $local_response, HTTPS: $domain_https_response, HTTP: $domain_http_response" >> "$LOG_FILE"
else
    echo "$(date): 🚨 Health check failed - Local: $local_response, HTTPS: $domain_https_response, HTTP: $domain_http_response" >> "$LOG_FILE"
    
    # Restart local API if needed
    if [ "$local_response" != "200" ]; then
        echo "$(date): 🔧 Restarting production API..." >> "$LOG_FILE"
        pkill -f "production_api.py"
        sleep 3
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 src/api/production_api.py > logs/production_api_persistent.log 2>&1 &
    fi
    
    # Restart proxy if needed
    if [ "$domain_http_response" != "200" ]; then
        echo "$(date): 🔧 Restarting HTTP proxy..." >> "$LOG_FILE"
        pkill -f "port80_proxy.py"
        sleep 3
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 agents/domain_config/port80_proxy.py > logs/proxy_service.log 2>&1 &
    fi
    
    echo "$(date): 🚀 Services restarted due to health check failure" >> "$LOG_FILE"
fi