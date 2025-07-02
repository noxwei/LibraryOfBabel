#!/usr/bin/env python3
"""
LibraryOfBabel QA Agent
Comprehensive testing system for MAM automation process
"""

import sqlite3
import subprocess
import json
import time
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass

@dataclass
class QATestResult:
    """QA test result with detailed metrics"""
    test_name: str
    status: str  # 'passed', 'failed', 'warning'
    duration_seconds: float
    details: Dict
    error_message: Optional[str] = None
    timestamp: str = None
    
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
                # Parse torrent ID from response
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
            return {
                'success': False,
                'error': 'Transmission command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
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
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_torrents(self) -> Dict:
        """List all torrents in Transmission"""
        cmd = ['transmission-remote', '-l']
        
        if self.username and self.password:
            cmd.extend(['-n', f'{self.username}:{self.password}'])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'torrents': self._parse_torrent_list(result.stdout)
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_torrent_id(self, output: str) -> Optional[str]:
        """Extract torrent ID from transmission output"""
        lines = output.strip().split('\n')
        for line in lines:
            if 'torrent added' in line.lower():
                # Look for ID in the response
                import re
                match = re.search(r'#(\d+)', line)
                if match:
                    return match.group(1)
        return None
    
    def _parse_torrent_info(self, output: str) -> Dict:
        """Parse torrent info from transmission output"""
        info = {}
        lines = output.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
    
    def _parse_torrent_list(self, output: str) -> List[Dict]:
        """Parse torrent list from transmission output"""
        torrents = []
        lines = output.strip().split('\n')
        
        # Skip header lines
        data_lines = [line for line in lines if line and not line.startswith('ID')]
        
        for line in data_lines[1:]:  # Skip sum line
            parts = line.split()
            if len(parts) >= 9:
                torrents.append({
                    'id': parts[0],
                    'done': parts[1],
                    'have': parts[2],
                    'eta': parts[3],
                    'up': parts[4],
                    'down': parts[5],
                    'ratio': parts[6],
                    'status': parts[7],
                    'name': ' '.join(parts[8:])
                })
        
        return torrents

class LibraryOfBabelQAAgent:
    """Comprehensive QA testing for LibraryOfBabel MAM automation"""
    
    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.setup_logging()
        
        self.db_path = self.config.get('db_path', './audiobook_ebook_tracker.db')
        self.mam_downloads_dir = Path(self.config.get('mam_downloads_dir', './mam_downloads'))
        self.temp_download_dir = Path(self.config.get('temp_download_dir', '/Users/weixiangzhang/Media Holding Station/Temporary Download'))
        self.completed_downloads_dir = Path(self.config.get('completed_downloads_dir', '/Users/weixiangzhang/Media Holding Station/Ebooks'))
        
        self.transmission_client = TransmissionClient(self.config.get('transmission', {}))
        self.test_results = []
        
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'db_path': './audiobook_ebook_tracker.db',
            'mam_downloads_dir': './mam_downloads',
            'temp_download_dir': '/Users/weixiangzhang/Media Holding Station/Temporary Download',
            'completed_downloads_dir': '/Users/weixiangzhang/Media Holding Station/Ebooks',
            'transmission': {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': 9091,
                'username': None,
                'password': None
            },
            'web_frontend_port': 3000,
            'test_timeout': 300
        }
        
        if config_file and Path(config_file).exists():
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        
        return default_config
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path('./qa_logs')
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'qa_session_{timestamp}.log'
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def run_comprehensive_qa(self) -> Dict:
        """Run complete QA test suite"""
        self.logger.info("🚀 Starting LibraryOfBabel QA Testing Suite")
        
        qa_start_time = time.time()
        
        # Test categories
        test_categories = [
            ('Database Integrity', self._test_database_integrity),
            ('MAM Downloads Validation', self._test_mam_downloads),
            ('Transmission Integration', self._test_transmission_integration),
            ('Web Frontend', self._test_web_frontend),
            ('Completed Downloads Analysis', self._test_completed_downloads),
            ('System Performance', self._test_system_performance),
            ('Data Consistency', self._test_data_consistency)
        ]
        
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        for category_name, test_function in test_categories:
            self.logger.info(f"\n📋 Testing: {category_name}")
            
            try:
                category_results = test_function()
                
                for result in category_results:
                    self.test_results.append(result)
                    
                    if result.status == 'passed':
                        passed_tests += 1
                        self.logger.info(f"✅ {result.test_name}")
                    elif result.status == 'failed':
                        failed_tests += 1
                        self.logger.error(f"❌ {result.test_name}: {result.error_message}")
                    elif result.status == 'warning':
                        warning_tests += 1
                        self.logger.warning(f"⚠️ {result.test_name}: {result.error_message}")
                        
            except Exception as e:
                self.logger.error(f"💥 Critical error in {category_name}: {e}")
                failed_tests += 1
        
        total_duration = time.time() - qa_start_time
        
        # Generate comprehensive report
        qa_summary = {
            'timestamp': datetime.now().isoformat(),
            'total_duration_seconds': total_duration,
            'tests_passed': passed_tests,
            'tests_failed': failed_tests,
            'tests_warning': warning_tests,
            'total_tests': len(self.test_results),
            'success_rate': passed_tests / len(self.test_results) * 100 if self.test_results else 0,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'status': r.status,
                    'duration': r.duration_seconds,
                    'details': r.details,
                    'error': r.error_message
                } for r in self.test_results
            ]
        }
        
        # Save report
        report_file = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(qa_summary, f, indent=2)
        
        self.logger.info(f"\n📊 QA Summary:")
        self.logger.info(f"   Total Tests: {len(self.test_results)}")
        self.logger.info(f"   Passed: {passed_tests}")
        self.logger.info(f"   Failed: {failed_tests}")
        self.logger.info(f"   Warnings: {warning_tests}")
        self.logger.info(f"   Success Rate: {qa_summary['success_rate']:.1f}%")
        self.logger.info(f"   Duration: {total_duration:.1f}s")
        self.logger.info(f"   Report: {report_file}")
        
        return qa_summary
    
    def _test_database_integrity(self) -> List[QATestResult]:
        """Test database schema and data integrity"""
        results = []
        
        # Test 1: Database connectivity
        start_time = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM audiobooks")
                audiobook_count = cursor.fetchone()[0]
                
                results.append(QATestResult(
                    test_name="Database Connectivity",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details={"audiobook_count": audiobook_count}
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Database Connectivity",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        # Test 2: Required tables exist
        start_time = time.time()
        required_tables = ['audiobooks', 'ebooks', 'search_attempts', 'download_queue', 'collection_stats']
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = [table for table in required_tables if table not in existing_tables]
                
                if not missing_tables:
                    results.append(QATestResult(
                        test_name="Required Tables Exist",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={"tables": existing_tables}
                    ))
                else:
                    results.append(QATestResult(
                        test_name="Required Tables Exist",
                        status="failed",
                        duration_seconds=time.time() - start_time,
                        details={"missing_tables": missing_tables},
                        error_message=f"Missing tables: {missing_tables}"
                    ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Required Tables Exist",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        # Test 3: Data consistency checks
        start_time = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check for orphaned ebooks
                cursor.execute("""
                    SELECT COUNT(*) FROM ebooks e 
                    LEFT JOIN audiobooks a ON e.audiobook_id = a.album_id 
                    WHERE a.album_id IS NULL
                """)
                orphaned_ebooks = cursor.fetchone()[0]
                
                # Check for duplicate audiobooks
                cursor.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT clean_title, clean_author, COUNT(*) as cnt
                        FROM audiobooks 
                        GROUP BY clean_title, clean_author 
                        HAVING cnt > 1
                    )
                """)
                duplicate_audiobooks = cursor.fetchone()[0]
                
                consistency_issues = []
                if orphaned_ebooks > 0:
                    consistency_issues.append(f"{orphaned_ebooks} orphaned ebooks")
                if duplicate_audiobooks > 0:
                    consistency_issues.append(f"{duplicate_audiobooks} duplicate audiobooks")
                
                if not consistency_issues:
                    results.append(QATestResult(
                        test_name="Data Consistency",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={"orphaned_ebooks": orphaned_ebooks, "duplicate_audiobooks": duplicate_audiobooks}
                    ))
                else:
                    results.append(QATestResult(
                        test_name="Data Consistency",
                        status="warning",
                        duration_seconds=time.time() - start_time,
                        details={"issues": consistency_issues},
                        error_message=f"Consistency issues: {', '.join(consistency_issues)}"
                    ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Data Consistency",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def _test_mam_downloads(self) -> List[QATestResult]:
        """Test MAM download functionality"""
        results = []
        
        # Test 1: Download directory exists and is accessible
        start_time = time.time()
        try:
            self.mam_downloads_dir.mkdir(exist_ok=True)
            
            # Test write permissions
            test_file = self.mam_downloads_dir / 'qa_test.tmp'
            test_file.write_text('QA test')
            test_file.unlink()
            
            results.append(QATestResult(
                test_name="MAM Downloads Directory",
                status="passed",
                duration_seconds=time.time() - start_time,
                details={"path": str(self.mam_downloads_dir)}
            ))
        except Exception as e:
            results.append(QATestResult(
                test_name="MAM Downloads Directory",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={"path": str(self.mam_downloads_dir)},
                error_message=str(e)
            ))
        
        # Test 2: Validate existing torrent files
        start_time = time.time()
        try:
            torrent_files = list(self.mam_downloads_dir.glob('*.torrent'))
            valid_torrents = 0
            invalid_torrents = []
            
            for torrent_file in torrent_files:
                try:
                    # Basic validation - check file size and content
                    if torrent_file.stat().st_size > 0:
                        content = torrent_file.read_bytes()
                        if content.startswith(b'd8:announce'):  # Basic torrent file check
                            valid_torrents += 1
                        else:
                            invalid_torrents.append(torrent_file.name)
                    else:
                        invalid_torrents.append(f"{torrent_file.name} (empty)")
                except Exception as e:
                    invalid_torrents.append(f"{torrent_file.name} ({str(e)})")
            
            details = {
                "total_torrents": len(torrent_files),
                "valid_torrents": valid_torrents,
                "invalid_torrents": invalid_torrents
            }
            
            if not invalid_torrents:
                results.append(QATestResult(
                    test_name="Torrent Files Validation",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details=details
                ))
            else:
                results.append(QATestResult(
                    test_name="Torrent Files Validation",
                    status="warning",
                    duration_seconds=time.time() - start_time,
                    details=details,
                    error_message=f"Invalid torrents: {len(invalid_torrents)}"
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Torrent Files Validation",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def _test_transmission_integration(self) -> List[QATestResult]:
        """Test Transmission CLI integration"""
        results = []
        
        # Test 1: Transmission CLI availability
        start_time = time.time()
        try:
            result = subprocess.run(['transmission-remote', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                results.append(QATestResult(
                    test_name="Transmission CLI Available",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details={"version": result.stdout.strip()}
                ))
            else:
                results.append(QATestResult(
                    test_name="Transmission CLI Available",
                    status="failed",
                    duration_seconds=time.time() - start_time,
                    details={},
                    error_message=f"Command failed: {result.stderr}"
                ))
        except subprocess.TimeoutExpired:
            results.append(QATestResult(
                test_name="Transmission CLI Available",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message="Command timed out"
            ))
        except FileNotFoundError:
            results.append(QATestResult(
                test_name="Transmission CLI Available",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message="transmission-remote not found"
            ))
        
        # Test 2: Transmission daemon connectivity
        start_time = time.time()
        try:
            torrent_list = self.transmission_client.list_torrents()
            
            if torrent_list['success']:
                results.append(QATestResult(
                    test_name="Transmission Daemon Connection",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details={"torrent_count": len(torrent_list.get('torrents', []))}
                ))
            else:
                results.append(QATestResult(
                    test_name="Transmission Daemon Connection",
                    status="failed",
                    duration_seconds=time.time() - start_time,
                    details={},
                    error_message=torrent_list.get('error', 'Unknown error')
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Transmission Daemon Connection",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        # Test 3: Test torrent addition (if torrent files exist)
        start_time = time.time()
        try:
            torrent_files = list(self.mam_downloads_dir.glob('*.torrent'))
            
            if torrent_files:
                # Test with first torrent file
                test_torrent = torrent_files[0]
                add_result = self.transmission_client.add_torrent(
                    str(test_torrent), 
                    str(self.temp_download_dir)
                )
                
                if add_result['success']:
                    results.append(QATestResult(
                        test_name="Torrent Addition Test",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={
                            "test_torrent": test_torrent.name,
                            "torrent_id": add_result.get('torrent_id')
                        }
                    ))
                else:
                    results.append(QATestResult(
                        test_name="Torrent Addition Test",
                        status="failed",
                        duration_seconds=time.time() - start_time,
                        details={"test_torrent": test_torrent.name},
                        error_message=add_result.get('error', 'Unknown error')
                    ))
            else:
                results.append(QATestResult(
                    test_name="Torrent Addition Test",
                    status="warning",
                    duration_seconds=time.time() - start_time,
                    details={},
                    error_message="No torrent files available for testing"
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Torrent Addition Test",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def _test_web_frontend(self) -> List[QATestResult]:
        """Test web frontend functionality"""
        results = []
        
        # Test 1: Frontend server accessibility
        start_time = time.time()
        try:
            port = self.config.get('web_frontend_port', 3000)
            response = requests.get(f'http://localhost:{port}', timeout=10)
            
            if response.status_code == 200:
                results.append(QATestResult(
                    test_name="Web Frontend Accessibility",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details={"status_code": response.status_code, "port": port}
                ))
            else:
                results.append(QATestResult(
                    test_name="Web Frontend Accessibility",
                    status="failed",
                    duration_seconds=time.time() - start_time,
                    details={"status_code": response.status_code, "port": port},
                    error_message=f"HTTP {response.status_code}"
                ))
        except requests.exceptions.RequestException as e:
            results.append(QATestResult(
                test_name="Web Frontend Accessibility",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={"port": self.config.get('web_frontend_port', 3000)},
                error_message=str(e)
            ))
        
        # Test 2: API endpoints
        start_time = time.time()
        try:
            port = self.config.get('web_frontend_port', 3000)
            base_url = f'http://localhost:{port}'
            
            endpoints_to_test = [
                '/api/stats',
                '/api/audiobooks/missing',
                '/api/audiobooks/matched',
                '/api/searches/recent',
                '/api/downloads/queue'
            ]
            
            endpoint_results = {}
            
            for endpoint in endpoints_to_test:
                try:
                    response = requests.get(f'{base_url}{endpoint}', timeout=5)
                    endpoint_results[endpoint] = {
                        'status_code': response.status_code,
                        'response_time': response.elapsed.total_seconds()
                    }
                except Exception as e:
                    endpoint_results[endpoint] = {
                        'error': str(e)
                    }
            
            failed_endpoints = [ep for ep, result in endpoint_results.items() 
                               if 'error' in result or result.get('status_code') != 200]
            
            if not failed_endpoints:
                results.append(QATestResult(
                    test_name="API Endpoints",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details=endpoint_results
                ))
            else:
                results.append(QATestResult(
                    test_name="API Endpoints",
                    status="warning",
                    duration_seconds=time.time() - start_time,
                    details=endpoint_results,
                    error_message=f"Failed endpoints: {failed_endpoints}"
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="API Endpoints",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def _test_completed_downloads(self) -> List[QATestResult]:
        """Test analysis of completed downloads"""
        results = []
        
        # Test 1: Completed downloads directory
        start_time = time.time()
        try:
            if self.completed_downloads_dir.exists():
                ebook_files = list(self.completed_downloads_dir.rglob('*.epub')) + \
                             list(self.completed_downloads_dir.rglob('*.pdf')) + \
                             list(self.completed_downloads_dir.rglob('*.mobi'))
                
                file_stats = {
                    'epub': len(list(self.completed_downloads_dir.rglob('*.epub'))),
                    'pdf': len(list(self.completed_downloads_dir.rglob('*.pdf'))),
                    'mobi': len(list(self.completed_downloads_dir.rglob('*.mobi'))),
                    'total': len(ebook_files)
                }
                
                results.append(QATestResult(
                    test_name="Completed Downloads Analysis",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details=file_stats
                ))
            else:
                results.append(QATestResult(
                    test_name="Completed Downloads Analysis",
                    status="warning",
                    duration_seconds=time.time() - start_time,
                    details={"path": str(self.completed_downloads_dir)},
                    error_message="Completed downloads directory does not exist"
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Completed Downloads Analysis",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def _test_system_performance(self) -> List[QATestResult]:
        """Test system performance metrics"""
        results = []
        
        # Test 1: Database query performance
        start_time = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Test several common queries
                query_tests = [
                    ("Count audiobooks", "SELECT COUNT(*) FROM audiobooks"),
                    ("Count ebooks", "SELECT COUNT(*) FROM ebooks"),
                    ("Missing ebooks query", """
                        SELECT COUNT(*) FROM audiobooks a
                        LEFT JOIN ebooks e ON a.album_id = e.audiobook_id
                        WHERE e.audiobook_id IS NULL
                    """),
                    ("Complex join query", """
                        SELECT a.title, a.author, e.ebook_title, e.match_confidence
                        FROM audiobooks a
                        INNER JOIN ebooks e ON a.album_id = e.audiobook_id
                        WHERE e.match_confidence > 0.8
                        ORDER BY e.match_confidence DESC
                        LIMIT 10
                    """)
                ]
                
                query_performance = {}
                
                for query_name, query in query_tests:
                    query_start = time.time()
                    cursor.execute(query)
                    cursor.fetchall()
                    query_time = time.time() - query_start
                    query_performance[query_name] = query_time
                
                max_query_time = max(query_performance.values())
                avg_query_time = sum(query_performance.values()) / len(query_performance)
                
                if max_query_time < 1.0:  # All queries under 1 second
                    results.append(QATestResult(
                        test_name="Database Query Performance",
                        status="passed",
                        duration_seconds=time.time() - start_time,
                        details={
                            "query_times": query_performance,
                            "max_time": max_query_time,
                            "avg_time": avg_query_time
                        }
                    ))
                else:
                    results.append(QATestResult(
                        test_name="Database Query Performance",
                        status="warning",
                        duration_seconds=time.time() - start_time,
                        details={
                            "query_times": query_performance,
                            "max_time": max_query_time,
                            "avg_time": avg_query_time
                        },
                        error_message=f"Slow queries detected (max: {max_query_time:.2f}s)"
                    ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Database Query Performance",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results
    
    def _test_data_consistency(self) -> List[QATestResult]:
        """Test data consistency across the system"""
        results = []
        
        # Test 1: Torrent files vs database records
        start_time = time.time()
        try:
            # Get torrent files
            torrent_files = list(self.mam_downloads_dir.glob('*.torrent'))
            torrent_ids_from_files = set()
            
            for torrent_file in torrent_files:
                # Extract torrent ID from filename
                import re
                match = re.search(r'_(\d+)\.torrent$', torrent_file.name)
                if match:
                    torrent_ids_from_files.add(match.group(1))
            
            # Get torrent IDs from database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT mam_torrent_id FROM ebooks WHERE mam_torrent_id IS NOT NULL")
                torrent_ids_from_db = set(row[0] for row in cursor.fetchall())
            
            # Find mismatches
            files_not_in_db = torrent_ids_from_files - torrent_ids_from_db
            db_not_in_files = torrent_ids_from_db - torrent_ids_from_files
            
            consistency_details = {
                "torrent_files_count": len(torrent_files),
                "torrent_ids_from_files": len(torrent_ids_from_files),
                "torrent_ids_from_db": len(torrent_ids_from_db),
                "files_not_in_db": len(files_not_in_db),
                "db_not_in_files": len(db_not_in_files)
            }
            
            if not files_not_in_db and not db_not_in_files:
                results.append(QATestResult(
                    test_name="Torrent Files vs Database Consistency",
                    status="passed",
                    duration_seconds=time.time() - start_time,
                    details=consistency_details
                ))
            else:
                results.append(QATestResult(
                    test_name="Torrent Files vs Database Consistency",
                    status="warning",
                    duration_seconds=time.time() - start_time,
                    details=consistency_details,
                    error_message=f"Mismatches found: {len(files_not_in_db)} files not in DB, {len(db_not_in_files)} DB records without files"
                ))
        except Exception as e:
            results.append(QATestResult(
                test_name="Torrent Files vs Database Consistency",
                status="failed",
                duration_seconds=time.time() - start_time,
                details={},
                error_message=str(e)
            ))
        
        return results

def main():
    """Run QA testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LibraryOfBabel QA Testing Agent')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--quick', action='store_true', help='Run quick tests only')
    parser.add_argument('--category', help='Run specific test category only')
    
    args = parser.parse_args()
    
    # Initialize QA agent
    qa_agent = LibraryOfBabelQAAgent(args.config)
    
    print("🔬 LibraryOfBabel QA Agent")
    print("=" * 50)
    
    # Run comprehensive QA
    qa_results = qa_agent.run_comprehensive_qa()
    
    # Exit with appropriate code
    if qa_results['tests_failed'] == 0:
        print("🎉 All tests passed!")
        exit(0)
    else:
        print(f"⚠️ {qa_results['tests_failed']} tests failed")
        exit(1)

if __name__ == "__main__":
    main()