#!/bin/bash
# LibraryOfBabel Service Manager - Keep API and Proxy Running
# Linda Zhang's "Never Down Again" guarantee

CONFIG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/config/key_rotation_config.json"
LOG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/service_manager.log"

# Load API key
API_KEY=$(python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
    print(config['current_key']['key'])
")

echo "$(date): 🚀 Service Manager started - Linda's watching!" >> "$LOG_FILE"

while true; do
    # Check if production API is running
    if ! pgrep -f "production_api.py" > /dev/null; then
        echo "$(date): 🚨 Production API down - restarting..." >> "$LOG_FILE"
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 src/api/production_api.py > logs/production_api_persistent.log 2>&1 &
        echo "$(date): ✅ Production API restarted" >> "$LOG_FILE"
    fi
    
    # Check if proxy is running
    if ! pgrep -f "port80_proxy.py" > /dev/null; then
        echo "$(date): 🚨 HTTP proxy down - restarting..." >> "$LOG_FILE"
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 agents/domain_config/port80_proxy.py > logs/proxy_service.log 2>&1 &
        echo "$(date): ✅ HTTP proxy restarted" >> "$LOG_FILE"
    fi
    
    # Wait 30 seconds before next check
    sleep 30
done