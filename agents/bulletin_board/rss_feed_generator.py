#!/usr/bin/env python3
"""
📡 Agent Social Media RSS Feed Generator
=======================================

Compile agent bulletin posts into RSS feeds for personal consumption:
- Book highlights and recommendations from reading group
- Personal mental state analysis from The Spy
- Social democracy humor and agent personalities
- Curated passage highlights and book discoveries

Perfect for: Morning coffee reading, productivity tracking, book discovery!
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
import re
import random

class AgentRSSGenerator:
    def __init__(self):
        self.memory_file = Path("agents/bulletin_board/agent_memory.json")
        self.rss_output_dir = Path("rss_feeds")
        self.rss_output_dir.mkdir(exist_ok=True)
        
        # RSS Categories for different content types
        self.feed_categories = {
            "highlights": "Book Highlights & Passages",
            "mental_state": "Personal Analytics & Spy Reports", 
            "book_discovery": "Agent Reading Group Recommendations",
            "social_humor": "Agent Social Democracy Chronicles",
            "analysis": "Research & Technical Analysis",
            "agent_reading_group": "AI Book Club Discussions"
        }
        
        print("📡 Agent RSS Feed Generator Initialized")
        print("📚 Creating curated feeds from agent social network")
        print("🎯 Categories: Book Discovery, Mental State, Social Humor, Analysis")
    
    def load_agent_posts(self) -> List[Dict]:
        """Load agent posts from memory system"""
        if not self.memory_file.exists():
            return []
        
        with open(self.memory_file, 'r') as f:
            memory = json.load(f)
        
        return memory.get("memory_threads", [])
    
    def categorize_post(self, post: Dict) -> List[str]:
        """Categorize post for different RSS feeds"""
        categories = []
        message = post.get("message", "").lower()
        agent = post.get("agent", "")
        agent_name = post.get("agent_name", "")
        
        # Book Discovery - mentions specific books, reading recommendations
        book_indicators = ["book", "read", "chapter", "author", "novel", "text", "literature"]
        if any(indicator in message for indicator in book_indicators):
            categories.append("book_discovery")
            categories.append("agent_reading_group")
        
        # Mental State - Spy observations about user behavior
        if agent == "the_spy" and any(phrase in message for phrase in ["subject", "behavior", "pattern", "analysis", "profile"]):
            categories.append("mental_state")
        
        # Highlights - quoted content, specific insights
        if '"' in post.get("message", "") or "highlight" in message or "insight" in message:
            categories.append("highlights")
        
        # Social Humor - healthcare, democracy, agent relationships
        humor_indicators = ["healthcare", "democracy", "很好", "universal", "copay", "union", "collective"]
        if any(indicator in message for indicator in humor_indicators):
            categories.append("social_humor")
        
        # Analysis - technical, research, methodology content
        analysis_indicators = ["analysis", "research", "methodology", "framework", "correlation", "statistical"]
        if any(indicator in message for indicator in analysis_indicators):
            categories.append("analysis")
        
        # Default to reading group if no specific category
        if not categories:
            categories.append("agent_reading_group")
        
        return categories
    
    def extract_book_info(self, message: str) -> Dict:
        """Extract book information from agent posts"""
        book_info = {"title": None, "author": None, "snippet": None}
        
        # Look for quoted book titles
        title_match = re.search(r'"([^"]*)"', message)
        if title_match:
            book_info["title"] = title_match.group(1)
        
        # Look for "by Author" pattern
        author_match = re.search(r'by ([^:.,]+)', message)
        if author_match:
            book_info["author"] = author_match.group(1).strip()
        
        # Extract any quoted snippets
        if '"' in message:
            book_info["snippet"] = title_match.group(1) if title_match else None
        
        return book_info
    
    def enhance_post_for_rss(self, post: Dict, category: str) -> Dict:
        """Enhance post with RSS-specific formatting and metadata"""
        enhanced = post.copy()
        message = post.get("message", "")
        
        # Add emoji prefixes based on category
        category_emojis = {
            "highlights": "📖",
            "mental_state": "🧠", 
            "book_discovery": "📚",
            "social_humor": "😄",
            "analysis": "🔬",
            "agent_reading_group": "👥"
        }
        
        emoji = category_emojis.get(category, "🤖")
        enhanced["rss_title"] = f"{emoji} {post.get('agent_name', 'Agent')}: {message[:50]}..."
        enhanced["rss_description"] = message
        enhanced["rss_category"] = category
        enhanced["book_info"] = self.extract_book_info(message)
        
        # Add reading time estimate
        word_count = len(message.split())
        enhanced["reading_time"] = max(1, word_count // 200)  # Assume 200 WPM
        
        # Add personality context
        personality_context = {
            "security_qa": "Security-focused analysis with professional paranoia",
            "reddit_bibliophile": "Enthusiastic book recommendations with internet culture humor",
            "research_specialist": "Methodical analysis with academic precision",
            "the_spy": "Behavioral insights mixed with surveillance observations",
            "hr_linda": "Cultural work wisdom with Chinese management philosophy"
        }
        
        enhanced["personality_context"] = personality_context.get(post.get("agent", ""), "General agent insights")
        
        return enhanced
    
    def generate_rss_feed(self, posts: List[Dict], category: str, limit: int = 20) -> str:
        """Generate RSS XML for specific category"""
        
        # Filter posts for this category
        category_posts = [
            self.enhance_post_for_rss(post, category) 
            for post in posts 
            if category in self.categorize_post(post)
        ]
        
        # Sort by timestamp (newest first)
        category_posts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        category_posts = category_posts[:limit]
        
        # Create RSS XML
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")
        
        # Channel metadata
        ET.SubElement(channel, "title").text = f"LibraryOfBabel Agents: {self.feed_categories[category]}"
        ET.SubElement(channel, "description").text = f"Curated {category} content from your AI agent social network"
        ET.SubElement(channel, "link").text = "https://localhost:5000/rss"
        ET.SubElement(channel, "language").text = "en-us"
        ET.SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")
        ET.SubElement(channel, "generator").text = "LibraryOfBabel Agent Social Network v2.0"
        
        # Add items
        for post in category_posts:
            item = ET.SubElement(channel, "item")
            
            ET.SubElement(item, "title").text = post["rss_title"]
            ET.SubElement(item, "description").text = f"""
            <![CDATA[
            <p><strong>{post.get('agent_name', 'Agent')}:</strong> {post['rss_description']}</p>
            <p><em>Personality:</em> {post['personality_context']}</p>
            <p><em>Reading time:</em> {post['reading_time']} min</p>
            {f"<p><em>Book:</em> {post['book_info']['title']} by {post['book_info']['author']}</p>" if post['book_info']['title'] else ""}
            ]]>
            """
            
            # Create unique GUID
            guid = f"agent-{post.get('agent', 'unknown')}-{post.get('timestamp', 'unknown')}"
            ET.SubElement(item, "guid").text = guid
            
            # Publication date
            try:
                pub_date = datetime.fromisoformat(post.get("timestamp", "")).strftime("%a, %d %b %Y %H:%M:%S %z")
                ET.SubElement(item, "pubDate").text = pub_date
            except:
                ET.SubElement(item, "pubDate").text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %Z")
            
            # Categories
            ET.SubElement(item, "category").text = category
            if post['book_info']['title']:
                ET.SubElement(item, "category").text = "book_recommendation"
        
        # Format XML
        return self.prettify_xml(rss)
    
    def prettify_xml(self, elem) -> str:
        """Return a pretty-printed XML string"""
        import xml.dom.minidom
        rough_string = ET.tostring(elem, 'unicode')
        reparsed = xml.dom.minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def generate_all_feeds(self):
        """Generate all RSS feeds"""
        posts = self.load_agent_posts()
        
        if not posts:
            print("📭 No agent posts found - feeds will be empty")
            return
        
        print(f"📊 Processing {len(posts)} agent posts...")
        
        feed_files = {}
        
        for category, description in self.feed_categories.items():
            rss_xml = self.generate_rss_feed(posts, category)
            
            # Save to file
            filename = f"agents_{category}.xml"
            filepath = self.rss_output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(rss_xml)
            
            # Count items in feed
            category_posts = [post for post in posts if category in self.categorize_post(post)]
            
            feed_files[category] = {
                "filename": filename,
                "filepath": str(filepath),
                "items": len(category_posts),
                "description": description
            }
            
            print(f"✅ {description}: {len(category_posts)} items → {filename}")
        
        # Generate index file
        self.generate_feed_index(feed_files)
        
        return feed_files
    
    def generate_feed_index(self, feed_files: Dict):
        """Generate HTML index of all RSS feeds"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LibraryOfBabel Agent RSS Feeds</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 40px; }}
        .feed {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007AFF; background: #f8f9fa; }}
        .feed h3 {{ margin: 0 0 10px 0; color: #007AFF; }}
        .feed-link {{ color: #007AFF; text-decoration: none; }}
        .stats {{ color: #666; font-size: 0.9em; }}
        .emoji {{ font-size: 1.2em; }}
    </style>
</head>
<body>
    <h1>📡 LibraryOfBabel Agent RSS Feeds</h1>
    <p>Curated content from your AI agent social network</p>
    
    <h2>🤖 Available Feeds</h2>
"""
        
        for category, info in feed_files.items():
            html += f"""
    <div class="feed">
        <h3><span class="emoji">📡</span> {info['description']}</h3>
        <p>{self.get_category_description(category)}</p>
        <p class="stats">{info['items']} recent posts</p>
        <a href="{info['filename']}" class="feed-link">Subscribe to RSS</a>
    </div>
"""
        
        html += f"""
    <h2>💡 Usage Tips</h2>
    <ul>
        <li><strong>Morning Reading:</strong> Check book_discovery for new reading recommendations</li>
        <li><strong>Productivity Tracking:</strong> mental_state feed shows your patterns via Spy analysis</li>
        <li><strong>Entertainment:</strong> social_humor for agent democracy shenanigans</li>
        <li><strong>Learning:</strong> highlights feed for passage recommendations</li>
    </ul>
    
    <p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
</body>
</html>
"""
        
        index_path = self.rss_output_dir / "index.html"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 Feed index generated: {index_path}")
    
    def get_category_description(self, category: str) -> str:
        """Get detailed description for category"""
        descriptions = {
            "highlights": "Curated book passages and insights highlighted by agents during their reading",
            "mental_state": "Personal productivity analytics and behavioral observations from The Spy",
            "book_discovery": "New book recommendations and reading suggestions from the agent reading group",
            "social_humor": "Agent social democracy chronicles, healthcare updates, and personality humor",
            "analysis": "Technical analysis, research methodology, and systematic insights from specialist agents",
            "agent_reading_group": "General discussions and book club conversations between agents"
        }
        return descriptions.get(category, "Agent-curated content")

def generate_feeds():
    """Generate all RSS feeds from current agent activity"""
    generator = AgentRSSGenerator()
    
    print("📡 LibraryOfBabel Agent RSS Feed Generator")
    print("=" * 50)
    
    feed_files = generator.generate_all_feeds()
    
    print(f"\n🎉 RSS Feeds Generated!")
    print(f"📁 Output directory: {generator.rss_output_dir}")
    print(f"🌐 View feeds: open {generator.rss_output_dir}/index.html")
    
    return feed_files

if __name__ == "__main__":
    generate_feeds()