-- =========================================================================
-- U004: Rollback Schema Separation
-- =========================================================================
-- Description: Rollback script for V004__Schema_separation.sql
-- Author: Database Architecture Team  
-- Date: 2025-08-15
-- =========================================================================

-- =============================================================================
-- MOVE ALL FUNCTIONS BACK TO PUBLIC SCHEMA
-- =============================================================================

-- Move API functions back to public
ALTER FUNCTION api.api_emotional_content_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_extended_semantic_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_fast_passage_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_fast_trigram_phonetic_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_passage_similarity_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_semantic_concept_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_semantic_phrase_search_optimized(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_semantic_similarity_explanation(TEXT, TEXT) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_book_construct(INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_book_count() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_book_page(INTEGER, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_book_random_page() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_book_summary(INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_book_toc(INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_collection_health() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_dashboard() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_list_authors(INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_list_titles(INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_random_author() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_random_citation() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_random_share_text() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_random_title() SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_search_count(TEXT) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_search_has_results(TEXT) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_search_simple(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_shortcuts_search_titles(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_v3_health() SET SCHEMA public;
ALTER FUNCTION api.api_v3_search(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_get_book_chunks(INTEGER, INTEGER, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_list_books(INTEGER, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.api_search_content_with_highlights(TEXT, INTEGER) SET SCHEMA public;
ALTER FUNCTION api.now() SET SCHEMA public;
ALTER FUNCTION api.hybrid_search(TEXT, REAL, INTEGER) SET SCHEMA public;

-- Move pipeline functions back to public
ALTER FUNCTION pipeline.api_ingest_complete_book(TEXT, TEXT, TEXT, TEXT) SET SCHEMA public;
ALTER FUNCTION pipeline.api_process_book_batch(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.api_process_book_content(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.batch_process_books_simple(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.generate_chunk_embeddings_batch(INTEGER, TEXT) SET SCHEMA public;
ALTER FUNCTION pipeline.check_embedding_write_locations() SET SCHEMA public;
ALTER FUNCTION pipeline.validate_embedding_search_capability() SET SCHEMA public;
ALTER FUNCTION pipeline.get_embedding_model_usage_stats() SET SCHEMA public;
ALTER FUNCTION pipeline.get_embedding_system_status() SET SCHEMA public;
ALTER FUNCTION pipeline.get_optimal_embedding_model() SET SCHEMA public;
ALTER FUNCTION pipeline.batch_process_unclassified_books(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.hybrid_ensemble_classification(TEXT) SET SCHEMA public;
ALTER FUNCTION pipeline.ml_phase1_subject_classification(TEXT) SET SCHEMA public;
ALTER FUNCTION pipeline.api_insert_book(TEXT, TEXT, TEXT, TEXT, TEXT) SET SCHEMA public;
ALTER FUNCTION pipeline.api_insert_chapter_chunk(INTEGER, INTEGER, TEXT, TEXT, TEXT) SET SCHEMA public;
ALTER FUNCTION pipeline.update_book_word_count(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.update_search_vector(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.update_book_statistics(INTEGER) SET SCHEMA public;
ALTER FUNCTION pipeline.log_search_performance(TEXT, INTEGER, REAL) SET SCHEMA public;
ALTER FUNCTION pipeline.get_search_performance_stats() SET SCHEMA public;
ALTER FUNCTION pipeline.refresh_book_statistics() SET SCHEMA public;

-- Move vector functions back to public  
ALTER FUNCTION vectors.api_get_sample_vector() SET SCHEMA public;
ALTER FUNCTION vectors.api_vector_search(REAL[], INTEGER) SET SCHEMA public;

-- =============================================================================
-- DROP SCHEMAS (CASCADE TO HANDLE ANY REMAINING OBJECTS)
-- =============================================================================

DROP SCHEMA IF EXISTS api CASCADE;
DROP SCHEMA IF EXISTS pipeline CASCADE;
DROP SCHEMA IF EXISTS vectors CASCADE;

SELECT 'V004 schema separation rollback completed - all functions moved back to public schema' AS rollback_message;