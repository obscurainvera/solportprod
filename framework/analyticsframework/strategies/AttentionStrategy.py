from config.Config import get_config
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import datetime,timedelta
from logs.logger import get_logger
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.BaseModels import (
    BaseTokenData, BaseStrategyConfig, ExecutionState, TradeLog
)
from framework.analyticsframework.models.SourceModels import AttentionTokenData
from framework.analyticsframework.models.StrategyModels import (
    InvestmentInstructions, EntryType, DCARule
)
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from actions.DexscrennerAction import DexScreenerAction
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler

logger = get_logger(__name__)

class AttentionStrategy(BaseStrategy):
    def __init__(self, analyticsHandler: AnalyticsHandler):
        self.analyticsHandler = analyticsHandler
        self.dexScreener = DexScreenerAction()

    def checkEntryConditions(self,tokenData: AttentionTokenData,strategyConfig: BaseStrategyConfig) -> bool:
        """Validate attention-specific entry conditions"""
        
                
        return True

    def validateChartConditions(self,tokenData: AttentionTokenData,chartConditions: Optional[Dict[str, Any]]) -> bool:
        """Validate chart conditions"""
       
            
        # Add chart validation logic
        return True

    def executeInvestment(self, executionId: int, tokenData: AttentionTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """Execute investment based on investment rules"""
        try:
            investmentInstructions = strategyConfig.investmentinstructions
            
            # Get real-time price
            priceData = self.dexScreener.getTokenPrice(tokenData.tokenid)
            if not priceData:
                logger.error(f"Could not get price data for token {tokenData.tokenid}")
                return False
                
            currentPrice = Decimal(str(priceData.price))
            
            # Calculate investment amount
            investmentAmount = Decimal(str(investmentInstructions.allocatedamount))
            if investmentAmount <= 0:
                logger.error(f"Invalid investment amount: {investmentAmount}")
                return False
                
            # Calculate coins to purchase
            coinsToPurchase = investmentAmount / currentPrice
            
            # Log the trade
            tradeLog = TradeLog(
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=investmentAmount,
                tokenprice=currentPrice,
                coins=coinsToPurchase,
                description=f"Initial investment in {tokenData.tokenname}",
                createdat=datetime.now(),
                lastupdatedat=datetime.now()
            )
            
            # Record the trade
            tradeId = self.analyticsHandler.logTrade(tradeLog)
            if not tradeId:
                logger.error(f"Failed to log trade for execution {executionId}")
                return False
                
            logger.info(f"Successfully executed investment for {tokenData.tokenname}: {investmentAmount} at {currentPrice}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing investment: {str(e)}")
            return False

    def _executeBulkInvestment(self, executionId: int,tokenData: AttentionTokenData,investmentInstructions: InvestmentInstructions) -> bool:
        """Execute a bulk investment with attention-based position sizing"""
        try:
            # Calculate position size based on attention score
            baseSize = investmentInstructions.allocatedamount
            attentionMultiplier = min(
                Decimal('2.0'),
                Decimal('1.0') + (tokenData.attentionscore / Decimal('100.0'))
            )
            positionSize = min(
                baseSize * attentionMultiplier,
                investmentInstructions.maxpositionsize
            )

            tradeRecord = TradeLog(
                tradeid=None,
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=positionSize,
                tokenprice=tokenData.price,
                coins=positionSize / tokenData.price,
                fees=Decimal('0'),
                pnl=None,
                pnlpct=None,
                description=f"Bulk entry (Attention Score: {tokenData.attentionscore})",
                createdat=datetime.now()
            )
            
            return self.analyticsHandler.logTrade(tradeRecord)

        except Exception as e:
            logger.error(f"Error executing bulk investment: {str(e)}")
            return False

    def _executeDCAInvestment(self, executionId: int,tokenData: AttentionTokenData,investmentInstructions: InvestmentInstructions) -> bool:
        """Setup DCA investment schedule with attention-based sizing"""
        try:
            if not investmentInstructions.dcarules:
                logger.error("DCA rules not configured")
                return False

            dcaRules = investmentInstructions.dcarules
            currentTime = datetime.now()

            # Adjust DCA amount based on attention score
            attentionMultiplier = min(
                Decimal('1.5'),
                Decimal('1.0') + (tokenData.attentionscore / Decimal('200.0'))
            )
            adjustedAmount = dcaRules.amountperinterval * attentionMultiplier

            firstEntry = TradeLog(
                tradeid=None,
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=adjustedAmount,
                tokenprice=tokenData.price,
                coins=adjustedAmount / tokenData.price,
                fees=Decimal('0'),
                pnl=None,
                pnlpct=None,
                description=f"DCA entry 1/{dcaRules.intervals} (Attention Score: {tokenData.attentionscore})",
                createdat=currentTime
            )

            if not self.analyticsHandler.logTrade(firstEntry):
                return False


            return True

        except Exception as e:
            logger.error(f"Error executing DCA investment: {str(e)}")
            return False

    