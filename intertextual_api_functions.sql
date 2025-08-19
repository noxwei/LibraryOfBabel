-- Intertextual Analysis API Functions
-- ====================================
-- PostgreSQL functions to expose intertextual analysis through REST API

-- Function 1: Author Influence Network Analysis
CREATE OR REPLACE FUNCTION api_author_influence_network(
    p_author TEXT DEFAULT NULL,
    p_influence_type TEXT DEFAULT 'stylistic_similarity',
    p_limit INTEGER DEFAULT 20
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    IF p_author IS NOT NULL THEN
        -- Get specific author's influence network
        EXECUTE format('
            SELECT json_build_object(
                ''success'', true,
                ''data'', json_build_object(
                    ''search_type'', ''author_influence_network'',
                    ''target_author'', %L,
                    ''influence_type'', %L,
                    ''direct_influences'', json_agg(
                        json_build_object(
                            ''connected_author'', CASE 
                                WHEN author_source = %L THEN author_target
                                ELSE author_source
                            END,
                            ''influence_score'', influence_score,
                            ''influence_type'', influence_type,
                            ''evidence_books'', evidence_books,
                            ''connection_direction'', CASE 
                                WHEN author_source = %L THEN ''outgoing''
                                ELSE ''incoming''
                            END
                        ) ORDER BY influence_score DESC
                    ),
                    ''total_connections'', COUNT(*),
                    ''avg_influence_score'', ROUND(AVG(influence_score)::numeric, 3)
                )
            )
            FROM author_influence_networks
            WHERE (author_source = %L OR author_target = %L)
            AND influence_type = %L
            LIMIT %s',
            p_author, p_influence_type, p_author, p_author, p_author, p_author, p_influence_type, p_limit
        ) INTO v_result;
    ELSE
        -- Get overview of influence network
        SELECT json_build_object(
            'success', true,
            'data', json_build_object(
                'search_type', 'influence_network_overview',
                'network_statistics', json_build_object(
                    'total_relationships', COUNT(*),
                    'unique_authors', COUNT(DISTINCT author_source) + COUNT(DISTINCT author_target),
                    'avg_influence_score', ROUND(AVG(influence_score)::numeric, 3),
                    'influence_types', array_agg(DISTINCT influence_type)
                ),
                'top_connected_authors', (
                    SELECT json_agg(
                        json_build_object(
                            'author', author,
                            'connection_count', connection_count,
                            'avg_score', avg_score
                        ) ORDER BY connection_count DESC
                    )
                    FROM (
                        SELECT 
                            author,
                            COUNT(*) as connection_count,
                            ROUND(AVG(influence_score)::numeric, 3) as avg_score
                        FROM (
                            SELECT author_source as author, influence_score FROM author_influence_networks
                            UNION ALL
                            SELECT author_target as author, influence_score FROM author_influence_networks
                        ) combined
                        GROUP BY author
                        ORDER BY COUNT(*) DESC
                        LIMIT 10
                    ) top_authors
                )
            )
        ) INTO v_result
        FROM author_influence_networks
        WHERE influence_type = p_influence_type;
    END IF;

    RETURN v_result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Author influence network query failed',
            'details', SQLERRM
        );
END;
$$;

