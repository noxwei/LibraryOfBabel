#!/bin/bash
# Production API Control Script
# =============================

DAEMON_SCRIPT="daemons/production_api_daemon.py"

case "$1" in
    start)
        echo "🚀 Starting Production API..."
        python3 "$DAEMON_SCRIPT" start
        ;;
    stop)
        echo "🛑 Stopping Production API..."
        python3 "$DAEMON_SCRIPT" stop
        ;;
    status)
        echo "📊 Production API Status:"
        python3 "$DAEMON_SCRIPT" status
        ;;
    restart)
        echo "🔄 Restarting Production API..."
        python3 "$DAEMON_SCRIPT" restart
        ;;
    logs)
        echo "📋 Production API Logs:"
        tail -f logs/production_api_daemon.log
        ;;
    test)
        echo "🧪 Testing Production API..."
        echo "Status endpoint:"
        curl -s "http://localhost:5562/status" | python3 -m json.tool
        echo ""
        echo "iOS Shortcuts health:"
        curl -s "http://localhost:5562/api/shortcuts/health" | python3 -m json.tool
        echo ""
        echo "Search count test:"
        if [ -z "$API_KEY" ]; then
            echo "❌ API_KEY environment variable not set. Set it first:"
            echo "export API_KEY=your_secure_api_key"
        else
            curl -s "http://localhost:5562/api/v4/search?q=python&action=count&api_key=$API_KEY" | python3 -m json.tool
        fi
        ;;
    *)
        echo "📖 Production API Control"
        echo "========================"
        echo "Usage: $0 {start|stop|status|restart|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the production API daemon"
        echo "  stop    - Stop the production API daemon"
        echo "  status  - Show daemon status and API health"
        echo "  restart - Restart the production API daemon"
        echo "  logs    - Show live log output"
        echo "  test    - Test all new API endpoints"
        echo ""
        echo "Features:"
        echo "  ✅ System status monitoring (/status)"
        echo "  ✅ iOS Shortcuts integration (/api/shortcuts/*)"
        echo "  ✅ ChatGPT Custom Actions ready"
        echo "  ✅ PostgreSQL stored procedures"
        echo "  ✅ Database-first architecture"
        echo ""
        exit 1
        ;;
esac 