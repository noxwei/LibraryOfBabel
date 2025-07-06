#!/bin/bash
# LibraryOfBabel Certificate Renewal Script

LOG_FILE="/Users/weixiangzhang/Local Dev/LibraryOfBabel/logs/cert-renewal.log"
SSL_DIR="/Users/weixiangzhang/Local Dev/LibraryOfBabel/ssl"

echo "$(date): Starting certificate renewal check" >> "$LOG_FILE"

cd "$SSL_DIR"
certbot renew \
    --config-dir "./letsencrypt-config" \
    --work-dir "./letsencrypt-work" \
    --logs-dir "./letsencrypt-logs" \
    --quiet

if [ $? -eq 0 ]; then
    echo "$(date): Certificate renewal successful" >> "$LOG_FILE"
    # Restart API to load new certificates
    launchctl stop com.librarybabel.api
    sleep 2
    launchctl start com.librarybabel.api
    echo "$(date): API restarted with new certificates" >> "$LOG_FILE"
else
    echo "$(date): Certificate renewal failed" >> "$LOG_FILE"
fi