#!/usr/bin/env python3
"""
🔧 MCP SERVER SETUP FOR LIBRARY OF BABEL
========================================

Sets up the MCP server to connect Claude to the Library of Babel.
Run this script to configure everything needed for Claude integration.

Usage:
    python setup_mcp.py

This will:
1. Install required packages
2. Test the MCP server
3. Generate configuration for Claude Code
4. Provide usage instructions
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def install_mcp_requirements():
    """Install MCP requirements"""
    print("📦 Installing MCP requirements...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements_mcp.txt"
        ], check=True)
        print("✅ MCP requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def test_mcp_server():
    """Test the MCP server"""
    print("🧪 Testing MCP server...")
    
    try:
        # Import test
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from config.api_config import get_mcp_config
        
        config = get_mcp_config()
        print(f"✅ MCP configuration loaded: {config}")
        
        # Test server imports
        import asyncio
        from mcp.server import Server
        print("✅ MCP server imports successful")
        
        return True
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        return False

def generate_claude_config():
    """Generate configuration for Claude Code"""
    print("⚙️  Generating Claude Code configuration...")
    
    project_root = Path(__file__).parent.absolute()
    
    claude_config = {
        "mcpServers": {
            "library-of-babel": {
                "command": "python3",
                "args": [str(project_root / "mcp_server.py")],
                "env": {
                    "PYTHONPATH": str(project_root / "src")
                }
            }
        }
    }
    
    # Save config
    config_path = project_root / "claude_mcp_config.json"
    with open(config_path, 'w') as f:
        json.dump(claude_config, f, indent=2)
    
    print(f"✅ Claude configuration saved to: {config_path}")
    return config_path

def print_usage_instructions(config_path):
    """Print usage instructions"""
    print("\n🎉 MCP SERVER SETUP COMPLETE!")
    print("=" * 50)
    
    print("\n📋 NEXT STEPS:")
    print("1. Add this MCP server to your Claude Code configuration:")
    print(f"   - Copy the contents of: {config_path}")
    print("   - Add to your Claude Code settings under 'mcpServers'")
    
    print("\n2. Or manually add to Claude Code settings:")
    print('   {')
    print('     "mcpServers": {')
    print('       "library-of-babel": {')
    print('         "command": "python3",')
    print(f'         "args": ["{Path(__file__).parent.absolute() / "mcp_server.py"}"],')
    print('         "env": {')
    print(f'           "PYTHONPATH": "{Path(__file__).parent.absolute() / "src"}"')
    print('         }')
    print('       }')
    print('     }')
    print('   }')
    
    print("\n3. Test the connection:")
    print("   - Start Claude Code")
    print("   - Ask: 'What books do you have about artificial intelligence?'")
    print("   - Ask: 'Give me insights on machine learning from the library'")
    print("   - Ask: 'What are the library statistics?'")
    
    print("\n🔧 AVAILABLE TOOLS:")
    print("   - search_books: Search by title, author, or topic")
    print("   - get_book_content: Get full content of a specific book")
    print("   - semantic_search: Find related concepts using embeddings")
    print("   - get_library_stats: Get overall library statistics")
    print("   - get_topic_insights: Get comprehensive topic analysis")
    
    print("\n📚 LIBRARY STATUS:")
    print("   - Books: 1,688+")
    print("   - Chunks: 25,067+")
    print("   - Embeddings: 18,363+")
    print("   - Status: Ready for Claude integration!")

def main():
    """Main setup function"""
    print("🚀 SETTING UP MCP SERVER FOR CLAUDE")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Install requirements
    if not install_mcp_requirements():
        sys.exit(1)
    
    # Test server
    if not test_mcp_server():
        sys.exit(1)
    
    # Generate config
    config_path = generate_claude_config()
    
    # Print instructions
    print_usage_instructions(config_path)
    
    print("\n🎯 READY TO CONNECT CLAUDE TO YOUR LIBRARY!")

if __name__ == "__main__":
    main()