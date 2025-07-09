#!/bin/bash
# API Key Rotation Check Wrapper for Cron

# Set working directory
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"

# Run monitoring check
/opt/homebrew/bin/python3 scripts/key_rotation_monitor.py --daemon >> logs/rotation_cron.log 2>&1

# Log completion
echo "[$(date)] Rotation monitoring check completed" >> logs/rotation_cron.log
