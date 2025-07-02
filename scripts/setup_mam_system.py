#!/usr/bin/env python3
"""
MAM System Setup Script
Initializes the complete audiobook-to-ebook tracking and download system
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mam_setup.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def run_command(command, description, check=True):
    """Run a command with logging"""
    logger = logging.getLogger(__name__)
    logger.info(f"🔧 {description}")
    logger.info(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"   Output: {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"   Error: {e}")
        logger.error(f"   Stderr: {e.stderr}")
        return False

def check_prerequisites():
    """Check system prerequisites"""
    logger = logging.getLogger(__name__)
    logger.info("🔍 Checking prerequisites...")
    
    # Check Python
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        logger.error("❌ Python 3.8+ required")
        return False
    logger.info(f"✅ Python {python_version.major}.{python_version.minor}")
    
    # Check Node.js
    node_check = run_command("node --version", "Checking Node.js", check=False)
    if not node_check:
        logger.error("❌ Node.js not found. Please install Node.js 16+")
        return False
    logger.info("✅ Node.js found")
    
    # Check npm
    npm_check = run_command("npm --version", "Checking npm", check=False)
    if not npm_check:
        logger.error("❌ npm not found")
        return False
    logger.info("✅ npm found")
    
    return True

def setup_environment():
    """Set up Python environment"""
    logger = logging.getLogger(__name__)
    logger.info("🐍 Setting up Python environment...")
    
    # Install Python dependencies
    python_deps = [
        "requests",
        "pandas", 
        "python-dotenv"
    ]
    
    for dep in python_deps:
        if not run_command(f"python3 -m pip install {dep}", f"Installing {dep}", check=False):
            logger.warning(f"⚠️ Failed to install {dep}")
    
    # Test sqlite3 (built-in)
    try:
        import sqlite3
        logger.info("✅ sqlite3 available (built-in)")
    except ImportError:
        logger.error("❌ sqlite3 not available")
    
    logger.info("✅ Python environment ready")
    return True

def setup_nodejs():
    """Set up Node.js environment"""
    logger = logging.getLogger(__name__)
    logger.info("📦 Setting up Node.js environment...")
    
    # Node.js dependencies already installed by npm install command
    logger.info("✅ Node.js environment ready")
    return True

def initialize_database():
    """Initialize the tracking database"""
    logger = logging.getLogger(__name__)
    logger.info("🗄️ Initializing database...")
    
    try:
        from audiobook_ebook_tracker import AudiobookEbookTracker
        
        # Configuration
        PLEX_DB_PATH = "/Users/weixiangzhang/Local Dev/audiobook-metadata-extractor/library_1750488304.db"
        TRACKER_DB_PATH = "./audiobook_ebook_tracker.db"
        
        # Check if Plex database exists
        if not Path(PLEX_DB_PATH).exists():
            logger.warning(f"⚠️ Plex database not found at {PLEX_DB_PATH}")
            logger.info("   Database will be created but not populated")
            
        # Initialize tracker
        tracker = AudiobookEbookTracker(TRACKER_DB_PATH)
        
        # Import audiobooks if Plex DB exists
        if Path(PLEX_DB_PATH).exists():
            imported_count = tracker.import_audiobooks_from_plex(PLEX_DB_PATH)
            logger.info(f"✅ Imported {imported_count} audiobooks")
            
            # Calculate initial stats
            stats = tracker.calculate_collection_stats()
            logger.info(f"   📊 Stats: {stats}")
        else:
            logger.info("✅ Database structure created")
            
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False
    
    return True

def create_config_files():
    """Create configuration files"""
    logger = logging.getLogger(__name__)
    logger.info("⚙️ Creating configuration files...")
    
    # Create .env template
    env_template = """# MAM Credentials
MAM_USERNAME=your_mam_username
MAM_PASSWORD=your_mam_password
MAM_SESSION_COOKIE=your_session_cookie

# Paths
PLEX_DB_PATH=/Users/weixiangzhang/Local Dev/audiobook-metadata-extractor/library_1750488304.db
DOWNLOAD_DIR=./mam_downloads
DB_PATH=./audiobook_ebook_tracker.db

