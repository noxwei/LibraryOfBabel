#!/bin/bash
# GitHub Actions Self-Hosted Runner Setup for LibraryOfBabel
# This creates a local CI/CD environment that matches production exactly

set -e

echo "🚀 Setting up GitHub Actions Self-Hosted Runner for LibraryOfBabel"
echo "=================================================================="

# Create runner directory
RUNNER_DIR="/Users/weixiangzhang/actions-runner"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download latest runner
echo "📥 Downloading GitHub Actions runner..."
curl -o actions-runner-osx-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-osx-x64-2.311.0.tar.gz

# Extract
echo "📦 Extracting runner..."
tar xzf ./actions-runner-osx-x64-2.311.0.tar.gz

# Make executable
chmod +x ./config.sh
chmod +x ./run.sh

echo "✅ Runner files prepared"
echo ""
echo "🔧 NEXT STEPS:"
echo "1. Go to GitHub.com → Your repo → Settings → Actions → Runners"
echo "2. Click 'New self-hosted runner'"
echo "3. Select macOS and copy the config command"
echo "4. Run the config command in $RUNNER_DIR"
echo "5. Start the runner with: cd $RUNNER_DIR && ./run.sh"
echo ""
echo "💡 The runner will have access to:"
echo "   - Your PostgreSQL database"
echo "   - SSL certificates in ssl/ folder"
echo "   - Ollama models"
echo "   - Real environment variables"
echo "   - Direct port access (5562, 5568)"
echo ""
echo "🎯 This enables true production testing!"