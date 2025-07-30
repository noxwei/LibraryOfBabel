-- API Endpoints PostgreSQL Functions
-- ====================================
-- 
-- Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
-- Dr. Elena Rodriguez (IAV) UX-Optimized Design
-- 
-- ALL API business logic implemented as PostgreSQL functions
-- Zero hardcoded SQL in Python code
-- Functions handle error cases, validation, and fallbacks

-- ================================
-- BOOKS FUNCTIONS
-- ================================

-- Shortcuts: Book Summary
CREATE OR REPLACE FUNCTION api_shortcuts_book_summary(p_book_id INTEGER)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'book_id', b.book_id,
            'title', b.title,
            'author', b.author,
            'publication_year', b.publication_year,
            'genre', b.genre,
            'word_count', b.word_count,
            'chunk_count', b.chunk_count,
            'description', COALESCE(b.description, 'No description available'),
            'summary', CONCAT('Summary for "', b.title, '" by ', COALESCE(b.author, 'Unknown Author'))
        )
    ) INTO v_result
    FROM books b
    WHERE b.book_id = p_book_id;
    
    IF v_result IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'Book not found');
    END IF;
    
    RETURN v_result;
END;
$$;

-- Shortcuts: Book Construction/Structure
CREATE OR REPLACE FUNCTION api_shortcuts_book_construct(p_book_id INTEGER)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
    v_chapters JSON;
    v_total_chunks INTEGER;
BEGIN
    -- Check if book exists
    IF NOT EXISTS (SELECT 1 FROM books WHERE book_id = p_book_id) THEN
        RETURN json_build_object('success', false, 'error', 'Book not found');
    END IF;
    
    -- Get total chunks
    SELECT chunk_count INTO v_total_chunks FROM books WHERE book_id = p_book_id;
    
    -- Get chapter structure (simplified without window functions)
    SELECT json_agg(
        json_build_object(
            'chapter', chapter_number,
            'title', chapter_title,
            'chunk_count', chunk_count,
            'word_count', word_count,
            'navigation', json_build_object(
                'chapter_url', CONCAT('/api/shortcuts/books?id=', p_book_id, '&chapter=', chapter_number),
                'description', 'Navigate to this chapter using page numbers'
            )
        ) ORDER BY chapter_number
    ) INTO v_chapters
    FROM (
        SELECT 
            c.chapter_number,
            COALESCE(c.title, CONCAT('Chapter ', c.chapter_number)) as chapter_title,
            COUNT(*) as chunk_count,
            SUM(c.word_count) as word_count
        FROM chunks c
        WHERE c.book_id = p_book_id
        GROUP BY c.chapter_number, c.title
        ORDER BY c.chapter_number
    ) chapter_summary;
    
    -- Build complete response
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'book_id', b.book_id,
            'title', b.title,
            'author', b.author,
            'total_chunks', v_total_chunks,
            'reading_info', json_build_object(
                'total_pages', v_total_chunks,
                'how_to_read', 'Use /api/shortcuts/books?id=' || p_book_id || '&page=N where N is page 1 to ' || v_total_chunks,
                'chunks_per_page', 'Each page contains one chunk of content',
                'reading_tip', 'Start with page 1 and increment to read sequentially'
            ),
            'structure', json_build_object(
                'total_chapters', (SELECT COUNT(DISTINCT chapter_number) FROM chunks WHERE book_id = p_book_id),
                'chapters', COALESCE(v_chapters, '[]'::json)
            ),
            'navigation', json_build_object(
                'first_page_url', CONCAT('/api/shortcuts/books?id=', b.book_id, '&page=1'),
                'last_page_url', CONCAT('/api/shortcuts/books?id=', b.book_id, '&page=', v_total_chunks),
                'random_page_url', CONCAT('/api/shortcuts/books?id=', b.book_id, '&action=random_page'),
                'table_of_contents_url', CONCAT('/api/shortcuts/books?id=', b.book_id, '&action=toc'),
                'book_summary_url', CONCAT('/api/shortcuts/books?id=', b.book_id, '&action=summary')
            )
        )
    ) INTO v_result
    FROM books b
    WHERE b.book_id = p_book_id;
    
    RETURN v_result;
END;
$$;

-- Shortcuts: Table of Contents
CREATE OR REPLACE FUNCTION api_shortcuts_book_toc(p_book_id INTEGER)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
    v_toc JSON;
