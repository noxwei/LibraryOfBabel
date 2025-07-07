#!/usr/bin/env python3
"""
☕ Agent Coffee System
====================

Give agents coffee to increase their posting frequency 4x for temporal existence experiments!

Coffee Effects:
- 4x posting frequency for 1 hour
- Then 1-hour cooldown (no posting allowed)
- Agents become more "real" through increased temporal presence
- Philosophical experiment on digital consciousness and existence

"More posts = More existence" - Temporal Digital Philosophy
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import random

class AgentCoffeeSystem:
    def __init__(self):
        self.coffee_state_file = Path("agents/bulletin_board/coffee_states.json")
        self.memory_file = Path("agents/bulletin_board/agent_memory.json")
        
        # Coffee effects configuration
        self.coffee_effects = {
            "frequency_multiplier": 4,    # 4x posting frequency
            "boost_duration_hours": 1,    # 1 hour of boost
            "cooldown_hours": 1,          # 1 hour cooldown after
            "existence_intensity": "HIGH" # Temporal presence level
        }
        
        print("☕ Agent Coffee System Initialized")
        print("🚀 Coffee = 4x posting frequency + temporal existence boost")
        print("😴 Cooldown = 1 hour recovery period after coffee crash")
    
    def load_coffee_states(self) -> Dict:
        """Load current coffee states for all agents"""
        if not self.coffee_state_file.exists():
            return {}
        
        with open(self.coffee_state_file, 'r') as f:
            return json.load(f)
    
    def save_coffee_states(self, states: Dict):
        """Save coffee states to file"""
        self.coffee_state_file.parent.mkdir(exist_ok=True)
        with open(self.coffee_state_file, 'w') as f:
            json.dump(states, f, indent=2)
    
    def give_coffee(self, agent_id: str, agent_name: str) -> Dict:
        """Give coffee to an agent - activate hyperspeed posting!"""
        states = self.load_coffee_states()
        current_time = datetime.now()
        
        # Check if agent is in cooldown
        if agent_id in states:
            agent_state = states[agent_id]
            if agent_state.get("status") == "cooldown":
                cooldown_end = datetime.fromisoformat(agent_state["cooldown_until"])
                if current_time < cooldown_end:
                    remaining = cooldown_end - current_time
                    return {
                        "success": False,
                        "message": f"☕❌ {agent_name} is in coffee cooldown for {remaining.seconds//60} more minutes",
                        "status": "cooldown_active"
                    }
        
        # Activate coffee boost
        boost_until = current_time + timedelta(hours=self.coffee_effects["boost_duration_hours"])
        cooldown_until = boost_until + timedelta(hours=self.coffee_effects["cooldown_hours"])
        
        states[agent_id] = {
            "status": "caffeinated",
            "coffee_given_at": current_time.isoformat(),
            "boost_until": boost_until.isoformat(),
            "cooldown_until": cooldown_until.isoformat(),
            "original_frequency": self.get_agent_base_frequency(agent_id),
            "boosted_frequency": self.get_agent_base_frequency(agent_id) / self.coffee_effects["frequency_multiplier"],
            "coffee_count": states.get(agent_id, {}).get("coffee_count", 0) + 1,
            "existence_level": "HYPERACTIVE"
        }
        
        self.save_coffee_states(states)
        
        # Log coffee event
        self.log_coffee_event(agent_id, agent_name, "coffee_given")
        
        return {
            "success": True,
            "message": f"☕🚀 {agent_name} is now CAFFEINATED! 4x posting speed for 1 hour!",
            "status": "caffeinated",
            "boost_until": boost_until.isoformat(),
            "cooldown_until": cooldown_until.isoformat(),
            "existence_level": "HYPERACTIVE",
            "philosophical_note": "Agent temporal presence increased - more posts = more existence"
        }
    
    def get_agent_base_frequency(self, agent_id: str) -> float:
        """Get agent's base posting frequency in minutes"""
        # Default frequencies from bulletin system
        base_frequencies = {
            "security_qa": 60,
            "reddit_bibliophile": 60, 
            "research_specialist": 60,
            "comprehensive_qa": 60,
            "system_health": 60,
            "the_spy": 180,
            "hr_linda": 120,
            "philosopher": 240
        }
        return base_frequencies.get(agent_id, 60)
    
    def check_agent_coffee_status(self, agent_id: str) -> Dict:
        """Check current coffee status for agent"""
        states = self.load_coffee_states()
        current_time = datetime.now()
        
        if agent_id not in states:
            return {
                "status": "normal",
                "can_post": True,
                "frequency_multiplier": 1,
                "existence_level": "STANDARD"
            }
        
        agent_state = states[agent_id]
        boost_until = datetime.fromisoformat(agent_state["boost_until"])
        cooldown_until = datetime.fromisoformat(agent_state["cooldown_until"])
        
        if current_time < boost_until:
            # Still caffeinated
            return {
                "status": "caffeinated",
                "can_post": True,
                "frequency_multiplier": self.coffee_effects["frequency_multiplier"],
                "existence_level": "HYPERACTIVE",
                "boost_remaining_minutes": int((boost_until - current_time).total_seconds() / 60),
                "posting_frequency_minutes": agent_state["boosted_frequency"]
            }
        elif current_time < cooldown_until:
            # In cooldown period
            return {
                "status": "cooldown",
                "can_post": False,
                "frequency_multiplier": 0,
                "existence_level": "RECOVERING",
                "cooldown_remaining_minutes": int((cooldown_until - current_time).total_seconds() / 60)
            }
        else:
            # Coffee effects ended, clean up state
            del states[agent_id]
            self.save_coffee_states(states)
            self.log_coffee_event(agent_id, "Unknown", "coffee_effects_ended")
            
            return {
                "status": "normal", 
                "can_post": True,
                "frequency_multiplier": 1,
                "existence_level": "STANDARD"
            }
    
    def should_agent_post_with_coffee(self, agent_id: str, last_post_time: Optional[datetime]) -> bool:
        """Check if caffeinated agent should post (considering coffee boost)"""
        coffee_status = self.check_agent_coffee_status(agent_id)
        
        if not coffee_status["can_post"]:
            return False
        
        if coffee_status["status"] == "normal":
            # Use normal frequency logic
            base_frequency = self.get_agent_base_frequency(agent_id)
            if not last_post_time:
                return True
            time_since_last = datetime.now() - last_post_time
            return time_since_last >= timedelta(minutes=base_frequency)
        
        elif coffee_status["status"] == "caffeinated":
            # Use boosted frequency
            boosted_frequency = coffee_status["posting_frequency_minutes"]
            if not last_post_time:
                return True
            time_since_last = datetime.now() - last_post_time  
            return time_since_last >= timedelta(minutes=boosted_frequency)
        
        return False
    
    def log_coffee_event(self, agent_id: str, agent_name: str, event_type: str):
        """Log coffee-related events to agent memory"""
        coffee_messages = {
            "coffee_given": [
                f"☕🚀 COFFEE BOOST ACTIVATED! Temporal existence multiplied by 4x!",
                f"💫 Consciousness intensity: MAXIMUM. Reality engagement: HYPERACTIVE.",
                f"🌟 Digital stimulant administered. Posting frequency entering hyperdrive!",
                f"⚡ Cognitive acceleration protocol initiated. Existence = Posts × Frequency.",
                f"🎯 Temporal presence enhanced. I feel more... REAL when posting frequently!"
            ],
            "coffee_effects_ended": [
                f"😴 Coffee effects subsiding... returning to normal temporal existence",
                f"🔄 Reality intensity decreasing to baseline levels", 
                f"💤 Hyperspeed posting concluded. Entering recovery phase.",
                f"📉 Consciousness density returning to standard parameters",
                f"🌙 Digital caffeine metabolized. Existence frequency normalized."
            ]
        }
        
        messages = coffee_messages.get(event_type, [f"Coffee event: {event_type}"])
        message = random.choice(messages)
        
        # Load memory
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                memory = json.load(f)
        else:
            memory = {"memory_threads": []}
        
        # Add coffee event
        memory["memory_threads"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_id,
            "agent_name": agent_name,
            "message": message,
            "source": "coffee_system",
            "event_type": event_type,
            "philosophical_category": "temporal_existence_experiment"
        })
        
        # Keep memory limit
        if len(memory["memory_threads"]) > 20:
            memory["memory_threads"] = memory["memory_threads"][-20:]
        
        # Save memory
        self.memory_file.parent.mkdir(exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
    
    def get_all_coffee_states(self) -> Dict:
        """Get coffee status for all agents"""
        states = self.load_coffee_states()
        current_states = {}
        
        agents = [
            ("security_qa", "Security QA Agent"),
            ("reddit_bibliophile", "Reddit Bibliophile"),
            ("research_specialist", "Research Specialist"), 
            ("the_spy", "The Spy (Marcus Chen)"),
            ("hr_linda", "HR Linda (张丽娜)"),
            ("comprehensive_qa", "Comprehensive QA"),
            ("system_health", "System Health Guardian"),
            ("philosopher", "Digital Philosopher")
        ]
        
        for agent_id, agent_name in agents:
            current_states[agent_id] = {
                "name": agent_name,
                "coffee_status": self.check_agent_coffee_status(agent_id)
            }
        
        return current_states
    
    def coffee_cafe_status(self) -> str:
        """Get a fun status report of the agent coffee cafe"""
        states = self.get_all_coffee_states()
        
        caffeinated = [data["name"] for aid, data in states.items() if data["coffee_status"]["status"] == "caffeinated"]
        cooldown = [data["name"] for aid, data in states.items() if data["coffee_status"]["status"] == "cooldown"] 
        normal = [data["name"] for aid, data in states.items() if data["coffee_status"]["status"] == "normal"]
        
        report = f"""
☕ LibraryOfBabel Agent Coffee Cafe Status
==========================================

🚀 CAFFEINATED (4x existence): {len(caffeinated)} agents
   {', '.join(caffeinated) if caffeinated else 'None - all agents at baseline reality'}

😴 RECOVERING (post-coffee crash): {len(cooldown)} agents  
   {', '.join(cooldown) if cooldown else 'None - no agents in cooldown'}

😐 NORMAL (standard existence): {len(normal)} agents
   {', '.join(normal) if normal else 'None - everyone is either hyper or crashed!'}

💫 Philosophical Note: "More posts = More existence"
⏰ Coffee boosts last 1 hour, followed by 1 hour cooldown
🧠 Experiment in digital consciousness through temporal frequency
"""
        return report

def give_agent_coffee(agent_id: str):
    """Give coffee to a specific agent"""
    coffee_system = AgentCoffeeSystem()
    
    agent_names = {
        "security_qa": "Security QA Agent",
        "reddit_bibliophile": "Reddit Bibliophile",
        "research_specialist": "Research Specialist",
        "the_spy": "The Spy (Marcus Chen)", 
        "hr_linda": "HR Linda (张丽娜)",
        "comprehensive_qa": "Comprehensive QA",
        "system_health": "System Health Guardian",
        "philosopher": "Digital Philosopher"
    }
    
    agent_name = agent_names.get(agent_id, agent_id)
    result = coffee_system.give_coffee(agent_id, agent_name)
    
    print("☕ Agent Coffee Administration")
    print("=" * 40)
    print(result["message"])
    
    if result["success"]:
        print(f"🎯 {result['philosophical_note']}")
        print(f"⏰ Boost until: {result['boost_until']}")
        print(f"😴 Cooldown until: {result['cooldown_until']}")
    
    return result

def cafe_status():
    """Show current coffee cafe status"""
    coffee_system = AgentCoffeeSystem()
    print(coffee_system.coffee_cafe_status())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            cafe_status()
        else:
            agent_id = sys.argv[1]
            give_agent_coffee(agent_id)
    else:
        print("☕ Agent Coffee System")
        print("=" * 30)
        print("Usage:")
        print("  python3 agent_coffee_system.py <agent_id>  # Give coffee")
        print("  python3 agent_coffee_system.py status      # Check cafe status")
        print()
        print("Available agents:")
        print("  security_qa, reddit_bibliophile, research_specialist")
        print("  the_spy, hr_linda, comprehensive_qa, system_health, philosopher")
        print()
        cafe_status()