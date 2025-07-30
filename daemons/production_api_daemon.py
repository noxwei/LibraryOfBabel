#!/usr/bin/env python3
"""
Production API Daemon
=====================

Runs the LibraryOfBabel Production API as a background daemon.
Provides start, stop, status, and restart functionality.

Usage:
    python3 production_api_daemon.py {start|stop|status|restart}
"""

import os
import sys
import time
import signal
import subprocess
import psutil
from pathlib import Path

# Configuration
DAEMON_NAME = "LibraryOfBabel Production API"
PID_FILE = "/Users/weixiangzhang/Local_Dev/LibraryOfBabel/api_daemon.pid"
LOG_FILE = "/Users/weixiangzhang/Local_Dev/LibraryOfBabel/logs/production_api_daemon.log"
API_SCRIPT = "/Users/weixiangzhang/Local_Dev/LibraryOfBabel/src/api/production_api.py"
WORKING_DIR = "/Users/weixiangzhang/Local_Dev/LibraryOfBabel"

def ensure_directories():
    """Ensure log directory exists"""
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

def get_pid():
    """Get daemon PID from file"""
    try:
        with open(PID_FILE, 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None

def save_pid(pid):
    """Save daemon PID to file"""
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))

def remove_pid_file():
    """Remove PID file"""
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass

def is_running():
    """Check if daemon is running"""
    pid = get_pid()
    if not pid:
        return False
    
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.name() == 'Python'
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def start_daemon():
    """Start the production API daemon"""
    if is_running():
        print(f"❌ {DAEMON_NAME} is already running (PID: {get_pid()})")
        return False
    
    ensure_directories()
    
    print(f"🚀 Starting {DAEMON_NAME}...")
    
    # Start the API process
    try:
        process = subprocess.Popen([
            'python3', API_SCRIPT
        ], 
        cwd=WORKING_DIR,
        stdout=open(LOG_FILE, 'a'),
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid  # Create new process group
        )
        
        # Wait a moment for startup
        time.sleep(3)
        
        if process.poll() is None:  # Process is still running
            save_pid(process.pid)
            print(f"✅ {DAEMON_NAME} started successfully (PID: {process.pid})")
            print(f"📋 Logs: {LOG_FILE}")
            print(f"🌐 API: https://api.ashortstayinhell.com:5562")
            print(f"📊 Status: https://api.ashortstayinhell.com:5562/status")
            print(f"🔒 SSL: Enabled with production certificates")
            return True
        else:
            print(f"❌ Failed to start {DAEMON_NAME}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting daemon: {e}")
        return False

def stop_daemon():
    """Stop the production API daemon"""
    pid = get_pid()
    
    if not pid or not is_running():
        print(f"❌ {DAEMON_NAME} is not running")
        return False
    
    print(f"🛑 Stopping {DAEMON_NAME} (PID: {pid})...")
    
    try:
        # Try graceful shutdown first
        os.kill(pid, signal.SIGTERM)
        
        # Wait up to 10 seconds for graceful shutdown
        for _ in range(10):
            if not is_running():
                break
            time.sleep(1)
        
        # Force kill if still running
        if is_running():
            os.kill(pid, signal.SIGKILL)
            time.sleep(1)
        
        if not is_running():
            remove_pid_file()
            print(f"✅ {DAEMON_NAME} stopped successfully")
            return True
        else:
            print(f"❌ Failed to stop {DAEMON_NAME}")
            return False
            
    except Exception as e:
        print(f"❌ Error stopping daemon: {e}")
        return False

def status_daemon():
    """Show daemon status"""
    pid = get_pid()
    
    print(f"📊 {DAEMON_NAME} Status")
    print("=" * 40)
    
    if is_running():
        print(f"✅ Status: RUNNING")
        print(f"🆔 PID: {pid}")
        print(f"📋 Logs: {LOG_FILE}")
        print(f"🌐 API: https://api.ashortstayinhell.com:5562")
        print(f"📊 Status: https://api.ashortstayinhell.com:5562/status")
        
        # Test API endpoints
        try:
            import requests
            response = requests.get("https://api.ashortstayinhell.com:5562/status", timeout=5, verify=False)
            if response.status_code == 200:
                data = response.json()
                print(f"📚 Books: {data.get('database', {}).get('book_count', 'N/A')}")
                print(f"🏗️ Architecture: {data.get('architecture', 'N/A')}")
                print(f"⚡ Performance: {data.get('performance', {}).get('optimization', 'N/A')}")
            else:
                print("⚠️ API responding but status endpoint failed")
        except Exception as e:
            print(f"⚠️ API test failed: {e}")
    else:
        print(f"❌ Status: STOPPED")
        if pid:
            print(f"⚠️ Stale PID file found: {pid}")
            remove_pid_file()

def restart_daemon():
    """Restart the production API daemon"""
    print(f"🔄 Restarting {DAEMON_NAME}...")
    
    if stop_daemon():
        time.sleep(2)
        if start_daemon():
            print(f"✅ {DAEMON_NAME} restarted successfully")
            return True
    
    print(f"❌ Failed to restart {DAEMON_NAME}")
    return False

def main():
    """Main daemon control function"""
    if len(sys.argv) != 2:
        print(f"📖 {DAEMON_NAME} Daemon Control")
        print("=" * 40)
        print("Usage: python3 production_api_daemon.py {start|stop|status|restart}")
        print("")
        print("Commands:")
        print("  start   - Start the production API daemon")
        print("  stop    - Stop the production API daemon")
        print("  status  - Show daemon status and API health")
        print("  restart - Restart the production API daemon")
        print("")
        print("The daemon will:")
        print("  ✅ Run the production API on port 5562")
        print("  ✅ Provide system status monitoring")
        print("  ✅ Support iOS Shortcuts integration")
        print("  ✅ Enable ChatGPT Custom Actions")
        print("  ✅ Use PostgreSQL stored procedures")
        print("  ✅ Serve on https://api.ashortstayinhell.com:5562")
        print("  ✅ Use SSL certificates for secure connections")
        print("")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        success = start_daemon()
        sys.exit(0 if success else 1)
    elif command == 'stop':
        success = stop_daemon()
        sys.exit(0 if success else 1)
    elif command == 'status':
        status_daemon()
        sys.exit(0)
    elif command == 'restart':
        success = restart_daemon()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 