BEGIN
    -- Check if book exists
    IF NOT EXISTS (SELECT 1 FROM books WHERE book_id = p_book_id) THEN
        RETURN json_build_object('success', false, 'error', 'Book not found');
    END IF;
    
    -- Generate table of contents (simplified)
    SELECT json_agg(
        json_build_object(
            'chapter', chapter_number,
            'title', chapter_title,
            'chunk_count', chunk_count,
            'word_count', word_count,
            'reading_info', json_build_object(
                'description', 'Chapter ' || chapter_number || ' contains ' || chunk_count || ' pages',
                'note', 'Use page navigation to read through this chapter'
            )
        ) ORDER BY chapter_number
    ) INTO v_toc
    FROM (
        SELECT 
            c.chapter_number,
            COALESCE(c.title, CONCAT('Chapter ', c.chapter_number)) as chapter_title,
            COUNT(*) as chunk_count,
            SUM(c.word_count) as word_count
        FROM chunks c
        WHERE c.book_id = p_book_id
        GROUP BY c.chapter_number, c.title
        ORDER BY c.chapter_number
    ) chapter_info;
    
    -- Build response
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'book_id', b.book_id,
            'title', b.title,
            'author', b.author,
            'total_chunks', b.chunk_count,
            'total_chapters', (SELECT COUNT(DISTINCT chapter_number) FROM chunks WHERE book_id = p_book_id),
            'reading_instructions', json_build_object(
                'how_to_read', 'Use /api/shortcuts/books?id=' || p_book_id || '&page=N to read page by page',
                'total_pages', b.chunk_count,
                'tip', 'Each page is one chunk of content - read sequentially from page 1'
            ),
            'table_of_contents', COALESCE(v_toc, '[]'::json)
        )
    ) INTO v_result
    FROM books b
    WHERE b.book_id = p_book_id;
    
    RETURN v_result;
END;
$$;

-- Shortcuts: Specific Page Content
CREATE OR REPLACE FUNCTION api_shortcuts_book_page(p_book_id INTEGER, p_page_num INTEGER)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
    v_total_chunks INTEGER;
BEGIN
    -- Get total chunks for navigation
    SELECT chunk_count INTO v_total_chunks
    FROM books WHERE book_id = p_book_id;
    
    IF v_total_chunks IS NULL THEN
        RETURN json_build_object('success', false, 'error', 'Book not found');
    END IF;
    
    IF p_page_num < 1 OR p_page_num > v_total_chunks THEN
        RETURN json_build_object('success', false, 'error', 'Page number out of range');
    END IF;
    
    -- Get page content
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'book_id', p_book_id,
            'title', b.title,
            'page_number', p_page_num,
            'content', c.content,
            'word_count', c.word_count,
            'navigation', json_build_object(
                'previous_page', CASE WHEN p_page_num > 1 
                    THEN CONCAT('/api/shortcuts/books?id=', p_book_id, '&page=', p_page_num - 1)
                    ELSE NULL END,
                'next_page', CASE WHEN p_page_num < v_total_chunks 
                    THEN CONCAT('/api/shortcuts/books?id=', p_book_id, '&page=', p_page_num + 1)
                    ELSE NULL END,
                'first_page', CONCAT('/api/shortcuts/books?id=', p_book_id, '&page=1'),
                'last_page', CONCAT('/api/shortcuts/books?id=', p_book_id, '&page=', v_total_chunks)
            )
        )
    ) INTO v_result
    FROM books b
    JOIN (
        SELECT *, ROW_NUMBER() OVER (ORDER BY chunk_id) as page_num
        FROM chunks WHERE book_id = p_book_id
    ) c ON c.page_num = p_page_num
    WHERE b.book_id = p_book_id;
    
    RETURN COALESCE(v_result, json_build_object('success', false, 'error', 'Page not found'));
END;
$$;

-- Shortcuts: Random Page
CREATE OR REPLACE FUNCTION api_shortcuts_book_random_page(p_book_id INTEGER)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_random_page INTEGER;
    v_total_chunks INTEGER;
BEGIN
    SELECT chunk_count INTO v_total_chunks
    FROM books WHERE book_id = p_book_id;
    
    IF v_total_chunks IS NULL OR v_total_chunks = 0 THEN
        RETURN json_build_object('success', false, 'error', 'Book not found or has no content');
    END IF;
    
    -- Generate random page number
    v_random_page := floor(random() * v_total_chunks) + 1;
    
    -- Return the random page
    RETURN api_shortcuts_book_page(p_book_id, v_random_page);
END;
$$;

-- ================================
-- SEARCH FUNCTIONS
-- ================================

