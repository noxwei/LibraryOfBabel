#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE API QA TEST SUITE - LibraryOfBabel
==================================================

Full endpoint validation following QA team standards.
Tests both v2 (port 5562) and v3 (port 5563) APIs.

Author: QA Team + API Agent
"""

import requests
import json
import time
from datetime import datetime
import sys

# API Configuration
API_KEY = "babel_secure_8a52a0ad3a1fe3bf3ade37d04deef0054d8f58035a0e9d4760a9a08548d8cebf"
V2_BASE = "https://api.ashortstayinhell.com:5562"
V3_BASE = "https://api.ashortstayinhell.com:5563/api/v3"

class APIQATester:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'v2_status': 'unknown',
            'v3_status': 'unknown',
            'detailed_results': []
        }
    
    def test_endpoint(self, name, url, expected_status=200, requires_auth=True):
        """Test a single endpoint"""
        self.results['tests_run'] += 1
        
        try:
            if requires_auth:
                url += f"{'&' if '?' in url else '?'}api_key={API_KEY}"
            
            start_time = time.time()
            response = requests.get(url, verify=False, timeout=10)
            response_time = round((time.time() - start_time) * 1000, 2)
            
            success = response.status_code == expected_status
            
            result = {
                'test': name,
                'url': url.replace(API_KEY, 'API_KEY_HIDDEN'),
                'expected_status': expected_status,
                'actual_status': response.status_code,
                'response_time_ms': response_time,
                'success': success,
                'error': None if success else f"Expected {expected_status}, got {response.status_code}"
            }
            
            if success:
                self.results['tests_passed'] += 1
                print(f"✅ {name}: PASS ({response_time}ms)")
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'results' in data:
                            result['result_count'] = len(data['results'])
                        elif 'status' in data:
                            result['api_status'] = data['status']
                    except:
                        pass
            else:
                self.results['tests_failed'] += 1
                print(f"❌ {name}: FAIL - {result['error']}")
                try:
                    result['response_body'] = response.text[:200]
                except:
                    pass
            
            self.results['detailed_results'].append(result)
            return success
            
        except Exception as e:
            self.results['tests_failed'] += 1
            result = {
                'test': name,
                'url': url.replace(API_KEY, 'API_KEY_HIDDEN'),
                'success': False,
                'error': str(e),
                'exception': True
            }
            self.results['detailed_results'].append(result)
            print(f"❌ {name}: FAIL - Exception: {e}")
            return False
    
    def run_v2_tests(self):
        """Test v2 API endpoints"""
        print("\n🧪 TESTING v2 API (port 5562)")
        print("=" * 40)
        
        # Health check (no auth)
        health_ok = self.test_endpoint("v2_health", f"{V2_BASE}/health", requires_auth=False)
        
        if health_ok:
            self.results['v2_status'] = 'healthy'
            
            # Core endpoints
            self.test_endpoint("v2_books_list", f"{V2_BASE}/books?page=1&page_size=5")
            self.test_endpoint("v2_book_details", f"{V2_BASE}/books/1373")
            self.test_endpoint("v2_book_chunks", f"{V2_BASE}/books/1373/chunks?page=1&page_size=3")
            self.test_endpoint("v2_chunk_detail", f"{V2_BASE}/chunks/1373_chapter_2?chunk_level=medium")
            
            # Search endpoints
            self.test_endpoint("v2_search_global", f"{V2_BASE}/search?q=Foucault&page=1&page_size=3")
            self.test_endpoint("v2_search_semantic", f"{V2_BASE}/search?q=cybernetic&type=semantic&page=1&page_size=3")
            
            # NEW: In-book search (our fix!)
            self.test_endpoint("v2_inbook_search", f"{V2_BASE}/books/1099/search?q=discourse&page=1&page_size=3")
        else:
            self.results['v2_status'] = 'down'
    
    def run_v3_tests(self):
        """Test v3 API endpoints"""
        print("\n🧪 TESTING v3 API (port 5563)")
        print("=" * 40)
        
        # Health check (no auth)
        health_ok = self.test_endpoint("v3_health", f"{V3_BASE}/health", requires_auth=False)
        
        if health_ok:
            # Try authenticated endpoints
            books_ok = self.test_endpoint("v3_books_list", f"{V3_BASE}/books?page=1&page_size=5")
            
            if books_ok:
                self.results['v3_status'] = 'healthy'
                self.test_endpoint("v3_book_details", f"{V3_BASE}/books/1373")
                self.test_endpoint("v3_search_global", f"{V3_BASE}/search?q=Foucault&limit=3")
                self.test_endpoint("v3_inbook_search", f"{V3_BASE}/books/1099/search?q=discourse&limit=3")
            else:
                self.results['v3_status'] = 'auth_issues'
        else:
            self.results['v3_status'] = 'down'
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 STARTING COMPREHENSIVE API QA TESTS")
        print("=" * 50)
        
        self.run_v2_tests()
        self.run_v3_tests()
        
        # Calculate success rate
        success_rate = round((self.results['tests_passed'] / self.results['tests_run']) * 100, 1) if self.results['tests_run'] > 0 else 0
        
        print(f"\n📋 QA TEST SUMMARY:")
        print(f"   Tests run: {self.results['tests_run']}")
        print(f"   Passed: {self.results['tests_passed']}")
        print(f"   Failed: {self.results['tests_failed']}")
        print(f"   Success rate: {success_rate}%")
        print(f"   v2 API Status: {self.results['v2_status']}")
        print(f"   v3 API Status: {self.results['v3_status']}")
        
        if success_rate >= 80:
            print("✅ API ENDPOINTS: HEALTHY")
        elif success_rate >= 60:
            print("⚠️ API ENDPOINTS: DEGRADED")
        else:
            print("❌ API ENDPOINTS: FAILING")
        
        # Save results
        report_file = f"agents/qa/reports/api_qa_test_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        self.results['success_rate'] = success_rate
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📋 QA Results saved: {report_file}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = APIQATester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)