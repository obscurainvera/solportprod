from config.config import get_config
"""
Take all the tokens that came through the pump fun bot and persist them to the database

Runs many times a minute
"""

from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.PumpFunAction import PumpFunAction
import time
import random

logger = get_logger(__name__)

class PumpFunScheduler:
    """Manages pump fun signals collection and scheduling"""
    
    def __init__(self, dbPath: str = None):
        # The dbPath parameter is no longer needed as PortfolioDB gets config internally
        # if dbPath is None:
        #     dbPath = config.get("DB_PATH")
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB() # Initialize without dbPath
        self.action = PumpFunAction(self.db)
        logger.info(f"Pump fun scheduler initialized using database configuration")

    def processPumpFunSignal(self, cookie: str, addDelay: bool = False) -> bool:
        """
        Process pump fun signals for a single cookie
        
        Args:
            cookie: API cookie to use
            addDelay: Whether to add random delay after processing
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Using cookie: {cookie[:15]}...")
            
            # Execute pump fun signals action with validated cookie
            success = self.action.processPumpFunTokens(cookie=cookie)
            
            if success:
                logger.info("Successfully processed pump fun signals")
            else:
                logger.warning("Failed to process pump fun signals")
            
            if addDelay:
                delay = random.uniform(5, 10)
                logger.info(f"Adding random delay of {delay:.2f} seconds")
                time.sleep(delay)
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing pump fun signals: {e}")
            return False

    def handlePumpFunAnalysisFromJob(self):
        """Process pump fun signals from scheduled job"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('pumpfun', {})
            if isValidCookie(cookie, 'pumpfun')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for pump fun API")
            return False

        for cookie in validCookies:
            self.processPumpFunSignal(cookie=cookie, addDelay=True)
        
        return True

    def handlePumpFunAnalysisFromAPI(self):
        """Process pump fun signals from API request"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('pumpfun', {})
            if isValidCookie(cookie, 'pumpfun')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for pump fun API")
            return False

        # Use only one cookie for API requests to minimize delay
        cookie = random.choice(validCookies)
        return self.processPumpFunSignal(cookie=cookie, addDelay=False) 