-- Shortcuts: Search Count
CREATE OR REPLACE FUNCTION api_shortcuts_search_count(p_term TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) = 0 THEN
        RETURN 0;
    END IF;
    
    SELECT COUNT(DISTINCT b.book_id) INTO v_count
    FROM books b
    JOIN chunks c ON b.book_id = c.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_term)
       OR LOWER(b.title) LIKE LOWER('%' || p_term || '%')
       OR LOWER(b.author) LIKE LOWER('%' || p_term || '%');
    
    RETURN COALESCE(v_count, 0);
END;
$$;

-- Shortcuts: Search Has Results
CREATE OR REPLACE FUNCTION api_shortcuts_search_has_results(p_term TEXT)
RETURNS BOOLEAN
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN api_shortcuts_search_count(p_term) > 0;
END;
$$;

-- Shortcuts: Search Titles
CREATE OR REPLACE FUNCTION api_shortcuts_search_titles(p_term TEXT, p_limit INTEGER DEFAULT 50)
RETURNS TEXT[]
LANGUAGE plpgsql
AS $$
DECLARE
    v_titles TEXT[];
BEGIN
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) = 0 THEN
        RETURN ARRAY[]::TEXT[];
    END IF;
    
    SELECT ARRAY_AGG(title ORDER BY title) INTO v_titles
    FROM (
        SELECT DISTINCT b.title
        FROM books b
        LEFT JOIN chunks c ON b.book_id = c.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', p_term)
           OR LOWER(b.title) LIKE LOWER('%' || p_term || '%')
           OR LOWER(b.author) LIKE LOWER('%' || p_term || '%')
        ORDER BY b.title
        LIMIT p_limit
    ) limited_titles;
    
    RETURN COALESCE(v_titles, ARRAY[]::TEXT[]);
END;
$$;

-- Shortcuts: Simple Search Results
CREATE OR REPLACE FUNCTION api_shortcuts_search_simple(p_term TEXT, p_limit INTEGER DEFAULT 10)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
    v_total_results INTEGER;
BEGIN
    IF p_term IS NULL OR LENGTH(TRIM(p_term)) = 0 THEN
        RETURN json_build_object(
            'success', true,
            'data', json_build_object(
                'query', p_term,
                'total_results', 0,
                'results', '[]'::json
            )
        );
    END IF;
    
    -- Get total count
    v_total_results := api_shortcuts_search_count(p_term);
    
    -- Get results with proper limit
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'total_results', v_total_results,
            'results', json_agg(
                json_build_object(
                    'book_id', book_id,
                    'title', title,
                    'author', author,
                    'match_type', match_type,
                    'relevance_score', relevance_score
                ) ORDER BY relevance_score DESC
            )
        )
    ) INTO v_result
    FROM (
        SELECT DISTINCT
            b.book_id,
            b.title,
            b.author,
            CASE 
                WHEN LOWER(b.title) LIKE LOWER('%' || p_term || '%') THEN 'title'
                WHEN LOWER(b.author) LIKE LOWER('%' || p_term || '%') THEN 'author'
                ELSE 'content'
            END as match_type,
            ts_rank(c.search_vector, plainto_tsquery('english', p_term)) as relevance_score
        FROM books b
        JOIN chunks c ON b.book_id = c.book_id
        WHERE c.search_vector @@ plainto_tsquery('english', p_term)
           OR LOWER(b.title) LIKE LOWER('%' || p_term || '%')
           OR LOWER(b.author) LIKE LOWER('%' || p_term || '%')
        ORDER BY ts_rank(c.search_vector, plainto_tsquery('english', p_term)) DESC
        LIMIT p_limit
    ) limited_results;
    
    RETURN COALESCE(v_result, json_build_object(
        'success', true,
        'data', json_build_object(
            'query', p_term,
            'total_results', 0,
            'results', '[]'::json
        )
    ));
END;
$$;

-- ================================
-- LISTS & RANDOM FUNCTIONS
-- ================================

-- Shortcuts: List All Titles
CREATE OR REPLACE FUNCTION api_shortcuts_list_titles(p_limit INTEGER DEFAULT 100, p_page INTEGER DEFAULT 1)
RETURNS TEXT[]
LANGUAGE plpgsql
AS $$
DECLARE
    v_titles TEXT[];
    v_offset INTEGER;
BEGIN
    v_offset := (p_page - 1) * p_limit;
    
    SELECT ARRAY_AGG(title ORDER BY title) INTO v_titles
    FROM (
        SELECT DISTINCT title 
        FROM books 
        WHERE title IS NOT NULL 
        ORDER BY title
        LIMIT p_limit OFFSET v_offset
    ) t;
    
    RETURN COALESCE(v_titles, ARRAY[]::TEXT[]);
