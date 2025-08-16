# API Server Startup Guide

## Quick Start

To start the LibraryOfBabel API server:

```bash
cd /Users/weixiangzhang/Local_Dev/LibraryOfBabel
./start_api_daemon.sh
```

## What the Script Does

The `start_api_daemon.sh` script:
- Sets working directory to project root
- Configures environment variables:
  - `PYTHONPATH`: Points to src directory
  - `API_KEY`: Authentication key
  - `API_PORT`: 5562
  - `API_HOST`: 0.0.0.0 (all interfaces)
  - `OLLAMA_MODEL`: llama3.2:3b
- Launches `src/api/standardized_production_api.py`

## Check If Running

```bash
ps aux | grep standardized_production_api.py
```

## Production URL

Once running, the API is accessible at:
`https://api.ashortstayinhell.com:5562`

## Environment Requirements

- Python 3.13+ (homebrew installation)
- PostgreSQL with project database
- Ollama with llama3.2:3b model
- All project dependencies installed

## Troubleshooting

If the script fails:
1. Check Python path: `/opt/homebrew/bin/python3`
2. Verify database connectivity
3. Ensure Ollama is running with required model
4. Check port 5562 is available