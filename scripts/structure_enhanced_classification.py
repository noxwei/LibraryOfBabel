#!/usr/bin/env python3
"""
Structure-Enhanced Classification System
=======================================
Use book structure analysis to improve genre classification accuracy
"""

import sys
import json
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.api_config import get_database_config

class StructureEnhancedClassifier:
    def __init__(self):
        self.db_config = get_database_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"
        
        # Structure-based genre indicators from your reports
        self.structure_patterns = {
            "Academic & Research": {
                "strong_indicators": ["table of contents", "bibliography", "notes", "references", "index"],
                "moderate_indicators": ["introduction", "preface", "acknowledgments", "foreword"],
                "chapter_patterns": [r"chapter\s+\d+", r"part\s+\d+", r"section\s+\d+"],
                "weight": 0.3
            },
            "Biography & Memoir": {
                "strong_indicators": ["acknowledgments", "about the author", "epilogue"],
                "moderate_indicators": ["introduction", "preface", "foreword"],
                "chapter_patterns": [r"chapter\s+\d+", r"part\s+(one|two|three)"],
                "weight": 0.2
            },
            "History": {
                "strong_indicators": ["bibliography", "notes", "index", "chronology", "timeline"],
                "moderate_indicators": ["introduction", "preface", "maps", "illustrations"],
                "chapter_patterns": [r"chapter\s+\d+", r"part\s+\d+"],
                "weight": 0.25
            },
            "Self-Help": {
                "strong_indicators": ["exercises", "worksheets", "action steps", "resources"],
                "moderate_indicators": ["introduction", "how to use this book"],
                "chapter_patterns": [r"step\s+\d+", r"lesson\s+\d+", r"chapter\s+\d+"],
                "weight": 0.2
            },
            "Literary Fiction": {
                "strong_indicators": ["praise for", "reviews", "advance praise"],
                "moderate_indicators": ["acknowledgments", "author's note"],
                "chapter_patterns": [r"chapter\s+\d+", r"part\s+(one|two|three)", r"book\s+(one|two|three)"],
                "weight": 0.15
            },
            "Science Fiction": {
                "strong_indicators": ["glossary", "appendix", "technical notes"],
                "moderate_indicators": ["introduction", "author's note"],
                "chapter_patterns": [r"chapter\s+\d+", r"part\s+\d+", r"book\s+\d+"],
                "weight": 0.1
            },
            "Fantasy": {
                "strong_indicators": ["glossary", "maps", "appendix", "world guide"],
                "moderate_indicators": ["prologue", "epilogue", "author's note"],
                "chapter_patterns": [r"chapter\s+\d+", r"part\s+\d+", r"book\s+\d+"],
                "weight": 0.1
            }
        }
    
    def analyze_book_structure(self, book_id):
        """Analyze the structural elements of a book"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get all chunks for structure analysis
                cur.execute("""
                    SELECT content, chunk_id
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    ORDER BY chunk_id
                    LIMIT 8
                """, (book_id,))
                
                chunks = cur.fetchall()
                
                structure_info = {
                    "has_toc": False,
                    "has_introduction": False,
                    "has_acknowledgments": False,
                    "has_bibliography": False,
                    "has_index": False,
                    "has_glossary": False,
                    "chapter_pattern": None,
                    "academic_indicators": 0,
                    "fiction_indicators": 0,
                    "front_matter_chunks": 0
                }
                
                # Analyze each chunk for structural elements
                for chunk in chunks:
                    content_lower = chunk['content'].lower()
                    
                    # Check for structural elements
                    if any(indicator in content_lower for indicator in ['table of contents', 'contents']):
                        structure_info["has_toc"] = True
                    
                    if any(indicator in content_lower for indicator in ['introduction', 'preface', 'foreword']):
                        structure_info["has_introduction"] = True
                    
                    if any(indicator in content_lower for indicator in ['acknowledgment', 'acknowledgement', 'thanks']):
                        structure_info["has_acknowledgments"] = True
                    
                    if any(indicator in content_lower for indicator in ['bibliography', 'references', 'works cited']):
                        structure_info["has_bibliography"] = True
                    
                    if 'index' in content_lower and len(chunk['content']) < 500:
                        structure_info["has_index"] = True
                    
                    if 'glossary' in content_lower:
                        structure_info["has_glossary"] = True
                    
                    # Check for chapter patterns
                    if re.search(r'chapter\s+\d+', content_lower):
                        structure_info["chapter_pattern"] = "numbered_chapters"
                    elif re.search(r'part\s+(one|two|three|\d+)', content_lower):
                        structure_info["chapter_pattern"] = "parts"
                    
                    # Count academic vs fiction indicators
                    academic_words = ['research', 'study', 'analysis', 'theory', 'hypothesis', 'methodology']
                    fiction_words = ['character', 'dialogue', 'plot', 'story', 'narrative', 'protagonist']
                    
                    structure_info["academic_indicators"] += sum(1 for word in academic_words if word in content_lower)
                    structure_info["fiction_indicators"] += sum(1 for word in fiction_words if word in content_lower)
                    
                    # Check if chunk is front matter
                    if any(indicator in content_lower for indicator in ['copyright', 'published', 'isbn', '©']):
                        structure_info["front_matter_chunks"] += 1
                
                return structure_info
                
        finally:
            conn.close()
    
    def calculate_structure_based_genre_scores(self, structure_info):
        """Calculate genre probability scores based on structure"""
        scores = {}
        
        for genre, patterns in self.structure_patterns.items():
            score = 0.0
            
            # Strong indicators
            for indicator in patterns["strong_indicators"]:
                if indicator == "table of contents" and structure_info["has_toc"]:
                    score += 0.4
                elif indicator == "bibliography" and structure_info["has_bibliography"]:
                    score += 0.4
                elif indicator == "index" and structure_info["has_index"]:
                    score += 0.3
                elif indicator == "acknowledgments" and structure_info["has_acknowledgments"]:
                    score += 0.2
                elif indicator == "glossary" and structure_info["has_glossary"]:
                    score += 0.3
            
            # Moderate indicators
            for indicator in patterns["moderate_indicators"]:
                if indicator == "introduction" and structure_info["has_introduction"]:
                    score += 0.1
                elif indicator == "acknowledgments" and structure_info["has_acknowledgments"]:
                    score += 0.1
            
            # Chapter patterns
            if structure_info["chapter_pattern"] == "numbered_chapters":
                score += 0.1
            
            # Academic vs fiction content
            if genre in ["Academic & Research", "History", "Biography & Memoir"]:
                if structure_info["academic_indicators"] > structure_info["fiction_indicators"]:
                    score += 0.2
            elif genre in ["Literary Fiction", "Science Fiction", "Fantasy"]:
                if structure_info["fiction_indicators"] > structure_info["academic_indicators"]:
                    score += 0.2
            
            scores[genre] = min(score, 1.0)  # Cap at 1.0
        
        return scores
    
    def enhanced_classify_with_structure(self, book_data, content_sample, structure_info):
        """Enhanced classification using both content and structure"""
        
        # Calculate structure-based scores
        structure_scores = self.calculate_structure_based_genre_scores(structure_info)
        
        # Create structure context for the prompt
        structure_context = []
        if structure_info["has_toc"]:
            structure_context.append("Has table of contents")
        if structure_info["has_bibliography"]:
            structure_context.append("Has bibliography/references")
        if structure_info["has_index"]:
            structure_context.append("Has index")
        if structure_info["has_acknowledgments"]:
            structure_context.append("Has acknowledgments")
        if structure_info["academic_indicators"] > structure_info["fiction_indicators"]:
            structure_context.append("Academic/research language")
        elif structure_info["fiction_indicators"] > structure_info["academic_indicators"]:
            structure_context.append("Fictional narrative language")
        
        structure_text = "; ".join(structure_context) if structure_context else "Standard book structure"
        
        # Enhanced prompt with structure information
        prompt = f"""You are an expert book classifier analyzing both content and structure.

