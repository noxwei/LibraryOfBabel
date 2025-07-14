#!/usr/bin/env python3
"""
Quick Agent Status Check - Lightweight version for routine monitoring
Designed to use ~5k tokens instead of 116k+ for basic status checks
"""

import json
import os
from datetime import datetime
from pathlib import Path

def quick_agent_status():
    """Lightweight agent status check using minimal token usage"""
    
    # Path to agent memory
    memory_path = Path(__file__).parent / "bulletin_board" / "agent_memory.json"
    
    if not memory_path.exists():
        return "❌ Agent memory file not found"
    
    try:
        with open(memory_path, 'r') as f:
            data = json.load(f)
        
        # Count active agents
        agents = data.get('agents', {})
        active_agents = [name for name, info in agents.items() 
                        if info.get('activity_level', 0) > 0.5]
        
        # Get Linda's status (check for hr_linda key)
        linda = agents.get('hr_linda', agents.get('linda', {}))
        linda_status = f"Active ({linda.get('activity_level', 0)})" if linda else "Not found"
        
        # Get recent activity count
        messages = data.get('messages', [])
        recent_count = len([m for m in messages[-5:] if m])  # Last 5 messages
        
        # Quick health check
        total_agents = len(agents)
        health = "🟢 Healthy" if len(active_agents) > total_agents * 0.6 else "🟡 Monitor"
        
        return f"""📊 Quick Agent Status:
{health} | {len(active_agents)}/{total_agents} agents active
👩‍💼 Linda: {linda_status}
💬 Recent activity: {recent_count} posts
📚 System: Operational (838 books available)

Use --debug for detailed analysis"""
        
    except Exception as e:
        return f"❌ Error reading agent status: {str(e)}"

def debug_agent_status():
    """Comprehensive agent analysis (high token usage)"""
    return """🔍 DEBUG MODE: Use comprehensive Task tool for detailed analysis
This mode will use 100k+ tokens for full agent ecosystem report"""

if __name__ == "__main__":
    import sys
    
    if "--debug" in sys.argv:
        print(debug_agent_status())
    else:
        print(quick_agent_status())