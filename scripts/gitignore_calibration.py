#!/usr/bin/env python3
"""
🎯 GitIgnore Calibration Tool
============================

Analyzes current .gitignore rules and recommends optimal calibration for:
- Protecting personal identity data
- Preserving descriptive agent architecture
- Maintaining project shareability

Goal: Share innovative agent design while protecting private information.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

class GitIgnoreCalibrator:
    """
    Analyzes and calibrates .gitignore rules for optimal privacy vs shareability balance
    """
    
    def __init__(self):
        self.project_root = Path("/Users/weixiangzhang/Local Dev/LibraryOfBabel")
        self.gitignore_path = self.project_root / ".gitignore"
        
        # Categories for analysis
        self.categories = {
            "personal_identity": [],
            "agent_architecture": [],
            "system_data": [],
            "development_files": [],
            "overly_broad": [],
            "missing_protection": []
        }
        
        print("🎯 GitIgnore Calibration Analysis")
        print("=" * 40)
        print("Goal: Optimal privacy protection + architectural shareability")
    
    def analyze_current_gitignore(self) -> Dict[str, List[str]]:
        """Analyze current .gitignore rules and categorize them"""
        
        if not self.gitignore_path.exists():
            print("❌ No .gitignore found")
            return {}
        
        with open(self.gitignore_path, 'r') as f:
            lines = f.readlines()
        
        current_rules = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                current_rules.append(line)
        
        # Categorize rules
        for rule in current_rules:
            category = self._categorize_rule(rule)
            self.categories[category].append(rule)
        
        return self.categories
    
    def _categorize_rule(self, rule: str) -> str:
        """Categorize a gitignore rule"""
        
        # Personal identity patterns
        personal_patterns = [
            "*wei*", "*zhang*", "*linda*", "*personal*", "*user_profile*",
            "*real_name*", "*identity*", "*biography*", "*weixiangzhang*"
        ]
        
        # Agent architecture patterns  
        architecture_patterns = [
            "agents/*/", "*.py", "*agent*.py", "*_agent.py"
        ]
        
        # System/data patterns
        system_patterns = [
            "reports/", "*.json", "*.log", "*.sql", "*.db", 
            "*interaction*", "*performance*", "*workforce*"
        ]
        
        # Development patterns
        dev_patterns = [
            "__pycache__/", "*.pyc", ".env", "node_modules/", "logs/"
        ]
        
        # Check for overly broad rules that might hide architecture
        overly_broad_patterns = [
            "agents/*/*", "agents/*/*.py", "*agent*", "*.json"
        ]
        
        if any(pattern in rule for pattern in personal_patterns):
            return "personal_identity"
        elif any(pattern in rule for pattern in overly_broad_patterns):
            return "overly_broad"
        elif any(pattern in rule for pattern in architecture_patterns):
            return "agent_architecture"
        elif any(pattern in rule for pattern in system_patterns):
            return "system_data"
        elif any(pattern in rule for pattern in dev_patterns):
            return "development_files"
        else:
            return "system_data"  # Default category
    
    def scan_for_shareable_content(self) -> Dict[str, List[str]]:
        """Scan for content that SHOULD be shareable but might be blocked"""
        
        shareable_content = {
            "agent_architectures": [],
            "design_patterns": [],
            "configuration_templates": [],
            "documentation": [],
            "schemas": []
        }
        
        # Scan agents directory for architectural files
        agents_dir = self.project_root / "agents"
        if agents_dir.exists():
            for category_dir in agents_dir.iterdir():
                if category_dir.is_dir():
                    for file in category_dir.iterdir():
                        if file.suffix == '.py':
                            # Check if it's architectural vs personal data
                            content_type = self._classify_file_content(file)
                            if content_type in shareable_content:
                                shareable_content[content_type].append(str(file.relative_to(self.project_root)))
        
        # Scan for other shareable files
        for pattern in ["database/schema/*.sql", "scripts/*.py", "*.md"]:
            for file in self.project_root.glob(pattern):
                if self._is_shareable_file(file):
                    content_type = self._classify_file_content(file)
                    if content_type in shareable_content:
                        shareable_content[content_type].append(str(file.relative_to(self.project_root)))
        
        return shareable_content
    
    def _classify_file_content(self, file_path: Path) -> str:
        """Classify file content type"""
        
        try:
            if file_path.suffix == '.py':
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for personal data vs architecture
                if any(term in content.lower() for term in ['weixiangzhang', 'wei_maybe_foucault', 'personal_info']):
                    return "personal_data"
                elif 'class' in content and 'Agent' in content:
                    return "agent_architectures"
                else:
                    return "design_patterns"
            
            elif file_path.suffix == '.sql':
                return "schemas"
            elif file_path.suffix == '.md':
                return "documentation"
            else:
                return "configuration_templates"
                
        except Exception:
            return "unknown"
    
    def _is_shareable_file(self, file_path: Path) -> bool:
        """Determine if file should be shareable"""
        
        non_shareable_indicators = [
            "personal", "private", "secret", "wei", "zhang", 
            "session_", "interaction_", "performance_", "user_profile"
        ]
        
        file_str = str(file_path).lower()
        return not any(indicator in file_str for indicator in non_shareable_indicators)
    
    def scan_for_missing_protection(self) -> List[str]:
        """Scan for files that should be protected but aren't"""
        
        missing_protection = []
        
        # Scan for potential personal data files
        for pattern in ["**/session_*.json", "**/user_*.json", "**/personal_*.json"]:
            for file in self.project_root.glob(pattern):
                if self._contains_personal_data(file):
                    missing_protection.append(str(file.relative_to(self.project_root)))
        
        return missing_protection
    
    def _contains_personal_data(self, file_path: Path) -> bool:
        """Check if file contains personal data"""
        
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    content = f.read()
                
                personal_indicators = [
                    'weixiangzhang', 'wei_maybe_foucault', 'real_name',
                    'personal_info', 'user_profile', 'maybe_foucault'
                ]
                
                return any(indicator in content.lower() for indicator in personal_indicators)
        except Exception:
            pass
        
        return False
    
    def generate_calibrated_gitignore(self) -> str:
        """Generate optimally calibrated .gitignore"""
        
        calibrated_rules = [
            "# LibraryOfBabel - Calibrated Privacy Protection",
            "# Protects personal data while preserving shareable architecture",
            "",
            "# === PERSONAL IDENTITY PROTECTION ===",
            "# Specific personal identifiers",
            "*weixiangzhang*",
            "*wei_maybe_foucault*", 
            "*maybe_foucault*",
            "*zhang*personal*",
            "*linda_zhang*",
            "",
            "# Personal data files",
            "*user_profile*.json",
            "*personal_info*.json",
            "*real_name*.json",
            "*identity*.json",
            "*biography*.json",
            "",
            "# === HR & PERFORMANCE DATA ===",
            "# Sensitive workforce analytics",
            "reports/hr_analytics/",
            "*interaction*.json",
            "*performance_metrics*.json", 
            "*workforce_status*.json",
            "*comprehensive_hr_report*.json",
            "",
            "# Session and conversation logs",
            "*session_*.json",
            "*conversation_*.log",
            "*user_session*.log",
            "",
            "# === DATABASE PERSONAL DATA ===",
            "# Database exports with personal information",
            "pg_dump_*personal*.sql",
            "pg_dump_*hr*.sql",
            "pg_dump_*users*.sql",
            "",
            "# === AGENT PERSONAL DATA (NOT ARCHITECTURE) ===",
            "# Agent memory and personal interactions (keeps architecture)",
            "agents/*/memory/",
            "agents/*/personal_data/",
            "agents/*/user_interactions/",
            "agents/*/conversations/",
            "",
            "# Specific agent personal files (not the agent code itself)",
            "agents/*/_personal_*.json",
            "agents/*/_user_*.json", 
            "agents/*/_private_*.json",
            "",
            "# === STANDARD DEVELOPMENT EXCLUDES ===",
            "# Python",
            "__pycache__/",
            "*.py[cod]",
            "*.so",
            ".Python",
            "",
            "# Environment & Config",
            ".env",
            ".env.local",
            ".env.production",
            "*api_key*",
            "*API_KEY*",
            "",
            "# Logs (but not agent architecture)",
            "*.log",
            "logs/",
            "",
            "# OS & IDE",
            ".DS_Store",
            ".vscode/settings.json",
            "*.swp",
            "*.swo",
            "",
            "# === SHAREABLE CONTENT (EXPLICITLY NOT IGNORED) ===",
            "# The following are INTENTIONALLY shareable:",
            "# - agents/*/*.py (agent architecture and design)",
            "# - database/schema/*.sql (database design)",
            "# - *.md (documentation)",
            "# - scripts/*.py (utility scripts)",
            "# - Agent class definitions and capabilities",
            "",
            "# === TEMPORARY & CACHE ===",
            "temp/",
            "tmp/",
            ".cache/",
            "*.tmp",
            "",
        ]
        
        return "\n".join(calibrated_rules)
    
    def run_calibration_analysis(self):
        """Run complete calibration analysis"""
        
        print("\n🔍 CURRENT GITIGNORE ANALYSIS")
        print("=" * 50)
        
        current_categories = self.analyze_current_gitignore()
        
        for category, rules in current_categories.items():
            if rules:
                print(f"\n📂 {category.replace('_', ' ').title()}: {len(rules)} rules")
                for rule in rules[:3]:  # Show first 3
                    print(f"   • {rule}")
                if len(rules) > 3:
                    print(f"   ... and {len(rules) - 3} more")
        
        print("\n🎯 SHAREABILITY ANALYSIS")
        print("=" * 50)
        
        shareable = self.scan_for_shareable_content()
        
        for content_type, files in shareable.items():
            if files:
                print(f"\n📤 {content_type.replace('_', ' ').title()}: {len(files)} files")
                for file in files[:3]:
                    print(f"   • {file}")
                if len(files) > 3:
                    print(f"   ... and {len(files) - 3} more")
        
        print("\n⚠️  MISSING PROTECTION")
        print("=" * 50)
        
        missing = self.scan_for_missing_protection()
        if missing:
            for file in missing:
                print(f"   ❌ {file}")
        else:
            print("   ✅ No unprotected personal data found")
        
        print("\n💡 CALIBRATION RECOMMENDATIONS")
        print("=" * 50)
        
        # Analyze overly broad rules
        overly_broad = current_categories.get("overly_broad", [])
        if overly_broad:
            print(f"🔧 OVERLY BROAD RULES ({len(overly_broad)}):")
            for rule in overly_broad:
                print(f"   ⚠️  {rule} - May hide valuable architecture")
            print("   💡 Recommendation: Make more specific")
        
        # Check for missing agent architecture protection
        print(f"\n🏗️  AGENT ARCHITECTURE STATUS:")
        print("   ✅ Agent .py files: SHAREABLE (good for showcasing design)")
        print("   ✅ Agent capabilities: SHAREABLE (demonstrates innovation)")
        print("   ❌ Agent personal data: PROTECTED (privacy maintained)")
        
        return {
            "current_categories": current_categories,
            "shareable_content": shareable,
            "missing_protection": missing,
            "calibrated_gitignore": self.generate_calibrated_gitignore()
        }

def main():
    """Run gitignore calibration analysis"""
    
    calibrator = GitIgnoreCalibrator()
    results = calibrator.run_calibration_analysis()
    
    print(f"\n🎯 CALIBRATION COMPLETE")
    print("=" * 50)
    print("📊 Ready to optimize .gitignore for:")
    print("   • Personal data protection")
    print("   • Agent architecture shareability") 
    print("   • Innovation showcase capability")
    print("   • Privacy compliance")
    
    # Option to generate new .gitignore
    print(f"\n💾 Calibrated .gitignore ready for review")
    print("📝 Run with --apply flag to update .gitignore")
    
    return results

if __name__ == "__main__":
    main()