"""
Persists all the attention scores for the that specific time period
"""

from config.Config import get_config
from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.AttentionAction import AttentionAction
import time
import random

logger = get_logger(__name__)

class AttentionScheduler:
    """Manages attention score collection and analysis scheduling"""
    
    def __init__(self, dbPath: str = None):
        # dbPath is deprecated, PortfolioDB handles config internally
        # if dbPath is None:
        #     dbPath = config.get("DB_PATH")
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB() # Initialize without dbPath
        self.action = AttentionAction(self.db)
        logger.info(f"Attention scheduler initialized using database configuration")

    def handleAttentionData(self):
        """Execute attention score collection and analysis"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('attention', {})
            if isValidCookie(cookie, 'attention')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for attention API")
            return False

        try:
            for cookie in validCookies:
                logger.info(f"Using cookie: {cookie[:15]}...")
                
                # Get and process attention scores
                attentionData = self.action.persistAttentionDataFromAPI(cookie=cookie)

                # Update inactive tokens after processing new data
                self.db.attention.updateInactiveTokens()
                logger.info("Updated status of inactive tokens")
                
                if attentionData and len(attentionData) > 0:
                    logger.info(f"Successfully processed {len(attentionData)} attention scores")
                    return True
            
            logger.warning("No attention data received")
            return False
                
        except Exception as e:
            logger.error(f"Failed to execute attention analysis: {str(e)}") 
            return False

    def persistAttentionDataForSolFromAPI(self):
        """Execute Solana-specific attention score collection and analysis"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('attention', {})
            if isValidCookie(cookie, 'attention')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for Solana attention API")
            return False

        try:
            for cookie in validCookies:
                logger.info(f"Using cookie for Solana API: {cookie[:15]}...")
                
                # Get and process Solana attention scores
                attentionData = self.action.persistAttentionDataForSolFromAPI(cookie=cookie)

                # Update inactive tokens after processing new data
                self.db.attention.updateInactiveTokens()
                logger.info("Updated status of inactive Solana tokens")
                
                if attentionData and len(attentionData) > 0:
                    logger.info(f"Successfully processed {len(attentionData)} Solana attention scores")
                    return len(attentionData)
            
            # This code is reachable if no attention data was found for any cookie
            logger.warning("No Solana attention data received")
            return False
                
        except Exception as e:
            logger.error(f"Failed to execute Solana attention analysis: {str(e)}") 
            return False