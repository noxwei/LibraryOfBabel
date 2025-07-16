#!/bin/bash
# Comprehensive Reclassification Daemon Control Script
# ====================================================

DAEMON_DIR="/Users/weixiangzhang/Local Dev/LibraryOfBabel/daemons"
DAEMON_SCRIPT="$DAEMON_DIR/comprehensive_reclassification_daemon.py"
PID_FILE="$DAEMON_DIR/reclassification.pid"
LOG_FILE="$DAEMON_DIR/reclassification.log"
STATE_FILE="$DAEMON_DIR/reclassification_state.json"

case "$1" in
    start)
        echo "🚀 Starting Comprehensive Reclassification Daemon..."
        echo "=================================================="
        
        # Check if already running
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "❌ Daemon already running (PID: $PID)"
                exit 1
            else
                echo "🧹 Cleaning up stale PID file"
                rm -f "$PID_FILE"
            fi
        fi
        
        # Start daemon
        cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
        nohup python3 "$DAEMON_SCRIPT" > "$LOG_FILE" 2>&1 &
        DAEMON_PID=$!
        
        echo "✅ Daemon started with PID: $DAEMON_PID"
        echo "📁 Logs: $LOG_FILE"
        echo "💾 State: $STATE_FILE"
        echo ""
        echo "📊 Monitor commands:"
        echo "   tail -f \"$LOG_FILE\"          # Live logs"
        echo "   ./daemon_control.sh status     # Check status"
        echo "   ./daemon_control.sh stop       # Stop daemon"
        ;;
        
    stop)
        echo "🛑 Stopping Comprehensive Reclassification Daemon..."
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "📤 Sending SIGTERM to PID $PID..."
                kill -TERM $PID
                
                # Wait for graceful shutdown
                for i in {1..10}; do
                    if ! ps -p $PID > /dev/null 2>&1; then
                        echo "✅ Daemon stopped gracefully"
                        rm -f "$PID_FILE"
                        exit 0
                    fi
                    sleep 1
                done
                
                # Force kill if necessary
                echo "⚠️  Daemon not responding, force killing..."
                kill -KILL $PID
                rm -f "$PID_FILE"
                echo "💀 Daemon force stopped"
            else
                echo "❌ Daemon not running (stale PID file)"
                rm -f "$PID_FILE"
            fi
        else
            echo "❌ Daemon not running (no PID file)"
        fi
        ;;
        
    status)
        echo "📊 Comprehensive Reclassification Daemon Status"
        echo "=============================================="
        
        # Check if running
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "🟢 Status: RUNNING (PID: $PID)"
                
                # Get process info
                CPU_MEM=$(ps -p $PID -o %cpu,%mem --no-headers)
                echo "⚡ Resource usage: $CPU_MEM (CPU%, MEM%)"
                
                # Show recent log lines
                if [ -f "$LOG_FILE" ]; then
                    echo ""
                    echo "📝 Recent log entries:"
                    tail -n 5 "$LOG_FILE" | sed 's/^/   /'
                fi
            else
                echo "🔴 Status: NOT RUNNING (stale PID file)"
                rm -f "$PID_FILE"
            fi
        else
            echo "🔴 Status: NOT RUNNING"
        fi
        
        # Show progress if state file exists
        if [ -f "$STATE_FILE" ]; then
            echo ""
            echo "📈 Progress Information:"
            python3 -c "
import json
try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    
    print(f'   📚 Books processed: {state.get(\"processed_count\", 0)}/{state.get(\"total_books\", \"?\")}')
    print(f'   🔄 Reclassified: {state.get(\"reclassified_count\", 0)}')
    print(f'   ❌ Failed: {state.get(\"failed_count\", 0)}')
    print(f'   📊 Status: {state.get(\"status\", \"unknown\")}')
    if 'last_update' in state:
        print(f'   🕐 Last update: {state[\"last_update\"]}')
except:
    print('   ⚠️  Could not read state file')
"
        fi
        ;;
        
    logs)
        echo "📝 Showing live logs (Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
        ;;
        
    progress)
        echo "📊 Detailed Progress Report"
        echo "=========================="
        
        if [ -f "$STATE_FILE" ]; then
            python3 -c "
import json
from datetime import datetime

try:
    with open('$STATE_FILE', 'r') as f:
        state = json.load(f)
    
    print(f'Status: {state.get(\"status\", \"unknown\").upper()}')
    print(f'Total books: {state.get(\"total_books\", 0)}')
    print(f'Processed: {state.get(\"processed_count\", 0)}')
    print(f'Reclassified: {state.get(\"reclassified_count\", 0)}')
    print(f'Failed: {state.get(\"failed_count\", 0)}')
    
    if state.get('total_books', 0) > 0:
        progress = (state.get('processed_count', 0) / state.get('total_books', 1)) * 100
        print(f'Progress: {progress:.1f}%')
    
    if 'start_time' in state:
        print(f'Started: {state[\"start_time\"]}')
    
    if 'genre_changes' in state and state['genre_changes']:
        print('\\nGenre Changes:')
        for old_genre, changes in state['genre_changes'].items():
            total = sum(changes.values())
            print(f'  {old_genre}: {total} books moved')
            for new_genre, count in changes.items():
                print(f'    → {new_genre}: {count}')
                
except Exception as e:
    print(f'Error reading state: {e}')
"
        else
            echo "❌ No state file found"
        fi
        ;;
        
    restart)
        echo "🔄 Restarting daemon..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    *)
        echo "📋 Comprehensive Reclassification Daemon Control"
        echo "=============================================="
        echo "Usage: $0 {start|stop|status|logs|progress|restart}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the reclassification daemon"
        echo "  stop      - Stop the daemon gracefully"  
        echo "  status    - Show daemon status and recent activity"
        echo "  logs      - Show live log output"
        echo "  progress  - Show detailed progress report"
        echo "  restart   - Stop and start the daemon"
        echo ""
        echo "Files:"
        echo "  Logs: $LOG_FILE"
        echo "  State: $STATE_FILE"
        echo "  PID: $PID_FILE"
        exit 1
        ;;
esac