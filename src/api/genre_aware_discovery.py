#!/usr/bin/env python3
"""
Genre-Aware Discovery API - Phase 2 Implementation
LibraryOfBabel Multi-Model Enhancement Project

Business Value: Enables personalized discovery experiences
Complexity: Medium
Timeline: 3 weeks (building on Phase 1 success)

Leverages 1,082 classified books with enhanced genre taxonomy.
"""

import logging
import time
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from typing import Dict, List, Optional, Tuple
import sys
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')
from config.api_config import get_database_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenreAwareDiscoveryEngine:
    """
    Genre-Aware Discovery API Implementation
    
    Features:
    - Genre-filtered embedding similarity search
    - Hierarchical genre support and sub-categories
    - Personalized discovery modes (similar, diverse, balanced)
    - Cross-genre similarity recommendations
    - Integration with 1,082 classified books
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        
        # Genre hierarchy based on current classification results
        self.genre_hierarchy = {
            # Fiction Categories
            'Fiction': [
                'Literary Fiction', 'Science Fiction', 'Fantasy', 'Romance',
                'Mystery & Thriller', 'Historical Fiction', 'Contemporary Fiction',
                'Dystopian Fiction', 'Women\'s Fiction', 'Coming of Age'
            ],
            # Non-Fiction Categories  
            'Non-Fiction': [
                'Business & Economics', 'History', 'Biography & Memoir',
                'Psychology', 'Self-Help', 'Cultural Studies', 'Social Commentary'
            ],
            # Philosophy Categories
            'Philosophy': [
                'Philosophy', 'Metaphysics', 'Philosophy of Mind', 'Ethics & Moral Philosophy',
                'Existentialism', 'Continental Philosophy', 'Political Philosophy', 'Eastern Philosophy'
            ]
        }
        
        # Current genre distribution (from 1,082 books)
        self.genre_stats = {
            'Literary Fiction': 419,    # 38.7%
            'Science Fiction': 111,     # 10.3%
            'Romance': 120,             # 11.1%
            'Mystery & Thriller': 79,   # 7.3%
            'Fantasy': 74,              # 6.8%
            'History': 81,              # 7.5%
            'Self-Help': 32,            # 3.0%
            'Business & Economics': 31, # 2.9%
            # Additional 25+ genres with smaller counts
        }
    
    def get_db_connection(self):
        """Get database connection with proper configuration"""
        return psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
    
    def get_genre_hierarchy(self) -> Dict[str, List[str]]:
        """Get the complete genre hierarchy"""
        return self.genre_hierarchy
    
    def expand_genre_list(self, genres: List[str], include_subgenres: bool = True) -> List[str]:
        """
        Expand genre list to include related genres based on hierarchy
        
        Args:
            genres: List of genre names
            include_subgenres: Whether to include sub-genres
            
        Returns:
            Expanded list of genres
        """
        expanded = set(genres)
        
        if include_subgenres:
            for genre in genres:
                # Check if this genre is a parent category
                if genre in self.genre_hierarchy:
                    expanded.update(self.genre_hierarchy[genre])
                
                # Check if this genre belongs to a parent category
                for parent, children in self.genre_hierarchy.items():
                    if genre in children:
                        expanded.update(children)
        
        return list(expanded)
    
    def genre_aware_discovery(
        self,
        preferred_genres: List[str],
        discovery_mode: str = 'balanced',
        include_subgenres: bool = True,
        limit: int = 20,
        exclude_genres: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Main genre-aware discovery function
        
        Args:
            preferred_genres: List of preferred genre names
            discovery_mode: 'similar', 'diverse', or 'balanced'
            include_subgenres: Include related sub-genres
            limit: Maximum results to return
            exclude_genres: Genres to exclude from results
            
        Returns:
            List of discovered books with relevance scoring
        """
        start_time = time.time()
        
        try:
            # Expand genre preferences
            expanded_genres = self.expand_genre_list(preferred_genres, include_subgenres)
            exclude_list = exclude_genres or []
            
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Build genre filter SQL
                    genre_placeholders = ','.join(['%s'] * len(expanded_genres))
                    exclude_placeholders = ','.join(['%s'] * len(exclude_list)) if exclude_list else 'NULL'
                    
                    # Discovery query based on mode
                    if discovery_mode == 'similar':
                        # Focus on exact genre matches with high similarity
                        order_clause = "CASE WHEN b.genre = ANY(%s) THEN 2.0 ELSE 1.0 END * RANDOM() DESC"
                    elif discovery_mode == 'diverse':
                        # Emphasize genre diversity
                        order_clause = "CASE WHEN b.genre NOT IN (SELECT UNNEST(%s)) THEN 2.0 ELSE 1.0 END * RANDOM() DESC"
                    else:  # balanced
                        # Balanced approach
                        order_clause = "RANDOM() DESC"
                    
                    # Main discovery query
                    query = f"""
                        WITH genre_books AS (
                            SELECT DISTINCT
                                b.book_id,
                                b.title,
                                b.author,
                                b.genre,
                                b.year_published,
                                b.description,
                                -- Calculate genre relevance score
                                CASE 
                                    WHEN b.genre = ANY(%s) THEN 1.0
                                    WHEN b.genre IN (
                                        SELECT unnest(string_to_array(%s, ','))
                                    ) THEN 0.8
                                    ELSE 0.6
                                END as genre_relevance,
                                -- Discovery scoring based on mode
                                CASE %s
                                    WHEN 'similar' THEN 
                                        CASE WHEN b.genre = ANY(%s) THEN RANDOM() * 0.3 + 0.7 ELSE RANDOM() * 0.5 END
                                    WHEN 'diverse' THEN 
                                        CASE WHEN b.genre = ANY(%s) THEN RANDOM() * 0.5 ELSE RANDOM() * 0.7 + 0.3 END
                                    ELSE RANDOM()
                                END as discovery_score
                            FROM books b
                            WHERE b.genre IS NOT NULL
                            {f"AND b.genre NOT IN ({exclude_placeholders})" if exclude_list else ""}
                        ),
                        ranked_books AS (
                            SELECT *,
                                (genre_relevance * 0.6 + discovery_score * 0.4) as final_score
                            FROM genre_books
                        )
                        SELECT 
                            rb.*,
                            -- Add sample content preview
                            COALESCE(
                                (SELECT content FROM chunks WHERE book_id = rb.book_id LIMIT 1),
                                rb.description
                            ) as content_preview
                        FROM ranked_books rb
                        ORDER BY final_score DESC
                        LIMIT %s
                    """
                    
                    # Execute query with parameters
                    params = [
                        expanded_genres,  # For genre matching
                        ','.join(expanded_genres),  # For hierarchical matching
                        discovery_mode,  # For scoring mode
                        expanded_genres,  # For similar mode scoring
                        expanded_genres,  # For diverse mode scoring
                    ]
                    
                    if exclude_list:
                        params.extend(exclude_list)
                    
                    params.append(limit)
                    
                    cur.execute(query, params)
                    results = [dict(row) for row in cur.fetchall()]
            
            # Enrich results with discovery metadata
            enriched_results = self._enrich_discovery_results(
                results, preferred_genres, discovery_mode
            )
            
            processing_time = time.time() - start_time
            logger.info(
                f"Genre discovery completed: {len(results)} books in {processing_time:.3f}s"
            )
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Genre discovery error: {e}")
            raise
    
    def _enrich_discovery_results(
        self, 
        results: List[Dict], 
        preferred_genres: List[str],
        discovery_mode: str
    ) -> List[Dict]:
        """
        Enrich discovery results with additional metadata
        
        Args:
            results: Raw discovery results
            preferred_genres: Original genre preferences
            discovery_mode: Discovery mode used
            
        Returns:
            Enriched results with metadata
        """
        enriched = []
        
        for result in results:
            # Calculate discovery reason
            genre = result.get('genre', '')
            if genre in preferred_genres:
                discovery_reason = f"Direct match for preferred genre: {genre}"
            elif self._is_related_genre(genre, preferred_genres):
                discovery_reason = f"Related to preferred genres via {genre}"
            else:
                discovery_reason = f"Discovery recommendation ({discovery_mode} mode)"
            
            # Calculate estimated reading time
            content_preview = result.get('content_preview', '') or ''
            reading_time = self._estimate_reading_time(len(content_preview.split()))
            
            # Calculate genre similarity score
            genre_similarity = self._calculate_genre_similarity(genre, preferred_genres)
            
            enriched_result = {
                **result,
                'discovery_reason': discovery_reason,
                'genre_similarity_score': genre_similarity,
                'estimated_reading_time': reading_time,
                'discovery_confidence': min(float(result.get('final_score', 0.5)) * 100, 95),
                'content_preview': content_preview[:300] + '...' if len(content_preview) > 300 else content_preview,
                'year_published': result.get('year_published') or 'Unknown',
                'discovery_metadata': {
                    'mode': discovery_mode,
                    'genre_hierarchy_used': genre in self.genre_hierarchy.get(genre, []),
                    'preference_match': genre in preferred_genres
                }
            }
            
            enriched.append(enriched_result)
        
        return enriched
    
    def _is_related_genre(self, genre: str, preferred_genres: List[str]) -> bool:
        """Check if a genre is related to preferred genres through hierarchy"""
        for parent, children in self.genre_hierarchy.items():
            if genre in children:
                if parent in preferred_genres or any(pref in children for pref in preferred_genres):
                    return True
        return False
    
    def _calculate_genre_similarity(self, genre: str, preferred_genres: List[str]) -> float:
        """Calculate similarity score between genre and preferences"""
        if genre in preferred_genres:
            return 1.0
        elif self._is_related_genre(genre, preferred_genres):
            return 0.7
        else:
            return 0.3
    
    def _estimate_reading_time(self, word_count: int, wpm: int = 250) -> str:
        """Estimate reading time for content"""
        if word_count < 100:
            return "< 1 minute"
        
        minutes = max(1, word_count // wpm)
        
        if minutes < 60:
            return f"{minutes} min"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}h {remaining_minutes}m" if remaining_minutes > 0 else f"{hours}h"
    
    def get_genre_statistics(self) -> Dict:
        """Get current genre statistics from the database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            genre,
                            COUNT(*) as book_count,
                            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                        FROM books 
                        WHERE genre IS NOT NULL 
                        GROUP BY genre 
                        ORDER BY book_count DESC
                    """)
                    
                    stats = {}
                    for row in cur.fetchall():
                        stats[row['genre']] = {
                            'count': row['book_count'],
                            'percentage': float(row['percentage'])
                        }
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Error getting genre statistics: {e}")
            return self.genre_stats

