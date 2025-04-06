from config.Config import get_config
from enum import Enum
from dataclasses import dataclass
from typing import Type
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.strategies.PortSummaryStrategy import PortSummaryStrategy
from framework.analyticsframework.strategies.AttentionStrategy import AttentionStrategy
from framework.analyticsframework.strategies.VolumeStrategy import VolumeStrategy
from framework.analyticsframework.strategies.PumpfunStrategy import PumpFunStrategy
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler

@dataclass
class SourceHandlerProperties:
    """Properties for each source handler"""
    source_type: SourceType
    handler_class: Type[BaseStrategy]
    description: str

class SourceHandler(Enum):
    """Enum for source types and their corresponding handlers"""
    PORTSUMMARY = SourceHandlerProperties(
        source_type=SourceType.PORTSUMMARY,
        handler_class=PortSummaryStrategy,
        description="Portfolio and wallet analysis handler"
    )
    ATTENTION = SourceHandlerProperties(
        source_type=SourceType.ATTENTION,
        handler_class=AttentionStrategy,
        description="Attention and momentum tracking handler"
    )
    VOLUME = SourceHandlerProperties(
        source_type=SourceType.VOLUME,
        handler_class=VolumeStrategy,
        description="Volume and liquidity tracking handler"
    )
    PUMPFUN = SourceHandlerProperties(
        source_type=SourceType.PUMPFUN,
        handler_class=PumpFunStrategy,
        description="Pump and meme detection handler"
    )

    def __init__(self, properties: SourceHandlerProperties):
        self._value_ = properties.source_type.value
        self.source_type = properties.source_type
        self.handler_class = properties.handler_class
        self.description = properties.description

    @classmethod
    def getHandler(cls, source_type: SourceType) -> Type[BaseStrategy]:
        """Get handler class for source type"""
        for handler in cls:
            if handler.source_type == source_type:
                return handler.handler_class
        raise ValueError(f"No handler found for source type: {source_type}")

    @classmethod
    def createHandler(cls, source_type: SourceType, analytics_handler: AnalyticsHandler) -> BaseStrategy:
        """Create handler instance for source type"""
        handler_class = cls.getHandler(source_type)
        return handler_class(analytics_handler)

    @classmethod
    def getAllHandlers(cls, analytics_handler: AnalyticsHandler) -> dict:
        """Get all handlers as a dictionary"""
        return {
            handler.source_type.value: handler.createHandler(handler.source_type, analytics_handler)
            for handler in cls
        }

    @property
    def value(self) -> str:
        """Get the enum value"""
        return self._value_ 