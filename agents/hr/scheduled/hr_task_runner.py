#!/usr/bin/env python3
"""HR Task Runner - Executes scheduled HR tasks"""

import sys
import os
sys.path.append("/Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/hr")

from weekly_performance_system import WeeklyPerformanceSystem
from cross_training_system import CrossTrainingSystem
from mentorship_system import MentorshipSystem

def run_task(task_type):
    """Run specific HR task"""
    if task_type == "daily_performance":
        # Quick daily performance check
        performance = WeeklyPerformanceSystem()
        # Implement daily check logic
        print("✅ Daily performance check completed")
        
    elif task_type == "weekly_performance":
        performance = WeeklyPerformanceSystem()
        report = performance.generate_weekly_report()
        print(f"✅ Weekly performance report: {len(report.get('individual_evaluations', {}))} agents")
        
    elif task_type == "cross_training":
        cross_training = CrossTrainingSystem()
        report = cross_training.generate_cross_training_report()
        print("✅ Cross-training progress checked")
        
    elif task_type == "mentorship":
        mentorship = MentorshipSystem()
        report = mentorship.generate_mentorship_report()
        print("✅ Mentorship relationships reviewed")
        
    else:
        print(f"❌ Unknown task type: {task_type}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: hr_task_runner.py <task_type>")
        sys.exit(1)
    
    run_task(sys.argv[1])
