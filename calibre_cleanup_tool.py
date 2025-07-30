#!/usr/bin/env python3
"""
Calibre Cleanup Tool
====================

Removes corrupted entries and audio file remnants from Calibre library
Based on audit results and Dr. Marcus Wong's quality standards

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
Quality Standards: Dr. Sarah Chen (陈雪芳) - PostgreSQL-First architecture
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

class CalibreCleanupTool:
    def __init__(self, calibre_library_path="/Users/weixiangzhang/Calibre Library"):
        self.calibre_library_path = calibre_library_path
        self.calibredb_path = "/Applications/calibre.app/Contents/MacOS/calibredb"
        self.cleanup_log = {
            "timestamp": datetime.now().isoformat(),
            "removed_books": [],
            "failed_removals": [],
            "total_removed": 0,
            "errors": []
        }
    
    def run_calibredb_command(self, args):
        """Execute calibredb command and return output"""
        cmd = [self.calibredb_path] + args + ["--library-path", self.calibre_library_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip(), True
        except subprocess.CalledProcessError as e:
            error_msg = f"Error running calibredb: {e.stderr.strip() if e.stderr else str(e)}"
            self.cleanup_log["errors"].append(error_msg)
            return error_msg, False
    
    def get_book_metadata(self, book_id):
        """Get detailed metadata for a book"""
        output, success = self.run_calibredb_command(["show_metadata", str(book_id)])
        if success:
            return output
        return None
    
    def remove_book(self, book_id, reason=""):
        """Remove a book from Calibre library"""
        print(f"🗑️  Removing book ID {book_id}: {reason}")
        
        # Get metadata before removal for logging
        metadata = self.get_book_metadata(book_id)
        title = "Unknown"
        if metadata:
            for line in metadata.split('\n'):
                if line.startswith('Title'):
                    title = line.split(':', 1)[1].strip()
                    break
        
        # Remove the book
        output, success = self.run_calibredb_command(["remove", str(book_id)])
        
        if success:
            self.cleanup_log["removed_books"].append({
                "id": book_id,
                "title": title,
                "reason": reason,
                "metadata": metadata
            })
            self.cleanup_log["total_removed"] += 1
            print(f"✅ Successfully removed book ID {book_id}: {title}")
            return True
        else:
            self.cleanup_log["failed_removals"].append({
                "id": book_id,
                "title": title,
                "reason": reason,
                "error": output
            })
            print(f"❌ Failed to remove book ID {book_id}: {output}")
            return False
    
    def remove_audio_file_remnants(self):
        """Remove books that are clearly audio file remnants"""
        print("🎵 Removing audio file remnants...")
        
        # Based on audit results, we have one definite audio file remnant
        audio_remnants = [
            {"id": "3", "reason": "Audio file remnant: TheNoiseofTime mp332"}
        ]
        
        for item in audio_remnants:
            self.remove_book(item["id"], item["reason"])
    
    def remove_severely_corrupted(self):
        """Remove books with severely corrupted metadata"""
        print("💥 Removing severely corrupted entries...")
        
        # Books with obviously broken metadata that can't be easily fixed
        corrupted_entries = []
        
        # Check for books with titles that are clearly broken
        output, success = self.run_calibredb_command(["list", "--fields", "id,title,authors"])
        if success:
            lines = output.split('\n')[1:]  # Skip header
            for line in lines:
                if line.strip():
                    parts = line.split(None, 2)
                    if len(parts) >= 2:
                        book_id = parts[0]
                        rest = ' '.join(parts[1:])
                        
                        # Look for clearly corrupted entries
                        if (len(rest) < 5 or  # Very short
                            rest.count(' ') < 2 or  # No proper title/author separation
                            any(char in rest for char in ['mp3', 'mp4', 'm4a']) or  # Audio extensions
                            rest.startswith('Unknown Unknown')):  # Double unknown
                            
                            corrupted_entries.append({
                                "id": book_id,
                                "reason": f"Severely corrupted metadata: {rest[:50]}..."
                            })
        
        for item in corrupted_entries:
            self.remove_book(item["id"], item["reason"])
    
    def verify_removal(self, book_id):
        """Verify that a book was actually removed"""
        output, success = self.run_calibredb_command(["show_metadata", str(book_id)])
        if success:
            return False  # Book still exists
        else:
            return True   # Book was removed (command failed)
    
    def run_cleanup(self, dry_run=False):
        """Run the cleanup process"""
        if dry_run:
            print("🧪 DRY RUN MODE - No books will be actually removed")
            return
        
        print("🚀 Starting Calibre Library Cleanup...")
        print(f"📚 Library Path: {self.calibre_library_path}")
        
        # Confirm with user
        response = input("⚠️  This will permanently remove corrupted books. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled by user")
            return
        
        # Step 1: Remove audio file remnants
        self.remove_audio_file_remnants()
        
        # Step 2: Remove severely corrupted entries
        self.remove_severely_corrupted()
        
        # Save cleanup log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"calibre_cleanup_log_{timestamp}.json"
        
        with open(log_file, 'w') as f:
            json.dump(self.cleanup_log, f, indent=2)
        
        # Print summary
        self.print_summary()
        print(f"📄 Cleanup log saved to: {log_file}")
    
    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "="*60)
        print("📊 CALIBRE CLEANUP SUMMARY")
        print("="*60)
        print(f"🗑️  Books Removed: {self.cleanup_log['total_removed']}")
        print(f"❌ Failed Removals: {len(self.cleanup_log['failed_removals'])}")
        print(f"⚠️  Errors: {len(self.cleanup_log['errors'])}")
        
        if self.cleanup_log["removed_books"]:
            print(f"\n📋 Removed Books:")
            for book in self.cleanup_log["removed_books"]:
                print(f"   ID {book['id']}: {book['title'][:50]}... ({book['reason']})")
        
        if self.cleanup_log["failed_removals"]:
            print(f"\n❌ Failed Removals:")
            for book in self.cleanup_log["failed_removals"]:
                print(f"   ID {book['id']}: {book['error']}")

if __name__ == "__main__":
    cleanup_tool = CalibreCleanupTool()
    
    # Check for dry run mode
    dry_run = "--dry-run" in sys.argv
    
    cleanup_tool.run_cleanup(dry_run=dry_run)