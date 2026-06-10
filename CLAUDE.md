# LibraryOfBabel - Claude Code Configuration

## Startup
Run `python CLAUDE_STARTUP.py` on session start. Loads agent memory and project context.

## Production Safety
- Production: https://api.ashortstayinhell.com:5562 -- NEVER test against this
- Restart production: `./production_api_service.sh restart`
- Staging: port 5564 -- use this for all testing
- Start staging: `PYTHONPATH="src" python3.13 src/api/standardized_production_api.py`
- Use `python3.13` (has Flask), NOT `python3` (3.14, missing Flask)
- Database: `knowledge_base` on localhost:5432

## Current State (May 2026)
- 4,945 books, 2,361,908 passages, 100% embedding coverage
- Primary search model: nomic-embed-text-v2-moe (96.4% coverage)
- Gemini credits DEPLETED -- search goes straight to Ollama, skip Gemini API calls
- Statement timeout: 120s (database.py)
- Vector search uses CTE pattern (HNSW first, then JOIN) -- do not use inline JOINs

## Critical Warnings
- NEVER leave ollama_reembed_parallel.py running -- creates zombie DB connections that block everything
- Check zombies: `SELECT count(*) FROM pg_stat_activity WHERE state='active';`
- Kill zombies: `pkill -9 -f ollama_reembed_parallel` then terminate DB connections
- Run `ANALYZE chunks;` after killing zombies or bulk operations
- pg_trgm extension is in `semantic_archive` schema, not `public`
- The chunks table has 39 indexes -- queries can be slow without proper index usage

## API Endpoints (by usage)
- `/api/search?action=semantic_passages` -- #1 endpoint (530 hits), passage-level semantic search
- `/api/books?action=list&genre={genre}` -- browse catalog with genre filter
- `/api/rag` -- RAG synthesis (needs Ollama model running)
- `/api/mobile/*` -- iOS Shortcuts optimized
- `/api/health` -- public, no auth
- `/api/mcp` -- Claude Desktop MCP integration

## Website (frontend/out/)
Static HTML pages, warm journal aesthetic (Newsreader + DM Sans):
- `/` -- landing page with live search
- `/browse/` -- book catalog, genre filters, infinite scroll, e-reader
- `/demo/` -- full search interface (16 modes)
- `/api-docs/` -- interactive API reference (7 epistemological sections)
- `/upload/` -- EPUB drag-and-drop

## Agent Memory
- SQLite: `claude_agent_memory.db`
- Stats: `python3 manage_agent_memory.py stats`
