#!/usr/bin/env python3
"""
🔄 Port 80 HTTP Proxy to HTTPS API on 5563
Quick solution while waiting for port 443 forwarding to work
"""

from flask import Flask, request, jsonify
import requests
import json
import os

app = Flask(__name__)

# Target API configuration
TARGET_API = "http://localhost:5563"
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    print("🚨 CRITICAL ERROR: API_KEY environment variable not set!")
    print("Set API_KEY environment variable before starting the proxy.")
    print("Example: export API_KEY=your_secure_api_key_here")
    exit(1)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def proxy(path):
    """Proxy all requests to the HTTPS API"""
    
    # Forward to HTTPS API
    target_url = f"{TARGET_API}/{path}"
    
    # Copy headers from original request
    headers = dict(request.headers)
    
    # Ensure API key is present
    if 'X-API-Key' not in headers:
        headers['X-API-Key'] = API_KEY
    
    try:
        # Forward the request
        if request.method == 'GET':
            response = requests.get(
                target_url, 
                headers=headers, 
                params=request.args,
                verify=False,  # Skip SSL verification for localhost
                timeout=30
            )
        elif request.method == 'POST':
            response = requests.post(
                target_url,
                headers=headers,
                params=request.args,
                json=request.get_json(),
                verify=False,
                timeout=30
            )
        else:
            return jsonify({"error": "Method not supported"}), 405
        
        # Return the response
        return response.content, response.status_code, dict(response.headers)
        
    except Exception as e:
        return jsonify({
            "error": "Proxy error",
            "details": str(e),
            "proxy_info": "HTTP-to-HTTPS bridge for LibraryOfBabel API"
        }), 503

if __name__ == '__main__':
    print("🔄 Starting HTTP-to-HTTPS Proxy on port 80")
    print("🎯 Forwarding to:", TARGET_API)
    print("🔑 Using API Key:", API_KEY[-8:])
    
    app.run(host='0.0.0.0', port=80, debug=False)