#!/usr/bin/env python3
"""
🧠 Claude Agent Memory System - LibraryOfBabel
==============================================

File-based persistent memory system for Claude Code agents.
Automatically initializes on Claude Code startup to provide:
- Session continuity across restarts
- Agent handoff coordination
- Task persistence and progress tracking
- Context preservation for 106K+ chunk processing system

Usage:
- Auto-loads when Claude Code starts
- Persists agent state to SQLite database
- Provides memory APIs for agent coordination
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

class ClaudeAgentMemory:
    """File-based persistent memory for Claude agents"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in LibraryOfBabel project root
            project_root = Path(__file__).parent
            db_path = project_root / "claude_agent_memory.db"

        self.db_path = db_path
        self.session_id = str(uuid.uuid4())
        self.startup_time = datetime.now()

        # Initialize database and load memory
        self._init_database()
        self._load_startup_context()

    def _init_database(self):
        """Initialize SQLite database with agent memory schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Agent sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TEXT NOT NULL,
                end_time TEXT,
                context_summary TEXT,
                current_tasks TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Agent memory entries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id)
            )
        ''')

        # Task tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_tasks (
                task_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                created_time TEXT NOT NULL,
                updated_time TEXT NOT NULL,
                completed_time TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id)
            )
        ''')

        # Agent handoffs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_handoffs (
                handoff_id TEXT PRIMARY KEY,
                from_session TEXT NOT NULL,
                to_session TEXT,
                handoff_time TEXT NOT NULL,
                context TEXT NOT NULL,
                pending_tasks TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')

        # LibraryOfBabel specific metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS library_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                chunks_processed INTEGER,
                books_count INTEGER,
                success_rate REAL,
                active_models TEXT,
                database_size_gb REAL,
                notes TEXT,
                FOREIGN KEY (session_id) REFERENCES agent_sessions (session_id)
            )
        ''')

        conn.commit()
        conn.close()

        print(f"🧠 Agent memory database initialized: {self.db_path}")

    def _load_startup_context(self):
        """Load context from previous sessions on startup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Register current session
        cursor.execute('''
            INSERT INTO agent_sessions (session_id, start_time, status)
            VALUES (?, ?, 'active')
        ''', (self.session_id, self.startup_time.isoformat()))

        # Get recent context (last 24 hours)
        yesterday = datetime.now() - timedelta(hours=24)
        cursor.execute('''
            SELECT session_id, start_time, context_summary, current_tasks
            FROM agent_sessions
            WHERE start_time > ?
            ORDER BY start_time DESC
            LIMIT 5
        ''', (yesterday.isoformat(),))

        recent_sessions = cursor.fetchall()

        # Get pending tasks from recent sessions
        cursor.execute('''
            SELECT task_id, title, description, status, priority, created_time
            FROM agent_tasks
            WHERE status IN ('pending', 'in_progress')
            AND session_id IN (
                SELECT session_id FROM agent_sessions
                WHERE start_time > ?
            )
            ORDER BY priority DESC, created_time DESC
            LIMIT 10
        ''', (yesterday.isoformat(),))

        pending_tasks = cursor.fetchall()

        # Get latest LibraryOfBabel metrics
        cursor.execute('''
            SELECT chunks_processed, books_count, success_rate, active_models, database_size_gb, notes
            FROM library_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        ''')

        latest_metrics = cursor.fetchone()

        conn.commit()
        conn.close()

        # Display startup context
        print("\n" + "="*60)
        print("🧠 CLAUDE AGENT MEMORY - STARTUP CONTEXT")
        print("="*60)
        print(f"📅 Session ID: {self.session_id}")
        print(f"⏰ Startup Time: {self.startup_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if recent_sessions:
            print(f"\n📋 Recent Sessions ({len(recent_sessions)}):")
            for session in recent_sessions[:3]:
                session_id, start_time, summary, tasks = session
                print(f"  • {start_time[:16]} - {session_id[:8]}...")
                if summary:
                    print(f"    Summary: {summary[:80]}...")

        if pending_tasks:
            print(f"\n⚡ Pending Tasks ({len(pending_tasks)}):")
            for task in pending_tasks[:5]:
                task_id, title, desc, status, priority, created = task
                print(f"  • [{status.upper()}] {title}")
                if desc:
                    print(f"    {desc[:60]}...")

        if latest_metrics:
            chunks, books, rate, models, size, notes = latest_metrics
            print(f"\n📊 LibraryOfBabel Metrics (Latest):")
            print(f"  • Chunks: {chunks:,} | Books: {books:,} | Success: {rate:.2%}")
            print(f"  • Models: {models} | DB Size: {size:.1f}GB")
            if notes:
                print(f"  • Notes: {notes[:60]}...")

        print("="*60)
        print("🚀 Ready for agent coordination and task execution!")
        print("="*60 + "\n")

    def store_memory(self, key: str, value: Any, memory_type: str = "context", metadata: Dict = None):
        """Store a memory entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO agent_memory (session_id, timestamp, memory_type, key, value, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            datetime.now().isoformat(),
            memory_type,
            key,
            json.dumps(value),
            json.dumps(metadata) if metadata else None
        ))

        conn.commit()
        conn.close()

    def get_memory(self, key: str, memory_type: str = "context") -> Optional[Any]:
        """Retrieve a memory entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT value FROM agent_memory
            WHERE key = ? AND memory_type = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (key, memory_type))

        result = cursor.fetchone()
        conn.close()

        if result:
            return json.loads(result[0])
        return None

    def add_task(self, title: str, description: str = "", priority: int = 1, metadata: Dict = None) -> str:
        """Add a new task"""
        task_id = str(uuid.uuid4())

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO agent_tasks (task_id, session_id, title, description, status, priority, created_time, updated_time, metadata)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        ''', (task_id, self.session_id, title, description, priority, now, now, json.dumps(metadata) if metadata else None))

        conn.commit()
        conn.close()

        print(f"📝 Task added: {title}")
        return task_id

    def update_task_status(self, task_id: str, status: str, notes: str = ""):
        """Update task status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE agent_tasks
            SET status = ?, updated_time = ?, completed_time = ?
            WHERE task_id = ?
        ''', (
            status,
            datetime.now().isoformat(),
            datetime.now().isoformat() if status == 'completed' else None,
            task_id
        ))

        conn.commit()
        conn.close()

        if notes:
            self.store_memory(f"task_notes_{task_id}", notes, "task_update")

    def record_library_metrics(self, chunks_processed: int, books_count: int, success_rate: float,
                             active_models: str, database_size_gb: float, notes: str = ""):
        """Record current LibraryOfBabel metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO library_metrics (session_id, timestamp, chunks_processed, books_count,
                                       success_rate, active_models, database_size_gb, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.session_id,
            datetime.now().isoformat(),
            chunks_processed,
            books_count,
            success_rate,
            active_models,
            database_size_gb,
            notes
        ))

        conn.commit()
        conn.close()

    def close_session(self, summary: str = ""):
        """Close current session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE agent_sessions
            SET end_time = ?, context_summary = ?, status = 'completed'
            WHERE session_id = ?
        ''', (datetime.now().isoformat(), summary, self.session_id))

        conn.commit()
        conn.close()

# Global instance - auto-initializes when module loads
_agent_memory = None

def get_agent_memory() -> ClaudeAgentMemory:
    """Get the global agent memory instance"""
    global _agent_memory
    if _agent_memory is None:
        _agent_memory = ClaudeAgentMemory()
    return _agent_memory

# Auto-initialize on import
if __name__ != "__main__":
    # This runs when the module is imported
    try:
        _agent_memory = ClaudeAgentMemory()

        # Record current LibraryOfBabel state
        _agent_memory.record_library_metrics(
            chunks_processed=106508,
            books_count=4932,
            success_rate=0.9999,
            active_models="BGE-M3, MxBAI, Nomic",
            database_size_gb=112.0,
            notes="Post-cleanup state after book verification and chunking analysis"
        )

        # Add key pending tasks
        _agent_memory.add_task(
            "Fix catastrophic chunking algorithm",
            "Replace word-based chunking with token-based chunking (256-2048 tokens) to fix Game of Thrones 5.4M word single chunk issue",
            priority=1
        )

        _agent_memory.add_task(
            "Complete embedding strategy migration",
            "Implement new embedding models (Qwen3-8B, nomic-v2-moe) to replace incomplete MxBAI and Nomic embeddings",
            priority=2
        )

    except Exception as e:
        print(f"⚠️ Agent memory initialization failed: {e}")

if __name__ == "__main__":
    # Test the system
    memory = ClaudeAgentMemory()

    # Test memory storage
    memory.store_memory("test_key", {"test": "value"}, "test")
    result = memory.get_memory("test_key", "test")
    print(f"Memory test: {result}")

    # Test task management
    task_id = memory.add_task("Test task", "This is a test task", priority=1)
    memory.update_task_status(task_id, "in_progress", "Starting work on test task")
    memory.update_task_status(task_id, "completed", "Test task finished successfully")

    print("✅ Agent memory system test completed")