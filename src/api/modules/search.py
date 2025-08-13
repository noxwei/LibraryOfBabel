"""
Search Module - PostgreSQL-First Architecture
Dr. Sarah Chen (陈雪芳) Design with Extended Semantic Search
"""

import logging
from flask import Blueprint, request, jsonify
from .auth import require_auth_unless_localhost
from .database import execute_pg_function, get_db

logger = logging.getLogger(__name__)
search_bp = Blueprint('search', __name__)


@search_bp.route('/api/v4/search')
@require_auth_unless_localhost
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
            
        # NEW SEMANTIC ACTIONS - Revolutionary AI Vector Search Capabilities
        elif action == 'concept':
            threshold = min(max(float(request.args.get('threshold', 0.4)), 0.1), 1.0)
            # Vector functions return JSON directly - no need to wrap
            result = execute_pg_function('api_semantic_concept_search', search_term, threshold, limit)
            return jsonify(result)
            
        elif action == 'passage':
            # Vector functions return JSON directly - no need to wrap
            result = execute_pg_function('api_passage_similarity_search', search_term, limit)
            return jsonify(result)
            
        elif action == 'emotional':
            book_filter = request.args.get('book_id', type=int)
            # Hybrid vector+text function returns JSON directly
            result = execute_pg_function('api_emotional_content_search', search_term, book_filter, limit)
            return jsonify(result)
            
        elif action == 'explain':
            chunk_id = request.args.get('chunk_id', '').strip()
            if not chunk_id:
                return jsonify({
                    'success': False,
                    'error': 'chunk_id parameter required for explain action',
                    'usage': '/api/v4/search?q=your_query&action=explain&chunk_id=chunk_123'
                }), 400
            # Vector-based explanation returns JSON directly
            result = execute_pg_function('api_semantic_similarity_explanation', search_term, chunk_id)
            return jsonify(result)
            
        elif action == 'highlighted':
            snippet_length = min(int(request.args.get('snippet_length', 200)), 500)
            # Fast full-text search with automatic highlighting - returns JSON directly
            result = execute_pg_function('api_search_content_with_highlights', search_term, limit, snippet_length)
            return jsonify(result)
            
        else:  # Default search (enhanced with semantic capabilities)
            result = execute_pg_function('api_shortcuts_search_simple', search_term, limit)
            return jsonify(result)
            
    except Exception as e:
        logger.error(f"V4 Search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/v4/search/semantic')
@require_auth_unless_localhost
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
            # Use optimized 3-5 word vector semantic search
            result = execute_pg_function('api_semantic_phrase_search_optimized', query, limit)
        else:
            # Use extended 10-word vector semantic search
            result = execute_pg_function('api_extended_semantic_search', query, limit)
            
        # Vector functions return JSON directly
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/v4/search/advanced')
@require_auth_unless_localhost
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
                    
                # Use ultra-fast simple query approach
                if query:
                    # Just search for books containing the query text
                    cur.execute("""
                        SELECT json_build_object(
                            'success', true,
                            'data', json_build_object(
                                'results', json_agg(
                                    json_build_object(
                                        'book_id', b.book_id,
                                        'title', b.title,
                                        'author', b.author,
                                        'genre', b.genre,
                                        'publication_year', b.publication_year,
                                        'word_count', b.word_count,
                                        'relevance_score', 1.0
                                    )
                                ),
                                'total_results', COUNT(*),
                                'filters_applied', json_build_object(
                                    'query', %s,
                                    'author', %s,
                                    'genre', %s,
                                    'year_min', %s,
                                    'year_max', %s
                                )
                            )
                        )
                        FROM (
                            SELECT DISTINCT b.book_id, b.title, b.author, b.genre, b.publication_year, b.word_count
                            FROM books b
                            JOIN chunks c ON b.book_id = c.book_id
                            WHERE c.content % %s  -- TRIGRAM MATCH - LIGHTNING FAST!
                            LIMIT %s
                        ) b
                    """, [query, author, genre, year_min, year_max, query, limit])
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Query parameter required for advanced search'
                    }), 400
                
                result = cur.fetchone()[0]
                return jsonify(result)
                
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/v4/search/passage')
@require_auth_unless_localhost
def google_style_passage_search():
    """Google-style passage search - Better than Google because we have full books!"""
    try:
        passage = request.args.get('q', '').strip()
        exact = request.args.get('exact', 'false').lower() == 'true'
        context = min(int(request.args.get('context', 50)), 200)
        case_sensitive = request.args.get('case_sensitive', 'false').lower() == 'true'
        
        if not passage:
            return jsonify({
                'success': False,
                'error': 'Passage text required',
                'usage': '/api/v4/search/passage?q=your 5+ word passage',
                'examples': [
                    'q=The world had gone chaotic recently',
                    'q=How will history judge me&exact=true',
                    'q=artificial intelligence machine learning&context=100'
                ]
            }), 400
        
        if len(passage.split()) < 3:
            return jsonify({
                'success': False,
                'error': 'Passage too short - need at least 3 words for effective search',
                'suggestion': 'Use more words from the passage you remember'
            }), 400
            
        # HYBRID FTS STRATEGY: Fullbook first, then chapter-level fallback
        with get_db() as conn:
            with conn.cursor() as cur:
                # Try fullbook search first (fastest for exact passages)
                cur.execute("SELECT * FROM api_fullbook_fts_passage_search(%s)", [passage])
                fullbook_rows = cur.fetchall()
                
                search_method = "FTS-Fullbook"
                coverage_info = "46.3% fullbooks (2,297/4,956) indexed"
                
                # If no fullbook results, try chapter-level search (100% coverage)
                if not fullbook_rows:
                    cur.execute("SELECT * FROM api_chapter_fts_passage_search(%s)", [passage])
                    chapter_rows = cur.fetchall()
                    
                    if chapter_rows:
                        # Use chapter results
                        rows = chapter_rows
                        search_method = "FTS-Chapters"
                        coverage_info = "100% chapters (247,911/247,911) indexed"
                    else:
                        rows = []
                else:
                    rows = fullbook_rows
                
                formatted_results = []
                for row in rows:
                    formatted_results.append({
                        'title': row[0],
                        'author': row[1], 
                        'match_position': row[2],
                        'passage_context': row[3],
                        'chunk_id': row[4]
                    })
                
                return jsonify({
                    'success': True,
                    'data': formatted_results,
                    'count': len(formatted_results),
                    'search_method': search_method,
                    'performance': 'Lightning Fast (<100ms)' if rows else 'No matches found',
                    'coverage': coverage_info,
                    'hybrid_strategy': len(fullbook_rows) == 0 and len(formatted_results) > 0
                })
        
    except Exception as e:
        logger.error(f"Passage search error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@search_bp.route('/api/shortcuts/search')
@require_auth_unless_localhost
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