BOOK: "{book_data['title']}" by {book_data['author']}
CURRENT: {book_data['genre']}

STRUCTURAL ANALYSIS: {structure_text}

CONTENT SAMPLE:
{content_sample}

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Academic & Research, Religion & Spirituality, Political Science

CLASSIFICATION GUIDELINES:
1. Use BOTH content and structure for classification
2. Books with bibliography/index/TOC often indicate academic or non-fiction
3. Fiction books typically have narrative structure without academic apparatus
4. Structure should support, not override, content analysis

What is the most accurate genre based on both content and structure?

GENRE:"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Extract genre
                valid_genres = ["Romance", "Literary Fiction", "Science Fiction", "Fantasy",
                              "Mystery & Thriller", "Historical Fiction", "Contemporary Fiction",
                              "Self-Help", "Biography & Memoir", "Psychology", "Philosophy",
                              "Business & Economics", "History", "Science & Nature",
                              "Programming & Technology", "Academic & Research",
                              "Religion & Spirituality", "Political Science"]
                
                for genre in valid_genres:
                    if genre.lower() in classification.lower():
                        return genre, structure_scores.get(genre, 0.0)
                
                return classification, 0.0
            else:
                return None, 0.0
                
        except Exception as e:
            print(f"Classification error: {e}")
            return None, 0.0

