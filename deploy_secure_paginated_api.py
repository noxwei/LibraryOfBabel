#!/usr/bin/env python3
"""
🚀 DEPLOY SECURE PAGINATED API TO PRODUCTION
============================================

Deploys the secure_paginated_api.py to api.ashortstayinhell.com:5562
with proper SSL certificates and environment configuration.
"""

import os
import sys
import subprocess
import signal
import time
import requests
import json
from datetime import datetime

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def kill_existing_processes():
    """Kill any existing API processes on port 5562"""
    log("🧹 Cleaning existing processes on port 5562...")
    try:
        # Kill processes using port 5562
        result = subprocess.run(['lsof', '-ti:5562'], capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        subprocess.run(['kill', '-9', pid], check=False)
                        log(f"   ✅ Killed process {pid}")
                    except:
                        pass
        
        # Also kill any paginated API processes
        subprocess.run(['pkill', '-f', 'paginated_api.py'], check=False)
        subprocess.run(['pkill', '-f', 'production_api.py'], check=False)
        
        time.sleep(2)
        log("   ✅ Existing processes cleaned")
    except Exception as e:
        log(f"   ⚠️ Warning during cleanup: {e}")

def verify_ssl_certificates():
    """Verify SSL certificates exist"""
    log("🔍 Verifying SSL certificates...")
    
    ssl_dir = "ssl/letsencrypt-config/live/api.ashortstayinhell.com"
    cert_files = ['fullchain.pem', 'privkey.pem']
    
    for cert_file in cert_files:
        cert_path = os.path.join(ssl_dir, cert_file)
        if os.path.exists(cert_path):
            log(f"   ✅ Found {cert_file}")
        else:
            log(f"   ❌ Missing {cert_file}")
            return False
    
    return True

def set_environment_variables():
    """Set required environment variables"""
    log("🔧 Setting environment variables...")
    
    env_vars = {
        'API_KEY': 'babel_secure_3f99c2d1d294fbebdfc6b10cce93652d',
        'PORT': '5562',
        'DB_HOST': 'localhost',
        'DB_NAME': 'knowledge_base',
        'DB_USER': 'weixiangzhang',
        'DB_PORT': '5432',
        'PYTHONPATH': '/Users/weixiangzhang/Local Dev/LibraryOfBabel/src'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        log(f"   ✅ Set {key}")
    
    return env_vars

def start_secure_paginated_api():
    """Start the secure paginated API"""
    log("🚀 Starting Secure Paginated API...")
    
    api_script = "src/api/secure_paginated_api.py"
    
    if not os.path.exists(api_script):
        log(f"   ❌ API script not found: {api_script}")
        return None
    
    # Start the API process
    cmd = [sys.executable, api_script]
    log(f"   📍 Command: {' '.join(cmd)}")
    
    # Redirect output to log file
    log_file = open('logs/production_secure_paginated_api.log', 'w')
    
    process = subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=os.environ.copy()
    )
    
    log(f"   🔄 Started process PID: {process.pid}")
    
    # Wait for API to start
    log("   ⏳ Waiting for API to start...")
    time.sleep(5)
    
    # Check if process is still running
    if process.poll() is None:
        log("   ✅ API process running")
        return process
    else:
        log("   ❌ API process failed to start")
        return None

def test_api_endpoints():
    """Test API endpoints to verify deployment"""
    log("🧪 Testing API endpoints...")
    
    base_url = "https://api.ashortstayinhell.com:5562"
    api_key = "babel_secure_3f99c2d1d294fbebdfc6b10cce93652d"
    
    # Test health endpoint (no auth required)
    try:
        response = requests.get(f"{base_url}/health", timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            log(f"   ✅ /health: {data.get('status', 'unknown')} - {data.get('books', 0)} books")
        else:
            log(f"   ❌ /health: HTTP {response.status_code}")
    except Exception as e:
        log(f"   ❌ /health: {e}")
    
    # Test books endpoint (auth required)
    try:
        response = requests.get(
            f"{base_url}/books?api_key={api_key}&page=1&page_size=5",
            timeout=10,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            total_books = data.get('pagination', {}).get('total_items', 0)
            log(f"   ✅ /books: {total_books} total books accessible")
        else:
            log(f"   ❌ /books: HTTP {response.status_code}")
    except Exception as e:
        log(f"   ❌ /books: {e}")
    
    # Test API docs (no auth required)
    try:
        response = requests.get(f"{base_url}/api-docs", timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            log(f"   ✅ /api-docs: {data.get('title', 'API Documentation')}")
        else:
            log(f"   ❌ /api-docs: HTTP {response.status_code}")
    except Exception as e:
        log(f"   ❌ /api-docs: {e}")

def main():
    """Main deployment function"""
    log("🚀 SECURE PAGINATED API DEPLOYMENT TO PRODUCTION")
    log("=" * 60)
    log("🎯 Target: api.ashortstayinhell.com:5562")
    log("📦 API: secure_paginated_api.py with authentication")
    log("")
    
    # Step 1: Clean existing processes
    kill_existing_processes()
    
    # Step 2: Verify SSL certificates
    if not verify_ssl_certificates():
        log("❌ SSL certificate verification failed")
        return False
    
    # Step 3: Set environment variables
    env_vars = set_environment_variables()
    
    # Step 4: Start the secure paginated API
    process = start_secure_paginated_api()
    if not process:
        log("❌ Failed to start API")
        return False
    
    # Step 5: Test endpoints
    log("")
    test_api_endpoints()
    
    # Step 6: Deployment summary
    log("")
    log("🎉 DEPLOYMENT COMPLETE!")
    log("=" * 60)
    log(f"📍 Production URL: https://api.ashortstayinhell.com:5562")
    log(f"🔑 API Key: {env_vars['API_KEY']}")
    log(f"📊 Process PID: {process.pid}")
    log("")
    log("📋 Test Commands:")
    log("   Health: curl -s 'https://api.ashortstayinhell.com:5562/health' | jq .")
    log(f"   Books: curl -s 'https://api.ashortstayinhell.com:5562/books?api_key={env_vars['API_KEY']}&page=1&page_size=5' | jq .pagination")
    log("")
    log("📁 Logs: tail -f logs/production_secure_paginated_api.log")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            log("✅ Deployment successful!")
            sys.exit(0)
        else:
            log("❌ Deployment failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        log("🛑 Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"❌ Deployment error: {e}")
        sys.exit(1)