#!/usr/bin/env python3
"""
Seed-Based Random Question Generator for LibraryOfBabel
Generates philosophical, analytical, and cross-domain questions using deterministic seeds
"""

import random
import psycopg2
import psycopg2.extras
import requests
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"

class SeedQuestionGenerator:
    def __init__(self):
        self.question_templates = {
            'philosophical': [
                "What is the relationship between {concept1} and {concept2} according to {author}?",
                "How does {author}'s perspective on {concept1} challenge conventional understanding?",
                "What would {author1} say about {author2}'s theory of {concept1}?",
                "How does the concept of {concept1} evolve from {book1} to {book2}?",
                "What are the implications of {concept1} for understanding {concept2}?",
                "How does {author} reconcile the tension between {concept1} and {concept2}?",
                "What would a conversation between {author1} and {author2} about {concept1} reveal?",
                "How does {concept1} manifest differently in {genre1} versus {genre2} literature?",
            ],
            'analytical': [
                "Compare and contrast how {author1} and {author2} approach {concept1}.",
                "What evidence does {author} provide for the claim that {concept1} influences {concept2}?",
                "How does the historical context of {book1} shape its treatment of {concept1}?",
                "What are the strengths and weaknesses of {author}'s argument about {concept1}?",
                "How does {author} use {concept1} to critique {concept2}?",
                "What assumptions underlie {author}'s discussion of {concept1}?",
                "How does {book1}'s portrayal of {concept1} reflect broader cultural attitudes?",
                "What would be the counterarguments to {author}'s position on {concept1}?",
            ],
            'synthetic': [
                "How might we synthesize {author1}'s {concept1} with {author2}'s {concept2}?",
                "What new insights emerge when we combine {book1}'s approach to {concept1} with {book2}'s perspective on {concept2}?",
                "How could {concept1} from {genre1} inform our understanding of {concept2} in {genre2}?",
                "What would a unified theory of {concept1} and {concept2} look like across these texts?",
                "How do patterns of {concept1} across multiple authors suggest new ways of thinking about {concept2}?",
                "What emerges when we read {concept1} through the lens of {concept2} across different works?",
                "How might {author}'s method for analyzing {concept1} be applied to understanding {concept2}?",
                "What would happen if we applied {book1}'s framework of {concept1} to {book2}'s treatment of {concept2}?",
            ],
            'exploratory': [
                "What questions does {author}'s treatment of {concept1} leave unanswered?",
                "How might {concept1} be relevant to contemporary issues not discussed in {book1}?",
                "What would {author} think about modern developments related to {concept1}?",
                "How does {concept1} in {book1} anticipate or contradict later thinking about {concept2}?",
                "What are the unexamined assumptions in how {author} discusses {concept1}?",
                "How might studying {concept1} across these works change how we approach {concept2}?",
                "What would a feminist/decolonial/ecological reading of {concept1} in {book1} reveal?",
                "How does the absence of discussion about {concept1} in {book2} tell us something significant?",
            ]
        }
        
        self.concept_pools = {
            'philosophical': [
                'consciousness', 'freedom', 'power', 'knowledge', 'identity', 'reality', 'truth', 'existence',
                'being', 'becoming', 'time', 'space', 'infinity', 'finitude', 'meaning', 'purpose',
                'ethics', 'morality', 'justice', 'responsibility', 'authenticity', 'alienation',
                'transcendence', 'immanence', 'subjectivity', 'objectivity', 'intersubjectivity',
                'language', 'communication', 'interpretation', 'understanding', 'experience',
                'perception', 'memory', 'imagination', 'desire', 'will', 'emotion', 'reason'
            ],
            'social': [
                'society', 'community', 'culture', 'tradition', 'modernity', 'postmodernity',
                'capitalism', 'socialism', 'democracy', 'authoritarianism', 'governance', 'sovereignty',
                'class', 'race', 'gender', 'sexuality', 'intersectionality', 'privilege', 'oppression',
                'resistance', 'revolution', 'reform', 'ideology', 'hegemony', 'discourse',
                'institutions', 'bureaucracy', 'technology', 'digitalization', 'globalization',
                'nationalism', 'cosmopolitanism', 'citizenship', 'rights', 'law', 'order'
            ],
            'scientific': [
                'evolution', 'genetics', 'consciousness', 'intelligence', 'artificial intelligence',
                'complexity', 'emergence', 'systems', 'information', 'entropy', 'chaos',
                'determinism', 'randomness', 'probability', 'causation', 'correlation',
                'reduction', 'holism', 'mechanism', 'vitalism', 'materialism', 'naturalism',
                'experimentation', 'observation', 'theory', 'hypothesis', 'paradigm',
                'scientific revolution', 'normal science', 'anomaly', 'crisis'
            ],
            'literary': [
                'narrative', 'character', 'plot', 'setting', 'theme', 'symbol', 'metaphor',
                'irony', 'tragedy', 'comedy', 'romance', 'epic', 'bildungsroman',
                'stream of consciousness', 'modernism', 'postmodernism', 'realism', 'surrealism',
                'allegory', 'satire', 'parody', 'intertextuality', 'metafiction',
                'voice', 'perspective', 'focalization', 'reliability', 'unreliability',
                'genre', 'form', 'style', 'tone', 'mood', 'atmosphere'
            ]
        }
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def get_random_content_by_seed(self, seed: int, content_type: str = 'all') -> Dict:
        """Get random content from database using seed for reproducibility"""
        random.seed(seed)
        
        conn = self.get_db_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            if content_type == 'authors':
                cursor.execute("SELECT DISTINCT author FROM books WHERE author IS NOT NULL")
                authors = [row['author'] for row in cursor.fetchall()]
                return {'authors': random.sample(authors, min(3, len(authors)))}
            
            elif content_type == 'books':
                cursor.execute("SELECT title, author FROM books ORDER BY RANDOM() LIMIT 3")
                books = cursor.fetchall()
                return {'books': [dict(book) for book in books]}
            
            elif content_type == 'concepts':
                # Extract concepts from chunk content using simple keyword extraction
                cursor.execute("""
                    SELECT content FROM chunks 
                    WHERE embedding_array IS NOT NULL 
                    ORDER BY RANDOM() 
                    LIMIT 5
                """)
                chunks = cursor.fetchall()
                
                # Simple concept extraction (this could be enhanced with NLP)
                concepts = []
                for chunk in chunks:
                    words = chunk['content'].lower().split()
                    # Look for philosophical/academic terms
                    for word in words:
                        if len(word) > 6 and word.isalpha():
                            concepts.append(word)
                
                return {'concepts': random.sample(concepts, min(5, len(concepts)))}
            
            else:  # 'all'
                # Get a mix of everything
                result = {}
                result.update(self.get_random_content_by_seed(seed, 'authors'))
                result.update(self.get_random_content_by_seed(seed + 1, 'books'))
                result.update(self.get_random_content_by_seed(seed + 2, 'concepts'))
                return result
                
        except Exception as e:
            logger.error(f"Error getting random content: {e}")
            return {}
        finally:
            conn.close()
    
    def generate_question_by_seed(self, seed: int, question_type: str = None) -> Dict:
        """Generate a question using deterministic seed"""
        random.seed(seed)
        
        # Select question type if not specified
        if not question_type:
            question_type = random.choice(list(self.question_templates.keys()))
        
        # Get content to use in question
        content = self.get_random_content_by_seed(seed)
        
        # Select template
        template = random.choice(self.question_templates[question_type])
        
        # Select concepts from pools
        concept_type = random.choice(list(self.concept_pools.keys()))
        concepts = random.sample(self.concept_pools[concept_type], 3)
        
        # Fill in template
        try:
            question = template.format(
                concept1=concepts[0] if len(concepts) > 0 else 'existence',
                concept2=concepts[1] if len(concepts) > 1 else 'meaning',
                concept3=concepts[2] if len(concepts) > 2 else 'knowledge',
                author=content.get('authors', ['Unknown'])[0] if content.get('authors') else 'Unknown',
                author1=content.get('authors', ['Unknown', 'Anonymous'])[0] if content.get('authors') else 'Unknown',
                author2=content.get('authors', ['Unknown', 'Anonymous'])[1] if len(content.get('authors', [])) > 1 else 'Anonymous',
                book1=content.get('books', [{'title': 'Unknown'}])[0]['title'] if content.get('books') else 'Unknown',
                book2=content.get('books', [{'title': 'Unknown'}, {'title': 'Anonymous'}])[1]['title'] if len(content.get('books', [])) > 1 else 'Anonymous',
                genre1=random.choice(['philosophy', 'literature', 'science']),
                genre2=random.choice(['sociology', 'psychology', 'history'])
            )
        except (KeyError, IndexError):
            # Fallback to simple question
            question = f"How does the concept of {concepts[0]} relate to {concepts[1]} in contemporary thought?"
        
        return {
            'seed': seed,
            'question': question,
            'type': question_type,
            'concepts': concepts[:2],
            'content_used': content,
            'generated_at': datetime.now().isoformat()
        }
    
    def generate_question_series(self, base_seed: int, count: int = 10) -> List[Dict]:
        """Generate a series of related questions"""
        questions = []
        
        for i in range(count):
            seed = base_seed + i
            question_data = self.generate_question_by_seed(seed)
            questions.append(question_data)
        
        return questions
    
    def ask_agent_question(self, question: str, model: str = "qwq:32b-q8_0") -> str:
        """Ask a question to Ollama agent and get response"""
        try:
            payload = {
                "model": model,
                "prompt": f"""You are a philosophical research assistant with access to a vast library of texts. Answer this question using deep analysis and cross-referential thinking:

{question}

Provide a thoughtful, well-reasoned response that draws connections between ideas and demonstrates sophisticated understanding.""",
                "stream": False
            }
            
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=300  # Increased timeout to 5 minutes for complex responses
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            logger.error(f"Error asking agent question: {e}")
            return f"Error generating response: {e}"
    
    def semantic_search_for_question(self, question: str, limit: int = 5) -> List[Dict]:
        """Use vector embeddings to find relevant content for a question"""
        try:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, current_dir)
            from vector_embeddings import VectorEmbeddingGenerator
            
            generator = VectorEmbeddingGenerator()
            results = generator.semantic_search(question, limit)
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def answer_question_with_context(self, question_data: Dict, model: str = None) -> Dict:
        """Answer a question using direct vector search - no LLM middleman"""
        question = question_data['question']
        
        # Get relevant context from vector search - this IS the answer
        context_chunks = self.semantic_search_for_question(question, limit=10)
        
        # Format the direct results
        direct_results = []
        for chunk in context_chunks:
            direct_results.append({
                'title': chunk['title'],
                'author': chunk['author'],
                'similarity': chunk['similarity_score'],
                'excerpt': chunk['content_preview'][:300] + "...",
                'chapter': chunk.get('chapter_number'),
                'relevance': f"{chunk['similarity_score']:.3f}"
            })
        
        return {
            'question_data': question_data,
            'direct_search_results': direct_results,
            'total_results': len(context_chunks),
            'search_completed_at': datetime.now().isoformat(),
            'method': 'direct_vector_search'
        }

