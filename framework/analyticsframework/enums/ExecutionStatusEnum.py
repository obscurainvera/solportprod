from config.Config import get_config
from enum import Enum
from dataclasses import dataclass

@dataclass
class ExecutionStatusProperties:
    """Properties for each execution status"""
    value: int
    description: str
    can_trade: bool

class ExecutionStatus(Enum):
    """Enum for execution statuses with properties"""
    ACTIVE = ExecutionStatusProperties(
        value=1,
        description="Execution is active and can trade",
        can_trade=True
    )
    INVESTED = ExecutionStatusProperties(
        value=2,
        description="Execution has partial exits",
        can_trade=True
    )
    TAKING_PROFIT = ExecutionStatusProperties(
        value=3,
        description="Started taking profit",
        can_trade=True
    )
    STOPPED_OUT = ExecutionStatusProperties(
        value=4,
        description="Hit stop loss",
        can_trade=False
    )
    COMPLETED_WITH_MOONBAG = ExecutionStatusProperties(
        value=5,
        description="Completed with moonbag",
        can_trade=False
    )
    COMPLETED = ExecutionStatusProperties(
        value=6,
        description="Fully completed",
        can_trade=False
    )
    FAILED = ExecutionStatusProperties(
        value=7,
        description="Failed during execution",
        can_trade=False
    )

    def __init__(self, properties: ExecutionStatusProperties):
        self._value_ = properties.value
        self.description = properties.description
        self.can_trade = properties.can_trade

    @classmethod
    def getDescription(cls, status_value: int) -> str:
        """Get description for status value"""
        try:
            status = cls(status_value)
            return status.description
        except ValueError:
            return "Unknown Status"

    @classmethod
    def canTrade(cls, status_value: int) -> bool:
        """Check if status allows trading"""
        try:
            status = cls(status_value)
            return status.can_trade
        except ValueError:
            return False

    @classmethod
    def fromValue(cls, value: int) -> 'ExecutionStatus':
        """
        Get enum instance from integer value
        
        Args:
            value: Integer value of the status
            
        Returns:
            ExecutionStatus: Matching enum instance or ACTIVE if not found
        """
        for status in cls:
            if status.value == value:
                return status
        return cls.ACTIVE  # Default to ACTIVE if not found

    @property
    def value(self) -> int:
        """Get the enum value"""
        return self._value_ 