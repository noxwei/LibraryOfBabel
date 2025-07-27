#!/bin/bash
"""
🔐 LibraryOfBabel Environment Setup Script
==========================================

This script helps you set up the BABEL_API_KEY and BABEL_API_BASE_URL
environment variables for the LibraryOfBabel project.

Usage:
    ./scripts/setup_api_key.sh [your_api_key] [your_base_url]

If no arguments are provided, the script will prompt you to enter them.
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 LibraryOfBabel Environment Setup${NC}"
echo "=========================================="

# Check if arguments were provided
if [ $# -eq 2 ]; then
    API_KEY="$1"
    BASE_URL="$2"
elif [ $# -eq 1 ]; then
    API_KEY="$1"
    echo -e "${YELLOW}Please enter your LibraryOfBabel API base URL:${NC}"
    read BASE_URL
else
    echo -e "${YELLOW}Please enter your LibraryOfBabel API key:${NC}"
    read -s API_KEY
    echo
    echo -e "${YELLOW}Please enter your LibraryOfBabel API base URL:${NC}"
    read BASE_URL
fi

# Validate API key format (basic check)
if [[ $API_KEY =~ ^babel_secure_[a-f0-9]{32}$ ]]; then
    echo -e "${GREEN}✅ Valid API key format detected${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: API key doesn't match expected format${NC}"
    echo "Expected format: babel_secure_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
fi

# Validate base URL format (basic check)
if [[ $BASE_URL =~ ^https?://[^/]+ ]]; then
    echo -e "${GREEN}✅ Valid base URL format detected${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Base URL doesn't match expected format${NC}"
    echo "Expected format: https://domain.com:port"
fi

# Set environment variables for current session
export BABEL_API_KEY="$API_KEY"
export BABEL_API_BASE_URL="$BASE_URL"
echo -e "${GREEN}✅ Environment variables set for current session${NC}"

# Add to shell profile for permanent setup
SHELL_PROFILE=""
if [ -f "$HOME/.zshrc" ]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_PROFILE="$HOME/.bash_profile"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_PROFILE="$HOME/.bashrc"
fi

if [ -n "$SHELL_PROFILE" ]; then
    # Remove any existing BABEL_API_KEY and BABEL_API_BASE_URL lines
    sed -i.bak '/export BABEL_API_KEY=/d' "$SHELL_PROFILE"
    sed -i.bak '/export BABEL_API_BASE_URL=/d' "$SHELL_PROFILE"
    
    # Add new environment variables
    echo "export BABEL_API_KEY=\"$API_KEY\"" >> "$SHELL_PROFILE"
    echo "export BABEL_API_BASE_URL=\"$BASE_URL\"" >> "$SHELL_PROFILE"
    echo -e "${GREEN}✅ Environment variables added to $SHELL_PROFILE${NC}"
    echo -e "${BLUE}💡 Run 'source $SHELL_PROFILE' to apply changes${NC}"
else
    echo -e "${RED}❌ Could not find shell profile file${NC}"
    echo "Please manually add the following to your shell profile:"
echo "export BABEL_API_KEY=\"YOUR_API_KEY_HERE\""
echo "export BABEL_API_BASE_URL=\"YOUR_BASE_URL_HERE\""
fi

# Test the configuration
echo -e "${BLUE}🧪 Testing configuration...${NC}"
python3 -c "
import os
api_key = os.getenv('BABEL_API_KEY')
base_url = os.getenv('BABEL_API_BASE_URL')

if api_key:
    print('✅ BABEL_API_KEY is set')
    print(f'   Key: {api_key[:20]}...{api_key[-4:]}')
else:
    print('❌ BABEL_API_KEY not found')

if base_url:
    print('✅ BABEL_API_BASE_URL is set')
    print(f'   URL: {base_url}')
else:
    print('❌ BABEL_API_BASE_URL not found')
"

echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${BLUE}📚 You can now run LibraryOfBabel scripts${NC}" 