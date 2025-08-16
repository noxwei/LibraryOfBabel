-- LibraryOfBabel Production Function Backup Migration
-- V006: Create backup schema and backup all current production functions
-- Date: 2025-08-16
-- Purpose: Safe CI/CD deployment with rollback capability

-- Create backup schema for production functions
CREATE SCHEMA IF NOT EXISTS function_backups;

-- Create backup tracking table
CREATE TABLE IF NOT EXISTS function_backups.deployment_backups (
    backup_id SERIAL PRIMARY KEY,
    backup_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployment_version TEXT,
    git_commit TEXT,
    backup_description TEXT,
    backed_up_functions INTEGER DEFAULT 0
);

-- Function to backup all existing functions to backup schema
CREATE OR REPLACE FUNCTION function_backups.backup_production_functions(
    p_deployment_version TEXT DEFAULT 'unknown',
    p_git_commit TEXT DEFAULT 'unknown',
    p_description TEXT DEFAULT 'Automated CI/CD backup'
) RETURNS INTEGER AS $$
DECLARE
    func_record RECORD;
    backup_count INTEGER := 0;
    backup_id INTEGER;
    function_def TEXT;
BEGIN
    -- Create new backup entry
    INSERT INTO function_backups.deployment_backups 
    (deployment_version, git_commit, backup_description)
    VALUES (p_deployment_version, p_git_commit, p_description)
    RETURNING deployment_backups.backup_id INTO backup_id;
    
    -- Log the backup start
    RAISE NOTICE 'Starting production function backup for deployment: %', p_deployment_version;
    
    -- Backup all user-defined functions from public schema
    FOR func_record IN 
        SELECT 
            p.proname as function_name,
            pg_get_functiondef(p.oid) as function_definition,
            n.nspname as schema_name
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        AND p.proname NOT LIKE 'pg_%'
        AND p.proname NOT LIKE 'information_schema_%'
        AND p.proowner != 10  -- Exclude system functions
    LOOP
        BEGIN
            -- Create backup function with timestamped name
            function_def := REPLACE(
                func_record.function_definition, 
                'CREATE OR REPLACE FUNCTION public.' || func_record.function_name,
                'CREATE OR REPLACE FUNCTION function_backups.' || func_record.function_name || '_backup_' || backup_id
            );
            
            -- Execute the backup function creation
            EXECUTE function_def;
            
            backup_count := backup_count + 1;
            
            RAISE NOTICE 'Backed up function: %', func_record.function_name;
            
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to backup function %: %', func_record.function_name, SQLERRM;
        END;
    END LOOP;
    
    -- Update backup record with count
    UPDATE function_backups.deployment_backups 
    SET backed_up_functions = backup_count 
    WHERE deployment_backups.backup_id = backup_id;
    
    RAISE NOTICE 'Production function backup completed: % functions backed up', backup_count;
    
    RETURN backup_count;
END;
$$ LANGUAGE plpgsql;

-- Function to restore functions from backup
CREATE OR REPLACE FUNCTION function_backups.restore_functions_from_backup(
    p_backup_id INTEGER
) RETURNS INTEGER AS $$
DECLARE
    func_record RECORD;
    restore_count INTEGER := 0;
    function_def TEXT;
    original_name TEXT;
BEGIN
    RAISE NOTICE 'Starting function restore from backup ID: %', p_backup_id;
    
    -- Get all backup functions for this backup ID
    FOR func_record IN 
        SELECT 
            p.proname as backup_function_name,
            pg_get_functiondef(p.oid) as function_definition
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'function_backups'
        AND p.proname LIKE '%_backup_' || p_backup_id
    LOOP
        BEGIN
            -- Extract original function name
            original_name := REGEXP_REPLACE(
                func_record.backup_function_name, 
                '_backup_\d+$', 
                ''
            );
            
            -- Create restore function definition
            function_def := REPLACE(
                func_record.function_definition,
                'CREATE OR REPLACE FUNCTION function_backups.' || func_record.backup_function_name,
                'CREATE OR REPLACE FUNCTION public.' || original_name
            );
            
            -- Execute the restore
            EXECUTE function_def;
            
            restore_count := restore_count + 1;
            
            RAISE NOTICE 'Restored function: %', original_name;
            
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'Failed to restore function %: %', original_name, SQLERRM;
        END;
    END LOOP;
    
    RAISE NOTICE 'Function restore completed: % functions restored', restore_count;
    
    RETURN restore_count;
END;
$$ LANGUAGE plpgsql;

-- Function to list available backups
CREATE OR REPLACE FUNCTION function_backups.list_backups()
RETURNS TABLE (
    backup_id INTEGER,
    backup_date TIMESTAMP,
    deployment_version TEXT,
    git_commit TEXT,
    description TEXT,
    function_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        db.backup_id,
        db.backup_date,
        db.deployment_version,
        db.git_commit,
        db.backup_description,
        db.backed_up_functions
    FROM function_backups.deployment_backups db
    ORDER BY db.backup_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Create initial backup of current production state
SELECT function_backups.backup_production_functions(
    'V006_initial_backup',
    'pre_cicd_setup',
    'Initial backup before CI/CD pipeline setup'
);

-- Grant permissions
GRANT USAGE ON SCHEMA function_backups TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA function_backups TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA function_backups TO PUBLIC;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'V006 Migration completed: Production function backup system established';
    RAISE NOTICE 'Available functions:';
    RAISE NOTICE '  - function_backups.backup_production_functions(version, commit, description)';
    RAISE NOTICE '  - function_backups.restore_functions_from_backup(backup_id)';
    RAISE NOTICE '  - function_backups.list_backups()';
END $$;