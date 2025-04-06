from config.Config import get_config
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from decimal import Decimal
from framework.analyticsframework.models.BaseModels import (
    BaseTokenData, BaseStrategyConfig, ExecutionState
)


class BaseStrategy(ABC):
    """Base interface for all strategy implementations"""
    
    @abstractmethod
    def checkEntryConditions(self, tokenData: BaseTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """Validate source-specific entry conditions"""
        pass

    @abstractmethod
    def validateChartConditions(self, tokenData: BaseTokenData, chartConditions: Optional[Dict[str, Any]]) -> bool:
        """Validate chart patterns and conditions"""
        pass

    @abstractmethod
    def executeInvestment(self, executionId: int, tokenData: BaseTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """
        Execute investment based on strategy configuration
        
        Args:
            executionId: Active execution ID
            tokenData: Current token data
            strategyConfig: Strategy configuration with investment rules
            
        Returns:
            bool: True if investment was executed successfully
        """
        pass
   