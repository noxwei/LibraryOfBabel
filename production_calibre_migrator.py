#!/usr/bin/env python3
"""
Production Calibre Migrator
===========================

Scale up the proven 5/5 successful process to handle all 5,749 books
Based on Dr. Marcus Wong & Dr. Sarah Chen's PostgreSQL-First architecture

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
Architecture: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First principles
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
from pathlib import Path
import logging
import time
import json
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PRODUCTION_MIGRATOR - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionCalibreMigrator:
    """Production-ready Calibre migrator that processes all books systematically"""
    
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library",
                 processed_epubs_path="ebooks/processed"):
        self.calibre_library_path = calibre_library_path
        self.processed_epubs_path = Path(processed_epubs_path)
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "batches_completed": 0
        }
        
    def connect_database(self):
        """Establish database connection"""
        return psycopg2.connect(
            host='localhost',
            database='knowledge_base',
            user='weixiangzhang',
            cursor_factory=RealDictCursor
        )
    
    def find_or_add_to_calibre(self, epub_path: Path) -> int:
        """Find existing Calibre ID using proven smart search strategy"""
        
        # Proven strategy: Use shorter search terms
        filename = epub_path.stem
        search_terms = []
        
        # Strategy 1: First few words of title
        title_part = filename.split(' - ')[0].strip()
        first_words = ' '.join(title_part.split()[:3])  # First 3 words
        search_terms.append(first_words)
        
        # Strategy 2: Just first 2 words
        first_two_words = ' '.join(title_part.split()[:2])  # First 2 words
        search_terms.append(first_two_words)
        
        # Strategy 3: Author name if available
        if ' - ' in filename:
            author_part = filename.split(' - ')[-1].replace('.epub', '').strip()
            if author_part:
                search_terms.append(author_part.split()[0])  # First name or last name
        
        for search_term in search_terms:
            cmd = [
                "/Applications/calibre.app/Contents/MacOS/calibredb",
                "search",
                "--library-path", self.calibre_library_path,
                search_term
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                calibre_ids = result.stdout.strip().split(',')
                calibre_id = int(calibre_ids[0])
                logger.debug(f"Found Calibre ID {calibre_id} for '{epub_path.name}' using search '{search_term}'")
                return calibre_id
        
        # If not found, add new book (though this is rare in production)
        logger.info(f"Adding new book to Calibre: {epub_path.name}")
        cmd = [
            "/Applications/calibre.app/Contents/MacOS/calibredb",
            "add",
            "--library-path", self.calibre_library_path,
            str(epub_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if "Added book ids:" in line:
                    calibre_id = int(line.split(":")[-1].strip())
                    logger.info(f"Added to Calibre with ID: {calibre_id}")
                    return calibre_id
        
        logger.error(f"Failed to find or add '{epub_path.name}': {result.stderr}")
        return None
    
    def extract_calibre_metadata(self, calibre_id: int) -> dict:
        """Extract enhanced metadata from Calibre"""
        cmd = [
            "/Applications/calibre.app/Contents/MacOS/calibredb",
            "show_metadata",
            "--library-path", self.calibre_library_path,
            str(calibre_id)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            metadata = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Title               :'):
                    metadata['title'] = line.split(':', 1)[1].strip()
                elif line.startswith('Author(s)           :'):
                    metadata['author'] = line.split(':', 1)[1].strip()
                elif line.startswith('Comments            :'):
                    metadata['description'] = line.split(':', 1)[1].strip()
                elif line.startswith('Tags                :'):
                    metadata['genre'] = line.split(':', 1)[1].strip()
                elif line.startswith('Published           :'):
                    year_str = line.split(':', 1)[1].strip()
                    try:
                        metadata['publication_year'] = int(year_str.split('-')[0])
                    except:
                        pass
                elif line.startswith('Publisher           :'):
                    metadata['publisher'] = line.split(':', 1)[1].strip()
                elif line.startswith('Identifiers         :'):
                    isbn_line = line.split(':', 1)[1].strip()
                    if 'isbn:' in isbn_line:
                        metadata['isbn'] = isbn_line.split('isbn:')[1].split()[0]
            
            return metadata
        
        return {}
    
    def find_database_book(self, epub_filename: str, cursor) -> int:
        """Find matching book in database with proven pattern matching"""
        
        search_patterns = [
            f"%{epub_filename}%",  # Exact filename
            f"%{epub_filename.replace('.epub', '')}%",  # Without extension
            f"%{epub_filename.split(' - ')[0]}%",  # Just the title part
            f"%{epub_filename.split(' - ')[-1].replace('.epub', '')}%"  # Just the author part
        ]
        
        for pattern in search_patterns:
            cursor.execute("""
                SELECT book_id, title, author 
                FROM books 
                WHERE file_path LIKE %s
                LIMIT 1
            """, (pattern,))
            
            result = cursor.fetchone()
            if result:
                return result['book_id']
        
        # Try title similarity search
        title_part = epub_filename.split(' - ')[0].strip()
        cursor.execute("""
            SELECT book_id, title, author 
            FROM books 
            WHERE LOWER(title) LIKE LOWER(%s)
            LIMIT 1
        """, (f"%{title_part}%",))
        
        result = cursor.fetchone()
        if result:
            return result['book_id']
        
        return None
    
    def sync_to_postgres(self, book_id: int, metadata: dict, cursor) -> dict:
        """Sync enhanced metadata to PostgreSQL"""
        try:
            cursor.execute("""
                SELECT * FROM api_apply_calibre_metadata_enhancement(
                    %s, 
                    %s,
                    'enhanced metadata from Calibre',
                    'calibre_wins'
                )
            """, (book_id, self.calibre_library_path))
            
            result = cursor.fetchone()
            
            if result and result['update_success']:
                return {
                    "success": True,
                    "message": result['enhancement_message'],
                    "quality_improvement": float(result['quality_improvement']),
                    "fields_updated": result['fields_updated']
                }
            else:
                return {
                    "success": False,
                    "message": result['enhancement_message'] if result else "Enhancement failed"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
    
    def process_single_book(self, epub_path: Path, cursor) -> dict:
        """Process a single EPUB with full error handling"""
        try:
            # Step 1: Find or add to Calibre
            calibre_id = self.find_or_add_to_calibre(epub_path)
            if not calibre_id:
                return {"success": False, "error": "Failed to get Calibre ID"}
            
            # Step 2: Extract metadata
            metadata = self.extract_calibre_metadata(calibre_id)
            if not metadata:
                return {"success": False, "error": "Failed to extract metadata"}
            
            # Step 3: Find database book
            book_id = self.find_database_book(epub_path.name, cursor)
            if not book_id:
                return {"success": False, "error": "No matching database book"}
            
            # Step 4: Sync to PostgreSQL
            sync_result = self.sync_to_postgres(book_id, metadata, cursor)
            
            if sync_result['success']:
                return {
                    "success": True,
                    "calibre_id": calibre_id,
                    "book_id": book_id,
                    "title": metadata.get('title', 'Unknown'),
                    "author": metadata.get('author', 'Unknown'),
                    "quality_improvement": sync_result.get('quality_improvement', 0),
                    "fields_updated": sync_result.get('fields_updated', [])
                }
            else:
                return {"success": False, "error": sync_result['message']}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_progress(self, progress_file="calibre_migration_progress.json"):
        """Save current progress to file"""
        progress_data = {
            "stats": self.stats,
            "timestamp": datetime.now().isoformat(),
            "books_per_hour": self.calculate_books_per_hour()
        }
        
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2, default=str)
    
    def calculate_books_per_hour(self) -> float:
        """Calculate processing rate"""
        if not self.stats["start_time"] or self.stats["total_processed"] == 0:
            return 0.0
        
        elapsed_hours = (time.time() - self.stats["start_time"]) / 3600
        return self.stats["total_processed"] / elapsed_hours if elapsed_hours > 0 else 0.0
    
    def run_production_migration(self, batch_size=25, max_books=None, start_from=0):
        """Run the complete production migration"""
        
        logger.info("🚀 Starting PRODUCTION Calibre migration")
        logger.info(f"Batch size: {batch_size}, Max books: {max_books}, Starting from: {start_from}")
        
        # Connect to database
        conn = self.connect_database()
        cursor = conn.cursor()
        
        # Get all EPUB files
        epub_files = sorted(list(self.processed_epubs_path.glob("*.epub")))
        total_files = len(epub_files)
        
        if max_books:
            epub_files = epub_files[start_from:start_from + max_books]
        else:
            epub_files = epub_files[start_from:]
        
        logger.info(f"📚 Processing {len(epub_files)} books from {total_files} total EPUBs")
        
        # Initialize stats
        self.stats["start_time"] = time.time()
        
        # Process in batches
        for i in range(0, len(epub_files), batch_size):
            batch = epub_files[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"📦 Processing batch {batch_num}: {len(batch)} books")
            
            batch_successful = 0
            batch_failed = 0
            
            for epub_path in batch:
                result = self.process_single_book(epub_path, cursor)
                
                self.stats["total_processed"] += 1
                
                if result["success"]:
                    self.stats["successful"] += 1
                    batch_successful += 1
                    logger.info(f"✅ {epub_path.name} -> {result['title']} by {result['author']}")
                else:
                    self.stats["failed"] += 1
                    batch_failed += 1
                    logger.warning(f"❌ {epub_path.name} -> {result['error']}")
                
                # Commit after each book
                conn.commit()
                
                # Brief pause
                time.sleep(0.1)
            
            self.stats["batches_completed"] += 1
            
            # Batch summary
            success_rate = (batch_successful / len(batch)) * 100
            overall_rate = (self.stats["successful"] / self.stats["total_processed"]) * 100
            books_per_hour = self.calculate_books_per_hour()
            
            logger.info(f"📊 Batch {batch_num} completed: {batch_successful}/{len(batch)} successful ({success_rate:.1f}%)")
            logger.info(f"📈 Overall: {self.stats['successful']}/{self.stats['total_processed']} successful ({overall_rate:.1f}%)")
            logger.info(f"⚡ Processing rate: {books_per_hour:.1f} books/hour")
            
            # Save progress
            self.save_progress()
            
            # Pause between batches
            time.sleep(1)
        
        # Final summary
        elapsed_time = time.time() - self.stats["start_time"]
        logger.info(f"🎉 Migration completed!")
        logger.info(f"📊 Final stats: {self.stats['successful']}/{self.stats['total_processed']} successful")
        logger.info(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
        logger.info(f"⚡ Average rate: {self.calculate_books_per_hour():.1f} books/hour")
        
        conn.close()

def main():
    """Command line interface for production migration"""
    parser = argparse.ArgumentParser(description="Production Calibre Migration")
    parser.add_argument("--batch-size", type=int, default=25, help="Books per batch")
    parser.add_argument("--max-books", type=int, help="Maximum books to process")
    parser.add_argument("--start-from", type=int, default=0, help="Start from book number")
    parser.add_argument("--calibre-path", type=str, default="/Users/weixiangzhang/Calibre Library")
    parser.add_argument("--epub-path", type=str, default="ebooks/processed")
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = ProductionCalibreMigrator(
        calibre_library_path=args.calibre_path,
        processed_epubs_path=args.epub_path
    )
    
    # Run migration
    migrator.run_production_migration(
        batch_size=args.batch_size,
        max_books=args.max_books,
        start_from=args.start_from
    )

if __name__ == "__main__":
    main() 