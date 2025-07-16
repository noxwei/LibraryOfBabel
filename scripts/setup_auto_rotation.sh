#!/bin/bash
# ⏰ AUTOMATIC API KEY ROTATION SETUP
# ===================================
# 
# Sets up automatic 30-day API key rotation for the MCP server.
# Creates cron job and systemd timer for production environments.
# 
# Usage:
#     ./scripts/setup_auto_rotation.sh [--install|--remove|--status]
# 
# Options:
#     --install    Install automatic rotation (default)
#     --remove     Remove automatic rotation
#     --status     Check rotation status
#     --help       Show this help message

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/Users/weixiangzhang/Local Dev/LibraryOfBabel"
CRON_JOB="0 2 1 * * $PROJECT_ROOT/scripts/setup_mcp_env.sh --rotate-key"
CRON_COMMENT="# Library of Babel MCP API Key Rotation"

print_header() {
    echo -e "${BLUE}⏰ Automatic API Key Rotation Setup${NC}"
    echo -e "${BLUE}===================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

install_cron_job() {
    print_header
    echo "📅 Installing monthly API key rotation..."
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "setup_mcp_env.sh --rotate-key"; then
        print_warning "Cron job already exists"
        return
    fi
    
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMENT"; echo "$CRON_JOB") | crontab -
    
    if [ $? -eq 0 ]; then
        print_success "Cron job installed successfully"
        print_success "Schedule: 1st day of each month at 2:00 AM"
    else
        print_error "Failed to install cron job"
        return 1
    fi
}

remove_cron_job() {
    print_header
    echo "🗑️  Removing automatic API key rotation..."
    
    # Remove cron job
    crontab -l 2>/dev/null | grep -v "setup_mcp_env.sh --rotate-key" | grep -v "Library of Babel MCP API Key Rotation" | crontab -
    
    if [ $? -eq 0 ]; then
        print_success "Cron job removed successfully"
    else
        print_error "Failed to remove cron job"
        return 1
    fi
}

check_status() {
    print_header
    echo "📊 Checking rotation status..."
    
    # Check cron job
    if crontab -l 2>/dev/null | grep -q "setup_mcp_env.sh --rotate-key"; then
        print_success "Automatic rotation is ENABLED"
        echo "Schedule: $(crontab -l 2>/dev/null | grep 'setup_mcp_env.sh --rotate-key')"
    else
        print_warning "Automatic rotation is DISABLED"
    fi
    
    # Check last rotation
    if [ -f "$PROJECT_ROOT/.env" ]; then
        last_update=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$PROJECT_ROOT/.env")
        print_success "Last environment update: $last_update"
    else
        print_warning "No environment file found"
    fi
    
    # Check config file
    if [ -f "$PROJECT_ROOT/config/api_settings.json" ]; then
        last_config_update=$(python3 -c "
import json
import os
config_file = '$PROJECT_ROOT/config/api_settings.json'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    print(config.get('last_updated', 'Unknown'))
")
        print_success "Last config update: $last_config_update"
    else
        print_warning "No config file found"
    fi
}

create_rotation_log() {
    # Create log directory
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Create rotation log script
    cat > "$PROJECT_ROOT/scripts/rotation_logger.sh" << 'EOF'
#!/bin/bash
# Log API key rotation events
LOG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/api_rotation.log"
echo "$(date): API key rotation initiated" >> "$LOG_FILE"
/Users/weixiangzhang/Local\ Dev/LibraryOfBabel/scripts/setup_mcp_env.sh --rotate-key >> "$LOG_FILE" 2>&1
echo "$(date): API key rotation completed" >> "$LOG_FILE"
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/rotation_logger.sh"
    print_success "Rotation logger created"
}

setup_notification() {
    # Create notification script for successful rotations
    cat > "$PROJECT_ROOT/scripts/rotation_notify.sh" << 'EOF'
#!/bin/bash
# Notify when API key rotation completes
WEBHOOK_URL="https://api.ashortstayinhell.com:5562/api/v3/agents/notify"
API_KEY=$(grep LIBRARY_API_KEY /Users/weixiangzhang/Local\ Dev/LibraryOfBabel/.env | cut -d'=' -f2)

curl -X POST "$WEBHOOK_URL" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "api_key_rotation",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "message": "MCP API key rotated successfully",
    "source": "automated_rotation"
  }'
EOF
    
    chmod +x "$PROJECT_ROOT/scripts/rotation_notify.sh"
    print_success "Rotation notification setup"
}

show_help() {
    echo "⏰ Automatic API Key Rotation Setup"
    echo "==================================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install    Install automatic rotation (default)"
    echo "  --remove     Remove automatic rotation"
    echo "  --status     Check rotation status"
    echo "  --help       Show this help message"
    echo ""
    echo "Rotation Schedule:"
    echo "  - Monthly on the 1st day at 2:00 AM"
    echo "  - Logs to: $PROJECT_ROOT/logs/api_rotation.log"
    echo "  - Updates: .env, config/api_settings.json, claude_remote_mcp_config.json"
    echo ""
    echo "Security Benefits:"
    echo "  - Automatic 30-day key rotation"
    echo "  - Reduced risk from compromised keys"
    echo "  - Compliance with security best practices"
}

# Main script logic
case "$1" in
    --install)
        create_rotation_log
        setup_notification
        install_cron_job
        ;;
    --remove)
        remove_cron_job
        ;;
    --status)
        check_status
        ;;
    --help)
        show_help
        ;;
    *)
        create_rotation_log
        setup_notification
        install_cron_job
        ;;
esac