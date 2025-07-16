#!/usr/bin/env python3
"""
🚀 PHASE 2C: MULTI-MODEL VECTOR RE-EMBEDDING WITH INTELLIGENT ROUTING
====================================================================

Re-embed the entire book collection using different embedding models based on content specifics:
- Technical/Academic: granite-embedding:278m (precise, factual)
- Fiction/Creative: bge-m3:latest (semantic, narrative understanding)  
- Cross-lingual: mxbai-embed-large:latest (multilingual content)
- General: nomic-embed-text:latest (fallback, broad coverage)

Features:
- Content-type classification for optimal model selection
- Batch processing with progress tracking
- Database updates with routing metadata
- Resume capability across restarts
- Performance analytics and comparison
"""

import os
import sys
import json
import time
import logging
import requests
import psycopg2
import psycopg2.extras
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from config.api_config import get_database_config

@dataclass
class EmbeddingModelConfig:
    """Configuration for embedding models"""
    name: str
    ollama_name: str
    dimensions: int
    specialization: str
    description: str
    use_cases: List[str]

class Phase2CMultiModelEmbedder:
    """
    🚀 Phase 2C: Multi-Model Vector Re-Embedding System
    
    Intelligently routes content to optimal embedding models based on:
    - Content type (technical, creative, academic, multilingual)
    - Genre classification
    - Language detection
    - Content complexity analysis
    """
    
    def __init__(self):
        self.embedder_dir = project_root / "logs" / "phase2c"
        self.embedder_dir.mkdir(parents=True, exist_ok=True)
        
        self.state_file = self.embedder_dir / "phase2c_state.json"
        self.log_file = self.embedder_dir / "phase2c_embedder.log"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("Phase2C")
        
        # Configuration
        self.ollama_base_url = "http://localhost:11434"
        self.db_config = get_database_config()
        
        # Multi-model configuration
        self.embedding_models = {
            "granite": EmbeddingModelConfig(
                name="granite",
                ollama_name="granite-embedding:278m",
                dimensions=768,
                specialization="technical_academic",
                description="Precise factual embedding for technical/academic content",
                use_cases=["Science & Technology", "Academic", "Philosophy", "Business & Economics"]
            ),
            "bge": EmbeddingModelConfig(
                name="bge",
                ollama_name="bge-m3:latest", 
                dimensions=1024,
                specialization="semantic_narrative",
                description="Rich semantic understanding for creative/narrative content",
                use_cases=["Fantasy", "Science Fiction", "Romance", "Literary Fiction", "Historical Fiction"]
            ),
            "mxbai": EmbeddingModelConfig(
                name="mxbai",
                ollama_name="mxbai-embed-large:latest",
                dimensions=1024,
                specialization="multilingual",
                description="Multilingual embedding for diverse language content",
                use_cases=["History", "Cultural Studies", "Biography & Memoir", "Travel"]
            ),
            "nomic": EmbeddingModelConfig(
                name="nomic",
                ollama_name="nomic-embed-text:latest",
                dimensions=768,
                specialization="general",
                description="General-purpose embedding with broad coverage",
                use_cases=["Mystery & Thriller", "Self-Help", "Psychology", "Reference"]
            )
        }
        
        # Processing parameters
        self.batch_size = 1  # Process 1 book at a time for stability  
        self.delay_between_batches = 1  # Seconds between batches
        self.delay_between_chunks = 0.2  # Seconds between chunk embeddings
        self.retry_attempts = 3
        
        # Load state
        self.state = self.load_state()
        
        self.logger.info("🚀 Phase 2C Multi-Model Embedder initialized")
        self.logger.info(f"📊 Available models: {list(self.embedding_models.keys())}")

    def load_state(self) -> Dict:
        """Load embedder state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.logger.info(f"📁 Loaded state: {state['books_processed']} books processed")
                    return state
            except Exception as e:
                self.logger.error(f"Failed to load state: {e}")
        
        # Default state
        return {
            "books_processed": 0,
            "books_successful": 0,
            "books_failed": 0,
            "last_book_id": None,
            "session_start": datetime.now().isoformat(),
            "total_runtime": 0,
            "model_usage": {model: 0 for model in self.embedding_models.keys()},
            "failed_book_ids": [],
            "phase": "2C",
            "version": "1.0"
        }

    def save_state(self):
        """Save current embedder state"""
        try:
            self.state["last_updated"] = datetime.now().isoformat()
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")

    def get_db_connection(self):
        """Get database connection with retry logic"""
        for attempt in range(3):
            try:
                return psycopg2.connect(**self.db_config)
            except psycopg2.Error as e:
                self.logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
        return None

    def classify_content_type(self, book: Dict) -> str:
        """Classify book content type for optimal model selection"""
        
        title = (book.get('title') or '').lower()
        genre = (book.get('genre') or '').lower() 
        description = (book.get('description') or '').lower()
        
        # Technical/Academic content indicators
        technical_keywords = [
            'technology', 'science', 'research', 'analysis', 'theory', 'methodology',
            'academic', 'scholarly', 'technical', 'engineering', 'mathematics',
            'physics', 'chemistry', 'biology', 'computer', 'algorithm'
        ]
        
        # Creative/Narrative content indicators  
        narrative_keywords = [
            'story', 'novel', 'fiction', 'fantasy', 'adventure', 'romance',
            'character', 'plot', 'narrative', 'tale', 'saga', 'epic'
        ]
        
        # Multilingual/Cultural content indicators
        cultural_keywords = [
            'culture', 'cultural', 'international', 'global', 'world', 'foreign',
            'translation', 'history', 'memoir', 'biography', 'travel', 'ethnography'
        ]
        
        combined_text = f"{title} {genre} {description}"
        
        # Count keyword matches
        technical_score = sum(1 for kw in technical_keywords if kw in combined_text)
        narrative_score = sum(1 for kw in narrative_keywords if kw in combined_text)
        cultural_score = sum(1 for kw in cultural_keywords if kw in combined_text)
        
        # Genre-based classification
        if genre:
            granite_genres = ['philosophy', 'science', 'technology', 'academic', 'business', 'economics']
            bge_genres = ['fiction', 'fantasy', 'science fiction', 'romance', 'literary']
            mxbai_genres = ['history', 'cultural', 'biography', 'memoir', 'travel']
            
            if any(g in genre for g in granite_genres):
                return "technical_academic"
            elif any(g in genre for g in bge_genres):
                return "semantic_narrative"
            elif any(g in genre for g in mxbai_genres):
                return "multilingual"
        
        # Keyword-based classification
        if technical_score >= narrative_score and technical_score >= cultural_score:
            return "technical_academic"
        elif narrative_score >= cultural_score:
            return "semantic_narrative"
        elif cultural_score > 0:
            return "multilingual"
        else:
            return "general"

    def select_optimal_model(self, book: Dict) -> str:
        """Select optimal embedding model based on content classification"""
        
        content_type = self.classify_content_type(book)
        
        # Map content types to models (temporarily using bge/mxbai for reliability)
        model_mapping = {
            "technical_academic": "bge",  # Temporary: using bge instead of granite
            "semantic_narrative": "bge", 
            "multilingual": "mxbai",
            "general": "nomic"
        }
        
        selected_model = model_mapping.get(content_type, "nomic")
        
        book_id = book.get('book_id', 'test')
        self.logger.debug(f"Book {book_id}: {content_type} -> {selected_model}")
        return selected_model

    def generate_embedding(self, text: str, model_key: str) -> Optional[List[float]]:
        """Generate embedding using specified model"""
        
        model_config = self.embedding_models[model_key]
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={
                        "model": model_config.ollama_name,
                        "prompt": text
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    embedding = response.json().get('embedding')
                    if embedding and len(embedding) == model_config.dimensions:
                        return embedding
                    else:
                        self.logger.warning(f"Invalid embedding dimensions from {model_key}")
                else:
                    self.logger.warning(f"API error from {model_key}: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout from {model_key}, attempt {attempt + 1}")
            except Exception as e:
                self.logger.warning(f"Error from {model_key}: {e}, attempt {attempt + 1}")
            
            if attempt < self.retry_attempts - 1:
                time.sleep(5)
        
        return None

    def process_book_chunks(self, book: Dict) -> bool:
        """Process all chunks for a book with optimal model"""
        
        book_id = book['book_id']
        optimal_model = self.select_optimal_model(book)
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get all chunks for this book
                    cur.execute("""
                        SELECT c.chunk_id, c.content, c.chapter_number as chunk_index
                        FROM chunks c 
                        WHERE c.book_id = %s 
                        ORDER BY c.chunk_id
                    """, (book_id,))
                    
                    chunks = cur.fetchall()
                    if not chunks:
                        self.logger.warning(f"No chunks found for book {book_id}")
                        return False
                    
                    self.logger.info(f"📖 Processing {len(chunks)} chunks for book {book_id} with {optimal_model}")
                    
                    updated_chunks = 0
                    for chunk in chunks:
                        # Generate new embedding
                        embedding = self.generate_embedding(chunk['content'], optimal_model)
                        
                        if embedding:
                            # Update chunk with new embedding and model info
                            cur.execute("""
                                UPDATE chunk_embeddings 
                                SET 
                                    embedding = %s,
                                    embedding_model = %s,
                                    embedding_dimension = %s,
                                    content_type = %s,
                                    routing_reason = %s
                                WHERE chunk_id = %s
                            """, (
                                json.dumps(embedding),
                                optimal_model,
                                self.embedding_models[optimal_model].dimensions,
                                self.classify_content_type(book),
                                f"Phase2C-{optimal_model}",
                                chunk['chunk_id']
                            ))
                            updated_chunks += 1
                            
                            # Throttle between chunk embeddings
                            time.sleep(self.delay_between_chunks)
                        else:
                            self.logger.error(f"Failed to generate embedding for chunk {chunk['chunk_id']}")
                    
                    conn.commit()
                    
                    if updated_chunks == len(chunks):
                        self.logger.info(f"✅ Successfully updated {updated_chunks} chunks for book {book_id}")
                        return True
                    else:
                        self.logger.warning(f"⚠️ Only updated {updated_chunks}/{len(chunks)} chunks for book {book_id}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Failed to process book {book_id}: {e}")
            return False

    def get_next_books(self) -> List[Dict]:
        """Get next batch of books to re-embed"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get books that need re-embedding
                    where_clause = "WHERE 1=1"
                    
                    # Exclude previously failed books
                    if self.state["failed_book_ids"]:
                        failed_ids = ','.join(map(str, self.state["failed_book_ids"]))
                        where_clause += f" AND b.book_id NOT IN ({failed_ids})"
                    
                    # Resume from last position
                    if self.state["last_book_id"]:
                        where_clause += f" AND b.book_id > {self.state['last_book_id']}"
                    
                    cur.execute(f"""
                        SELECT DISTINCT b.book_id, b.title, b.author, b.genre, b.description, b.word_count
                        FROM books b
                        INNER JOIN chunk_embeddings ce ON b.book_id = ce.book_id
                        {where_clause}
                        ORDER BY b.book_id ASC
                        LIMIT %s
                    """, (self.batch_size,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch books: {e}")
            return []

    def run_phase2c_embedding(self):
        """Main Phase 2C re-embedding process"""
        
        self.logger.info("🚀 Starting Phase 2C Multi-Model Re-Embedding")
        self.logger.info(f"📊 Current progress: {self.state['books_processed']} books processed")
        
        while True:
            # Get next batch of books
            books = self.get_next_books()
            
            if not books:
                self.logger.info("✅ Phase 2C re-embedding complete - no more books to process!")
                break
            
            # Process each book in the batch
            for book in books:
                book_id = book['book_id']
                title = book.get('title', 'Unknown')[:50]
                
                self.logger.info(f"📚 Processing book {book_id}: {title}")
                
                start_time = time.time()
                
                # Determine optimal model and process
                optimal_model = self.select_optimal_model(book)
                success = self.process_book_chunks(book)
                
                processing_time = time.time() - start_time
                
                if success:
                    self.state["books_successful"] += 1
                    self.state["model_usage"][optimal_model] += 1
                    self.logger.info(f"   ✅ Re-embedded with {optimal_model} ({processing_time:.1f}s)")
                else:
                    self.state["books_failed"] += 1
                    self.state["failed_book_ids"].append(book_id)
                    self.logger.error(f"   ❌ Failed re-embedding ({processing_time:.1f}s)")
                
                # Update state
                self.state["books_processed"] += 1
                self.state["last_book_id"] = book_id
                self.state["total_runtime"] += processing_time
                
                # Save state periodically
                if self.state["books_processed"] % 5 == 0:
                    self.save_state()
                    success_rate = (self.state["books_successful"] / self.state["books_processed"] * 100)
                    self.logger.info(f"📊 Progress: {self.state['books_processed']} books, {success_rate:.1f}% success rate")
                    
                    # Show model usage distribution
                    self.logger.info(f"🎯 Model usage: {dict(self.state['model_usage'])}")
            
            # Delay between batches
            time.sleep(self.delay_between_batches)
        
        # Final save and summary
        self.save_state()
        self.logger.info("🏁 Phase 2C Multi-Model Re-Embedding Complete!")
        self.print_summary()

    def print_summary(self):
        """Print final summary of Phase 2C re-embedding"""
        
        total_books = self.state["books_processed"]
        successful = self.state["books_successful"]
        failed = self.state["books_failed"]
        success_rate = (successful / total_books * 100) if total_books > 0 else 0
        
        print("\n" + "="*60)
        print("🚀 PHASE 2C MULTI-MODEL RE-EMBEDDING SUMMARY")
        print("="*60)
        print(f"📊 Books Processed: {total_books}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️ Total Runtime: {self.state['total_runtime']:.1f}s")
        
        if total_books > 0:
            avg_time = self.state['total_runtime'] / total_books
            print(f"⚡ Avg Time/Book: {avg_time:.1f}s")
        
        print("\n🎯 MODEL USAGE DISTRIBUTION:")
        for model, count in self.state['model_usage'].items():
            if count > 0:
                config = self.embedding_models[model]
                percentage = (count / successful * 100) if successful > 0 else 0
                print(f"  {model:>6s}: {count:>3d} books ({percentage:>5.1f}%) - {config.specialization}")
        
        print(f"\n📁 State File: {self.state_file}")
        print(f"📋 Log File: {self.log_file}")
        print("="*60)

def main():
    """Main Phase 2C entry point"""
    
    embedder = Phase2CMultiModelEmbedder()
    
    try:
        embedder.run_phase2c_embedding()
    except KeyboardInterrupt:
        embedder.logger.info("🛑 Phase 2C interrupted by user")
        embedder.save_state()
    except Exception as e:
        embedder.logger.error(f"💥 Phase 2C crashed: {e}")
        embedder.save_state()
        raise

if __name__ == "__main__":
    main()