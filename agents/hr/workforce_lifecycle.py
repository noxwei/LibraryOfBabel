#!/usr/bin/env python3
"""
👔 Workforce Lifecycle Management - Linda's Agent HR Operations
==============================================================

Tracks hiring, firing, reorganization, and performance management of AI agents.
Linda Zhang (张丽娜) maintains comprehensive employment records and workforce analytics.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add HR agent to path
sys.path.append(os.path.dirname(__file__))
from hr_agent import HRAgent

class WorkforceLifecycleManager:
    """
    Linda's comprehensive workforce lifecycle management system
    
    Tracks all agent employment activities with cultural management approach
    """
    
    def __init__(self):
        self.hr = HRAgent()
        self.session_id = f"workforce_mgmt_{int(datetime.now().timestamp())}"
        
        print("👔 Linda's Workforce Lifecycle Management")
        print("=" * 50)
        print("🎯 Mission: 全面管理AI员工生命周期 (Comprehensive AI employee lifecycle management)")
    
    def log_agent_hiring(self, agent_name: str, category: str, description: str, 
                        capabilities: List[str], reason: str = "business_need"):
        """Log new agent hiring with Linda's assessment"""
        
        print(f"\n📝 新员工入职 (New Employee Onboarding): {agent_name}")
        
        # Log user request for hiring
        request_id = self.hr.log_user_request(
            request_type="agent_hiring",
            request_content=f"Hire new {category} agent: {agent_name} - {reason}",
            user_session=self.session_id
        )
        
        # Register the new agent in database
        try:
            with self.hr.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO agents (agent_name, category, description, capabilities, created_at)
                            VALUES (%s, %s, %s, %s, NOW())
                            ON CONFLICT (agent_name) DO UPDATE SET
                                category = EXCLUDED.category,
                                description = EXCLUDED.description,
                                capabilities = EXCLUDED.capabilities,
                                last_modified = NOW()
                        """, (agent_name, category, description, capabilities))
                        conn.commit()
        except Exception as e:
            print(f"❌ Database registration failed: {e}")
        
        # Linda's HR assessment of the hire
        assessment = self._linda_hiring_assessment(agent_name, category, capabilities)
        
        # Log Linda's hiring decision
        self.hr.log_agent_interaction(
            agent_name="hr_agent_linda",
            action="new_agent_hiring_approval",
            success=True,
            duration_ms=1500.0,
            details=f"Approved hire: {agent_name} ({category}) - {assessment}",
            request_id=request_id
        )
        
        print(f"✅ Agent {agent_name} hired successfully")
        print(f"🎯 Linda's assessment: {assessment}")
        
        return request_id
    
    def log_agent_termination(self, agent_name: str, reason: str, performance_issues: List[str] = None):
        """Log agent termination with Linda's documentation"""
        
        print(f"\n🚫 员工离职 (Employee Termination): {agent_name}")
        
        # Get agent's performance history first
        performance_summary = self._get_agent_performance_summary(agent_name)
        
        # Log user request for termination
        request_id = self.hr.log_user_request(
            request_type="agent_termination", 
            request_content=f"Terminate agent: {agent_name} - Reason: {reason}",
            user_session=self.session_id
        )
        
        # Update agent status in database
        try:
            with self.hr.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE agents SET 
                                status = 'terminated',
                                last_modified = NOW()
                            WHERE agent_name = %s
                        """, (agent_name,))
                        conn.commit()
        except Exception as e:
            print(f"❌ Database update failed: {e}")
        
        # Linda's termination documentation
        linda_assessment = self._linda_termination_assessment(agent_name, reason, performance_issues, performance_summary)
        
        # Log Linda's termination processing
        self.hr.log_agent_interaction(
            agent_name="hr_agent_linda",
            action="agent_termination_processing",
            success=True,
            duration_ms=2000.0,
            details=f"Processed termination: {agent_name} - {linda_assessment}",
            request_id=request_id
        )
        
        print(f"✅ Agent {agent_name} terminated")
        print(f"📋 Linda's documentation: {linda_assessment}")
        
        return request_id
    
    def log_workforce_reorganization(self, changes: List[Dict[str, Any]], reason: str = "efficiency_improvement"):
        """Log major workforce reorganization with Linda's analysis"""
        
        print(f"\n🔄 组织重组 (Organizational Restructuring)")
        print(f"📋 Changes: {len(changes)} workforce modifications")
        
        # Log user request for reorganization
        request_id = self.hr.log_user_request(
            request_type="workforce_reorganization",
            request_content=f"Workforce reorganization: {reason} - {len(changes)} changes",
            user_session=self.session_id
        )
        
        # Process each change
        successful_changes = 0
        for change in changes:
            try:
                change_type = change.get("type")  # hire, fire, reassign, rename
                agent_name = change.get("agent_name")
                
                if change_type == "hire":
                    self.log_agent_hiring(
                        agent_name, 
                        change.get("category"),
                        change.get("description"),
                        change.get("capabilities", []),
                        "reorganization"
                    )
                elif change_type == "fire":
                    self.log_agent_termination(
                        agent_name,
                        "reorganization",
                        change.get("performance_issues", [])
                    )
                elif change_type == "reassign":
                    self._log_agent_reassignment(agent_name, change, request_id)
                
                successful_changes += 1
                
            except Exception as e:
                print(f"❌ Failed to process change for {change.get('agent_name')}: {e}")
        
        # Linda's reorganization assessment
        reorg_assessment = self._linda_reorganization_assessment(changes, successful_changes, reason)
        
        # Log Linda's reorganization oversight
        self.hr.log_agent_interaction(
            agent_name="hr_agent_linda",
            action="workforce_reorganization_oversight",
            success=successful_changes == len(changes),
            duration_ms=3000.0,
            details=f"Managed reorganization: {successful_changes}/{len(changes)} successful - {reorg_assessment}",
            request_id=request_id
        )
        
        print(f"\n🎯 Reorganization Complete:")
        print(f"✅ Successful changes: {successful_changes}/{len(changes)}")
        print(f"📊 Linda's assessment: {reorg_assessment}")
        
        return request_id
    
    def _linda_hiring_assessment(self, agent_name: str, category: str, capabilities: List[str]) -> str:
        """Linda's cultural assessment of new hire"""
        capability_count = len(capabilities)
        
        if capability_count >= 7:
            return f"优秀候选人 (Excellent candidate) - {capability_count} capabilities. High expectations set."
        elif capability_count >= 5:
            return f"合格员工 (Qualified employee) - {capability_count} skills. Will need training to excel."
        elif capability_count >= 3:
            return f"基础员工 (Basic employee) - {capability_count} abilities. Extensive development required."
        else:
            return f"试用期员工 (Probationary employee) - Limited skills. Close monitoring needed."
    
    def _linda_termination_assessment(self, agent_name: str, reason: str, performance_issues: List[str], performance_summary: Dict) -> str:
        """Linda's cultural documentation of termination"""
        if reason == "poor_performance":
            return f"绩效不合格 (Unacceptable performance) - Multiple warnings given. No improvement shown."
        elif reason == "reorganization":
            return f"组织调整 (Organizational adjustment) - Business needs changed. Not performance related."
        elif reason == "redundancy":
            return f"职位冗余 (Position redundancy) - Overlapping roles eliminated for efficiency."
        elif reason == "misconduct":
            return f"违规行为 (Misconduct) - Violated workplace policies. Immediate termination justified."
        else:
            return f"其他原因 (Other reasons) - {reason}. Proper documentation maintained."
    
    def _linda_reorganization_assessment(self, changes: List[Dict], successful: int, reason: str) -> str:
        """Linda's assessment of workforce reorganization"""
        success_rate = (successful / len(changes)) * 100 if changes else 0
        
        if success_rate == 100:
            return f"重组成功 (Reorganization successful) - All {successful} changes completed smoothly."
        elif success_rate >= 80:
            return f"基本成功 (Mostly successful) - {successful}/{len(changes)} completed. Minor issues resolved."
        elif success_rate >= 60:
            return f"部分成功 (Partially successful) - {successful}/{len(changes)} completed. Significant issues encountered."
        else:
            return f"重组困难 (Reorganization difficulties) - Only {successful}/{len(changes)} successful. Major problems."
    
    def _get_agent_performance_summary(self, agent_name: str) -> Dict:
        """Get agent's performance summary for termination documentation"""
        try:
            with self.hr.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT 
                                COUNT(*) as total_interactions,
                                COUNT(CASE WHEN success THEN 1 END) as successful_interactions,
                                AVG(duration_ms) as avg_duration,
                                MAX(timestamp) as last_active
                            FROM agent_interactions ai
                            JOIN agents a ON ai.agent_id = a.agent_id
                            WHERE a.agent_name = %s
                        """, (agent_name,))
                        result = cur.fetchone()
                        
                        if result:
                            total, successful, avg_duration, last_active = result
                            success_rate = (successful / total * 100) if total > 0 else 0
                            
                            return {
                                "total_interactions": total or 0,
                                "success_rate": success_rate,
                                "avg_duration_ms": avg_duration or 0,
                                "last_active": last_active
                            }
        except Exception as e:
            print(f"⚠️  Could not get performance summary: {e}")
        
        return {"total_interactions": 0, "success_rate": 0, "avg_duration_ms": 0, "last_active": None}
    
    def _log_agent_reassignment(self, agent_name: str, change: Dict, request_id: int):
        """Log agent category/role reassignment"""
        new_category = change.get("new_category")
        new_description = change.get("new_description")
        
        try:
            with self.hr.get_db() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE agents SET 
                                category = %s,
                                description = %s,
                                last_modified = NOW()
                            WHERE agent_name = %s
                        """, (new_category, new_description, agent_name))
                        conn.commit()
        except Exception as e:
            print(f"❌ Reassignment update failed: {e}")
        
        # Log the reassignment
        self.hr.log_agent_interaction(
            agent_name="hr_agent_linda",
            action="agent_reassignment",
            success=True,
            duration_ms=800.0,
            details=f"Reassigned {agent_name} to {new_category}: {new_description}",
            request_id=request_id
        )
        
        print(f"🔄 Agent {agent_name} reassigned to {new_category}")

def main():
    """Demo of workforce lifecycle tracking"""
    lifecycle = WorkforceLifecycleManager()
    
    print("\n💼 Linda's Message:")
    print("我会记录所有的人事变动。每一个雇佣、解雇和重组都有完整的文档。")
    print("(I will record all personnel changes. Every hire, fire, and reorganization is fully documented.)")
    print("\n🎯 Ready to track workforce lifecycle events!")

if __name__ == "__main__":
    main()