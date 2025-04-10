from config.Config import get_config
"""
Monitors active strategy executions for profit targets and stop losses

Runs every minute to check current prices aga,inst strategy conditions
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
        """
        Initialize scheduler with database instance
        
        Args:
            db_path: Path to SQLite database file (DEPRECATED)
        """
        try:
            self.db = PortfolioDB() # Initialize without db_path
            self.analyticsHandler = AnalyticsHandler(self.db)
            self.strategyFramework = StrategyFramework()
            self.monitor = ExecutionMonitor()  # ExecutionMonitor doesn't accept a db parameter
            logger.info(f"Execution Monitor scheduler initialized using database configuration")
        except Exception as e:
            logger.error(f"Error initializing ExecutionMonitorScheduler: {e}")
            # Initialize with minimal dependencies to avoid cascading failures
            self.monitor = ExecutionMonitor()

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
            
            # Try to recover connections if they're closed
            try:
                # Reinitialize classes that may have closed connections
                self.db = PortfolioDB()
                self.analyticsHandler = AnalyticsHandler(self.db)
                self.strategyFramework = StrategyFramework()
                logger.info("Successfully reinitialized connections after error")
            except Exception as re_init_error:
                logger.error(f"Failed to reinitialize connections: {re_init_error}")
                
            return False 