from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from typing import List, Dict, Optional, Any
from logs.logger import get_logger
import json
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager


logger = get_logger(__name__)

class AttentionReportHandler(BaseDBHandler):
    """
    Handler for attention report operations.
    Provides methods to query and filter attention data for reporting.
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
    
    def getAttentionReport(self,
                         tokenId: str = None,
                         name: str = None,
                         chain: str = None,
                         currentStatus: str = None,
                         minAttentionCount: int = None,
                         maxAttentionCount: int = None,
                         sortBy: str = "attentioncount",
                         sortOrder: str = "desc") -> List[Dict[str, Any]]:
        """
        Get attention report data with optional filters.
        
        Args:
            tokenId: Filter by token ID (partial match)
            name: Filter by token name (partial match)
            chain: Filter by chain name (partial match)
            currentStatus: Filter by current status (exact match)
            minAttentionCount: Minimum attention count filter
            maxAttentionCount: Maximum attention count filter
            sortBy: Field to sort by (default: attentioncount)
            sortOrder: Sort order (asc or desc, default: desc)
            
        Returns:
            List of attention data dictionaries
        """
        # Build the base query - join with attentiondata to get the latest attention score
        query = """
            SELECT 
                r.id,
                r.tokenid,
                r.name,
                r.chain,
                r.currentstatus,
                r.attentioncount,
                a.attentionscore,
                r.firstseenat,
                r.lastseenat
            FROM attentiontokenregistry r
            LEFT JOIN (
                SELECT tokenid, attentionscore
                FROM attentiondata
                WHERE (tokenid, recordedat) IN (
                    SELECT tokenid, MAX(recordedat)
                    FROM attentiondata
                    GROUP BY tokenid
                )
            ) a ON r.tokenid = a.tokenid
            WHERE 1=1
        """
        params = []

        # Add filters based on parameters
        if tokenId:
            query += " AND r.tokenid LIKE ?"
            params.append(f"%{tokenId}%")
        
        if name:
            query += " AND r.name LIKE ?"
            params.append(f"%{name}%")
        
        if chain:
            query += " AND r.chain LIKE ?"
            params.append(f"%{chain}%")
        
        if currentStatus:
            query += " AND LOWER(r.currentstatus) = LOWER(?)"
            params.append(currentStatus)
        
        if minAttentionCount is not None:
            query += " AND r.attentioncount >= ?"
            params.append(minAttentionCount)
        
        if maxAttentionCount is not None:
            query += " AND r.attentioncount <= ?"
            params.append(maxAttentionCount)
            
        # Validate sort parameters
        valid_sort_fields = ["id", "tokenid", "name", "chain", "currentstatus", "attentioncount", "attentionscore", "firstseenat", "lastseenat"]
        valid_sort_orders = ["asc", "desc"]
        
        if sortBy not in valid_sort_fields:
            sortBy = "attentioncount"
        
        if sortOrder.lower() not in valid_sort_orders:
            sortOrder = "desc"
            
        # Add sorting
        query += f" ORDER BY r.{sortBy} {sortOrder.upper()}"

        # Execute query
        with self.transaction() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convert results to list of dictionaries
            attentionData = []
            for row in results:
                attentionData.append({
                    'id': row[0],
                    'tokenId': row[1],
                    'name': row[2],
                    'chain': row[3],
                    'currentStatus': row[4],
                    'attentionCount': row[5],
                    'attentionScore': float(row[6]) if row[6] else None,
                    'firstSeenAt': row[7],
                    'lastSeenAt': row[8]
                })

        return attentionData
    
    def getAttentionHistoryById(self, tokenId: str) -> List[Dict[str, Any]]:
        """
        Get historical attention data for a specific token, grouped by date.
        
        Args:
            tokenId: The token ID to get history for
            
        Returns:
            List of historical attention data grouped by date
        """
        # Get all historical records
        history_query = """
            SELECT 
                h.historyid,
                h.tokenid,
                h.attentionscore,
                h.recordedat,
                h.updatedat
            FROM attentiondatahistory h
            WHERE h.tokenid = ?
            ORDER BY h.updatedat ASC
        """
        
        # Get the latest record from attentiondata
        latest_query = """
            SELECT 
                id,
                tokenid,
                attentionscore,
                recordedat,
                updatedat
            FROM attentiondata
            WHERE tokenid = ?
            ORDER BY updatedat DESC
            LIMIT 1
        """
        
        with self.transaction() as cursor:
            # Get historical records
            cursor.execute(history_query, (tokenId,))
            history_results = cursor.fetchall()
            
            # Get latest record
            cursor.execute(latest_query, (tokenId,))
            latest_record = cursor.fetchone()
            
            # Group records by date
            history_data = {}
            
            # Process historical records
            for row in history_results:
                date_part = row[4].split(' ')[0]  # Extract date from updatedat
                
                if date_part not in history_data:
                    history_data[date_part] = {
                        'date': date_part,
                        'records': []
                    }
                
                history_data[date_part]['records'].append({
                    'historyId': row[0],
                    'tokenId': row[1],
                    'attentionScore': float(row[2]),
                    'recordedAt': row[3],
                    'updatedAt': row[4]
                })
            
            # Add latest record if it exists
            if latest_record:
                date_part = latest_record[4].split(' ')[0]
                
                if date_part not in history_data:
                    history_data[date_part] = {
                        'date': date_part,
                        'records': []
                    }
                
                history_data[date_part]['records'].append({
                    'historyId': latest_record[0],
                    'tokenId': latest_record[1],
                    'attentionScore': float(latest_record[2]),
                    'recordedAt': latest_record[3],
                    'updatedAt': latest_record[4]
                })
            
            # Process each date group to get the latest record for that date
            result = []
            for date, data in history_data.items():
                # Sort records by updatedAt to get the latest
                sorted_records = sorted(data['records'], key=lambda x: x['updatedAt'], reverse=True)
                latest_record = sorted_records[0]
                
                result.append({
                    'date': date,
                    'attentionScore': latest_record['attentionScore'],
                    'recordedAt': latest_record['recordedAt'],
                    'updatedAt': latest_record['updatedAt']
                })
            
            # Sort final result by date
            result.sort(key=lambda x: x['date'])
            
            return result
    
    def getAttentionStatusOptions(self) -> List[str]:
        """
        Get all unique status options from the registry
        
        Returns:
            List of status values
        """
        query = """
            SELECT DISTINCT currentstatus
            FROM attentiontokenregistry
            WHERE currentstatus IS NOT NULL
        """
        
        with self.transaction() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [row[0] for row in results]
    
    def getChainOptions(self) -> List[str]:
        """
        Get all unique chain options from the registry
        
        Returns:
            List of chain values
        """
        query = """
            SELECT DISTINCT chain
            FROM attentiontokenregistry
            WHERE chain IS NOT NULL
        """
        
        with self.transaction() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [row[0] for row in results] 