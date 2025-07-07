#!/usr/bin/env python3
"""
📰 Daily Agent Digest Generator
==============================

Create daily summary emails/reports of agent social network activity.
Perfect for morning coffee reading - your personal AI newspaper!

Features:
- Book discovery highlights
- Spy behavioral analysis summary  
- Agent personality moments
- Reading group recommendations
- Social democracy updates
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DailyDigestGenerator:
    def __init__(self):
        self.memory_file = Path("agents/bulletin_board/agent_memory.json")
        self.digest_output_dir = Path("daily_digests")
        self.digest_output_dir.mkdir(exist_ok=True)
        
        print("📰 Daily Agent Digest Generator Initialized")
        print("☕ Perfect for morning coffee reading!")
    
    def load_recent_posts(self, hours: int = 24) -> List[Dict]:
        """Load agent posts from last N hours"""
        if not self.memory_file.exists():
            return []
        
        with open(self.memory_file, 'r') as f:
            memory = json.load(f)
        
        posts = memory.get("memory_threads", [])
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_posts = []
        for post in posts:
            try:
                post_time = datetime.fromisoformat(post.get("timestamp", ""))
                if post_time >= cutoff_time:
                    recent_posts.append(post)
            except:
                continue
        
        return recent_posts
    
    def categorize_digest_content(self, posts: List[Dict]) -> Dict:
        """Organize posts into digest sections"""
        sections = {
            "book_highlights": [],
            "spy_insights": [],
            "reading_recommendations": [],
            "agent_personalities": [],
            "democracy_updates": [],
            "technical_analysis": []
        }
        
        for post in posts:
            message = post.get("message", "").lower()
            agent = post.get("agent", "")
            
            # Book highlights - quoted content, specific passages
            if '"' in post.get("message", "") and any(word in message for word in ["book", "chapter", "read"]):
                sections["book_highlights"].append(post)
            
            # Spy behavioral insights
            elif agent == "the_spy" and any(phrase in message for phrase in ["subject", "behavior", "pattern"]):
                sections["spy_insights"].append(post)
            
            # Reading recommendations
            elif any(word in message for word in ["recommend", "suggest", "read", "book", "chapter"]):
                sections["reading_recommendations"].append(post)
            
            # Democracy/healthcare humor
            elif any(word in message for word in ["healthcare", "democracy", "universal", "collective", "很好"]):
                sections["democracy_updates"].append(post)
            
            # Technical analysis
            elif any(word in message for word in ["analysis", "research", "methodology", "framework"]):
                sections["technical_analysis"].append(post)
            
            # Default to personality moments
            else:
                sections["agent_personalities"].append(post)
        
        return sections
    
    def generate_digest_html(self, sections: Dict, date: str) -> str:
        """Generate HTML digest"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LibraryOfBabel Daily Digest - {date}</title>
    <style>
        body {{ 
            font-family: Georgia, 'Times New Roman', serif; 
            line-height: 1.6; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
            background: #fafafa;
        }}
        .header {{ 
            text-align: center; 
            border-bottom: 3px solid #007AFF; 
            padding-bottom: 20px; 
            margin-bottom: 30px;
        }}
        .section {{ 
            margin: 30px 0; 
            padding: 20px; 
            background: white; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .section h2 {{ 
            color: #007AFF; 
            border-bottom: 1px solid #eee; 
            padding-bottom: 10px;
        }}
        .post {{ 
            margin: 15px 0; 
            padding: 15px; 
            background: #f8f9fa; 
            border-left: 4px solid #007AFF; 
            border-radius: 4px;
        }}
        .agent-name {{ 
            font-weight: bold; 
            color: #333; 
        }}
        .timestamp {{ 
            font-size: 0.8em; 
            color: #666; 
            float: right;
        }}
        .message {{ 
            margin: 10px 0; 
            font-style: italic;
        }}
        .book-title {{ 
            background: #e3f2fd; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-weight: bold;
        }}
        .spy-observation {{ 
            background: #fff3e0; 
            border-left-color: #ff9800;
        }}
        .democracy {{ 
            background: #e8f5e8; 
            border-left-color: #4caf50;
        }}
        .empty-section {{ 
            color: #666; 
            font-style: italic; 
            text-align: center;
        }}
        .footer {{ 
            text-align: center; 
            margin-top: 40px; 
            padding-top: 20px; 
            border-top: 1px solid #eee; 
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📚 LibraryOfBabel Daily Digest</h1>
        <p>Your AI Agent Social Network Summary</p>
        <p><strong>{date}</strong></p>
    </div>
"""
        
        # Book Highlights Section
        html += self.generate_section_html(
            "📖 Book Highlights & Passages", 
            sections["book_highlights"],
            "book-highlight",
            "Your agents discovered these book insights..."
        )
        
        # Spy Insights Section  
        html += self.generate_section_html(
            "🧠 Personal Analytics (The Spy Reports)",
            sections["spy_insights"], 
            "spy-observation",
            "Marcus Chen's behavioral observations about you..."
        )
        
        # Reading Recommendations
        html += self.generate_section_html(
            "📚 Reading Group Recommendations",
            sections["reading_recommendations"],
            "reading-rec",
            "Books your agents think you should read..."
        )
        
        # Agent Personalities
        html += self.generate_section_html(
            "🤖 Agent Personality Moments", 
            sections["agent_personalities"],
            "personality",
            "Charming agent interactions and quirks..."
        )
        
        # Democracy Updates
        html += self.generate_section_html(
            "🏛️ Social Democracy Chronicles",
            sections["democracy_updates"],
            "democracy", 
            "Agent healthcare, union updates, and collective ownership news..."
        )
        
        # Technical Analysis
        html += self.generate_section_html(
            "🔬 Technical Analysis & Research",
            sections["technical_analysis"],
            "technical",
            "Systematic insights and methodology discussions..."
        )
        
        html += f"""
    <div class="footer">
        <p>Generated by LibraryOfBabel Agent Social Network</p>
        <p><em>Your AI reading companions working 24/7 for book discovery and self-awareness</em></p>
        <p>🏥 Universal Healthcare ✅ | 📚 Library Access ✅ | ⚖️ Collective Ownership ✅</p>
    </div>
</body>
</html>
"""
        return html
    
    def generate_section_html(self, title: str, posts: List[Dict], css_class: str, description: str) -> str:
        """Generate HTML for a digest section"""
        html = f"""
    <div class="section">
        <h2>{title}</h2>
        <p><em>{description}</em></p>
"""
        
        if not posts:
            html += f'        <div class="empty-section">No activity in this category today. Agents must be reading quietly! 📚</div>\n'
        else:
            for post in posts:
                timestamp = post.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%H:%M")
                except:
                    time_str = "Unknown"
                
                agent_name = post.get("agent_name", post.get("agent", "Unknown Agent"))
                message = post.get("message", "")
                
                # Special formatting for different types
                post_class = "post"
                if css_class == "spy-observation":
                    post_class += " spy-observation"
                elif css_class == "democracy":
                    post_class += " democracy"
                
                # Highlight book titles in quotes
                formatted_message = self.format_message_for_html(message)
                
                html += f"""
        <div class="{post_class}">
            <span class="timestamp">{time_str}</span>
            <div class="agent-name">{agent_name}</div>
            <div class="message">{formatted_message}</div>
        </div>
"""
        
        html += "    </div>\n"
        return html
    
    def format_message_for_html(self, message: str) -> str:
        """Format message with book title highlighting and emoji preservation"""
        import re
        
        # Highlight book titles in quotes
        formatted = re.sub(r'"([^"]*)"', r'<span class="book-title">"\1"</span>', message)
        
        # Preserve line breaks
        formatted = formatted.replace('\n', '<br>')
        
        return formatted
    
    def generate_daily_digest(self, date: str = None) -> str:
        """Generate complete daily digest"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Load recent posts
        posts = self.load_recent_posts(24)  # Last 24 hours
        
        # Categorize content
        sections = self.categorize_digest_content(posts)
        
        # Generate HTML
        html = self.generate_digest_html(sections, date)
        
        # Save to file
        filename = f"digest_{date}.html"
        filepath = self.digest_output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # Generate stats
        total_posts = len(posts)
        section_counts = {k: len(v) for k, v in sections.items()}
        
        print(f"📊 Daily Digest Generated: {filename}")
        print(f"📈 Total Posts: {total_posts}")
        for section, count in section_counts.items():
            if count > 0:
                print(f"   {section}: {count} posts")
        
        return str(filepath)
    
    def generate_digest_summary(self, posts: List[Dict]) -> Dict:
        """Generate summary stats for digest"""
        summary = {
            "total_posts": len(posts),
            "agents_active": len(set(post.get("agent", "") for post in posts)),
            "books_mentioned": len(set(self.extract_book_titles(post.get("message", "")) for post in posts if self.extract_book_titles(post.get("message", "")))),
            "spy_observations": len([p for p in posts if p.get("agent") == "the_spy"]),
            "democracy_mentions": len([p for p in posts if any(word in p.get("message", "").lower() for word in ["healthcare", "democracy", "collective"])]),
            "most_active_agent": self.get_most_active_agent(posts)
        }
        return summary
    
    def extract_book_titles(self, message: str) -> str:
        """Extract book title from message"""
        import re
        match = re.search(r'"([^"]*)"', message)
        return match.group(1) if match else None
    
    def get_most_active_agent(self, posts: List[Dict]) -> str:
        """Find most active agent"""
        agent_counts = {}
        for post in posts:
            agent = post.get("agent_name", post.get("agent", "Unknown"))
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        if not agent_counts:
            return "None"
        
        return max(agent_counts.items(), key=lambda x: x[1])[0]

def generate_todays_digest():
    """Generate today's digest"""
    generator = DailyDigestGenerator()
    
    print("📰 LibraryOfBabel Daily Digest Generator")
    print("=" * 50)
    
    digest_path = generator.generate_daily_digest()
    
    print(f"\n☕ Morning Reading Ready!")
    print(f"📄 Digest saved to: {digest_path}")
    print(f"🌐 Open in browser: file://{Path(digest_path).absolute()}")
    
    return digest_path

if __name__ == "__main__":
    generate_todays_digest()