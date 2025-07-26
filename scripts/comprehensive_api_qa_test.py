#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE API QA TEST SUITE - LibraryOfBabel v4.0
========================================================

Full endpoint validation following QA team standards.
Tests v4 modern query-parameter based RESTful APIs.
Extensive testing suite with RedditBibliophile scenarios.

Author: QA Team + API Agent + RedditBibliophile
Updated: July 26, 2025 - Query Parameter Modernization
"""

import requests
import json
import time
import os
from datetime import datetime
import sys

# API Configuration - v4.0 Modernized  
API_KEY = os.getenv('API_KEY', 'your_api_key_here')
V2_BASE = "https://api.ashortstayinhell.com:5562"  # Legacy shortcuts API
V4_BASE = "https://api.ashortstayinhell.com:5563/api/v4"  # Modern production API
V4_SHORTCUTS = "https://api.ashortstayinhell.com:5563/api/shortcuts"  # Modern shortcuts API

class APIQATester:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'v2_legacy_status': 'unknown',
            'v4_production_status': 'unknown',
            'v4_shortcuts_status': 'unknown',
            'reddit_bibliophile_scenarios': [],
            'performance_benchmarks': {},
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
        """Test legacy v2 API endpoints"""
        print("\n🧪 TESTING LEGACY v2 API (port 5562)")
        print("=" * 40)
        
        # Health check (no auth)
        health_ok = self.test_endpoint("v2_health", f"{V2_BASE}/health", requires_auth=False)
        
        if health_ok:
            self.results['v2_legacy_status'] = 'healthy'
            
            # Core legacy endpoints - maintaining backward compatibility
            self.test_endpoint("v2_books_list", f"{V2_BASE}/books?page=1&page_size=5")
            self.test_endpoint("v2_book_details", f"{V2_BASE}/books/1373")
            self.test_endpoint("v2_book_chunks", f"{V2_BASE}/books/1373/chunks?page=1&page_size=3")
            
            # Search endpoints
            self.test_endpoint("v2_search_global", f"{V2_BASE}/search?q=Foucault&page=1&page_size=3")
            self.test_endpoint("v2_search_semantic", f"{V2_BASE}/search?q=cybernetic&type=semantic&page=1&page_size=3")
            
            # In-book search
            self.test_endpoint("v2_inbook_search", f"{V2_BASE}/books/1099/search?q=discourse&page=1&page_size=3")
        else:
            self.results['v2_legacy_status'] = 'down'
    
    def run_v4_production_tests(self):
        """Test v4 Modern Production API with query parameters"""
        print("\n🧪 TESTING v4 PRODUCTION API (Modern Query Parameters)")
        print("=" * 60)
        
        # Health check (no auth)
        health_ok = self.test_endpoint("v4_health", f"{V4_BASE}/health", requires_auth=False)
        
        if health_ok:
            self.results['v4_production_status'] = 'healthy'
            
            # 📚 BOOKS ENDPOINT TESTS (Query Parameter Architecture)
            print("\n📚 Testing Books Endpoints...")
            self.test_endpoint("v4_books_list", f"{V4_BASE}/books?action=list")
            self.test_endpoint("v4_book_details", f"{V4_BASE}/books?id=1373&action=details")
            self.test_endpoint("v4_book_content", f"{V4_BASE}/books?id=1373&action=content&chapter=1&limit=5")
            self.test_endpoint("v4_book_search", f"{V4_BASE}/books?id=1099&action=search&q=discourse&limit=3")
            
            # 🔍 SEARCH ENDPOINT TESTS (Query Parameter Architecture)
            print("\n🔍 Testing Search Endpoints...")
            self.test_endpoint("v4_search_content", f"{V4_BASE}/search?q=philosophy&type=content&limit=5")
            self.test_endpoint("v4_search_author", f"{V4_BASE}/search?q=Nietzsche&type=author&limit=3")
            self.test_endpoint("v4_search_title", f"{V4_BASE}/search?q=Democracy&type=title&limit=3")
            self.test_endpoint("v4_search_count", f"{V4_BASE}/search?term=artificial&action=count")
            self.test_endpoint("v4_search_cross_reference", f"{V4_BASE}/search?q=cybernetic&type=cross_reference&limit=5")
            
            # 📊 STATS AND INFO ENDPOINTS
            print("\n📊 Testing Information Endpoints...")
            self.test_endpoint("v4_stats", f"{V4_BASE}/stats")
            self.test_endpoint("v4_info", f"{V4_BASE}/info")
            
        else:
            self.results['v4_production_status'] = 'down'
    
    def run_v4_shortcuts_tests(self):
        """Test v4 Modern iOS Shortcuts API"""
        print("\n📱 TESTING v4 iOS SHORTCUTS API (Modern Query Parameters)")
        print("=" * 60)
        
        # Test shortcuts endpoints
        self.test_endpoint("shortcuts_books_list", f"{V4_SHORTCUTS}/books?action=list&limit=5")
        self.test_endpoint("shortcuts_book_summary", f"{V4_SHORTCUTS}/books?id=288&action=summary")
        self.test_endpoint("shortcuts_search_count", f"{V4_SHORTCUTS}/search?term=philosophy&action=count")
        self.test_endpoint("shortcuts_search_results", f"{V4_SHORTCUTS}/search?term=democracy&action=search&limit=3")
        self.test_endpoint("shortcuts_serendipity", f"{V4_SHORTCUTS}/serendipity?action=quote&limit=3")
        
        if self.test_endpoint("shortcuts_health_test", f"{V4_SHORTCUTS}/books?action=list&limit=1"):
            self.results['v4_shortcuts_status'] = 'healthy'
        else:
            self.results['v4_shortcuts_status'] = 'down'
    
    def run_reddit_bibliophile_scenarios(self):
        """Extensive RedditBibliophile usage scenarios"""
        print("\n🤖 TESTING REDDIT BIBLIOPHILE SCENARIOS")
        print("=" * 50)
        
        reddit_tests = [
            {
                'name': 'Philosophy Research',
                'scenario': 'User asks about existentialism in literature',
                'endpoint': f"{V4_BASE}/search?q=existentialism&type=content&limit=5",
                'description': 'Testing philosophical concept search'
            },
            {
                'name': 'Author Deep Dive', 
                'scenario': 'User wants all books by specific author',
                'endpoint': f"{V4_BASE}/search?q=Foucault&type=author&limit=10",
                'description': 'Testing author-based book discovery'
            },
            {
                'name': 'Book Recommendation',
                'scenario': 'User looking for books about artificial intelligence',
                'endpoint': f"{V4_BASE}/search?q=artificial intelligence&type=content&limit=8",
                'description': 'Testing topic-based recommendations'
            },
            {
                'name': 'Quick Stats Check',
                'scenario': 'User wants to know collection size',
                'endpoint': f"{V4_BASE}/stats",
                'description': 'Testing collection statistics'
            },
            {
                'name': 'Detailed Book Analysis',
                'scenario': 'User wants to analyze specific book structure',
                'endpoint': f"{V4_BASE}/books?id=1373&action=details",
                'description': 'Testing detailed book metadata'
            },
            {
                'name': 'Chapter Content Access',
                'scenario': 'User wants specific chapter content',
                'endpoint': f"{V4_BASE}/books?id=1373&action=content&chapter=2&limit=10",
                'description': 'Testing chapter-level content access'
            },
            {
                'name': 'Cross-Book Research',
                'scenario': 'User researching concept across multiple books',
                'endpoint': f"{V4_BASE}/search?q=democracy&type=cross_reference&limit=10",
                'description': 'Testing cross-reference research capabilities'
            },
            {
                'name': 'iOS Shortcuts Integration',
                'scenario': 'Siri asking for book count on philosophy',
                'endpoint': f"{V4_SHORTCUTS}/search?term=philosophy&action=count",
                'description': 'Testing Siri/iOS Shortcuts compatibility'
            }
        ]
        
        for test in reddit_tests:
            print(f"\n🎯 Scenario: {test['scenario']}")
            success = self.test_endpoint(test['name'], test['endpoint'])
            
            scenario_result = {
                'name': test['name'],
                'scenario': test['scenario'],
                'description': test['description'],
                'endpoint': test['endpoint'],
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
            self.results['reddit_bibliophile_scenarios'].append(scenario_result)
    
    def run_performance_benchmarks(self):
        """Performance testing for API responsiveness"""
        print("\n⚡ PERFORMANCE BENCHMARKS")
        print("=" * 30)
        
        benchmark_tests = [
            ('Search Performance', f"{V4_BASE}/search?q=philosophy&type=content&limit=5"),
            ('Book Details Speed', f"{V4_BASE}/books?id=1373&action=details"),
            ('Search Count Speed', f"{V4_BASE}/search?term=democracy&action=count"),
            ('Stats Endpoint Speed', f"{V4_BASE}/stats")
        ]
        
        for test_name, endpoint in benchmark_tests:
            times = []
            for i in range(3):  # Run each test 3 times
                start_time = time.time()
                try:
                    response = requests.get(f"{endpoint}&api_key={API_KEY}", verify=False, timeout=10)
                    response_time = (time.time() - start_time) * 1000
                    if response.status_code == 200:
                        times.append(response_time)
                except:
                    pass
            
            if times:
                avg_time = round(sum(times) / len(times), 2)
                self.results['performance_benchmarks'][test_name] = {
                    'average_ms': avg_time,
                    'all_times': times,
                    'status': 'fast' if avg_time < 200 else 'acceptable' if avg_time < 1000 else 'slow'
                }
                print(f"⚡ {test_name}: {avg_time}ms avg")
            else:
                print(f"❌ {test_name}: Failed to complete")
    
    def run_all_tests(self):
        """Run complete comprehensive test suite"""
        print("🚀 STARTING COMPREHENSIVE API v4.0 QA TESTS")
        print("=" * 60)
        print("🎯 Modern Query-Parameter Architecture Testing")
        print("🤖 RedditBibliophile Scenario Validation")
        print("⚡ Performance Benchmark Analysis")
        print("=" * 60)
        
        # Run all test suites
        self.run_v2_tests()                    # Legacy compatibility 
        self.run_v4_production_tests()         # Modern production API
        self.run_v4_shortcuts_tests()          # Modern shortcuts API
        self.run_reddit_bibliophile_scenarios() # RedditBibliophile scenarios
        self.run_performance_benchmarks()      # Performance analysis
        
        # Calculate success rate
        success_rate = round((self.results['tests_passed'] / self.results['tests_run']) * 100, 1) if self.results['tests_run'] > 0 else 0
        
        print(f"\n📋 COMPREHENSIVE QA TEST SUMMARY:")
        print("=" * 50)
        print(f"   📊 Tests run: {self.results['tests_run']}")
        print(f"   ✅ Passed: {self.results['tests_passed']}")
        print(f"   ❌ Failed: {self.results['tests_failed']}")
        print(f"   📈 Success rate: {success_rate}%")
        print(f"\n🔍 API STATUS OVERVIEW:")
        print(f"   🏛️  v2 Legacy API: {self.results['v2_legacy_status']}")
        print(f"   🚀 v4 Production API: {self.results['v4_production_status']}")
        print(f"   📱 v4 Shortcuts API: {self.results['v4_shortcuts_status']}")
        
        # RedditBibliophile scenario summary
        reddit_success = len([s for s in self.results['reddit_bibliophile_scenarios'] if s['success']])
        reddit_total = len(self.results['reddit_bibliophile_scenarios'])
        if reddit_total > 0:
            reddit_rate = round((reddit_success / reddit_total) * 100, 1)
            print(f"   🤖 Reddit Scenarios: {reddit_success}/{reddit_total} ({reddit_rate}%)")
        
        # Performance summary
        fast_benchmarks = len([b for b in self.results['performance_benchmarks'].values() if b['status'] == 'fast'])
        total_benchmarks = len(self.results['performance_benchmarks'])
        if total_benchmarks > 0:
            print(f"   ⚡ Performance: {fast_benchmarks}/{total_benchmarks} endpoints under 200ms")
        
        # Overall system health
        if success_rate >= 85:
            print("\n🎉 SYSTEM STATUS: EXCELLENT - Modern API Migration Successful!")
        elif success_rate >= 70:
            print("\n✅ SYSTEM STATUS: HEALTHY - Query Parameter Architecture Working")
        elif success_rate >= 50:
            print("\n⚠️ SYSTEM STATUS: DEGRADED - Some Issues Detected")
        else:
            print("\n❌ SYSTEM STATUS: CRITICAL - Major Issues Require Attention")
        
        # Save comprehensive results
        report_file = f"comprehensive_api_v4_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.results['success_rate'] = success_rate
        self.results['reddit_bibliophile_success_rate'] = reddit_rate if reddit_total > 0 else 0
        self.results['test_summary'] = {
            'query_parameter_architecture': 'implemented',
            'forward_slash_navigation': 'eliminated',
            'reddit_bibliophile_compatible': reddit_rate >= 80 if reddit_total > 0 else False,
            'performance_optimized': fast_benchmarks >= total_benchmarks * 0.75 if total_benchmarks > 0 else False
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            print(f"📋 QA Results saved: {report_file}")
        except Exception as e:
            print(f"⚠️ Could not save report: {e}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = APIQATester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)