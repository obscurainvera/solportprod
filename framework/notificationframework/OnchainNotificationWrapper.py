from config.Config import get_config
"""
Wrapper for converting OnchainInfo objects to notification content
"""
from typing import List, Optional, Dict, Set
from database.operations.schema import OnchainInfo
from framework.notificationframework.NotificationManager import NotificationManager
from framework.notificationframework.OnchainNotificationStrategies import OnchainNotificationStrategies
from logs.logger import get_logger

logger = get_logger(__name__)

class OnchainNotificationWrapper:
    """
    Wrapper class for OnchainNotificationStrategies
    This class is maintained for backward compatibility
    All functionality has been moved to OnchainNotificationStrategies
    """
    
    def __init__(self, notificationManager: NotificationManager):
        """
        Initialize the wrapper with a notification manager
        
        Args:
            notificationManager: NotificationManager instance for sending notifications
        """
        self.notificationManager = notificationManager
    
    def sendTokenNotification(self, token: OnchainInfo, is_new_token: bool) -> bool:
        """
        Send notification for a token if it meets the criteria
        Delegates to OnchainNotificationStrategies
        
        Args:
            token: OnchainInfo object to send notification for
            is_new_token: Whether this token is being parsed for the first time
            
        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        # Create a mock existingToken based on is_new_token flag
        existingToken = None if is_new_token else {}
        
        # Delegate to the strategy class
        return OnchainNotificationStrategies.handleTokenNotification(
            token=token,
            existingToken=existingToken,
            notificationManager=self.notificationManager
        )
    
    def processTokens(self, tokens: List[OnchainInfo]) -> int:
        """
        Process a list of tokens and send notifications for those that meet criteria
        Delegates to OnchainNotificationStrategies
        
        Args:
            tokens: List of OnchainInfo objects to process
            
        Returns:
            int: Number of notifications sent successfully
        """
        # Create a map of token IDs to None (indicating they're all new)
        # This is just for backward compatibility
        existingTokensMap = {token.tokenid: None for token in tokens}
        
        # Delegate to the strategy class
        return OnchainNotificationStrategies.processTokenForNotification(
            tokens=tokens,
            existingTokensMap=existingTokensMap,
            notificationManager=self.notificationManager
        )
