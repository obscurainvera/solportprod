from config.Config import get_config
"""
Enums for the notification framework
"""
from enum import Enum
from typing import Dict, List, Optional

class NotificationSource(Enum):
    """
    Enum for notification message sources
    Each source represents a different part of the application that can send notifications
    """
    PORTSUMMARY = "PORTSUMMARY"
    ATTENTION = "ATTENTION"
    VOLUME = "VOLUME"
    SYSTEM = "SYSTEM"
    ERROR = "ERROR"
    
    def __str__(self) -> str:
        return self.value

class ChatGroup(Enum):
    """
    Enum for notification chat groups
    Each chat group represents a different target group for notifications
    """
    PORTSUMMARY_CHAT = "PORTSUMMARY_CHAT"
    ATTENTION_CHAT = "ATTENTION_CHAT"
    VOLUME_CHAT = "VOLUME_CHAT"
    SYSTEM_CHAT = "SYSTEM_CHAT"
    ERROR_CHAT = "ERROR_CHAT"
    
    def __str__(self) -> str:
        return self.value

class NotificationStatus(Enum):
    """
    Enum for notification message status
    """
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    
    def __str__(self) -> str:
        return self.value

class NotificationServiceType(Enum):
    """
    Enum for notification service types
    """
    TELEGRAM = "TELEGRAM"
    SLACK = "SLACK"
    EMAIL = "EMAIL"
    
    def __str__(self) -> str:
        return self.value 