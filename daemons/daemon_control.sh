#!/bin/bash
# GENRE CLASSIFICATION DAEMON CONTROL SCRIPT
# ===========================================

DAEMON_SCRIPT="/Users/weixiangzhang/Local Dev/LibraryOfBabel/daemons/genre_classification_daemon.py"
DAEMON_DIR="/Users/weixiangzhang/Local Dev/LibraryOfBabel/daemons"

# Ensure we're in the right directory
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"

case "$1" in
    start)
        echo "🚀 Starting Genre Classification Daemon..."
        python3 "$DAEMON_SCRIPT" start
        ;;
    stop)
        echo "🛑 Stopping Genre Classification Daemon..."
        python3 "$DAEMON_SCRIPT" stop
        ;;
    status)
        python3 "$DAEMON_SCRIPT" status
        ;;
    restart)
        echo "🔄 Restarting Genre Classification Daemon..."
        python3 "$DAEMON_SCRIPT" stop
        sleep 3
        python3 "$DAEMON_SCRIPT" start
        ;;
    logs)
        echo "📋 Showing recent daemon logs..."
        tail -f "$DAEMON_DIR/genre_daemon.log"
        ;;
    progress)
        echo "📊 Current Progress:"
        python3 "$DAEMON_SCRIPT" status | grep -E "(Books Processed|Successful|Failed|Success Rate)"
        ;;
    quick-start)
        echo "⚡ Quick Start - Warming up Magistral first..."
        curl -s http://localhost:11434/api/generate \
             -d '{"model":"magistral","prompt":"Ready","stream":false,"options":{"max_tokens":5}}' \
             --max-time 60 > /dev/null
        echo "✅ Magistral warm, starting daemon..."
        python3 "$DAEMON_SCRIPT" start
        ;;
    *)
        echo "📖 Genre Classification Daemon Control"
        echo "======================================"
        echo "Usage: $0 {start|stop|status|restart|logs|progress|quick-start}"
        echo ""
        echo "Commands:"
        echo "  start       - Start the daemon"
        echo "  stop        - Stop the daemon" 
        echo "  status      - Show daemon status and progress"
        echo "  restart     - Restart the daemon"
        echo "  logs        - Show live log output"
        echo "  progress    - Quick progress check"
        echo "  quick-start - Warm up Magistral then start daemon"
        echo ""
        echo "The daemon will:"
        echo "  ✅ Process 1,210 missing book genres"
        echo "  ✅ Resume from last position if interrupted"
        echo "  ✅ Save progress every 5 books"
        echo "  ✅ Run autonomously in background"
        echo ""
        exit 1
        ;;
esac