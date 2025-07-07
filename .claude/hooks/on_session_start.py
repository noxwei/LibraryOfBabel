#!/usr/bin/env python3
"""
🎣 Claude Code Session Start Hook
===============================

Automatically executed when a new Claude Code session begins.
Ensures Linda's HR system starts tracking immediately.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_hr_initialization():
    """Run HR auto-initialization script"""
    
    # Get project root directory
    project_root = Path(__file__).parent.parent.parent
    auto_init_script = project_root / "scripts" / "auto_init_hr.py"
    
    print("🎣 Claude Code Session Start Hook Triggered")
    print("=" * 45)
    
    if auto_init_script.exists():
        try:
            # Change to project directory
            os.chdir(project_root)
            
            # Run HR auto-initialization
            result = subprocess.run([
                sys.executable, str(auto_init_script)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ HR auto-initialization completed successfully")
                print(result.stdout)
            else:
                print("⚠️  HR auto-initialization had issues:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("⏰ HR initialization timed out (30s) - continuing anyway")
        except Exception as e:
            print(f"❌ HR initialization failed: {e}")
    else:
        print(f"⚠️  HR auto-init script not found: {auto_init_script}")
        print("Continuing without HR initialization")

def main():
    """Main hook execution"""
    run_hr_initialization()

if __name__ == "__main__":
    main()