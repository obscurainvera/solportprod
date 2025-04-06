from config.Config import get_config
from enum import Enum
from dataclasses import dataclass

@dataclass
class TradeTypeProperties:
    """Properties for each trade type"""
    value: int
    description: str
    affects_balance: str  # 'INCREASE' or 'DECREASE'

class TradeType(Enum):
    """Enum for trade types with properties"""
    BUY = TradeTypeProperties(
        value=1,
        description="Buy/Entry Trade",
        affects_balance="INCREASE"
    )
    SELL = TradeTypeProperties(
        value=2,
        description="Sell/Exit Trade",
        affects_balance="DECREASE"
    )

    def __init__(self, properties: TradeTypeProperties):
        self._value_ = properties.value
        self.description = properties.description
        self.affects_balance = properties.affects_balance

    @classmethod
    def getDescription(cls, type_value: int) -> str:
        """Get description for trade type value"""
        try:
            trade_type = cls(type_value)
            return trade_type.description
        except ValueError:
            return "Unknown Trade Type"

    @classmethod
    def affectsBalancePositively(cls, type_value: int) -> bool:
        """Check if trade type increases balance"""
        try:
            trade_type = cls(type_value)
            return trade_type.affects_balance == "INCREASE"
        except ValueError:
            return False

    @property
    def value(self) -> int:
        """Get the enum value"""
        return self._value_ 