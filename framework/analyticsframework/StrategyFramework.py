from config.Config import get_config
from typing import Dict, List, Optional, Type, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.BaseModels import (
    BaseTokenData, BaseStrategyConfig, ExecutionState, TradeLog
)
from framework.analyticsframework.models.StrategyModels import (
    EntryType, DCARule, ProfitTarget, ProfitTakingInstructions, MoonBagInstructions,InvestmentInstructions,
    RiskManagementInstructions
)
from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from logs.logger import get_logger
from actions.DexscrennerAction import DexScreenerAction, TokenPrice
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
logger = get_logger(__name__)

class StrategyFramework:
    """Core framework for processing tokens through strategies"""
    
    def __init__(self):
        self.config = get_config()
        self.db = DatabaseConnectionManager()
        self.analyticsHandler = AnalyticsHandler(self.db)
        self.dexScreener = DexScreenerAction()
        

    def checkExistingExecution(self, tokenData: BaseTokenData, strategyConfig: BaseStrategyConfig) -> Optional[int]:
        """
        Check if token already has an active execution for this strategy
        """
        try:
            existingExecutions = self.analyticsHandler.getExecutionsForTokenAndStrategy(
                tokenId=tokenData.tokenid,
                strategyId=strategyConfig.strategyid
            )
             
            if existingExecutions:
                activeStatuses = [ExecutionStatus.ACTIVE.value, ExecutionStatus.INVESTED.value]
                activeExecutions = [e for e in existingExecutions if e['status'] in activeStatuses]
                
                if activeExecutions:
                    logger.info(
                        f"Token {tokenData.tokenid} ({tokenData.tokenname}) already has active execution "
                        f"for strategy {strategyConfig.strategyid} ({strategyConfig.strategyname}). "
                        f"Execution ID: {activeExecutions[0]['executionid']}"
                    )
                    return activeExecutions[0]['executionid']  # Return existing execution ID
             
            return None
        except Exception as e:
            logger.error(f"Error checking existing executions: {str(e)}")
            return None
                
    def handleStrategy(self, strategy: BaseStrategy, tokenData: BaseTokenData, strategyConfig: BaseStrategyConfig, description: Optional[str] = None) -> Optional[int]:
        """Process token through a single strategy"""
        try:
            # Check if this token is already being processed by this strategy
            existingExecutionId = self.checkExistingExecution(tokenData, strategyConfig)
            if existingExecutionId:
                return existingExecutionId
            
            # Validate entry conditions
            if not strategy.checkEntryConditions(tokenData, strategyConfig):
                return None

            # Create execution with ACTIVE status
            executionId = self.createExecution(strategy, tokenData, strategyConfig, description)
            if not executionId:
                return None

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
                
                else:
                    logger.error(f"No trade details found for execution {executionId}")
                    return None
            
            return executionId

        except Exception as e:
            logger.error(f"Error processing strategy {strategyConfig.strategyid}: {str(e)}")
            return None

    def createExecution(self, strategy: BaseStrategy, tokenData: BaseTokenData, 
                         strategyConfig: BaseStrategyConfig, description: Optional[str] = None) -> Optional[int]:
        """Create a new strategy execution"""
        try:
            # Create execution state with only required initial details
            executionState = ExecutionState(
                executionid=0,  # Set by database
                strategyid=strategyConfig.strategyid,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                allotedamount=strategyConfig.investmentinstructions.allocatedamount,
                status=ExecutionStatus.ACTIVE,
                description=description or strategyConfig.description,
                createdat=datetime.now(),
                updatedat=datetime.now()
            )

            executionId = self.analyticsHandler.recordExecution(executionState)
            if executionId:
                logger.info(f"Created execution {executionId} for token {tokenData.tokenid} - {tokenData.tokenname}")
            else:
                logger.error(f"Failed to create execution for token {tokenData.tokenid} - {tokenData.tokenname}")
                
            return executionId

        except Exception as e:
            logger.error(f"Error creating execution: {str(e)}")
            return None

    def getProfitTargets(self, executionState: ExecutionState, currentPrice: Decimal, profitTakingInstructions: ProfitTakingInstructions) -> Optional[ProfitTarget]:
        """
        Get the highest profit target that has been hit
        
        Args:
            executionState: Current execution state
            currentPrice: Current token price
            profitRules: Profit taking configuration
            
        Returns:
            Optional[ProfitTarget]: Matched profit target if any
        """
        try:
            # Calculate current profit percentage
            entryPrice = executionState.avgentryprice
            currentProfitPct = ((currentPrice - entryPrice) / entryPrice) * Decimal('100')

            # Check if minimum profit threshold is met
            if currentProfitPct < profitTakingInstructions.minprofitpct:
                return None

            # Sort targets by pricePct descending to check highest targets first
            sortedTargets = sorted(
                profitTakingInstructions.targets, 
                key=lambda x: x.pricepct, 
                reverse=True
            )

            # Find the highest target that has been hit
            for target in sortedTargets:
                if currentProfitPct >= target.pricepct:
                    return target

            return None

        except Exception as e:
            logger.error(f"Error checking profit targets: {str(e)}")
            return None

    def takeProfits(self, executionState: ExecutionState, tokenData: BaseTokenData, 
                    strategyConfig: BaseStrategyConfig, target: ProfitTarget, 
                    currentPrice: Decimal) -> bool:
        """
        Execute profit taking for a token based on the target
        
        Args:
            executionState: Current execution state
            tokenData: Token data with current price
            strategyConfig: Strategy configuration
            target: Profit target to execute
            currentPrice: Current token price
            
        Returns:
            bool: True if profit taking was successfully executed
        """
        try:
            # Step 1: Check moon bag eligibility
            moonBagInstructions, qualifiesForMoonbag = self._checkMoonBagEligibility(
                executionState, strategyConfig, currentPrice
            )
            
            # Step 2: Calculate sell amount and create trade record
            tradeRecord, sellAmount, sellCoins = self._createSellTradeRecord(
                executionState, tokenData, target, currentPrice, 
                moonBagInstructions, qualifiesForMoonbag
            )
            
            # Step 3: Log the trade
            if not self._logTrade(tradeRecord):
                return False
                
            # Step 4: Update execution state
            self.updateExecutionAfterSell(
                executionState, sellCoins, sellAmount, qualifiesForMoonbag
            )

            return True

        except Exception as e:
            logger.error(f"Error executing profit taking: {str(e)}")
            return False

    def _checkMoonBagEligibility(self, executionState: ExecutionState, 
                               strategyConfig: BaseStrategyConfig, 
                               currentPrice: Decimal) -> Tuple[Optional[MoonBagInstructions], bool]:
        """
        Check if the execution qualifies for a moon bag
        
        Args:
            executionState: Current execution state
            strategyConfig: Strategy configuration
            currentPrice: Current token price
            
        Returns:
            Tuple[Optional[MoonBagInstructions], bool]: Moon bag instructions and eligibility flag
        """
        moonBagInstructions = strategyConfig.profittakinginstructions.moonbaginstructions
        
        qualifiesForMoonbag = (
            moonBagInstructions and 
            moonBagInstructions.enabled and 
            self.shouldHaveMoonBag(executionState, currentPrice, moonBagInstructions)
        )
        
        return moonBagInstructions, qualifiesForMoonbag

    def _createSellTradeRecord(self, executionState: ExecutionState, 
                             tokenData: BaseTokenData, 
                             target: ProfitTarget,
                             currentPrice: Decimal,
                             moonBagInstructions: Optional[MoonBagInstructions],
                             qualifiesForMoonbag: bool) -> Tuple[TradeLog, Decimal, Decimal]:
        """
        Calculate sell amount and create trade record
        
        Args:
            executionState: Current execution state
            tokenData: Token data with current price
            target: Profit target to execute
            currentPrice: Current token price
            moonBagInstructions: Moon bag instructions if any
            qualifiesForMoonbag: Whether execution qualifies for moon bag
            
        Returns:
            Tuple[TradeLog, Decimal, Decimal]: Trade record, sell amount, and sell coins
        """
        # Calculate sell amount
        totalCoins = executionState.remainingcoins
        sellCoins = totalCoins * (target.sizepct / Decimal('100'))
        
        # Apply moon bag only if we qualify
        if qualifiesForMoonbag:
            moonBagCoins = totalCoins * (moonBagInstructions.sizepct / Decimal('100'))
            sellCoins = min(sellCoins, totalCoins - moonBagCoins)
            logger.info(f"Keeping {moonBagCoins} coins as moon bag for execution {executionState.executionid}")
        
        sellAmount = sellCoins * currentPrice
        
        # Create sell trade record
        tradeRecord = TradeLog(
            tradeid=None,
            executionid=executionState.executionid,
            tokenid=tokenData.tokenid,
            tokenname=tokenData.tokenname,
            tradetype=TradeType.SELL.value,
            amount=sellAmount,
            tokenprice=currentPrice,
            coins=sellCoins,
            description=self.generateTradeDescription(target, moonBagInstructions),
            createdat=datetime.now()
        )
        
        return tradeRecord, sellAmount, sellCoins

    def _logTrade(self, tradeRecord: TradeLog) -> bool:
        """
        Log a trade to the database
        
        Args:
            tradeRecord: Trade record to log
            
        Returns:
            bool: True if trade was successfully logged
        """
        tradeId = self.analyticsHandler.logTrade(tradeRecord)
        if not tradeId:
            logger.error(f"Failed to log trade for execution {tradeRecord.executionid}")
            return False
            
        logger.info(f"Logged trade {tradeId} for execution {tradeRecord.executionid}")
        return True

    def updateExecutionAfterSell(self, executionState: ExecutionState, 
                                sellCoins: Decimal, 
                                sellAmount: Decimal,
                                qualifiesForMoonbag: bool) -> None:
        """
        Update execution state after a sell operation
        
        Args:
            executionState: Current execution state
            sellCoins: Number of coins sold
            sellAmount: Amount received from sell
            qualifiesForMoonbag: Whether execution qualifies for moon bag
        """
        # Calculate remaining coins
        totalCoins = executionState.remainingcoins
        remainingCoins = totalCoins - sellCoins
        
        # Update amount taken out
        currentAmountTakenOut = executionState.amounttakenout or Decimal('0')
        updatedAmountTakenOut = currentAmountTakenOut + sellAmount
        
        # Calculate new average entry price
        totalInvested = executionState.investedamount or Decimal('0')
        newAvgEntryPrice = None
        
        if remainingCoins > 0:
            # Calculate new average entry price using the formula:
            # (total invested - total taken out) / remaining coins
            newAvgEntryPrice = (totalInvested - updatedAmountTakenOut) / remainingCoins
        
        # Determine the new status
        newStatus = self._determineNewStatus(remainingCoins, qualifiesForMoonbag)
        
        logger.info(
            f"Execution {executionState.executionid} update: "
            f"Remaining coins: {remainingCoins}, "
            f"Amount taken out: {updatedAmountTakenOut}, "
            f"New avg price: {newAvgEntryPrice}, "
            f"New status: {newStatus.name}"
        )
        
        # Update execution in database
        self.analyticsHandler.updateExecution(
            executionId=executionState.executionid,
            investedAmount=totalInvested,
            remainingCoins=remainingCoins,
            avgEntryPrice=newAvgEntryPrice,
            status=newStatus,
            amountTakenOut=updatedAmountTakenOut
        )

    def _determineNewStatus(self, remainingCoins: Decimal, qualifiesForMoonbag: bool) -> ExecutionStatus:
        """
        Determine the new execution status based on remaining coins and moon bag qualification
        
        Args:
            remainingCoins: Number of coins remaining
            qualifiesForMoonbag: Whether execution qualifies for moon bag
            
        Returns:
            ExecutionStatus: New execution status
        """
        if remainingCoins <= 0:
            # No coins left, execution is completed
            return ExecutionStatus.COMPLETED
        elif qualifiesForMoonbag:
            # Has remaining coins and qualifies for moon bag
            return ExecutionStatus.COMPLETED_WITH_MOONBAG
        else:
            # Has remaining coins but doesn't qualify for moon bag, stay as INVESTED
            return ExecutionStatus.INVESTED

    def shouldHaveMoonBag(self, executionState: ExecutionState,
                         currentPrice: Decimal,
                         moonBagInstructions: MoonBagInstructions) -> bool:
        """Check if moon bag conditions are met"""
        try:
            # Get all trades for this execution
            trades = self.analyticsHandler.getExecutionTrades(executionState.executionid)
            
            # Calculate total investment and returns
            totalInvested = Decimal('0')
            totalReturned = Decimal('0')
            
            for trade in trades:
                if trade['tradetype'] == TradeType.BUY.value:
                    totalInvested += trade['amount']
                elif trade['tradetype'] == TradeType.SELL.value:
                    totalReturned += trade['amount']
            
            # Calculate remaining position value
            remainingValue = executionState.remainingcoins * currentPrice
            
            # Calculate total profit percentage
            totalValue = totalReturned + remainingValue
            profitPct = ((totalValue - totalInvested) / totalInvested) * Decimal('100')
            
            logger.info(f"Moon bag check - Invested: {totalInvested}, "
                       f"Returned: {totalReturned}, Remaining: {remainingValue}, "
                       f"Profit%: {profitPct}%")

            # Check minimum profit requirement
            if profitPct < moonBagInstructions.minprofitpct:
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking moon bag conditions: {str(e)}")
            return False

    def generateTradeDescription(self, target: ProfitTarget,
                              moonBagInstructions: Optional[MoonBagInstructions]) -> str:
        """Generate descriptive message for trade"""
        baseDesc = f"Take profit at {target.pricepct}% target"
        
        if moonBagInstructions and moonBagInstructions.enabled:
            return f"{baseDesc} (Keeping {moonBagInstructions.sizepct}% as moon bag)"
        
        return baseDesc

    def getActiveExecutions(self) -> List[Tuple[ExecutionState, BaseStrategyConfig]]:
        """Get all active executions with their strategy configs"""
        return self.analyticsHandler.getActiveExecutionsWithConfig()
    
    def isStopLossHit(self, executionState: ExecutionState, currentPrice: Decimal, riskManagementInstructions: RiskManagementInstructions) -> bool:
        try:
            if not executionState.investedamount or executionState.investedamount <= 0 or not executionState.avgentryprice or not riskManagementInstructions.stoplossenabled:
                logger.debug(f"Skipping stop loss check for execution {executionState.executionid} - no investment yet or stop loss not enabled")
                return False

            entryPrice = executionState.avgentryprice
            currentLossPct = ((currentPrice - entryPrice) / entryPrice) * Decimal('100')
            
            # Check if loss exceeds stop loss percentage
            if currentLossPct <= -riskManagementInstructions.stoplosspct:
                logger.warning(
                    f"Stop loss triggered - Entry: {entryPrice}, Current: {currentPrice}, "
                    f"Loss: {currentLossPct}%, Stop: {riskManagementInstructions.stoplosspct}%"
                )
                return True
                
            return False

        except Exception as e:
            logger.error(f"Error checking stop loss: {str(e)}")
            return False
        
    def handleStrategyForTokenWithoutValidation(self, strategy: BaseStrategy, tokenData: BaseTokenData, strategyConfig: BaseStrategyConfig, description: Optional[str] = None) -> Optional[int]:
        """Process token through a single strategy"""
        try:

            # Create execution with ACTIVE status
            executionId = self.createExecution(strategy, tokenData, strategyConfig, description)
            if not executionId:
                return None

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
                
                else:
                    logger.error(f"No trade details found for execution {executionId}")
                    return None
            
            return executionId

        except Exception as e:
            logger.error(f"Error processing strategy {strategyConfig.strategyid}: {str(e)}")
            return None

  

    