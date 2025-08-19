#!/bin/bash
# LibraryOfBabel API Service Manager
# Provides start/stop/restart/status commands for the API

API_PID_FILE="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/api.pid"
API_LOG_FILE="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/api_persistent.log"
API_SCRIPT="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/start_api_daemon.sh"

start_api() {
    if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        echo "API is already running (PID: $(cat "$API_PID_FILE"))"
        return 0
    fi
    
    echo "Starting LibraryOfBabel API..."
    cd /Users/weixiangzhang/Local_Dev/LibraryOfBabel
    nohup "$API_SCRIPT" > "$API_LOG_FILE" 2>&1 &
    echo $! > "$API_PID_FILE"
    sleep 2
    
    if kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        echo "✅ API started successfully (PID: $(cat "$API_PID_FILE"))"
        echo "📊 Test: curl -s https://api.ashortstayinhell.com:5562/health"
    else
        echo "❌ Failed to start API"
        return 1
    fi
}

stop_api() {
    if [ ! -f "$API_PID_FILE" ]; then
        echo "API PID file not found. Attempting to kill by process name..."
        pkill -f "standardized_production_api.py"
        return 0
    fi
    
    PID=$(cat "$API_PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Stopping API (PID: $PID)..."
        kill "$PID"
        sleep 2
        
        if kill -0 "$PID" 2>/dev/null; then
            echo "Force killing API..."
            kill -9 "$PID"
        fi
        
        rm -f "$API_PID_FILE"
        echo "✅ API stopped"
    else
        echo "API was not running"
        rm -f "$API_PID_FILE"
    fi
}

status_api() {
    if [ -f "$API_PID_FILE" ] && kill -0 "$(cat "$API_PID_FILE")" 2>/dev/null; then
        PID=$(cat "$API_PID_FILE")
        echo "✅ API is running (PID: $PID)"
        echo "📊 Health check: $(curl -s https://api.ashortstayinhell.com:5562/health | jq -r '.status' 2>/dev/null || echo 'Failed')"
        echo "🔗 MCP endpoint: $(curl -s https://api.ashortstayinhell.com:5562/api/mcp | jq -r '.data.name' 2>/dev/null || echo 'Failed')"
    else
        echo "❌ API is not running"
        return 1
    fi
}

case "$1" in
    start)
        start_api
        ;;
    stop)
        stop_api
        ;;
    restart)
        stop_api
        sleep 1
        start_api
        ;;
    status)
        status_api
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo "  start   - Start the LibraryOfBabel API"
        echo "  stop    - Stop the API"
        echo "  restart - Restart the API"
        echo "  status  - Check if API is running"
        exit 1
        ;;
esac