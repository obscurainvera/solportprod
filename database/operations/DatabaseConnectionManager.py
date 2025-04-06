from config.config import get_config
import threading
from contextlib import contextmanager
from typing import ContextManager, Generator
from logs.logger import get_logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

logger = get_logger(__name__)

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

    def __new__(cls, db_url: str = None):
        """
        Creates or returns the singleton instance of the connection manager.
        
        Why singleton?
        - Prevents multiple managers for same database
        - Controls connection pool
        - Centralizes connection management
        
        Args:
            db_url: Database connection URL
        
        Returns:
            DatabaseConnectionManager: Singleton instance
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
                db_url = db_url or get_config().get_database_url()
                cls._instance.db_url = db_url
                # Configure SQLAlchemy engine with PostgreSQL-specific settings for cloud environments
                cls._instance.engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=int(os.getenv('DB_POOL_SIZE', '5')),
                    max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '10')),
                    pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
                    pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '1800')),
                    pool_pre_ping=True,  # Verify connections before usage
                    connect_args={
                        'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
                    }
                )
                cls._instance.Session = sessionmaker(bind=cls._instance.engine)
            return cls._instance

    @contextmanager
    def get_connection(self):
        """
        Gets a thread-local database connection.
        
        Why thread-local?
        - Each thread gets its own connection
        - Prevents connection sharing between threads
        - Ensures thread safety
        
        How it works:
        1. Checks if thread has a connection
        2. Creates new connection if needed
        3. Returns connection for use
        4. Connection persists for thread lifetime
        
        Returns:
            Connection: Database connection
        """
        if not hasattr(self._local, 'connection'):
            self._local.connection = self.engine.connect()
        yield self._local.connection

    @contextmanager
    def transaction(self):
        """
        Provides a transaction context for database operations.
        
        Why use transactions?
        - Ensures atomic operations
        - Automatic rollback on errors
        - Groups related operations
        
        How it works:
        1. Gets connection
        2. Creates session
        3. Executes operations
        4. Commits if successful
        5. Rolls back if error occurs
        
        Usage:
            with db.transaction() as session:
                session.execute("INSERT INTO...")
        
        Returns:
            Session: Database session for operations
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction rolled back due to error: {str(e)}")
            raise e
        finally:
            session.close()

    @contextmanager
    def table_lock(self, table_name: str):
        """
        Provides table-level locking for thread-safe operations.
        
        Why table locks?
        - Prevents concurrent modifications
        - Finer control than database locks
        - Better performance than full DB locks
        
        How it works:
        1. Creates lock for table if not exists
        2. Acquires lock before operations
        3. Releases lock after operations
        
        Usage:
            with db.table_lock('users'):
                # perform thread-safe operations
        
        Args:
            table_name: Name of table to lock
        """
        if table_name not in self._locks:
            self._locks[table_name] = threading.Lock()
        with self._locks[table_name]:
            yield

    def close(self):
        """
        Closes the thread's database connection.
        
        Why needed?
        - Releases database resources
        - Prevents connection leaks
        - Proper cleanup
        
        When to use:
        - Application shutdown
        - Thread completion
        - Resource cleanup
        """
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection 