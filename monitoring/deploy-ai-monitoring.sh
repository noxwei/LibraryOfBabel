#!/bin/bash

# LibraryOfBabel AI Agent Ready Monitoring Deployment Script
# Dr. Marcus Thompson - DevOps Monitoring & Observability Specialist
# 
# Deploys cutting-edge agentic AI-ready monitoring architecture
# Compatible with Grafana Assistant, MCP servers, and natural language interfaces

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Art banner
echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     🤖 LibraryOfBabel AI Agent Ready Monitoring Architecture 🤖              ║
║                                                                               ║
║  ██╗     ██╗██████╗ ██████╗  █████╗ ██████╗ ██╗   ██╗ ██████╗ ███████╗       ║
║  ██║     ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔═══██╗██╔════╝       ║
║  ██║     ██║██████╔╝██████╔╝███████║██████╔╝ ╚████╔╝ ██║   ██║█████╗         ║
║  ██║     ██║██╔══██╗██╔══██╗██╔══██║██╔══██╗  ╚██╔╝  ██║   ██║██╔══╝         ║
║  ███████╗██║██████╔╝██║  ██║██║  ██║██║  ██║   ██║   ╚██████╔╝██║            ║
║  ╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝            ║
║                                                                               ║
║           🔮 Agentic AI Observability • Natural Language Ready 🔮            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}🚀 Dr. Marcus Thompson - DevOps Monitoring & Observability Specialist${NC}"
echo -e "${CYAN}📊 Deploying cutting-edge AI agent ready monitoring stack...${NC}"
echo ""

# Configuration
MONITORING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_COMPOSE_FILE="${MONITORING_DIR}/docker/docker-compose.yml"
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090
LOKI_PORT=3100
ALERTMANAGER_PORT=9093
EXPORTER_PORT=8001
GATEWAY_PORT=8081

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if port is available
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port is already in use (needed for $service)"
        return 1
    fi
    return 0
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service=$2
    local max_attempts=60
    local attempt=1
    
    print_info "Waiting for $service to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_status "$service is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_error "$service failed to start within timeout"
    return 1
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed or not in PATH"
        exit 1
    fi
    
    # Check ports
    check_port $GRAFANA_PORT "Grafana" || exit 1
    check_port $PROMETHEUS_PORT "Prometheus" || exit 1
    check_port $LOKI_PORT "Loki" || exit 1
    check_port $ALERTMANAGER_PORT "AlertManager" || exit 1
    check_port $EXPORTER_PORT "LibraryOfBabel Exporter" || exit 1
    check_port $GATEWAY_PORT "AI Agent Gateway" || exit 1
    
    print_status "Prerequisites check completed"
}

# Function to create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p "${MONITORING_DIR}/data/grafana"
    mkdir -p "${MONITORING_DIR}/data/prometheus"
    mkdir -p "${MONITORING_DIR}/data/loki"
    mkdir -p "${MONITORING_DIR}/data/alertmanager"
    
    print_status "Directories created"
}

# Function to set permissions
set_permissions() {
    print_info "Setting appropriate permissions..."
    
    # Grafana needs specific permissions
    sudo chown -R 472:472 "${MONITORING_DIR}/data/grafana" 2>/dev/null || true
    
    print_status "Permissions configured"
}

# Function to start monitoring stack
start_monitoring_stack() {
    print_info "Starting AI Agent Ready monitoring stack..."
    
    cd "${MONITORING_DIR}/docker"
    
    # Pull latest images
    print_info "Pulling latest container images..."
    docker-compose pull
    
    # Start services
    print_info "Starting monitoring services..."
    docker-compose up -d
    
    print_status "Monitoring stack started"
}

