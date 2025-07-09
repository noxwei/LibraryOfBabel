#!/usr/bin/env python3
"""
🔄 HTTP to HTTPS Redirect Service for api.ashortstayinhell.com
Redirects HTTP traffic on port 80 to HTTPS on port 5563
"""

from flask import Flask, request, redirect, url_for
import os

app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def redirect_to_https(path):
    """Redirect all HTTP traffic to HTTPS on port 5563"""
    # Construct the HTTPS URL
    https_url = f"https://api.ashortstayinhell.com:5563/{path}"
    
    # Preserve query parameters
    if request.query_string:
        https_url += f"?{request.query_string.decode()}"
    
    return redirect(https_url, code=301)

@app.route('/health')
def health_check():
    """Health check for the redirect service"""
    return {
        'status': 'healthy',
        'service': 'HTTP to HTTPS redirect',
        'redirect_target': 'https://api.ashortstayinhell.com:5563'
    }

if __name__ == '__main__':
    print("🔄 Starting HTTP to HTTPS redirect service on port 80")
    print("🎯 Redirecting to: https://api.ashortstayinhell.com:5563")
    
    app.run(host='0.0.0.0', port=80, debug=False)