#!/usr/bin/env python3
"""
LibraryOfBabel Hybrid Search Demo
Showcases the best of both worlds: exact references + semantic discovery
"""

import requests
import json
import sys
from typing import Dict, List

HYBRID_API_URL = "http://localhost:5560"

def test_hybrid_search(query: str, exact_limit: int = 5, semantic_limit: int = 5):
    """Test hybrid search with a specific query"""
    print(f"\n🔗 HYBRID SEARCH DEMO")
    print("=" * 60)
    print(f"Query: '{query}'")
    print("=" * 60)
    
    try:
        # Perform hybrid search
        response = requests.get(f"{HYBRID_API_URL}/api/hybrid-search", params={
            'q': query,
            'exact_limit': exact_limit,
            'semantic_limit': semantic_limit
        })
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return
        
        data = response.json()
        
        # Display metadata
        metadata = data['query_metadata']
        print(f"⚡ Response time: {metadata['response_time_ms']}ms")
        print(f"🕒 Timestamp: {metadata['timestamp']}")
        print()
        
        # Display exact references
        exact = data['exact_references']
        print(f"📖 EXACT REFERENCES ({exact['count']} results)")
        print("   " + exact['description'])
        print("-" * 50)
        
        for i, result in enumerate(exact['results'][:3], 1):
            print(f"{i}. 📚 {result['title']} by {result['author']}")
            print(f"   📍 {result['citation']['chapter_ref']} | Type: {result['chunk_type']}")
            print(f"   ⭐ Relevance: {result['relevance_rank']:.3f} | Words: {result['word_count']}")
            
            # Show navigation info
            nav = result['navigation']
            nav_info = []
            if nav.get('previous'):
                nav_info.append("◀ Previous")
            if nav.get('next'):
                nav_info.append("Next ▶")
            if nav.get('chapter_outline'):
                nav_info.append(f"{len(nav['chapter_outline'])} chapters")
            
            if nav_info:
                print(f"   🧭 Navigation: {' | '.join(nav_info)}")
            
            # Show content highlight
            if 'highlighted_content' in result:
                print(f"   💡 Content: {result['highlighted_content']}")
            else:
                print(f"   💡 Preview: {result['content_preview'][:150]}...")
            
            print()
        
        print()
        
        # Display semantic discovery
        semantic = data['semantic_discovery']
        print(f"🧠 SEMANTIC DISCOVERY ({semantic['count']} results)")
        print("   " + semantic['description'])
        print("-" * 50)
        
        for i, result in enumerate(semantic['results'][:3], 1):
            print(f"{i}. 🎯 {result['title']} by {result['author']}")
            print(f"   🎨 {result['relevance_explanation']}")
            print(f"   💭 Preview: {result['content_preview'][:150]}...")
            print()
        
        # Display usage guide
        guide = data['usage_guide']
        print("💡 USAGE GUIDE")
        print("-" * 50)
        print(f"📖 Exact References: {guide['exact_references']}")
        print(f"🧠 Semantic Discovery: {guide['semantic_discovery']}")
        print(f"🧭 Navigation: {guide['navigation']}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_chunk_detail(chunk_id: str):
    """Test chunk detail with navigation"""
    print(f"\n📖 CHUNK DETAIL DEMO")
    print("=" * 60)
    print(f"Chunk ID: {chunk_id}")
    print("=" * 60)
    
    try:
        response = requests.get(f"{HYBRID_API_URL}/api/chunk/{chunk_id}")
        
        if response.status_code == 404:
            print("❌ Chunk not found")
            return
        elif response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return
        
        data = response.json()
        
        # Show chunk details
        chunk = data['chunk_details']
        print(f"📚 Title: {chunk['title']}")
        print(f"✍️  Author: {chunk['author']}")
        print(f"📅 Year: {chunk['publication_year'] or 'Unknown'}")
        print(f"📖 Type: {chunk['chunk_type']}")
        print(f"📍 Location: Chapter {chunk['chapter_number']}, Section {chunk['section_number'] or 'N/A'}")
        print(f"📊 Stats: {chunk['word_count']} words, {chunk['character_count']} characters")
        print()
        
        # Show reading context
        context = data['reading_context']
        print(f"🧭 Reading Context: {context['current_location']}")
        print(f"📖 Book Context: {context['book_context']}")
        print()
        
        # Show navigation
        nav = data['navigation']
        if nav.get('previous'):
            prev = nav['previous']
            print(f"◀ Previous: Chapter {prev['chapter_number']}, {prev['type']}")
            print(f"   Preview: {prev['preview']}...")
        
        if nav.get('next'):
            next_chunk = nav['next']
            print(f"▶ Next: Chapter {next_chunk['chapter_number']}, {next_chunk['type']}")
            print(f"   Preview: {next_chunk['preview']}...")
        
        if nav.get('chapter_outline'):
            print(f"📋 Chapter Outline: {len(nav['chapter_outline'])} chapters available")
        
        print()
        
        # Show content preview
        print("📄 CONTENT PREVIEW")
        print("-" * 30)
        print(chunk['content'][:500] + "..." if len(chunk['content']) > 500 else chunk['content'])
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run hybrid search demos"""
    print("🚀 LibraryOfBabel Hybrid Search Demo")
    print("=" * 60)
    print("Demonstrating the best of both worlds:")
    print("📖 Lossless exact references with navigation")
    print("🧠 Semantic discovery for knowledge exploration")
    print()
    
    # Test queries
    test_queries = [
        "consciousness and free will",
        "power and resistance", 
        "technology and society"
    ]
    
    for query in test_queries:
        test_hybrid_search(query)
        print("\n" + "="*80 + "\n")
    
    # Test chunk detail (use a likely chunk ID)
    print("Testing chunk navigation...")
    test_chunk_detail("1_chapter_1")  # Try a common chunk ID pattern

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Custom query from command line
        query = " ".join(sys.argv[1:])
        test_hybrid_search(query)
    else:
        # Run full demo
        main()