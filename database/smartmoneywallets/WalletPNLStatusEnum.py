from config.Config import get_config
from enum import Enum
from dataclasses import dataclass
from typing import Optional

@dataclass
class WalletStatusProperties:
    """Properties for each wallet status"""
    value: int
    description: str
    minProfit: Optional[float] = None
    maxProfit: Optional[float] = None

class SmartWalletPnlStatus(Enum):
    """
    Enum for wallet PNL status with properties
    HIGH_PNL_SM: Wallets with profit > 300K
    LOW_PNL_SM: Wallets with profit <= 300K
    """
    HIGH_PNL_SM = WalletStatusProperties(
        value=1,
        description="High PNL Smart Money",
        minProfit=300000.0,
        maxProfit=None
    )
    LOW_PNL_SM = WalletStatusProperties(
        value=2,
        description="Low PNL Smart Money",
        minProfit=0.0,
        maxProfit=300000.0
    )

    def __init__(self, properties: WalletStatusProperties):
        self._value_ = properties.value
        self.description = properties.description
        self.minProfit = properties.minProfit
        self.maxProfit = properties.maxProfit

    @classmethod
    def getSmartWalletPNLStatus(cls, profit: float) -> 'SmartWalletPnlStatus':
        """Determine wallet status based on profit amount"""
        for status in cls:
            if status.minProfit is not None and status.maxProfit is not None:
                if status.minProfit <= profit <= status.maxProfit:
                    return status
            elif status.minProfit is not None and profit >= status.minProfit:
                return status
            elif status.maxProfit is not None and profit <= status.maxProfit:
                return status
        return cls.LOW_PNL_SM  # Default status

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