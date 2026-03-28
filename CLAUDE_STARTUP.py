#!/usr/bin/env python3
"""
🚀 Claude Code Startup Initialization - LibraryOfBabel
=====================================================

THIS FILE IS AUTOMATICALLY CHECKED WHEN CLAUDE CODE STARTS

Purpose: Ensure Claude has immediate access to:
- Agent memory and session continuity
- Project context and current state
- Pending tasks and priorities
- LibraryOfBabel metrics and status

Usage: Claude Code will automatically import and run this on startup
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def claude_startup_check():
    """Essential startup checks and context loading for Claude Code"""

    print("\n" + "🚀" * 30)
    print("CLAUDE CODE STARTUP - LIBRARYOFBABEL")
    print("🚀" * 30)

    try:
        # Import and initialize agent memory
        from claude_agent_memory import get_agent_memory

        memory = get_agent_memory()

        print("✅ Agent memory system loaded successfully")

        # Get pending tasks
        import sqlite3
        conn = sqlite3.connect(memory.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM agent_tasks WHERE status = 'pending'
        ''')
        pending_count = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM agent_tasks WHERE status = 'in_progress'
        ''')
        in_progress_count = cursor.fetchone()[0]

        # Get latest metrics
        cursor.execute('''
            SELECT chunks_processed, books_count, success_rate, database_size_gb
            FROM library_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        metrics = cursor.fetchone()

        conn.close()

        print(f"📊 Current State:")
        if metrics:
            chunks, books, rate, size = metrics
            print(f"   • {chunks:,} chunks processed | {books:,} books | {rate:.2%} success rate")
            print(f"   • Database: {size:.1f}GB")

        print(f"📋 Tasks: {pending_count} pending, {in_progress_count} in progress")

        # Show critical reminders
        print("\n🎯 CRITICAL REMINDERS:")
        print("   • NEVER test with production (https://api.ashortstayinhell.com:5562)")
        print("   • Database: 'knowledge_base' | Use 'staging' not 'production_api_service'")
        print("   • Agent memory persists across sessions - check tasks before starting new work")

        # Show high priority tasks
        conn = sqlite3.connect(memory.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT title, description, priority FROM agent_tasks
            WHERE status IN ('pending', 'in_progress')
            ORDER BY priority DESC, created_time ASC
            LIMIT 3
        ''')
        priority_tasks = cursor.fetchall()
        conn.close()

        if priority_tasks:
            print("\n⚡ HIGH PRIORITY TASKS:")
            for i, (title, desc, priority) in enumerate(priority_tasks, 1):
                print(f"   {i}. [{priority}] {title}")
                if desc and len(desc) > 0:
                    print(f"      {desc[:80]}...")

        print("\n✅ Claude Code ready with full project context!")
        print("🚀" * 30 + "\n")

        return True

    except Exception as e:
        print(f"❌ Startup check failed: {e}")
        print("⚠️  Agent memory may not be available")
        return False

# Auto-run when imported
if __name__ != "__main__":
    claude_startup_check()

# Also run when executed directly
if __name__ == "__main__":
    claude_startup_check()