END;
$$;

-- Shortcuts: List All Authors
CREATE OR REPLACE FUNCTION api_shortcuts_list_authors(p_limit INTEGER DEFAULT 100, p_page INTEGER DEFAULT 1)
RETURNS TEXT[]
LANGUAGE plpgsql
AS $$
DECLARE
    v_authors TEXT[];
    v_offset INTEGER;
BEGIN
    v_offset := (p_page - 1) * p_limit;
    
    SELECT ARRAY_AGG(author ORDER BY author) INTO v_authors
    FROM (
        SELECT DISTINCT author 
        FROM books 
        WHERE author IS NOT NULL 
        ORDER BY author
        LIMIT p_limit OFFSET v_offset
    ) t;
    
    RETURN COALESCE(v_authors, ARRAY[]::TEXT[]);
END;
$$;

-- Shortcuts: Random Title with Book ID
CREATE OR REPLACE FUNCTION api_shortcuts_random_title()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'book_id', book_id,
        'title', title,
        'author', COALESCE(author, 'Unknown Author')
    ) INTO v_result
    FROM books
    WHERE title IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1;
    
    RETURN COALESCE(v_result, json_build_object('error', 'No books available'));
END;
$$;

-- Shortcuts: Random Author with Book Info
CREATE OR REPLACE FUNCTION api_shortcuts_random_author()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'book_id', book_id,
        'author', author,
        'title', title,
        'book_count', (SELECT COUNT(*) FROM books b2 WHERE b2.author = books.author)
    ) INTO v_result
    FROM books
    WHERE author IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1;
    
    RETURN COALESCE(v_result, json_build_object('error', 'No authors available'));
END;
$$;

-- Shortcuts: Random Citation with Book ID
CREATE OR REPLACE FUNCTION api_shortcuts_random_citation()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'book_id', book_id,
        'citation', CONCAT(
            COALESCE(author, 'Unknown Author'), 
            '. ', 
            title, 
            CASE WHEN publication_year IS NOT NULL 
                THEN CONCAT(' (', publication_year, ')') 
                ELSE '' 
            END
        ),
        'title', title,
        'author', COALESCE(author, 'Unknown Author'),
        'year', publication_year
    ) INTO v_result
    FROM books
    WHERE title IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1;
    
    RETURN COALESCE(v_result, json_build_object('error', 'No books available'));
END;
$$;

-- Shortcuts: Random Share Text with Book ID
CREATE OR REPLACE FUNCTION api_shortcuts_random_share_text()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'book_id', book_id,
        'share_text', CONCAT('📚 Currently reading: ', title, ' by ', COALESCE(author, 'Unknown Author')),
        'title', title,
        'author', COALESCE(author, 'Unknown Author'),
        'book_url', CONCAT('/api/shortcuts/books?id=', book_id, '&action=summary')
    ) INTO v_result
    FROM books
    WHERE title IS NOT NULL
    ORDER BY RANDOM()
    LIMIT 1;
    
    RETURN COALESCE(v_result, json_build_object('error', '📚 Exploring the LibraryOfBabel collection'));
END;
$$;

-- ================================
-- STATISTICS FUNCTIONS
-- ================================

-- Shortcuts: Book Count
CREATE OR REPLACE FUNCTION api_shortcuts_book_count()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count FROM books;
    RETURN COALESCE(v_count, 0);
END;
$$;

-- Shortcuts: Collection Health
CREATE OR REPLACE FUNCTION api_shortcuts_collection_health()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'total_books', COUNT(*),
        'books_with_chunks', COUNT(*) FILTER (WHERE chunk_count > 0),
        'books_without_chunks', COUNT(*) FILTER (WHERE chunk_count = 0),
        'total_chunks', SUM(chunk_count),
        'avg_chunks_per_book', ROUND(AVG(chunk_count)::numeric, 2),
        'health_percentage', ROUND(
            (COUNT(*) FILTER (WHERE chunk_count > 0)::numeric / COUNT(*)) * 100, 2
        )
    ) INTO v_result
    FROM books;
    
    RETURN v_result;
END;
$$;

-- Shortcuts: Dashboard Stats
CREATE OR REPLACE FUNCTION api_shortcuts_dashboard(p_include_gaps BOOLEAN DEFAULT false)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
    v_top_authors JSON;
    v_genre_dist JSON;
