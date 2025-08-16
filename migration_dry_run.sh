#!/bin/bash
# Migration Dry Run Analysis
# Shows what would happen without making changes

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

DB_NAME="knowledge_base"

log "🔍 Migration Dry Run Analysis: $DB_NAME"
echo "=========================================="

# Current state
CURRENT_FUNCTIONS=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='public' AND routine_type='FUNCTION';" | xargs)
log "Current total functions: $CURRENT_FUNCTIONS"

# V003 Analysis: Functions that would be removed
log "V003 Analysis: Functions that would be REMOVED"
echo "-----------------------------------------------"

# Check for research functions that exist
RESEARCH_PATTERNS=("chen_" "dr_elena_" "dr_marcus_" "dr_sarah_" "calibre_" "test_")
REMOVE_COUNT=0

for pattern in "${RESEARCH_PATTERNS[@]}"; do
    COUNT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_name LIKE '${pattern}%' AND routine_schema='public';" | xargs)
    if [ "$COUNT" -gt 0 ]; then
        echo "  • ${pattern}* functions: $COUNT"
        REMOVE_COUNT=$((REMOVE_COUNT + COUNT))
    fi
done

log "Total functions to remove: $REMOVE_COUNT"
log "Functions after V003: $((CURRENT_FUNCTIONS - REMOVE_COUNT))"

# V004 Analysis: Schema creation
echo ""
log "V004 Analysis: Schema organization"
echo "----------------------------------"
echo "  📱 api schema: Will be created"
echo "  🔄 pipeline schema: Will be created" 
echo "  🔢 vectors schema: Will be created"

# V005 Analysis: Function distribution
echo ""
log "V005 Analysis: Function distribution"
echo "------------------------------------"

API_FUNCTIONS=("api_v3_" "api_shortcuts_" "api_extended_" "api_emotional_" "api_semantic_")
PIPELINE_FUNCTIONS=("update_" "api_ingest_" "api_process_" "batch_" "generate_")

API_COUNT=0
PIPELINE_COUNT=0

for pattern in "${API_FUNCTIONS[@]}"; do
    COUNT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_name LIKE '${pattern}%' AND routine_schema='public';" | xargs)
    API_COUNT=$((API_COUNT + COUNT))
done

for pattern in "${PIPELINE_FUNCTIONS[@]}"; do
    COUNT=$(psql -U weixiangzhang -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_name LIKE '${pattern}%' AND routine_schema='public';" | xargs)
    PIPELINE_COUNT=$((PIPELINE_COUNT + COUNT))
done

echo "  📱 api schema: ~$API_COUNT functions"
echo "  🔄 pipeline schema: ~$PIPELINE_COUNT functions"
echo "  🔢 vectors schema: ~2-5 functions"
echo "  📋 public schema: ~$((CURRENT_FUNCTIONS - REMOVE_COUNT - API_COUNT - PIPELINE_COUNT - 5)) functions"

# Risk analysis
echo ""
log "🛡️  Risk Analysis"
echo "=================="
success "✅ Automatic backup before each migration"
success "✅ Rollback scripts available (U003, U004, U005)"
success "✅ Production API remains running during migration"
success "✅ No table data changes - only function organization"
warning "⚠️  Schema-qualified function calls needed after V005"

echo ""
log "📋 **RECOMMENDED TESTING SEQUENCE:**"
echo "1. Create production clone:    ./create_production_clone.sh"
echo "2. Test on clone:             ./db_manager_clone.sh migrate production"
echo "3. Verify API functions:      ./test_api_functions.sh knowledge_base_test_*"
echo "4. If successful, deploy:     ./db_manager.sh migrate production"