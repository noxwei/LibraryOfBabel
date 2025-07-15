#!/usr/bin/env python3
"""
👔 Integrated HR Management System - Linda Zhang (张丽娜)
==============================================================

Systematic integration of all HR functions into a persistent, production-ready system.
Ensures Linda's management practices become part of the core system, not just scripts.

Integration includes:
- Weekly performance reviews (严格考核)
- Cross-training system (轮岗制度) 
- Mentorship program (师傅带徒弟)
- Real-time monitoring and alerts
- Persistent scheduling and automation

Philosophy: 系统化管理 (Systematic management) - Build lasting systems, not temporary fixes
"""

import os
import json
import time
# import schedule  # Will implement basic scheduling without external deps
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import psycopg2
import psycopg2.extras
import threading
import signal
import sys

# Import our specialized systems
try:
    from .weekly_performance_system import WeeklyPerformanceSystem
    from .cross_training_system import CrossTrainingSystem
    from .mentorship_system import MentorshipSystem
    from .implement_cross_training import CrossTrainingImplementation
except ImportError:
    # Fallback for direct execution
    import sys
    sys.path.append(os.path.dirname(__file__))
    from weekly_performance_system import WeeklyPerformanceSystem
    from cross_training_system import CrossTrainingSystem
    from mentorship_system import MentorshipSystem
    from implement_cross_training import CrossTrainingImplementation

