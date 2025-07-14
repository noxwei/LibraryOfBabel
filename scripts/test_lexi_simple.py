#!/usr/bin/env python3

import requests
import json
import os

# Set API key
API_KEY = os.getenv('API_KEY', 'YOUR_API_KEY_HERE')  # Set via environment variable
headers = {'Authorization': f'Bearer {API_KEY}'}

print("🎭 Testing Lexi Mascot Endpoints")
print("=" * 40)

# Test health endpoint
print("\n1. Testing Health Endpoint...")
try:
    response = requests.get('http://localhost:5000/api/v3/mascot/health', 
                          headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test chat endpoint
print("\n2. Testing Chat Endpoint...")
try:
    chat_data = {
        'query': 'Hello Lexi! Are you working?',
        'context': 'testing'
    }
    response = requests.post('http://localhost:5000/api/v3/mascot/chat', 
                           headers=headers, 
                           json=chat_data,
                           timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Lexi says: {result.get('response', 'No response')}")
        print(f"Full response: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 40)
print("Test complete!")