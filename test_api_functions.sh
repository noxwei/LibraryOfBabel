#!/bin/bash
# API Function Verification Test
# Tests critical production functions before/after migration

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Database to test (pass as parameter)
DB_NAME=${1:-"knowledge_base"}

log "🧪 Testing Critical API Functions on: $DB_NAME"
echo "================================================="

# Critical production functions to test
CRITICAL_FUNCTIONS=(
    "api_v3_health"
    "api_shortcuts_search_simple"
    "api_shortcuts_dashboard" 
    "api_shortcuts_collection_health"
    "api_extended_semantic_search"
)

PASSED=0
FAILED=0

for func in "${CRITICAL_FUNCTIONS[@]}"; do
    echo -n "Testing $func: "
    
    # Check if function exists in any schema
    SCHEMA=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "
        SELECT routine_schema 
        FROM information_schema.routines 
        WHERE routine_name = '$func' 
        LIMIT 1;" | xargs)
    
    if [ -n "$SCHEMA" ]; then
        # Try to execute function with minimal parameters
        case $func in
            "api_v3_health")
                RESULT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ${SCHEMA}.${func}();" 2>/dev/null || echo "ERROR")
                ;;
            "api_shortcuts_search_simple")
                RESULT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ${SCHEMA}.${func}('test', 1);" 2>/dev/null || echo "ERROR")
                ;;
            "api_shortcuts_dashboard")
                RESULT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ${SCHEMA}.${func}();" 2>/dev/null || echo "ERROR")
                ;;
            "api_shortcuts_collection_health")
                RESULT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ${SCHEMA}.${func}();" 2>/dev/null || echo "ERROR")
                ;;
            "api_extended_semantic_search")
                RESULT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM ${SCHEMA}.${func}('test', 1);" 2>/dev/null || echo "ERROR")
                ;;
        esac
        
        if [ "$RESULT" != "ERROR" ] && [ -n "$RESULT" ]; then
            success "PASS (schema: $SCHEMA)"
            ((PASSED++))
        else
            error "FAIL (execution error)"
            ((FAILED++))
        fi
    else
        error "FAIL (not found)"
        ((FAILED++))
    fi
done

echo ""
echo "📊 **TEST RESULTS**"
echo "==================="
echo "✅ Passed: $PASSED"
echo "❌ Failed: $FAILED"
echo "Database: $DB_NAME"

if [ $FAILED -eq 0 ]; then
    success "🎉 All critical API functions working!"
    exit 0
else
    error "⚠️  Some API functions failed - review before production deployment"
    exit 1
fi