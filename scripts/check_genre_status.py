#!/usr/bin/env python3
import sys
sys.path.append('/Users/weixiangzhang/Local_Dev/LibraryOfBabel')
from config.api_config import get_database_config
import psycopg2

config = get_database_config()
conn = psycopg2.connect(**config)
cur = conn.cursor()

# Check missing genres
cur.execute("SELECT COUNT(*) FROM books WHERE genre IS NULL OR genre = ''")
missing = cur.fetchone()[0]

# Check classified books
cur.execute("SELECT COUNT(*) FROM books WHERE genre IS NOT NULL AND genre != ''")
classified = cur.fetchone()[0]

# Total books
cur.execute("SELECT COUNT(*) FROM books")
total = cur.fetchone()[0]

print(f"Genre Classification Status:")
print(f"  Total books: {total}")
print(f"  Classified: {classified}")
print(f"  Missing genres: {missing}")
print(f"  Completion: {(classified/total)*100:.1f}%")

conn.close()