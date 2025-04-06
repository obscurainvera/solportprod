from config.Config import get_config
import threading
from contextlib import contextmanager
from typing import ContextManager, Generator
from logs.logger import get_logger
import os
import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

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
                
                if config.DB_TYPE == 'sqlite':
                    # SQLite support retained for development
                    from sqlalchemy import create_engine
                    from sqlalchemy.orm import sessionmaker
                    
                    cls._instance.db_url = f'sqlite:///{config.DB_PATH}'
                    cls._instance.engine = create_engine(cls._instance.db_url)
                    cls._instance.Session = sessionmaker(bind=cls._instance.engine)
                    cls._instance.connection_type = 'sqlite'
                else:
                    # Use psycopg2 connection pooling for PostgreSQL
                    try:
                        cls._instance.pool = psycopg2.pool.ThreadedConnectionPool(
                            minconn=1,
                            maxconn=config.DB_POOL_SIZE,
                            dbname=config.DB_NAME,
                            user=config.DB_USER,
                            password=config.DB_PASSWORD,
                            host=config.DB_HOST,
                            port=config.DB_PORT,
                            sslmode=config.DB_SSLMODE
                        )
                        cls._instance.connection_type = 'postgres'
                        logger.info(f"Initialized PostgreSQL connection pool to {config.DB_HOST}")
                    except Exception as e:
                        logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
                        raise
            
            return cls._instance

    @contextmanager
    def get_connection(self):
        """
        Gets a database connection from the pool.
        
        Returns:
            Connection: Database connection
        """
        connection = None
        try:
            if self.connection_type == 'sqlite':
                if not hasattr(self._local, 'connection'):
                    self._local.connection = self.engine.connect()
                connection = self._local.connection
            else:
                # Get PostgreSQL connection from pool
                connection = self.pool.getconn()
            
            yield connection
        finally:
            if self.connection_type == 'postgres' and connection:
                # Return PostgreSQL connection to pool
                self.pool.putconn(connection)

    @contextmanager
    def transaction(self):
        """
        Provides a transaction context for database operations.
        
        Returns:
            Cursor: Database cursor for operations
        """
        if self.connection_type == 'sqlite':
            # Use SQLAlchemy session for SQLite
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
        else:
            # Use psycopg2 for PostgreSQL
            conn = self.pool.getconn()
            try:
                # Auto-commit is off by default in psycopg2
                cur = conn.cursor(cursor_factory=RealDictCursor)
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {str(e)}")
                raise e
            finally:
                cur.close()
                self.pool.putconn(conn)

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
        """
        if self.connection_type == 'sqlite':
            if hasattr(self._local, 'connection'):
                self._local.connection.close()
                del self._local.connection
        else:
            # Close the PostgreSQL connection pool
            if hasattr(self, 'pool'):
                self.pool.closeall()
                logger.info("Closed all PostgreSQL connections in the pool") 