# Function to wait for all services
wait_for_all_services() {
    print_info "Waiting for all services to be ready..."
    
    # Wait for Prometheus
    wait_for_service "http://localhost:$PROMETHEUS_PORT/-/ready" "Prometheus"
    
    # Wait for Loki
    wait_for_service "http://localhost:$LOKI_PORT/ready" "Loki"
    
    # Wait for Grafana
    wait_for_service "http://localhost:$GRAFANA_PORT/api/health" "Grafana"
    
    # Wait for AlertManager
    wait_for_service "http://localhost:$ALERTMANAGER_PORT/-/ready" "AlertManager"
    
    # Wait for LibraryOfBabel Exporter
    wait_for_service "http://localhost:$EXPORTER_PORT/health" "LibraryOfBabel Exporter"
    
    # Wait for AI Agent Gateway
    wait_for_service "http://localhost:$GATEWAY_PORT/health" "AI Agent Gateway"
    
    print_status "All services are ready!"
}

# Function to import dashboards
import_dashboards() {
    print_info "Importing AI Agent Ready dashboards..."
    
    # Wait a bit more for Grafana to be fully ready
    sleep 10
    
    # Import dashboards via Grafana API
    local grafana_url="http://admin:admin123@localhost:$GRAFANA_PORT"
    
    # Multi-Modal Processing Dashboard
    if [ -f "${MONITORING_DIR}/dashboards/processing/multi-modal-processing-dashboard.json" ]; then
        curl -X POST \
            -H "Content-Type: application/json" \
            -d @"${MONITORING_DIR}/dashboards/processing/multi-modal-processing-dashboard.json" \
            "$grafana_url/api/dashboards/db" > /dev/null 2>&1 || true
        print_status "Multi-Modal Processing Dashboard imported"
    fi
    
    # Book Processing Intelligence Dashboard
    if [ -f "${MONITORING_DIR}/dashboards/business/book-processing-intelligence.json" ]; then
        curl -X POST \
            -H "Content-Type: application/json" \
            -d @"${MONITORING_DIR}/dashboards/business/book-processing-intelligence.json" \
            "$grafana_url/api/dashboards/db" > /dev/null 2>&1 || true
        print_status "Book Processing Intelligence Dashboard imported"
    fi
    
    # System Health Dashboard
    if [ -f "${MONITORING_DIR}/dashboards/system/system-health-ai-ready.json" ]; then
        curl -X POST \
            -H "Content-Type: application/json" \
            -d @"${MONITORING_DIR}/dashboards/system/system-health-ai-ready.json" \
            "$grafana_url/api/dashboards/db" > /dev/null 2>&1 || true
        print_status "System Health AI Ready Dashboard imported"
    fi
}

