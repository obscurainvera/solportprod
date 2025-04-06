from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import List, Dict, Optional, Any, Set
from decimal import Decimal
import sqlite3
from logs.logger import get_logger
from datetime import datetime
from actions.DexscrennerAction import DexScreenerAction
from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus

logger = get_logger(__name__)

class StrategyPerformanceHandler(BaseDBHandler):
    """
    Handler for strategy performance report operations.
    Provides methods to query and analyze both strategy configuration and execution data.
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
        self._min_total_pnl = None  # Used for filtering after price updates
        
    def _build_strategy_query(self, 
                            strategy_name: str = None,
                            source: str = None,
                            min_realized_pnl: float = None,
                            sortBy: str = "strategyname",
                            sortOrder: str = "asc") -> tuple:
        """
        Build the query and parameters for fetching strategy configurations.
        
        Args:
            strategy_name: Optional filter by strategy name (case-insensitive partial match)
            source: Optional filter by source
            min_realized_pnl: Optional filter by minimum realized PNL
            sortBy: Field to sort by
            sortOrder: Sort order (asc/desc)
            
        Returns:
            tuple: (query_string, query_parameters)
        """
        query = """
            SELECT 
                s.strategyid,
                s.strategyname,
                s.source,
                s.description,
                s.createdat,
                s.updatedat
            FROM strategyconfig s
            WHERE 1=1
        """
        params = []
        
        # Apply strategy name filter if specified (case-insensitive partial match)
        if strategy_name:
            query += " AND LOWER(s.strategyname) LIKE LOWER(?)"
            params.append(f"%{strategy_name}%")
        
        # Apply source filter if specified
        if source:
            query += " AND s.source = ?"
            params.append(source)
            
        # Add sorting - ensure valid fields only
        valid_sort_fields = {
            "strategyid": "s.strategyid", 
            "strategyname": "s.strategyname",
            "source": "s.source",
            "createdat": "s.createdat",
            "updatedat": "s.updatedat"
        }
        
        # Default sort if not found
        sort_field = valid_sort_fields.get(sortBy, "s.strategyname")
        sort_order_normalized = sortOrder.upper() if sortOrder.upper() in ["ASC", "DESC"] else "ASC"
        query += f" ORDER BY {sort_field} {sort_order_normalized}"
        
        return query, params
    
    def getStrategyConfigReport(self,
                              strategy_name: str = None,
                              source: str = None,
                              min_realized_pnl: float = None,
                              min_total_pnl: float = None,
                              sortBy: str = "strategyname",
                              sortOrder: str = "asc") -> List[Dict[str, Any]]:
        """
        Get strategy configuration report with performance metrics.
        
        Args:
            strategy_name: Optional filter by strategy name
            source: Optional filter by source
            min_realized_pnl: Optional filter by minimum realized PNL
            min_total_pnl: Optional filter by minimum total PNL
            sortBy: Field to sort by (default: strategyname)
            sortOrder: Sort order (asc/desc, default: asc)
            
        Returns:
            List[Dict[str, Any]]: List of strategy configurations with performance metrics
        """
        try:
            # Save min_total_pnl for later filtering after getting prices
            self._min_total_pnl = min_total_pnl
            
            # Build the query
            query, params = self._build_strategy_query(strategy_name, source, min_realized_pnl, sortBy, sortOrder)
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                
                columns = [col[0] for col in cursor.description]
                strategies = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Enhance strategies with execution data
                strategies = self._enhance_strategies_with_execution_data(strategies, cursor, min_realized_pnl)
                
                # Log the result
                logger.info(f"Retrieved {len(strategies)} strategy configurations")
                
                return strategies
                
        except Exception as e:
            logger.error(f"Failed to get strategy config report: {str(e)}")
            return []
    
    def _enhance_strategies_with_execution_data(self, 
                                             strategies: List[Dict[str, Any]], 
                                             cursor,
                                             min_realized_pnl: float = None) -> List[Dict[str, Any]]:
        """
        Enhance strategy configurations with execution data (amounts, PNL, etc.)
        
        Args:
            strategies: List of strategy configurations
            cursor: Database cursor
            min_realized_pnl: Optional filter by minimum realized PNL
            
        Returns:
            List[Dict[str, Any]]: Enhanced strategy configurations
        """
        for strategy in strategies:
            strategy_id = strategy['strategyid']
            
            # Get execution summary data for this strategy
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(investedamount), 0) as total_invested,
                    COALESCE(SUM(amounttakenout), 0) as total_taken_out,
                    COUNT(executionid) as execution_count
                FROM strategyexecution
                WHERE strategyid = ?
            """, (strategy_id,))
            
            exec_summary = cursor.fetchone()
            
            if exec_summary:
                # Add summary data to strategy object
                strategy['amountInvested'] = float(exec_summary[0] or 0)
                strategy['amountTakenOut'] = float(exec_summary[1] or 0)
                strategy['executionCount'] = int(exec_summary[2] or 0)
                
                # Calculate realized PNL
                strategy['realizedPnl'] = strategy['amountTakenOut'] - strategy['amountInvested']
            else:
                # No executions found for this strategy
                strategy['amountInvested'] = 0
                strategy['amountTakenOut'] = 0
                strategy['executionCount'] = 0
                strategy['realizedPnl'] = 0
            
            # Get remaining coins for PNL calculation
            cursor.execute("""
                SELECT 
                    tokenid,
                    remainingcoins
                FROM strategyexecution
                WHERE strategyid = ? AND remainingcoins > 0
            """, (strategy_id,))
            
            remaining_coins = cursor.fetchall()
            strategy['tokenHoldings'] = [{'tokenId': row[0], 'remainingCoins': row[1]} for row in remaining_coins]
        
        # Apply realized PNL filter if specified
        if min_realized_pnl is not None:
            strategies = [s for s in strategies if s['realizedPnl'] >= min_realized_pnl]
            
        return strategies
    
    def _extract_token_ids(self, strategies: List[Dict[str, Any]]) -> Set[str]:
        """
        Extract all unique token IDs from strategy holdings.
        
        Args:
            strategies: List of strategy data with token holdings
            
        Returns:
            Set[str]: Set of unique token IDs
        """
        token_ids = set()
        for strategy in strategies:
            holdings = strategy.get('tokenHoldings', [])
            for holding in holdings:
                token_id = holding.get('tokenId')
                if token_id:
                    token_ids.add(token_id)
        return token_ids
    
    def updateStrategyTokenPrices(self, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update token prices and calculate total PNL for strategies.
        
        Args:
            strategies: List of strategy records with token holdings
            
        Returns:
            List[Dict[str, Any]]: Updated strategies with token prices and PNL calculations
        """
        if not strategies:
            return []
            
        try:
            # Extract all unique token IDs
            token_ids = self._extract_token_ids(strategies)
            
            if not token_ids:
                # No tokens to fetch prices for
                for strategy in strategies:
                    strategy['remainingCoinsValue'] = 0
                    strategy['pnl'] = strategy.get('realizedPnl', 0)
                return strategies
                
            # Use DexScreenerAction to get token prices in batch
            dex_action = DexScreenerAction()
            token_prices = dex_action.getBatchTokenPrices(list(token_ids))
            
            # Calculate remaining value and total PNL for each strategy
            for strategy in strategies:
                remaining_value = 0
                
                # Calculate value for each token holding
                for holding in strategy.get('tokenHoldings', []):
                    token_id = holding.get('tokenId')
                    remaining_coins = float(holding.get('remainingCoins', 0) or 0)
                    
                    # Get current price for token
                    current_price = 0
                    if token_id in token_prices and token_prices[token_id]:
                        current_price = token_prices[token_id].price
                    
                    # Add value to total remaining value
                    holding_value = remaining_coins * current_price
                    remaining_value += holding_value
                    
                    # Store price in holding
                    holding['currentPrice'] = current_price
                    holding['value'] = holding_value
                
                # Update strategy with total remaining value
                strategy['remainingCoinsValue'] = remaining_value
                
                # Calculate total PNL
                strategy['pnl'] = float(strategy.get('realizedPnl', 0) or 0) + remaining_value
            
            # Apply total PNL filter if specified
            if self._min_total_pnl is not None:
                strategies = [s for s in strategies if s.get('pnl', 0) >= self._min_total_pnl]
                
            return strategies
            
        except Exception as e:
            logger.error(f"Failed to update strategy token prices: {str(e)}")
            return strategies  # Return original strategies without price updates
    
    def _build_executions_query(self,
                              strategyId: int = None,
                              strategy_name: str = None,
                              source: str = None,
                              token_id: str = None,
                              token_name: str = None,
                              min_realized_pnl: float = None,
                              sortBy: str = "createdat",
                              sortOrder: str = "desc") -> tuple:
        """
        Build the query and parameters for fetching strategy executions.
        
        Args:
            strategyId: Optional filter by strategy ID
            strategy_name: Optional filter by strategy name (case-insensitive partial match)
            source: Optional filter by source
            token_id: Optional filter by token ID (exact match)
            token_name: Optional filter by token name (case-insensitive partial match)
            min_realized_pnl: Optional filter by minimum realized PNL
            sortBy: Field to sort by
            sortOrder: Sort order (asc/desc)
            
        Returns:
            tuple: (query_string, query_parameters)
        """
        query = """
            SELECT 
                e.executionid,
                e.strategyid,
                s.strategyname,
                s.source,
                e.tokenid,
                e.tokenname,
                e.description,
                e.avgentryprice,
                e.investedamount,
                e.remainingcoins,
                e.amounttakenout,
                e.status,
                e.createdat,
                e.updatedat
            FROM strategyexecution e
            JOIN strategyconfig s ON e.strategyid = s.strategyid
            WHERE 1=1
        """
        params = []
        
        # Apply strategy ID filter if specified
        if strategyId:
            query += " AND e.strategyid = ?"
            params.append(strategyId)
            
        # Apply strategy name filter if specified (case-insensitive partial match)
        if strategy_name:
            query += " AND LOWER(s.strategyname) LIKE LOWER(?)"
            params.append(f"%{strategy_name}%")
            
        # Apply token ID filter if specified
        if token_id:
            query += " AND e.tokenid = ?"
            params.append(token_id)
        
        # Apply source filter if specified
        if source:
            query += " AND s.source = ?"
            params.append(source)
            
        # Apply token name filter if specified (case-insensitive partial match)
        if token_name:
            query += " AND LOWER(e.tokenname) LIKE LOWER(?)"
            params.append(f"%{token_name}%")
        
        # Calculate realized PNL for filtering
        realized_pnl_subquery = "(e.amounttakenout - e.investedamount)"
        
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
            "investedamount": "e.investedamount",
            "amounttakenout": "e.amounttakenout",
            "createdat": "e.createdat",
            "updatedat": "e.updatedat"
        }
        
        # Default sort if not found
        sort_field = valid_sort_fields.get(sortBy, "e.createdat")
        sort_order_normalized = sortOrder.upper() if sortOrder.upper() in ["ASC", "DESC"] else "DESC"
        query += f" ORDER BY {sort_field} {sort_order_normalized}"
        
        return query, params
    
    def _enhance_executions_with_metrics(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance execution data with calculated metrics (PNL, status descriptions, etc.)
        
        Args:
            executions: List of raw execution data
            
        Returns:
            List[Dict[str, Any]]: Enhanced executions with additional metrics
        """
        # Extract all token IDs for token price fetching
        token_ids = set()
        
        for execution in executions:
            amount_invested = float(execution.get('investedamount', 0) or 0)
            amount_taken_out = float(execution.get('amounttakenout', 0) or 0)
            remaining_coins = float(execution.get('remainingcoins', 0) or 0)
            entry_price = float(execution.get('avgentryprice', 0) or 0)
            
            # Calculate realized PNL
            realized_pnl = amount_taken_out - amount_invested
            execution['realizedPnl'] = realized_pnl
            
            # Format the status with description
            status_value = int(execution.get('status', 0) or 0)
            execution['statusDescription'] = ExecutionStatus.getDescription(status_value)
            execution['canTrade'] = ExecutionStatus.canTrade(status_value)
            
            # Avg entry price may need calculation if not available
            if not entry_price and amount_invested > 0 and float(execution.get('coinsacquired', 0) or 0) > 0:
                entry_price = amount_invested / float(execution.get('coinsacquired', 1) or 1)
                execution['avgentryprice'] = entry_price
            
            # Store token_id for price lookup (ensure camelCase for frontend)
            execution['tokenId'] = execution.get('tokenid')
            
            # Add to token IDs for batch lookup
            if execution.get('tokenid'):
                token_ids.add(execution.get('tokenid'))
                
        return executions, token_ids
        
    def getStrategyExecutions(self, 
                            strategyId: int,
                            min_realized_pnl: float = None,
                            min_total_pnl: float = None) -> List[Dict[str, Any]]:
        """
        Get executions for a specific strategy.
        
        Args:
            strategyId: Strategy ID to get executions for
            min_realized_pnl: Optional filter by minimum realized PNL
            min_total_pnl: Optional filter by minimum total PNL
            
        Returns:
            List[Dict[str, Any]]: List of executions for the strategy
        """
        try:
            # Save min_total_pnl for later filtering after getting prices
            self._min_total_pnl = min_total_pnl
            
            # Build the query
            query, params = self._build_executions_query(
                strategyId=strategyId,
                min_realized_pnl=min_realized_pnl
            )
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                
                columns = [col[0] for col in cursor.description]
                executions = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Calculate additional metrics
                executions, _ = self._enhance_executions_with_metrics(executions)
                
                # Log the result
                logger.info(f"Retrieved {len(executions)} executions for strategy ID {strategyId}")
                
                return executions
                
        except Exception as e:
            logger.error(f"Failed to get strategy executions: {str(e)}")
            return []
    
    def getAllExecutions(self,
                       strategy_name: str = None,
                       source: str = None,
                       token_id: str = None,
                       token_name: str = None,
                       min_realized_pnl: float = None,
                       min_total_pnl: float = None,
                       sortBy: str = "createdat",
                       sortOrder: str = "desc") -> List[Dict[str, Any]]:
        """
        Get all strategy executions with optional filters.
        
        Args:
            strategy_name: Optional filter by strategy name
            source: Optional filter by source
            token_id: Optional filter by token ID
            token_name: Optional filter by token name
            min_realized_pnl: Optional filter by minimum realized PNL
            min_total_pnl: Optional filter by minimum total PNL
            sortBy: Field to sort by (default: createdat)
            sortOrder: Sort order (asc/desc, default: desc)
            
        Returns:
            List[Dict[str, Any]]: List of executions with performance metrics
        """
        try:
            # Save min_total_pnl for later filtering after getting prices
            self._min_total_pnl = min_total_pnl
            
            # Build the query
            query, params = self._build_executions_query(
                strategy_name=strategy_name,
                source=source,
                token_id=token_id,
                token_name=token_name,
                min_realized_pnl=min_realized_pnl,
                sortBy=sortBy,
                sortOrder=sortOrder
            )
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                
                columns = [col[0] for col in cursor.description]
                executions = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Calculate additional metrics
                executions, _ = self._enhance_executions_with_metrics(executions)
                
                # Log the result
                logger.info(f"Retrieved {len(executions)} executions")
                
                return executions
                
        except Exception as e:
            logger.error(f"Failed to get executions: {str(e)}")
            return []
    
    def updateExecutionPrices(self, executions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update token prices and calculate total PNL for executions.
        
        Args:
            executions: List of execution records
            
        Returns:
            List[Dict[str, Any]]: Updated executions with token prices and PNL calculations
        """
        if not executions:
            return []
            
        try:
            # Extract all unique token IDs
            token_ids = {execution.get('tokenId') for execution in executions if execution.get('tokenId')}
            
            if not token_ids:
                # No tokens to fetch prices for
                return executions
                
            # Use DexScreenerAction to get token prices in batch
            dex_action = DexScreenerAction()
            token_prices = dex_action.getBatchTokenPrices(list(token_ids))
            
            # Calculate remaining value and total PNL for each execution
            for execution in executions:
                token_id = execution.get('tokenId')
                remaining_coins = float(execution.get('remainingcoins', 0) or 0)
                amount_invested = float(execution.get('investedamount', 0) or 0)
                amount_taken_out = float(execution.get('amounttakenout', 0) or 0)
                realized_pnl = float(execution.get('realizedPnl', 0) or 0)
                
                # Get current price for token
                current_price = 0
                if token_id in token_prices and token_prices[token_id]:
                    current_price = token_prices[token_id].price
                
                # Calculate remaining value
                remaining_value = remaining_coins * current_price
                
                # Update execution with token price data
                execution['currentPrice'] = current_price
                execution['remainingValue'] = remaining_value
                execution['pnl'] = realized_pnl + remaining_value
            
            # Apply total PNL filter if specified
            if self._min_total_pnl is not None:
                executions = [e for e in executions if e.get('pnl', 0) >= self._min_total_pnl]
                
            return executions
            
        except Exception as e:
            logger.error(f"Failed to update execution prices: {str(e)}")
            return executions  # Return original executions without price updates
    
    def getStrategyConfigById(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed configuration for a specific strategy.
        
        Args:
            strategy_id: ID of the strategy to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Strategy configuration with all details, or None if not found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                # Query for full strategy configuration
                cursor.execute("""
                    SELECT 
                        strategyid,
                        strategyname,
                        source,
                        description,
                        strategyentryconditions,
                        chartconditions,
                        investmentinstructions,
                        profittakinginstructions,
                        riskmanagementinstructions,
                        moonbaginstructions,
                        additionalinstructions,
                        status,
                        active,
                        createdat,
                        updatedat
                    FROM strategyconfig
                    WHERE strategyid = ?
                """, (strategy_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Strategy with ID {strategy_id} not found")
                    return None
                    
                columns = [col[0] for col in cursor.description]
                strategy = dict(zip(columns, row))
                
                # Get execution summary data for this strategy
                cursor.execute("""
                    SELECT 
                        COALESCE(SUM(investedamount), 0) as total_invested,
                        COALESCE(SUM(amounttakenout), 0) as total_taken_out,
                        COUNT(executionid) as execution_count
                    FROM strategyexecution
                    WHERE strategyid = ?
                """, (strategy_id,))
                
                exec_summary = cursor.fetchone()
                
                if exec_summary:
                    # Add summary data to strategy object
                    strategy['amountInvested'] = float(exec_summary[0] or 0)
                    strategy['amountTakenOut'] = float(exec_summary[1] or 0)
                    strategy['executionCount'] = int(exec_summary[2] or 0)
                    
                    # Calculate realized PNL
                    strategy['realizedPnl'] = strategy['amountTakenOut'] - strategy['amountInvested']
                else:
                    # No executions found for this strategy
                    strategy['amountInvested'] = 0
                    strategy['amountTakenOut'] = 0
                    strategy['executionCount'] = 0
                    strategy['realizedPnl'] = 0
                
                # Convert boolean fields
                strategy['active'] = bool(strategy['active'])
                
                logger.info(f"Retrieved strategy configuration for ID {strategy_id}")
                return strategy
                
        except Exception as e:
            logger.error(f"Failed to get strategy configuration for ID {strategy_id}: {str(e)}")
            return None 