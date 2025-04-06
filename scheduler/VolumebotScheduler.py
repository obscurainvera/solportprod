from config.config import get_config
"""
Take all the tokens that came through the volume bot and persist them to the database

Runs many times a minute
"""

from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.VolumebotAction import VolumebotAction
import time
import random

logger = get_logger(__name__)

class VolumeBotScheduler:
    """Manages volume signals collection and scheduling"""
    
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
        self.action = VolumebotAction(self.db)
        logger.info(f"Volume bot scheduler initialized using database configuration")

    def processVolumeSignal(self, cookie: str, addDelay: bool = False) -> bool:
        """
        Process volume signals for a single cookie
        
        Args:
            cookie: API cookie to use
            addDelay: Whether to add random delay after processing
        Returns:
            bool: Success status
        """
        try:
            if addDelay:
                delay = random.uniform(5, 10)
                logger.info(f"Adding random delay of {delay:.2f} seconds")
                time.sleep(delay)

            logger.info(f"Using cookie: {cookie[:15]}...")
            
            # Execute volume signals action with validated cookie
            success = self.action.processVolumebotTokens(cookie=cookie)
            
            if success:
                logger.info("Successfully processed volume signals")
            else:
                logger.warning("Failed to process volume signals")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing volume signals: {e}")
            return False

    def handleVolumeAnalysisFromJob(self):
        """Execute volume signals collection and analysis with delays"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('volumebot', {})
            if isValidCookie(cookie, 'volumebot')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for volume API")
            return

        for cookie in validCookies:
            self.processVolumeSignal(cookie, addDelay=True)

    def handleVolumeAnalysisFromAPI(self):
        """Execute volume signals collection and analysis without delays"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('volumebot', {})
            if isValidCookie(cookie, 'volumebot')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for volume API")
            return

        # Use only one cookie for API requests to minimize delay
        cookie = random.choice(validCookies)
        return self.processVolumeSignal(cookie=cookie, addDelay=False)