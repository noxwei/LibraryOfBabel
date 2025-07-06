#!/usr/bin/env python3
"""
LibraryOfBabel Knowledge Graph Explorer
Interactive tool to visualize and explore knowledge connections
"""

import json
import requests
from datetime import datetime
from typing import Dict, List

class KnowledgeGraphExplorer:
    """Interactive knowledge graph explorer for LibraryOfBabel"""
    
    def __init__(self, api_base: str = "http://localhost:5560"):
        self.api_base = api_base
        self.session = requests.Session()
        
        print("🕸️ LibraryOfBabel Knowledge Graph Explorer")
        print("=" * 50)
    
    def api_call(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Make API call to LibraryOfBabel"""
        url = f"{self.api_base}{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ API Error: {e}")
            return {"success": False, "error": str(e)}
    
    def explore_concept_connections(self, concept1: str, concept2: str):
        """Explore connections between two concepts"""
        print(f"\n🔍 Exploring: '{concept1}' ↔ '{concept2}'")
        print("-" * 40)
        
        response = self.api_call("/api/v2/search/cross-reference", "POST", {
            "concept1": concept1,
            "concept2": concept2
        })
        
        if not response.get("success"):
            print("❌ Failed to get connections")
            return
        
        data = response["data"]
        connections = data["direct_connections"]
        
        print(f"📊 Found {len(connections)} direct connections")
        print(f"🎯 AI Analysis: {data.get('analysis', '').strip()}")
        
        print(f"\n📚 Books with both concepts:")
        for i, conn in enumerate(connections, 1):
            print(f"  {i}. **{conn['title']}** by {conn['author']}")
            print(f"     Chapter {conn['chapter_number']} | Similarity: {conn['similarity_score']:.3f}")
            print(f"     Preview: {conn['content_preview'][:100]}...")
            print()
    
    def find_concept_context(self, concept: str, limit: int = 5):
        """Find books and passages that discuss a concept"""
        print(f"\n🧠 Concept Analysis: '{concept}'")
        print("-" * 30)
        
        response = self.api_call(f"/api/v2/search/semantic?q={concept}&limit={limit}&analysis=true")
        
        if not response.get("success"):
            print("❌ Search failed")
            return
        
        data = response["data"]
        results = data["results"]
        
        print(f"📊 Found {len(results)} relevant passages")
        print(f"🎯 AI Analysis: {data.get('analysis', '')}")
        
        print(f"\n📖 Books discussing '{concept}':")
        authors_seen = set()
        for i, result in enumerate(results, 1):
            author = result['author']
            if author not in authors_seen:
                print(f"  {i}. **{result['title']}** by {author}")
                print(f"     Similarity: {result['similarity_score']:.3f}")
                print(f"     Preview: {result['content_preview'][:120]}...")
                authors_seen.add(author)
                print()
    
    def discover_serendipitous_connections(self, theme: str, seed: int = None):
        """Discover unexpected connections using serendipity engine"""
        if seed is None:
            seed = hash(theme) % 1000
        
        print(f"\n🎲 Serendipity Discovery: '{theme}'")
        print("-" * 35)
        
        response = self.api_call("/api/v2/discovery/serendipity", "POST", {
            "theme": theme,
            "seed": seed,
            "chunks": 4
        })
        
        if not response.get("success"):
            print("❌ Serendipity discovery failed")
            return
        
        data = response["data"]
        chunks = data["source_chunks"]
        
        print(f"✨ Generated insight from {len(chunks)} diverse sources")
        print(f"🎭 Authors combined: {', '.join(data['discovery_metadata']['authors_combined'])}")
        print(f"🌈 Conceptual diversity: {data['discovery_metadata']['conceptual_diversity']}/4")
        
        print(f"\n📚 Unexpected connections found:")
        for i, chunk in enumerate(chunks, 1):
            print(f"  {i}. **{chunk['title']}** by {chunk['author']}")
            print(f"     Genre: {chunk['genre']} | Words: {chunk['word_count']}")
            print(f"     Content: {chunk['content'][:150]}...")
            print()
    
    def show_knowledge_map(self, central_concept: str):
        """Show a text-based knowledge map around a central concept"""
        print(f"\n🗺️ Knowledge Map: '{central_concept}'")
        print("=" * 40)
        
        # Get semantic matches for the central concept
        response = self.api_call(f"/api/v2/search/semantic?q={central_concept}&limit=8&analysis=true")
        
        if not response.get("success"):
            print("❌ Failed to generate knowledge map")
            return
        
        data = response["data"]
        results = data["results"]
        authors = data["search_metadata"]["authors_found"]
        
        print(f"🎯 Central Concept: **{central_concept.upper()}**")
        print(f"📊 Connected to {len(results)} passages across {len(authors)} authors")
        print()
        
        # Group by author
        author_connections = {}
        for result in results:
            author = result["author"]
            if author not in author_connections:
                author_connections[author] = []
            author_connections[author].append(result)
        
        print("🕸️ Knowledge Network:")
        for author, connections in author_connections.items():
            print(f"  📚 **{author}**")
            for conn in connections:
                print(f"    ├─ {conn['title']}")
                print(f"    │  Similarity: {conn['similarity_score']:.3f}")
                print(f"    │  Chapter {conn['chapter_number']}")
            print()
    
    def interactive_exploration(self):
        """Interactive knowledge graph exploration"""
        print("\n🚀 Welcome to Interactive Knowledge Exploration!")
        print("Commands:")
        print("  1. 'connect <concept1> <concept2>' - Find connections between concepts")
        print("  2. 'explore <concept>' - Analyze a single concept")
        print("  3. 'map <concept>' - Show knowledge map around concept")
        print("  4. 'serendipity <theme>' - Discover unexpected connections")
        print("  5. 'examples' - Show example queries")
        print("  6. 'quit' - Exit")
        print()
        
        while True:
            try:
                command = input("🔍 Enter command: ").strip().lower()
                
                if command == "quit":
                    print("👋 Happy knowledge exploring!")
                    break
                elif command == "examples":
                    self.show_examples()
                elif command.startswith("connect "):
                    parts = command[8:].split()
                    if len(parts) >= 2:
                        concept1 = parts[0]
                        concept2 = " ".join(parts[1:])
                        self.explore_concept_connections(concept1, concept2)
                    else:
                        print("Usage: connect <concept1> <concept2>")
                elif command.startswith("explore "):
                    concept = command[8:]
                    self.find_concept_context(concept)
                elif command.startswith("map "):
                    concept = command[4:]
                    self.show_knowledge_map(concept)
                elif command.startswith("serendipity "):
                    theme = command[12:]
                    self.discover_serendipitous_connections(theme)
                else:
                    print("❓ Unknown command. Type 'examples' for help.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def show_examples(self):
        """Show example queries"""
        print("\n💡 Example Queries:")
        print("  connect consciousness artificial")
        print("  connect power surveillance")
        print("  connect freedom control")
        print("  explore posthuman")
        print("  explore capitalism")
        print("  map technology")
        print("  map consciousness")
        print("  serendipity digital identity")
        print("  serendipity power structures")
        print()
    
    def quick_demo(self):
        """Run a quick demonstration of knowledge graph capabilities"""
        print("🎬 Quick Knowledge Graph Demo")
        print("=" * 35)
        
        demos = [
            ("consciousness", "artificial intelligence"),
            ("power", "surveillance"),
            ("freedom", "control")
        ]
        
        for concept1, concept2 in demos:
            self.explore_concept_connections(concept1, concept2)
            print("\n" + "="*50 + "\n")
        
        # Serendipity demo
        self.discover_serendipitous_connections("digital consciousness")
        
        # Knowledge map demo
        self.show_knowledge_map("technology")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LibraryOfBabel Knowledge Graph Explorer')
    parser.add_argument('--demo', action='store_true', help='Run quick demo')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--connect', nargs=2, help='Connect two concepts')
    parser.add_argument('--explore', help='Explore a single concept')
    parser.add_argument('--map', help='Show knowledge map for concept')
    
    args = parser.parse_args()
    
    explorer = KnowledgeGraphExplorer()
    
    if args.demo:
        explorer.quick_demo()
    elif args.interactive:
        explorer.interactive_exploration()
    elif args.connect:
        explorer.explore_concept_connections(args.connect[0], args.connect[1])
    elif args.explore:
        explorer.find_concept_context(args.explore)
    elif args.map:
        explorer.show_knowledge_map(args.map)
    else:
        print("\n🎯 Quick commands:")
        print("  python3 knowledge_graph_explorer.py --demo")
        print("  python3 knowledge_graph_explorer.py --interactive")
        print("  python3 knowledge_graph_explorer.py --connect consciousness artificial")
        print("  python3 knowledge_graph_explorer.py --explore technology")
        print("  python3 knowledge_graph_explorer.py --map consciousness")

if __name__ == "__main__":
    main()