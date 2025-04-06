from config.Config import get_config
from decimal import Decimal
from typing import Optional, Dict, Any, List
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.BaseModels import BaseTokenData, BaseStrategyConfig, ExecutionState, TradeLog
from framework.analyticsframework.models.SourceModels import PortSummaryTokenData
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
import logging
from framework.analyticsframework.models.StrategyModels import (
     EntryType, DCARule, InvestmentInstructions
)
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from datetime import datetime, timedelta
from actions.DexscrennerAction import DexScreenerAction


logger = logging.getLogger(__name__)

class PortSummaryStrategy(BaseStrategy):
    """Strategy implementation for portfolio summary based tokens"""

    def __init__(self, analyticsHandler: AnalyticsHandler):
        self.analyticsHandler = analyticsHandler
        self.dexScreener = DexScreenerAction()
    
    def _checkRequiredTags(self, tokenData: PortSummaryTokenData, requiredTags: List[str]) -> bool:
        if not requiredTags:
            logger.warning("No required tags defined in strategy")
            return True

        # Convert required tags to set
        requiredTagsSet = set(requiredTags)
        
        # Convert token tags string to list and then to set
        tokenTags = set(tag.strip() for tag in tokenData.tags.split(',')) if tokenData.tags else set()

        # Check if all required tags are present
        if not requiredTagsSet.issubset(tokenTags):
            missingTags = requiredTagsSet - tokenTags
            logger.info(f"Token {tokenData.tokenname} missing required tags: {missingTags}")
            return False

        return True

    def _checkTokenAge(self, tokenData: PortSummaryTokenData, minAge: int, maxAge: int) -> bool:
        if minAge == -1 and maxAge == -1:
            return True

        try:
            tokenAge = int(tokenData.tokenage)
            
            if minAge != -1 and tokenAge < minAge:
                logger.info(f"Token {tokenData.tokenname} age ({tokenAge} days) is less than minimum required age ({minAge} days)")
                return False
            
            if maxAge != -1 and tokenAge > maxAge:
                logger.info(f"Token {tokenData.tokenname} age ({tokenAge} days) exceeds maximum allowed age ({maxAge} days)")
                return False
                
            return True
            
        except ValueError:
            logger.warning(f"Invalid token age format for {tokenData.tokenname}: {tokenData.tokenage}")
            return False

    def _checkSmartBalance(self, tokenData: PortSummaryTokenData, minSmartBalance: float) -> bool:
        if tokenData.smartbalance < minSmartBalance:
            logger.info(f"Token {tokenData.tokenname} smart balance ({tokenData.smartbalance}) is less than minimum required ({minSmartBalance})")
            return False
        return True
    
    def _checkAttentionStatus(self, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        if strategyConfig.strategyentryconditions.attentioninfo['isavailable'] == True:
            if tokenData.attentioninfo.isavailable == False:
                logger.info(f"Token {tokenData.tokenname} is not available in attention data")
                return False

        return True

    def checkEntryConditions(self, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """
        Validate entry conditions for PortSummary tokens
        Checks tags, age, and smart balance requirements
        """
        try:
            entryConditions = strategyConfig.strategyentryconditions
            
            # Check tags
            if not self._checkRequiredTags(tokenData, entryConditions.requiredtags):
                return False
                
            # Check age
            if not self._checkTokenAge(tokenData, entryConditions.minage, entryConditions.maxage):
                return False
                
            # Check smart balance
            if not self._checkSmartBalance(tokenData, entryConditions.minsmartbalance):
                return False
            
            # Check attention status
            if not self._checkAttentionStatus(tokenData, strategyConfig):
                return False

            logger.info(f"Token {tokenData.tokenname} matches all entry conditions")
            return True

        except Exception as e:
            logger.error(f"Error validating entry conditions: {str(e)}")
            return False
        
        
        #Implement chart conditions once we implement alchemy api
    def validateChartConditions(self, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        return True


    def executeInvestment(self, executionId: int, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """Execute investment based on investment rules"""
        try:
            investmentInstructions = strategyConfig.investmentinstructions
            
            # Get real-time price from DexScreener
            priceData = self.dexScreener.getTokenPrice(tokenData.tokenid)
            if not priceData:
                logger.error(f"Failed to get real-time price for token {tokenData.tokenid}")
                return False
                
            # Update token data with real-time price
            realTimePrice = Decimal(str(priceData.price))
            
            # Update token price for trade execution
            tokenData.price = realTimePrice
            
            if investmentInstructions.entrytype == EntryType.BULK.name:
                return self.executeBulkInvestment(executionId, tokenData, investmentInstructions)
            elif investmentInstructions.entrytype == EntryType.DCA.name:
                return self.executeDCAInvestement(executionId, tokenData, investmentInstructions)
            else:
                logger.error(f"Unknown entry type: {investmentInstructions.entrytype}")
                return False

        except Exception as e:
            logger.error(f"Error executing investment: {str(e)}")
            return False

    def executeBulkInvestment(self, executionId: int, tokenData: PortSummaryTokenData, investmentInstructions: InvestmentInstructions) -> bool:
        """Execute a bulk investment"""
        try:
            # Calculate position size
            # positionSize = min(investmentInstructions.allocated_amount, investmentInstructions.max_position_size)
            positionSize = Decimal(str(investmentInstructions.allocatedamount))
            tokenPrice = Decimal(str(tokenData.price))
            
            # Create trade record with real-time price
            tradeRecord = TradeLog(
                tradeid=None,
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=positionSize,
                tokenprice=tokenPrice,  # Using real-time price
                coins=positionSize / tokenPrice,
                description="Bulk entry position",
                createdat=datetime.now()
            )
            
            # Log trade
            return self.analyticsHandler.logTrade(tradeRecord)

        except Exception as e:
            logger.error(f"Error executing bulk investment: {str(e)}")
            return False

    def executeDCAInvestement(self, executionId: int, tokenData: PortSummaryTokenData, investmentInstructions: InvestmentInstructions) -> bool:
        """Setup DCA investment schedule with real-time price"""
        try:
            if not investmentInstructions.dcarules:
                logger.error("DCA rules not configured")
                return False

            dcaRules = investmentInstructions.dcarules
            currentTime = datetime.now()

            # Create first DCA entry with real-time price
            first_entry = TradeLog(
                trade_id=None,
                execution_id=executionId,
                token_id=tokenData.tokenid,
                token_name=tokenData.tokenname,
                trade_type=TradeType.BUY.value,
                amount=dcaRules.amountperinterval,
                token_price=tokenData.price,  # Using real-time price
                coins=dcaRules.amountperinterval / tokenData.price,
                fees=Decimal('0'),
                pnl=None,
                pnl_pct=None,
                description=f"DCA entry 1/{dcaRules.intervals}",
                created_time=currentTime
            )

            # Log first trade
            if not self.analyticsHandler.logTrade(first_entry):
                return False

            return True

        except Exception as e:
            logger.error(f"Error executing DCA investment: {str(e)}")
            return False