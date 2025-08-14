#!/usr/bin/env python3
"""
Show processed chunk outlines from database
"""

import psycopg2
import psycopg2.extras
import json
import os

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    database='knowledge_base',
    user='weixiangzhang',
    password=os.environ.get('DB_PASSWORD')
)

print('📊 SHOWING 5 PROCESSED CHUNK OUTLINES FROM DATABASE')
print('=' * 60)

with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
    # Get 5 chunks with outlines
    cur.execute("""
        SELECT 
            c.chunk_id,
            b.title as book_title,
            c.word_count,
            c.outline_summary,
            c.outline_key_points,
            c.outline_characters,
            c.outline_locations,
            c.outline_mood_tone,
            c.outline_quality,
            c.outline_processing_time
        FROM chunks c
        JOIN books b ON c.book_id = b.book_id
        WHERE c.outline_summary IS NOT NULL
        AND c.outline_summary != ''
        ORDER BY c.outline_quality DESC
        LIMIT 5
    """)
    
    results = cur.fetchall()
    
    for i, chunk in enumerate(results, 1):
        print(f'\n🔸 CHUNK {i}: {chunk["chunk_id"]}')
        print(f'   📚 Book: {chunk["book_title"]}')
        print(f'   📊 Words: {chunk["word_count"]:,} | Quality: {chunk["outline_quality"]:.2f} | Time: {chunk["outline_processing_time"]:.1f}s')
        print(f'   💭 Mood: {chunk["outline_mood_tone"]}')
        print(f'   📝 Summary: {chunk["outline_summary"][:120]}...')
        
        # Parse and show key points
        try:
            key_points = chunk['outline_key_points'] or []
            if isinstance(key_points, str):
                key_points = json.loads(key_points)
            if key_points:
                print(f'   🔹 Key Points:')
                for point in key_points[:2]:
                    print(f'      • {point[:80]}...')
        except Exception as e:
            print(f'   🔹 Key Points: (error: {e})')
            
        # Parse and show characters
        try:
            characters = chunk['outline_characters'] or []
            if isinstance(characters, str):
                characters = json.loads(characters)
            if characters:
                # Clean character names (remove * and extra formatting)
                clean_chars = [char.replace('*', '').strip() for char in characters]
                print(f'   👥 Characters: {", ".join(clean_chars[:4])}')
        except Exception as e:
            print(f'   👥 Characters: (error: {e})')
            
        # Parse and show locations
        try:
            locations = chunk['outline_locations'] or []
            if isinstance(locations, str):
                locations = json.loads(locations)
            if locations:
                # Clean location names (remove * and extra formatting)
                clean_locs = [loc.replace('*', '').strip() for loc in locations]
                print(f'   📍 Locations: {", ".join(clean_locs[:3])}')
        except Exception as e:
            print(f'   📍 Locations: (error: {e})')

conn.close()
print('\n' + '=' * 60)
print('✅ All outlines stored directly in PostgreSQL chunks table!')
print('🚀 Ready to scale up processing to more chunks!')