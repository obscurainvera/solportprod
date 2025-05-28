from config.Config import get_config


"""
Take all the tokens from the onchain data and persist them to the database

Runs many times a minute
"""

from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.OnchainAction import OnchainAction
import time
import random
from dotenv import load_dotenv
from config.Security import isCookieExpired
import requests

logger = get_logger(__name__)


class OnchainScheduler:
    """Manages onchain data collection and scheduling"""

    def __init__(self, dbPath: str = None):
        """
        Initialize scheduler with database instance

        Args:
            dbPath: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB()
        self.action = OnchainAction(self.db)
        logger.info(f"Onchain scheduler initialized using database configuration")

    def processOnchainData(self, cookie: str, addDelay: bool = False) -> bool:
        """
        Process onchain data for a single cookie

        Args:
            cookie: API cookie to use
            addDelay: Whether to add random delay after processing
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Using cookie: {cookie[:15]}...")

            # Hit the health check API first
            try:
                requests.get('https://solportprod.onrender.com', timeout=10)
            except Exception as api_error:
                logger.warning(f"Health check API call failed: {api_error}. Continuing with processing...")

            # Execute onchain data action with validated cookie
            success = self.action.processOnchainTokens(cookie=cookie)

            if success:
                logger.info("Successfully processed onchain data")
            else:
                logger.warning("Failed to process onchain data")

            return success

        except Exception as e:
            logger.error(f"Error processing onchain data: {e}")
            return False

    def handleOnchainAnalysisFromJob(self):
        """Execute onchain data collection and analysis with delays"""
        config = get_config()

        if isCookieExpired(config.VOLUME_EXPIRY):  # Using the same cookie as volume for now
            logger.warning("Volume cookie expired")
            return False

        self.processOnchainData(config.VOLUME_COOKIE, addDelay=True)

    def handleOnchainAnalysisFromAPI(self):
        """Execute onchain data collection and analysis without delays"""
        config = get_config()

        if isCookieExpired(config.VOLUME_EXPIRY):  # Using the same cookie as volume for now
            logger.warning("Volume cookie expired")
            return False
        return self.processOnchainData(cookie=config.VOLUME_COOKIE, addDelay=False)
