from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from typing import List, Dict, Optional, Any
from decimal import Decimal
import sqlite3
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from logs.logger import get_logger
from datetime import datetime
from actions.DexscrennerAction import DexScreenerAction

logger = get_logger(__name__)

class StrategyExecutionReportHandler(BaseDBHandler):
    """
    Handler for strategy execution report operations.
    Provides methods to query and filter strategy execution data for reporting.
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
    
    def getAllExecutions(self, 
                         source: str = None,
                         token_name: str = None,
                         min_realized_pnl: float = None,
                         min_total_pnl: float = None,
                         sortBy: str = "createdat",
                         sortOrder: str = "desc") -> List[Dict[str, Any]]:
        """
        Get all strategy executions with optional filters.
        
        Args:
            source: Optional filter by source
            token_name: Optional filter by token name (partial match)
            min_realized_pnl: Optional filter by minimum realized PNL
            min_total_pnl: Optional filter by minimum total PNL
            sortBy: Field to sort by (default: createdat)
            sortOrder: Sort order (asc/desc, default: desc)
            
        Returns:
            List[Dict[str, Any]]: List of executions with calculated metrics
        """
        try:
            query = """
                SELECT 
                    e.*,
                    s.strategyname,
                    s.source,
                    s.description
                FROM executionstate e
                JOIN strategyconfig s ON e.strategyid = s.strategyid
                WHERE 1=1
            """
            params = []
            
            # Apply filters
            if source:
                query += " AND s.source = ?"
                params.append(source)
                
            if token_name:
                query += " AND e.tokenname LIKE ?"
                params.append(f"%{token_name}%")
                
            # Calculate realized PNL for filtering
            realized_pnl_subquery = "(e.amounttakenout - e.amountinvested)"
            
            if min_realized_pnl is not None:
                query += f" AND {realized_pnl_subquery} >= ?"
                params.append(min_realized_pnl)
                
            # Add sorting - ensure valid fields only
            valid_sort_fields = {
                "executionid": "e.executionid", 
                "strategyname": "s.strategyname",
                "tokenname": "e.tokenname",
                "source": "s.source",
                "status": "e.status",
                "amountinvested": "e.amountinvested",
                "amounttakenout": "e.amounttakenout",
                "createdat": "e.createdat",
                "updatedat": "e.updatedat"
            }
            
            # Default sort if not found
            sort_field = valid_sort_fields.get(sortBy, "e.createdat")
            query += f" ORDER BY {sort_field} {sortOrder}"
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                
                columns = [col[0] for col in cursor.description]
                executions = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Calculate additional metrics for each execution
                for execution in executions:
                    amount_invested = execution.get('amountinvested', 0) or 0
                    amount_taken_out = execution.get('amounttakenout', 0) or 0
                    remaining_coins = execution.get('remainingcoins', 0) or 0
                    entry_price = execution.get('entryprice', 0) or 0
                    
                    # Calculate realized PNL
                    realized_pnl = amount_taken_out - amount_invested
                    execution['realized_pnl'] = realized_pnl
                    
                    # Avg entry price may need calculation if not available
                    if not entry_price and amount_invested > 0 and execution.get('coinsacquired', 0) > 0:
                        entry_price = amount_invested / execution.get('coinsacquired', 1)
                        execution['entryprice'] = entry_price
                    
                    # Store token_id for price lookup
                    execution['token_id'] = execution.get('tokenid')
                
                # At this point, we need token prices to calculate total PNL
                # Store min_total_pnl for later filtering after getting prices
                self._min_total_pnl = min_total_pnl
                
                return executions
                
        except Exception as e:
            logger.error(f"Failed to get executions: {str(e)}")
            return []
    
    def updateExecutionPrices(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update current token prices and calculate remaining value and total PNL for executions.
        
        Args:
            executions: List of execution records
            
        Returns:
            List[Dict[str, Any]]: Updated executions with current prices and PNL calculations
        """
        if not executions:
            return []
            
        try:
            # Extract all unique token IDs
            token_ids = {execution['token_id'] for execution in executions if 'token_id' in execution}
            
            if not token_ids:
                # No tokens to fetch prices for
                return executions
                
            # Use DexScreenerAction to get token prices in batch
            dex_action = DexScreenerAction()
            token_prices = dex_action.getBatchTokenPrices(list(token_ids))
            
            # Calculate remaining value and total PNL for each execution
            for execution in executions:
                token_id = execution.get('token_id')
                remaining_coins = execution.get('remainingcoins', 0) or 0
                amount_invested = execution.get('amountinvested', 0) or 0
                amount_taken_out = execution.get('amounttakenout', 0) or 0
                realized_pnl = execution.get('realized_pnl', 0)
                
                # Get current price for token
                current_price = 0
                if token_id in token_prices and token_prices[token_id]:
                    current_price = token_prices[token_id].price
                
                # Calculate remaining value
                remaining_value = remaining_coins * current_price
                
                # Update execution with token price data
                execution['current_price'] = current_price
                execution['remaining_value'] = remaining_value
                execution['pnl'] = realized_pnl + remaining_value
            
            # Apply total PNL filter if specified
            if hasattr(self, '_min_total_pnl') and self._min_total_pnl is not None:
                executions = [e for e in executions if e.get('pnl', 0) >= self._min_total_pnl]
                
            return executions
            
        except Exception as e:
            logger.error(f"Failed to update execution prices: {str(e)}")
            return executions  # Return original executions without price updates
    
    def getTokenPrice(self, token_id: str) -> Optional[float]:
        """
        Get current price for a specific token.
        
        Args:
            token_id: The token ID to get price for
            
        Returns:
            Optional[float]: Current token price or None if not available
        """
        try:
            dex_action = DexScreenerAction()
            price_data = dex_action.getTokenPrice(token_id)
            
            if price_data:
                return price_data.price
            return None
            
        except Exception as e:
            logger.error(f"Failed to get token price: {str(e)}")
            return None 