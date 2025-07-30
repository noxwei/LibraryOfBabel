#!/usr/bin/env python3
"""
Advanced Search Result Caching System
====================================

Implements intelligent caching for LibraryOfBabel API while phonetic daemon runs.
- Multi-tier caching (memory + Redis if available)
- Query normalization for cache hits
- TTL-based expiration
- Cache warming for common queries
"""

import psycopg2
import psycopg2.extras
import psycopg2.pool
import time
import json
import hashlib
import threading
from functools import lru_cache
from flask import Flask, request, jsonify
from typing import Dict, Any, List, Optional, Tuple
import logging

# Try Redis for persistent caching
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

app = Flask(__name__)

class AdvancedCacheSystem:
    """Multi-tier caching system for search results"""
    
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'memory_size': 0,
            'redis_hits': 0
        }
        self.cache_lock = threading.RLock()
        self.max_memory_cache_size = 1000  # Max items in memory
        self.default_ttl = 3600  # 1 hour TTL
        
        # Initialize Redis if available
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except:
                logger.info("⚠️ Redis unavailable, using memory-only cache")
                self.redis_client = None
        else:
            logger.info("⚠️ Redis not installed, using memory-only cache")
    
    def normalize_query(self, query: str) -> str:
        """Normalize query for consistent caching"""
        if not query:
            return ""
        
        # Convert to lowercase and strip
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        # Remove common punctuation
        for char in '.,!?;:"\'()[]{}':
            normalized = normalized.replace(char, '')
        
        return normalized
    
    def generate_cache_key(self, query: str, search_type: str = "standard") -> str:
        """Generate consistent cache key"""
        normalized_query = self.normalize_query(query)
        key_data = f"{search_type}:{normalized_query}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache (memory first, then Redis)"""
        with self.cache_lock:
            # Check memory cache first
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                
                # Check if expired
                if time.time() - cache_entry['timestamp'] < cache_entry['ttl']:
                    self.cache_stats['hits'] += 1
                    logger.debug(f"Memory cache HIT: {cache_key[:8]}...")
                    return cache_entry['data']
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
                    self.cache_stats['memory_size'] = len(self.memory_cache)
            
            # Check Redis cache
            if self.redis_client:
                try:
                    redis_data = self.redis_client.get(f"search:{cache_key}")
                    if redis_data:
                        result = json.loads(redis_data)
                        
                        # Store in memory cache for faster access
                        self._store_in_memory(cache_key, result)
                        
                        self.cache_stats['redis_hits'] += 1
                        logger.debug(f"Redis cache HIT: {cache_key[:8]}...")
                        return result
                except Exception as e:
                    logger.warning(f"Redis get error: {e}")
            
            self.cache_stats['misses'] += 1
            return None
    
    def store_in_cache(self, cache_key: str, data: Dict[str, Any], ttl: int = None) -> None:
        """Store result in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Store in memory cache
        self._store_in_memory(cache_key, data, ttl)
        
        # Store in Redis cache
        if self.redis_client:
            try:
                redis_data = json.dumps(data)
                self.redis_client.setex(f"search:{cache_key}", ttl, redis_data)
                logger.debug(f"Stored in Redis: {cache_key[:8]}...")
            except Exception as e:
                logger.warning(f"Redis store error: {e}")
    
    def _store_in_memory(self, cache_key: str, data: Dict[str, Any], ttl: int = None) -> None:
        """Store in memory cache with LRU eviction"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.cache_lock:
            # Evict oldest if at capacity
            if len(self.memory_cache) >= self.max_memory_cache_size:
                oldest_key = min(
                    self.memory_cache.keys(),
                    key=lambda k: self.memory_cache[k]['timestamp']
                )
                del self.memory_cache[oldest_key]
            
            self.memory_cache[cache_key] = {
                'data': data,
                'timestamp': time.time(),
                'ttl': ttl
            }
            self.cache_stats['memory_size'] = len(self.memory_cache)
            logger.debug(f"Stored in memory: {cache_key[:8]}...")
    
    def warm_cache(self, common_queries: List[str]) -> None:
        """Pre-warm cache with common queries"""
        logger.info(f"🔥 Warming cache with {len(common_queries)} common queries...")
        
        warmed = 0
        for query in common_queries:
            cache_key = self.generate_cache_key(query)
            
            # Skip if already cached
            if self.get_from_cache(cache_key):
                continue
            
            # Execute search and cache result
            try:
                result = execute_search_query(query)
                if result:
                    self.store_in_cache(cache_key, result, ttl=7200)  # 2 hour TTL for warmed cache
                    warmed += 1
            except Exception as e:
                logger.warning(f"Cache warm failed for '{query}': {e}")
        
        logger.info(f"✅ Cache warmed: {warmed} queries cached")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate_percent': round(hit_rate, 1),
            'total_hits': self.cache_stats['hits'],
            'total_misses': self.cache_stats['misses'],
            'redis_hits': self.cache_stats['redis_hits'],
            'memory_cache_size': self.cache_stats['memory_size'],
            'redis_available': self.redis_client is not None
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        with self.cache_lock:
            self.memory_cache.clear()
            self.cache_stats['memory_size'] = 0
        
        if self.redis_client:
            try:
                # Clear only search-related keys
                for key in self.redis_client.scan_iter(match="search:*"):
                    self.redis_client.delete(key)
                logger.info("✅ Redis cache cleared")
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")
        
        logger.info("✅ Cache cleared")

