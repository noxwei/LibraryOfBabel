#!/bin/bash
"""
Phonetic Daemon Management Script - Dr. Rodriguez & Dr. Chen
===========================================================
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/phonetic_daemon.py"

case "$1" in
    start)
        echo "🚀 Starting phonetic processing daemon..."
        python3 "$DAEMON_SCRIPT" start &
        echo "✅ Daemon started in background"
        echo "💡 Use './manage_phonetic_daemon.sh status' to check progress"
        ;;
    stop)
        echo "🛑 Stopping phonetic daemon..."
        python3 "$DAEMON_SCRIPT" stop
        ;;
    status)
        python3 "$DAEMON_SCRIPT" status
        ;;
    restart)
        echo "🔄 Restarting phonetic daemon..."
        python3 "$DAEMON_SCRIPT" stop
        sleep 3
        python3 "$DAEMON_SCRIPT" start &
        echo "✅ Daemon restarted"
        ;;
    logs)
        echo "📋 Phonetic daemon logs:"
        echo "========================"
        tail -f /tmp/phonetic_daemon.log
        ;;
    *)
        echo "📖 Phonetic Daemon Management - Dr. Rodriguez & Dr. Chen"
        echo "Usage: $0 {start|stop|status|restart|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start phonetic processing in background"
        echo "  stop    - Stop the running daemon"
        echo "  status  - Check daemon status and progress"
        echo "  restart - Restart the daemon"
        echo "  logs    - Show live daemon logs"
        echo ""
        echo "💡 The daemon processes 165,206 chunks for audiobook search enhancement"
        echo "📊 Progress is saved and can be resumed if interrupted"
        ;;
esac