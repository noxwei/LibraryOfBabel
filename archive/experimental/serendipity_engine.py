#!/usr/bin/env python3
"""
🎲 Serendipity Engine for LibraryOfBabel
Generates unique insights by randomly sampling chunks across the library
and using AI to synthesize unexpected connections and conclusions
"""

import random
import logging
import psycopg2
import psycopg2.extras
from typing import List, Dict, Optional, Tuple
from vector_embeddings import VectorEmbeddingGenerator
import requests
import json
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SerendipityEngine:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
        
        self.vector_generator = VectorEmbeddingGenerator()
        
        # Ollama for insight synthesis
        self.ollama_url = "http://localhost:11434/api/generate"
        self.synthesis_model = "llama3.1:8b"  # Use smart model for insights
        
        # Insight generation parameters
        self.min_chunk_words = 100
        self.max_chunk_words = 2000
        self.insight_history = []
        
    def get_random_chunks(self, num_chunks: int = 4, seed_number: Optional[int] = None) -> List[Dict]:
        """Get random chunks from different books using a seed number"""
        if seed_number:
            random.seed(seed_number)
            logger.info(f"🎲 Using seed: {seed_number}")
        
        conn = psycopg2.connect(**self.db_config)
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get total chunk count for random selection
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE word_count >= %s AND word_count <= %s", 
                          (self.min_chunk_words, self.max_chunk_words))
            total_chunks = cursor.fetchone()['count']
            
            if total_chunks < num_chunks:
                logger.warning(f"Only {total_chunks} suitable chunks available")
                num_chunks = total_chunks
            
            # Generate random offsets
            random_offsets = random.sample(range(total_chunks), num_chunks)
            
            selected_chunks = []
            
            for offset in random_offsets:
                cursor.execute("""
                    SELECT 
                        c.chunk_id, c.content, c.chunk_type, c.chapter_number, c.word_count,
                        b.title, b.author, b.genre, b.publication_year
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.word_count >= %s AND c.word_count <= %s
                    ORDER BY c.chunk_id
                    LIMIT 1 OFFSET %s
                """, (self.min_chunk_words, self.max_chunk_words, offset))
                
                chunk = cursor.fetchone()
                if chunk:
                    selected_chunks.append(dict(chunk))
            
            # Ensure chunks are from different books
            unique_chunks = []
            seen_books = set()
            
            for chunk in selected_chunks:
                book_title = chunk['title']
                if book_title not in seen_books:
                    unique_chunks.append(chunk)
                    seen_books.add(book_title)
                
                if len(unique_chunks) >= num_chunks:
                    break
            
            # If we need more chunks from different books, try again
            if len(unique_chunks) < num_chunks:
                logger.info(f"Found {len(unique_chunks)} chunks from unique books, attempting to find more...")
                
                # Get chunks from remaining books
                remaining_books_query = """
                    SELECT DISTINCT b.title FROM books b 
                    WHERE b.title NOT IN %s
                """
                
                cursor.execute(remaining_books_query, (tuple(seen_books),))
                remaining_books = [row['title'] for row in cursor.fetchall()]
                
                for book_title in remaining_books:
                    if len(unique_chunks) >= num_chunks:
                        break
                    
                    cursor.execute("""
                        SELECT 
                            c.chunk_id, c.content, c.chunk_type, c.chapter_number, c.word_count,
                            b.title, b.author, b.genre, b.publication_year
                        FROM chunks c
                        JOIN books b ON c.book_id = b.book_id
                        WHERE b.title = %s 
                        AND c.word_count >= %s AND c.word_count <= %s
                        ORDER BY RANDOM()
                        LIMIT 1
                    """, (book_title, self.min_chunk_words, self.max_chunk_words))
                    
                    chunk = cursor.fetchone()
                    if chunk:
                        unique_chunks.append(dict(chunk))
            
            logger.info(f"📚 Selected {len(unique_chunks)} chunks from different books")
            return unique_chunks
            
        except Exception as e:
            logger.error(f"Error getting random chunks: {e}")
            return []
        finally:
            conn.close()
    
    def synthesize_insights(self, chunks: List[Dict], focus_theme: str = None) -> Dict:
        """Use AI to synthesize insights from random chunks"""
        if not chunks:
            return {"error": "No chunks provided for synthesis"}
        
        # Prepare context for AI
        chunk_summaries = []
        for i, chunk in enumerate(chunks, 1):
            summary = f"""
Passage {i}: "{chunk['title']}" by {chunk['author']} (Genre: {chunk.get('genre', 'Unknown')})
Chapter {chunk.get('chapter_number', 'Unknown')}, {chunk['word_count']} words
Content: {chunk['content'][:500]}...
            """
            chunk_summaries.append(summary.strip())
        
        # Create synthesis prompt
        theme_instruction = f" Focus on the theme of '{focus_theme}'." if focus_theme else ""
        
        synthesis_prompt = f"""You are a brilliant interdisciplinary scholar analyzing randomly selected passages from a personal library. Your task is to find unexpected connections and generate unique insights.

{chr(10).join(chunk_summaries)}

TASK: Analyze these {len(chunks)} passages and create a unique intellectual synthesis.{theme_instruction}

Generate:
1. **Unexpected Connection**: What surprising link exists between these seemingly unrelated passages?
2. **Emergent Pattern**: What deeper pattern or principle emerges when viewed together?
3. **Novel Insight**: What new understanding or hypothesis does this combination suggest?
4. **Practical Implication**: How might this insight apply to contemporary issues or understanding?

Be creative, intellectually rigorous, and look for connections that aren't obvious. This is serendipitous knowledge discovery!

Format your response as:
**Connection:** [brief description]
**Pattern:** [deeper principle]
**Insight:** [novel understanding]
**Implication:** [practical relevance]
"""
        
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.synthesis_model,
                    "prompt": synthesis_prompt,
                    "stream": False
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                synthesis = result.get('response', 'Failed to generate synthesis')
                
                return {
                    "synthesis_prompt": synthesis_prompt,
                    "ai_synthesis": synthesis,
                    "chunks_analyzed": len(chunks),
                    "books_involved": [f"{chunk['title']} by {chunk['author']}" for chunk in chunks],
                    "genres_mixed": list(set(chunk.get('genre', 'Unknown') for chunk in chunks)),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"Ollama synthesis failed: {response.status_code}")
                return {"error": f"AI synthesis failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return {"error": f"Synthesis error: {e}"}
    
    def generate_serendipitous_insight(self, seed_number: int = None, num_chunks: int = 4, focus_theme: str = None) -> Dict:
        """Generate a complete serendipitous insight from random chunks"""
        if seed_number is None:
            seed_number = random.randint(1, 999)
        
        logger.info(f"🎲 Generating serendipitous insight with seed {seed_number}")
        
        # Get random chunks
        chunks = self.get_random_chunks(num_chunks, seed_number)
        
        if not chunks:
            return {"error": "No suitable chunks found"}
        
        # Synthesize insights
        synthesis_result = self.synthesize_insights(chunks, focus_theme)
        
        # Add metadata
        insight = {
            "insight_id": f"serendipity_{seed_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "seed_number": seed_number,
            "source_chunks": chunks,
            "synthesis": synthesis_result,
            "discovery_metadata": {
                "total_words_analyzed": sum(chunk['word_count'] for chunk in chunks),
                "genres_combined": list(set(chunk.get('genre', 'Unknown') for chunk in chunks)),
                "authors_combined": list(set(chunk['author'] for chunk in chunks)),
                "time_span": self.calculate_time_span(chunks),
                "conceptual_diversity": len(set(chunk.get('genre', 'Unknown') for chunk in chunks))
            }
        }
        
        # Store in history
        self.insight_history.append(insight)
        
        return insight
    
    def calculate_time_span(self, chunks: List[Dict]) -> str:
        """Calculate the time span of publication years in chunks"""
        years = [chunk.get('publication_year') for chunk in chunks if chunk.get('publication_year')]
        if not years:
            return "Unknown time span"
        
        years = [int(year) for year in years if str(year).isdigit()]
        if not years:
            return "Unknown time span"
        
        min_year, max_year = min(years), max(years)
        if min_year == max_year:
            return f"Single year: {min_year}"
        else:
            return f"{max_year - min_year} year span ({min_year}-{max_year})"
    
    def generate_insight_series(self, num_insights: int = 5, focus_theme: str = None) -> List[Dict]:
        """Generate a series of serendipitous insights"""
        logger.info(f"🎲 Generating series of {num_insights} serendipitous insights")
        
        insights = []
        used_seeds = set()
        
        for i in range(num_insights):
            # Generate unique seed
            seed = random.randint(1, 999)
            while seed in used_seeds:
                seed = random.randint(1, 999)
            used_seeds.add(seed)
            
            insight = self.generate_serendipitous_insight(seed, focus_theme=focus_theme)
            if 'error' not in insight:
                insights.append(insight)
                logger.info(f"✅ Generated insight {i+1}/{num_insights} (seed: {seed})")
            else:
                logger.error(f"❌ Failed to generate insight {i+1}: {insight['error']}")
        
        return insights
    
    def explore_conceptual_space(self, anchor_concept: str, exploration_depth: int = 3) -> Dict:
        """Use serendipity to explore conceptual space around an anchor concept"""
        logger.info(f"🔍 Exploring conceptual space around '{anchor_concept}'")
        
        # Start with anchor concept search
        anchor_results = self.vector_generator.semantic_search(anchor_concept, limit=2, similarity_threshold=0.3)
        
        if not anchor_results:
            return {"error": f"No content found related to '{anchor_concept}'"}
        
        # Get random chunks for serendipitous connections
        random_chunks = self.get_random_chunks(exploration_depth)
        
        # Combine anchor chunks with random chunks
        all_chunks = []
        
        # Add anchor chunks
        for result in anchor_results:
            chunk_info = {
                'chunk_id': result.get('chunk_id', 'unknown'),
                'content': result.get('content_preview', ''),
                'title': result['title'],
                'author': result['author'],
                'genre': result.get('genre', 'Unknown'),
                'similarity_to_anchor': result['similarity_score']
            }
            all_chunks.append(chunk_info)
        
        # Add random chunks
        all_chunks.extend(random_chunks)
        
        # Synthesize with focus on anchor concept
        synthesis = self.synthesize_insights(all_chunks, focus_theme=anchor_concept)
        
        return {
            "anchor_concept": anchor_concept,
            "exploration_chunks": all_chunks,
            "synthesis": synthesis,
            "discovery_type": "conceptual_space_exploration",
            "timestamp": datetime.now().isoformat()
        }
    
    def find_library_hidden_gems(self, num_discoveries: int = 3) -> List[Dict]:
        """Find hidden gems by combining low-similarity chunks that might reveal unexpected insights"""
        logger.info(f"💎 Searching for {num_discoveries} hidden gems in the library")
        
        gems = []
        
        for i in range(num_discoveries):
            # Get chunks from very different genres/authors
            conn = psycopg2.connect(**self.db_config)
            
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                # Get chunks from maximally different contexts
                cursor.execute("""
                    SELECT 
                        c.chunk_id, c.content, c.chunk_type, c.chapter_number, c.word_count,
                        b.title, b.author, b.genre, b.publication_year
                    FROM chunks c
                    JOIN books b ON c.book_id = b.book_id
                    WHERE c.word_count >= %s AND c.word_count <= %s
                    ORDER BY RANDOM()
                    LIMIT 4
                """, (self.min_chunk_words, self.max_chunk_words))
                
                diverse_chunks = [dict(row) for row in cursor.fetchall()]
                
                if len(diverse_chunks) >= 3:
                    synthesis = self.synthesize_insights(diverse_chunks, focus_theme="hidden connections")
                    
                    gem = {
                        "gem_id": f"hidden_gem_{i+1}_{datetime.now().strftime('%H%M%S')}",
                        "discovery_method": "maximum_diversity_sampling",
                        "chunks": diverse_chunks,
                        "synthesis": synthesis,
                        "uniqueness_score": len(set(chunk['genre'] for chunk in diverse_chunks)),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    gems.append(gem)
                    logger.info(f"💎 Found hidden gem {i+1}: {len(diverse_chunks)} diverse chunks")
                
            except Exception as e:
                logger.error(f"Error finding hidden gem {i+1}: {e}")
            finally:
                conn.close()
        
        return gems
    
    def format_insight_report(self, insight: Dict) -> str:
        """Format insight for human consumption"""
        if 'error' in insight:
            return f"❌ Error: {insight['error']}"
        
        synthesis = insight['synthesis']
        metadata = insight.get('discovery_metadata', {})
        
        report = f"""
🎲 **SERENDIPITOUS INSIGHT #{insight['seed_number']}**
🕒 Generated: {insight.get('timestamp', 'Unknown')}

📚 **Source Material:**
   • {metadata.get('total_words_analyzed', 0):,} words analyzed
   • {len(insight['source_chunks'])} books: {', '.join(metadata.get('authors_combined', []))}
   • Genres: {', '.join(metadata.get('genres_combined', []))}
   • Time span: {metadata.get('time_span', 'Unknown')}
   • Conceptual diversity: {metadata.get('conceptual_diversity', 0)}/10

🧠 **AI SYNTHESIS:**
{synthesis.get('ai_synthesis', 'No synthesis available')}

🔬 **DISCOVERY METADATA:**
   • Insight ID: {insight['insight_id']}
   • Reproducible with seed: {insight['seed_number']}
        """
        
        return report


def main():
    """Main function for serendipity engine"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LibraryOfBabel Serendipity Engine")
    parser.add_argument("--insight", type=int, help="Generate insight with specific seed (1-999)")
    parser.add_argument("--series", type=int, default=3, help="Generate series of insights")
    parser.add_argument("--theme", type=str, help="Focus theme for insights")
    parser.add_argument("--explore", type=str, help="Explore conceptual space around concept")
    parser.add_argument("--gems", type=int, default=2, help="Find hidden gems")
    parser.add_argument("--chunks", type=int, default=4, help="Number of chunks per insight")
    
    args = parser.parse_args()
    
    engine = SerendipityEngine()
    
    if args.insight:
        if 1 <= args.insight <= 999:
            insight = engine.generate_serendipitous_insight(args.insight, args.chunks, args.theme)
            print(engine.format_insight_report(insight))
        else:
            print("❌ Seed number must be between 1 and 999")
    
    elif args.explore:
        exploration = engine.explore_conceptual_space(args.explore)
        if 'error' in exploration:
            print(f"❌ {exploration['error']}")
        else:
            print(f"🔍 **CONCEPTUAL EXPLORATION: {args.explore}**")
            print(f"Synthesis: {exploration['synthesis'].get('ai_synthesis', 'No synthesis')}")
    
    elif args.gems:
        gems = engine.find_library_hidden_gems(args.gems)
        for i, gem in enumerate(gems, 1):
            print(f"\n💎 **HIDDEN GEM #{i}**")
            print(f"Uniqueness Score: {gem['uniqueness_score']}/10")
            print(f"Synthesis: {gem['synthesis'].get('ai_synthesis', 'No synthesis')}")
    
    else:
        # Default: generate series
        insights = engine.generate_insight_series(args.series, args.theme)
        
        print(f"🎲 **SERENDIPITY SERIES: {len(insights)} INSIGHTS**")
        if args.theme:
            print(f"🎯 Theme: {args.theme}")
        
        for i, insight in enumerate(insights, 1):
            print(f"\n{'='*80}")
            print(engine.format_insight_report(insight))


if __name__ == "__main__":
    main()