def test_structure_enhanced_classification():
    """Test the structure-enhanced classification on a few books"""
    classifier = StructureEnhancedClassifier()
    db_config = get_database_config()
    conn = psycopg2.connect(**db_config, cursor_factory=RealDictCursor)
    
    try:
        with conn.cursor() as cur:
            # Get a few diverse books for testing
            cur.execute("""
                SELECT b.book_id, b.title, b.author, b.genre
                FROM books b
                WHERE EXISTS (
                    SELECT 1 FROM chunks c WHERE c.book_id = b.book_id
                )
                AND b.genre IN ('Literary Fiction', 'History', 'Biography & Memoir', 'Academic & Research')
                ORDER BY RANDOM()
                LIMIT 5
            """)
            
            books = cur.fetchall()
            
            print("🧪 TESTING STRUCTURE-ENHANCED CLASSIFICATION")
            print("=" * 60)
            
            for book in books:
                print(f"\n📚 Book: \"{book['title'][:50]}...\" by {book['author']}")
                print(f"🏷️  Current: {book['genre']}")
                
                # Analyze structure
                structure_info = classifier.analyze_book_structure(book['book_id'])
                print(f"📋 Structure: TOC={structure_info['has_toc']}, "
                      f"Intro={structure_info['has_introduction']}, "
                      f"Ack={structure_info['has_acknowledgments']}, "
                      f"Bib={structure_info['has_bibliography']}")
                
                # Get content sample (simplified)
                cur.execute("""
                    SELECT content FROM chunks 
                    WHERE book_id = %s AND content IS NOT NULL 
                    ORDER BY chunk_id LIMIT 3
                """, (book['book_id'],))
                chunks = cur.fetchall()
                content_sample = " ... ".join([chunk['content'][:200] for chunk in chunks])
                
                # Classify with structure enhancement
                new_genre, structure_score = classifier.enhanced_classify_with_structure(
                    book, content_sample, structure_info
                )
                
                print(f"🎯 Enhanced: {new_genre} (structure confidence: {structure_score:.2f})")
                print(f"{'✅ CHANGE' if new_genre != book['genre'] else '✅ CONFIRM'}")
                
    finally:
        conn.close()

if __name__ == '__main__':
    test_structure_enhanced_classification()