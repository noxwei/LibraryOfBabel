#!/usr/bin/env python3
"""
🚀 Agent Bulletin Board Setup
Quick setup script for the agent social network system
"""

import os
import subprocess
from pathlib import Path
from bulletin_system import AgentBulletinSystem, create_git_hook

def setup_bulletin_board():
    """Set up the complete bulletin board system"""
    print("🤖 Setting up Agent Bulletin Board System...")
    
    # Initialize the system
    system = AgentBulletinSystem()
    print("✅ Agent social network initialized")
    
    # Create git hook
    hook_path = Path(".git/hooks/pre-commit")
    hook_content = create_git_hook()
    
    # Make sure hooks directory exists
    hook_path.parent.mkdir(exist_ok=True)
    
    # Write the hook
    with open(hook_path, 'w') as f:
        f.write(hook_content)
    
    # Make it executable
    os.chmod(hook_path, 0o755)
    print("✅ Git hook installed for automatic bulletin messages")
    
    # Generate some test activity
    test_files = [
        "docs/test_research.md",
        "agents/security/test_security.md", 
        "agents/qa/test_qa.md"
    ]
    
    print("\n🎭 Generating initial agent activity...")
    for test_file in test_files:
        message = system.generate_bulletin_message(test_file)
        print(f"  {message}")
    
    print("\n📊 Agent Network Status:")
    stats = system.get_agent_stats()
    for agent, stat in stats.items():
        agent_name = system.agents["agents"][agent]["name"]
        print(f"  {agent_name}: {stat['messages']} messages")
    
    print("\n🎉 Bulletin Board System Ready!")
    print("Now every new .md file will automatically get agent commentary!")
    print("The agents are watching... 👁️")

if __name__ == "__main__":
    setup_bulletin_board()