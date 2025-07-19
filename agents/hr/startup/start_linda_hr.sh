#!/bin/bash
# Linda's HR System Startup Script
# Starts all HR system components

echo "👔 Starting Linda's HR Management System..."

# Start HR API
echo "Starting HR API..."
python3 /Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/hr/api/hr_api.py &
HR_API_PID=$!

# Start monitoring (if needed)
echo "HR system components started"
echo "HR API PID: $HR_API_PID"

# Save PIDs for shutdown
echo $HR_API_PID > "/Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/hr/startup/hr_pids.txt"

echo "✅ Linda's HR system is operational"
echo "👔 Linda: 系统已就绪！(System ready!)"
