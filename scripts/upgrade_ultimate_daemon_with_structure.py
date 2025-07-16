#!/usr/bin/env python3
"""
Upgrade Ultimate Daemon with Structure Intelligence
==================================================
Integrate book structure analysis into the ultimate classification daemon
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def upgrade_daemon_with_structure():
    """Add structure intelligence to the ultimate daemon"""
    
    daemon_file = project_root / "daemons" / "ultimate_library_reclassification_daemon.py"
    
    # Read current daemon
    with open(daemon_file, 'r') as f:
        daemon_code = f.read()
    
    # Structure analysis method to insert
    structure_method = '''
    def analyze_book_structure_intelligence(self, book_id):
        """Advanced structure analysis for enhanced classification"""
        conn = psycopg2.connect(**self.db_config, cursor_factory=RealDictCursor)
        
        try:
            with conn.cursor() as cur:
                # Get first 6 chunks for structure analysis (front matter + early content)
                cur.execute("""
                    SELECT content, chunk_id
                    FROM chunks
                    WHERE book_id = %s
                    AND content IS NOT NULL
                    ORDER BY chunk_id
                    LIMIT 6
                """, (book_id,))
                
                chunks = cur.fetchall()
                
                structure_intelligence = {
                    "academic_score": 0.0,
                    "fiction_score": 0.0,
                    "genre_hints": [],
                    "confidence_boost": 0.0
                }
                
                for chunk in chunks:
                    content_lower = chunk['content'].lower()
                    
                    # Academic indicators (increase confidence for non-fiction)
                    academic_indicators = [
                        'bibliography', 'references', 'index', 'table of contents', 
                        'research', 'study', 'analysis', 'methodology', 'hypothesis',
                        'citations', 'notes', 'appendix', 'works cited'
                    ]
                    
                    academic_count = sum(1 for indicator in academic_indicators if indicator in content_lower)
                    structure_intelligence["academic_score"] += academic_count * 0.1
                    
                    # Fiction indicators (increase confidence for fiction)
                    fiction_indicators = [
                        'chapter', 'character', 'dialogue', 'protagonist', 'plot',
                        'story', 'narrative', 'novel', 'fiction', 'characters'
                    ]
                    
                    fiction_count = sum(1 for indicator in fiction_indicators if indicator in content_lower)
                    structure_intelligence["fiction_score"] += fiction_count * 0.05
                    
                    # Specific genre hints
                    if any(word in content_lower for word in ['biography', 'memoir', 'life story', 'autobiography']):
                        structure_intelligence["genre_hints"].append("Biography & Memoir")
                    
                    if any(word in content_lower for word in ['history', 'historical', 'century', 'timeline']):
                        structure_intelligence["genre_hints"].append("History")
                    
                    if any(word in content_lower for word in ['psychology', 'psychological', 'therapy', 'mental']):
                        structure_intelligence["genre_hints"].append("Psychology")
                    
                    if any(word in content_lower for word in ['philosophy', 'philosophical', 'theory', 'ethics']):
                        structure_intelligence["genre_hints"].append("Philosophy")
                    
                    if any(word in content_lower for word in ['business', 'economics', 'market', 'finance']):
                        structure_intelligence["genre_hints"].append("Business & Economics")
                    
                    if any(word in content_lower for word in ['science fiction', 'sci-fi', 'future', 'technology', 'space']):
                        structure_intelligence["genre_hints"].append("Science Fiction")
                    
                    if any(word in content_lower for word in ['fantasy', 'magic', 'magical', 'dragon', 'wizard']):
                        structure_intelligence["genre_hints"].append("Fantasy")
                
                # Calculate confidence boost based on structural clarity
                if structure_intelligence["academic_score"] > 0.3:
                    structure_intelligence["confidence_boost"] = 0.2
                elif structure_intelligence["fiction_score"] > 0.3:
                    structure_intelligence["confidence_boost"] = 0.15
                
                return structure_intelligence
                
        finally:
            conn.close()
'''

    # Enhanced classification method
    enhanced_classify_method = '''
    def classify_with_structure_intelligence(self, book_data, content, structure_intel):
        """Classification enhanced with structural intelligence"""
        
        # Build structure context
        structure_context = ""
        if structure_intel["academic_score"] > 0.2:
            structure_context = "STRUCTURE: Academic/research book with bibliography, references, or scholarly apparatus. "
        elif structure_intel["fiction_score"] > 0.2:
            structure_context = "STRUCTURE: Narrative fiction with chapters and story elements. "
        
        if structure_intel["genre_hints"]:
            most_common_hint = max(set(structure_intel["genre_hints"]), key=structure_intel["genre_hints"].count)
            structure_context += f"STRONG STRUCTURAL INDICATOR: {most_common_hint}. "
        
        prompt = f"""You are an expert book classifier using both content and structural analysis.

BOOK: "{book_data['title']}" by {book_data['author']}
CURRENT: {book_data['genre']}

{structure_context}

CONTENT SAMPLE:
{content}

AVAILABLE GENRES:
Romance, Literary Fiction, Science Fiction, Fantasy, Mystery & Thriller, Historical Fiction, Contemporary Fiction, Self-Help, Biography & Memoir, Psychology, Philosophy, Business & Economics, History, Science & Nature, Programming & Technology, Academic & Research, Religion & Spirituality, Political Science

ENHANCED CLASSIFICATION RULES:
1. Use BOTH content and structural indicators for maximum accuracy
2. Academic structure (bibliography, index, references) strongly suggests non-fiction
3. Chapter-based narrative structure suggests fiction genres
4. Respect structural hints but prioritize actual content
5. Choose the most specific and accurate genre

