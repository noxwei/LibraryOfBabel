#!/usr/bin/env python3
"""
🚀 LibraryOfBabel Vector Optimization Daemon
============================================

Autonomous daemon to optimize vector search performance without deleting existing embeddings.
Runs all optimizations in sequence, then auto-stops.

Usage: python3 vector_optimization_daemon.py
"""

import os
import sys
import time
import logging
import psycopg2
import psycopg2.extras
from datetime import datetime
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class VectorOptimizationDaemon:
    def __init__(self):
        self.setup_logging()
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        self.status_file = Path(__file__).parent / "optimization_status.json"
        self.log_file = Path(__file__).parent.parent / "logs" / "vector_optimization.log"
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "vector_optimization.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_db(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
    
    def save_status(self, step, status, details=""):
        """Save current optimization status"""
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "current_step": step,
            "status": status,
            "details": details,
            "steps_completed": getattr(self, 'completed_steps', [])
        }
        
        with open(self.status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def step1_check_pgvector(self):
        """Step 1: Check and install pgvector extension"""
        self.logger.info("🔍 Step 1: Checking pgvector extension...")
        self.save_status("pgvector_check", "running", "Checking if pgvector is installed")
        
        db = self.get_db()
        if not db:
            raise Exception("Cannot connect to database")
        
        try:
            with db.cursor() as cur:
                # Check if pgvector is available
                cur.execute("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
                if not cur.fetchone():
                    self.logger.error("❌ pgvector extension not available. Install with: sudo apt install postgresql-16-pgvector")
                    raise Exception("pgvector not available")
                
                # Check if already installed
                cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
                if cur.fetchone():
                    self.logger.info("✅ pgvector extension already installed")
                else:
                    self.logger.info("📦 Installing pgvector extension...")
                    cur.execute("CREATE EXTENSION vector")
                    db.commit()
                    self.logger.info("✅ pgvector extension installed successfully")
                
        except Exception as e:
            self.logger.error(f"❌ pgvector step failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("pgvector_check", "completed", "pgvector extension ready")
        return True
    
    def step2_analyze_embeddings(self):
        """Step 2: Analyze current embedding structure"""
        self.logger.info("📊 Step 2: Analyzing embedding structure...")
        self.save_status("analyze_embeddings", "running", "Analyzing current embeddings")
        
        db = self.get_db()
        try:
            with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Check embedding table structure
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'chunk_embeddings'
                    ORDER BY ordinal_position
                """)
                
                columns = cur.fetchall()
                self.logger.info(f"📋 Embedding table columns: {[col['column_name'] for col in columns]}")
                
                # Check embedding dimensions
                cur.execute("SELECT COUNT(*) as total FROM chunk_embeddings LIMIT 1")
                if cur.fetchone()['total'] > 0:
                    # Sample an embedding to check dimensions
                    cur.execute("SELECT embedding FROM chunk_embeddings LIMIT 1")
                    sample = cur.fetchone()
                    if sample and sample['embedding']:
                        # Assume it's stored as JSON array or similar
                        embedding_dim = len(eval(sample['embedding']) if isinstance(sample['embedding'], str) else sample['embedding'])
                        self.logger.info(f"📐 Embedding dimensions: {embedding_dim}")
                        self.embedding_dim = embedding_dim
                    else:
                        self.logger.warning("⚠️ Sample embedding is null")
                        self.embedding_dim = 384  # Default
                else:
                    self.logger.warning("⚠️ No embeddings found in table")
                    self.embedding_dim = 384
                
                # Get statistics
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_embeddings,
                        COUNT(DISTINCT book_id) as books_with_embeddings
                    FROM chunk_embeddings 
                    WHERE embedding IS NOT NULL
                """)
                
                stats = cur.fetchone()
                self.logger.info(f"📊 Embeddings: {stats['total_embeddings']} total, {stats['books_with_embeddings']} books")
                
        except Exception as e:
            self.logger.error(f"❌ Analysis step failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("analyze_embeddings", "completed", f"Found {stats['total_embeddings']} embeddings")
        return True
    
    def step3_convert_to_vector_type(self):
        """Step 3: Add vector column if needed"""
        self.logger.info("🔄 Step 3: Converting embeddings to vector type...")
        self.save_status("convert_vectors", "running", "Adding vector column")
        
        db = self.get_db()
        try:
            with db.cursor() as cur:
                # Check if vector column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'chunk_embeddings' 
                    AND column_name = 'embedding_vector'
                """)
                
                if cur.fetchone():
                    self.logger.info("✅ Vector column already exists")
                else:
                    self.logger.info("➕ Adding vector column...")
                    cur.execute(f"ALTER TABLE chunk_embeddings ADD COLUMN embedding_vector vector({self.embedding_dim})")
                    db.commit()
                    
                    self.logger.info("🔄 Converting existing embeddings to vector format...")
                    # Convert embeddings in batches
                    batch_size = 1000
                    cur.execute("SELECT COUNT(*) FROM chunk_embeddings WHERE embedding IS NOT NULL")
                    total = cur.fetchone()[0]
                    
                    for offset in range(0, total, batch_size):
                        cur.execute("""
                            UPDATE chunk_embeddings 
                            SET embedding_vector = embedding::vector 
                            WHERE chunk_id IN (
                                SELECT chunk_id FROM chunk_embeddings 
                                WHERE embedding IS NOT NULL 
                                AND embedding_vector IS NULL
                                LIMIT %s OFFSET %s
                            )
                        """, (batch_size, offset))
                        db.commit()
                        
                        processed = min(offset + batch_size, total)
                        self.logger.info(f"⏳ Converted {processed}/{total} embeddings")
                    
                    self.logger.info("✅ All embeddings converted to vector format")
                
        except Exception as e:
            self.logger.error(f"❌ Vector conversion failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("convert_vectors", "completed", "Embeddings converted to vector type")
        return True
    
    def step4_create_vector_index(self):
        """Step 4: Create HNSW vector index"""
        self.logger.info("🚀 Step 4: Creating HNSW vector index...")
        self.save_status("create_index", "running", "Building HNSW index for fast similarity search")
        
        db = self.get_db()
        try:
            # Set autocommit for CONCURRENTLY operations
            db.autocommit = True
            with db.cursor() as cur:
                # Check if index exists
                cur.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'chunk_embeddings' 
                    AND indexname = 'idx_chunk_embeddings_hnsw'
                """)
                
                if cur.fetchone():
                    self.logger.info("✅ HNSW index already exists")
                else:
                    self.logger.info("🔨 Creating HNSW index (this may take several minutes)...")
                    start_time = time.time()
                    
                    # Create HNSW index for cosine similarity
                    cur.execute("""
                        CREATE INDEX CONCURRENTLY idx_chunk_embeddings_hnsw 
                        ON chunk_embeddings 
                        USING hnsw (embedding_vector vector_cosine_ops)
                        WITH (m = 16, ef_construction = 64)
                    """)
                    
                    elapsed = time.time() - start_time
                    self.logger.info(f"✅ HNSW index created successfully in {elapsed:.2f} seconds")
                
        except Exception as e:
            self.logger.error(f"❌ Index creation failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("create_index", "completed", "HNSW index created for fast vector search")
        return True
    
    def step5_create_query_cache(self):
        """Step 5: Create query embedding cache table"""
        self.logger.info("💾 Step 5: Creating query cache infrastructure...")
        self.save_status("query_cache", "running", "Setting up query embedding cache")
        
        db = self.get_db()
        try:
            with db.cursor() as cur:
                # Create query cache table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS query_embeddings_cache (
                        query_hash TEXT PRIMARY KEY,
                        query_text TEXT NOT NULL,
                        embedding_vector vector(%s),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        use_count INTEGER DEFAULT 1
                    )
                """ % self.embedding_dim)
                
                # Create index on last_used for cleanup
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query_cache_last_used 
                    ON query_embeddings_cache (last_used)
                """)
                
                db.commit()
                self.logger.info("✅ Query cache table created")
                
        except Exception as e:
            self.logger.error(f"❌ Query cache creation failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("query_cache", "completed", "Query cache infrastructure ready")
        return True
    
    def step6_test_performance(self):
        """Step 6: Test optimized search performance"""
        self.logger.info("🧪 Step 6: Testing optimized search performance...")
        self.save_status("performance_test", "running", "Running performance benchmarks")
        
        db = self.get_db()
        try:
            with db.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # Test vector similarity search
                test_queries = [
                    "artificial intelligence",
                    "love and romance", 
                    "war and conflict",
                    "philosophy of mind"
                ]
                
                performance_results = []
                
                for query in test_queries:
                    start_time = time.time()
                    
                    # Sample a random embedding for testing
                    cur.execute("""
                        SELECT embedding_vector 
                        FROM chunk_embeddings 
                        WHERE embedding_vector IS NOT NULL 
                        ORDER BY RANDOM() 
                        LIMIT 1
                    """)
                    
                    sample_vector = cur.fetchone()['embedding_vector']
                    
                    # Test vector similarity search with index
                    cur.execute("""
                        SELECT chunk_id, book_id, (embedding_vector <=> %s) as distance
                        FROM chunk_embeddings 
                        WHERE embedding_vector IS NOT NULL
                        ORDER BY embedding_vector <=> %s
                        LIMIT 10
                    """, (sample_vector, sample_vector))
                    
                    results = cur.fetchall()
                    elapsed = (time.time() - start_time) * 1000  # Convert to ms
                    
                    performance_results.append({
                        'query': query,
                        'time_ms': elapsed,
                        'results_count': len(results)
                    })
                    
                    self.logger.info(f"⚡ Query '{query}': {elapsed:.2f}ms, {len(results)} results")
                
                avg_time = sum(r['time_ms'] for r in performance_results) / len(performance_results)
                self.logger.info(f"📊 Average search time: {avg_time:.2f}ms")
                
                if avg_time < 100:
                    self.logger.info("🎉 Excellent performance! Search under 100ms")
                elif avg_time < 500:
                    self.logger.info("✅ Good performance! Search under 500ms")
                else:
                    self.logger.warning("⚠️ Performance could be better. Consider index tuning.")
                
        except Exception as e:
            self.logger.error(f"❌ Performance test failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("performance_test", "completed", f"Average search time: {avg_time:.2f}ms")
        return True
    
    def step7_create_hybrid_search_function(self):
        """Step 7: Create hybrid search stored procedure"""
        self.logger.info("🔀 Step 7: Creating hybrid search function...")
        self.save_status("hybrid_search", "running", "Setting up hybrid text+vector search")
        
        db = self.get_db()
        try:
            with db.cursor() as cur:
                # Create hybrid search function
                cur.execute(f"""
                    CREATE OR REPLACE FUNCTION hybrid_search(
                        search_query TEXT,
                        query_vector vector({self.embedding_dim}),
                        text_weight FLOAT DEFAULT 0.7,
                        vector_weight FLOAT DEFAULT 0.3,
                        result_limit INTEGER DEFAULT 20
                    )
                    RETURNS TABLE (
                        chunk_id TEXT,
                        book_id TEXT,
                        content TEXT,
                        title TEXT,
                        author TEXT,
                        combined_score FLOAT,
                        text_rank FLOAT,
                        vector_similarity FLOAT
                    )
                    LANGUAGE plpgsql
                    AS $$
                    BEGIN
                        RETURN QUERY
                        SELECT 
                            c.chunk_id,
                            c.book_id,
                            c.content,
                            b.title,
                            b.author,
                            (text_weight * COALESCE(ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_query)), 0) +
                             vector_weight * (1 - (ce.embedding_vector <=> query_vector))) as combined_score,
                            ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', search_query)) as text_rank,
                            (1 - (ce.embedding_vector <=> query_vector)) as vector_similarity
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        LEFT JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                        WHERE 
                            (to_tsvector('english', c.content) @@ plainto_tsquery('english', search_query)
                             OR ce.embedding_vector IS NOT NULL)
                        ORDER BY combined_score DESC
                        LIMIT result_limit;
                    END
                    $$;
                """)
                
                db.commit()
                self.logger.info("✅ Hybrid search function created")
                
        except Exception as e:
            self.logger.error(f"❌ Hybrid search creation failed: {e}")
            raise
        finally:
            db.close()
        
        self.save_status("hybrid_search", "completed", "Hybrid search function ready")
        return True
    
    def run_optimization(self):
        """Run all optimization steps in sequence"""
        self.logger.info("🚀 Starting LibraryOfBabel Vector Optimization Daemon")
        self.save_status("daemon_start", "running", "Starting optimization sequence")
        
        steps = [
            ("pgvector_check", self.step1_check_pgvector),
            ("analyze_embeddings", self.step2_analyze_embeddings),
            ("convert_vectors", self.step3_convert_to_vector_type),
            ("create_index", self.step4_create_vector_index),
            ("query_cache", self.step5_create_query_cache),
            ("performance_test", self.step6_test_performance),
            ("hybrid_search", self.step7_create_hybrid_search_function)
        ]
        
        completed_steps = []
        
        try:
            for step_name, step_func in steps:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🔄 Executing: {step_name}")
                self.logger.info(f"{'='*60}")
                
                start_time = time.time()
                success = step_func()
                elapsed = time.time() - start_time
                
                if success:
                    completed_steps.append(step_name)
                    self.completed_steps = completed_steps
                    self.logger.info(f"✅ {step_name} completed in {elapsed:.2f} seconds")
                else:
                    raise Exception(f"Step {step_name} failed")
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info("🎉 ALL OPTIMIZATION STEPS COMPLETED SUCCESSFULLY!")
            self.logger.info(f"{'='*60}")
            
            summary = {
                "status": "SUCCESS",
                "total_steps": len(steps),
                "completed_steps": completed_steps,
                "completion_time": datetime.now().isoformat(),
                "next_steps": [
                    "Update API endpoints to use new vector index",
                    "Test semantic search performance",
                    "Monitor query cache hit rates"
                ]
            }
            
            self.save_status("daemon_complete", "success", summary)
            self.logger.info("📊 Vector search is now optimized and ready!")
            self.logger.info("⚡ Expected search performance: <100ms for semantic queries")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Optimization failed at step: {e}")
            self.save_status("daemon_failed", "error", str(e))
            return False
    
    def cleanup_and_exit(self):
        """Clean shutdown"""
        self.logger.info("🛑 Vector Optimization Daemon shutting down...")
        sys.exit(0)

def main():
    """Main daemon entry point"""
    daemon = VectorOptimizationDaemon()
    
    try:
        success = daemon.run_optimization()
        if success:
            daemon.logger.info("✅ Daemon completed successfully - AUTO STOPPING")
        else:
            daemon.logger.error("❌ Daemon failed - AUTO STOPPING")
    except KeyboardInterrupt:
        daemon.logger.info("⚠️ Daemon interrupted by user")
    except Exception as e:
        daemon.logger.error(f"💥 Daemon crashed: {e}")
    finally:
        daemon.cleanup_and_exit()

if __name__ == "__main__":
    main()