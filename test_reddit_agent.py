#!/usr/bin/env python3
"""
Test Reddit Bibliophile Agent with our available ebooks
"""

import sys
import os
from pathlib import Path

# Add agent path
sys.path.append('agents/reddit_bibliophile')

from reddit_bibliophile_agent import RedditBibliophileAgent

def main():
    print("🤓 Testing Reddit Bibliophile Agent - u/DataScientistBookworm")
    print("=" * 60)
    
    # Initialize agent
    agent = RedditBibliophileAgent()
    
    # Check what ebooks we have
    downloads_dir = Path('ebooks/downloads')
    ebooks = list(downloads_dir.glob('*.epub'))
    
    print(f"📚 Found {len(ebooks)} ebook(s) to analyze:")
    for book in ebooks:
        print(f"   - {book.name}")
    
    if len(ebooks) == 0:
        print("❌ No ebooks found to analyze")
        return
    
    print(f"\n🧠 Starting Reddit-style analysis of {len(ebooks)} books...")
    
    try:
        # Run the full analysis (this will find and analyze our books)
        analysis_result = agent.run_full_analysis(target_books=len(ebooks))
        
        print(f"✅ Reddit analysis complete!")
        print(f"   📊 Books analyzed: {analysis_result.get('books_analyzed', 0)}")
        print(f"   📊 Reports generated: {analysis_result.get('reports_generated', 0)}")
        print(f"   🕸️ Knowledge graph created: {analysis_result.get('knowledge_graph_created', False)}")
        
        if analysis_result.get('reddit_analysis_file'):
            print(f"   📝 Reddit post saved: {analysis_result['reddit_analysis_file']}")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 Reddit agent testing complete!")
    print(f"📊 Check 'reports/reddit_analysis/' for detailed results")

if __name__ == "__main__":
    main()