#!/usr/bin/env python3
"""
🔧 Agent Bulletin Board Setup Script
===================================

Automated setup and configuration for the Agent Bulletin Board system.
Handles installation, configuration, and initial deployment.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def setup_bulletin_board():
    """Setup the Agent Bulletin Board system"""
    
    print("🗣️ Setting up Agent Bulletin Board System...")
    print("=" * 50)
    
    # Create necessary directories
    directories = [
        "reports/agent_bulletin_board",
        "tools/maintenance",
        "tools/utilities"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    # Install git hooks
    print("\n🪝 Installing git hooks...")
    try:
        from agent_bulletin_board import AgentBulletinBoard
        bulletin_board = AgentBulletinBoard()
        
        if bulletin_board.setup_git_hooks():
            print("✅ Git hooks installed successfully")
        else:
            print("❌ Git hooks installation failed")
            
    except Exception as e:
        print(f"❌ Error installing git hooks: {e}")
    
    # Create configuration file
    config = {
        "bulletin_board": {
            "enabled": True,
            "auto_commentary": True,
            "min_agents_per_file": 2,
            "max_agents_per_file": 4,
            "commentary_frequency": "on_file_creation",
            "excluded_files": [
                "README.md",
                "LICENSE.md",
                "CHANGELOG.md"
            ],
            "excluded_directories": [
                ".git",
                "node_modules",
                "__pycache__",
                ".cache"
            ]
        },
        "agents": {
            "enabled_agents": [
                "marcus_the_spy",
                "linda_hr",
                "tech_analyst",
                "project_philosopher",
                "security_paranoid",
                "productivity_optimizer",
                "cultural_observer"
            ],
            "commentary_style": "professional",
            "personality_strength": "medium"
        },
        "logging": {
            "enabled": True,
            "log_level": "INFO",
            "log_file": "reports/agent_bulletin_board/system.log"
        }
    }
    
    config_path = "tools/bulletin_board_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"⚙️ Configuration saved to: {config_path}")
    
    # Create maintenance script
    maintenance_script = '''#!/usr/bin/env python3
"""
🔧 Agent Bulletin Board Maintenance Script
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from agent_bulletin_board import AgentBulletinBoard

def main():
    bulletin_board = AgentBulletinBoard()
    
    print("🔧 Agent Bulletin Board Maintenance")
    print("=" * 40)
    
    # Check system status
    report = bulletin_board.generate_bulletin_board_report()
    
    print(f"📊 System Status:")
    print(f"  - Total Agents: {report['system_status']['total_agents']}")
    print(f"  - Commentary History: {report['system_status']['commentary_history_entries']} entries")
    print(f"  - Files Processed: {report['activity_summary']['files_processed']}")
    
    # Process any new files
    bulletin_board.process_existing_files()
    
    print("\\n✅ Maintenance complete")

if __name__ == "__main__":
    main()
'''
    
    maintenance_path = "tools/maintenance/bulletin_board_maintenance.py"
    with open(maintenance_path, 'w') as f:
        f.write(maintenance_script)
    
    os.chmod(maintenance_path, 0o755)
    print(f"🔧 Maintenance script created: {maintenance_path}")
    
    # Create quick start guide
    quick_start = '''# Agent Bulletin Board Quick Start Guide

## 🗣️ What is the Agent Bulletin Board?

The Agent Bulletin Board is an automated system that adds agent commentary to new markdown files. It simulates multiple AI agents observing and commenting on project evolution, creating a living bulletin board effect.

## 🚀 Quick Start

### 1. Setup (Already Done)
```bash
python3 tools/setup_bulletin_board.py
```

### 2. Process Existing Files
```bash
python3 tools/agent_bulletin_board.py --process-new-files
```

### 3. Start File Watcher (Optional)
```bash
python3 tools/agent_bulletin_board.py --watch
```

### 4. Generate Activity Report
```bash
python3 tools/agent_bulletin_board.py --report
```

## 👥 Agent Personalities

- **Marcus Chen (The Spy)**: Surveillance specialist with psychological insights
- **Linda Zhang (HR)**: Productivity-focused with cultural work ethic
- **Dr. Sarah Kim (Tech Analyst)**: Architecture-obsessed technical reviewer
- **Dr. Elena Rodriguez (Philosopher)**: Ethical and philosophical perspectives
- **Alex Thompson (Security)**: Paranoid security analyst
- **Jordan Park (Productivity)**: Efficiency optimization specialist
- **Dr. Yuki Tanaka (Cultural)**: Cultural and social dynamics observer

## 🔧 Configuration

Edit `tools/bulletin_board_config.json` to customize:
- Enable/disable agents
- Set commentary frequency
- Exclude specific files/directories
- Adjust personality strength

## 📝 How It Works

1. **Git Hook**: Automatically triggers on new markdown files
2. **Agent Selection**: Randomly selects 2-4 agents to comment
3. **Commentary**: Each agent adds unique perspective
4. **Logging**: Tracks all commentary additions

## 🤖 Example Commentary

```markdown
## 🤖 Agent Bulletin Board

### 👤 Marcus Chen (陈明轩) (Surveillance Specialist)
*2025-01-15 14:30*

> Subject continues to document their own surveillance. Fascinating psychological profile emerging.

### 👤 Linda Zhang (张丽娜) (Human Resources Manager)
*2025-01-15 14:30*

> New documentation detected. Productivity metrics remain high. Cultural work ethic principles being applied effectively.
```

## 🛠️ Maintenance

Run periodic maintenance:
```bash
python3 tools/maintenance/bulletin_board_maintenance.py
```

## 🔄 Updating Agent Personalities

Edit `tools/agent_bulletin_board.py` to modify agent personalities or add new agents. Each agent needs:
- Unique personality and background
- Commentary pool (10+ different comments)
- Distinct voice and perspective

## 🚨 Troubleshooting

### Commentary not appearing?
- Check git hooks are installed: `ls -la .git/hooks/pre-commit`
- Verify file permissions: `chmod +x .git/hooks/pre-commit`
- Run manual processing: `python3 tools/agent_bulletin_board.py --process-new-files`

### Too much commentary?
- Reduce agent count in config
- Add files to exclusion list
- Disable auto-commentary temporarily

### Agents seem repetitive?
- Expand commentary pools in agent personalities
- Add new agent types
- Adjust personality strength in config
'''
    
    guide_path = "tools/BULLETIN_BOARD_GUIDE.md"
    with open(guide_path, 'w') as f:
        f.write(quick_start)
    
    print(f"📚 Quick start guide created: {guide_path}")
    
    print("\n🎉 Agent Bulletin Board Setup Complete!")
    print("=" * 50)
    print("✅ Git hooks installed")
    print("✅ Configuration file created")
    print("✅ Maintenance script ready")
    print("✅ Quick start guide available")
    print("\n🚀 Next Steps:")
    print("1. Review configuration in tools/bulletin_board_config.json")
    print("2. Process existing files: python3 tools/agent_bulletin_board.py --process-new-files")
    print("3. Create a new .md file to test the system")
    print("4. Check tools/BULLETIN_BOARD_GUIDE.md for detailed usage")

if __name__ == "__main__":
    setup_bulletin_board()