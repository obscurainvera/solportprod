from config.Config import get_config
"""
Strategies for determining which onchain tokens should trigger notifications
"""
from typing import Optional, Dict, Any, List, Set, Tuple
from database.operations.schema import OnchainInfo
from database.operations.PortfolioDB import PortfolioDB
from database.onchain.OnchainHandler import OnchainHandler
from framework.notificationframework.NotificationManager import NotificationManager
from framework.notificationframework.NotificationContent import TokenNotificationContent
from framework.notificationframework.NotificationEnums import NotificationSource, ChatGroup
from logs.logger import get_logger

logger = get_logger(__name__)

class OnchainNotificationStrategies:
    """
    Strategies for determining which onchain tokens should trigger notifications
    This class centralizes all notification criteria for easier management and modification
    """
    
    @classmethod
    def getOnchainTokenInfo(cls, db: PortfolioDB, token_ids: List[str]) -> Dict[str, Dict]:
        """
        Get information about existing tokens efficiently in a single database query
        
        Args:
            db: Database instance
            token_ids: List of token IDs to check
            
        Returns:
            Dict[str, Dict]: Dictionary mapping token IDs to their info
        """
        if not token_ids:
            return {}
            
        try:
            # Use the efficient batch query method
            return db.onchain.getOnchainInfoTokens(token_ids)
        except Exception as e:
            logger.error(f"Error getting existing tokens info: {str(e)}")
            return {}
    
    @staticmethod
    def is_new_token(token: OnchainInfo, existingToken: Optional[Dict]) -> bool:
        """
        Determine if a token is new (not previously seen in the database)
        
        Args:
            token: OnchainInfo object to evaluate
            existingToken: Token info from database if exists, None if new
            
        Returns:
            bool: True if token is new, False otherwise
        """
        isNewToken = existingToken is not None and existingToken.get('count', 0) == 1
        
        if isNewToken:
            logger.info(f"Found new token: {token.name} with rank {token.rank}")
            
        return isNewToken
    
    @staticmethod
    def is_top_ranked(token: OnchainInfo, min_rank: int = 1, max_rank: int = 10) -> bool:
        """
        Determine if a token has a top rank within the specified range
        
        Args:
            token: OnchainInfo object to evaluate
            min_rank: Minimum rank (inclusive)
            max_rank: Maximum rank (inclusive)
            
        Returns:
            bool: True if token rank is within range, False otherwise
        """
        if token.rank and min_rank <= token.rank <= max_rank:
            logger.info(f"Token {token.name} has top rank: {token.rank}")
            return True
            
        return False
    
    @staticmethod
    def has_high_liquidity(token: OnchainInfo, min_liquidity: float = 50000) -> bool:
        """
        Determine if a token has high liquidity
        
        Args:
            token: OnchainInfo object to evaluate
            min_liquidity: Minimum liquidity threshold
            
        Returns:
            bool: True if token has high liquidity, False otherwise
        """
        if token.liquidity and token.liquidity > min_liquidity:
            logger.info(f"Token {token.name} has high liquidity: {token.liquidity}")
            return True
            
        return False
    
    @staticmethod
    def has_high_price_change(token: OnchainInfo, min_change_percent: float = 5) -> bool:
        """
        Determine if a token has significant price change in the last hour
        
        Args:
            token: OnchainInfo object to evaluate
            min_change_percent: Minimum price change percentage
            
        Returns:
            bool: True if token has significant price change, False otherwise
        """
        if token.price1h and token.price1h > min_change_percent:
            logger.info(f"Token {token.name} has high price change: {token.price1h}%")
            return True
            
        return False
    
    @staticmethod
    def has_many_makers(token: OnchainInfo, min_makers: int = 100) -> bool:
        """
        Determine if a token has a high number of makers
        
        Args:
            token: OnchainInfo object to evaluate
            min_makers: Minimum number of makers
            
        Returns:
            bool: True if token has many makers, False otherwise
        """
        if token.makers and token.makers > min_makers:
            logger.info(f"Token {token.name} has many makers: {token.makers}")
            return True
            
        return False
    
    @staticmethod
    def shouldNotifyNewAndTopTanked(token: OnchainInfo, existingToken: Optional[Dict]) -> bool:
        """
        Current notification strategy: Only notify for new tokens with rank 1-10
        
        Args:
            token: OnchainInfo object to check
            existingToken: Existing token info from database or None if token is new
            x
        Returns:
            bool: True if notification should be sent, False otherwise
        """
        isNewToken = OnchainNotificationStrategies.is_new_token(token, existingToken)
        isTopRanked = OnchainNotificationStrategies.is_top_ranked(token, 1, 2)
        
        if isTopRanked:
            logger.info(f"Will send notification for new token {token.name} with rank {token.rank}")
            return True
        
        return False
        
    @staticmethod
    def getChatGroupForStrategy(strategy_name: str) -> ChatGroup:
        """
        Get the appropriate chat group for a notification strategy
        Different strategies may send notifications to different chat groups
        
        Args:
            strategy_name: Name of the strategy being used
            
        Returns:
            ChatGroup: The chat group to send notifications to
        """
        # Map strategies to chat groups
        strategy_chat_map = {
            "new_top_ranked": ChatGroup.ONCHAIN_CHAT,
            # Add more strategies and their target chat groups as needed
            
        }
        
        # Return the mapped chat group or default to ONCHAIN_CHAT
        return strategy_chat_map.get(strategy_name, ChatGroup.ONCHAIN_CHAT)
        
    @staticmethod
    def createNotificationContent(onchainTokenInfo: OnchainInfo, strategyName: str) -> TokenNotificationContent:
        """
        Convert OnchainInfo object to TokenNotificationContent
        
        Args:
            token: OnchainInfo object to convert
            
        Returns:
            TokenNotificationContent: Notification content for the token
        """
    
        
        return TokenNotificationContent(
        subject=strategyName,
        tokenid=onchainTokenInfo.tokenid,
        name=onchainTokenInfo.name,
        chain=onchainTokenInfo.chain,
        price=onchainTokenInfo.price,
        marketcap=onchainTokenInfo.marketcap,
        liquidity=onchainTokenInfo.liquidity,
        makers=onchainTokenInfo.makers,
        rank=onchainTokenInfo.rank,
        id=onchainTokenInfo.id,
        onchaininfoid=onchainTokenInfo.onchaininfoid,
        age=onchainTokenInfo.age,
        count=onchainTokenInfo.count,
        createdat=onchainTokenInfo.createdat,
        updatedat=onchainTokenInfo.updatedat,
        dexScreenerUrl=f"https://dexscreener.com/{onchainTokenInfo.chain.lower()}/{onchainTokenInfo.tokenid}"
    )
        
    @classmethod
    def handleNotification(cls, token: OnchainInfo, existingToken: Optional[Dict], notificationManager: NotificationManager) -> bool:
        """
        Process a token and send notification if it meets the criteria
        
        Args:
            token: OnchainInfo object to process
            existingToken: Existing token info from database or None if token is new
            notificationManager: NotificationManager instance for sending notifications
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            # Determine which strategy to use and if notification should be sent
            strategyName = None
            shouldNotify = False
            
            # Check new top ranked strategy
            if cls.shouldNotifyNewAndTopTanked(token, existingToken):
                strategyName = "new_top_ranked"
                shouldNotify = True
            
            # Add more strategy checks here as needed
            # if cls.shouldNotifyHighLiquidity(token, existingToken):
            #     strategy_name = "high_liquidity"
            #     should_notify = True
            
            if not shouldNotify:
                logger.info(f"Token {token.name} does not meet any notification criteria")
                return False
                
            # Get the appropriate chat group for this strategy
            chatGroup = cls.getChatGroupForStrategy(strategyName)
            logger.info(f"Using strategy '{strategyName}' with chat group '{chatGroup.value}'")
                
            # Convert to notification content
            content = cls.createNotificationContent(token,strategyName)
            
            # Send notification to the strategy-specific chat group
            result = notificationManager.sendTokenNotification(
                source=NotificationSource.ONCHAIN,
                tokenContent=content,
                chatGroup=chatGroup
            )
            
            if result:
                logger.info(f"Successfully sent notification for token {token.name} with rank {token.rank} to {chatGroup.value}")
            else:
                logger.warning(f"Failed to send notification for token {token.name} to {chatGroup.value}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error processing token {token.name} for notification: {str(e)}")
            return False
            
    @classmethod
    def sendNotification(cls, tokens: List[OnchainInfo], db: PortfolioDB, notificationManager: NotificationManager) -> int:
        """
        Process a list of tokens and send notifications for those that meet criteria
        
        Args:
            tokens: List of OnchainInfo objects to process
            db: Database instance to efficiently query existing tokens
            notificationManager: NotificationManager instance for sending notifications
            
        Returns:
            int: Number of notifications sent successfully
        """
        if not tokens:
            logger.info("No tokens to process for notifications")
            return 0
            
        sentCount = 0
        
        # Extract all token IDs
        tokenIds = [token.tokenid for token in tokens]
        
        # Get existing tokens info in a single efficient query
        exsistingOnchainTokens = cls.getOnchainTokenInfo(db, tokenIds)
        logger.info(f"Found {len(exsistingOnchainTokens)} existing tokens out of {len(tokenIds)} total tokens")
        
        # Process tokens that meet notification criteria
        for token in tokens:
            try:
                # Get existing token info if available
                existingToken = exsistingOnchainTokens.get(token.tokenid)
                
                # Process token for notification
                if cls.handleNotification(token, existingToken, notificationManager):
                    sentCount += 1
                    
            except Exception as e:
                logger.error(f"Error processing token {token.name}: {str(e)}")
                continue
                
        logger.info(f"Sent {sentCount} onchain token notifications")
        return sentCount
