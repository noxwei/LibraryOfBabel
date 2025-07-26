#!/bin/bash
# Safe Daemon Starter for Bulk EPUB Processor
# Expands LibraryOfBabel to 5,000+ books safely

echo "🚀 Starting Bulk EPUB Processor Daemon"
echo "Target: 5,000+ books in PostgreSQL database"
echo "================================================"

# Check if daemon is already running
PID_FILE="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/bulk_processor.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  Daemon already running with PID $PID"
        echo "Use 'kill $PID' to stop it first"
        exit 1
    else
        echo "🧹 Cleaning up stale PID file"
        rm -f "$PID_FILE"
    fi
fi

# Change to project directory
cd /Users/weixiangzhang/Local_Dev/LibraryOfBabel

# Start daemon in background
echo "📚 Starting background processing..."
nohup python3 bulk_processor_daemon.py > daemon_output.log 2>&1 &

# Wait a moment and check if it started
sleep 2

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "✅ Daemon started successfully!"
    echo "📝 PID: $PID"
    echo "📊 Progress file: daemon_progress.json"
    echo "📋 Log file: bulk_processor.log"
    echo "💻 Output log: daemon_output.log"
    echo ""
    echo "📊 Monitor progress with:"
    echo "   tail -f bulk_processor.log"
    echo "   cat daemon_progress.json"
    echo ""
    echo "🛑 Stop daemon with:"
    echo "   kill $PID"
    echo "   # or use: pkill -f bulk_processor_daemon.py"
else
    echo "❌ Failed to start daemon"
    echo "Check daemon_output.log for errors"
    exit 1
fi