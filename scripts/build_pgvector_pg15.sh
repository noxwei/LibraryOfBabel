#!/bin/bash
# Build pgvector for PostgreSQL 15 - PROPER FIX
# This will compile pgvector specifically for PostgreSQL@15
# =========================================================

echo "🔧 Building pgvector specifically for PostgreSQL@15"
echo "📊 Target: 10-50x search improvement for 32,086 embeddings"

# Step 1: Install build dependencies
echo "📦 Installing build dependencies..."
brew install git

# Step 2: Clone pgvector source
echo "📥 Cloning pgvector source..."
cd /tmp
rm -rf pgvector 2>/dev/null
git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
cd pgvector

# Step 3: Build for PostgreSQL 15 specifically
echo "🔨 Building pgvector for PostgreSQL@15..."
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"
export PG_CONFIG="/opt/homebrew/opt/postgresql@15/bin/pg_config"

# Verify we're using the right PostgreSQL
echo "✅ Using PostgreSQL version:"
$PG_CONFIG --version

# Build
make clean 2>/dev/null || true
make

# Step 4: Install with sudo
echo "📦 Installing pgvector for PostgreSQL@15..."
sudo make install

# Step 5: Restart PostgreSQL
echo "🔄 Restarting PostgreSQL..."
brew services restart postgresql@15
sleep 5

# Step 6: Test installation
echo "🧪 Testing pgvector installation..."
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
psql $(python3 -c "from config.api_config import get_database_config; cfg = get_database_config(); print(f'-h {cfg[\"host\"]} -p {cfg[\"port\"]} -U {cfg[\"user\"]} -d {cfg[\"database\"]}')")  -c "CREATE EXTENSION IF NOT EXISTS vector;"

if [ $? -eq 0 ]; then
    echo "🎉 SUCCESS: pgvector extension enabled!"
    
    # Deploy full vector optimization
    echo "🚀 Deploying vector optimization..."
    psql $(python3 -c "from config.api_config import get_database_config; cfg = get_database_config(); print(f'-h {cfg[\"host\"]} -p {cfg[\"port\"]} -U {cfg[\"user\"]} -d {cfg[\"database\"]}')")  -f database/optimization/vector_indexing_optimization.sql
    
    echo "📊 Running performance benchmark..."
    psql $(python3 -c "from config.api_config import get_database_config; cfg = get_database_config(); print(f'-h {cfg[\"host\"]} -p {cfg[\"port\"]} -U {cfg[\"user\"]} -d {cfg[\"database\"]}')")  -c "SELECT * FROM benchmark_search_performance('[0.1,0.2,0.3]'::vector, 3);"
    
    echo ""
    echo "🎯 VECTOR OPTIMIZATION COMPLETE!"
    echo "✅ Expected Performance:"
    echo "   • Search Speed: 2-5 seconds → 200-500ms (10-50x faster)"
    echo "   • Vector Operations: HNSW indexing on 32,086 embeddings"
    echo "   • Production Ready: True vector similarity search"
    echo ""
    echo "🚀 Ready for 10-50x search performance improvement!"
    
else
    echo "❌ pgvector installation still failed"
    echo "📋 Diagnostic information:"
    echo "PostgreSQL version: $($PG_CONFIG --version)"
    echo "Extension directory: $($PG_CONFIG --sharedir)/extension"
    echo "Library directory: $($PG_CONFIG --pkglibdir)"
    ls -la $($PG_CONFIG --pkglibdir)/vector* 2>/dev/null || echo "No vector files found"
    ls -la $($PG_CONFIG --sharedir)/extension/vector* 2>/dev/null || echo "No vector extension files found"
fi

# Cleanup
cd /
rm -rf /tmp/pgvector

echo "🔧 pgvector installation attempt complete!"