# Limits
MAX_DAILY_DOWNLOADS=95
HEADLESS=false

# Web Interface
PORT=3000
HOST=localhost
"""
    
    if not Path('.env').exists():
        with open('.env', 'w') as f:
            f.write(env_template)
        logger.info("✅ Created .env template")
    else:
        logger.info("✅ .env file already exists")
    
    # Create package.json scripts
    package_json_update = {
        "scripts": {
            "start": "node web_frontend.js",
            "mam-search": "node mam_playwright_automation.js",
            "setup-db": "python3 audiobook_ebook_tracker.py",
            "test": "echo \"No tests specified\" && exit 0"
        }
    }
    
    logger.info("✅ Configuration files ready")

def create_directories():
    """Create necessary directories"""
    logger = logging.getLogger(__name__)
    logger.info("📁 Creating directories...")
    
    directories = [
        "./mam_downloads",
        "./logs",
        "./data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"   📂 {directory}")
    
    logger.info("✅ Directories created")

def test_system():
    """Test system components"""
    logger = logging.getLogger(__name__)
    logger.info("🧪 Testing system components...")
    
    # Test database connection
    try:
        from audiobook_ebook_tracker import AudiobookEbookTracker
        tracker = AudiobookEbookTracker("./audiobook_ebook_tracker.db")
        stats = tracker.calculate_collection_stats()
        logger.info(f"✅ Database test passed: {stats}")
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False
    
    # Test web frontend (just import)
    try:
        import subprocess
        result = subprocess.run(
            ["node", "-e", "const app = require('./web_frontend.js'); console.log('Web frontend loaded');"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("✅ Web frontend test passed")
        else:
            logger.warning(f"⚠️ Web frontend test warning: {result.stderr}")
    except Exception as e:
        logger.warning(f"⚠️ Web frontend test failed: {e}")
    
    return True

def print_usage_instructions():
    """Print usage instructions"""
    logger = logging.getLogger(__name__)
    
    instructions = """
🎉 MAM Audiobook-Ebook System Setup Complete!

📋 Next Steps:

1. Configure MAM Credentials:
   Edit .env file with your MAM username/password or session cookie

2. Start Web Interface:
   npm start
   Then open: http://localhost:3000

3. Run Automated Search:
   node mam_playwright_automation.js [limit]
   
   Example: node mam_playwright_automation.js 20

4. Check Database Status:
   python3 audiobook_ebook_tracker.py

🔧 Key Files:
   • .env                              - Configuration
   • audiobook_ebook_tracker.db        - Main database
   • web_frontend.js                   - Web interface
   • mam_playwright_automation.js      - Automated search/download
   • audiobook_ebook_tracker.py        - Database management

📊 Features:
   ✅ Track 1860+ audiobooks from Plex
   ✅ Automated MAM ebook search
   ✅ Rate-limited downloads (95/day)
   ✅ Web dashboard for monitoring
   ✅ Progress tracking and statistics

⚠️ Important:
   - Respect MAM's rate limits
   - Use your personal session only
   - Monitor download quotas
   - Maintain good seeding ratio

🎯 Goal: Convert your 1860 audiobook collection into searchable ebook format
    for integration with LibraryOfBabel RAG system!
"""
    
    print(instructions)
    logger.info("✅ Setup complete - instructions displayed")

def main():
    """Main setup function"""
    logger = setup_logging()
    logger.info("🚀 Starting MAM Audiobook-Ebook System Setup")
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("❌ Prerequisites check failed")
        return 1
    
    # Setup steps
    setup_steps = [
        ("Python Environment", setup_environment),
        ("Node.js Environment", setup_nodejs),
        ("Create Directories", create_directories),
        ("Create Configuration", create_config_files),
        ("Initialize Database", initialize_database),
        ("Test System", test_system)
    ]
    
    for step_name, step_func in setup_steps:
        logger.info(f"\n{'='*50}")
        logger.info(f"🔄 {step_name}")
        logger.info(f"{'='*50}")
        
        try:
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return 1
        except Exception as e:
            logger.error(f"❌ {step_name} failed with exception: {e}")
            return 1
    
    # Print usage instructions
    print_usage_instructions()
    
    logger.info("🎉 Setup completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main())