#!/usr/bin/env python3
"""
Comprehensive QA Agent - LibraryOfBabel
======================================

Unified QA system combining:
- System testing (downloads, Transmission, web frontend)
- Database performance optimization 
- Vulnerability detection and fixes
- Security scanning integration

This agent consolidates functionality from:
- /agents/qa_system/qa_agent.py (system testing)
- /src/qa_agent.py (database optimization)
"""

import os
import json
import time
import sqlite3
import subprocess
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging
from dataclasses import dataclass
import threading

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/comprehensive_qa.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ComprehensiveQA")

@dataclass
class QATestResult:
    """Comprehensive QA test result with detailed metrics"""
    test_name: str
    category: str  # 'system', 'database', 'security', 'performance'
    status: str  # 'passed', 'failed', 'warning'
    duration_seconds: float
    details: Dict
    error_message: Optional[str] = None
    timestamp: str = None
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class TransmissionClient:
    """Interface to Transmission CLI for download testing"""
    
    def __init__(self, config):
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 9091)
        self.username = config.get('username')
        self.password = config.get('password')
        self.logger = logging.getLogger(__name__)
    
    def add_torrent(self, torrent_file_path: str, download_dir: str = None) -> Dict:
        """Add torrent to Transmission and return torrent info"""
        cmd = ['transmission-remote']
        
        if self.username and self.password:
            cmd.extend(['-n', f'{self.username}:{self.password}'])
        
        cmd.extend(['-a', torrent_file_path])
        
        if download_dir:
            cmd.extend(['-w', download_dir])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                torrent_id = self._extract_torrent_id(output)
                
                return {
                    'success': True,
                    'torrent_id': torrent_id,
                    'output': output
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'output': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Transmission command timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_torrent_status(self, torrent_id: str) -> Dict:
        """Get status of specific torrent"""
        cmd = ['transmission-remote', '-t', torrent_id, '-i']
        
        if self.username and self.password:
            cmd.extend(['-n', f'{self.username}:{self.password}'])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'status': self._parse_torrent_info(result.stdout)
                }
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _extract_torrent_id(self, output: str) -> Optional[str]:
        """Extract torrent ID from transmission output"""
        lines = output.split('\n')
        for line in lines:
            if 'responded:' in line and 'success' in line:
                # Look for torrent ID in response
                words = line.split()
                for word in words:
                    if word.isdigit():
                        return word
        return None
    
    def _parse_torrent_info(self, output: str) -> Dict:
        """Parse torrent information from transmission output"""
        info = {}
        lines = output.split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info

