from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import Dict, List, Optional, Any
import sqlite3
from datetime import datetime
from logs.logger import get_logger
from decimal import Decimal
from actions.SMWalletInvestmentRangeReportAction import SMWalletInvestmentRangeReportAction

logger = get_logger(__name__)

class SMWalletInvestmentRangeReportHandler(BaseDBHandler):
    """
    Handler for smart money wallet investment range report operations.
    Provides methods to fetch data from the database for investment range reports.
    """
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
        self.reportAction = SMWalletInvestmentRangeReportAction()
        
    def getInvestmentRangeReport(self, walletAddress: str) -> Dict[str, Any]:
        """
        Get investment performance metrics categorized by investment amount ranges.
        
        Args:
            walletAddress: The wallet address to analyze
            
        Returns:
            Dictionary with investment metrics for each range
        """
        try:
            # Fetch token data from the database
            tokens = self._fetchWalletTokens(walletAddress)
            
            # Delegate processing to the action class
            return self.reportAction.processReportData(tokens, walletAddress)
                
        except Exception as e:
            logger.error(f"Error generating investment range report for {walletAddress}: {str(e)}")
            return {"error": str(e), "walletAddress": walletAddress}
    
    def _fetchWalletTokens(self, walletAddress: str) -> List[sqlite3.Row]:
        """
        Fetch token data for a specific wallet from the database.
        
        Args:
            walletAddress: The wallet address to fetch tokens for
            
        Returns:
            List of token data rows
        """
        query = """
            SELECT 
                walletaddress,
                tokenid,
                name,
                amountinvested,
                amounttakenout,
                remainingcoins,
                unprocessedpnl
            FROM smwallettoppnltoken
            WHERE walletaddress = ?
            AND amountinvested > 0
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (walletAddress,))
            return cursor.fetchall()
    
    def getInvestmentRangeReportForWallets(self, walletAddresses: List[str]) -> List[Dict[str, Any]]:
        """
        Get investment range reports for multiple wallets.
        
        Args:
            walletAddresses: List of wallet addresses to generate reports for
            
        Returns:
            List of investment range reports for each wallet
        """
        reports = []
        
        for walletAddress in walletAddresses:
            report = self.getInvestmentRangeReport(walletAddress)
            reports.append(report)
            
        return reports
        
    def getTopWalletsInvestmentRangeReport(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get investment range reports for top wallets based on total PNL.
        
        Args:
            limit: Maximum number of top wallets to include
            
        Returns:
            List of investment range reports for top wallets
        """
        try:
            # Get top wallets by total PNL from database
            wallet_addresses = self._fetchTopWalletAddresses(limit)
            
            # Get reports for each wallet
            return self.getInvestmentRangeReportForWallets(wallet_addresses)
                
        except Exception as e:
            logger.error(f"Error getting top wallets investment range report: {str(e)}")
            return []
    
    def _fetchTopWalletAddresses(self, limit: int) -> List[str]:
        """
        Fetch addresses of top wallets by total PNL from the database.
        
        Args:
            limit: Maximum number of wallets to return
            
        Returns:
            List of wallet addresses sorted by total PNL
        """
        query = """
            SELECT DISTINCT walletaddress
            FROM smwallettoppnltoken
            GROUP BY walletaddress
            ORDER BY SUM(unprocessedpnl) DESC
            LIMIT ?
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (limit,))
            wallets = cursor.fetchall()
            return [wallet[0] for wallet in wallets]
    
    def getTokensByRange(self, walletAddress: str, rangeId: str) -> List[Dict[str, Any]]:
        """
        Get tokens for a specific wallet and investment range.
        
        Args:
            walletAddress: The wallet address to fetch tokens for
            rangeId: The ID of the investment range
            
        Returns:
            List of token data for the specified range
        """
        try:
            # Check if rangeId is valid
            if not rangeId or rangeId == 'undefined':
                logger.warning(f"Invalid range ID: {rangeId}")
                return []
                
            # First, get the range boundaries from the range ID
            rangeBoundaries = self._getRangeBoundaries(rangeId)
            if not rangeBoundaries:
                logger.warning(f"Invalid range ID: {rangeId}")
                return []
                
            minAmount, maxAmount = rangeBoundaries
            
            # Fetch tokens within the range
            query = """
                SELECT 
                    walletaddress,
                    tokenid,
                    name,
                    amountinvested,
                    amounttakenout,
                    remainingcoins,
                    unprocessedpnl
                FROM smwallettoppnltoken
                WHERE walletaddress = ?
                AND amountinvested > 0
                AND amountinvested >= ?
                AND (amountinvested < ? OR ? IS NULL)
                ORDER BY amountinvested DESC
            """
            
            with self.transaction() as cursor:
                cursor.execute(query, (walletAddress, minAmount, maxAmount, maxAmount))
                tokens = cursor.fetchall()
                
                # Convert to list of dictionaries
                result = []
                for token in tokens:
                    result.append({
                        "walletaddress": token[0],
                        "tokenid": token[1],
                        "name": token[2],
                        "amountinvested": float(token[3]),
                        "amounttakenout": float(token[4]),
                        "remainingcoins": float(token[5]),
                        "unprocessedpnl": float(token[6])
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error fetching tokens by range for {walletAddress}, range {rangeId}: {str(e)}")
            return []
            
    def _getRangeBoundaries(self, rangeId: str) -> Optional[tuple]:
        """
        Get the min and max amount boundaries for a range ID.
        
        Args:
            rangeId: The ID of the investment range
            
        Returns:
            Tuple of (min_amount, max_amount) or None if invalid range ID
        """
        # Map range IDs to their boundaries
        rangeMap = {
            "0-1k": (0, 1000),
            "1k-10k": (1001, 10000),
            "10k-50k": (10001, 50000),
            "50k-100k": (50001, 100000),
            "100k-500k": (100001, 500000),
            "500k-1m": (500001, 1000000),
            "1m+": (1000001, float('inf'))
        }
        
        return rangeMap.get(rangeId) 