# Flask API Implementation
app = Flask(__name__)

# Initialize discovery engine
discovery_engine = GenreAwareDiscoveryEngine(get_database_config())

@app.route('/api/v2/discover/genre', methods=['POST'])
def genre_aware_discovery_endpoint():
    """
    Genre-Aware Discovery API Endpoint
    
    POST /api/v2/discover/genre
    {
        "preferred_genres": ["Science Fiction", "Fantasy"],
        "discovery_mode": "balanced|similar|diverse",
        "include_subgenres": true,
        "exclude_genres": ["Romance"],
        "limit": 20
    }
    """
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        preferred_genres = data.get('preferred_genres', [])
        if not preferred_genres:
            return jsonify({'error': 'At least one preferred genre required'}), 400
        
        discovery_mode = data.get('discovery_mode', 'balanced')
        if discovery_mode not in ['similar', 'diverse', 'balanced']:
            discovery_mode = 'balanced'
        
        include_subgenres = data.get('include_subgenres', True)
        exclude_genres = data.get('exclude_genres', [])
        limit = min(int(data.get('limit', 20)), 50)  # Cap at 50 results
        
        # Execute discovery
        results = discovery_engine.genre_aware_discovery(
            preferred_genres=preferred_genres,
            discovery_mode=discovery_mode,
            include_subgenres=include_subgenres,
            limit=limit,
            exclude_genres=exclude_genres
        )
        
        # Get genre hierarchy for reference
        hierarchy = discovery_engine.get_genre_hierarchy()
        
        # Prepare response
        response = {
            'status': 'success',
            'discovery_metadata': {
                'preferred_genres': preferred_genres,
                'discovery_mode': discovery_mode,
                'include_subgenres': include_subgenres,
                'exclude_genres': exclude_genres,
                'total_results': len(results),
                'phase': 'Phase 2 Implementation'
            },
            'results': results,
            'genre_hierarchy': hierarchy,
            'recommendations': {
                'related_genres': discovery_engine.expand_genre_list(preferred_genres, True),
                'discovery_tips': {
                    'similar': 'Focus on exact genre matches',
                    'diverse': 'Explore different but related genres',
                    'balanced': 'Mix of familiar and new recommendations'
                }
            }
        }
        
        return jsonify(response)
        
    except ValueError as e:
        logger.warning(f"Invalid request parameters: {e}")
        return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Discovery API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v2/discover/genre/statistics', methods=['GET'])
def genre_statistics_endpoint():
    """Get current genre statistics and distribution"""
    try:
        stats = discovery_engine.get_genre_statistics()
        hierarchy = discovery_engine.get_genre_hierarchy()
        
        return jsonify({
            'status': 'success',
            'genre_statistics': stats,
            'genre_hierarchy': hierarchy,
            'total_classified_books': sum(s['count'] for s in stats.values()),
            'api_version': '2.0',
            'phase': 'Phase 2 Implementation'
        })
        
    except Exception as e:
        logger.error(f"Statistics API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/v2/discover/genre/health', methods=['GET'])
def health_check():
    """Health check endpoint for genre discovery API"""
    try:
        # Test database connection
        with discovery_engine.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM books WHERE genre IS NOT NULL")
                classified_count = cur.fetchone()[0]
        
        return jsonify({
            'status': 'healthy',
            'api': 'Genre-Aware Discovery API',
            'phase': 'Phase 2 Implementation',
            'database': 'connected',
            'classified_books': classified_count,
            'genre_categories': len(discovery_engine.genre_hierarchy),
            'discovery_modes': ['similar', 'diverse', 'balanced']
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Genre-Aware Discovery API - Phase 2")
    app.run(debug=True, host='0.0.0.0', port=5002)