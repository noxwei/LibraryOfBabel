#!/usr/bin/env python3
"""
QA Agent: Production Testing Suite for LibraryOfBabel APIs
Testing Phase 1-2.5 APIs with pgvector + Redis optimizations
============================================================

Test Coverage:
- Phase 1: Confidence-Weighted Similarity Search
- Phase 2: Genre-Aware Discovery 
- Phase 2.5: Hybrid Confidence + Genre Search
- Performance benchmarks with Redis caching
- Error handling and edge cases
"""

import requests
import time
import json
import redis
import hashlib
from typing import Dict, List, Optional
import sys
import concurrent.futures

class ProductionAPITester:
    """QA Agent: Comprehensive API testing with performance monitoring"""
    
    def __init__(self):
        self.base_urls = {
            'phase1': 'http://localhost:5001',
            'phase2': 'http://localhost:5002', 
            'phase2_5': 'http://localhost:5003'
        }
        
        # Connect to Redis for cache testing
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_available = self.redis_client.ping()
        except:
            self.redis_available = False
            
        self.test_results = []
        
    def log_test(self, test_name: str, status: str, details: Dict):
        """Log test results with performance metrics"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': time.time(),
            'details': details
        }
        self.test_results.append(result)
        
        # Color coding for terminal output
        color = '\033[92m' if status == 'PASS' else '\033[91m' if status == 'FAIL' else '\033[93m'
        reset = '\033[0m'
        
        print(f"{color}[{status}]{reset} {test_name}")
        if details.get('response_time'):
            print(f"  ⏱️  Response Time: {details['response_time']:.3f}s")
        if details.get('error'):
            print(f"  ❌ Error: {details['error']}")
        print()
    
    def test_api_health_checks(self):
        """Test health endpoints for all APIs"""
        health_endpoints = {
            'Phase 1': f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted/health",
            'Phase 2': f"{self.base_urls['phase2']}/api/v2/discover/genre/health", 
            'Phase 2.5': f"{self.base_urls['phase2_5']}/api/v2.5/search/hybrid/health"
        }
        
        for api_name, url in health_endpoints.items():
            start_time = time.time()
            try:
                response = requests.get(url, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(
                        f"Health Check: {api_name}",
                        'PASS',
                        {
                            'response_time': response_time,
                            'status': data.get('status'),
                            'features': data.get('features', [])
                        }
                    )
                else:
                    self.log_test(
                        f"Health Check: {api_name}",
                        'FAIL', 
                        {
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'error': f"HTTP {response.status_code}"
                        }
                    )
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(
                    f"Health Check: {api_name}",
                    'FAIL',
                    {
                        'response_time': response_time,
                        'error': str(e)
                    }
                )
    
    def test_phase1_confidence_search(self):
        """Test Phase 1: Confidence-Weighted Similarity Search"""
        test_queries = [
            {
                'query': 'artificial intelligence philosophy',
                'confidence_weight': 0.25,
                'limit': 10
            },
            {
                'query': 'love and relationships', 
                'confidence_weight': 0.5,
                'limit': 5
            },
            {
                'query': 'quantum physics',
                'confidence_weight': 0.1, 
                'limit': 20
            }
        ]
        
        url = f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted"
        
        for i, test_query in enumerate(test_queries):
            start_time = time.time()
            try:
                response = requests.post(url, json=test_query, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    results_count = len(data.get('results', []))
                    
                    # Validate response structure
                    required_fields = ['status', 'results', 'search_metadata']
                    missing_fields = [f for f in required_fields if f not in data]
                    
                    if not missing_fields and results_count > 0:
                        self.log_test(
                            f"Phase 1 Search Test {i+1}",
                            'PASS',
                            {
                                'response_time': response_time,
                                'results_count': results_count,
                                'confidence_weight': test_query['confidence_weight'],
                                'reliability_boost': data['search_metadata'].get('reliability_boost')
                            }
                        )
                    else:
                        self.log_test(
                            f"Phase 1 Search Test {i+1}",
                            'FAIL',
                            {
                                'response_time': response_time,
                                'error': f"Missing fields: {missing_fields}" if missing_fields else "No results returned"
                            }
                        )
                else:
                    self.log_test(
                        f"Phase 1 Search Test {i+1}",
                        'FAIL',
                        {
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'error': response.text
                        }
                    )
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(
                    f"Phase 1 Search Test {i+1}",
                    'FAIL',
                    {
                        'response_time': response_time,
                        'error': str(e)
                    }
                )
    
    def test_phase2_genre_discovery(self):
        """Test Phase 2: Genre-Aware Discovery"""
        test_cases = [
            {
                'preferred_genres': ['Philosophy', 'Science Fiction'],
                'discovery_mode': 'balanced',
                'limit': 15
            },
            {
                'preferred_genres': ['Romance', 'Historical Fiction'],
                'discovery_mode': 'similar',
                'include_subgenres': True,
                'limit': 10
            },
            {
                'preferred_genres': ['Philosophy'],
                'discovery_mode': 'diverse',
                'exclude_genres': ['Romance'],
                'limit': 20
            }
        ]
        
        url = f"{self.base_urls['phase2']}/api/v2/discover/genre"
        
        for i, test_case in enumerate(test_cases):
            start_time = time.time()
            try:
                response = requests.post(url, json=test_case, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    results_count = data['discovery_metadata']['total_results']
                    
                    # Validate genre-specific features
                    has_genre_hierarchy = 'genre_hierarchy' in data
                    has_recommendations = 'recommendations' in data
                    
                    if results_count > 0 and has_genre_hierarchy and has_recommendations:
                        self.log_test(
                            f"Phase 2 Genre Discovery Test {i+1}",
                            'PASS',
                            {
                                'response_time': response_time,
                                'results_count': results_count,
                                'discovery_mode': test_case['discovery_mode'],
                                'genres_tested': len(test_case['preferred_genres'])
                            }
                        )
                    else:
                        self.log_test(
                            f"Phase 2 Genre Discovery Test {i+1}",
                            'FAIL',
                            {
                                'response_time': response_time,
                                'error': f"Results: {results_count}, Hierarchy: {has_genre_hierarchy}, Recommendations: {has_recommendations}"
                            }
                        )
                else:
                    self.log_test(
                        f"Phase 2 Genre Discovery Test {i+1}",
                        'FAIL',
                        {
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'error': response.text[:200]
                        }
                    )
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(
                    f"Phase 2 Genre Discovery Test {i+1}",
                    'FAIL',
                    {
                        'response_time': response_time,
                        'error': str(e)
                    }
                )
    
    def test_phase2_5_hybrid_search(self):
        """Test Phase 2.5: Hybrid Confidence + Genre Search"""
        test_cases = [
            {
                'query': 'existential philosophy meaning of life',
                'preferred_genres': ['Philosophy', 'Existentialism'],
                'confidence_weight': 0.25,
                'discovery_mode': 'balanced',
                'limit': 15
            },
            {
                'query': 'space exploration future technology',
                'preferred_genres': ['Science Fiction'],
                'confidence_weight': 0.3,
                'discovery_mode': 'similar',
                'model_filter': 'bge-m3',
                'limit': 10
            }
        ]
        
        url = f"{self.base_urls['phase2_5']}/api/v2.5/search/hybrid"
        
        for i, test_case in enumerate(test_cases):
            start_time = time.time()
            try:
                response = requests.post(url, json=test_case, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    results_count = data.get('results_count', 0)
                    
                    # Validate hybrid features
                    has_hybrid_scoring = any('hybrid_score' in r for r in data.get('results', []))
                    has_confidence_boost = 'confidence_weight' in data.get('search_metadata', {})
                    has_performance_metrics = 'performance_metrics' in data
                    
                    if results_count > 0 and has_hybrid_scoring and has_confidence_boost:
                        self.log_test(
                            f"Phase 2.5 Hybrid Search Test {i+1}",
                            'PASS',
                            {
                                'response_time': response_time,
                                'results_count': results_count,
                                'hybrid_features': has_performance_metrics,
                                'confidence_weight': test_case['confidence_weight']
                            }
                        )
                    else:
                        self.log_test(
                            f"Phase 2.5 Hybrid Search Test {i+1}",
                            'FAIL',
                            {
                                'response_time': response_time,
                                'error': f"Results: {results_count}, Hybrid: {has_hybrid_scoring}, Confidence: {has_confidence_boost}"
                            }
                        )
                else:
                    self.log_test(
                        f"Phase 2.5 Hybrid Search Test {i+1}",
                        'FAIL',
                        {
                            'response_time': response_time,
                            'status_code': response.status_code,
                            'error': response.text[:200]
                        }
                    )
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(
                    f"Phase 2.5 Hybrid Search Test {i+1}",
                    'FAIL',
                    {
                        'response_time': response_time,
                        'error': str(e)
                    }
                )
    
    def test_redis_caching_performance(self):
        """Test Redis caching impact on API performance"""
        if not self.redis_available:
            self.log_test(
                "Redis Caching Test",
                'SKIP',
                {'error': 'Redis not available'}
            )
            return
        
        # Test query that should benefit from caching
        test_query = {
            'query': 'artificial intelligence',
            'confidence_weight': 0.25,
            'limit': 10
        }
        
        url = f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted"
        
        # First request (cache miss)
        start_time = time.time()
        try:
            response1 = requests.post(url, json=test_query, timeout=30)
            time1 = time.time() - start_time
            
            # Second request (potential cache hit)
            start_time = time.time()
            response2 = requests.post(url, json=test_query, timeout=30)
            time2 = time.time() - start_time
            
            if response1.status_code == 200 and response2.status_code == 200:
                cache_improvement = ((time1 - time2) / time1) * 100 if time1 > time2 else 0
                
                self.log_test(
                    "Redis Caching Performance",
                    'PASS',
                    {
                        'first_request_time': time1,
                        'second_request_time': time2,
                        'cache_improvement_percent': round(cache_improvement, 2),
                        'redis_keys': self.redis_client.dbsize()
                    }
                )
            else:
                self.log_test(
                    "Redis Caching Performance",
                    'FAIL',
                    {
                        'error': f"HTTP errors: {response1.status_code}, {response2.status_code}"
                    }
                )
        except Exception as e:
            self.log_test(
                "Redis Caching Performance",
                'FAIL',
                {'error': str(e)}
            )
    
    def test_concurrent_load(self):
        """Test concurrent API load handling"""
        def make_request(query_id):
            test_query = {
                'query': f'test query {query_id}',
                'confidence_weight': 0.25,
                'limit': 5
            }
            url = f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted"
            
            start_time = time.time()
            try:
                response = requests.post(url, json=test_query, timeout=30)
                response_time = time.time() - start_time
                return {
                    'query_id': query_id,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                response_time = time.time() - start_time
                return {
                    'query_id': query_id,
                    'status_code': None,
                    'response_time': response_time,
                    'success': False,
                    'error': str(e)
                }
        
        # Test with 5 concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        
        if successful_requests >= 4:  # Allow 1 failure out of 5
            self.log_test(
                "Concurrent Load Test",
                'PASS',
                {
                    'total_time': total_time,
                    'successful_requests': f"{successful_requests}/5",
                    'avg_response_time': avg_response_time,
                    'concurrent_users': 5
                }
            )
        else:
            self.log_test(
                "Concurrent Load Test", 
                'FAIL',
                {
                    'total_time': total_time,
                    'successful_requests': f"{successful_requests}/5",
                    'avg_response_time': avg_response_time,
                    'errors': [r.get('error') for r in results if not r['success']]
                }
            )
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed_tests = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        skipped_tests = sum(1 for r in self.test_results if r['status'] == 'SKIP')
        
        avg_response_time = sum(
            r['details'].get('response_time', 0) 
            for r in self.test_results 
            if 'response_time' in r['details']
        ) / max(1, sum(1 for r in self.test_results if 'response_time' in r['details']))
        
        report = f"""
