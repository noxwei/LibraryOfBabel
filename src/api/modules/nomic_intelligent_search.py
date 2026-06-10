"""
Nomic Intelligent Chapter Search Module
======================================

Dr. Sarah Chen (陈雪芳) - Advanced Semantic Search with Intelligent Content Previews
Uses nomic-embed-text-v2-moe for chapter-level semantic search with smart content extraction.

Features:
- Chapter-level semantic search (8k token window coverage)
- Intelligent content previews (keyword-based extraction)
- Genre-aware search optimization
- Real-time embedding generation
- Copyright-safe content previews
"""

import logging
import os
import requests
import re
import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
from .database import get_db

logger = logging.getLogger(__name__)

class NomicIntelligentSearch:
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINIAPI_KEY", "")
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent"
        self.model_name = "nomic-embed-text-v2-moe"
        self.embedding_dim = 768
        # Fallback to Ollama if no Gemini key
        self.ollama_url = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434" if os.getenv("RUNNING_IN_CONTAINER") == "true" else "http://localhost:11434")
        self.max_chapter_words = 8000  # Ensure full token coverage
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences for intelligent extraction"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def extract_keyword_sentences(self, text: str, query_terms: List[str], max_sentences: int = 3) -> str:
        """Extract sentences with highest keyword density"""
        sentences = self.split_sentences(text)
        
        scored_sentences = []
        for sent in sentences:
            score = sum(1 for term in query_terms if term.lower() in sent.lower())
            if score > 0:
                scored_sentences.append((score, sent))
        
        # Sort by score and take top sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[0], reverse=True)[:max_sentences]
        
        if top_sentences:
            return " ".join([sent for score, sent in top_sentences])
        else:
            # Fallback to first few sentences if no keywords found
            return " ".join(sentences[:2])
    
    def trim_to_word_limit_with_period(self, text: str, max_words: int = 200) -> str:
        """Trim text to ~max_words and end at the next period to complete the thought"""
        words = text.split()
        
        if len(words) <= max_words:
            return text
        
        # Take approximately max_words
        truncated = ' '.join(words[:max_words])
        
        # Find the next period after the word limit
        remaining_text = ' '.join(words[max_words:])
        period_index = remaining_text.find('.')
        
        if period_index != -1:
            # Add text up to and including the next period
            next_sentence_part = remaining_text[:period_index + 1]
            final_text = truncated + ' ' + next_sentence_part
        else:
            # No period found, just end with ellipsis
            final_text = truncated + '...'
        
        return final_text.strip()
    
    def extract_context_window(self, text: str, query_terms: List[str], window_size: int = 200) -> str:
        """Extract context around first keyword match"""
        text_lower = text.lower()
        
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in text_lower:
                index = text_lower.find(term_lower)
                start = max(0, index - window_size)
                end = min(len(text), index + len(term) + window_size)
                
                # Find word boundaries
                while start > 0 and text[start] != ' ':
                    start -= 1
                while end < len(text) and text[end] != ' ':
                    end += 1
                
                context = text[start:end].strip()
                if len(context) > 50:
                    return context
        
        # Fallback to beginning
        return text[:300]
    
    def intelligent_preview(self, text: str, query: str, max_words: int = 200) -> Dict:
        """Generate intelligent preview using multiple methods"""
        query_terms = [term.strip() for term in query.split() if len(term.strip()) > 2]
        
        # Method 1: Keyword-rich sentences
        keyword_preview = self.extract_keyword_sentences(text, query_terms, 5)
        
        # Method 2: Context window around keywords
        context_preview = self.extract_context_window(text, query_terms, 300)
        
        # Choose best preview
        if len(keyword_preview) > 100 and any(term.lower() in keyword_preview.lower() for term in query_terms):
            best_preview = keyword_preview
            method = "keyword_sentences"
        elif len(context_preview) > 100:
            best_preview = context_preview
            method = "context_window"
        else:
            best_preview = text[:600]  # Fallback to beginning
            method = "basic_fallback"
        
        # Trim to ~200 words and end at next period
        best_preview = self.trim_to_word_limit_with_period(best_preview, max_words)
        
        return {
            'preview': best_preview,
            'method': method,
            'terms_found': [term for term in query_terms if term.lower() in best_preview.lower()]
        }
    
    def generate_reading_link(self, book_id: int, chunk_id: str, words_per_page: int = 500) -> str:
        """Generate a reading link that takes you directly to the page containing this chapter"""
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    # Sum word counts of all chunks that come before this one (by chunk_id sort order)
                    cur.execute("""
                        SELECT COALESCE(SUM(c.word_count), 0) as cumulative_words
                        FROM chunks c
                        WHERE c.book_id = %s
                            AND c.chunk_id < %s
                    """, (book_id, chunk_id))

                    cumulative_words = cur.fetchone()[0]

                    # Calculate page number (1-indexed)
                    page_num = max(1, (cumulative_words // words_per_page) + 1)

                    reading_link = f"/api/books?action=page&id={book_id}&page_num={page_num}&words_per_page={words_per_page}"

                    return reading_link
                    
        except Exception as e:
            logger.error(f"Error generating reading link for book {book_id}, chunk {chunk_id}: {e}")
            # Fallback to first page
            return f"/api/books?action=page&id={book_id}&page_num=1&words_per_page={words_per_page}"
    
    def generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """Generate embedding for search query using Ollama (Gemini credits depleted)."""
        # Gemini credits depleted — go straight to Ollama to avoid wasted API calls
        return self._embed_via_ollama(query)

    def _embed_via_gemini(self, query: str) -> Optional[List[float]]:
        """Generate embedding via Google Gemini API"""
        try:
            response = requests.post(
                f"{self.gemini_url}?key={self.gemini_api_key}",
                json={
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": query}]},
                    "outputDimensionality": self.embedding_dim
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json().get("embedding", {}).get("values", [])
            else:
                logger.error(f"Gemini embedding error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            return None

    def _embed_via_ollama(self, query: str) -> Optional[List[float]]:
        """Fallback: generate embedding via local Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": "nomic-embed-text-v2-moe",
                    "prompt": f"search_query: {query}"
                },
                timeout=30
            )
            if response.status_code == 200:
                return response.json().get('embedding', [])
            else:
                logger.error(f"Ollama embedding error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def _run_vector_search(self, cur, vector_str: str, model_name: str, limit: int, genre_filter: Optional[str], sort_field: str) -> List[Dict]:
        """Run a single vector search against a specific embedding model.

        Uses a CTE to do fast HNSW vector search first, then joins/filters
        to avoid the planner pulling all chunks through expensive JOINs.
        """
        # Fetch more candidates than needed since some will be filtered out
        candidate_multiplier = 5
        candidate_limit = limit * candidate_multiplier

        base_query = """
            WITH candidates AS (
                SELECT ce.chunk_id, ce.book_id,
                       (1.0 - (ce.embedding_vector <=> %s::vector)) as similarity_score
                FROM chunk_embeddings ce
                WHERE ce.embedding_model = %s
                ORDER BY ce.embedding_vector <=> %s::vector
                LIMIT %s
            )
            SELECT
                ca.chunk_id,
                ca.book_id,
                b.title,
                b.author,
                b.genre,
                c.chunk_type,
                c.word_count,
                c.content,
                ca.similarity_score
            FROM candidates ca
            JOIN chunks c ON ca.chunk_id = c.chunk_id
            JOIN books b ON ca.book_id = b.book_id
            WHERE c.chunk_type = 'chapter'
                AND c.word_count <= %s
                AND c.content IS NOT NULL
        """
        params = [vector_str, model_name, vector_str, candidate_limit, self.max_chapter_words]

        if genre_filter:
            base_query += " AND b.genre ILIKE %s"
            params.append(f"%{genre_filter}%")

        if sort_field == 'alpha_title':
            base_query += " ORDER BY b.title ASC"
        elif sort_field == 'alpha_author':
            base_query += " ORDER BY b.author ASC, b.title ASC"
        else:
            base_query += " ORDER BY ca.similarity_score DESC"

        base_query += " LIMIT %s"
        params.append(limit)

        cur.execute(base_query, params)
        return [dict(row) for row in cur.fetchall()]

    def search_chapters_semantic(self, query: str, limit: int = 10, genre_filter: Optional[str] = None, sort_field: str = 'relevance') -> List[Dict]:
        """Semantic search with multi-model fallback: Gemini first, then nomic-v2-moe to fill gaps."""

        # Generate query embedding via Ollama (nomic-v2-moe)
        query_embedding = self.generate_query_embedding(query)
        if not query_embedding:
            raise Exception("Failed to generate query embedding")

        try:
            with get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

                    vector_str = f"[{','.join(map(str, query_embedding))}]"

                    # Search nomic-v2-moe embeddings (96.4% coverage, Gemini credits depleted)
                    rows = self._run_vector_search(cur, vector_str, 'nomic-embed-text-v2-moe', limit, genre_filter, sort_field)

                    results = []
                    for row_dict in rows:
                        # Generate intelligent preview (300 words, ending at period)
                        preview_data = self.intelligent_preview(row_dict['content'], query, 300)
                        
                        # Generate reading link to the exact page containing this chapter
                        reading_link = self.generate_reading_link(row_dict['book_id'], row_dict['chunk_id'])
                        
                        result = {
                            'chunk_id': row_dict['chunk_id'],
                            'book_id': row_dict['book_id'],
                            'title': row_dict['title'],
                            'author': row_dict['author'],
                            'genre': row_dict['genre'],
                            'chunk_type': row_dict['chunk_type'],
                            'word_count': row_dict['word_count'],
                            'similarity_score': float(row_dict['similarity_score']),
                            'preview': preview_data['preview'],
                            'preview_method': preview_data['method'],
                            'query_terms_found': preview_data['terms_found'],
                            'reading_link': reading_link,
                            'search_model': self.model_name,
                            'search_type': 'chapter_semantic'
                        }
                        
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            logger.error(f"Chapter semantic search error: {e}")
            raise e

# Global instance
nomic_search = NomicIntelligentSearch()

def nomic_chapter_semantic_search(query: str, limit: int = 10, genre_filter: Optional[str] = None, sort_field: str = 'relevance') -> Dict[str, Any]:
    """
    Public function for nomic chapter-level semantic search with intelligent previews
    
    Args:
        query: Search query string
        limit: Maximum number of results (default: 10)
        genre_filter: Optional genre filter
    
    Returns:
        Dict containing search results and metadata
    """
    try:
        results = nomic_search.search_chapters_semantic(query, limit, genre_filter, sort_field)
        
        return {
            'success': True,
            'results': results,
            'total_results': len(results),
            'search_metadata': {
                'query': query,
                'model': 'nomic-embed-text-v2-moe',
                'search_type': 'chapter_semantic',
                'max_chapter_words': nomic_search.max_chapter_words,
                'genre_filter': genre_filter,
                'intelligent_preview': True
            }
        }
        
    except Exception as e:
        logger.error(f"Nomic chapter search error for query '{query}': {e}")
        return {
            'success': False,
            'error': str(e),
            'results': [],
            'total_results': 0
        }