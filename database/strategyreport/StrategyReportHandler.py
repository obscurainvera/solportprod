from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import List, Dict, Optional, Any
from decimal import Decimal
import sqlite3
from logs.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class StrategyReportHandler(BaseDBHandler):
    """
    Handler for strategy report operations.
    Provides methods to query and filter strategy configuration data for reporting.
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
    
    def getAllStrategies(self, 
                        source: str = None,
                        strategyname: str = None,
                        status: str = None,
                        active: bool = None,
                        sortBy: str = "createdat",
                        sortOrder: str = "desc") -> List[Dict[str, Any]]:
        """
        Get all strategies with optional filters.
        
        Args:
            source: Optional filter by source
            strategyname: Optional filter by strategy name (partial match)
            status: Optional filter by status
            active: Optional filter by active state
            sortBy: Field to sort by (default: createdat)
            sortOrder: Sort order (asc/desc, default: desc)
            
        Returns:
            List[Dict[str, Any]]: List of matching strategies
        """
        try:
            query = "SELECT * FROM strategyconfig WHERE 1=1"
            params = []
            
            # Apply filters
            if source:
                query += " AND source = ?"
                params.append(source)
                
            if strategyname:
                query += " AND strategyname LIKE ?"
                params.append(f"%{strategyname}%")
                
            if status:
                query += " AND status = ?"
                params.append(status)
                
            if active is not None:
                query += " AND active = ?"
                params.append(1 if active else 0)
                
            # Add sorting
            valid_sort_fields = ["strategyid", "strategyname", "source", "status", "createdat", "updatedat"]
            if sortBy in valid_sort_fields:
                query += f" ORDER BY {sortBy} {sortOrder}"
            else:
                query += " ORDER BY createdat DESC"
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                
                columns = [col[0] for col in cursor.description]
                strategies = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return strategies
                
        except Exception as e:
            logger.error(f"Failed to get strategies: {str(e)}")
            return []
            
    def getStrategyById(self, strategyId: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific strategy by ID.
        
        Args:
            strategyId: The ID of the strategy to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Strategy details or None if not found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM strategyconfig WHERE strategyid = ?
                ''', (strategyId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                columns = [col[0] for col in cursor.description]
                strategy = dict(zip(columns, row))
                
                # Get related executions count - safely check if table exists first
                try:
                    cursor.execute('''
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='executionstate'
                    ''')
                    
                    table_exists = cursor.fetchone() is not None
                    
                    if table_exists:
                        cursor.execute('''
                            SELECT COUNT(*) FROM executionstate 
                            WHERE strategyid = ?
                        ''', (strategyId,))
                        
                        execution_count = cursor.fetchone()[0]
                    else:
                        # Table doesn't exist, set count to 0
                        execution_count = 0
                except Exception as e:
                    logger.warning(f"Could not query execution count: {str(e)}")
                    execution_count = 0
                
                strategy['execution_count'] = execution_count
                
                return strategy
                
        except Exception as e:
            logger.error(f"Failed to get strategy by ID: {str(e)}")
            return None
            
    def getStrategyExecutionsCount(self) -> List[Dict[str, Any]]:
        """
        Get count of executions for each strategy.
        
        Returns:
            List[Dict[str, Any]]: List of strategies with their execution counts
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT s.strategyid, s.strategyname, s.source, COUNT(e.executionid) as execution_count
                    FROM strategyconfig s
                    LEFT JOIN executionstate e ON s.strategyid = e.strategyid
                    GROUP BY s.strategyid
                    ORDER BY execution_count DESC
                ''')
                
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get strategy execution counts: {str(e)}")
            return [] 