from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from logs.logger import get_logger

logger = get_logger(__name__)

class ReportsHandler(BaseDBHandler):
    """Handler for generating reports from portfolio data"""
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        
    def getPortSummaryReport(self, filters: Dict) -> List[Dict]:
        """
        Get filtered portfolio summary data
        
        Args:
            filters: Dictionary containing:
                - tokenid (str, optional): Partial token ID match
                - name (str, optional): Partial name match
                - smartbalance_op (str, optional): Operator (>, <, >=, <=, =)
                - smartbalance_val (float, optional): Value to compare against
                - limit (int, optional): Number of records to return
                - offset (int, optional): Number of records to skip
                
        Returns:
            List[Dict]: Filtered portfolio summary records
        """
        try:
            query = """
                SELECT 
                    portsummaryid,
                    chainname,
                    tokenid,
                    name,
                    tokenage,
                    mcap,
                    avgprice,
                    smartbalance,
                    tags,
                    createdat,
                    updatedat
                FROM portsummary 
                WHERE 1=1
            """
            params = []
            
            # Add filters dynamically
            if filters.get('tokenid'):
                query += " AND tokenid LIKE ?"
                params.append(f"%{filters['tokenid']}%")
                
            if filters.get('name'):
                query += " AND name LIKE ?"
                params.append(f"%{filters['name']}%")
                
            if filters.get('smartbalance_op') and filters.get('smartbalance_val') is not None:
                op = filters['smartbalance_op']
                if op in ['>', '<', '>=', '<=', '=']:
                    query += f" AND smartbalance {op} ?"
                    params.append(float(filters['smartbalance_val']))
                    
            # Add pagination
            if filters.get('limit'):
                query += " LIMIT ?"
                params.append(int(filters['limit']))
                
                if filters.get('offset'):
                    query += " OFFSET ?"
                    params.append(int(filters['offset']))
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting portfolio summary report: {str(e)}")
            return [] 