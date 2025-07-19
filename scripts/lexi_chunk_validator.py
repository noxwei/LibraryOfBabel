#!/usr/bin/env python3
"""
🎧 Dr. Alexandra "Lexi" Hartwell - Chunk-by-Chunk TTS Validator
================================================================

Processes Eve Babitz "Slow Days, Fast Company" chunk by chunk with validation
and cleaning before TTS generation.
"""

import os
import re
import json
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime

class LexiChunkValidator:
    """
    Chunk-by-chunk TTS validation and processing system
    """
    
    def __init__(self):
        self.name = "Dr. Alexandra \"Lexi\" Hartwell"
        self.title = "Audio Synthesis Agent"
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'port': 5432
        }
        
        # Eve Babitz book configuration
        self.target_book_id = 1015
        self.book_title = "Slow Days, Fast Company"
        self.author = "Eve Babitz"
        
        # Output directories
        self.audio_output_dir = Path("audio/synthesis/eve_babitz")
        self.validation_log_dir = Path("audio/validation_logs")
        
        # Create directories
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_log_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🎧 {self.name} - Chunk Validator Initialized")
        print(f"📚 Target: {self.book_title} by {self.author} (Book ID: {self.target_book_id})")
        print(f"🎵 Audio Output: {self.audio_output_dir}")
        
    def get_db_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except psycopg2.Error as e:
            print(f"❌ Database connection failed: {e}")
            return None
    
    def get_eve_babitz_chunks(self):
        """Retrieve all chunks for Eve Babitz book"""
        with self.get_db_connection() as conn:
            if not conn:
                return []
                
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT chunk_id, content, word_count, chapter_number, 
                           section_number, paragraph_number
                    FROM chunks 
                    WHERE book_id = %s 
                    ORDER BY chapter_number, section_number, paragraph_number;
                """, (self.target_book_id,))
                
                chunks = cur.fetchall()
                print(f"📊 Retrieved {len(chunks)} chunks from {self.book_title}")
                return chunks
    
    def clean_chunk_text(self, raw_text):
        """Clean text artifacts for TTS processing"""
        
        # Store original for comparison
        original_length = len(raw_text)
        
        # Remove common formatting artifacts
        cleaned = re.sub(r'\[.*?\]', '', raw_text)           # [page numbers, footnotes]
        cleaned = re.sub(r'\{.*?\}', '', cleaned)            # {editorial notes}
        cleaned = re.sub(r'__{2,}', ' ', cleaned)            # multiple underscores
        cleaned = re.sub(r'--{2,}', ' — ', cleaned)          # multiple dashes to em-dash
        
        # Fix character encoding issues (common OCR problems)
        encoding_fixes = {
            'â€™': "'",     # smart apostrophe
            'â€œ': '"',     # smart quote open
            'â€': '"',      # smart quote close
            'â€"': '—',     # em dash
            'â€¦': '...',   # ellipsis
            'Ã¡': 'á',     # accented a
            'Ã©': 'é',     # accented e
            'Ã­': 'í',     # accented i
            'Ã³': 'ó',     # accented o
            'Ãº': 'ú',     # accented u
        }
        
        for bad, good in encoding_fixes.items():
            cleaned = cleaned.replace(bad, good)
        
        # Remove OCR artifacts and weird characters
        cleaned = re.sub(r'\b[A-Z]{4,}\b', '', cleaned)      # RANDOM ALL CAPS WORDS
        cleaned = re.sub(r'[^\w\s\.,!?;:\-\'"()—…]+', '', cleaned)  # strange characters
        
        # Fix spacing issues
        cleaned = re.sub(r'\s+', ' ', cleaned)               # multiple spaces
        cleaned = re.sub(r'\s+([,.!?;:])', r'\1', cleaned)   # space before punctuation
        
        # Clean up
        cleaned = cleaned.strip()
        
        # Log cleaning results
        cleaned_length = len(cleaned)
        chars_removed = original_length - cleaned_length
        
        return {
            'original_text': raw_text,
            'cleaned_text': cleaned,
            'original_length': original_length,
            'cleaned_length': cleaned_length,
            'chars_removed': chars_removed,
            'cleaning_ratio': chars_removed / original_length if original_length > 0 else 0
        }
    
    def validate_chunk_quality(self, cleaning_result):
        """Assess chunk quality for TTS suitability"""
        
        text = cleaning_result['cleaned_text']
        
        # Quality metrics
        quality_report = {
            'word_count': len(text.split()),
            'sentence_count': len(re.findall(r'[.!?]+', text)),
            'has_dialogue': '"' in text or "'" in text,
            'avg_sentence_length': 0,
            'readability_score': 'unknown',
            'tts_suitability': 'unknown',
            'issues': []
        }
        
        # Calculate average sentence length
        sentences = re.split(r'[.!?]+', text)
        if sentences:
            total_words = sum(len(sentence.split()) for sentence in sentences if sentence.strip())
            quality_report['avg_sentence_length'] = total_words / len(sentences)
        
        # Check for potential TTS issues
        if quality_report['word_count'] < 10:
            quality_report['issues'].append("Very short chunk - may not be substantial")
        
        if quality_report['word_count'] > 5000:
            quality_report['issues'].append("Very long chunk - consider splitting")
        
        if quality_report['avg_sentence_length'] > 50:
            quality_report['issues'].append("Very long sentences - may affect TTS flow")
        
        # Overall TTS suitability
        if len(quality_report['issues']) == 0:
            quality_report['tts_suitability'] = 'excellent'
        elif len(quality_report['issues']) <= 2:
            quality_report['tts_suitability'] = 'good'
        else:
            quality_report['tts_suitability'] = 'needs_review'
        
        return quality_report
    
    def process_first_chunk(self):
        """Process and validate the first chunk for review"""
        
        print(f"\n🎯 PROCESSING FIRST CHUNK - {self.book_title}")
        print("=" * 60)
        
        # Get chunks
        chunks = self.get_eve_babitz_chunks()
        
        if not chunks:
            print("❌ No chunks found for Eve Babitz book")
            return None
        
        # Process first chunk
        first_chunk = chunks[0]
        chunk_id = first_chunk['chunk_id']
        
        print(f"📖 Processing Chunk ID: {chunk_id}")
        print(f"📊 Chapter {first_chunk['chapter_number']}, Section {first_chunk['section_number']}")
        print(f"📝 Original word count: {first_chunk['word_count']}")
        
        # Clean the text
        cleaning_result = self.clean_chunk_text(first_chunk['content'])
        
        print(f"\n🧹 TEXT CLEANING RESULTS:")
        print(f"   Original length: {cleaning_result['original_length']} chars")
        print(f"   Cleaned length: {cleaning_result['cleaned_length']} chars")
        print(f"   Characters removed: {cleaning_result['chars_removed']}")
        print(f"   Cleaning ratio: {cleaning_result['cleaning_ratio']:.1%}")
        
        # Validate quality
        quality_report = self.validate_chunk_quality(cleaning_result)
        
        print(f"\n📊 QUALITY ASSESSMENT:")
        print(f"   Word count: {quality_report['word_count']}")
        print(f"   Sentence count: {quality_report['sentence_count']}")
        print(f"   Has dialogue: {quality_report['has_dialogue']}")
        print(f"   Avg sentence length: {quality_report['avg_sentence_length']:.1f} words")
        print(f"   TTS Suitability: {quality_report['tts_suitability']}")
        
        if quality_report['issues']:
            print(f"   ⚠️ Issues found:")
            for issue in quality_report['issues']:
                print(f"      - {issue}")
        
        # Show text preview
        preview_text = cleaning_result['cleaned_text'][:200]
        print(f"\n📖 CLEANED TEXT PREVIEW:")
        print(f"   \"{preview_text}{'...' if len(cleaning_result['cleaned_text']) > 200 else ''}\"")
        
        # Save validation log
        validation_log = {
            'timestamp': datetime.now().isoformat(),
            'chunk_id': chunk_id,
            'book_title': self.book_title,
            'author': self.author,
            'chapter_number': first_chunk['chapter_number'],
            'cleaning_result': cleaning_result,
            'quality_report': quality_report,
            'processed_by': self.name
        }
        
        log_file = self.validation_log_dir / f"chunk_{chunk_id}_validation.json"
        with open(log_file, 'w') as f:
            json.dump(validation_log, f, indent=2)
        
        print(f"\n💾 Validation log saved: {log_file}")
        print(f"\n🎯 READY FOR REVIEW: First chunk processed and validated!")
        print(f"   Next step: Generate TTS audio for chunk {chunk_id}")
        
        return {
            'chunk_id': chunk_id,
            'cleaned_text': cleaning_result['cleaned_text'],
            'quality_report': quality_report,
            'validation_log_path': log_file
        }

def main():
    """Main processing function"""
    print("🚀 Starting Lexi's Chunk-by-Chunk TTS Validator...")
    
    validator = LexiChunkValidator()
    
    # Process first chunk
    result = validator.process_first_chunk()
    
    if result:
        print(f"\n✅ SUCCESS: First chunk ready for TTS generation!")
        print(f"🎧 Chunk ID: {result['chunk_id']}")
        print(f"📝 Text length: {len(result['cleaned_text'])} characters")
        print(f"🎯 Quality: {result['quality_report']['tts_suitability']}")
        print(f"\n📋 Next: Review output and approve TTS generation")
    else:
        print(f"\n❌ FAILED: Could not process first chunk")
    
    return result

if __name__ == "__main__":
    main()