from config.Config import get_config
"""
Telegram implementation of the notification service
"""
from typing import Dict, Optional, List, Any, Union
import requests
import json
from datetime import datetime
import pytz
from framework.notificationframework.AbstractNotificationService import AbstractNotificationService
from framework.notificationframework.NotificationEnums import NotificationSource, ChatGroup, NotificationStatus, NotificationServiceType
from database.operations.schema import Notification, NotificationButton
from framework.notificationframework.NotificationContent import TokenNotificationContent
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.auth.ServiceCredentialsEnum import ServiceCredentials, CredentialType
from logs.logger import get_logger

logger = get_logger(__name__)

class TelegramNotificationService(AbstractNotificationService):
    """
    Telegram implementation of the notification service.
    Handles sending messages to Telegram chat groups.
    """
    
    def __init__(self, db: DatabaseConnectionManager):
        """
        Initialize the Telegram notification service
        
        Args:
            db: Database connection handler
        """
        super().__init__(db)
        self.service = ServiceCredentials.get_by_name("telegram")
        self.baseUrl = self.service.metadata.get('base_url', "https://api.telegram.org/bot{token}/sendMessage")
        self.session = requests.Session()
        
    def getServiceType(self) -> NotificationServiceType:
        """
        Return the type of notification service
        
        Returns:
            NotificationServiceType: TELEGRAM
        """
        return NotificationServiceType.TELEGRAM
    
    def getChatIdForGroup(self) -> Optional[str]:
        """
        Get the chat ID from credentials
        
        Returns:
            Optional[str]: Chat ID if found, None otherwise
        """
        try:
            # Get credentials with CHAT_ID type
            credential = self.db.credentials.getCredentialsByType(
                serviceName=self.service.service_name,
                credentialType=CredentialType.CHAT_ID.value
            )
            
            if not credential:
                logger.error(f"No chat ID credentials found for service {self.service.service_name}")
                return None
            
            # The chat ID is stored directly in the apikey column
            return credential.get('apikey')
            
        except Exception as e:
            logger.error(f"Failed to get chat ID: {e}")
            return None
    
    def getBotToken(self) -> Optional[str]:
        """
        Get the bot token from credentials
        
        Returns:
            Optional[str]: Bot token if found, None otherwise
        """
        try:
            # Get API key credentials
            credential = self.db.credentials.getCredentialsByType(
                serviceName=self.service.service_name,
                credentialType=CredentialType.API_KEY.value
            )
            
            if not credential:
                logger.error(f"No bot token credentials found for service {self.service.service_name}")
                return None
            
            return credential.get('apikey')
            
        except Exception as e:
            logger.error(f"Failed to get bot token: {e}")
            return None
    
    def sendNotification(self, notification: Notification) -> bool:
        """
        Send a notification using Telegram
        
        Args:
            notification: Notification object with message details
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        try:
            # Get chat ID
            chatId = self.getChatIdForGroup()
            if not chatId:
                logger.error("No chat ID found")
                self._updateNotificationStatus(notification, NotificationStatus.FAILED, 
                                              "No chat ID found for chat group")
                return False
            
            # Get bot token
            token = self.getBotToken()
            if not token:
                logger.error("No Telegram bot token found")
                self._updateNotificationStatus(notification, NotificationStatus.FAILED, 
                                              "No Telegram bot token found")
                return False
            
            # Construct the URL with the token
            url = self.baseUrl.format(token=token)
            
            # Prepare request payload
            payload = {
                'chat_id': chatId,
                'text': notification.content,
                'parse_mode': 'HTML'
            }
            
            # Add buttons if present
            if notification.buttons:
                inline_keyboard = []
                row = []
                
                for button in notification.buttons:
                    row.append({
                        "text": button.text,
                        "url": button.url
                    })
                    
                    # Create a new row every 2 buttons
                    if len(row) == 2:
                        inline_keyboard.append(row)
                        row = []
                
                # Add any remaining buttons in the last row
                if row:
                    inline_keyboard.append(row)
                    
                # Add reply markup with inline keyboard
                payload['reply_markup'] = {
                    'inline_keyboard': inline_keyboard
                }
            
            # Send the message
            response = self.session.post(
                url,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            
            # Update notification status
            self._updateNotificationStatus(notification, NotificationStatus.SENT)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            self._updateNotificationStatus(notification, NotificationStatus.FAILED, str(e))
            return False
    
    def _updateNotificationStatus(self, notification: Notification, status: NotificationStatus, 
                                 errorDetails: Optional[str] = None) -> None:
        """
        Update the notification status in the database
        
        Args:
            notification: Notification to update
            status: New status to set
            errorDetails: Optional error details if status is FAILED
        """
        try:
            # Update notification fields
            notification.status = status.value
            
            if status == NotificationStatus.SENT:
                # Set sent time
                notification.sentat = datetime.now(pytz.UTC)
                
            if status == NotificationStatus.FAILED and errorDetails:
                # Set error details
                notification.errordetails = errorDetails
                
            notification.updatedat = datetime.now(pytz.UTC)
            
            # Update in database
            if notification.id:
                self.db.notification.updateNotification(notification)
                
        except Exception as e:
            logger.error(f"Failed to update notification status: {e}")
    
    def sendMessage(self, source: NotificationSource, content: Union[str, TokenNotificationContent], 
                   chatGroup: Optional[ChatGroup] = None,
                   buttons: List[NotificationButton] = None) -> bool:
        """
        Simplified interface to send a message
        
        Args:
            source: Source of the notification
            content: Content of the message (string or TokenNotificationContent)
            chatGroup: Optional chat group, if not provided will be determined by source
            buttons: Optional list of buttons to add to the notification
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        try:
            # Process content if it's a TokenNotificationContent
            if isinstance(content, TokenNotificationContent):
                # Format content as string
                content_str = content.formatTelegramMessage()
                
                # Get default buttons for token if none provided
                if not buttons:
                    button_configs = content.getDefaultButtons()
                    buttons = [NotificationButton(text=btn['text'], url=btn['url']) for btn in button_configs]
            else:
                content_str = content
            
            # Follow the notification flow:
            # 1. Create notification object
            notification = self.createNotification(source, content_str, chatGroup, buttons)
            
            # 2. Save to database with pending status
            savedNotification = self.db.notification.createNotification(notification)
            if not savedNotification:
                logger.error("Failed to save notification to database")
                return False
            
            # 3. Send the notification
            return self.sendNotification(savedNotification)
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
            
    def sendTokenNotification(self, source: NotificationSource, 
                             tokenContent: TokenNotificationContent,
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
        return self.sendMessage(source, tokenContent, chatGroup) 