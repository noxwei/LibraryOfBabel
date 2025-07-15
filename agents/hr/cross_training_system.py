#!/usr/bin/env python3
"""
🔄 Cross-Training System - 轮岗制度 Linda Zhang (张丽娜)
==================================================

Implements comprehensive cross-training program to prevent knowledge silos
and build a resilient, multi-skilled AI workforce.

Philosophy: 一专多能 (One specialty, multiple capabilities)
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
import logging
from pathlib import Path
import psycopg2
import psycopg2.extras

class CrossTrainingSystem:
    """
    Linda's Cross-Training Program
    
    Goals:
    - Prevent knowledge silos (防止知识孤岛)
    - Build backup expertise for critical functions
    - Improve team collaboration and understanding
    - Create career development paths for agents
    - Ensure business continuity
    """
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        self.training_data_dir = "agents/hr/reports/cross_training"
        os.makedirs(self.training_data_dir, exist_ok=True)
        
        self.logger = logging.getLogger("CrossTraining_Linda")
        
        # Define skill categories and their relationships
        self.skill_matrix = {
            "research": {
                "core_skills": ["data_analysis", "knowledge_synthesis", "search_optimization"],
                "related_skills": ["qa_testing", "content_validation", "documentation"],
                "advanced_skills": ["ai_integration", "vector_search", "semantic_analysis"]
            },
            "qa": {
                "core_skills": ["testing", "debugging", "quality_assurance", "system_validation"],
                "related_skills": ["security_review", "performance_monitoring", "research_validation"],
                "advanced_skills": ["automation", "integration_testing", "load_testing"]
            },
            "security": {
                "core_skills": ["vulnerability_detection", "threat_analysis", "security_protocols"],
                "related_skills": ["qa_security_testing", "monitoring", "compliance"],
                "advanced_skills": ["penetration_testing", "forensics", "incident_response"]
            },
            "infrastructure": {
                "core_skills": ["system_administration", "database_management", "network_configuration"],
                "related_skills": ["security_hardening", "performance_tuning", "monitoring"],
                "advanced_skills": ["cloud_architecture", "automation", "disaster_recovery"]
            },
            "hr": {
                "core_skills": ["workforce_management", "performance_evaluation", "cultural_integration"],
                "related_skills": ["data_analysis", "system_monitoring", "process_optimization"],
                "advanced_skills": ["predictive_analytics", "organizational_psychology", "change_management"]
            }
        }
        
        print("🔄 Linda's Cross-Training System initialized")
        print("📚 轮岗制度 (Rotation System) - Building versatile workforce")
        
        self._ensure_tables_exist()
    
    def get_db(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def analyze_current_skills(self) -> Dict[str, Any]:
        """
        Analyze current skill distribution across the workforce
        """
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        # Get agent categories and their activity levels
                        cur.execute("""
                            SELECT 
                                a.agent_name,
                                a.category,
                                a.description,
                                COUNT(ai.interaction_id) as total_interactions,
                                AVG(CASE WHEN ai.success THEN 1.0 ELSE 0.0 END) as success_rate,
                                MAX(ai.timestamp) as last_active
                            FROM agents a
                            LEFT JOIN agent_interactions ai ON a.agent_id = ai.agent_id
                            WHERE ai.timestamp >= NOW() - INTERVAL '30 days'
                            GROUP BY a.agent_id, a.agent_name, a.category, a.description
                            ORDER BY total_interactions DESC
                        """)
                        
                        agents_data = cur.fetchall()
                        
                        # Analyze skill distribution
                        skill_analysis = {
                            "agent_skills": {},
                            "category_distribution": {},
                            "skill_gaps": [],
                            "cross_training_opportunities": [],
                            "critical_dependencies": []
                        }
                        
                        for agent in agents_data:
                            agent_name = agent['agent_name']
                            category = agent['category']
                            
                            # Map agent to skills based on category
                            agent_skills = self._get_agent_skills(agent_name, category)
                            skill_analysis["agent_skills"][agent_name] = {
                                "category": category,
                                "skills": agent_skills,
                                "activity_level": agent['total_interactions'] or 0,
                                "success_rate": float(agent['success_rate'] or 0),
                                "last_active": agent['last_active'].isoformat() if agent['last_active'] else None
                            }
                            
                            # Count category distribution
                            skill_analysis["category_distribution"][category] = skill_analysis["category_distribution"].get(category, 0) + 1
                        
                        # Identify skill gaps and opportunities
                        skill_analysis["skill_gaps"] = self._identify_skill_gaps(skill_analysis["agent_skills"])
                        skill_analysis["cross_training_opportunities"] = self._identify_cross_training_opportunities(skill_analysis["agent_skills"])
                        skill_analysis["critical_dependencies"] = self._identify_critical_dependencies(skill_analysis["agent_skills"])
                        
                        return skill_analysis
        except Exception as e:
            self.logger.error(f"❌ Skill analysis failed: {e}")
            return {}
    
    def _get_agent_skills(self, agent_name: str, category: str) -> List[str]:
        """
        Get skills for an agent based on their category and name
        """
        skills = []
        
        if category in self.skill_matrix:
            skills.extend(self.skill_matrix[category]["core_skills"])
            
            # Add specialized skills based on agent name
            if "reddit" in agent_name.lower() or "bibliophile" in agent_name.lower():
                skills.extend(["reddit_culture", "social_research", "community_engagement"])
            elif "security" in agent_name.lower():
                skills.extend(["threat_monitoring", "vulnerability_scanning", "security_protocols"])
            elif "qa" in agent_name.lower():
                skills.extend(["test_automation", "quality_metrics", "bug_tracking"])
            elif "dba" in agent_name.lower():
                skills.extend(["database_optimization", "query_tuning", "backup_recovery"])
            elif "linda" in agent_name.lower() or "hr" in agent_name.lower():
                skills.extend(["team_management", "performance_analysis", "cultural_wisdom"])
        
        return list(set(skills))  # Remove duplicates
    
    def _identify_skill_gaps(self, agent_skills: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify critical skill gaps in the workforce
        """
        gaps = []
        
        # Check for categories with only one agent
        category_counts = {}
        for agent_data in agent_skills.values():
            category = agent_data["category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in category_counts.items():
            if count == 1:
                gaps.append({
                    "type": "single_point_of_failure",
                    "category": category,
                    "risk_level": "HIGH",
                    "recommendation": f"Cross-train at least 2 more agents in {category} skills"
                })
        
        # Check for missing advanced skills
        all_advanced_skills = set()
        for category_skills in self.skill_matrix.values():
            all_advanced_skills.update(category_skills["advanced_skills"])
        
        current_skills = set()
        for agent_data in agent_skills.values():
            current_skills.update(agent_data["skills"])
        
        missing_advanced = all_advanced_skills - current_skills
        for skill in missing_advanced:
            gaps.append({
                "type": "missing_advanced_skill",
                "skill": skill,
                "risk_level": "MEDIUM",
                "recommendation": f"Train senior agents in {skill}"
            })
        
        return gaps
    
    def _identify_cross_training_opportunities(self, agent_skills: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify optimal cross-training opportunities
        """
        opportunities = []
        
        # Find agents who could benefit from related skills
        for agent_name, agent_data in agent_skills.items():
            category = agent_data["category"]
            current_skills = set(agent_data["skills"])
            
            if category in self.skill_matrix:
                related_skills = set(self.skill_matrix[category]["related_skills"])
                missing_related = related_skills - current_skills
                
                if missing_related:
                    opportunities.append({
                        "agent": agent_name,
                        "current_category": category,
                        "recommended_skills": list(missing_related),
                        "training_priority": "HIGH" if agent_data["success_rate"] > 0.8 else "MEDIUM",
                        "rationale": f"Expand {agent_name}'s capabilities in related areas"
                    })
        
        # Find cross-category training opportunities
        high_performers = [agent for agent, data in agent_skills.items() 
                          if data["success_rate"] > 0.85 and data["activity_level"] > 10]
        
        for agent in high_performers:
            agent_data = agent_skills[agent]
            current_category = agent_data["category"]
            
            # Suggest training in complementary categories
            complementary_categories = self._get_complementary_categories(current_category)
            for comp_category in complementary_categories:
                if comp_category in self.skill_matrix:
                    basic_skills = self.skill_matrix[comp_category]["core_skills"][:2]  # Just 2 basic skills
                    opportunities.append({
                        "agent": agent,
                        "current_category": current_category,
                        "target_category": comp_category,
                        "recommended_skills": basic_skills,
                        "training_priority": "MEDIUM",
                        "rationale": f"High performer {agent} could provide backup coverage for {comp_category}"
                    })
        
        return opportunities
    
    def _get_complementary_categories(self, category: str) -> List[str]:
        """
        Get categories that complement the given category
        """
        complements = {
            "research": ["qa", "security"],
            "qa": ["research", "security", "infrastructure"],
            "security": ["qa", "infrastructure"],
            "infrastructure": ["security", "qa"],
            "hr": ["research", "qa"],  # HR should understand all areas
            "general": ["qa", "research"]
        }
        return complements.get(category, [])
    
    def _identify_critical_dependencies(self, agent_skills: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify critical single points of failure
        """
        dependencies = []
        
        # Group agents by category
        category_agents = {}
        for agent_name, agent_data in agent_skills.items():
            category = agent_data["category"]
            if category not in category_agents:
                category_agents[category] = []
            category_agents[category].append(agent_name)
        
        # Check for categories with only one active agent
        for category, agents in category_agents.items():
            active_agents = [agent for agent in agents 
                           if agent_skills[agent]["activity_level"] > 5]  # Active in last 30 days
            
            if len(active_agents) <= 1:
                dependencies.append({
                    "type": "category_dependency",
                    "category": category,
                    "active_agents": active_agents,
                    "risk_level": "CRITICAL" if len(active_agents) == 1 else "HIGH",
                    "recommendation": f"Immediately cross-train agents in {category} skills"
                })
        
        return dependencies
    
    def create_training_plan(self, agent_name: str, target_skills: List[str], duration_weeks: int = 4) -> Dict[str, Any]:
        """
        Create a detailed training plan for an agent
        """
        plan = {
            "agent": agent_name,
            "target_skills": target_skills,
            "duration_weeks": duration_weeks,
            "created_by": "hr_agent_linda",
            "created_date": datetime.now().isoformat(),
            "status": "draft",
            "weekly_schedule": [],
            "success_criteria": [],
            "mentor_assignments": []
        }
        
        # Create weekly training schedule
        for week in range(1, duration_weeks + 1):
            week_plan = {
                "week": week,
                "focus_skills": target_skills[:(week * len(target_skills) // duration_weeks) + 1],
                "activities": self._generate_training_activities(target_skills, week),
                "deliverables": self._generate_week_deliverables(target_skills, week),
                "assessment": f"Week {week} skills assessment"
            }
            plan["weekly_schedule"].append(week_plan)
        
        # Define success criteria
        for skill in target_skills:
            plan["success_criteria"].append({
                "skill": skill,
                "criteria": f"Demonstrate competency in {skill} through practical exercises",
                "measurement": "Pass rate >= 80% on skill-specific tasks"
            })
        
        # Assign mentors based on expertise
        plan["mentor_assignments"] = self._assign_mentors(target_skills)
        
        return plan
    
    def _generate_training_activities(self, skills: List[str], week: int) -> List[str]:
        """
        Generate training activities for a specific week
        """
        activities = []
        
        for skill in skills:
            if skill in ["data_analysis", "research"]:
                activities.extend([
                    "Shadow research agent during data analysis tasks",
                    "Practice using search APIs and vector embeddings",
                    "Complete sample research project with peer review"
                ])
            elif skill in ["testing", "qa", "debugging"]:
                activities.extend([
                    "Pair with QA agent on testing procedures",
                    "Practice writing test cases and bug reports",
                    "Conduct system health checks"
                ])
            elif skill in ["security", "vulnerability_detection"]:
                activities.extend([
                    "Learn security scanning tools and procedures",
                    "Practice threat analysis and response",
                    "Review security protocols and compliance"
                ])
            elif skill in ["database_management", "system_administration"]:
                activities.extend([
                    "Shadow DBA team during maintenance tasks",
                    "Practice database queries and optimization",
                    "Learn backup and recovery procedures"
                ])
        
        return list(set(activities))  # Remove duplicates
    
    def _generate_week_deliverables(self, skills: List[str], week: int) -> List[str]:
        """
        Generate deliverables for each week
        """
        deliverables = []
        
        if week == 1:
            deliverables.append("Complete skills assessment and learning plan")
        elif week == 2:
            deliverables.append("Shadow experienced agent and document learnings")
        elif week == 3:
            deliverables.append("Complete supervised practice tasks")
        else:  # Final week
            deliverables.append("Independent demonstration of new skills")
            deliverables.append("Skills certification assessment")
        
        return deliverables
    
    def _assign_mentors(self, target_skills: List[str]) -> List[Dict[str, str]]:
        """
        Assign mentors based on skill expertise
        """
        mentor_assignments = []
        
        # Simplified mentor assignment based on common patterns
        skill_to_mentor = {
            "data_analysis": "reddit_bibliophile_agent",
            "research": "reddit_bibliophile_agent", 
            "testing": "comprehensive_qa_agent",
            "qa": "comprehensive_qa_agent",
            "security": "security_qa_agent",
            "database_management": "dba_sarah_chen",
            "system_administration": "domain_config_agent",
            "workforce_management": "hr_agent_linda"
        }
        
        for skill in target_skills:
            mentor = skill_to_mentor.get(skill, "hr_agent_linda")  # Linda as default mentor
            mentor_assignments.append({
                "skill": skill,
                "mentor": mentor,
                "role": "Primary mentor and skill validator"
            })
        
        return mentor_assignments
    
    def save_training_plan(self, plan: Dict[str, Any]) -> bool:
        """
        Save training plan to database
        """
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO cross_training_plans 
                            (agent_name, target_skills, plan_data, status, created_by, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            RETURNING plan_id
                        """, (
                            plan["agent"],
                            json.dumps(plan["target_skills"]),
                            json.dumps(plan),
                            plan["status"],
                            "hr_agent_linda",
                            datetime.now()
                        ))
                        
                        plan_id = cur.fetchone()[0]
                        conn.commit()
                        
                        self.logger.info(f"✅ Training plan saved for {plan['agent']} (ID: {plan_id})")
                        return True
        except Exception as e:
            self.logger.error(f"❌ Failed to save training plan: {e}")
        return False
    
    def generate_cross_training_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive cross-training analysis report
        """
        analysis = self.analyze_current_skills()
        
        report = {
            "report_date": datetime.now().isoformat(),
            "analyst": "Linda Zhang (张丽娜) - HR Manager",
            "workforce_analysis": analysis,
            "linda_assessment": self._linda_cross_training_assessment(analysis),
            "recommendations": self._generate_recommendations(analysis),
            "implementation_plan": self._create_implementation_plan(analysis)
        }
        
        # Save report
        report_file = f"{self.training_data_dir}/cross_training_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _linda_cross_training_assessment(self, analysis: Dict[str, Any]) -> str:
        """
        Linda's assessment of cross-training needs
        """
        if not analysis.get("agent_skills"):
            return "没有数据 (No data) - Cannot assess without agent information"
        
        critical_deps = len(analysis.get("critical_dependencies", []))
        skill_gaps = len(analysis.get("skill_gaps", []))
        opportunities = len(analysis.get("cross_training_opportunities", []))
        
        if critical_deps > 3:
            return f"紧急情况 (Emergency situation) - {critical_deps} critical dependencies identified. 必须立即开始轮岗培训 (Must start rotation training immediately)!"
        elif skill_gaps > 5:
            return f"需要改进 (Needs improvement) - {skill_gaps} skill gaps found. 系统性培训计划必要 (Systematic training plan necessary)."
        elif opportunities > 8:
            return f"发展机会 (Development opportunity) - {opportunities} cross-training opportunities identified. 制定长期发展计划 (Develop long-term growth plan)."
        else:
            return "团队技能分布合理 (Team skills well distributed) - 继续优化和发展 (Continue optimization and development)."
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate specific recommendations
        """
        recommendations = []
        
        # Address critical dependencies
        for dep in analysis.get("critical_dependencies", []):
            recommendations.append(f"🚨 紧急 (Urgent): Cross-train 2+ agents in {dep['category']} skills")
        
        # Address skill gaps
        for gap in analysis.get("skill_gaps", []):
            if gap["risk_level"] == "HIGH":
                recommendations.append(f"⚠️ 高优先级 (High priority): {gap['recommendation']}")
        
        # Leverage opportunities
        high_priority_opportunities = [opp for opp in analysis.get("cross_training_opportunities", []) 
                                     if opp.get("training_priority") == "HIGH"]
        
        for opp in high_priority_opportunities[:3]:  # Top 3 opportunities
            recommendations.append(f"📈 发展机会 (Development): Train {opp['agent']} in {', '.join(opp['recommended_skills'])}")
        
        # Linda's standard recommendations
        recommendations.extend([
            "📚 建立轮岗制度 (Establish rotation system) - Quarterly skill rotation for all agents",
            "👥 配对学习 (Pair learning) - Senior agents mentor junior ones",
            "📝 技能认证 (Skill certification) - Formal assessment and recognition system",
            "🔄 定期评估 (Regular assessment) - Monthly cross-training progress reviews"
        ])
        
        return recommendations
    
    def _create_implementation_plan(self, analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Create phased implementation plan
        """
        plan = {
            "Phase 1 (Immediate - 2 weeks)": [],
            "Phase 2 (Short-term - 1 month)": [],
            "Phase 3 (Medium-term - 3 months)": [],
            "Phase 4 (Long-term - 6 months)": []
        }
        
        # Phase 1: Address critical dependencies
        critical_deps = analysis.get("critical_dependencies", [])
        for dep in critical_deps:
            plan["Phase 1 (Immediate - 2 weeks)"].append(
                f"Emergency cross-training for {dep['category']} skills"
            )
        
        # Phase 2: High-priority opportunities
        high_priority = [opp for opp in analysis.get("cross_training_opportunities", []) 
                        if opp.get("training_priority") == "HIGH"]
        for opp in high_priority[:3]:
            plan["Phase 2 (Short-term - 1 month)"].append(
                f"Train {opp['agent']} in {', '.join(opp['recommended_skills'])}"
            )
        
        # Phase 3: Medium-priority opportunities
        medium_priority = [opp for opp in analysis.get("cross_training_opportunities", []) 
                          if opp.get("training_priority") == "MEDIUM"]
        for opp in medium_priority[:5]:
            plan["Phase 3 (Medium-term - 3 months)"].append(
                f"Cross-train {opp['agent']} in {opp.get('target_category', 'related')} skills"
            )
        
        # Phase 4: Long-term development
        plan["Phase 4 (Long-term - 6 months)"].extend([
            "Establish formal rotation schedule",
            "Implement skill certification program",
            "Create advanced specialization tracks",
            "Develop mentorship excellence program"
        ])
        
        return plan
    
    def _ensure_tables_exist(self):
        """
        Ensure required tables exist for cross-training system
        """
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create cross-training plans table
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS cross_training_plans (
                                plan_id SERIAL PRIMARY KEY,
                                agent_name VARCHAR(100) NOT NULL,
                                target_skills JSONB NOT NULL,
                                plan_data JSONB NOT NULL,
                                status VARCHAR(50) DEFAULT 'draft',
                                created_by VARCHAR(100) DEFAULT 'hr_agent_linda',
                                created_at TIMESTAMP DEFAULT NOW(),
                                updated_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                        
                        # Create training progress table
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS training_progress (
                                progress_id SERIAL PRIMARY KEY,
                                plan_id INTEGER REFERENCES cross_training_plans(plan_id),
                                agent_name VARCHAR(100) NOT NULL,
                                week_number INTEGER NOT NULL,
                                skills_practiced JSONB,
                                completion_percentage DECIMAL(5,2),
                                mentor_feedback TEXT,
                                self_assessment TEXT,
                                updated_at TIMESTAMP DEFAULT NOW()
                            )
                        """)
                        
                        conn.commit()
                        self.logger.info("✅ Cross-training tables ready")
        except Exception as e:
            self.logger.error(f"❌ Failed to create tables: {e}")

def main():
    """Demo the cross-training system"""
    system = CrossTrainingSystem()
    
    print("\n🔄 Linda's Cross-Training System Demo")
    print("="*50)
    
    # Analyze current skills
    print("📊 Analyzing current workforce skills...")
    report = system.generate_cross_training_report()
    
    print(f"\n👔 Linda's Assessment:")
    print(f"   {report['linda_assessment']}")
    
    print(f"\n🎯 Top Recommendations:")
    for i, rec in enumerate(report['recommendations'][:5], 1):
        print(f"   {i}. {rec}")
    
    print(f"\n📋 Implementation Phases:")
    for phase, actions in report['implementation_plan'].items():
        if actions:
            print(f"   {phase}:")
            for action in actions[:2]:  # Show top 2 per phase
                print(f"     • {action}")
    
    # Create a sample training plan
    print("\n📚 Creating sample training plan...")
    sample_plan = system.create_training_plan(
        "reddit_bibliophile_agent", 
        ["testing", "quality_assurance", "security_review"],
        duration_weeks=4
    )
    
    success = system.save_training_plan(sample_plan)
    if success:
        print(f"✅ Training plan created for {sample_plan['agent']}")
        print(f"   Skills: {', '.join(sample_plan['target_skills'])}")
        print(f"   Duration: {sample_plan['duration_weeks']} weeks")
        print(f"   Mentors: {len(sample_plan['mentor_assignments'])} assigned")
    
    print("\n✅ 轮岗制度 (Cross-Training System) Ready!")
    return report

if __name__ == "__main__":
    main()