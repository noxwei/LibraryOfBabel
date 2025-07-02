#!/usr/bin/env python3
"""
Test script to verify the cleaned up folder structure works properly
"""

import sys
import os
from pathlib import Path

# Add agents path
sys.path.append('agents/reddit_bibliophile')

def test_folder_structure():
    """Test that all folders are properly organized"""
    
    expected_folders = [
        'ebooks/torrents',
        'ebooks/downloads', 
        'ebooks/analysis',
        'audiobooks/samples',
        'audiobooks/transcripts',
        'agents/reddit_bibliophile',
        'agents/qa_system',
        'agents/seeding_monitor',
        'agents/logs',
        'database/schema',
        'database/data',
        'config/agent_configs',
        'config/system_configs',
        'reports/qa_reports',
        'reports/knowledge_graphs',
        'reports/reddit_analysis',
        'src/epub_processing',
        'src/database_management',
        'src/search_indexing'
    ]
    
    print("🔍 Testing cleaned folder structure...")
    
    all_good = True
    for folder in expected_folders:
        folder_path = Path(folder)
        if folder_path.exists():
            print(f"✅ {folder}")
        else:
            print(f"❌ {folder} - Missing!")
            all_good = False
    
    return all_good

def test_reddit_agent():
    """Test that Reddit agent can be imported with new structure"""
    print("\n🤓 Testing Reddit Bibliophile Agent...")
    
    try:
        # Add the agent path to Python path
        agent_path = os.path.abspath('agents/reddit_bibliophile')
        if agent_path not in sys.path:
            sys.path.insert(0, agent_path)
        
        from reddit_bibliophile_agent import RedditBibliophileAgent
        
        # Initialize agent
        agent = RedditBibliophileAgent()
        
        print("✅ Reddit agent imported successfully")
        print(f"✅ Database path: {agent.db_path}")
        print(f"✅ Analysis dir: {agent.analysis_dir}")
        print(f"✅ Downloads dir: {agent.downloads_dir}")
        
        return True
        
    except Exception as e:
        print(f"❌ Reddit agent failed: {e}")
        return False

def test_database_access():
    """Test database accessibility"""
    print("\n🗄️ Testing database access...")
    
    db_path = Path('database/data/audiobook_ebook_tracker.db')
    
    if db_path.exists():
        print(f"✅ Database found: {db_path}")
        print(f"✅ Database size: {db_path.stat().st_size / 1024 / 1024:.1f} MB")
        return True
    else:
        print(f"❌ Database not found: {db_path}")
        return False

def main():
    """Run all tests"""
    print("🧹 LibraryOfBabel - Clean Folder Structure Test")
    print("=" * 50)
    
    results = []
    
    # Test folder structure
    results.append(test_folder_structure())
    
    # Test Reddit agent
    results.append(test_reddit_agent())
    
    # Test database
    results.append(test_database_access())
    
    print("\n📊 Test Results:")
    passed = sum(results)
    total = len(results)
    
    print(f"   Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Clean structure is working!")
        return 0
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    exit(main())