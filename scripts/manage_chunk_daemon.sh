#!/bin/bash
#
# Chunk Processing Daemon Management Script
# Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
# ====================================================
#
# Convenient wrapper script for managing the chunk processing daemon.
#

DAEMON_SCRIPT="$(dirname "$0")/chunk_processing_daemon.py"
DAEMON_NAME="Chunk Processing Daemon"

case "$1" in
    start)
        echo "Starting $DAEMON_NAME..."
        if [ -n "$2" ]; then
            echo "Using batch size: $2"
            nohup python3 "$DAEMON_SCRIPT" start "$2" > /tmp/chunk_daemon_startup.log 2>&1 &
        else
            echo "Using default batch size: 5"
            nohup python3 "$DAEMON_SCRIPT" start > /tmp/chunk_daemon_startup.log 2>&1 &
        fi
        sleep 2
        echo "Startup log:"
        cat /tmp/chunk_daemon_startup.log
        ;;
    stop)
        echo "Stopping $DAEMON_NAME..."
        python3 "$DAEMON_SCRIPT" stop
        ;;
    restart)
        echo "Restarting $DAEMON_NAME..."
        python3 "$DAEMON_SCRIPT" stop
        sleep 3
        if [ -n "$2" ]; then
            nohup python3 "$DAEMON_SCRIPT" start "$2" > /tmp/chunk_daemon_startup.log 2>&1 &
        else
            nohup python3 "$DAEMON_SCRIPT" start > /tmp/chunk_daemon_startup.log 2>&1 &
        fi
        sleep 2
        cat /tmp/chunk_daemon_startup.log
        ;;
    status)
        echo "=== $DAEMON_NAME Status ==="
        python3 "$DAEMON_SCRIPT" status
        echo ""
        echo "=== Process Status ==="
        if [ -f /tmp/chunk_processing_daemon.pid ]; then
            PID=$(cat /tmp/chunk_processing_daemon.pid)
            if ps -p $PID > /dev/null 2>&1; then
                echo "✓ Daemon is running (PID: $PID)"
                echo "Process details:"
                ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
            else
                echo "✗ Daemon is not running (stale PID file)"
            fi
        else
            echo "✗ Daemon is not running (no PID file)"
        fi
        ;;
    logs|log)
        echo "=== $DAEMON_NAME Logs ==="
        if [ -f /tmp/chunk_processing_daemon.log ]; then
            if [ "$2" = "tail" ] || [ "$2" = "follow" ] || [ "$2" = "-f" ]; then
                tail -f /tmp/chunk_processing_daemon.log
            else
                tail -50 /tmp/chunk_processing_daemon.log
            fi
        else
            echo "No log file found at /tmp/chunk_processing_daemon.log"
        fi
        ;;
    reset)
        echo "Resetting $DAEMON_NAME progress..."
        python3 "$DAEMON_SCRIPT" reset
        ;;
    health)
        echo "=== System Health Check ==="
        python3 -c "
import sys
import os
sys.path.append(os.path.join(os.path.dirname('$DAEMON_SCRIPT'), '..', 'src'))

from api.modules.database import get_readonly_db, test_connection, ConnectionType

print('Testing database connections...')
try:
    readonly_ok = test_connection(ConnectionType.READONLY)
    admin_ok = test_connection(ConnectionType.ADMIN)
    
    print(f'Read-only connection: {'✓ OK' if readonly_ok else '✗ FAILED'}')
    print(f'Admin connection: {'✓ OK' if admin_ok else '✗ FAILED'}')
    
    if readonly_ok:
        with get_readonly_db() as conn:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        COUNT(*) as total_books,
                        COUNT(*) FILTER (WHERE chunk_count IS NULL OR chunk_count = 0) as books_without_chunks,
                        COUNT(*) FILTER (WHERE chunk_count > 0) as books_with_chunks
                    FROM books b
                    INNER JOIN book_contents bc ON b.book_id = bc.book_id
                ''')
                total, without_chunks, with_chunks = cur.fetchone()
                
                print(f'\\nBooks Status:')
                print(f'  Total books with content: {total}')
                print(f'  Books with chunks: {with_chunks}')
                print(f'  Books without chunks: {without_chunks}')
                if total > 0:
                    print(f'  Health percentage: {(with_chunks/total*100):.1f}%')
    
except Exception as e:
    print(f'Health check failed: {e}')
"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|reset|health} [batch_size]"
        echo ""
        echo "Commands:"
        echo "  start [batch_size]  - Start the daemon (default batch size: 5)"
        echo "  stop                - Stop the daemon"
        echo "  restart [batch_size] - Restart the daemon"
        echo "  status              - Show daemon status and progress"
        echo "  logs [tail]         - Show logs (use 'tail' for live tail)"
        echo "  reset               - Reset progress tracking"
        echo "  health              - Run system health check"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start with default batch size (5)"
        echo "  $0 start 10        # Start with batch size 10"
        echo "  $0 logs tail       # Follow logs in real time"
        echo "  $0 health          # Check system health"
        exit 1
        ;;
esac