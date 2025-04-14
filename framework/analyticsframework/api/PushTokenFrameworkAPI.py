from config.Config import get_config
from typing import Optional, Dict, Any, List, Tuple
from database.portsummary.PortfolioHandler import PortfolioHandler
from framework.analyticsframework.models.BaseModels import (
    BaseTokenData,
    BaseStrategyConfig,
)
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.SourceModels import (
    PortSummaryTokenData,
    AttentionTokenData,
    SmartMoneyTokenData,
    VolumeTokenData,
    PumpFunTokenData,
)
from framework.analyticsframework.StrategyFramework import StrategyFramework
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticsframework.enums.PushSourceEnum import PushSource
from framework.analyticsframework.enums.SourceHandlerEnum import SourceHandler
from framework.analyticsframework.models.StrategyModels import StrategyConfig
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from logs.logger import get_logger
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from datetime import datetime, timedelta
from decimal import Decimal
import pytz
from framework.analyticsframework.models.StrategyModels import AttentionInfo

logger = get_logger(__name__)


class PushTokenAPI:
    """API for analyzing tokens through the analytics framework"""

    def __init__(self):
        self.config = get_config()
        self.db = DatabaseConnectionManager()
        self.analyticsHandler = AnalyticsHandler(self.db)
        self.strategyFramework = StrategyFramework()
        self.strategyHandlers = SourceHandler.getAllHandlers(self.analyticsHandler)

    @staticmethod
    def getSourceTokenDataHandler(
        sourceType: str, tokenId: str
    ) -> Optional[BaseTokenData]:
        try:
            db = DatabaseConnectionManager()

            if sourceType == SourceType.PORTSUMMARY.value:
                portfolioHandler = db.portfolio
                tokenData = portfolioHandler.getTokenDataForAnalysis(tokenId)
                if tokenData:
                    return PushTokenAPI.mapPortfolioTokenData(tokenData)

            elif sourceType == SourceType.ATTENTION.value:
                attentionHandler = db.attention
                tokenData = attentionHandler.getTokenDataForAnalysis(tokenId)
                if tokenData:
                    return PushTokenAPI.mapAttentionTokenData(tokenData)

            elif sourceType == SourceType.VOLUME.value:
                volumeHandler = db.volume
                # Get both state and info
                tokenState = volumeHandler.getTokenState(tokenId)
                tokenInfo = volumeHandler.getTokenInfo(tokenId)
                if tokenState and tokenInfo:
                    # Combine state and info
                    combinedTokenData = {**tokenState, **tokenInfo}
                    return PushTokenAPI.mapVolumeTokenData(combinedTokenData)

            elif sourceType == SourceType.PUMPFUN.value:
                pumpfunHandler = db.pumpfun
                # Get both state and info
                tokenState = pumpfunHandler.getTokenState(tokenId)
                tokenInfo = pumpfunHandler.getTokenInfo(tokenId)
                if tokenState and tokenInfo:
                    # Combine state and info
                    combinedTokenData = {**tokenState, **tokenInfo}
                return PushTokenAPI.mapPumpFunTokenData(combinedTokenData)

            elif sourceType == SourceType.SMARTMONEY.value:
                # For smart money, we need to handle it differently as it's wallet-based
                # We'll get the top tokens for high PNL wallets
                smWalletHandler = db.smWalletTopPNLToken
                tokenData = smWalletHandler.getSMWalletTopPNLToken(None, tokenId)
                if tokenData:
                    return PushTokenAPI.mapSmartMoneyTokenData(tokenData)

            return None

        except Exception as e:
            logger.error(f"Error getting token data: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def mapPortfolioTokenData(tokenData: Dict) -> PortSummaryTokenData:
        """
        Map raw portfolio token data to PortSummaryTokenData model

        Args:
            tokenData: Raw token data from database

        Returns:
            PortSummaryTokenData: Mapped token data
        """
        # Get attention info from the attention handler
        db = DatabaseConnectionManager()
        attentionInfo = None
        try:
            attentionData = db.attention.getAttentionInfo(tokenData["tokenid"])
            if attentionData:
                attentionInfo = AttentionInfo(
                    isavailable=True,
                    attentionscore=attentionData["attentionscore"],
                    repeats=attentionData["consecutiverecords"],
                    attentionstatus=attentionData["currentstatus"],
                )
        except Exception as e:
            logger.error(
                f"Failed to get attention info for token {tokenData['tokenid']}: {str(e)}"
            )
            attentionInfo = None

        mappedData = {
            # BaseTokenData fields
            "tokenid": tokenData["tokenid"],
            "tokenname": tokenData["name"],
            "chainname": tokenData["chainname"],
            "price": tokenData["currentprice"],
            "marketcap": tokenData["mcap"],
            "holders": tokenData.get(
                "walletsinvesting1000", 0
            ),  # Using this as holders count
            # PortSummaryTokenData specific fields
            "tokenage": tokenData["tokenage"],
            "avgprice": tokenData["avgprice"],
            "smartbalance": tokenData["smartbalance"],
            "walletsinvesting1000": tokenData["walletsinvesting1000"],
            "walletsinvesting5000": tokenData["walletsinvesting5000"],
            "walletsinvesting10000": tokenData["walletsinvesting10000"],
            "qtychange1d": tokenData["qtychange1d"],
            "qtychange7d": tokenData["qtychange7d"],
            "qtychange30d": tokenData["qtychange30d"],
            "status": tokenData["status"],
            "portsummaryid": tokenData.get("portsummaryid"),
            "tags": tokenData.get("tags"),
            "markedinactive": tokenData.get("markedinactive"),
            "attentioninfo": attentionInfo,
        }
        return PortSummaryTokenData(**mappedData)

    def pushToken(self,tokenData: BaseTokenData,sourceType: str,pushSource: PushSource = PushSource.SCHEDULER,description: Optional[str] = None,) -> bool:
        try:
            # Get active strategies for token's source type
            allActiveStrategies: List[Dict] = (
                self.analyticsHandler.getAllActiveStrategies(sourceType, pushSource)
            )

            if not allActiveStrategies:
                logger.info(f"No active strategies found for source {sourceType}")
                return False

            # Get the appropriate strategy handler
            strategyHandler = self.strategyHandlers.get(sourceType)
            if not strategyHandler:
                logger.error(f"No strategy handler found for source type: {sourceType}")
                return False

            success = False
            for strategy in allActiveStrategies:
                # Convert dictionary to StrategyConfig
                strategyConfig = StrategyConfig(**strategy)

                # Process token through strategy
                executionId = self.strategyFramework.handleStrategy(
                    strategy=strategyHandler,
                    tokenData=tokenData,
                    strategyConfig=strategyConfig,
                    description=description,
                )

                if executionId:
                    success = True
                    logger.info(
                        f"Successfully processed token {tokenData.tokenid} "
                        f"with strategy {strategyConfig.strategyid} "
                        f"(execution_id: {executionId})"
                    )

            return success

        except Exception as e:
            logger.error(f"Error analyzing token: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def mapAttentionTokenData(tokenData: Dict) -> AttentionTokenData:
        """
        Map raw attention token data to AttentionTokenData model

        Args:
            tokenData: Raw token data from database

        Returns:
            AttentionTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            "tokenid": tokenData["tokenid"],
            "tokenname": tokenData.get("name", ""),
            "chainname": tokenData.get("chain", ""),
            "price": 0,  # Attention data doesn't have price
            "marketcap": 0,  # Attention data doesn't have marketcap
            "holders": 0,  # Attention data doesn't have holders
            # AttentionTokenData specific fields
            "attentionscore": tokenData["attentionscore"],
            "change1hbps": tokenData.get("change1hbps"),
            "change1dbps": tokenData.get("change1dbps"),
            "change7dbps": tokenData.get("change7dbps"),
            "change30dbps": tokenData.get("change30dbps"),
            "attentioncount": tokenData.get("attentioncount"),
            "createdat": tokenData.get("createdat"),
            "updatedat": tokenData.get("updatedat"),
        }
        return AttentionTokenData(**mappedData)

    @staticmethod
    def mapVolumeTokenData(tokenData: Dict) -> VolumeTokenData:
        """
        Map raw volume token data to VolumeTokenData model

        Args:
            tokenData: Raw token data from database

        Returns:
            VolumeTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            "tokenid": tokenData["tokenid"],
            "tokenname": tokenData.get("tokenname", tokenData.get("name", "")),
            "chainname": tokenData.get("chain", ""),
            "price": tokenData.get("price", 0),
            "marketcap": tokenData.get("marketcap", 0),
            "holders": 0,  # Volume data doesn't typically have holders
            # VolumeTokenData specific fields
            "buysolqty": tokenData.get("buysolqty", 0),
            "occurrencecount": tokenData.get("occurrencecount", 0),
            "percentilerankpepeats": tokenData.get("percentilerankpeats", 0),
            "percentileranksol": tokenData.get("percentileranksol", 0),
            "dexstatus": tokenData.get("dexstatus", 0),  # 0 -> false
            "change1hpct": tokenData.get("change1hpct", 0),
            "avgvolume24h": tokenData.get(
                "volume24h", 0
            ),  # Using volume24h from DB as avgvolume24h
            "volumespikepct": tokenData.get(
                "change1hpct", 0
            ),  # Using change1hpct as volumespikepct
        }
        return VolumeTokenData(**mappedData)

    @staticmethod
    def mapPumpFunTokenData(tokenData: Dict) -> PumpFunTokenData:
        """
        Map raw pump fun token data to PumpFunTokenData model

        Args:
            tokenData: Raw token data from database

        Returns:
            PumpFunTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            "tokenid": tokenData["tokenid"],
            "tokenname": tokenData.get("tokenname", tokenData.get("name", "")),
            "chainname": tokenData.get("chain", ""),
            "price": tokenData.get("price", 0),
            "marketcap": tokenData.get("marketcap", 0),
            "holders": 0,  # Pump fun data doesn't typically have holders
            # PumpFunTokenData specific fields
            "buysolqty": tokenData.get("buysolqty", 0),
            "occurrencecount": tokenData.get("occurrencecount", 0),
            "percentilerankpepeats": tokenData.get("percentilerankpeats", 0),
            "percentileranksol": tokenData.get("percentileranksol", 0),
            "dexstatus": tokenData.get("dexstatus", 0),  # 0 -> false
            "change1hpct": tokenData.get("change1hpct", 0),
            "avgvolume24h": tokenData.get(
                "volume24h", 0
            ),  # Using volume24h from DB as avgvolume24h
            "volumespikepct": tokenData.get(
                "change1hpct", 0
            ),  # Using change1hpct as volumespikepct
        }
        return PumpFunTokenData(**mappedData)

    @staticmethod
    def mapSmartMoneyTokenData(tokenData: Dict) -> SmartMoneyTokenData:
        """
        Map raw smart money token data to SmartMoneyTokenData model

        Args:
            tokenData: Raw token data from database

        Returns:
            SmartMoneyTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            "tokenid": tokenData["tokenid"],
            "tokenname": tokenData.get("name", ""),
            "chainname": "",  # Smart money data doesn't typically have chain info
            "price": 0,  # Smart money data doesn't have price
            "marketcap": 0,  # Smart money data doesn't have marketcap
            "holders": 0,  # Smart money data doesn't have holders
            # SmartMoneyTokenData specific fields
            "walletaddress": tokenData["walletaddress"],
            "unprocessedpnl": tokenData.get("unprocessedpnl", 0),
            "unprocessedroi": tokenData.get("unprocessedroi", 0),
            "transactionscount": tokenData.get("transactionscount", 0),
            "amountinvested": tokenData.get("amountinvested"),
            "amounttakenout": tokenData.get("amounttakenout"),
            "remainingcoins": tokenData.get("remainingcoins"),
            "status": tokenData.get("status", 0),
        }
        return SmartMoneyTokenData(**mappedData)

    def pushAllTokens(
        self, sourceType: str, pushSource: PushSource = PushSource.SCHEDULER
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Push all tokens from a specific source type to the analytics framework

        Args:
            sourceType: Source type (e.g., PORTSUMMARY, ATTENTION, etc.)
            pushSource: Source that pushed the token (API or SCHEDULER)

        Returns:
            Tuple containing success status and statistics
        """
        try:
            if sourceType == SourceType.PORTSUMMARY.value:
                return self.pushAllPortSummaryTokens(pushSource)
            else:
                logger.warning(
                    f"Source type {sourceType} is not yet supported for bulk token pushing"
                )
                return False, {
                    "error": f"Source type {sourceType} is not yet supported for bulk token pushing"
                }
        except Exception as e:
            logger.error(
                f"Failed to push all tokens for source {sourceType}: {str(e)}",
                exc_info=True,
            )
            return False, {"error": str(e)}

    def pushAllPortSummaryTokens(
        self, pushSource: PushSource = PushSource.SCHEDULER
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Push all portfolio summary tokens to the analytics framework

        Args:
            pushSource: Source that pushed the token (API or SCHEDULER)

        Returns:
            Tuple containing success status and statistics
        """
        try:
            # Get all tokens from portfolio summary
            tokens = self.db.portfolio.getActivePortfolioTokens()

            if not tokens:
                logger.info("No active tokens found in portfolio summary")
                return False, {"total": 0, "processed": 0, "success": 0, "failed": 0}

            logger.info(f"Found {len(tokens)} active tokens in portfolio summary")

            # Process each token
            successCount = 0
            failedCount = 0
            processedTokens = []
            failedTokens = []

            for token in tokens:
                try:
                    # Convert to PortSummaryTokenData
                    tokenData = self.mapPortfolioTokenData(token)

                    # Push to strategy framework
                    success = self.pushToken(
                        tokenData=tokenData,
                        sourceType=SourceType.PORTSUMMARY.value,
                        pushSource=pushSource,
                    )

                    if success:
                        successCount += 1
                        processedTokens.append(
                            {
                                "tokenId": tokenData.tokenid,
                                "tokenName": tokenData.tokenname,
                            }
                        )
                        logger.info(
                            f"Successfully pushed token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework"
                        )
                    else:
                        failedCount += 1
                        failedTokens.append(
                            {
                                "tokenId": tokenData.tokenid,
                                "tokenName": tokenData.tokenname,
                            }
                        )
                        logger.warning(
                            f"Failed to push token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework"
                        )

                except Exception as tokenError:
                    failedCount += 1
                    failedTokens.append(
                        {
                            "tokenId": token.get("tokenid", "unknown"),
                            "error": str(tokenError),
                        }
                    )
                    logger.error(
                        f"Error processing token {token.get('tokenid', 'unknown')}: {str(tokenError)}"
                    )
                    continue

            stats = {
                "total": len(tokens),
                "processed": successCount + failedCount,
                "success": successCount,
                "failed": failedCount,
                "successTokens": processedTokens[
                    :10
                ],  # Limit the number of tokens in the response
                "failedTokens": failedTokens[:10],
            }

            logger.info(
                f"Successfully pushed {successCount}/{len(tokens)} tokens to strategy framework"
            )
            return successCount > 0, stats

        except Exception as e:
            logger.error(
                f"Failed to push portfolio summary tokens to strategy framework: {str(e)}",
                exc_info=True,
            )
            return False, {"error": str(e)}

    def pushTokenToStrategy(
        self,
        tokenId: str,
        sourceType: str,
        strategyId: int,
        description: Optional[str] = None,
    ) -> Optional[int]:
        """
        Push a token to a specific strategy

        Args:
            tokenId: ID of the token to push
            sourceType: Type of data source
            strategyId: ID of the strategy to push to
            description: Optional description for the execution

        Returns:
            Optional[int]: Execution ID if successful, None otherwise
        """
        try:
            # Get token data from source
            tokenData = self.getSourceTokenDataHandler(sourceType, tokenId)
            if not tokenData:
                logger.error(f"Token {tokenId} not found in {sourceType} source")
                return None

            # Get strategy configuration
            strategyConfig = self.analyticsHandler.getStrategyById(strategyId)
            if not strategyConfig:
                logger.error(f"Strategy with ID {strategyId} not found")
                return None

            # Verify strategy is for the correct source type
            if strategyConfig["source"] != sourceType:
                logger.error(
                    f"Strategy {strategyId} is not configured for source type {sourceType}"
                )
                return None

            # Get the appropriate strategy handler
            strategyHandler = self.strategyHandlers.get(sourceType)
            if not strategyHandler:
                logger.error(f"No strategy handler found for source type: {sourceType}")
                return None

            # Convert dictionary to StrategyConfig model
            strategyConfigModel = StrategyConfig(**strategyConfig)

            # Process token through specific strategy
            executionId = (
                self.strategyFramework.handleStrategyForTokenWithoutValidation(
                    strategy=strategyHandler,
                    tokenData=tokenData,
                    strategyConfig=strategyConfigModel,
                    description=description,
                )
            )

            if executionId:
                logger.info(
                    f"Successfully pushed token {tokenId} to strategy {strategyId}"
                )
                return executionId
            else:
                logger.error(f"Failed to push token {tokenId} to strategy {strategyId}")
                return None

        except Exception as e:
            logger.error(f"Error pushing token to strategy: {str(e)}", exc_info=True)
            return None
