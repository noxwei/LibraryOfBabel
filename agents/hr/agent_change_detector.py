#!/usr/bin/env python3
"""
🔍 Agent Change Detection System
===============================

Automatically detects when agents are created, deleted, or modified.
Linda Zhang (张丽娜) tracks all workforce changes in real-time.
"""

import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List
import hashlib
import json

class AgentChangeDetector:
    """
    Monitors agent directory for changes and logs workforce modifications
    """
    
    def __init__(self, hr_manager=None):
        self.agents_dir = Path("agents")
        self.hr = hr_manager
        self.last_scan = {}
        self.known_agents = set()
        
    def scan_for_agent_changes(self) -> Dict[str, List[str]]:
        """Scan for agent file changes and categorize them"""
        changes = {
            "new_agents": [],
            "deleted_agents": [],
            "modified_agents": [],
            "renamed_agents": []
        }
        
        current_agents = self._get_current_agents()
        
        # Detect new agents
        new_agents = current_agents - self.known_agents
        for agent in new_agents:
            changes["new_agents"].append(agent)
            if self.hr:
                self._log_agent_creation(agent)
        
        # Detect deleted agents
        deleted_agents = self.known_agents - current_agents
        for agent in deleted_agents:
            changes["deleted_agents"].append(agent)
            if self.hr:
                self._log_agent_deletion(agent)
        
        # Detect modified agents
        for agent in current_agents.intersection(self.known_agents):
            if self._agent_was_modified(agent):
                changes["modified_agents"].append(agent)
                if self.hr:
                    self._log_agent_modification(agent)
        
        # Update tracking
        self.known_agents = current_agents
        
        return changes
    
    def _get_current_agents(self) -> Set[str]:
        """Get list of current agent files"""
        agents = set()
        
        if self.agents_dir.exists():
            for category_dir in self.agents_dir.iterdir():
                if category_dir.is_dir() and not category_dir.name.startswith('.'):
                    for agent_file in category_dir.glob("*_agent.py"):
                        agent_name = f"{category_dir.name}/{agent_file.stem}"
                        agents.add(agent_name)
        
        return agents
    
    def _agent_was_modified(self, agent_path: str) -> bool:
        """Check if agent file was modified since last scan"""
        try:
            file_path = self.agents_dir / f"{agent_path}.py"
            if not file_path.exists():
                return False
            
            # Get file modification time and content hash
            mtime = file_path.stat().st_mtime
            with open(file_path, 'rb') as f:
                content_hash = hashlib.md5(f.read()).hexdigest()
            
            # Check against last known state
            last_state = self.last_scan.get(agent_path, {})
            last_mtime = last_state.get('mtime', 0)
            last_hash = last_state.get('hash', '')
            
            # Update tracking
            self.last_scan[agent_path] = {
                'mtime': mtime,
                'hash': content_hash
            }
            
            return mtime != last_mtime or content_hash != last_hash
            
        except Exception as e:
            print(f"⚠️  Could not check modification for {agent_path}: {e}")
            return False
    
    def _log_agent_creation(self, agent_path: str):
        """Log new agent creation to HR system"""
        try:
            category, agent_name = agent_path.split('/', 1)
            
            # Extract agent info from file
            agent_info = self._extract_agent_info(agent_path)
            
            print(f"📝 New agent detected: {agent_name} ({category})")
            
            # Log to HR system
            request_id = self.hr.log_user_request(
                request_type="agent_creation_detected",
                request_content=f"New agent file created: {agent_path}",
                user_session="auto_detection"
            )
            
            self.hr.log_agent_interaction(
                agent_name="hr_agent_linda",
                action="new_agent_file_detected",
                success=True,
                duration_ms=100.0,
                details=f"Detected new agent: {agent_name} in {category} category - {agent_info.get('description', 'No description')}",
                request_id=request_id
            )
            
        except Exception as e:
            print(f"❌ Failed to log agent creation for {agent_path}: {e}")
    
    def _log_agent_deletion(self, agent_path: str):
        """Log agent deletion to HR system"""
        try:
            category, agent_name = agent_path.split('/', 1)
            
            print(f"🗑️  Agent deleted: {agent_name} ({category})")
            
            # Log to HR system
            request_id = self.hr.log_user_request(
                request_type="agent_deletion_detected",
                request_content=f"Agent file deleted: {agent_path}",
                user_session="auto_detection"
            )
            
            self.hr.log_agent_interaction(
                agent_name="hr_agent_linda", 
                action="agent_file_deletion_detected",
                success=True,
                duration_ms=150.0,
                details=f"Detected agent deletion: {agent_name} from {category} category",
                request_id=request_id
            )
            
        except Exception as e:
            print(f"❌ Failed to log agent deletion for {agent_path}: {e}")
    
    def _log_agent_modification(self, agent_path: str):
        """Log agent modification to HR system"""
        try:
            category, agent_name = agent_path.split('/', 1)
            
            print(f"✏️  Agent modified: {agent_name} ({category})")
            
            # Log to HR system
            self.hr.log_agent_interaction(
                agent_name="hr_agent_linda",
                action="agent_file_modification_detected", 
                success=True,
                duration_ms=75.0,
                details=f"Detected modification to agent: {agent_name} in {category} category"
            )
            
        except Exception as e:
            print(f"❌ Failed to log agent modification for {agent_path}: {e}")
    
    def _extract_agent_info(self, agent_path: str) -> Dict[str, str]:
        """Extract basic info from agent file"""
        info = {"description": "Unknown agent", "capabilities": []}
        
        try:
            file_path = self.agents_dir / f"{agent_path}.py"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Look for docstring description
                if '"""' in content:
                    docstring = content.split('"""')[1].strip()
                    first_line = docstring.split('\n')[0].strip()
                    if first_line:
                        info["description"] = first_line[:100]
                
                # Look for class definition
                lines = content.split('\n')
                for line in lines:
                    if line.strip().startswith('class ') and 'Agent' in line:
                        info["type"] = "agent_class"
                        break
                
        except Exception as e:
            print(f"⚠️  Could not extract info from {agent_path}: {e}")
        
        return info

def auto_detect_agent_changes():
    """Standalone function to detect and log agent changes"""
    try:
        # Import HR system
        import sys
        sys.path.append(os.path.dirname(__file__))
        from hr_agent import HRAgent
        
        hr = HRAgent()
        detector = AgentChangeDetector(hr)
        
        print("🔍 Scanning for agent changes...")
        changes = detector.scan_for_agent_changes()
        
        total_changes = sum(len(change_list) for change_list in changes.values())
        
        if total_changes > 0:
            print(f"\n📊 Agent Changes Detected:")
            for change_type, agents in changes.items():
                if agents:
                    print(f"   {change_type}: {len(agents)} agents")
                    for agent in agents:
                        print(f"      • {agent}")
        else:
            print("✅ No agent changes detected")
        
        return changes
        
    except Exception as e:
        print(f"❌ Agent change detection failed: {e}")
        return {}

if __name__ == "__main__":
    auto_detect_agent_changes()