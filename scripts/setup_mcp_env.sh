#!/bin/bash
# 🔐 MCP ENVIRONMENT SETUP SCRIPT
# ===============================
# 
# Sets up environment variables for the Remote MCP server.
# Handles 30-day API key rotation automatically.
# 
# Usage:
#     ./scripts/setup_mcp_env.sh [--rotate-key]
# 
# Options:
#     --rotate-key    Generate new API key and update environment
#     --test         Test current environment configuration
#     --help         Show this help message

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/Users/weixiangzhang/Local Dev/LibraryOfBabel"
ENV_FILE="$PROJECT_ROOT/.env"
CONFIG_FILE="$PROJECT_ROOT/config/api_settings.json"

print_header() {
    echo -e "${BLUE}🔐 MCP Environment Setup${NC}"
    echo -e "${BLUE}========================${NC}"
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

generate_api_key() {
    # Generate a secure API key
    openssl rand -hex 32
}

get_current_api_key() {
    # Get current API key from config
    python3 -c "
import json
import os
config_file = '$CONFIG_FILE'
if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    print(config.get('api', {}).get('api_key', ''))
else:
    print('')
"
}

update_env_file() {
    local api_key="$1"
    
    # Create or update .env file
    if [ -f "$ENV_FILE" ]; then
        # Update existing file
        if grep -q "LIBRARY_API_KEY" "$ENV_FILE"; then
            sed -i "" "s/LIBRARY_API_KEY=.*/LIBRARY_API_KEY=$api_key/" "$ENV_FILE"
        else
            echo "LIBRARY_API_KEY=$api_key" >> "$ENV_FILE"
        fi
    else
        # Create new file
        cat > "$ENV_FILE" << EOF
# Library of Babel MCP Environment Variables
# Updated: $(date)
LIBRARY_API_KEY=$api_key
EOF
    fi
    
    print_success "Environment file updated: $ENV_FILE"
}

update_config_file() {
    local api_key="$1"
    
    # Update API config using Python
    python3 -c "
import json
import os
from datetime import datetime

config_file = '$CONFIG_FILE'
api_key = '$api_key'

if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Update API key
    config['api']['api_key'] = api_key
    config['last_updated'] = datetime.now().isoformat() + 'Z'
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print('Config updated successfully')
else:
    print('Config file not found')
"
    
    print_success "Configuration file updated: $CONFIG_FILE"
}

rotate_api_key() {
    print_header
    echo "🔄 Rotating API key..."
    
    # Generate new API key
    new_key=$(generate_api_key)
    
    # Update files
    update_env_file "$new_key"
    update_config_file "$new_key"
    
    # Update Claude configuration
    update_claude_config "$new_key"
    
    print_success "API key rotated successfully"
    print_warning "New key: ${new_key:0:20}..."
    print_warning "Remember to restart your MCP server!"
}

update_claude_config() {
    local api_key="$1"
    local claude_config="$PROJECT_ROOT/claude_remote_mcp_config.json"
    
    # Update Claude configuration
    python3 -c "
import json
import os

config_file = '$claude_config'
api_key = '$api_key'

if os.path.exists(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Update API key in environment
    config['mcpServers']['library-of-babel']['env']['LIBRARY_API_KEY'] = api_key
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print('Claude config updated')
else:
    print('Claude config not found')
"
    
    print_success "Claude configuration updated"
}

test_environment() {
    print_header
    echo "🧪 Testing MCP environment..."
    
    # Check .env file
    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        if [ -n "$LIBRARY_API_KEY" ]; then
            print_success "Environment variable set: LIBRARY_API_KEY=${LIBRARY_API_KEY:0:20}..."
        else
            print_error "LIBRARY_API_KEY not set in .env file"
        fi
    else
        print_error ".env file not found"
    fi
    
    # Check config file
    current_key=$(get_current_api_key)
    if [ -n "$current_key" ]; then
        print_success "Config file key: ${current_key:0:20}..."
    else
        print_error "No API key found in config file"
    fi
    
    # Test API connection
    echo "🔗 Testing API connection..."
    response=$(curl -s -H "Authorization: Bearer $LIBRARY_API_KEY" https://api.ashortstayinhell.com:5562/health)
    
    if echo "$response" | grep -q "success"; then
        print_success "API connection successful"
    else
        print_error "API connection failed"
    fi
}

setup_initial_environment() {
    print_header
    echo "🚀 Setting up initial MCP environment..."
    
    # Get current API key from config
    current_key=$(get_current_api_key)
    
    if [ -n "$current_key" ]; then
        print_success "Found existing API key in config"
        update_env_file "$current_key"
        update_claude_config "$current_key"
    else
        print_warning "No API key found, generating new one..."
        rotate_api_key
        return
    fi
    
    print_success "MCP environment setup complete!"
}

show_help() {
    echo "🔐 MCP Environment Setup Script"
    echo "==============================="
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --rotate-key    Generate new API key and update environment"
    echo "  --test         Test current environment configuration"
    echo "  --help         Show this help message"
    echo ""
    echo "Files managed:"
    echo "  - $ENV_FILE"
    echo "  - $CONFIG_FILE"
    echo "  - $PROJECT_ROOT/claude_remote_mcp_config.json"
    echo ""
    echo "30-day rotation reminder:"
    echo "  Run with --rotate-key every 30 days to maintain security"
}

# Main script logic
case "$1" in
    --rotate-key)
        rotate_api_key
        ;;
    --test)
        test_environment
        ;;
    --help)
        show_help
        ;;
    *)
        setup_initial_environment
        ;;
esac