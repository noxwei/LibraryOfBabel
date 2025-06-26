#!/usr/bin/env python3
"""
LibraryOfBabel Search API
=========================

RESTful API for AI research agents to query the knowledge base.
Provides semantic search, cross-referencing, and structured responses.

Author: API Agent
Version: 1.0
"""

import os
import json
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
from contextlib import contextmanager
import threading
from functools import lru_cache
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Individual search result with relevance scoring."""
    book_id: str
    title: str
    author: str
    relevance_score: float
    matching_chunks: List[Dict[str, Any]]
    total_matches: int
    publication_date: Optional[str] = None
    genre: Optional[str] = None

@dataclass
class SearchResponse:
    """Complete search response with metadata."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: int
    facets: Dict[str, List[Dict[str, Any]]]
    suggestions: List[str]
    cross_references: List[Dict[str, Any]]

class SearchAPI:
    """Main search API class with caching and optimization."""
    
    def __init__(self, data_dir: str = None, cache_size: int = 1000):
        """Initialize the search API."""
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '../../output')
        self.cache_size = cache_size
        self.books_data = {}
        self.search_index = {}
        self.author_index = defaultdict(list)
        self.term_index = defaultdict(list)
        self.book_connections = defaultdict(list)
        self.lock = threading.RLock()
        
        # Initialize Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()
        
        # Load data
        self._load_book_data()
        self._build_search_indexes()
        
        logger.info(f"Search API initialized with {len(self.books_data)} books")
    
    def _setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'books_loaded': len(self.books_data),
                'timestamp': time.time()
            })
        
        @self.app.route('/search', methods=['GET', 'POST'])
        def search():
            """Main search endpoint."""
            if request.method == 'POST':
                data = request.get_json()
                query = data.get('query', '')
                search_type = data.get('type', 'general')
                filters = data.get('filters', {})
                limit = data.get('limit', 10)
                offset = data.get('offset', 0)
            else:
                query = request.args.get('query', '')
                search_type = request.args.get('type', 'general')
                filters = {}
                limit = int(request.args.get('limit', 10))
                offset = int(request.args.get('offset', 0))
            
            if not query:
                return jsonify({'error': 'Query parameter is required'}), 400
            
            try:
                response = self.search_books(query, search_type, filters, limit, offset)
                return jsonify(asdict(response))
            except Exception as e:
                logger.error(f"Search error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/books/<book_id>', methods=['GET'])
        def get_book(book_id):
            """Get detailed book information."""
            try:
                book_data = self.get_book_details(book_id)
                if book_data:
                    return jsonify(book_data)
                else:
                    return jsonify({'error': 'Book not found'}), 404
            except Exception as e:
                logger.error(f"Get book error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/authors', methods=['GET'])
        def list_authors():
            """List all authors with book counts."""
            try:
                authors = self.get_authors_list()
                return jsonify(authors)
            except Exception as e:
                logger.error(f"Authors list error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/cross-reference', methods=['POST'])
        def cross_reference():
            """Find cross-references between concepts."""
            data = request.get_json()
            concept_a = data.get('concept_a', '')
            concept_b = data.get('concept_b', '')
            
            if not concept_a or not concept_b:
                return jsonify({'error': 'Both concept_a and concept_b are required'}), 400
            
            try:
                references = self.find_cross_references(concept_a, concept_b)
                return jsonify(references)
            except Exception as e:
                logger.error(f"Cross-reference error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/extract-quotes', methods=['POST'])
        def extract_quotes():
            """Extract quotes with context."""
            data = request.get_json()
            topic = data.get('topic', '')
            context_length = data.get('context_length', 200)
            min_relevance = data.get('min_relevance', 0.5)
            
            if not topic:
                return jsonify({'error': 'Topic parameter is required'}), 400
            
            try:
                quotes = self.extract_relevant_quotes(topic, context_length, min_relevance)
                return jsonify(quotes)
            except Exception as e:
                logger.error(f"Quote extraction error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/suggest-books', methods=['POST'])
        def suggest_books():
            """Suggest related books based on content similarity."""
            data = request.get_json()
            book_id = data.get('book_id', '')
            threshold = data.get('threshold', 0.7)
            limit = data.get('limit', 5)
            
            if not book_id:
                return jsonify({'error': 'book_id parameter is required'}), 400
            
            try:
                suggestions = self.suggest_related_books(book_id, threshold, limit)
                return jsonify(suggestions)
            except Exception as e:
                logger.error(f"Book suggestion error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _load_book_data(self):
        """Load all processed book data from JSON files."""
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory not found: {self.data_dir}")
            return
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_processed.json'):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        book_data = json.load(f)
                    
                    # Generate book ID from filename
                    book_id = filename.replace('_processed.json', '')
                    self.books_data[book_id] = book_data
                    
                    logger.debug(f"Loaded book: {book_data['metadata']['title']}")
                    
                except Exception as e:
                    logger.error(f"Failed to load {filename}: {e}")
    
    def _build_search_indexes(self):
        """Build search indexes for fast retrieval."""
        logger.info("Building search indexes...")
        
        for book_id, book_data in self.books_data.items():
            metadata = book_data['metadata']
            chapters = book_data['chapters']
            
            # Author index
            author = metadata.get('author', 'Unknown')
            self.author_index[author.lower()].append(book_id)
            
            # Term index for full-text search
            title_words = self._extract_search_terms(metadata.get('title', ''))
            author_words = self._extract_search_terms(author)
            subject_words = self._extract_search_terms(metadata.get('subject', ''))
            
            # Index metadata terms
            for term in title_words + author_words + subject_words:
                self.term_index[term].append({
                    'book_id': book_id,
                    'type': 'metadata',
                    'field': 'title' if term in title_words else 'author' if term in author_words else 'subject',
                    'relevance': 1.0
                })
            
            # Index chapter content
            for chapter in chapters:
                content_words = self._extract_search_terms(chapter['content'])
                title_words = self._extract_search_terms(chapter['title'])
                
                # Weight chapter titles higher
                for term in title_words:
                    self.term_index[term].append({
                        'book_id': book_id,
                        'type': 'chapter_title',
                        'chapter_id': chapter.get('chapter_number', 0),
                        'content': chapter['title'],
                        'relevance': 0.9
                    })
                
                # Index content terms
                for term in content_words:
                    self.term_index[term].append({
                        'book_id': book_id,
                        'type': 'content',
                        'chapter_id': chapter.get('chapter_number', 0),
                        'content': chapter['content'][:500],  # First 500 chars
                        'relevance': 0.7
                    })
        
        logger.info(f"Search indexes built with {len(self.term_index)} terms")
    
    def _extract_search_terms(self, text: str) -> List[str]:
        """Extract searchable terms from text."""
        if not text:
            return []
        
        # Convert to lowercase and remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words and filter out short terms
        words = [word for word in text.split() if len(word) >= 3]
        
        # Remove common stop words
        stop_words = {'the', 'and', 'but', 'for', 'are', 'with', 'this', 'that', 'was', 'will', 'you', 'not'}
        words = [word for word in words if word not in stop_words]
        
        return words
    
    @lru_cache(maxsize=1000)
    def search_books(self, query: str, search_type: str = 'general', 
                    filters: Dict = None, limit: int = 10, offset: int = 0) -> SearchResponse:
        """
        Main search function supporting multiple search types.
        
        Args:
            query: Search query string
            search_type: Type of search ('general', 'author', 'topic', 'cross_reference')
            filters: Additional filters (author, year, genre, etc.)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            SearchResponse with results and metadata
        """
        start_time = time.time()
        
        if filters is None:
            filters = {}
        
        # Convert filters to dict if it's not already (for caching)
        if not isinstance(filters, dict):
            filters = {}
        
        try:
            if search_type == 'author':
                results = self._search_by_author(query, filters, limit, offset)
            elif search_type == 'topic':
                results = self._search_by_topic(query, filters, limit, offset)
            elif search_type == 'cross_reference':
                results = self._search_cross_references(query, filters, limit, offset)
            else:
                results = self._search_general(query, filters, limit, offset)
            
            # Calculate search time
            search_time_ms = int((time.time() - start_time) * 1000)
            
            # Generate facets
            facets = self._generate_facets(results)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(query)
            
            # Find cross-references
            cross_references = self._find_related_concepts(query, results)
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time_ms=search_time_ms,
                facets=facets,
                suggestions=suggestions,
                cross_references=cross_references
            )
            
        except Exception as e:
            logger.error(f"Search error for query '{query}': {e}")
            raise
    
    def _search_general(self, query: str, filters: Dict, limit: int, offset: int) -> List[SearchResult]:
        """General search across all fields."""
        search_terms = self._extract_search_terms(query)
        if not search_terms:
            return []
        
        # Score books based on term matches
        book_scores = defaultdict(float)
        book_matches = defaultdict(list)
        
        for term in search_terms:
            if term in self.term_index:
                for match in self.term_index[term]:
                    book_id = match['book_id']
                    relevance = match['relevance']
                    
                    # Apply term frequency boost
                    term_boost = 1.0
                    if match['type'] == 'metadata':
                        term_boost = 2.0
                    elif match['type'] == 'chapter_title':
                        term_boost = 1.5
                    
                    book_scores[book_id] += relevance * term_boost
                    book_matches[book_id].append(match)
        
        # Apply filters
        filtered_books = self._apply_filters(book_scores.keys(), filters)
        
        # Sort by relevance score
        sorted_books = sorted(
            [(book_id, score) for book_id, score in book_scores.items() if book_id in filtered_books],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Pagination
        paginated_books = sorted_books[offset:offset + limit]
        
        # Build search results
        results = []
        for book_id, score in paginated_books:
            book_data = self.books_data[book_id]
            
            # Get best matching chunks
            chunks = self._get_best_chunks(book_matches[book_id], query, limit=5)
            
            result = SearchResult(
                book_id=book_id,
                title=book_data['metadata']['title'],
                author=book_data['metadata']['author'],
                relevance_score=score,
                matching_chunks=chunks,
                total_matches=len(book_matches[book_id]),
                publication_date=book_data['metadata'].get('publication_date'),
                genre=book_data['metadata'].get('subject')
            )
            results.append(result)
        
        return results
    
    def _search_by_author(self, author_query: str, filters: Dict, limit: int, offset: int) -> List[SearchResult]:
        """Search specifically by author name."""
        author_lower = author_query.lower()
        matching_books = []
        
        for author, book_ids in self.author_index.items():
            if author_lower in author or any(term in author for term in author_lower.split()):
                for book_id in book_ids:
                    if book_id in self.books_data:
                        matching_books.append((book_id, 1.0))  # Perfect match score
        
        # Apply filters
        filtered_books = self._apply_filters([book_id for book_id, _ in matching_books], filters)
        
        # Filter and paginate
        filtered_matches = [(book_id, score) for book_id, score in matching_books if book_id in filtered_books]
        paginated_books = filtered_matches[offset:offset + limit]
        
        # Build results
        results = []
        for book_id, score in paginated_books:
            book_data = self.books_data[book_id]
            
            result = SearchResult(
                book_id=book_id,
                title=book_data['metadata']['title'],
                author=book_data['metadata']['author'],
                relevance_score=score,
                matching_chunks=[],
                total_matches=1,
                publication_date=book_data['metadata'].get('publication_date'),
                genre=book_data['metadata'].get('subject')
            )
            results.append(result)
        
        return results
    
    def _search_by_topic(self, topic_query: str, filters: Dict, limit: int, offset: int) -> List[SearchResult]:
        """Search by topic/subject with semantic grouping."""
        # Use general search but weight subject fields higher
        search_terms = self._extract_search_terms(topic_query)
        if not search_terms:
            return []
        
        book_scores = defaultdict(float)
        book_matches = defaultdict(list)
        
        for term in search_terms:
            if term in self.term_index:
                for match in self.term_index[term]:
                    book_id = match['book_id']
                    relevance = match['relevance']
                    
                    # Higher weight for subject/topic matches
                    if match.get('field') == 'subject' or match['type'] == 'metadata':
                        relevance *= 2.5
                    elif match['type'] == 'chapter_title':
                        relevance *= 1.8
                    
                    book_scores[book_id] += relevance
                    book_matches[book_id].append(match)
        
        # Apply filters
        filtered_books = self._apply_filters(book_scores.keys(), filters)
        
        # Sort and paginate
        sorted_books = sorted(
            [(book_id, score) for book_id, score in book_scores.items() if book_id in filtered_books],
            key=lambda x: x[1],
            reverse=True
        )
        
        paginated_books = sorted_books[offset:offset + limit]
        
        # Build results
        results = []
        for book_id, score in paginated_books:
            book_data = self.books_data[book_id]
            
            chunks = self._get_best_chunks(book_matches[book_id], topic_query, limit=5)
            
            result = SearchResult(
                book_id=book_id,
                title=book_data['metadata']['title'],
                author=book_data['metadata']['author'],
                relevance_score=score,
                matching_chunks=chunks,
                total_matches=len(book_matches[book_id]),
                publication_date=book_data['metadata'].get('publication_date'),
                genre=book_data['metadata'].get('subject')
            )
            results.append(result)
        
        return results
    
    def _search_cross_references(self, query: str, filters: Dict, limit: int, offset: int) -> List[SearchResult]:
        """Search for cross-references between concepts."""
        # Extract multiple concepts from query
        concepts = [concept.strip() for concept in query.split(',')]
        if len(concepts) < 2:
            concepts = query.split(' and ')
        
        if len(concepts) < 2:
            return self._search_general(query, filters, limit, offset)
        
        # Find books that contain all concepts
        concept_books = []
        for concept in concepts:
            concept_terms = self._extract_search_terms(concept)
            concept_book_ids = set()
            
            for term in concept_terms:
                if term in self.term_index:
                    for match in self.term_index[term]:
                        concept_book_ids.add(match['book_id'])
            
            concept_books.append(concept_book_ids)
        
        # Find intersection of all concept book sets
        if concept_books:
            common_books = concept_books[0]
            for book_set in concept_books[1:]:
                common_books = common_books.intersection(book_set)
        else:
            common_books = set()
        
        # Apply filters
        filtered_books = self._apply_filters(common_books, filters)
        
        # Score books based on concept co-occurrence
        book_scores = {}
        for book_id in filtered_books:
            score = 0.0
            for concept in concepts:
                concept_terms = self._extract_search_terms(concept)
                for term in concept_terms:
                    if term in self.term_index:
                        for match in self.term_index[term]:
                            if match['book_id'] == book_id:
                                score += match['relevance']
            
            book_scores[book_id] = score
        
        # Sort and paginate
        sorted_books = sorted(book_scores.items(), key=lambda x: x[1], reverse=True)
        paginated_books = sorted_books[offset:offset + limit]
        
        # Build results
        results = []
        for book_id, score in paginated_books:
            book_data = self.books_data[book_id]
            
            # Find chunks that contain multiple concepts
            cross_ref_chunks = self._find_cross_reference_chunks(book_id, concepts)
            
            result = SearchResult(
                book_id=book_id,
                title=book_data['metadata']['title'],
                author=book_data['metadata']['author'],
                relevance_score=score,
                matching_chunks=cross_ref_chunks,
                total_matches=len(cross_ref_chunks),
                publication_date=book_data['metadata'].get('publication_date'),
                genre=book_data['metadata'].get('subject')
            )
            results.append(result)
        
        return results
    
    def _apply_filters(self, book_ids: List[str], filters: Dict) -> List[str]:
        """Apply filters to book results."""
        if not filters:
            return list(book_ids)
        
        filtered_books = []
        for book_id in book_ids:
            if book_id not in self.books_data:
                continue
            
            book_data = self.books_data[book_id]
            metadata = book_data['metadata']
            
            # Apply filters
            include_book = True
            
            if 'author' in filters:
                author_filter = filters['author'].lower()
                if author_filter not in metadata.get('author', '').lower():
                    include_book = False
            
            if 'year' in filters:
                year_filter = filters['year']
                pub_date = metadata.get('publication_date', '')
                if str(year_filter) not in pub_date:
                    include_book = False
            
            if 'genre' in filters:
                genre_filter = filters['genre'].lower()
                if genre_filter not in metadata.get('subject', '').lower():
                    include_book = False
            
            if 'min_words' in filters:
                min_words = filters['min_words']
                if metadata.get('total_words', 0) < min_words:
                    include_book = False
            
            if include_book:
                filtered_books.append(book_id)
        
        return filtered_books
    
    def _get_best_chunks(self, matches: List[Dict], query: str, limit: int = 5) -> List[Dict]:
        """Get the best matching chunks for a query."""
        # Score chunks by relevance
        chunk_scores = defaultdict(float)
        chunk_data = {}
        
        for match in matches:
            if match['type'] in ['content', 'chapter_title']:
                chunk_key = f"{match['book_id']}_{match.get('chapter_id', 0)}"
                chunk_scores[chunk_key] += match['relevance']
                
                if chunk_key not in chunk_data:
                    chunk_data[chunk_key] = {
                        'chapter_id': match.get('chapter_id', 0),
                        'content': match.get('content', ''),
                        'type': match['type']
                    }
        
        # Sort by score and return top chunks
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
        
        best_chunks = []
        for chunk_key, score in sorted_chunks[:limit]:
            chunk_info = chunk_data[chunk_key]
            best_chunks.append({
                'chapter_id': chunk_info['chapter_id'],
                'content': chunk_info['content'],
                'relevance_score': score,
                'type': chunk_info['type']
            })
        
        return best_chunks
    
    def _find_cross_reference_chunks(self, book_id: str, concepts: List[str]) -> List[Dict]:
        """Find chunks that contain multiple concepts."""
        if book_id not in self.books_data:
            return []
        
        book_data = self.books_data[book_id]
        chapters = book_data['chapters']
        
        cross_ref_chunks = []
        
        for chapter in chapters:
            content_lower = chapter['content'].lower()
            concept_matches = 0
            
            for concept in concepts:
                concept_terms = self._extract_search_terms(concept)
                if any(term in content_lower for term in concept_terms):
                    concept_matches += 1
            
            # Include chunks that contain at least 2 concepts
            if concept_matches >= 2:
                cross_ref_chunks.append({
                    'chapter_id': chapter.get('chapter_number', 0),
                    'title': chapter['title'],
                    'content': chapter['content'][:500],  # First 500 chars
                    'concept_matches': concept_matches,
                    'relevance_score': concept_matches / len(concepts)
                })
        
        # Sort by relevance
        cross_ref_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return cross_ref_chunks[:10]  # Return top 10
    
    def _generate_facets(self, results: List[SearchResult]) -> Dict[str, List[Dict]]:
        """Generate facets for search results."""
        facets = {
            'authors': defaultdict(int),
            'years': defaultdict(int),
            'genres': defaultdict(int)
        }
        
        for result in results:
            # Author facet
            facets['authors'][result.author] += 1
            
            # Year facet
            if result.publication_date:
                year = result.publication_date[:4]  # Extract year
                if year.isdigit():
                    facets['years'][year] += 1
            
            # Genre facet
            if result.genre:
                facets['genres'][result.genre] += 1
        
        # Convert to list format
        formatted_facets = {}
        for facet_type, facet_data in facets.items():
            formatted_facets[facet_type] = [
                {'value': value, 'count': count}
                for value, count in sorted(facet_data.items(), key=lambda x: x[1], reverse=True)
            ]
        
        return formatted_facets
    
    def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions based on query."""
        # Simple suggestion logic - can be enhanced with ML
        suggestions = []
        
        # Add variations of the query
        if ' ' in query:
            words = query.split()
            if len(words) > 1:
                suggestions.append(' '.join(words[:-1]))  # Remove last word
                suggestions.append(' '.join(words[1:]))   # Remove first word
        
        # Add related terms from index
        query_terms = self._extract_search_terms(query)
        for term in query_terms:
            if term in self.term_index:
                # Find books with this term and suggest their titles
                term_matches = self.term_index[term][:5]  # Top 5 matches
                for match in term_matches:
                    if match['type'] == 'metadata' and match['book_id'] in self.books_data:
                        book_title = self.books_data[match['book_id']]['metadata']['title']
                        if book_title not in suggestions:
                            suggestions.append(book_title)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _find_related_concepts(self, query: str, results: List[SearchResult]) -> List[Dict]:
        """Find concepts related to the query based on search results."""
        related_concepts = []
        
        # Extract common terms from top results
        term_frequency = defaultdict(int)
        
        for result in results[:5]:  # Top 5 results
            for chunk in result.matching_chunks:
                chunk_terms = self._extract_search_terms(chunk['content'])
                for term in chunk_terms:
                    term_frequency[term] += 1
        
        # Find terms that appear frequently but aren't in the original query
        query_terms = set(self._extract_search_terms(query))
        
        for term, frequency in sorted(term_frequency.items(), key=lambda x: x[1], reverse=True):
            if term not in query_terms and frequency > 1:
                related_concepts.append({
                    'concept': term,
                    'frequency': frequency,
                    'related_books': len([r for r in results if term in str(r.matching_chunks)])
                })
        
        return related_concepts[:10]  # Top 10 related concepts
    
    def get_book_details(self, book_id: str) -> Optional[Dict]:
        """Get detailed information about a specific book."""
        if book_id not in self.books_data:
            return None
        
        book_data = self.books_data[book_id]
        
        # Add computed fields
        details = {
            'book_id': book_id,
            'metadata': book_data['metadata'],
            'chapters': book_data['chapters'],
            'statistics': {
                'total_chapters': len(book_data['chapters']),
                'total_words': book_data['metadata']['total_words'],
                'avg_chapter_length': book_data['metadata']['total_words'] // len(book_data['chapters']) if book_data['chapters'] else 0
            }
        }
        
        return details
    
    def get_authors_list(self) -> List[Dict]:
        """Get list of all authors with book counts."""
        authors = []
        
        for author, book_ids in self.author_index.items():
            book_count = len(book_ids)
            total_words = sum(
                self.books_data[book_id]['metadata']['total_words']
                for book_id in book_ids
                if book_id in self.books_data
            )
            
            authors.append({
                'author': author,
                'book_count': book_count,
                'total_words': total_words,
                'book_ids': book_ids
            })
        
        # Sort by book count
        authors.sort(key=lambda x: x['book_count'], reverse=True)
        
        return authors
    
    def find_cross_references(self, concept_a: str, concept_b: str) -> Dict:
        """Find books that discuss both concepts."""
        # Find books containing concept A
        concept_a_terms = self._extract_search_terms(concept_a)
        concept_a_books = set()
        
        for term in concept_a_terms:
            if term in self.term_index:
                for match in self.term_index[term]:
                    concept_a_books.add(match['book_id'])
        
        # Find books containing concept B
        concept_b_terms = self._extract_search_terms(concept_b)
        concept_b_books = set()
        
        for term in concept_b_terms:
            if term in self.term_index:
                for match in self.term_index[term]:
                    concept_b_books.add(match['book_id'])
        
        # Find intersection
        common_books = concept_a_books.intersection(concept_b_books)
        
        # Build detailed results
        cross_references = []
        
        for book_id in common_books:
            if book_id in self.books_data:
                book_data = self.books_data[book_id]
                
                # Find chapters that contain both concepts
                relevant_chapters = []
                for chapter in book_data['chapters']:
                    content_lower = chapter['content'].lower()
                    
                    has_concept_a = any(term in content_lower for term in concept_a_terms)
                    has_concept_b = any(term in content_lower for term in concept_b_terms)
                    
                    if has_concept_a and has_concept_b:
                        relevant_chapters.append({
                            'chapter_id': chapter.get('chapter_number', 0),
                            'title': chapter['title'],
                            'content_preview': chapter['content'][:300]
                        })
                
                if relevant_chapters:
                    cross_references.append({
                        'book_id': book_id,
                        'title': book_data['metadata']['title'],
                        'author': book_data['metadata']['author'],
                        'relevant_chapters': relevant_chapters
                    })
        
        return {
            'concept_a': concept_a,
            'concept_b': concept_b,
            'total_books': len(cross_references),
            'cross_references': cross_references
        }
    
    def extract_relevant_quotes(self, topic: str, context_length: int = 200, 
                               min_relevance: float = 0.5) -> Dict:
        """Extract relevant quotes with context."""
        topic_terms = self._extract_search_terms(topic)
        quotes = []
        
        for book_id, book_data in self.books_data.items():
            for chapter in book_data['chapters']:
                content = chapter['content']
                
                # Find sentences containing topic terms
                sentences = re.split(r'[.!?]+', content)
                
                for i, sentence in enumerate(sentences):
                    sentence_lower = sentence.lower()
                    
                    # Check if sentence contains topic terms
                    term_matches = sum(1 for term in topic_terms if term in sentence_lower)
                    relevance = term_matches / len(topic_terms) if topic_terms else 0
                    
                    if relevance >= min_relevance:
                        # Get context around the sentence
                        context_start = max(0, i - 1)
                        context_end = min(len(sentences), i + 2)
                        context = '. '.join(sentences[context_start:context_end])
                        
                        # Limit context length
                        if len(context) > context_length:
                            context = context[:context_length] + '...'
                        
                        quotes.append({
                            'book_id': book_id,
                            'title': book_data['metadata']['title'],
                            'author': book_data['metadata']['author'],
                            'chapter_id': chapter.get('chapter_number', 0),
                            'chapter_title': chapter['title'],
                            'quote': sentence.strip(),
                            'context': context,
                            'relevance_score': relevance
                        })
        
        # Sort by relevance
        quotes.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            'topic': topic,
            'total_quotes': len(quotes),
            'quotes': quotes[:20]  # Return top 20 quotes
        }
    
    def suggest_related_books(self, book_id: str, threshold: float = 0.7, 
                             limit: int = 5) -> Dict:
        """Suggest books related to a given book."""
        if book_id not in self.books_data:
            return {'error': 'Book not found'}
        
        source_book = self.books_data[book_id]
        source_metadata = source_book['metadata']
        
        # Get terms from source book
        source_terms = set()
        source_terms.update(self._extract_search_terms(source_metadata['title']))
        source_terms.update(self._extract_search_terms(source_metadata.get('subject', '')))
        
        # Add terms from chapter content
        for chapter in source_book['chapters']:
            chapter_terms = self._extract_search_terms(chapter['content'])
            source_terms.update(chapter_terms[:50])  # Limit to avoid too many terms
        
        # Find similar books
        book_similarities = {}
        
        for other_book_id, other_book_data in self.books_data.items():
            if other_book_id == book_id:
                continue
            
            other_metadata = other_book_data['metadata']
            other_terms = set()
            other_terms.update(self._extract_search_terms(other_metadata['title']))
            other_terms.update(self._extract_search_terms(other_metadata.get('subject', '')))
            
            # Add terms from chapter content
            for chapter in other_book_data['chapters']:
                chapter_terms = self._extract_search_terms(chapter['content'])
                other_terms.update(chapter_terms[:50])
            
            # Calculate similarity (Jaccard index)
            intersection = len(source_terms.intersection(other_terms))
            union = len(source_terms.union(other_terms))
            
            if union > 0:
                similarity = intersection / union
                if similarity >= threshold:
                    book_similarities[other_book_id] = similarity
        
        # Sort by similarity
        sorted_books = sorted(book_similarities.items(), key=lambda x: x[1], reverse=True)
        
        # Build suggestions
        suggestions = []
        for other_book_id, similarity in sorted_books[:limit]:
            other_book_data = self.books_data[other_book_id]
            suggestions.append({
                'book_id': other_book_id,
                'title': other_book_data['metadata']['title'],
                'author': other_book_data['metadata']['author'],
                'similarity_score': similarity,
                'genre': other_book_data['metadata'].get('subject')
            })
        
        return {
            'source_book_id': book_id,
            'source_title': source_metadata['title'],
            'suggestions': suggestions
        }
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """Run the Flask application."""
        logger.info(f"Starting LibraryOfBabel Search API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main function to run the API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LibraryOfBabel Search API')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--data-dir', help='Directory containing processed book data')
    
    args = parser.parse_args()
    
    # Initialize and run API
    api = SearchAPI(data_dir=args.data_dir)
    api.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()