from config.Config import get_config
"""
Notification Manager
Provides a simple interface for sending notifications
"""
from typing import Dict, List, Optional, Union
from decimal import Decimal
from framework.notificationframework.AbstractNotificationService import AbstractNotificationService
from framework.notificationframework.TelegramNotificationService import TelegramNotificationService
from framework.notificationframework.NotificationEnums import NotificationSource, ChatGroup, NotificationStatus, NotificationServiceType
from database.operations.schema import Notification, NotificationButton
from framework.notificationframework.NotificationContent import TokenNotificationContent
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from logs.logger import get_logger

logger = get_logger(__name__)

class NotificationManager:
    """
    Notification Manager
    Provides a simple interface for sending notifications to various services
    """
    
    def __init__(self, db: DatabaseConnectionManager):
        """
        Initialize the notification manager
        
        Args:
            db: Database connection handler
        """
        self.db = db
        self._registerServices()
    
    def _registerServices(self):
        """Register notification services"""
        self.services = {}
        
        # Register Telegram service
        try:
            telegramService = TelegramNotificationService(self.db)
            self.services[NotificationServiceType.TELEGRAM] = telegramService
            logger.info("Telegram notification service registered")
        except Exception as e:
            logger.error(f"Failed to register Telegram notification service: {e}")
        
        # Register other services here as they are implemented
    
    def sendMessage(self, source: NotificationSource, content: Union[str, TokenNotificationContent], 
                   chatGroup: Optional[ChatGroup] = None,
                   buttons: List[NotificationButton] = None,
                   serviceType: NotificationServiceType = NotificationServiceType.TELEGRAM) -> bool:
        """
        Send a notification message
        
        Args:
            source: Source of the notification
            content: Content of the message (string or TokenNotificationContent)
            chatGroup: Optional chat group, if not provided will be determined by source
            buttons: Optional list of buttons to add to the notification
            serviceType: Type of service to use for sending the message
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        try:
            # Get the notification service
            service = self.services.get(serviceType)
            if not service:
                logger.error(f"No notification service registered for type {serviceType}")
                return False
            
            # Send the message using the selected service
            return service.sendMessage(source, content, chatGroup, buttons)
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def createButton(self, text: str, url: str) -> NotificationButton:
        """
        Create a notification button
        
        Args:
            text: Button text
            url: URL to open when button is clicked
            
        Returns:
            NotificationButton: Created button
        """
        return NotificationButton(text=text, url=url)
    
    def createTokenContent(self, subject: str, contractAddress: str, symbol: str, chain: str, **kwargs) -> TokenNotificationContent:
        """
        Create token notification content
        
        Args:
            subject: Notification subject
            contractAddress: Contract address of the token
            symbol: Token symbol
            chain: Blockchain (e.g., sol, eth)
            **kwargs: Additional token properties
                - tokenName: Full token name
                - currentPrice: Current token price
                - balanceUsd: Total balance in USD
                - marketCap: Market cap
                - liquidity: Liquidity
                - fullyDilutedValue: Fully diluted value
                - holderCount: Number of holders/wallets
                - description: Additional description
                - changePercent1h: 1-hour price change
                - changePercent24h: 24-hour price change
                - txnChartUrl: Transaction chart URL
                - dexScreenerUrl: DexScreener URL
                
        Returns:
            TokenNotificationContent: Structured token content
        """
        # Convert numeric values to Decimal if provided as strings
        numericFields = ['currentPrice', 'balanceUsd', 'marketCap', 'liquidity', 
                          'fullyDilutedValue', 'changePercent1h', 'changePercent24h']
        
        for field in numericFields:
            if field in kwargs and isinstance(kwargs[field], str):
                try:
                    kwargs[field] = Decimal(kwargs[field])
                except:
                    logger.warning(f"Failed to convert {field} to Decimal: {kwargs[field]}")
        
        # Convert holder count to int if provided as string
        if 'holderCount' in kwargs and isinstance(kwargs['holderCount'], str):
            try:
                kwargs['holderCount'] = int(kwargs['holderCount'])
            except:
                logger.warning(f"Failed to convert holderCount to int: {kwargs['holderCount']}")
        
        return TokenNotificationContent(
            subject=subject,
            contractAddress=contractAddress,
            symbol=symbol,
            chain=chain,
            **kwargs
        )
    
    def sendTokenNotification(self, source: NotificationSource, tokenContent: Union[TokenNotificationContent, Dict], 
                             chatGroup: Optional[ChatGroup] = None,
                             serviceType: NotificationServiceType = NotificationServiceType.TELEGRAM) -> bool:
        """
        Send a token notification
        
        Args:
            source: Source of the notification
            tokenContent: TokenNotificationContent object or dict with token data
            chatGroup: Optional chat group, if not provided will be determined by source
            serviceType: Type of service to use for sending the message
            
        Returns:
            bool: True if sending was successful, False otherwise
        """
        try:
            # Convert dict to TokenNotificationContent if needed
            if isinstance(tokenContent, dict):
                
                # Extract subject, contractAddress, symbol, chain
                subject = tokenContent.pop('subject')
                contractAddress = tokenContent.pop('tokenid')
                symbol = tokenContent.pop('name')
                chain = tokenContent.pop('chain')
            
                # Create TokenNotificationContent
                tokenContent = self.createTokenContent(
                    subject=subject,
                    contractAddress=contractAddress,
                    symbol=symbol,
                    chain=chain,
                    **tokenContent
                )
            else:
                tokenContent = tokenContent
            
            # Get the notification service
            service = self.services.get(serviceType)
            if not service:
                logger.error(f"No notification service registered for type {serviceType}")
                return False
            
            # Send token notification
            return service.sendTokenNotification(source, tokenContent, chatGroup)
            
        except Exception as e:
            logger.error(f"Failed to send token notification: {e}")
            return False
    
    def processPendingNotifications(self, limit: int = 10) -> int:
        """
        Process pending notifications
        
        Args:
            limit: Maximum number of notifications to process
            
        Returns:
            int: Number of notifications successfully sent
        """
        try:
            # Get pending notifications
            pendingNotifications = self.db.notification.getPendingNotifications(limit)
            
            if not pendingNotifications:
                logger.info("No pending notifications to process")
                return 0
            
            # Send each notification
            successCount = 0
            for notification in pendingNotifications:
                try:
                    # Get the service type
                    serviceType = NotificationServiceType(notification.servicetype) \
                        if notification.servicetype else NotificationServiceType.TELEGRAM
                    
                    # Get the service
                    service = self.services.get(serviceType)
                    if not service:
                        logger.error(f"No notification service registered for type {serviceType}")
                        continue
                    
                    # Send the notification
                    success = service.sendNotification(notification)
                    if success:
                        successCount += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process notification {notification.id}: {e}")
            
            logger.info(f"Successfully sent {successCount} out of {len(pendingNotifications)} pending notifications")
            return successCount
            
        except Exception as e:
            logger.error(f"Failed to process pending notifications: {e}")
            return 0
    
    def retryFailedNotifications(self, limit: int = 5) -> int:
        """
        Retry failed notifications
        
        Args:
            limit: Maximum number of notifications to retry
            
        Returns:
            int: Number of notifications successfully sent
        """
        try:
            # Get failed notifications
            failedNotifications = self.db.notification.getFailedNotifications(limit)
            
            if not failedNotifications:
                logger.info("No failed notifications to retry")
                return 0
            
            # Retry each notification
            successCount = 0
            for notification in failedNotifications:
                try:
                    # Update status to pending
                    notification.status = NotificationStatus.PENDING.value
                    notification.errordetails = None
                    self.db.notification.updateNotification(notification)
                    
                    # Get the service type
                    serviceType = NotificationServiceType(notification.servicetype) \
                        if notification.servicetype else NotificationServiceType.TELEGRAM
                    
                    # Get the service
                    service = self.services.get(serviceType)
                    if not service:
                        logger.error(f"No notification service registered for type {serviceType}")
                        continue
                    
                    # Send the notification
                    success = service.sendNotification(notification)
                    if success:
                        successCount += 1
                    
                except Exception as e:
                    logger.error(f"Failed to retry notification {notification.id}: {e}")
            
            logger.info(f"Successfully retried {successCount} out of {len(failedNotifications)} failed notifications")
            return successCount
            
        except Exception as e:
            logger.error(f"Failed to retry failed notifications: {e}")
            return 0 