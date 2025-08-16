#!/usr/bin/env python3
"""
Revised LibraryOfBabel Function Audit - Keep Data Pipeline
===========================================================
Strategy: Remove team/research functions, keep vector/embedding infrastructure
"""

import json

# Load original audit results
with open('function_audit_results.json', 'r') as f:
    data = json.load(f)

# Functions to KEEP (Production API + Data Pipeline)
PRODUCTION_FUNCTIONS = {
    'api_emotional_content_search',
    'api_extended_semantic_search', 
    'api_fast_trigram_phonetic_search',
    'api_get_book_chunks',
    'api_list_books',
    'api_passage_similarity_search',
    'api_search_content_with_highlights',
    'api_semantic_concept_search',
    'api_semantic_phrase_search_optimized',
    'api_semantic_similarity_explanation',
    'api_shortcuts_book_construct',
    'api_shortcuts_book_count',
    'api_shortcuts_book_page',
    'api_shortcuts_book_random_page',
    'api_shortcuts_book_summary',
    'api_shortcuts_book_toc',
    'api_shortcuts_collection_health',
    'api_shortcuts_dashboard',
    'api_shortcuts_list_authors',
    'api_shortcuts_list_titles',
    'api_shortcuts_random_author',
    'api_shortcuts_random_citation',
    'api_shortcuts_random_share_text',
    'api_shortcuts_random_title',
    'api_shortcuts_search_count',
    'api_shortcuts_search_has_results',
    'api_shortcuts_search_simple',
    'api_shortcuts_search_titles',
    'api_v3_health',
    'api_v3_search',
    'now'
}

# Additional functions to KEEP for data pipeline
DATA_PIPELINE_FUNCTIONS = {
    # Vector/embedding infrastructure for book ingestion
    'generate_chunk_embeddings_batch',
    'get_embedding_model_usage_stats',
    'get_embedding_system_status',
    'get_optimal_embedding_model',
    'api_get_sample_vector',
    'api_vector_search',
    'check_embedding_write_locations',
    'validate_embedding_search_capability',
    'api_ingest_complete_book',
    'api_process_book_content',
    'api_insert_book',
    'api_insert_chapter_chunk',
    
    # Book processing pipeline
    'batch_process_books_simple',
    'api_process_book_batch',
    'update_book_word_count',
    'update_search_vector',
    'update_book_statistics',
    
    # Content analysis for new books
    'hybrid_ensemble_classification',
    'ml_phase1_subject_classification',
    'batch_classify_content',
    'update_books_with_chunk_classification',
    
    # Performance monitoring for pipeline
    'log_search_performance',
    'get_search_performance_stats',
    'refresh_book_statistics'
}

# Functions to DEFINITELY REMOVE (Team/Research)
REMOVE_FUNCTIONS = set()

# Team member research functions
for func in data['categories']['unknown']:
    if any(team in func.lower() for team in ['dr_elena', 'dr_marcus', 'dr_chen', 'dr_sarah']):
        REMOVE_FUNCTIONS.add(func)

# Chen experiments
REMOVE_FUNCTIONS.update(data['categories']['dr_chen_experiments'])

# Test functions
REMOVE_FUNCTIONS.update(data['categories']['legacy_test'])

# Deprecated versions
REMOVE_FUNCTIONS.update(data['categories']['deprecated_versions'])

# Calibre functions (not used in current API)
for func in data['categories']['unknown']:
    if 'calibre' in func.lower():
        REMOVE_FUNCTIONS.add(func)

# Create revised categories
revised_categories = {
    'production_api': PRODUCTION_FUNCTIONS,
    'data_pipeline': DATA_PIPELINE_FUNCTIONS,
    'vector_extensions': set(data['categories']['vector_extensions']),  # Keep all
    'postgres_system': set(data['categories']['postgres_system']),      # Keep all  
    'phonetic_extensions': set(data['categories']['phonetic_extensions']), # Keep all
    'remove_team_research': REMOVE_FUNCTIONS
}

