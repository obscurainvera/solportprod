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
    Connection pooling for PostgreSQL is handled here.

    Key features:
    - Thread-safe connections
    - Connection pooling
    - Table-level locking
    - Transaction management
    """

    # Lock for thread-safe operations
    _lock = threading.Lock()
    # Dictionary to store table locks
    _locks = {}

    def __init__(self, db_url: str = None):
        """
        Initializes the connection manager.
        Actual connection initialization is lazy - happens on first use.

        Args:
            db_url: Database connection URL (deprecated, kept for compatibility)
        """
        self.config = get_config()
        self.connection_type = "postgres"
        self.pool = None
        self._pool_closed = False
        self.logger = logger

        # Store the initialization parameters for lazy connection
        self._initialized = False

    def _check_pool_status(self):
        """
        Check if pool is available and initialized.
        Returns:
            bool: True if pool is available, False otherwise
        """
        return not (self.pool is None or self._pool_closed)

    def _initialize_pool_if_needed(self):
        """
        Initializes the connection pool if needed.
        Returns:
            bool: True if pool is available (either already or newly initialized), False if initialization failed
        """
        # Fast path - pool is already initialized and available
        if self._check_pool_status():
            return True

        # Slow path - acquire lock and initialize pool
        with self._lock:
            # Double-check pattern to avoid unnecessary initialization
            if self._check_pool_status():
                return True

            # Actually initialize the pool
            return self._initialize_pool()

    def _initialize_pool(self):
        """Initialize the connection pool"""
        try:
            # Set connection parameters
            conn_params = {
                "user": self.config.DB_USER,
                "password": self.config.DB_PASSWORD,
                "host": self.config.DB_HOST,
                "port": self.config.DB_PORT,
                "dbname": self.config.DB_NAME,
            }

            # Log connection attempt (without password)
            log_params = conn_params.copy()
            log_params["password"] = "****" if log_params["password"] else "None"
            logger.info(f"Initializing PostgreSQL connection pool with: {log_params}")

            # Create connection pool
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1, maxconn=self.config.DB_POOL_SIZE, **conn_params
            )
            self._pool_closed = False
            self._initialized = True

            # Test the connection
            test_connection = self.pool.getconn()
            self.pool.putconn(test_connection)

            logger.info(
                f"Successfully initialized PostgreSQL connection pool to {self.config.DB_HOST}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            self.pool = None
            self._pool_closed = True
            self._initialized = False

            # Print more detailed error information
            logger.error(
                f"Database connection error details: {type(e).__name__}: {str(e)}"
            )
            logger.error(
                f"Connection parameters: Host={self.config.DB_HOST}, Port={self.config.DB_PORT}, "
                + f"Database={self.config.DB_NAME}, User={self.config.DB_USER}"
            )

            if isinstance(e, psycopg2.OperationalError):
                logger.error(
                    "This is typically a connection issue (server not running, "
                    + "incorrect credentials, etc.)"
                )
                logger.error(
                    "Make sure PostgreSQL is installed and running, and that your "
                    + "credentials are correct."
                )

            return False

    def is_pool_closed(self):
        """Check if the connection pool is closed"""
        return self._pool_closed or self.pool is None

    def _check_and_initialize_pool(self):
        """
        Check if pool needs initialization and initialize if needed.

        Returns:
            bool: True if pool is available (either already or after initialization),
                  False if initialization failed
        """
        # Fast path - pool is available
        if self._check_pool_status():
            return True

        # Pool unavailable - try to initialize it
        logger.info("Connection pool unavailable, initializing")
        return self._initialize_pool_if_needed()

    @contextmanager
    def get_connection(self):
        """
        Gets a database connection from the pool.

        Returns:
            Connection: Database connection
        """
        connection = None
        try:
            # Ensure pool is initialized
            if not self._check_and_initialize_pool():
                raise DatabaseConnectionError(
                    "Database connection pool is not initialized and could not be reinitialized. "
                    + "Make sure PostgreSQL is running and credentials are correct."
                )

            # Get connection from pool
            try:
                connection = self.pool.getconn()
            except psycopg2.pool.PoolError as e:
                # If pool error, try to reinitialize once and get connection again
                logger.warning(
                    f"Pool error when getting connection: {str(e)}, attempting to reinitialize"
                )
                if self._initialize_pool():
                    connection = self.pool.getconn()
                    logger.info(
                        "Successfully got connection after pool reinitialization"
                    )
                else:
                    self._handle_connection_error(e, "get_connection")

            yield connection
        except Exception as e:
            if not isinstance(e, DatabaseConnectionError):
                self._handle_connection_error(e, "get_connection", connection)
            else:
                # Already handled, just re-raise
                raise
        finally:
            if connection and self._check_pool_status():
                # Return PostgreSQL connection to pool if it's still open
                try:
                    if not connection.closed:
                        try:
                            self.pool.putconn(connection)
                        except psycopg2.pool.PoolError as e:
                            # Handle "trying to put unkeyed connection" error
                            if "unkeyed connection" in str(e):
                                logger.warning(
                                    f"Attempted to return unkeyed connection to pool: {str(e)}"
                                )
                                # Just close the connection instead of returning it to the pool
                                try:
                                    connection.close()
                                    logger.info(
                                        "Successfully closed unkeyed connection"
                                    )
                                except Exception as close_error:
                                    logger.error(
                                        f"Error closing unkeyed connection: {close_error}"
                                    )
                            else:
                                self._handle_connection_error(
                                    e, "return connection to pool"
                                )
                except Exception as putconn_error:
                    logger.error(f"Error returning connection to pool: {putconn_error}")
                    # Flag for reinitialization if the pool appears to be closed
                    if "connection pool is closed" in str(putconn_error):
                        logger.warning(
                            "Pool appears to be closed, will reinitialize on next transaction"
                        )
                        self._pool_closed = True

    def _handle_connection_error(
        self, error, operation="database operation", connection=None
    ):
        """
        Standardized handling of database connection errors.

        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            connection: Optional connection to clean up

        Raises:
            DatabaseConnectionError: A wrapped version of the original error with more context
        """
        # Determine error type and provide appropriate logging
        if isinstance(error, psycopg2.OperationalError):
            logger.error(f"Database connection error during {operation}: {error}")
            logger.error(
                "This is typically a connection issue (server not running, network, credentials)"
            )

            # If this is a connection issue, mark the pool for reinitialization
            self._pool_closed = True

        elif isinstance(error, psycopg2.pool.PoolError):
            logger.error(f"Pool error during {operation}: {error}")
            logger.error("Connection pool may need to be reinitialized")

        elif isinstance(error, psycopg2.IntegrityError):
            logger.error(f"Database integrity error during {operation}: {error}")
            logger.error(
                "This is typically a constraint violation (unique, foreign key)"
            )

        else:
            logger.error(f"Unexpected database error during {operation}: {error}")

        # Clean up connection if provided
        if connection and hasattr(connection, "closed") and not connection.closed:
            try:
                connection.rollback()
                logger.info("Rolled back transaction after error")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")

        # Wrap the original error to provide a consistent interface
        raise DatabaseConnectionError(
            f"Database error during {operation}: {str(error)}"
        ) from error

    def _get_transaction_cursor(self):
        """
        Helper method to get a connection and cursor for transactions.

        Returns:
            tuple: (connection, cursor)
        """
        if not self._check_and_initialize_pool():
            raise DatabaseConnectionError(
                "Database connection pool could not be initialized"
            )
        conn = self.pool.getconn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        original_execute = cur.execute

        def patched_execute(query, params=None):
            if hasattr(query, "text"):
                query = query.text
            if params:
                if isinstance(params, (list, tuple)):
                    params = tuple(
                        1 if p is True else 0 if p is False else p for p in params
                    )
                elif isinstance(params, dict):
                    params = {
                        k: (1 if v is True else 0 if v is False else v)
                        for k, v in params
                    }
            return original_execute(query, params)

        cur.execute = patched_execute
        return conn, cur

    @contextmanager
    def transaction(self):
        """
        Provides a transaction context for database operations.

        Returns:
            Cursor: Database cursor for operations
        """
        conn = None
        cur = None
        try:
            # First attempt to get connection and cursor
            try:
                conn, cur = self._get_transaction_cursor()
            except psycopg2.pool.PoolError as e:
                logger.error(f"Pool error on first attempt: {str(e)}")
                if self._initialize_pool():
                    logger.info("Reinitialized pool after error")
                    try:
                        conn, cur = self._get_transaction_cursor()
                    except psycopg2.pool.PoolError as e2:
                        self._handle_connection_error(
                            e2, "transaction after reinitialization"
                        )
                else:
                    self._handle_connection_error(e, "transaction")

            # Yield the cursor for the transaction
            yield cur
            if not cur.closed and not conn.closed:
                conn.commit()
        except Exception as e:
            if conn and not conn.closed:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during transaction rollback: {rollback_error}")
            self._handle_connection_error(e, "transaction", None)
        finally:
            # Close cursor first
            if cur and not cur.closed:
                try:
                    cur.close()
                except Exception as close_error:
                    logger.error(f"Error closing cursor: {close_error}")
            # Then return connection to pool
            if conn and self._check_pool_status() and not conn.closed:
                try:
                    self.pool.putconn(conn)
                except psycopg2.pool.PoolError as e:
                    logger.warning(f"Pool error on return: {str(e)}")
                    if "unkeyed connection" in str(e):
                        try:
                            conn.close()
                            logger.info("Closed unkeyed connection")
                        except Exception as close_error:
                            logger.error(
                                f"Error closing unkeyed connection: {close_error}"
                            )
                    else:
                        self._handle_connection_error(e, "return connection to pool")

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
        if self.pool and not self._pool_closed:
            try:
                logger.info("Closing PostgreSQL connection pool")
                self.pool.closeall()
                self._pool_closed = True
                logger.info("Closed all PostgreSQL connections in the pool")
            except Exception as e:
                logger.error(f"Error closing PostgreSQL connection pool: {e}")
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
