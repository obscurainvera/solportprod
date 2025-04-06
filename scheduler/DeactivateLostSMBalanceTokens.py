from config.Config import get_config
"""
Marks portfolio records as inactive if they haven't been seen for more than 2 days
Runs daily to clean up tokens that are no longer tracked by smart money wallets
"""

from apscheduler.schedulers.background import BackgroundScheduler
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger

logger = get_logger(__name__)

class DeactiveLostSMBalanceTokens:
    """Manages detection and deactivation of tokens no longer tracked by smart money"""
    
    def __init__(self, db_path: str = None):
        # db_path is deprecated
        # if db_path is None:
        #     db_path = config.get("DB_PATH")
        """
        Initialize with database connection
        
        Args:
            db_path: Path to database file (DEPRECATED)
        """
        self.db = PortfolioDB() # Initialize without db_path
        logger.info(f"Deactivation scheduler initialized using database configuration")

    def handleTokenDeactivation(self):
        """Process tokens that should be marked inactive"""
        try:
            # Our updated function can handle the transaction internally
            deactivatedTokens = self.db.portfolio.deactivateTokensLostSMBalance()
            logger.info(f"Deactivated {deactivatedTokens} tokens no longer tracked")
            return True
                
        except Exception as e:
            logger.error(f"Failed to process token deactivation: {e}")
            return False

    