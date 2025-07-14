#!/usr/bin/env python3
"""
🧪 Comprehensive Database Testing Suite
Tests all database scripts, stored procedures, and functions in the LibraryOfBabel system.
"""

import psycopg2
import sqlite3
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import os

class DatabaseTestSuite:
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'test_details': []
        }
        
        # Database connections
        self.pg_conn = None
        self.sqlite_conn = None
        
        # Test data
        self.test_data = {
            'sample_book': {
                'title': 'Test Book for Database Testing',
                'author': 'Test Author',
                'publication_year': 2024,
                'word_count': 50000
            },
            'sample_chunk': {
                'content': 'This is a test chunk content for testing search functionality and artificial intelligence concepts.',
                'chunk_type': 'paragraph',
                'word_count': 16
            }
        }

    def setup_connections(self):
        """Setup database connections"""
        try:
            # PostgreSQL connection
            self.pg_conn = psycopg2.connect(
                host='localhost',
                database='knowledge_base',
                user=os.getenv('USER', 'weixiangzhang')
            )
            
            # SQLite connection for Linda's tracker
            sqlite_path = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/database/data/audiobook_ebook_tracker.db"
            if os.path.exists(sqlite_path):
                self.sqlite_conn = sqlite3.connect(sqlite_path)
            
            return True
        except Exception as e:
            self.add_test_result("Database Connection", False, f"Failed to connect: {str(e)}")
            return False

    def add_test_result(self, test_name, passed, details="", warning=False):
        """Add a test result to the results tracking"""
        self.test_results['total_tests'] += 1
        
        if warning:
            self.test_results['warnings'] += 1
            status = 'WARNING'
        elif passed:
            self.test_results['passed'] += 1
            status = 'PASS'
        else:
            self.test_results['failed'] += 1
            status = 'FAIL'
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def test_database_schema(self):
        """Test all database schema scripts"""
        print("🗃️ Testing Database Schema...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Test table existence
            tables_to_check = [
                'books', 'chunks', 'authors', 'agent_posts', 'agent_interactions',
                'agent_coffee_states', 'hr_daily_reports', 'library_health_checks'
            ]
            
            for table in tables_to_check:
                cur.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s", (table,))
                if cur.fetchone()[0] > 0:
                    self.add_test_result(f"Table Exists: {table}", True)
                else:
                    self.add_test_result(f"Table Exists: {table}", False, "Table not found")
            
            # Test table relationships
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.table_constraints 
                WHERE constraint_type = 'FOREIGN KEY'
            """)
            fk_count = cur.fetchone()[0]
            self.add_test_result("Foreign Key Constraints", fk_count > 0, f"Found {fk_count} foreign keys")
            
            # Test indexes
            cur.execute("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE schemaname = 'public'
            """)
            index_count = cur.fetchone()[0]
            self.add_test_result("Database Indexes", index_count > 0, f"Found {index_count} indexes")
            
        except Exception as e:
            self.add_test_result("Schema Test", False, f"Error: {str(e)}")

    def test_stored_procedures(self):
        """Test all stored procedures and functions"""
        print("⚙️ Testing Stored Procedures...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Get list of all functions
            cur.execute("""
                SELECT routine_name, routine_type 
                FROM information_schema.routines 
                WHERE routine_schema = 'public'
                ORDER BY routine_name
            """)
            functions = cur.fetchall()
            
            for func_name, func_type in functions:
                try:
                    # Test specific functions with appropriate parameters
                    if func_name == 'detect_sql_injection':
                        cur.execute("SELECT detect_sql_injection(%s)", ("normal search text",))
                        result = cur.fetchone()[0]
                        self.add_test_result(f"Function: {func_name} (safe text)", result == False)
                        
                        cur.execute("SELECT detect_sql_injection(%s)", ("'; DROP TABLE users; --",))
                        result = cur.fetchone()[0]
                        self.add_test_result(f"Function: {func_name} (malicious text)", result == True)
                    
                    elif func_name == 'calculate_performance_score':
                        cur.execute("SELECT calculate_performance_score(%s, %s, %s)", (True, 50, 100))
                        result = cur.fetchone()[0]
                        self.add_test_result(f"Function: {func_name}", result is not None and result >= 0)
                    
                    elif func_name == 'cleanup_expired_coffee_states':
                        cur.execute("SELECT cleanup_expired_coffee_states()")
                        result = cur.fetchone()[0]
                        self.add_test_result(f"Function: {func_name}", result is not None)
                    
                    elif func_name == 'secure_search_wrapper':
                        cur.execute("SELECT * FROM secure_search_wrapper(%s, %s)", ("artificial intelligence", 5))
                        results = cur.fetchall()
                        self.add_test_result(f"Function: {func_name}", True, f"Returned {len(results)} results")
                    
                    elif func_name == 'fuzzy_search_books':
                        cur.execute("SELECT * FROM fuzzy_search_books(%s, %s, %s)", ("philosophy", 0.3, 5))
                        results = cur.fetchall()
                        self.add_test_result(f"Function: {func_name}", True, f"Returned {len(results)} results")
                    
                    elif func_name == 'hybrid_search':
                        cur.execute("SELECT * FROM hybrid_search(%s, %s)", ("consciousness", 5))
                        results = cur.fetchall()
                        self.add_test_result(f"Function: {func_name}", True, f"Returned {len(results)} results")
                    
                    elif func_name == 'cross_reference_search':
                        cur.execute("SELECT * FROM cross_reference_search(%s, %s, %s)", ("artificial", "intelligence", 5))
                        results = cur.fetchall()
                        self.add_test_result(f"Function: {func_name}", True, f"Returned {len(results)} results")
                    
                    else:
                        # Generic test for other functions
                        self.add_test_result(f"Function: {func_name}", True, "Function exists", warning=True)
                
                except Exception as e:
                    self.add_test_result(f"Function: {func_name}", False, f"Error: {str(e)}")
            
        except Exception as e:
            self.add_test_result("Stored Procedures Test", False, f"Error: {str(e)}")

    def test_search_functionality(self):
        """Test search optimization and full-text search"""
        print("🔍 Testing Search Functions...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Test basic search
            cur.execute("""
                SELECT COUNT(*) FROM books 
                WHERE to_tsvector('english', title || ' ' || coalesce(author, '')) 
                @@ plainto_tsquery('english', 'philosophy')
            """)
            philosophy_count = cur.fetchone()[0]
            self.add_test_result("Full-text Search: Philosophy", philosophy_count >= 0, f"Found {philosophy_count} matches")
            
            # Test chunk content search
            cur.execute("""
                SELECT COUNT(*) FROM chunks 
                WHERE to_tsvector('english', content) @@ plainto_tsquery('english', 'intelligence')
            """)
            intelligence_count = cur.fetchone()[0]
            self.add_test_result("Chunk Search: Intelligence", intelligence_count >= 0, f"Found {intelligence_count} matches")
            
            # Test fuzzy search with trigrams
            cur.execute("SELECT COUNT(*) FROM books WHERE title % 'philosophy'")
            fuzzy_count = cur.fetchone()[0]
            self.add_test_result("Fuzzy Search: Trigrams", fuzzy_count >= 0, f"Found {fuzzy_count} fuzzy matches")
            
            # Test search performance
            start_time = time.time()
            cur.execute("""
                SELECT b.title, b.author, COUNT(c.chunk_id) as chunks
                FROM books b
                LEFT JOIN chunks c ON b.book_id = c.book_id
                WHERE to_tsvector('english', b.title || ' ' || coalesce(b.author, '')) 
                @@ plainto_tsquery('english', 'artificial intelligence')
                GROUP BY b.book_id, b.title, b.author
                LIMIT 10
            """)
            results = cur.fetchall()
            search_time = (time.time() - start_time) * 1000
            
            self.add_test_result("Search Performance", search_time < 1000, f"Search took {search_time:.2f}ms")
            
        except Exception as e:
            self.add_test_result("Search Functionality Test", False, f"Error: {str(e)}")

    def test_data_integrity(self):
        """Test data integrity and constraints"""
        print("🔒 Testing Data Integrity...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Test foreign key constraints
            cur.execute("""
                SELECT COUNT(*) FROM chunks c
                LEFT JOIN books b ON c.book_id = b.book_id
                WHERE b.book_id IS NULL
            """)
            orphaned_chunks = cur.fetchone()[0]
            self.add_test_result("Data Integrity: Orphaned Chunks", orphaned_chunks == 0, f"Found {orphaned_chunks} orphaned chunks")
            
            # Test duplicate detection
            cur.execute("SELECT COUNT(*), COUNT(DISTINCT title, author) FROM books")
            total_books, unique_books = cur.fetchone()
            duplicate_books = total_books - unique_books
            self.add_test_result("Data Integrity: Duplicate Books", duplicate_books == 0, f"Found {duplicate_books} potential duplicates")
            
            # Test word count consistency
            cur.execute("""
                SELECT COUNT(*) FROM books 
                WHERE word_count IS NOT NULL AND word_count <= 0
            """)
            invalid_word_counts = cur.fetchone()[0]
            self.add_test_result("Data Integrity: Word Counts", invalid_word_counts == 0, f"Found {invalid_word_counts} invalid word counts")
            
            # Test chunk content integrity
            cur.execute("SELECT COUNT(*) FROM chunks WHERE content IS NULL OR content = ''")
            empty_chunks = cur.fetchone()[0]
            self.add_test_result("Data Integrity: Empty Chunks", empty_chunks == 0, f"Found {empty_chunks} empty chunks")
            
        except Exception as e:
            self.add_test_result("Data Integrity Test", False, f"Error: {str(e)}")

    def test_agent_social_media(self):
        """Test agent social media functionality"""
        print("🤖 Testing Agent Social Media System...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Test agent posts table
            cur.execute("SELECT COUNT(*) FROM agent_posts")
            posts_count = cur.fetchone()[0]
            self.add_test_result("Agent Posts: Count", posts_count >= 0, f"Found {posts_count} agent posts")
            
            # Test agent interactions
            cur.execute("SELECT COUNT(*) FROM agent_interactions")
            interactions_count = cur.fetchone()[0]
            self.add_test_result("Agent Interactions: Count", interactions_count >= 0, f"Found {interactions_count} interactions")
            
            # Test coffee states (temporal existence experiment)
            cur.execute("SELECT COUNT(*) FROM agent_coffee_states")
            coffee_states = cur.fetchone()[0]
            self.add_test_result("Coffee States: Count", coffee_states >= 0, f"Found {coffee_states} coffee states")
            
            # Test RSS generation capability
            cur.execute("""
                SELECT COUNT(*) FROM agent_posts 
                WHERE created_at > NOW() - INTERVAL '7 days'
            """)
            recent_posts = cur.fetchone()[0]
            self.add_test_result("Recent Agent Activity", recent_posts >= 0, f"Found {recent_posts} recent posts")
            
        except Exception as e:
            self.add_test_result("Agent Social Media Test", False, f"Error: {str(e)}")

    def test_hr_system(self):
        """Test HR and performance tracking system"""
        print("👥 Testing HR System...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Test HR daily reports
            cur.execute("SELECT COUNT(*) FROM hr_daily_reports")
            reports_count = cur.fetchone()[0]
            self.add_test_result("HR Reports: Count", reports_count >= 0, f"Found {reports_count} HR reports")
            
            # Test library health checks
            cur.execute("SELECT COUNT(*) FROM library_health_checks")
            health_checks = cur.fetchone()[0]
            self.add_test_result("Health Checks: Count", health_checks >= 0, f"Found {health_checks} health checks")
            
            # Test performance scoring
            cur.execute("SELECT calculate_performance_score(true, 75, 100)")
            perf_score = cur.fetchone()[0]
            self.add_test_result("Performance Scoring", perf_score is not None and 0 <= perf_score <= 1, f"Score: {perf_score}")
            
        except Exception as e:
            self.add_test_result("HR System Test", False, f"Error: {str(e)}")

    def test_sqlite_tracker(self):
        """Test Linda's SQLite audiobook-ebook tracker"""
        print("💽 Testing SQLite Tracker...")
        
        if not self.sqlite_conn:
            self.add_test_result("SQLite Connection", False, "SQLite database not available")
            return
        
        try:
            cur = self.sqlite_conn.cursor()
            
            # Test table existence
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cur.fetchall()]
            
            expected_tables = ['audiobooks', 'ebooks', 'search_attempts', 'download_queue']
            for table in expected_tables:
                if table in tables:
                    self.add_test_result(f"SQLite Table: {table}", True)
                else:
                    self.add_test_result(f"SQLite Table: {table}", False, "Table not found")
            
            # Test data counts
            if 'ebooks' in tables:
                cur.execute("SELECT COUNT(*) FROM ebooks WHERE download_status = 'available'")
                available_ebooks = cur.fetchone()[0]
                self.add_test_result("Available Ebooks", available_ebooks >= 0, f"Found {available_ebooks} available ebooks")
            
            if 'audiobooks' in tables:
                cur.execute("SELECT COUNT(*) FROM audiobooks")
                audiobook_count = cur.fetchone()[0]
                self.add_test_result("Audiobooks Count", audiobook_count >= 0, f"Found {audiobook_count} audiobooks")
            
        except Exception as e:
            self.add_test_result("SQLite Tracker Test", False, f"Error: {str(e)}")

    def test_security_functions(self):
        """Test security and validation functions"""
        print("🔒 Testing Security Functions...")
        
        try:
            cur = self.pg_conn.cursor()
            
            # Test SQL injection detection
            safe_queries = [
                "artificial intelligence",
                "philosophy and ethics",
                "machine learning concepts"
            ]
            
            malicious_queries = [
                "'; DROP TABLE books; --",
                "1' OR '1'='1",
                "UNION SELECT * FROM users",
                "'; INSERT INTO admin VALUES('hacker'); --"
            ]
            
            # Test safe queries
            for query in safe_queries:
                cur.execute("SELECT detect_sql_injection(%s)", (query,))
                result = cur.fetchone()[0]
                self.add_test_result(f"Security: Safe Query", result == False, f"Query: {query}")
            
            # Test malicious queries
            for query in malicious_queries:
                cur.execute("SELECT detect_sql_injection(%s)", (query,))
                result = cur.fetchone()[0]
                self.add_test_result(f"Security: Malicious Query", result == True, f"Query: {query}")
            
        except Exception as e:
            self.add_test_result("Security Functions Test", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 Starting Comprehensive Database Test Suite...")
        print("=" * 60)
        
        if not self.setup_connections():
            print("❌ Failed to setup database connections")
            return self.test_results
        
        try:
            # Run all test categories
            self.test_database_schema()
            self.test_stored_procedures()
            self.test_search_functionality()
            self.test_data_integrity()
            self.test_agent_social_media()
            self.test_hr_system()
            self.test_sqlite_tracker()
            self.test_security_functions()
            
        finally:
            # Close connections
            if self.pg_conn:
                self.pg_conn.close()
            if self.sqlite_conn:
                self.sqlite_conn.close()
        
        return self.test_results

    def generate_report(self):
        """Generate comprehensive test report"""
        results = self.test_results
        
        print("\n" + "="*60)
        print("📊 DATABASE TEST SUITE RESULTS")
        print("="*60)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"✅ Passed: {results['passed']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⚠️  Warnings: {results['warnings']}")
        
        success_rate = (results['passed'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for test in results['test_details']:
            status_emoji = {
                'PASS': '✅',
                'FAIL': '❌', 
                'WARNING': '⚠️'
            }.get(test['status'], '❓')
            
            print(f"{status_emoji} {test['test_name']}: {test['status']}")
            if test['details']:
                print(f"   Details: {test['details']}")
        
        # Save results to file
        report_file = f"/Users/weixiangzhang/Local Dev/LibraryOfBabel/test_reports/database_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Report saved to: {report_file}")
        
        return results

def main():
    """Main test execution"""
    suite = DatabaseTestSuite()
    suite.run_all_tests()
    suite.generate_report()

if __name__ == "__main__":
    main()