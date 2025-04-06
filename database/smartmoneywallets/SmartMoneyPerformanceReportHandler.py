from config.Config import get_config
from typing import List, Dict, Any, Optional, Tuple
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from decimal import Decimal
from logs.logger import get_logger
from sqlalchemy import text

logger = get_logger(__name__)

class SmartMoneyPerformanceReportHandler(BaseDBHandler):
    """
    Handler for Smart Money Performance Report.
    Provides data for the Smart Money Performance Report showing wallet performance metrics.
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
    
    def getSmartMoneyPerformanceReport(self, 
                                     walletAddress: str = None,
                                     minProfitAndLoss: float = None,
                                     maxProfitAndLoss: float = None,
                                     minTradeCount: int = None,
                                     maxTradeCount: int = None,
                                     minInvestedAmount: float = None,
                                     sortBy: str = "profitandloss",
                                     sortOrder: str = "desc") -> List[Dict[str, Any]]:
        """
        Get Smart Money Performance Report with optional filters
        
        Args:
            walletAddress: Filter by wallet address (optional)
            minProfitAndLoss: Minimum profit and loss (optional)
            maxProfitAndLoss: Maximum profit and loss (optional)
            minTradeCount: Minimum trade count (optional)
            maxTradeCount: Maximum trade count (optional)
            minInvestedAmount: Minimum invested amount for win rate calculation (optional)
            sortBy: Field to sort by (default: profitandloss)
            sortOrder: Sort order (asc or desc, default: desc)
            
        Returns:
            List of wallet performance data dictionaries
        """
        try:
            config = get_config()
            
            # Validate sort parameters
            valid_sort_fields = ["walletaddress", "profitandloss", "tradecount", "winrate"]
            if sortBy not in valid_sort_fields:
                sortBy = "profitandloss"
                
            if sortOrder.lower() not in ["asc", "desc"]:
                sortOrder = "desc"
                
            # Map frontend sort field to database field
            db_sort_field = sortBy
            
            # Build query conditions
            conditions = ["1=1"]  # Always true condition to simplify query building
            params = []
            
            if walletAddress:
                if config.DB_TYPE == 'postgres':
                    conditions.append("w.walletaddress LIKE %s")
                else:
                    conditions.append("w.walletaddress LIKE ?")
                params.append(f"%{walletAddress}%")
                
            if minProfitAndLoss is not None:
                if config.DB_TYPE == 'postgres':
                    conditions.append("w.profitandloss >= %s")
                else:
                    conditions.append("w.profitandloss >= ?")
                params.append(minProfitAndLoss)
                
            if maxProfitAndLoss is not None:
                if config.DB_TYPE == 'postgres':
                    conditions.append("w.profitandloss <= %s")
                else:
                    conditions.append("w.profitandloss <= ?")
                params.append(maxProfitAndLoss)
                
            if minTradeCount is not None:
                if config.DB_TYPE == 'postgres':
                    conditions.append("w.tradecount >= %s")
                else:
                    conditions.append("w.tradecount >= ?")
                params.append(minTradeCount)
                
            if maxTradeCount is not None:
                if config.DB_TYPE == 'postgres':
                    conditions.append("w.tradecount <= %s")
                else:
                    conditions.append("w.tradecount <= ?")
                params.append(maxTradeCount)
            
            # Base query to get wallet data
            query = f"""
            SELECT 
                w.walletaddress,
                w.profitandloss,
                w.tradecount
            FROM smartmoneywallets w
            WHERE {" AND ".join(conditions)}
            ORDER BY {db_sort_field} {sortOrder}
            """
            
            # Execute the query
            wallet_results = []
            with self.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text(query), tuple(params))
                else:
                    cursor.execute(query, tuple(params))
                wallet_results = cursor.fetchall()
            
            # Process results
            results = []
            for wallet_row in wallet_results:
                wallet_address = wallet_row[0]
                
                # Calculate win rate based on token performance
                win_rate = self.calculateWinRate(wallet_address, minInvestedAmount)
                
                # Create result dictionary
                result = {
                    "walletaddress": wallet_address,
                    "profitandloss": wallet_row[1],
                    "tradecount": wallet_row[2],
                    "winrate": win_rate
                }
                
                results.append(result)
            
            # If sorting by win rate, we need to sort the results in Python
            if sortBy == "winrate":
                results.sort(key=lambda x: x["winrate"], reverse=(sortOrder.lower() == "desc"))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get Smart Money Performance Report: {str(e)}")
            return []
    
    def calculateWinRate(self, walletAddress: str, minInvestedAmount: float = None) -> float:
        """
        Calculate win rate for a wallet based on token performance
        
        Args:
            walletAddress: Wallet address
            minInvestedAmount: Minimum invested amount to consider (optional)
            
        Returns:
            Win rate as a percentage (0-100)
        """
        try:
            config = get_config()
            
            # Build query conditions
            if config.DB_TYPE == 'postgres':
                conditions = ["walletaddress = %s"]
            else:
                conditions = ["walletaddress = ?"]
            params = [walletAddress]
            
            if minInvestedAmount is not None:
                if config.DB_TYPE == 'postgres':
                    conditions.append("amountinvested >= %s")
                else:
                    conditions.append("amountinvested >= ?")
                params.append(minInvestedAmount)
            
            # Query to get token performance data
            query = f"""
            SELECT 
                tokenid,
                unprocessedpnl
            FROM smwallettoppnltoken
            WHERE {" AND ".join(conditions)}
            """
            
            # Execute the query
            token_results = []
            with self.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text(query), tuple(params))
                else:
                    cursor.execute(query, tuple(params))
                token_results = cursor.fetchall()
            
            # Calculate win rate
            total_tokens = len(token_results)
            if total_tokens == 0:
                return 0.0
                
            winning_tokens = sum(1 for row in token_results if row[1] > 0)
            win_rate = (winning_tokens / total_tokens) * 100
            
            return win_rate
            
        except Exception as e:
            logger.error(f"Failed to calculate win rate for wallet {walletAddress}: {str(e)}")
            return 0.0
    
    def getTopPerformers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing wallets
        
        Args:
            limit: Number of wallets to return (default: 10)
            
        Returns:
            List of top performing wallet data
        """
        try:
            config = get_config()
            
            query = """
            SELECT 
                w.walletaddress,
                w.profitandloss,
                w.tradecount
            FROM smartmoneywallets w
            ORDER BY w.profitandloss DESC
            LIMIT ?
            """
            
            # Execute the query
            results = []
            with self.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    # In PostgreSQL, LIMIT uses $1 or %s instead of ?
                    pg_query = query.replace('?', '%s')
                    cursor.execute(text(pg_query), (limit,))
                else:
                    cursor.execute(query, (limit,))
                results = cursor.fetchall()
            
            # Process results
            top_performers = []
            for row in results:
                wallet_address = row[0]
                
                # Calculate win rate
                win_rate = self.calculateWinRate(wallet_address)
                
                # Create result dictionary
                performer = {
                    "walletaddress": wallet_address,
                    "profitandloss": row[1],
                    "tradecount": row[2],
                    "winrate": win_rate
                }
                
                top_performers.append(performer)
            
            return top_performers
            
        except Exception as e:
            logger.error(f"Failed to get top performers: {str(e)}")
            return [] 