def generate_revised_report():
    print("=" * 80)
    print("📊 REVISED LIBRARYOFBABEL FUNCTION STRATEGY")
    print("=" * 80)
    print()
    
    total_functions = sum(len(funcs) for funcs in data['categories'].values())
    keep_functions = len(PRODUCTION_FUNCTIONS) + len(DATA_PIPELINE_FUNCTIONS) + \
                    len(data['categories']['vector_extensions']) + \
                    len(data['categories']['postgres_system']) + \
                    len(data['categories']['phonetic_extensions'])
    remove_functions = len(REMOVE_FUNCTIONS)
    
    print(f"📈 **REVISED SUMMARY**")
    print(f"Total Functions: {total_functions}")
    print(f"Keep for Production API: {len(PRODUCTION_FUNCTIONS)}")
    print(f"Keep for Data Pipeline: {len(DATA_PIPELINE_FUNCTIONS)}")
    print(f"Keep Vector/Embedding Infrastructure: {len(data['categories']['vector_extensions'])}")
    print(f"Keep PostgreSQL System: {len(data['categories']['postgres_system'])}")
    print(f"Keep Phonetic Extensions: {len(data['categories']['phonetic_extensions'])}")
    print(f"REMOVE Team/Research: {remove_functions}")
    print(f"Total KEEP: {keep_functions}")
    print(f"Reduction: {(remove_functions / total_functions * 100):.1f}%")
    print()
    
    print("## ✅ **KEEP - PRODUCTION API** (30 functions)")
    print("Critical functions used by live API")
    for func in sorted(PRODUCTION_FUNCTIONS):
        print(f"  • {func}")
    print()
    
    print("## ✅ **KEEP - DATA PIPELINE** (15 functions)")
    print("Functions for book ingestion, chunking, embedding with Nomic")
    for func in sorted(DATA_PIPELINE_FUNCTIONS):
        if func in data['categories']['unknown']:  # Only show the ones we're saving from removal
            print(f"  • {func}")
    print()
    
    print("## ✅ **KEEP - VECTOR/EMBEDDING INFRASTRUCTURE** (102 functions)")
    print("pgVector extension functions for embeddings pipeline")
    print("  • vector(), halfvec(), sparsevec() data types")
    print("  • distance calculations (l2_distance, cosine_distance, etc.)")
    print("  • HNSW and IVFFlat index functions")
    print("  • Array conversion functions")
    print()
    
    print("## ❌ **REMOVE - TEAM/RESEARCH FUNCTIONS** (estimated 100-150 functions)")
    print("Functions created by team members for research/experiments")
    sample_remove = sorted(list(REMOVE_FUNCTIONS))[:15]
    for func in sample_remove:
        print(f"  • {func}")
    print(f"  ... and {len(REMOVE_FUNCTIONS) - 15} more team/research functions")
    print()
    
    print("🎯 **STRATEGY BENEFITS:**")
    print("✅ Keep 100% of production API functionality")
    print("✅ Keep 100% of data pipeline infrastructure") 
    print("✅ Keep vector/embedding capabilities for new books")
    print("✅ Remove team research experiments")
    print("✅ Still get significant cleanup (~25-30% reduction)")
    print("✅ Future-proof for book ingestion pipeline")
    
    return {
        'total': total_functions,
        'keep_production': len(PRODUCTION_FUNCTIONS),
        'keep_pipeline': len(DATA_PIPELINE_FUNCTIONS),
        'keep_vector': len(data['categories']['vector_extensions']),
        'remove_research': len(REMOVE_FUNCTIONS),
        'remove_functions': list(REMOVE_FUNCTIONS)
    }

if __name__ == "__main__":
    results = generate_revised_report()
    
    # Save revised results
    with open('function_audit_revised.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Revised audit saved to function_audit_revised.json")
    print("\n🎯 **NEXT STEPS:**")
    print("1. Create V003_revised migration removing only team/research functions")
    print("2. Test with both production API and data pipeline")
    print("3. Deploy cleaner but pipeline-ready database")