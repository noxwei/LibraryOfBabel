-- =========================================================================
-- Manual Research Function Cleanup - Production Safe
-- =========================================================================
-- Description: Directly remove research functions from knowledge_base
-- Based on: V003__Selective_cleanup_team_research.sql analysis
-- Safety: Flyway backups provide full restoration capability
-- =========================================================================

-- Remove Dr. Chen research experiments
DROP FUNCTION IF EXISTS chen_analogical_patterns(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_analogical_search(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_desire_surveillance_synthesis(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_fantasy_mythic_resonance(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_foucauldian_power_analysis(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_foucauldian_power_fast(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_genre_transcendence(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_lightning_search(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_queer_taboo_desire_analysis(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_rhizomatic_exploration(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_rhizomatic_exploration_fast(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS chen_scifi_speculative_bridges(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_chen_refined_clustering(TEXT, INTEGER) CASCADE;

-- Remove Dr. Elena research functions
DROP FUNCTION IF EXISTS dr_elena_assess_book_metadata_completeness(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_batch_repair_encoding_issues(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_cleanup_enhancement_logs() CASCADE;
DROP FUNCTION IF EXISTS dr_elena_collection_health_summary() CASCADE;
DROP FUNCTION IF EXISTS dr_elena_description_enhancement_summary() CASCADE;
DROP FUNCTION IF EXISTS dr_elena_get_books_for_epub_migration(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_get_books_needing_descriptions(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_get_next_enhancement_batch(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_log_description_enhancement(INTEGER, TEXT) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_log_epub_migration(INTEGER, TEXT) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_recalculate_word_counts() CASCADE;
DROP FUNCTION IF EXISTS dr_elena_recent_enhancement_activity() CASCADE;
DROP FUNCTION IF EXISTS dr_elena_repair_encoding_artifacts(TEXT) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_repair_encoding_artifacts_enhanced(TEXT) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_update_book_metadata(INTEGER, JSONB) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_validate_chunk_content_quality(INTEGER) CASCADE;

-- Remove Dr. Marcus research functions
DROP FUNCTION IF EXISTS dr_marcus_bulk_metadata_sync(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_cleanup_sync_logs() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_get_migration_queue(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_get_sync_statistics() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_log_calibre_migration(INTEGER, TEXT) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_normalize_genre_tags() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_standardize_author_names() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_sync_metadata_from_calibre(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_validate_library_consistency() CASCADE;

-- Remove Dr. Sarah research functions
DROP FUNCTION IF EXISTS dr_sarah_chen_calibre_linkage_schema() CASCADE;
DROP FUNCTION IF EXISTS dr_sarah_chen_calibre_metadata_architecture() CASCADE;
DROP FUNCTION IF EXISTS dr_sarah_chen_robust_calibre_linkage() CASCADE;
DROP FUNCTION IF EXISTS dr_sarah_chen_robust_calibre_linkage_functions() CASCADE;

-- Remove Calibre experiment functions
DROP FUNCTION IF EXISTS api_apply_calibre_metadata_enhancement(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_batch_calibre_linkage(INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_batch_calibre_metadata_sync(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_batch_robust_calibre_linkage(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_calibre_linkage_diagnostics() CASCADE;
DROP FUNCTION IF EXISTS api_calibre_linkage_statistics() CASCADE;
DROP FUNCTION IF EXISTS api_extract_calibre_metadata(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_find_calibre_book_author_fallback(TEXT) CASCADE;
DROP FUNCTION IF EXISTS api_find_calibre_book_exact_match(TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS api_find_calibre_book_fuzzy_match(TEXT) CASCADE;
DROP FUNCTION IF EXISTS api_get_calibre_linked_books(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_link_calibre_book(INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_resolve_calibre_path(TEXT) CASCADE;
DROP FUNCTION IF EXISTS api_robust_calibre_linkage(INTEGER) CASCADE;

-- Remove test/benchmark functions
DROP FUNCTION IF EXISTS benchmark_search_performance(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_black_technology_search_enhanced(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_book_download(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_fast_vector_functions(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_fixed_speed(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_fuzzy_match(TEXT, REAL, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_guaranteed_fast(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_json_semantic_functions(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_lightning_speed(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_replacement_functions(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_simple_speed(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_subset_speed(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_trigram_capability(TEXT) CASCADE;
DROP FUNCTION IF EXISTS test_trigram_speed_quick(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_ultra_strategies(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_vector_performance(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS test_vector_semantic_functions(TEXT, INTEGER) CASCADE;

-- Remove deprecated API versions
DROP FUNCTION IF EXISTS api_search_fixed_fast(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_shortcuts_search_enhanced(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS hybrid_search_v2(TEXT, REAL, INTEGER) CASCADE;

SELECT 'Manual cleanup completed - research functions removed from knowledge_base' AS cleanup_message;