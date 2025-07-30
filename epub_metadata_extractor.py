#!/usr/bin/env python3
"""
EPUB Metadata Extractor
========================

Extracts clean metadata directly from EPUB files to fix corrupted Calibre entries
Based on Dr. Marcus Wong & Dr. Sarah Chen's PostgreSQL-First architecture

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
Architecture: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First principles
"""

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import re
from datetime import datetime
import subprocess

class EPUBMetadataExtractor:
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library"):
        self.calibre_library_path = calibre_library_path
        self.calibredb_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
        self.namespaces = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'opf': 'http://www.idpf.org/2007/opf',
            'meta': 'http://www.idpf.org/2007/opf'
        }
        self.extraction_results = {
            "timestamp": datetime.now().isoformat(),
            "processed_files": [],
            "metadata_fixes": [],
            "errors": []
        }
    
    def find_epub_files(self, search_dirs=None):
        """Find all EPUB files in specified directories"""
        if search_dirs is None:
            search_dirs = [
                "ebooks/processed",
                "ebooks/downloads", 
                "src/ebooks/downloads"
            ]
        
        epub_files = []
        for search_dir in search_dirs:
            search_path = Path(search_dir)
            if search_path.exists():
                epub_files.extend(search_path.glob("**/*.epub"))
        
        print(f"📚 Found {len(epub_files)} EPUB files across {len(search_dirs)} directories")
        return epub_files
    
    def extract_epub_metadata(self, epub_path):
        """Extract metadata from EPUB file"""
        try:
            with zipfile.ZipFile(epub_path, 'r') as zip_file:
                # Find the OPF file
                container_xml = zip_file.read('META-INF/container.xml')
                container_root = ET.fromstring(container_xml)
                
                opf_path = None
                for rootfile in container_root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile'):
                    if rootfile.get('media-type') == 'application/oebps-package+xml':
                        opf_path = rootfile.get('full-path')
                        break
                
                if not opf_path:
                    return None
                
                # Read and parse OPF file
                opf_content = zip_file.read(opf_path)
                opf_root = ET.fromstring(opf_content)
                
                # Extract metadata
                metadata = {
                    'title': None,
                    'author': None,
                    'isbn': None,
                    'description': None,
                    'publisher': None,
                    'publication_date': None,
                    'language': None,
                    'series': None,
                    'series_index': None
                }
                
                # Extract title
                title_elem = opf_root.find('.//dc:title', self.namespaces)
                if title_elem is not None:
                    metadata['title'] = title_elem.text
                
                # Extract author(s)
                authors = []
                for creator in opf_root.findall('.//dc:creator', self.namespaces):
                    if creator.text:
                        authors.append(creator.text)
                if authors:
                    metadata['author'] = ', '.join(authors)
                
                # Extract ISBN
                for identifier in opf_root.findall('.//dc:identifier', self.namespaces):
                    if identifier.text and ('isbn' in str(identifier.get('id', '')).lower() or 
                                          'isbn' in str(identifier.get('{http://www.idpf.org/2007/opf}scheme', '')).lower() or
                                          identifier.text.replace('-', '').replace(' ', '').isdigit() and len(identifier.text.replace('-', '').replace(' ', '')) in [10, 13]):
                        metadata['isbn'] = identifier.text
                        break
                
                # Extract description
                description_elem = opf_root.find('.//dc:description', self.namespaces)
                if description_elem is not None:
                    metadata['description'] = description_elem.text
                
                # Extract publisher
                publisher_elem = opf_root.find('.//dc:publisher', self.namespaces)
                if publisher_elem is not None:
                    metadata['publisher'] = publisher_elem.text
                
                # Extract publication date
                date_elem = opf_root.find('.//dc:date', self.namespaces)
                if date_elem is not None:
                    metadata['publication_date'] = date_elem.text
                
                # Extract language
                language_elem = opf_root.find('.//dc:language', self.namespaces)
                if language_elem is not None:
                    metadata['language'] = language_elem.text
                
                return metadata
                
        except Exception as e:
            self.extraction_results["errors"].append({
                "file": str(epub_path),
                "error": str(e)
            })
            return None
    
    def find_matching_calibre_book(self, epub_metadata):
        """Find matching book in Calibre library by title similarity"""
        if not epub_metadata.get('title'):
            return None
        
        title = epub_metadata['title']
        
        # Try exact title match first
        try:
            cmd = [self.calibredb_path, "list", "--library-path", self.calibre_library_path, 
                   "--search", f'title:"={title}"', "--fields", "id,title,authors"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            if lines and lines[0].strip():
                book_id = lines[0].split()[0]
                return book_id
        except:
            pass
        
        # Try partial title match
        try:
            # Search for books with similar titles (first 10 words)
            title_words = title.split()[:10]  # First 10 words
            search_title = ' '.join(title_words)
            
            cmd = [self.calibredb_path, "list", "--library-path", self.calibre_library_path, 
                   "--search", f'title:"{search_title}"', "--fields", "id,title,authors"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split(None, 2)
                    if len(parts) >= 2:
                        book_id = parts[0]
                        calibre_title = parts[1] if len(parts) > 1 else ""
                        
                        # Check if titles are similar (allowing for truncation)
                        if (calibre_title.lower() in title.lower() or 
                            title.lower().startswith(calibre_title.lower()) or
                            calibre_title.lower().startswith(title.lower()[:len(calibre_title)])):
                            return book_id
        except:
            pass
        
        return None
    
    def update_calibre_metadata(self, book_id, epub_metadata):
        """Update Calibre book metadata with EPUB metadata"""
        updates = []
        
        if epub_metadata.get('title'):
            updates.extend(["--title", epub_metadata['title']])
        
        if epub_metadata.get('author'):
            updates.extend(["--authors", epub_metadata['author']])
        
        if epub_metadata.get('isbn'):
            updates.extend(["--isbn", epub_metadata['isbn']])
        
        if epub_metadata.get('description'):
            updates.extend(["--comments", epub_metadata['description']])
        
        if epub_metadata.get('publisher'):
            updates.extend(["--publisher", epub_metadata['publisher']])
        
        if epub_metadata.get('publication_date'):
            # Parse date to YYYY-MM-DD format
            pub_date = epub_metadata['publication_date']
            if pub_date:
                # Extract year if it's a full date
                year_match = re.search(r'\d{4}', pub_date)
                if year_match:
                    updates.extend(["--pubdate", year_match.group()])
        
        if updates:
            try:
                cmd = [self.calibredb_path, "set_metadata", "--library-path", self.calibre_library_path, 
                       str(book_id)] + updates
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return True, f"Updated metadata for book ID {book_id}"
            except subprocess.CalledProcessError as e:
                return False, f"Failed to update book ID {book_id}: {e.stderr}"
        
        return False, "No metadata updates needed"
    
    def fix_truncated_titles(self):
        """Fix known truncated titles by finding their EPUB sources"""
        print("✂️  Fixing truncated titles...")
        
        # Get list of books with potentially truncated titles
        truncated_books = []
        try:
            cmd = [self.calibredb_path, "list", "--library-path", self.calibre_library_path, 
                   "--fields", "id,title,authors"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split(None, 2)
                    if len(parts) >= 2:
                        book_id = parts[0]
                        title_and_rest = ' '.join(parts[1:])
                        
                        # Look for titles that seem truncated
                        if (len(title_and_rest) < 100 and  # Reasonable title length
                            (title_and_rest.endswith(' ') or  # Ends with space
                             not title_and_rest.split()[-1].isalpha() or  # Last word not complete
                             len(title_and_rest.split()[0]) < 20)):  # Very short first word
                            
                            truncated_books.append({
                                "id": book_id,
                                "current_title": title_and_rest[:50]  # First 50 chars
                            })
        
        except Exception as e:
            print(f"❌ Error getting book list: {e}")
            return
        
        print(f"📋 Found {len(truncated_books)} books with potentially truncated titles")
        
        # Find EPUB files and try to match them
        epub_files = self.find_epub_files()
        
        fixes_applied = 0
        for book_info in truncated_books[:10]:  # Limit to first 10 for now
            print(f"🔍 Processing book ID {book_info['id']}: {book_info['current_title']}...")
            
            # Try to find matching EPUB by searching filenames
            best_match = None
            for epub_path in epub_files:
                epub_filename = epub_path.stem.lower()
                current_title_words = book_info['current_title'].lower().split()[:3]  # First 3 words
                
                # Check if filename contains significant words from current title
                matches = sum(1 for word in current_title_words if word in epub_filename)
                if matches >= 2:  # At least 2 words match
                    epub_metadata = self.extract_epub_metadata(epub_path)
                    if epub_metadata and epub_metadata.get('title'):
                        best_match = epub_metadata
                        break
            
            if best_match:
                success, message = self.update_calibre_metadata(book_info['id'], best_match)
                if success:
                    fixes_applied += 1
                    print(f"✅ {message}")
                    self.extraction_results["metadata_fixes"].append({
                        "book_id": book_info['id'],
                        "old_title": book_info['current_title'],
                        "new_title": best_match['title'],
                        "epub_source": str(epub_path)
                    })
                else:
                    print(f"❌ {message}")
        
        print(f"🔧 Applied {fixes_applied} metadata fixes")
    
    def run_metadata_extraction(self):
        """Run the complete metadata extraction and fixing process"""
        print("🚀 Starting EPUB Metadata Extraction and Calibre Fixes...")
        
        # Fix truncated titles first
        self.fix_truncated_titles()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"epub_metadata_extraction_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.extraction_results, f, indent=2)
        
        print(f"📄 Extraction report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("📊 METADATA EXTRACTION SUMMARY")
        print("="*60)
        print(f"🔧 Metadata Fixes Applied: {len(self.extraction_results['metadata_fixes'])}")
        print(f"❌ Errors: {len(self.extraction_results['errors'])}")
        
        if self.extraction_results["metadata_fixes"]:
            print(f"\n✅ Fixed Titles:")
            for fix in self.extraction_results["metadata_fixes"]:
                print(f"   ID {fix['book_id']}: {fix['old_title'][:30]}... → {fix['new_title'][:30]}...")

if __name__ == "__main__":
    extractor = EPUBMetadataExtractor()
    extractor.run_metadata_extraction()