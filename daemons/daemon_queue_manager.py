#!/usr/bin/env python3
"""
🎯 DAEMON QUEUE MANAGER - Dr. Sarah Chen's PostgreSQL-First Architecture
=========================================================================

Intelligent daemon orchestration system with Grafana monitoring integration.
Coordinates sequential daemon execution with real-time progress tracking.

Features:
- Sequential daemon execution (no conflicts)
- Queue status tracking and management
- Grafana metrics export via Prometheus
- Incremental processing with pause/resume
- Automatic recovery and retry logic
- Real-time progress monitoring
"""

import os
import sys
import json
import time
import signal
import logging
import psycopg2
import psycopg2.extras
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import requests

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

class DaemonStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class QueuedDaemon:
    """Represents a daemon in the processing queue"""
    daemon_id: str
    daemon_name: str
    script_path: str
    arguments: List[str]
    priority: int
    status: DaemonStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_pct: float = 0.0
    chunks_processed: int = 0
    chunks_target: int = 0
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class QueueMetrics:
    """Queue performance metrics for Grafana"""
    total_queued: int = 0
    currently_running: int = 0
    completed_today: int = 0
    failed_today: int = 0
    average_processing_time: float = 0.0
    queue_depth: int = 0
    estimated_completion_time: Optional[datetime] = None

