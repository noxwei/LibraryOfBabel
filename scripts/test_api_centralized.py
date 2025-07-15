#!/usr/bin/env python3
"""
🧪 CENTRALIZED API TEST SCRIPT
=============================

Uses centralized configuration to ensure consistent API key usage.
No more hardcoded keys or configuration mismatches.
"""

import sys
import os
import requests
import json
import urllib3
from pathlib import Path

# Add config directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "config"))

from api_config import get_api_key, get_base_url, validate_configuration

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CentralizedAPITest:
    def __init__(self):
        # Use centralized configuration
        self.api_key = get_api_key()
        self.base_url = get_base_url()
        
        print(f"🔧 Using centralized config:")
        print(f"   API Key: {self.api_key[:20]}...")
        print(f"   Base URL: {self.base_url}")
        
        # Validate configuration
        if not validate_configuration():
            raise Exception("❌ Configuration validation failed!")
    
    def test_endpoint(self, name: str, endpoint: str, params: dict = None) -> bool:
        """Test an API endpoint"""
        if params is None:
            params = {}
        
        # Always include API key from centralized config
        params['api_key'] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        print(f"🧪 Testing: {name}")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, params=params, verify=False, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get('results', [])) if 'results' in data else 'N/A'
                print(f"   ✅ SUCCESS - Results: {result_count}")
                return True
            else:
                print(f"   ❌ FAILED - HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ ERROR - {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run comprehensive API test using centralized configuration"""
        print("🚀 CENTRALIZED API CONFIGURATION TEST")
        print("=" * 50)
        
        tests = [
            ("Health Check", "/health", {}),
            ("Books List", "/books", {"page_size": 3}),
            ("Book Details", "/books/1373", {}),
            ("Book Chunks", "/books/1373/chunks", {"page_size": 2}),
            ("Traditional Search", "/search", {"q": "Foucault", "page_size": 3}),
            ("In-Book Search", "/books/1099/search", {"q": "discourse", "page_size": 3}),
            ("Fuzzy Semantic Search", "/fuzzy-search", {"q": "artificial intelligence", "type": "semantic", "limit": 3}),
            ("V3 Health (Legacy)", "/api/v3/health", {}),
            ("V3 Search (Legacy)", "/api/v3/search", {"q": "philosophy", "limit": 2})
        ]
        
        passed = 0
        total = len(tests)
        
        for name, endpoint, params in tests:
            if self.test_endpoint(name, endpoint, params):
                passed += 1
        
        success_rate = (passed / total) * 100
        
        print(f"\n📊 CENTRALIZED CONFIG TEST RESULTS:")
        print(f"   Passed: {passed}/{total}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT - Centralized configuration working perfectly!")
        elif success_rate >= 80:
            print("✅ GOOD - Centralized configuration working well")
        else:
            print("⚠️ Issues detected - check configuration")
        
        return success_rate >= 80

def main():
    """Main test function"""
    try:
        tester = CentralizedAPITest()
        success = tester.run_comprehensive_test()
        
        if success:
            print("\n🎯 CENTRALIZED CONFIGURATION: VALIDATED")
            print("🔧 All scripts can now use consistent API configuration")
            print("📝 Future updates will be centrally managed")
        else:
            print("\n⚠️ Configuration issues detected")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()