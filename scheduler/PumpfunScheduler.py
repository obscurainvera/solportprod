from config.Config import get_config

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
from dotenv import load_dotenv
from config.Config import get_config
from config.Security import isCookieExpired
import requests

logger = get_logger(__name__)

# Load environment variables
load_dotenv()


class PumpFunScheduler:
    """Manages pump fun signals collection and scheduling"""

    def __init__(self, dbPath: str = None):
        """
        Initialize scheduler with database instance

        Args:
            dbPath: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB()  # Initialize without dbPath
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

            # Hit the health check API first
            try:
                requests.get('https://solportprod.onrender.com', timeout=10)
            except Exception as api_error:
                logger.warning(f"Health check API call failed: {api_error}. Continuing with processing...")

            # Execute pump fun signals action with validated cookie
            success = self.action.processPumpFunTokens(cookie=cookie)

            if success:
                logger.info("Successfully processed pump fun signals")
            else:
                logger.warning("Failed to process pump fun signals")

            return success

        except Exception as e:
            logger.error(f"Error processing pump fun signals: {e}")
            return False

    def handlePumpFunAnalysisFromJob(self):
        """Process pump fun signals from scheduled job"""

        config = get_config()

        if isCookieExpired(config.PUMPFUN_EXPIRY):
            logger.warning("Pump fun cookie expired")
            return False

        self.processPumpFunSignal(config.PUMPFUN_COOKIE, addDelay=True)

        return True

    def handlePumpFunAnalysisFromAPI(self):
        """Process pump fun signals from API request"""

        config = get_config()


        if isCookieExpired(config.PUMPFUN_EXPIRY):
            logger.warning("Pump fun cookie expired")
            return False

        return self.processPumpFunSignal(cookie=config.PUMPFUN_COOKIE, addDelay=False)
