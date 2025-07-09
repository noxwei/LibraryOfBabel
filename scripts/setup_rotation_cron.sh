#!/bin/bash
# 🔒 Setup API Key Rotation Monitoring Cron Job

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔒 Setting up API Key Rotation Monitoring"
echo "Project Directory: $PROJECT_DIR"

# Create a wrapper script for cron
cat > "$PROJECT_DIR/scripts/rotation_check.sh" << 'EOF'
#!/bin/bash
# API Key Rotation Check Wrapper for Cron

# Set working directory
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"

# Run monitoring check
/opt/homebrew/bin/python3 scripts/key_rotation_monitor.py --daemon >> logs/rotation_cron.log 2>&1

# Log completion
echo "[$(date)] Rotation monitoring check completed" >> logs/rotation_cron.log
EOF

chmod +x "$PROJECT_DIR/scripts/rotation_check.sh"

echo "✅ Created rotation check wrapper script"

# Create example crontab entry
cat > "$PROJECT_DIR/scripts/crontab_example.txt" << 'EOF'
# API Key Rotation Monitoring - Run daily at 9 AM
0 9 * * * /Users/weixiangzhang/Local\ Dev/LibraryOfBabel/scripts/rotation_check.sh

# Alternative: Run every 6 hours
# 0 */6 * * * /Users/weixiangzhang/Local\ Dev/LibraryOfBabel/scripts/rotation_check.sh
EOF

echo "📋 To set up automated monitoring, run:"
echo "   crontab -e"
echo "   Then add the line from: scripts/crontab_example.txt"
echo ""
echo "🔒 Manual monitoring check:"
echo "   python3 scripts/key_rotation_monitor.py"
echo ""
echo "📊 Check rotation status:"
echo "   python3 config/api_key_rotation.py --status"
echo ""
echo "✅ Setup complete!"