# Initialize global cache system
cache_system = AdvancedCacheSystem()

# Database connection pool
connection_pool = psycopg2.pool.ThreadedConnectionPool(
    2, 20, **DB_CONFIG
)

def get_db_connection():
    """Get database connection from pool"""
    return connection_pool.getconn()

def return_db_connection(conn):
    """Return database connection to pool"""
    connection_pool.putconn(conn)

def execute_search_query(query: str, limit: int = 10) -> Dict[str, Any]:
    """Execute optimized search query"""
    if not query or len(query) < 2:
        return {"error": "Query too short", "results": [], "count": 0}
    
    start_time = time.time()
    conn = None
    
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Optimized full-text search with ranking
            cur.execute("""
                SELECT c.chunk_id, 
                       LEFT(c.content, 200) as content_preview,
                       b.title, 
                       b.author,
                       ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
                FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                  AND ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', %s)) > 0.05
                ORDER BY rank DESC
                LIMIT %s
            """, (query, query, query, limit))
            
            results = cur.fetchall()
            query_time = (time.time() - start_time) * 1000
            
            return {
                "query": query,
                "results": [dict(r) for r in results],
                "count": len(results),
                "query_time_ms": round(query_time, 1),
                "cache_status": "miss",
                "optimization": "full_text_search_with_ranking"
            }
    
    except Exception as e:
        logger.error(f"Search query error: {e}")
        return {
            "error": str(e),
            "results": [],
            "count": 0,
            "query_time_ms": round((time.time() - start_time) * 1000, 1)
        }
    
    finally:
        if conn:
            return_db_connection(conn)

@app.route('/search')
def cached_search():
    """Search endpoint with advanced caching"""
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results
    
    if not query:
        return jsonify({"error": "Query parameter required"}), 400
    
    if len(query) < 2:
        return jsonify({"error": "Query too short"}), 400
    
    start_time = time.time()
    
    # Generate cache key
    cache_key = cache_system.generate_cache_key(query)
    
    # Try to get from cache
    cached_result = cache_system.get_from_cache(cache_key)
    if cached_result:
        cached_result['cache_status'] = 'hit'
        cached_result['total_time_ms'] = round((time.time() - start_time) * 1000, 1)
        return jsonify(cached_result)
    
    # Execute search
    result = execute_search_query(query, limit)
    
    # Cache successful results
    if result.get('count', 0) > 0 and 'error' not in result:
        cache_system.store_in_cache(cache_key, result)
    
    result['total_time_ms'] = round((time.time() - start_time) * 1000, 1)
    return jsonify(result)

@app.route('/cache/stats')
def cache_stats():
    """Get cache performance statistics"""
    return jsonify(cache_system.get_stats())