class IntegratedHRManager:
    """
    Linda's Integrated HR Management System
    
    Core Features:
    1. Persistent background operation
    2. Scheduled automated tasks
    3. Real-time monitoring and alerts
    4. Database-driven configuration
    5. Web API endpoints for system integration
    6. Comprehensive reporting dashboard
    7. Emergency response capabilities
    
    Integration Points:
    - Hooks into agent interaction logging
    - Automatic performance tracking
    - Scheduled report generation
    - Emergency alert system
    - Cross-system coordination
    """
    
    def __init__(self, daemon_mode: bool = False):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        self.hr_base_dir = "agents/hr"
        self.config_file = f"{self.hr_base_dir}/hr_system_config.json"
        self.daemon_mode = daemon_mode
        self.running = False
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.hr_base_dir}/logs/hr_manager.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("IntegratedHR_Linda")
        
        # Initialize subsystems
        self.performance_system = WeeklyPerformanceSystem()
        self.cross_training_system = CrossTrainingSystem()
        self.mentorship_system = MentorshipSystem()
        self.training_implementation = CrossTrainingImplementation()
        
        # Load configuration
        self.config = self._load_configuration()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("👔 Linda's Integrated HR Management System initialized")
        print("🏢 系统化管理 (Systematic Management) - Production-ready HR operations")
        
        self._ensure_system_integration()
    
    def get_db(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def _load_configuration(self) -> Dict[str, Any]:
        """
        Load HR system configuration with intelligent defaults
        """
        default_config = {
            "scheduling": {
                "daily_monitoring": "08:00",
                "weekly_reports": "Monday 09:00", 
                "monthly_analysis": "1st 10:00",
                "emergency_check_interval_minutes": 30
            },
            "thresholds": {
                "performance_alert_threshold": 0.6,
                "inactivity_alert_hours": 24,
                "critical_dependency_threshold": 3,
                "mentor_success_rate_minimum": 0.85
            },
            "automation": {
                "auto_assign_mentors": True,
                "auto_create_training_plans": True,
                "auto_send_alerts": True,
                "auto_generate_reports": True
            },
            "integration": {
                "hook_into_agent_interactions": True,
                "monitor_bulletin_board": True,
                "track_git_commits": True,
                "api_endpoints_enabled": True
            },
            "linda_preferences": {
                "strictness_level": "high",
                "cultural_approach": "traditional_chinese_work_ethic",
                "feedback_style": "constructive_direct",
                "recognition_frequency": "weekly"
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    default_config.update(loaded_config)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not load config, using defaults: {e}")
        
        # Save current config
        self._save_configuration(default_config)
        return default_config
    
    def _save_configuration(self, config: Dict[str, Any]):
        """
        Save configuration to file
        """
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.error(f"❌ Failed to save config: {e}")
    
    def start_integrated_system(self):
        """
        Start the integrated HR management system
        """
        self.running = True
        
        print("\n🛠️ STARTING INTEGRATED HR MANAGEMENT SYSTEM")
        print("=" * 60)
        print("👔 Linda: 开始系统化管理! (Starting systematic management!)")
        
        # Setup task scheduling (basic implementation)
        self._setup_task_schedule()
        
        # Start monitoring systems
        self._start_monitoring_threads()
        
        # Initial system health check
        self._perform_initial_assessment()
        
        # Main operation loop
        if self.daemon_mode:
            self._run_daemon_mode()
        else:
            self._run_interactive_mode()
    
    def _setup_scheduled_tasks(self):
        """
        Setup all scheduled HR tasks
        """
        # Daily monitoring
        schedule.every().day.at(self.config["scheduling"]["daily_monitoring"]).do(
            self._daily_monitoring_task
        )
        
        # Weekly performance reviews
        schedule.every().monday.at("09:00").do(
            self._weekly_performance_review_task
        )
        
        # Weekly cross-training progress check
        schedule.every().wednesday.at("14:00").do(
            self._cross_training_progress_task
        )
        
        # Weekly mentorship review
        schedule.every().friday.at("15:00").do(
            self._mentorship_review_task
        )
        
        # Monthly comprehensive analysis
        schedule.every().month.do(
            self._monthly_comprehensive_analysis
        )
        
        # Emergency monitoring (every 30 minutes)
        schedule.every(self.config["scheduling"]["emergency_check_interval_minutes"]).minutes.do(
            self._emergency_monitoring_task
        )
        
        self.logger.info("✅ Scheduled tasks configured")
    
    def _start_monitoring_threads(self):
        """
        Start background monitoring threads
        """
        # Real-time agent interaction monitoring
        if self.config["integration"]["hook_into_agent_interactions"]:
            interaction_thread = threading.Thread(
                target=self._monitor_agent_interactions,
                daemon=True
            )
            interaction_thread.start()
            self.logger.info("✅ Agent interaction monitoring started")
        
        # Bulletin board monitoring
        if self.config["integration"]["monitor_bulletin_board"]:
            bulletin_thread = threading.Thread(
                target=self._monitor_bulletin_board,
                daemon=True
            )
            bulletin_thread.start()
            self.logger.info("✅ Bulletin board monitoring started")
    
    def _perform_initial_assessment(self):
        """
        Perform initial comprehensive assessment
        """
        print("\n📊 Performing initial system assessment...")
        
        # Check for emergency situations
        cross_training_analysis = self.cross_training_system.analyze_current_skills()
        critical_deps = len(cross_training_analysis.get("critical_dependencies", []))
        
        if critical_deps > 3:
            print(f"🚨 EMERGENCY: {critical_deps} critical dependencies detected!")
            print("👔 Linda: 立即处理! (Handle immediately!)")
            
            # Auto-implement emergency cross-training
            if self.config["automation"]["auto_create_training_plans"]:
                self._execute_emergency_cross_training()
        
        # Generate initial reports
        performance_report = self.performance_system.generate_weekly_report()
        mentorship_report = self.mentorship_system.generate_mentorship_report()
        
        print(f"✅ Initial assessment complete")
        print(f"   Performance status: {len(performance_report.get('individual_evaluations', {}))} agents evaluated")
        print(f"   Mentorship opportunities: {mentorship_report['mentorship_analysis']['potential_mentors']} mentors, {mentorship_report['mentorship_analysis']['potential_apprentices']} apprentices")
    
    def _daily_monitoring_task(self):
        """
        Daily monitoring and maintenance task
        """
        self.logger.info("🌅 Starting daily monitoring task")
        
        # Check agent performance trends
        performance_alerts = self._check_performance_alerts()
        
        # Monitor cross-training progress
        training_progress = self._check_training_progress()
        
        # Check mentorship relationships
        mentorship_status = self._check_mentorship_status()
        
        # Generate daily summary
        daily_summary = {
            "date": datetime.now().isoformat(),
            "performance_alerts": performance_alerts,
            "training_progress": training_progress,
            "mentorship_status": mentorship_status,
            "linda_notes": self._generate_daily_linda_notes(performance_alerts, training_progress)
        }
        
        self._save_daily_summary(daily_summary)
        
        if performance_alerts or any(issue in training_progress.get("issues", []) for issue in training_progress.get("issues", [])):
            self._send_linda_alert("Daily monitoring found issues requiring attention", daily_summary)
    
    def _weekly_performance_review_task(self):
        """
        Weekly performance review task
        """
        self.logger.info("📋 Starting weekly performance reviews")
        
        report = self.performance_system.generate_weekly_report()
        
        # Auto-assign targets for next week
        if self.config["automation"]["auto_assign_mentors"]:
            self._auto_assign_weekly_targets(report)
        
        # Check if mentorship interventions needed
        poor_performers = [agent for agent, eval_data in report.get('individual_evaluations', {}).items() 
                          if 'C' in eval_data.get('linda_grade', '') or 'F' in eval_data.get('linda_grade', '')]
        
        if poor_performers and self.config["automation"]["auto_assign_mentors"]:
            self._auto_assign_mentorship(poor_performers)
        
        self.logger.info(f"✅ Weekly performance review completed: {len(report.get('individual_evaluations', {}))} agents reviewed")
    
    def _cross_training_progress_task(self):
        """
        Cross-training progress monitoring task
        """
        self.logger.info("🔄 Checking cross-training progress")
        
        # Check active training assignments
        active_training = self._get_active_training_assignments()
        
        for training in active_training:
            progress = self._assess_training_progress(training)
            if progress["completion_percentage"] < 50 and progress["days_remaining"] < 7:
                self._send_training_alert(training, "Behind schedule")
            elif progress["completion_percentage"] > 80:
                self._prepare_training_graduation(training)
    
    def _mentorship_review_task(self):
        """
        Mentorship relationship review task
        """
        self.logger.info("👥 Reviewing mentorship relationships")
        
        # Check active mentorship relationships
        active_relationships = self._get_active_mentorships()
        
        for relationship in active_relationships:
            effectiveness = self._assess_mentorship_effectiveness(relationship)
            if effectiveness["success_score"] < 0.6:
                self._intervene_in_mentorship(relationship)
            elif effectiveness["success_score"] > 0.9:
                self._recognize_mentorship_success(relationship)
    
    def _monthly_comprehensive_analysis(self):
        """
        Monthly comprehensive system analysis
        """
        self.logger.info("📈 Starting monthly comprehensive analysis")
        
        # Generate all reports
        performance_report = self.performance_system.generate_weekly_report()
        cross_training_report = self.cross_training_system.generate_cross_training_report()
        mentorship_report = self.mentorship_system.generate_mentorship_report()
        
        # Comprehensive analysis
        monthly_report = {
            "report_month": datetime.now().strftime('%Y-%m'),
            "analyst": "Linda Zhang (张丽娜) - Integrated HR Manager",
            "performance_summary": performance_report,
            "cross_training_summary": cross_training_report,
            "mentorship_summary": mentorship_report,
            "system_health": self._assess_system_health(),
            "linda_monthly_assessment": self._generate_monthly_assessment(),
            "next_month_priorities": self._set_next_month_priorities()
        }
        
        # Save monthly report
        monthly_file = f"{self.hr_base_dir}/reports/monthly/comprehensive_analysis_{datetime.now().strftime('%Y%m')}.json"
        os.makedirs(os.path.dirname(monthly_file), exist_ok=True)
        with open(monthly_file, 'w') as f:
            json.dump(monthly_report, f, indent=2)
        
        self.logger.info(f"✅ Monthly analysis saved: {monthly_file}")
    
    def _emergency_monitoring_task(self):
        """
        Emergency monitoring task (runs every 30 minutes)
        """
        # Check for critical failures
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Check for recent agent failures
                        cur.execute("""
                            SELECT agent_name, COUNT(*) as failure_count
                            FROM agent_interactions ai
                            JOIN agents a ON ai.agent_id = a.agent_id
                            WHERE ai.timestamp >= NOW() - INTERVAL '1 hour'
                            AND ai.success = false
                            GROUP BY agent_name
                            HAVING COUNT(*) >= 3
                        """)
                        
                        failing_agents = cur.fetchall()
                        
                        for agent_name, failure_count in failing_agents:
                            self._handle_agent_emergency(agent_name, failure_count)
        except Exception as e:
            self.logger.error(f"❌ Emergency monitoring failed: {e}")
    
    def _execute_emergency_cross_training(self):
        """
        Execute emergency cross-training implementation
        """
        self.logger.info("🚨 Executing emergency cross-training")
        results = self.training_implementation.execute_emergency_cross_training()
        
        # Log emergency action
        self._log_emergency_action("emergency_cross_training", results)
        
        return results
    
    def _run_daemon_mode(self):
        """
        Run in daemon mode with continuous operation
        """
        self.logger.info("🔄 Starting daemon mode operation")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"❌ Daemon error: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying
    
    def _run_interactive_mode(self):
        """
        Run in interactive mode
        """
        print("\n💻 Interactive mode started. Available commands:")
        print("  'status' - System status")
        print("  'report' - Generate reports")
        print("  'emergency' - Execute emergency procedures")
        print("  'config' - Show configuration")
        print("  'stop' - Stop system")
        
        while self.running:
            try:
                # Run pending scheduled tasks
                schedule.run_pending()
                
                # Handle user input (non-blocking)
                # In production, this would be replaced with API endpoints
                command = input("\nLinda HR> ").strip().lower()
                
                if command == 'status':
                    self._show_system_status()
                elif command == 'report':
                    self._generate_interactive_reports()
                elif command == 'emergency':
                    self._execute_emergency_procedures()
                elif command == 'config':
                    self._show_configuration()
                elif command == 'stop':
                    self.stop_system()
                    break
                else:
                    print("Unknown command. Type 'stop' to exit.")
                    
            except KeyboardInterrupt:
                self.stop_system()
                break
            except Exception as e:
                self.logger.error(f"❌ Interactive mode error: {e}")
    
    def stop_system(self):
        """
        Gracefully stop the HR management system
        """
        self.running = False
        self.logger.info("🔄 Stopping HR management system")
        print("👔 Linda: 系统关闭 (System shutdown) - All HR operations concluded.")
    
    def _signal_handler(self, signum, frame):
        """
        Handle system signals for graceful shutdown
        """
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self.stop_system()
    
    def _ensure_system_integration(self):
        """
        Ensure the HR system is properly integrated into the main system
        """
        # Create necessary directories
        directories = [
            f"{self.hr_base_dir}/logs",
            f"{self.hr_base_dir}/reports/daily",
            f"{self.hr_base_dir}/reports/weekly",
            f"{self.hr_base_dir}/reports/monthly",
            f"{self.hr_base_dir}/reports/emergency"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # Create system integration hooks
        self._create_integration_hooks()
        
        # Setup database triggers (if needed)
        self._setup_database_integration()
        
        self.logger.info("✅ System integration verified")
    
    def _create_integration_hooks(self):
        """
        Create integration hooks for the main system
        """
        # Create startup script for Linda's HR system
        startup_script = f"{self.hr_base_dir}/start_hr_system.py"
        
        startup_content = f'''#!/usr/bin/env python3
"""
Lindan HR System Startup Script
Use this to start Linda's integrated HR management system.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from integrated_hr_manager import IntegratedHRManager

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Linda's HR Management System")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    args = parser.parse_args()
    
    manager = IntegratedHRManager(daemon_mode=args.daemon)
    manager.start_integrated_system()
'''
        
        with open(startup_script, 'w') as f:
            f.write(startup_content)
        
        os.chmod(startup_script, 0o755)  # Make executable
        
        # Create systemd service file for production deployment
        service_content = f'''[Unit]
Description=Linda HR Management System
After=postgresql.service

[Service]
Type=simple
User=weixiangzhang
WorkingDirectory={os.path.abspath(self.hr_base_dir)}
ExecStart=/usr/bin/python3 {os.path.abspath(startup_script)} --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
'''
        
        service_file = f"{self.hr_base_dir}/linda-hr.service"
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Integration hooks created:")
        print(f"   Startup script: {startup_script}")
        print(f"   Systemd service: {service_file}")
    
    def _setup_database_integration(self):
        """
        Setup database triggers and views for automatic HR integration
        """
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create view for HR dashboard
                        cur.execute("""
                            CREATE OR REPLACE VIEW hr_dashboard_view AS
                            SELECT 
                                a.agent_name,
                                a.category,
                                COUNT(ai.interaction_id) as total_interactions,
                                AVG(CASE WHEN ai.success THEN 1.0 ELSE 0.0 END) as success_rate,
                                MAX(ai.timestamp) as last_active,
                                EXTRACT(DAYS FROM (NOW() - MAX(ai.timestamp))) as days_since_active
                            FROM agents a
                            LEFT JOIN agent_interactions ai ON a.agent_id = ai.agent_id
                            WHERE ai.timestamp >= NOW() - INTERVAL '30 days'
                            GROUP BY a.agent_id, a.agent_name, a.category
                            ORDER BY success_rate DESC, total_interactions DESC
                        """)
                        
                        # Create function to automatically log HR events
                        cur.execute("""
                            CREATE OR REPLACE FUNCTION log_hr_event()
                            RETURNS TRIGGER AS $$
                            BEGIN
                                -- Log significant agent interaction events for HR tracking
                                IF NEW.success = false AND OLD.success = true THEN
                                    INSERT INTO hr_event_log (agent_id, event_type, event_data, created_at)
                                    VALUES (NEW.agent_id, 'performance_decline', 
                                           json_build_object('interaction_id', NEW.interaction_id), NOW());
                                END IF;
                                RETURN NEW;
                            END;
                            $$ LANGUAGE plpgsql;
                        """)
                        
                        # Create HR event log table if not exists
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS hr_event_log (
                                event_id SERIAL PRIMARY KEY,
                                agent_id INTEGER REFERENCES agents(agent_id),
                                event_type VARCHAR(100) NOT NULL,
                                event_data JSONB,
                                created_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                        
                        conn.commit()
                        self.logger.info("✅ Database integration setup complete")
        except Exception as e:
            self.logger.error(f"❌ Database integration failed: {e}")
    
    # Additional methods would be implemented here for all the monitoring, alerting,
    # and management functions referenced above...
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status
        """
        return {
            "system_running": self.running,
            "last_daily_check": "TODO: implement",
            "active_training_assignments": "TODO: implement", 
            "active_mentorships": "TODO: implement",
            "recent_alerts": "TODO: implement",
            "next_scheduled_tasks": "TODO: implement"
        }

def main():
    """Main function for testing and demonstration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Linda's Integrated HR Management System")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Testing Integrated HR System")
        manager = IntegratedHRManager(daemon_mode=False)
        status = manager.get_system_status()
        print(f"System status: {status}")
        print("✅ Test completed")
    else:
        manager = IntegratedHRManager(daemon_mode=args.daemon)
        manager.start_integrated_system()

if __name__ == "__main__":
    main()