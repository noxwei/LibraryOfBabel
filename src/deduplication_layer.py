#!/usr/bin/env python3
"""
📚 DEDUPLICATION LAYER - LibraryOfBabel DBA Team Solution
=========================================================

Multi-level deduplication system to prevent duplicate book ingestion:
1. Title + Author fuzzy matching
2. File path duplicate detection  
3. ISBN validation
4. Content hash comparison
5. Metadata fingerprinting

Designed by DBA Team:
- Dr. Sarah Chen: Database integrity & constraints
- Dr. Marcus Thompson: Content comparison algorithms  
- Dr. Elena Rodriguez: Performance optimization
- Dr. James Park: Pipeline integration

Supervised by: Linda Zhang (张丽娜) - HR Manager
"""

import os
import hashlib
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import difflib
import re
from pathlib import Path

# Import for content extraction
try:
    from epub_processor import BookMetadata, ChapterInfo
except ImportError:
    from src.epub_processor import BookMetadata, ChapterInfo

@dataclass
class DuplicateMatch:
    """Represents a potential duplicate match."""
    book_id: int
    match_type: str  # 'title_author', 'file_path', 'isbn', 'content_hash'
    confidence: float  # 0.0 to 1.0
    existing_title: str
    existing_author: str
    existing_file_path: str
    match_details: str

