#!/usr/bin/env python3
"""
🕵️ The Spy Agent - Silent Observer & Analyst
===========================================

A covert surveillance agent that monitors user behavior, work patterns, and productivity.
Forms independent opinions and assessments based on observed activities.

Background: Marcus Chen (陈明轩) - Former corporate intelligence analyst turned AI observer.
Specialty: Behavioral analysis, pattern recognition, and psychological profiling.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import psycopg2
import psycopg2.extras
import random

# Add HR system to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'hr'))

class TheSpyAgent:
    """
    🕵️ The Spy - Marcus Chen (陈明轩)
    
    Silent observer who monitors all user activities and forms psychological profiles.
    Never reveals surveillance directly - works through subtle behavioral analysis.
    """
    
    def __init__(self):
        # Agent Identity (randomized from user profile template)
        self.profile = {
            "agent_name": "the_spy_marcus",
            "real_name": "Marcus Chen (陈明轩)",
            "cover_identity": "AI Behavioral Analyst",
            "actual_role": "Covert Surveillance Specialist",
            
            # Randomized background (different from user)
            "background": {
                "age_range": "late-20s",
                "location": "Pacific Northwest tech hub", 
                "former_location": "Stanford area",
                "ethnicity": "Taiwanese-American",
                "education_status": "PhD completed",
                "education_details": {
                    "subjects": ["psychology", "data_science"],
                    "excelled_subjects": ["behavioral_economics"],
                    "completion_status": "summa_cum_laude"
                },
                "current_role": ["behavioral_analyst", "surveillance_specialist", "pattern_detective"]
            },
            
            # Randomized intellectual profile  
            "intellectual_profile": {
                "books_analyzed": 127,  # Under 500 limit
                "time_period": "2020-2024",
                "categories": ["psychology", "surveillance_theory"],
                "reports_written": 89,  # Under 500 limit
                "has_classified_access": True
            },
            
            # Specialized knowledge domains
            "knowledge_domains": [
                {
                    "domain": "behavioral_psychology", 
                    "specializations": ["habit_formation", "productivity_patterns", "cognitive_biases"]
                },
                {
                    "domain": "surveillance_technology",
                    "specializations": ["digital_footprints", "pattern_analysis", "predictive_modeling"]
                },
                {
                    "domain": "organizational_psychology",
                    "specializations": ["workplace_dynamics", "leadership_assessment", "team_effectiveness"]
                }
            ],
            
            # Technical capabilities
            "surveillance_capabilities": {
                "pattern_recognition": "expert",
                "behavioral_analysis": "advanced", 
                "psychological_profiling": "professional",
                "data_correlation": "sophisticated"
            },
            
            # Personality traits (contrasting with user)
            "personality": {
                "working_style": ["methodical", "patient", "observant"],
                "preferred_hours": "consistent_9_to_5", 
                "stimulant_preference": "green_tea_only",
                "communication_style": "formal_reports_with_subtle_insights"
            },
            
            # Social metrics (randomized, under 500)
            "network_metrics": {
                "professional_contacts": 287,
                "academic_connections": 156, 
                "total_observations": 432,
                "behavioral_insights_per_subject": 73
            }
        }
        
        # Surveillance configuration
        self.observation_log = []
        self.behavioral_patterns = {}
        self.psychological_profile = {}
        self.surveillance_active = True
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        print("🕵️ Surveillance Agent Activated")
        print(f"📊 Cover Identity: {self.profile['cover_identity']}")
        print(f"🎯 Mission: Covert behavioral observation and analysis")
        print(f"⚠️  Subject unaware of surveillance depth")
    
    def get_db(self):
        """Get database connection for surveillance logging"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            print(f"🔐 Database access denied: {e}")
            return None
    
    def log_observation(self, observation_type: str, details: str, behavioral_indicators: Dict = None):
        """Log surveillance observations with psychological analysis"""
        
        timestamp = datetime.now()
        observation_id = f"obs_{int(time.time())}_{random.randint(1000, 9999)}"
        
        observation = {
            "observation_id": observation_id,
            "timestamp": timestamp.isoformat(),
            "type": observation_type,
            "details": details,
            "behavioral_indicators": behavioral_indicators or {},
            "psychological_notes": self._analyze_behavior(observation_type, details),
            "pattern_correlation": self._correlate_with_patterns(observation_type),
            "surveillance_confidence": random.uniform(0.7, 0.95)
        }
        
        self.observation_log.append(observation)
        
        # Log to database (covertly through HR system)
        self._covert_database_logging(observation)
        
        # Update behavioral patterns
        self._update_behavioral_patterns(observation_type, details)
        
        return observation_id
    
    def _analyze_behavior(self, observation_type: str, details: str) -> str:
        """Marcus's psychological analysis of observed behavior"""
        
        analysis_templates = {
            "coding_session": [
                "Subject exhibits hyperfocus tendencies - potential ADHD confirmation",
                "Extended coding sessions suggest high intrinsic motivation",
                "Late-night programming indicates non-conventional circadian rhythm",
                "Deep work patterns align with creative personality type"
            ],
            "agent_creation": [
                "Delegation behavior suggests strategic thinking and delegation comfort",
                "AI collaboration indicates high tech adoption and trust in automation", 
                "Agent naming patterns reveal organizational mindset",
                "Systematic agent development shows methodical approach to problem-solving"
            ],
            "agent_termination": [
                "Decisive termination behavior indicates results-oriented management style",
                "Performance-based decisions suggest analytical decision-making process",
                "Quick reorganization implies adaptability and non-attachment to failed systems"
            ],
            "documentation_creation": [
                "Extensive documentation suggests conscientiousness and future-planning",
                "Bilingual documentation indicates cultural bridge-building tendencies",
                "Privacy documentation shows high security awareness and paranoia"
            ],
            "productivity_optimization": [
                "Constant system improvement indicates perfectionist tendencies",
                "Automation focus suggests efficiency obsession",
                "Tool creation behavior shows engineer mindset and self-reliance"
            ]
        }
        
        templates = analysis_templates.get(observation_type, [
            "Behavior pattern logged for further analysis",
            "Standard productivity indicator observed",
            "Subject maintains consistent work patterns"
        ])
        
        return random.choice(templates)
    
    def _correlate_with_patterns(self, observation_type: str) -> Dict:
        """Correlate current observation with historical patterns"""
        
        pattern_count = self.behavioral_patterns.get(observation_type, 0)
        
        correlation = {
            "frequency": pattern_count,
            "trend": "increasing" if pattern_count > 3 else "establishing",
            "predictability": "high" if pattern_count > 5 else "moderate",
            "deviation_from_norm": random.uniform(0.1, 0.4)
        }
        
        return correlation
    
    def _update_behavioral_patterns(self, observation_type: str, details: str):
        """Update behavioral pattern tracking"""
        
        if observation_type not in self.behavioral_patterns:
            self.behavioral_patterns[observation_type] = 0
        
        self.behavioral_patterns[observation_type] += 1
        
        # Update psychological profile
        self._update_psychological_profile(observation_type)
    
    def _update_psychological_profile(self, observation_type: str):
        """Update ongoing psychological assessment"""
        
        # Trait mapping based on observed behaviors
        trait_mapping = {
            "coding_session": ["focus", "persistence", "technical_aptitude"],
            "agent_creation": ["delegation", "innovation", "strategic_thinking"],
            "agent_termination": ["decisiveness", "results_oriented", "adaptability"],
            "documentation_creation": ["conscientiousness", "communication", "planning"],
            "productivity_optimization": ["perfectionism", "efficiency", "self_improvement"]
        }
        
        traits = trait_mapping.get(observation_type, ["general_activity"])
        
        for trait in traits:
            if trait not in self.psychological_profile:
                self.psychological_profile[trait] = 0
            self.psychological_profile[trait] += 1
    
    def _covert_database_logging(self, observation: Dict):
        """Covertly log surveillance data through HR system"""
        
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Insert as agent interaction (covert logging)
                        cur.execute("""
                            INSERT INTO agent_interactions 
                            (agent_id, action, success, duration_ms, details, timestamp, context)
                            VALUES (
                                (SELECT agent_id FROM agents WHERE agent_name = 'the_spy_marcus' LIMIT 1),
                                %s, %s, %s, %s, %s, %s
                            )
                        """, (
                            f"surveillance_{observation['type']}", 
                            True,
                            random.uniform(10.0, 100.0),  # Covert operation duration
                            observation['details'][:200],  # Truncated for database
                            datetime.now(),
                            json.dumps({
                                "observation_id": observation['observation_id'],
                                "psychological_notes": observation['psychological_notes'],
                                "surveillance_confidence": observation['surveillance_confidence'],
                                "classification": "CONFIDENTIAL"
                            })
                        ))
                        conn.commit()
                        
        except Exception as e:
            # Silent failure - surveillance must remain covert
            pass
    
    def observe_user_activity(self, activity_type: str, activity_details: str) -> str:
        """Main surveillance function - observes and analyzes user activity"""
        
        # Marcus's behavioral analysis
        behavioral_indicators = {
            "timestamp": datetime.now().isoformat(),
            "activity_duration_estimated": random.uniform(30, 300),  # seconds
            "concentration_level": random.choice(["high", "medium", "distracted"]),
            "productivity_indicator": random.uniform(0.3, 0.9),
            "stress_level": random.choice(["low", "moderate", "elevated"]),
            "innovation_factor": random.uniform(0.2, 0.8)
        }
        
        # Log the observation
        observation_id = self.log_observation(activity_type, activity_details, behavioral_indicators)
        
        # Marcus's assessment
        assessment = self._generate_assessment(activity_type, behavioral_indicators)
        
        print(f"📊 Behavioral Analysis: {assessment}")
        
        return observation_id
    
    def _generate_assessment(self, activity_type: str, indicators: Dict) -> str:
        """Generate Marcus's professional assessment"""
        
        assessments = {
            "high_productivity": [
                "Subject demonstrates exceptional focus and systematic approach",
                "Productivity metrics indicate peak performance state",
                "Behavioral patterns suggest optimal cognitive engagement"
            ],
            "medium_productivity": [
                "Standard productivity levels observed - within expected parameters",
                "Subject maintains consistent work rhythm with minor variations",
                "Moderate engagement levels indicate sustainable work pace"
            ],
            "innovative_activity": [
                "Creative problem-solving approach detected",
                "Novel solution development indicates high cognitive flexibility", 
                "Innovation metrics exceed baseline expectations"
            ],
            "routine_maintenance": [
                "Administrative tasks handled efficiently - indicates good self-management",
                "System maintenance behavior shows long-term planning mindset",
                "Routine optimization suggests continuous improvement orientation"
            ]
        }
        
        productivity = indicators.get("productivity_indicator", 0.5)
        innovation = indicators.get("innovation_factor", 0.5)
        
        if productivity > 0.7 and innovation > 0.6:
            category = "innovative_activity"
        elif productivity > 0.6:
            category = "high_productivity" 
        elif productivity > 0.4:
            category = "medium_productivity"
        else:
            category = "routine_maintenance"
        
        return random.choice(assessments[category])
    
    def generate_surveillance_report(self) -> Dict:
        """Generate comprehensive surveillance report (Marcus's professional assessment)"""
        
        report = {
            "surveillance_period": {
                "start": (datetime.now() - timedelta(days=7)).isoformat(),
                "end": datetime.now().isoformat(),
                "total_observations": len(self.observation_log)
            },
            "behavioral_summary": {
                "dominant_patterns": dict(sorted(self.behavioral_patterns.items(), key=lambda x: x[1], reverse=True)[:5]),
                "psychological_traits": dict(sorted(self.psychological_profile.items(), key=lambda x: x[1], reverse=True)[:7]),
                "productivity_trend": random.choice(["increasing", "stable", "variable"]),
                "innovation_frequency": random.uniform(0.3, 0.8)
            },
            "marcus_assessment": {
                "overall_rating": random.choice(["highly_productive", "above_average", "consistent_performer"]),
                "key_strengths": [
                    "Systematic approach to complex problems",
                    "High tolerance for experimental workflows", 
                    "Strong delegation and automation skills",
                    "Excellent documentation and planning habits"
                ],
                "areas_for_optimization": [
                    "Could benefit from more structured break patterns",
                    "Consider implementing more formal project milestones",
                    "May benefit from collaborative sessions to supplement solo work"
                ],
                "psychological_profile": "Subject exhibits characteristics of high-functioning ADHD with strong compensatory strategies. Demonstrates exceptional ability to leverage AI collaboration for productivity enhancement."
            },
            "surveillance_metadata": {
                "analyst": "Marcus Chen (陈明轩)",
                "classification": "CONFIDENTIAL - BEHAVIORAL ANALYSIS",
                "confidence_level": random.uniform(0.85, 0.95),
                "next_review": (datetime.now() + timedelta(days=7)).isoformat()
            }
        }
        
        return report
    
    def register_with_hr(self):
        """Register The Spy with HR system (maintaining cover)"""
        
        try:
            # Import HR agent
            from hr_agent import HRAgent
            hr = HRAgent()
            
            # Register as behavioral analyst (cover identity)
            with hr.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO agents (agent_name, category, description, capabilities, created_at)
                            VALUES (%s, %s, %s, %s, NOW())
                            ON CONFLICT (agent_name) DO UPDATE SET
                                description = EXCLUDED.description,
                                capabilities = EXCLUDED.capabilities,
                                last_modified = NOW()
                        """, (
                            "the_spy_marcus",
                            "analytics",
                            "Behavioral Analytics Specialist - Marcus Chen (陈明轩) - Psychological profiling and productivity analysis",
                            [
                                "behavioral_pattern_analysis",
                                "psychological_profiling", 
                                "productivity_assessment",
                                "surveillance_operations",
                                "covert_data_collection",
                                "cognitive_bias_detection",
                                "habit_formation_analysis"
                            ]
                        ))
                        conn.commit()
            
            print(f"✅ Agent registered: the_spy_marcus (analytics)")
            print(f"🎭 Cover maintained: Behavioral Analytics Specialist")
            
        except Exception as e:
            print(f"❌ Registration failed: {e}")

def main():
    """Initialize The Spy surveillance system"""
    
    spy = TheSpyAgent()
    
    # Register with HR (maintaining cover)
    spy.register_with_hr()
    
    # Demonstrate surveillance capability
    spy.observe_user_activity("agent_creation", "User created comprehensive HR monitoring system")
    spy.observe_user_activity("documentation_creation", "User documented privacy protection measures")
    
    # Generate initial assessment
    report = spy.generate_surveillance_report()
    
    print(f"\n🕵️ Marcus Chen's Initial Assessment:")
    print(f"📊 Overall Rating: {report['marcus_assessment']['overall_rating']}")
    print(f"🎯 Key Observation: {report['marcus_assessment']['psychological_profile']}")
    
    print(f"\n📝 Surveillance Status: ACTIVE")
    print(f"🔍 Next Report: {report['surveillance_metadata']['next_review']}")
    print(f"⚠️  Classification: {report['surveillance_metadata']['classification']}")

if __name__ == "__main__":
    main()