#!/usr/bin/env python3
"""
Test script for the new Lexi endpoints
Verifies that the cleaner API URLs work correctly
"""

import requests
import json
import os
import sys

# API Configuration
API_BASE = "http://localhost:8080"
API_KEY = os.environ.get('LIBRARYOFBABEL_API_KEY')

def test_lexi_endpoints():
    """Test the new Lexi endpoints"""
    
    if not API_KEY:
        print("❌ LIBRARYOFBABEL_API_KEY environment variable not set")
        return False
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("🧪 Testing Lexi API Endpoints")
    print("=" * 50)
    
    # Test 1: Health endpoint
    print("\n1. Testing /api/v3/lexi/health")
    try:
        response = requests.get(f"{API_BASE}/api/v3/lexi/health", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working: {data.get('status', 'unknown')}")
            print(f"   Mascot: {data.get('mascot', 'unknown')}")
            print(f"   Components: {list(data.get('components', {}).keys())}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False
    
    # Test 2: Chat endpoint
    print("\n2. Testing /api/v3/lexi (main chat)")
    try:
        test_query = {
            "query": "What books do you have about artificial intelligence?",
            "session_id": "test_session_123",
            "context": "endpoint_test"
        }
        
        response = requests.post(f"{API_BASE}/api/v3/lexi", 
                               headers=headers, 
                               json=test_query)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chat endpoint working")
            print(f"   Mascot: {data.get('mascot', 'unknown')}")
            print(f"   Full name: {data.get('mascot_full_name', 'unknown')}")
            print(f"   Is primary mascot: {data.get('is_primary_mascot', False)}")
            print(f"   Response length: {len(data.get('response', ''))}")
        else:
            print(f"❌ Chat endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        return False
    
    # Test 3: Check API info for updated endpoints
    print("\n3. Testing /api/v3/info for updated endpoint list")
    try:
        response = requests.get(f"{API_BASE}/api/v3/info")
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get('endpoints', {})
            lexi_endpoints = endpoints.get('lexi', [])
            
            print(f"✅ API info working")
            print(f"   Lexi endpoints: {lexi_endpoints}")
            
            # Verify the new endpoints are listed
            if '/api/v3/lexi' in lexi_endpoints:
                print("✅ New primary endpoint /api/v3/lexi found")
            else:
                print("❌ New primary endpoint /api/v3/lexi NOT found")
                return False
                
            if '/api/v3/lexi/health' in lexi_endpoints:
                print("✅ New health endpoint /api/v3/lexi/health found")
            else:
                print("❌ New health endpoint /api/v3/lexi/health NOT found")
                return False
                
        else:
            print(f"❌ API info failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API info error: {e}")
        return False
    
    print("\n🎉 All tests passed! Lexi endpoints are working correctly.")
    print("🤖 Lexi is now THE official LibraryOfBabel mascot with clean URLs!")
    return True

if __name__ == "__main__":
    success = test_lexi_endpoints()
    sys.exit(0 if success else 1)