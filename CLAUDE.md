# LibraryOfBabel - Claude Code Configuration

## 🧠 STARTUP REQUIREMENT
**ALWAYS RUN ON CLAUDE CODE START**: `python CLAUDE_STARTUP.py`
This loads agent memory, session continuity, and project context.

## Production Safety
- This is the main Bash(./production_api_service.sh restart to restart the api restart on public site.
- never test with produciton website https://api.ashortstayinhell.com:5562
- when testing with local host, do not use 5562
- our database db is called knowledge_base
- never use production_api_service for testing, thats how to restart production. use staging

## Agent Memory System
- File-based persistent memory: `claude_agent_memory.db`
- Session continuity across Claude Code restarts
- Task tracking and agent coordination
- LibraryOfBabel metrics and state persistence
- when starting start CLAUDE_STARTUP.py