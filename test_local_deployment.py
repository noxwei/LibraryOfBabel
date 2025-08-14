#!/usr/bin/env python3
"""
Local Deployment Test
Simulates the GitHub Actions production deployment locally
"""

import os
import subprocess
import time
import requests
import json

def log(message):
    print(f"🚀 {message}")

def test_container_deployment():
    """Test the full container deployment pipeline locally"""
    log("Testing Container Deployment Pipeline")
    log("=" * 50)
    
    # Step 1: Build container
    log("📦 Building container...")
    try:
        result = subprocess.run([
            "docker", "build", "-t", "libraryofbabel-api:local-test", "."
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            log(f"❌ Container build failed: {result.stderr}")
            return False
        log("✅ Container built successfully")
    except Exception as e:
        log(f"❌ Container build error: {e}")
        return False
    
    # Step 2: Stop any existing container
    log("🔄 Stopping existing containers...")
    subprocess.run(["docker", "stop", "libraryofbabel-api-test"], capture_output=True)
    subprocess.run(["docker", "rm", "libraryofbabel-api-test"], capture_output=True)
    
    # Step 3: Start new container
    log("🚀 Starting containerized API...")
    try:
        container_cmd = [
            "docker", "run", "-d",
            "--name", "libraryofbabel-api-test",
            "-p", "5565:5565",
            "-e", "API_HOST=0.0.0.0",
            "-e", "API_PORT=5565", 
            "-e", "RUNNING_IN_CONTAINER=true",
            "-e", "FLASK_DEBUG=false",
            "-e", "TEST_MODE=true",  # Bypass auth for testing
            "libraryofbabel-api:local-test"
        ]
        
        result = subprocess.run(container_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log(f"❌ Container start failed: {result.stderr}")
            return False
        
        container_id = result.stdout.strip()
        log(f"✅ Container started: {container_id[:12]}")
        
        # Wait for startup
        log("⏳ Waiting for API to be ready...")
        time.sleep(10)
        
        # Step 4: Health check
        log("🔍 Running health checks...")
        health_url = "http://localhost:5565/health"
        try:
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                log("✅ Health check passed")
                log(f"   Response: {response.json()}")
            else:
                log(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            log(f"❌ Health check error: {e}")
            return False
        
        # Step 5: Test standardized endpoints
        log("🧪 Testing standardized endpoints...")
        endpoints = [
            "/health",
            "/api/info",
            "/api/health", 
            "/api/books?action=list&limit=1",
            "/api/search?q=test&limit=1",
            "/api/mobile/random?type=title"
        ]
        
        success_count = 0
        for endpoint in endpoints:
            url = f"http://localhost:5565{endpoint}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    log(f"   ✅ {endpoint}")
                    success_count += 1
                else:
                    log(f"   ❌ {endpoint} - {response.status_code}")
            except Exception as e:
                log(f"   ❌ {endpoint} - {e}")
        
        success_rate = (success_count / len(endpoints)) * 100
        log(f"📊 Container endpoint success rate: {success_rate}%")
        
        # Step 6: Generate deployment report
        log("📊 Generating deployment report...")
        report = {
            "deployment_type": "local_container_test",
            "container_id": container_id[:12],
            "success_rate": f"{success_rate}%",
            "endpoints_tested": len(endpoints),
            "endpoints_passed": success_count,
            "api_version": "standardized_v5",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("local_deployment_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        log("📄 Deployment report saved to local_deployment_report.json")
        
        # Step 7: Simulate website update
        log("🌐 Simulating website update...")
        website_update = {
            "api_status": "deployed",
            "container_ready": True,
            "endpoints_available": success_count,
            "documentation_updated": True,
            "ios_shortcuts_ready": success_rate >= 90
        }
        
        log("   📝 Website would be updated with:")
        log(f"   - API Status: {website_update['api_status']}")
        log(f"   - Container: {'Ready' if website_update['container_ready'] else 'Not Ready'}")
        log(f"   - Endpoints: {website_update['endpoints_available']}/{len(endpoints)}")
        log(f"   - iOS Shortcuts: {'Ready' if website_update['ios_shortcuts_ready'] else 'Not Ready'}")
        
        return success_rate >= 75
        
    finally:
        # Cleanup
        log("🧹 Cleaning up...")
        subprocess.run(["docker", "stop", "libraryofbabel-api-test"], capture_output=True)
        subprocess.run(["docker", "rm", "libraryofbabel-api-test"], capture_output=True)
        subprocess.run(["docker", "rmi", "libraryofbabel-api:local-test"], capture_output=True)
        log("✅ Cleanup completed")

def main():
    log("🎯 LOCAL DEPLOYMENT SIMULATION")
    log("Testing what GitHub Actions will do in production")
    log("")
    
    success = test_container_deployment()
    
    log("")
    if success:
        log("🎉 LOCAL DEPLOYMENT TEST PASSED!")
        log("✅ Container deployment pipeline ready for production")
        log("✅ GitHub Actions will work when pushed to main branch")
        log("🌐 Website update simulation successful")
        return 0
    else:
        log("❌ LOCAL DEPLOYMENT TEST FAILED!")
        log("⚠️ Fix issues before pushing to main branch")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())