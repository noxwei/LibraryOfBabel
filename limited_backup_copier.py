#!/usr/bin/env python3
"""
Limited EPUB Backup Copier - Test First 10 Files
=================================================

Test version that copies only first N files for validation.
"""

import sys
sys.path.append('/Users/weixiangzhang/Local_Dev/LibraryOfBabel')
from smart_backup_copier import SmartBackupCopier
import logging

class LimitedBackupCopier(SmartBackupCopier):
    """Limited version for testing first N files"""
    
    def __init__(self, *args, **kwargs):
        self.test_limit = kwargs.pop('test_limit', 10)
        super().__init__(*args, **kwargs)
    
    def identify_unique_files_to_copy(self, source_files, existing_prefixes):
        """Override to limit files for testing"""
        # Get full list first
        unique_files = super().identify_unique_files_to_copy(source_files, existing_prefixes)
        
        # Limit to test_limit for validation
        limited_files = unique_files[:self.test_limit]
        
        logging.getLogger(__name__).info(f"🧪 TEST MODE: Limiting to first {len(limited_files)} files")
        
        return limited_files

if __name__ == "__main__":
    copier = LimitedBackupCopier(test_limit=10)
    copier.run_backup_copy(dry_run=False)