Based on both content analysis and structural intelligence, what is the correct genre?

GENRE:"""

        try:
            start_time = time.time()
            
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.05, "top_p": 0.9}
                },
                timeout=25
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                classification = result['response'].strip()
                
                # Enhanced genre extraction with structure confidence
                classification_lines = [line.strip() for line in classification.split('\\n') if line.strip()]
                
                for line in classification_lines:
                    for genre in self.valid_genres:
                        if genre.lower() == line.lower() or genre.lower() in line.lower():
                            # Apply structure confidence boost
                            confidence = 1.0 + structure_intel["confidence_boost"]
                            return genre, duration, confidence
                
                # Fallback
                if classification_lines:
                    return classification_lines[0], duration, 1.0
                
                return classification, duration, 1.0
            else:
                return None, duration, 0.0
                
        except Exception as e:
            self.logger.error(f"Enhanced classification error: {e}")
            return None, 25, 0.0
'''

    # Update the process_book method
    updated_process_book = '''
    def process_book(self, book):
        """Process a single book with structure intelligence"""
        try:
            self.logger.info(f"📚 Processing: \\"{book['title'][:50]}...\\" by {book['author']}")
            
            # Get structure intelligence
            structure_intel = self.analyze_book_structure_intelligence(book['book_id'])
            
            # Get optimized content
            content = self.get_optimized_content_sample(book['book_id'])
            if not content or len(content) < 80:
                self.logger.warning(f"❌ Insufficient content for {book['title']}")
                return "insufficient_content"
            
            # Classify with structure intelligence
            new_genre, duration, confidence = self.classify_with_structure_intelligence(book, content, structure_intel)
            if not new_genre:
                self.logger.warning(f"❌ Classification failed for {book['title']}")
                return "classification_failed"
            
            confidence_indicator = "🔥" if confidence > 1.1 else "🎯"
            self.logger.info(f"{confidence_indicator} Classification: {new_genre} ({duration:.1f}s, confidence: {confidence:.2f})")
            
            # Log structure insights
            if structure_intel["genre_hints"]:
                hints = list(set(structure_intel["genre_hints"]))[:2]
                self.logger.info(f"📋 Structure hints: {', '.join(hints)}")
            
            # Update if different
            if new_genre != book['genre']:
                if new_genre in self.valid_genres:
                    if self.update_book_genre(book['book_id'], new_genre):
                        self.logger.info(f"✅ UPDATED: {book['genre']} → {new_genre}")
                        
                        # Track changes
                        old_genre = book['genre']
                        if old_genre not in self.state['genre_changes']:
                            self.state['genre_changes'][old_genre] = {}
                        if new_genre not in self.state['genre_changes'][old_genre]:
                            self.state['genre_changes'][old_genre][new_genre] = 0
                        self.state['genre_changes'][old_genre][new_genre] += 1
                        
                        return "reclassified"
                    else:
                        return "update_failed"
                else:
                    self.logger.warning(f"⚠️  Invalid genre returned: {new_genre}")
                    return "invalid_genre"
            else:
                self.logger.info(f"✅ CONFIRMED: {new_genre}")
                return "confirmed"
                
        except Exception as e:
            self.logger.error(f"💥 Error processing {book['title']}: {e}")
            return "error"
'''

    # Check if we need to insert the methods
    if "analyze_book_structure_intelligence" not in daemon_code:
        # Find insertion point after get_optimized_content_sample method
        insertion_point = daemon_code.find("def classify_with_llama_optimized(self, book_data, content):")
        
        if insertion_point != -1:
            # Insert structure intelligence methods
            updated_code = (daemon_code[:insertion_point] + 
                          structure_method + "\n" +
                          enhanced_classify_method + "\n" +
                          daemon_code[insertion_point:])
            
            # Replace the process_book method
            old_process_start = updated_code.find("def process_book(self, book):")
            old_process_end = updated_code.find("def run(self):", old_process_start)
            
            if old_process_start != -1 and old_process_end != -1:
                updated_code = (updated_code[:old_process_start] + 
                              updated_process_book + "\n" +
                              updated_code[old_process_end:])
                
                # Write the upgraded daemon
                with open(daemon_file, 'w') as f:
                    f.write(updated_code)
                
                print("✅ Ultimate daemon upgraded with structure intelligence!")
                print("🔥 New features:")
                print("   • Academic vs fiction structure detection")
                print("   • Genre-specific structural hints")
                print("   • Confidence boosting based on structure clarity")
                print("   • Enhanced logging with structure insights")
                return True
            else:
                print("❌ Could not locate process_book method for replacement")
                return False
        else:
            print("❌ Could not find insertion point in daemon code")
            return False
    else:
        print("✅ Daemon already has structure intelligence!")
        return True

if __name__ == '__main__':
    print("🚀 UPGRADING ULTIMATE DAEMON WITH STRUCTURE INTELLIGENCE")
    print("=" * 60)
    
    success = upgrade_daemon_with_structure()
    
    if success:
        print("\n🎯 Your book structure analysis reports have been integrated!")
        print("📊 Expected improvements:")
        print("   • 60-80% front matter detection → better content selection")
        print("   • Academic structure recognition → accurate non-fiction classification")
        print("   • Fiction narrative detection → precise fiction genre assignment")
        print("   • Genre-specific hints → enhanced accuracy")
        print("\n⚡ Restart the ultimate daemon to activate enhanced classification!")
    else:
        print("\n❌ Upgrade failed. Manual integration may be required.")