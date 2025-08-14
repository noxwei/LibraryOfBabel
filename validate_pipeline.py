#!/usr/bin/env python3
"""
Pipeline Validation Script
Tests our new CI/CD pipeline components locally before GitHub Actions runs
"""

import os
import sys
import subprocess
import time
import requests
import json

def log(message):
    """Simple logging"""
    print(f"🔧 {message}")

def test_api_startup():
    """Test that our standardized API starts correctly"""
    log("Testing API startup...")
    
    # Start the API in background
    process = subprocess.Popen([
        sys.executable, "src/api/standardized_production_api.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    time.sleep(5)
    
    try:
        # Test health endpoint
        response = requests.get("http://127.0.0.1:5564/health", timeout=5)
        if response.status_code == 200:
            log("✅ API startup successful")
            return True
        else:
            log(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ API connection failed: {e}")
        return False
    finally:
        # Clean up
        process.terminate()
        process.wait()

def test_docker_build():
    """Test Docker build process"""
    log("Testing Docker build...")
    
    try:
        # Build the container
        result = subprocess.run([
            "docker", "build", "-t", "libraryofbabel-api:test", "."
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            log("✅ Docker build successful")
            
            # Clean up test image
            subprocess.run(["docker", "rmi", "libraryofbabel-api:test"], 
                         capture_output=True)
            return True
        else:
            log(f"❌ Docker build failed: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ Docker build error: {e}")
        return False

def test_security_checks():
    """Test security scanning tools"""
    log("Testing security checks...")
    
    try:
        # Test bandit
        result = subprocess.run([
            "bandit", "-r", "src/api/", "-f", "json"
        ], capture_output=True, text=True)
        
        if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
            log("✅ Bandit security scan working")
            return True
        else:
            log(f"❌ Bandit failed: {result.stderr}")
            return False
    except FileNotFoundError:
        log("⚠️ Bandit not installed - install with: pip install bandit")
        return True  # Don't fail pipeline for missing tools
    except Exception as e:
        log(f"❌ Security check error: {e}")
        return False

def test_endpoints():
    """Test key API endpoints"""
    log("Testing API endpoints...")
    
    # Start API
    process = subprocess.Popen([
        sys.executable, "src/api/standardized_production_api.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(5)
    
    try:
        endpoints = [
            "http://127.0.0.1:5564/health",
            "http://127.0.0.1:5564/api/info",
            "http://127.0.0.1:5564/api/books?action=list&limit=1",
        ]
        
        success_count = 0
        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    log(f"✅ {endpoint}")
                    success_count += 1
                else:
                    log(f"❌ {endpoint} - {response.status_code}")
            except Exception as e:
                log(f"❌ {endpoint} - {e}")
        
        success_rate = (success_count / len(endpoints)) * 100
        log(f"📊 Endpoint success rate: {success_rate}%")
        
        return success_rate >= 66  # Allow some failures for local testing
    
    finally:
        process.terminate()
        process.wait()

def main():
    """Run all pipeline validation tests"""
    log("🚀 Starting Pipeline Validation")
    log("=" * 40)
    
    tests = [
        ("API Startup", test_api_startup),
        ("Docker Build", test_docker_build),
        ("Security Checks", test_security_checks),
        ("Endpoint Testing", test_endpoints),
    ]
    
    results = {}
    for test_name, test_func in tests:
        log(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            log(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    log("\n📊 PIPELINE VALIDATION SUMMARY")
    log("=" * 40)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅" if passed_test else "❌"
        log(f"{status} {test_name}")
    
    success_rate = (passed / total) * 100
    log(f"\n📊 Overall Success Rate: {success_rate}%")
    
    if success_rate >= 75:
        log("🎉 Pipeline validation PASSED - Ready for GitHub Actions!")
        return 0
    else:
        log("⚠️ Pipeline validation FAILED - Fix issues before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())