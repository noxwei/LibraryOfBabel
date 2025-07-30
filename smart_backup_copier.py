#!/usr/bin/env python3
"""
Smart EPUB Backup Copier
========================

Copies unique EPUBs from working directory to external backup drive,
avoiding duplicates based on filename prefix matching.

Author: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
Purpose: Create complete master archive without duplicates
"""

import os
import shutil
import logging
from pathlib import Path
from collections import defaultdict
import hashlib
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - SMART_BACKUP - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmartBackupCopier:
    """Intelligent EPUB backup copier with deduplication"""
    
    def __init__(self, 
                 source_dir="/Users/weixiangzhang/Local_Dev/LibraryOfBabel",
                 backup_dir="/Volumes/Everything/Ebooks",
                 prefix_length=10):
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        self.prefix_length = prefix_length
        
        # Statistics
        self.stats = {
            "source_files_found": 0,
            "backup_files_existing": 0,
            "unique_files_to_copy": 0,
            "files_copied": 0,
            "files_skipped": 0,
            "copy_errors": 0,
            "bytes_copied": 0
        }
        
        # Validation
        if not self.source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        if not self.backup_dir.exists():
            raise ValueError(f"Backup directory does not exist: {backup_dir}")
    
    def get_filename_prefix(self, epub_path):
        """Get normalized filename prefix for comparison"""
        filename = Path(epub_path).stem
        prefix = filename[:self.prefix_length].lower()
        # Remove common artifacts
        prefix = prefix.replace('_', ' ').replace('-', ' ')
        return prefix.strip()
    
    def scan_existing_backup_files(self):
        """Scan existing files in backup directory"""
        logger.info(f"🔍 Scanning existing backup files in {self.backup_dir}")
        
        existing_prefixes = set()
        existing_files = list(self.backup_dir.rglob("*.epub"))
        
        for epub_path in existing_files:
            prefix = self.get_filename_prefix(epub_path)
            existing_prefixes.add(prefix)
        
        self.stats["backup_files_existing"] = len(existing_files)
        logger.info(f"📚 Found {len(existing_files)} existing EPUBs with {len(existing_prefixes)} unique prefixes")
        
        return existing_prefixes
    
    def scan_source_files(self):
        """Scan source files to copy"""
        logger.info(f"🔍 Scanning source files in {self.source_dir}")
        
        source_files = list(self.source_dir.rglob("*.epub"))
        self.stats["source_files_found"] = len(source_files)
        
        logger.info(f"📚 Found {len(source_files)} EPUB files in source directory")
        return source_files
    
    def identify_unique_files_to_copy(self, source_files, existing_prefixes):
        """Identify unique files that need to be copied"""
        logger.info("🎯 Identifying unique files to copy...")
        
        unique_files = []
        source_prefixes = set()
        
        for epub_path in source_files:
            prefix = self.get_filename_prefix(epub_path)
            
            # Skip if already exists in backup
            if prefix in existing_prefixes:
                self.stats["files_skipped"] += 1
                continue
            
            # Skip if we already have this prefix from source (avoid source duplicates)
            if prefix in source_prefixes:
                self.stats["files_skipped"] += 1
                continue
            
            unique_files.append(epub_path)
            source_prefixes.add(prefix)
        
        self.stats["unique_files_to_copy"] = len(unique_files)
        logger.info(f"✅ Identified {len(unique_files)} unique files to copy")
        logger.info(f"⏭️ Skipped {self.stats['files_skipped']} duplicate/existing files")
        
        return unique_files
    
    def copy_file_safely(self, source_path, dest_path):
        """Copy file with error handling and verification"""
        try:
            # Create destination directory if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            
            # Verify copy
            if dest_path.exists() and dest_path.stat().st_size == source_path.stat().st_size:
                self.stats["files_copied"] += 1
                self.stats["bytes_copied"] += source_path.stat().st_size
                return True
            else:
                logger.error(f"❌ Copy verification failed: {dest_path}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Copy error for {source_path}: {e}")
            self.stats["copy_errors"] += 1
            return False
    
    def run_backup_copy(self, dry_run=False):
        """Run the complete backup copy process"""
        logger.info("🚀 Starting Smart EPUB Backup Copy Process")
        logger.info(f"📁 Source: {self.source_dir}")
        logger.info(f"💾 Backup: {self.backup_dir}")
        logger.info(f"🔤 Prefix Length: {self.prefix_length} characters")
        logger.info(f"🧪 Dry Run: {dry_run}")
        
        try:
            # Step 1: Scan existing backup files
            existing_prefixes = self.scan_existing_backup_files()
            
            # Step 2: Scan source files
            source_files = self.scan_source_files()
            
            # Step 3: Identify unique files to copy
            unique_files = self.identify_unique_files_to_copy(source_files, existing_prefixes)
            
            if not unique_files:
                logger.info("✨ No unique files found to copy - backup is already complete!")
                return
            
            # Step 4: Copy files
            logger.info(f"📦 Starting copy process for {len(unique_files)} files...")
            
            for i, source_path in enumerate(unique_files):
                if i % 100 == 0:
                    logger.info(f"   Progress: {i}/{len(unique_files)} files copied...")
                
                # Generate destination path (maintain filename)
                dest_path = self.backup_dir / source_path.name
                
                # Handle filename conflicts (rare but possible)
                counter = 1
                while dest_path.exists():
                    stem = source_path.stem
                    suffix = source_path.suffix
                    dest_path = self.backup_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                if dry_run:
                    logger.debug(f"DRY RUN: Would copy {source_path} → {dest_path}")
                    self.stats["files_copied"] += 1
                else:
                    success = self.copy_file_safely(source_path, dest_path)
                    if success:
                        logger.debug(f"✅ Copied: {source_path.name}")
            
            # Final statistics
            self.print_final_report()
            
        except Exception as e:
            logger.error(f"❌ Backup process failed: {e}")
            raise
    
    def print_final_report(self):
        """Print final backup report"""
        copied_gb = self.stats["bytes_copied"] / (1024**3)
        
        logger.info("=" * 60)
        logger.info("📊 SMART BACKUP COPY REPORT")
        logger.info("=" * 60)
        logger.info(f"📚 Source files found: {self.stats['source_files_found']:,}")
        logger.info(f"💾 Existing backup files: {self.stats['backup_files_existing']:,}")
        logger.info(f"✅ Unique files copied: {self.stats['files_copied']:,}")
        logger.info(f"⏭️ Files skipped (duplicates): {self.stats['files_skipped']:,}")
        logger.info(f"❌ Copy errors: {self.stats['copy_errors']:,}")
        logger.info(f"💽 Data copied: {copied_gb:.2f} GB")
        logger.info("=" * 60)
        
        # Calculate new totals
        new_backup_total = self.stats["backup_files_existing"] + self.stats["files_copied"]
        logger.info(f"🎯 NEW BACKUP TOTAL: {new_backup_total:,} unique EPUB files")
        logger.info(f"📈 Growth: +{self.stats['files_copied']:,} files ({self.stats['files_copied']/self.stats['backup_files_existing']*100:.1f}% increase)")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart EPUB Backup Copier")
    parser.add_argument("--source", default="/Users/weixiangzhang/Local_Dev/LibraryOfBabel",
                       help="Source directory to copy from")
    parser.add_argument("--backup", default="/Volumes/Everything/Ebooks",
                       help="Backup directory to copy to")
    parser.add_argument("--prefix-length", type=int, default=10,
                       help="Number of characters for duplicate detection")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be copied without actually copying")
    
    args = parser.parse_args()
    
    copier = SmartBackupCopier(
        source_dir=args.source,
        backup_dir=args.backup,
        prefix_length=args.prefix_length
    )
    
    copier.run_backup_copy(dry_run=args.dry_run)