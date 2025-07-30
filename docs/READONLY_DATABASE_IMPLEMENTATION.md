# LibraryOfBabel Read-Only Database Implementation

**Dr. Sarah Chen (陈雪芳) PostgreSQL Security Implementation**

## Overview

This implementation provides read-only database connections for the LibraryOfBabel API to prevent accidental data deletion while maintaining full functionality for query operations and PostgreSQL function execution.

## Architecture

### Connection Types

1. **Read-Only Connection** (Default)
   - Used for all API operations
   - Cannot execute INSERT, UPDATE, DELETE, or DDL operations
   - Can execute SELECT queries and PostgreSQL functions
   - Session-level read-only enforcement

2. **Admin Connection** (Restricted Use)
   - Used only for maintenance operations
   - Full database privileges
   - Requires separate credentials
   - Logged for audit purposes

## Database Setup

### 1. Create Read-Only User

Execute the SQL commands in `/database/schema/create_readonly_user.sql`:

```bash
psql -U postgres -d knowledge_base -f database/schema/create_readonly_user.sql
```

### 2. Set Strong Passwords

Replace the placeholder passwords in the SQL script:

```sql
-- Replace this password
CREATE USER libraryofbabel_api_readonly WITH PASSWORD 'your_secure_readonly_password_here';

-- And this one for admin user
CREATE USER libraryofbabel_admin WITH PASSWORD 'your_secure_admin_password_here';
```

### 3. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.readonly.example .env
```

Edit `.env` with your actual passwords:

```bash
# Read-Only API User (Default for all API operations)
DB_READONLY_USER=libraryofbabel_api_readonly
DB_READONLY_PASSWORD=your_actual_secure_readonly_password

# Admin User (For maintenance operations only)
DB_ADMIN_USER=libraryofbabel_admin
DB_ADMIN_PASSWORD=your_actual_secure_admin_password
```

## Code Implementation

### Enhanced Database Module

The updated `/src/api/modules/database.py` provides:

1. **Connection Type Management**
   ```python
   from api.modules.database import ConnectionType, get_db
   
   # Read-only connection (default)
   with get_db(ConnectionType.READONLY) as conn:
       # Safe operations only
   
   # Admin connection (use with caution)
   with get_db(ConnectionType.ADMIN) as conn:
       # Full privileges
   ```

2. **Function Execution**
   ```python
   from api.modules.database import execute_pg_function
   
   # Uses read-only connection by default
   result = execute_pg_function('api_list_books', 1, 20)
   
   # Explicitly specify connection type if needed
   result = execute_pg_function('api_list_books', 1, 20, 
                               connection_type=ConnectionType.READONLY)
   ```

3. **Admin Operations**
   ```python
   from api.modules.database import execute_admin_operation
   
   # For maintenance operations only
   result = execute_admin_operation(
       "UPDATE books SET processed = true WHERE processed IS NULL"
   )
   ```

### Backward Compatibility

Existing code continues to work without changes:

```python
# This still works and now uses read-only connection by default
from api.modules.database import execute_pg_function
result = execute_pg_function('api_text_search', 'python programming')
```

## Security Features

### Multi-Layer Protection

1. **Database User Privileges**
   - Read-only user lacks INSERT/UPDATE/DELETE privileges
   - Explicit REVOKE statements for dangerous operations

2. **Session-Level Enforcement**
   - `SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY`
   - PostgreSQL prevents write operations at session level

3. **Application-Level Controls**
   - Connection type validation
   - Audit logging for admin operations
   - Explicit warnings for privileged operations

### Function Safety

PostgreSQL functions can still be executed because:
- Read-only user has EXECUTE privileges on functions
- Functions are designed to be read-only operations (SELECT-based)
- Functions cannot perform destructive operations due to user privileges

## Testing

### Run Security Tests

Execute the comprehensive test suite:

```bash
python test_readonly_security.py
```

This tests:
- Basic connection functionality
- PostgreSQL function execution
- Write operation blocking
- Session characteristics

### Manual Testing

```python
from api.modules.database import test_readonly_safety