-- Function 2: Thematic Evolution Analysis
CREATE OR REPLACE FUNCTION api_thematic_evolution(
    p_theme TEXT DEFAULT NULL,
    p_evolution_type TEXT DEFAULT 'historical',
    p_limit INTEGER DEFAULT 20
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    IF p_theme IS NOT NULL THEN
        -- Get specific theme evolution
        SELECT json_build_object(
            'success', true,
            'data', json_build_object(
                'search_type', 'theme_evolution',
                'theme', p_theme,
                'evolution_patterns', json_agg(
                    json_build_object(
                        'time_period', time_period,
                        'prevalence_score', prevalence_score,
                        'evolution_stage', evolution_stage,
                        'representative_books', (
                            SELECT json_agg(
                                json_build_object(
                                    'book_id', b.book_id,
                                    'title', b.title,
                                    'author', b.author
                                )
                            )
                            FROM unnest(te.representative_books) as book_id
                            JOIN books b ON b.book_id = book_id
                        )
                    ) ORDER BY prevalence_score DESC
                ),
                'evolution_summary', json_build_object(
                    'total_periods', COUNT(*),
                    'peak_prevalence', MAX(prevalence_score),
                    'avg_prevalence', ROUND(AVG(prevalence_score)::numeric, 3)
                )
            )
        ) INTO v_result
        FROM thematic_evolution te
        WHERE theme_name = p_theme
        AND (p_evolution_type = 'all' OR evolution_stage = p_evolution_type);
    ELSE
        -- Get thematic evolution overview
        SELECT json_build_object(
            'success', true,
            'data', json_build_object(
                'search_type', 'thematic_evolution_overview',
                'evolution_type', p_evolution_type,
                'theme_rankings', json_agg(
                    json_build_object(
                        'theme_name', theme_name,
                        'pattern_count', pattern_count,
                        'avg_prevalence', avg_prevalence,
                        'peak_prevalence', peak_prevalence,
                        'time_periods', time_periods
                    ) ORDER BY avg_prevalence DESC
                ),
                'evolution_statistics', json_build_object(
                    'total_themes', COUNT(DISTINCT theme_name),
                    'total_patterns', SUM(pattern_count),
                    'avg_theme_prevalence', ROUND(AVG(avg_prevalence)::numeric, 3)
                )
            )
        ) INTO v_result
        FROM (
            SELECT 
                theme_name,
                COUNT(*) as pattern_count,
                ROUND(AVG(prevalence_score)::numeric, 3) as avg_prevalence,
                MAX(prevalence_score) as peak_prevalence,
                array_agg(DISTINCT time_period) as time_periods
            FROM thematic_evolution
            WHERE (p_evolution_type = 'all' OR evolution_stage = p_evolution_type)
            GROUP BY theme_name
            ORDER BY AVG(prevalence_score) DESC
            LIMIT p_limit
        ) theme_stats;
    END IF;

    RETURN v_result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Thematic evolution query failed',
            'details', SQLERRM
        );
END;
$$;

