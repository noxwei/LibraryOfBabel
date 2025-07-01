#!/bin/bash

# LibraryOfBabel QA Runner Script
# Comprehensive testing for MAM automation system

set -e

echo "🔬 LibraryOfBabel QA Testing Suite"
echo "=================================="

# Check dependencies
echo "📋 Checking system dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check Transmission CLI
if ! command -v transmission-remote &> /dev/null; then
    echo "⚠️ transmission-remote not found - Transmission tests will be skipped"
    echo "   Install with: brew install transmission"
fi

# Check if database exists
if [ ! -f "./audiobook_ebook_tracker.db" ]; then
    echo "⚠️ Database not found - some tests may fail"
fi

# Check if web frontend is running
WEB_RUNNING=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$WEB_RUNNING" != "200" ]; then
    echo "⚠️ Web frontend not running on port 3000 - web tests will fail"
    echo "   Start with: node web_frontend.js"
fi

echo ""
echo "🚀 Running QA tests..."

# Run QA agent with configuration
python3 qa_agent.py --config qa_config.json

echo ""
echo "✅ QA testing complete!"
echo "📊 Check qa_report_*.json for detailed results"