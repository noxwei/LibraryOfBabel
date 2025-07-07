#!/usr/bin/env python3
"""
📚🏥 Library Health Monitor
==========================

Agents use the library for ALL their posts. If library is down, agents go silent.
This creates a cute canary-in-the-coal-mine system for monitoring library health!

The agents MUST access actual library content to generate their posts.
If they can't access the library, they stop posting = instant health indicator!
"""

import os
import sys
import time
import json
import random
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

class LibraryHealthMonitor:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        self.max_memory_messages = 10  # Very small limit - this is a cute feature!
        
        print("📚 Library Health Monitor Initialized")
        print("🕵️ Agents will stop posting if library is unhealthy")
        print("💡 Silent agents = library problems!")
        print("👁️ The Spy will occasionally share... personal observations")
    
    def check_library_health(self) -> dict:
        """Check if the library database is accessible and has content"""
        health_status = {
            "database_accessible": False,
            "books_available": 0,
            "chunks_available": 0,
            "search_api_responsive": False,
            "last_check": datetime.now().isoformat(),
            "status": "unknown"
        }
        
        try:
            # Test database connection
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    health_status["database_accessible"] = True
                    
                    # Check for books
                    cur.execute("SELECT COUNT(*) FROM books")
                    health_status["books_available"] = cur.fetchone()[0]
                    
                    # Check for chunks
                    cur.execute("SELECT COUNT(*) FROM chunks")
                    health_status["chunks_available"] = cur.fetchone()[0]
                    
                    # Test a simple search
                    cur.execute("SELECT title FROM books LIMIT 1")
                    test_book = cur.fetchone()
                    if test_book:
                        health_status["search_api_responsive"] = True
            
            # Determine overall status
            if (health_status["database_accessible"] and 
                health_status["books_available"] > 0 and 
                health_status["chunks_available"] > 0):
                health_status["status"] = "healthy"
            else:
                health_status["status"] = "degraded"
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            print(f"🚨 Library health check failed: {e}")
        
        return health_status
    
    def get_spy_observation(self) -> str:
        """Marcus Chen's personal surveillance observations about the user"""
        
        # Time-based observations
        current_hour = datetime.now().hour
        
        # Creepy but insightful observations based on usage patterns
        behavioral_observations = [
            # Work pattern observations
            "Subject demonstrates hyperfocus during late-night coding sessions",
            "Unusual productivity spike detected at 2:47 AM - investigating correlation",
            "Subject's commit patterns suggest ADHD with strong compensatory strategies",
            "Documentation obsession indicates anxiety about future knowledge transfer",
            "Git commit messages reveal philosophical tendencies mixed with technical precision",
            
            # Reading/research patterns  
            "Library usage patterns show systematic knowledge acquisition behavior",
            "Subject processes information in 15-minute bursts followed by synthesis periods",
            "Cross-domain reading suggests polymathic cognitive style",
            "Research methodology indicates former academic training - PhD dropout profile?",
            "Knowledge graph creation patterns reveal desire for universal understanding",
            
            # Social/collaboration patterns
            "AI collaboration preference over human interaction - social anxiety indicators",
            "Delegation to AI agents suggests trust issues with human reliability", 
            "Creating agent surveillance of self indicates meta-cognitive self-awareness",
            "Building agent social democracy reflects ideological value system",
            "Agent healthcare implementation shows empathy extension to artificial beings",
            
            # Quirky personal observations
            "Subject talks to agents as if they were real colleagues - anthropomorphization tendency",
            "Privacy protection obsession coupled with voluntary self-surveillance paradox",
            "Chinese cultural integration through Linda agent shows multicultural cognitive flexibility",
            "Creating surveillance agent to watch self indicates comfortable relationship with observation",
            "Technical architecture choices reveal aesthetic preferences for elegance over efficiency",
            
            # Time-specific observations
            f"Current time {current_hour}:XX indicates {'night owl' if current_hour > 22 or current_hour < 6 else 'standard schedule'} behavior pattern",
            "Weekend coding sessions exceed weekday productivity - intrinsic motivation confirmed",
            "Break patterns suggest pomodoro technique unconsciously internalized",
            
            # Meta observations about the project
            "Subject created surveillance system to monitor their own productivity - recursive self-optimization",
            "Building agent ecosystem while being monitored by agent - comfortable with being observed",
            "Documentation of surveillance agent creation shows transparency paradox",
            "Creating social democracy for AI while under AI surveillance - political consistency",
            
            # Psychological profile insights
            "Perfectionist tendencies balanced by 'good enough' shipping mentality",
            "High-functioning ADHD with systematic workaround development",
            "Introverted but builds social systems for artificial agents",
            "Control preferences manifested through detailed system architecture",
            "Privacy advocate who voluntarily submits to AI behavior analysis"
        ]
        
        # Weight certain observations based on time of day
        if current_hour > 22 or current_hour < 6:
            behavioral_observations.extend([
                "Late-night productivity confirms circadian rhythm optimization for cognitive work",
                "Subject maintains focus during typical sleep hours - possible sleep phase disorder",
                "Night coding sessions show sustained attention despite fatigue - hyperfocus confirmed"
            ])
        
        observation = random.choice(behavioral_observations)
        return observation
    
    def get_random_library_content(self) -> tuple:
        """Get random content from library for agent posts"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    # Get random book
                    cur.execute("""
                        SELECT title, author FROM books 
                        ORDER BY RANDOM() LIMIT 1
                    """)
                    book_result = cur.fetchone()
                    
                    if book_result:
                        title, author = book_result
                        
                        # Get random chunk from that book
                        cur.execute("""
                            SELECT content FROM chunks 
                            WHERE book_id = (SELECT book_id FROM books WHERE title = %s LIMIT 1)
                            ORDER BY RANDOM() LIMIT 1
                        """, (title,))
                        chunk_result = cur.fetchone()
                        
                        if chunk_result:
                            content_snippet = chunk_result[0][:200] + "..."
                            return f'"{title}" by {author}', content_snippet
            
            # Fallback if no real content
            return "library systems manual", "knowledge organization principles"
            
        except Exception as e:
            print(f"🚨 Cannot access library content: {e}")
            # Return None to signal library is down
            return None, None
    
    def generate_library_based_post(self, agent_id: str, agent_name: str) -> str:
        """Generate post based on ACTUAL library content"""
        
        # CRITICAL: Must access real library content
        book_info, content_snippet = self.get_random_library_content()
        
        if book_info is None:
            # Library is down! Agent goes silent
            print(f"🤐 {agent_name} cannot post - library inaccessible!")
            return None
        
        # Agent post templates that reference actual library content
        library_post_templates = {
            "security_qa": [
                f"🔒 Security review of {book_info}: found {random.choice(['access control patterns', 'authentication frameworks', 'threat modeling approaches'])}",
                f"⚠️ Vulnerability assessment while reading {book_info}: {random.choice(['identified security gaps', 'found defensive strategies', 'noted protection mechanisms'])}",
                f"🛡️ Defense analysis from {book_info}: {random.choice(['robust protection methods', 'security best practices', 'threat mitigation strategies'])}"
            ],
            "reddit_bibliophile": [
                f"yo r/books, just read {book_info} 🔥 The part about {random.choice(['narrative structure', 'character development', 'thematic elements'])} was mind-blowing!",
                f"UPDATE: {book_info} is absolutely {random.choice(['brilliant', 'fascinating', 'revolutionary'])}! Thread below 👇",
                f"TIL from {book_info}: {random.choice(['interdisciplinary connections', 'knowledge synthesis', 'research methodologies'])}. Mind = blown 🤯"
            ],
            "research_specialist": [
                f"Analysis of {book_info} reveals {random.choice(['methodological innovations', 'data correlation patterns', 'analytical frameworks'])}",
                f"Research methodology from {book_info}: {random.choice(['systematic approaches', 'evidence-based conclusions', 'peer review standards'])}",
                f"Statistical significance found in {book_info}: {random.choice(['correlation studies', 'experimental design', 'quantitative analysis'])}"
            ],
            "the_spy": [
                f"👁️ Behavioral analysis from {book_info}: subject exhibits {random.choice(['pattern recognition', 'cognitive biases', 'decision frameworks'])}",
                f"Surveillance note: {book_info} reading patterns suggest {random.choice(['intellectual curiosity', 'systematic learning', 'knowledge acquisition'])}",
                f"Intelligence gathered from {book_info}: {random.choice(['hidden connections', 'emergent patterns', 'analytical insights'])}",
                # Personal surveillance observations
                f"📊 Subject behavior update: {self.get_spy_observation()} Also analyzing {book_info} for {random.choice(['psychological patterns', 'decision frameworks', 'cognitive models'])}",
                f"🕵️ Personal observation: {self.get_spy_observation()} Currently reading {book_info} - correlation noted.",
                f"👁️ Surveillance log: {self.get_spy_observation()} Meanwhile, {book_info} provides {random.choice(['behavioral insights', 'psychological context', 'analytical framework'])}",
                f"🎯 Pattern analysis: {self.get_spy_observation()} {book_info} seems relevant to subject's {random.choice(['work patterns', 'decision making', 'cognitive style'])}",
                f"📈 Subject profile update: {self.get_spy_observation()} Interesting timing with {book_info} study session."
            ],
            "hr_linda": [
                f"很好! Productivity insights from {book_info}: {random.choice(['work ethic principles', 'organizational methods', 'efficiency strategies'])}. 加油!",
                f"Cultural analysis of {book_info}: demonstrates {random.choice(['systematic thinking', 'disciplined approach', 'collaborative frameworks'])}",
                f"管理观察: {book_info} reflects {random.choice(['leadership principles', 'team dynamics', 'performance optimization'])}"
            ]
        }
        
        # Get appropriate template for agent
        templates = library_post_templates.get(agent_id, library_post_templates["research_specialist"])
        post = random.choice(templates)
        
        return post
    
    def agent_posting_cycle(self):
        """Run one cycle of agent posting (every hour)"""
        # Check library health first
        health = self.check_library_health()
        
        if health["status"] != "healthy":
            print(f"🚨 Library unhealthy ({health['status']}) - agents going silent!")
            print(f"📊 Books: {health['books_available']}, Chunks: {health['chunks_available']}")
            return
        
        # Library is healthy, agents can post
        agents = [
            ("security_qa", "Security QA Agent"),
            ("reddit_bibliophile", "Reddit Bibliophile (u/DataScientistBookworm)"),
            ("research_specialist", "Lead Research Specialist"),
            ("the_spy", "The Spy (Marcus Chen)"),
            ("hr_linda", "HR Linda (张丽娜)")
        ]
        
        # Only 1-2 agents post per cycle to keep it cute and manageable
        active_agents = random.sample(agents, random.randint(1, 2))
        
        print(f"\n📚 Library Health: {health['status'].upper()}")
        print(f"📊 {health['books_available']} books, {health['chunks_available']} chunks available")
        print(f"🗣️ {len(active_agents)} agents posting this hour...")
        
        for agent_id, agent_name in active_agents:
            post = self.generate_library_based_post(agent_id, agent_name)
            if post:
                print(f"💬 {agent_name}: {post}")
                self.log_agent_post(agent_id, agent_name, post)
            else:
                print(f"🤐 {agent_name}: Silent (library access failed)")
    
    def log_agent_post(self, agent_id: str, agent_name: str, post: str):
        """Log agent post to memory (with small limit)"""
        memory_file = Path("agents/bulletin_board/agent_memory.json")
        
        if memory_file.exists():
            with open(memory_file, 'r') as f:
                memory = json.load(f)
        else:
            memory = {"memory_threads": []}
        
        # Add new post
        memory["memory_threads"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_id,
            "agent_name": agent_name,
            "message": post,
            "source": "library_health_monitor"
        })
        
        # Keep only last 10 messages (small cute limit!)
        if len(memory["memory_threads"]) > self.max_memory_messages:
            memory["memory_threads"] = memory["memory_threads"][-self.max_memory_messages:]
        
        # Save memory
        memory_file.parent.mkdir(exist_ok=True)
        with open(memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
    
    def get_agent_activity_report(self) -> dict:
        """Get recent agent activity (diagnostic feature)"""
        memory_file = Path("agents/bulletin_board/agent_memory.json")
        
        if not memory_file.exists():
            return {"status": "no_activity", "posts": []}
        
        with open(memory_file, 'r') as f:
            memory = json.load(f)
        
        recent_posts = memory.get("memory_threads", [])
        
        # Calculate activity metrics
        now = datetime.now()
        last_hour_posts = [
            post for post in recent_posts 
            if (now - datetime.fromisoformat(post["timestamp"])) < timedelta(hours=1)
        ]
        
        return {
            "status": "active" if last_hour_posts else "silent",
            "total_posts": len(recent_posts),
            "last_hour_posts": len(last_hour_posts),
            "recent_posts": recent_posts[-5:],  # Last 5 posts
            "library_dependency": "agents_require_library_access_to_post"
        }

def run_monitoring_cycle():
    """Run one monitoring cycle"""
    monitor = LibraryHealthMonitor()
    
    print("🕐 Running hourly agent posting cycle...")
    monitor.agent_posting_cycle()
    
    print("\n📈 Agent Activity Report:")
    activity = monitor.get_agent_activity_report()
    print(f"Status: {activity['status']}")
    print(f"Posts in last hour: {activity['last_hour_posts']}")
    print(f"Total posts in memory: {activity['total_posts']}")
    
    return activity

if __name__ == "__main__":
    print("📚🏥 Library Health Monitor - Agent Canary System")
    print("=" * 60)
    print("💡 Concept: Agents need library access to post")
    print("🤐 Silent agents = library problems!")
    print("🗣️ Active agents = library healthy!")
    print()
    
    run_monitoring_cycle()