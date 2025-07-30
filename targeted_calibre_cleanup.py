#!/usr/bin/env python3
"""
Targeted Calibre Cleanup Tool
==============================

Removes only the specific problematic entries identified in the audit
Based on Dr. Marcus Wong & Dr. Sarah Chen's precision approach

Author: Dr. Marcus Wong (王志明) - Calibre EPUB Library Architect
"""

import subprocess
import json
import sys
from datetime import datetime

class TargetedCalibreCleanup:
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
    
    def remove_unknown_authors(self):
        """Remove the 9 specific books with Unknown authors from audit"""
        print("👤 Removing books with Unknown authors...")
        
        # These are the specific IDs from our audit report
        unknown_author_ids = [7, 9, 218, 455, 456, 1097, 1424, 1452]
        # Note: ID 3 was already removed (the audio file)
        
        for book_id in unknown_author_ids:
            # Verify it still has Unknown author before removing
            metadata = self.get_book_metadata(book_id)
            if metadata and "Unknown" in metadata:
                self.remove_book(book_id, "Unknown author")
            else:
                print(f"ℹ️  Book ID {book_id} no longer has Unknown author, skipping")
    
    def check_library_after_cleanup(self):
        """Check library status after cleanup"""
        print("📊 Checking library status after cleanup...")
        
        # Count total books
        output, success = self.run_calibredb_command(["list", "--fields", "id"])
        if success:
            lines = output.split('\n')[1:]  # Skip header
            total_books = len([line for line in lines if line.strip()])
            print(f"📚 Total books remaining: {total_books}")
        
        # Check for remaining Unknown authors
        output, success = self.run_calibredb_command(["list", "--search", "authors:Unknown", "--fields", "id,title,authors"])
        if success:
            lines = output.split('\n')[1:]  # Skip header
            unknown_count = len([line for line in lines if line.strip()])
            print(f"👤 Books with Unknown authors remaining: {unknown_count}")
    
    def run_targeted_cleanup(self, dry_run=False):
        """Run the targeted cleanup process"""
        if dry_run:
            print("🧪 DRY RUN MODE - No books will be actually removed")
            print("Would remove books with these issues:")
            print("- Unknown authors (8 books)")
            return
        
        print("🚀 Starting Targeted Calibre Library Cleanup...")
        print(f"📚 Library Path: {self.calibre_library_path}")
        
        # Confirm with user
        response = input("⚠️  This will remove books with Unknown authors. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled by user")
            return
        
        # Remove books with Unknown authors
        self.remove_unknown_authors()
        
        # Check library status
        self.check_library_after_cleanup()
        
        # Save cleanup log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"targeted_cleanup_log_{timestamp}.json"
        
        with open(log_file, 'w') as f:
            json.dump(self.cleanup_log, f, indent=2)
        
        # Print summary
        self.print_summary()
        print(f"📄 Cleanup log saved to: {log_file}")
    
    def print_summary(self):
        """Print cleanup summary"""
        print("\n" + "="*60)
        print("📊 TARGETED CLEANUP SUMMARY")
        print("="*60)
        print(f"🗑️  Books Removed: {self.cleanup_log['total_removed']}")
        print(f"❌ Failed Removals: {len(self.cleanup_log['failed_removals'])}")
        print(f"⚠️  Errors: {len(self.cleanup_log['errors'])}")
        
        if self.cleanup_log["removed_books"]:
            print(f"\n📋 Removed Books:")
            for book in self.cleanup_log["removed_books"]:
                print(f"   ID {book['id']}: {book['title'][:50]}...")
        
        if self.cleanup_log["failed_removals"]:
            print(f"\n❌ Failed Removals:")
            for book in self.cleanup_log["failed_removals"]:
                print(f"   ID {book['id']}: {book['error']}")

if __name__ == "__main__":
    cleanup_tool = TargetedCalibreCleanup()
    
    # Check for dry run mode
    dry_run = "--dry-run" in sys.argv
    
    cleanup_tool.run_targeted_cleanup(dry_run=dry_run)