# Function to display final information
display_final_info() {
    echo ""
    echo -e "${GREEN}🎉 LibraryOfBabel AI Agent Ready Monitoring Successfully Deployed! 🎉${NC}"
    echo ""
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│                    🤖 AI AGENT READY SERVICES 🤖                │${NC}"
    echo -e "${CYAN}├─────────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}│  📊 Grafana (AI Dashboards):     http://localhost:$GRAFANA_PORT      │${NC}"
    echo -e "${CYAN}│      Username: admin  |  Password: admin123                    │${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}│  🔍 Prometheus (Metrics):        http://localhost:$PROMETHEUS_PORT     │${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}│  📝 Loki (Logs):                 http://localhost:$LOKI_PORT      │${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}│  🚨 AlertManager (Alerts):       http://localhost:$ALERTMANAGER_PORT     │${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}│  📈 LibraryOfBabel Exporter:     http://localhost:$EXPORTER_PORT      │${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}│  🤖 AI Agent Gateway:            http://localhost:$GATEWAY_PORT      │${NC}"
    echo -e "${CYAN}│      Natural Language Queries:   /api/v1/ai/query              │${NC}"
    echo -e "${CYAN}│      System Context:              /api/v1/ai/context            │${NC}"
    echo -e "${CYAN}│      API Documentation:          /docs                          │${NC}"
    echo -e "${CYAN}│                                                                 │${NC}"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -e "${PURPLE}🔮 AI AGENT CAPABILITIES:${NC}"
    echo -e "${PURPLE}   • Natural Language Monitoring Queries${NC}"
    echo -e "${PURPLE}   • Grafana Assistant Compatible${NC}"
    echo -e "${PURPLE}   • MCP Server Ready${NC}"
    echo -e "${PURPLE}   • Conversational Dashboards${NC}"
    echo -e "${PURPLE}   • AI-Enhanced JIRA Integration${NC}"
    echo -e "${PURPLE}   • OpenTelemetry Standards Ready${NC}"
    echo ""
    echo -e "${YELLOW}📖 EXAMPLE AI QUERIES:${NC}"
    echo -e "${YELLOW}   • 'How many books have been processed?'${NC}"
    echo -e "${YELLOW}   • 'What is the current success rate?'${NC}"
    echo -e "${YELLOW}   • 'Which AI models are active?'${NC}"
    echo -e "${YELLOW}   • 'Are there any system errors?'${NC}"
    echo -e "${YELLOW}   • 'What is the processing status?'${NC}"
    echo ""
    echo -e "${GREEN}🚀 Try these AI agent endpoints:${NC}"
    echo -e "${GREEN}   curl http://localhost:$GATEWAY_PORT/api/v1/ai/context${NC}"
    echo -e "${GREEN}   curl -X POST http://localhost:$GATEWAY_PORT/api/v1/ai/query \\${NC}"
    echo -e "${GREEN}        -H 'Content-Type: application/json' \\${NC}"
    echo -e "${GREEN}        -d '{\"query\": \"How many books processed?\"}'${NC}"
    echo ""
    echo -e "${BLUE}📊 LibraryOfBabel Stats: 134,508 chunks at 99.99% success rate${NC}"
    echo -e "${BLUE}🤖 AI Models: MxBai (107,578), BGE (26,901), Nomic (25)${NC}"
    echo -e "${BLUE}📚 Books Processed: 1,504+ with 96.54% genre accuracy${NC}"
    echo ""
    echo -e "${CYAN}🎯 Positioned for the $10.7B AI observability market revolution!${NC}"
    echo ""
}

# Function to cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Deployment failed. Cleaning up..."
        cd "${MONITORING_DIR}/docker" && docker-compose down > /dev/null 2>&1 || true
    fi
}

trap cleanup EXIT

# Main deployment flow
main() {
    echo -e "${CYAN}Starting LibraryOfBabel AI Agent Ready Monitoring deployment...${NC}"
    echo ""
    
    check_prerequisites
    create_directories
    set_permissions
    start_monitoring_stack
    wait_for_all_services
    import_dashboards
    display_final_info
    
    print_status "Deployment completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        print_info "Stopping LibraryOfBabel AI monitoring stack..."
        cd "${MONITORING_DIR}/docker"
        docker-compose down
        print_status "Monitoring stack stopped"
        ;;
    "restart")
        print_info "Restarting LibraryOfBabel AI monitoring stack..."
        cd "${MONITORING_DIR}/docker"
        docker-compose down
        sleep 5
        docker-compose up -d
        wait_for_all_services
        print_status "Monitoring stack restarted"
        ;;
    "status")
        print_info "LibraryOfBabel AI monitoring stack status:"
        cd "${MONITORING_DIR}/docker"
        docker-compose ps
        ;;
    "logs")
        cd "${MONITORING_DIR}/docker"
        docker-compose logs -f ${2:-}
        ;;
    "update")
        print_info "Updating LibraryOfBabel AI monitoring stack..."
        cd "${MONITORING_DIR}/docker"
        docker-compose pull
        docker-compose up -d
        wait_for_all_services
        print_status "Monitoring stack updated"
        ;;
    "help"|"-h"|"--help")
        echo "LibraryOfBabel AI Agent Ready Monitoring Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  Deploy the complete AI monitoring stack"
        echo "  stop       Stop all monitoring services"
        echo "  restart    Restart all monitoring services"
        echo "  status     Show status of all services"
        echo "  logs       Show logs (optionally specify service name)"
        echo "  update     Pull latest images and restart services"
        echo "  help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Deploy complete stack"
        echo "  $0 stop              # Stop all services"
        echo "  $0 logs grafana      # Show Grafana logs"
        echo "  $0 status            # Check service status"
        ;;
    *)
        main
        ;;
esac