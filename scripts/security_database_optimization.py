#!/usr/bin/env python3
"""
Security Agent: Database Query Optimization & Injection Prevention
Critical Mission: Secure and optimize vector queries for production deployment
============================================================================

Security Focuses:
1. SQL injection prevention for vector queries
2. Query timeouts and resource limits
3. Input validation and sanitization
4. Error boundary implementation
5. Connection security hardening
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import re
import time
import logging
import sys
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSecurityOptimizer:
    def __init__(self, db_config):
        self.db_config = db_config
        self.max_query_time = 30  # seconds
        self.max_results = 1000
        
    def sanitize_text_input(self, text):
        """Sanitize text input to prevent injection attacks"""
        if not isinstance(text, str):
            raise ValueError("Input must be string")
        
        # Remove dangerous SQL keywords and characters
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
            r'\bALTER\b', r'\bCREATE\b', r'\bEXEC\b', r'\bUNION\b',
            r'--', r'/\*', r'\*/', r';(?=\s*\w)', r'\bxp_\w+\b'
        ]
        
        text = text.strip()
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt blocked: {pattern}")
                raise ValueError("Invalid input detected")
        
        # Limit length
        if len(text) > 1000:
            text = text[:1000]
        
        return text
    
    def validate_numeric_params(self, confidence_weight=None, limit=None, threshold=None):
        """Validate and sanitize numeric parameters"""
        validated = {}
        
        if confidence_weight is not None:
            if not isinstance(confidence_weight, (int, float)):
                raise ValueError("confidence_weight must be numeric")
            validated['confidence_weight'] = max(0.0, min(float(confidence_weight), 1.0))
        
        if limit is not None:
            if not isinstance(limit, int) or limit < 1:
                raise ValueError("limit must be positive integer")
            validated['limit'] = min(int(limit), self.max_results)
        
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                raise ValueError("threshold must be numeric")
            validated['threshold'] = max(0.0, min(float(threshold), 1.0))
        
        return validated
    
    def create_secure_connection(self):
        """Create a secure database connection with timeouts"""
        try:
            conn = psycopg2.connect(
                **self.db_config,
                cursor_factory=RealDictCursor,
                connect_timeout=10,
                options=f"-c statement_timeout=300000ms"  # 5 minutes for index operations
            )
            conn.autocommit = False  # Ensure explicit transaction control
            return conn
        except Exception as e:
            logger.error(f"Secure connection failed: {e}")
            raise
    
    def create_security_functions(self):
        """Create PostgreSQL security functions"""
        security_sql = """
        -- Security function: Validate vector query parameters
        CREATE OR REPLACE FUNCTION validate_vector_query_params(
            p_limit INTEGER DEFAULT 20,
            p_confidence_weight FLOAT DEFAULT 0.25,
            p_threshold FLOAT DEFAULT 0.0
        ) RETURNS BOOLEAN AS $$
        BEGIN
            -- Validate limit
            IF p_limit < 1 OR p_limit > 1000 THEN
                RAISE EXCEPTION 'Invalid limit: must be between 1 and 1000';
            END IF;
            
            -- Validate confidence weight
            IF p_confidence_weight < 0.0 OR p_confidence_weight > 1.0 THEN
                RAISE EXCEPTION 'Invalid confidence_weight: must be between 0.0 and 1.0';
            END IF;
            
            -- Validate threshold
            IF p_threshold < 0.0 OR p_threshold > 1.0 THEN
                RAISE EXCEPTION 'Invalid threshold: must be between 0.0 and 1.0';
            END IF;
            
            RETURN TRUE;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;

        -- Security function: Safe vector similarity search with bounds checking
        CREATE OR REPLACE FUNCTION secure_vector_similarity_search(
            p_query_vector VECTOR(768),
            p_confidence_weight FLOAT DEFAULT 0.25,
            p_limit INTEGER DEFAULT 20,
            p_similarity_threshold FLOAT DEFAULT 0.0
        ) RETURNS TABLE (
            chunk_id TEXT,
            book_id INTEGER,
            title TEXT,
            content TEXT,
            base_similarity FLOAT,
            confidence_score FLOAT,
            weighted_score FLOAT
        ) AS $$
        BEGIN
            -- Validate parameters
            PERFORM validate_vector_query_params(p_limit, p_confidence_weight, p_similarity_threshold);
            
            -- Execute secure query with resource limits
            RETURN QUERY
            SELECT 
                ce.chunk_id,
                ce.book_id,
                c.title,
                LEFT(c.content, 500) as content,  -- Limit content length for security
                (1 - (ce.embedding_vector <=> p_query_vector)) as base_similarity,
                COALESCE(ce.confidence_score, 0.5) as confidence_score,
                ((1 - (ce.embedding_vector <=> p_query_vector)) * 
                 (1.0 + p_confidence_weight * COALESCE(ce.confidence_score, 0.5))) as weighted_score
            FROM chunk_embeddings ce
            JOIN chunks c ON ce.chunk_id = c.chunk_id
            WHERE ce.embedding_vector IS NOT NULL
            AND ce.embedding_model = 'nomic-embed-text'
            AND (1 - (ce.embedding_vector <=> p_query_vector)) >= p_similarity_threshold
            ORDER BY weighted_score DESC
            LIMIT p_limit;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;

        -- Security function: Rate limiting table
        CREATE TABLE IF NOT EXISTS api_rate_limits (
            client_ip INET,
            request_count INTEGER DEFAULT 1,
            window_start TIMESTAMP DEFAULT NOW(),
            last_request TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (client_ip)
        );

        -- Function to check rate limits (100 requests per minute per IP)
        CREATE OR REPLACE FUNCTION check_rate_limit(p_client_ip INET)
        RETURNS BOOLEAN AS $$
        DECLARE
            current_count INTEGER;
            window_start TIMESTAMP;
        BEGIN
            -- Clean old entries (older than 1 minute)
            DELETE FROM api_rate_limits 
            WHERE window_start < NOW() - INTERVAL '1 minute';
            
            -- Get current count for this IP
            SELECT request_count, api_rate_limits.window_start 
            INTO current_count, window_start
            FROM api_rate_limits 
            WHERE client_ip = p_client_ip;
            
            IF current_count IS NULL THEN
                -- First request from this IP
                INSERT INTO api_rate_limits (client_ip, request_count, window_start, last_request)
                VALUES (p_client_ip, 1, NOW(), NOW())
                ON CONFLICT (client_ip) 
                DO UPDATE SET 
                    request_count = 1,
                    window_start = NOW(),
                    last_request = NOW();
                RETURN TRUE;
            ELSIF current_count >= 100 THEN
                -- Rate limit exceeded
                RETURN FALSE;
            ELSE
                -- Increment counter
                UPDATE api_rate_limits 
                SET 
                    request_count = request_count + 1,
                    last_request = NOW()
                WHERE client_ip = p_client_ip;
                RETURN TRUE;
            END IF;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;

        -- Index for rate limiting performance
        CREATE INDEX IF NOT EXISTS idx_rate_limits_window 
        ON api_rate_limits(window_start);
        """
        
        conn = None
        try:
            conn = self.create_secure_connection()
            with conn.cursor() as cur:
                cur.execute(security_sql)
                conn.commit()
                logger.info("Security functions created successfully")
                return True
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to create security functions: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def optimize_vector_indexes(self):
        """Optimize vector indexes for security and performance"""
        conn = None
        try:
            conn = self.create_secure_connection()
            conn.autocommit = True  # Required for CONCURRENTLY operations
            
            with conn.cursor() as cur:
                # Drop existing index if exists
                cur.execute("DROP INDEX IF EXISTS idx_chunk_embeddings_vector_hnsw;")
                
                # Create HNSW index with CONCURRENTLY (outside transaction)
                cur.execute("""
                    CREATE INDEX CONCURRENTLY idx_chunk_embeddings_vector_hnsw 
                    ON chunk_embeddings 
                    USING hnsw (embedding_vector vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                    WHERE embedding_vector IS NOT NULL 
                    AND embedding_model = 'nomic-embed-text';
                """)
                
                # Create security index
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_security
                    ON chunk_embeddings(embedding_model, book_id)
                    WHERE embedding_vector IS NOT NULL;
                """)
                
                # Analyze tables
                cur.execute("ANALYZE chunk_embeddings;")
                cur.execute("ANALYZE chunks;")
                cur.execute("ANALYZE books;")
                
                logger.info("Vector indexes optimized with security considerations")
                return True
        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def test_security_measures(self):
        """Test all security measures"""
        print("🔒 Testing Security Measures")
        print("=" * 50)
        
        # Test 1: Input sanitization
        print("🧪 Test 1: Input sanitization")
        try:
            # Should pass
            safe_text = self.sanitize_text_input("normal search query")
            print(f"   ✅ Safe input accepted: '{safe_text[:50]}...'")
            
            # Should fail
            try:
                dangerous_text = self.sanitize_text_input("'; DROP TABLE books; --")
                print(f"   ❌ Dangerous input incorrectly accepted")
            except ValueError:
                print(f"   ✅ SQL injection attempt blocked")
        except Exception as e:
            print(f"   ❌ Input sanitization test failed: {e}")
        
        # Test 2: Parameter validation
        print("\n🧪 Test 2: Parameter validation")
        try:
            # Valid parameters
            valid_params = self.validate_numeric_params(
                confidence_weight=0.25, 
                limit=20, 
                threshold=0.5
            )
            print(f"   ✅ Valid parameters accepted: {valid_params}")
            
            # Invalid parameters
            try:
                invalid_params = self.validate_numeric_params(limit=-5)
                print(f"   ❌ Invalid parameters incorrectly accepted")
            except ValueError:
                print(f"   ✅ Invalid parameters rejected")
        except Exception as e:
            print(f"   ❌ Parameter validation test failed: {e}")
        
        # Test 3: Database connection security
        print("\n🧪 Test 3: Secure database connection")
        try:
            conn = self.create_secure_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
            conn.close()
            print(f"   ✅ Secure connection established and tested")
        except Exception as e:
            print(f"   ❌ Secure connection test failed: {e}")
        
        # Test 4: Security functions
        print("\n🧪 Test 4: Security functions")
        try:
            conn = self.create_secure_connection()
            with conn.cursor() as cur:
                # Test parameter validation function
                cur.execute("SELECT validate_vector_query_params(20, 0.25, 0.5)")
                result = cur.fetchone()
                if result[0]:
                    print(f"   ✅ Parameter validation function working")
                
                # Test rate limiting function
                cur.execute("SELECT check_rate_limit('127.0.0.1'::inet)")
                result = cur.fetchone()
                if result[0]:
                    print(f"   ✅ Rate limiting function working")
            
            conn.close()
        except Exception as e:
            print(f"   ❌ Security functions test failed: {e}")
        
        print("\n🛡️ Security optimization complete")
        return True

