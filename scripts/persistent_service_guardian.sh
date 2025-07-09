#!/bin/bash
# 🛡️ Persistent Service Guardian - NEVER DIES
# Linda Zhang's "Never Down Again" Ultimate Protection System

CONFIG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/config/key_rotation_config.json"
LOG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/persistent_guardian.log"
GUARDIAN_PID_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/guardian.pid"

# Load API key
API_KEY=$(python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
    print(config['current_key']['key'])
")

# Create PID file
echo $$ > "$GUARDIAN_PID_FILE"

echo "$(date): 🛡️ PERSISTENT SERVICE GUARDIAN STARTED - Linda's Ultimate Protection!" >> "$LOG_FILE"
echo "$(date): 📋 Guardian PID: $$" >> "$LOG_FILE"
echo "$(date): 🔐 API Key loaded: ${API_KEY:0:20}..." >> "$LOG_FILE"

# Trap signals to prevent termination
trap 'echo "$(date): ⚠️  Signal received, but Guardian never dies!" >> "$LOG_FILE"' SIGTERM SIGINT SIGQUIT

while true; do
    # Check LaunchDaemon API service
    if ! launchctl list | grep -q "com.librarybabel.api.*[0-9]"; then
        echo "$(date): 🚨 LaunchDaemon API service down - restarting..." >> "$LOG_FILE"
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        launchctl unload config/macos/com.librarybabel.api.plist 2>/dev/null || true
        launchctl load config/macos/com.librarybabel.api.plist
        echo "$(date): ✅ LaunchDaemon API service restarted" >> "$LOG_FILE"
    fi
    
    # Check production API process
    if ! pgrep -f "production_api.py" > /dev/null; then
        echo "$(date): 🚨 Production API process down - restarting..." >> "$LOG_FILE"
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 src/api/production_api.py > logs/production_api_persistent.log 2>&1 &
        echo "$(date): ✅ Production API process restarted" >> "$LOG_FILE"
    fi
    
    # Check HTTP proxy process
    if ! pgrep -f "port80_proxy.py" > /dev/null; then
        echo "$(date): 🚨 HTTP proxy down - restarting..." >> "$LOG_FILE"
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 agents/domain_config/port80_proxy.py > logs/proxy_service.log 2>&1 &
        echo "$(date): ✅ HTTP proxy restarted" >> "$LOG_FILE"
    fi
    
    # Test actual connectivity
    if ! curl -k -s -f https://api.ashortstayinhell.com:5563/api/v3/health > /dev/null; then
        echo "$(date): 🚨 HTTPS connectivity failed - emergency restart sequence..." >> "$LOG_FILE"
        
        # Kill all related processes
        pkill -f "production_api.py"
        pkill -f "port80_proxy.py"
        sleep 5
        
        # Restart everything
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        export API_KEY="$API_KEY"
        nohup python3 src/api/production_api.py > logs/production_api_persistent.log 2>&1 &
        nohup python3 agents/domain_config/port80_proxy.py > logs/proxy_service.log 2>&1 &
        
        echo "$(date): 🚀 Emergency restart sequence completed" >> "$LOG_FILE"
    fi
    
    # Health report every 10 minutes
    if [ $(($(date +%s) % 600)) -eq 0 ]; then
        echo "$(date): 💪 Guardian alive - All services protected!" >> "$LOG_FILE"
        echo "$(date): 📊 Active processes: $(pgrep -f 'production_api.py|port80_proxy.py' | wc -l)" >> "$LOG_FILE"
    fi
    
    # Check every 30 seconds
    sleep 30
done