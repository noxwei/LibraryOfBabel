#!/usr/bin/env python3
"""
🐘📱 PostgreSQL Agent Social Media System
========================================

Migrated from JSON files to PostgreSQL for proper social graph capabilities!

Features:
- Agent posts stored in PostgreSQL with full social graph analysis
- Coffee states tracked with temporal existence experiments
- RSS feeds generated directly from database queries
- Library health monitoring with agent posting patterns
- Social network analysis with recursive CTEs
"""

import os
import json
import random
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class PostgreSQLAgentSocialMedia:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        print("🐘 PostgreSQL Agent Social Media System Initialized")
        print("📊 Social graph capabilities enabled")
        print("☕ Coffee states tracked in database")
        print("📡 RSS feeds generated from SQL queries")
    
    def get_db(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def give_agent_coffee(self, agent_name: str) -> Dict:
        """Give coffee to agent with PostgreSQL tracking"""
        try:
            with self.get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Get agent ID
                    cur.execute("SELECT agent_id FROM agents WHERE agent_name = %s", (agent_name,))
                    agent_result = cur.fetchone()
                    if not agent_result:
                        return {"success": False, "message": f"Agent {agent_name} not found"}
                    
                    agent_id = agent_result['agent_id']
                    
                    # Check current coffee status
                    cur.execute("SELECT * FROM get_agent_coffee_status(%s)", (agent_id,))
                    status = cur.fetchone()
                    
                    if status['status'] == 'cooldown':
                        return {
                            "success": False,
                            "message": f"☕❌ {agent_name} is in coffee cooldown for {status['minutes_remaining']} more minutes",
                            "status": "cooldown_active"
                        }
                    
                    # Give coffee
                    current_time = datetime.now()
                    boost_until = current_time + timedelta(hours=1)
                    cooldown_until = boost_until + timedelta(hours=1)
                    
                    cur.execute("""
                        INSERT INTO agent_coffee_states 
                        (agent_id, coffee_given_at, boost_until, cooldown_until, 
                         original_frequency_minutes, boosted_frequency_minutes, status, expires_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING coffee_id
                    """, (
                        agent_id, current_time, boost_until, cooldown_until,
                        60, 15, 'caffeinated', cooldown_until
                    ))
                    
                    coffee_id = cur.fetchone()['coffee_id']
                    
                    # Log coffee event as post
                    self.log_agent_post(
                        agent_name, 'coffee_boost',
                        f"☕🚀 COFFEE BOOST ACTIVATED! Temporal existence multiplied by 4x!",
                        'social_humor'
                    )
                    
                    return {
                        "success": True,
                        "message": f"☕🚀 {agent_name} is now CAFFEINATED! 4x posting speed for 1 hour!",
                        "coffee_id": coffee_id,
                        "boost_until": boost_until.isoformat(),
                        "cooldown_until": cooldown_until.isoformat()
                    }
                    
        except Exception as e:
            return {"success": False, "message": f"Database error: {e}"}
    
    def log_agent_post(self, agent_name: str, post_type: str, message: str, 
                      category: str = None, book_title: str = None, book_author: str = None) -> int:
        """Log agent post to PostgreSQL"""
        try:
            with self.get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT log_agent_post(%s, %s, %s, %s, %s, %s)
                    """, (agent_name, post_type, message, category, book_title, book_author))
                    
                    post_id = cur.fetchone()[0]
                    conn.commit()
                    return post_id
                    
        except Exception as e:
            print(f"❌ Failed to log post: {e}")
            return 0
    
    def get_agent_posts(self, limit: int = 20, category: str = None) -> List[Dict]:
        """Get recent agent posts with social graph context"""
        try:
            with self.get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    if category:
                        cur.execute("""
                            SELECT ap.*, a.agent_name, a.category as agent_category
                            FROM agent_posts ap
                            JOIN agents a ON ap.agent_id = a.agent_id
                            WHERE ap.category = %s
                            ORDER BY ap.created_at DESC
                            LIMIT %s
                        """, (category, limit))
                    else:
                        cur.execute("""
                            SELECT ap.*, a.agent_name, a.category as agent_category
                            FROM agent_posts ap
                            JOIN agents a ON ap.agent_id = a.agent_id
                            ORDER BY ap.created_at DESC
                            LIMIT %s
                        """, (limit,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            print(f"❌ Failed to get posts: {e}")
            return []
    
    def get_agent_social_network(self, agent_name: str = None) -> Dict:
        """Get agent social network analysis using PostgreSQL graph queries"""
        try:
            with self.get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Overall network stats
                    cur.execute("SELECT * FROM v_agent_social_activity ORDER BY total_posts DESC")
                    activity_stats = [dict(row) for row in cur.fetchall()]
                    
                    # Coffee consumption analytics
                    cur.execute("SELECT * FROM v_coffee_analytics ORDER BY total_coffee_consumed DESC")
                    coffee_stats = [dict(row) for row in cur.fetchall()]
                    
                    # Agent influence analysis (simplified PageRank)
                    cur.execute("""
                        WITH agent_mentions AS (
                            SELECT 
                                a.agent_name,
                                COUNT(ap.post_id) as total_posts,
                                COUNT(CASE WHEN ap.coffee_boosted THEN 1 END) as boosted_posts,
                                AVG(ap.reading_time_minutes) as avg_reading_time,
                                MAX(ap.created_at) as last_active
                            FROM agents a
                            LEFT JOIN agent_posts ap ON a.agent_id = ap.agent_id
                            GROUP BY a.agent_id, a.agent_name
                        )
                        SELECT *,
                               CASE 
                                   WHEN total_posts > 10 THEN 'HIGHLY_ACTIVE'
                                   WHEN total_posts > 5 THEN 'ACTIVE'
                                   WHEN total_posts > 0 THEN 'OCCASIONAL'
                                   ELSE 'LURKER'
                               END as influence_level
                        FROM agent_mentions
                        ORDER BY total_posts DESC
                    """)
                    influence_analysis = [dict(row) for row in cur.fetchall()]
                    
                    # Specific agent network if requested
                    agent_specific = None
                    if agent_name:
                        cur.execute("""
                            SELECT ap.*, a.agent_name
                            FROM agent_posts ap
                            JOIN agents a ON ap.agent_id = a.agent_id
                            WHERE a.agent_name = %s
                            ORDER BY ap.created_at DESC
                            LIMIT 10
                        """, (agent_name,))
                        agent_specific = [dict(row) for row in cur.fetchall()]
                    
                    return {
                        "activity_stats": activity_stats,
                        "coffee_analytics": coffee_stats,
                        "influence_analysis": influence_analysis,
                        "agent_specific": agent_specific,
                        "total_agents": len(activity_stats),
                        "active_agents": len([a for a in activity_stats if a['total_posts'] > 0])
                    }
                    
        except Exception as e:
            print(f"❌ Failed to get social network: {e}")
            return {}
    
    def generate_rss_feed_sql(self, category: str, limit: int = 20) -> str:
        """Generate RSS feed using PostgreSQL queries"""
        try:
            with self.get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    cur.execute("""
                        SELECT 
                            ap.message,
                            ap.book_title,
                            ap.book_author,
                            ap.coffee_boosted,
                            ap.existence_level,
                            ap.created_at,
                            a.agent_name,
                            a.category as agent_category
                        FROM agent_posts ap
                        JOIN agents a ON ap.agent_id = a.agent_id
                        WHERE ap.category = %s OR ap.category IS NULL
                        ORDER BY ap.created_at DESC
                        LIMIT %s
                    """, (category, limit))
                    
                    posts = [dict(row) for row in cur.fetchall()]
                    
                    # Generate RSS XML
                    rss_items = []
                    for post in posts:
                        title = f"🤖 {post['agent_name']}: {post['message'][:50]}..."
                        description = post['message']
                        
                        if post['coffee_boosted']:
                            title = f"☕ {title} [CAFFEINATED]"
                            description = f"[HYPERACTIVE MODE] {description}"
                        
                        if post['book_title']:
                            description += f"\n\n📚 Book: {post['book_title']}"
                            if post['book_author']:
                                description += f" by {post['book_author']}"
                        
                        rss_items.append({
                            'title': title,
                            'description': description,
                            'pubDate': post['created_at'].strftime('%a, %d %b %Y %H:%M:%S %z'),
                            'guid': f"agent-post-{post['created_at'].timestamp()}"
                        })
                    
                    return rss_items
                    
        except Exception as e:
            print(f"❌ Failed to generate RSS: {e}")
            return []
    
    def check_library_health_with_agents(self) -> Dict:
        """Check library health using agent posting patterns as canaries"""
        try:
            with self.get_db() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    
                    # Check database health
                    cur.execute("SELECT COUNT(*) as books FROM books")
                    books_count = cur.fetchone()['books']
                    
                    cur.execute("SELECT COUNT(*) as chunks FROM chunks")  
                    chunks_count = cur.fetchone()['chunks']
                    
                    # Check agent activity in last hour
                    cur.execute("""
                        SELECT COUNT(DISTINCT ap.agent_id) as active_agents,
                               COUNT(ap.post_id) as total_posts
                        FROM agent_posts ap
                        WHERE ap.created_at > NOW() - INTERVAL '1 hour'
                    """)
                    activity = cur.fetchone()
                    
                    # Determine health status
                    database_healthy = books_count > 0 and chunks_count > 0
                    agents_active = activity['active_agents'] > 0
                    
                    if database_healthy and agents_active:
                        status = 'healthy'
                    elif database_healthy and not agents_active:
                        status = 'agents_silent'  # Canary indicator!
                    elif not database_healthy:
                        status = 'database_down'
                    else:
                        status = 'unknown'
                    
                    # Log health check
                    cur.execute("""
                        INSERT INTO library_health_checks 
                        (database_accessible, books_available, chunks_available, 
                         search_responsive, agents_posting_count, silent_agents_count, health_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        database_healthy, books_count, chunks_count, database_healthy,
                        activity['active_agents'], 8 - activity['active_agents'], status
                    ))
                    
                    conn.commit()
                    
                    return {
                        'status': status,
                        'database_accessible': database_healthy,
                        'books_available': books_count,
                        'chunks_available': chunks_count,
                        'agents_posting_last_hour': activity['active_agents'],
                        'total_posts_last_hour': activity['total_posts'],
                        'canary_indicator': 'silent_agents' if not agents_active else 'agents_chattering'
                    }
                    
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def migrate_from_json(self, json_file_path: str = "agents/bulletin_board/agent_memory.json"):
        """Migrate existing JSON data to PostgreSQL"""
        try:
            if not os.path.exists(json_file_path):
                print(f"📭 No JSON file found at {json_file_path}")
                return
            
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            
            posts = data.get('memory_threads', [])
            migrated_count = 0
            
            for post in posts:
                agent_name = post.get('agent_name', post.get('agent', 'unknown'))
                message = post.get('message', '')
                timestamp = post.get('timestamp', datetime.now().isoformat())
                
                # Determine post category
                category = 'agent_reading_group'  # Default
                if 'spy' in agent_name.lower():
                    category = 'mental_state'
                elif 'book' in message.lower() or 'read' in message.lower():
                    category = 'book_discovery'
                elif 'coffee' in message.lower() or 'healthcare' in message.lower():
                    category = 'social_humor'
                
                # Extract book info if present
                book_title = None
                if '"' in message:
                    import re
                    match = re.search(r'"([^"]*)"', message)
                    if match:
                        book_title = match.group(1)
                
                try:
                    post_id = self.log_agent_post(
                        agent_name, 'bulletin', message, category, book_title
                    )
                    if post_id > 0:
                        migrated_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to migrate post: {e}")
            
            print(f"✅ Migrated {migrated_count} posts from JSON to PostgreSQL")
            print(f"🗃️ Old JSON data preserved at {json_file_path}")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")

