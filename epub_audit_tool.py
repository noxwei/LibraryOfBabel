#!/usr/bin/env python3
"""
EPUB File Audit Tool
====================

Comprehensive audit of all EPUB files in the working directory.
Identifies unique books by comparing first 10 characters of filenames.

Author: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Architecture
Purpose: Determine true EPUB collection size vs Calibre library
"""

import os
import logging
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
import zipfile
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - EPUB_AUDIT - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EPUBAuditor:
    """Comprehensive EPUB file auditor"""
    
    def __init__(self, working_directory="/Users/weixiangzhang/Local_Dev/LibraryOfBabel"):
        self.working_dir = Path(working_directory)
        self.calibre_lib = Path("/Users/weixiangzhang/Calibre Library")
        
        # Results storage
        self.all_epubs = []
        self.unique_by_prefix = {}
        self.duplicates_by_prefix = defaultdict(list)
        self.size_stats = {}
        
        # Include additional directories if they exist
        self.search_paths = [
            self.working_dir,
            Path("/Users/weixiangzhang/Desktop"),
            self.calibre_lib,
            Path("/Volumes/Everything/Ebooks")  # External drive with additional EPUBs
        ]
        
    def find_all_epubs(self):
        """Find all EPUB files in all search paths"""
        logger.info("🔍 Starting comprehensive EPUB search...")
        
        epub_files = []
        
        for search_path in self.search_paths:
            if not search_path.exists():
                logger.warning(f"⚠️ Path does not exist: {search_path}")
                continue
                
            logger.info(f"📁 Searching: {search_path}")
            
            try:
                # Find all .epub files recursively
                found_epubs = list(search_path.rglob("*.epub"))
                epub_files.extend(found_epubs)
                logger.info(f"   Found {len(found_epubs)} EPUBs")
            except PermissionError as e:
                logger.warning(f"⚠️ Permission denied: {search_path} - {e}")
            except Exception as e:
                logger.error(f"❌ Error searching {search_path}: {e}")
        
        logger.info(f"📚 Total EPUB files found: {len(epub_files)}")
        return epub_files
    
    def get_file_info(self, epub_path):
        """Get detailed information about an EPUB file"""
        try:
            stat = epub_path.stat()
            
            # Basic file info
            info = {
                'path': str(epub_path),
                'name': epub_path.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024*1024), 2),
                'modified_time': stat.st_mtime,
                'directory': str(epub_path.parent),
                'is_valid': False,
                'prefix_10': epub_path.stem[:10].lower(),
                'prefix_20': epub_path.stem[:20].lower(),
                'file_hash': None
            }
            
            # Validate EPUB structure
            try:
                with zipfile.ZipFile(epub_path, 'r') as zip_file:
                    files = zip_file.namelist()
                    if 'META-INF/container.xml' in files:
                        info['is_valid'] = True
                        # Quick integrity test
                        zip_file.testzip()
            except Exception as e:
                logger.debug(f"EPUB validation failed for {epub_path.name}: {e}")
            
            # Calculate file hash for exact duplicate detection
            try:
                with open(epub_path, 'rb') as f:
                    # Read first 64KB for hash (faster than full file)
                    chunk = f.read(65536)
                    info['file_hash'] = hashlib.md5(chunk).hexdigest()[:16]
            except Exception as e:
                logger.debug(f"Hash calculation failed for {epub_path.name}: {e}")
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting file info for {epub_path}: {e}")
            return None
    
    def categorize_by_location(self, epub_files):
        """Categorize EPUBs by their location"""
        categories = {
            'calibre_library': [],
            'working_directory': [],
            'desktop': [],
            'external_everything_drive': [],
            'other': []
        }
        
        for epub_path in epub_files:
            path_str = str(epub_path)
            
            if '/Calibre Library/' in path_str:
                categories['calibre_library'].append(epub_path)
            elif '/LibraryOfBabel/' in path_str:
                categories['working_directory'].append(epub_path)
            elif '/Desktop/' in path_str:
                categories['desktop'].append(epub_path)
            elif '/Volumes/Everything/Ebooks' in path_str:
                categories['external_everything_drive'].append(epub_path)
            else:
                categories['other'].append(epub_path)
        
        return categories
    
    def analyze_duplicates_by_prefix(self, epub_info_list):
        """Analyze duplicates based on filename prefixes"""
        prefix_groups = defaultdict(list)
        
        # Group by 10-character prefix
        for info in epub_info_list:
            if info:
                prefix = info['prefix_10']
                prefix_groups[prefix].append(info)
        
        # Separate unique vs duplicate groups
        unique_books = {}
        duplicate_groups = {}
        
        for prefix, files in prefix_groups.items():
            if len(files) == 1:
                unique_books[prefix] = files[0]
            else:
                duplicate_groups[prefix] = files
        
        return unique_books, duplicate_groups
    
    def generate_report(self, epub_files, categories, unique_books, duplicate_groups):
        """Generate comprehensive audit report"""
        
        # Calculate statistics
        total_files = len(epub_files)
        total_unique = len(unique_books)
        total_duplicate_groups = len(duplicate_groups)
        total_duplicates = sum(len(group) for group in duplicate_groups.values())
        
        # Size statistics
        total_size_bytes = sum(info['size_bytes'] for info in self.all_epubs if info)
        total_size_gb = round(total_size_bytes / (1024**3), 2)
        avg_size_mb = round(total_size_bytes / (1024**2) / total_files, 2) if total_files > 0 else 0
        
        # Valid EPUB count
        valid_epubs = sum(1 for info in self.all_epubs if info and info['is_valid'])
        
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'summary': {
                'total_epub_files_found': total_files,
                'unique_books_by_prefix': total_unique,
                'duplicate_groups': total_duplicate_groups,
                'total_duplicate_files': total_duplicates,
                'calibre_library_books': 2871,  # Known from previous check
                'coverage_analysis': {
                    'unique_epubs_vs_calibre': f"{total_unique} unique vs 2,871 Calibre ({total_unique/2871*100:.1f}% coverage)" if total_unique <= 2871 else f"{total_unique} unique vs 2,871 Calibre ({total_unique/2871*100:.1f}% - MORE than Calibre!)",
                    'potential_new_books': max(0, total_unique - 2871)
                }
            },
            'location_breakdown': {
                'calibre_library': len(categories['calibre_library']),
                'working_directory': len(categories['working_directory']),
                'desktop': len(categories['desktop']),
                'external_everything_drive': len(categories['external_everything_drive']),
                'other_locations': len(categories['other'])
            },
            'file_statistics': {
                'total_size_gb': total_size_gb,
                'average_file_size_mb': avg_size_mb,
                'valid_epub_files': valid_epubs,
                'invalid_epub_files': total_files - valid_epubs
            },
            'top_duplicate_groups': [],
            'unique_books_sample': []
        }
        
        # Add top duplicate groups
        sorted_duplicates = sorted(duplicate_groups.items(), key=lambda x: len(x[1]), reverse=True)
        for prefix, files in sorted_duplicates[:10]:
            report['top_duplicate_groups'].append({
                'prefix': prefix,
                'count': len(files),
                'files': [f['name'] for f in files[:5]]  # First 5 files
            })
        
        # Add sample unique books
        unique_sample = list(unique_books.values())[:20]
        for book in unique_sample:
            report['unique_books_sample'].append({
                'name': book['name'],
                'size_mb': book['size_mb'],
                'location': book['directory'].split('/')[-2:] if '/' in book['directory'] else book['directory']
            })
        
        return report
    
    def run_audit(self):
        """Run complete EPUB audit"""
        logger.info("🚀 Starting comprehensive EPUB audit...")
        
        # Find all EPUBs
        epub_files = self.find_all_epubs()
        if not epub_files:
            logger.error("❌ No EPUB files found!")
            return
        
        # Get detailed info for each file
        logger.info("📊 Analyzing EPUB files...")
        epub_info_list = []
        
        for i, epub_path in enumerate(epub_files):
            if i % 100 == 0:
                logger.info(f"   Processed {i}/{len(epub_files)} files...")
            
            info = self.get_file_info(epub_path)
            epub_info_list.append(info)
        
        self.all_epubs = epub_info_list
        
        # Categorize by location
        categories = self.categorize_by_location(epub_files)
        
        # Analyze duplicates
        logger.info("🔍 Analyzing duplicates by filename prefix...")
        unique_books, duplicate_groups = self.analyze_duplicates_by_prefix(epub_info_list)
        
        # Generate report
        logger.info("📋 Generating comprehensive report...")
        report = self.generate_report(epub_files, categories, unique_books, duplicate_groups)
        
        # Save report
        with open('epub_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        self.print_summary(report)
        
        return report
    
    def print_summary(self, report):
        """Print audit summary"""
        summary = report['summary']
        location = report['location_breakdown']
        stats = report['file_statistics']
        
        print("\n" + "="*70)
        print("📚 COMPREHENSIVE EPUB AUDIT RESULTS")
        print("="*70)
        print(f"🔍 Total EPUB Files Found: {summary['total_epub_files_found']:,}")
        print(f"📖 Unique Books (by prefix): {summary['unique_books_by_prefix']:,}")
        print(f"🔄 Duplicate Groups: {summary['duplicate_groups']:,}")
        print(f"📁 Total Duplicate Files: {summary['total_duplicate_files']:,}")
        print()
        print("📍 LOCATION BREAKDOWN:")
        print(f"   📚 Calibre Library: {location['calibre_library']:,}")
        print(f"   🏗️ Working Directory: {location['working_directory']:,}")
        print(f"   🖥️ Desktop: {location['desktop']:,}")
        print(f"   💽 External Drive (/Volumes/Everything/Ebooks): {location['external_everything_drive']:,}")
        print(f"   📂 Other Locations: {location['other_locations']:,}")
        print()
        print("📊 FILE STATISTICS:")
        print(f"   💾 Total Size: {stats['total_size_gb']:.2f} GB")
        print(f"   📏 Average File Size: {stats['average_file_size_mb']:.1f} MB")
        print(f"   ✅ Valid EPUBs: {stats['valid_epub_files']:,}")
        print(f"   ❌ Invalid EPUBs: {stats['invalid_epub_files']:,}")
        print()
        print("🎯 CALIBRE COMPARISON:")
        print(f"   {summary['coverage_analysis']['unique_epubs_vs_calibre']}")
        if summary['coverage_analysis']['potential_new_books'] > 0:
            print(f"   🚀 Potential NEW books for Calibre: {summary['coverage_analysis']['potential_new_books']:,}")
        print()
        print("📋 Report saved to: epub_audit_report.json")
        print("="*70)

if __name__ == "__main__":
    auditor = EPUBAuditor()
    auditor.run_audit()