class ComprehensiveQAAgent:
    """
    Unified QA Agent for LibraryOfBabel
    
    Combines system testing, database optimization, and security validation
    into a single comprehensive quality assurance system.
    """
    
    def __init__(self, config_file: str = "qa_config.json"):
        self.config = self._load_config(config_file)
        self.results = []
        self.fixes_applied = []
        self.performance_improvements = []
        self.security_enhancements = []
        
        # Database configuration
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        
        # Initialize Transmission client
        self.transmission = TransmissionClient(self.config.get('transmission', {}))
        
        logger.info("🔧 Comprehensive QA Agent initialized")
        logger.info(f"📊 Config loaded: {len(self.config)} sections")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load QA configuration from file"""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "transmission": {
                    "host": "localhost",
                    "port": 9091,
                    "username": None,
                    "password": None
                },
                "database": {
                    "performance_thresholds": {
                        "query_time_ms": 1000,
                        "connection_time_ms": 500
                    }
                },
                "system": {
                    "api_endpoints": ["http://localhost:5563/api/v3/info"],
                    "timeout_seconds": 30
                }
            }
    
    def connect_db(self):
        """Establish database connection with error handling"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    # ================================
    # SYSTEM TESTING (from qa_system/qa_agent.py)
    # ================================
    
    def test_database_connectivity(self) -> QATestResult:
        """Test database connection and basic operations"""
        start_time = time.time()
        
        try:
            with self.connect_db() as conn:
                if not conn:
                    return QATestResult(
                        test_name="database_connectivity",
                        category="system",
                        status="failed",
                        duration_seconds=time.time() - start_time,
                        details={},
                        error_message="Failed to connect to database",
                        severity="critical"
                    )
                
                with conn.cursor() as cur:
                    # Test basic query
                    cur.execute("SELECT COUNT(*) FROM books")
                    book_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM chunks")
                    chunk_count = cur.fetchone()[0]
                    
                    return QATestResult(
                        test_name="database_connectivity",
                        category="system",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={
                            "book_count": book_count,
                            "chunk_count": chunk_count,
                            "connection_successful": True
                        }
                    )
        
        except Exception as e:
            return QATestResult(
                test_name="database_connectivity",
                category="system",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e),
                severity="high"
            )
    
    def test_api_endpoints(self) -> List[QATestResult]:
        """Test API endpoint availability and response times"""
        results = []
        
        endpoints = self.config.get('system', {}).get('api_endpoints', [])
        timeout = self.config.get('system', {}).get('timeout_seconds', 30)
        
        for endpoint in endpoints:
            start_time = time.time()
            
            try:
                response = requests.get(endpoint, timeout=timeout)
                duration = time.time() - start_time
                
                status = "passed" if response.status_code == 200 else "failed"
                severity = "low" if status == "passed" else "medium"
                
                results.append(QATestResult(
                    test_name=f"api_endpoint_{endpoint.split('/')[-1]}",
                    category="system",
                    status=status,
                    duration_seconds=duration,
                    details={
                        "endpoint": endpoint,
                        "status_code": response.status_code,
                        "response_time_ms": duration * 1000,
                        "content_length": len(response.content)
                    },
                    error_message=None if status == "passed" else f"HTTP {response.status_code}",
                    severity=severity
                ))
                
            except Exception as e:
                results.append(QATestResult(
                    test_name=f"api_endpoint_{endpoint.split('/')[-1]}",
                    category="system",
                    status="failed",
                    duration_seconds=time.time() - start_time,
                    details={"endpoint": endpoint},
                    error_message=str(e),
                    severity="high"
                ))
        
        return results
    
    def test_transmission_connectivity(self) -> QATestResult:
        """Test Transmission daemon connectivity"""
        start_time = time.time()
        
        try:
            # Test basic connection by listing torrents
            cmd = ['transmission-remote', '-l']
            
            if self.transmission.username and self.transmission.password:
                cmd.extend(['-n', f'{self.transmission.username}:{self.transmission.password}'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return QATestResult(
                    test_name="transmission_connectivity",
                    category="system",
                    status="passed",
                    duration_seconds=duration,
                    details={
                        "transmission_accessible": True,
                        "output_lines": len(result.stdout.split('\n'))
                    }
                )
            else:
                return QATestResult(
                    test_name="transmission_connectivity",
                    category="system",
                    status="failed",
                    duration_seconds=duration,
                    details={},
                    error_message=result.stderr,
                    severity="medium"
                )
        
        except Exception as e:
            return QATestResult(
                test_name="transmission_connectivity",
                category="system",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e),
                severity="medium"
            )
    
    # ================================
    # DATABASE OPTIMIZATION (from src/qa_agent.py)
    # ================================
    
    def analyze_chaos_report(self, report_file: str = "config/reddit_nerd_chaos_report.json") -> QATestResult:
        """Analyze Reddit Nerd Librarian chaos testing report"""
        start_time = time.time()
        
        if not Path(report_file).exists():
            return QATestResult(
                test_name="chaos_report_analysis",
                category="performance",
                status="warning",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=f"Chaos report not found: {report_file}",
                severity="low"
            )
        
        try:
            with open(report_file, 'r') as f:
                report = json.load(f)
            
            # Extract performance issues
            issues = {
                'unicode_performance': [],
                'sql_injection_speed': [],
                'missing_intersections': [],
                'response_time_variance': []
            }
            
            for attack in report.get('successful_chaos_attacks', []):
                response_time = attack.get('response_time_ms', 0)
                query = attack.get('query', '')
                attack_type = attack.get('attack_type', '')
                
                if attack_type == 'unicode_chaos' and response_time > 1000:
                    issues['unicode_performance'].append({
                        'query': query[:50] + "...",
                        'response_time': response_time,
                        'severity': 'high' if response_time > 1500 else 'medium'
                    })
                
                if attack_type == 'sql_injection' and response_time > 1000:
                    issues['sql_injection_speed'].append({
                        'query': query[:50] + "...",
                        'response_time': response_time
                    })
                
                if attack_type == 'intersection_bomb' and attack.get('results_count', 0) == 0:
                    issues['missing_intersections'].append(query[:50] + "...")
            
            # Determine overall status
            total_issues = sum(len(issue_list) for issue_list in issues.values())
            status = "passed" if total_issues == 0 else "warning" if total_issues < 10 else "failed"
            severity = "low" if total_issues < 5 else "medium" if total_issues < 15 else "high"
            
            return QATestResult(
                test_name="chaos_report_analysis",
                category="performance",
                status=status,
                duration_seconds=time.time() - start_time,
                details={
                    "total_attacks": len(report.get('successful_chaos_attacks', [])),
                    "performance_issues": issues,
                    "issue_count": total_issues
                },
                severity=severity
            )
        
        except Exception as e:
            return QATestResult(
                test_name="chaos_report_analysis",
                category="performance",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e),
                severity="medium"
            )
    
    def optimize_unicode_queries(self) -> QATestResult:
        """Apply Unicode query optimizations to database"""
        start_time = time.time()
        
        try:
            with self.connect_db() as conn:
                if not conn:
                    return QATestResult(
                        test_name="unicode_optimization",
                        category="database",
                        status="failed",
                        duration_seconds=time.time() - start_time,
                        details={},
                        error_message="Database connection failed",
                        severity="high"
                    )
                
                with conn.cursor() as cur:
                    # Create optimized Unicode text search function
                    cur.execute("""
                        CREATE OR REPLACE FUNCTION optimize_unicode_search(search_text TEXT)
                        RETURNS TABLE(chunk_id INTEGER, relevance REAL) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT c.chunk_id, 
                                   ts_rank(to_tsvector('english', c.content), 
                                          plainto_tsquery('english', search_text)) as relevance
                            FROM chunks c
                            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', search_text)
                            ORDER BY relevance DESC
                            LIMIT 100;
                        END;
                        $$ LANGUAGE plpgsql;
                    """)
                    
                    # Create index for better Unicode handling
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_chunks_content_unicode 
                        ON chunks USING gin(to_tsvector('english', content))
                    """)
                    
                    conn.commit()
                    
                    self.performance_improvements.append({
                        'type': 'unicode_optimization',
                        'description': 'Optimized Unicode text search with dedicated function and index',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return QATestResult(
                        test_name="unicode_optimization",
                        category="database",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={
                            "optimization_applied": True,
                            "function_created": "optimize_unicode_search",
                            "index_created": "idx_chunks_content_unicode"
                        }
                    )
        
        except Exception as e:
            return QATestResult(
                test_name="unicode_optimization",
                category="database",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e),
                severity="medium"
            )
    
    def implement_sql_injection_protection(self) -> QATestResult:
        """Implement SQL injection protection measures"""
        start_time = time.time()
        
        try:
            with self.connect_db() as conn:
                if not conn:
                    return QATestResult(
                        test_name="sql_injection_protection",
                        category="security",
                        status="failed",
                        duration_seconds=time.time() - start_time,
                        details={},
                        error_message="Database connection failed",
                        severity="critical"
                    )
                
                with conn.cursor() as cur:
                    # Create input validation function
                    cur.execute("""
                        CREATE OR REPLACE FUNCTION validate_search_input(input_text TEXT)
                        RETURNS BOOLEAN AS $$
                        BEGIN
                            -- Block obvious SQL injection patterns
                            IF input_text ~* '(;|--|/\\*|\\*/|\\bUNION\\b|\\bSELECT\\b|\\bINSERT\\b|\\bUPDATE\\b|\\bDELETE\\b|\\bDROP\\b)' THEN
                                RETURN FALSE;
                            END IF;
                            
                            -- Block excessively long inputs
                            IF LENGTH(input_text) > 1000 THEN
                                RETURN FALSE;
                            END IF;
                            
                            RETURN TRUE;
                        END;
                        $$ LANGUAGE plpgsql;
                    """)
                    
                    # Create secure search wrapper
                    cur.execute("""
                        CREATE OR REPLACE FUNCTION secure_text_search(search_query TEXT)
                        RETURNS TABLE(
                            chunk_id INTEGER,
                            book_id INTEGER,
                            content TEXT,
                            relevance REAL
                        ) AS $$
                        BEGIN
                            -- Validate input first
                            IF NOT validate_search_input(search_query) THEN
                                RAISE EXCEPTION 'Invalid search input detected';
                            END IF;
                            
                            -- Perform safe search
                            RETURN QUERY
                            SELECT c.chunk_id, c.book_id, 
                                   LEFT(c.content, 500) as content,
                                   ts_rank(to_tsvector('english', c.content), 
                                          plainto_tsquery('english', search_query)) as relevance
                            FROM chunks c
                            WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', search_query)
                            ORDER BY relevance DESC
                            LIMIT 50;
                        END;
                        $$ LANGUAGE plpgsql;
                    """)
                    
                    conn.commit()
                    
                    self.security_enhancements.append({
                        'type': 'sql_injection_protection',
                        'description': 'Input validation and secure search wrapper functions',
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return QATestResult(
                        test_name="sql_injection_protection",
                        category="security",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={
                            "protection_implemented": True,
                            "validation_function": "validate_search_input",
                            "secure_search_function": "secure_text_search"
                        }
                    )
        
        except Exception as e:
            return QATestResult(
                test_name="sql_injection_protection",
                category="security",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e),
                severity="high"
            )
    
    # ================================
    # COMPREHENSIVE QA ORCHESTRATION
    # ================================
    
    def run_comprehensive_qa(self) -> Dict:
        """Run complete QA suite covering all categories"""
        logger.info("🚀 Starting comprehensive QA testing suite...")
        start_time = time.time()
        
        self.results = []
        
        # System Testing
        logger.info("📊 Running system tests...")
        self.results.append(self.test_database_connectivity())
        self.results.extend(self.test_api_endpoints())
        self.results.append(self.test_transmission_connectivity())
        
        # Performance Testing
        logger.info("⚡ Running performance tests...")
        self.results.append(self.analyze_chaos_report())
        
        # Database Optimization
        logger.info("🗄️ Running database optimizations...")
        self.results.append(self.optimize_unicode_queries())
        
        # Security Testing
        logger.info("🔒 Running security tests...")
        self.results.append(self.implement_sql_injection_protection())
        
        # Generate comprehensive report
        total_duration = time.time() - start_time
        
        # Calculate statistics
        stats = {
            'total_tests': len(self.results),
            'passed': len([r for r in self.results if r.status == 'passed']),
            'failed': len([r for r in self.results if r.status == 'failed']),
            'warnings': len([r for r in self.results if r.status == 'warning']),
            'critical_issues': len([r for r in self.results if r.severity == 'critical']),
            'high_issues': len([r for r in self.results if r.severity == 'high']),
            'total_duration_seconds': total_duration
        }
        
        # Overall health score
        health_score = (stats['passed'] / stats['total_tests']) * 100 if stats['total_tests'] > 0 else 0
        
        # Reduce score for critical issues
        if stats['critical_issues'] > 0:
            health_score = max(0, health_score - (stats['critical_issues'] * 25))
        if stats['high_issues'] > 0:
            health_score = max(0, health_score - (stats['high_issues'] * 10))
        
        comprehensive_report = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': total_duration,
            'statistics': stats,
            'health_score': round(health_score, 2),
            'health_status': self._get_health_status(health_score),
            'test_results': [
                {
                    'test_name': r.test_name,
                    'category': r.category,
                    'status': r.status,
                    'severity': r.severity,
                    'duration_seconds': r.duration_seconds,
                    'details': r.details,
                    'error_message': r.error_message,
                    'timestamp': r.timestamp
                } for r in self.results
            ],
            'improvements_applied': {
                'performance': len(self.performance_improvements),
                'security': len(self.security_enhancements),
                'total_fixes': len(self.fixes_applied)
            }
        }
        
        # Save report
        report_path = Path(f"qa_logs/comprehensive_qa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        logger.info(f"📋 Comprehensive QA complete: {stats['passed']}/{stats['total_tests']} passed")
        logger.info(f"🏥 System health score: {health_score:.1f}%")
        logger.info(f"📄 Report saved: {report_path}")
        
        return comprehensive_report
    
    def _get_health_status(self, score: float) -> str:
        """Convert health score to status"""
        if score >= 95:
            return "excellent"
        elif score >= 85:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 50:
            return "poor"
        else:
            return "critical"

def main():
    """Main function for running comprehensive QA"""
    agent = ComprehensiveQAAgent()
    report = agent.run_comprehensive_qa()
    
    # Print summary
    print("\n" + "="*60)
    print("🔧 COMPREHENSIVE QA AGENT - SUMMARY")
    print("="*60)
    print(f"📊 Tests Run: {report['statistics']['total_tests']}")
    print(f"✅ Passed: {report['statistics']['passed']}")
    print(f"❌ Failed: {report['statistics']['failed']}")
    print(f"⚠️  Warnings: {report['statistics']['warnings']}")
    print(f"🏥 Health Score: {report['health_score']}% ({report['health_status']})")
    print(f"⏱️  Duration: {report['duration_seconds']:.2f} seconds")
    print("="*60)
    
    return report

if __name__ == "__main__":
    main()