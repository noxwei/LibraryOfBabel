#!/bin/bash
# Safe Production Clone Testing Script
# Creates exact copy of production for migration testing

set -e

PROJECT_DIR="/Users/weixiangzhang/Local_Dev/LibraryOfBabel"
cd "$PROJECT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

log "🔬 Creating Production Clone for Safe Testing"
echo "============================================="

# Step 1: Create clone database
log "Step 1: Creating production clone database..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CLONE_DB="knowledge_base_test_$TIMESTAMP"

psql -U weixiangzhang -d postgres -c "CREATE DATABASE $CLONE_DB;" || {
    error "Failed to create clone database"
    exit 1
}
success "Created clone database: $CLONE_DB"

# Step 2: Dump and restore production data
log "Step 2: Copying production data to clone..."
pg_dump -U weixiangzhang -d knowledge_base --clean --if-exists | \
    psql -U weixiangzhang -d "$CLONE_DB" -q

success "Production data copied to clone"

# Step 3: Verify clone has same function count
PROD_FUNCTIONS=$(psql -U weixiangzhang -d knowledge_base -t -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='public' AND routine_type='FUNCTION';" | xargs)
CLONE_FUNCTIONS=$(psql -U weixiangzhang -d "$CLONE_DB" -t -c "SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema='public' AND routine_type='FUNCTION';" | xargs)

log "Production functions: $PROD_FUNCTIONS"
log "Clone functions: $CLONE_FUNCTIONS"

if [ "$PROD_FUNCTIONS" = "$CLONE_FUNCTIONS" ]; then
    success "Clone verified - function counts match"
else
    error "Clone verification failed - function counts don't match"
    exit 1
fi

# Step 4: Test migrations on clone
log "Step 3: Testing migrations on clone database..."
echo "Updating db_manager.sh to use clone database..."

# Temporarily modify db_manager for clone testing
sed "s/PRODUCTION_DB=\"knowledge_base\"/PRODUCTION_DB=\"$CLONE_DB\"/" db_manager.sh > db_manager_clone.sh
chmod +x db_manager_clone.sh

success "Clone ready for migration testing"
echo ""
echo "🧪 **CLONE TESTING COMMANDS:**"
echo "Test V003 cleanup:     ./db_manager_clone.sh migrate production"
echo "Verify functions:      psql -U weixiangzhang -d $CLONE_DB -c \"\\df\""
echo "Check schemas:         psql -U weixiangzhang -d $CLONE_DB -c \"\\dn\""
echo "Rollback if needed:    ./db_manager_clone.sh rollback production"
echo ""
echo "📊 **COMPARE RESULTS:**"
echo "Production:  psql -U weixiangzhang -d knowledge_base"
echo "Clone Test:  psql -U weixiangzhang -d $CLONE_DB"
echo ""
echo "🗑️  **CLEANUP WHEN DONE:**"
echo "Drop clone:  psql -U weixiangzhang -d postgres -c \"DROP DATABASE $CLONE_DB;\""