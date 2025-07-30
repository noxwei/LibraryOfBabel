#!/bin/bash
"""
Calibre Linkage Daemon Management Script
========================================

Easy management of the Calibre linkage background daemon.
Provides start, stop, status, and monitoring capabilities.

Author: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
"""

DAEMON_NAME="calibre_linkage_daemon"
DAEMON_PATH="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/daemons/calibre_linkage_daemon.py"
PID_FILE="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/pids/calibre_daemon.pid"
LOG_FILE="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/calibre_linkage_daemon.log"
PROGRESS_FILE="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/calibre_linkage_daemon_progress.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure directories exist
mkdir -p "$(dirname "$PID_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

print_usage() {
    echo "🔧 Calibre Linkage Daemon Management"
    echo "Usage: $0 {start|stop|restart|status|logs|progress|stats}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the daemon in background"
    echo "  stop      - Stop the daemon gracefully"
    echo "  restart   - Restart the daemon"
    echo "  status    - Check if daemon is running"
    echo "  logs      - Follow daemon logs in real-time"
    echo "  progress  - Show current progress"
    echo "  stats     - Show statistics summary"
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

start_daemon() {
    if is_running; then
        echo -e "${YELLOW}⚠️ Daemon is already running (PID: $(cat "$PID_FILE"))${NC}"
        return 1
    fi
    
    echo -e "${BLUE}🚀 Starting Calibre Linkage Daemon...${NC}"
    
    # Start daemon in background
    cd "$(dirname "$DAEMON_PATH")"
    nohup python3 "$DAEMON_PATH" > "$LOG_FILE" 2>&1 &
    DAEMON_PID=$!
    
    # Save PID
    echo "$DAEMON_PID" > "$PID_FILE"
    
    # Wait a moment and check if it started successfully
    sleep 2
    if is_running; then
        echo -e "${GREEN}✅ Daemon started successfully (PID: $DAEMON_PID)${NC}"
        echo -e "${BLUE}📍 Log file: $LOG_FILE${NC}"
        echo -e "${BLUE}📊 Progress file: $PROGRESS_FILE${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start daemon${NC}"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    if ! is_running; then
        echo -e "${YELLOW}⚠️ Daemon is not running${NC}"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    echo -e "${BLUE}🛑 Stopping Calibre Linkage Daemon (PID: $PID)...${NC}"
    
    # Send SIGTERM for graceful shutdown
    kill -TERM "$PID"
    
    # Wait for graceful shutdown
    for i in {1..10}; do
        if ! is_running; then
            echo -e "${GREEN}✅ Daemon stopped gracefully${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    if is_running; then
        echo -e "${YELLOW}⚠️ Graceful shutdown failed, forcing stop...${NC}"
        kill -KILL "$PID"
        sleep 1
        if ! is_running; then
            echo -e "${GREEN}✅ Daemon stopped (forced)${NC}"
            rm -f "$PID_FILE"
            return 0
        else
            echo -e "${RED}❌ Failed to stop daemon${NC}"
            return 1
        fi
    fi
}

daemon_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✅ Calibre Linkage Daemon is running (PID: $PID)${NC}"
        
        # Show process info
        ps -p "$PID" -o pid,ppid,etime,cpu,pmem,cmd
        
        return 0
    else
        echo -e "${RED}❌ Calibre Linkage Daemon is not running${NC}"
        return 1
    fi
}

show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}❌ Log file not found: $LOG_FILE${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📝 Following daemon logs (Ctrl+C to exit):${NC}"
    tail -f "$LOG_FILE"
}

show_progress() {
    if [ ! -f "$PROGRESS_FILE" ]; then
        echo -e "${YELLOW}⚠️ Progress file not found: $PROGRESS_FILE${NC}"
        echo -e "${BLUE}💡 Daemon may not have started yet or no progress saved${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📊 Current Progress:${NC}"
    cat "$PROGRESS_FILE" | python3 -m json.tool
}

show_stats() {
    if [ ! -f "$PROGRESS_FILE" ]; then
        echo -e "${YELLOW}⚠️ No progress file found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📈 Calibre Linkage Daemon Statistics:${NC}"
    python3 -c "
import json
try:
    with open('$PROGRESS_FILE', 'r') as f:
        data = json.load(f)
    
    stats = data.get('stats', {})
    runtime = data.get('runtime_minutes', 0)
    
    print(f'🕐 Runtime: {runtime:.1f} minutes')
    print(f'📚 Total Calibre Books: {stats.get(\"total_calibre_books_found\", 0)}')
    print(f'✅ Linkages Created: {stats.get(\"linkages_created\", 0)}')
    print(f'🔄 Linkages Updated: {stats.get(\"linkages_updated\", 0)}')
    print(f'❌ Processing Errors: {stats.get(\"processing_errors\", 0)}')
    print(f'📦 Batches Completed: {stats.get(\"batches_completed\", 0)}')
    
    total_success = stats.get('linkages_created', 0) + stats.get('linkages_updated', 0)
    total_books = stats.get('total_calibre_books_found', 0)
    
    if total_books > 0:
        completion_rate = (total_success / total_books) * 100
        print(f'📊 Completion Rate: {completion_rate:.1f}%')
        print(f'🔗 Download Links Ready: {total_success}')
    
except Exception as e:
    print(f'❌ Error reading progress: {e}')
"
}

# Main script logic
case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 2
        start_daemon
        ;;
    status)
        daemon_status
        ;;
    logs)
        show_logs
        ;;
    progress)
        show_progress
        ;;
    stats)
        show_stats
        ;;
    *)
        print_usage
        exit 1
        ;;
esac

exit $?