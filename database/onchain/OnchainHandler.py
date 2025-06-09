from config.Config import get_config
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
import json
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.operations.schema import OnchainInfo
from logs.logger import get_logger
import pytz
from sqlalchemy import text

logger = get_logger(__name__)

# Table Schema Documentation
SCHEMA_DOCS = {
    "onchaininfo": {
        "id": "Internal unique ID",
        "tokenid": "Token's contract address",
        "name": "Trading symbol (e.g., 'ROME')",
        "chain": "Blockchain (e.g., 'SOL')",
        "count": "Count of updates",
        "createdat": "When record was created",
        "updatedat": "Last data update",
    },
    "onchainstate": {
        "id": "Internal unique ID",
        "onchaininfoid": "Reference to onchaininfo.id",
        "tokenid": "Token's contract address",
        "price": "Current token price in USD",
        "marketcap": "Total market capitalization",
        "liquidity": "Available trading liquidity",
        "makers": "Number of makers",
        "price1h": "1-hour price change",
        "rank": "Ranking based on change_pct_1h",
        "age": "Token age",
        "createdat": "When record was created",
        "updatedat": "Last state update timestamp",
        "createdatist": "When record was created (IST timezone)",
    },
    "onchainhistory": {
        "id": "Internal unique ID",
        "onchainstateid": "Reference to onchainstate.id",
        "tokenid": "Token's contract address",
        "price": "Token price at snapshot",
        "marketcap": "Market cap at snapshot",
        "liquidity": "Liquidity at snapshot",
        "makers": "Number of makers at snapshot",
        "price1h": "1-hour price change at snapshot",
        "rank": "Ranking at snapshot",
        "age": "Token age at snapshot",
        "createdat": "When record was created",
        "createdatist": "When record was created (IST timezone)",
    },
}


