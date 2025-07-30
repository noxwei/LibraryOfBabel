#!/usr/bin/env python3
"""
Calibre File Relocator
======================

Moves EPUB files from ebooks/processed to Calibre Library location
while maintaining PostgreSQL references and file integrity.

Part of the three-way EPUB-Calibre-PostgreSQL synchronization system.
"""

import psycopg2
import subprocess
import shutil
import hashlib
import os
from pathlib import Path
import logging
import json
import time
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - FILE_RELOCATOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calibre_file_relocator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CalibreFileRelocator:
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library", 
                 processed_epub_path="ebooks/processed"):
        self.calibre_library_path = calibre_library_path
        self.processed_epub_path = Path(processed_epub_path)
        self.backup_path = Path("ebooks/backup_before_calibre_move")
        
        # Ensure backup directory exists
        self.backup_path.mkdir(exist_ok=True)
        
        logger.info("📁 File Relocator initialized")
        logger.info(f"   Calibre Library: {self.calibre_library_path}")
        logger.info(f"   Processed EPUBs: {self.processed_epub_path}")
        logger.info(f"   Backup Location: {self.backup_path}")
        
    def calculate_file_hash(self, file_path):
        """Calculate MD5 hash for file integrity verification"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
        
    def get_calibre_book_path(self, calibre_id):
        """Get the actual file path of a book in Calibre library"""
        try:
            # Get book metadata to construct the path
            cmd = [
                "/Applications/calibre.app/Contents/MacOS/calibredb",
                "show_metadata",
                "--library-path", self.calibre_library_path,
                str(calibre_id)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse the output to get title and author for path construction
                title = None
                author = None
                
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip().startswith('Title               :'):
                        title = line.split(':', 1)[1].strip()
                    elif line.strip().startswith('Author(s)           :'):
                        author_line = line.split(':', 1)[1].strip()
                        # Extract main author name (before any brackets)
                        author = author_line.split('[')[0].strip()
                        
                if title and author:
                    # Calibre uses Author/Title (ID) structure
                    # Clean names for filesystem
                    clean_author = self._clean_filename(author)
                    clean_title = self._clean_filename(title)
                    
                    # Construct expected Calibre path structure
                    calibre_dir = f"{clean_author}/{clean_title} ({calibre_id})"
                    
                    # Look for EPUB file in that directory
                    full_dir_path = os.path.join(self.calibre_library_path, calibre_dir)
                    if os.path.exists(full_dir_path):
                        # Find EPUB file in directory
                        for file in os.listdir(full_dir_path):
                            if file.endswith('.epub'):
                                return f"{calibre_dir}/{file}"
                                
        except Exception as e:
            logger.error(f"❌ Failed to get Calibre path for ID {calibre_id}: {e}")
            
        return None
        
    def _clean_filename(self, name):
        """Clean a string for use in filesystem paths"""
        # Remove characters that aren't filesystem-safe
        import re
        cleaned = re.sub(r'[<>:"/\\|?*]', '', name)
        cleaned = cleaned.strip('. ')
        return cleaned[:50]  # Limit length
        
    def backup_original_file(self, epub_path):
        """Create backup of original EPUB file"""
        try:
            backup_file = self.backup_path / epub_path.name
            shutil.copy2(epub_path, backup_file)
            logger.info(f"💾 Backed up: {epub_path.name}")
            return backup_file
        except Exception as e:
            logger.error(f"❌ Backup failed for {epub_path.name}: {e}")
            return None
            
    def update_postgres_file_path(self, book_id, new_calibre_path, calibre_id, original_hash):
        """Update PostgreSQL with new Calibre file location"""
        try:
            conn = psycopg2.connect(host='localhost', database='knowledge_base', user='weixiangzhang')
            cursor = conn.cursor()
            
            # Deploy file sync schema if needed
            cursor.execute("""
                ALTER TABLE books ADD COLUMN IF NOT EXISTS calibre_id INTEGER;
                ALTER TABLE books ADD COLUMN IF NOT EXISTS calibre_file_path TEXT;
                ALTER TABLE books ADD COLUMN IF NOT EXISTS file_sync_status TEXT DEFAULT 'pending';
                ALTER TABLE books ADD COLUMN IF NOT EXISTS last_file_sync TIMESTAMP;
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calibre_file_sync (
                    id SERIAL PRIMARY KEY,
                    book_id INTEGER REFERENCES books(book_id),
                    original_path TEXT NOT NULL,
                    calibre_path TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'pending',
                    sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_integrity_hash TEXT,
                    backup_location TEXT
                );
            """)
            
            # Update books table
            cursor.execute("""
                UPDATE books SET 
                    calibre_id = %s,
                    calibre_file_path = %s,
                    file_sync_status = 'synced',
                    last_file_sync = CURRENT_TIMESTAMP
                WHERE book_id = %s
            """, (calibre_id, new_calibre_path, book_id))
            
            # Insert sync tracking record
            cursor.execute("""
                INSERT INTO calibre_file_sync 
                (book_id, original_path, calibre_path, sync_status, file_integrity_hash, backup_location)
                VALUES (%s, %s, %s, 'synced', %s, %s)
                ON CONFLICT DO NOTHING
            """, (book_id, str(self.processed_epub_path), new_calibre_path, original_hash, str(self.backup_path)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Updated PostgreSQL for book_id {book_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL update failed for book_id {book_id}: {e}")
            return False
            
    def find_database_book_for_epub(self, epub_path):
        """Find corresponding PostgreSQL book record for EPUB file"""
        try:
            conn = psycopg2.connect(host='localhost', database='knowledge_base', user='weixiangzhang')
            cursor = conn.cursor()
            
            # Try multiple matching strategies
            epub_name = epub_path.stem
            
            # Strategy 1: Exact file_path match
            cursor.execute("SELECT book_id, title, author FROM books WHERE file_path LIKE %s", 
                          (f"%{epub_path.name}%",))
            result = cursor.fetchone()
            
            if result:
                conn.close()
                return result[0], result[1], result[2]
                
            # Strategy 2: Filename similarity
            cursor.execute("""
                SELECT book_id, title, author 
                FROM books 
                WHERE LOWER(file_path) LIKE LOWER(%s) 
                OR LOWER(title) LIKE LOWER(%s)
                LIMIT 1
            """, (f"%{epub_name}%", f"%{epub_name[:20]}%"))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0], result[1], result[2]
                
        except Exception as e:
            logger.error(f"❌ Database lookup failed for {epub_path.name}: {e}")
            
        return None, None, None
        
    def verify_calibre_file_integrity(self, calibre_path, original_hash):
        """Verify file integrity after move to Calibre"""
        try:
            if os.path.exists(calibre_path):
                new_hash = self.calculate_file_hash(calibre_path)
                return new_hash == original_hash
        except Exception as e:
            logger.error(f"❌ File integrity check failed: {e}")
            
        return False
        
    def relocate_epub_to_calibre(self, epub_path):
        """Main function to relocate EPUB from processed to Calibre"""
        logger.info(f"🚀 Processing: {epub_path.name}")
        
        # Step 1: Calculate original file hash
        try:
            original_hash = self.calculate_file_hash(epub_path)
            logger.info(f"🔍 Original hash: {original_hash[:8]}...")
        except Exception as e:
            logger.error(f"❌ Failed to calculate hash for {epub_path.name}: {e}")
            return False
            
        # Step 2: Backup original file
        backup_file = self.backup_original_file(epub_path)
        if not backup_file:
            logger.error(f"❌ Cannot proceed without backup for {epub_path.name}")
            return False
            
        # Step 3: Find corresponding database record
        book_id, title, author = self.find_database_book_for_epub(epub_path)
        if not book_id:
            logger.warning(f"⚠️ No database record found for {epub_path.name}")
            return False
            
        logger.info(f"📖 Found book: '{title}' by {author} (ID: {book_id})")
        
        # Step 4: Add to Calibre if not already there
        try:
            # Check if already in Calibre by searching
            search_cmd = [
                "/Applications/calibre.app/Contents/MacOS/calibredb",
                "search",
                "--library-path", self.calibre_library_path,
                f"title:=\"{title[:20]}\" or author:={author.split()[0] if author else 'unknown'}"
            ]
            
            search_result = subprocess.run(search_cmd, capture_output=True, text=True, timeout=30)
            
            calibre_id = None
            if search_result.returncode == 0 and search_result.stdout.strip():
                # Book found in Calibre
                calibre_ids = search_result.stdout.strip().split(',')
                calibre_id = int(calibre_ids[0])
                logger.info(f"📚 Book already in Calibre with ID: {calibre_id}")
            else:
                # Add to Calibre
                add_cmd = [
                    "/Applications/calibre.app/Contents/MacOS/calibredb",
                    "add",
                    "--library-path", self.calibre_library_path,
                    str(epub_path)
                ]
                
                add_result = subprocess.run(add_cmd, capture_output=True, text=True, timeout=60)
                
                if add_result.returncode == 0:
                    # Extract Calibre ID from output
                    for line in add_result.stdout.strip().split('\n'):
                        if "Added book ids:" in line:
                            calibre_id = int(line.split(":")[-1].strip())
                            logger.info(f"📚 Added to Calibre with ID: {calibre_id}")
                            break
                            
        except Exception as e:
            logger.error(f"❌ Calibre operation failed for {epub_path.name}: {e}")
            return False
            
        if not calibre_id:
            logger.error(f"❌ Failed to get Calibre ID for {epub_path.name}")
            return False
            
        # Step 5: Get Calibre's file path
        calibre_file_path = self.get_calibre_book_path(calibre_id)
        if not calibre_file_path:
            logger.error(f"❌ Failed to get Calibre file path for ID {calibre_id}")
            return False
            
        logger.info(f"📁 Calibre path: {calibre_file_path}")
        
        # Step 6: Verify file integrity in Calibre location
        full_calibre_path = os.path.join(self.calibre_library_path, calibre_file_path)
        if not self.verify_calibre_file_integrity(full_calibre_path, original_hash):
            logger.error(f"❌ File integrity check failed for {epub_path.name}")
            return False
            
        # Step 7: Update PostgreSQL with new location
        success = self.update_postgres_file_path(book_id, calibre_file_path, calibre_id, original_hash)
        if not success:
            logger.error(f"❌ PostgreSQL update failed for {epub_path.name}")
            return False
            
        # Step 8: Remove original file (it's now in Calibre and backed up)
        try:
            epub_path.unlink()
            logger.info(f"🗑️ Removed original file: {epub_path.name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to remove original file {epub_path.name}: {e}")
            
        logger.info(f"✅ Successfully relocated: {epub_path.name}")
        return True
        
    def relocate_all_processed_epubs(self, max_files=None):
        """Relocate all EPUB files from processed folder to Calibre"""
        epub_files = list(self.processed_epub_path.glob("*.epub"))
        
        if max_files:
            epub_files = epub_files[:max_files]
            
        total_files = len(epub_files)
        successful = 0
        failed = 0
        
        logger.info(f"🚀 Starting relocation of {total_files} EPUB files")
        
        for i, epub_path in enumerate(epub_files, 1):
            logger.info(f"📊 Progress: {i}/{total_files}")
            
            try:
                if self.relocate_epub_to_calibre(epub_path):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"❌ Relocation failed for {epub_path.name}: {e}")
                failed += 1
                
            # Small delay to avoid overwhelming the system
            time.sleep(0.5)
            
        logger.info("📊 Relocation Summary:")
        logger.info(f"   ✅ Successful: {successful}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   📈 Success Rate: {(successful/total_files)*100:.1f}%")
        
        # Save relocation report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful/total_files)*100 if total_files > 0 else 0
        }
        
        with open('calibre_relocation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
            
        return successful, failed
        
def main():
    parser = argparse.ArgumentParser(description='Calibre File Relocator')
    parser.add_argument('--migrate-all', action='store_true', help='Relocate all processed EPUB files')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--single-file', type=str, help='Relocate a single specific file')
    
    args = parser.parse_args()
    
    relocator = CalibreFileRelocator()
    
    if args.single_file:
        epub_path = Path(args.single_file)
        if epub_path.exists():
            success = relocator.relocate_epub_to_calibre(epub_path)
            if success:
                logger.info("🎉 Single file relocation completed successfully!")
            else:
                logger.error("❌ Single file relocation failed!")
        else:
            logger.error(f"❌ File not found: {args.single_file}")
            
    elif args.migrate_all:
        successful, failed = relocator.relocate_all_processed_epubs(args.max_files)
        if successful > 0:
            logger.info("🎉 Batch relocation completed!")
        else:
            logger.error("❌ No files were successfully relocated!")
    else:
        logger.info("ℹ️ Use --migrate-all to start relocation or --single-file <path> for single file")
        
if __name__ == "__main__":
    main() 