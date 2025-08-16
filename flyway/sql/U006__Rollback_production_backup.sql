-- LibraryOfBabel Production Function Backup Rollback
-- U006: Remove function backup system if needed
-- Date: 2025-08-16

-- Drop backup functions
DROP FUNCTION IF EXISTS function_backups.backup_production_functions(TEXT, TEXT, TEXT);
DROP FUNCTION IF EXISTS function_backups.restore_functions_from_backup(INTEGER);
DROP FUNCTION IF EXISTS function_backups.list_backups();

-- Drop backup table
DROP TABLE IF EXISTS function_backups.deployment_backups;

-- Drop backup schema (only if empty)
DROP SCHEMA IF EXISTS function_backups CASCADE;

-- Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'U006 Rollback completed: Production function backup system removed';
END $$;