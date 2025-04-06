from config.Config import get_config
from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import time
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus
from framework.analyticsframework.enums.SourceHandlerEnum import SourceHandler
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.BaseModels import ExecutionState, BaseStrategyConfig, BaseTokenData
from framework.analyticsframework.StrategyFramework import StrategyFramework
from framework.analyticsframework.models.StrategyModels import (
    ProfitTarget,RiskManagementInstructions
)
from logs.logger import get_logger
from framework.analyticsframework.models.StrategyModels import ProfitTakingInstructions
from actions.DexscrennerAction import DexScreenerAction
from framework.analyticsframework.models.StrategyModels import TokenConvictionEnum
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
from framework.analyticsframework.enums.SourceTypeEnum import SourceType


logger = get_logger(__name__)

class ExecutionMonitor:
    def __init__(self):
        self.config = get_config()
        self.strategyFramework = StrategyFramework()
        self.dexScreener = DexScreenerAction()
        self.analyticsHandler = self.strategyFramework.analyticsHandler

    def monitorActiveExecutions(self):
        """Monitor and update active executions"""
        # Initialize stats
        stats = {
            "executionsProcessed": 0,
            "stopLossesTriggered": 0,
            "profitTargetsHit": 0,
            "investmentsMade": 0,
            "errors": 0
        }
         
        try:
            # Get all active executions with their configs
            activeExecutions = self.strategyFramework.getActiveExecutions()
            
            if not activeExecutions:
                logger.info("No active executions found to monitor")
                return stats
            
            logger.info(f"Found {len(activeExecutions)} active executions to process")
            
            for executionState, strategyConfig in activeExecutions:
                try:
                    logger.info(f"Processing execution for token ID: {executionState.tokenid}, Name: {executionState.tokenname}")
                    stats["executionsProcessed"] += 1

                    if executionState.status == ExecutionStatus.INVESTED:
                        self.processProfitTaking(executionState, strategyConfig,stats)
                    
                    if (executionState.status == ExecutionStatus.ACTIVE) and (strategyConfig.status == TokenConvictionEnum.HIGH.value):
                        self.processInvestment(executionState, strategyConfig, stats)          

                except Exception as e:
                    logger.error(f"Error processing execution {executionState.executionid}: {str(e)}")
                    stats["errors"] += 1

            logger.info(f"Monitoring cycle completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error monitoring executions: {str(e)}")
            return stats

    def handleStopLoss(self, executionState: ExecutionState, tokenData: BaseTokenData, 
                       strategyConfig: BaseStrategyConfig, currentPrice: Decimal) -> bool:
        """
        Handle stop loss execution for a token
        
        Args:
            executionState: Current execution state
            tokenData: Token data with current price
            strategyConfig: Strategy configuration
            currentPrice: Current token price
            
        Returns:
            bool: True if stop loss was successfully executed
        """
        logger.warning(f"Stop loss triggered for execution {executionState.executionid}")
        
        # Create a full exit target
        stopLossTarget = ProfitTarget(
            pricepct=Decimal('0'),  # Not relevant for stop loss
            sizepct=Decimal('100')  # Full position exit
        )
        
        # Execute stop loss
        success = self.strategyFramework.takeProfits(
            executionState=executionState,
            tokenData=tokenData,
            strategyConfig=strategyConfig,
            target=stopLossTarget,
            currentPrice=currentPrice
        )
        
        if success:
            logger.info(f"Successfully executed stop loss for execution {executionState.executionid}")
        else:
            logger.error(f"Failed to execute stop loss for execution {executionState.executionid}")
            
        return success

    def processProfitTaking(self, executionState: ExecutionState, strategyConfig: BaseStrategyConfig,stats: Dict[str, Any]):
        """Process a single execution"""
        try:
            # Get current price
            priceData = self.dexScreener.getTokenPrice(executionState.tokenid)
            if not priceData:
                logger.warning(f"Could not get price for token {executionState.tokenid}")
                return

            currentPrice = Decimal(str(priceData.price))

            # Create minimal token data object for profit taking
            tokenData = BaseTokenData(
                tokenid=executionState.tokenid,
                tokenname=executionState.tokenname,
                price=currentPrice,
                marketcap=Decimal(str(getattr(priceData, 'marketcap', '0'))),
                holders=getattr(priceData, 'holders', 0),
                chainname=getattr(priceData, 'chainname', 'solana')
            )

            # Check stop loss first
            if self.strategyFramework.isStopLossHit(executionState, currentPrice, strategyConfig.riskmanagementinstructions):
                self.handleStopLoss(executionState, tokenData, strategyConfig, currentPrice)
                return  # Exit early after stop loss

            # Continue with profit target checks if stop loss not triggered
            profitTarget = self.strategyFramework.getProfitTargets(
                executionState=executionState,
                currentPrice=currentPrice,
                profitTakingInstructions=strategyConfig.profittakinginstructions
            )

            if profitTarget:
                logger.info(
                    f"Profit target hit for execution {executionState.executionid}: "
                    f"{profitTarget.pricepct}%"
                )
                
                # Execute profit taking with objects we already have
                success = self.strategyFramework.takeProfits(
                    executionState=executionState,
                    tokenData=tokenData,
                    strategyConfig=strategyConfig,
                    target=profitTarget,
                    currentPrice=currentPrice
                )
                
                if success:
                    logger.info(
                        f"Successfully executed profit taking for execution "
                        f"{executionState.executionid}"
                    )
                else:
                    logger.error(
                        f"Failed to execute profit taking for execution "
                        f"{executionState.executionid}"
                    )

                if success.get("stopLossTriggered", False):
                    stats["stopLossesTriggered"] += 1
                if success.get("profitTargetHit", False):
                    stats["profitTargetsHit"] += 1

        except Exception as e:
            logger.error(f"Error processing execution {executionState.executionid}: {str(e)}")

    def processInvestment(self, executionState: ExecutionState, strategyConfig: BaseStrategyConfig, stats: Dict[str, Any]):
        """process the execution for investing if its a high conviction token"""
        try:
            # Convert source string to SourceType enum
            sourceType = SourceType(strategyConfig.source)
            # Create a proper instance of the strategy handler
            strategy = SourceHandler.createHandler(sourceType, self.analyticsHandler)
            
            # Get token data from source
            tokenData = PushTokenAPI.getSourceTokenDataHandler(strategyConfig.source, executionState.tokenid)
            if not tokenData:
                logger.error(f"Failed to get token data for token {executionState.tokenid}")
                return None
                
            # Validate entry conditions
            if not strategy.checkEntryConditions(tokenData, strategyConfig):
                logger.info(f"Entry conditions not met for token {executionState.tokenid}")
                return None
   
            executionId = executionState.executionid

            # Validate chart conditions
            if not strategy.validateChartConditions(tokenData, strategyConfig.chartconditions):
                logger.info(f"Chart conditions not met for token {tokenData.tokenid} ({tokenData.tokenname})")
                return executionId

            # Execute investment based on type
            success = strategy.executeInvestment(executionId, tokenData, strategyConfig)
            if success:
                # Get trade details to update execution
                tradeDetails = self.analyticsHandler.getExecutionTrades(executionId)
                if tradeDetails:
                    # Calculate execution metrics
                    totalAmount = sum(t['amount'] for t in tradeDetails)
                    totalCoins = sum(t['coins'] for t in tradeDetails)
                    avgEntryPrice = totalAmount / totalCoins if totalCoins > 0 else Decimal('0')
                    
                    self.analyticsHandler.updateExecution(
                        executionId=executionId,
                        investedAmount=totalAmount,
                        remainingCoins=totalCoins,
                        avgEntryPrice=avgEntryPrice,
                        status=ExecutionStatus.INVESTED
                    )
                    stats["investmentsMade"] += 1
                else:
                    logger.error(f"No trade details found for execution {executionId}")
                    return None
            else:
                logger.error(f"Failed to execute investment for execution {executionId}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing execution {executionState.executionid}: {str(e)}")
            return None

