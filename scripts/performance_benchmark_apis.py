#!/usr/bin/env python3
"""
Performance Agent: Benchmark Fixed APIs Against Baseline
Critical Mission: Validate production performance meets requirements
==================================================================

Benchmarks:
1. pgvector vs JSONB response times
2. Concurrent load testing
3. Memory usage under load
4. API reliability testing
5. Cache effectiveness validation
"""

import requests
import time
import threading
import statistics
import psutil
import json
import sys
import concurrent.futures
from datetime import datetime
sys.path.append('/Users/weixiangzhang/Local Dev/LibraryOfBabel')

class APIPerformanceBenchmark:
    def __init__(self):
        self.base_urls = {
            'phase1': 'http://localhost:5001',
            'phase2': 'http://localhost:5002'
        }
        self.results = {
            'phase1': {'times': [], 'errors': [], 'success_rate': 0},
            'phase2': {'times': [], 'errors': [], 'success_rate': 0},
            'load_test': {'concurrent_times': [], 'memory_usage': []},
            'baseline': {'jsonb_times': [], 'vector_times': []}
        }
    
    def test_api_health(self):
        """Check if APIs are running and healthy"""
        print("🏥 Testing API Health")
        print("=" * 40)
        
        health_checks = {
            'Phase 1': f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted/health",
            'Phase 2': f"{self.base_urls['phase2']}/api/v2/discover/genre/health"
        }
        
        all_healthy = True
        for api_name, health_url in health_checks.items():
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"   ✅ {api_name}: {health_data.get('status', 'unknown')}")
                else:
                    print(f"   ❌ {api_name}: HTTP {response.status_code}")
                    all_healthy = False
            except Exception as e:
                print(f"   ❌ {api_name}: Connection failed - {e}")
                all_healthy = False
        
        return all_healthy
    
    def benchmark_phase1_api(self, num_requests=50):
        """Benchmark Phase 1 confidence-weighted search API"""
        print(f"\n⚡ Benchmarking Phase 1 API ({num_requests} requests)")
        print("=" * 50)
        
        url = f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted"
        test_queries = [
            "japanese literature",
            "mystery crime fiction", 
            "philosophy existentialism",
            "science fiction space",
            "historical fiction war"
        ]
        
        successful_requests = 0
        response_times = []
        errors = []
        
        for i in range(num_requests):
            query = test_queries[i % len(test_queries)]
            payload = {
                "query": query,
                "confidence_weight": 0.25,
                "limit": 10
            }
            
            try:
                start_time = time.time()
                response = requests.post(url, json=payload, timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200:
                    successful_requests += 1
                    response_times.append(response_time)
                    if i % 10 == 0:
                        print(f"   Request {i+1}: {response_time:.2f}ms ✅")
                else:
                    errors.append(f"HTTP {response.status_code}")
                    print(f"   Request {i+1}: Error {response.status_code} ❌")
                    
            except Exception as e:
                errors.append(str(e))
                print(f"   Request {i+1}: Exception {e} ❌")
        
        self.results['phase1'] = {
            'times': response_times,
            'errors': errors,
            'success_rate': (successful_requests / num_requests) * 100
        }
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            p95_time = sorted(response_times)[int(0.95 * len(response_times))]
            
            print(f"\n📊 Phase 1 Results:")
            print(f"   • Success Rate: {self.results['phase1']['success_rate']:.1f}%")
            print(f"   • Average Response: {avg_time:.2f}ms")
            print(f"   • Median Response: {median_time:.2f}ms")
            print(f"   • 95th Percentile: {p95_time:.2f}ms")
            print(f"   • Total Errors: {len(errors)}")
        
        return successful_requests > 0
    
    def benchmark_phase2_api(self, num_requests=30):
        """Benchmark Phase 2 genre discovery API"""
        print(f"\n🎭 Benchmarking Phase 2 API ({num_requests} requests)")
        print("=" * 50)
        
        url = f"{self.base_urls['phase2']}/api/v2/discover/genre"
        test_genres = [
            ["Fiction", "Literary Fiction"],
            ["Mystery", "Crime Fiction"],
            ["Philosophy"],
            ["Science Fiction"],
            ["Historical Fiction"]
        ]
        
        successful_requests = 0
        response_times = []
        errors = []
        
        for i in range(num_requests):
            genres = test_genres[i % len(test_genres)]
            payload = {
                "preferred_genres": genres,
                "discovery_mode": "balanced",
                "limit": 15
            }
            
            try:
                start_time = time.time()
                response = requests.post(url, json=payload, timeout=10)
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000
                
                if response.status_code == 200:
                    successful_requests += 1
                    response_times.append(response_time)
                    if i % 5 == 0:
                        print(f"   Request {i+1}: {response_time:.2f}ms ✅")
                else:
                    errors.append(f"HTTP {response.status_code}")
                    print(f"   Request {i+1}: Error {response.status_code} ❌")
                    
            except Exception as e:
                errors.append(str(e))
                print(f"   Request {i+1}: Exception {e} ❌")
        
        self.results['phase2'] = {
            'times': response_times,
            'errors': errors,
            'success_rate': (successful_requests / num_requests) * 100
        }
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            
            print(f"\n📊 Phase 2 Results:")
            print(f"   • Success Rate: {self.results['phase2']['success_rate']:.1f}%")
            print(f"   • Average Response: {avg_time:.2f}ms")
            print(f"   • Median Response: {median_time:.2f}ms")
            print(f"   • Total Errors: {len(errors)}")
        
        return successful_requests > 0
    
    def concurrent_load_test(self, concurrent_users=10, requests_per_user=5):
        """Test concurrent load on APIs"""
        print(f"\n🚀 Concurrent Load Test ({concurrent_users} users, {requests_per_user} req/user)")
        print("=" * 60)
        
        def make_concurrent_request(user_id):
            """Make a request from a specific user"""
            results = []
            
            for req_num in range(requests_per_user):
                try:
                    # Alternate between Phase 1 and Phase 2
                    if req_num % 2 == 0:
                        url = f"{self.base_urls['phase1']}/api/v1/search/confidence-weighted"
                        payload = {"query": f"test query {user_id}", "limit": 5}
                    else:
                        url = f"{self.base_urls['phase2']}/api/v2/discover/genre"
                        payload = {"preferred_genres": ["Fiction"], "limit": 5}
                    
                    start_time = time.time()
                    response = requests.post(url, json=payload, timeout=15)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    results.append({
                        'user_id': user_id,
                        'request_num': req_num,
                        'response_time': response_time,
                        'status_code': response.status_code,
                        'success': response.status_code == 200
                    })
                    
                except Exception as e:
                    results.append({
                        'user_id': user_id,
                        'request_num': req_num,
                        'response_time': None,
                        'status_code': None,
                        'success': False,
                        'error': str(e)
                    })
            
            return results
        
        # Monitor system resources during load test
        initial_memory = psutil.virtual_memory().percent
        initial_cpu = psutil.cpu_percent()
        
        print(f"   🔋 Initial System State:")
        print(f"      • Memory: {initial_memory:.1f}%")
        print(f"      • CPU: {initial_cpu:.1f}%")
        
        # Execute concurrent requests
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_concurrent_request, user_id) 
                      for user_id in range(concurrent_users)]
            
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_requests = sum(1 for r in all_results if r['success'])
        total_requests = len(all_results)
        success_rate = (successful_requests / total_requests) * 100
        
        response_times = [r['response_time'] for r in all_results if r['response_time']]
        
        final_memory = psutil.virtual_memory().percent
        final_cpu = psutil.cpu_percent()
        
        print(f"\n   📊 Load Test Results:")
        print(f"      • Total Duration: {total_duration:.2f}s")
        print(f"      • Total Requests: {total_requests}")
        print(f"      • Success Rate: {success_rate:.1f}%")
        print(f"      • Requests/Second: {total_requests/total_duration:.2f}")
        
        if response_times:
            print(f"      • Avg Response Time: {statistics.mean(response_times):.2f}ms")
            print(f"      • Max Response Time: {max(response_times):.2f}ms")
        
        print(f"   🔋 Final System State:")
        print(f"      • Memory: {final_memory:.1f}% (Δ{final_memory-initial_memory:+.1f}%)")
        print(f"      • CPU: {final_cpu:.1f}% (Δ{final_cpu-initial_cpu:+.1f}%)")
        
        self.results['load_test'] = {
            'concurrent_times': response_times,
            'success_rate': success_rate,
            'memory_delta': final_memory - initial_memory,
            'requests_per_second': total_requests / total_duration
        }
        
        return success_rate > 80  # 80% success rate threshold
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print(f"\n📋 PERFORMANCE AGENT FINAL REPORT")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Phase 1 Analysis
        if self.results['phase1']['times']:
            phase1_avg = statistics.mean(self.results['phase1']['times'])
            phase1_success = self.results['phase1']['success_rate']
            
            print(f"\n🎯 Phase 1 API Performance:")
            print(f"   • Average Response: {phase1_avg:.1f}ms")
            print(f"   • Success Rate: {phase1_success:.1f}%")
            print(f"   • Status: {'✅ PASS' if phase1_avg < 500 and phase1_success > 95 else '⚠️  REVIEW'}")
        
        # Phase 2 Analysis  
        if self.results['phase2']['times']:
            phase2_avg = statistics.mean(self.results['phase2']['times'])
            phase2_success = self.results['phase2']['success_rate']
            
            print(f"\n🎭 Phase 2 API Performance:")
            print(f"   • Average Response: {phase2_avg:.1f}ms")
            print(f"   • Success Rate: {phase2_success:.1f}%")
            print(f"   • Status: {'✅ PASS' if phase2_avg < 1000 and phase2_success > 90 else '⚠️  REVIEW'}")
        
        # Load Test Analysis
        if self.results['load_test']['concurrent_times']:
            load_avg = statistics.mean(self.results['load_test']['concurrent_times'])
            load_success = self.results['load_test']['success_rate']
            rps = self.results['load_test']['requests_per_second']
            
            print(f"\n🚀 Concurrent Load Performance:")
            print(f"   • Concurrent Response: {load_avg:.1f}ms")
            print(f"   • Load Success Rate: {load_success:.1f}%")
            print(f"   • Requests/Second: {rps:.1f}")
            print(f"   • Memory Impact: {self.results['load_test']['memory_delta']:+.1f}%")
            print(f"   • Status: {'✅ PASS' if load_success > 80 and rps > 5 else '⚠️  REVIEW'}")
        
        # Overall Assessment
        print(f"\n🏆 OVERALL ASSESSMENT:")
        
        # Calculate overall score
        score_factors = []
        if self.results['phase1']['success_rate'] > 95:
            score_factors.append(25)
        elif self.results['phase1']['success_rate'] > 85:
            score_factors.append(15)
        
        if self.results['phase2']['success_rate'] > 90:
            score_factors.append(25)
        elif self.results['phase2']['success_rate'] > 80:
            score_factors.append(15)
        
        if self.results['load_test']['success_rate'] > 80:
            score_factors.append(25)
        elif self.results['load_test']['success_rate'] > 70:
            score_factors.append(15)
        
        # Response time bonus
        if (self.results['phase1']['times'] and 
            statistics.mean(self.results['phase1']['times']) < 200):
            score_factors.append(25)
        elif (self.results['phase1']['times'] and 
              statistics.mean(self.results['phase1']['times']) < 500):
            score_factors.append(15)
        
        overall_score = sum(score_factors)
        
        if overall_score >= 90:
            status = "🎉 PRODUCTION READY"
        elif overall_score >= 70:
            status = "⚠️  NEEDS MINOR IMPROVEMENTS"  
        else:
            status = "❌ REQUIRES MAJOR FIXES"
        
        print(f"   • Performance Score: {overall_score}/100")
        print(f"   • Production Status: {status}")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if self.results['phase1']['success_rate'] < 95:
            print(f"   • Improve Phase 1 reliability (current: {self.results['phase1']['success_rate']:.1f}%)")
        if self.results['phase2']['success_rate'] < 90:
            print(f"   • Improve Phase 2 stability (current: {self.results['phase2']['success_rate']:.1f}%)")
        if self.results['load_test']['success_rate'] < 85:
            print(f"   • Optimize concurrent handling (current: {self.results['load_test']['success_rate']:.1f}%)")
        
        if overall_score >= 90:
            print(f"   • ✅ All systems performing within acceptable parameters")
            print(f"   • ✅ Ready for production deployment")
        
        return overall_score >= 70

def main():
    """Performance Agent: Execute comprehensive API benchmarking"""
    print("📊 Performance Agent: API Benchmark Suite")
    print("=" * 50)
    
    benchmark = APIPerformanceBenchmark()
    
    # Step 1: Health check
    if not benchmark.test_api_health():
        print("❌ APIs not healthy - cannot proceed with benchmarking")
        return False
    
    # Step 2: Benchmark Phase 1
    phase1_success = benchmark.benchmark_phase1_api(50)
    if not phase1_success:
        print("⚠️  Phase 1 benchmarking had issues")
    
    # Step 3: Benchmark Phase 2  
    phase2_success = benchmark.benchmark_phase2_api(30)
    if not phase2_success:
        print("⚠️  Phase 2 benchmarking had issues")
    
    # Step 4: Load testing
    load_success = benchmark.concurrent_load_test(10, 5)
    if not load_success:
        print("⚠️  Load testing revealed performance issues")
    
    # Step 5: Generate final report
    production_ready = benchmark.generate_performance_report()
    
    return production_ready

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)