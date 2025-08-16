#!/bin/bash
# LibraryOfBabel Database Manager
# Flyway wrapper for database migrations and operations

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/Users/weixiangzhang/Local_Dev/LibraryOfBabel"
FLYWAY_DIR="$PROJECT_DIR/flyway"
FLYWAY_CONF="$FLYWAY_DIR/conf/flyway.conf"
LOGS_DIR="$PROJECT_DIR/logs"
BACKUP_DIR="$PROJECT_DIR/backups/database"

# Database configurations
PRODUCTION_DB="knowledge_base"
STAGING_DB="library_staging"
TEST_DB="library_test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] DB:${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create necessary directories
mkdir -p "$LOGS_DIR" "$BACKUP_DIR"

# Check if Flyway is installed
check_flyway() {
    if ! command -v flyway &> /dev/null; then
        error "Flyway is not installed. Please install it first:"
        echo "  brew install flyway"
        echo "  Or download from: https://flywaydb.org/download/"
        exit 1
    fi
}

# Get database URL for environment
get_db_url() {
    local env=$1
    case $env in
        "production")
            echo "jdbc:postgresql://localhost:5432/$PRODUCTION_DB"
            ;;
        "staging")
            echo "jdbc:postgresql://localhost:5432/$STAGING_DB"
            ;;
        "test")
            echo "jdbc:postgresql://localhost:5432/$TEST_DB"
            ;;
        *)
            error "Unknown environment: $env"
            exit 1
            ;;
    esac
}

# Create database if it doesn't exist
create_database() {
    local env=$1
    local db_name
    
    case $env in
        "production") db_name=$PRODUCTION_DB ;;
        "staging") db_name=$STAGING_DB ;;
        "test") db_name=$TEST_DB ;;
        *) error "Unknown environment: $env"; exit 1 ;;
    esac
    
    log "Creating database $db_name if it doesn't exist..."
    
    # Check if database exists
    if psql -U weixiangzhang -lqt | cut -d \| -f 1 | grep -qw "$db_name"; then
        success "Database $db_name already exists"
    else
        log "Creating database $db_name..."
        createdb -U weixiangzhang "$db_name"
        success "Database $db_name created"
    fi
}

# Run Flyway command with environment-specific settings
run_flyway() {
    local env=$1
    local command=$2
    shift 2
    local extra_args="$@"
    
    local db_url=$(get_db_url "$env")
    
    log "Running Flyway $command on $env environment..."
    
    cd "$PROJECT_DIR"
    
    # Set environment variables for Flyway
    export FLYWAY_URL="$db_url"
    export FLYWAY_USER="weixiangzhang"
    export FLYWAY_LOCATIONS="filesystem:$FLYWAY_DIR/sql"
    export FLYWAY_CONFIG_FILES="$FLYWAY_CONF"
    
    # Run Flyway command
    flyway -configFiles="$FLYWAY_CONF" \
           -url="$db_url" \
           -user="weixiangzhang" \
           -locations="filesystem:$FLYWAY_DIR/sql" \
           "$command" $extra_args
}

# Backup database schema and functions
backup_database() {
    local env=$1
    local db_name
    
    case $env in
        "production") db_name=$PRODUCTION_DB ;;
        "staging") db_name=$STAGING_DB ;;
        *) error "Backup only supported for production and staging"; exit 1 ;;
    esac
    
    local backup_timestamp=$(date +"%Y%m%d_%H%M%S")
    local schema_backup="$BACKUP_DIR/${env}_schema_${backup_timestamp}.sql"
    local functions_backup="$BACKUP_DIR/${env}_functions_${backup_timestamp}.sql"
    
    log "Creating database backup for $env environment..."
    
    # Backup schema structure
    pg_dump -U weixiangzhang \
            -d "$db_name" \
            --schema-only \
            --no-owner \
            --no-privileges \
            -f "$schema_backup"
    
    # Backup functions specifically
    pg_dump -U weixiangzhang \
            -d "$db_name" \
            --schema-only \
            --no-owner \
            --no-privileges \
            -t "flyway_schema_history" \
            -f "$functions_backup"
    
    success "Database backup created:"
    echo "  Schema: $schema_backup"
    echo "  Functions: $functions_backup"
    
    # Keep only last 10 backups
    ls -t "$BACKUP_DIR"/${env}_schema_*.sql | tail -n +11 | xargs rm -f 2>/dev/null || true
    ls -t "$BACKUP_DIR"/${env}_functions_*.sql | tail -n +11 | xargs rm -f 2>/dev/null || true
    
    # Save latest backup info
    echo "$schema_backup" > "$BACKUP_DIR/${env}_latest_schema.txt"
    echo "$functions_backup" > "$BACKUP_DIR/${env}_latest_functions.txt"
}

# Restore database from backup
restore_database() {
    local env=$1
    local backup_file=$2
    
    if [ -z "$backup_file" ]; then
        # Use latest backup
        local latest_file="$BACKUP_DIR/${env}_latest_schema.txt"
        if [ -f "$latest_file" ]; then
            backup_file=$(cat "$latest_file")
        else
            error "No backup file specified and no latest backup found"
            exit 1
        fi
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    local db_name
    case $env in
        "production") db_name=$PRODUCTION_DB ;;
        "staging") db_name=$STAGING_DB ;;
        *) error "Restore only supported for production and staging"; exit 1 ;;
    esac
    
    warning "This will restore database $db_name from backup. Continue? (y/N)"
    read -r confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log "Restore cancelled"
        return 0
    fi
    
    log "Restoring database $db_name from $backup_file..."
    
    # Restore from backup
    psql -U weixiangzhang -d "$db_name" -f "$backup_file"
    
    success "Database restored from backup"
}

