#!/usr/bin/env python3
"""
🧪 Quick Test for Magistral Genre Classification
"""

import requests
import time

def test_magistral_classification():
    """Quick test of Magistral for genre classification"""
    
    test_prompt = """
You are an expert librarian. Classify this book into ONE genre from this list:
1. Fiction
2. Science Fiction & Fantasy
3. Philosophy & Theory
4. History & Biography
5. Science & Technology

Book: "The Foundation" by Isaac Asimov - A science fiction series about psychohistory and the fall of a galactic empire.

Respond with just the genre name:"""

    print("🧪 Testing Magistral Genre Classification...")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "magistral",
                "prompt": test_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "max_tokens": 20
                }
            },
            timeout=60
        )
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json().get('response', '').strip()
            print(f"✅ Magistral Response: '{result}'")
            print(f"⏱️  Processing Time: {processing_time:.1f}s")
            
            if "Science Fiction" in result:
                print("🎯 Correct classification!")
                return True
            else:
                print("❓ Unexpected classification")
                return False
        else:
            print(f"❌ Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_magistral_classification()
    if success:
        print("\n✅ Magistral is ready for genre classification!")
    else:
        print("\n❌ Magistral test failed")