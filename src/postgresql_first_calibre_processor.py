#!/usr/bin/env python3
"""
Dr. Sarah Chen (陈雪芳) - PostgreSQL-First Calibre Processor
===========================================================

CRITICAL: This is the ONLY acceptable architecture for Calibre integration
- ALL database logic in PostgreSQL functions
- Python layer is THIN and calls single functions only
- NO hardcoded SQL in Python application code
- Clean separation between application and database concerns

Mission: "数据库是图书馆的心脏 - Database logic stays in database"
Author: Dr. Sarah Chen (陈雪芳) - Database Architecture Guardian
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CalibreProcessingResult:
    """Result of Calibre processing operation"""
    success: bool
    books_processed: int
    successful_enhancements: int
    failed_enhancements: int
    total_conflicts: int
    average_quality_improvement: float
    processing_time_ms: int
    message: str

class PostgreSQLFirstCalibreProcessor:
    """
    Dr. Sarah Chen approved Calibre processor
    
    Architecture Principles:
    1. ALL database operations through PostgreSQL functions
    2. NO hardcoded SQL in Python
    3. Single function calls with comprehensive error handling
    4. Clean separation of concerns
    """
    
    def __init__(self, db_host: str = "localhost", db_name: str = "knowledge_base", 
                 db_user: str = "weixiangzhang", calibre_library_path: str = None):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.calibre_library_path = calibre_library_path or "/Users/weixiangzhang/Calibre Library"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Dr.Sarah.Chen.CalibreProcessor - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Database connection
        self.conn = None
        
    def connect_database(self) -> bool:
        """Establish database connection with error handling"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                cursor_factory=RealDictCursor
            )
            self.logger.info("Database connection established")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def validate_system_readiness(self) -> Tuple[bool, Dict]:
        """
        Dr. Sarah Chen approved function call pattern
        Single function call with comprehensive result processing
        """
        if not self.conn:
            return False, {"error": "No database connection"}
            
        try:
            with self.conn.cursor() as cursor:
                # Single function call - Dr. Sarah Chen approved pattern
                cursor.execute("SELECT * FROM api_validate_calibre_integration()")
                validation_results = cursor.fetchall()
                
                # Simple result processing - no database logic in Python
                validation_summary = {
                    "system_ready": True,
                    "checks": []
                }
                
                for result in validation_results:
                    check_info = {
                        "validation_check": result['validation_check'],
                        "status": result['status'],
                        "count_value": result['count_value'],
                        "recommendation": result['recommendation']
                    }
                    validation_summary["checks"].append(check_info)
                    
                    # Check for critical issues
                    if result['status'] in ['MISSING', 'FAILED']:
                        validation_summary["system_ready"] = False
                
                self.logger.info(f"System validation completed: {validation_summary['system_ready']}")
                return validation_summary["system_ready"], validation_summary
                
        except Exception as e:
            self.logger.error(f"System validation failed: {e}")
            return False, {"error": str(e)}
    
    def read_calibre_metadata_opf(self, metadata_path: str) -> Optional[str]:
        """Read metadata.opf file content"""
        try:
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                self.logger.warning(f"Metadata file not found: {metadata_path}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to read metadata file {metadata_path}: {e}")
            return None
    
    def enhance_single_book_metadata(self, book_id: int, calibre_library_path: str, 
                                   metadata_content: str) -> Dict:
        """
        Dr. Sarah Chen approved single book enhancement
        Single function call with result processing only
        """
        if not self.conn:
            return {"success": False, "message": "No database connection"}
            
        try:
            with self.conn.cursor() as cursor:
                # Single function call - Dr. Sarah Chen approved pattern
                cursor.execute("""
                    SELECT * FROM api_apply_calibre_metadata_enhancement(%s, %s, %s, %s)
                """, (book_id, calibre_library_path, metadata_content, 'calibre_wins'))
                
                result = cursor.fetchone()
                self.conn.commit()
                
                # Simple result processing - no database logic in Python
                if result and result['update_success']:
                    self.logger.info(f"Book {book_id} enhanced: {result['fields_updated']}")
                    return {
                        "success": True,
                        "book_id": book_id,
                        "fields_updated": result['fields_updated'],
                        "conflicts_detected": result['conflicts_detected'],
                        "quality_improvement": float(result['quality_improvement']),
                        "final_quality_score": float(result['final_quality_score']),
                        "message": result['enhancement_message']
                    }
                else:
                    return {
                        "success": False,
                        "book_id": book_id,
                        "message": result['enhancement_message'] if result else "Enhancement failed"
                    }
                    
        except Exception as e:
            self.logger.error(f"Single book enhancement failed: {e}")
            return {"success": False, "book_id": book_id, "message": str(e)}
    
    def process_calibre_batch(self, batch_size: int = 50) -> CalibreProcessingResult:
        """
        Dr. Sarah Chen approved batch processing
        Single function call with comprehensive error handling
        """
        if not self.conn:
            return CalibreProcessingResult(
                False, 0, 0, 0, 0, 0.0, 0, "No database connection"
            )
            
        try:
            with self.conn.cursor() as cursor:
                # Single function call - Dr. Sarah Chen approved pattern
                cursor.execute("""
                    SELECT * FROM api_batch_calibre_metadata_sync(%s, %s)
                """, (batch_size, self.calibre_library_path))
                
                result = cursor.fetchone()
                self.conn.commit()
                
                # Simple result processing - no database logic in Python
                if result:
                    processing_result = CalibreProcessingResult(
                        success=True,
                        books_processed=result['books_processed'],
                        successful_enhancements=result['successful_enhancements'],
                        failed_enhancements=result['failed_enhancements'],
                        total_conflicts=result['total_conflicts'],
                        average_quality_improvement=float(result['average_quality_improvement']),
                        processing_time_ms=result['processing_time_ms'],
                        message=result['processing_message']
                    )
                    
                    self.logger.info(f"Batch processing completed: {processing_result.message}")
                    return processing_result
                else:
                    return CalibreProcessingResult(
                        False, 0, 0, 0, 0, 0.0, 0, "No result from batch processing"
                    )
                    
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return CalibreProcessingResult(
                False, 0, 0, 0, 0, 0.0, 0, f"Processing failed: {str(e)}"
            )
    
    def get_processing_queue(self, batch_size: int = 50) -> List[Dict]:
        """
        Dr. Sarah Chen approved queue retrieval
        Single function call for migration queue
        """
        if not self.conn:
            return []
            
        try:
            with self.conn.cursor() as cursor:
                # Single function call - Dr. Sarah Chen approved pattern  
                cursor.execute("SELECT * FROM dr_marcus_get_migration_queue(%s)", (batch_size,))
                queue_results = cursor.fetchall()
                
                # Simple result processing - no database logic in Python
                queue_books = []
                for book in queue_results:
                    queue_books.append({
                        "book_id": book['book_id'],
                        "title": book['title'],
                        "author": book['author'],
                        "file_path": book['file_path'],
                        "current_description": book['current_description'],
                        "current_genre": book['current_genre'],
                        "migration_priority": float(book['migration_priority'])
                    })
                
                self.logger.info(f"Retrieved {len(queue_books)} books for processing")
                return queue_books
                
        except Exception as e:
            self.logger.error(f"Queue retrieval failed: {e}")
            return []
    
    def run_continuous_processing(self, batch_size: int = 25, max_batches: int = 10):
        """
        Dr. Sarah Chen approved continuous processing
        Clean batch processing with proper error handling
        """
        self.logger.info("Starting continuous Calibre metadata processing")
        
        if not self.connect_database():
            self.logger.error("Cannot start processing - database connection failed")
            return
        
        # Validate system readiness
        system_ready, validation_info = self.validate_system_readiness()
        if not system_ready:
            self.logger.error(f"System not ready for processing: {validation_info}")
            return
        
        total_processed = 0
        total_enhanced = 0
        batch_count = 0
        
        try:
            while batch_count < max_batches:
                batch_count += 1
                self.logger.info(f"Processing batch {batch_count}/{max_batches}")
                
                # Process batch using single function call
                result = self.process_calibre_batch(batch_size)
                
                if result.success:
                    total_processed += result.books_processed
                    total_enhanced += result.successful_enhancements
                    
                    self.logger.info(f"Batch {batch_count} results: {result.message}")
                    
                    # Stop if no more books to process
                    if result.books_processed == 0:
                        self.logger.info("No more books to process - stopping")
                        break
                else:
                    self.logger.error(f"Batch {batch_count} failed: {result.message}")
                    break
                    
        except KeyboardInterrupt:
            self.logger.info("Processing interrupted by user")
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
        finally:
            if self.conn:
                self.conn.close()
                
        self.logger.info(f"Processing completed: {total_processed} books processed, {total_enhanced} enhanced")

def main():
    """Command line interface for Dr. Sarah Chen's Calibre processor"""
    parser = argparse.ArgumentParser(description="PostgreSQL-First Calibre Metadata Processor")
    parser.add_argument("--batch-size", type=int, default=25, help="Batch size for processing")
    parser.add_argument("--max-batches", type=int, default=10, help="Maximum batches to process")
    parser.add_argument("--calibre-path", type=str, help="Path to Calibre library")
    parser.add_argument("--validate-only", action="store_true", help="Only validate system readiness")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = PostgreSQLFirstCalibreProcessor(
        calibre_library_path=args.calibre_path
    )
    
    if args.validate_only:
        # Validation only mode
        if processor.connect_database():
            ready, info = processor.validate_system_readiness()
            print(f"System Ready: {ready}")
            print(json.dumps(info, indent=2, default=str))
        sys.exit(0)
    
    # Run continuous processing
    processor.run_continuous_processing(
        batch_size=args.batch_size,
        max_batches=args.max_batches
    )

if __name__ == "__main__":
    main()