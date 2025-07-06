#!/usr/bin/env python3
"""
Code Quality Agent - Technical Debt Remediation & Directory Cleanup
===================================================================

Comprehensive agent to fix technical debt, standardize code quality,
and clean up the entire LibraryOfBabel directory structure.

Author: Code Quality Agent
Version: 1.0
"""

import os
import re
import ast
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import logging
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TechnicalDebtIssue:
    """Represents a technical debt issue found in the codebase"""
    file_path: str
    issue_type: str
    line_number: int
    description: str
    severity: str  # low, medium, high, critical
    fix_suggestion: str
    estimated_effort: int  # minutes

@dataclass 
class CodeQualityMetrics:
    """Code quality metrics before and after cleanup"""
    total_files: int
    total_lines: int
    import_inconsistencies: int
    hardcoded_configs: int
    path_inconsistencies: int
    duplicate_code_blocks: int
    unused_imports: int
    missing_type_hints: int
    long_functions: int
    timestamp: str

class CodeQualityAgent:
    """Comprehensive code quality and technical debt remediation agent"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.issues: List[TechnicalDebtIssue] = []
        self.metrics_before: Optional[CodeQualityMetrics] = None
        self.metrics_after: Optional[CodeQualityMetrics] = None
        
        # Patterns for technical debt detection
        self.debt_patterns = {
            'hardcoded_config': [
                r"'host':\s*'localhost'",
                r"'database':\s*'[^']*'",
                r"'user':\s*'[^']*'",
                r"DB_CONFIG\s*=\s*{",
                r"database.*=.*['\"][^'\"]+['\"]"
            ],
            'import_issues': [
                r"^import\s+.*,.*$",  # Multiple imports on one line
                r"^from\s+.*\s+import\s+\*$",  # Star imports
            ],
            'path_issues': [
                r"os\.path\.join",  # Old path joining
                r"\/[^\/\s]*\/[^\/\s]*\/",  # Hardcoded paths with slashes
            ],
            'code_smells': [
                r"def\s+\w+\([^)]*\).*:\s*\n(\s+.*\n){50,}",  # Very long functions
                r"#\s*TODO",  # TODO comments
                r"#\s*FIXME",  # FIXME comments
                r"#\s*HACK",  # HACK comments
            ]
        }
        
        # Standard import order
        self.import_order = ['__future__', 'builtins', 'standard', 'third_party', 'local']
        
        # Files to clean up or organize
        self.cleanup_targets = {
            'move_to_scripts': ['analyze_completed_downloads.py'],  # Removed MAM setup
            'move_to_tests': ['test_clean_structure.py', 'test_reddit_agent.py', 'validation_test.py'],
            'consolidate_configs': ['missing_ebooks.json'],  # Removed MAM session
            'organize_logs': ['*.log'],
            'archive_old_reports': ['*_report.json', 'ebook_analysis_*.json']
        }

    def analyze_technical_debt(self) -> List[TechnicalDebtIssue]:
        """Scan entire codebase for technical debt patterns"""
        logger.info("🔍 Scanning codebase for technical debt...")
        
        python_files = list(self.project_root.rglob("*.py"))
        # Skip node_modules and other irrelevant directories
        python_files = [f for f in python_files if 'node_modules' not in str(f)]
        
        for file_path in python_files:
            self._analyze_file(file_path)
        
        logger.info(f"Found {len(self.issues)} technical debt issues")
        return self.issues

    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file for technical debt"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            
            # Check for hardcoded configurations
            self._check_hardcoded_config(file_path, lines)
            
            # Check import issues
            self._check_import_issues(file_path, lines)
            
            # Check path handling issues
            self._check_path_issues(file_path, lines)
            
            # Check for code smells
            self._check_code_smells(file_path, content, lines)
            
            # Check for missing type hints
            self._check_missing_type_hints(file_path, content)
            
        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")

    def _check_hardcoded_config(self, file_path: Path, lines: List[str]):
        """Check for hardcoded configuration values"""
        for i, line in enumerate(lines, 1):
            for pattern in self.debt_patterns['hardcoded_config']:
                if re.search(pattern, line):
                    self.issues.append(TechnicalDebtIssue(
                        file_path=str(file_path),
                        issue_type='hardcoded_config',
                        line_number=i,
                        description=f"Hardcoded configuration: {line.strip()}",
                        severity='medium',
                        fix_suggestion="Move to environment variables or config file",
                        estimated_effort=15
                    ))

    def _check_import_issues(self, file_path: Path, lines: List[str]):
        """Check for import-related issues"""
        imports = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(('import ', 'from ')):
                imports.append((i, line.strip()))
        
        # Check import ordering
        if len(imports) > 1:
            current_order = self._categorize_imports([imp[1] for imp in imports])
            if not self._is_import_order_correct(current_order):
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path),
                    issue_type='import_order',
                    line_number=imports[0][0],
                    description="Import order not following PEP 8",
                    severity='low',
                    fix_suggestion="Reorder imports: stdlib, third-party, local",
                    estimated_effort=5
                ))

    def _check_path_issues(self, file_path: Path, lines: List[str]):
        """Check for path handling issues"""
        for i, line in enumerate(lines, 1):
            if 'Path' in line:
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path),
                    issue_type='path_handling',
                    line_number=i,
                    description="Using Path instead of pathlib",
                    severity='low',
                    fix_suggestion="Replace with pathlib.Path operations",
                    estimated_effort=5
                ))

    def _check_code_smells(self, file_path: Path, content: str, lines: List[str]):
        """Check for code smells and quality issues"""
        # Check for very long functions
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        self.issues.append(TechnicalDebtIssue(
                            file_path=str(file_path),
                            issue_type='long_function',
                            line_number=node.lineno,
                            description=f"Function '{node.name}' is {func_lines} lines long",
                            severity='medium',
                            fix_suggestion="Consider breaking into smaller functions",
                            estimated_effort=30
                        ))
        except SyntaxError:
            pass  # Skip files with syntax errors

        # Check for TODO/FIXME comments
        for i, line in enumerate(lines, 1):
            if re.search(r'#\s*(TODO|FIXME|HACK)', line, re.IGNORECASE):
                self.issues.append(TechnicalDebtIssue(
                    file_path=str(file_path),
                    issue_type='todo_comment',
                    line_number=i,
                    description=f"Unresolved comment: {line.strip()}",
                    severity='low',
                    fix_suggestion="Address the comment or remove if not needed",
                    estimated_effort=10
                ))

    def _check_missing_type_hints(self, file_path: Path, content: str):
        """Check for missing type hints in function definitions"""
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    # Check if function has type hints
                    has_return_annotation = node.returns is not None
                    has_arg_annotations = any(arg.annotation for arg in node.args.args)
                    
                    if not has_return_annotation and not has_arg_annotations:
                        self.issues.append(TechnicalDebtIssue(
                            file_path=str(file_path),
                            issue_type='missing_type_hints',
                            line_number=node.lineno,
                            description=f"Function '{node.name}' missing type hints",
                            severity='low',
                            fix_suggestion="Add type hints for parameters and return value",
                            estimated_effort=10
                        ))
        except SyntaxError:
            pass

    def _categorize_imports(self, imports: List[str]) -> List[str]:
        """Categorize imports into standard, third-party, and local"""
        categories = []
        for imp in imports:
            if imp.startswith('from __future__'):
                categories.append('__future__')
            elif any(imp.startswith(f'import {mod}') or imp.startswith(f'from {mod}') 
                    for mod in ['os', 'sys', 'json', 'time', 'datetime', 're', 'pathlib']):
                categories.append('standard')
            elif imp.startswith('from .') or imp.startswith('import .'):
                categories.append('local')
            else:
                categories.append('third_party')
        return categories

    def _is_import_order_correct(self, order: List[str]) -> bool:
        """Check if import order follows PEP 8"""
        expected_order = ['__future__', 'standard', 'third_party', 'local']
        current_indices = [expected_order.index(cat) if cat in expected_order else len(expected_order) 
                          for cat in order]
        return current_indices == sorted(current_indices)

    def fix_technical_debt(self) -> Dict[str, int]:
        """Fix identified technical debt issues"""
        logger.info("🔧 Starting technical debt remediation...")
        
        fixes_applied = defaultdict(int)
        
        # Group issues by file for efficient processing
        issues_by_file = defaultdict(list)
        for issue in self.issues:
            issues_by_file[issue.file_path].append(issue)
        
        for file_path, file_issues in issues_by_file.items():
            fixes_count = self._fix_file_issues(Path(file_path), file_issues)
            for fix_type, count in fixes_count.items():
                fixes_applied[fix_type] += count
        
        logger.info(f"Applied {sum(fixes_applied.values())} fixes across {len(fixes_applied)} categories")
        return dict(fixes_applied)

    def _fix_file_issues(self, file_path: Path, issues: List[TechnicalDebtIssue]) -> Dict[str, int]:
        """Fix issues in a single file"""
        fixes_applied = defaultdict(int)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Sort issues by line number in reverse order to avoid line number shifts
            issues.sort(key=lambda x: x.line_number, reverse=True)
            
            modified = False
            for issue in issues:
                if issue.issue_type == 'hardcoded_config' and issue.severity in ['medium', 'high']:
                    # Create environment variable version
                    line_idx = issue.line_number - 1
                    if line_idx < len(lines):
                        original_line = lines[line_idx]
                        fixed_line = self._fix_hardcoded_config(original_line)
                        if fixed_line != original_line:
                            lines[line_idx] = fixed_line
                            fixes_applied['hardcoded_config'] += 1
                            modified = True
                
                elif issue.issue_type == 'path_handling':
                    # Fix path handling
                    line_idx = issue.line_number - 1
                    if line_idx < len(lines):
                        original_line = lines[line_idx]
                        fixed_line = self._fix_path_handling(original_line)
                        if fixed_line != original_line:
                            lines[line_idx] = fixed_line
                            fixes_applied['path_handling'] += 1
                            modified = True
            
            # Write back modified file
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                logger.info(f"Fixed {sum(fixes_applied.values())} issues in {file_path}")
            
        except Exception as e:
            logger.warning(f"Failed to fix issues in {file_path}: {e}")
        
        return dict(fixes_applied)

    def _fix_hardcoded_config(self, line: str) -> str:
        """Fix hardcoded configuration by suggesting environment variables"""
        # This is a simple example - in practice, you'd want more sophisticated replacement
        if "'host': os.getenv('DB_HOST', 'localhost')" in line:
            return line.replace("'host': os.getenv('DB_HOST', 'localhost')", "'host': os.getenv('DB_HOST', 'localhost')")
        elif "'database':" in line and "'knowledge_base'" in line:
            return line.replace("'knowledge_base'", "os.getenv('DB_NAME', 'knowledge_base')")
        elif "'user':" in line:
            # Extract the username and replace with env var
            match = re.search(r"'user':\s*'([^']*)'", line)
            if match:
                username = match.group(1)
                return line.replace(f"'user': os.getenv('DB_USER', '{username}')", f"'user': os.getenv('DB_USER', '{username}')")
        
        return line

    def _fix_path_handling(self, line: str) -> str:
        """Fix path handling to use pathlib"""
        # Simple replacement for Path
        if 'Path' in line:
            # This is a simplified replacement - real implementation would be more sophisticated
            return line.replace('Path', 'Path')
        
        return line

    def cleanup_directory_structure(self) -> Dict[str, int]:
        """Clean up and organize the directory structure"""
        logger.info("🧹 Cleaning up directory structure...")
        
        cleanup_stats = defaultdict(int)
        
        # Create necessary directories
        self._ensure_directories_exist()
        
        # Move files to appropriate locations
        cleanup_stats.update(self._move_files_to_proper_locations())
        
        # Clean up duplicate files
        cleanup_stats.update(self._remove_duplicate_files())
        
        # Organize configuration files
        cleanup_stats.update(self._organize_config_files())
        
        # Archive old reports and logs
        cleanup_stats.update(self._archive_old_files())
        
        logger.info(f"Directory cleanup completed: {dict(cleanup_stats)}")
        return dict(cleanup_stats)

    def _ensure_directories_exist(self):
        """Ensure all necessary directories exist"""
        required_dirs = [
            'scripts',
            'config/environment',
            'logs/archive',
            'reports/archive',
            'docs/maintenance'
        ]
        
        for dir_path in required_dirs:
            (self.project_root / dir_path).mkdir(parents=True, exist_ok=True)

    def _move_files_to_proper_locations(self) -> Dict[str, int]:
        """Move files to their proper locations"""
        moves_made = defaultdict(int)
        
        # Move scripts
        for script_name in self.cleanup_targets['move_to_scripts']:
            src = self.project_root / script_name
            if src.exists():
                dst = self.project_root / 'scripts' / script_name
                shutil.move(str(src), str(dst))
                moves_made['scripts_moved'] += 1
        
        # Move test files
        for test_name in self.cleanup_targets['move_to_tests']:
            src = self.project_root / test_name
            if src.exists():
                dst = self.project_root / 'tests' / test_name
                if not dst.exists():  # Avoid overwriting existing tests
                    shutil.move(str(src), str(dst))
                    moves_made['tests_moved'] += 1
        
        return dict(moves_made)

    def _remove_duplicate_files(self) -> Dict[str, int]:
        """Remove duplicate files"""
        duplicates_removed = defaultdict(int)
        
        # Find and remove duplicate Python files
        python_files = list(self.project_root.rglob("*.py"))
        python_files = [f for f in python_files if 'node_modules' not in str(f)]
        
        file_hashes = {}
        for file_path in python_files:
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                
                if file_hash in file_hashes:
                    # Found duplicate
                    original = file_hashes[file_hash]
                    logger.info(f"Found duplicate: {file_path} (original: {original})")
                    # Only remove if it's clearly a duplicate in wrong location
                    if 'test_' in file_path.name and 'tests' not in str(file_path):
                        file_path.unlink()
                        duplicates_removed['duplicates_removed'] += 1
                else:
                    file_hashes[file_hash] = file_path
            except Exception as e:
                logger.warning(f"Failed to check duplicate {file_path}: {e}")
        
        return dict(duplicates_removed)

    def _organize_config_files(self) -> Dict[str, int]:
        """Organize configuration files"""
        configs_organized = defaultdict(int)
        
        # Move JSON config files to config directory
        json_files = list(self.project_root.glob("*.json"))
        for json_file in json_files:
            if json_file.name in ['package.json', 'package-lock.json']:
                continue  # Skip npm files
            
            dst_dir = self.project_root / 'config'
            dst_file = dst_dir / json_file.name
            
            if not dst_file.exists():
                shutil.move(str(json_file), str(dst_file))
                configs_organized['configs_moved'] += 1
        
        return dict(configs_organized)

    def _archive_old_files(self) -> Dict[str, int]:
        """Archive old log files and reports"""
        archived = defaultdict(int)
        
        # Archive log files
        log_files = list(self.project_root.glob("*.log"))
        for log_file in log_files:
            dst = self.project_root / 'logs' / 'archive' / log_file.name
            if not dst.exists():
                shutil.move(str(log_file), str(dst))
                archived['logs_archived'] += 1
        
        # Archive old report files
        report_files = list(self.project_root.glob("*report*.json"))
        report_files.extend(list(self.project_root.glob("ebook_analysis_*.json")))
        
        for report_file in report_files:
            dst = self.project_root / 'reports' / 'archive' / report_file.name
            if not dst.exists():
                shutil.move(str(report_file), str(dst))
                archived['reports_archived'] += 1
        
        return dict(archived)

    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive code quality report"""
        logger.info("📊 Generating code quality report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'technical_debt_summary': {
                'total_issues': len(self.issues),
                'issues_by_severity': Counter(issue.severity for issue in self.issues),
                'issues_by_type': Counter(issue.issue_type for issue in self.issues),
                'estimated_total_effort_minutes': sum(issue.estimated_effort for issue in self.issues)
            },
            'top_priority_fixes': [
                asdict(issue) for issue in sorted(self.issues, 
                    key=lambda x: (x.severity == 'critical', x.severity == 'high', x.estimated_effort), 
                    reverse=True)[:10]
            ],
            'files_with_most_issues': Counter(issue.file_path for issue in self.issues).most_common(5),
            'recommendations': self._generate_recommendations()
        }
        
        # Save report
        report_path = self.project_root / 'reports' / f'code_quality_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Quality report saved to {report_path}")
        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if any(issue.issue_type == 'hardcoded_config' for issue in self.issues):
            recommendations.append("Implement environment-based configuration management")
        
        if any(issue.issue_type == 'import_order' for issue in self.issues):
            recommendations.append("Set up automatic import sorting with isort or black")
        
        if any(issue.issue_type == 'long_function' for issue in self.issues):
            recommendations.append("Refactor large functions into smaller, focused functions")
        
        if any(issue.issue_type == 'missing_type_hints' for issue in self.issues):
            recommendations.append("Add type hints for better code maintainability")
        
        recommendations.append("Set up pre-commit hooks for code quality checks")
        recommendations.append("Consider adding automated code formatting with black")
        
        return recommendations

    def run_full_cleanup(self) -> Dict[str, Any]:
        """Run complete code quality cleanup process"""
        logger.info("🚀 Starting full code quality cleanup...")
        
        start_time = datetime.now()
        
        # Step 1: Analyze technical debt
        self.analyze_technical_debt()
        
        # Step 2: Fix technical debt
        fixes_applied = self.fix_technical_debt()
        
        # Step 3: Clean up directory structure
        cleanup_stats = self.cleanup_directory_structure()
        
        # Step 4: Generate report
        quality_report = self.generate_quality_report()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'cleanup_duration_seconds': duration,
            'technical_debt_fixes': fixes_applied,
            'directory_cleanup': cleanup_stats,
            'total_issues_found': len(self.issues),
            'quality_report_path': str(self.project_root / 'reports' / f'code_quality_report_{end_time.strftime("%Y%m%d_%H%M%S")}.json')
        }
        
        logger.info(f"✅ Full cleanup completed in {duration:.2f} seconds")
        logger.info(f"Summary: {summary}")
        
        return summary


def main():
    """Run the Code Quality Agent"""
    agent = CodeQualityAgent()
    result = agent.run_full_cleanup()
    
    print("\n🎉 Code Quality Agent Cleanup Complete!")
    print(f"📊 Found and processed {result['total_issues_found']} issues")
    print(f"🔧 Applied {sum(result['technical_debt_fixes'].values())} technical debt fixes")
    print(f"🧹 Performed {sum(result['directory_cleanup'].values())} cleanup operations")
    print(f"⏱️  Total time: {result['cleanup_duration_seconds']:.2f} seconds")
    
    return result


if __name__ == "__main__":
    main()