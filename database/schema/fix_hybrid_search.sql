-- Fix hybrid search function variable naming conflict
CREATE OR REPLACE FUNCTION hybrid_search(
    search_query_text TEXT,
    exact_weight REAL DEFAULT 0.7,
    fuzzy_weight REAL DEFAULT 0.3,
    result_limit INTEGER DEFAULT 10
) RETURNS TABLE(
    book_id INTEGER,
    title VARCHAR(500),
    author VARCHAR(200),
    combined_score REAL,
    exact_relevance REAL,
    fuzzy_similarity REAL,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH exact_matches AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            ts_rank(b.search_vector, plainto_tsquery('english', search_query_text)) as exact_score,
            'exact' as match_type
        FROM books b
        WHERE b.search_vector @@ plainto_tsquery('english', search_query_text)
    ),
    fuzzy_matches AS (
        SELECT 
            b.book_id,
            b.title,
            b.author,
            GREATEST(
                similarity(b.title, search_query_text),
                similarity(coalesce(b.author, ''), search_query_text)
            ) as fuzzy_score,
            'fuzzy' as match_type
        FROM books b
        WHERE (b.title % search_query_text OR coalesce(b.author, '') % search_query_text)
        AND NOT EXISTS (
            SELECT 1 FROM exact_matches em WHERE em.book_id = b.book_id
        )
    ),
    combined_results AS (
        SELECT 
            em.book_id, em.title, em.author,
            em.exact_score * exact_weight as weighted_exact,
            0.0 as weighted_fuzzy,
            em.exact_score,
            0.0 as fuzzy_score,
            em.match_type
        FROM exact_matches em
        UNION ALL
        SELECT 
            fm.book_id, fm.title, fm.author,
            0.0 as weighted_exact,
            fm.fuzzy_score * fuzzy_weight as weighted_fuzzy,
            0.0 as exact_score,
            fm.fuzzy_score,
            fm.match_type
        FROM fuzzy_matches fm
    )
    SELECT 
        cr.book_id,
        cr.title,
        cr.author,
        (cr.weighted_exact + cr.weighted_fuzzy) as combined_score,
        cr.exact_score,
        cr.fuzzy_score,
        cr.match_type
    FROM combined_results cr
    ORDER BY combined_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;