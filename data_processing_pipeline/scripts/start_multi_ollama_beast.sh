#!/bin/bash
# Multi-Ollama Beast Mode Startup Script
# LibraryOfBabel Embedding Pipeline v2.0

set -e  # Exit on any error

echo "🚀 Starting Multi-Ollama Beast Mode"
echo "==================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
CONFIG_DIR="$SCRIPT_DIR/../configs"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if Ollama is installed
    if ! command -v ollama >/dev/null 2>&1; then
        error "Ollama not installed. Please install Ollama first."
        exit 1
    fi
    
    # Check if PostgreSQL is accessible
    if ! command -v psql >/dev/null 2>&1; then
        error "PostgreSQL client not installed."
        exit 1
    fi
    
    # Test database connection
    if ! psql -d knowledge_base -c "SELECT 1;" >/dev/null 2>&1; then
        error "Cannot connect to knowledge_base database."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        error "Python 3 not installed."
        exit 1
    fi
    
    # Check system resources
    local memory_gb=$(sysctl -n hw.memsize | awk '{print int($1/1024/1024/1024)}')
    if [ "$memory_gb" -lt 16 ]; then
        warning "System has only ${memory_gb}GB RAM. Recommended: 32GB+"
    fi
    
    log "✅ Prerequisites check passed"
}

# Clean up existing instances
cleanup_existing() {
    log "🧹 Cleaning up existing instances..."
    
    # Kill existing Ollama processes
    if pgrep -f "ollama serve" >/dev/null; then
        log "Stopping existing Ollama instances..."
        pkill -f "ollama serve" || true
        sleep 5
    fi
    
    # Kill existing daemon
    if pgrep -f "multi_ollama_bge_daemon" >/dev/null; then
        log "Stopping existing BGE daemon..."
        pkill -f "multi_ollama_bge_daemon" || true
        sleep 3
    fi
    
    # Check for port conflicts
    for port in 11434 11435 11436; do
        if lsof -i :$port >/dev/null 2>&1; then
            warning "Port $port is in use, attempting to free it..."
            kill -9 $(lsof -ti :$port) 2>/dev/null || true
        fi
    done
    
    log "✅ Cleanup complete"
}

# Start Ollama instances
start_ollama_instances() {
    log "🔧 Starting Ollama instances..."
    
    # Start primary instance (11434)
    log "Starting primary Ollama instance (port 11434)..."
    ollama serve > "$LOG_DIR/ollama_11434.log" 2>&1 &
    local primary_pid=$!
    
    # Wait a moment for primary to start
    sleep 5
    
    # Start secondary instance (11435)
    log "Starting secondary Ollama instance (port 11435)..."
    OLLAMA_HOST=127.0.0.1:11435 ollama serve > "$LOG_DIR/ollama_11435.log" 2>&1 &
    local secondary_pid=$!
    
    # Wait a moment
    sleep 3
    
    # Start tertiary instance (11436)
    log "Starting tertiary Ollama instance (port 11436)..."
    OLLAMA_HOST=127.0.0.1:11436 ollama serve > "$LOG_DIR/ollama_11436.log" 2>&1 &
    local tertiary_pid=$!
    
    # Wait for all instances to start
    log "⏳ Waiting for instances to start..."
    sleep 10
    
    # Verify instances are running
    local healthy_count=0
    for port in 11434 11435 11436; do
        if curl -s "http://localhost:$port/api/ps" >/dev/null 2>&1; then
            log "✅ Port $port: Instance running"
            ((healthy_count++))
        else
            error "❌ Port $port: Instance failed to start"
        fi
    done
    
    if [ "$healthy_count" -ne 3 ]; then
        error "Only $healthy_count/3 instances started successfully"
        exit 1
    fi
    
    # Save PIDs
    echo "$primary_pid" > "$LOG_DIR/ollama_11434.pid"
    echo "$secondary_pid" > "$LOG_DIR/ollama_11435.pid" 
    echo "$tertiary_pid" > "$LOG_DIR/ollama_11436.pid"
    
    log "✅ All Ollama instances started successfully"
}

