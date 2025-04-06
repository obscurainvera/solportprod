from config.Config import get_config
"""
Abstract base class for notification services
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Union
from framework.notificationframework.NotificationEnums import NotificationSource, ChatGroup, NotificationStatus, NotificationServiceType
from database.operations.schema import Notification, NotificationButton
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager

class AbstractNotificationService(ABC):
    """
    Abstract base class for notification services.
    Defines the interface that all notification services must implement.
    """
    
    def __init__(self, db: DatabaseConnectionManager):
        """
        Initialize the notification service with database connection
        
        Args:
            db: Database connection handler
        """
        self.db = db
        self.serviceType = self.getServiceType()
    
    @abstractmethod
    def getServiceType(self) -> NotificationServiceType:
        """
        Return the type of notification service
        
        Returns:
            NotificationServiceType: Type of notification service (e.g. TELEGRAM)
        """
        pass
    
    @abstractmethod
    def sendNotification(self, notification: Notification) -> bool:
        """
        Send a notification using the service
        
        Args:
            notification: Notification object with message details
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def getChatIdForGroup(self) -> Optional[str]:
        """
        Get the chat ID from credentials
        
        Returns:
            Optional[str]: Chat ID if found, None otherwise
        """
        pass
    
    def mapSourceToChatGroups(self, source: NotificationSource) -> List[ChatGroup]:
        """
        Map a notification source to its corresponding chat groups
        This method can be overridden by subclasses to customize the mapping
        
        Args:
            source: Source of the notification
            
        Returns:
            List[ChatGroup]: List of chat groups for the source
        """
        mapping = {
            NotificationSource.PORTSUMMARY: [ChatGroup.PORTSUMMARY_CHAT],
            NotificationSource.ATTENTION: [ChatGroup.ATTENTION_CHAT],
            NotificationSource.VOLUME: [ChatGroup.VOLUME_CHAT],
            NotificationSource.SYSTEM: [ChatGroup.SYSTEM_CHAT],
            NotificationSource.ERROR: [ChatGroup.ERROR_CHAT]
        }
        
        return mapping.get(source, [ChatGroup.SYSTEM_CHAT])
    
    def createNotification(self, source: NotificationSource, content: str, 
                          chatGroup: Optional[ChatGroup] = None, 
                          buttons: List[NotificationButton] = None) -> Notification:
        """
        Create a notification object
        
        Args:
            source: Source of the notification
            content: Content of the notification message
            chatGroup: Optional chat group, if not provided will be determined by source
            buttons: Optional list of buttons to add to the notification
            
        Returns:
            Notification: Created notification object
        """
        if chatGroup is None:
            # Get the first chat group mapped to this source
            chatGroups = self.mapSourceToChatGroups(source)
            chatGroup = chatGroups[0] if chatGroups else ChatGroup.SYSTEM_CHAT
        
        notification = Notification(
            source=source.value,
            chatgroup=chatGroup.value,
            content=content,
            servicetype=self.serviceType.value,
            buttons=buttons or []
        )
        
        return notification
    
    def sendMessage(self, source: NotificationSource, content: Union[str, object], 
                   chatGroup: Optional[ChatGroup] = None,
                   buttons: List[NotificationButton] = None) -> bool:
        """
        Create and send a notification
        
        Args:
            source: Source of the notification
            content: Content of the message (can be string or object depending on implementation)
            chatGroup: Optional chat group, if not provided will be determined by source
            buttons: Optional list of buttons to add to the notification
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        # Implementation should handle content processing
        raise NotImplementedError("This method should be implemented by subclasses")
        
    def sendTokenNotification(self, source: NotificationSource, tokenContent: object,
                             chatGroup: Optional[ChatGroup] = None) -> bool:
        """
        Send a token notification with structured content
        
        Args:
            source: Source of the notification
            tokenContent: Structured token content
            chatGroup: Optional chat group, if not provided will be determined by source
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        # Implementation should handle tokenContent processing
        raise NotImplementedError("This method should be implemented by subclasses") 