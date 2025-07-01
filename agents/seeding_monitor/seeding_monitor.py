#!/usr/bin/env python3
"""
MAM Seeding Monitor
Ensures compliance with 2-week minimum seeding requirement for all downloaded torrents
"""

import sqlite3
import subprocess
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

@dataclass
class SeedingRecord:
    """Track seeding compliance for downloaded torrents"""
    torrent_id: str
    transmission_id: str
    mam_torrent_id: str
    title: str
    download_date: datetime
    seeding_start_date: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    status: str = 'downloading'  # downloading, seeding, completed, removed
    ratio: float = 0.0
    upload_bytes: int = 0
    download_bytes: int = 0
    peers_connected: int = 0
    seeding_days: float = 0.0
    compliance_status: str = 'pending'  # pending, compliant, non_compliant, exempt
    
    @property
    def days_since_download(self) -> float:
        """Calculate days since download started"""
        if self.download_date:
            return (datetime.now() - self.download_date).total_seconds() / 86400
        return 0.0
    
    @property
    def required_seeding_end_date(self) -> datetime:
        """Calculate when 2-week seeding requirement ends"""
        if self.seeding_start_date:
            return self.seeding_start_date + timedelta(days=14)
        elif self.download_date:
            # Assume seeding started same day as download completed
            return self.download_date + timedelta(days=14)
        return datetime.now() + timedelta(days=14)
    
    @property
    def is_seeding_requirement_met(self) -> bool:
        """Check if 2-week seeding requirement is satisfied"""
        return (
            self.seeding_days >= 14.0 or 
            datetime.now() >= self.required_seeding_end_date
        )

