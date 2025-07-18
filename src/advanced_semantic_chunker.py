#!/usr/bin/env python3
"""
🏛️ Advanced Semantic Chunker - Dr. Sarah Chen (陈雪芳) Implementation
================================================================

Advanced chunk processing system for LibraryOfBabel that implements:
- Content-aware boundaries (no mid-sentence cuts)  
- Hierarchical structure (book->chapter->paragraph->sentence)
- Multi-modal embedding preparation
- Semantic coherence scoring
- Citation and reference preservation

Lead: Dr. Sarah Chen (陈雪芳) - Database Systems Librarian
Team: LibraryOfBabel DBA Team
Philosophy: "数据库是图书馆的心脏 - every chunk must preserve meaning"
"""

import os
import re
import json
import spacy
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import yake
from textstat import flesch_reading_ease, flesch_kincaid_grade
import hashlib

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Load spaCy model for advanced NLP
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("⚠️  Please install spaCy English model: python -m spacy download en_core_web_sm")
    nlp = None

class AdvancedSemanticChunker:
    """
    Dr. Sarah Chen's implementation of semantic-aware chunking system.
    
    Features:
    - Content-aware boundaries (respects sentences, paragraphs, sections)
    - Hierarchical chunk levels (micro, small, medium, large, mega)
    - Semantic coherence scoring
    - Citation and reference preservation
    - Named entity recognition
    - Keyphrase extraction
    - Reading complexity analysis
    """
    
    def __init__(self, db_config: Dict[str, Any] = None):
        # Dr. Chen's systematic approach to configuration
        self.chunk_configs = {
            'micro': {
                'target_size': 200,
                'min_size': 100,
                'max_size': 300,
                'boundary_type': 'sentence',
                'coherence_threshold': 0.8
            },
            'small': {
                'target_size': 500,
                'min_size': 300,
                'max_size': 700,
                'boundary_type': 'paragraph',
                'coherence_threshold': 0.7
            },
            'medium': {
                'target_size': 1500,
                'min_size': 1000,
                'max_size': 2000,
                'boundary_type': 'section',
                'coherence_threshold': 0.6
            },
            'large': {
                'target_size': 4000,
                'min_size': 3000,
                'max_size': 5000,
                'boundary_type': 'subsection',
                'coherence_threshold': 0.5
            },
            'mega': {
                'target_size': 8000,
                'min_size': 6000,
                'max_size': 10000,
                'boundary_type': 'chapter',
                'coherence_threshold': 0.4
            }
        }
        
        # Database connection (Dr. Chen's PostgreSQL expertise)
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Initialize NLP tools
        self.stop_words = set(stopwords.words('english'))
        self.kw_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # Extract 1-3 word phrases
            dedupLim=0.7,
            top=10
        )
        
        # Setup logging with Dr. Chen's systematic approach
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - 陈雪芳 - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🏛️ Dr. Sarah Chen's Advanced Semantic Chunker initialized")
        self.logger.info("严格的数据库管理带来优秀的用户体验 (Strict database management brings excellent user experience)")
    
    def detect_content_boundaries(self, text: str) -> List[Dict[str, Any]]:
        """
        Dr. Chen's algorithm for detecting natural content boundaries.
        
        Uses multiple signals:
        - Sentence endings
        - Paragraph breaks
        - Section headers
        - Citation patterns
        - Topic shifts
        """
        boundaries = []
        
        # Detect sentences
        sentences = sent_tokenize(text)
        current_pos = 0
        
        for i, sentence in enumerate(sentences):
            start_pos = text.find(sentence, current_pos)
            end_pos = start_pos + len(sentence)
            
            # Calculate boundary strength (0.0 to 1.0)
            boundary_strength = self._calculate_boundary_strength(
                text, start_pos, end_pos, i, sentences
            )
            
            boundaries.append({
                'position': end_pos,
                'type': 'sentence',
                'strength': boundary_strength,
                'content': sentence,
                'index': i
            })
            
            current_pos = end_pos
        
        # Detect paragraph boundaries
        paragraphs = text.split('\n\n')
        current_pos = 0
        
        for paragraph in paragraphs:
            if paragraph.strip():
                end_pos = text.find(paragraph, current_pos) + len(paragraph)
                boundaries.append({
                    'position': end_pos,
                    'type': 'paragraph',
                    'strength': 0.8,  # Paragraphs are strong boundaries
                    'content': paragraph.strip()
                })
                current_pos = end_pos
        
        # Sort boundaries by position
        boundaries.sort(key=lambda x: x['position'])
        
        return boundaries
    
    def _calculate_boundary_strength(self, text: str, start: int, end: int, 
                                   sentence_idx: int, all_sentences: List[str]) -> float:
        """
        Calculate how good a boundary this position represents.
        Dr. Chen's systematic scoring approach.
        """
        strength = 0.3  # Base strength for sentence boundary
        
        sentence = all_sentences[sentence_idx]
        
        # Boost for paragraph endings
        if sentence.endswith(('\n\n', '\n')):
            strength += 0.3
        
        # Boost for section headers
        if re.match(r'^(Chapter|Section|\d+\.|\w+:)', sentence.strip()):
            strength += 0.4
        
        # Boost for citations
        if re.search(r'\(.*?\d{4}.*?\)|ibid\.|op\. cit\.', sentence):
            strength += 0.2
        
        # Boost for dialogue endings
        if sentence.strip().endswith('"') or sentence.strip().endswith("'"):
            strength += 0.1
        
        # Boost for list endings
        if re.search(r'^\s*\d+\.|^\s*[a-z]\)|^\s*[-*]', sentence):
            strength += 0.1
        
        # Check for topic shift using next sentence
        if sentence_idx < len(all_sentences) - 1:
            current_words = set(word_tokenize(sentence.lower()))
            next_words = set(word_tokenize(all_sentences[sentence_idx + 1].lower()))
            
            # Remove stop words
            current_words -= self.stop_words
            next_words -= self.stop_words
            
            if current_words and next_words:
                overlap = len(current_words & next_words) / len(current_words | next_words)
                if overlap < 0.3:  # Low overlap suggests topic shift
                    strength += 0.2
        
        return min(strength, 1.0)
    
    def create_semantic_chunks(self, text: str, book_id: int, 
                             chunk_level: str = 'medium') -> List[Dict[str, Any]]:
        """
        Dr. Chen's main chunking algorithm that creates content-aware chunks.
        """
        config = self.chunk_configs[chunk_level]
        boundaries = self.detect_content_boundaries(text)
        
        chunks = []
        current_chunk_start = 0
        current_chunk_text = ""
        
        for boundary in boundaries:
            # Consider adding this boundary's content to current chunk
            potential_chunk = current_chunk_text + boundary['content']
            
            # Check if we should finalize current chunk
            should_finalize = (
                len(potential_chunk) >= config['target_size'] and
                boundary['strength'] >= config['coherence_threshold']
            ) or len(potential_chunk) >= config['max_size']
            
            if should_finalize and len(current_chunk_text) >= config['min_size']:
                # Finalize current chunk
                chunk = self._create_chunk_metadata(
                    current_chunk_text, book_id, len(chunks), chunk_level
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk_start = boundary['position'] - len(boundary['content'])
                current_chunk_text = boundary['content']
            else:
                # Add to current chunk
                current_chunk_text = potential_chunk
        
        # Handle final chunk
        if current_chunk_text and len(current_chunk_text) >= config['min_size']:
            chunk = self._create_chunk_metadata(
                current_chunk_text, book_id, len(chunks), chunk_level
            )
            chunks.append(chunk)
        
        self.logger.info(f"Created {len(chunks)} semantic chunks at {chunk_level} level")
        return chunks
    
    def _create_chunk_metadata(self, text: str, book_id: int, 
                              chunk_index: int, chunk_level: str) -> Dict[str, Any]:
        """
        Dr. Chen's comprehensive metadata creation for each chunk.
        """
        # Generate unique chunk ID
        chunk_id = f"{book_id}_{chunk_level}_{chunk_index:04d}"
        
        # Extract metadata
        metadata = {
            'chunk_id': chunk_id,
            'book_id': book_id,
            'content': text,
            'chunk_level': chunk_level,
            'chunk_index': chunk_index,
            'char_count': len(text),
            'word_count': len(word_tokenize(text)),
            'sentence_count': len(sent_tokenize(text)),
            'created_at': datetime.now().isoformat(),
            
            # Reading complexity
            'reading_ease': flesch_reading_ease(text),
            'reading_grade': flesch_kincaid_grade(text),
            
            # Content analysis
            'keyphrases': self._extract_keyphrases(text),
            'entities': self._extract_entities(text),
            'citations': self._extract_citations(text),
            
            # Content hash for deduplication
            'content_hash': hashlib.md5(text.encode()).hexdigest()
        }
        
        return metadata
    
    def _extract_keyphrases(self, text: str) -> List[str]:
        """Extract key phrases using YAKE algorithm."""
        try:
            keywords = self.kw_extractor.extract_keywords(text)
            return [kw[1] for kw in keywords[:10]]  # Top 10 keyphrases
        except:
            return []
    
    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities using spaCy."""
        if not nlp:
            return []
        
        try:
            doc = nlp(text[:1000])  # Limit text length for performance
            entities = []
            
            for ent in doc.ents:
                if ent.label_ in ['PERSON', 'ORG', 'GPE', 'DATE', 'WORK_OF_ART']:
                    entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'confidence': 1.0  # spaCy doesn't provide confidence scores
                    })
            
            return entities[:20]  # Limit to top 20 entities
        except:
            return []
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract citation patterns."""
        citation_patterns = [
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2021)
            r'\d{4}[a-z]?',          # 2021a
            r'ibid\.',               # ibid.
            r'op\. cit\.',          # op. cit.
            r'et al\.',             # et al.
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            citations.extend(matches)
        
        return list(set(citations))[:10]  # Unique citations, max 10
    
    def process_book_semantic_chunks(self, book_id: int, 
                                   levels: List[str] = None) -> Dict[str, Any]:
        """
        Dr. Chen's complete book processing pipeline.
        Creates multiple hierarchical chunk levels for a single book.
        """
        if levels is None:
            levels = ['micro', 'small', 'medium', 'large', 'mega']
        
        # Get book content from database
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT b.title, b.author, c.content 
                    FROM books b
                    JOIN chunks c ON b.book_id = c.book_id 
                    WHERE b.book_id = %s
                    ORDER BY c.chapter_number, c.chunk_id
                """, (book_id,))
                
                book_data = cur.fetchall()
                
                if not book_data:
                    self.logger.error(f"Book {book_id} not found")
                    return {'error': f'Book {book_id} not found'}
        
        # Combine all content
        full_text = '\n\n'.join([chunk['content'] for chunk in book_data])
        book_title = book_data[0]['title']
        book_author = book_data[0]['author']
        
        self.logger.info(f"Processing book: {book_title} by {book_author}")
        
        # Process each chunk level
        results = {
            'book_id': book_id,
            'title': book_title,
            'author': book_author,
            'processing_timestamp': datetime.now().isoformat(),
            'chunk_levels': {}
        }
        
        for level in levels:
            self.logger.info(f"Creating {level} level chunks for book {book_id}")
            chunks = self.create_semantic_chunks(full_text, book_id, level)
            
            results['chunk_levels'][level] = {
                'chunk_count': len(chunks),
                'chunks': chunks,
                'config': self.chunk_configs[level]
            }
        
        return results
    
    def save_semantic_chunks_to_db(self, chunks_data: Dict[str, Any]) -> bool:
        """
        Dr. Chen's database insertion with transaction safety.
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Create semantic chunks table if not exists
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS semantic_chunks (
                            chunk_id VARCHAR(255) PRIMARY KEY,
                            book_id INTEGER REFERENCES books(book_id),
                            content TEXT NOT NULL,
                            chunk_level VARCHAR(20) NOT NULL,
                            chunk_index INTEGER NOT NULL,
                            char_count INTEGER,
                            word_count INTEGER,
                            sentence_count INTEGER,
                            reading_ease FLOAT,
                            reading_grade FLOAT,
                            keyphrases JSONB,
                            entities JSONB,
                            citations JSONB,
                            content_hash VARCHAR(32),
                            created_at TIMESTAMP DEFAULT NOW(),
                            
                            -- Dr. Chen's indexing strategy
                            UNIQUE(book_id, chunk_level, chunk_index)
                        );
                        
                        -- Indexes for performance (Dr. Chen's expertise)
                        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_book_id 
                            ON semantic_chunks(book_id);
                        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_level 
                            ON semantic_chunks(chunk_level);
                        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_hash 
                            ON semantic_chunks(content_hash);
                        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_keyphrases 
                            ON semantic_chunks USING GIN(keyphrases);
                        CREATE INDEX IF NOT EXISTS idx_semantic_chunks_entities 
                            ON semantic_chunks USING GIN(entities);
                    """)
                    
                    # Insert chunks for each level
                    for level, level_data in chunks_data['chunk_levels'].items():
                        for chunk in level_data['chunks']:
                            cur.execute("""
                                INSERT INTO semantic_chunks 
                                (chunk_id, book_id, content, chunk_level, chunk_index,
                                 char_count, word_count, sentence_count, reading_ease, 
                                 reading_grade, keyphrases, entities, citations, content_hash)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (chunk_id) DO UPDATE SET
                                content = EXCLUDED.content,
                                char_count = EXCLUDED.char_count,
                                word_count = EXCLUDED.word_count,
                                keyphrases = EXCLUDED.keyphrases,
                                entities = EXCLUDED.entities,
                                citations = EXCLUDED.citations
                            """, (
                                chunk['chunk_id'], chunk['book_id'], chunk['content'],
                                chunk['chunk_level'], chunk['chunk_index'],
                                chunk['char_count'], chunk['word_count'], 
                                chunk['sentence_count'], chunk['reading_ease'],
                                chunk['reading_grade'], json.dumps(chunk['keyphrases']),
                                json.dumps(chunk['entities']), json.dumps(chunk['citations']),
                                chunk['content_hash']
                            ))
                    
                    conn.commit()
                    
            self.logger.info(f"✅ Successfully saved semantic chunks for book {chunks_data['book_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save semantic chunks: {e}")
            return False

def main():
    """
    Dr. Sarah Chen's testing and demonstration function.
    """
    print("🏛️ Dr. Sarah Chen (陈雪芳) - Advanced Semantic Chunker")
    print("Database Systems Librarian - LibraryOfBabel")
    print("严格的数据库管理带来优秀的用户体验")
    print()
    
    chunker = AdvancedSemanticChunker()
    
    # Test with a sample book
    test_book_id = 1099  # Use a known book ID
    
    print(f"Testing semantic chunking on book {test_book_id}...")
    results = chunker.process_book_semantic_chunks(test_book_id, ['small', 'medium'])
    
    if 'error' not in results:
        print(f"✅ Successfully processed: {results['title']}")
        print(f"📊 Chunk levels created: {list(results['chunk_levels'].keys())}")
        
        for level, data in results['chunk_levels'].items():
            print(f"   {level}: {data['chunk_count']} chunks")
        
        # Save to database
        if chunker.save_semantic_chunks_to_db(results):
            print("✅ Saved to database successfully")
        else:
            print("❌ Failed to save to database")
    else:
        print(f"❌ Error: {results['error']}")

if __name__ == "__main__":
    main()