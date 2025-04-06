from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.schema import PortfolioSummary
from typing import List, Dict, Optional, Any
from decimal import Decimal
import sqlite3
from logs.logger import get_logger
from datetime import datetime
import json
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager

logger = get_logger(__name__)

class PortSummaryReportHandler(BaseDBHandler):
    """
    Handler for port summary report operations.
    Provides methods to query and filter port summary data for reporting.
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
    
    def getPortSummaryReport(self, 
                            tokenId: str = None, 
                            name: str = None, 
                            chainName: str = None,
                            minMarketCap: float = None,
                            maxMarketCap: float = None,
                            minTokenAge: float = None,
                            maxTokenAge: float = None,
                            sortBy: str = "smartbalance",
                            sortOrder: str = "desc",
                            selectedTags: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get port summary report data with optional filters.
        
        Args:
            tokenId: Filter by token ID (partial match)
            name: Filter by token name (partial match)
            chainName: Filter by chain name (partial match)
            minMarketCap: Minimum market cap filter
            maxMarketCap: Maximum market cap filter
            minTokenAge: Minimum token age filter
            maxTokenAge: Maximum token age filter
            sortBy: Field to sort by (default: smartbalance)
            sortOrder: Sort order (asc or desc, default: desc)
            selectedTags: List of tags to filter by
            
        Returns:
            List of port summary data dictionaries
        """
        # Build the base query
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
                tags
            FROM portsummary
            WHERE status = 1
        """
        params = []

        # Add filters based on parameters
        if tokenId:
            query += " AND tokenid LIKE ?"
            params.append(f"%{tokenId}%")
        
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        if chainName:
            query += " AND chainname LIKE ?"
            params.append(f"%{chainName}%")
        
        if minMarketCap is not None:
            query += " AND mcap >= ?"
            params.append(minMarketCap)
        
        if maxMarketCap is not None:
            query += " AND mcap <= ?"
            params.append(maxMarketCap)
        
        if minTokenAge is not None:
            query += " AND CAST(tokenage AS FLOAT) >= ?"
            params.append(minTokenAge)
        
        if maxTokenAge is not None:
            query += " AND CAST(tokenage AS FLOAT) <= ?"
            params.append(maxTokenAge)
            
        # Validate sort parameters
        valid_sort_fields = ["portsummaryid", "chainname", "tokenid", "name", "tokenage", "mcap", "avgprice", "smartbalance"]
        valid_sort_orders = ["asc", "desc"]
        
        if sortBy not in valid_sort_fields:
            sortBy = "smartbalance"
        
        if sortOrder.lower() not in valid_sort_orders:
            sortOrder = "desc"
            
        # Add sorting
        query += f" ORDER BY {sortBy} {sortOrder.upper()}"

        # Execute query
        with self.transaction() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convert results to list of dictionaries
            portSummaryData = []
            for row in results:
                # Try to parse tags as JSON if it's a string
                tags = row[8]
                if tags and isinstance(tags, str):
                    try:
                        parsed_tags = json.loads(tags)
                        tags = parsed_tags
                    except Exception as e:
                        logger.error(f"Error parsing tags JSON: {e}")
                        # If parsing fails, split by comma (common format in the database)
                        if ',' in tags:
                            tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                        else:
                            # If it's a single tag, make it a list
                            tags = [tags]
                
                # Filter tags if selectedTags is provided
                if selectedTags:
                    # Only include records that have at least one of the selected tags
                    matching_tags = [tag for tag in tags if tag in selectedTags]
                    if not matching_tags:  # Skip records with no matching tags
                        continue
                
                portSummaryData.append({
                    'portsummaryid': row[0],
                    'chainname': row[1],
                    'tokenid': row[2],
                    'name': row[3],
                    'tokenage': float(row[4]) if row[4] else None,
                    'mcap': float(row[5]) if row[5] else None,
                    'avgprice': float(row[6]) if row[6] else None,
                    'smartbalance': float(row[7]) if row[7] else None,
                    'tags': tags if tags else []
                })

        return portSummaryData
    
    def getPortSummaryById(self, portsummaryId: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific port summary record by ID.
        
        Args:
            portsummaryId: The ID of the port summary record
            
        Returns:
            Dictionary with port summary data or None if not found
        """
        query = """
            SELECT 
                portsummaryid,
                chainname,
                tokenid,
                name,
                tokenage,
                mcap,
                currentprice,
                avgprice,
                smartbalance,
                walletsinvesting1000,
                walletsinvesting5000,
                walletsinvesting10000,
                qtychange1d,
                qtychange7d,
                qtychange30d,
                status,
                firstseen,
                lastseen,
                tags
            FROM portsummary
            WHERE portsummaryid = ?
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (portsummaryId,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                'portsummaryid': row[0],
                'chainname': row[1],
                'tokenid': row[2],
                'name': row[3],
                'tokenage': float(row[4]) if row[4] else None,
                'mcap': float(row[5]) if row[5] else None,
                'currentprice': float(row[6]) if row[6] else None,
                'avgprice': float(row[7]) if row[7] else None,
                'smartbalance': float(row[8]) if row[8] else None,
                'walletsinvesting1000': row[9],
                'walletsinvesting5000': row[10],
                'walletsinvesting10000': row[11],
                'qtychange1d': float(row[12]) if row[12] else None,
                'qtychange7d': float(row[13]) if row[13] else None,
                'qtychange30d': float(row[14]) if row[14] else None,
                'status': row[15],
                'firstseen': row[16],
                'lastseen': row[17],
                'tags': row[18]
            }
    
    def getTopPerformers(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing tokens based on market cap.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of top performing tokens
        """
        query = """
            SELECT 
                portsummaryid,
                chainname,
                tokenid,
                name,
                tokenage,
                mcap,
                avgprice,
                smartbalance
            FROM portsummary
            WHERE status = 1
            ORDER BY mcap DESC
            LIMIT ?
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            port_summary_data = []
            for row in results:
                port_summary_data.append({
                    'portsummaryid': row[0],
                    'chainname': row[1],
                    'tokenid': row[2],
                    'name': row[3],
                    'tokenage': float(row[4]) if row[4] else None,
                    'mcap': float(row[5]) if row[5] else None,
                    'avgprice': float(row[6]) if row[6] else None,
                    'smartbalance': float(row[7]) if row[7] else None
                })
                
            return port_summary_data

    def getTokenHistory(self, token_id: str) -> List[Dict[str, Any]]:
        """
        Get historical data for a specific token from both portsummary and portsummaryhistory tables.
        Groups data by date and takes the maximum values for mcap and smartbalance.
        
        Args:
            token_id (str): The token ID to fetch history for
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing historical data for the token
        """
        try:
            # Use a more efficient query that handles grouping at the database level
            query = """
                WITH combined_data AS (
                    -- Get current data from portsummary
                    SELECT 
                        tokenid,
                        name,
                        chainname,
                        tokenage,
                        mcap,
                        avgprice as price,
                        smartbalance,
                        updatedat,
                        strftime('%Y-%m-%d', updatedat) as date_key
                    FROM 
                        portsummary
                    WHERE 
                        tokenid = ?
                    
                    UNION ALL
                    
                    -- Get historical data from portsummaryhistory
                    SELECT 
                        tokenid,
                        name,
                        chainname,
                        tokenage,
                        mcap,
                        avgprice as price,
                        smartbalance,
                        updatedat,
                        strftime('%Y-%m-%d', updatedat) as date_key
                    FROM 
                        portsummaryhistory
                    WHERE 
                        tokenid = ?
                )
                SELECT 
                    tokenid,
                    name,
                    chainname,
                    tokenage,
                    MAX(mcap) as mcap,
                    MAX(price) as price,
                    MAX(smartbalance) as smartbalance,
                    date_key as updated_at,
                    MIN(updatedat) as first_updated,
                    MAX(updatedat) as last_updated
                FROM 
                    combined_data
                GROUP BY 
                    date_key
                ORDER BY 
                    date_key ASC
            """
            
            # Use transaction with cursor like in getPortSummaryById
            with self.transaction() as cursor:
                # Execute the query with the token_id parameter twice (once for each part of the UNION)
                cursor.execute(query, (token_id, token_id))
                records = cursor.fetchall()
                
                if not records:
                    return []
                
                # Process the records
                result = []
                for record in records:
                    # Extract values with proper type conversion
                    tokenid = record[0]
                    name = record[1]
                    chainname = record[2]
                    tokenage = record[3]
                    mcap = float(record[4]) if record[4] is not None else 0
                    price = float(record[5]) if record[5] is not None else 0
                    smartbalance = float(record[6]) if record[6] is not None else 0
                    date_str = record[7]
                    first_updated = record[8]
                    last_updated = record[9]
                    
                    # Parse the date to ensure it's in a consistent format
                    try:
                        # The date is already in YYYY-MM-DD format from the SQL query
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        result.append({
                            'tokenid': tokenid,
                            'name': name,
                            'chainname': chainname,
                            'tokenage': tokenage,
                            'mcap': mcap,
                            'price': price,
                            'smartbalance': smartbalance,
                            'updated_at': date_str,
                            'timestamp': date_obj.timestamp(),
                            'first_updated': first_updated,
                            'last_updated': last_updated
                        })
                    except Exception as e:
                        logger.error(f"Error parsing date {date_str}: {str(e)}")
                        # Skip records with invalid dates
                        continue
                
                # Log the first few records for debugging
                if result:
                    logger.info(f"First record: {result[0]}")
                    if len(result) > 1:
                        logger.info(f"Last record: {result[-1]}")
                
                return result
                
        except Exception as e:
            logger.error(f"Error fetching token history: {str(e)}")
            return [] 