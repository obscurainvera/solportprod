from config.Config import get_config
import threading
from contextlib import contextmanager
from typing import ContextManager, Generator
from logs.logger import get_logger
import os
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor
import sys
from psycopg2 import DatabaseError

logger = get_logger(__name__)

class DatabaseConnectionError(Exception):
    """Exception raised for database connection errors."""
    pass

class DatabaseConnectionManager:
    """
    Manages database connections with thread safety.
    Uses singleton pattern to ensure only one manager exists per database.
    
    Key features:
    - Thread-safe connections
    - Connection pooling
    - Table-level locking
    - Transaction management
    """
    
    # Singleton instance
    _instance = None
    # Lock for thread-safe singleton creation
    _lock = threading.Lock()
    # Thread-local storage for connections
    _local = threading.local()
    # Dictionary to store table locks
    _locks = {}
    # Flag to track if pool is closed
    _pool_closed = False

    def __new__(cls, db_url: str = None):
        """
        Creates or returns the singleton instance of the connection manager.
        
        Why singleton?
        - Prevents multiple managers for same database
        - Controls connection pool
        - Centralizes connection management
        
        Args:
            db_url: Database connection URL (deprecated, kept for compatibility)
        
        Returns:
            DatabaseConnectionManager: Singleton instance
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
                config = get_config()
                
                # Store configuration for use in connection methods
                cls._instance.config = config
                
                # Default to PostgreSQL
                cls._instance.connection_type = 'postgres'
                cls._instance.pool = None
                cls._instance._pool_closed = False
                cls._instance.logger = logger
            
                # Use psycopg2 connection pooling for PostgreSQL
                try:
                    # Set connection parameters
                    conn_params = {
                        'user': config.DB_USER,
                        'password': config.DB_PASSWORD,
                        'host': config.DB_HOST,
                        'port': config.DB_PORT,
                        'dbname': config.DB_NAME
                    }
                    
                    # Log connection attempt (without password)
                    log_params = conn_params.copy()
                    log_params['password'] = '****' if log_params['password'] else 'None'
                    logger.info(f"Connecting to PostgreSQL with: {log_params}")
                    
                    # Create connection pool
                    cls._instance.pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=1,
                        maxconn=config.DB_POOL_SIZE,
                        **conn_params
                    )
                    
                    # Test the connection
                    conn = cls._instance.pool.getconn()
                    cls._instance.pool.putconn(conn)
                    
                    logger.info(f"Successfully initialized PostgreSQL connection pool to {config.DB_HOST}")
                except Exception as e:
                    logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
                    # Make sure we still have a connection_type even when initialization fails
                    cls._instance.connection_type = 'postgres'
                    cls._instance.pool = None
                    
                    # Print more detailed error information
                    logger.error(f"Database connection error details: {type(e).__name__}: {str(e)}")
                    logger.error(f"Connection parameters: Host={config.DB_HOST}, Port={config.DB_PORT}, " +
                                f"Database={config.DB_NAME}, User={config.DB_USER}")
                    
                    if isinstance(e, psycopg2.OperationalError):
                        logger.error("This is typically a connection issue (server not running, " +
                                    "incorrect credentials, etc.)")
                        logger.error("Make sure PostgreSQL is installed and running, and that your " +
                                    "credentials are correct.")
                    
                    # Don't raise here - we'll handle the error gracefully when methods are called
            
            return cls._instance

    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            config = self.config
            # Set connection parameters
            conn_params = {
                'user': config.DB_USER,
                'password': config.DB_PASSWORD,
                'host': config.DB_HOST,
                'port': config.DB_PORT,
                'dbname': config.DB_NAME
            }
            
            # Log connection attempt (without password)
            log_params = conn_params.copy()
            log_params['password'] = '****' if log_params['password'] else 'None'
            logger.info(f"Initializing PostgreSQL connection pool with: {log_params}")
            
            # Create connection pool
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=config.DB_POOL_SIZE,
                **conn_params
            )
            self._pool_closed = False
            
            # Test the connection
            conn = self.pool.getconn()
            self.pool.putconn(conn)
            
            logger.info(f"Successfully initialized PostgreSQL connection pool to {config.DB_HOST}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            self.pool = None
            self._pool_closed = True
            return False
            
    def is_pool_closed(self):
        """Check if the connection pool is closed"""
        return self._pool_closed or self.pool is None
        
    def reinitialize_pool_if_closed(self):
        """Reinitialize the connection pool if it's closed"""
        if self.is_pool_closed():
            logger.warning("Connection pool is closed, attempting to reinitialize...")
            return self._initialize_pool()
        return True

    @contextmanager
    def get_connection(self):
        """
        Gets a database connection from the pool.
        
        Returns:
            Connection: Database connection
        """
        connection = None
        try:
            # Check if pool needs to be initialized or reinitialized
            if self.pool is None or self._pool_closed:
                logger.warning("Connection pool is unavailable, attempting to initialize/reinitialize")
                if not self._initialize_pool():
                    raise Exception("Database connection pool is not initialized and could not be reinitialized. " +
                                "Make sure PostgreSQL is running and credentials are correct.")
                logger.info("Pool successfully (re)initialized")
            
            # Get connection from pool
            try:
                connection = self.pool.getconn()
            except psycopg2.pool.PoolError as e:
                # If pool error, try to reinitialize and get connection again
                logger.warning(f"Pool error when getting connection: {str(e)}, attempting to reinitialize")
                if self._initialize_pool():
                    connection = self.pool.getconn()
                    logger.info("Successfully got connection after pool reinitialization")
                else:
                    raise Exception("Failed to reinitialize pool after error")
            
            yield connection
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            # Re-raise the exception
            raise
        finally:
            if connection and self.pool and not self._pool_closed:
                # Return PostgreSQL connection to pool if it's still open
                try:
                    if not connection.closed:
                        try:
                            self.pool.putconn(connection)
                        except psycopg2.pool.PoolError as e:
                            # Handle "trying to put unkeyed connection" error
                            if "unkeyed connection" in str(e):
                                logger.warning(f"Attempted to return unkeyed connection to pool: {str(e)}")
                                # Just close the connection instead of returning it to the pool
                                try:
                                    connection.close()
                                    logger.info("Successfully closed unkeyed connection")
                                except Exception as close_error:
                                    logger.error(f"Error closing unkeyed connection: {close_error}")
                            else:
                                raise
                except Exception as putconn_error:
                    logger.error(f"Error returning connection to pool: {putconn_error}")
                    # Don't mark the pool as closed here, instead try to reinitialize
                    if "connection pool is closed" in str(putconn_error):
                        logger.warning("Pool appears to be closed, will reinitialize on next transaction")

    @contextmanager
    def transaction(self):
        """
        Provides a transaction context for database operations.
        
        Returns:
            Cursor: Database cursor for operations
        """
        # Use psycopg2 for PostgreSQL
        conn = None
        cur = None
        try:
            if self.pool is None or self._pool_closed:
                # Try to reinitialize the pool if it's closed or None
                if not self._initialize_pool():
                    raise Exception("Database connection pool is not initialized and could not be reinitialized. " +
                                   "Make sure PostgreSQL is running and credentials are correct.")
                
            conn = self.pool.getconn()
            # Auto-commit is off by default in psycopg2
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            # Patch the cursor to handle SQLAlchemy text() objects correctly
            original_execute = cur.execute
            def patched_execute(query, params=None):
                # If query is SQLAlchemy text(), convert to string
                if hasattr(query, 'text'):
                    query = query.text
                    
                # Convert boolean params for PostgreSQL
                if params and isinstance(params, (list, tuple)):
                    params = tuple(1 if p is True else 0 if p is False else p for p in params)
                elif params and isinstance(params, dict):
                    params = {k: (1 if v is True else 0 if v is False else v) for k, v in params.items()}
                    
                return original_execute(query, params)
            
            cur.execute = patched_execute
            
            yield cur
            
            # Only commit if cursor hasn't been closed
            if not cur.closed and conn and not conn.closed:
                conn.commit()
                
        except psycopg2.pool.PoolError as e:
            logger.error(f"Pool error: {str(e)}")
            # Try to reinitialize the pool
            if self._initialize_pool():
                logger.info("Successfully reinitialized the connection pool after pool error")
                # Try again with the new pool
                try:
                    conn = self.pool.getconn()
                    cur = conn.cursor(cursor_factory=RealDictCursor)
                    
                    # Patch the cursor again
                    original_execute = cur.execute
                    def patched_execute(query, params=None):
                        # If query is SQLAlchemy text(), convert to string
                        if hasattr(query, 'text'):
                            query = query.text
                            
                        # Convert boolean params for PostgreSQL
                        if params and isinstance(params, (list, tuple)):
                            params = tuple(1 if p is True else 0 if p is False else p for p in params)
                        elif params and isinstance(params, dict):
                            params = {k: (1 if v is True else 0 if v is False else v) for k, v in params.items()}
                            
                        return original_execute(query, params)
                    
                    cur.execute = patched_execute
                    
                    yield cur
                    
                    # Only commit if cursor hasn't been closed
                    if not cur.closed and conn and not conn.closed:
                        conn.commit()
                    return
                except Exception as retry_e:
                    logger.error(f"Failed to use reinitialized pool: {str(retry_e)}")
            raise e
        except Exception as e:
            if conn:
                try:
                    # Only rollback if connection is still open
                    if not conn.closed:
                        conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during transaction rollback: {rollback_error}")
            
            logger.error(f"Transaction error: {str(e)}")
            
            # Provide more detailed error information
            if isinstance(e, psycopg2.OperationalError):
                logger.error("This is typically a connection issue or SQL syntax error")
            elif isinstance(e, psycopg2.IntegrityError):
                logger.error("This is typically a constraint violation (unique, foreign key, etc.)")
            
            raise e
        finally:
            # Close cursor first
            if cur:
                try:
                    if not cur.closed:
                        cur.close()
                except Exception as close_error:
                    logger.error(f"Error closing cursor: {close_error}")
            
            # Then return connection to pool
            if conn and self.pool and not self._pool_closed:
                try:
                    if not conn.closed:
                        try:
                            self.pool.putconn(conn)
                        except psycopg2.pool.PoolError as e:
                            # Handle "trying to put unkeyed connection" error
                            if "unkeyed connection" in str(e):
                                logger.warning(f"Attempted to return unkeyed connection to pool: {str(e)}")
                                # Just close the connection instead of returning it to the pool
                                try:
                                    conn.close()
                                    logger.info("Successfully closed unkeyed connection")
                                except Exception as close_error:
                                    logger.error(f"Error closing unkeyed connection: {close_error}")
                            else:
                                raise
                except Exception as putconn_error:
                    logger.error(f"Error returning connection to pool: {putconn_error}")
                    # Don't mark the pool as closed here, instead try to reinitialize
                    if "connection pool is closed" in str(putconn_error):
                        logger.warning("Pool appears to be closed, will reinitialize on next transaction")

    @contextmanager
    def table_lock(self, table_name: str):
        """
        Provides table-level locking for thread-safe operations.
        
        Args:
            table_name: Name of table to lock
        """
        if table_name not in self._locks:
            self._locks[table_name] = threading.Lock()
        with self._locks[table_name]:
            yield

    def close(self):
        """
        Closes all database connections.
        This method should only be called during application shutdown.
        """
        # Close the PostgreSQL connection pool
        if hasattr(self, 'pool') and self.pool and not self._pool_closed:
            try:
                # Log first to ensure we see this in case of any issues
                logger.info("Closing PostgreSQL connection pool")
                self.pool.closeall()
                self._pool_closed = True
                logger.info("Closed all PostgreSQL connections in the pool")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL connection pool: {e}")
                # Still mark as closed so we'll reinitialize next time
                self._pool_closed = True
    
    def reconnect(self, force=False):
        """
        Attempt to safely reconnect to the database by reinitializing the pool.
        
        Args:
            force: If True, close the existing pool before reinitializing
            
        Returns:
            bool: True if reconnection was successful, False otherwise
        """
        logger.info(f"Attempting to reconnect to database (force={force})")
        
        if force and self.pool and not self._pool_closed:
            try:
                logger.info("Forcing pool closure before reconnection")
                self.pool.closeall()
            except Exception as e:
                logger.error(f"Error closing pool during forced reconnection: {e}")
            finally:
                self._pool_closed = True
                
        return self._initialize_pool()

    def create_postgres_connection(self):
        """Establishes a PostgreSQL database connection with the specified parameters."""
        try:
            # Log connection parameters (without the actual password content)
            connection_params = {
                'user': self.config.DB_USER,
                'password': 'None' if not self.config.DB_PASSWORD else '****',
                'host': self.config.DB_HOST,
                'port': self.config.DB_PORT,
                'dbname': self.config.DB_NAME
            }
            self.logger.info(f"Connecting to PostgreSQL with: {connection_params}")
            
            # Create the connection
            connection = psycopg2.connect(
                user=self.config.DB_USER,
                password=self.config.DB_PASSWORD,
                host=self.config.DB_HOST,
                port=self.config.DB_PORT,
                dbname=self.config.DB_NAME,
                connect_timeout=self.config.DB_CONNECT_TIMEOUT,  # Add timeout for connection attempts
                sslmode=self.config.DB_SSLMODE,
                gssencmode=self.config.DB_GSSENCMODE
            )
            connection.autocommit = False
            
            # If connection successful, log success
            self.logger.info(f"Successfully connected to PostgreSQL database: {self.config.DB_NAME}")
            return connection
        except psycopg2.Error as e:
            error_msg = f"Error connecting to PostgreSQL database: {e}"
            self.logger.error(error_msg)
            # Include connection details in error log for debugging
            self.logger.error(f"Connection failed with parameters: user={self.config.DB_USER}, "
                              f"host={self.config.DB_HOST}, port={self.config.DB_PORT}, "
                              f"dbname={self.config.DB_NAME}")
            raise DatabaseConnectionError(error_msg) 