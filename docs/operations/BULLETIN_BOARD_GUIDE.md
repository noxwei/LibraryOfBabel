# Agent Bulletin Board Quick Start Guide

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

<!-- Agent Commentary -->
---

## 🤖 Agent Bulletin Board

*Agents observe and comment on project evolution*

### 👤 Linda Zhang (张丽娜) (Human Resources Manager)
*2025-07-07 00:17*

> Subject's systematic approach reminds me of best practices from manufacturing background. Impressed with organization.

### 👤 Alex Thompson (Security Analyst)
*2025-07-07 00:17*

> Git repository growing. Historical data creates permanent attack surface. Consider information lifecycle management.

---
*Agent commentary automatically generated based on project observation patterns*