# Test write operation blocking
results = test_readonly_safety()
print(results)
```

## Migration Guide

### For Existing Applications

1. **Update Environment Variables**
   ```bash
   # Add new variables to your .env file
   DB_READONLY_USER=libraryofbabel_api_readonly
   DB_READONLY_PASSWORD=your_password
   ```

2. **No Code Changes Required**
   - Existing `execute_pg_function()` calls work unchanged
   - Automatically use read-only connections

3. **For Admin Operations**
   ```python
   # Replace direct database operations with admin function
   # OLD:
   # with get_db() as conn:
   #     cur.execute("UPDATE ...")
   
   # NEW:
   from api.modules.database import execute_admin_operation
   execute_admin_operation("UPDATE ...")
   ```

## Best Practices

### Development

1. **Default to Read-Only**
   - All API endpoints use read-only connections by default
   - Only use admin connections for maintenance scripts

2. **Explicit Admin Operations**
   ```python
   # Good: Explicit admin operation
   execute_admin_operation("UPDATE books SET status = 'processed'")
   
   # Avoid: Direct admin connection usage
   with get_admin_db() as conn:  # Use sparingly
   ```

3. **Error Handling**
   ```python
   try:
       result = execute_pg_function('api_search', query)
   except psycopg2.Error as e:
       logger.error(f"Database error: {e}")
       # Handle read-only constraint violations gracefully
   ```

### Production Deployment

1. **Separate Credentials**
   - Use different passwords for development/staging/production
   - Store in secure environment variable management

2. **Connection Monitoring**
   ```python
   # Monitor connection types in logs
   logger.info(f"Database connection: {connection_type.value}")
   ```

3. **Regular Security Testing**
   ```bash
   # Run security tests in CI/CD pipeline
   python test_readonly_security.py
   ```

## Troubleshooting

### Common Issues

1. **"Permission Denied" Errors**
   ```
   Solution: Verify read-only user has EXECUTE privileges on functions
   Check: GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO libraryofbabel_readonly;
   ```

2. **"User Does Not Exist" Errors**
   ```
   Solution: Ensure read-only user was created properly
   Check: SELECT usename FROM pg_user WHERE usename = 'libraryofbabel_api_readonly';
   ```

3. **Connection Timeouts**
   ```
   Solution: Verify database host/port configuration
   Check: Environment variables DB_HOST, DB_PORT
   ```

### Debugging

```python
# Test specific connection type
from api.modules.database import test_connection, ConnectionType

test_connection(ConnectionType.READONLY)
test_connection(ConnectionType.ADMIN)
```

## Security Considerations

### Password Management

1. Use strong, unique passwords for each environment
2. Rotate passwords regularly
3. Store in secure credential management systems
4. Never commit passwords to version control

### Access Control

1. Limit admin user usage to maintenance windows
2. Monitor admin operations through application logs
3. Consider IP restrictions for admin connections
4. Implement connection pooling for read-only connections

### Monitoring

```python
# Log all admin operations
logger.warning(f"Admin operation: {sql_query} by {user}")
```

## Files Modified/Created

### Modified Files
- `/src/api/modules/database.py` - Enhanced with read-only connection support

### New Files
- `/database/schema/create_readonly_user.sql` - Database user setup
- `/.env.readonly.example` - Environment configuration template
- `/test_readonly_security.py` - Comprehensive security tests
- `/docs/READONLY_DATABASE_IMPLEMENTATION.md` - This documentation

## Support

For issues or questions regarding this implementation, contact:
- **Dr. Sarah Chen (陈雪芳)** - Database Architecture Lead
- **Technical Team** - LibraryOfBabel Development

---

*LibraryOfBabel PostgreSQL Security Implementation - Dr. Sarah Chen (陈雪芳)*