# Load BGE-M3 models
load_models() {
    log "📥 Loading BGE-M3 models..."
    
    # Load on primary instance (11434)
    log "Loading BGE-M3 on primary instance..."
    if ! ollama pull bge-m3; then
        error "Failed to load BGE-M3 on primary instance"
        exit 1
    fi
    
    # Load on secondary instance (11435)
    log "Loading BGE-M3 on secondary instance..."
    if ! curl -s -X POST "http://localhost:11435/api/pull" \
         -H "Content-Type: application/json" \
         -d '{"name":"bge-m3"}' >/dev/null; then
        error "Failed to load BGE-M3 on secondary instance"
        exit 1
    fi
    
    # Load on tertiary instance (11436)
    log "Loading BGE-M3 on tertiary instance..."
    if ! curl -s -X POST "http://localhost:11436/api/pull" \
         -H "Content-Type: application/json" \
         -d '{"name":"bge-m3"}' >/dev/null; then
        error "Failed to load BGE-M3 on tertiary instance"
        exit 1
    fi
    
    log "✅ BGE-M3 models loaded on all instances"
}

# Verify setup
verify_setup() {
    log "🔍 Verifying setup..."
    
    local healthy_models=0
    for port in 11434 11435 11436; do
        if curl -s "http://localhost:$port/api/ps" | grep -q "bge-m3"; then
            log "✅ Port $port: BGE-M3 loaded and ready"
            ((healthy_models++))
        else
            error "❌ Port $port: BGE-M3 not loaded"
        fi
    done
    
    if [ "$healthy_models" -ne 3 ]; then
        error "Only $healthy_models/3 instances have BGE-M3 loaded"
        exit 1
    fi
    
    # Test embedding generation
    log "🧪 Testing embedding generation..."
    local test_response=$(curl -s -X POST "http://localhost:11434/api/embeddings" \
        -H "Content-Type: application/json" \
        -d '{"model":"bge-m3","prompt":"test embedding"}')
    
    if echo "$test_response" | grep -q "embedding"; then
        log "✅ Embedding generation test passed"
    else
        error "❌ Embedding generation test failed"
        exit 1
    fi
    
    log "✅ Setup verification complete"
}

# Display status
display_status() {
    echo ""
    log "🎉 Multi-Ollama Beast Mode Setup Complete!"
    echo "========================================"
    echo ""
    echo -e "${BLUE}Configuration:${NC}"
    echo "  • 3 Ollama instances running (ports 11434, 11435, 11436)"
    echo "  • BGE-M3 model loaded on all instances"
    echo "  • Ready for 42-worker load-balanced processing"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Start the multi-Ollama daemon:"
    echo "     cd $SCRIPT_DIR"
    echo "     nohup python3 multi_ollama_bge_daemon.py 42 > ../logs/daemon.log 2>&1 &"
    echo "     disown"
    echo ""
    echo "  2. Monitor progress:"
    echo "     tail -f ../logs/daemon.log"
    echo ""
    echo "  3. Check system health:"
    echo "     ./health_check_multi_ollama.sh"
    echo ""
    echo -e "${BLUE}Log Files:${NC}"
    echo "  • Ollama instances: $LOG_DIR/ollama_*.log"
    echo "  • Process IDs: $LOG_DIR/ollama_*.pid"
    echo ""
    echo -e "${GREEN}🚀 Ready to process 1.5M+ embeddings at 51K+/hour!${NC}"
}

# Main execution
main() {
    # Trap to cleanup on exit
    trap 'error "Script interrupted. Cleaning up..."; cleanup_existing; exit 1' INT TERM
    
    check_prerequisites
    cleanup_existing
    start_ollama_instances
    load_models
    verify_setup
    display_status
    
    log "✅ Multi-Ollama Beast Mode startup complete!"
}

# Run main function
main "$@"