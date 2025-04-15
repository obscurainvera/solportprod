from config.Config import get_config


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
from dotenv import load_dotenv
from config.Security import isCookieExpired
import requests

logger = get_logger(__name__)


class VolumeBotScheduler:
    """Manages volume signals collection and scheduling"""

    def __init__(self, dbPath: str = None):
        """
        Initialize scheduler with database instance

        Args:
            dbPath: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB()
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
            logger.info(f"Using cookie: {cookie[:15]}...")

            # Hit the health check API first
            try:
                requests.get('https://solportprod.onrender.com', timeout=10)
            except Exception as api_error:
                logger.warning(f"Health check API call failed: {api_error}. Continuing with processing...")

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
        config = get_config()

        if isCookieExpired(config.VOLUME_EXPIRY):
            logger.warning("Volume cookie expired")
            return False

        self.processVolumeSignal(config.VOLUME_COOKIE, addDelay=True)

    def handleVolumeAnalysisFromAPI(self):
        """Execute volume signals collection and analysis without delays"""
        config = get_config()

        if isCookieExpired(config.VOLUME_EXPIRY):
            logger.warning("Volume cookie expired")
            return False
        return self.processVolumeSignal(cookie=config.VOLUME_COOKIE, addDelay=False)
