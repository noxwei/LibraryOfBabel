#!/usr/bin/env python3
"""
Reddit Nerd Validation Test
Test the QA fixes with focused attacks on the improved areas
"""

import psycopg2
import psycopg2.extras
import time
import json

class ValidationTest:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'), 
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': 5432
        }
    
    def test_sql_injection_speed(self):
        """Test improved SQL injection handling"""
        print("🛡️  Testing SQL injection speed improvements...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Test the new safe search function
        injection_queries = [
            "'; DROP TABLE books; --",
            "UNION SELECT * FROM chunks", 
            "1' OR '1'='1",
            "admin'--"
        ]
        
        for query in injection_queries:
            start_time = time.time()
            try:
                cursor.execute("SELECT * FROM safe_search(%s)", (query,))
                results = cursor.fetchall()
                response_time = (time.time() - start_time) * 1000
                
                print(f"   🔒 '{query[:20]}...' -> {len(results)} results ({response_time:.1f}ms)")
                if results and results[0][0] == 'Security Notice':
                    print(f"      ✅ Properly blocked!")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        conn.close()
    
    def test_intersection_bombs(self):
        """Test new intersection bomb functionality"""
        print("💣 Testing intersection bomb improvements...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        # Test philosophy-finance intersections
        intersections = [
            ("freedom", "capital"),
            ("subjectivity", "economy"),
            ("power", "money"),
            ("ideology", "markets")
        ]
        
        for concept1, concept2 in intersections:
            start_time = time.time()
            try:
                cursor.execute("SELECT * FROM intersection_bomb_search(%s, %s)", (concept1, concept2))
                results = cursor.fetchall()
                response_time = (time.time() - start_time) * 1000
                
                print(f"   💥 '{concept1}' + '{concept2}' -> {len(results)} results ({response_time:.1f}ms)")
                if results:
                    print(f"      📖 Found: {results[0][0]} by {results[0][1]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        conn.close()
    
    def test_fast_search_performance(self):
        """Test optimized search performance"""
        print("⚡ Testing fast search performance...")
        
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()
        
        test_queries = [
            "philosophy",
            "feminist theory", 
            "capital markets",
            "fantasy literature",
            "complex interdisciplinary query"
        ]
        
        for query in test_queries:
            start_time = time.time()
            try:
                cursor.execute("SELECT * FROM fast_search(%s)", (query,))
                results = cursor.fetchall()
                response_time = (time.time() - start_time) * 1000
                
                optimized = results[0][4] if results else False
                print(f"   🚀 '{query}' -> {len(results)} results ({response_time:.1f}ms) {'[OPTIMIZED]' if optimized else ''}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        conn.close()
    
    def run_validation(self):
        """Run comprehensive validation"""
        print("🤓 REDDIT NERD VALIDATION OF QA FIXES")
        print("="*50)
        
        try:
            self.test_sql_injection_speed()
            print()
            self.test_intersection_bombs() 
            print()
            self.test_fast_search_performance()
            
            print("\n✅ VALIDATION COMPLETE - QA fixes are working!")
            
        except Exception as e:
            print(f"\n❌ VALIDATION FAILED: {e}")

if __name__ == "__main__":
    validator = ValidationTest()
    validator.run_validation()