#!/usr/bin/env python3
"""
🔧 Agent Memory Management - LibraryOfBabel
==========================================

Utilities to manage the agent memory database:
- Clean up duplicate tasks
- View memory statistics
- Reset sessions
- Export/import agent state
"""

import sqlite3
from claude_agent_memory import get_agent_memory
from datetime import datetime

def cleanup_duplicate_tasks():
    """Remove duplicate tasks with same title"""
    memory = get_agent_memory()
    conn = sqlite3.connect(memory.db_path)
    cursor = conn.cursor()

    # Find duplicates
    cursor.execute('''
        SELECT title, COUNT(*) as count
        FROM agent_tasks
        WHERE status = 'pending'
        GROUP BY title
        HAVING count > 1
    ''')

    duplicates = cursor.fetchall()
    cleaned_count = 0

    for title, count in duplicates:
        # Keep the oldest one, delete the rest
        cursor.execute('''
            DELETE FROM agent_tasks
            WHERE task_id NOT IN (
                SELECT task_id FROM agent_tasks
                WHERE title = ? AND status = 'pending'
                ORDER BY created_time ASC
                LIMIT 1
            ) AND title = ? AND status = 'pending'
        ''', (title, title))

        deleted = cursor.rowcount
        cleaned_count += deleted
        print(f"🧹 Cleaned {deleted} duplicate tasks: {title}")

    conn.commit()
    conn.close()

    print(f"✅ Total duplicates cleaned: {cleaned_count}")
    return cleaned_count

def view_memory_stats():
    """Show agent memory database statistics"""
    memory = get_agent_memory()
    conn = sqlite3.connect(memory.db_path)
    cursor = conn.cursor()

    print("\n📊 AGENT MEMORY STATISTICS")
    print("="*40)

    # Sessions
    cursor.execute("SELECT COUNT(*) FROM agent_sessions")
    session_count = cursor.fetchone()[0]
    print(f"Sessions: {session_count}")

    # Tasks by status
    cursor.execute('''
        SELECT status, COUNT(*) FROM agent_tasks
        GROUP BY status
    ''')
    for status, count in cursor.fetchall():
        print(f"Tasks ({status}): {count}")

    # Memory entries
    cursor.execute('''
        SELECT memory_type, COUNT(*) FROM agent_memory
        GROUP BY memory_type
    ''')
    for mem_type, count in cursor.fetchall():
        print(f"Memory ({mem_type}): {count}")

    # Handoffs
    cursor.execute("SELECT COUNT(*) FROM agent_handoffs")
    handoff_count = cursor.fetchone()[0]
    print(f"Handoffs: {handoff_count}")

    # Database size
    cursor.execute("PRAGMA page_count")
    pages = cursor.fetchone()[0]
    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]
    db_size_mb = (pages * page_size) / (1024 * 1024)
    print(f"Database size: {db_size_mb:.2f} MB")

    conn.close()

def reset_pending_tasks():
    """Reset all pending tasks (use with caution)"""
    memory = get_agent_memory()
    conn = sqlite3.connect(memory.db_path)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM agent_tasks WHERE status = 'pending'")
    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"🚨 Reset {deleted} pending tasks")
    return deleted

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "stats":
            view_memory_stats()
        elif command == "cleanup":
            cleanup_duplicate_tasks()
        elif command == "reset-tasks":
            confirm = input("⚠️  This will delete all pending tasks. Type 'yes' to confirm: ")
            if confirm.lower() == 'yes':
                reset_pending_tasks()
            else:
                print("Cancelled")
        else:
            print("Available commands: stats, cleanup, reset-tasks")
    else:
        print("📊 Agent Memory Management")
        print("Usage: python3 manage_agent_memory.py [stats|cleanup|reset-tasks]")
        print()
        view_memory_stats()