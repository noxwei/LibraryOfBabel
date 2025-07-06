#!/usr/bin/env python3
"""
🚀 Mass Download Orchestrator
Coordinates priority downloads from Babel's Archive → LibraryOfBabel processing pipeline
"""

import json
import requests
import time
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mass_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MassDownloadOrchestrator:
    """Orchestrates mass downloads of priority books"""
    
    def __init__(self, max_downloads: int = 800):
        self.babel_archive_api = "http://localhost:8181/api"
        self.max_downloads = max_downloads
        self.download_count = 0
        
        # Paths
        self.queue_file = "completed_books_download_queue.json"
        self.babel_downloads_dir = Path("../babels-archive/downloads")
        self.library_downloads_dir = Path("ebooks/downloads")
        
        # Stats
        self.stats = {
            'total_requested': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'books_not_found': 0,
            'processing_queue': [],
            'start_time': time.time()
        }
        
    def load_priority_queue(self) -> List[Dict]:
        """Load the priority download queue"""
        try:
            with open(self.queue_file, 'r') as f:
                queue = json.load(f)
            logger.info(f"📚 Loaded {len(queue)} priority books from queue")
            return queue
        except FileNotFoundError:
            logger.error(f"❌ Queue file not found: {self.queue_file}")
            return []
        except Exception as e:
            logger.error(f"❌ Error loading queue: {e}")
            return []
    
    def search_book_via_babel_archive(self, title: str, author: str) -> Optional[Dict]:
        """Search for book via Babel's Archive API"""
        try:
            # Clean search terms
            search_query = f"{title} {author}".strip()
            
            # Call Babel's Archive search API
            response = requests.get(
                f"{self.babel_archive_api}/books/search",
                params={
                    'q': search_query,
                    'maxResults': 3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                if results and len(results) > 0:
                    # Return the first/best match
                    return results[0]
                else:
                    logger.warning(f"📭 No results found for: {title} by {author}")
                    return None
            else:
                logger.error(f"❌ Search API error {response.status_code}: {title}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error searching '{title}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error searching '{title}': {e}")
            return None
    
    def download_book_via_babel_archive(self, book_data: Dict, priority_book: Dict) -> bool:
        """Download book via Babel's Archive API"""
        try:
            # Trigger download via Babel's Archive
            download_request = {
                'title': book_data.get('title', priority_book['title']),
                'author': book_data.get('author', priority_book['author']),
                'book_id': book_data.get('id', ''),
                'priority': True,
                'source': 'completed_books_queue'
            }
            
            response = requests.post(
                f"{self.babel_archive_api}/books/download",
                json=download_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Download initiated: {priority_book['title']} by {priority_book['author']}")
                
                # Add to processing queue for later LibraryOfBabel ingestion
                self.stats['processing_queue'].append({
                    'title': priority_book['title'],
                    'author': priority_book['author'],
                    'download_id': result.get('downloadId', ''),
                    'completed_date': priority_book['completed_date'],
                    'download_initiated': datetime.now().isoformat()
                })
                
                return True
            else:
                logger.error(f"❌ Download failed {response.status_code}: {priority_book['title']}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error downloading '{priority_book['title']}': {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading '{priority_book['title']}': {e}")
            return False
    
    def process_priority_queue(self, queue: List[Dict]) -> None:
        """Process the priority download queue"""
        logger.info(f"🚀 Starting mass download of {len(queue)} priority books")
        logger.info(f"📊 Download limit: {self.max_downloads}")
        
        for i, book in enumerate(queue):
            if self.download_count >= self.max_downloads:
                logger.warning(f"⚠️ Reached download limit ({self.max_downloads})")
                break
            
            title = book['title']
            author = book['author']
            completed_date = book['completed_date']
            
            logger.info(f"📖 [{i+1}/{len(queue)}] Processing: {title} by {author}")
            self.stats['total_requested'] += 1
            
            # Search for book
            search_result = self.search_book_via_babel_archive(title, author)
            
            if search_result:
                # Attempt download
                if self.download_book_via_babel_archive(search_result, book):
                    self.stats['successful_downloads'] += 1
                    self.download_count += 1
                    
                    # Brief pause between downloads to be respectful
                    time.sleep(2)
                else:
                    self.stats['failed_downloads'] += 1
            else:
                self.stats['books_not_found'] += 1
            
            # Progress update every 10 books
            if (i + 1) % 10 == 0:
                self.print_progress_update()
        
        logger.info("🎯 Mass download phase completed!")
    
    def print_progress_update(self):
        """Print progress statistics"""
        elapsed = time.time() - self.stats['start_time']
        logger.info(f"""
📊 Progress Update:
   📚 Total Requested: {self.stats['total_requested']}
   ✅ Successful Downloads: {self.stats['successful_downloads']}
   ❌ Failed Downloads: {self.stats['failed_downloads']}
   📭 Books Not Found: {self.stats['books_not_found']}
   ⏱️ Elapsed Time: {elapsed:.1f}s
   💾 Processing Queue: {len(self.stats['processing_queue'])} books
        """)
    
    def setup_library_integration(self):
        """Set up integration with LibraryOfBabel processing"""
        # Ensure LibraryOfBabel download directory exists
        self.library_downloads_dir.mkdir(parents=True, exist_ok=True)
        
        # Create symbolic link from Babel's Archive downloads to LibraryOfBabel
        if not (self.library_downloads_dir / "babel_archive_link").exists():
            try:
                (self.library_downloads_dir / "babel_archive_link").symlink_to(
                    self.babel_downloads_dir.absolute()
                )
                logger.info("🔗 Created symbolic link for automatic processing")
            except Exception as e:
                logger.warning(f"⚠️ Could not create symbolic link: {e}")
    
    def save_processing_queue(self):
        """Save processing queue for LibraryOfBabel ingestion"""
        processing_file = f"processing_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(processing_file, 'w') as f:
            json.dump({
                'stats': self.stats,
                'processing_queue': self.stats['processing_queue'],
                'generated_at': datetime.now().isoformat(),
                'total_downloads': self.download_count
            }, f, indent=2)
        
        logger.info(f"💾 Saved processing queue: {processing_file}")
        return processing_file
    
    def trigger_library_processing(self):
        """Trigger LibraryOfBabel automated processing"""
        try:
            # Look for the automated processor
            processor_script = Path("src/automated_ebook_processor.py")
            if processor_script.exists():
                logger.info("🤖 Triggering LibraryOfBabel automated processing...")
                
                import subprocess
                result = subprocess.run([
                    "python3", str(processor_script)
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info("✅ LibraryOfBabel processing initiated successfully")
                else:
                    logger.error(f"❌ Processing error: {result.stderr}")
            else:
                logger.warning("⚠️ Automated processor not found, manual processing required")
                
        except Exception as e:
            logger.error(f"❌ Error triggering processing: {e}")
    
    def run_mass_download(self):
        """Main orchestrator method"""
        logger.info("🚀 Mass Download Orchestrator Starting...")
        logger.info("="*60)
        
        # Load priority queue
        queue = self.load_priority_queue()
        if not queue:
            logger.error("❌ No books to download. Exiting.")
            return
        
        # Setup LibraryOfBabel integration
        self.setup_library_integration()
        
        # Process downloads
        self.process_priority_queue(queue)
        
        # Save results
        processing_file = self.save_processing_queue()
        
        # Print final statistics
        self.print_final_stats()
        
        # Trigger LibraryOfBabel processing
        self.trigger_library_processing()
        
        logger.info("🎯 Mass download orchestration complete!")
        return processing_file
    
    def print_final_stats(self):
        """Print final download statistics"""
        elapsed = time.time() - self.stats['start_time']
        success_rate = (self.stats['successful_downloads'] / max(self.stats['total_requested'], 1)) * 100
        
        logger.info(f"""
🎯 FINAL DOWNLOAD STATISTICS:
==================================================
📚 Total Books Requested: {self.stats['total_requested']}
✅ Successful Downloads: {self.stats['successful_downloads']}
❌ Failed Downloads: {self.stats['failed_downloads']}
📭 Books Not Found: {self.stats['books_not_found']}
📊 Success Rate: {success_rate:.1f}%
⏱️ Total Time: {elapsed:.1f}s
💾 Books Ready for Processing: {len(self.stats['processing_queue'])}
🔄 Downloads Remaining: {self.max_downloads - self.download_count}

🚀 Next Steps:
1. Downloaded EPUBs will be automatically processed by LibraryOfBabel
2. Books will be ingested into PostgreSQL knowledge base
3. AI agents will have access to your completed reading collection
4. Enhanced search capabilities across your read books
==================================================
        """)

def main():
    # Create orchestrator with download limit
    orchestrator = MassDownloadOrchestrator(max_downloads=800)
    
    # Run the mass download
    processing_file = orchestrator.run_mass_download()
    
    print(f"\n✅ Mass download complete! Processing queue saved to: {processing_file}")
    print("🎯 Your completed books are now being downloaded and will be processed into LibraryOfBabel!")

if __name__ == "__main__":
    main()