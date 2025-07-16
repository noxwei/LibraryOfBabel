#!/usr/bin/env python3
"""
🔧 CENTRALIZED API CONFIGURATION MANAGEMENT
==========================================

Single source of truth for all API configuration including:
- API keys
- Base URLs  
- Database connections
- Environment settings

This prevents configuration mismatches across scripts, daemons, and tests.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class APIConfig:
    """Centralized configuration manager for LibraryOfBabel API"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self.project_root = self.config_dir.parent
        self.config_file = self.config_dir / "api_settings.json"
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self._config = json.load(f)
        else:
            self._config = self._create_default_config()
            self._save_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        return {
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
                "project_root": str(self.project_root),
                "logs_dir": str(self.project_root / "logs"),
                "scripts_dir": str(self.project_root / "scripts"),
                "src_dir": str(self.project_root / "src")
            },
            "features": {
                "fuzzy_search": True,
                "vector_embeddings": True,
                "in_book_search": True,
                "chunking_levels": ["small", "medium", "large"]
            },
            "embedding_models": {
                "default": "nomic-embed-text",
                "available": {
                    "nomic-embed-text": {
                        "dimension": 768,
                        "max_length": 8000,
                        "description": "Optimized for text embeddings",
                        "model_id": "nomic-embed-text:latest"
                    },
                    "bge-m3": {
                        "dimension": 1024,
                        "max_length": 8192,
                        "description": "BGE M3 multilingual embedding model",
                        "model_id": "bge-m3:latest"
                    },
                    "mxbai-embed-large": {
                        "dimension": 1024,
                        "max_length": 8000,
                        "description": "MixedBread AI large embedding model",
                        "model_id": "mxbai-embed-large:latest"
                    },
                    "granite-embedding": {
                        "dimension": 768,
                        "max_length": 8192,
                        "description": "IBM Granite embedding model (278M parameters)",
                        "model_id": "granite-embedding:278m"
                    }
                }
            },
            "version": "unified",
            "last_updated": "2025-07-14T23:15:00Z"
        }
    
    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    @property
    def api_key(self) -> str:
        """Get current API key"""
        return self._config["api"]["api_key"]
    
    @property
    def base_url(self) -> str:
        """Get API base URL"""
        return self._config["api"]["base_url"]
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self._config["database"]
    
    @property
    def project_paths(self) -> Dict[str, str]:
        """Get project paths"""
        return self._config["paths"]
    
    @property
    def embedding_models(self) -> Dict[str, Any]:
        """Get embedding models configuration"""
        return self._config["embedding_models"]
    
    def get_default_embedding_model(self) -> str:
        """Get default embedding model name"""
        return self._config["embedding_models"]["default"]
    
    def get_available_embedding_models(self) -> Dict[str, Dict]:
        """Get all available embedding models"""
        return self._config["embedding_models"]["available"]
    
    def update_api_key(self, new_key: str):
        """Update API key and save configuration"""
        self._config["api"]["api_key"] = new_key
        self._config["last_updated"] = self._get_timestamp()
        self._save_config()
        print(f"✅ API key updated: {new_key[:20]}...")
    
    def update_base_url(self, new_url: str):
        """Update base URL and save configuration"""
        self._config["api"]["base_url"] = new_url
        self._config["last_updated"] = self._get_timestamp()
        self._save_config()
        print(f"✅ Base URL updated: {new_url}")
    
    def get_full_config(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self._config.copy()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"
    
    def validate_config(self) -> bool:
        """Validate configuration completeness"""
        required_keys = [
            "api.api_key",
            "api.base_url", 
            "database.host",
            "database.database"
        ]
        
        for key_path in required_keys:
            keys = key_path.split('.')
            current = self._config
            
            try:
                for key in keys:
                    current = current[key]
                if not current:
                    print(f"❌ Missing required config: {key_path}")
                    return False
            except KeyError:
                print(f"❌ Missing required config: {key_path}")
                return False
        
        print("✅ Configuration validation passed")
        return True
    
    def export_env_vars(self) -> Dict[str, str]:
        """Export configuration as environment variables"""
        return {
            "API_KEY": self.api_key,
            "API_BASE_URL": self.base_url,
            "DB_HOST": self.database_config["host"],
            "DB_NAME": self.database_config["database"],
            "DB_USER": self.database_config["user"],
            "DB_PORT": str(self.database_config["port"]),
            "PROJECT_ROOT": self.project_paths["project_root"]
        }
    
    def generate_daemon_config(self) -> str:
        """Generate environment variables section for daemon plist"""
        env_vars = self.export_env_vars()
        
        xml_content = """    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>PYTHONPATH</key>
        <string>{project_root}/src</string>""".format(project_root=env_vars["PROJECT_ROOT"])
        
        for key, value in env_vars.items():
            xml_content += f"""
        <key>{key}</key>
        <string>{value}</string>"""
        
        xml_content += """
    </dict>"""
        
        return xml_content


# Global configuration instance
config = APIConfig()

def get_api_key() -> str:
    """Get current API key - primary interface"""
    return config.api_key

def get_base_url() -> str:
    """Get current base URL - primary interface"""
    return config.base_url

def get_database_config() -> Dict[str, Any]:
    """Get database configuration - primary interface"""
    return config.database_config

def update_api_key(new_key: str):
    """Update API key across all configurations"""
    config.update_api_key(new_key)

def validate_configuration() -> bool:
    """Validate all configuration"""
    return config.validate_config()

def get_available_embedding_models() -> Dict[str, Dict]:
    """Get available embedding models - primary interface"""
    return config.get_available_embedding_models()

def get_default_embedding_model() -> str:
    """Get default embedding model - primary interface"""
    return config.get_default_embedding_model()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LibraryOfBabel API Configuration Manager")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--update-key", type=str, help="Update API key")
    parser.add_argument("--update-url", type=str, help="Update base URL")
    parser.add_argument("--export-env", action="store_true", help="Export environment variables")
    parser.add_argument("--daemon-config", action="store_true", help="Generate daemon configuration")
    
    args = parser.parse_args()
    
    if args.show:
        print("📋 Current Configuration:")
        print(json.dumps(config.get_full_config(), indent=2))
    
    elif args.validate:
        validate_configuration()
    
    elif args.update_key:
        update_api_key(args.update_key)
    
    elif args.update_url:
        config.update_base_url(args.update_url)
    
    elif args.export_env:
        print("🔧 Environment Variables:")
        for key, value in config.export_env_vars().items():
            print(f"export {key}={value}")
    
    elif args.daemon_config:
        print("🤖 Daemon Configuration XML:")
        print(config.generate_daemon_config())
    
    else:
        parser.print_help()