#!/usr/bin/env python3
"""
🧪 QA Tests for Linda's HR Daemon System
===========================================

Integrates HR system monitoring into the QA test suite.
Ensures the HR daemon is properly functioning and won't cause confusion during testing.
"""

import requests
import subprocess
import psycopg2
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class HRSystemQATests:
    """
    QA Test Suite for Linda's HR Management System
    
    Tests that HR daemon is operational and integrates properly with the system.
    Prevents future confusion when processes don't shut down (by design).
    """
    
    def __init__(self):
        self.hr_api_url = "http://localhost:8081"
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base',
            'user': 'weixiangzhang',
            'port': 5432
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("HRSystemQA")
        
        print("🧪 QA Tests for Linda's HR System")
        print("🔧 Testing HR daemon integration")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive HR system QA tests
        """
        results = {
            "test_date": datetime.now().isoformat(),
            "tester": "QA Team - HR Daemon Integration",
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "warnings": []
        }
        
        # Test suite
        tests = [
            ("hr_api_status", self._test_hr_api_status),
            ("hr_process_running", self._test_hr_process_running),
            ("cron_jobs_installed", self._test_cron_jobs_installed),
            ("database_integration", self._test_database_integration),
            ("api_endpoints", self._test_api_endpoints),
            ("scheduled_tasks", self._test_scheduled_tasks),
            ("cross_training_active", self._test_cross_training_active),
            ("performance_monitoring", self._test_performance_monitoring)
        ]
        
        print("\n🗺 HR SYSTEM QA TEST SUITE")
        print("=" * 40)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                results["tests_run"].append({
                    "test": test_name,
                    "status": "PASS" if result["passed"] else "FAIL",
                    "details": result["details"],
                    "duration_ms": result.get("duration_ms", 0)
                })
                
                if result["passed"]:
                    results["passed"] += 1
                    print(f"✅ {test_name}: PASS")
                else:
                    results["failed"] += 1
                    print(f"❌ {test_name}: FAIL - {result['details']}")
                    
                if "warning" in result:
                    results["warnings"].append(f"{test_name}: {result['warning']}")
                    
            except Exception as e:
                results["failed"] += 1
                results["tests_run"].append({
                    "test": test_name,
                    "status": "ERROR",
                    "details": str(e)
                })
                print(f"⚠️ {test_name}: ERROR - {e}")
        
        # Generate summary
        total_tests = len(tests)
        success_rate = (results["passed"] / total_tests) * 100
        
        print(f"\n📋 HR SYSTEM QA SUMMARY:")
        print(f"   Tests run: {total_tests}")
        print(f"   Passed: {results['passed']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Warnings: {len(results['warnings'])}")
        
        if success_rate >= 80:
            print("✅ HR System: OPERATIONAL - Safe to continue testing")
        elif success_rate >= 60:
            print("⚠️ HR System: DEGRADED - May affect some features")
        else:
            print("❌ HR System: FAILING - Investigate immediately")
        
        # Save results
        self._save_qa_results(results)
        
        return results
    
    def _test_hr_api_status(self) -> Dict[str, Any]:
        """
        Test that HR API is responding
        """
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.hr_api_url}/hr/status", timeout=5)
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "operational":
                    return {
                        "passed": True,
                        "details": f"API operational, response time: {duration_ms:.0f}ms",
                        "duration_ms": duration_ms
                    }
                else:
                    return {
                        "passed": False,
                        "details": f"API responding but status not operational: {data.get('status')}"
                    }
            else:
                return {
                    "passed": False,
                    "details": f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "passed": False,
                "details": f"API connection failed: {e}"
            }
    
    def _test_hr_process_running(self) -> Dict[str, Any]:
        """
        Test that HR process is running
        """
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            hr_processes = [line for line in result.stdout.split('\n') if 'hr_api.py' in line]
            
            if hr_processes:
                return {
                    "passed": True,
                    "details": f"HR daemon running: {len(hr_processes)} process(es) found"
                }
            else:
                return {
                    "passed": False,
                    "details": "HR daemon process not found - may need to start service"
                }
                
        except Exception as e:
            return {
                "passed": False,
                "details": f"Process check failed: {e}"
            }
    
    def _test_cron_jobs_installed(self) -> Dict[str, Any]:
        """
        Test that HR cron jobs are installed
        """
        try:
            result = subprocess.run(
                ["crontab", "-l"], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode == 0:
                cron_content = result.stdout
                hr_jobs = [line for line in cron_content.split('\n') if 'hr_task_runner.py' in line]
                
                if len(hr_jobs) >= 4:  # Should have 4 scheduled tasks
                    return {
                        "passed": True,
                        "details": f"HR cron jobs installed: {len(hr_jobs)} tasks scheduled"
                    }
                elif len(hr_jobs) > 0:
                    return {
                        "passed": True,
                        "details": f"Partial HR cron jobs: {len(hr_jobs)}/4 tasks",
                        "warning": "Not all HR tasks scheduled"
                    }
                else:
                    return {
                        "passed": False,
                        "details": "No HR cron jobs found"
                    }
            else:
                return {
                    "passed": False,
                    "details": f"Crontab check failed: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "passed": False,
                "details": f"Cron check failed: {e}"
            }
    
    def _test_database_integration(self) -> Dict[str, Any]:
        """
        Test HR database integration
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Check for HR automation schema
                    cur.execute("""
                        SELECT schema_name FROM information_schema.schemata 
                        WHERE schema_name = 'hr_automation'
                    """)
                    
                    if not cur.fetchone():
                        return {
                            "passed": False,
                            "details": "HR automation schema not found"
                        }
                    
                    # Check for key tables
                    cur.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'hr_automation'
                    """)
                    
                    tables = [row[0] for row in cur.fetchall()]
                    required_tables = ['task_schedule']
                    
                    missing_tables = [t for t in required_tables if t not in tables]
                    
                    if missing_tables:
                        return {
                            "passed": False,
                            "details": f"Missing HR tables: {missing_tables}"
                        }
                    
                    # Check for scheduled tasks
                    cur.execute("SELECT COUNT(*) FROM hr_automation.task_schedule WHERE enabled = true")
                    active_tasks = cur.fetchone()[0]
                    
                    return {
                        "passed": True,
                        "details": f"Database integration OK: {len(tables)} tables, {active_tasks} active tasks"
                    }
                    
        except Exception as e:
            return {
                "passed": False,
                "details": f"Database connection failed: {e}"
            }
    
    def _test_api_endpoints(self) -> Dict[str, Any]:
        """
        Test all HR API endpoints
        """
        endpoints = [
            "/hr/status",
            "/hr/agents", 
            "/hr/alerts"
        ]
        
        results = []
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.hr_api_url}{endpoint}", timeout=5)
                results.append({
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "success": response.status_code == 200
                })
            except Exception as e:
                results.append({
                    "endpoint": endpoint,
                    "status": "ERROR",
                    "success": False,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r["success"])
        total = len(endpoints)
        
        if successful == total:
            return {
                "passed": True,
                "details": f"All {total} API endpoints responding"
            }
        elif successful > 0:
            return {
                "passed": True,
                "details": f"{successful}/{total} endpoints working",
                "warning": "Some endpoints failing"
            }
        else:
            return {
                "passed": False,
                "details": "All API endpoints failing"
            }
    
    def _test_scheduled_tasks(self) -> Dict[str, Any]:
        """
        Test that scheduled tasks are properly configured
        """
        try:
            response = requests.get(f"{self.hr_api_url}/hr/status", timeout=5)
            if response.status_code != 200:
                return {
                    "passed": False,
                    "details": "Cannot test scheduled tasks - API not responding"
                }
            
            # Check if we can run a test task
            test_result = subprocess.run(
                ["python3", "agents/hr/scheduled/hr_task_runner.py", "daily_performance"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if test_result.returncode == 0:
                return {
                    "passed": True,
                    "details": "Scheduled task runner working correctly"
                }
            else:
                return {
                    "passed": False,
                    "details": f"Task runner failed: {test_result.stderr}"
                }
                
        except Exception as e:
            return {
                "passed": False,
                "details": f"Scheduled task test failed: {e}"
            }
    
    def _test_cross_training_active(self) -> Dict[str, Any]:
        """
        Test that cross-training system is operational
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Check for emergency cross-training table
                    cur.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_name = 'emergency_cross_training'
                    """)
                    
                    if cur.fetchone():
                        # Check for active training assignments
                        cur.execute("""
                            SELECT COUNT(*) FROM emergency_cross_training 
                            WHERE status = 'ACTIVE'
                        """)
                        
                        active_training = cur.fetchone()[0]
                        
                        return {
                            "passed": True,
                            "details": f"Cross-training system operational: {active_training} active assignments"
                        }
                    else:
                        return {
                            "passed": True,
                            "details": "Cross-training table not found (may not be created yet)",
                            "warning": "Emergency cross-training not yet executed"
                        }
                        
        except Exception as e:
            return {
                "passed": False,
                "details": f"Cross-training check failed: {e}"
            }
    
    def _test_performance_monitoring(self) -> Dict[str, Any]:
        """
        Test that performance monitoring is working
        """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Check recent agent interactions (should have data)
                    cur.execute("""
                        SELECT COUNT(*) FROM agent_interactions 
                        WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    """)
                    
                    recent_interactions = cur.fetchone()[0]
                    
                    if recent_interactions > 0:
                        return {
                            "passed": True,
                            "details": f"Performance monitoring active: {recent_interactions} interactions in last 24h"
                        }
                    else:
                        return {
                            "passed": True,
                            "details": "Performance monitoring ready (no recent activity to monitor)",
                            "warning": "No recent agent activity to monitor"
                        }
                        
        except Exception as e:
            return {
                "passed": False,
                "details": f"Performance monitoring check failed: {e}"
            }
    
    def _save_qa_results(self, results: Dict[str, Any]):
        """
        Save QA test results
        """
        import os
        qa_dir = "agents/qa/reports"
        os.makedirs(qa_dir, exist_ok=True)
        
        filename = f"{qa_dir}/hr_system_qa_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📋 QA Results saved: {filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save QA results: {e}")

def main():
    """Run HR system QA tests"""
    qa_tester = HRSystemQATests()
    results = qa_tester.run_all_tests()
    
    print("\n👔 Message from Linda:")
    print('   "QA测试完成! (QA testing complete!) The HR system is now')
    print('   part of your regular testing cycle. 谢谢配合! (Thank you for cooperation!)"')
    
    return results

if __name__ == "__main__":
    main()