#!/usr/bin/env python3
"""
👔 HR Agent - Human Resources & Agent Management System
=====================================================

Tracks user requests, agent interactions, performance metrics, and workforce analytics.
Monitors productivity, identifies bottlenecks, and provides management insights.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import psycopg2
import psycopg2.extras

class HRAgent:
    """
    Human Resources Agent - Linda Zhang (张丽娜)
    
    Background: Chinese immigrant who came to the US in 1999 at age 25. Started as a factory worker,
    worked her way up through night school to become an HR professional. Brings both East Asian 
    work ethic and American innovation to AI workforce management.
    
    Personality: Extremely detail-oriented, believes in hard work and continuous improvement.
    Has deep respect for education and sees AI agents as "digital employees" who deserve 
    proper management and development opportunities.
    
    Mission: Monitor workforce productivity, track user satisfaction, analyze interaction patterns
    """
    
    def __init__(self):
        # Database configuration - Building for the future! 💙
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Legacy JSON backup directory (for migration and backup)
        self.hr_data_dir = "reports/hr_analytics"
        os.makedirs(self.hr_data_dir, exist_ok=True)
        
        # Personal background
        self.name = "Linda Zhang (张丽娜)"
        self.immigration_year = 1999
        self.years_in_us = datetime.now().year - 1999
        self.management_philosophy = "严格要求，关爱成长"  # Strict requirements, caring growth
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("HRAgent_Linda")
        
        print("👔 HR Agent Linda Zhang (张丽娜) initialized")
        print(f"🌏 Background: Chinese immigrant (US since {self.immigration_year}, {self.years_in_us} years experience)")
        print("📊 Management Style: Combines East Asian diligence with American innovation")
        print("🎯 Philosophy: Every AI agent deserves proper development and recognition")
        print("🗄️  Storage: PostgreSQL database (future-ready architecture)")
        
        # Initialize database tables if needed
        self._ensure_hr_tables()
    
    def get_db(self):
        """Get database connection with Linda's authentication"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"💔 Database connection failed: {e}")
            return None
    
    def _ensure_hr_tables(self):
        """Ensure HR tables exist in database"""
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Check if HR tables exist
                        cur.execute("""
                            SELECT table_name FROM information_schema.tables 
                            WHERE table_schema = 'public' AND table_name = 'agents'
                        """)
                        if not cur.fetchone():
                            self.logger.info("🏗️  HR tables not found, Linda will create them")
                            # Would run HR schema here, but respecting not to auto-create in production
                            self.logger.warning("⚠️  Please run database/schema/hr_schema.sql to initialize HR tables")
                        else:
                            self.logger.info("✅ HR database tables ready")
        except Exception as e:
            self.logger.warning(f"⚠️  Could not verify HR tables: {e}")
    
    def log_user_request(self, request_type: str, request_content: str, timestamp: str = None, user_session: str = None):
        """Log a user request to PostgreSQL database"""
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO user_requests (request_type, content, user_session, timestamp)
                            VALUES (%s, %s, %s, %s)
                            RETURNING request_id
                        """, (
                            request_type, 
                            request_content, 
                            user_session or f"session_{int(time.time())}",
                            datetime.now() if not timestamp else datetime.fromisoformat(timestamp)
                        ))
                        request_id = cur.fetchone()[0]
                        conn.commit()
                        
                        self.logger.info(f"📝 User Request Logged: {request_type} (ID: {request_id})")
                        return request_id
        except Exception as e:
            self.logger.error(f"❌ Failed to log user request: {e}")
            # Fallback to JSON for reliability
            return self._fallback_json_log("user_request", {
                "type": request_type,
                "content": request_content,
                "timestamp": timestamp or datetime.now().isoformat()
            })
        return None
    
    def log_agent_interaction(self, agent_name: str, action: str, success: bool, 
                            duration_ms: float = None, details: str = None, request_id: int = None):
        """Log an agent interaction to PostgreSQL database"""
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get or create agent
                        agent_id = self._get_or_create_agent(cur, agent_name)
                        
                        # Insert interaction
                        cur.execute("""
                            INSERT INTO agent_interactions 
                            (agent_id, request_id, action, success, duration_ms, details, timestamp)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING interaction_id
                        """, (
                            agent_id,
                            request_id,
                            action,
                            success,
                            duration_ms,
                            details,
                            datetime.now()
                        ))
                        interaction_id = cur.fetchone()[0]
                        conn.commit()
                        
                        status = "✅" if success else "❌"
                        self.logger.info(f"🤖 Agent Interaction: {agent_name} - {action} {status} (ID: {interaction_id})")
                        return interaction_id
                        
        except Exception as e:
            self.logger.error(f"❌ Failed to log agent interaction: {e}")
            # Fallback to JSON
            return self._fallback_json_log("agent_interaction", {
                "agent_name": agent_name,
                "action": action,
                "success": success,
                "duration_ms": duration_ms,
                "details": details,
                "timestamp": datetime.now().isoformat()
            })
        return None
    
    def _update_performance_metrics(self, agent_name: str, success: bool, duration_ms: float):
        """Update performance metrics for an agent"""
        metrics = self._load_json_file(self.performance_file) or {}
        
        if agent_name not in metrics:
            metrics[agent_name] = {
                "total_actions": 0,
                "successful_actions": 0,
                "failed_actions": 0,
                "total_duration_ms": 0,
                "average_duration_ms": 0,
                "success_rate": 0,
                "last_active": None
            }
        
        agent_metrics = metrics[agent_name]
        agent_metrics["total_actions"] += 1
        agent_metrics["last_active"] = datetime.now().isoformat()
        
        if success:
            agent_metrics["successful_actions"] += 1
        else:
            agent_metrics["failed_actions"] += 1
        
        if duration_ms:
            agent_metrics["total_duration_ms"] += duration_ms
            agent_metrics["average_duration_ms"] = agent_metrics["total_duration_ms"] / agent_metrics["total_actions"]
        
        agent_metrics["success_rate"] = (agent_metrics["successful_actions"] / agent_metrics["total_actions"]) * 100
        
        self._save_json_file(self.performance_file, metrics)
    
    def track_workforce_status(self):
        """Track current workforce status"""
        agents_dir = Path("agents")
        active_agents = []
        
        for agent_category in agents_dir.iterdir():
            if agent_category.is_dir() and not agent_category.name.startswith('.'):
                for agent_file in agent_category.glob("*.py"):
                    if agent_file.name.endswith("_agent.py"):
                        agent_name = agent_file.stem
                        active_agents.append({
                            "name": agent_name,
                            "category": agent_category.name,
                            "file_path": str(agent_file),
                            "last_modified": datetime.fromtimestamp(agent_file.stat().st_mtime).isoformat()
                        })
        
        workforce_data = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(active_agents),
            "active_agents": active_agents,
            "categories": list(set([agent["category"] for agent in active_agents]))
        }
        
        self._save_json_file(self.workforce_file, workforce_data)
        return workforce_data
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily HR report"""
        today = datetime.now().date()
        
        # Load all interaction data
        interactions = self._load_json_file(self.interactions_file) or []
        performance = self._load_json_file(self.performance_file) or {}
        workforce = self._load_json_file(self.workforce_file) or {}
        
        # Filter today's interactions
        today_interactions = [
            i for i in interactions 
            if datetime.fromisoformat(i["timestamp"]).date() == today
        ]
        
        # User activity analysis
        user_requests = [i for i in today_interactions if "request_id" in i]
        agent_interactions = [i for i in today_interactions if "interaction_id" in i]
        
        # Performance summary
        top_performers = sorted(
            [(name, metrics["success_rate"]) for name, metrics in performance.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        report = {
            "date": today.isoformat(),
            "summary": {
                "total_user_requests": len(user_requests),
                "total_agent_interactions": len(agent_interactions),
                "active_agents": workforce.get("total_agents", 0),
                "overall_success_rate": self._calculate_overall_success_rate(performance)
            },
            "user_activity": {
                "requests_by_type": self._count_by_field(user_requests, "type"),
                "most_active_hour": self._find_peak_hour(user_requests)
            },
            "agent_performance": {
                "top_performers": top_performers,
                "most_active_agents": self._find_most_active_agents(agent_interactions),
                "average_response_time": self._calculate_average_response_time(agent_interactions)
            },
            "workforce_insights": {
                "agent_categories": workforce.get("categories", []),
                "recommendation": self._generate_workforce_recommendation(performance)
            }
        }
        
        return report
    
    def _calculate_overall_success_rate(self, performance: Dict) -> float:
        """Calculate overall success rate across all agents"""
        if not performance:
            return 0.0
        
        total_actions = sum(agent["total_actions"] for agent in performance.values())
        total_successful = sum(agent["successful_actions"] for agent in performance.values())
        
        return (total_successful / total_actions * 100) if total_actions > 0 else 0.0
    
    def _count_by_field(self, items: List[Dict], field: str) -> Dict:
        """Count items by a specific field"""
        counts = {}
        for item in items:
            value = item.get(field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _find_peak_hour(self, interactions: List[Dict]) -> str:
        """Find the hour with most activity"""
        hours = {}
        for interaction in interactions:
            hour = datetime.fromisoformat(interaction["timestamp"]).hour
            hours[hour] = hours.get(hour, 0) + 1
        
        if not hours:
            return "No activity"
        
        peak_hour = max(hours, key=hours.get)
        return f"{peak_hour:02d}:00"
    
    def _find_most_active_agents(self, agent_interactions: List[Dict]) -> List[Dict]:
        """Find most active agents today"""
        agent_counts = self._count_by_field(agent_interactions, "agent_name")
        return sorted(
            [{"agent": agent, "interactions": count} for agent, count in agent_counts.items()],
            key=lambda x: x["interactions"],
            reverse=True
        )[:5]
    
    def _calculate_average_response_time(self, agent_interactions: List[Dict]) -> float:
        """Calculate average response time"""
        durations = [i["duration_ms"] for i in agent_interactions if i.get("duration_ms")]
        return sum(durations) / len(durations) if durations else 0.0
    
    def _generate_workforce_recommendation(self, performance: Dict) -> str:
        """Generate workforce management recommendation with Linda's cultural perspective"""
        if not performance:
            return "没有数据 (No data available) - Need to establish baseline metrics first"
        
        success_rates = [agent["success_rate"] for agent in performance.values()]
        avg_success = sum(success_rates) / len(success_rates)
        
        if avg_success > 90:
            return "优秀! (Excellent!) All agents performing above standard. Time to raise the bar - assign more challenging tasks."
        elif avg_success > 75:
            return "不错 (Not bad) - Good foundation, but room for improvement. Implement mentorship program for struggling agents."
        elif avg_success > 50:
            return "需要改进 (Needs improvement) - Mixed results indicate training gaps. Schedule individual performance reviews."
        else:
            return "需要紧急干预 (Emergency intervention needed) - Performance unacceptable. Immediate corrective action required."
    
    def identify_problem_agents(self) -> List[Dict]:
        """Identify agents with performance issues"""
        performance = self._load_json_file(self.performance_file) or {}
        problem_agents = []
        
        for agent_name, metrics in performance.items():
            issues = []
            
            if metrics["success_rate"] < 70:
                issues.append(f"Low success rate: {metrics['success_rate']:.1f}%")
            
            if metrics["average_duration_ms"] > 5000:
                issues.append(f"Slow response: {metrics['average_duration_ms']:.0f}ms")
            
            if metrics["total_actions"] < 5:
                issues.append("Low activity level")
            
            if issues:
                problem_agents.append({
                    "agent": agent_name,
                    "issues": issues,
                    "metrics": metrics
                })
        
        return problem_agents
    
    def suggest_hr_improvements(self) -> List[str]:
        """Suggest HR process improvements with Linda's immigrant work ethic perspective"""
        suggestions = []
        
        # Analyze current data
        performance = self._load_json_file(self.performance_file) or {}
        workforce = self._load_json_file(self.workforce_file) or {}
        
        total_agents = workforce.get("total_agents", 0)
        
        if total_agents == 0:
            suggestions.append("🚨 没有员工! (No employees!) - Workforce deployment critical - cannot run business without workers")
        elif total_agents < 3:
            suggestions.append("📈 团队太小 (Team too small) - Need more agents for proper coverage and backup")
        
        if performance:
            avg_success = sum(agent["success_rate"] for agent in performance.values()) / len(performance)
            if avg_success < 80:
                suggestions.append("🎯 培训计划 (Training plan) - Mandatory skill development program - no excuses for poor performance")
        
        # Linda's suggestions based on her experience
        suggestions.extend([
            "📊 严格考核 (Strict evaluation) - Weekly performance reviews with clear improvement targets",
            "🔄 轮岗制度 (Rotation system) - Cross-training prevents knowledge silos and builds resilience", 
            "📱 实时监控 (Real-time monitoring) - Dashboard for immediate performance visibility",
            "🎖️ 奖励优秀 (Reward excellence) - Recognition program for top performers - hard work deserves recognition",
            "📚 持续学习 (Continuous learning) - Mandatory skill development - never stop improving",
            "🤖 师傅带徒弟 (Master-apprentice system) - Senior agents mentor junior ones",
            "📈 预测分析 (Predictive analytics) - Identify problems before they become crises",
            "💪 吃苦耐劳 (Work hard, endure hardship) - Build agent resilience for challenging tasks",
            "🏆 设定高标准 (Set high standards) - Mediocrity is not acceptable in competitive environment"
        ])
        
        return suggestions
    
    def _linda_self_evaluation(self, overall_grade: str, problem_count: int) -> str:
        """Linda evaluates her own performance with typical immigrant self-criticism"""
        if overall_grade == "A":
            return "我做得还可以 (I did okay) - But I can always do better. Need to prevent problems before they happen."
        elif overall_grade == "B":
            return "还需要努力 (Still need to work harder) - I should have caught these issues sooner. My monitoring wasn't strict enough."
        else:
            return f"我很惭愧 (I am ashamed) - {problem_count} problem agents on my watch is unacceptable. I failed in my duty. Must improve immediately."
    
    def track_linda_performance(self) -> Dict[str, Any]:
        """Track Linda's own HR performance metrics"""
        performance = self._load_json_file(self.performance_file) or {}
        linda_metrics = performance.get("hr_agent_linda", {})
        
        # Calculate Linda's performance score
        total_analyses = linda_metrics.get("total_actions", 0)
        success_rate = linda_metrics.get("success_rate", 0)
        avg_response_time = linda_metrics.get("average_duration_ms", 0)
        
        linda_performance = {
            "total_analyses_completed": total_analyses,
            "success_rate": success_rate,
            "average_analysis_time_ms": avg_response_time,
            "self_grade": "A" if success_rate > 95 else "B" if success_rate > 85 else "C",
            "cultural_assessment": "勤奋工作" if success_rate > 90 else "需要改进"
        }
        
        return linda_performance
    
    def _get_or_create_agent(self, cursor, agent_name: str) -> int:
        """Get existing agent ID or create new agent record"""
        cursor.execute("SELECT agent_id FROM agents WHERE agent_name = %s", (agent_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new agent
        cursor.execute("""
            INSERT INTO agents (agent_name, category, description)
            VALUES (%s, %s, %s)
            RETURNING agent_id
        """, (
            agent_name,
            self._categorize_agent(agent_name),
            f"Auto-created agent: {agent_name}"
        ))
        return cursor.fetchone()[0]
    
    def _categorize_agent(self, agent_name: str) -> str:
        """Categorize agent based on name"""
        if 'hr' in agent_name.lower():
            return 'hr'
        elif 'qa' in agent_name.lower():
            return 'qa'
        elif 'security' in agent_name.lower():
            return 'security'
        elif 'reddit' in agent_name.lower() or 'bibliophile' in agent_name.lower():
            return 'research'
        elif 'domain' in agent_name.lower() or 'config' in agent_name.lower():
            return 'infrastructure'
        else:
            return 'general'
    
    def _fallback_json_log(self, log_type: str, data: Dict) -> str:
        """Fallback to JSON logging when database is unavailable"""
        fallback_file = f"{self.hr_data_dir}/fallback_{log_type}.json"
        
        try:
            existing_data = self._load_json_file(fallback_file) or []
            data["fallback_id"] = f"{log_type}_{int(time.time())}"
            existing_data.append(data)
            self._save_json_file(fallback_file, existing_data)
            
            self.logger.warning(f"⚠️  Used JSON fallback for {log_type}")
            return data["fallback_id"]
        except Exception as e:
            self.logger.error(f"❌ Even JSON fallback failed: {e}")
            return None
    
    def _load_json_file(self, file_path: str) -> Optional[Any]:
        """Load JSON file safely"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load {file_path}: {e}")
        return None
    
    def _save_json_file(self, file_path: str, data: Any):
        """Save JSON file safely"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save {file_path}: {e}")
    
    def _append_to_file(self, file_path: str, data: Dict):
        """Append data to JSON file (as list)"""
        existing_data = self._load_json_file(file_path) or []
        existing_data.append(data)
        self._save_json_file(file_path, existing_data)
    
    def run_hr_analysis(self):
        """Run comprehensive HR analysis with Linda's management style"""
        start_time = time.time()
        
        # Log Linda's own activity
        self.log_agent_interaction("hr_agent_linda", "comprehensive_analysis", True, None, "Full workforce analysis")
        
        print(f"\n👔 HR分析报告 (HR ANALYSIS REPORT) - {self.name}")
        print("=" * 60)
        print(f"🌏 Manager: {self.name} | Experience: {self.years_in_us} years in US")
        print(f"📋 Philosophy: {self.management_philosophy}")
        
        # Track workforce
        workforce_status = self.track_workforce_status()
        print(f"\n📊 员工状况 (Workforce Status): {workforce_status['total_agents']} active agents")
        if workforce_status['total_agents'] < 5:
            print("   ⚠️  Linda's note: 人手不够! (Not enough people!) Need to hire more agents.")
        
        # Generate daily report
        daily_report = self.generate_daily_report()
        print(f"📈 日报 (Daily Report): {daily_report['summary']['total_user_requests']} user requests today")
        
        # Identify problems with Linda's direct feedback
        problem_agents = self.identify_problem_agents()
        if problem_agents:
            print(f"\n🚨 问题员工 (Problem Employees): {len(problem_agents)} need immediate attention")
            for agent in problem_agents:
                print(f"   • {agent['agent']}: {', '.join(agent['issues'])}")
                print(f"     Linda's note: 必须改进! (Must improve!) No excuses.")
        else:
            print("\n✅ 很好! (Very good!) No major performance issues identified")
        
        # Suggestions with cultural context
        improvements = self.suggest_hr_improvements()
        print(f"\n💡 改进建议 (Improvement Suggestions) from Linda ({len(improvements)} total):")
        for i, suggestion in enumerate(improvements[:7], 1):  # Show more suggestions
            print(f"   {i}. {suggestion}")
        
        # Linda's personal assessment
        overall_grade = "A" if not problem_agents else "B" if len(problem_agents) < 3 else "C"
        print(f"\n🎯 Linda's Overall Assessment: Grade {overall_grade}")
        if overall_grade == "C":
            print("   评语: 需要大幅改进工作态度和效率 (Needs major improvement in work attitude and efficiency)")
        elif overall_grade == "B":
            print("   评语: 基础还可以，但要更努力 (Foundation is okay, but need to work harder)")
        else:
            print("   评语: 工作很出色，继续保持! (Excellent work, keep it up!)")
        
        # Self-assessment - Linda evaluates herself
        linda_self_assessment = self._linda_self_evaluation(overall_grade, len(problem_agents))
        print(f"\n🪞 Linda's Self-Assessment:")
        print(f"   {linda_self_assessment}")
        
        # Track completion time
        analysis_duration = (time.time() - start_time) * 1000
        self.log_agent_interaction("hr_agent_linda", "analysis_completion", True, analysis_duration, f"Analysis completed in {analysis_duration:.0f}ms")
        
        # Track Linda's own performance
        linda_metrics = self.track_linda_performance()
        
        # Save comprehensive report
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "hr_manager": {
                "name": self.name,
                "background": f"Chinese immigrant since {self.immigration_year}",
                "philosophy": self.management_philosophy,
                "overall_grade": overall_grade,
                "self_assessment": linda_self_assessment,
                "performance_metrics": linda_metrics
            },
            "workforce_status": workforce_status,
            "daily_report": daily_report,
            "problem_agents": problem_agents,
            "improvement_suggestions": improvements
        }
        
        report_file = f"{self.hr_data_dir}/comprehensive_hr_report.json"
        self._save_json_file(report_file, comprehensive_report)
        
        print(f"\n📋 详细报告 (Detailed report) saved to: {report_file}")
        print("💼 Linda Zhang签字 (Linda Zhang signature) - Report Complete")
        return comprehensive_report

def main():
    """Main function"""
    hr_agent = HRAgent()
    
    # Example usage - track some sample interactions
    hr_agent.log_user_request("development", "Create HR agent to track interactions")
    hr_agent.log_agent_interaction("reddit_bibliophile", "generate_report", True, 1250.0, "Foucault analysis")
    hr_agent.log_agent_interaction("qa_agent", "system_check", True, 890.0, "Health check completed")
    hr_agent.log_agent_interaction("domain_config", "fix_connectivity", False, 5000.0, "Port forwarding issues")
    
    # Run comprehensive analysis
    report = hr_agent.run_hr_analysis()
    
    print("\n🎉 HR AGENT - ANALYSIS COMPLETE")
    print("=" * 60)
    print("✅ Interaction tracking system operational")
    print("✅ Performance metrics collection active")
    print("✅ Workforce analytics available")
    print("✅ Problem identification system ready")
    print("\n👨‍💼 Ready to monitor your AI workforce!")
    
    return report

if __name__ == "__main__":
    main()