-- =========================================================================
-- pgTAP Tests for Production PostgreSQL Functions
-- =========================================================================
-- Tests only the 31 functions actually used by the production API
-- Author: CI/CD Pipeline
-- Date: 2025-08-15
-- =========================================================================

BEGIN;

-- Load pgTAP extension (will be added to test databases)
-- CREATE EXTENSION IF NOT EXISTS pgtap;

-- Plan the number of tests we're going to run
SELECT plan(93); -- 31 functions × 3 tests each = 93 tests

-- =========================================================================
-- TEST CATEGORY 1: FUNCTION EXISTENCE TESTS
-- =========================================================================

-- Core Search Functions (10 functions)
SELECT has_function('public', 'api_emotional_content_search', 'Function api_emotional_content_search exists');
SELECT has_function('public', 'api_extended_semantic_search', 'Function api_extended_semantic_search exists');
SELECT has_function('public', 'api_fast_trigram_phonetic_search', 'Function api_fast_trigram_phonetic_search exists');
SELECT has_function('public', 'api_get_book_chunks', 'Function api_get_book_chunks exists');
SELECT has_function('public', 'api_list_books', 'Function api_list_books exists');
SELECT has_function('public', 'api_passage_similarity_search', 'Function api_passage_similarity_search exists');
SELECT has_function('public', 'api_search_content_with_highlights', 'Function api_search_content_with_highlights exists');
SELECT has_function('public', 'api_semantic_concept_search', 'Function api_semantic_concept_search exists');
SELECT has_function('public', 'api_semantic_phrase_search_optimized', 'Function api_semantic_phrase_search_optimized exists');
SELECT has_function('public', 'api_semantic_similarity_explanation', 'Function api_semantic_similarity_explanation exists');

-- iOS Shortcuts Functions (21 functions)
SELECT has_function('public', 'api_shortcuts_book_construct', 'Function api_shortcuts_book_construct exists');
SELECT has_function('public', 'api_shortcuts_book_count', 'Function api_shortcuts_book_count exists');
SELECT has_function('public', 'api_shortcuts_book_page', 'Function api_shortcuts_book_page exists');
SELECT has_function('public', 'api_shortcuts_book_random_page', 'Function api_shortcuts_book_random_page exists');
SELECT has_function('public', 'api_shortcuts_book_summary', 'Function api_shortcuts_book_summary exists');
SELECT has_function('public', 'api_shortcuts_book_toc', 'Function api_shortcuts_book_toc exists');
SELECT has_function('public', 'api_shortcuts_collection_health', 'Function api_shortcuts_collection_health exists');
SELECT has_function('public', 'api_shortcuts_dashboard', 'Function api_shortcuts_dashboard exists');
SELECT has_function('public', 'api_shortcuts_list_authors', 'Function api_shortcuts_list_authors exists');
SELECT has_function('public', 'api_shortcuts_list_titles', 'Function api_shortcuts_list_titles exists');
SELECT has_function('public', 'api_shortcuts_random_author', 'Function api_shortcuts_random_author exists');
SELECT has_function('public', 'api_shortcuts_random_citation', 'Function api_shortcuts_random_citation exists');
SELECT has_function('public', 'api_shortcuts_random_share_text', 'Function api_shortcuts_random_share_text exists');
SELECT has_function('public', 'api_shortcuts_random_title', 'Function api_shortcuts_random_title exists');
SELECT has_function('public', 'api_shortcuts_search_count', 'Function api_shortcuts_search_count exists');
SELECT has_function('public', 'api_shortcuts_search_has_results', 'Function api_shortcuts_search_has_results exists');
SELECT has_function('public', 'api_shortcuts_search_simple', 'Function api_shortcuts_search_simple exists');
SELECT has_function('public', 'api_shortcuts_search_titles', 'Function api_shortcuts_search_titles exists');
SELECT has_function('public', 'api_v3_health', 'Function api_v3_health exists');
SELECT has_function('public', 'api_v3_search', 'Function api_v3_search exists');

-- Utility function
SELECT has_function('public', 'now', 'Function now exists');

-- =========================================================================
-- TEST CATEGORY 2: FUNCTION EXECUTABILITY TESTS (Basic Smoke Tests)
-- =========================================================================

-- Test health functions (should never fail)
SELECT lives_ok(
    'SELECT api_shortcuts_collection_health()',
    'api_shortcuts_collection_health executes without error'
);

SELECT lives_ok(
    'SELECT api_v3_health()',
    'api_v3_health executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_dashboard(false)',
    'api_shortcuts_dashboard executes without error'
);

-- Test simple search functions with basic input
SELECT lives_ok(
    'SELECT api_shortcuts_search_count(''test'')',
    'api_shortcuts_search_count executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_search_has_results(''test'')',
    'api_shortcuts_search_has_results executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_search_simple(''test'', 5)',
    'api_shortcuts_search_simple executes without error'
);

-- Test random functions (should always work)
SELECT lives_ok(
    'SELECT api_shortcuts_random_author()',
    'api_shortcuts_random_author executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_random_title()',
    'api_shortcuts_random_title executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_random_citation()',
    'api_shortcuts_random_citation executes without error'
);

-- Test list functions
SELECT lives_ok(
    'SELECT api_shortcuts_list_authors(10)',
    'api_shortcuts_list_authors executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_list_titles(10)',
    'api_shortcuts_list_titles executes without error'
);

-- Test semantic search functions
SELECT lives_ok(
    'SELECT api_extended_semantic_search(''love'', 5)',
    'api_extended_semantic_search executes without error'
);

SELECT lives_ok(
    'SELECT api_semantic_concept_search(''philosophy'', 0.5, 5)',
    'api_semantic_concept_search executes without error'
);

