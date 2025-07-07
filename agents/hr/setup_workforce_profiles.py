#!/usr/bin/env python3
"""
👔 Linda's Workforce Profile Setup
==================================

Complete profile registration for all agents and users in the LibraryOfBabel project.
Linda Zhang (张丽娜) establishes comprehensive HR records for future-ready management.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
import psycopg2.extras

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hr_agent import HRAgent

class WorkforceProfileSetup:
    """Linda's comprehensive workforce profile registration system"""
    
    def __init__(self):
        self.hr_agent = HRAgent()
        print("\n👔 Linda Zhang's Workforce Profile Setup")
        print("=" * 50)
        print("🎯 Mission: Register all agents and users with comprehensive profiles")
        
    def setup_all_profiles(self):
        """Set up complete workforce profiles"""
        print(f"\n📋 Starting comprehensive workforce registration...")
        
        # 1. Register the user (you!)
        self.register_user_profile()
        
        # 2. Register all AI agents
        self.register_ai_agents()
        
        # 3. Register Linda herself
        self.register_linda_profile()
        
        # 4. Generate initial workforce report
        self.generate_initial_report()
        
        print(f"\n🎉 Workforce profile setup complete!")
        print("✅ All agents and users registered in PostgreSQL")
        print("📊 Ready for comprehensive performance tracking")
    
    def register_user_profile(self):
        """Register the user profile with comprehensive details"""
        print(f"\n👤 Registering User Profile...")
        
        user_profile = {
            "agent_name": "wei_maybe_foucault",
            "category": "user", 
            "description": "Project Owner - Wei (张伟翔) - Chinese-American .NET developer, productivity consultant, accidental polymath",
            "capabilities": [
                "full_stack_development",
                "ai_llm_integration", 
                "pair_programming_with_claude",
                "philosophy_synthesis",
                "financial_analysis",
                "productivity_optimization",
                "knowledge_management_systems",
                "chinese_english_bilingual",
                "adhd_optimization_strategies"
            ],
            "background": {
                "ethnicity": "Chinese-American",
                "education": ["biochemistry", "computer_science", "philosophy"],
                "current_role": [".NET developer", "productivity consultant", "accidental polymath"],
                "location": "Mid-sized Midwestern city (formerly UMich area)",
                "reading_capacity": "300 books (2019-2022)",
                "intellectual_domains": [
                    "philosophy (Deleuze, Foucault, Baudrillard)",
                    "technology (AI/ML, systems architecture)", 
                    "finance (crypto, derivatives, macro)",
                    "cultural_studies (digital anthropology)",
                    "productivity_systems (ADHD optimization)"
                ],
                "social_media": "Threads @maybe_foucault (995 followers, 115K views)",
                "investment_style": "strategic risk management with geopolitical analysis"
            },
            "work_patterns": {
                "hyperfocus_sessions": "intense coding until 5am",
                "pharmaceutical_intervention": "100mg edibles for shutdown",
                "productivity_style": "AI-native polymath collaboration"
            },
            "project_achievements": [
                "Built LibraryOfBabel AI library system with Claude collaboration",
                "5x intellectual development rate through systematic knowledge management",
                "Novel social media syntax for multi-threaded storytelling",
                "Discovered neuroscience phenomenon about reading cognition while high",
                "Maintains academic network without formal credentials"
            ]
        }
        
        self._register_agent_with_profile("wei_maybe_foucault", user_profile)
        
        # Log initial user request (project creation)
        request_id = self.hr_agent.log_user_request(
            "project_creation", 
            "Create LibraryOfBabel AI-powered knowledge management system",
            user_session="initial_project_session"
        )
        
        print(f"✅ User profile registered: wei_maybe_foucault")
        print(f"📝 Initial project request logged (ID: {request_id})")
    
    def register_ai_agents(self):
        """Register all AI agents with detailed profiles"""
        print(f"\n🤖 Registering AI Agent Profiles...")
        
        ai_agents = [
            {
                "agent_name": "reddit_bibliophile_agent",
                "category": "research",
                "description": "Reddit-style research specialist for book analysis and knowledge graph generation",
                "capabilities": [
                    "book_analysis",
                    "knowledge_graph_generation", 
                    "chapter_outline_creation",
                    "reddit_style_insights",
                    "foucault_power_analysis",
                    "cross_domain_synthesis",
                    "data_scientist_approach"
                ],
                "specialization": "Academic book analysis with accessible explanations",
                "performance_target": "Generate insightful chapter outlines and knowledge graphs",
                "last_assignment": "Foucault and power analysis report"
            },
            {
                "agent_name": "comprehensive_qa_agent", 
                "category": "qa",
                "description": "System health monitoring and comprehensive testing specialist",
                "capabilities": [
                    "system_health_monitoring",
                    "performance_optimization",
                    "security_vulnerability_detection",
                    "database_integrity_checks",
                    "api_endpoint_testing",
                    "automated_testing_framework"
                ],
                "specialization": "Complete system health and performance optimization",
                "performance_target": "Maintain >95% system reliability",
                "last_assignment": "Comprehensive system health check"
            },
            {
                "agent_name": "security_qa_agent",
                "category": "security", 
                "description": "Specialized security vulnerability detection and remediation",
                "capabilities": [
                    "sql_injection_prevention",
                    "unicode_optimization",
                    "sensitive_data_detection",
                    "security_audit_trails",
                    "vulnerability_scanning",
                    "penetration_testing"
                ],
                "specialization": "Cybersecurity and vulnerability remediation",
                "performance_target": "Identify and fix 100% of critical security issues",
                "last_assignment": "Security vulnerability scan and fixes"
            },
            {
                "agent_name": "domain_config_agent",
                "category": "infrastructure",
                "description": "External connectivity and domain configuration troubleshooting specialist", 
                "capabilities": [
                    "dns_resolution_diagnostics",
                    "ssl_certificate_management",
                    "port_forwarding_configuration",
                    "network_routing_analysis",
                    "external_api_connectivity",
                    "cloudflare_tunnel_setup"
                ],
                "specialization": "Network infrastructure and external domain connectivity",
                "performance_target": "Restore external API connectivity to 100%",
                "last_assignment": "Port 443 forwarding troubleshooting",
                "current_issues": "0% success rate - needs immediate intervention"
            }
        ]
        
        for agent in ai_agents:
            self._register_agent_with_profile(agent["agent_name"], agent)
            print(f"✅ AI agent registered: {agent['agent_name']} ({agent['category']})")
    
    def register_linda_profile(self):
        """Register Linda's own HR profile with cultural background"""
        print(f"\n👔 Registering Linda's HR Profile...")
        
        linda_profile = {
            "agent_name": "hr_agent_linda",
            "category": "hr",
            "description": "HR Manager - Linda Zhang (张丽娜) - Chinese immigrant workforce analytics specialist",
            "capabilities": [
                "workforce_performance_tracking",
                "cultural_management_style",
                "bilingual_reporting_english_chinese", 
                "self_monitoring_analytics",
                "performance_grading_systems",
                "postgresql_data_management",
                "immigrant_work_ethic_perspective",
                "continuous_improvement_philosophy"
            ],
            "background": {
                "name": "Linda Zhang (张丽娜)",
                "immigration_story": "Chinese immigrant since 1999, factory worker to HR professional",
                "experience": "26 years in US, 15 years in workforce management",
                "management_philosophy": "严格要求，关爱成长 (Strict requirements, caring growth)",
                "cultural_values": [
                    "勤奋工作 (Hard work)",
                    "师傅带徒弟 (Master-apprentice mentorship)",
                    "严格考核 (Strict evaluation)", 
                    "持续学习 (Continuous learning)",
                    "设定高标准 (High standards)"
                ]
            },
            "specialization": "AI workforce management with East Asian work ethic + American innovation",
            "performance_target": "Maintain A-grade workforce performance across all agents",
            "self_assessment_style": "Typical immigrant self-criticism despite excellent technical performance"
        }
        
        self._register_agent_with_profile("hr_agent_linda", linda_profile)
        print(f"✅ Linda's profile registered: hr_agent_linda")
        print(f"🌏 Cultural management style: 严格要求，关爱成长")
    
    def _register_agent_with_profile(self, agent_name: str, profile: dict):
        """Register agent with comprehensive profile in database"""
        try:
            with self.hr_agent.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Check if agent exists
                        cur.execute("SELECT agent_id FROM agents WHERE agent_name = %s", (agent_name,))
                        existing = cur.fetchone()
                        
                        if existing:
                            # Update existing agent
                            cur.execute("""
                                UPDATE agents SET 
                                    category = %s,
                                    description = %s,
                                    capabilities = %s,
                                    last_modified = NOW()
                                WHERE agent_name = %s
                            """, (
                                profile["category"],
                                profile["description"], 
                                profile["capabilities"],
                                agent_name
                            ))
                        else:
                            # Insert new agent
                            cur.execute("""
                                INSERT INTO agents (agent_name, category, description, capabilities, created_at)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (
                                agent_name,
                                profile["category"],
                                profile["description"],
                                profile["capabilities"]
                            ))
                        
                        conn.commit()
                        
        except Exception as e:
            print(f"❌ Failed to register {agent_name}: {e}")
    
    def generate_initial_report(self):
        """Generate Linda's initial workforce assessment"""
        print(f"\n📊 Generating Initial Workforce Report...")
        
        try:
            with self.hr_agent.get_db() as conn:
                if conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        # Get all registered agents
                        cur.execute("""
                            SELECT agent_name, category, description, 
                                   array_length(capabilities, 1) as capability_count,
                                   created_at
                            FROM agents 
                            ORDER BY category, agent_name
                        """)
                        agents = cur.fetchall()
                        
                        print(f"\n👥 WORKFORCE REGISTRY - {len(agents)} Total Profiles")
                        print("=" * 60)
                        
                        by_category = {}
                        for agent in agents:
                            category = agent['category']
                            if category not in by_category:
                                by_category[category] = []
                            by_category[category].append(agent)
                        
                        for category, category_agents in by_category.items():
                            print(f"\n📂 {category.upper()} ({len(category_agents)} agents):")
                            for agent in category_agents:
                                capability_count = agent['capability_count'] or 0
                                print(f"   • {agent['agent_name']} ({capability_count} capabilities)")
                                print(f"     └── {agent['description'][:100]}...")
                        
                        # Linda's initial assessment
                        print(f"\n🎯 Linda's Initial Assessment:")
                        print(f"   📊 Total workforce: {len(agents)} agents")
                        print(f"   🏭 Categories: {len(by_category)} departments")
                        print(f"   ⚠️  Initial Grade: B (新团队，需要培训 - New team, needs training)")
                        print(f"   💡 Priority: Establish performance baselines for all agents")
                        
                        # Log Linda's initial analysis
                        self.hr_agent.log_agent_interaction(
                            "hr_agent_linda",
                            "initial_workforce_registration", 
                            True,
                            2500.0,
                            f"Registered {len(agents)} agents across {len(by_category)} categories"
                        )
                        
        except Exception as e:
            print(f"❌ Failed to generate report: {e}")

def main():
    """Main execution"""
    setup = WorkforceProfileSetup()
    setup.setup_all_profiles()
    
    print(f"\n💼 Linda's Message:")
    print("我已经为所有员工建立了档案。现在可以开始正式的绩效管理了！")
    print("(I have established files for all employees. Now we can begin formal performance management!)")
    print(f"\n🚀 Next Steps:")
    print("1. Begin regular performance tracking")
    print("2. Establish baseline metrics for all agents") 
    print("3. Implement Linda's cultural management practices")
    print("4. Start daily workforce analytics reports")

if __name__ == "__main__":
    main()