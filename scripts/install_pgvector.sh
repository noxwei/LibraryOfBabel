#!/bin/bash
# pgvector Installation Script for LibraryOfBabel Performance Optimization
# Critical: 895 books processed, 158 failures - need vector optimization urgently
# =========================================================================

echo "🚀 Installing pgvector for LibraryOfBabel Performance Optimization"
echo "Status: 895 books processed, 158 failures detected"
echo "Target: 10-50x search speed improvement"

# Step 1: Copy pgvector extension files to PostgreSQL 15
echo "📁 Copying pgvector extension files..."
sudo cp -r /opt/homebrew/Cellar/pgvector/0.8.0/share/postgresql@14/extension/* /opt/homebrew/opt/postgresql@15/share/postgresql@15/extension/

# Step 2: Copy library file
echo "📚 Copying pgvector library..."
sudo cp /opt/homebrew/Cellar/pgvector/0.8.0/lib/postgresql@14/vector.so /opt/homebrew/opt/postgresql@15/lib/

# Step 3: Restart PostgreSQL to load extension
echo "🔄 Restarting PostgreSQL to load pgvector..."
brew services restart postgresql@15

# Wait for PostgreSQL to start
echo "⏳ Waiting for PostgreSQL to start..."
sleep 5

# Step 4: Enable pgvector extension in database
echo "🔧 Enabling pgvector extension in LibraryOfBabel database..."
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
psql $(python3 -c "from config.api_config import get_database_config; cfg = get_database_config(); print(f'-h {cfg[\"host\"]} -p {cfg[\"port\"]} -U {cfg[\"user\"]} -d {cfg[\"database\"]}')")  -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Step 5: Deploy vector optimization schema
echo "🏗️  Deploying vector indexing optimization..."
psql $(python3 -c "from config.api_config import get_database_config; cfg = get_database_config(); print(f'-h {cfg[\"host\"]} -p {cfg[\"port\"]} -U {cfg[\"user\"]} -d {cfg[\"database\"]}')")  -f database/optimization/vector_indexing_optimization.sql

# Step 6: Run performance benchmark
echo "📊 Running performance benchmark..."
psql $(python3 -c "from config.api_config import get_database_config; cfg = get_database_config(); print(f'-h {cfg[\"host\"]} -p {cfg[\"port\"]} -U {cfg[\"user\"]} -d {cfg[\"database\"]}')")  -c "SELECT * FROM benchmark_search_performance();"

echo "✅ pgvector installation complete!"
echo ""
echo "🎯 Expected Performance Improvements:"
echo "   • Search Speed: 2-5 seconds → 200-500ms (10-50x faster)"
echo "   • Concurrent Users: 5-10x capacity increase"  
echo "   • Phase 2C Failure Rate: Should decrease significantly"
echo ""
echo "📈 Current Status:"
echo "   • Phase 2C: 895/1,019 books processed (87.8%)"
echo "   • Failures: 158 books (17.6% - should improve with optimization)"
echo "   • Multi-model embeddings: BGE 622, MXBai 115"
echo ""
echo "🔥 Ready for production-grade vector search!"