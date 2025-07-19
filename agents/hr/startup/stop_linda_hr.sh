#!/bin/bash
# Linda's HR System Shutdown Script

echo "👔 Stopping Linda's HR Management System..."

if [ -f /Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/hr/startup/hr_pids.txt ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping process $pid"
            kill $pid
        fi
    done < /Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/hr/startup/hr_pids.txt
    rm /Users/weixiangzhang/Local_Dev/LibraryOfBabel/agents/hr/startup/hr_pids.txt
fi

echo "✅ HR system stopped"
echo "👔 Linda: 系统关闭 (System shutdown complete)"
