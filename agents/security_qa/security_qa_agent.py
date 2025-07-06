#!/usr/bin/env python3
"""
Security QA Agent - LibraryOfBabel Project
Specialized agent for security vulnerability detection and remediation
"""

import os
import json
import logging
import subprocess
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class SecurityQAAgent:
    """
    Advanced Security QA Agent for LibraryOfBabel project
    
    Capabilities:
    - Detect sensitive data exposure (API keys, passwords, tokens)
    - Identify security vulnerabilities in code
    - Analyze file permissions and access patterns
    - Generate security remediation reports
    - Automated cleanup of security issues
    """
    
    def __init__(self, project_root: str = "/Users/weixiangzhang/Local Dev/LibraryOfBabel"):
        self.project_root = Path(project_root)
        self.setup_logging()
        self.security_issues = []
        self.remediation_actions = []
        
        # Security patterns to detect
        self.sensitive_patterns = {
            'api_keys': [
                r'api_key\s*=\s*["\']([^"\']+)["\']',
                r'API_KEY\s*=\s*["\']([^"\']+)["\']',
                r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API keys
                r'pk_[a-zA-Z0-9]{32,}',  # Stripe public keys
                r'Bearer\s+[a-zA-Z0-9\-_]{32,}',  # Bearer tokens
            ],
            'passwords': [
                r'password\s*=\s*["\']([^"\']+)["\']',
                r'PASSWORD\s*=\s*["\']([^"\']+)["\']',
                r'pwd\s*=\s*["\']([^"\']+)["\']',
            ],
            'secrets': [
                r'secret\s*=\s*["\']([^"\']+)["\']',
                r'SECRET\s*=\s*["\']([^"\']+)["\']',
                r'token\s*=\s*["\']([^"\']+)["\']',
                r'TOKEN\s*=\s*["\']([^"\']+)["\']',
            ],
            'database_urls': [
                r'postgresql://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+',
                r'mysql://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+',
                r'mongodb://[^:\s]+:[^@\s]+@[^/\s]+/[^\s]+',
            ]
        }
        
        # Files that should never contain sensitive data
        self.high_risk_files = [
            '*.py', '*.js', '*.json', '*.yml', '*.yaml', 
            '*.md', '*.txt', '*.log', '*.conf', '*.config'
        ]
        
        # Directories to exclude from security scan
        self.exclude_dirs = [
            'node_modules', 'venv', '.git', '__pycache__', 
            '.pytest_cache', 'build', 'dist'
        ]
    
    def setup_logging(self):
        """Setup logging for security operations"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"security_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("SecurityQAAgent")
    
    def scan_for_sensitive_data(self) -> List[Dict]:
        """Scan project for sensitive data exposure"""
        self.logger.info("🔍 Starting sensitive data scan...")
        
        sensitive_findings = []
        
        for file_path in self.get_scannable_files():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check each pattern category
                    for category, patterns in self.sensitive_patterns.items():
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            for match in matches:
                                finding = {
                                    'file': str(file_path.relative_to(self.project_root)),
                                    'category': category,
                                    'pattern': pattern,
                                    'match': match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0),
                                    'line_number': content[:match.start()].count('\n') + 1,
                                    'severity': 'HIGH' if category in ['api_keys', 'passwords'] else 'MEDIUM'
                                }
                                sensitive_findings.append(finding)
                                self.logger.warning(f"🚨 Sensitive data found: {finding['file']}:{finding['line_number']}")
                                
            except Exception as e:
                self.logger.error(f"Error scanning {file_path}: {e}")
        
        return sensitive_findings
    
    def get_scannable_files(self) -> List[Path]:
        """Get list of files to scan for security issues"""
        scannable_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check if file matches high-risk patterns
                if any(file_path.match(pattern) for pattern in self.high_risk_files):
                    scannable_files.append(file_path)
        
        return scannable_files
    
    def analyze_file_permissions(self) -> List[Dict]:
        """Analyze file permissions for security issues"""
        self.logger.info("🔒 Analyzing file permissions...")
        
        permission_issues = []
        
        for file_path in self.get_scannable_files():
            try:
                stat_info = file_path.stat()
                mode = oct(stat_info.st_mode)[-3:]  # Get last 3 octal digits
                
                # Check for overly permissive files
                if mode in ['777', '666', '755'] and file_path.suffix in ['.py', '.sh', '.key', '.pem']:
                    issue = {
                        'file': str(file_path.relative_to(self.project_root)),
                        'current_permissions': mode,
                        'issue': 'Overly permissive file permissions',
                        'severity': 'MEDIUM',
                        'recommendation': 'Change to 644 for regular files, 755 for executables'
                    }
                    permission_issues.append(issue)
                    
            except Exception as e:
                self.logger.error(f"Error checking permissions for {file_path}: {e}")
        
        return permission_issues
    
    def detect_security_vulnerabilities(self) -> List[Dict]:
        """Detect common security vulnerabilities in code"""
        self.logger.info("🛡️ Detecting security vulnerabilities...")
        
        vulnerabilities = []
        
        # Common vulnerability patterns
        vuln_patterns = {
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'cursor\.execute\s*\(\s*["\'].*\+.*["\']',
                r'query\s*=\s*["\'].*\+.*["\']',
            ],
            'command_injection': [
                r'subprocess\.call\s*\(\s*shell\s*=\s*True',
                r'os\.system\s*\(',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            'path_traversal': [
                r'open\s*\(\s*.*\+.*\)',
                r'file\s*=\s*.*\+.*',
            ],
            'weak_crypto': [
                r'md5\s*\(',
                r'sha1\s*\(',
                r'DES\s*\(',
            ]
        }
        
        for file_path in self.get_scannable_files():
            if file_path.suffix == '.py':
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        for vuln_type, patterns in vuln_patterns.items():
                            for pattern in patterns:
                                matches = re.finditer(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    vuln = {
                                        'file': str(file_path.relative_to(self.project_root)),
                                        'vulnerability': vuln_type,
                                        'pattern': pattern,
                                        'line_number': content[:match.start()].count('\n') + 1,
                                        'code_snippet': match.group(0),
                                        'severity': 'HIGH' if vuln_type in ['sql_injection', 'command_injection'] else 'MEDIUM'
                                    }
                                    vulnerabilities.append(vuln)
                                    
                except Exception as e:
                    self.logger.error(f"Error analyzing {file_path}: {e}")
        
        return vulnerabilities
    
    def generate_remediation_plan(self, analysis_doc: str) -> Dict:
        """Generate automated remediation plan based on security analysis"""
        self.logger.info("📋 Generating remediation plan...")
        
        remediation_plan = {
            'timestamp': datetime.now().isoformat(),
            'critical_actions': [],
            'high_priority_actions': [],
            'medium_priority_actions': [],
            'automated_fixes': [],
            'manual_review_required': []
        }
        
        # Parse analysis document for specific issues
        if 'api_key.txt' in analysis_doc:
            remediation_plan['critical_actions'].append({
                'action': 'Remove API key file from repository',
                'file': 'api_key.txt',
                'command': 'git rm api_key.txt && git commit -m "Remove sensitive API key file"',
                'automated': True
            })
        
        if '*.log' in analysis_doc:
            remediation_plan['high_priority_actions'].append({
                'action': 'Add log files to .gitignore',
                'files': '*.log',
                'command': 'echo "*.log" >> .gitignore && git add .gitignore',
                'automated': True
            })
        
        if 'SSL configs' in analysis_doc:
            remediation_plan['medium_priority_actions'].append({
                'action': 'Review SSL configuration files for sensitive data',
                'directory': 'ssl/',
                'automated': False,
                'manual_review': True
            })
        
        return remediation_plan
    
    def execute_automated_fixes(self, remediation_plan: Dict) -> Dict:
        """Execute automated security fixes"""
        self.logger.info("🔧 Executing automated security fixes...")
        
        execution_results = {
            'successful_fixes': [],
            'failed_fixes': [],
            'skipped_fixes': []
        }
        
        for action in remediation_plan.get('critical_actions', []) + remediation_plan.get('automated_fixes', []):
            if action.get('automated', False):
                try:
                    if 'command' in action:
                        result = subprocess.run(
                            action['command'], 
                            shell=True, 
                            capture_output=True, 
                            text=True,
                            cwd=self.project_root
                        )
                        
                        if result.returncode == 0:
                            execution_results['successful_fixes'].append({
                                'action': action['action'],
                                'output': result.stdout
                            })
                            self.logger.info(f"✅ Successfully executed: {action['action']}")
                        else:
                            execution_results['failed_fixes'].append({
                                'action': action['action'],
                                'error': result.stderr
                            })
                            self.logger.error(f"❌ Failed to execute: {action['action']}")
                            
                except Exception as e:
                    execution_results['failed_fixes'].append({
                        'action': action['action'],
                        'error': str(e)
                    })
                    self.logger.error(f"❌ Exception executing {action['action']}: {e}")
            else:
                execution_results['skipped_fixes'].append(action)
        
        return execution_results
    
    def generate_security_report(self, analysis_doc: str) -> Dict:
        """Generate comprehensive security report"""
        self.logger.info("📊 Generating comprehensive security report...")
        
        # Run all security scans
        sensitive_data = self.scan_for_sensitive_data()
        permission_issues = self.analyze_file_permissions()
        vulnerabilities = self.detect_security_vulnerabilities()
        remediation_plan = self.generate_remediation_plan(analysis_doc)
        
        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'summary': {
                'total_sensitive_data_findings': len(sensitive_data),
                'total_permission_issues': len(permission_issues),
                'total_vulnerabilities': len(vulnerabilities),
                'critical_issues': len([f for f in sensitive_data if f['severity'] == 'HIGH']),
                'high_priority_fixes': len(remediation_plan.get('high_priority_actions', [])),
                'automated_fixes_available': len(remediation_plan.get('automated_fixes', []))
            },
            'detailed_findings': {
                'sensitive_data': sensitive_data,
                'permission_issues': permission_issues,
                'vulnerabilities': vulnerabilities
            },
            'remediation_plan': remediation_plan,
            'analysis_document': analysis_doc
        }
        
        # Save report
        report_path = self.project_root / "reports" / f"security_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📋 Security report saved to: {report_path}")
        
        return report
    
    def run_security_audit(self, analysis_doc: str) -> Dict:
        """Run complete security audit with remediation"""
        self.logger.info("🚀 Starting comprehensive security audit...")
        
        # Generate security report
        report = self.generate_security_report(analysis_doc)
        
        # Execute automated fixes
        execution_results = self.execute_automated_fixes(report['remediation_plan'])
        
        # Update report with execution results
        report['execution_results'] = execution_results
        
        # Print summary
        self.print_security_summary(report)
        
        return report
    
    def print_security_summary(self, report: Dict):
        """Print security audit summary"""
        print("\n" + "="*60)
        print("🛡️  SECURITY QA AGENT - AUDIT SUMMARY")
        print("="*60)
        print(f"📊 Scan Results:")
        print(f"   • Sensitive Data Findings: {report['summary']['total_sensitive_data_findings']}")
        print(f"   • Permission Issues: {report['summary']['total_permission_issues']}")
        print(f"   • Security Vulnerabilities: {report['summary']['total_vulnerabilities']}")
        print(f"   • Critical Issues: {report['summary']['critical_issues']}")
        
        if report.get('execution_results'):
            print(f"\n🔧 Automated Fixes:")
            print(f"   • Successful: {len(report['execution_results']['successful_fixes'])}")
            print(f"   • Failed: {len(report['execution_results']['failed_fixes'])}")
            print(f"   • Skipped: {len(report['execution_results']['skipped_fixes'])}")
        
        print(f"\n📋 Next Steps:")
        print(f"   • Review manual fixes required")
        print(f"   • Implement environment variable configuration")
        print(f"   • Update .gitignore for sensitive files")
        print("="*60)

def main():
    """Main function for running Security QA Agent"""
    analysis_doc = """
    # LibraryOfBabel Security Analysis
    
    ## Critical Security Issues Found:
    
    1. **API Key Exposure**: /api_key.txt contains sensitive API credentials
    2. **Log File Exposure**: Multiple .log files contain potentially sensitive information
    3. **SSL Configuration**: SSL configs may contain sensitive certificate data
    4. **Scattered Sensitive Files**: Configuration files with potential credentials
    
    ## Immediate Actions Required:
    - Remove api_key.txt from repository
    - Add *.log to .gitignore
    - Move sensitive configs to environment variables
    - Review SSL certificate files for sensitive data
    """
    
    agent = SecurityQAAgent()
    report = agent.run_security_audit(analysis_doc)
    
    return report

if __name__ == "__main__":
    main()