from config.Config import get_config
from enum import Enum
from dataclasses import dataclass
from typing import Optional

@dataclass
class TokenStatusProperties:
    """Properties for each token status"""
    value: int
    description: str
    minPnl: Optional[float] = None
    maxPnl: Optional[float] = None

class TokenStatus(Enum):
    """
    Enum for token PNL status with properties
    HIGH_PNL_TOKEN: Tokens with PNL > 10000
    LOW_PNL_TOKEN: Tokens with PNL <= 10000
    """
    HIGH_PNL_TOKEN = TokenStatusProperties(
        value=1,
        description="High PNL Token",
        minPnl=10000.0,
        maxPnl=None
    )
    LOW_PNL_TOKEN = TokenStatusProperties(
        value=2,
        description="Low PNL Token",
        minPnl=0.0,
        maxPnl=10000.0
    )

    def __init__(self, properties: TokenStatusProperties):
        self._value_ = properties.value
        self.description = properties.description
        self.minPnl = properties.minPnl
        self.maxPnl = properties.maxPnl

    @classmethod
    def getStatusFromPNL(cls, pnl: float) -> 'TokenStatus':
        """Determine token status based on PNL amount"""
        for status in cls:
            if status.minPnl is not None and status.maxPnl is not None:
                if status.minPnl <= pnl <= status.maxPnl:
                    return status
            elif status.minPnl is not None and pnl >= status.minPnl:
                return status
            elif status.maxPnl is not None and pnl <= status.maxPnl:
                return status
        return cls.LOW_PNL_TOKEN  # Default status

    @classmethod
    def getDescription(cls, statusValue: int) -> str:
        """Get description for status value"""
        try:
            status = cls(statusValue)
            return status.description
        except ValueError:
            return "Unknown Status"

    @property
    def value(self) -> int:
        """Get the enum value"""
        return self._value_ 