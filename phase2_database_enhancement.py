#!/usr/bin/env python3
"""
🚀 PHASE 2: STABLE 4-MODEL DATABASE ENHANCEMENT
===============================================

Creates the multi-modal embedding columns using only the 4 reliable models:
- nomic-embed-text: 768d general semantic search
- mxbai-embed-large: 1024d high-precision matching  
- bge-m3: 1024d multilingual understanding
- granite-embedding: 768d technical/academic content

Avoids snowflake-arctic-embed due to timeout issues.
"""

import os
import psycopg2
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase2DatabaseEnhancer:
    """PostgreSQL schema enhancement with 4 reliable embedding models"""
    
    def __init__(self):
        self.models = {
            "nomic": {
                "column": "embedding_nomic",
                "dimensions": 768,
                "description": "General semantic search"
            },
            "mxbai": {
                "column": "embedding_mxbai", 
                "dimensions": 1024,
                "description": "High-precision matching"
            },
            "bge": {
                "column": "embedding_bge",
                "dimensions": 1024,
                "description": "Multilingual understanding"
            },
            "granite": {
                "column": "embedding_granite",
                "dimensions": 768,
                "description": "Technical/academic content"
            }
        }
        
    def get_db_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(
                host='localhost',
                database='knowledge_base',
                user='weixiangzhang',
                password=os.environ.get('DB_PASSWORD', 'Weixiang135!')
            )
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
            
    def create_embedding_columns(self):
        """Create the 4 new embedding columns with indexes"""
        logger.info("🗄️ Creating 4-model embedding schema...")
        
        conn = self.get_db_connection()
        if not conn:
            return False
            
        try:
            with conn.cursor() as cur:
                for model_key, config in self.models.items():
                    column = config["column"]
                    dimensions = config["dimensions"]
                    description = config["description"]
                    
                    logger.info(f"   📊 Adding {column} ({dimensions}d) - {description}")
                    
                    # Add column if not exists
                    cur.execute(f"""
                        ALTER TABLE chunks 
                        ADD COLUMN IF NOT EXISTS {column} vector({dimensions})
                    """)
                    
                    # Create optimized index
                    index_name = f"idx_{column}_cosine"
                    cur.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON chunks USING ivfflat ({column} vector_cosine_ops)
                        WITH (lists = 100)
                    """)
                    
                    # Add helpful comment
                    cur.execute(f"""
                        COMMENT ON COLUMN chunks.{column} IS 
                        'Multi-modal embedding: {description} ({dimensions}d vector)'
                    """)
                    
                conn.commit()
                logger.info("✅ All 4 embedding columns created successfully!")
                
                # Verify schema
                cur.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'chunks' 
                    AND column_name LIKE 'embedding_%'
                    ORDER BY column_name
                """)
                
                columns = cur.fetchall()
                logger.info("📋 Current embedding columns:")
                for col_name, col_type in columns:
                    logger.info(f"   • {col_name}: {col_type}")
                
                return True
                
        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            return False
        finally:
            conn.close()
            
    def add_metadata_columns(self):
        """Add content classification metadata columns"""
        logger.info("📝 Adding metadata columns...")
        
        conn = self.get_db_connection()
        if not conn:
            return False
            
        try:
            with conn.cursor() as cur:
                # Add content type classification
                cur.execute("""
                    ALTER TABLE chunks 
                    ADD COLUMN IF NOT EXISTS content_type TEXT,
                    ADD COLUMN IF NOT EXISTS routing_reason TEXT,
                    ADD COLUMN IF NOT EXISTS embedding_model_used TEXT,
                    ADD COLUMN IF NOT EXISTS last_embedding_update TIMESTAMP DEFAULT NOW()
                """)
                
                # Create index for content type queries
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_content_type 
                    ON chunks(content_type)
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_embedding_model 
                    ON chunks(embedding_model_used)
                """)
                
                # Add comments
                cur.execute("""
                    COMMENT ON COLUMN chunks.content_type IS 
                    'Content classification: technical_academic, semantic_narrative, multilingual, general';
                    COMMENT ON COLUMN chunks.routing_reason IS 
                    'Explanation of why specific embedding model was selected';
                    COMMENT ON COLUMN chunks.embedding_model_used IS 
                    'Primary embedding model used for this chunk';
                """)
                
                conn.commit()
                logger.info("✅ Metadata columns added successfully!")
                return True
                
        except Exception as e:
            logger.error(f"Metadata columns failed: {e}")
            return False
        finally:
            conn.close()
            
    def verify_schema(self):
        """Verify the enhanced schema is ready"""
        logger.info("🔍 Verifying enhanced schema...")
        
        conn = self.get_db_connection()
        if not conn:
            return False
            
        try:
            with conn.cursor() as cur:
                # Check all expected columns exist
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'chunks' 
                    AND (column_name LIKE 'embedding_%' OR column_name IN ('content_type', 'routing_reason', 'embedding_model_used'))
                    ORDER BY column_name
                """)
                
                schema_columns = cur.fetchall()
                
                # Check indexes
                cur.execute("""
                    SELECT indexname, indexdef
                    FROM pg_indexes 
                    WHERE tablename = 'chunks' 
                    AND indexname LIKE '%embedding%'
                    ORDER BY indexname
                """)
                
                indexes = cur.fetchall()
                
                logger.info("📊 ENHANCED SCHEMA SUMMARY")
                logger.info("=" * 50)
                logger.info("📋 Columns:")
                for col_name, col_type, nullable in schema_columns:
                    logger.info(f"   • {col_name}: {col_type} {'(nullable)' if nullable == 'YES' else ''}")
                
                logger.info("\n🗂️ Indexes:")
                for idx_name, idx_def in indexes:
                    logger.info(f"   • {idx_name}")
                
                # Count existing data
                cur.execute("SELECT COUNT(*) FROM chunks WHERE content IS NOT NULL")
                total_chunks = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM chunks WHERE embedding_nomic IS NOT NULL")
                embedded_chunks = cur.fetchone()[0]
                
                logger.info(f"\n📈 Data Status:")
                logger.info(f"   • Total chunks: {total_chunks:,}")
                logger.info(f"   • Embedded chunks: {embedded_chunks:,}")
                logger.info(f"   • Completion: {embedded_chunks/total_chunks*100:.1f}%" if total_chunks > 0 else "   • No chunks found")
                
                logger.info("✅ Schema verification complete!")
                return True
                
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            return False
        finally:
            conn.close()
            
    def run_phase2_enhancement(self):
        """Run complete Phase 2 database enhancement"""
        logger.info("🚀 Starting Phase 2: 4-Model Database Enhancement")
        
        # Step 1: Create embedding columns
        if not self.create_embedding_columns():
            logger.error("❌ Failed to create embedding columns")
            return False
            
        # Step 2: Add metadata columns
        if not self.add_metadata_columns():
            logger.error("❌ Failed to add metadata columns")
            return False
            
        # Step 3: Verify schema
        if not self.verify_schema():
            logger.error("❌ Schema verification failed")
            return False
            
        logger.info("🎉 Phase 2 database enhancement complete!")
        logger.info("📋 Ready for Phase 3: Intelligent Content Routing")
        return True

if __name__ == "__main__":
    enhancer = Phase2DatabaseEnhancer()
    success = enhancer.run_phase2_enhancement()
    exit(0 if success else 1)