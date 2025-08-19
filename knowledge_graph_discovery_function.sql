CREATE OR REPLACE FUNCTION api_knowledge_graph_discovery(
    p_theme TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    IF p_theme IS NOT NULL THEN
        -- Theme-based discovery
        EXECUTE format('
            SELECT json_build_object(
                ''success'', true,
                ''data'', json_build_object(
                    ''search_type'', ''knowledge_graph_theme_discovery'',
                    ''theme'', %L,
                    ''results'', json_agg(
                        json_build_object(
                            ''book_id'', b.book_id,
                            ''title'', b.title,
                            ''author'', b.author,
                            ''semantic_theme'', bsc.theme_label,
                            ''cluster_id'', bsc.cluster_id,
                            ''original_genre'', COALESCE(b.genre, ''Unclassified''),
                            ''word_count'', COALESCE(
                                (SELECT word_count FROM chunks WHERE book_id = b.book_id AND chunk_type = ''fullbook'' LIMIT 1), 
                                0
                            )
                        ) ORDER BY b.title
                    ),
                    ''total_results'', COUNT(*),
                    ''related_themes'', (
                        SELECT array_agg(DISTINCT other_theme.theme_label)
                        FROM book_semantic_clusters other_theme
                        WHERE other_theme.cluster_id IN (
                            SELECT cluster_id FROM book_semantic_clusters 
                            WHERE theme_label = %L 
                            LIMIT 3
                        )
                        AND other_theme.theme_label != %L
                    )
                )
            )
            FROM book_semantic_clusters bsc
            JOIN books b ON bsc.book_id = b.book_id
            WHERE bsc.theme_label = %L
            LIMIT %s',
            p_theme, p_theme, p_theme, p_theme, p_limit
        ) INTO v_result;
    ELSE
        -- Overview of all themes
        SELECT json_build_object(
            'success', true,
            'data', json_build_object(
                'search_type', 'knowledge_graph_overview',
                'theme_distribution', json_agg(
                    json_build_object(
                        'theme_label', theme_label,
                        'book_count', book_count,
                        'percentage', ROUND((book_count::numeric / total_books * 100), 1)
                    ) ORDER BY book_count DESC
                ),
                'total_themes', COUNT(*),
                'total_books', MAX(total_books)
            )
        ) INTO v_result
        FROM (
            SELECT 
                theme_label,
                COUNT(*) as book_count,
                SUM(COUNT(*)) OVER () as total_books
            FROM book_semantic_clusters
            GROUP BY theme_label
        ) theme_stats;
    END IF;

    RETURN v_result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Knowledge graph discovery failed',
            'details', SQLERRM
        );
END;
$$;