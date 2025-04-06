from config.Config import get_config
from typing import Dict, List, Optional, Any
from datetime import datetime
from logs.logger import get_logger
from decimal import Decimal
from actions.DexscrennerAction import DexScreenerAction, TokenPrice

logger = get_logger(__name__)

class SMWalletInvestmentRangeReportAction:
    """
    Action class for computing investment range report metrics.
    Contains business logic for analyzing wallet token investments by amount ranges.
    """
    
    def __init__(self):
        self.config = get_config()
        """Initialize the action class"""
        self.dexScreener = DexScreenerAction()
    
    def getInvestmentRanges(self) -> List[Dict[str, Any]]:
        """
        Get predefined investment ranges for categorization
        
        Returns:
            List of ranges with min, max and label
        """
        return [
            {"min": 0, "max": 1000, "label": "0-1K", "id": "0-1k"},
            {"min": 1001, "max": 10000, "label": "1K-10K", "id": "1k-10k"},
            {"min": 10001, "max": 50000, "label": "10K-50K", "id": "10k-50k"},
            {"min": 50001, "max": 100000, "label": "50K-100K", "id": "50k-100k"},
            {"min": 100001, "max": 500000, "label": "100K-500K", "id": "100k-500k"},
            {"min": 500001, "max": 1000000, "label": "500K-1M", "id": "500k-1m"},
            {"min": 1000001, "max": None, "label": "1M+", "id": "1m+"} # No upper limit for this range
        ]
        
    def buildReportStructure(self, walletAddress: str, tokenCount: int) -> Dict[str, Any]:
        """
        Create the base report structure with initialized metrics
        
        Args:
            walletAddress: The wallet address being analyzed
            tokenCount: Total number of tokens for the wallet
            
        Returns:
            Dictionary with initialized report structure
        """
        return {
            "walletAddress": walletAddress,
            "ranges": [],
            "totalTokens": tokenCount,
            "totalInvested": 0,
            "totalTakenOut": 0,
            "totalRealizedPnl": 0,
            "totalRealizedReturnPercentage": 0,
            "totalRealizedWinRate": 0,
            "totalRemainingValue": 0,
            "totalPnl": 0,
            "totalReturnPercentage": 0,
            "totalWinRate": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    def processReportData(self, tokens: List[Any], walletAddress: str) -> Dict[str, Any]:
        """
        Process token data into a comprehensive investment range report
        
        Args:
            tokens: List of token data from database
            walletAddress: Address of the wallet being analyzed
            
        Returns:
            Complete investment range report
        """
        # Initialize report structure
        result = self.buildReportStructure(walletAddress, len(tokens))
        
        # Get investment ranges
        ranges = self.getInvestmentRanges()
        
        # Process each range
        for rangeInfo in ranges:
            rangeData = self.calculateRangeMetrics(tokens, rangeInfo["min"], rangeInfo["max"])
            
            if rangeData["numTokens"] > 0:
                result["ranges"].append({
                    "id": rangeInfo["id"],
                    "label": rangeInfo["label"],
                    "minAmount": rangeInfo["min"],
                    "maxAmount": rangeInfo["max"],
                    "numTokens": rangeData["numTokens"],
                    "totalInvested": round(rangeData["totalInvested"], 2),
                    "totalTakenOut": round(rangeData["totalTakenOut"], 2),
                    "realizedPnl": round(rangeData["realizedPnl"], 2),
                    "realizedReturnPercentage": round(rangeData["realizedReturnPercentage"], 2),
                    "realizedWinCount": rangeData["realizedWinCount"],
                    "realizedLossCount": rangeData["realizedLossCount"],
                    "realizedWinRate": round(rangeData["realizedWinRate"], 2),
                    "remainingValue": round(rangeData["remainingValue"], 2),
                    "totalPnl": round(rangeData["totalPnl"], 2),
                    "totalReturnPercentage": round(rangeData["totalReturnPercentage"], 2),
                    "totalWinCount": rangeData["totalWinCount"],
                    "totalLossCount": rangeData["totalLossCount"],
                    "totalWinRate": round(rangeData["totalWinRate"], 2)
                })
                
                # Accumulate totals
                result["totalInvested"] += rangeData["totalInvested"]
                result["totalTakenOut"] += rangeData["totalTakenOut"]
                result["totalRealizedPnl"] += rangeData["realizedPnl"]
                result["totalRemainingValue"] += rangeData["remainingValue"]
                result["totalPnl"] += rangeData["totalPnl"]
                
        # Calculate overall metrics
        if result["totalInvested"] > 0:
            result["totalRealizedReturnPercentage"] = round((result["totalRealizedPnl"] / result["totalInvested"]) * 100, 2)
            result["totalReturnPercentage"] = round((result["totalPnl"] / result["totalInvested"]) * 100, 2)
        
        # Calculate overall win rates
        realizedWins = sum(r["realizedWinCount"] for r in result["ranges"])
        totalWins = sum(r["totalWinCount"] for r in result["ranges"])
        totalTrades = sum(r["numTokens"] for r in result["ranges"])
        
        if totalTrades > 0:
            result["totalRealizedWinRate"] = round((realizedWins / totalTrades) * 100, 2)
            result["totalWinRate"] = round((totalWins / totalTrades) * 100, 2)
                
        return result

    def calculateRangeMetrics(self, tokens: List[Any], minAmount: float, maxAmount: Optional[float]) -> Dict[str, Any]:
        """
        Calculate investment metrics for tokens within a specific range.
        
        Args:
            tokens: List of token records from the database
            minAmount: Minimum investment amount for the range
            maxAmount: Maximum investment amount for the range (or None for no upper limit)
            
        Returns:
            Dictionary with calculated metrics for the range
        """
        # Initialize metrics
        rangeMetrics = {
            "numTokens": 0,
            "totalInvested": 0,
            "totalTakenOut": 0,
            "realizedPnl": 0,
            "realizedReturnPercentage": 0,
            "realizedWinCount": 0,
            "realizedLossCount": 0,
            "realizedWinRate": 0,
            "remainingValue": 0,
            "totalPnl": 0,
            "totalReturnPercentage": 0,
            "totalWinCount": 0,
            "totalLossCount": 0,
            "totalWinRate": 0
        }
        
        # Filter tokens within the range
        rangeTokens = []
        for token in tokens:
            amountInvested = float(token[3]) if token[3] is not None else 0
            
            if amountInvested >= minAmount and (maxAmount is None or amountInvested <= maxAmount):
                rangeTokens.append(token)
        
        # Calculate metrics if there are tokens in this range
        if rangeTokens:
            rangeMetrics["numTokens"] = len(rangeTokens)
            
            # Initialize dictionaries to store token data
            tokensWithRemainingCoins = {}
            tokenIdToIndexMap = {}
            
            # First pass: calculate realized metrics and identify tokens with remaining coins
            for i, token in enumerate(rangeTokens):
                tokenId = token[1]
                tokenIdToIndexMap[tokenId] = i
                
                amountInvested = float(token[3]) if token[3] is not None else 0
                amountTakenOut = float(token[4]) if token[4] is not None else 0
                remainingCoins = float(token[5]) if token[5] is not None else 0
                
                # Calculate realized PNL
                realizedPNL = amountTakenOut - amountInvested
                
                rangeMetrics["totalInvested"] += amountInvested
                rangeMetrics["totalTakenOut"] += amountTakenOut
                rangeMetrics["realizedPnl"] += realizedPNL
                
                # Count realized wins and losses
                if realizedPNL >= 0:
                    rangeMetrics["realizedWinCount"] += 1
                else:
                    rangeMetrics["realizedLossCount"] += 1
                
                # Store tokens with remaining coins for batch price lookup
                if remainingCoins > 0:
                    tokensWithRemainingCoins[tokenId] = remainingCoins
            
            # Fetch token prices for tokens with remaining coins
            remainingValues = self.calculateRemainingValues(tokensWithRemainingCoins)
            
            # Second pass: calculate total metrics with remaining values
            for tokenId in tokenIdToIndexMap:
                tokenIndex = tokenIdToIndexMap[tokenId]
                token = rangeTokens[tokenIndex]
                
                amountInvested = float(token[3]) if token[3] is not None else 0
                amountTakenOut = float(token[4]) if token[4] is not None else 0
                
                # Calculate realized PNL
                realizedPNL = amountTakenOut - amountInvested
                
                # Get remaining value for this token
                remainingValue = remainingValues.get(tokenId, 0)
                rangeMetrics["remainingValue"] += remainingValue
                
                # Calculate total PNL
                totalPNL = realizedPNL + remainingValue
                rangeMetrics["totalPnl"] += totalPNL
                
                # Count total wins and losses
                if totalPNL >= 0:
                    rangeMetrics["totalWinCount"] += 1
                else:
                    rangeMetrics["totalLossCount"] += 1
            
            # Calculate return percentages if there's investment
            if rangeMetrics["totalInvested"] > 0:
                rangeMetrics["realizedReturnPercentage"] = (rangeMetrics["realizedPnl"] / rangeMetrics["totalInvested"]) * 100
                rangeMetrics["totalReturnPercentage"] = (rangeMetrics["totalPnl"] / rangeMetrics["totalInvested"]) * 100
            
            # Calculate win rates
            if rangeMetrics["numTokens"] > 0:
                rangeMetrics["realizedWinRate"] = (rangeMetrics["realizedWinCount"] / rangeMetrics["numTokens"]) * 100
                rangeMetrics["totalWinRate"] = (rangeMetrics["totalWinCount"] / rangeMetrics["numTokens"]) * 100
        
        return rangeMetrics

    def calculateRemainingValues(self, tokensWithRemainingCoins: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate the current value of remaining coins using DexScreener prices
        
        Args:
            tokens_with_remaining_coins: Dictionary mapping token IDs to remaining coin amounts
            
        Returns:
            Dictionary mapping token IDs to current USD values
        """
        remainingValues = {}
        
        # Skip if no tokens with remaining coins
        if not tokensWithRemainingCoins:
            return remainingValues
            
        try:
            # Get token IDs for batch price lookup
            tokenIds = list(tokensWithRemainingCoins.keys())
            
            # Fetch prices from DexScreener
            tokenPrices = self.dexScreener.getBatchTokenPrices(tokenIds)
            
            # Calculate remaining value for each token
            for tokenId, remainingCoins in tokensWithRemainingCoins.items():
                tokenPriceData = tokenPrices.get(tokenId)
                if tokenPriceData and tokenPriceData.price:
                    remainingValues[tokenId] = remainingCoins * tokenPriceData.price
                else:
                    remainingValues[tokenId] = 0
                    logger.warning(f"Could not fetch price for token {tokenId}")
                    
        except Exception as e:
            logger.error(f"Error fetching token prices: {str(e)}")
            # Set all remaining values to 0 if price fetching fails
            for tokenId in tokensWithRemainingCoins:
                remainingValues[tokenId] = 0
                
        return remainingValues 