"""
Search Module - PostgreSQL-First Architecture
Dr. Sarah Chen (陈雪芳) Design with Extended Semantic Search
"""

import logging
from flask import Blueprint, request, jsonify
from .auth import require_auth
from .database import execute_pg_function, get_db

logger = logging.getLogger(__name__)
search_bp = Blueprint('search', __name__)


@search_bp.route('/api/v4/search')
@require_auth
def v4_search():
    """V4 Multi-type search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        term = request.args.get('term', '').strip()
        search_term = query or term
        search_type = request.args.get('type', 'content')
        action = request.args.get('action', 'search')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term required',
                'usage': '/api/v4/search?q=your_search_term'
            }), 400
            
        # Route based on action
        if action == 'count':
            count = execute_pg_function('api_shortcuts_search_count', search_term)
            return jsonify({'success': True, 'count': count})
            
        elif action == 'has_results':
            has_results = execute_pg_function('api_shortcuts_search_has_results', search_term)
            return jsonify({'success': True, 'has_results': has_results})
            
        elif action == 'titles':
            titles = execute_pg_function('api_shortcuts_search_titles', search_term, limit)
            return jsonify({'success': True, 'titles': titles})
            
        else:  # Default search
            result = execute_pg_function('api_shortcuts_search_simple', search_term, limit)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"V4 Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/v4/search/semantic')
@require_auth
def semantic_search():
    """Extended semantic search for compound queries (10-word capability)"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 50)), 100)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query required',
                'usage': '/api/v4/search/semantic?q=artificial intelligence machine learning'
            }), 400
            
        # Determine search type based on query length
        word_count = len(query.split())
        
        if word_count <= 5:
            # Use optimized 3-5 word semantic search
            result = execute_pg_function('api_semantic_phrase_search_optimized', query, limit)
        else:
            # Use extended 10-word semantic search
            result = execute_pg_function('api_extended_semantic_search', query, limit)
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/v4/search/advanced')
@require_auth
def advanced_search():
    """Advanced search with multiple filters"""
    try:
        query = request.args.get('q', '').strip()
        author = request.args.get('author', '').strip()
        genre = request.args.get('genre', '').strip()
        year_min = request.args.get('year_min', type=int)
        year_max = request.args.get('year_max', type=int)
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Build dynamic search using PostgreSQL functions
        with get_db() as conn:
            with conn.cursor() as cur:
                where_conditions = []
                params = []
                
                if query:
                    where_conditions.append("(c.search_vector @@ plainto_tsquery('english', %s) OR LOWER(b.title) LIKE LOWER(%s) OR LOWER(b.author) LIKE LOWER(%s))")
                    params.extend([query, f'%{query}%', f'%{query}%'])
                    
                if author:
                    where_conditions.append("LOWER(b.author) LIKE LOWER(%s)")
                    params.append(f'%{author}%')
                    
                if genre:
                    where_conditions.append("LOWER(b.genre) LIKE LOWER(%s)")
                    params.append(f'%{genre}%')
                    
                if year_min:
                    where_conditions.append("b.publication_year >= %s")
                    params.append(year_min)
                    
                if year_max:
                    where_conditions.append("b.publication_year <= %s")
                    params.append(year_max)
                    
                if not where_conditions:
                    return jsonify({
                        'success': False,
                        'error': 'At least one search parameter required'
                    }), 400
                    
                params.append(limit)
                
                cur.execute(f"""
                    SELECT json_build_object(
                        'success', true,
                        'data', json_build_object(
                            'results', json_agg(DISTINCT
                                json_build_object(
                                    'book_id', b.book_id,
                                    'title', b.title,
                                    'author', b.author,
                                    'genre', b.genre,
                                    'publication_year', b.publication_year,
                                    'word_count', b.word_count,
                                    'relevance_score', CASE 
                                        WHEN %s != '' THEN ts_rank(c.search_vector, plainto_tsquery('english', %s))
                                        ELSE 1.0 
                                    END
                                ) ORDER BY CASE 
                                    WHEN %s != '' THEN ts_rank(c.search_vector, plainto_tsquery('english', %s))
                                    ELSE 1.0 
                                END DESC
                            ),
                            'total_results', COUNT(DISTINCT b.book_id),
                            'filters_applied', json_build_object(
                                'query', %s,
                                'author', %s,
                                'genre', %s,
                                'year_min', %s,
                                'year_max', %s
                            )
                        )
                    )
                    FROM books b
                    LEFT JOIN chunks c ON b.book_id = c.book_id
                    WHERE {' AND '.join(where_conditions)}
                    GROUP BY b.book_id, b.title, b.author, b.genre, b.publication_year, b.word_count
                    LIMIT %s
                """, [query, query, query, query, query, author, genre, year_min, year_max] + params)
                
                result = cur.fetchone()[0]
                return jsonify(result)
                
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/shortcuts/search')
@require_auth
def shortcuts_search():
    """iOS Shortcuts optimized search"""
    try:
        term = request.args.get('term', '').strip()
        action = request.args.get('action', 'simple')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not term:
            return jsonify({
                'success': False,
                'error': 'Search term required',
                'usage': '/api/shortcuts/search?term=philosophy&action=simple'
            }), 400
            
        if action == 'count':
            count = execute_pg_function('api_shortcuts_search_count', term)
            return jsonify(count)  # Return simple integer for iOS Shortcuts
            
        elif action == 'has_results':
            has_results = execute_pg_function('api_shortcuts_search_has_results', term)
            return jsonify(has_results)  # Return simple boolean
            
        elif action == 'titles':
            titles = execute_pg_function('api_shortcuts_search_titles', term, limit)
            return jsonify(titles)  # Return simple array
            
        else:  # simple search
            result = execute_pg_function('api_shortcuts_search_simple', term, limit)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"Shortcuts search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500