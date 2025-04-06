from config.Config import get_config
"""
Monitors active strategy executions for profit targets and stop losses

Runs every minute to check current prices against strategy conditions
"""

from framework.analyticsframework.ExecutionMonitor import ExecutionMonitor
from framework.analyticsframework.StrategyFramework import StrategyFramework
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger
import time

logger = get_logger(__name__)

class ExecutionMonitorScheduler:
    """Manages execution monitoring scheduling"""
    
    def __init__(self, db_path: str = None):
        # db_path is deprecated
        # if db_path is None:
        #     db_path = config.get("DB_PATH")
        """
        Initialize scheduler with database instance
        
        Args:
            db_path: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB() # Initialize without db_path
        self.analyticsHandler = AnalyticsHandler(self.db)
        self.strategyFramework = StrategyFramework()
        self.monitor = ExecutionMonitor(self.db)
        logger.info(f"Execution Monitor scheduler initialized using database configuration")

    def handleActiveExecutionsMonitoring(self):
        """Monitor all active executions for profit targets and stop losses"""
        try:
            logger.info("Starting active executions monitoring...")
            
            # Monitor active executions
            monitoringStats = self.monitor.monitorActiveExecutions()
            
            if monitoringStats:
                logger.info(f"Monitoring completed: {monitoringStats}")
                return True
            
            logger.warning("No active executions to monitor")
            return False
            
        except Exception as e:
            logger.error(f"Failed to monitor active executions: {e}")
            return False 