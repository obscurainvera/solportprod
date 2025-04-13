from config.Config import get_config
from enum import Enum, auto
from typing import Optional


class PushSource(Enum):
    """Enum for different sources that can push tokens to analytics framework"""

    SCHEDULER = 0
    API = 1

    @classmethod
    def fromValue(cls, value: int) -> Optional["PushSource"]:
        """
        Get enum instance from value

        Args:
            value: Integer value

        Returns:
            Optional[PushSource]: Corresponding enum instance or None if not found
        """
        for source in cls:
            if source.value == value:
                return source
        return None

    @classmethod
    def fromString(cls, name: str) -> Optional["PushSource"]:
        """
        Get enum instance from string name

        Args:
            name: String name of enum (case insensitive)

        Returns:
            Optional[PushSource]: Corresponding enum instance or None if not found
        """
        try:
            return cls[name.upper()]
        except (KeyError, AttributeError):
            return None
