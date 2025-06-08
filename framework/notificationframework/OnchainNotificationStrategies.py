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
    
    # Track tokens we've already processed to avoid duplicate notifications
    processed_tokens: Set[str] = set()
    
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
            return db.onchain.getExistingTokensInfo(token_ids)
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
        isNewToken = existingToken is None
        
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
            
        Returns:
            bool: True if notification should be sent, False otherwise
        """
        # Check if token is new
        is_new = existingToken is None
        
        # Check if token rank is between 1 and 10
        is_top_ranked = token.rank is not None and 1 <= token.rank <= 10
        
        # Only notify for new tokens with rank 1-10
        if is_new and is_top_ranked:
            logger.info(f"Token {token.name} is new and has rank {token.rank}, will send notification")
            return True
            
        logger.info(f"Token {token.name} does not meet notification criteria: is_new={is_new}, rank={token.rank}")
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
            # "high_liquidity": ChatGroup.LIQUIDITY_CHAT,
            # "price_surge": ChatGroup.PRICE_ALERTS_CHAT,
        }
        
        # Return the mapped chat group or default to ONCHAIN_CHAT
        return strategy_chat_map.get(strategy_name, ChatGroup.ONCHAIN_CHAT)
        
    @staticmethod
    def createNotificationContent(token: OnchainInfo) -> TokenNotificationContent:
        """
        Convert OnchainInfo object to TokenNotificationContent
        
        Args:
            token: OnchainInfo object to convert
            
        Returns:
            TokenNotificationContent: Notification content for the token
        """
        # Format price with appropriate precision
        price_str = f"${token.price:.8f}" if token.price and token.price < 0.01 else f"${token.price:.4f}" if token.price else "Unknown"
        
        # Format liquidity with commas for readability
        liquidity_str = f"${token.liquidity:,.2f}" if token.liquidity else "Unknown"
        
        # Format price change with sign
        price_change_1h = f"{token.price1h:+.2f}%" if token.price1h is not None else "Unknown"
        price_change_24h = f"{token.price24h:+.2f}%" if token.price24h is not None else "Unknown"
        
        return TokenNotificationContent(
            tokenName=token.name,
            tokenSymbol=token.symbol,
            tokenAddress=token.tokenid,
            chain=token.chain,
            price=price_str,
            priceChange1h=price_change_1h,
            priceChange24h=price_change_24h,
            liquidity=liquidity_str,
            volume24h=f"${token.volume24h:,.2f}" if token.volume24h else "Unknown",
            marketCap=f"${token.marketcap:,.2f}" if token.marketcap else "Unknown",
            rank=f"#{token.rank}" if token.rank else "Unknown",
            holders=f"{token.holders:,}" if token.holders else "Unknown",
            makers=f"{token.makers:,}" if token.makers else "Unknown",
            dexScreenerUrl=f"https://dexscreener.com/{token.chain.lower()}/{token.tokenid}"
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
            # Skip if we've already processed this token
            if token.tokenid in cls.processed_tokens:
                logger.info(f"Token {token.name} already processed, skipping notification check")
                return False
                
            # Add to processed tokens set
            cls.processed_tokens.add(token.tokenid)
            
            # Determine which strategy to use and if notification should be sent
            strategy_name = None
            should_notify = False
            
            # Check new top ranked strategy
            if cls.shouldNotifyNewAndTopTanked(token, existingToken):
                strategy_name = "new_top_ranked"
                should_notify = True
            
            # Add more strategy checks here as needed
            # if cls.shouldNotifyHighLiquidity(token, existingToken):
            #     strategy_name = "high_liquidity"
            #     should_notify = True
            
            if not should_notify:
                logger.info(f"Token {token.name} does not meet any notification criteria")
                return False
                
            # Get the appropriate chat group for this strategy
            chat_group = cls.getChatGroupForStrategy(strategy_name)
            logger.info(f"Using strategy '{strategy_name}' with chat group '{chat_group.value}'")
                
            # Convert to notification content
            content = cls.createNotificationContent(token)
            
            # Send notification to the strategy-specific chat group
            result = notificationManager.sendTokenNotification(
                source=NotificationSource.ONCHAIN,
                tokenContent=content,
                chatGroup=chat_group
            )
            
            if result:
                logger.info(f"Successfully sent notification for token {token.name} with rank {token.rank} to {chat_group.value}")
            else:
                logger.warning(f"Failed to send notification for token {token.name} to {chat_group.value}")
                
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
