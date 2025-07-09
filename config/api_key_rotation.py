#!/usr/bin/env python3
"""
🔒 API Key Rotation System - 30-Day High-Security Protocol
LibraryOfBabel Security Module
"""

import os
import secrets
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APIKeyRotation")

class APIKeyRotationManager:
    """
    High-Security 30-Day API Key Rotation Manager
    
    Features:
    - 30-day automatic rotation
    - Multi-key support for zero downtime
    - Comprehensive audit logging
    - Emergency rotation capability
    """
    
    def __init__(self):
        self.config_file = "config/key_rotation_config.json"
        self.rotation_days = 30  # High-security 30-day rotation
        self.grace_period_hours = 48  # 48-hour grace period
        self.key_prefix = "babel_secure_"
        
        # Load current configuration
        self.config = self._load_config()
        
        logger.info("🔒 30-Day API Key Rotation Manager initialized")
    
    def _load_config(self) -> Dict:
        """Load rotation configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return self._create_initial_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._create_initial_config()
    
    def _create_initial_config(self) -> Dict:
        """Create initial configuration"""
        # Get API key from environment or use the new rotated key
        api_key = os.environ.get('API_KEY', os.environ.get('BABEL_API_KEY', ''))
        
        config = {
            "current_key": {
                "key": api_key,
                "created_date": datetime.now().isoformat(),
                "rotation_date": (datetime.now() + timedelta(days=self.rotation_days)).isoformat(),
                "status": "active"
            },
            "previous_key": None,
            "rotation_history": [],
            "security_settings": {
                "rotation_days": self.rotation_days,
                "grace_period_hours": self.grace_period_hours,
                "auto_rotation_enabled": True,
                "emergency_rotation_enabled": True
            }
        }
        self._save_config(config)
        return config
    
    def _save_config(self, config: Dict):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("🔒 Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def generate_new_key(self) -> str:
        """Generate cryptographically secure new API key"""
        return f"{self.key_prefix}{secrets.token_hex(32)}"
    
    def needs_rotation(self) -> bool:
        """Check if key needs rotation based on 30-day schedule"""
        try:
            current_key = self.config.get("current_key", {})
            rotation_date_str = current_key.get("rotation_date")
            
            if not rotation_date_str:
                return True
            
            rotation_date = datetime.fromisoformat(rotation_date_str)
            return datetime.now() >= rotation_date
        except Exception as e:
            logger.error(f"Error checking rotation need: {e}")
            return True
    
    def rotate_key(self, force: bool = False) -> Dict:
        """
        Perform API key rotation with zero downtime
        
        Args:
            force: Force rotation even if not scheduled
            
        Returns:
            Dict with rotation result
        """
        if not force and not self.needs_rotation():
            return {
                "success": False,
                "message": "Rotation not needed yet",
                "next_rotation": self.config["current_key"]["rotation_date"]
            }
        
        try:
            # Generate new key
            new_key = self.generate_new_key()
            rotation_timestamp = datetime.now().isoformat()
            
            # Move current key to previous (grace period)
            current_key = self.config["current_key"]
            
            # Update configuration
            self.config["previous_key"] = {
                **current_key,
                "status": "grace_period",
                "grace_expires": (datetime.now() + timedelta(hours=self.grace_period_hours)).isoformat()
            }
            
            self.config["current_key"] = {
                "key": new_key,
                "created_date": rotation_timestamp,
                "rotation_date": (datetime.now() + timedelta(days=self.rotation_days)).isoformat(),
                "status": "active"
            }
            
            # Add to rotation history
            self.config["rotation_history"].append({
                "timestamp": rotation_timestamp,
                "old_key_preview": current_key["key"][:20] + "..." if current_key.get("key") else "N/A",
                "new_key_preview": new_key[:20] + "...",
                "rotation_type": "forced" if force else "scheduled",
                "success": True
            })
            
            # Keep only last 10 rotation records
            if len(self.config["rotation_history"]) > 10:
                self.config["rotation_history"] = self.config["rotation_history"][-10:]
            
            self._save_config(self.config)
            
            logger.info(f"🔄 API Key rotated successfully - Next rotation: {self.config['current_key']['rotation_date']}")
            
            return {
                "success": True,
                "new_key": new_key,
                "rotation_date": rotation_timestamp,
                "next_rotation": self.config["current_key"]["rotation_date"],
                "message": "Key rotated successfully - Update your .env file"
            }
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return {
                "success": False,
                "message": f"Rotation failed: {str(e)}"
            }
    
    def validate_key(self, provided_key: str) -> bool:
        """
        Validate API key (supports current and grace period keys)
        
        Args:
            provided_key: The key to validate
            
        Returns:
            True if key is valid, False otherwise
        """
        if not provided_key:
            return False
        
        current_key = self.config.get("current_key", {}).get("key")
        if provided_key == current_key:
            return True
        
        # Check grace period key
        previous_key = self.config.get("previous_key")
        if previous_key and isinstance(previous_key, dict) and previous_key.get("status") == "grace_period":
            grace_expires = datetime.fromisoformat(previous_key["grace_expires"])
            if datetime.now() <= grace_expires and provided_key == previous_key.get("key"):
                return True
        
        return False
    
    def get_rotation_status(self) -> Dict:
        """Get current rotation status"""
        current_key = self.config.get("current_key", {})
        next_rotation = datetime.fromisoformat(current_key.get("rotation_date", datetime.now().isoformat()))
        days_until_rotation = (next_rotation - datetime.now()).days
        
        return {
            "current_key_created": current_key.get("created_date"),
            "next_rotation_date": current_key.get("rotation_date"),
            "days_until_rotation": days_until_rotation,
            "rotation_needed": self.needs_rotation(),
            "grace_period_active": bool(self.config.get("previous_key") and isinstance(self.config.get("previous_key"), dict) and self.config.get("previous_key", {}).get("status") == "grace_period"),
            "rotation_history_count": len(self.config.get("rotation_history", [])),
            "security_level": "HIGH (30-day rotation)"
        }
    
    def emergency_rotate(self) -> Dict:
        """Emergency rotation for security incidents"""
        logger.warning("🚨 EMERGENCY API KEY ROTATION INITIATED")
        return self.rotate_key(force=True)
    
    def cleanup_expired_keys(self):
        """Clean up expired grace period keys"""
        previous_key = self.config.get("previous_key")
        if previous_key and previous_key.get("status") == "grace_period":
            grace_expires = datetime.fromisoformat(previous_key["grace_expires"])
            if datetime.now() > grace_expires:
                self.config["previous_key"] = None
                self._save_config(self.config)
                logger.info("🧹 Expired grace period key cleaned up")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LibraryOfBabel API Key Rotation Manager")
    parser.add_argument("--rotate", action="store_true", help="Rotate API key")
    parser.add_argument("--status", action="store_true", help="Show rotation status")
    parser.add_argument("--emergency", action="store_true", help="Emergency rotation")
    parser.add_argument("--validate", type=str, help="Validate an API key")
    
    args = parser.parse_args()
    
    manager = APIKeyRotationManager()
    
    if args.status:
        status = manager.get_rotation_status()
        print("\n🔒 API Key Rotation Status:")
        print("=" * 40)
        for key, value in status.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print()
    
    elif args.rotate:
        result = manager.rotate_key()
        if result["success"]:
            print(f"✅ Key rotated successfully!")
            print(f"New key: {result['new_key']}")
            print(f"Next rotation: {result['next_rotation']}")
            print("\n🔄 Update your .env file with the new key!")
        else:
            print(f"❌ Rotation failed: {result['message']}")
    
    elif args.emergency:
        result = manager.emergency_rotate()
        if result["success"]:
            print(f"🚨 EMERGENCY ROTATION COMPLETE!")
            print(f"New key: {result['new_key']}")
            print(f"Next rotation: {result['next_rotation']}")
            print("\n⚠️  IMMEDIATELY update your .env file!")
        else:
            print(f"❌ Emergency rotation failed: {result['message']}")
    
    elif args.validate:
        is_valid = manager.validate_key(args.validate)
        print(f"Key validation: {'✅ VALID' if is_valid else '❌ INVALID'}")
    
    else:
        print("🔒 LibraryOfBabel API Key Rotation Manager")
        print("Use --help for available commands")

if __name__ == "__main__":
    main()