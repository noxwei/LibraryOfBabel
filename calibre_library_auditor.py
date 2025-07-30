#!/usr/bin/env python3
"""
Calibre Library Auditor
========================

Identifies corrupted entries, Unknown authors, audio file remnants, and metadata issues
Based on Dr. Marcus Wong & Dr. Sarah Chen's quality standards

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
Quality Standards: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First architecture
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import datetime

class CalibreLibraryAuditor:
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library"):
        self.calibre_library_path = calibre_library_path
        self.calibredb_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "unknown_authors": [],
            "audio_file_remnants": [],
            "truncated_titles": [],
            "corrupted_metadata": [],
            "quality_issues": [],
            "total_books": 0,
            "issues_found": 0
        }
    
    def run_calibredb_command(self, args):
        """Execute calibredb command and return output"""
        cmd = [self.calibredb_path] + args + ["--library-path", self.calibre_library_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running calibredb: {e}")
            return None
    
    def audit_unknown_authors(self):
        """Find all books with Unknown authors"""
        print("🔍 Auditing Unknown authors...")
        output = self.run_calibredb_command(["list", "--search", "authors:Unknown", "--fields", "id,title,authors"])
        
        if output:
            lines = output.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split(None, 2)  # Split into max 3 parts
                    if len(parts) >= 3:
                        book_id = parts[0]
                        # Title is everything except the last part (authors)
                        title_and_authors = ' '.join(parts[1:])
                        # Find "Unknown" in the line to separate title from authors
                        if "Unknown" in title_and_authors:
                            title = title_and_authors.replace("Unknown", "").strip()
                            self.audit_results["unknown_authors"].append({
                                "id": book_id,
                                "title": title,
                                "issue": "Unknown author"
                            })
    
    def audit_audio_file_remnants(self):
        """Find entries that look like audio files"""
        print("🔍 Auditing audio file remnants...")
        output = self.run_calibredb_command(["list", "--fields", "id,title,authors"])
        
        if output:
            lines = output.split('\n')[1:]  # Skip header
            audio_patterns = [r'mp3', r'mp4', r'm4a', r'wav', r'flac', r'aac']
            
            for line in lines:
                if line.strip():
                    for pattern in audio_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            parts = line.split(None, 2)
                            if len(parts) >= 2:
                                book_id = parts[0]
                                title = parts[1] if len(parts) > 1 else "Unknown"
                                self.audit_results["audio_file_remnants"].append({
                                    "id": book_id,
                                    "title": title,
                                    "issue": f"Contains audio file pattern: {pattern}",
                                    "line": line
                                })
                                break
    
    def audit_truncated_titles(self):
        """Find titles that appear truncated"""
        print("🔍 Auditing truncated titles...")
        output = self.run_calibredb_command(["list", "--fields", "id,title,authors"])
        
        if output:
            lines = output.split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    # Look for titles that end abruptly or are very short
                    parts = line.split(None, 2)
                    if len(parts) >= 2:
                        book_id = parts[0]
                        title_part = parts[1] if len(parts) > 1 else ""
                        
                        # Check for truncation indicators
                        if (len(title_part) < 10 or 
                            title_part.endswith(' ') or 
                            not title_part or
                            re.search(r'\w{3,}$', title_part) is None):  # Ends with partial word
                            
                            self.audit_results["truncated_titles"].append({
                                "id": book_id,
                                "title": title_part,
                                "issue": "Potentially truncated title",
                                "line": line
                            })
    
    def audit_metadata_quality(self):
        """Check overall metadata quality"""
        print("🔍 Auditing metadata quality...")
        output = self.run_calibredb_command(["list", "--fields", "id,title,authors,series,tags"])
        
        if output:
            lines = output.split('\n')
            self.audit_results["total_books"] = len(lines) - 1  # Exclude header
            
            for line in lines[1:]:  # Skip header
                if line.strip():
                    parts = line.split(None, 2)
                    if len(parts) >= 1:
                        book_id = parts[0]
                        
                        # Check for quality issues
                        quality_issues = []
                        
                        if "Unknown" in line:
                            quality_issues.append("Unknown metadata")
                        
                        if len(line) < 20:
                            quality_issues.append("Very short metadata")
                        
                        if not re.search(r'[A-Za-z]{3,}', line):
                            quality_issues.append("No readable text")
                        
                        if quality_issues:
                            self.audit_results["quality_issues"].append({
                                "id": book_id,
                                "issues": quality_issues,
                                "line": line
                            })
    
    def get_detailed_metadata(self, book_id):
        """Get detailed metadata for a specific book"""
        output = self.run_calibredb_command(["show_metadata", str(book_id)])
        return output
    
    def run_full_audit(self):
        """Run complete audit of Calibre library"""
        print("🚀 Starting Calibre Library Audit...")
        print(f"📚 Library Path: {self.calibre_library_path}")
        
        self.audit_unknown_authors()
        self.audit_audio_file_remnants()
        self.audit_truncated_titles()
        self.audit_metadata_quality()
        
        # Calculate total issues
        self.audit_results["issues_found"] = (
            len(self.audit_results["unknown_authors"]) +
            len(self.audit_results["audio_file_remnants"]) +
            len(self.audit_results["truncated_titles"]) +
            len(self.audit_results["quality_issues"])
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"calibre_audit_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)
        
        self.print_summary()
        print(f"📄 Detailed report saved to: {report_file}")
        
        return self.audit_results
    
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "="*60)
        print("📊 CALIBRE LIBRARY AUDIT SUMMARY")
        print("="*60)
        print(f"📚 Total Books: {self.audit_results['total_books']}")
        print(f"❌ Total Issues Found: {self.audit_results['issues_found']}")
        print(f"👤 Unknown Authors: {len(self.audit_results['unknown_authors'])}")
        print(f"🎵 Audio File Remnants: {len(self.audit_results['audio_file_remnants'])}")
        print(f"✂️  Truncated Titles: {len(self.audit_results['truncated_titles'])}")
        print(f"⚠️  Quality Issues: {len(self.audit_results['quality_issues'])}")
        
        if self.audit_results["issues_found"] > 0:
            print(f"\n🔧 Cleanup required for {self.audit_results['issues_found']} problematic entries")
        else:
            print(f"\n✅ Library appears clean!")

if __name__ == "__main__":
    auditor = CalibreLibraryAuditor()
    auditor.run_full_audit()