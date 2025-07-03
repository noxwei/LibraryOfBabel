#!/usr/bin/env python3
"""
🤖 Enhanced Librarian Agent for LibraryOfBabel
Advanced AI agent with semantic search, genre analysis, and intelligent recommendations
"""

import os
import sys
import json
import logging
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from vector_embeddings import VectorEmbeddingGenerator
from genre_classifier import GenreClassifier
import psycopg2
import psycopg2.extras

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedLibrarianAgent:
    def __init__(self):
        self.vector_generator = VectorEmbeddingGenerator()
        self.genre_classifier = GenreClassifier()
        
        # Personality and responses
        self.personality = {
            "name": "Alexandria",
            "role": "AI Research Librarian",
            "style": "scholarly_enthusiastic",
            "expertise": ["cross-referencing", "semantic analysis", "philosophical connections"]
        }
        
        # Search memory for conversation context
        self.search_history = []
        self.conversation_context = []
        
    def greet_user(self) -> str:
        """Friendly greeting with library status"""
        stats = self.get_library_stats()
        
        greetings = [
            f"📚 Hello! I'm {self.personality['name']}, your AI research librarian.",
            f"🔍 Welcome to your personal LibraryOfBabel! I'm {self.personality['name']}.",
            f"✨ Greetings, knowledge seeker! {self.personality['name']} at your service.",
        ]
        
        greeting = random.choice(greetings)
        
        status = f"""
{greeting}

📊 **Your Library Status:**
   • {stats.get('total_books', 0)} books indexed
   • {stats.get('total_chunks', 0)} searchable chunks  
   • {stats.get('embedded_chunks', 0)} with semantic embeddings
   • {stats.get('classified_books', 0)} AI-classified genres

🎯 **What I can help you with:**
   • Semantic search across your entire library
   • Cross-genre philosophical connections
   • Author relationship mapping
   • Personalized reading recommendations
   • Deep concept exploration

Ask me anything like:
   "Find books connecting consciousness and technology"
   "What does Foucault say about power?"
   "Recommend something philosophical but accessible"
   "Show me the intersection of science fiction and philosophy"

How can I assist your research today? 🤔
        """
        
        return status
    
    def get_library_stats(self) -> Dict:
        """Get comprehensive library statistics"""
        try:
            conn = psycopg2.connect(**self.vector_generator.db_config)
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("SELECT COUNT(*) FROM books")
            total_books = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chunks")
            total_chunks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding_array IS NOT NULL")
            embedded_chunks = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM books WHERE genre IS NOT NULL")
            classified_books = cursor.fetchone()[0]
            
            # Genre distribution
            cursor.execute("""
                SELECT genre, COUNT(*) as count 
                FROM books 
                WHERE genre IS NOT NULL 
                GROUP BY genre 
                ORDER BY count DESC
            """)
            genres = cursor.fetchall()
            
            return {
                "total_books": total_books,
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "classified_books": classified_books,
                "genre_distribution": dict(genres),
                "embedding_completion": round((embedded_chunks / max(total_chunks, 1)) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting library stats: {e}")
            return {}
        finally:
            if 'conn' in locals():
                conn.close()
    
    def semantic_search_with_analysis(self, query: str, limit: int = 8) -> Dict:
        """Enhanced semantic search with intelligent analysis"""
        logger.info(f"🔍 Semantic search: '{query}'")
        
        # Perform semantic search
        results = self.vector_generator.semantic_search(query, limit=limit, similarity_threshold=0.2)
        
        if not results:
            return {
                "query": query,
                "results": [],
                "analysis": "No relevant passages found. Try rephrasing your query or using broader terms.",
                "suggestions": self.generate_search_suggestions()
            }
        
        # Analyze results for patterns
        analysis = self.analyze_search_results(query, results)
        
        # Generate follow-up suggestions
        suggestions = self.generate_contextual_suggestions(query, results)
        
        return {
            "query": query,
            "results": results,
            "analysis": analysis,
            "suggestions": suggestions,
            "search_metadata": {
                "total_results": len(results),
                "avg_similarity": round(sum(r['similarity_score'] for r in results) / len(results), 3),
                "genres_found": list(set(r.get('genre', 'Unknown') for r in results if r.get('genre'))),
                "authors_found": list(set(r['author'] for r in results if r.get('author')))
            }
        }
    
    def analyze_search_results(self, query: str, results: List[Dict]) -> str:
        """Intelligent analysis of search results"""
        if not results:
            return "No results to analyze."
        
        # Extract patterns
        authors = [r['author'] for r in results if r.get('author')]
        genres = [r.get('genre', 'Unknown') for r in results if r.get('genre')]
        similarities = [r['similarity_score'] for r in results]
        
        author_counts = {}
        for author in authors:
            author_counts[author] = author_counts.get(author, 0) + 1
        
        genre_counts = {}
        for genre in genres:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Generate analysis
        analysis_parts = []
        
        # Similarity analysis
        avg_similarity = sum(similarities) / len(similarities)
        if avg_similarity > 0.6:
            analysis_parts.append(f"🎯 **Strong thematic match** (avg similarity: {avg_similarity:.3f})")
        elif avg_similarity > 0.4:
            analysis_parts.append(f"📚 **Good conceptual relevance** (avg similarity: {avg_similarity:.3f})")
        else:
            analysis_parts.append(f"🔍 **Broad thematic connections** (avg similarity: {avg_similarity:.3f})")
        
        # Author patterns
        if len(set(authors)) < len(authors):
            top_author = max(author_counts, key=author_counts.get)
            analysis_parts.append(f"✍️ **{top_author}** appears multiple times - strong relevance to your query")
        
        # Genre patterns
        if genres:
            top_genre = max(genre_counts, key=genre_counts.get)
            if genre_counts[top_genre] > 1:
                analysis_parts.append(f"📖 **{top_genre}** genre shows strong connection to this topic")
        
        # Cross-genre insights
        unique_genres = set(genres)
        if len(unique_genres) > 2:
            analysis_parts.append(f"🌐 **Cross-disciplinary relevance** spanning {', '.join(unique_genres)}")
        
        return " • ".join(analysis_parts)
    
    def generate_contextual_suggestions(self, original_query: str, results: List[Dict]) -> List[str]:
        """Generate intelligent follow-up suggestions based on results"""
        if not results:
            return self.generate_search_suggestions()
        
        suggestions = []
        
        # Author-based suggestions
        authors = list(set(r['author'] for r in results[:3] if r.get('author')))
        for author in authors[:2]:
            suggestions.append(f"More works by {author}")
        
        # Genre-based suggestions
        genres = list(set(r.get('genre', '') for r in results if r.get('genre')))
        for genre in genres[:2]:
            if genre != 'Unknown':
                suggestions.append(f"Explore {genre} concepts")
        
        # Conceptual suggestions based on content
        key_terms = self.extract_key_terms_from_results(results)
        for term in key_terms[:2]:
            if term.lower() not in original_query.lower():
                suggestions.append(f"'{term}' in philosophical context")
        
        # Cross-reference suggestions
        if len(set(r['author'] for r in results)) > 1:
            author1, author2 = list(set(r['author'] for r in results))[:2]
            suggestions.append(f"Compare {author1} and {author2} perspectives")
        
        return suggestions[:5]
    
    def extract_key_terms_from_results(self, results: List[Dict]) -> List[str]:
        """Extract important terms from search results"""
        # Simple keyword extraction from titles and content previews
        important_terms = []
        
        for result in results[:3]:
            title = result.get('title', '')
            content = result.get('content_preview', '')
            
            # Extract philosophical/academic terms (simplified)
            terms = ['consciousness', 'reality', 'power', 'identity', 'freedom', 'ethics', 
                    'society', 'culture', 'knowledge', 'truth', 'existence', 'human',
                    'technology', 'future', 'artificial', 'intelligence', 'mind']
            
            for term in terms:
                if term in title.lower() or term in content.lower():
                    if term not in important_terms:
                        important_terms.append(term)
        
        return important_terms
    
    def generate_search_suggestions(self) -> List[str]:
        """Generate general search suggestions"""
        return [
            "consciousness and artificial intelligence",
            "power dynamics in society", 
            "identity formation and culture",
            "technology's impact on humanity",
            "philosophical approaches to reality",
            "ethics in modern life"
        ]
    
    def find_philosophical_connections(self, concept1: str, concept2: str) -> Dict:
        """Find books that connect two philosophical concepts"""
        logger.info(f"🔗 Finding connections between '{concept1}' and '{concept2}'")
        
        # Search for books containing both concepts
        combined_query = f"{concept1} {concept2}"
        results = self.vector_generator.semantic_search(combined_query, limit=5, similarity_threshold=0.3)
        
        # Also try individual searches for broader context
        results1 = self.vector_generator.semantic_search(concept1, limit=3, similarity_threshold=0.4)
        results2 = self.vector_generator.semantic_search(concept2, limit=3, similarity_threshold=0.4)
        
        analysis = f"""
🔗 **Philosophical Connection Analysis: {concept1} ↔ {concept2}**

**Direct Connections:** {len(results)} passages discuss both concepts
**{concept1} Context:** Found in {len(results1)} relevant passages  
**{concept2} Context:** Found in {len(results2)} relevant passages

**Synthesis Opportunity:** {"High" if len(results) > 2 else "Moderate" if len(results) > 0 else "Requires deeper exploration"}
        """
        
        return {
            "concept1": concept1,
            "concept2": concept2,
            "direct_connections": results,
            "concept1_context": results1,
            "concept2_context": results2,
            "analysis": analysis
        }
    
    def recommend_reading_path(self, starting_interest: str, depth_level: str = "medium") -> Dict:
        """Generate a personalized reading path through the library"""
        logger.info(f"📖 Generating reading path for '{starting_interest}' (depth: {depth_level})")
        
        # Find initial books on the topic
        initial_results = self.vector_generator.semantic_search(starting_interest, limit=10, similarity_threshold=0.3)
        
        if not initial_results:
            return {
                "error": f"No books found related to '{starting_interest}'. Try a broader search term."
            }
        
        # Categorize by difficulty/accessibility
        foundational = []
        intermediate = []
        advanced = []
        
        for result in initial_results:
            genre = result.get('genre', '')
            similarity = result['similarity_score']
            
            if genre in ['Biography/Memoir', 'Literary Fiction'] or similarity > 0.6:
                foundational.append(result)
            elif genre in ['Philosophy', 'Politics/Social Science'] and similarity > 0.5:
                intermediate.append(result)
            else:
                advanced.append(result)
        
        # Create reading path based on depth level
        if depth_level == "light":
            path = foundational[:3]
            description = "Accessible introduction through narrative and personal perspectives"
        elif depth_level == "deep":
            path = foundational[:1] + intermediate[:2] + advanced[:2]
            description = "Comprehensive exploration from accessible to scholarly perspectives"
        else:  # medium
            path = foundational[:2] + intermediate[:2]
            description = "Balanced exploration with accessible and analytical perspectives"
        
        return {
            "starting_interest": starting_interest,
            "depth_level": depth_level,
            "reading_path": path,
            "description": description,
            "estimated_reading_time": f"{len(path) * 2}-{len(path) * 4} weeks",
            "next_suggestions": self.generate_contextual_suggestions(starting_interest, path)
        }
    
    def analyze_author_relationships(self, author_name: str) -> Dict:
        """Analyze an author's work and find related authors in the library"""
        logger.info(f"👤 Analyzing author relationships for '{author_name}'")
        
        # Find all works by this author
        try:
            conn = psycopg2.connect(**self.vector_generator.db_config)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cursor.execute("""
                SELECT b.title, b.genre, b.word_count, b.genre_confidence,
                       COUNT(c.chunk_id) as chunk_count
                FROM books b
                LEFT JOIN chunks c ON b.book_id = c.book_id
                WHERE b.author ILIKE %s
                GROUP BY b.book_id, b.title, b.genre, b.word_count, b.genre_confidence
                ORDER BY b.title
            """, (f'%{author_name}%',))
            
            author_books = [dict(row) for row in cursor.fetchall()]
            
            if not author_books:
                return {"error": f"No books found by '{author_name}' in your library."}
            
            # Get a sample of the author's content for similarity search
            cursor.execute("""
                SELECT content FROM chunks c
                JOIN books b ON c.book_id = b.book_id
                WHERE b.author ILIKE %s
                ORDER BY c.chunk_id
                LIMIT 3
            """, (f'%{author_name}%',))
            
            content_samples = [row['content'] for row in cursor.fetchall()]
            combined_content = " ".join(content_samples)[:5000]  # Limit length
            
        except Exception as e:
            logger.error(f"Error analyzing author: {e}")
            return {"error": f"Database error analyzing '{author_name}'"}
        finally:
            if 'conn' in locals():
                conn.close()
        
        # Find conceptually similar authors
        if combined_content:
            similar_results = self.vector_generator.semantic_search(combined_content, limit=10, similarity_threshold=0.3)
            
            # Extract other authors from results
            related_authors = {}
            for result in similar_results:
                other_author = result['author']
                if other_author and author_name.lower() not in other_author.lower():
                    if other_author in related_authors:
                        related_authors[other_author] += result['similarity_score']
                    else:
                        related_authors[other_author] = result['similarity_score']
            
            # Sort by conceptual similarity
            top_related = sorted(related_authors.items(), key=lambda x: x[1], reverse=True)[:5]
        else:
            top_related = []
        
        # Analyze author's themes
        genres = [book['genre'] for book in author_books if book['genre']]
        primary_genre = max(set(genres), key=genres.count) if genres else "Unknown"
        
        total_words = sum(book['word_count'] or 0 for book in author_books)
        avg_confidence = sum(book['genre_confidence'] or 0 for book in author_books) / len(author_books)
        
        return {
            "author": author_name,
            "books_in_library": len(author_books),
            "total_words": total_words,
            "primary_genre": primary_genre,
            "classification_confidence": round(avg_confidence, 3),
            "book_details": author_books,
            "conceptually_related_authors": top_related,
            "analysis": f"{author_name} appears to focus on {primary_genre} themes with {len(author_books)} works totaling {total_words:,} words in your library."
        }
    
    def interactive_session(self):
        """Start an interactive librarian session"""
        print(self.greet_user())
        
        while True:
            try:
                print("\n" + "="*80)
                user_input = input("\n🤔 What would you like to explore? (or 'quit' to exit): ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print(f"\n📚 Thank you for using LibraryOfBabel! Happy reading! - {self.personality['name']}")
                    break
                
                if not user_input:
                    continue
                
                # Parse intent and respond appropriately
                response = self.process_user_query(user_input)
                print(f"\n{response}")
                
            except KeyboardInterrupt:
                print(f"\n\n👋 Goodbye! - {self.personality['name']}")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.error(f"Interactive session error: {e}")
    
    def process_user_query(self, query: str) -> str:
        """Process and respond to user queries intelligently"""
        query_lower = query.lower()
        
        # Simple intent detection
        if any(word in query_lower for word in ['recommend', 'suggest', 'should read']):
            result = self.recommend_reading_path(query)
            return self.format_reading_path_response(result)
        
        elif any(word in query_lower for word in ['connect', 'connection', 'relationship']):
            # Extract concepts for connection analysis
            words = query.split()
            concepts = [w for w in words if len(w) > 3 and w.lower() not in ['connect', 'connection', 'between', 'and', 'the']]
            if len(concepts) >= 2:
                result = self.find_philosophical_connections(concepts[0], concepts[1])
                return self.format_connection_response(result)
        
        elif any(word in query_lower for word in ['author', 'who is', 'wrote']):
            # Extract author name
            words = query.split()
            potential_author = " ".join(words[-2:])  # Simple extraction
            result = self.analyze_author_relationships(potential_author)
            return self.format_author_response(result)
        
        # Default to semantic search
        result = self.semantic_search_with_analysis(query)
        return self.format_search_response(result)
    
    def format_search_response(self, result: Dict) -> str:
        """Format semantic search results for display"""
        if not result['results']:
            return f"❌ {result['analysis']}\n\n💡 Try: {', '.join(result['suggestions'][:3])}"
        
        response = f"🔍 **Search Results for:** {result['query']}\n\n"
        response += f"📊 {result['analysis']}\n\n"
        
        for i, res in enumerate(result['results'][:5], 1):
            response += f"**{i}. {res['title']}** by {res['author']}\n"
            response += f"   📖 Genre: {res.get('genre', 'Unknown')} | Similarity: {res['similarity_score']:.3f}\n"
            response += f"   💭 {res['content_preview'][:200]}...\n\n"
        
        if result['suggestions']:
            response += f"🎯 **Related Searches:** {', '.join(result['suggestions'][:3])}"
        
        return response
    
    def format_connection_response(self, result: Dict) -> str:
        """Format philosophical connection results"""
        if 'error' in result:
            return f"❌ {result['error']}"
        
        response = f"🔗 **Philosophical Connections: {result['concept1']} ↔ {result['concept2']}**\n\n"
        response += result['analysis'] + "\n\n"
        
        if result['direct_connections']:
            response += "📚 **Books exploring both concepts:**\n"
            for res in result['direct_connections'][:3]:
                response += f"• **{res['title']}** by {res['author']} (similarity: {res['similarity_score']:.3f})\n"
        
        return response
    
    def format_reading_path_response(self, result: Dict) -> str:
        """Format reading path recommendations"""
        if 'error' in result:
            return f"❌ {result['error']}"
        
        response = f"📖 **Reading Path: {result['starting_interest']}**\n\n"
        response += f"🎯 {result['description']}\n"
        response += f"⏱️ Estimated time: {result['estimated_reading_time']}\n\n"
        
        for i, book in enumerate(result['reading_path'], 1):
            response += f"**{i}. {book['title']}** by {book['author']}\n"
            response += f"   📊 Relevance: {book['similarity_score']:.3f} | Genre: {book.get('genre', 'Unknown')}\n\n"
        
        return response
    
    def format_author_response(self, result: Dict) -> str:
        """Format author analysis results"""
        if 'error' in result:
            return f"❌ {result['error']}"
        
        response = f"👤 **Author Analysis: {result['author']}**\n\n"
        response += f"📚 {result['books_in_library']} books ({result['total_words']:,} words)\n"
        response += f"🏷️ Primary genre: {result['primary_genre']}\n"
        response += f"🎯 Classification confidence: {result['classification_confidence']}\n\n"
        
        if result['conceptually_related_authors']:
            response += "🔗 **Conceptually similar authors in your library:**\n"
            for author, similarity in result['conceptually_related_authors'][:3]:
                response += f"• {author} (similarity: {similarity:.3f})\n"
        
        return response


def main():
    """Main function for enhanced librarian agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced LibraryOfBabel Librarian Agent")
    parser.add_argument("--interactive", action="store_true", help="Start interactive session")
    parser.add_argument("--search", type=str, help="Perform semantic search")
    parser.add_argument("--connect", nargs=2, metavar=('CONCEPT1', 'CONCEPT2'), help="Find philosophical connections")
    parser.add_argument("--author", type=str, help="Analyze author relationships")
    parser.add_argument("--recommend", type=str, help="Get reading recommendations")
    parser.add_argument("--depth", choices=['light', 'medium', 'deep'], default='medium', help="Reading depth level")
    
    args = parser.parse_args()
    
    librarian = EnhancedLibrarianAgent()
    
    if args.interactive:
        librarian.interactive_session()
    elif args.search:
        result = librarian.semantic_search_with_analysis(args.search)
        print(librarian.format_search_response(result))
    elif args.connect:
        result = librarian.find_philosophical_connections(args.connect[0], args.connect[1])
        print(librarian.format_connection_response(result))
    elif args.author:
        result = librarian.analyze_author_relationships(args.author)
        print(librarian.format_author_response(result))
    elif args.recommend:
        result = librarian.recommend_reading_path(args.recommend, args.depth)
        print(librarian.format_reading_path_response(result))
    else:
        print(librarian.greet_user())


if __name__ == "__main__":
    main()