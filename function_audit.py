#!/usr/bin/env python3
"""
LibraryOfBabel Function Audit Tool
==================================
Analyzes all 489 PostgreSQL functions and categorizes them by usage
"""

import re
import subprocess
import json
from collections import defaultdict

# Functions actually used by production API
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

def get_all_functions():
    """Get all function names from the database"""
    cmd = [
        'psql', '-U', 'weixiangzhang', '-d', 'knowledge_base',
        '-t', '-c', 
        "SELECT routine_name FROM information_schema.routines WHERE routine_schema='public' AND routine_type='FUNCTION' ORDER BY routine_name;"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error querying database: {result.stderr}")
        return []
    
    functions = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    return functions

def categorize_functions(functions):
    """Categorize functions by purpose and usage"""
    categories = {
        'production_api': set(),
        'legacy_test': set(),
        'development_temp': set(),
        'postgres_system': set(),
        'vector_extensions': set(),
        'phonetic_extensions': set(),
        'deprecated_versions': set(),
        'dr_chen_experiments': set(),
        'unknown': set()
    }
    
    for func in functions:
        func_lower = func.lower()
        
        # Production API functions
        if func in PRODUCTION_FUNCTIONS:
            categories['production_api'].add(func)
        
        # Legacy test functions
        elif any(keyword in func_lower for keyword in ['test_', 'benchmark_', 'debug_']):
            categories['legacy_test'].add(func)
        
        # Development/temp functions
        elif any(keyword in func_lower for keyword in ['temp_', 'temporary_', 'draft_', 'example_']):
            categories['development_temp'].add(func)
        
        # PostgreSQL system/extension functions
        elif any(keyword in func_lower for keyword in ['gin_', 'gtrgm_', 'pg_']):
            categories['postgres_system'].add(func)
        
        # Vector/embedding extension functions
        elif any(keyword in func_lower for keyword in ['vector', 'halfvec', 'sparsevec', 'embedding', 'hnsw', 'ivfflat']):
            categories['vector_extensions'].add(func)
        
        # Phonetic extension functions  
        elif any(keyword in func_lower for keyword in ['metaphone', 'soundex', 'levenshtein', 'dmetaphone']):
            categories['phonetic_extensions'].add(func)
        
        # Deprecated versions (multiple versions of same function)
        elif any(keyword in func_lower for keyword in ['_v1', '_v2', '_old', '_deprecated', '_backup', '_fixed', '_enhanced']):
            categories['deprecated_versions'].add(func)
        
        # Dr. Chen experimental functions
        elif any(keyword in func_lower for keyword in ['chen_', 'dr_chen', 'foucauldian', 'rhizomatic']):
            categories['dr_chen_experiments'].add(func)
        
        else:
            categories['unknown'].add(func)
    
    return categories

def analyze_function_dependencies():
    """Analyze which functions call other functions"""
    print("🔍 Analyzing function dependencies...")
    
    # Get function definitions to check for internal calls
    cmd = [
        'pg_dump', '-U', 'weixiangzhang', '-d', 'knowledge_base',
        '--schema-only', '--no-owner', '--no-privileges'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error dumping schema: {result.stderr}")
        return {}
    
    schema_dump = result.stdout
    dependencies = defaultdict(set)
    
    # Simple regex to find function calls within function definitions
    function_pattern = r'CREATE OR REPLACE FUNCTION\s+(\w+)\s*\('
    call_pattern = r'(\w+)\s*\('
    
    current_function = None
    for line in schema_dump.split('\n'):
        # Find function definitions
        func_match = re.search(function_pattern, line, re.IGNORECASE)
        if func_match:
            current_function = func_match.group(1)
            continue
        
        # Find function calls within definitions
        if current_function and 'api_' in line:
            calls = re.findall(r'(api_\w+)\s*\(', line)
            for call in calls:
                if call != current_function:  # Don't count self-references
                    dependencies[current_function].add(call)
    
    return dependencies

def generate_audit_report(categories, dependencies):
    """Generate comprehensive audit report"""
    
    print("=" * 80)
    print("📊 LIBRARYOFBABEL FUNCTION AUDIT REPORT")
    print("=" * 80)
    print()
    
    total_functions = sum(len(funcs) for funcs in categories.values())
    
    print(f"📈 **SUMMARY**")
    print(f"Total Functions Analyzed: {total_functions}")
    print(f"Production Functions (KEEP): {len(categories['production_api'])}")
    print(f"Functions to Remove: {total_functions - len(categories['production_api'])}")
    print(f"Reduction: {((total_functions - len(categories['production_api'])) / total_functions * 100):.1f}%")
    print()
    
    # Detailed breakdown
    for category, funcs in categories.items():
        if not funcs:
            continue
            
        print(f"## {category.replace('_', ' ').title()} ({len(funcs)} functions)")
        
        if category == 'production_api':
            print("✅ **KEEP** - These are used by the live production API")
        else:
            print("❌ **REMOVE** - These can be safely archived")
        
        if len(funcs) <= 10:
            for func in sorted(funcs):
                print(f"  - {func}")
        else:
            sample = sorted(list(funcs))[:5]
            for func in sample:
                print(f"  - {func}")
            print(f"  ... and {len(funcs) - 5} more")
        print()
    
    # Dependency analysis
    print("## 🔗 **FUNCTION DEPENDENCIES**")
    production_deps = set()
    for func in categories['production_api']:
        if func in dependencies:
            production_deps.update(dependencies[func])
    
    missing_deps = production_deps - categories['production_api']
    if missing_deps:
        print("⚠️  **CAUTION**: Production functions call these functions:")
        for dep in sorted(missing_deps):
            print(f"  - {dep}")
        print("Consider keeping these for production functionality.")
    else:
        print("✅ No missing dependencies found.")
    print()
    
    return {
        'total': total_functions,
        'keep': len(categories['production_api']),
        'remove': total_functions - len(categories['production_api']),
        'categories': {k: list(v) for k, v in categories.items()},
        'dependencies': {k: list(v) for k, v in dependencies.items()}
    }

def main():
    print("🔍 Starting LibraryOfBabel Function Audit...")
    print()
    
    # Get all functions
    functions = get_all_functions()
    print(f"📊 Found {len(functions)} functions to analyze")
    
    # Categorize functions
    categories = categorize_functions(functions)
    
    # Analyze dependencies
    dependencies = analyze_function_dependencies()
    
    # Generate report
    audit_results = generate_audit_report(categories, dependencies)
    
    # Save results
    with open('function_audit_results.json', 'w') as f:
        json.dump(audit_results, f, indent=2)
    
    print("💾 Audit results saved to function_audit_results.json")
    print()
    print("🎯 **NEXT STEPS:**")
    print("1. Review the audit results")
    print("2. Create Flyway migration to archive unused functions")
    print("3. Test production API with cleaned database")
    print("4. Deploy cleaner, faster database!")

if __name__ == "__main__":
    main()