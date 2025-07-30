#!/usr/bin/env python3
"""
Phonetic Query Cache System - Dr. Sarah Chen
===========================================

High-performance caching layer for phonetic search queries.
Implements LRU cache with phonetic variant generation and query optimization.
"""

import time
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Set
from collections import OrderedDict
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class CachedResult:
    """Cached search result with metadata"""
    results: List[Dict]
    query_hash: str
    timestamp: float
    match_count: int
    phonetic_variants: List[str]
    performance_metrics: Dict[str, float]

class PhoneticQueryCache:
    """High-performance phonetic query cache with intelligent variant generation"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, CachedResult] = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        self.phonetic_variants_cache: Dict[str, List[str]] = {}
        
        # Academic term phonetic mappings for enhanced accuracy
        self.academic_phonetic_mappings = {
            # Philosophers
            'foucault': ['focault', 'fuko', 'fukault'],
            'nietzsche': ['nietzche', 'nitsche', 'nietsche'],
            'heidegger': ['heideger', 'hydegger', 'hiedegger'],
            'sartre': ['sarter', 'sartr', 'sarttre'],
            'derrida': ['derida', 'derrda', 'derrrida'],
            'deleuze': ['deleuze', 'deleuse', 'deluse'],
            'agamben': ['agamban', 'agamben', 'agamban'],
            
            # Critical theory terms
            'biopolitics': ['bio-politics', 'bio politics', 'biopolitics'],
            'biopower': ['bio-power', 'bio power', 'biopower'],
            'disciplinary': ['disciplinery', 'diciplinary', 'disciplanary'],
            'panopticon': ['panopticon', 'panoptikon', 'panoptican'],
            'governmentality': ['governmentality', 'governmental', 'gouvernmentality'],
            
            # Common academic mishearings
            'consciousness': ['consciouness', 'conciousness', 'consciosness'],
            'phenomenology': ['phenomenalogy', 'phenominalogy', 'fenomenology'],
            'epistemology': ['epistimoligy', 'epistomology', 'epistemologia'],
            'ontology': ['antology', 'ontolgy', 'ontologia'],
            'hermeneutics': ['hermenautics', 'hermeneutics', 'hermanutics'],
        }
    
    def _generate_query_hash(self, query: str, query_type: str = 'content', limit: int = 20) -> str:
        """Generate unique hash for query parameters"""
        query_normalized = query.lower().strip()
        hash_input = f"{query_normalized}|{query_type}|{limit}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _generate_phonetic_variants(self, query: str) -> List[str]:
        """Generate phonetic variants for enhanced search accuracy"""
        query_lower = query.lower().strip()
        
        # Check cache first
        if query_lower in self.phonetic_variants_cache:
            return self.phonetic_variants_cache[query_lower]
        
        variants = set([query_lower])
        
        # Add academic term mappings
        for term, mappings in self.academic_phonetic_mappings.items():
            if term in query_lower:
                for mapping in mappings:
                    variants.add(query_lower.replace(term, mapping))
        
        # Add common phonetic transformations
        variants.update(self._apply_phonetic_transformations(query_lower))
        
        # Cache the results
        variant_list = list(variants)
        self.phonetic_variants_cache[query_lower] = variant_list
        
        return variant_list
    
    def _apply_phonetic_transformations(self, query: str) -> Set[str]:
        """Apply systematic phonetic transformations"""
        variants = set()
        
        # Common letter substitutions in academic contexts
        transformations = [
            ('ph', 'f'),    # philosophy -> filosofy
            ('qu', 'kw'),   # quote -> kwote  
            ('ch', 'k'),    # chaos -> kaos
            ('x', 'ks'),    # text -> tekst
            ('c', 'k'),     # consciousness -> konsciousness
            ('tion', 'shun'), # nation -> nashun
            ('sion', 'shun'), # vision -> vishun
        ]
        
        for old, new in transformations:
            if old in query:
                variants.add(query.replace(old, new))
        
        return variants
    
    def _is_cache_valid(self, cached_result: CachedResult) -> bool:
        """Check if cached result is still valid"""
        return (time.time() - cached_result.timestamp) < self.ttl_seconds
    
    def _evict_oldest(self):
        """Remove oldest entry when cache is full"""
        if len(self.cache) >= self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"Evicted oldest cache entry: {oldest_key}")
    
    def get(self, query: str, query_type: str = 'content', limit: int = 20) -> Optional[CachedResult]:
        """Get cached result if available and valid"""
        query_hash = self._generate_query_hash(query, query_type, limit)
        
        if query_hash not in self.cache:
            self.miss_count += 1
            return None
        
        cached_result = self.cache[query_hash]
        
        if not self._is_cache_valid(cached_result):
            del self.cache[query_hash]
            self.miss_count += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(query_hash)
        self.hit_count += 1
        
        logger.debug(f"Cache hit for query: {query[:50]}... (hash: {query_hash[:8]})")
        return cached_result
    
    def put(self, query: str, results: List[Dict], query_type: str = 'content', 
            limit: int = 20, performance_metrics: Optional[Dict[str, float]] = None):
        """Cache search results with metadata"""
        query_hash = self._generate_query_hash(query, query_type, limit)
        
        # Evict oldest if needed
        self._evict_oldest()
        
        # Generate phonetic variants for this query
        phonetic_variants = self._generate_phonetic_variants(query)
        
        cached_result = CachedResult(
            results=results,
            query_hash=query_hash,
            timestamp=time.time(),
            match_count=len(results),
            phonetic_variants=phonetic_variants,
            performance_metrics=performance_metrics or {}
        )
        
        self.cache[query_hash] = cached_result
        logger.debug(f"Cached results for query: {query[:50]}... ({len(results)} results)")
    
    def get_phonetic_suggestions(self, query: str) -> List[str]:
        """Get phonetic variant suggestions for query expansion"""
        return self._generate_phonetic_variants(query)
    
    def get_author_similarity_cache(self, author_query: str) -> Optional[List[Dict]]:
        """Specialized cache for author similarity searches"""
        cache_key = f"author_sim_{author_query.lower()}"
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if self._is_cache_valid(cached):
                self.cache.move_to_end(cache_key)
                return cached.results
        
        return None
    
    def cache_author_similarity(self, author_query: str, results: List[Dict]):
        """Cache author similarity search results"""
        cache_key = f"author_sim_{author_query.lower()}"
        self._evict_oldest()
        
        cached_result = CachedResult(
            results=results,
            query_hash=cache_key,
            timestamp=time.time(),
            match_count=len(results),
            phonetic_variants=[],
            performance_metrics={}
        )
        
        self.cache[cache_key] = cached_result
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache performance statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'phonetic_variants_cached': len(self.phonetic_variants_cache),
            'ttl_seconds': self.ttl_seconds
        }
    
    def clear_expired(self):
        """Remove all expired entries from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, cached_result in self.cache.items()
            if (current_time - cached_result.timestamp) >= self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def warm_cache_with_common_queries(self):
        """Pre-warm cache with common academic search terms"""
        common_queries = [
            'philosophy', 'consciousness', 'foucault', 'power', 'knowledge',
            'biopolitics', 'discipline', 'democracy', 'freedom', 'ethics',
            'phenomenology', 'ontology', 'epistemology', 'hermeneutics',
            'postmodernism', 'critical theory', 'deconstruction'
        ]
        
        logger.info("Cache warming initiated for common academic queries")
        # Note: Actual warming would require database access
        # This is a placeholder for the warming mechanism

# Global cache instance
phonetic_cache = PhoneticQueryCache(max_size=1000, ttl_seconds=3600)

# Utility functions for integration
def get_cached_search_results(query: str, query_type: str = 'content', 
                            limit: int = 20) -> Optional[List[Dict]]:
    """Utility function to get cached search results"""
    cached = phonetic_cache.get(query, query_type, limit)
    return cached.results if cached else None

def cache_search_results(query: str, results: List[Dict], query_type: str = 'content',
                        limit: int = 20, performance_metrics: Optional[Dict] = None):
    """Utility function to cache search results"""
    phonetic_cache.put(query, results, query_type, limit, performance_metrics)

def get_phonetic_query_suggestions(query: str) -> List[str]:
    """Get phonetic variant suggestions for a query"""
    return phonetic_cache.get_phonetic_suggestions(query)

def get_cache_performance_stats() -> Dict[str, any]:
    """Get cache performance statistics"""
    return phonetic_cache.get_cache_stats()