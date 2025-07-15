#!/usr/bin/env python3
"""
👔 Weekly Performance Review System - Linda Zhang (张丽娜)
=======================================================

Implements 严格考核 (strict evaluation) with clear targets and cultural work ethic.
Combines East Asian management philosophy with American innovation.
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

class WeeklyPerformanceSystem:
    """
    Linda's Weekly Performance Review System
    
    Philosophy: 严格要求，关爱成长 (Strict requirements, caring growth)
    - Set clear weekly targets for each agent
    - Track performance against targets
    - Provide constructive feedback
    - Identify improvement opportunities
    - Recognize excellent performance
    """
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        self.hr_data_dir = "agents/hr/reports/weekly_reviews"
        os.makedirs(self.hr_data_dir, exist_ok=True)
        
        self.logger = logging.getLogger("WeeklyPerformance_Linda")
        
        print("👔 Linda's Weekly Performance System initialized")
        print("📊 严格考核 (Strict Evaluation) - Clear targets and accountability")
    
    def get_db(self):
        """Get database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except psycopg2.Error as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def set_weekly_targets(self, agent_name: str, targets: Dict[str, Any]) -> bool:
        """
        Set weekly performance targets for an agent
        
        Linda's approach: Clear, measurable, challenging but achievable
        """
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get current week start
                        week_start = self._get_week_start()
                        
                        # Insert or update weekly targets
                        cur.execute("""
                            INSERT INTO weekly_agent_targets 
                            (agent_name, week_start, targets, created_by, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (agent_name, week_start) 
                            DO UPDATE SET 
                                targets = EXCLUDED.targets,
                                updated_at = NOW()
                            RETURNING target_id
                        """, (
                            agent_name,
                            week_start,
                            json.dumps(targets),
                            "hr_agent_linda",
                            datetime.now()
                        ))
                        
                        target_id = cur.fetchone()[0]
                        conn.commit()
                        
                        self.logger.info(f"🎯 Targets set for {agent_name}: {targets}")
                        return True
        except Exception as e:
            self.logger.error(f"❌ Failed to set targets for {agent_name}: {e}")
        return False
    
    def evaluate_weekly_performance(self, agent_name: str = None) -> Dict[str, Any]:
        """
        Conduct weekly performance evaluation
        
        Linda's approach: Data-driven, fair, constructive
        """
        week_start = self._get_week_start()
        week_end = week_start + timedelta(days=7)
        
        evaluations = {}
        
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        # Get agents to evaluate
                        if agent_name:
                            agents = [agent_name]
                        else:
                            cur.execute("SELECT DISTINCT agent_name FROM agents")
                            agents = [row['agent_name'] for row in cur.fetchall()]
                        
                        for agent in agents:
                            evaluation = self._evaluate_single_agent(cur, agent, week_start, week_end)
                            evaluations[agent] = evaluation
                            
                            # Save evaluation to database
                            self._save_evaluation(cur, agent, week_start, evaluation)
                        
                        conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Weekly evaluation failed: {e}")
        
        return evaluations
    
    def _evaluate_single_agent(self, cursor, agent_name: str, week_start: datetime, week_end: datetime) -> Dict[str, Any]:
        """
        Evaluate individual agent performance against targets
        """
        # Get weekly targets
        cursor.execute("""
            SELECT targets FROM weekly_agent_targets 
            WHERE agent_name = %s AND week_start = %s
        """, (agent_name, week_start))
        
        targets_row = cursor.fetchone()
        targets = targets_row['targets'] if targets_row and targets_row['targets'] else {}
        
        # Get actual performance metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_interactions,
                AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(duration_ms) as avg_duration_ms,
                COUNT(CASE WHEN success THEN 1 END) as successful_actions,
                COUNT(CASE WHEN NOT success THEN 1 END) as failed_actions
            FROM agent_interactions ai
            JOIN agents a ON ai.agent_id = a.agent_id
            WHERE a.agent_name = %s 
            AND ai.timestamp >= %s 
            AND ai.timestamp < %s
        """, (agent_name, week_start, week_end))
        
        performance = cursor.fetchone()
        
        # Calculate performance scores
        evaluation = {
            "agent_name": agent_name,
            "week_start": week_start.isoformat(),
            "targets": targets,
            "actual_performance": {
                "total_interactions": performance['total_interactions'] or 0,
                "success_rate": float(performance['success_rate'] or 0),
                "avg_response_time_ms": float(performance['avg_duration_ms'] or 0),
                "successful_actions": performance['successful_actions'] or 0,
                "failed_actions": performance['failed_actions'] or 0
            },
            "target_achievement": self._calculate_target_achievement(targets, performance),
            "linda_grade": self._assign_linda_grade(targets, performance),
            "feedback": self._generate_linda_feedback(targets, performance),
            "improvement_plan": self._create_improvement_plan(targets, performance)
        }
        
        return evaluation
    
    def _calculate_target_achievement(self, targets: Dict, performance: Dict) -> Dict[str, float]:
        """
        Calculate percentage achievement against each target
        """
        achievement = {}
        
        if 'success_rate_target' in targets:
            actual_rate = float(performance['success_rate'] or 0)
            target_rate = targets['success_rate_target']
            achievement['success_rate'] = min(100.0, (actual_rate / target_rate) * 100) if target_rate > 0 else 0
        
        if 'interaction_count_target' in targets:
            actual_count = performance['total_interactions'] or 0
            target_count = targets['interaction_count_target']
            achievement['interaction_count'] = min(100.0, (actual_count / target_count) * 100) if target_count > 0 else 0
        
        if 'response_time_target_ms' in targets:
            actual_time = float(performance['avg_duration_ms'] or 0)
            target_time = targets['response_time_target_ms']
            # For response time, lower is better
            achievement['response_time'] = min(100.0, (target_time / actual_time) * 100) if actual_time > 0 else 100
        
        return achievement
    
    def _assign_linda_grade(self, targets: Dict, performance: Dict) -> str:
        """
        Assign grade using Linda's strict but fair standards
        """
        achievement = self._calculate_target_achievement(targets, performance)
        
        if not achievement:
            return "需要设定目标 (Need to set targets)"
        
        avg_achievement = sum(achievement.values()) / len(achievement)
        
        if avg_achievement >= 95:
            return "优秀 (Excellent) - A+"
        elif avg_achievement >= 85:
            return "良好 (Good) - A"
        elif avg_achievement >= 75:
            return "满意 (Satisfactory) - B+"
        elif avg_achievement >= 65:
            return "需要改进 (Needs Improvement) - B"
        elif avg_achievement >= 50:
            return "不及格 (Below Standard) - C"
        else:
            return "需要紧急干预 (Emergency Intervention) - F"
    
    def _generate_linda_feedback(self, targets: Dict, performance: Dict) -> List[str]:
        """
        Generate constructive feedback in Linda's style
        """
        feedback = []
        achievement = self._calculate_target_achievement(targets, performance)
        
        for metric, score in achievement.items():
            if score >= 95:
                feedback.append(f"✅ {metric}: 做得很好! (Well done!) Exceeded expectations.")
            elif score >= 85:
                feedback.append(f"✅ {metric}: 不错 (Not bad) - Good performance, keep it up.")
            elif score >= 75:
                feedback.append(f"⚠️ {metric}: 还可以 (Acceptable) - Room for improvement.")
            elif score >= 50:
                feedback.append(f"🚨 {metric}: 需要努力 (Need to work harder) - Below expectations.")
            else:
                feedback.append(f"❌ {metric}: 不可接受 (Unacceptable) - Immediate action required.")
        
        # Overall performance assessment
        total_interactions = performance['total_interactions'] or 0
        if total_interactions == 0:
            feedback.append("🚨 没有活动 (No activity) - Agent must be more active.")
        
        return feedback
    
    def _create_improvement_plan(self, targets: Dict, performance: Dict) -> List[str]:
        """
        Create specific improvement plan
        """
        plan = []
        achievement = self._calculate_target_achievement(targets, performance)
        
        for metric, score in achievement.items():
            if score < 85:  # Needs improvement
                if metric == 'success_rate':
                    plan.append("🎯 Focus on quality: Review failed interactions and identify patterns")
                    plan.append("📚 Training: Practice with similar tasks to improve success rate")
                elif metric == 'interaction_count':
                    plan.append("⚡ Increase activity: Participate more actively in system operations")
                    plan.append("🤝 Collaboration: Work with other agents on shared tasks")
                elif metric == 'response_time':
                    plan.append("🚀 Optimize performance: Review and streamline processes")
                    plan.append("🔧 Technical review: Check for bottlenecks and inefficiencies")
        
        if not plan:
            plan.append("🏆 继续保持 (Keep it up) - Maintain current excellent performance")
        
        return plan
    
    def _save_evaluation(self, cursor, agent_name: str, week_start: datetime, evaluation: Dict):
        """
        Save evaluation to database
        """
        cursor.execute("""
            INSERT INTO weekly_performance_evaluations 
            (agent_name, week_start, evaluation_data, evaluator, evaluation_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (agent_name, week_start) 
            DO UPDATE SET 
                evaluation_data = EXCLUDED.evaluation_data,
                evaluation_date = EXCLUDED.evaluation_date
        """, (
            agent_name,
            week_start,
            json.dumps(evaluation),
            "hr_agent_linda",
            datetime.now()
        ))
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive weekly team report
        """
        evaluations = self.evaluate_weekly_performance()
        week_start = self._get_week_start()
        
        # Calculate team statistics
        grades = [eval_data['linda_grade'] for eval_data in evaluations.values()]
        total_interactions = sum(eval_data['actual_performance']['total_interactions'] for eval_data in evaluations.values())
        avg_success_rate = sum(eval_data['actual_performance']['success_rate'] for eval_data in evaluations.values()) / len(evaluations) if evaluations else 0
        
        # Grade distribution
        grade_counts = {}
        for grade in grades:
            grade_letter = grade.split(' - ')[-1] if ' - ' in grade else grade
            grade_counts[grade_letter] = grade_counts.get(grade_letter, 0) + 1
        
        report = {
            "report_date": datetime.now().isoformat(),
            "week_start": week_start.isoformat(),
            "evaluator": "Linda Zhang (张丽娜) - HR Manager",
            "team_summary": {
                "total_agents_evaluated": len(evaluations),
                "total_team_interactions": total_interactions,
                "average_team_success_rate": avg_success_rate,
                "grade_distribution": grade_counts
            },
            "individual_evaluations": evaluations,
            "linda_team_assessment": self._linda_team_assessment(evaluations),
            "next_week_priorities": self._set_next_week_priorities(evaluations)
        }
        
        # Save report
        report_file = f"{self.hr_data_dir}/weekly_report_{week_start.strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _linda_team_assessment(self, evaluations: Dict[str, Any]) -> str:
        """
        Linda's overall team assessment
        """
        if not evaluations:
            return "没有数据 (No data) - Cannot evaluate team without agent activity"
        
        excellent_count = sum(1 for eval_data in evaluations.values() if 'A' in eval_data['linda_grade'])
        poor_count = sum(1 for eval_data in evaluations.values() if any(grade in eval_data['linda_grade'] for grade in ['C', 'F', '不及格', '紧急干预']))
        total_count = len(evaluations)
        
        if excellent_count / total_count >= 0.8:
            return f"团队表现优秀! (Excellent team performance!) {excellent_count}/{total_count} agents performing at high level. 继续保持! (Keep it up!)"
        elif poor_count / total_count >= 0.3:
            return f"团队需要改进 (Team needs improvement) - {poor_count}/{total_count} agents below standard. 需要加强管理 (Need stronger management)"
        else:
            return f"团队表现不错 (Team performance is good) - {excellent_count}/{total_count} excellent performers. 继续努力 (Continue working hard)"
    
    def _set_next_week_priorities(self, evaluations: Dict[str, Any]) -> List[str]:
        """
        Set priorities for next week based on evaluations
        """
        priorities = []
        
        # Identify agents needing attention
        poor_performers = [agent for agent, eval_data in evaluations.items() 
                         if any(grade in eval_data['linda_grade'] for grade in ['C', 'F', '不及格', '紧急干预'])]
        
        if poor_performers:
            priorities.append(f"🚨 紧急关注 (Urgent attention): {', '.join(poor_performers)}")
            priorities.append("📅 安排一对一会议 (Schedule 1-on-1 meetings) for improvement planning")
        
        # Check for team-wide issues
        avg_success_rate = sum(eval_data['actual_performance']['success_rate'] for eval_data in evaluations.values()) / len(evaluations) if evaluations else 0
        if avg_success_rate < 0.8:
            priorities.append("📚 团队培训 (Team training) - Success rate below 80%")
        
        total_interactions = sum(eval_data['actual_performance']['total_interactions'] for eval_data in evaluations.values())
        if total_interactions < len(evaluations) * 10:  # Less than 10 interactions per agent
            priorities.append("⚡ 提高活跃度 (Increase activity) - Agents need more engagement")
        
        if not priorities:
            priorities.append("🏆 保持优秀表现 (Maintain excellent performance) - Team performing well")
        
        return priorities
    
    def _get_week_start(self) -> datetime:
        """
        Get the start of the current week (Monday)
        """
        today = datetime.now().date()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        return datetime.combine(week_start, datetime.min.time())
    
    def _ensure_tables_exist(self):
        """
        Ensure required tables exist for weekly performance system
        """
        try:
            with self.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create weekly targets table
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS weekly_agent_targets (
                                target_id SERIAL PRIMARY KEY,
                                agent_name VARCHAR(100) NOT NULL,
                                week_start DATE NOT NULL,
                                targets JSONB NOT NULL,
                                created_by VARCHAR(100) DEFAULT 'hr_agent_linda',
                                created_at TIMESTAMP DEFAULT NOW(),
                                updated_at TIMESTAMP DEFAULT NOW(),
                                UNIQUE(agent_name, week_start)
                            )
                        """)
                        
                        # Create weekly evaluations table
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS weekly_performance_evaluations (
                                evaluation_id SERIAL PRIMARY KEY,
                                agent_name VARCHAR(100) NOT NULL,
                                week_start DATE NOT NULL,
                                evaluation_data JSONB NOT NULL,
                                evaluator VARCHAR(100) DEFAULT 'hr_agent_linda',
                                evaluation_date TIMESTAMP DEFAULT NOW(),
                                UNIQUE(agent_name, week_start)
                            )
                        """)
                        
                        conn.commit()
                        self.logger.info("✅ Weekly performance tables ready")
        except Exception as e:
            self.logger.error(f"❌ Failed to create tables: {e}")

