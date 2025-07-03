#!/bin/bash
# LibraryOfBabel Drag-and-Drop Status Checker

echo "🔍 LibraryOfBabel Drag-and-Drop Status Check"
echo "============================================"

# Check launch agent
echo "📋 Checking background service..."
if launchctl list | grep -q "com.librarybabel.ebook-processor"; then
    echo "✅ Background service is RUNNING"
    echo "   Status: $(launchctl list | grep com.librarybabel.ebook-processor)"
else
    echo "❌ Background service is NOT running"
fi

echo ""

# Check for manual process
echo "🔄 Checking manual processes..."
if ps aux | grep -q "[a]utomated_ebook_processor"; then
    echo "✅ Manual process is RUNNING"
    echo "   Process: $(ps aux | grep [a]utomated_ebook_processor | awk '{print $2, $11, $12, $13, $14}')"
else
    echo "❌ No manual process running"
fi

echo ""

# Check logs
echo "📊 Checking recent logs..."
if [ -f "logs/ebook-processor.out.log" ]; then
    echo "✅ Service logs found"
    echo "   Latest: $(tail -1 logs/ebook-processor.out.log 2>/dev/null || echo 'No recent entries')"
elif [ -f "ebook_processor.log" ]; then
    echo "✅ Processing logs found"  
    echo "   Latest: $(tail -1 ebook_processor.log 2>/dev/null || echo 'No recent entries')"
else
    echo "❌ No log files found"
fi

echo ""

# Check directories
echo "📁 Checking folder structure..."
if [ -d "ebooks/downloads" ]; then
    files_count=$(find ebooks/downloads -name "*.epub" -o -name "*.mobi" -o -name "*.azw3" -o -name "*.azw" 2>/dev/null | wc -l)
    echo "✅ Downloads folder exists with $files_count ebook(s) waiting"
else
    echo "❌ Downloads folder not found"
fi

echo ""

# Recommendations
echo "🚀 Quick Actions:"
echo ""
echo "   Start real-time monitoring:"
echo "   python3 src/automated_ebook_processor.py --mode realtime"
echo ""
echo "   Install background service:"
echo "   ./install-launch-agent.sh"
echo ""
echo "   Test with file drop:"
echo "   # Drag an EPUB to ebooks/downloads/ folder"