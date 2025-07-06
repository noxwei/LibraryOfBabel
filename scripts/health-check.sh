#!/bin/bash
# LibraryOfBabel Health Check Script

API_URL="https://localhost:5562/api/secure/info"
LOG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/health-check.log"

# Test API availability
response=$(curl -k -s -o /dev/null -w "%{http_code}" "$API_URL")

if [ "$response" = "200" ]; then
    echo "$(date): API health check passed (HTTP $response)" >> "$LOG_FILE"
else
    echo "$(date): API health check failed (HTTP $response)" >> "$LOG_FILE"
    # Restart API service
    launchctl stop com.librarybabel.api
    sleep 5
    launchctl start com.librarybabel.api
    echo "$(date): API service restarted due to health check failure" >> "$LOG_FILE"
fi