# Validate database state
validate_database() {
    local env=$1
    local db_url=$(get_db_url "$env")
    
    log "Validating $env database..."
    
    # Check basic connectivity
    if ! psql "$db_url" -U weixiangzhang -c "SELECT 1;" > /dev/null 2>&1; then
        error "Cannot connect to $env database"
        return 1
    fi
    
    # Check Flyway schema history exists
    if ! psql "$db_url" -U weixiangzhang -c "SELECT 1 FROM flyway_schema_history LIMIT 1;" > /dev/null 2>&1; then
        warning "Flyway schema history table not found - database may need initialization"
        return 1
    fi
    
    # Check core tables exist
    local required_tables=("books" "authors" "chunks")
    for table in "${required_tables[@]}"; do
        if ! psql "$db_url" -U weixiangzhang -c "SELECT 1 FROM $table LIMIT 1;" > /dev/null 2>&1; then
            error "Required table '$table' not found"
            return 1
        fi
    done
    
    # Check core functions exist
    local required_functions=("api_system_health_check" "api_search_comprehensive")
    for func in "${required_functions[@]}"; do
        if ! psql "$db_url" -U weixiangzhang -c "SELECT 1 FROM information_schema.routines WHERE routine_name = '$func';" | grep -q "1"; then
            error "Required function '$func' not found"
            return 1
        fi
    done
    
    success "$env database validation passed"
    return 0
}

# Show database status
status() {
    local env=${1:-"all"}
    
    log "📊 Database Status Report"
    echo "================================"
    
    if [[ "$env" == "all" || "$env" == "production" ]]; then
        echo -n "Production ($PRODUCTION_DB): "
        if validate_database "production" > /dev/null 2>&1; then
            success "HEALTHY"
        else
            error "UNHEALTHY"
        fi
    fi
    
    if [[ "$env" == "all" || "$env" == "staging" ]]; then
        echo -n "Staging ($STAGING_DB): "
        if validate_database "staging" > /dev/null 2>&1; then
            success "HEALTHY"
        else
            warning "NOT READY"
        fi
    fi
    
    if [[ "$env" == "all" || "$env" == "test" ]]; then
        echo -n "Test ($TEST_DB): "
        if validate_database "test" > /dev/null 2>&1; then
            success "HEALTHY"
        else
            echo "NOT CREATED"
        fi
    fi
    
    echo "================================"
    
    # Show Flyway info for each environment
    if [[ "$env" == "all" ]]; then
        for db_env in "production" "staging"; do
            echo "$db_env Flyway Status:"
            run_flyway "$db_env" "info" 2>/dev/null || echo "  Not initialized"
            echo ""
        done
    fi
}

# Main command handler
case "$1" in
    # Migration commands
    migrate)
        check_flyway
        create_database "$2"
        run_flyway "$2" "migrate"
        ;;
    undo)
        check_flyway
        run_flyway "$2" "undo"
        ;;
    baseline)
        check_flyway
        create_database "$2"
        run_flyway "$2" "baseline"
        ;;
    info)
        check_flyway
        run_flyway "$2" "info"
        ;;
    validate)
        check_flyway
        if [ -n "$2" ]; then
            validate_database "$2"
        else
            run_flyway "production" "validate"
        fi
        ;;
    
    # Database management
    create)
        create_database "$2"
        ;;
    backup)
        backup_database "$2"
        ;;
    restore)
        restore_database "$2" "$3"
        ;;
    status)
        status "$2"
        ;;
    
    *)
        echo "🗄️  LibraryOfBabel Database Manager"
        echo "===================================="
        echo "Usage: $0 {command} {environment} [options]"
        echo ""
        echo "Environments: production, staging, test"
        echo ""
        echo "Migration Commands:"
        echo "  migrate {env}        - Apply pending migrations"
        echo "  undo {env}          - Rollback last migration"
        echo "  baseline {env}      - Initialize Flyway on existing database"
        echo "  info {env}          - Show migration status"
        echo "  validate {env}      - Validate database against migrations"
        echo ""
        echo "Database Management:"
        echo "  create {env}        - Create database if it doesn't exist"
        echo "  backup {env}        - Backup database schema and functions"
        echo "  restore {env} [file] - Restore from backup"
        echo "  status [env]        - Show database status (all envs if not specified)"
        echo ""
        echo "Examples:"
        echo "  $0 migrate staging           # Apply migrations to staging"
        echo "  $0 backup production         # Backup production database"
        echo "  $0 validate staging          # Validate staging database"
        echo "  $0 status                    # Show status of all databases"
        echo ""
        echo "Integration with deploy_manager.sh:"
        echo "  ./deploy_manager.sh db staging migrate"
        echo "  ./deploy_manager.sh db production backup"
        echo ""
        exit 1
        ;;
esac