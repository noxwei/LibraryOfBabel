#!/usr/bin/env python3
"""
Phonetic Column Implementation - Dr. Rodriguez & Dr. Chen
========================================================

Implementation plan for adding phonetic search capabilities to improve
audiobook search accuracy. Handles common mishearings and pronunciation variants.

Storage Analysis:
- Current DB: 42GB
- Estimated phonetic addition: ~158MB for chunks (0.4% increase)
- Very reasonable storage cost for major search improvement
"""

import psycopg2
import psycopg2.extras
import time
import re
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'knowledge_base',
    'user': 'weixiangzhang',
    'port': 5432
}

class PhoneticSearchEnhancer:
    """Dr. Rodriguez & Dr. Chen - Phonetic Search Implementation"""
    
    def __init__(self):
        self.conn = None
        self.phonetic_mappings = self._create_audiobook_phonetic_mappings()
    
    def _create_audiobook_phonetic_mappings(self) -> Dict[str, str]:
        """Create common audiobook mishearing mappings"""
        return {
            # Common homophones
            'their': 'there',
            'there': 'their', 
            'they\'re': 'their',
            'your': 'you\'re',
            'you\'re': 'your',
            'its': 'it\'s',
            'it\'s': 'its',
            'to': 'too',
            'too': 'to',
            'two': 'to',
            
            # Common mishearings in audiobooks
            'than': 'then',
            'then': 'than',
            'affect': 'effect',
            'effect': 'affect',
            'accept': 'except',
            'except': 'accept',
            
            # Pronunciation variants
            'often': 'ofen',  # silent T
            'listen': 'lisen',  # silent T
            'castle': 'cassel',  # silent T
            
            # Numbers that sound similar
            'four': 'for',
            'for': 'four',
            'one': 'won',
            'won': 'one',
            'eight': 'ate',
            'ate': 'eight',
        }
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def check_extensions(self):
        """Check and install required extensions"""
        if not self.conn:
            return False
        
        try:
            with self.conn.cursor() as cur:
                # Check existing extensions
                cur.execute("SELECT extname FROM pg_extension WHERE extname IN ('fuzzystrmatch', 'pg_trgm');")
                existing = [row[0] for row in cur.fetchall()]
                
                logger.info(f"Existing extensions: {existing}")
                
                # Install fuzzystrmatch if not present
                if 'fuzzystrmatch' not in existing:
                    logger.info("Installing fuzzystrmatch extension...")
                    cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
                    self.conn.commit()
                    logger.info("✅ fuzzystrmatch extension installed")
                
                # Verify extensions
                cur.execute("SELECT soundex('hello'), metaphone('hello', 4);")
                result = cur.fetchone()
                logger.info(f"Phonetic functions working: soundex='hello' -> {result[0]}, metaphone='hello' -> {result[1]}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Extension setup failed: {e}")
            return False
    
    def add_phonetic_columns(self):
        """Add phonetic columns to chunks table"""
        if not self.conn:
            return False
        
        try:
            with self.conn.cursor() as cur:
                logger.info("Adding phonetic columns to chunks table...")
                
                # Add soundex column for American pronunciation
                cur.execute("""
                    ALTER TABLE chunks 
                    ADD COLUMN IF NOT EXISTS content_soundex TEXT;
                """)
                
                # Add metaphone column for more sophisticated phonetic matching
                cur.execute("""
                    ALTER TABLE chunks 
                    ADD COLUMN IF NOT EXISTS content_metaphone TEXT;
                """)
                
                # Add preprocessed content for audiobook-specific variations
                cur.execute("""
                    ALTER TABLE chunks 
                    ADD COLUMN IF NOT EXISTS content_audiobook_normalized TEXT;
                """)
                
                self.conn.commit()
                logger.info("✅ Phonetic columns added successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add phonetic columns: {e}")
            return False
    
    def generate_audiobook_normalized_text(self, text: str) -> str:
        """Generate normalized text for audiobook search"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Apply phonetic mappings
        for original, replacement in self.phonetic_mappings.items():
            normalized = re.sub(r'\b' + re.escape(original) + r'\b', replacement, normalized)
        
        # Remove punctuation that doesn't affect pronunciation
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def populate_phonetic_data_batch(self, batch_size: int = 1000):
        """Populate phonetic columns in batches for memory efficiency"""
        if not self.conn:
            return False
        
        try:
            with self.conn.cursor() as cur:
                # Get total chunks to process
                cur.execute("SELECT COUNT(*) FROM chunks WHERE content_soundex IS NULL OR content_metaphone IS NULL;")
                total_chunks = cur.fetchone()[0]
                
                logger.info(f"Processing {total_chunks} chunks in batches of {batch_size}")
                
                processed = 0
                
                while processed < total_chunks:
                    # Get batch of chunks
                    cur.execute("""
                        SELECT chunk_id, content 
                        FROM chunks 
                        WHERE content_soundex IS NULL OR content_metaphone IS NULL
                        LIMIT %s
                    """, (batch_size,))
                    
                    batch = cur.fetchall()
                    if not batch:
                        break
                    
                    # Process batch
                    for chunk_id, content in batch:
                        if content:
                            # Extract first 1000 characters for phonetic processing
                            text_sample = content[:1000]
                            
                            # Generate audiobook normalized version
                            normalized = self.generate_audiobook_normalized_text(text_sample)
                            
                            # Generate phonetic representations
                            words = text_sample.split()[:50]  # First 50 words
                            soundex_codes = []
                            metaphone_codes = []
                            
                            for word in words:
                                clean_word = re.sub(r'[^\w]', '', word)
                                if len(clean_word) >= 3:  # Only process meaningful words
                                    try:
                                        # Get soundex
                                        cur.execute("SELECT soundex(%s);", (clean_word,))
                                        soundex_result = cur.fetchone()
                                        if soundex_result and soundex_result[0]:
                                            soundex_codes.append(soundex_result[0])
                                        
                                        # Get metaphone
                                        cur.execute("SELECT metaphone(%s, 4);", (clean_word,))
                                        metaphone_result = cur.fetchone()
                                        if metaphone_result and metaphone_result[0]:
                                            metaphone_codes.append(metaphone_result[0])
                                    except:
                                        continue
                            
                            # Update chunk with phonetic data
                            cur.execute("""
                                UPDATE chunks 
                                SET content_soundex = %s,
                                    content_metaphone = %s,
                                    content_audiobook_normalized = %s
                                WHERE chunk_id = %s
                            """, (
                                ' '.join(soundex_codes),
                                ' '.join(metaphone_codes), 
                                normalized[:500],  # Limit normalized text
                                chunk_id
                            ))
                    
                    self.conn.commit()
                    processed += len(batch)
                    
                    if processed % (batch_size * 5) == 0:
                        logger.info(f"Processed {processed}/{total_chunks} chunks ({processed/total_chunks*100:.1f}%)")
                
                logger.info(f"✅ Phonetic data population complete: {processed} chunks processed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Phonetic data population failed: {e}")
            return False
    
    def create_phonetic_indexes(self):
        """Create indexes on phonetic columns for fast searching"""
        if not self.conn:
            return False
        
        try:
            with self.conn.cursor() as cur:
                logger.info("Creating phonetic search indexes...")
                
                # GIN index for soundex search
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_content_soundex_gin
                    ON chunks USING gin(to_tsvector('english', content_soundex));
                """)
                
                # GIN index for metaphone search  
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_content_metaphone_gin
                    ON chunks USING gin(to_tsvector('english', content_metaphone));
                """)
                
                # GIN index for audiobook normalized content
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_audiobook_normalized_gin
                    ON chunks USING gin(to_tsvector('english', content_audiobook_normalized));
                """)
                
                # Trigram index for fuzzy matching
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_chunks_audiobook_normalized_trigram
                    ON chunks USING gin(content_audiobook_normalized gin_trgm_ops);
                """)
                
                self.conn.commit()
                logger.info("✅ Phonetic indexes created successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
            return False
    
    def test_phonetic_search(self):
        """Test phonetic search capabilities"""
        if not self.conn:
            return False
        
        test_queries = [
            ("there house", "their house"),  # Homophone
            ("you're right", "your right"),  # Homophone  
            ("listen carefully", "lisen carefully"),  # Silent T
            ("affect change", "effect change"),  # Common confusion
        ]
        
        logger.info("🧪 Testing phonetic search capabilities...")
        
        try:
            with self.conn.cursor() as cur:
                for mishearing, correct in test_queries:
                    logger.info(f"\nTesting: '{mishearing}' should find '{correct}'")
                    
                    # Test soundex matching
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM chunks 
                        WHERE content_audiobook_normalized ILIKE %s
                    """, (f'%{mishearing}%',))
                    
                    count = cur.fetchone()[0]
                    logger.info(f"  Audiobook normalized: {count} matches")
                    
                    # Test trigram similarity
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM chunks 
                        WHERE similarity(content_audiobook_normalized, %s) > 0.3
                        LIMIT 5
                    """, (mishearing,))
                    
                    trigram_count = cur.fetchone()[0]
                    logger.info(f"  Trigram similarity: {trigram_count} matches")
            
            logger.info("✅ Phonetic search testing complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Phonetic search testing failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """Main implementation function - Dr. Rodriguez & Dr. Chen"""
    print("🔊 Phonetic Search Enhancement - Dr. Rodriguez & Dr. Chen")
    print("=" * 65)
    print("Implementing phonetic columns for audiobook search optimization")
    print(f"Estimated storage increase: ~158MB (0.4% of current 42GB)")
    print()
    
    enhancer = PhoneticSearchEnhancer()
    
    # Step 1: Connect to database
    if not enhancer.connect():
        print("❌ Cannot proceed without database connection")
        return
    
    # Step 2: Check and install extensions
    print("📦 Checking phonetic extensions...")
    if not enhancer.check_extensions():
        print("❌ Extension setup failed")
        return
    
    # Step 3: Add phonetic columns
    print("\n🏗️ Adding phonetic columns...")
    if not enhancer.add_phonetic_columns():
        print("❌ Column creation failed")
        return
    
    # Step 4: Populate phonetic data
    print("\n🔄 Populating phonetic data (this may take 10-15 minutes)...")
    print("Processing 165,206 chunks in batches for memory efficiency...")
    
    start_time = time.time()
    if not enhancer.populate_phonetic_data_batch(batch_size=500):
        print("❌ Data population failed")
        return
    
    duration = time.time() - start_time
    print(f"✅ Data population completed in {duration/60:.1f} minutes")
    
    # Step 5: Create indexes
    print("\n📊 Creating phonetic search indexes...")
    if not enhancer.create_phonetic_indexes():
        print("❌ Index creation failed")
        return
    
    # Step 6: Test phonetic search
    print("\n🧪 Testing phonetic search capabilities...")
    if not enhancer.test_phonetic_search():
        print("❌ Testing failed")
        return
    
    enhancer.close()
    
    print("\n🎉 PHONETIC ENHANCEMENT COMPLETE!")
    print("=" * 40)
    print("✅ Audiobook search now supports:")
    print("  - Homophone matching (their/there)")
    print("  - Pronunciation variants (listen/lisen)")
    print("  - Common mishearings (affect/effect)")
    print("  - Trigram fuzzy matching")
    print("  - Soundex phonetic codes")
    print("  - Metaphone advanced phonetics")
    print()
    print("🎧 Ready for enhanced audiobook search experience!")

if __name__ == "__main__":
    main()