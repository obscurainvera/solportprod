from config.Config import get_config
"""
Scheduler to persist all the smart money wallets data from the API
"""

from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.SmartMoneyWalletsAction import SmartMoneyWalletsAction
import time
import random

logger = get_logger(__name__)

class SmartMoneyWalletScheduler:
    """Manages smart money wallets data collection and analysis"""
    
    def __init__(self, dbPath: str = None):
        # dbPath is deprecated
        # if dbPath is None:
        #     dbPath = config.get("DB_PATH")
        """
        Initialize with database connection

        Args:
            dbPath: Path to database file (DEPRECATED)
        """
        self.db = PortfolioDB() # Initialize without dbPath
        self.action = SmartMoneyWalletsAction(self.db)
        logger.info(f"Smart Money Wallet scheduler initialized using database configuration")

    def executeActions(self):
        """Process smart money wallets analysis"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('smartmoneywallets', {})
            if isValidCookie(cookie, 'smartmoneywallets')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for smart money wallets API")
            return False

        for cookie in validCookies:
            try:
                logger.info(f"Using cookie: {cookie[:15]}...")
                
                success = self.action.getAllSmartMoneyWallets(cookie=cookie)
                
                if success:
                    logger.info("Successfully analyzed wallet behaviour")
                else:
                    logger.warning("Failed to analyze wallet behaviour")
                
                # Add delay between requests
                delay = random.uniform(2.0, 5.0)
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Failed to execute wallet behaviour analysis: {e}")
                continue
                
        return True 