class OnchainHandler(BaseDBHandler):
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self.schema = SCHEMA_DOCS
        self._createTables()

    def _createTables(self):
        """Creates all necessary tables for the onchain information system"""
        try:
            with self.conn_manager.transaction() as cursor:
                # 1. Base Token Information
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS onchaininfo (
                        id SERIAL PRIMARY KEY,
                        tokenid TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        chain TEXT NOT NULL,
                        count INTEGER DEFAULT 1,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP
                    )
                """
                    )
                )

                # 2. Token Current State
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS onchainstate (
                        id SERIAL PRIMARY KEY,
                        onchaininfoid INTEGER NOT NULL,
                        tokenid TEXT NOT NULL UNIQUE,
                        price DECIMAL NOT NULL,
                        marketcap DECIMAL NOT NULL,
                        liquidity DECIMAL NOT NULL,
                        makers INTEGER NOT NULL,
                        price1h DECIMAL NOT NULL,
                        rank INTEGER NOT NULL,
                        age TEXT,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP,
                        createdatist TIMESTAMP,
                        FOREIGN KEY(onchaininfoid) REFERENCES onchaininfo(id),
                        FOREIGN KEY(tokenid) REFERENCES onchaininfo(tokenid)
                    )
                """
                    )
                )

                # 3. Token History
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS onchainhistory (
                        id SERIAL PRIMARY KEY,
                        onchainstateid INTEGER NOT NULL,
                        tokenid TEXT NOT NULL,
                        price DECIMAL NOT NULL,
                        marketcap DECIMAL NOT NULL,
                        liquidity DECIMAL NOT NULL,
                        makers INTEGER NOT NULL,
                        price1h DECIMAL NOT NULL,
                        rank INTEGER NOT NULL,
                        age TEXT,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        createdatist TIMESTAMP,
                        FOREIGN KEY(onchainstateid) REFERENCES onchainstate(id),
                        FOREIGN KEY(tokenid) REFERENCES onchaininfo(tokenid)
                    )
                """
                    )
                )

            # Create indices in separate transactions
            self._createIndex(
                "idx_onchaininfo_tokenid", "onchaininfo", "tokenid"
            )
            self._createIndex(
                "idx_onchainstate_tokenid", "onchainstate", "tokenid"
            )
            self._createIndex(
                "idx_onchainhistory_tokenid", "onchainhistory", "tokenid"
            )

        except Exception as e:
            logger.error(f"Error creating tables for OnchainHandler: {e}")

    def _createIndex(self, index_name, table_name, column_name):
        """Create an index safely in its own transaction"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"
                    )
                )
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")

    def getTableDocumentation(self, tableName: str) -> dict:
        """Get documentation for a specific table"""
        return self.schema.get(tableName, {})

    def getColumnDescription(self, tableName: str, columnName: str) -> str:
        """Get description for a specific column"""
        tableSchema = self.schema.get(tableName, {})
        return tableSchema.get(columnName, "No description available")

    def getExistingTokenInfo(self, tokenId: str) -> Optional[Dict]:
        """
        Get current token info if exists
        
        Args:
            tokenId: Token ID to check
            
        Returns:
            Dict: Token info or None if not found
        """
        query = "SELECT * FROM onchaininfo WHERE tokenid = %s"
        params = (tokenId,)
        
        
        with self.conn_manager.transaction() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
            
            return [dict(row) for row in result]
        
    def getExistingTokensInfo(self, tokenIds: List[str]) -> Dict[str, Dict]:
        """
        Get current token info for multiple tokens in a single query
        
        Args:
            tokenIds: List of token IDs to check
            
        Returns:
            Dict[str, Dict]: Dictionary mapping token IDs to their info, or empty dict if none found
        """
        if not tokenIds:
            return {}
        
        try:
            # Convert list to tuple for SQL IN clause
            tokenIds_tuple = tuple(tokenIds)
            
            # Use different query syntax based on number of tokens
            if len(tokenIds) == 1:
                query = "SELECT * FROM onchaininfo WHERE tokenid = %s"
                params = (tokenIds[0],)
            else:
                # Format for IN clause with proper parameterization
                placeholders = ','.join(['%s'] * len(tokenIds))
                query = f"SELECT * FROM onchaininfo WHERE tokenid IN ({placeholders})"
                params = tokenIds
            
            result_dict = {}
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                for row in results:
                    row_dict = dict(row)
                    result_dict[row_dict['tokenid']] = row_dict
                    
            logger.info(f"Retrieved info for {len(result_dict)} tokens out of {len(tokenIds)} requested")
            return result_dict
            
        except Exception as e:
            logger.error(f"Error getting existing tokens info: {str(e)}")
            return {}

    def getExistingTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get current token state if exists"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text(
                    """
                SELECT * FROM onchainstate 
                WHERE tokenid = %s
            """
                ),
                (tokenId,),
            )
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None

    def insertTokenData(self, onchainToken: 'OnchainInfo') -> bool:
        """
        Insert or update token data into the database
        
        Args:
            onchainToken: OnchainInfo object containing token data
            
        Returns:
            bool: Success status
        """
        try:
            # Get current time
            now = datetime.now()
            
            # Also get IST timezone time for the new column
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(pytz.UTC).astimezone(ist)
            
            # First, check if token already exists in onchaininfo
            existingInfo = self.getExistingTokenInfo(onchainToken.tokenid)
            
            if existingInfo:
                # Update existing token info
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(
                        text(
                            """
                        UPDATE onchaininfo
                        SET count = count + 1,
                            updatedat = %s
                        WHERE tokenid = %s
                        RETURNING id
                        """
                        ),
                        (now, onchainToken.tokenid),
                    )
                    result = cursor.fetchone()
                    onchainInfoId = result["id"]
            else:
                # Insert new token info
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(
                        text(
                            """
                        INSERT INTO onchaininfo
                        (tokenid, name, chain, createdat, updatedat)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """
                        ),
                        (
                            onchainToken.tokenid,
                            onchainToken.name,
                            onchainToken.chain,
                            now,
                            now,
                        ),
                    )
                    result = cursor.fetchone()
                    onchainInfoId = result["id"]
            
            # Check if token state exists
            existingState = self.getExistingTokenState(onchainToken.tokenid)
            
            if existingState:
                # Save current state to history
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(
                        text(
                            """
                        INSERT INTO onchainhistory
                        (onchainstateid, tokenid, price, marketcap, liquidity, makers, price1h, rank, age, createdat, createdatist)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        ),
                        (
                            existingState["id"],
                            existingState["tokenid"],
                            existingState["price"],
                            existingState["marketcap"],
                            existingState["liquidity"],
                            existingState["makers"],
                            existingState["price1h"],
                            existingState["rank"],
                            existingState["age"],
                            now,
                            now_ist,
                        ),
                    )
                
                # Update token state
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(
                        text(
                            """
                        UPDATE onchainstate
                        SET price = %s,
                            marketcap = %s,
                            liquidity = %s,
                            makers = %s,
                            price1h = %s,
                            rank = %s,
                            age = %s,
                            updatedat = %s
                        WHERE tokenid = %s
                        """
                        ),
                        (
                            onchainToken.price,
                            onchainToken.marketcap,
                            onchainToken.liquidity,
                            onchainToken.makers,
                            onchainToken.price1h,
                            onchainToken.rank,
                            onchainToken.age,
                            now,
                            onchainToken.tokenid,
                        ),
                    )
            else:
                # Insert new token state
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(
                        text(
                            """
                        INSERT INTO onchainstate
                        (onchaininfoid, tokenid, price, marketcap, liquidity, makers, price1h, rank, age, createdat, updatedat, createdatist)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        ),
                        (
                            onchainInfoId,
                            onchainToken.tokenid,
                            onchainToken.price,
                            onchainToken.marketcap,
                            onchainToken.liquidity,
                            onchainToken.makers,
                            onchainToken.price1h,
                            onchainToken.rank,
                            onchainToken.age,
                            now,
                            now,
                            now_ist,
                        ),
                    )
            
            return True
        
        except Exception as e:
            logger.error(f"Error inserting token data: {e}")
            return False

    def getTokenState(self, tokenId: str) -> Optional[Dict]:
        """
        Get complete token state including info and current state
        
        Args:
            tokenId: Token ID to retrieve
            
        Returns:
            Dict: Combined token info and state or None if not found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute(
                    text(
                        """
                    SELECT i.*, s.*
                    FROM onchaininfo i
                    JOIN onchainstate s ON i.tokenid = s.tokenid
                    WHERE i.tokenid = %s
                    """
                    ),
                    (tokenId,),
                )
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
        except Exception as e:
            logger.error(f"Error retrieving token state: {e}")
            return None

    def getTopRankedTokens(self, limit: int = 100) -> List[Dict]:
        """
        Get top ranked tokens based on rank
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[Dict]: List of token states sorted by rank
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute(
                    text(
                        """
                    SELECT i.*, s.*
                    FROM onchaininfo i
                    JOIN onchainstate s ON i.tokenid = s.tokenid
                    ORDER BY s.rank ASC
                    LIMIT %s
                    """
                    ),
                    (limit,),
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error retrieving top ranked tokens: {e}")
            return []

    def getTokenHistory(self, tokenId: str, limit: int = 100) -> List[Dict]:
        """
        Get historical data for a specific token
        
        Args:
            tokenId: Token ID to retrieve history for
            limit: Maximum number of history records to return
            
        Returns:
            List[Dict]: List of historical token states
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute(
                    text(
                        """
                    SELECT *
                    FROM onchainhistory
                    WHERE tokenid = %s
                    ORDER BY createdat DESC
                    LIMIT %s
                    """
                    ),
                    (tokenId, limit),
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error retrieving token history: {e}")
            return []
