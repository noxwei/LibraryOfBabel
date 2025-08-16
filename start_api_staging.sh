#!/bin/bash
# LibraryOfBabel Staging API Server Script
# Runs on port 5568 with wildcard SSL certificate

cd /Users/weixiangzhang/Local_Dev/LibraryOfBabel

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="/Users/weixiangzhang/Local_Dev/LibraryOfBabel/src"
export API_KEY="${STAGING_API_KEY}"
# Authentication token sourced from environment
export API_PORT="5568"
export API_HOST="0.0.0.0"
export OLLAMA_MODEL="llama3.2:3b"
export SSL_CERT_PATH="./ssl/letsencrypt-config/live/wildcard-ashortstayinhell/fullchain.pem"
export SSL_KEY_PATH="./ssl/letsencrypt-config/live/wildcard-ashortstayinhell/privkey.pem"

echo "🚀 Starting LibraryOfBabel Staging API Server"
echo "📍 URL: https://staging.ashortstayinhell.com:5568"
echo "🔒 SSL: Wildcard certificate enabled"
echo "🔑 API Key: ${API_KEY}"

exec /opt/homebrew/bin/python3 src/api/standardized_production_api.py