#!/usr/bin/env python3
"""
External Drive Duplicate Scanner
================================

Scans /Volumes/Everything/Ebooks and identifies books not already in Calibre
using filename prefix comparison (first 15 characters) for duplicate detection.

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
"""

import os
from pathlib import Path
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - EXTERNAL_SCANNER - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExternalDriveScanner:
    def __init__(self, external_path="/Volumes/Everything/Ebooks", calibre_path="/Users/weixiangzhang/Calibre Library"):
        self.external_path = Path(external_path)
        self.calibre_path = Path(calibre_path)
        self.prefix_length = 15
        
    def get_calibre_prefixes(self):
        """Get filename prefixes of all books currently in Calibre"""
        logger.info("🔍 Scanning existing Calibre library...")
        calibre_prefixes = set()
        
        calibre_epubs = list(self.calibre_path.rglob("*.epub"))
        logger.info(f"📚 Found {len(calibre_epubs)} EPUBs in Calibre library")
        
        for epub_path in calibre_epubs:
            prefix = epub_path.stem[:self.prefix_length].lower()
            calibre_prefixes.add(prefix)
            
        logger.info(f"📋 Extracted {len(calibre_prefixes)} unique prefixes from Calibre")
        return calibre_prefixes
    
    def scan_external_drive(self):
        """Scan external drive and identify unique books"""
        logger.info("🔍 Scanning external drive for EPUBs...")
        
        if not self.external_path.exists():
            logger.error(f"❌ External drive not found: {self.external_path}")
            return {}
            
        external_epubs = list(self.external_path.rglob("*.epub"))
        logger.info(f"📚 Found {len(external_epubs)} EPUBs on external drive")
        
        # Get existing Calibre prefixes
        calibre_prefixes = self.get_calibre_prefixes()
        
        # Analyze external drive books
        unique_books = []
        duplicate_books = []
        external_prefixes = set()
        
        for epub_path in external_epubs:
            prefix = epub_path.stem[:self.prefix_length].lower()
            
            if prefix in calibre_prefixes:
                duplicate_books.append(str(epub_path))
            else:
                if prefix not in external_prefixes:
                    unique_books.append(str(epub_path))
                    external_prefixes.add(prefix)
                else:
                    # Duplicate within external drive itself
                    duplicate_books.append(str(epub_path))
        
        results = {
            "scan_timestamp": datetime.now().isoformat(),
            "external_drive_path": str(self.external_path),
            "calibre_library_path": str(self.calibre_path),
            "statistics": {
                "total_external_epubs": len(external_epubs),
                "total_calibre_epubs": len(list(self.calibre_path.rglob("*.epub"))),
                "unique_calibre_prefixes": len(calibre_prefixes),
                "unique_books_to_import": len(unique_books),
                "duplicate_books_skipped": len(duplicate_books),
                "deduplication_rate": f"{(len(duplicate_books)/len(external_epubs)*100):.1f}%"
            },
            "unique_books": unique_books[:50],  # First 50 for preview
            "total_unique_books": len(unique_books),
            "sample_duplicates": duplicate_books[:10]  # Sample of duplicates
        }
        
        logger.info("=" * 60)
        logger.info("📊 EXTERNAL DRIVE SCAN RESULTS")
        logger.info("=" * 60)
        logger.info(f"📚 Total EPUBs on external drive: {results['statistics']['total_external_epubs']:,}")
        logger.info(f"📚 Total EPUBs in Calibre: {results['statistics']['total_calibre_epubs']:,}")
        logger.info(f"✨ Unique books to import: {results['statistics']['unique_books_to_import']:,}")
        logger.info(f"⏭️  Duplicates skipped: {results['statistics']['duplicate_books_skipped']:,}")
        logger.info(f"📈 Deduplication rate: {results['statistics']['deduplication_rate']}")
        logger.info("=" * 60)
        
        return results
    
    def save_results(self, results, filename="external_drive_scan_results.json"):
        """Save scan results to file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"💾 Scan results saved to: {filename}")
        
    def preview_unique_books(self, results, limit=20):
        """Preview unique books that would be imported"""
        logger.info(f"📋 PREVIEW - First {limit} unique books to import:")
        logger.info("-" * 80)
        
        for i, book_path in enumerate(results['unique_books'][:limit], 1):
            book_name = Path(book_path).stem
            logger.info(f"{i:2d}. {book_name}")
            
        if len(results['unique_books']) > limit:
            remaining = len(results['unique_books']) - limit
            logger.info(f"... and {remaining:,} more unique books")

if __name__ == "__main__":
    scanner = ExternalDriveScanner()
    
    logger.info("🚀 Starting external drive duplicate scan...")
    results = scanner.scan_external_drive()
    
    scanner.save_results(results)
    scanner.preview_unique_books(results)
    
    logger.info("✅ External drive scan completed!")