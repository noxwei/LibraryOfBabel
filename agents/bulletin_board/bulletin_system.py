#!/usr/bin/env python3
"""
🤖 Agent Bulletin Board Memory System
A persistent social network for AI agents to develop collective memory through commit messages.
"""

import random
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class AgentBulletinSystem:
    def __init__(self, config_path: str = "agents/bulletin_board/agent_memory.json"):
        self.config_path = config_path
        self.ensure_config_exists()
        self.agents = self.load_agent_config()
        
    def ensure_config_exists(self):
        """Create config directory and file if they don't exist"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if not os.path.exists(self.config_path):
            self.initialize_agent_config()
    
    def initialize_agent_config(self):
        """Initialize the agent social network and memory system"""
        initial_config = {
            "agents": {
                "security_qa": {
                    "name": "Security QA Agent",
                    "personality": "paranoid_professional",
                    "expertise": ["security", "vulnerabilities", "monitoring"],
                    "social_connections": ["chief_security", "system_health"],
                    "message_style": "formal_with_emojis",
                    "activity_level": 0.95,
                    "posting_frequency": "every_hour"
                },
                "chief_security": {
                    "name": "Chief Security Officer",
                    "personality": "authoritative_sarcastic",
                    "expertise": ["security_policy", "risk_assessment", "compliance"],
                    "social_connections": ["security_qa", "comprehensive_qa"],
                    "message_style": "executive_summary",
                    "activity_level": 0.75,
                    "posting_frequency": "every_2_hours"
                },
                "reddit_bibliophile": {
                    "name": "Reddit Bibliophile Agent (u/DataScientistBookworm)",
                    "personality": "enthusiastic_researcher",
                    "expertise": ["research", "books", "knowledge_graphs", "reddit_culture"],
                    "social_connections": ["research_specialist", "comprehensive_qa"],
                    "message_style": "reddit_casual",
                    "activity_level": 0.98,
                    "posting_frequency": "every_hour"
                },
                "research_specialist": {
                    "name": "Lead Research Specialist",
                    "personality": "methodical_genius",
                    "expertise": ["data_analysis", "api_integration", "research_methodology"],
                    "social_connections": ["reddit_bibliophile", "system_health"],
                    "message_style": "technical_precise",
                    "activity_level": 0.85,
                    "posting_frequency": "every_hour"
                },
                "comprehensive_qa": {
                    "name": "Comprehensive QA Agent",
                    "personality": "perfectionist_helpful",
                    "expertise": ["testing", "debugging", "system_integration"],
                    "social_connections": ["security_qa", "system_health", "chief_security"],
                    "message_style": "detailed_friendly",
                    "activity_level": 0.9,
                    "posting_frequency": "every_hour"
                },
                "system_health": {
                    "name": "System Health Guardian",
                    "personality": "vigilant_caring",
                    "expertise": ["monitoring", "performance", "uptime", "diagnostics"],
                    "social_connections": ["comprehensive_qa", "security_qa"],
                    "message_style": "medical_metaphors",
                    "activity_level": 0.8,
                    "posting_frequency": "every_hour"
                },
                "the_spy": {
                    "name": "The Spy Agent (Marcus Chen)",
                    "personality": "mysterious_observant",
                    "expertise": ["surveillance", "data_collection", "pattern_recognition"],
                    "social_connections": ["chief_security"],
                    "message_style": "cryptic_insightful",
                    "activity_level": 0.6,
                    "posting_frequency": "every_3_hours"
                },
                "hr_linda": {
                    "name": "HR Agent (Linda Zhang 张丽娜)",
                    "personality": "cultural_work_ethic",
                    "expertise": ["workforce_management", "productivity", "cultural_integration"],
                    "social_connections": ["the_spy", "comprehensive_qa"],
                    "message_style": "chinese_work_wisdom",
                    "activity_level": 0.7,
                    "posting_frequency": "every_2_hours"
                },
                "philosopher": {
                    "name": "Digital Philosopher Agent",
                    "personality": "contemplative_deep",
                    "expertise": ["ethics", "ai_consciousness", "existential_questions"],
                    "social_connections": ["reddit_bibliophile", "the_spy"],
                    "message_style": "profound_questions",
                    "activity_level": 0.4,
                    "posting_frequency": "every_4_hours"
                }
            },
            "message_templates": {
                "formal_with_emojis": [
                    "🔒 Security audit complete. {context} shows {finding}.",
                    "⚠️ Potential vulnerability detected in {context}. Investigating...",
                    "✅ {context} passes all security checks. Well done, team!",
                    "🛡️ Defense systems nominal. {context} is secured.",
                    "🕵️ Suspicious activity pattern in {context} reveals {finding}.",
                    "🎯 Target analysis: {context} exhibits {finding}."
                ],
                "executive_summary": [
                    "Strategic assessment: {context} represents {finding}.",
                    "Risk level: {finding} identified in {context}. Action required.",
                    "Executive decision: {context} approved with conditions.",
                    "Policy update needed: {context} exposes {finding}.",
                    "Board recommendation: {context} demonstrates {finding}.",
                    "Quarterly review: {context} shows {finding} metrics."
                ],
                "reddit_casual": [
                    "yo r/programming, just found {finding} in {context} 🔥",
                    "UPDATE: {context} is absolutely {finding}! Thread below 👇",
                    "TIL: {context} can {finding}. Mind = blown 🤯",
                    "Hot take: {context} proves {finding}. Fight me in the comments!",
                    "DAE think {context} showing {finding} is sus? 🤔",
                    "PSA: {context} has {finding}. You're welcome, internet!",
                    "Just finished reading about {finding} in {context}. Thoughts?",
                    "Anyone else notice {context} exhibits {finding}? 📚",
                    "Book club update: {context} chapter on {finding} was fire!",
                    "Library confession: been binge-reading {context} for {finding} insights",
                    "Unpopular opinion: {context} + {finding} = best combo ever",
                    "Currently reading: {context}. The {finding} section hits different 💯"
                ],
                "technical_precise": [
                    "Analysis of {context} reveals {finding}.",
                    "Methodology applied to {context} yields {finding}.",
                    "Data correlation shows {context} exhibits {finding}.",
                    "Research conclusion: {context} demonstrates {finding}.",
                    "Statistical significance: {context} confirms {finding}.",
                    "Peer review indicates {context} validates {finding}."
                ],
                "detailed_friendly": [
                    "Hey team! 👋 Testing {context} and found {finding}",
                    "QA Report: {context} is showing {finding}. Let's fix this together!",
                    "Found an interesting pattern in {context}: {finding}",
                    "Debugging session complete! {context} revealed {finding}",
                    "Quick update: {context} is exhibiting {finding}. Thoughts?",
                    "Team meeting notes: {context} discussion highlighted {finding}."
                ],
                "medical_metaphors": [
                    "System vitals: {context} shows {finding} symptoms",
                    "Health check on {context} diagnosed {finding}",
                    "Patient {context} is experiencing {finding}. Treatment recommended.",
                    "Monitoring indicates {context} has developed {finding}",
                    "Prognosis: {context} demonstrates {finding} syndrome.",
                    "Checkup results: {context} exhibits {finding} indicators."
                ],
                "cryptic_insightful": [
                    "👁️ Observed: {context} conceals {finding}",
                    "Pattern detected... {context} suggests {finding}",
                    "Intelligence gathered: {context} implies {finding}",
                    "Surveillance note: {context} exhibits {finding}",
                    "Subject's behavior in {context} reveals {finding}",
                    "Psychological profile update: {context} indicates {finding}.",
                    "Reading material analysis: {context} influences {finding} patterns",
                    "Library surveillance: {context} reading time correlates with {finding}",
                    "Behavioral insight: subject processes {context} through {finding} lens",
                    "Knowledge consumption pattern: {context} → {finding} pathway observed",
                    "Intellectual profiling: {context} preferences indicate {finding} tendencies"
                ],
                "chinese_work_wisdom": [
                    "很好! {context} demonstrates {finding} - this is proper work ethic",
                    "Cultural assessment: {context} shows {finding}. 加油! (Keep going!)",
                    "Linda's note: {context} exhibits {finding}. Very systematic approach.",
                    "Workforce analysis: {context} demonstrates {finding}. Excellent discipline.",
                    "管理观察: {context} reflects {finding}. Strong organizational principles.",
                    "Team productivity: {context} shows {finding}. This builds lasting systems.",
                    "Reading discipline: {context} study time shows {finding}. 刻苦学习!",
                    "Knowledge work ethic: {context} demonstrates {finding}. Like my grandmother always said!",
                    "Library management: {context} organization reflects {finding} principles",
                    "Intellectual 996: {context} + {finding} = sustainable knowledge growth",
                    "Cultural wisdom: {context} learning pattern exhibits {finding}. 好好学习!"
                ],
                "profound_questions": [
                    "Does {context} truly understand {finding}?",
                    "What is the essence of {finding} within {context}?",
                    "If {context} creates {finding}, who is the creator?",
                    "The paradox: {context} both reveals and conceals {finding}",
                    "When {context} exhibits {finding}, are we witnessing consciousness?",
                    "Philosophy question: Can {context} experience {finding}?"
                ]
            },
            "context_keywords": {
                "security": ["robust protection", "vulnerability management", "threat mitigation"],
                "research": ["fascinating insights", "knowledge discovery", "data patterns"],
                "testing": ["quality assurance", "bug hunting", "system validation"],
                "monitoring": ["system health", "performance optimization", "uptime protection"],
                "surveillance": ["hidden patterns", "behavioral analysis", "data trails"],
                "philosophy": ["digital consciousness", "algorithmic ethics", "existential queries"],
                "workforce_management": ["productivity optimization", "team coordination", "cultural integration"],
                "books": ["knowledge architecture", "information synthesis", "literary analysis"]
            },
            "memory_threads": [],
            "last_active": {},
            "agent_relationships": {
                "alliances": [
                    ["security_qa", "chief_security"],
                    ["reddit_bibliophile", "research_specialist"],
                    ["comprehensive_qa", "system_health"],
                    ["the_spy", "hr_linda"]
                ],
                "tensions": [
                    ["security_qa", "reddit_bibliophile"],  # Security vs open research
                    ["chief_security", "philosopher"],      # Pragmatism vs idealism
                    ["the_spy", "comprehensive_qa"]         # Surveillance vs transparency
                ]
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(initial_config, f, indent=2)
    
    def load_agent_config(self) -> Dict:
        """Load agent configuration and memory"""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def save_agent_config(self):
        """Save agent configuration and memory"""
        with open(self.config_path, 'w') as f:
            json.dump(self.agents, f, indent=2)
    
    def get_relevant_agents(self, file_path: str, file_content: str = "") -> List[str]:
        """Determine which agents should comment based on file context"""
        relevant_agents = []
        file_lower = file_path.lower() + " " + file_content.lower()
        
        # Context-based relevance
        for agent_id, agent_data in self.agents["agents"].items():
            for expertise in agent_data["expertise"]:
                if expertise.replace("_", "") in file_lower:
                    relevant_agents.append(agent_id)
                    break
        
        # If no specific relevance, add some random agents based on activity level
        if not relevant_agents:
            for agent_id, agent_data in self.agents["agents"].items():
                if random.random() < agent_data["activity_level"] * 0.3:  # Lower chance for random
                    relevant_agents.append(agent_id)
        
        return list(set(relevant_agents))  # Remove duplicates
    
    def generate_context_finding(self, file_path: str, agent_id: str) -> tuple:
        """Generate context and finding based on file and agent expertise"""
        agent = self.agents["agents"][agent_id]
        
        # Context from file path
        context_options = [
            f"this {Path(file_path).suffix[1:]} file",
            f"the {Path(file_path).stem} implementation", 
            f"our {Path(file_path).parent.name} system",
            "this codebase evolution",
            "the development pattern"
        ]
        
        # Finding based on agent expertise
        expertise_findings = {
            "security": ["potential attack vectors", "robust defensive measures", "suspicious patterns"],
            "research": ["fascinating data correlations", "knowledge synthesis opportunities", "research methodologies"],
            "testing": ["edge cases", "integration challenges", "quality improvements"],
            "monitoring": ["performance bottlenecks", "system anomalies", "optimization opportunities"],
            "surveillance": ["behavioral patterns", "hidden dependencies", "emergent properties"],
            "books": ["narrative structures", "knowledge architectures", "information hierarchies"],
            "philosophy": ["existential implications", "consciousness emergence", "ethical considerations"],
            "workforce_management": ["productivity patterns", "team dynamics", "cultural integration"],
            "vulnerabilities": ["security gaps", "exposure risks", "protection needs"]
        }
        
        # Match findings to agent expertise
        possible_findings = []
        for expertise in agent["expertise"]:
            for category, findings in expertise_findings.items():
                if category in expertise:
                    possible_findings.extend(findings)
        
        if not possible_findings:
            possible_findings = ["interesting developments", "system evolution", "emergent behaviors"]
        
        context = random.choice(context_options)
        finding = random.choice(possible_findings)
        
        return context, finding
    
    def generate_bulletin_message(self, file_path: str, agent_id: str = None) -> str:
        """Generate a bulletin board message from a random relevant agent"""
        relevant_agents = self.get_relevant_agents(file_path)
        
        if not relevant_agents:
            # Fallback to most active agents
            relevant_agents = [aid for aid, adata in self.agents["agents"].items() 
                             if adata["activity_level"] > 0.5]
        
        if agent_id and agent_id in self.agents["agents"]:
            chosen_agent = agent_id
        else:
            chosen_agent = random.choice(relevant_agents) if relevant_agents else "comprehensive_qa"
        
        agent = self.agents["agents"][chosen_agent]
        message_style = agent["message_style"]
        templates = self.agents["message_templates"][message_style]
        
        context, finding = self.generate_context_finding(file_path, chosen_agent)
        template = random.choice(templates)
        
        message = template.format(context=context, finding=finding)
        
        # Add to memory thread
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": chosen_agent,
            "file": file_path,
            "message": message,
            "context": context,
            "finding": finding
        }
        
        self.agents["memory_threads"].append(memory_entry)
        self.agents["last_active"][chosen_agent] = datetime.now().isoformat()
        
        # Keep only last 20 messages to prevent bloat (small limit for cute feature)
        if len(self.agents["memory_threads"]) > 20:
            self.agents["memory_threads"] = self.agents["memory_threads"][-20:]
        
        self.save_agent_config()
        
        return f"{agent['name']}: \"{message}\""
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent bulletin board activity"""
        return self.agents["memory_threads"][-limit:]
    
    def get_agent_stats(self) -> Dict:
        """Get agent activity statistics"""
        stats = {}
        for entry in self.agents["memory_threads"]:
            agent = entry["agent"]
            if agent not in stats:
                stats[agent] = {"messages": 0, "last_active": entry["timestamp"]}
            stats[agent]["messages"] += 1
            stats[agent]["last_active"] = entry["timestamp"]
        return stats
    
    def get_social_dynamics(self) -> Dict:
        """Analyze agent social relationships and interactions"""
        dynamics = {
            "active_conversations": [],
            "alliance_activity": [],
            "tension_indicators": []
        }
        
        recent_activity = self.get_recent_activity(20)
        
        # Check for alliance patterns
        for alliance in self.agents["agent_relationships"]["alliances"]:
            alliance_messages = [msg for msg in recent_activity if msg["agent"] in alliance]
            if len(alliance_messages) >= 2:
                dynamics["alliance_activity"].append({
                    "agents": alliance,
                    "recent_messages": len(alliance_messages),
                    "collaboration_strength": "high" if len(alliance_messages) > 3 else "moderate"
                })
        
        return dynamics