@app.route('/cache/warm', methods=['POST'])
def warm_cache():
    """Warm cache with common queries"""
    common_queries = [
        "the great gatsby",
        "to kill a mockingbird", 
        "pride and prejudice",
        "harry potter",
        "lord of the rings",
        "data science",
        "machine learning",
        "python programming",
        "javascript tutorial",
        "artificial intelligence",
        "climate change",
        "quantum physics",
        "world history",
        "philosophy of mind",
        "economic theory"
    ]
    
    # Run warming in background thread
    def warm_in_background():
        cache_system.warm_cache(common_queries)
    
    threading.Thread(target=warm_in_background, daemon=True).start()
    
    return jsonify({
        "message": "Cache warming started",
        "queries_count": len(common_queries)
    })

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all caches"""
    cache_system.clear_cache()
    return jsonify({"message": "Cache cleared"})

def test_caching_performance():
    """Test caching system performance"""
    print("🚀 Testing Advanced Caching System")
    print("=" * 50)
    
    # Start test server
    def run_server():
        app.run(host='127.0.0.1', port=9006, debug=False, use_reloader=False)
    
    import threading
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    import requests
    
    test_queries = [
        "python programming",
        "data science methods", 
        "machine learning algorithms",
        "javascript frameworks",
        "climate change research"
    ]
    
    print("🧪 Testing cache misses (first run):")
    first_run_times = []
    
    for query in test_queries:
        start = time.time()
        try:
            response = requests.get(
                "http://127.0.0.1:9006/search",
                params={'q': query},
                timeout=5
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                cache_status = data.get('cache_status', 'unknown')
                results = data.get('count', 0)
                
                print(f"  '{query}' -> {elapsed:.1f}ms ({cache_status}, {results} results)")
                first_run_times.append(elapsed)
            else:
                print(f"  '{query}' -> ERROR {response.status_code}")
                
        except Exception as e:
            print(f"  '{query}' -> ERROR: {e}")
    
    print(f"\n🔥 Testing cache hits (second run):")
    second_run_times = []
    
    for query in test_queries:
        start = time.time()
        try:
            response = requests.get(
                "http://127.0.0.1:9006/search", 
                params={'q': query},
                timeout=5
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                cache_status = data.get('cache_status', 'unknown')
                results = data.get('count', 0)
                
                print(f"  '{query}' -> {elapsed:.1f}ms ({cache_status}, {results} results)")
                second_run_times.append(elapsed)
            else:
                print(f"  '{query}' -> ERROR {response.status_code}")
                
        except Exception as e:
            print(f"  '{query}' -> ERROR: {e}")
    
    # Get cache stats
    try:
        stats_response = requests.get("http://127.0.0.1:9006/cache/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            print(f"\n📊 Cache Performance:")
            print(f"  Hit rate: {stats['hit_rate_percent']}%")
            print(f"  Total hits: {stats['total_hits']}")
            print(f"  Total misses: {stats['total_misses']}")
            print(f"  Memory cache size: {stats['memory_cache_size']}")
            print(f"  Redis available: {stats['redis_available']}")
    except:
        print("  Could not retrieve cache stats")
    
    # Calculate performance improvement
    if first_run_times and second_run_times:
        avg_first = sum(first_run_times) / len(first_run_times)
        avg_second = sum(second_run_times) / len(second_run_times)
        improvement = ((avg_first - avg_second) / avg_first) * 100
        
        print(f"\n🎯 Performance Improvement:")
        print(f"  Average uncached: {avg_first:.1f}ms")
        print(f"  Average cached: {avg_second:.1f}ms")
        print(f"  Speed improvement: {improvement:.1f}%")
        
        if improvement > 80:
            print("  ✅ EXCELLENT: Cache working very well")
        elif improvement > 50:
            print("  ✅ GOOD: Significant cache benefit")
        elif improvement > 20:
            print("  ⚠️ FAIR: Some cache benefit")
        else:
            print("  ❌ POOR: Cache not providing much benefit")

if __name__ == "__main__":
    test_caching_performance()