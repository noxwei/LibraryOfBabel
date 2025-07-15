#!/usr/bin/env python3
"""Log development activity for HR tracking"""

import argparse
import psycopg2
import json
from datetime import datetime
import os

def log_activity(commit_hash, author, message, date):
    """Log development activity to HR system"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'user': os.getenv('DB_USER', 'weixiangzhang'),
        'port': int(os.getenv('DB_PORT', 5432))
    }
    
    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO hr_automation.development_activity 
                    (commit_hash, author, commit_message, commit_date, logged_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (commit_hash, author, message, date, datetime.now()))
                conn.commit()
                print(f"✅ Logged development activity: {commit_hash[:8]} by {author}")
    except Exception as e:
        print(f"❌ Failed to log activity: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", required=True)
    parser.add_argument("--author", required=True) 
    parser.add_argument("--message", required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    
    log_activity(args.commit, args.author, args.message, args.date)