class TransmissionSeedingMonitor:
    """Monitor and enforce seeding compliance through Transmission"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 9091)
        self.username = config.get('username')
        self.password = config.get('password')
        self.db_path = config.get('db_path', './audiobook_ebook_tracker.db')
        
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.init_seeding_database()
    
    def setup_logging(self):
        """Setup logging for seeding monitor"""
        log_dir = Path('./seeding_logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'seeding_monitor.log'),
                logging.StreamHandler()
            ]
        )
    
    def init_seeding_database(self):
        """Initialize seeding tracking tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                -- Seeding compliance tracking
                CREATE TABLE IF NOT EXISTS seeding_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    torrent_id TEXT UNIQUE,
                    transmission_id TEXT,
                    mam_torrent_id TEXT,
                    title TEXT,
                    download_date DATETIME,
                    seeding_start_date DATETIME,
                    last_checked DATETIME,
                    status TEXT DEFAULT 'downloading',
                    ratio REAL DEFAULT 0.0,
                    upload_bytes INTEGER DEFAULT 0,
                    download_bytes INTEGER DEFAULT 0,
                    peers_connected INTEGER DEFAULT 0,
                    seeding_days REAL DEFAULT 0.0,
                    compliance_status TEXT DEFAULT 'pending',
                    notes TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Seeding violations log
                CREATE TABLE IF NOT EXISTS seeding_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    torrent_id TEXT,
                    violation_type TEXT,
                    violation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_date DATETIME,
                    resolution_notes TEXT
                );
                
                -- Seeding compliance summary
                CREATE TABLE IF NOT EXISTS seeding_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_date DATE UNIQUE,
                    total_torrents INTEGER,
                    seeding_torrents INTEGER,
                    compliant_torrents INTEGER,
                    non_compliant_torrents INTEGER,
                    pending_torrents INTEGER,
                    total_ratio REAL,
                    total_uploaded_gb REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_seeding_records_torrent ON seeding_records (torrent_id);
                CREATE INDEX IF NOT EXISTS idx_seeding_records_status ON seeding_records (status);
                CREATE INDEX IF NOT EXISTS idx_seeding_records_compliance ON seeding_records (compliance_status);
                CREATE INDEX IF NOT EXISTS idx_seeding_violations_torrent ON seeding_violations (torrent_id);
            """)
    
    def run_transmission_command(self, args: List[str]) -> Dict:
        """Execute transmission-remote command"""
        cmd = ['transmission-remote']
        
        if self.username and self.password:
            cmd.extend(['-n', f'{self.username}:{self.password}'])
        
        cmd.extend(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_all_torrents(self) -> List[Dict]:
        """Get detailed info for all torrents in Transmission"""
        result = self.run_transmission_command(['-l'])
        
        if not result['success']:
            self.logger.error(f"Failed to get torrent list: {result.get('error', result.get('stderr'))}")
            return []
        
        torrents = []
        lines = result['stdout'].strip().split('\n')
        
        # Skip header and sum lines
        for line in lines[1:-1]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 9:
                    torrent_id = parts[0].strip('*')
                    
                    # Get detailed info for each torrent
                    detailed_info = self.get_torrent_details(torrent_id)
                    if detailed_info:
                        torrents.append(detailed_info)
        
        return torrents
    
    def get_torrent_details(self, torrent_id: str) -> Optional[Dict]:
        """Get detailed information for specific torrent"""
        result = self.run_transmission_command(['-t', torrent_id, '-i'])
        
        if not result['success']:
            return None
        
        details = {}
        lines = result['stdout'].strip().split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                details[key.strip()] = value.strip()
        
        # Parse key metrics
        try:
            details['id'] = torrent_id
            details['ratio_parsed'] = float(details.get('Ratio', '0').replace(',', ''))
            details['percent_done'] = float(details.get('Percent Done', '0%').replace('%', ''))
            
            # Parse upload/download bytes
            upload_str = details.get('Uploaded', '0 B')
            download_str = details.get('Downloaded', '0 B')
            
            details['upload_bytes'] = self.parse_bytes(upload_str)
            details['download_bytes'] = self.parse_bytes(download_str)
            
            # Parse peers
            details['peers_connected'] = int(details.get('Peers', '0').split()[0])
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Error parsing torrent details for {torrent_id}: {e}")
        
        return details
    
    def parse_bytes(self, size_str: str) -> int:
        """Parse size string like '1.2 GB' to bytes"""
        if not size_str or size_str == 'None':
            return 0
        
        parts = size_str.split()
        if len(parts) != 2:
            return 0
        
        try:
            value = float(parts[0].replace(',', ''))
            unit = parts[1].upper()
            
            multipliers = {
                'B': 1,
                'KB': 1024,
                'MB': 1024**2,
                'GB': 1024**3,
                'TB': 1024**4
            }
            
            return int(value * multipliers.get(unit, 1))
        except (ValueError, KeyError):
            return 0
    
    def update_seeding_records(self):
        """Update seeding records with current Transmission status"""
        self.logger.info("🔍 Updating seeding records from Transmission...")
        
        transmission_torrents = self.get_all_torrents()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for torrent in transmission_torrents:
                torrent_id = torrent.get('id')
                torrent_name = torrent.get('Name', 'Unknown')
                
                # Check if this is a MAM torrent (look for corresponding ebook record)
                cursor.execute("""
                    SELECT mam_torrent_id, ebook_title 
                    FROM ebooks 
                    WHERE local_file_path LIKE ? OR ebook_title LIKE ?
                """, (f'%{torrent_name}%', f'%{torrent_name}%'))
                
                ebook_match = cursor.fetchone()
                mam_torrent_id = ebook_match[0] if ebook_match else None
                
                # Determine status
                percent_done = torrent.get('percent_done', 0)
                transmission_status = torrent.get('Status', '').lower()
                
                if percent_done >= 100 and 'seed' in transmission_status:
                    status = 'seeding'
                elif percent_done >= 100:
                    status = 'completed'
                elif percent_done > 0:
                    status = 'downloading'
                else:
                    status = 'queued'
                
                # Calculate seeding time
                seeding_start = None
                if status == 'seeding':
                    # Check if we have a record
                    cursor.execute("SELECT seeding_start_date FROM seeding_records WHERE transmission_id = ?", (torrent_id,))
                    existing_record = cursor.fetchone()
                    
                    if existing_record and existing_record[0]:
                        seeding_start = datetime.fromisoformat(existing_record[0])
                    else:
                        seeding_start = datetime.now()
                
                seeding_days = 0.0
                if seeding_start:
                    seeding_days = (datetime.now() - seeding_start).total_seconds() / 86400
                
                # Update or insert seeding record
                cursor.execute("""
                    INSERT OR REPLACE INTO seeding_records (
                        torrent_id, transmission_id, mam_torrent_id, title,
                        download_date, seeding_start_date, last_checked,
                        status, ratio, upload_bytes, download_bytes,
                        peers_connected, seeding_days, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"transmission_{torrent_id}",
                    torrent_id,
                    mam_torrent_id,
                    torrent_name,
                    datetime.now().isoformat(),  # Approximate, should be tracked from download
                    seeding_start.isoformat() if seeding_start else None,
                    datetime.now().isoformat(),
                    status,
                    torrent.get('ratio_parsed', 0.0),
                    torrent.get('upload_bytes', 0),
                    torrent.get('download_bytes', 0),
                    torrent.get('peers_connected', 0),
                    seeding_days,
                    datetime.now().isoformat()
                ))
            
            conn.commit()
        
        self.logger.info(f"✅ Updated {len(transmission_torrents)} torrent records")
    
    def check_seeding_compliance(self) -> Dict:
        """Check seeding compliance for all torrents"""
        self.logger.info("🔍 Checking seeding compliance...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update compliance status for all records
            cursor.execute("""
                UPDATE seeding_records 
                SET compliance_status = CASE
                    WHEN seeding_days >= 14.0 THEN 'compliant'
                    WHEN status = 'seeding' AND seeding_days < 14.0 THEN 'pending'
                    WHEN status != 'seeding' AND seeding_days < 14.0 THEN 'non_compliant'
                    ELSE 'pending'
                END,
                updated_at = ?
            """, (datetime.now().isoformat(),))
            
            # Get compliance summary
            cursor.execute("""
                SELECT 
                    compliance_status,
                    COUNT(*) as count,
                    AVG(ratio) as avg_ratio,
                    SUM(upload_bytes) as total_upload
                FROM seeding_records
                GROUP BY compliance_status
            """)
            
            compliance_summary = {}
            for row in cursor.fetchall():
                status, count, avg_ratio, total_upload = row
                compliance_summary[status] = {
                    'count': count,
                    'avg_ratio': avg_ratio or 0.0,
                    'total_upload_gb': (total_upload or 0) / (1024**3)
                }
            
            # Find violations
            cursor.execute("""
                SELECT torrent_id, transmission_id, title, seeding_days, status, ratio
                FROM seeding_records
                WHERE compliance_status = 'non_compliant'
                ORDER BY seeding_days ASC
            """)
            
            violations = []
            for row in cursor.fetchall():
                torrent_id, transmission_id, title, seeding_days, status, ratio = row
                violations.append({
                    'torrent_id': torrent_id,
                    'transmission_id': transmission_id,
                    'title': title,
                    'seeding_days': seeding_days,
                    'status': status,
                    'ratio': ratio,
                    'days_remaining': 14.0 - seeding_days
                })
            
            # Log violations
            for violation in violations:
                cursor.execute("""
                    INSERT OR IGNORE INTO seeding_violations (
                        torrent_id, violation_type, description
                    ) VALUES (?, ?, ?)
                """, (
                    violation['torrent_id'],
                    'insufficient_seeding',
                    f"Only seeded for {violation['seeding_days']:.1f} days (requirement: 14 days)"
                ))
            
            conn.commit()
        
        # Create summary report
        total_torrents = sum(summary['count'] for summary in compliance_summary.values())
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_torrents': total_torrents,
            'compliance_summary': compliance_summary,
            'violations': violations,
            'compliance_rate': (compliance_summary.get('compliant', {}).get('count', 0) / total_torrents * 100) if total_torrents > 0 else 0,
            'total_upload_gb': sum(summary['total_upload_gb'] for summary in compliance_summary.values())
        }
        
        self.logger.info(f"📊 Compliance Check Results:")
        self.logger.info(f"   Total torrents: {total_torrents}")
        self.logger.info(f"   Compliant: {compliance_summary.get('compliant', {}).get('count', 0)}")
        self.logger.info(f"   Pending: {compliance_summary.get('pending', {}).get('count', 0)}")
        self.logger.info(f"   Non-compliant: {compliance_summary.get('non_compliant', {}).get('count', 0)}")
        self.logger.info(f"   Compliance rate: {report['compliance_rate']:.1f}%")
        
        if violations:
            self.logger.warning(f"⚠️ {len(violations)} seeding violations found!")
            for violation in violations[:5]:  # Show first 5
                self.logger.warning(f"   - {violation['title']}: {violation['seeding_days']:.1f}/14 days")
        
        return report
    
    def enforce_seeding_policy(self, remove_non_compliant: bool = False):
        """Enforce seeding policy (optionally remove non-compliant torrents)"""
        self.logger.info("🛡️ Enforcing seeding policy...")
        
        if remove_non_compliant:
            self.logger.warning("⚠️ Removing non-compliant torrents is DANGEROUS and not recommended for MAM!")
            self.logger.warning("   This could hurt your ratio and standing. Manual review recommended.")
            return
        
        # For now, just log warnings
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT transmission_id, title, seeding_days
                FROM seeding_records
                WHERE compliance_status = 'non_compliant'
                AND status != 'seeding'
            """)
            
            for row in cursor.fetchall():
                transmission_id, title, seeding_days = row
                self.logger.warning(f"🚨 SEEDING VIOLATION: {title} (ID: {transmission_id}) - only seeded {seeding_days:.1f}/14 days")
    
    def generate_seeding_report(self, output_file: str = None) -> str:
        """Generate comprehensive seeding compliance report"""
        if not output_file:
            output_file = f"seeding_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        self.update_seeding_records()
        compliance_report = self.check_seeding_compliance()
        
        # Add detailed torrent information
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT torrent_id, transmission_id, mam_torrent_id, title,
                       download_date, seeding_start_date, status, ratio,
                       upload_bytes, download_bytes, seeding_days, compliance_status
                FROM seeding_records
                ORDER BY compliance_status, seeding_days DESC
            """)
            
            detailed_records = []
            for row in cursor.fetchall():
                record = {
                    'torrent_id': row[0],
                    'transmission_id': row[1],
                    'mam_torrent_id': row[2],
                    'title': row[3],
                    'download_date': row[4],
                    'seeding_start_date': row[5],
                    'status': row[6],
                    'ratio': row[7],
                    'upload_gb': (row[8] or 0) / (1024**3),
                    'download_gb': (row[9] or 0) / (1024**3),
                    'seeding_days': row[10],
                    'compliance_status': row[11]
                }
                detailed_records.append(record)
        
        full_report = {
            **compliance_report,
            'detailed_records': detailed_records,
            'seeding_policy': {
                'minimum_days': 14,
                'description': 'MAM requires minimum 2 weeks (14 days) seeding',
                'consequences': 'Failure to seed properly can result in account penalties'
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(full_report, f, indent=2, default=str)
        
        self.logger.info(f"📋 Seeding report saved to: {output_file}")
        return output_file

def main():
    """Run seeding monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MAM Seeding Compliance Monitor')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--check-only', action='store_true', help='Only check compliance, no updates')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    
    args = parser.parse_args()
    
    # Default configuration
    config = {
        'host': 'localhost',
        'port': 9091,
        'username': None,
        'password': None,
        'db_path': './audiobook_ebook_tracker.db'
    }
    
    # Load configuration if provided
    if args.config and Path(args.config).exists():
        with open(args.config, 'r') as f:
            file_config = json.load(f)
            config.update(file_config.get('transmission', {}))
    
    print("🛡️ MAM Seeding Compliance Monitor")
    print("=" * 40)
    print("📋 2-WEEK SEEDING REQUIREMENT ENFORCED")
    print("=" * 40)
    
    monitor = TransmissionSeedingMonitor(config)
    
    if args.continuous:
        print("🔄 Starting continuous monitoring...")
        while True:
            try:
                monitor.update_seeding_records()
                monitor.check_seeding_compliance()
                time.sleep(3600)  # Check every hour
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
    elif args.report:
        report_file = monitor.generate_seeding_report()
        print(f"📋 Report generated: {report_file}")
    elif args.check_only:
        monitor.check_seeding_compliance()
    else:
        monitor.update_seeding_records()
        monitor.check_seeding_compliance()
        monitor.enforce_seeding_policy()

if __name__ == "__main__":
    main()