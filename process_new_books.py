#!/usr/bin/env python3
"""
🚀 LibraryOfBabel One-Click Ebook Processing Automation
Double-click this script to process all new ebooks with:
- EPUB text extraction and chunking
- Database ingestion with duplicate detection
- Vector embedding generation
- AI-powered genre classification
- Complete automation with progress reporting
"""

import os
import sys
import subprocess
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
log_file = f"processing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class EbookProcessor:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.venv_path = self.script_dir / "venv"
        self.ebook_dirs = [
            self.script_dir / "ebooks" / "downloads",
            Path.home() / "Downloads",  # Check Downloads folder
            Path.home() / "Desktop",     # Check Desktop
        ]
        
        # Processing statistics
        self.stats = {
            "start_time": time.time(),
            "epub_files_found": 0,
            "books_processed": 0,
            "books_ingested": 0,
            "embeddings_generated": 0,
            "genres_classified": 0,
            "errors": []
        }
    
    def print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    📚 LibraryOfBabel Ebook Processor 🤖                     ║
║                          One-Click Automation System                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✨ EPUB Processing        📊 Vector Embeddings      🎭 Genre Classification ║
║  🗄️  Database Ingestion    🔍 Semantic Search        🚫 Duplicate Detection  ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
        logger.info("🚀 LibraryOfBabel Ebook Processor Started")
    
    def check_prerequisites(self):
        """Check if all required components are available"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check virtual environment
        if not self.venv_path.exists():
            logger.error("❌ Virtual environment not found. Run setup first.")
            return False
        
        # Check database connection
        try:
            result = subprocess.run([
                str(self.venv_path / "bin" / "python3"),
                "-c", "import psycopg2; conn=psycopg2.connect(database='knowledge_base', user='weixiangzhang'); conn.close(); print('OK')"
            ], capture_output=True, text=True, cwd=self.script_dir)
            
            if result.returncode != 0:
                logger.error("❌ Database connection failed")
                return False
        except Exception as e:
            logger.error(f"❌ Database check failed: {e}")
            return False
        
        # Check Ollama
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if "nomic-embed-text" not in result.stdout:
                logger.error("❌ Ollama nomic-embed-text model not found")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama check failed: {e}")
            return False
        
        logger.info("✅ All prerequisites satisfied")
        return True
    
    def find_new_epub_files(self):
        """Find new EPUB files that haven't been processed"""
        logger.info("📁 Scanning for new EPUB files...")
        
        new_files = []
        
        for ebook_dir in self.ebook_dirs:
            if ebook_dir.exists():
                logger.info(f"   Scanning: {ebook_dir}")
                
                # Find all EPUB files
                epub_files = list(ebook_dir.glob("**/*.epub"))
                
                for epub_file in epub_files:
                    # Check if already processed (simple filename check)
                    output_name = epub_file.stem + "_processed.json"
                    output_file = self.script_dir / "output" / output_name
                    
                    if not output_file.exists():
                        new_files.append(epub_file)
                        logger.info(f"   📖 New: {epub_file.name}")
        
        self.stats["epub_files_found"] = len(new_files)
        logger.info(f"📊 Found {len(new_files)} new EPUB files")
        return new_files
    
    def run_command(self, command, description):
        """Run a command with logging and error handling"""
        logger.info(f"⚡ {description}...")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.script_dir,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info(f"✅ {description} completed successfully")
                return True, result.stdout
            else:
                logger.error(f"❌ {description} failed: {result.stderr}")
                self.stats["errors"].append(f"{description}: {result.stderr}")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ {description} timed out")
            self.stats["errors"].append(f"{description}: Timeout")
            return False, "Timeout"
        except Exception as e:
            logger.error(f"💥 {description} crashed: {e}")
            self.stats["errors"].append(f"{description}: {e}")
            return False, str(e)
    
    def process_epub_files(self, epub_files):
        """Process EPUB files for text extraction"""
        if not epub_files:
            logger.info("⏭️  No new EPUB files to process")
            return True
        
        # Create temporary directory with EPUB files
        temp_dir = self.script_dir / "temp_processing"
        temp_dir.mkdir(exist_ok=True)
        
        # Copy files to processing directory
        for epub_file in epub_files:
            target_file = temp_dir / epub_file.name
            if not target_file.exists():
                import shutil
                shutil.copy2(epub_file, target_file)
        
        # Run batch processor
        success, output = self.run_command([
            str(self.venv_path / "bin" / "python3"),
            "src/batch_processor.py",
            "--input", str(temp_dir),
            "--output", "output"
        ], f"EPUB processing for {len(epub_files)} books")
        
        if success:
            # Count processed files
            processed_count = output.count("✅ Processing complete")
            self.stats["books_processed"] = processed_count
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return success
    
    def ingest_to_database(self):
        """Ingest processed JSON files to database"""
        success, output = self.run_command([
            str(self.venv_path / "bin" / "python3"),
            "database/schema/ingest_data.py"
        ], "Database ingestion")
        
        if success:
            # Parse ingestion stats from output
            if "Books inserted:" in output:
                try:
                    lines = output.split('\n')
                    for line in lines:
                        if "Books inserted:" in line:
                            count = int(line.split(':')[1].strip())
                            self.stats["books_ingested"] = count
                            break
                except:
                    pass
        
        return success
    
    def generate_embeddings(self):
        """Generate vector embeddings for new chunks"""
        success, output = self.run_command([
            str(self.venv_path / "bin" / "python3"),
            "src/vector_embeddings.py",
            "--generate",
            "--batch-size", "20"
        ], "Vector embedding generation")
        
        if success:
            # Parse embedding stats
            if "Total processed:" in output:
                try:
                    lines = output.split('\n')
                    for line in lines:
                        if "Total processed:" in line:
                            count = int(line.split(':')[1].strip().replace(',', ''))
                            self.stats["embeddings_generated"] = count
                            break
                except:
                    pass
        
        return success
    
    def classify_genres(self):
        """AI-powered genre classification"""
        success, output = self.run_command([
            str(self.venv_path / "bin" / "python3"),
            "src/genre_classifier.py",
            "--classify-all",
            "--min-confidence", "0.3"
        ], "AI genre classification")
        
        if success:
            # Parse genre classification stats
            if "Updated:" in output:
                try:
                    lines = output.split('\n')
                    for line in lines:
                        if "Updated:" in line:
                            count = int(line.split(':')[1].strip())
                            self.stats["genres_classified"] = count
                            break
                except:
                    pass
        
        return success
    
    def generate_report(self):
        """Generate processing report"""
        total_time = time.time() - self.stats["start_time"]
        
        report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        📊 PROCESSING COMPLETE REPORT 📊                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏱️  Total Processing Time: {total_time/60:.1f} minutes

