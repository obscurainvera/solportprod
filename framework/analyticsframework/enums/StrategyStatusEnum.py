from config.Config import get_config
from enum import Enum
from dataclasses import dataclass

@dataclass
class StrategyStatusProperties:
    """Properties for each strategy status"""
    value: int
    description: str

class StrategyStatus(Enum):
    """Enum for strategy statuses with properties"""
    INACTIVE = StrategyStatusProperties(
        value=0,
        description="Strategy is inactive and not processing"
    )
    ACTIVE = StrategyStatusProperties(
        value=1,
        description="Strategy is active and processing"
    )
    PAUSED = StrategyStatusProperties(
        value=2,
        description="Strategy is temporarily paused"
    )
    ARCHIVED = StrategyStatusProperties(
        value=3,
        description="Strategy is archived and cannot be reactivated"
    )

    def __init__(self, properties: StrategyStatusProperties):
        self._value_ = properties.value
        self.description = properties.description

    @classmethod
    def getDescription(cls, status_value: int) -> str:
        """Get description for status value"""
        try:
            status = cls(status_value)
            return status.description
        except ValueError:
            return "Unknown Status"

    @property
    def value(self) -> int:
        """Get the enum value"""
        return self._value_ 