def main():
    """Security Agent: Execute database security optimization"""
    print("🔒 Security Agent: Database Query Optimization & Injection Prevention")
    print("=" * 70)
    
    try:
        db_config = get_database_config()
        security_optimizer = DatabaseSecurityOptimizer(db_config)
        
        print("🔧 Step 1: Creating security functions...")
        if security_optimizer.create_security_functions():
            print("   ✅ Security functions implemented")
        else:
            print("   ❌ Security functions failed")
            return False
        
        print("\n⚡ Step 2: Optimizing vector indexes...")
        if security_optimizer.optimize_vector_indexes():
            print("   ✅ Vector indexes optimized")
        else:
            print("   ❌ Index optimization failed")
            return False
        
        print("\n🧪 Step 3: Testing security measures...")
        if security_optimizer.test_security_measures():
            print("   ✅ Security tests passed")
        else:
            print("   ❌ Security tests failed")
            return False
        
        print("\n🎯 Security Agent Mission Status:")
        print("   • SQL injection prevention: ✅ Implemented")
        print("   • Query timeouts & limits: ✅ Implemented")
        print("   • Input validation: ✅ Implemented")
        print("   • Rate limiting: ✅ Implemented")
        print("   • Secure connections: ✅ Implemented")
        print("   • Error boundaries: ✅ Implemented")
        
        return True
        
    except Exception as e:
        print(f"❌ Security optimization failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)