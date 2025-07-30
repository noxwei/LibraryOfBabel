"""
Database Connection Module
Dr. Sarah Chen (陈雪芳) PostgreSQL-First Architecture
Enhanced with Read-Only Connection Security
"""

import os
import psycopg2
import psycopg2.extras
import logging
from contextlib import contextmanager
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Database connection types for different access levels"""
    READONLY = "readonly"
    ADMIN = "admin"


def get_db_config(connection_type: ConnectionType = ConnectionType.READONLY):
    """
    Get database configuration from environment
    
    Args:
        connection_type: Type of connection (readonly or admin)
        
    Returns:
        dict: Database connection configuration
    """
    base_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'knowledge_base'),
        'connect_timeout': 10,
    }
    
    if connection_type == ConnectionType.READONLY:
        # Read-only connection for API operations
        base_config.update({
            'user': os.getenv('DB_READONLY_USER', 'libraryofbabel_api_readonly'),
            'password': os.getenv('DB_READONLY_PASSWORD', ''),
            'application_name': 'LibraryOfBabel_API_ReadOnly'
        })
    elif connection_type == ConnectionType.ADMIN:
        # Admin connection for maintenance operations
        base_config.update({
            'user': os.getenv('DB_ADMIN_USER', 'libraryofbabel_admin'),
            'password': os.getenv('DB_ADMIN_PASSWORD', ''),
            'application_name': 'LibraryOfBabel_API_Admin'
        })
    else:
        # Fallback to original configuration for backward compatibility
        base_config.update({
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'password': os.getenv('DB_PASSWORD', ''),
            'application_name': 'LibraryOfBabel_API'
        })
    
    return base_config


@contextmanager
def get_db(connection_type: ConnectionType = ConnectionType.READONLY):
    """
    Database connection context manager with connection type support
    
    Args:
        connection_type: Type of connection (readonly for API operations, admin for maintenance)
    """
    conn = None
    try:
        config = get_db_config(connection_type)
        conn = psycopg2.connect(**config)
        
        # For read-only connections, ensure transaction is read-only
        if connection_type == ConnectionType.READONLY:
            conn.autocommit = True
            # Set session to read-only as additional safety measure
            with conn.cursor() as cur:
                cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        else:
            conn.autocommit = True
            
        yield conn
    except Exception as e:
        logger.error(f"Database connection error ({connection_type.value}): {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass  # Connection might be in invalid state
        raise
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass  # Connection might already be closed


@contextmanager 
def get_readonly_db():
    """Convenience function for read-only database connections"""
    with get_db(ConnectionType.READONLY) as conn:
        yield conn


@contextmanager
def get_admin_db():
    """Convenience function for admin database connections (use with caution)"""
    logger.warning("Admin database connection requested - ensure this is for maintenance operations only")
    with get_db(ConnectionType.ADMIN) as conn:
        yield conn


def execute_pg_function(function_name, *params, connection_type: ConnectionType = ConnectionType.READONLY):
    """
    Execute PostgreSQL function and return result
    
    Args:
        function_name: Name of the PostgreSQL function to execute
        *params: Parameters to pass to the function
        connection_type: Type of database connection to use (default: READONLY)
    """
    try:
        with get_db(connection_type) as conn:
            with conn.cursor() as cur:
                if params:
                    # Build parameter placeholders
                    placeholders = ', '.join(['%s'] * len(params))
                    cur.execute(f"SELECT {function_name}({placeholders})", params)
                else:
                    cur.execute(f"SELECT {function_name}()")
                result = cur.fetchone()[0]
                return result
    except Exception as e:
        logger.error(f"Error executing {function_name} with {connection_type.value} connection: {e}")
        raise


def execute_pg_function_dict(function_name, *params, connection_type: ConnectionType = ConnectionType.READONLY):
    """
    Execute PostgreSQL function and return result as dict
    
    Args:
        function_name: Name of the PostgreSQL function to execute
        *params: Parameters to pass to the function
        connection_type: Type of database connection to use (default: READONLY)
    """
    try:
        with get_db(connection_type) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if params:
                    placeholders = ', '.join(['%s'] * len(params))
                    cur.execute(f"SELECT {function_name}({placeholders})", params)
                else:
                    cur.execute(f"SELECT {function_name}()")
                result = cur.fetchone()[0]
                return result
    except Exception as e:
        logger.error(f"Error executing {function_name} with {connection_type.value} connection: {e}")
        raise


def execute_admin_operation(sql_query, params=None):
    """
    Execute administrative SQL operations (USE WITH EXTREME CAUTION)
    
    Args:
        sql_query: SQL query to execute
        params: Parameters for the query
        
    Returns:
        Query result
        
    Note:
        This function should only be used for maintenance operations
        and requires admin database credentials
    """
    logger.warning(f"Admin operation requested: {sql_query[:100]}...")
    try:
        with get_admin_db() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(sql_query, params)
                else:
                    cur.execute(sql_query)
                
                # Handle different types of queries
                if sql_query.strip().upper().startswith(('SELECT', 'WITH')):
                    return cur.fetchall()
                else:
                    return cur.rowcount
    except Exception as e:
        logger.error(f"Error executing admin operation: {e}")
        raise


def test_connection(connection_type: ConnectionType = ConnectionType.READONLY):
    """
    Test database connection
    
    Args:
        connection_type: Type of connection to test
    """
    try:
        with get_db(connection_type) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test_value")
                result = cur.fetchone()
                logger.info(f"Database connection successful ({connection_type.value})")
                return result[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed ({connection_type.value}): {e}")
        return False


def test_readonly_safety():
    """
    Test that read-only connection actually prevents write operations
    
    Returns:
        dict: Test results showing which operations were properly blocked
    """
    test_results = {
        'readonly_connection_works': False,
        'insert_blocked': False,
        'update_blocked': False,
        'delete_blocked': False,
        'create_blocked': False
    }
    
    try:
        # Test that basic SELECT works
        with get_readonly_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
                test_results['readonly_connection_works'] = True
                
        # Test that INSERT is blocked
        try:
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO books (title, author) VALUES ('test', 'test')")
        except psycopg2.Error:
            test_results['insert_blocked'] = True
            
        # Test that UPDATE is blocked
        try:
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE books SET title = 'test' WHERE book_id = 1")
        except psycopg2.Error:
            test_results['update_blocked'] = True
            
        # Test that DELETE is blocked
        try:
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM books WHERE book_id = 999999")
        except psycopg2.Error:
            test_results['delete_blocked'] = True
            
        # Test that CREATE is blocked
        try:
            with get_readonly_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE TABLE test_table (id INTEGER)")
        except psycopg2.Error:
            test_results['create_blocked'] = True
            
        logger.info(f"Read-only safety test results: {test_results}")
        return test_results
        
    except Exception as e:
        logger.error(f"Error during read-only safety test: {e}")
        return test_results