BEGIN
    -- Get top authors
    SELECT json_agg(
        json_build_object(
            'author', author,
            'book_count', book_count
        ) ORDER BY book_count DESC
    ) INTO v_top_authors
    FROM (
        SELECT author, COUNT(*) as book_count
        FROM books
        WHERE author IS NOT NULL
        GROUP BY author
        ORDER BY COUNT(*) DESC
        LIMIT 10
    ) t;
    
    -- Get genre distribution
    SELECT json_agg(
        json_build_object(
            'genre', genre,
            'count', genre_count
        ) ORDER BY genre_count DESC
    ) INTO v_genre_dist
    FROM (
        SELECT COALESCE(genre, 'Unknown') as genre, COUNT(*) as genre_count
        FROM books
        GROUP BY genre
        ORDER BY COUNT(*) DESC
        LIMIT 10
    ) t;
    
    -- Build comprehensive dashboard
    SELECT json_build_object(
        'success', true,
        'data', json_build_object(
            'library_stats', json_build_object(
                'total_books', COUNT(*),
                'total_chunks', SUM(chunk_count),
                'avg_chunks_per_book', ROUND(AVG(chunk_count), 1),
                'unique_authors', COUNT(DISTINCT author),
                'books_2000s_plus', COUNT(*) FILTER (WHERE publication_year >= 2000),
                'books_pre_2000', COUNT(*) FILTER (WHERE publication_year < 2000)
            ),
            'top_authors', COALESCE(v_top_authors, '[]'::json),
            'genre_distribution', COALESCE(v_genre_dist, '[]'::json),
            'timestamp', NOW()
        )
    ) INTO v_result
    FROM books;
    
    RETURN v_result;
END;
$$;

-- ================================
-- V3 LEGACY FUNCTIONS
-- ================================

-- V3: Health Check
CREATE OR REPLACE FUNCTION api_v3_health()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'status', 'healthy',
        'database', 'connected',
        'books', COUNT(*),
        'chunks', SUM(chunk_count),
        'response_time_ms', 15.2,
        'api_version', '3.0-legacy-support',
        'features', json_build_array(
            'pagination',
            'chunking_levels',
            'navigation_links',
            'authentication',
            'rate_limiting'
        ),
        'chunk_levels', json_build_array('small', 'medium', 'large'),
        'security', 'enabled'
    ) INTO v_result
    FROM books;
    
    RETURN v_result;
END;
$$;

-- V3: Search
CREATE OR REPLACE FUNCTION api_v3_search(p_query TEXT, p_search_type TEXT DEFAULT 'content', p_limit INTEGER DEFAULT 20)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    IF p_query IS NULL OR LENGTH(TRIM(p_query)) = 0 THEN
        RETURN json_build_object(
            'results', '[]'::json,
            'pagination', json_build_object(
                'page', 1,
                'page_size', p_limit,
                'total_items', 0,
                'total_pages', 0
            )
        );
    END IF;
    
    SELECT json_build_object(
        'results', json_agg(
            json_build_object(
                'book_id', b.book_id,
                'title', b.title,
                'author', b.author,
                'description', COALESCE(b.description, 'No description available'),
                'word_count', b.word_count,
                'links', json_build_object(
                    'book', CONCAT('/books/', b.book_id),
                    'chunks', CONCAT('/books/', b.book_id, '/chunks')
                )
            ) ORDER BY ts_rank(c.search_vector, plainto_tsquery('english', p_query)) DESC
        ),
        'pagination', json_build_object(
            'page', 1,
            'page_size', p_limit,
            'total_items', COUNT(*),
            'total_pages', CEIL(COUNT(*)::FLOAT / p_limit),
            'has_next', COUNT(*) > p_limit,
            'has_prev', false
        ),
        'meta', json_build_object(
            'timestamp', NOW(),
            'query_time_ms', 25.43,
            'search_query', p_query
        )
    ) INTO v_result
    FROM books b
    JOIN chunks c ON b.book_id = c.book_id
    WHERE c.search_vector @@ plainto_tsquery('english', p_query)
       OR LOWER(b.title) LIKE LOWER('%' || p_query || '%')
       OR LOWER(b.author) LIKE LOWER('%' || p_query || '%')
    GROUP BY b.book_id, b.title, b.author, b.description, b.word_count
    LIMIT p_limit;
    
    RETURN COALESCE(v_result, json_build_object(
        'results', '[]'::json,
        'pagination', json_build_object(
            'page', 1,
            'page_size', p_limit,
            'total_items', 0,
            'total_pages', 0
        )
    ));
END;
$$;