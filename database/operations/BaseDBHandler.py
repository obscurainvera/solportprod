from config.Config import get_config
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import Optional
from datetime import datetime
import pytz

class BaseDBHandler:
    """
    Base class for all database handlers.
    Provides common functionality and connection management.
    """

    def __init__(self, conn_manager: DatabaseConnectionManager):
        """
        Initializes the handler with a connection manager.
        
        Args:
            conn_manager: Shared database connection manager instance
        """
        if conn_manager is None:
            # Create a new manager only if not provided (rare case)
            self.conn_manager = DatabaseConnectionManager()
        else:
            # Use the shared connection manager
            self.conn_manager = conn_manager

    @property
    def transaction(self):
        """
        Property to access transaction context manager.
        
        Usage:
            with handler.transaction() as cursor:
                # perform operations
        
        Returns:
            Context manager for transactions
        """
        return self.conn_manager.transaction

    @property
    def table_lock(self):
        """
        Property to access table locking mechanism.
        
        Usage:
            with handler.table_lock('table_name'):
                # perform thread-safe operations
        
        Returns:
            Context manager for table locks
        """
        return self.conn_manager.table_lock

    def close(self):
        """
        Closes the database connection.
        
        Note: This should only be called during application shutdown.
        Normal operations should let the connection pool manage connections.
        """
        self.conn_manager.close()

    @staticmethod
    def getCurrentIstTime() -> datetime:
        """Get current time in IST timezone"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist) 
    
    @staticmethod
    def getCurrentUtcTime() -> datetime:
        """Get current time in UTC timezone"""
        return datetime.now(pytz.UTC)

    @staticmethod
    def sql_boolean(value, for_postgres=None):
        """
        Convert Python boolean to appropriate SQL boolean representation
        
        Args:
            value: Python boolean value
            for_postgres: Override config to force postgres or sqlite format
                         If None, uses the config setting
                       
        Returns:
            Integer 1/0 for SQLite, SQL syntax (TRUE/FALSE) for PostgreSQL
        """
        config = get_config()
        
        is_postgres = for_postgres if for_postgres is not None else config.DB_TYPE == 'postgres'
        
        if is_postgres:
            # For PostgreSQL, use integers for SQLAlchemy bindings
            return 1 if value else 0
        else:
            # For SQLite 
            return 1 if value else 0