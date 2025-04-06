from config.Config import get_config
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.BaseModels import (
    BaseStrategyConfig, ExecutionState, TradeLog
)
from framework.analyticsframework.models.SourceModels import PumpFunTokenData
from framework.analyticsframework.models.StrategyModels import (
    EntryType, DCARule, InvestmentInstructions
)
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from actions.DexscrennerAction import DexScreenerAction
from logs.logger import get_logger

logger = get_logger(__name__)

class PumpFunStrategy(BaseStrategy):
    def __init__(self, analyticsHandler: AnalyticsHandler):
        self.analyticsHandler = analyticsHandler
        self.dexScreener = DexScreenerAction()

    def checkEntryConditions(self, tokenData: PumpFunTokenData,strategyConfig: BaseStrategyConfig) -> bool:
        """Validate pump and fun token specific entry conditions"""
        
            
        return True

    def validateChartConditions(self,tokenData: PumpFunTokenData,chartConditions: Optional[Dict[str, Any]]) -> bool:
        """Validate chart conditions for pump tokens"""
    
            
        return True

    def executeInvestment(self, executionId: int, tokenData: PumpFunTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """Execute investment based on pump metrics"""
        try:
            investmentInstructions = strategyConfig.investmentinstructions
            
            # Get real-time price
            priceData = self.dexScreener.getTokenPrice(tokenData.tokenid)
            if not priceData:
                logger.error(f"Failed to get real-time price for token {tokenData.tokenid}")
                return False
                
            # Update token data with real-time price
            realTimePrice = Decimal(str(priceData.price))
        
            
            tokenData.price = realTimePrice
            
            if investmentInstructions.entrytype == EntryType.BULK.name:
                return self._executeBulkInvestment(
                    executionId,
                    tokenData,
                    investmentInstructions
                )
            elif investmentInstructions.entrytype == EntryType.DCA.name:
                return self._executeDCAInvestment(
                    executionId,
                    tokenData,
                    investmentInstructions
                )
            else:
                logger.error(f"Unknown entry type: {investmentInstructions.entrytype}")
                return False

        except Exception as e:
            logger.error(f"Error executing investment: {str(e)}")
            return False

    def _executeBulkInvestment(self, executionId: int,tokenData: PumpFunTokenData,investmentInstructions: InvestmentInstructions) -> bool:
        """Execute a bulk investment with pump-based position sizing"""
        try:
            # Calculate position size based on pump and meme scores
            baseSize = Decimal(str(investmentInstructions.allocatedamount))

            # Ensure price is Decimal
            tokenPrice = Decimal(str(tokenData.price))

            tradeRecord = TradeLog(
                tradeid=None,
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=baseSize,
                tokenprice=tokenPrice,
                coins=baseSize / tokenPrice,
                description=f"Bulk entry (Repeats: {tokenData.percentilerankpepeats}, Sol Spent: {tokenData.percentileranksol})",
                createdat=datetime.now()
            )
            
            return self.analyticsHandler.logTrade(tradeRecord)

        except Exception as e:
            logger.error(f"Error executing bulk investment: {str(e)}")
            return False

    def _executeDCAInvestment(self, executionId: int,tokenData: PumpFunTokenData,investmentInstructions: InvestmentInstructions) -> bool:
        """Setup DCA investment schedule with pump-based sizing"""
        try:
            if not investmentInstructions.dcarules:
                logger.error("DCA rules not configured")
                return False

            dcaRules = investmentInstructions.dcarules
            currentTime = datetime.now()

            # Ensure price is Decimal
            tokenPrice = Decimal(str(tokenData.price))

            # Adjust DCA amount based on pump metrics
            pumpMultiplier = min(
                Decimal('1.5'),
                Decimal('1.0') + (tokenData.pumpscore / Decimal('200.0'))
            )
            adjustedAmount = Decimal(str(dcaRules.amountperinterval)) * pumpMultiplier

            firstEntry = TradeLog(
                tradeid=None,
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=adjustedAmount,
                tokenprice=tokenPrice,
                coins=adjustedAmount / tokenPrice,
                description=f"DCA entry 1/{dcaRules.intervals} (Pump Score: {tokenData.pumpscore})",
                createdat=currentTime
            )

            if not self.analyticsHandler.logTrade(firstEntry):
                return False

            return True

        except Exception as e:
            logger.error(f"Error executing DCA investment: {str(e)}")
            return False

    