📚 File Processing:
   • EPUB files found: {self.stats['epub_files_found']}
   • Books processed: {self.stats['books_processed']}
   • Books ingested: {self.stats['books_ingested']}

🤖 AI Enhancement:
   • Vector embeddings: {self.stats['embeddings_generated']}
   • Genres classified: {self.stats['genres_classified']}

{"❌ Errors encountered: " + str(len(self.stats['errors'])) if self.stats['errors'] else "✅ No errors - Perfect run!"}

🔍 Next Steps:
   • Test semantic search: python3 src/vector_embeddings.py --search "your query"
   • Check genre stats: python3 src/genre_classifier.py --stats
   • Start search API: python3 src/api/search_api.py

📁 Log saved to: {log_file}
        """
        
        print(report)
        logger.info("📋 Processing report generated")
        
        # Save report to file
        report_file = f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
    
    def run_full_pipeline(self):
        """Run the complete processing pipeline"""
        self.print_banner()
        
        # Prerequisites check
        if not self.check_prerequisites():
            logger.error("💥 Prerequisites not met. Exiting.")
            return False
        
        # Find new files
        epub_files = self.find_new_epub_files()
        
        if not epub_files:
            logger.info("🎉 No new books to process. Library is up to date!")
            self.generate_report()
            return True
        
        logger.info(f"🚀 Starting processing pipeline for {len(epub_files)} books...")
        
        # Processing steps
        steps = [
            (self.process_epub_files, epub_files),
            (self.ingest_to_database, ),
            (self.generate_embeddings, ),
            (self.classify_genres, )
        ]
        
        for i, step_info in enumerate(steps, 1):
            step_func = step_info[0]
            step_args = step_info[1:] if len(step_info) > 1 else ()
            
            logger.info(f"📋 Step {i}/{len(steps)}: {step_func.__name__}")
            
            success = step_func(*step_args)
            if not success:
                logger.error(f"💥 Pipeline failed at step {i}. Check logs for details.")
                self.generate_report()
                return False
        
        logger.info("🎉 Complete pipeline finished successfully!")
        self.generate_report()
        return True


def main():
    """Main entry point"""
    try:
        processor = EbookProcessor()
        success = processor.run_full_pipeline()
        
        if success:
            print("\n🎉 All done! Your library has been updated with AI-powered features.")
            input("\nPress Enter to exit...")
        else:
            print("\n💥 Processing encountered errors. Check the log file for details.")
            input("\nPress Enter to exit...")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Processing interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()