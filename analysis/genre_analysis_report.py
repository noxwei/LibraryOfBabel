#!/usr/bin/env python3
"""
📊 LIBRARYOFBABEL GENRE ANALYSIS REPORT
=======================================

Comprehensive analysis of genre data quality and standardization needs.
Identifies missing genres and out-of-range values for remediation.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Set

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

def define_standard_genre_taxonomy() -> Dict[str, List[str]]:
    """Define standard genre categories for digital library"""
    return {
        "Fiction": [
            "Literary Fiction", "Historical Fiction", "Contemporary Fiction",
            "Experimental Fiction", "Biographical Fiction"
        ],
        "Science Fiction & Fantasy": [
            "Science Fiction", "Fantasy", "Dystopian", "Utopian", 
            "Space Opera", "Cyberpunk", "Steampunk", "Urban Fantasy"
        ],
        "Philosophy & Theory": [
            "Philosophy", "Political Theory", "Social Theory", "Critical Theory",
            "Ethics", "Metaphysics", "Epistemology", "Logic"
        ],
        "History & Biography": [
            "History", "Biography", "Autobiography", "Memoir", 
            "Historical Analysis", "Political History", "Social History"
        ],
        "Science & Technology": [
            "Science", "Technology", "Mathematics", "Computer Science",
            "Neuroscience", "Psychology", "Sociology", "Anthropology"
        ],
        "Politics & Government": [
            "Political Science", "Government", "Public Policy", 
            "International Relations", "Political Economy"
        ],
        "Literature & Criticism": [
            "Literary Criticism", "Literary Theory", "Comparative Literature",
            "Cultural Studies", "Gender Studies", "Postcolonial Studies"
        ],
        "Business & Economics": [
            "Economics", "Business", "Finance", "Management", 
            "Entrepreneurship", "Marketing", "Strategy"
        ],
        "Arts & Culture": [
            "Art", "Music", "Film", "Theater", "Cultural Criticism",
            "Media Studies", "Visual Arts"
        ],
        "Reference & Education": [
            "Reference", "Textbook", "Academic", "Educational",
            "Manual", "Guide", "Encyclopedia"
        ]
    }

def analyze_current_genres() -> Dict[str, any]:
    """Analyze current genre data from database query results"""
    
    # Current genre data from database
    current_genres = {
        "公众号：古德猫宁李": 4,
        "Science Fiction": 2,
        "Dystopia": 1,
        "Fiction": 1,
        "Fiction / Dystopian": 1,
        "Ghosts": 1,
        "LIT004160 Literary Criticism / Lgbt": 1,
        "Manipulation": 1,
        "Non-Fiction: History": 1,
        "Novela, Ciencia ficción": 1,
        "Novela, Drama, Fantástico": 1,
        "Novela, Fantástico": 1,
        "Novela, Fantástico, Juvenil": 1,
        "Reference": 1,
        "COM060120 Computers / Web / Search Engines": 1,
        "Science Fiction/Fantasy": 1,
        "book": 1,
        "chenjin5.com沉金书屋": 1,
        "cj5": 1,
        "classic science fiction series": 1,
        "humour": 1,
        "neuroscience": 1,
        "none": 1,
        "paranormal": 1,
        "productivity secret": 1,
        "sf": 1,
        "theory": 1,
        "Relato, Ciencia ficción": 1,
        "Classics": 1
    }
    
    standard_taxonomy = define_standard_genre_taxonomy()
    all_standard_genres = set()
    for category, genres in standard_taxonomy.items():
        all_standard_genres.update([g.lower() for g in genres])
        all_standard_genres.add(category.lower())
    
    # Classify current genres
    valid_genres = []
    mappable_genres = []
    out_of_range_genres = []
    non_genre_values = []
    
    for genre, count in current_genres.items():
        genre_lower = genre.lower().strip()
        
        if genre_lower in all_standard_genres:
            valid_genres.append((genre, count, "Standard"))
        elif any(standard in genre_lower for standard in all_standard_genres):
            mappable_genres.append((genre, count, "Mappable"))
        elif genre_lower in ['none', 'book', 'cj5'] or '公众号' in genre or 'chenjin5.com' in genre:
            non_genre_values.append((genre, count, "Non-genre metadata"))
        elif genre.startswith(('LIT', 'COM')):
            mappable_genres.append((genre, count, "Library classification code"))
        else:
            out_of_range_genres.append((genre, count, "Out of range"))
    
    return {
        "total_books_with_genres": sum(current_genres.values()),
        "unique_genre_values": len(current_genres),
        "valid_genres": valid_genres,
        "mappable_genres": mappable_genres,
        "out_of_range_genres": out_of_range_genres,
        "non_genre_values": non_genre_values,
        "standard_taxonomy": standard_taxonomy
    }

def generate_genre_mapping_rules() -> Dict[str, str]:
    """Generate mapping rules for standardizing genres"""
    return {
        # Direct mappings
        "Science Fiction": "Science Fiction & Fantasy",
        "Dystopia": "Science Fiction & Fantasy",
        "Fiction": "Fiction",
        "Fiction / Dystopian": "Science Fiction & Fantasy",
        "Reference": "Reference & Education",
        "neuroscience": "Science & Technology",
        "theory": "Philosophy & Theory",
        "Classics": "Literature & Criticism",
        
        # Spanish language mappings
        "Novela, Ciencia ficción": "Science Fiction & Fantasy",
        "Novela, Drama, Fantástico": "Science Fiction & Fantasy", 
        "Novela, Fantástico": "Science Fiction & Fantasy",
        "Novela, Fantástico, Juvenil": "Science Fiction & Fantasy",
        "Relato, Ciencia ficción": "Science Fiction & Fantasy",
        
        # Abbreviations and variants
        "sf": "Science Fiction & Fantasy",
        "Science Fiction/Fantasy": "Science Fiction & Fantasy",
        "classic science fiction series": "Science Fiction & Fantasy",
        "humour": "Literature & Criticism",
        "paranormal": "Science Fiction & Fantasy",
        
        # Library codes
        "LIT004160 Literary Criticism / Lgbt": "Literature & Criticism",
        "COM060120 Computers / Web / Search Engines": "Science & Technology",
        "Non-Fiction: History": "History & Biography",
        
        # Remove non-genre values
        "none": None,
        "book": None,
        "cj5": None,
        "公众号：古德猫宁李": None,
        "chenjin5.com沉金书屋": None,
        "Manipulation": "Philosophy & Theory",  # Could be psychology/philosophy
        "Ghosts": "Science Fiction & Fantasy",
        "productivity secret": "Business & Economics"
    }

def main():
    """Generate comprehensive genre analysis report"""
    
    print("📊 LIBRARYOFBABEL GENRE ANALYSIS REPORT")
    print("=" * 60)
    print()
    
    # Database statistics
    print("📈 DATABASE STATISTICS")
    print("-" * 30)
    print(f"Total Books: 1,243")
    print(f"Books with Missing Genres: 1,210 (97.3%)")
    print(f"Books with Populated Genres: 33 (2.7%)")
    print(f"Unique Genre Values: 29")
    print()
    
    # Genre analysis
    analysis = analyze_current_genres()
    
    print("🔍 GENRE QUALITY ANALYSIS")
    print("-" * 30)
    print(f"Valid Standard Genres: {len(analysis['valid_genres'])}")
    print(f"Mappable Genres: {len(analysis['mappable_genres'])}")
    print(f"Out-of-Range Genres: {len(analysis['out_of_range_genres'])}")
    print(f"Non-Genre Values: {len(analysis['non_genre_values'])}")
    print()
    
    # Valid genres
    if analysis['valid_genres']:
        print("✅ VALID GENRES")
        print("-" * 20)
        for genre, count, status in analysis['valid_genres']:
            print(f"  {genre} ({count} books) - {status}")
        print()
    
    # Mappable genres
    if analysis['mappable_genres']:
        print("🔄 MAPPABLE GENRES")
        print("-" * 20)
        for genre, count, status in analysis['mappable_genres']:
            print(f"  {genre} ({count} books) - {status}")
        print()
    
    # Out of range genres
    if analysis['out_of_range_genres']:
        print("❌ OUT-OF-RANGE GENRES")
        print("-" * 25)
        for genre, count, status in analysis['out_of_range_genres']:
            print(f"  {genre} ({count} books) - {status}")
        print()
    
    # Non-genre values
    if analysis['non_genre_values']:
        print("🚫 NON-GENRE VALUES")
        print("-" * 20)
        for genre, count, status in analysis['non_genre_values']:
            print(f"  {genre} ({count} books) - {status}")
        print()
    
    # Mapping recommendations
    print("🎯 STANDARDIZATION RECOMMENDATIONS")
    print("-" * 40)
    
    mapping_rules = generate_genre_mapping_rules()
    
    print("1. IMMEDIATE MAPPING OPPORTUNITIES:")
    mappable_count = 0
    for current_genre, target_genre in mapping_rules.items():
        if target_genre:  # Exclude None mappings
            if current_genre in [g[0] for g in analysis['mappable_genres']] or \
               current_genre in [g[0] for g in analysis['valid_genres']]:
                count = next((c for g, c, _ in analysis['mappable_genres'] + analysis['valid_genres'] if g == current_genre), 0)
                print(f"   '{current_genre}' → '{target_genre}' ({count} books)")
                mappable_count += count
    
    print(f"\n   Total mappable books: {mappable_count}")
    
    print("\n2. REMOVE NON-GENRE VALUES:")
    removable_count = 0
    for current_genre, target_genre in mapping_rules.items():
        if target_genre is None:
            count = next((c for g, c, _ in analysis['non_genre_values'] if g == current_genre), 0)
            if count > 0:
                print(f"   Remove '{current_genre}' ({count} books)")
                removable_count += count
    
    print(f"\n   Total books to clean: {removable_count}")
    
    # Strategy for missing genres
    print("\n3. MISSING GENRE RECOVERY STRATEGY:")
    print("   📚 Content-based classification for 1,210 books")
    print("   🤖 Use embedding models + LLM classification")
    print("   📖 Analyze book titles, descriptions, and content")
    print("   🏷️  Implement automated genre tagging system")
    
    # Standard taxonomy
    print(f"\n📋 STANDARD GENRE TAXONOMY")
    print("-" * 30)
    taxonomy = analysis['standard_taxonomy']
    for category, subcategories in taxonomy.items():
        print(f"{category}:")
        for subcat in subcategories[:3]:  # Show first 3
            print(f"  • {subcat}")
        if len(subcategories) > 3:
            print(f"  • ... ({len(subcategories)-3} more)")
        print()
    
    print("🎯 NEXT STEPS")
    print("-" * 15)
    print("1. Implement automated genre classification using embeddings")
    print("2. Apply mapping rules to existing 33 books with genres")
    print("3. Develop content-based genre detection for 1,210 missing books")
    print("4. Integrate with chunking system for enhanced search")
    print("5. Add genre-based filtering to search API")

if __name__ == "__main__":
    main()