class DeduplicationLayer:
    """
    📚 DBA Team Deduplication System
    
    Multi-layered approach to prevent duplicate book ingestion:
    - Level 1: Exact matches (file path, ISBN)
    - Level 2: Fuzzy matches (title + author similarity)  
    - Level 3: Content analysis (hash comparison)
    - Level 4: Metadata fingerprinting
    """
    
    def __init__(self, db_config: Dict):
        """Initialize deduplication system"""
        self.db_config = db_config
        
        # Similarity thresholds (configurable by DBA team)
        self.title_similarity_threshold = 0.85  # Dr. Marcus recommendation
        self.author_similarity_threshold = 0.90  # Dr. Marcus recommendation
        self.combined_similarity_threshold = 0.88  # Dr. Elena optimization
        
        # Content analysis settings
        self.content_sample_size = 5000  # First 5KB for hash comparison
        self.enable_content_hashing = True  # Dr. Sarah toggle
        
        # Performance settings (Dr. Elena optimizations)
        self.max_comparison_batch = 100  # Limit comparisons per check
        self.cache_recent_checks = True
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("DeduplicationLayer")
        
        # DBA team member identification
        self.team_signature = "DBA_TEAM_v1.0"
        
        self.logger.info("📚 DBA Team Deduplication Layer initialized")
        self.logger.info(f"🎯 Title similarity threshold: {self.title_similarity_threshold}")
        self.logger.info(f"🎯 Author similarity threshold: {self.author_similarity_threshold}")
        self.logger.info(f"🎯 Combined threshold: {self.combined_similarity_threshold}")
    
    def get_db_connection(self):
        """Get database connection (Dr. Sarah's method)"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def generate_content_md5(self, chapters: List[ChapterInfo]) -> str:
        """Generate MD5 hash of book content (Dr. Sarah Chen's method)"""
        if not chapters:
            return ""
        
        # Combine all chapter content for consistent hashing
        combined_content = ""
        for chapter in sorted(chapters, key=lambda c: c.spine_order):
            combined_content += f"CHAPTER_{chapter.spine_order}:{chapter.title}\n{chapter.content}\n"
        
        # Generate MD5 hash
        content_bytes = combined_content.encode('utf-8')
        md5_hash = hashlib.md5(content_bytes).hexdigest()
        
        self.logger.info(f"📊 Generated MD5 hash: {md5_hash} (content size: {len(content_bytes):,} bytes)")
        return md5_hash
    
    def check_for_duplicates(self, metadata: BookMetadata, chapters: List[ChapterInfo]) -> List[DuplicateMatch]:
        """
        🔍 Multi-level duplicate detection
        
        Returns list of potential duplicates with confidence scores.
        Empty list means no duplicates found - safe to ingest.
        """
        duplicates = []
        
        self.logger.info(f"🔍 DBA Team checking for duplicates: '{metadata.title}' by {metadata.author}")
        
        # Generate content MD5 hash first (Dr. Sarah's priority)
        content_md5 = self.generate_content_md5(chapters)
        
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    self.logger.error("❌ Cannot check duplicates - database unavailable")
                    return []
                
                # Level 1: Exact matches including MD5 (Dr. Sarah's constraints)
                exact_duplicates = self._check_exact_matches(conn, metadata, content_md5)
                duplicates.extend(exact_duplicates)
                
                # Level 2: Fuzzy title/author matches (Dr. Marcus's algorithms)
                fuzzy_duplicates = self._check_fuzzy_matches(conn, metadata)
                duplicates.extend(fuzzy_duplicates)
                
                # Level 3: Content hash comparison (Dr. James's processing)
                if self.enable_content_hashing and chapters:
                    content_duplicates = self._check_content_matches(conn, metadata, chapters)
                    duplicates.extend(content_duplicates)
                
                # Level 4: Advanced metadata fingerprinting (Dr. Elena's optimization)
                metadata_duplicates = self._check_metadata_fingerprint(conn, metadata)
                duplicates.extend(metadata_duplicates)
        
        except Exception as e:
            self.logger.error(f"❌ Duplicate checking failed: {e}")
            return []
        
        # Remove duplicates from duplicates list and sort by confidence
        unique_duplicates = self._deduplicate_matches(duplicates)
        unique_duplicates.sort(key=lambda x: x.confidence, reverse=True)
        
        if unique_duplicates:
            self.logger.warning(f"⚠️ Found {len(unique_duplicates)} potential duplicates")
            for dup in unique_duplicates:
                self.logger.warning(f"   📚 {dup.match_type}: {dup.confidence:.2f} confidence - {dup.match_details}")
        else:
            self.logger.info("✅ No duplicates found - safe to ingest")
        
        return unique_duplicates
    
    def _check_exact_matches(self, conn, metadata: BookMetadata, content_md5: str = None) -> List[DuplicateMatch]:
        """Level 1: Check for exact matches (Dr. Sarah Chen's implementation)"""
        duplicates = []
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Check MD5 hash duplicates (HIGHEST PRIORITY - Dr. Sarah's requirement)
            if content_md5:
                cur.execute("""
                    SELECT book_id, title, author, file_path, md5_hash
                    FROM books 
                    WHERE md5_hash = %s
                """, (content_md5,))
                
                for row in cur.fetchall():
                    duplicates.append(DuplicateMatch(
                        book_id=row['book_id'],
                        match_type='md5_hash',
                        confidence=1.0,  # Perfect content match
                        existing_title=row['title'],
                        existing_author=row['author'] or 'Unknown',
                        existing_file_path=row['file_path'] or '',
                        match_details=f"Identical content MD5: {content_md5}"
                    ))
            
            # Check file path duplicates
            if metadata.file_path:
                cur.execute("""
                    SELECT book_id, title, author, file_path
                    FROM books 
                    WHERE file_path = %s
                """, (metadata.file_path,))
                
                for row in cur.fetchall():
                    duplicates.append(DuplicateMatch(
                        book_id=row['book_id'],
                        match_type='file_path',
                        confidence=1.0,  # Exact match
                        existing_title=row['title'],
                        existing_author=row['author'] or 'Unknown',
                        existing_file_path=row['file_path'] or '',
                        match_details=f"Exact file path match: {metadata.file_path}"
                    ))
            
            # Check ISBN duplicates  
            if metadata.isbn:
                # Clean ISBN for comparison
                clean_isbn = re.sub(r'[^0-9X]', '', metadata.isbn.upper())
                if clean_isbn:
                    cur.execute("""
                        SELECT book_id, title, author, file_path, isbn
                        FROM books 
                        WHERE REGEXP_REPLACE(UPPER(isbn), '[^0-9X]', '', 'g') = %s
                    """, (clean_isbn,))
                    
                    for row in cur.fetchall():
                        duplicates.append(DuplicateMatch(
                            book_id=row['book_id'],
                            match_type='isbn',
                            confidence=1.0,  # Exact match
                            existing_title=row['title'],
                            existing_author=row['author'] or 'Unknown',
                            existing_file_path=row['file_path'] or '',
                            match_details=f"ISBN match: {metadata.isbn} = {row['isbn']}"
                        ))
        
        return duplicates
    
    def _check_fuzzy_matches(self, conn, metadata: BookMetadata) -> List[DuplicateMatch]:
        """Level 2: Fuzzy title/author matching (Dr. Marcus Thompson's algorithms)"""
        duplicates = []
        
        if not metadata.title or not metadata.author:
            return duplicates
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Get candidate books with similar titles
            cur.execute("""
                SELECT book_id, title, author, file_path
                FROM books 
                WHERE title IS NOT NULL AND author IS NOT NULL
                ORDER BY similarity(title, %s) DESC
                LIMIT %s
            """, (metadata.title, self.max_comparison_batch))
            
            for row in cur.fetchall():
                # Calculate similarity scores
                title_similarity = self._calculate_similarity(
                    metadata.title.lower().strip(), 
                    row['title'].lower().strip()
                )
                
                author_similarity = self._calculate_similarity(
                    metadata.author.lower().strip(),
                    (row['author'] or '').lower().strip()
                )
                
                # Combined confidence score (Dr. Marcus's formula)
                combined_confidence = (title_similarity * 0.7) + (author_similarity * 0.3)
                
                # Check if it meets our thresholds
                if (title_similarity >= self.title_similarity_threshold and 
                    author_similarity >= self.author_similarity_threshold) or \
                   combined_confidence >= self.combined_similarity_threshold:
                    
                    duplicates.append(DuplicateMatch(
                        book_id=row['book_id'],
                        match_type='title_author',
                        confidence=combined_confidence,
                        existing_title=row['title'],
                        existing_author=row['author'] or 'Unknown',
                        existing_file_path=row['file_path'] or '',
                        match_details=f"Title: {title_similarity:.2f}, Author: {author_similarity:.2f}"
                    ))
        
        return duplicates
    
    def _check_content_matches(self, conn, metadata: BookMetadata, chapters: List[ChapterInfo]) -> List[DuplicateMatch]:
        """Level 3: Content hash comparison (Dr. James Park's processing)"""
        duplicates = []
        
        if not chapters:
            return duplicates
        
        # Generate content hash from first chapter sample
        content_sample = chapters[0].content[:self.content_sample_size] if chapters else ""
        content_hash = hashlib.sha256(content_sample.encode('utf-8')).hexdigest()
        
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Look for books with similar word counts (rough content size filter)
            word_count_range = metadata.total_words * 0.1  # 10% variance
            min_words = max(0, metadata.total_words - word_count_range)
            max_words = metadata.total_words + word_count_range
            
            cur.execute("""
                SELECT b.book_id, b.title, b.author, b.file_path, b.word_count,
                       c.content
                FROM books b
                JOIN chunks c ON b.book_id = c.book_id
                WHERE b.word_count BETWEEN %s AND %s
                  AND c.chapter_number = 1
                ORDER BY ABS(b.word_count - %s)
                LIMIT %s
            """, (min_words, max_words, metadata.total_words, 20))
            
            for row in cur.fetchall():
                # Compare content hashes
                existing_sample = (row['content'] or '')[:self.content_sample_size]
                existing_hash = hashlib.sha256(existing_sample.encode('utf-8')).hexdigest()
                
                if content_hash == existing_hash:
                    duplicates.append(DuplicateMatch(
                        book_id=row['book_id'],
                        match_type='content_hash',
                        confidence=0.95,  # Very high confidence for exact hash match
                        existing_title=row['title'],
                        existing_author=row['author'] or 'Unknown',
                        existing_file_path=row['file_path'] or '',
                        match_details=f"Identical content hash and word count: {metadata.total_words}"
                    ))
        
        return duplicates
    
    def _check_metadata_fingerprint(self, conn, metadata: BookMetadata) -> List[DuplicateMatch]:
        """Level 4: Advanced metadata fingerprinting (Dr. Elena Rodriguez's optimization)"""
        duplicates = []
        
        # Create metadata fingerprint
        fingerprint_parts = []
        if metadata.title:
            # Normalize title (remove articles, punctuation)
            normalized_title = re.sub(r'^(the|a|an)\s+', '', metadata.title.lower())
            normalized_title = re.sub(r'[^\w\s]', '', normalized_title)
            fingerprint_parts.append(normalized_title.strip())
        
        if metadata.author:
            # Normalize author (last name first)
            author_parts = metadata.author.lower().split()
            if len(author_parts) > 1:
                normalized_author = f"{author_parts[-1]} {' '.join(author_parts[:-1])}"
            else:
                normalized_author = metadata.author.lower()
            fingerprint_parts.append(normalized_author.strip())
        
        if metadata.publication_date:
            # Extract year
            year_match = re.search(r'\d{4}', metadata.publication_date)
            if year_match:
                fingerprint_parts.append(year_match.group())
        
        if len(fingerprint_parts) >= 2:  # Need at least title + author
            fingerprint = '|'.join(fingerprint_parts)
            fingerprint_hash = hashlib.md5(fingerprint.encode('utf-8')).hexdigest()
            
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                # This would require a fingerprint column in the future
                # For now, use a simpler approach
                
                # Check for books with same normalized title + author + year
                if len(fingerprint_parts) >= 3:
                    title_part, author_part, year_part = fingerprint_parts[:3]
                    
                    cur.execute("""
                        SELECT book_id, title, author, file_path, publication_date
                        FROM books 
                        WHERE LOWER(REGEXP_REPLACE(title, '^(the|a|an)\\s+', '', 'i')) LIKE %s
                          AND LOWER(author) LIKE %s
                          AND (publication_date LIKE %s OR publication_year = %s)
                    """, (f"%{title_part}%", f"%{author_part.split()[0]}%", f"%{year_part}%", int(year_part)))
                    
                    for row in cur.fetchall():
                        duplicates.append(DuplicateMatch(
                            book_id=row['book_id'],
                            match_type='metadata_fingerprint',
                            confidence=0.80,
                            existing_title=row['title'],
                            existing_author=row['author'] or 'Unknown',
                            existing_file_path=row['file_path'] or '',
                            match_details=f"Normalized metadata match: {fingerprint}"
                        ))
        
        return duplicates
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using difflib (Dr. Marcus's method)"""
        if not str1 or not str2:
            return 0.0
        
        # Use SequenceMatcher for accurate similarity
        similarity = difflib.SequenceMatcher(None, str1, str2).ratio()
        return similarity
    
    def _deduplicate_matches(self, duplicates: List[DuplicateMatch]) -> List[DuplicateMatch]:
        """Remove duplicate matches for the same book_id"""
        seen_book_ids = set()
        unique_duplicates = []
        
        for dup in duplicates:
            if dup.book_id not in seen_book_ids:
                unique_duplicates.append(dup)
                seen_book_ids.add(dup.book_id)
            else:
                # Keep the one with higher confidence
                for i, existing in enumerate(unique_duplicates):
                    if existing.book_id == dup.book_id and dup.confidence > existing.confidence:
                        unique_duplicates[i] = dup
                        break
        
        return unique_duplicates
    
    def is_safe_to_ingest(self, metadata: BookMetadata, chapters: List[ChapterInfo], 
                         confidence_threshold: float = 0.75) -> Tuple[bool, List[DuplicateMatch]]:
        """
        🎯 Main decision method: Is this book safe to ingest?
        
        Returns:
            (is_safe, potential_duplicates)
            
        is_safe = False if high-confidence duplicates found
        """
        duplicates = self.check_for_duplicates(metadata, chapters)
        
        # Check if any duplicates exceed confidence threshold
        high_confidence_duplicates = [d for d in duplicates if d.confidence >= confidence_threshold]
        
        is_safe = len(high_confidence_duplicates) == 0
        
        if not is_safe:
            self.logger.warning(f"🚫 INGESTION BLOCKED - {len(high_confidence_duplicates)} high-confidence duplicates found")
        else:
            self.logger.info("✅ INGESTION APPROVED - No high-confidence duplicates")
        
        return is_safe, duplicates
    
    def log_duplicate_prevention(self, metadata: BookMetadata, duplicates: List[DuplicateMatch], 
                               action_taken: str):
        """Log duplicate prevention action for DBA team audit"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'title': metadata.title,
            'author': metadata.author,
            'file_path': metadata.file_path,
            'duplicates_found': len(duplicates),
            'action_taken': action_taken,
            'team_signature': self.team_signature,
            'duplicates_details': [
                {
                    'match_type': d.match_type,
                    'confidence': d.confidence,
                    'existing_book_id': d.book_id,
                    'match_details': d.match_details
                } for d in duplicates
            ]
        }
        
        self.logger.info(f"📝 DBA Team audit log: {action_taken} for '{metadata.title}'")
        
        # Could save to database audit table in the future
        return log_entry

def main():
    """Test the deduplication layer"""
    # Example usage
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': 5432
    }
    
    dedup = DeduplicationLayer(db_config)
    print("🔍 DBA Team Deduplication Layer - Test Mode")
    print("✅ System initialized and ready for integration")

if __name__ == "__main__":
    main()