-- Function 3: Content Analysis Deep Dive
CREATE OR REPLACE FUNCTION api_content_analysis(
    p_analysis_type TEXT DEFAULT 'overview',
    p_filter_value TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
)
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_result JSON;
BEGIN
    CASE p_analysis_type
        WHEN 'stylometric' THEN
            -- Stylometric analysis
            SELECT json_build_object(
                'success', true,
                'data', json_build_object(
                    'analysis_type', 'stylometric_features',
                    'books', json_agg(
                        json_build_object(
                            'book_id', bca.book_id,
                            'title', b.title,
                            'author', b.author,
                            'stylometric_profile', bca.stylometric_features,
                            'lexical_diversity', bca.lexical_diversity,
                            'narrative_structure', bca.narrative_structure
                        ) ORDER BY bca.lexical_diversity DESC
                    ),
                    'statistics', json_build_object(
                        'avg_lexical_diversity', ROUND(AVG(bca.lexical_diversity)::numeric, 4),
                        'diversity_range', json_build_object(
                            'min', MIN(bca.lexical_diversity),
                            'max', MAX(bca.lexical_diversity)
                        ),
                        'narrative_structures', (
                            SELECT json_object_agg(narrative_structure, count)
                            FROM (
                                SELECT narrative_structure, COUNT(*) as count
                                FROM book_content_analysis
                                WHERE narrative_structure IS NOT NULL
                                GROUP BY narrative_structure
                            ) ns
                        )
                    )
                )
            ) INTO v_result
            FROM book_content_analysis bca
            JOIN books b ON bca.book_id = b.book_id
            WHERE bca.stylometric_features IS NOT NULL
            LIMIT p_limit;
            
        WHEN 'thematic' THEN
            -- Thematic analysis
            SELECT json_build_object(
                'success', true,
                'data', json_build_object(
                    'analysis_type', 'thematic_landscape',
                    'books', json_agg(
                        json_build_object(
                            'book_id', bca.book_id,
                            'title', b.title,
                            'author', b.author,
                            'dominant_themes', (
                                SELECT json_agg(
                                    json_build_object('theme', key, 'score', value)
                                    ORDER BY value DESC
                                )
                                FROM json_each_text(bca.themes::json) as t(key, value)
                                WHERE value::float > 0
                                LIMIT 5
                            ),
                            'temporal_context', bca.temporal_markers
                        )
                    ),
                    'theme_distribution', (
                        SELECT json_object_agg(theme, total_score)
                        FROM (
                            SELECT 
                                key as theme,
                                ROUND(SUM(value::float)::numeric, 2) as total_score
                            FROM book_content_analysis,
                                 json_each_text(themes::json) as t(key, value)
                            WHERE value::float > 0
                            GROUP BY key
                            ORDER BY SUM(value::float) DESC
                            LIMIT 10
                        ) theme_totals
                    )
                )
            ) INTO v_result
            FROM book_content_analysis bca
            JOIN books b ON bca.book_id = b.book_id
            WHERE bca.themes IS NOT NULL
            LIMIT p_limit;
            
        WHEN 'entities' THEN
            -- Named entity analysis
            SELECT json_build_object(
                'success', true,
                'data', json_build_object(
                    'analysis_type', 'named_entities',
                    'books', json_agg(
                        json_build_object(
                            'book_id', bca.book_id,
                            'title', b.title,
                            'author', b.author,
                            'entity_profile', bca.named_entities,
                            'entity_summary', (
                                SELECT json_object_agg(entity_type, array_length(entities, 1))
                                FROM json_each(bca.named_entities::json) as e(entity_type, entities)
                                WHERE json_array_length(entities) > 0
                            )
                        )
                    ),
                    'entity_statistics', (
                        SELECT json_object_agg(entity_type, total_count)
                        FROM (
                            SELECT 
                                key as entity_type,
                                SUM(json_array_length(value)) as total_count
                            FROM book_content_analysis,
                                 json_each(named_entities::json) as e(key, value)
                            WHERE json_array_length(value) > 0
                            GROUP BY key
                            ORDER BY SUM(json_array_length(value)) DESC
                        ) entity_totals
                    )
                )
            ) INTO v_result
            FROM book_content_analysis bca
            JOIN books b ON bca.book_id = b.book_id
            WHERE bca.named_entities IS NOT NULL
            LIMIT p_limit;
            
        ELSE
            -- Overview analysis
            SELECT json_build_object(
                'success', true,
                'data', json_build_object(
                    'analysis_type', 'content_overview',
                    'analysis_scope', json_build_object(
                        'total_books_analyzed', COUNT(*),
                        'avg_lexical_diversity', ROUND(AVG(lexical_diversity)::numeric, 4),
                        'narrative_structure_distribution', (
                            SELECT json_object_agg(narrative_structure, structure_count)
                            FROM (
                                SELECT narrative_structure, COUNT(*) as structure_count
                                FROM book_content_analysis
                                WHERE narrative_structure IS NOT NULL
                                GROUP BY narrative_structure
                            ) structures
                        )
                    ),
                    'readability_overview', json_build_object(
                        'books_with_scores', COUNT(*) FILTER (WHERE readability_scores IS NOT NULL),
                        'avg_grade_estimate', ROUND(
                            AVG((readability_scores->>'flesch_kincaid_grade')::float)::numeric, 1
                        ) FILTER (WHERE readability_scores->>'flesch_kincaid_grade' IS NOT NULL)
                    ),
                    'sample_books', (
                        SELECT json_agg(
                            json_build_object(
                                'book_id', bca.book_id,
                                'title', b.title,
                                'author', b.author,
                                'analysis_highlights', json_build_object(
                                    'lexical_diversity', bca.lexical_diversity,
                                    'narrative_structure', bca.narrative_structure,
                                    'top_theme', (
                                        SELECT key
                                        FROM json_each_text(bca.themes::json) as t(key, value)
                                        WHERE value::float > 0
                                        ORDER BY value::float DESC
                                        LIMIT 1
                                    )
                                )
                            )
                        )
                        FROM book_content_analysis bca
                        JOIN books b ON bca.book_id = b.book_id
                        ORDER BY bca.lexical_diversity DESC
                        LIMIT 5
                    )
                )
            ) INTO v_result
            FROM book_content_analysis;
    END CASE;

    RETURN v_result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'Content analysis query failed',
            'details', SQLERRM
        );
END;
$$;