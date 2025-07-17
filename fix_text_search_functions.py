#!/usr/bin/env python3
"""
🔧 Fix Text Search Functions - Use search_vector column
======================================================

Fix the PostgreSQL functions to use the optimized search_vector column
instead of regenerating tsvector on every search (which takes 28+ seconds!)
"""

import psycopg2
import os
import time

def fix_text_search_functions():
    """Fix text search functions to use optimized search_vector column"""
    
    print("🔧 FIXING TEXT SEARCH FUNCTIONS - Using search_vector column")
    print("=" * 60)
    
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        with conn.cursor() as cur:
            
            # Fix api_text_search function to use search_vector
            print("📝 Fixing api_text_search function...")
            cur.execute("DROP FUNCTION IF EXISTS api_text_search(text,integer,integer)")
            
            cur.execute("""
                CREATE OR REPLACE FUNCTION api_text_search(
                    p_query TEXT,
                    p_limit INTEGER DEFAULT 20,
                    p_book_id INTEGER DEFAULT NULL
                ) RETURNS TABLE (
                    chunk_id VARCHAR(255),
                    book_id INTEGER,
                    content TEXT,
                    title VARCHAR(500),
                    author VARCHAR(255),
                    chapter_number INTEGER,
                    text_rank FLOAT,
                    search_type TEXT,
                    execution_time_ms INTEGER
                ) LANGUAGE plpgsql AS $$
                DECLARE
                    v_start_time TIMESTAMP;
                BEGIN
                    v_start_time := clock_timestamp();
                    
                    -- Input validation
                    IF p_query IS NULL OR p_query = '' THEN
                        RAISE EXCEPTION 'Search query cannot be empty';
                    END IF;
                    
                    IF p_limit < 1 OR p_limit > 100 THEN
                        p_limit := 20;
                    END IF;
                    
                    -- Execute OPTIMIZED text search using pre-computed search_vector
                    RETURN QUERY
                    SELECT 
                        c.chunk_id,
                        c.book_id,
                        c.content,
                        b.title,
                        b.author,
                        c.chapter_number,
                        ts_rank(c.search_vector, plainto_tsquery('english', p_query))::FLOAT as text_rank,
                        'text_search'::TEXT as search_type,
                        EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time))::INTEGER * 1000 as execution_time_ms
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE 
                        c.search_vector @@ plainto_tsquery('english', p_query)
                        AND (p_book_id IS NULL OR c.book_id = p_book_id)
                    ORDER BY text_rank DESC
                    LIMIT p_limit;
                END
                $$;
            """)
            
            print("✅ api_text_search function fixed!")
            
            # Fix hybrid search function to use search_vector
            print("📝 Fixing api_hybrid_search_optimized function...")
            cur.execute("DROP FUNCTION IF EXISTS api_hybrid_search_optimized(text,vector,double precision,double precision,integer)")
            
            cur.execute("""
                CREATE OR REPLACE FUNCTION api_hybrid_search_optimized(
                    p_query TEXT,
                    p_query_vector vector(384),
                    p_text_weight FLOAT DEFAULT 0.7,
                    p_vector_weight FLOAT DEFAULT 0.3,
                    p_limit INTEGER DEFAULT 20
                ) RETURNS TABLE (
                    chunk_id VARCHAR(255),
                    book_id INTEGER,
                    content TEXT,
                    title VARCHAR(500),
                    author VARCHAR(255),
                    combined_score FLOAT,
                    text_rank FLOAT,
                    vector_similarity FLOAT,
                    search_type TEXT,
                    execution_time_ms INTEGER
                ) LANGUAGE plpgsql AS $$
                DECLARE
                    v_start_time TIMESTAMP;
                BEGIN
                    v_start_time := clock_timestamp();
                    
                    -- Input validation
                    IF p_query IS NULL OR p_query = '' THEN
                        RAISE EXCEPTION 'Search query cannot be empty';
                    END IF;
                    
                    IF p_query_vector IS NULL THEN
                        RAISE EXCEPTION 'Query vector cannot be null';
                    END IF;
                    
                    IF p_limit < 1 OR p_limit > 100 THEN
                        p_limit := 20;
                    END IF;
                    
                    -- OPTIMIZED hybrid search using search_vector column
                    RETURN QUERY
                    WITH text_candidates AS (
                        SELECT 
                            c.chunk_id,
                            c.book_id,
                            c.content,
                            b.title,
                            b.author,
                            ts_rank(c.search_vector, plainto_tsquery('english', p_query))::FLOAT as text_rank
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE c.search_vector @@ plainto_tsquery('english', p_query)
                        ORDER BY text_rank DESC
                        LIMIT p_limit * 2
                    ),
                    vector_candidates AS (
                        SELECT 
                            c.chunk_id,
                            c.book_id,
                            c.content,
                            b.title,
                            b.author,
                            (1 - (ce.embedding_vector <=> p_query_vector))::FLOAT as vector_similarity
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        JOIN chunk_embeddings ce ON c.chunk_id = ce.chunk_id
                        WHERE ce.embedding_vector IS NOT NULL
                        ORDER BY ce.embedding_vector <=> p_query_vector
                        LIMIT p_limit * 2
                    ),
                    combined_results AS (
                        SELECT 
                            COALESCE(tc.chunk_id, vc.chunk_id) as chunk_id,
                            COALESCE(tc.book_id, vc.book_id) as book_id,
                            COALESCE(tc.content, vc.content) as content,
                            COALESCE(tc.title, vc.title) as title,
                            COALESCE(tc.author, vc.author) as author,
                            (p_text_weight * COALESCE(tc.text_rank, 0.0) + 
                             p_vector_weight * COALESCE(vc.vector_similarity, 0.0))::FLOAT as combined_score,
                            COALESCE(tc.text_rank, 0.0)::FLOAT as text_rank,
                            COALESCE(vc.vector_similarity, 0.0)::FLOAT as vector_similarity
                        FROM text_candidates tc
                        FULL OUTER JOIN vector_candidates vc ON tc.chunk_id = vc.chunk_id
                    )
                    SELECT 
                        cr.chunk_id,
                        cr.book_id,
                        cr.content,
                        cr.title,
                        cr.author,
                        cr.combined_score,
                        cr.text_rank,
                        cr.vector_similarity,
                        'hybrid_search'::TEXT as search_type,
                        EXTRACT(EPOCH FROM (clock_timestamp() - v_start_time))::INTEGER * 1000 as execution_time_ms
                    FROM combined_results cr
                    ORDER BY cr.combined_score DESC
                    LIMIT p_limit;
                END
                $$;
            """)
            
            print("✅ api_hybrid_search_optimized function fixed!")
            
            conn.commit()
            print("🎉 ALL FUNCTIONS OPTIMIZED!")
            
            # Test the optimized functions
            print("\n🧪 TESTING OPTIMIZED FUNCTIONS:")
            print("-" * 30)
            
            # Test text search
            start_time = time.time()
            cur.execute("SELECT COUNT(*) FROM api_text_search('technology', 10)")
            result_count = cur.fetchone()[0]
            text_time = (time.time() - start_time) * 1000
            print(f"⚡ Text search: {text_time:.2f}ms ({result_count} results)")
            
            # Test hybrid search
            cur.execute("SELECT embedding_vector FROM chunk_embeddings WHERE embedding_vector IS NOT NULL ORDER BY RANDOM() LIMIT 1")
            vector_result = cur.fetchone()
            if vector_result:
                sample_vector = vector_result[0]
                start_time = time.time()
                cur.execute("SELECT COUNT(*) FROM api_hybrid_search_optimized('artificial intelligence', %s, 0.7, 0.3, 10)", (sample_vector,))
                result_count = cur.fetchone()[0]
                hybrid_time = (time.time() - start_time) * 1000
                print(f"🔀 Hybrid search: {hybrid_time:.2f}ms ({result_count} results)")
            
            print("\n🎯 Performance Improvement:")
            print(f"   Text search: 28,345ms → {text_time:.2f}ms = {((28345-text_time)/28345*100):.1f}% faster!")
            if vector_result:
                print(f"   Hybrid search: Fixed and optimized!")
                
            return True
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

if __name__ == "__main__":
    success = fix_text_search_functions()
    if success:
        print("\n🚀 Ready to run optimized performance tests!")
    else:
        print("\n❌ Fix failed - check error messages")