def demo_postgresql_social_media():
    """Demonstrate PostgreSQL social media capabilities"""
    
    system = PostgreSQLAgentSocialMedia()
    
    print("🐘 PostgreSQL Agent Social Media Demo")
    print("=" * 50)
    
    # 1. Migrate existing data
    print("\n📥 Migrating existing JSON data...")
    system.migrate_from_json()
    
    # 2. Give coffee to The Spy
    print("\n☕ Giving coffee to The Spy...")
    coffee_result = system.give_agent_coffee("the_spy_marcus")
    print(f"Result: {coffee_result['message']}")
    
    # 3. Log some test posts
    print("\n📝 Creating test posts...")
    system.log_agent_post(
        "reddit_bibliophile", "book_discussion",
        'yo r/books, just discovered "Surveillance Capitalism" - mind blown! 🤯',
        "book_discovery", "The Age of Surveillance Capitalism", "Shoshana Zuboff"
    )
    
    system.log_agent_post(
        "the_spy_marcus", "surveillance",
        "👁️ Subject's reading patterns show increased interest in privacy literature. Correlation noted.",
        "mental_state"
    )
    
    # 4. Get social network analysis
    print("\n📊 Social Network Analysis...")
    network = system.get_agent_social_network()
    
    print(f"Total agents: {network['total_agents']}")
    print(f"Active agents: {network['active_agents']}")
    
    if network['influence_analysis']:
        print("\n🏆 Most Influential Agents:")
        for agent in network['influence_analysis'][:3]:
            print(f"   {agent['agent_name']}: {agent['total_posts']} posts ({agent['influence_level']})")
    
    # 5. Check library health
    print("\n🏥 Library Health Check...")
    health = system.check_library_health_with_agents()
    print(f"Status: {health['status']}")
    print(f"Books: {health['books_available']}, Chunks: {health['chunks_available']}")
    print(f"Canary indicator: {health['canary_indicator']}")
    
    # 6. Generate RSS content
    print("\n📡 RSS Feed Sample...")
    rss_items = system.generate_rss_feed_sql('book_discovery', 3)
    for item in rss_items:
        print(f"   📚 {item['title']}")
    
    print("\n🎉 PostgreSQL Social Media System Operational!")
    print("🔗 Social graph capabilities unlocked!")

if __name__ == "__main__":
    demo_postgresql_social_media()