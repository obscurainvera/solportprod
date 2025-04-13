from config.Config import get_config
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.portsummary.PortfolioHandler import PortfolioHandler
from database.smwalletsbehaviour.SmartMoneyWalletBehaviourHandler import (
    SmartMoneyWalletBehaviourHandler,
)
from database.walletinvested.WalletsInvestedHandler import WalletsInvestedHandler
from database.job.job_handler import JobHandler
from database.smartmoneywallets.SmartMoneyWalletsHandler import SmartMoneyWalletsHandler
from database.smartmoneywallets.SMWalletTopPNLTokenHandler import (
    SMWalletTopPNLTokenHandler,
)
from database.smartmoneywallets.SmartMoneyPerformanceReportHandler import (
    SmartMoneyPerformanceReportHandler,
)
from database.attention.AttentionHandler import AttentionHandler
from database.volume.VolumeHandler import VolumeHandler
from database.pumpfun.PumpfunHandler import PumpFunHandler
from database.auth.TokenHandler import TokenHandler
from database.auth.CredentialsHandler import CredentialsHandler
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.notification.NotificationHandler import NotificationHandler
from typing import Optional, Any, List, Tuple
from logs.logger import get_logger
from framework.analyticsframework.models.BaseModels import (
    ExecutionState,
    BaseStrategyConfig,
)
from sqlalchemy import text

import sys
import traceback
import threading

logger = get_logger(__name__)


