#!/bin/bash
# LibraryOfBabel Launch Agent Installation Script
# Installs background service for automatic ebook processing

set -e

echo "🚀 LibraryOfBabel Launch Agent Installation"
echo "============================================"

# Define paths
PLIST_SOURCE="config/macos/com.librarybabel.ebook-processor.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$LAUNCH_AGENTS_DIR/com.librarybabel.ebook-processor.plist"

# Create LaunchAgents directory if it doesn't exist
echo "📁 Creating LaunchAgents directory..."
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist file
echo "📋 Installing launch agent plist..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 644 "$PLIST_DEST"

# Unload existing agent if running
echo "⏹️ Stopping any existing agent..."
launchctl unload "$PLIST_DEST" 2>/dev/null || true

# Load the new agent
echo "🔄 Loading launch agent..."
launchctl load "$PLIST_DEST"

# Check if agent is loaded
echo "✅ Checking agent status..."
if launchctl list | grep -q "com.librarybabel.ebook-processor"; then
    echo "✅ SUCCESS: LibraryOfBabel ebook processor is now running!"
    echo ""
    echo "📥 Your system is now ready for drag-and-drop ebook processing!"
    echo "   - Drag EPUB files to: ebooks/downloads/"
    echo "   - Processing happens automatically in background"
    echo "   - Get notifications when complete"
    echo "   - Service auto-starts on system boot"
    echo ""
    echo "📊 To check logs:"
    echo "   tail -f logs/ebook-processor.out.log"
    echo "   tail -f logs/ebook-processor.err.log"
    echo ""
    echo "⏹️ To stop the service:"
    echo "   launchctl unload ~/Library/LaunchAgents/com.librarybabel.ebook-processor.plist"
    echo ""
    echo "🔄 To restart the service:"
    echo "   launchctl unload ~/Library/LaunchAgents/com.librarybabel.ebook-processor.plist"
    echo "   launchctl load ~/Library/LaunchAgents/com.librarybabel.ebook-processor.plist"
else
    echo "❌ ERROR: Failed to load launch agent"
    echo "Check the plist file and try again"
    exit 1
fi