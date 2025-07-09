#!/usr/bin/env python3
"""
🔒 API Key Rotation Monitoring Script
Automated monitoring and alerting for 30-day key rotation
"""

import os
import sys
import json
from datetime import datetime, timedelta
# Email imports removed - not needed for basic monitoring

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.api_key_rotation import APIKeyRotationManager

class RotationMonitor:
    """Monitor API key rotation and send alerts"""
    
    def __init__(self):
        self.manager = APIKeyRotationManager()
        self.alerts_enabled = True
        self.log_file = "logs/rotation_monitor.log"
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Log monitoring messages"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        
        print(f"🔒 {level}: {message}")
    
    def check_rotation_needed(self) -> dict:
        """Check if rotation is needed and return status"""
        status = self.manager.get_rotation_status()
        
        if status["rotation_needed"]:
            self.log_message("⚠️  API Key rotation needed!", "WARNING")
            return {
                "action_needed": True,
                "urgency": "high",
                "message": "API key rotation is overdue",
                "details": status
            }
        
        days_until = status["days_until_rotation"]
        
        if days_until <= 3:
            self.log_message(f"🔔 API Key rotation in {days_until} days", "INFO")
            return {
                "action_needed": False,
                "urgency": "medium",
                "message": f"API key rotation due in {days_until} days",
                "details": status
            }
        
        if days_until <= 7:
            self.log_message(f"📅 API Key rotation in {days_until} days", "INFO")
            return {
                "action_needed": False,
                "urgency": "low",
                "message": f"API key rotation due in {days_until} days",
                "details": status
            }
        
        return {
            "action_needed": False,
            "urgency": "none",
            "message": f"API key rotation in {days_until} days",
            "details": status
        }
    
    def send_alert(self, alert_data: dict):
        """Send alert notification (placeholder for actual implementation)"""
        if not self.alerts_enabled:
            return
        
        urgency = alert_data["urgency"]
        message = alert_data["message"]
        
        # Log alert
        self.log_message(f"ALERT ({urgency.upper()}): {message}", "ALERT")
        
        # In a real implementation, you might send:
        # - Email notifications
        # - Slack/Discord messages
        # - SMS alerts
        # - PagerDuty incidents
        
        # For now, just create a prominent alert file
        alert_file = f"alerts/rotation_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(alert_file), exist_ok=True)
        
        with open(alert_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "alert_type": "api_key_rotation",
                "urgency": urgency,
                "message": message,
                "details": alert_data["details"],
                "action_required": alert_data["action_needed"]
            }, f, indent=2)
        
        print(f"🚨 Alert created: {alert_file}")
    
    def auto_rotate_if_needed(self):
        """Automatically rotate key if needed"""
        if self.manager.needs_rotation():
            self.log_message("🔄 Initiating automatic key rotation", "INFO")
            
            result = self.manager.rotate_key()
            
            if result["success"]:
                self.log_message(f"✅ Automatic rotation successful. New key: {result['new_key'][:20]}...", "SUCCESS")
                
                # Send success alert
                self.send_alert({
                    "action_needed": True,
                    "urgency": "high",
                    "message": "API key automatically rotated - Update .env file",
                    "details": {
                        "new_key": result['new_key'],
                        "next_rotation": result['next_rotation']
                    }
                })
            else:
                self.log_message(f"❌ Automatic rotation failed: {result['message']}", "ERROR")
                
                # Send failure alert
                self.send_alert({
                    "action_needed": True,
                    "urgency": "critical",
                    "message": f"Automatic key rotation failed: {result['message']}",
                    "details": result
                })
    
    def run_monitoring_check(self):
        """Run complete monitoring check"""
        self.log_message("🔍 Running API key rotation monitoring check", "INFO")
        
        # Clean up expired keys
        self.manager.cleanup_expired_keys()
        
        # Check rotation status
        check_result = self.check_rotation_needed()
        
        # Send alerts if needed
        if check_result["urgency"] in ["high", "critical"]:
            self.send_alert(check_result)
        
        # Auto-rotate if configured and needed
        if check_result["action_needed"]:
            self.auto_rotate_if_needed()
        
        self.log_message("✅ Monitoring check completed", "INFO")
        
        return check_result

def main():
    """Main monitoring function"""
    monitor = RotationMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Run as daemon (would typically use proper daemon libraries)
        print("🔒 Starting API key rotation monitor in daemon mode")
        monitor.run_monitoring_check()
    else:
        # Run single check
        result = monitor.run_monitoring_check()
        print(f"\n📊 Monitoring Result: {result['message']}")

if __name__ == "__main__":
    main()