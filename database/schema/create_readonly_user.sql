/*
📚 LIBRARYOFBABEL - READ-ONLY DATABASE USER SETUP
================================================

Dr. Sarah Chen (陈雪芳) PostgreSQL Security Implementation
Creates a read-only user for API application access
*/

-- Create the read-only role for the API application
CREATE ROLE libraryofbabel_readonly;

-- Create the actual user that will connect from the application
CREATE USER libraryofbabel_api_readonly WITH PASSWORD 'your_secure_readonly_password_here';

-- Add the user to the read-only role
GRANT libraryofbabel_readonly TO libraryofbabel_api_readonly;

-- Grant connection to the database
GRANT CONNECT ON DATABASE knowledge_base TO libraryofbabel_readonly;

-- Grant usage on the public schema
GRANT USAGE ON SCHEMA public TO libraryofbabel_readonly;

-- Grant SELECT permissions on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO libraryofbabel_readonly;

-- Grant SELECT permissions on all future tables (auto-grant)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO libraryofbabel_readonly;

-- Grant USAGE on all sequences (needed for SERIAL columns)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO libraryofbabel_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO libraryofbabel_readonly;

-- Grant EXECUTE permissions on all existing functions (PostgreSQL functions for API)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO libraryofbabel_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO libraryofbabel_readonly;

-- Explicitly deny dangerous operations to ensure read-only access
-- Note: This is redundant since we're not granting these privileges, but explicit for security
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM libraryofbabel_readonly;
REVOKE CREATE ON SCHEMA public FROM libraryofbabel_readonly;
REVOKE CREATE ON DATABASE knowledge_base FROM libraryofbabel_readonly;

-- Verify the setup by checking privileges
SELECT 
    grantee, 
    table_name, 
    privilege_type 
FROM information_schema.table_privileges 
WHERE grantee = 'libraryofbabel_readonly'
ORDER BY table_name, privilege_type;

-- Check function privileges
SELECT 
    grantee,
    routine_name,
    privilege_type
FROM information_schema.routine_privileges 
WHERE grantee = 'libraryofbabel_readonly'
ORDER BY routine_name;

/*
IMPORTANT SECURITY NOTES:
========================

1. Change 'your_secure_readonly_password_here' to a strong password
2. Store the password securely using environment variables
3. This user can execute PostgreSQL functions but cannot modify data directly
4. The functions themselves should be designed to be read-only operations
5. For admin operations, use a separate admin user with full privileges

ADMIN USER SETUP (for maintenance operations):
============================================
For write operations, create a separate admin user:

CREATE USER libraryofbabel_admin WITH PASSWORD 'your_secure_admin_password_here';
GRANT ALL PRIVILEGES ON DATABASE knowledge_base TO libraryofbabel_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO libraryofbabel_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO libraryofbabel_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO libraryofbabel_admin;
*/