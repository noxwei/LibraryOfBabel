-- =========================================================================
-- V003: Selective Cleanup - Remove Team/Research Functions Only
-- =========================================================================
-- Description: Remove 76 team/research functions, preserve production API + data pipeline
-- Author: Database Audit System (Revised Strategy)
-- Date: 2025-08-15
-- Dependencies: V002__Core_api_functions.sql
-- 
-- STRATEGY: Remove team research experiments while preserving:
-- ✅ Production API functions (31 functions)
-- ✅ Data pipeline functions (24 functions) 
-- ✅ Vector/embedding infrastructure (102 functions)
-- ✅ PostgreSQL system functions (102 functions)
-- ✅ Phonetic extensions (7 functions)
-- 
-- TOTAL: Keep 266 functions, remove 76 team/research functions (16.6% reduction)
-- =========================================================================

-- =============================================================================
-- REMOVE CATEGORY 1: CALIBRE INTEGRATION EXPERIMENTS (14 functions)
-- =============================================================================
-- These were experimental Calibre integration functions not used by production

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

-- =============================================================================
-- REMOVE CATEGORY 2: DEPRECATED API VERSIONS (4 functions)
-- =============================================================================

DROP FUNCTION IF EXISTS api_search_fixed_fast(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS api_shortcuts_search_enhanced(TEXT, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_repair_encoding_artifacts_enhanced(TEXT) CASCADE;
DROP FUNCTION IF EXISTS hybrid_search_v2(TEXT, REAL, INTEGER) CASCADE;

-- =============================================================================
-- REMOVE CATEGORY 3: DR. CHEN RESEARCH EXPERIMENTS (13 functions)
-- =============================================================================

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

-- =============================================================================
-- REMOVE CATEGORY 4: LEGACY TEST FUNCTIONS (17 functions)
-- =============================================================================

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

-- =============================================================================
-- REMOVE CATEGORY 5: DR. TEAM MEMBER RESEARCH FUNCTIONS (28 functions)
-- =============================================================================
-- Functions created by specific team members for research purposes

-- Dr. Elena research functions
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
DROP FUNCTION IF EXISTS dr_elena_update_book_metadata(INTEGER, JSONB) CASCADE;
DROP FUNCTION IF EXISTS dr_elena_validate_chunk_content_quality(INTEGER) CASCADE;

-- Dr. Marcus research functions
DROP FUNCTION IF EXISTS dr_marcus_bulk_metadata_sync(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_cleanup_sync_logs() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_get_migration_queue(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_get_sync_statistics() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_log_calibre_migration(INTEGER, TEXT) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_normalize_genre_tags() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_standardize_author_names() CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_sync_metadata_from_calibre(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS dr_marcus_validate_library_consistency() CASCADE;

-- Dr. Sarah research functions  
DROP FUNCTION IF EXISTS dr_sarah_chen_calibre_linkage_schema() CASCADE;
DROP FUNCTION IF EXISTS dr_sarah_chen_calibre_metadata_architecture() CASCADE;
DROP FUNCTION IF EXISTS dr_sarah_chen_robust_calibre_linkage() CASCADE;
DROP FUNCTION IF EXISTS dr_sarah_chen_robust_calibre_linkage_functions() CASCADE;

-- =============================================================================
-- SUMMARY OF CHANGES
-- =============================================================================
-- Functions Removed: ~76 team/research functions
-- Functions Preserved:
--   ✅ 31 production API functions (100% kept)
--   ✅ 24 data pipeline functions (100% kept)  
--   ✅ 102 vector/embedding functions (100% kept)
--   ✅ 102 PostgreSQL system functions (100% kept)
--   ✅ 7 phonetic extension functions (100% kept)
--
-- Total Functions After Cleanup: ~266 (16.6% reduction)
-- 
-- BENEFITS:
-- • Cleaner, more maintainable database
-- • Faster schema operations  
-- • Preserved production functionality
-- • Preserved data pipeline capabilities
-- • Future-ready for book ingestion with Nomic embeddings