def main():
    """Command line interface for seed question system"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed-based Question Generator for LibraryOfBabel")
    parser.add_argument('--seed', type=int, default=42, help='Seed for question generation')
    parser.add_argument('--count', type=int, default=1, help='Number of questions to generate')
    parser.add_argument('--type', choices=['philosophical', 'analytical', 'synthetic', 'exploratory'], help='Type of question')
    parser.add_argument('--ask-agent', action='store_true', help='Ask agent to answer the questions')
    parser.add_argument('--model', default='qwq:32b-q8_0', help='Ollama model to use')
    
    args = parser.parse_args()
    
    generator = SeedQuestionGenerator()
    
    if args.count == 1:
        question_data = generator.generate_question_by_seed(args.seed, args.type)
        print(f"🎲 Seed: {question_data['seed']}")
        print(f"❓ Question: {question_data['question']}")
        print(f"📝 Type: {question_data['type']}")
        print(f"🔑 Concepts: {', '.join(question_data['concepts'])}")
        
        if args.ask_agent:
            print(f"\n🔍 Searching vector database...")
            result = generator.answer_question_with_context(question_data)
            print(f"\n📚 Found {result['total_results']} relevant sources:")
            for i, source in enumerate(result['direct_search_results'][:5], 1):
                print(f"  {i}. {source['title']} by {source['author']} (similarity: {source['relevance']})")
                print(f"     {source['excerpt']}\n")
    else:
        questions = generator.generate_question_series(args.seed, args.count)
        for i, q in enumerate(questions, 1):
            print(f"\n{i}. Seed {q['seed']}: {q['question']}")
            
            if args.ask_agent:
                result = generator.answer_question_with_context(q)
                print(f"   📚 Found {result['total_results']} sources, top match: {result['direct_search_results'][0]['title'] if result['direct_search_results'] else 'None'}")

if __name__ == "__main__":
    main()