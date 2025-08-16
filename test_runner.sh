#!/bin/bash
# LibraryOfBabel Database Test Runner
# Runs pgTAP tests on PostgreSQL functions

set -e  # Exit on any error

# Configuration
PROJECT_DIR="/Users/weixiangzhang/Local_Dev/LibraryOfBabel"
TEST_DIR="$PROJECT_DIR/tests/database"
LOGS_DIR="$PROJECT_DIR/logs"
DB_MANAGER="$PROJECT_DIR/db_manager.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] TEST:${NC} $1"
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
mkdir -p "$LOGS_DIR"

# Install minimal pgTAP functions if not available
setup_pgtap() {
    local env=$1
    local db_name
    
    case $env in
        "production") db_name="knowledge_base" ;;
        "staging") db_name="library_staging" ;;
        "test") db_name="library_test" ;;
        *) error "Unknown environment: $env"; exit 1 ;;
    esac
    
    log "Setting up minimal pgTAP functions for $env..."
    
    # Create minimal pgTAP functions if they don't exist
    psql -U weixiangzhang -d "$db_name" -c "
    CREATE OR REPLACE FUNCTION plan(integer) RETURNS TEXT AS \$\$
    BEGIN
        RETURN 'TAP version 13' || E'\n' || '1..' || \$1;
    END;
    \$\$ LANGUAGE plpgsql;
    
    CREATE OR REPLACE FUNCTION has_function(text, text, text) RETURNS TEXT AS \$\$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.routines 
                  WHERE routine_schema = \$1 AND routine_name = \$2) THEN
            RETURN 'ok - ' || \$3;
        ELSE
            RETURN 'not ok - ' || \$3;
        END IF;
    END;
    \$\$ LANGUAGE plpgsql;
    
    CREATE OR REPLACE FUNCTION lives_ok(text, text) RETURNS TEXT AS \$\$
    DECLARE
        result TEXT;
    BEGIN
        BEGIN
            EXECUTE \$1;
            RETURN 'ok - ' || \$2;
        EXCEPTION WHEN OTHERS THEN
            RETURN 'not ok - ' || \$2 || ' (ERROR: ' || SQLERRM || ')';
        END;
    END;
    \$\$ LANGUAGE plpgsql;
    
    CREATE OR REPLACE FUNCTION ok(boolean, text) RETURNS TEXT AS \$\$
    BEGIN
        IF \$1 THEN
            RETURN 'ok - ' || \$2;
        ELSE
            RETURN 'not ok - ' || \$2;
        END IF;
    END;
    \$\$ LANGUAGE plpgsql;
    
    CREATE OR REPLACE FUNCTION finish() RETURNS TEXT AS \$\$
    BEGIN
        RETURN '# Test completed';
    END;
    \$\$ LANGUAGE plpgsql;
    " > /dev/null 2>&1
    
    success "Minimal pgTAP functions installed for $env"
}

# Run tests on specific environment
run_tests() {
    local env=$1
    local test_file=${2:-"test_production_functions.sql"}
    local db_name
    
    case $env in
        "production") db_name="knowledge_base" ;;
        "staging") db_name="library_staging" ;;
        "test") db_name="library_test" ;;
        *) error "Unknown environment: $env"; exit 1 ;;
    esac
    
    log "Running database tests on $env environment..."
    
    # Setup pgTAP functions
    setup_pgtap "$env"
    
    # Run the test file
    local test_path="$TEST_DIR/$test_file"
    local log_file="$LOGS_DIR/test_${env}_$(date +%Y%m%d_%H%M%S).log"
    
    if [ ! -f "$test_path" ]; then
        error "Test file not found: $test_path"
        return 1
    fi
    
    log "Executing tests from $test_file..."
    
    # Run tests and capture output
    if psql -U weixiangzhang -d "$db_name" -f "$test_path" > "$log_file" 2>&1; then
        # Parse results
        local total_tests=$(grep -c "^ok\|^not ok" "$log_file" || echo "0")
        local passed_tests=$(grep -c "^ok" "$log_file" || echo "0")
        local failed_tests=$(grep -c "^not ok" "$log_file" || echo "0")
        
        echo ""
        echo "📊 Test Results for $env:"
        echo "================================"
        echo "Total Tests: $total_tests"
        echo "Passed: $passed_tests"
        echo "Failed: $failed_tests"
        echo "Log file: $log_file"
        echo ""
        
        if [ "$failed_tests" -eq 0 ]; then
            success "All tests passed on $env!"
            return 0
        else
            warning "$failed_tests tests failed on $env"
            echo "Failed tests:"
            grep "^not ok" "$log_file" || echo "No failed test details found"
            return 1
        fi
    else
        error "Test execution failed on $env"
        echo "Check log file: $log_file"
        return 1
    fi
}

# Validate database before running tests
validate_database() {
    local env=$1
    
    log "Validating $env database before testing..."
    
    if "$DB_MANAGER" validate "$env"; then
        success "$env database validation passed"
        return 0
    else
        error "$env database validation failed"
        return 1
    fi
}

# Main command handler
case "$1" in
    run)
        env=${2:-"staging"}
        test_file=${3:-"test_production_functions.sql"}
        
        # Validate database first
        validate_database "$env"
        
        # Run tests
        run_tests "$env" "$test_file"
        ;;
    
    setup)
        env=${2:-"staging"}
        setup_pgtap "$env"
        ;;
    
    validate)
        env=${2:-"staging"}
        validate_database "$env"
        ;;
    
    *)
        echo "🧪 LibraryOfBabel Database Test Runner"
        echo "======================================"
        echo "Usage: $0 {command} {environment} [test_file]"
        echo ""
        echo "Environments: production, staging, test"
        echo ""
        echo "Commands:"
        echo "  run {env} [test_file]    - Run database tests (default: test_production_functions.sql)"
        echo "  setup {env}              - Install minimal pgTAP functions"
        echo "  validate {env}           - Validate database before testing"
        echo ""
        echo "Examples:"
        echo "  $0 run staging                          # Run all production function tests on staging"
        echo "  $0 run test test_production_functions.sql   # Run specific test file on test DB"
        echo "  $0 setup staging                        # Setup pgTAP on staging"
        echo ""
        echo "Integration with CI/CD:"
        echo "  ./deploy_manager.sh staging start  # Creates staging environment"
        echo "  $0 run staging                      # Validates all 31 production functions"
        echo "  ./deploy_manager.sh deploy          # Safe deployment if tests pass"
        echo ""
        exit 1
        ;;
esac