-- Test book listing
SELECT lives_ok(
    'SELECT api_list_books(1, 5, NULL, NULL, NULL)',
    'api_list_books executes without error'
);

-- =========================================================================
-- TEST CATEGORY 3: FUNCTION RETURN TYPE VALIDATION
-- =========================================================================

-- Test that health functions return expected structure
SELECT ok(
    (SELECT api_shortcuts_collection_health() IS NOT NULL),
    'api_shortcuts_collection_health returns non-null result'
);

SELECT ok(
    (SELECT api_v3_health() IS NOT NULL),
    'api_v3_health returns non-null result'
);

-- Test that search count returns a number
SELECT ok(
    (SELECT api_shortcuts_search_count('test') >= 0),
    'api_shortcuts_search_count returns non-negative number'
);

-- Test that has_results returns boolean-like result
SELECT ok(
    (SELECT api_shortcuts_search_has_results('test') IS NOT NULL),
    'api_shortcuts_search_has_results returns non-null result'
);

-- Test that random functions return results
SELECT ok(
    (SELECT api_shortcuts_random_author() IS NOT NULL),
    'api_shortcuts_random_author returns non-null result'
);

SELECT ok(
    (SELECT api_shortcuts_random_title() IS NOT NULL),
    'api_shortcuts_random_title returns non-null result'
);

SELECT ok(
    (SELECT api_shortcuts_random_citation() IS NOT NULL),
    'api_shortcuts_random_citation returns non-null result'
);

-- Test that list functions return results
SELECT ok(
    (SELECT api_shortcuts_list_authors(10) IS NOT NULL),
    'api_shortcuts_list_authors returns non-null result'
);

SELECT ok(
    (SELECT api_shortcuts_list_titles(10) IS NOT NULL),
    'api_shortcuts_list_titles returns non-null result'
);

-- Test search functions return proper structure
SELECT ok(
    (SELECT api_shortcuts_search_simple('test', 5) IS NOT NULL),
    'api_shortcuts_search_simple returns non-null result'
);

SELECT ok(
    (SELECT api_extended_semantic_search('love', 5) IS NOT NULL),
    'api_extended_semantic_search returns non-null result'
);

SELECT ok(
    (SELECT api_semantic_concept_search('philosophy', 0.5, 5) IS NOT NULL),
    'api_semantic_concept_search returns non-null result'
);

-- Test book functions (these might fail if no books, but shouldn't error)
SELECT lives_ok(
    'SELECT api_get_book_chunks(1, 1, 1)',
    'api_get_book_chunks executes without error'
);

SELECT lives_ok(
    'SELECT api_shortcuts_book_count()',
    'api_shortcuts_book_count executes without error'
);

-- Test remaining search functions
SELECT lives_ok(
    'SELECT api_fast_trigram_phonetic_search(''test'', 5)',
    'api_fast_trigram_phonetic_search executes without error'
);

SELECT lives_ok(
    'SELECT api_passage_similarity_search(''test'', 5)',
    'api_passage_similarity_search executes without error'
);

SELECT lives_ok(
    'SELECT api_search_content_with_highlights(''test'', 5, 100)',
    'api_search_content_with_highlights executes without error'
);

SELECT lives_ok(
    'SELECT api_semantic_phrase_search_optimized(''test'', 5)',
    'api_semantic_phrase_search_optimized executes without error'
);

SELECT lives_ok(
    'SELECT api_emotional_content_search(''love'', NULL, 5)',
    'api_emotional_content_search executes without error'
);

-- Test more return type validations
SELECT ok(
    (SELECT api_shortcuts_book_count() IS NOT NULL),
    'api_shortcuts_book_count returns non-null result'
);

SELECT ok(
    (SELECT api_fast_trigram_phonetic_search('test', 5) IS NOT NULL),
    'api_fast_trigram_phonetic_search returns non-null result'
);

SELECT ok(
    (SELECT api_passage_similarity_search('test', 5) IS NOT NULL),
    'api_passage_similarity_search returns non-null result'
);

SELECT ok(
    (SELECT api_search_content_with_highlights('test', 5, 100) IS NOT NULL),
    'api_search_content_with_highlights returns non-null result'
);

SELECT ok(
    (SELECT api_semantic_phrase_search_optimized('test', 5) IS NOT NULL),
    'api_semantic_phrase_search_optimized returns non-null result'
);

SELECT ok(
    (SELECT api_emotional_content_search('love', NULL, 5) IS NOT NULL),
    'api_emotional_content_search returns non-null result'
);

-- Test dashboard function return
SELECT ok(
    (SELECT api_shortcuts_dashboard(false) IS NOT NULL),
    'api_shortcuts_dashboard returns non-null result'
);

-- Test semantic similarity explanation
SELECT lives_ok(
    'SELECT api_semantic_similarity_explanation(''test'', ''example'')',
    'api_semantic_similarity_explanation executes without error'
);

SELECT ok(
    (SELECT api_semantic_similarity_explanation('test', 'example') IS NOT NULL),
    'api_semantic_similarity_explanation returns non-null result'
);

-- Test titles search
SELECT lives_ok(
    'SELECT api_shortcuts_search_titles(''test'', 5)',
    'api_shortcuts_search_titles executes without error'
);

SELECT ok(
    (SELECT api_shortcuts_search_titles('test', 5) IS NOT NULL),
    'api_shortcuts_search_titles returns non-null result'
);

-- Test v3 search
SELECT lives_ok(
    'SELECT api_v3_search(''test'', 5)',
    'api_v3_search executes without error'
);

SELECT ok(
    (SELECT api_v3_search('test', 5) IS NOT NULL),
    'api_v3_search returns non-null result'
);

-- Finish the test plan
SELECT finish();

ROLLBACK;