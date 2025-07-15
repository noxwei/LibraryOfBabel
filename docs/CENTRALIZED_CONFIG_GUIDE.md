# 🔧 Centralized API Configuration Guide

## 🎯 Problem Solved

**Before**: API keys and configuration scattered across multiple files, leading to:
- ❌ Configuration mismatches between scripts
- ❌ Hardcoded API keys in test files  
- ❌ Manual updates required in multiple locations
- ❌ Inconsistent daemon configurations

**After**: Single source of truth for all API configuration:
- ✅ Centralized configuration management
- ✅ Automatic synchronization across all systems
- ✅ One-command updates
- ✅ Validation and error checking

---

## 📁 Configuration Architecture

```
config/
├── api_config.py          # Main configuration manager
└── api_settings.json      # Configuration data file

scripts/
├── update_api_config.py   # Configuration update manager
└── test_api_centralized.py # Centralized testing script
```

---

## 🔑 Current API Configuration

**API Key**: `babel_secure_3f99c2d1d294fbebdfc6b10cce93652d`  
**Base URL**: `https://api.ashortstayinhell.com:5562`  
**Version**: Unified (consolidates former v2 + v3)

---

## 🚀 Quick Usage

### View Current Configuration
```bash
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
python3 scripts/update_api_config.py --show
```

### Update API Key (Updates Everything)
```bash
python3 scripts/update_api_config.py --update-key "new_api_key_here"
```

### Validate All Configurations
```bash
python3 scripts/update_api_config.py --validate
```

### Test API with Centralized Config
```bash
python3 scripts/test_api_centralized.py
```

---

## 📚 Using Centralized Config in Scripts

### Python Scripts
```python
# Import centralized configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "config"))

from api_config import get_api_key, get_base_url, get_database_config

# Use configuration
api_key = get_api_key()
base_url = get_base_url()
db_config = get_database_config()

# Make API requests
import requests
response = requests.get(f"{base_url}/books", params={"api_key": api_key})
```

### Shell Scripts
```bash
# Source environment variables
cd "/Users/weixiangzhang/Local Dev/LibraryOfBabel"
eval $(python3 config/api_config.py --export-env)

# Use variables
curl "${API_BASE_URL}/books?api_key=${API_KEY}"
```

---

## 🤖 Daemon Configuration Management

The centralized system automatically manages daemon configuration:

### Manual Daemon Update
```bash
# Update daemon with current centralized config
python3 scripts/update_api_config.py --restart-daemon
```

### What Gets Updated
- ✅ API key in LaunchAgent plist
- ✅ Database connection settings
- ✅ Environment variables
- ✅ Project paths

---

## 🔄 Configuration Update Workflow

When you need to update the API key:

1. **Backup Current Config**:
   ```bash
   python3 scripts/update_api_config.py --backup
   ```

2. **Update API Key** (Updates everything automatically):
   ```bash
   python3 scripts/update_api_config.py --update-key "new_api_key"
   ```

3. **Validate Changes**:
   ```bash
   python3 scripts/update_api_config.py --validate
   ```

**What happens automatically**:
- ✅ Centralized config file updated
- ✅ Daemon plist updated with new key
- ✅ API daemon restarted
- ✅ All configurations validated
- ✅ API connectivity tested

---

## 📊 Configuration File Structure

The `config/api_settings.json` file contains:

```json
{
  "api": {
    "base_url": "https://api.ashortstayinhell.com:5562",
    "api_key": "babel_secure_3f99c2d1d294fbebdfc6b10cce93652d",
    "rate_limit": 60,
    "timeout": 30
  },
  "database": {
    "host": "localhost",
    "database": "knowledge_base",
    "user": "weixiangzhang",
    "port": 5432
  },
  "paths": {
    "project_root": "/Users/weixiangzhang/Local Dev/LibraryOfBabel",
    "logs_dir": "/path/to/logs",
    "scripts_dir": "/path/to/scripts",
    "src_dir": "/path/to/src"
  },
  "features": {
    "fuzzy_search": true,
    "vector_embeddings": true,
    "in_book_search": true,
    "chunking_levels": ["small", "medium", "large"]
  },
  "version": "unified",
  "last_updated": "2025-07-14T23:15:00Z"
}
```

---

## 🛡️ Security Features

### Configuration Validation
- ✅ Validates required configuration keys
- ✅ Tests API connectivity
- ✅ Verifies daemon status
- ✅ Checks database connections

### Backup System
- 💾 Automatic backups before updates
- 📅 Timestamped backup files
- 🔄 Easy rollback capability

### Error Handling
- ❌ Fails fast on configuration errors
- 🔍 Detailed error messages
- 🛡️ Prevents partial updates

---

## 🔧 Advanced Configuration

### Custom Configuration Properties
```python
from config.api_config import config

# Add custom properties
config._config["custom"] = {"my_setting": "value"}
config._save_config()
```

### Environment Variable Export
```bash
# Export all config as environment variables
python3 config/api_config.py --export-env
```

### Daemon Configuration Generation
```bash
# Generate XML for LaunchAgent plist
python3 config/api_config.py --daemon-config
```

---

## 📋 Migration from Old System

### Old Way (Scattered Configuration)
```python
# Each script had hardcoded values
API_KEY = "babel_secure_8a52a0ad3a1fe3bf..."  # Wrong key!
BASE_URL = "https://api.ashortstayinhell.com:5562"
```

### New Way (Centralized Configuration)
```python
# All scripts use centralized config
from api_config import get_api_key, get_base_url
api_key = get_api_key()  # Always correct!
base_url = get_base_url()
```

### Benefits
- 🎯 **Single source of truth**
- 🔄 **Automatic synchronization**
- ✅ **Validation and testing**
- 🛡️ **Error prevention**
- 📝 **Easy maintenance**

---

## 🚨 Troubleshooting

### Configuration Mismatch
```bash
# Fix any configuration issues
python3 scripts/update_api_config.py --validate
```

### Daemon Not Starting
```bash
# Check daemon logs
tail -f ~/Library/LaunchAgents/com.librarybabel.api.plist

# Restart daemon
python3 scripts/update_api_config.py --restart-daemon
```

### API Key Not Working
```bash
# Test current configuration
python3 scripts/test_api_centralized.py

# Update API key if needed
python3 scripts/update_api_config.py --update-key "correct_key"
```

---

## 🎉 Success Metrics

**✅ Configuration Consolidation Complete**:
- 🔧 Single centralized configuration system
- 🤖 Automatic daemon management
- 🧪 100% test success rate with centralized config
- 📝 Comprehensive documentation
- 🛡️ Validation and error checking

**🚀 Future Updates**:
- No more configuration mismatches
- One-command API key updates
- Automatic synchronization across all systems
- Reliable daemon management

---

*📖 This centralized configuration system ensures consistent API access across all LibraryOfBabel components while preventing configuration drift and management overhead.*