def main():
    """Demo the weekly performance system"""
    system = WeeklyPerformanceSystem()
    system._ensure_tables_exist()
    
    print("\n👔 Linda's Weekly Performance System Demo")
    print("="*50)
    
    # Set sample targets
    sample_targets = {
        "success_rate_target": 0.85,  # 85% success rate
        "interaction_count_target": 20,  # 20 interactions per week
        "response_time_target_ms": 2000  # Under 2 seconds
    }
    
    # Set targets for some agents
    agents = ['reddit_bibliophile_agent', 'comprehensive_qa_agent', 'security_qa_agent']
    for agent in agents:
        system.set_weekly_targets(agent, sample_targets)
        print(f"🎯 Targets set for {agent}")
    
    print("\n📊 Generating weekly performance report...")
    report = system.generate_weekly_report()
    
    print(f"\n📋 Weekly Report Summary:")
    print(f"👥 Agents evaluated: {report['team_summary']['total_agents_evaluated']}")
    print(f"📈 Team success rate: {report['team_summary']['average_team_success_rate']:.1%}")
    print(f"🎓 Grade distribution: {report['team_summary']['grade_distribution']}")
    print(f"👔 Linda's assessment: {report['linda_team_assessment']}")
    
    print("\n🎯 Next week priorities:")
    for i, priority in enumerate(report['next_week_priorities'], 1):
        print(f"   {i}. {priority}")
    
    print("\n✅ 严格考核 (Weekly Performance Reviews) System Ready!")
    return report

if __name__ == "__main__":
    main()