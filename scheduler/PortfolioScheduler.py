from config.Config import get_config
"""
Takes all the token help by smart money through portfolio summary api and persists them to the database

Runs every four hours

"""
from apscheduler.schedulers.background import BackgroundScheduler
from actions.portfolio.PortfolioSummaryAction import PortfolioSummaryAction
from config.Constants import PORTFOLIO_CATEGORIES
from config.Security import COOKIE_MAP, isValidCookie
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger
import time
import random
from actions.portfolio.PortfolioTaggerAction import PortfolioTaggerAction
logger = get_logger(__name__)

class PortfolioScheduler:
    """Manages portfolio data collection and scheduling"""
    
    def __init__(self, dbPath: str = None):
        # dbPath is deprecated
        # if dbPath is None:
        #     dbPath = config.get("DB_PATH")
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file (DEPRECATED)
        """
        self.db = PortfolioDB() # Initialize without dbPath
        self.action = PortfolioSummaryAction(self.db)
        logger.info(f"Portfolio scheduler initialized using database configuration")

    def handlePortfolioSummaryUpdate(self):
        """
        Execute portfolio update if valid cookie exists
        
        Returns:
            dict: Portfolio update statistics
        """
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('portfolio', {})
            if isValidCookie(cookie, 'portfolio')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for portfolio actions")
            return

        logger.info("Starting portfolio update cycle")
        
        # Track all tokens seen across all categories
        allReceivedTokenIds = []
        categoriesProcessed = 0
        totalTokensProcessed = 0
        totalTokensInserted = 0
        totalTokensUpdated = 0
        totalTokensReactivated = 0

        for cookie in validCookies:
            try:
                logger.debug(f"Using cookie: {cookie[:15]}...")
                
                # Iterate through portfolio categories
                for category in PORTFOLIO_CATEGORIES:
                    stats = self.action.getPortfolioSummaryAPIData(
                        cookie=cookie,
                        marketAge=category["market_age"],
                        pnlWallet=category["pnl_wallet"],
                        ownership=category["ownership"]
                    )
                    
                    if stats and 'tokenIds' in stats:
                        categoriesProcessed += 1
                        tokensProcessed = stats.get('processed', 0)
                        totalTokensProcessed += tokensProcessed
                        
                        # Add token IDs to our list
                        allReceivedTokenIds += stats['tokenIds']
                        
                        # Update statistics
                        tokensInserted = stats.get('inserted', 0)
                        tokensUpdated = stats.get('updated', 0)
                        tokensReactivated = stats.get('reactivated', 0)
                        
                        totalTokensInserted += tokensInserted
                        totalTokensUpdated += tokensUpdated
                        totalTokensReactivated += tokensReactivated
                        
                        logger.info(f"Received {len(stats['tokenIds'])} tokens from category {category['market_age']}")
                        logger.info(f"Processed {tokensProcessed} tokens from {category['market_age']}. "
                                   f"Inserted: {tokensInserted}, Updated: {tokensUpdated}, Reactivated: {tokensReactivated}")
                        
                    # Sleep between API calls
                    delay = random.uniform(10, 15)
                    logger.info(f"Sleeping for {delay} seconds")
                    time.sleep(delay)
                    logger.info("Sleep completed")
                
            except Exception as e:
                logger.error(f"Failed to execute action: {str(e)}")

        # After processing all categories and collecting all tokens,
        # mark tokens that weren't seen in any API response as inactive
        if categoriesProcessed > 0:
            # Get unique token IDs (remove duplicates)
            uniqueTokenIds = list(set(allReceivedTokenIds))
            logger.info(f"Processed {categoriesProcessed} categories with {totalTokensProcessed} total tokens")
            logger.info(f"Found {len(uniqueTokenIds)} unique tokens across all categories")
            
            # Mark tokens not in any response as inactive
            tokensMarkedInactive = self.action.markInactiveTokens(uniqueTokenIds)
            logger.info(f"Marked {tokensMarkedInactive} tokens as inactive after processing all categories")
            
            logger.info(f"Portfolio update job completed. "
                      f"Categories processed: {categoriesProcessed}, "
                      f"Total tokens processed: {totalTokensProcessed}, "
                      f"Unique tokens: {len(uniqueTokenIds)}, "
                      f"Tokens inserted: {totalTokensInserted}, "
                      f"Tokens updated: {totalTokensUpdated}, "
                      f"Tokens reactivated: {totalTokensReactivated}, "
                      f"Tokens marked inactive: {tokensMarkedInactive}")
            
        # Add tags and push tokens to strategy framework
        # PortfolioTaggerAction(self.db).addTagsToActivePortSummaryTokens()
        # self.action.pushPortSummaryTokensToStrategyFramework()
        
        return {
            "categoriesProcessed": categoriesProcessed,
            "totalTokensProcessed": totalTokensProcessed,
            "uniqueTokensProcessed": len(set(allReceivedTokenIds)) if allReceivedTokenIds else 0,
            "tokensInserted": totalTokensInserted,
            "tokensUpdated": totalTokensUpdated,
            "tokensReactivated": totalTokensReactivated,
            "tokensMarkedInactive": tokensMarkedInactive if 'tokensMarkedInactive' in locals() else 0
        }