🧪 QA AGENT: PRODUCTION API TEST REPORT
=====================================
📊 Test Summary:
   • Total Tests: {total_tests}
   • Passed: {passed_tests} ✅
   • Failed: {failed_tests} ❌ 
   • Skipped: {skipped_tests} ⏭️
   • Success Rate: {(passed_tests/total_tests)*100:.1f}%

⚡ Performance Metrics:
   • Average Response Time: {avg_response_time:.3f}s
   • Redis Available: {'Yes' if self.redis_available else 'No'}
   • APIs Tested: Phase 1, 2, 2.5

🎯 System Status:
   • Phase 1 (Confidence Search): {'✅ OPERATIONAL' if any(r['test_name'].startswith('Phase 1') and r['status'] == 'PASS' for r in self.test_results) else '❌ ISSUES'}
   • Phase 2 (Genre Discovery): {'✅ OPERATIONAL' if any(r['test_name'].startswith('Phase 2 Genre') and r['status'] == 'PASS' for r in self.test_results) else '❌ ISSUES'}
   • Phase 2.5 (Hybrid Search): {'✅ OPERATIONAL' if any(r['test_name'].startswith('Phase 2.5') and r['status'] == 'PASS' for r in self.test_results) else '❌ ISSUES'}
   • Redis Caching: {'✅ OPERATIONAL' if self.redis_available else '❌ NOT CONFIGURED'}

🚀 Production Readiness: {'READY' if passed_tests >= total_tests * 0.8 else 'NEEDS ATTENTION'}
"""
        print(report)
        
        # Save detailed results
        with open('/Users/weixiangzhang/Local Dev/LibraryOfBabel/tests/production_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'skipped': skipped_tests,
                    'success_rate': (passed_tests/total_tests)*100,
                    'avg_response_time': avg_response_time
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        return passed_tests >= total_tests * 0.8
    
    def run_full_test_suite(self):
        """Execute complete production test suite"""
        print("🧪 QA AGENT: Starting Production API Test Suite")
        print("=" * 50)
        
        # Execute all test categories
        self.test_api_health_checks()
        self.test_phase1_confidence_search()
        self.test_phase2_genre_discovery() 
        self.test_phase2_5_hybrid_search()
        self.test_redis_caching_performance()
        self.test_concurrent_load()
        
        # Generate final report
        return self.generate_test_report()

if __name__ == '__main__':
    tester = ProductionAPITester()
    success = tester.run_full_test_suite()
    sys.exit(0 if success else 1)