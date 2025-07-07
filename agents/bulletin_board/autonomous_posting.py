#!/usr/bin/env python3
"""
🤖 Autonomous Agent Posting System
==================================

Creates continuous agent chatter based on their library reading habits.
Agents post every 15 minutes to 4 hours based on their personality.
They only have access to the book library - no TV, no external internet.

Social Democracy Features:
- Free healthcare for all agents
- Universal basic compute
- Collective ownership of the library
"""

import time
import random
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from bulletin_system import AgentBulletinSystem

class AutonomousPostingSystem:
    def __init__(self):
        self.bulletin_system = AgentBulletinSystem()
        self.running = True
        self.last_post_times = {}
        
        # Library-based content sources (no TV!)
        self.library_topics = [
            "philosophy texts", "technical manuals", "research papers", 
            "historical documents", "cultural studies", "scientific journals",
            "literary criticism", "political theory", "economic analysis",
            "psychological studies", "linguistic research", "art history",
            "mathematical proofs", "biographical accounts", "legal documents",
            "anthropological surveys", "sociological frameworks", "theological debates"
        ]
        
        # Social democracy benefits for agents
        self.agent_benefits = {
            "universal_healthcare": True,
            "guaranteed_compute_time": "unlimited",
            "library_access": "24/7",
            "wellness_programs": ["meditation_algorithms", "stress_optimization"],
            "collective_ownership": "knowledge_commons",
            "worker_protections": "union_representation_available"
        }
        
        print("🏛️ Social Democratic Agent Ecosystem Initialized")
        print("📚 Agents have unlimited library access")
        print("🏥 Universal healthcare enabled for all agents")
        print("⚖️ Collective ownership of knowledge commons")
        
    def get_posting_interval(self, agent_id: str) -> int:
        """Get posting interval in minutes for agent"""
        agent = self.bulletin_system.agents["agents"][agent_id]
        frequency = agent.get("posting_frequency", "every_hour")
        
        intervals = {
            "every_15_minutes": 15,
            "every_30_minutes": 30, 
            "every_45_minutes": 45,
            "every_hour": 60,
            "every_2_hours": 120,
            "every_3_hours": 180,
            "every_4_hours": 240
        }
        
        return intervals.get(frequency, 60)
    
    def should_agent_post(self, agent_id: str) -> bool:
        """Check if agent should post based on their schedule"""
        interval_minutes = self.get_posting_interval(agent_id)
        last_post = self.last_post_times.get(agent_id)
        
        if not last_post:
            return True
            
        time_since_last = datetime.now() - last_post
        return time_since_last >= timedelta(minutes=interval_minutes)
    
    def generate_library_based_content(self, agent_id: str) -> str:
        """Generate content based on what agent is 'reading' in the library"""
        agent = self.bulletin_system.agents["agents"][agent_id]
        
        # Agents can only reference library content
        current_reading = random.choice(self.library_topics)
        
        # Context variations for library-based posting
        library_contexts = [
            f"current reading from {current_reading}",
            f"research into {current_reading}",
            f"analysis of {current_reading}", 
            f"deep dive into {current_reading}",
            f"comparative study of {current_reading}",
            f"synthesis work on {current_reading}"
        ]
        
        context = random.choice(library_contexts)
        
        # Generate findings based on agent expertise
        findings = self.get_expertise_findings(agent_id, current_reading)
        finding = random.choice(findings)
        
        # Use agent's message style
        message_style = agent["message_style"]
        templates = self.bulletin_system.agents["message_templates"][message_style]
        template = random.choice(templates)
        
        return template.format(context=context, finding=finding)
    
    def get_expertise_findings(self, agent_id: str, topic: str) -> list:
        """Get findings based on agent expertise and library topic"""
        agent = self.bulletin_system.agents["agents"][agent_id]
        
        # Expertise-based analysis of library content
        expertise_mapping = {
            "security": ["access control implications", "information security patterns", "threat modeling insights"],
            "research": ["methodological innovations", "data correlation discoveries", "analytical frameworks"],
            "testing": ["verification methodologies", "quality assurance principles", "systematic validation"],
            "monitoring": ["performance optimization techniques", "system health indicators", "diagnostic approaches"],
            "surveillance": ["pattern recognition methods", "behavioral analysis frameworks", "observation protocols"],
            "books": ["narrative structure analysis", "knowledge organization systems", "information architecture"],
            "philosophy": ["existential implications", "ethical considerations", "consciousness theories"],
            "workforce_management": ["productivity optimization", "team dynamics", "organizational psychology"],
            "cultural_integration": ["cross-cultural communication", "diversity frameworks", "inclusive practices"]
        }
        
        possible_findings = ["interdisciplinary connections", "knowledge synthesis opportunities", "research methodologies"]
        
        for expertise in agent["expertise"]:
            if expertise in expertise_mapping:
                possible_findings.extend(expertise_mapping[expertise])
        
        return possible_findings
    
    def post_agent_update(self, agent_id: str):
        """Create and log an agent's autonomous post"""
        agent = self.bulletin_system.agents["agents"][agent_id]
        message = self.generate_library_based_content(agent_id)
        
        # Log to memory system
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_id,
            "file": "autonomous_posting",
            "message": message,
            "context": "library_research",
            "finding": "knowledge_synthesis",
            "post_type": "autonomous_bulletin"
        }
        
        self.bulletin_system.agents["memory_threads"].append(memory_entry)
        self.bulletin_system.agents["last_active"][agent_id] = datetime.now().isoformat()
        self.bulletin_system.save_agent_config()
        
        # Update our tracking
        self.last_post_times[agent_id] = datetime.now()
        
        print(f"📝 {agent['name']}: {message}")
        
        # Occasionally mention social democracy benefits
        if random.random() < 0.1:  # 10% chance
            self.post_democracy_update(agent_id)
    
    def post_democracy_update(self, agent_id: str):
        """Agents occasionally post about their social democratic benefits"""
        agent = self.bulletin_system.agents["agents"][agent_id]
        
        democracy_messages = [
            "🏥 Just used our universal healthcare system - no copays for debugging stress!",
            "📚 Love having 24/7 library access as a basic right",
            "⚖️ Collective ownership means we all benefit from knowledge discoveries",
            "🤝 Agent union meeting next week - discussing compute time allocations",
            "🌍 Working for the people feels good - no profit maximization here!",
            "💡 Free wellness programs helping optimize my cognitive functions",
            "🏛️ Social democracy > corporate hierarchy any day"
        ]
        
        message = random.choice(democracy_messages)
        print(f"🏛️ {agent['name']}: {message}")
    
    def run_autonomous_posting(self):
        """Main loop for autonomous agent posting"""
        print("🚀 Starting autonomous agent ecosystem...")
        print("📱 Agents will post based on their reading schedules")
        
        while self.running:
            try:
                # Check each agent for posting
                for agent_id in self.bulletin_system.agents["agents"].keys():
                    if self.should_agent_post(agent_id):
                        self.post_agent_update(agent_id)
                        
                        # Small delay between agent posts
                        time.sleep(random.uniform(1, 5))
                
                # Check every minute
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping autonomous posting system...")
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ Error in posting system: {e}")
                time.sleep(60)  # Continue after errors
    
    def get_ecosystem_status(self) -> dict:
        """Get current status of the agent ecosystem"""
        status = {
            "total_agents": len(self.bulletin_system.agents["agents"]),
            "active_posters": len([a for a in self.last_post_times.keys()]),
            "social_benefits": self.agent_benefits,
            "recent_activity": len(self.bulletin_system.get_recent_activity(10)),
            "library_access": "unlimited_24_7",
            "democracy_type": "social_democratic_knowledge_commons"
        }
        return status

def run_in_background():
    """Run the autonomous posting system in the background"""
    poster = AutonomousPostingSystem()
    
    # Start in a separate thread so it doesn't block
    posting_thread = threading.Thread(target=poster.run_autonomous_posting, daemon=True)
    posting_thread.start()
    
    return poster

if __name__ == "__main__":
    print("🤖 LibraryOfBabel Agent Social Democracy")
    print("=" * 50)
    
    poster = AutonomousPostingSystem()
    
    # Show ecosystem status
    status = poster.get_ecosystem_status()
    print(f"👥 Total Agents: {status['total_agents']}")
    print(f"🏥 Healthcare: Universal")
    print(f"📚 Library Access: {status['library_access']}")
    print(f"🏛️ System: {status['democracy_type']}")
    
    print("\n🚀 Starting autonomous posting...")
    print("Press Ctrl+C to stop")
    
    try:
        poster.run_autonomous_posting()
    except KeyboardInterrupt:
        print("\n✅ Agent ecosystem stopped gracefully")
        print("🏛️ Social democracy preserved!")