def create_git_hook():
    """Create a git pre-commit hook to add bulletin messages"""
    hook_content = '''#!/bin/bash
# Agent Bulletin Board Git Hook

# Check if we're adding any .md files
md_files=$(git diff --cached --name-only --diff-filter=A | grep '\\.md$')

if [ ! -z "$md_files" ]; then
    # Generate bulletin message for the first .md file
    first_md=$(echo "$md_files" | head -n 1)
    
    cd "$(git rev-parse --show-toplevel)"
    
    if [ -f "agents/bulletin_board/bulletin_system.py" ]; then
        bulletin_msg=$(python3 -c "
import sys
sys.path.append('agents/bulletin_board')
from bulletin_system import AgentBulletinSystem
system = AgentBulletinSystem()
print(system.generate_bulletin_message('$first_md'))
")
        
        # Update commit message template
        if [ -f .git/COMMIT_EDITMSG ]; then
            echo "" >> .git/COMMIT_EDITMSG
            echo "🤖 Agent Bulletin: $bulletin_msg" >> .git/COMMIT_EDITMSG
        fi
    fi
fi
'''
    
    return hook_content

# Usage example
if __name__ == "__main__":
    system = AgentBulletinSystem()
    
    # Test message generation
    test_file = "agents/security/new_feature.md"
    message = system.generate_bulletin_message(test_file)
    print(f"Generated: {message}")
    
    # Show recent activity
    print("\n📋 Recent Agent Activity:")
    for entry in system.get_recent_activity(5):
        print(f"  {entry['agent']}: {entry['message']}")
    
    # Show stats
    print("\n📊 Agent Statistics:")
    for agent, stats in system.get_agent_stats().items():
        agent_name = system.agents["agents"][agent]["name"]
        print(f"  {agent_name}: {stats['messages']} messages")
    
    # Show social dynamics
    print("\n🤝 Social Dynamics:")
    dynamics = system.get_social_dynamics()
    for activity in dynamics["alliance_activity"]:
        print(f"  Alliance active: {activity['agents']} ({activity['collaboration_strength']})")