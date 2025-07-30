#!/usr/bin/env python3
"""
Calibre Path Resolver
=====================

Resolves actual file paths for books in Calibre library
Based on Dr. Marcus Wong's investigation of Calibre directory structure

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
"""

import subprocess
import os
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)

class CalibrePathResolver:
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library"):
        self.calibre_library_path = Path(calibre_library_path)
        self.calibredb_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
    
    def get_book_metadata(self, book_id):
        """Get complete metadata for a Calibre book"""
        try:
            cmd = [self.calibredb_path, "show_metadata", str(book_id), 
                   "--library-path", str(self.calibre_library_path)]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse metadata - handle multiline fields like Comments
            metadata = {}
            current_key = None
            current_value = []
            
            for line in result.stdout.split('\n'):
                if ':' in line and not line.startswith(' '):
                    # Save previous field if exists
                    if current_key:
                        metadata[current_key] = '\n'.join(current_value).strip()
                    
                    # Start new field
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    current_value = [value.strip()] if value.strip() else []
                elif current_key and line.strip():
                    # Continuation of multiline field
                    current_value.append(line.strip())
            
            # Save last field
            if current_key:
                metadata[current_key] = '\n'.join(current_value).strip()
            
            return metadata
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get metadata for book {book_id}: {e}")
            return None
    
    def resolve_calibre_file_path(self, book_id):
        """Resolve the actual file path for a Calibre book"""
        try:
            # Get book metadata
            metadata = self.get_book_metadata(book_id)
            if not metadata:
                return None
            
            title = metadata.get('Title', '').strip()
            author = metadata.get('Author(s)', '').strip()
            
            if not title or not author:
                logger.error(f"Missing title or author for book {book_id}")
                return None
            
            # Clean author name (remove sort information in brackets)
            author_clean = re.sub(r'\s*\[.*?\]', '', author)
            author_clean = author_clean.split(',')[0].strip()  # Take first author if multiple
            
            # Build expected directory path
            # Format: /Author/Title (ID)/Title - Author.epub
            book_dir_name = f"{title} ({book_id})"
            epub_filename = f"{title} - {author_clean}.epub"
            
            # Construct full path
            full_path = self.calibre_library_path / author_clean / book_dir_name / epub_filename
            
            # Check if file exists
            if full_path.exists():
                return str(full_path)
            
            # If not found, try to find it by searching
            logger.warning(f"Expected path not found: {full_path}")
            return self.search_for_book_file(book_id, title, author_clean)
            
        except Exception as e:
            logger.error(f"Error resolving path for book {book_id}: {e}")
            return None
    
    def search_for_book_file(self, book_id, title, author):
        """Search for book file in Calibre library when expected path fails"""
        try:
            # Search for directories containing the book ID
            for author_dir in self.calibre_library_path.iterdir():
                if not author_dir.is_dir():
                    continue
                
                for book_dir in author_dir.iterdir():
                    if not book_dir.is_dir():
                        continue
                    
                    # Check if directory name contains the book ID
                    if f"({book_id})" in book_dir.name:
                        # Look for EPUB file in this directory
                        for file in book_dir.iterdir():
                            if file.suffix.lower() == '.epub':
                                logger.info(f"Found book {book_id} at: {file}")
                                return str(file)
            
            logger.error(f"Could not find file for book {book_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for book {book_id}: {e}")
            return None
    
    def validate_calibre_path(self, file_path):
        """Validate that a Calibre file path exists and is accessible"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            
            if not path.is_file():
                return False, "Path is not a file"
            
            if path.suffix.lower() != '.epub':
                return False, "File is not an EPUB"
            
            # Check file size (should be reasonable)
            file_size = path.stat().st_size
            if file_size < 1000:
                return False, "File too small"
            
            return True, "Valid EPUB file"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_file_info(self, file_path):
        """Get detailed file information"""
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            return {
                'size_bytes': stat.st_size,
                'modified_time': stat.st_mtime,
                'is_readable': os.access(path, os.R_OK),
                'file_extension': path.suffix.lower()
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return None

def test_path_resolver():
    """Test the path resolver with known book IDs"""
    resolver = CalibrePathResolver()
    
    # Test with book ID 2229 (Can't Even)
    test_ids = [2229, 2230, 2231]
    
    for book_id in test_ids:
        print(f"\n🔍 Testing book ID: {book_id}")
        
        # Get metadata
        metadata = resolver.get_book_metadata(book_id)
        if metadata:
            print(f"   Title: {metadata.get('Title', 'Unknown')}")
            print(f"   Author: {metadata.get('Author(s)', 'Unknown')}")
        
        # Resolve path
        file_path = resolver.resolve_calibre_file_path(book_id)
        if file_path:
            print(f"   ✅ Path: {file_path}")
            
            # Validate
            is_valid, msg = resolver.validate_calibre_path(file_path)
            if is_valid:
                print(f"   ✅ Validation: {msg}")
                
                # Get file info
                file_info = resolver.get_file_info(file_path)
                if file_info:
                    print(f"   📁 Size: {file_info['size_bytes']:,} bytes")
            else:
                print(f"   ❌ Validation failed: {msg}")
        else:
            print(f"   ❌ Could not resolve path")

if __name__ == "__main__":
    test_path_resolver()