class PortfolioDB:
    """
    Main database facade that coordinates between different handlers.
    This class acts as a single entry point for all database operations
    while delegating the actual work to specific handlers.

    Key features:
    - Single shared database connection manager
    - Domain-specific handlers for different operations
    - Unified interface for database operations
    - Cloud-ready with PostgreSQL support
    """

    # Singleton instance and lock
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_url: str = None):
        """
        Singleton pattern implementation to ensure only one database instance exists.

        Args:
            db_url: Database connection URL (can be SQLite file or PostgreSQL connection string)

        Returns:
            PortfolioDB: Single instance of the database handler
        """
        with cls._lock:
            if cls._instance is None:
                # Get the database URL from configuration if not provided
                db_url = db_url or get_config().get_database_url()

                cls._instance = super(PortfolioDB, cls).__new__(cls)
                cls._instance.db_url = db_url
                cls._instance._initialized = False

            return cls._instance

    def __init__(self, db_url: str = None):
        """
        Initialize handlers only once when the instance is first created.
        Subsequent calls to __init__ will not re-initialize handlers.

        Args:
            db_url: Database connection URL
        """
        # Skip initialization if already done
        if hasattr(self, "_initialized") and self._initialized:
            return

        # Store the db_url from __new__ or update it if provided
        if db_url:
            self.db_url = db_url

        self._init_handlers()
        self._initialized = True

    def _init_handlers(self):
        """
        Initialize all database handlers.
        Each handler is responsible for a specific domain of database operations.
        """
        self.conn_manager = DatabaseConnectionManager(self.db_url)

        # Initialize handlers
        self._handlers = {
            "portfolio": PortfolioHandler(self.conn_manager),
            "walletsInvested": WalletsInvestedHandler(self.conn_manager),
            "job": JobHandler(self.conn_manager),
            "smartMoneyWallets": SmartMoneyWalletsHandler(self.conn_manager),
            "smWalletTopPNLToken": SMWalletTopPNLTokenHandler(self.conn_manager),
            "smartMoneyPerformanceReport": SmartMoneyPerformanceReportHandler(
                self.conn_manager
            ),
            "attention": AttentionHandler(self.conn_manager),
            "volume": VolumeHandler(self.conn_manager),
            "pumpfun": PumpFunHandler(self.conn_manager),
            "token": TokenHandler(self.conn_manager),
            "credentials": CredentialsHandler(self.conn_manager),
            "analytics": AnalyticsHandler(self.conn_manager),
            "notification": NotificationHandler(self.conn_manager),
            "smWalletBehaviour": SmartMoneyWalletBehaviourHandler(self.conn_manager),
        }

        # Set direct properties for commonly used handlers for ease of access
        self.portfolio = self._handlers["portfolio"]
        self.walletsInvested = self._handlers["walletsInvested"]
        self.job = self._handlers["job"]
        self.smartMoneyWallets = self._handlers["smartMoneyWallets"]
        self.smWalletTopPNLToken = self._handlers["smWalletTopPNLToken"]
        self.smartMoneyPerformanceReport = self._handlers["smartMoneyPerformanceReport"]
        self.attention = self._handlers["attention"]
        self.volume = self._handlers["volume"]
        self.pumpfun = self._handlers["pumpfun"]
        self.token = self._handlers["token"]
        self.credentials = self._handlers["credentials"]
        self.analytics = self._handlers["analytics"]
        self.notification = self._handlers["notification"]
        self.smWalletBehaviour = self._handlers["smWalletBehaviour"]

        # Also create a handler map for getattr fallback lookup
        self._handler_method_map = {}
        for handler_name, handler in self._handlers.items():
            for method_name in dir(handler):
                # Skip private methods and properties
                if not method_name.startswith("_") and callable(
                    getattr(handler, method_name)
                ):
                    self._handler_method_map[method_name] = handler

    def __getattr__(self, name: str) -> Any:
        """
        Magic method to delegate method calls to appropriate handlers.
        Uses a pre-built method map for O(1) lookup instead of O(n) search.

        Args:
            name: Name of the method being called

        Returns:
            Method from appropriate handler

        Raises:
            AttributeError: If method not found in any handler
        """
        # Fast path - check in pre-built map
        if name in self._handler_method_map:
            return getattr(self._handler_method_map[name], name)

        # Slow path - check attributes of each handler (for non-method attributes)
        for handler in self._handlers.values():
            if hasattr(handler, name):
                return getattr(handler, name)

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def check_connection(self) -> bool:
        """
        Verify database connection is working properly.
        Used for health checks and monitoring.

        Returns:
            bool: True if connection is successful, raises exception otherwise
        """
        try:
            with self.conn_manager.transaction() as session:
                # Simple query to test connection, works for both SQLite and PostgreSQL
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            raise

    def close(self):
        """
        Close database connections. This should only be called
        during application shutdown, not between requests.
        """
        if hasattr(self, "conn_manager"):
            logger.info("Closing PortfolioDB connection manager")
            try:
                self.conn_manager.close()
                logger.info("Successfully closed database connections")
            except Exception as e:
                logger.error(f"Error while closing database connections: {str(e)}")

    def execute_query(self, query: str, params=None):
        """
        Execute a raw SQL query and return the results.
        Query should be database-agnostic or properly formatted for the target database.

        Args:
            query: SQL query to execute (use %s placeholders for PostgreSQL or ? for SQLite)
            params: Optional parameters for the query

        Returns:
            List of dictionaries containing the query results

        Raises:
            Exception: If there's an error executing the query
        """
        try:
            with self.conn_manager.transaction() as session:
                # Always use SQLAlchemy text for PostgreSQL compatibility
                result = session.execute(text(query), params or {})

                # Convert rows to dictionaries
                columns = result.keys()
                results = [dict(zip(columns, row)) for row in result.fetchall()]
                return results

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise

    @property
    def transaction(self):
        """
        Property to access the transaction context manager.

        How to use:
        with db.transaction() as cursor:
            # perform multiple operations in single transaction

        Returns:
            Context manager for database transactions
        """
        return self.conn_manager.transaction

    @property
    def table_lock(self):
        """
        Property to access table locking mechanism.

        How to use:
        with db.table_lock('table_name'):
            # perform thread-safe operations

        Returns:
            Context manager for table locking
        """
        return self.conn_manager.table_lock

    def __enter__(self):
        """
        Context manager entry point.

        How to use:
        with PortfolioDB() as db:
            # use database

        Returns:
            PortfolioDB instance
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        Closes database connection when exiting context.
        """
        self.close()

    def get_handler(self, handler_type: str) -> Optional[Any]:
        """
        Get specific handler instance by type.

        How to use:
        portfolio_handler = db.get_handler('portfolio')

        Args:
            handler_type: Type of handler ('portfolio', 'token_analysis', 'jobs')

        Returns:
            Handler instance or None if not found
        """
        # Map logical handler names to actual handler keys
        handler_mapping = {
            "portfolio": "portfolio",
            "port_summary_report": "portfolio",
            "token_analysis": "walletsInvested",
            "jobs": "job",
            "wallet_behaviour": "smartMoneyWallets",
            "top_pnl_token": "smWalletTopPNLToken",
            "attention": "attention",
            "volume": "volume",
            "pumpfun": "pumpfun",
            "analytics": "analytics",
            "smWalletBehaviour": "smWalletBehaviour",
        }

        handler_key = handler_mapping.get(handler_type, handler_type)
        return self._handlers.get(handler_key)