class DaemonQueueManager:
    """
    🚀 Dr. Sarah Chen's Daemon Queue Management System
    
    Orchestrates daemon execution with intelligent scheduling, monitoring,
    and Grafana integration for the LibraryOfBabel system.
    """
    
    def __init__(self):
        self.queue_dir = project_root / "logs" / "daemon_queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        self.queue_file = self.queue_dir / "queue_state.json"
        self.metrics_file = self.queue_dir / "queue_metrics.json"  
        self.log_file = self.queue_dir / "queue_manager.log"
        self.pid_file = project_root / "pids" / "daemon_queue_manager.pid"
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("DaemonQueueManager")
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'database': 'knowledge_base', 
            'user': 'weixiangzhang',
            'password': os.environ.get('DB_PASSWORD')
        }
        
        # Queue management
        self.daemon_queue: List[QueuedDaemon] = []
        self.current_daemon: Optional[QueuedDaemon] = None
        self.running = False
        self.metrics = QueueMetrics()
        
        # Prometheus metrics port for Grafana
        self.metrics_port = 8001
        
        # Load existing queue
        self.load_queue_state()
        
        self.logger.info("🎯 Daemon Queue Manager initialized")
        self.logger.info(f"📊 Queue depth: {len(self.daemon_queue)}")
        
    def load_queue_state(self):
        """Load queue state from previous session"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    self.daemon_queue = []
                    for daemon_data in data.get('queue', []):
                        daemon = QueuedDaemon(
                            daemon_id=daemon_data['daemon_id'],
                            daemon_name=daemon_data['daemon_name'],
                            script_path=daemon_data['script_path'],
                            arguments=daemon_data['arguments'],
                            priority=daemon_data['priority'],
                            status=DaemonStatus(daemon_data['status']),
                            created_at=datetime.fromisoformat(daemon_data['created_at']),
                            started_at=datetime.fromisoformat(daemon_data['started_at']) if daemon_data.get('started_at') else None,
                            completed_at=datetime.fromisoformat(daemon_data['completed_at']) if daemon_data.get('completed_at') else None,
                            progress_pct=daemon_data.get('progress_pct', 0.0),
                            chunks_processed=daemon_data.get('chunks_processed', 0),
                            chunks_target=daemon_data.get('chunks_target', 0),
                            error_message=daemon_data.get('error_message'),
                            retry_count=daemon_data.get('retry_count', 0),
                            max_retries=daemon_data.get('max_retries', 3)
                        )
                        self.daemon_queue.append(daemon)
                    
                    self.logger.info(f"📁 Loaded queue: {len(self.daemon_queue)} daemons")
            except Exception as e:
                self.logger.error(f"Failed to load queue state: {e}")
                
    def save_queue_state(self):
        """Save current queue state"""
        try:
            queue_data = []
            for daemon in self.daemon_queue:
                daemon_dict = asdict(daemon)
                # Convert datetime objects to ISO strings
                for field in ['created_at', 'started_at', 'completed_at']:
                    if daemon_dict[field]:
                        daemon_dict[field] = daemon_dict[field].isoformat()
                daemon_dict['status'] = daemon.status.value
                queue_data.append(daemon_dict)
            
            state = {
                "last_updated": datetime.now().isoformat(),
                "queue": queue_data,
                "metrics": asdict(self.metrics)
            }
            
            with open(self.queue_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save queue state: {e}")
            
    def add_daemon(self, daemon_name: str, script_path: str, arguments: List[str] = None, 
                   priority: int = 5, chunks_target: int = 0) -> str:
        """Add daemon to processing queue"""
        if arguments is None:
            arguments = []
            
        daemon_id = f"{daemon_name}_{int(time.time())}"
        
        daemon = QueuedDaemon(
            daemon_id=daemon_id,
            daemon_name=daemon_name,
            script_path=script_path,
            arguments=arguments,
            priority=priority,
            status=DaemonStatus.PENDING,
            created_at=datetime.now(),
            chunks_target=chunks_target
        )
        
        # Insert based on priority (lower number = higher priority)
        insert_pos = len(self.daemon_queue)
        for i, existing_daemon in enumerate(self.daemon_queue):
            if daemon.priority < existing_daemon.priority:
                insert_pos = i
                break
                
        self.daemon_queue.insert(insert_pos, daemon)
        self.save_queue_state()
        
        self.logger.info(f"➕ Added daemon to queue: {daemon_name} (ID: {daemon_id}, Priority: {priority})")
        return daemon_id
        
    def get_next_daemon(self) -> Optional[QueuedDaemon]:
        """Get next pending daemon from queue"""
        for daemon in self.daemon_queue:
            if daemon.status == DaemonStatus.PENDING:
                return daemon
        return None
        
    def start_daemon(self, daemon: QueuedDaemon) -> bool:
        """Start execution of a daemon"""
        try:
            daemon.status = DaemonStatus.RUNNING
            daemon.started_at = datetime.now()
            self.current_daemon = daemon
            
            # Build command
            cmd = ["python3", daemon.script_path] + daemon.arguments
            
            self.logger.info(f"🚀 Starting daemon: {daemon.daemon_name}")
            self.logger.info(f"📄 Command: {' '.join(cmd)}")
            
            # Start daemon process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root
            )
            
            # Monitor daemon progress
            return self.monitor_daemon_progress(daemon, process)
            
        except Exception as e:
            daemon.status = DaemonStatus.FAILED
            daemon.error_message = str(e)
            self.logger.error(f"💥 Failed to start daemon {daemon.daemon_name}: {e}")
            return False
            
    def monitor_daemon_progress(self, daemon: QueuedDaemon, process: subprocess.Popen) -> bool:
        """Monitor daemon execution and update progress"""
        try:
            # Monitor process output for progress updates
            while process.poll() is None:
                # Check for daemon state file updates (multi-modal daemon pattern)
                self.update_daemon_progress(daemon)
                time.sleep(5)  # Check every 5 seconds
                
            # Process completed
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                daemon.status = DaemonStatus.COMPLETED
                daemon.completed_at = datetime.now()
                daemon.progress_pct = 100.0
                self.logger.info(f"✅ Daemon completed successfully: {daemon.daemon_name}")
                return True
            else:
                daemon.status = DaemonStatus.FAILED
                daemon.error_message = f"Exit code: {process.returncode}, STDERR: {stderr}"
                self.logger.error(f"❌ Daemon failed: {daemon.daemon_name} - {daemon.error_message}")
                return False
                
        except Exception as e:
            daemon.status = DaemonStatus.FAILED
            daemon.error_message = str(e)
            self.logger.error(f"💥 Error monitoring daemon {daemon.daemon_name}: {e}")
            return False
        finally:
            self.current_daemon = None
            self.save_queue_state()
            
    def update_daemon_progress(self, daemon: QueuedDaemon):
        """Update daemon progress from state files"""
        try:
            # Check for multi-modal daemon state file
            if "multi_modal" in daemon.daemon_name:
                state_file = project_root / "logs" / "multi_modal_daemon" / "daemon_state.json"
                if state_file.exists():
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                        daemon.chunks_processed = state.get('chunks_processed', 0)
                        if daemon.chunks_target > 0:
                            daemon.progress_pct = min(100.0, (daemon.chunks_processed / daemon.chunks_target) * 100)
                            
        except Exception as e:
            self.logger.warning(f"Could not update progress for {daemon.daemon_name}: {e}")
            
    def update_metrics(self):
        """Update queue metrics for Grafana"""
        self.metrics.total_queued = len(self.daemon_queue)
        self.metrics.currently_running = sum(1 for d in self.daemon_queue if d.status == DaemonStatus.RUNNING)
        
        today = datetime.now().date()
        self.metrics.completed_today = sum(1 for d in self.daemon_queue 
                                         if d.status == DaemonStatus.COMPLETED 
                                         and d.completed_at and d.completed_at.date() == today)
        self.metrics.failed_today = sum(1 for d in self.daemon_queue 
                                      if d.status == DaemonStatus.FAILED 
                                      and d.completed_at and d.completed_at.date() == today)
        
        self.metrics.queue_depth = sum(1 for d in self.daemon_queue if d.status == DaemonStatus.PENDING)
        
        # Save metrics for Prometheus/Grafana export
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(asdict(self.metrics), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")
            
    def run_queue_manager(self):
        """Main queue processing loop"""
        self.logger.info("🚀 Starting Daemon Queue Manager")
        
        # Write PID file
        self.pid_file.parent.mkdir(exist_ok=True)
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
        self.running = True
        
        try:
            while self.running:
                # Update metrics
                self.update_metrics()
                
                # Check for next daemon to run
                if not self.current_daemon:
                    next_daemon = self.get_next_daemon()
                    if next_daemon:
                        success = self.start_daemon(next_daemon)
                        if not success and next_daemon.retry_count < next_daemon.max_retries:
                            # Retry failed daemon
                            next_daemon.retry_count += 1
                            next_daemon.status = DaemonStatus.PENDING
                            self.logger.info(f"🔄 Retrying daemon: {next_daemon.daemon_name} (attempt {next_daemon.retry_count + 1})")
                    else:
                        # No pending daemons
                        time.sleep(10)
                else:
                    # Update progress of current daemon
                    self.update_daemon_progress(self.current_daemon)
                    time.sleep(5)
                    
                # Save state periodically
                self.save_queue_state()
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Queue manager interrupted by user")
        except Exception as e:
            self.logger.error(f"💥 Queue manager error: {e}")
        finally:
            self.running = False
            self.cleanup()
            
    def cleanup(self):
        """Cleanup queue manager resources"""
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
            self.logger.info("🧹 Queue manager cleanup complete")
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
            
    def get_queue_status(self) -> Dict:
        """Get current queue status for API/monitoring"""
        return {
            "queue_depth": len([d for d in self.daemon_queue if d.status == DaemonStatus.PENDING]),
            "running_daemons": len([d for d in self.daemon_queue if d.status == DaemonStatus.RUNNING]),
            "completed_daemons": len([d for d in self.daemon_queue if d.status == DaemonStatus.COMPLETED]),
            "failed_daemons": len([d for d in self.daemon_queue if d.status == DaemonStatus.FAILED]),
            "current_daemon": self.current_daemon.daemon_name if self.current_daemon else None,
            "metrics": asdict(self.metrics)
        }

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Received shutdown signal - stopping queue manager...")
    if hasattr(signal_handler, 'manager'):
        signal_handler.manager.running = False

def main():
    """Main queue manager entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "add":
        # Add daemon to queue mode
        if len(sys.argv) < 4:
            print("Usage: python daemon_queue_manager.py add <daemon_name> <script_path> [args...]")
            sys.exit(1)
            
        manager = DaemonQueueManager()
        daemon_name = sys.argv[2]
        script_path = sys.argv[3]
        arguments = sys.argv[4:] if len(sys.argv) > 4 else []
        
        daemon_id = manager.add_daemon(daemon_name, script_path, arguments)
        print(f"✅ Added daemon to queue: {daemon_name} (ID: {daemon_id})")
        return
        
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        # Show queue status
        manager = DaemonQueueManager()
        status = manager.get_queue_status()
        print("📊 DAEMON QUEUE STATUS")
        print("=" * 50)
        print(f"Queue Depth: {status['queue_depth']}")
        print(f"Running: {status['running_daemons']}")
        print(f"Completed: {status['completed_daemons']}")
        print(f"Failed: {status['failed_daemons']}")
        print(f"Current Daemon: {status['current_daemon'] or 'None'}")
        return
    
    # Run queue manager
    manager = DaemonQueueManager()
    signal_handler.manager = manager
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        manager.run_queue_manager()
    except Exception as e:
        manager.logger.error(f"💥 Fatal queue manager error: {e}")
        raise

if __name__ == "__main__":
    main()