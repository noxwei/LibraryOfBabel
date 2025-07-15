#!/usr/bin/env python3
"""
🔧 API CONFIGURATION UPDATE MANAGER
===================================

Centralized script to update API configuration across all systems:
- Updates centralized config file
- Updates daemon configuration
- Restarts services
- Validates changes

Prevents configuration mismatches by managing all updates in one place.
"""

import sys
import os
import json
import subprocess
from pathlib import Path

# Add config directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "config"))

from api_config import config, validate_configuration

class APIConfigManager:
    def __init__(self):
        self.project_root = project_root
        self.daemon_plist = Path.home() / "Library/LaunchAgents/com.librarybabel.api.plist"
        self.daemon_service = "com.librarybabel.api"
    
    def update_api_key(self, new_key: str):
        """Update API key across all configurations"""
        print(f"🔧 Updating API key to: {new_key[:20]}...")
        
        # 1. Update centralized configuration
        config.update_api_key(new_key)
        
        # 2. Update daemon configuration
        self.update_daemon_config()
        
        # 3. Restart daemon
        self.restart_daemon()
        
        # 4. Validate all changes
        self.validate_all_configs()
        
        print("✅ API key update complete!")
    
    def update_daemon_config(self):
        """Update daemon plist with current configuration"""
        print("🤖 Updating daemon configuration...")
        
        if not self.daemon_plist.exists():
            print(f"❌ Daemon plist not found: {self.daemon_plist}")
            return False
        
        # Read current plist
        with open(self.daemon_plist, 'r') as f:
            content = f.read()
        
        # Find and replace environment variables section
        env_start = content.find('<key>EnvironmentVariables</key>')
        if env_start == -1:
            print("❌ Could not find EnvironmentVariables section in plist")
            return False
        
        # Find the end of the dict
        dict_start = content.find('<dict>', env_start)
        dict_end = content.find('</dict>', dict_start) + 7
        
        # Generate new environment variables section
        new_env_section = config.generate_daemon_config()
        
        # Replace the section
        new_content = content[:env_start] + new_env_section + content[dict_end:]
        
        # Write updated plist
        with open(self.daemon_plist, 'w') as f:
            f.write(new_content)
        
        print("✅ Daemon configuration updated")
        return True
    
    def restart_daemon(self):
        """Restart the API daemon"""
        print("🔄 Restarting API daemon...")
        
        try:
            # Unload daemon
            subprocess.run(['launchctl', 'unload', str(self.daemon_plist)], 
                          capture_output=True, check=False)
            
            # Load daemon with new config
            subprocess.run(['launchctl', 'load', str(self.daemon_plist)], 
                          capture_output=True, check=True)
            
            print("✅ Daemon restarted successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to restart daemon: {e}")
            return False
    
    def validate_all_configs(self):
        """Validate all configurations are consistent"""
        print("🔍 Validating all configurations...")
        
        # 1. Validate centralized config
        if not validate_configuration():
            print("❌ Centralized configuration validation failed")
            return False
        
        # 2. Test API connectivity
        import requests
        import urllib3
        urllib3.disable_warnings()
        
        try:
            api_key = config.api_key
            base_url = config.base_url
            
            response = requests.get(f"{base_url}/health", verify=False, timeout=10)
            if response.status_code != 200:
                print(f"❌ API health check failed: {response.status_code}")
                return False
            
            # Test authenticated endpoint
            response = requests.get(
                f"{base_url}/books", 
                params={"api_key": api_key, "page_size": 1},
                verify=False, 
                timeout=10
            )
            if response.status_code != 200:
                print(f"❌ API authentication test failed: {response.status_code}")
                return False
            
            print("✅ API connectivity validated")
            
        except Exception as e:
            print(f"❌ API validation failed: {e}")
            return False
        
        # 3. Check daemon status
        try:
            result = subprocess.run(['launchctl', 'list', self.daemon_service], 
                                  capture_output=True, text=True)
            if self.daemon_service not in result.stdout:
                print("❌ Daemon not found in launchctl list")
                return False
            
            print("✅ Daemon status validated")
            
        except Exception as e:
            print(f"❌ Daemon validation failed: {e}")
            return False
        
        print("🎉 All configurations validated successfully!")
        return True
    
    def show_current_config(self):
        """Display current configuration"""
        print("📋 CURRENT API CONFIGURATION")
        print("=" * 40)
        
        full_config = config.get_full_config()
        
        print(f"🔑 API Key: {config.api_key[:20]}...")
        print(f"🌐 Base URL: {config.base_url}")
        print(f"🗄️ Database: {config.database_config['database']}@{config.database_config['host']}")
        print(f"📅 Last Updated: {full_config['last_updated']}")
        print(f"🔧 Version: {full_config['version']}")
        
        print(f"\n🎯 Features:")
        for feature, enabled in full_config['features'].items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {feature}")
    
    def backup_config(self):
        """Create backup of current configuration"""
        backup_file = self.project_root / "config" / f"api_settings_backup_{config._get_timestamp().replace(':', '-')}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(config.get_full_config(), f, indent=2)
        
        print(f"💾 Configuration backed up to: {backup_file}")
        return backup_file


def main():
    """Main configuration management interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LibraryOfBabel API Configuration Manager")
    parser.add_argument("--update-key", type=str, help="Update API key across all systems")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    parser.add_argument("--validate", action="store_true", help="Validate all configurations")
    parser.add_argument("--restart-daemon", action="store_true", help="Restart API daemon")
    parser.add_argument("--backup", action="store_true", help="Backup current configuration")
    
    args = parser.parse_args()
    
    manager = APIConfigManager()
    
    if args.update_key:
        manager.backup_config()
        manager.update_api_key(args.update_key)
    
    elif args.show:
        manager.show_current_config()
    
    elif args.validate:
        success = manager.validate_all_configs()
        if not success:
            sys.exit(1)
    
    elif args.restart_daemon:
        manager.restart_daemon()
    
    elif args.backup:
        manager.backup_config()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()