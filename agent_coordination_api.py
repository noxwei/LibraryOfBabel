#!/usr/bin/env python3
"""
🤝 Agent Coordination API - LibraryOfBabel
==========================================

Coordination layer for Claude agents to share context, handoff tasks,
and maintain project continuity across sessions and interruptions.

Features:
- Agent handoff protocol
- Context transfer between sessions
- Task delegation and status tracking
- Inter-agent communication logs
"""

from claude_agent_memory import get_agent_memory
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

class AgentCoordinator:
    """Manages coordination between Claude agents"""

    def __init__(self):
        self.memory = get_agent_memory()
        self.agent_id = self.memory.session_id

    def request_handoff(self, context: Dict, pending_tasks: List[str] = None) -> str:
        """Request handoff to next agent with context"""
        handoff_id = str(uuid.uuid4())

        # Store handoff request
        import sqlite3
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO agent_handoffs (handoff_id, from_session, handoff_time, context, pending_tasks, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (
            handoff_id,
            self.agent_id,
            datetime.now().isoformat(),
            json.dumps(context),
            json.dumps(pending_tasks) if pending_tasks else None
        ))

        conn.commit()
        conn.close()

        # Store handoff context in memory
        self.memory.store_memory(f"handoff_{handoff_id}", {
            "context": context,
            "pending_tasks": pending_tasks,
            "status": "handoff_requested",
            "timestamp": datetime.now().isoformat()
        }, "handoff")

        print(f"📤 Handoff requested: {handoff_id}")
        print(f"   Context keys: {list(context.keys())}")
        if pending_tasks:
            print(f"   Pending tasks: {len(pending_tasks)}")

        return handoff_id

    def accept_handoff(self, handoff_id: str) -> Optional[Dict]:
        """Accept and process a handoff request"""
        import sqlite3
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()

        # Get handoff details
        cursor.execute('''
            SELECT from_session, context, pending_tasks, status
            FROM agent_handoffs
            WHERE handoff_id = ?
        ''', (handoff_id,))

        result = cursor.fetchone()
        if not result:
            return None

        from_session, context_json, tasks_json, status = result
        if status != 'pending':
            return None

        # Mark as accepted
        cursor.execute('''
            UPDATE agent_handoffs
            SET to_session = ?, status = 'accepted'
            WHERE handoff_id = ?
        ''', (self.agent_id, handoff_id))

        conn.commit()
        conn.close()

        # Parse handoff data
        context = json.loads(context_json)
        pending_tasks = json.loads(tasks_json) if tasks_json else []

        # Store received context
        self.memory.store_memory(f"received_handoff_{handoff_id}", {
            "from_session": from_session,
            "context": context,
            "pending_tasks": pending_tasks,
            "accepted_time": datetime.now().isoformat()
        }, "handoff_received")

        print(f"📥 Handoff accepted: {handoff_id}")
        print(f"   From session: {from_session[:8]}...")
        print(f"   Received context: {list(context.keys())}")

        return {
            "handoff_id": handoff_id,
            "context": context,
            "pending_tasks": pending_tasks,
            "from_session": from_session
        }

    def get_pending_handoffs(self) -> List[Dict]:
        """Get all pending handoffs"""
        import sqlite3
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT handoff_id, from_session, handoff_time, context, pending_tasks
            FROM agent_handoffs
            WHERE status = 'pending'
            ORDER BY handoff_time DESC
        ''')

        handoffs = []
        for row in cursor.fetchall():
            handoff_id, from_session, time, context_json, tasks_json = row
            handoffs.append({
                "handoff_id": handoff_id,
                "from_session": from_session,
                "handoff_time": time,
                "context": json.loads(context_json),
                "pending_tasks": json.loads(tasks_json) if tasks_json else []
            })

        conn.close()
        return handoffs

    def log_agent_action(self, action: str, details: Dict = None):
        """Log agent action for coordination tracking"""
        self.memory.store_memory(f"action_{datetime.now().isoformat()}", {
            "action": action,
            "details": details or {},
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat()
        }, "agent_action")

    def get_agent_history(self, limit: int = 10) -> List[Dict]:
        """Get recent agent actions for context"""
        import sqlite3
        conn = sqlite3.connect(self.memory.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT timestamp, key, value FROM agent_memory
            WHERE memory_type = 'agent_action'
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

        actions = []
        for timestamp, key, value_json in cursor.fetchall():
            value = json.loads(value_json)
            actions.append({
                "timestamp": timestamp,
                "action": value.get("action"),
                "details": value.get("details", {}),
                "agent_id": value.get("agent_id")
            })

        conn.close()
        return actions

# Helper functions for common coordination patterns
def claude_session_handoff(summary: str, current_tasks: List[str] = None):
    """Standard handoff when Claude session ends"""
    coordinator = AgentCoordinator()

    context = {
        "session_summary": summary,
        "end_time": datetime.now().isoformat(),
        "project_state": "LibraryOfBabel - 106K+ chunks, chunking algorithm needs fixing",
        "database_status": "knowledge_base - 4,932 books, 112GB",
        "critical_tasks": current_tasks or []
    }

    return coordinator.request_handoff(context, current_tasks)

def claude_session_start():
    """Check for handoffs when Claude starts"""
    coordinator = AgentCoordinator()

    pending_handoffs = coordinator.get_pending_handoffs()
    if pending_handoffs:
        print(f"\n🔄 Found {len(pending_handoffs)} pending handoffs:")
        for handoff in pending_handoffs:
            print(f"   • {handoff['handoff_id'][:8]}... from {handoff['from_session'][:8]}...")
            print(f"     Context: {list(handoff['context'].keys())}")

        # Auto-accept the most recent handoff
        latest_handoff = pending_handoffs[0]
        return coordinator.accept_handoff(latest_handoff["handoff_id"])

    return None

if __name__ == "__main__":
    # Test coordination system
    coordinator = AgentCoordinator()

    # Test handoff
    handoff_id = coordinator.request_handoff({
        "test_context": "This is a test handoff",
        "current_work": "Testing agent coordination"
    }, ["task1", "task2"])

    # Test acceptance
    result = coordinator.accept_handoff(handoff_id)
    print(f"Handoff result: {result}")

    # Test action logging
    coordinator.log_agent_action("test_action", {"test": "details"})

    print("✅ Agent coordination system test completed")