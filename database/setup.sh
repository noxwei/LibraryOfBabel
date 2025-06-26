#!/bin/bash

# LibraryOfBabel PostgreSQL Database Setup Script
# This script installs PostgreSQL and sets up the knowledge base database

set -e  # Exit on any error

echo "🚀 Starting LibraryOfBabel Database Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    print_error "Homebrew is not installed. Please install Homebrew first:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Check if PostgreSQL is already installed
if command -v psql &> /dev/null; then
    print_warning "PostgreSQL is already installed"
    POSTGRES_VERSION=$(psql --version | grep -oE '[0-9]+\.[0-9]+')
    print_status "Current version: $POSTGRES_VERSION"
else
    print_status "Installing PostgreSQL 15..."
    brew install postgresql@15
    
    # Add PostgreSQL to PATH
    print_status "Adding PostgreSQL to PATH..."
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_CONFIG="$HOME/.zshrc"
    else
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
    
    if ! grep -q "/opt/homebrew/opt/postgresql@15/bin" "$SHELL_CONFIG" 2>/dev/null; then
        echo 'export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"' >> "$SHELL_CONFIG"
        print_status "Added to $SHELL_CONFIG"
    fi
    
    # Source the path for current session
    export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
    
    print_success "PostgreSQL 15 installed successfully"
fi

# Start PostgreSQL service
print_status "Starting PostgreSQL service..."
brew services start postgresql@15 || print_warning "PostgreSQL service may already be running"

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
sleep 3

# Create the knowledge_base database if it doesn't exist
print_status "Creating knowledge_base database..."
if ! psql postgres -lqt | cut -d \| -f 1 | grep -qw knowledge_base; then
    createdb knowledge_base
    print_success "Created knowledge_base database"
else
    print_warning "knowledge_base database already exists"
fi

# Set up database schema
print_status "Setting up database schema..."
DB_DIR="$(dirname "$0")"

if [ -f "$DB_DIR/schema.sql" ]; then
    psql knowledge_base -f "$DB_DIR/schema.sql"
    print_success "Database schema created"
else
    print_error "schema.sql not found in $DB_DIR"
    exit 1
fi

# Set up search optimization
if [ -f "$DB_DIR/search_optimization.sql" ]; then
    print_status "Setting up search optimization..."
    psql knowledge_base -f "$DB_DIR/search_optimization.sql"
    print_success "Search optimization configured"
else
    print_warning "search_optimization.sql not found, skipping optimization"
fi

# Check database connection
print_status "Testing database connection..."
if psql knowledge_base -c "SELECT version();" > /dev/null 2>&1; then
    print_success "Database connection successful"
else
    print_error "Failed to connect to database"
    exit 1
fi

print_success "Database setup completed successfully!"
echo ""
echo "📊 Database Information:"
echo "  Database Name: knowledge_base"
echo "  Connection: psql knowledge_base"
echo "  Status: Ready for data ingestion"
echo ""
echo "🔧 Next Steps:"
echo "  1. Run: python3 database/ingest_data.py"
echo "  2. Test queries: psql knowledge_base -f database/test_queries.sql"
echo ""
print_success "Setup complete! Your LibraryOfBabel database is ready."