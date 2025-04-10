from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.schema import PortfolioSummary
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import List, Dict, Optional, Set, Any
from decimal import Decimal
import json
from logs.logger import get_logger
from config.PortfolioStatusEnum import PortfolioStatus
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = get_logger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class PortfolioHandler(BaseDBHandler):
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)  # Properly initialize base class
        self._create_tables()

    def _create_tables(self):
        with self.conn_manager.transaction() as cursor:
            config = get_config()
            if config.DB_TYPE == 'postgres':
                # PostgreSQL syntax
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS portsummary (
                        portsummaryid SERIAL PRIMARY KEY,
                        chainname TEXT NOT NULL,
                        tokenid TEXT NOT NULL,
                        name TEXT NOT NULL,
                        tokenage TEXT NOT NULL,
                        mcap DECIMAL NOT NULL,
                        currentprice DECIMAL NOT NULL,
                        avgprice DECIMAL NOT NULL,
                        smartbalance DECIMAL NOT NULL,
                        walletsinvesting1000 INTEGER NOT NULL,
                        walletsinvesting5000 INTEGER NOT NULL,
                        walletsinvesting10000 INTEGER NOT NULL,
                        qtychange1d DECIMAL NOT NULL,
                        qtychange7d DECIMAL NOT NULL,
                        qtychange30d DECIMAL NOT NULL,
                        status INTEGER DEFAULT 1,
                        firstseen TIMESTAMP NOT NULL,
                        lastseen TIMESTAMP NOT NULL,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT,
                        markedinactive TIMESTAMP
                    )
                '''))
                
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS portsummaryhistory (
                        historyid SERIAL PRIMARY KEY,
                        portsummaryid INTEGER NOT NULL,
                        tokenid TEXT NOT NULL,
                        chainname TEXT NOT NULL,
                        name TEXT NOT NULL,
                        tokenage TEXT NOT NULL,
                        mcap DECIMAL NOT NULL,
                        currentprice DECIMAL NOT NULL,
                        avgprice DECIMAL NOT NULL,
                        smartbalance DECIMAL NOT NULL,
                        walletsinvesting1000 INTEGER NOT NULL,
                        walletsinvesting5000 INTEGER NOT NULL,
                        walletsinvesting10000 INTEGER NOT NULL,
                        qtychange1d DECIMAL NOT NULL,
                        qtychange7d DECIMAL NOT NULL,
                        qtychange30d DECIMAL NOT NULL,
                        status INTEGER DEFAULT 1,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT,
                        FOREIGN KEY (portsummaryid) REFERENCES portsummary(portsummaryid) ON DELETE CASCADE
                    )
                '''))
            else:
                # SQLite syntax
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS portsummary (
                        portsummaryid INTEGER PRIMARY KEY AUTOINCREMENT,
                        chainname TEXT NOT NULL,
                        tokenid TEXT NOT NULL,
                        name TEXT NOT NULL,
                        tokenage TEXT NOT NULL,
                        mcap DECIMAL NOT NULL,
                        currentprice DECIMAL NOT NULL,
                        avgprice DECIMAL NOT NULL,
                        smartbalance DECIMAL NOT NULL,
                        walletsinvesting1000 INTEGER NOT NULL,
                        walletsinvesting5000 INTEGER NOT NULL,
                        walletsinvesting10000 INTEGER NOT NULL,
                        qtychange1d DECIMAL NOT NULL,
                        qtychange7d DECIMAL NOT NULL,
                        qtychange30d DECIMAL NOT NULL,
                        status INTEGER DEFAULT 1,
                        firstseen TIMESTAMP NOT NULL,
                        lastseen TIMESTAMP NOT NULL,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT,
                        markedinactive TIMESTAMP
                    )
                '''))
                
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS portsummaryhistory (
                        historyid INTEGER PRIMARY KEY AUTOINCREMENT,
                        portsummaryid INTEGER NOT NULL,
                        tokenid TEXT NOT NULL,
                        chainname TEXT NOT NULL,
                        name TEXT NOT NULL,
                        tokenage TEXT NOT NULL,
                        mcap DECIMAL NOT NULL,
                        currentprice DECIMAL NOT NULL,
                        avgprice DECIMAL NOT NULL,
                        smartbalance DECIMAL NOT NULL,
                        walletsinvesting1000 INTEGER NOT NULL,
                        walletsinvesting5000 INTEGER NOT NULL,
                        walletsinvesting10000 INTEGER NOT NULL,
                        qtychange1d DECIMAL NOT NULL,
                        qtychange7d DECIMAL NOT NULL,
                        qtychange30d DECIMAL NOT NULL,
                        status INTEGER DEFAULT 1,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        tags TEXT,
                        FOREIGN KEY (portsummaryid) REFERENCES portsummary(portsummaryid) ON DELETE CASCADE
                    )
                '''))

    def insertSummary(self, item: PortfolioSummary, session: Optional[Any] = None) -> None:
        currentTime = datetime.now()
        
        # Ensure timestamp fields are set
        if not hasattr(item, 'firstseen') or item.firstseen is None:
            item.firstseen = currentTime
        if not hasattr(item, 'lastseen') or item.lastseen is None:
            item.lastseen = currentTime
        if not hasattr(item, 'createdat') or item.createdat is None:
            item.createdat = currentTime
        if not hasattr(item, 'updatedat') or item.updatedat is None:
            item.updatedat = currentTime
        
        config = get_config()
        if config.DB_TYPE == 'postgres':
            # PostgreSQL syntax with named parameters
            query = """
                INSERT INTO portsummary (
                    chainname, tokenid, name, tokenage, mcap, currentprice,
                    avgprice, smartbalance, walletsinvesting1000,
                    walletsinvesting5000, walletsinvesting10000,
                    qtychange1d, qtychange7d, qtychange30d, status, tags,
                    firstseen, lastseen, createdat, updatedat
                ) VALUES (
                    %(chainname)s, %(tokenid)s, %(name)s, %(tokenage)s, %(mcap)s, %(currentprice)s,
                    %(avgprice)s, %(smartbalance)s, %(walletsinvesting1000)s,
                    %(walletsinvesting5000)s, %(walletsinvesting10000)s,
                    %(qtychange1d)s, %(qtychange7d)s, %(qtychange30d)s, %(status)s, %(tags)s,
                    %(firstseen)s, %(lastseen)s, %(createdat)s, %(updatedat)s
                )
            """
            params = {
                'chainname': item.chainname,
                'tokenid': item.tokenid,
                'name': item.name,
                'tokenage': item.tokenage,
                'mcap': item.mcap,
                'currentprice': item.currentprice,
                'avgprice': item.avgprice,
                'smartbalance': item.smartbalance,
                'walletsinvesting1000': item.walletsinvesting1000,
                'walletsinvesting5000': item.walletsinvesting5000,
                'walletsinvesting10000': item.walletsinvesting10000,
                'qtychange1d': item.qtychange1d,
                'qtychange7d': item.qtychange7d,
                'qtychange30d': item.qtychange30d,
                'status': item.status,
                'tags': json.dumps(item.tags) if item.tags else None,
                'firstseen': item.firstseen,
                'lastseen': item.lastseen,
                'createdat': item.createdat,
                'updatedat': item.updatedat
            }

            if session:
                session.execute(text(query), params)
            else:
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(text(query), params)
        else:
            # SQLite syntax with positional parameters
            query = """
                INSERT INTO portsummary (
                    chainname, tokenid, name, tokenage, mcap, currentprice,
                    avgprice, smartbalance, walletsinvesting1000,
                    walletsinvesting5000, walletsinvesting10000,
                    qtychange1d, qtychange7d, qtychange30d, status, tags,
                    firstseen, lastseen, createdat, updatedat
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
            params = (
                item.chainname, item.tokenid, item.name, item.tokenage, item.mcap, item.currentprice,
                item.avgprice, item.smartbalance, item.walletsinvesting1000,
                item.walletsinvesting5000, item.walletsinvesting10000,
                item.qtychange1d, item.qtychange7d, item.qtychange30d, item.status,
                json.dumps(item.tags) if item.tags else None,
                item.firstseen, item.lastseen, item.createdat, item.updatedat
            )
            
            if session:
                session.execute(query, params)
            else:
                with self.conn_manager.transaction() as cursor:
                    cursor.execute(query, params)

    def updateSummary(self, item: PortfolioSummary, cursor: Optional[Any] = None) -> None:
        currentTime = datetime.now()
        config = get_config()
        
        if config.DB_TYPE == 'postgres':
            query = """
                UPDATE portsummary SET
                    chainname = %s, name = %s, tokenage = %s, mcap = %s,
                    currentprice = %s, avgprice = %s, smartbalance = %s,
                    walletsinvesting1000 = %s, walletsinvesting5000 = %s,
                    walletsinvesting10000 = %s, qtychange1d = %s,
                    qtychange7d = %s, qtychange30d = %s, status = %s,
                    tags = %s, lastseen = %s, updatedat = %s
                WHERE tokenid = %s
            """
        else:
            query = """
                UPDATE portsummary SET
                    chainname = ?, name = ?, tokenage = ?, mcap = ?,
                    currentprice = ?, avgprice = ?, smartbalance = ?,
                    walletsinvesting1000 = ?, walletsinvesting5000 = ?,
                    walletsinvesting10000 = ?, qtychange1d = ?,
                    qtychange7d = ?, qtychange30d = ?, status = ?,
                    tags = ?, lastseen = ?, updatedat = ?
                WHERE tokenid = ?
            """
        
        params = (
            item.chainname, item.name, item.tokenage, str(item.mcap),
            str(item.currentprice), str(item.avgprice), str(item.smartbalance),
            item.walletsinvesting1000, item.walletsinvesting5000,
            item.walletsinvesting10000, str(item.qtychange1d),
            str(item.qtychange7d), str(item.qtychange30d), item.status,
            json.dumps(item.tags) if item.tags else '[]', currentTime, currentTime, item.tokenid
        )

        if cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text(query), params)
            else:
                cursor.execute(query, params)
        else:
            with self.conn_manager.transaction() as cur:
                if config.DB_TYPE == 'postgres':
                    cur.execute(text(query), params)
                else:
                    cur.execute(query, params)

    def insertHistory(self, item: PortfolioSummary, cursor: Optional[Any] = None) -> None:
        current_time = datetime.now()
        config = get_config()
        
        if config.DB_TYPE == 'postgres':
            query = """
                INSERT INTO portsummaryhistory (
                    portsummaryid, tokenid, chainname, name, tokenage,
                    mcap, currentprice, avgprice, smartbalance,
                    walletsinvesting1000, walletsinvesting5000,
                    walletsinvesting10000, qtychange1d, qtychange7d,
                    qtychange30d, status, tags, createdat, updatedat
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
        else:
            query = """
                INSERT INTO portsummaryhistory (
                    portsummaryid, tokenid, chainname, name, tokenage,
                    mcap, currentprice, avgprice, smartbalance,
                    walletsinvesting1000, walletsinvesting5000,
                    walletsinvesting10000, qtychange1d, qtychange7d,
                    qtychange30d, status, tags, createdat, updatedat
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """
        
        # Ensure createdat is not None
        item_createdat = item.createdat if hasattr(item, 'createdat') and item.createdat is not None else current_time
        
        # Ensure tags are properly serialized as JSON
        if hasattr(item, 'tags'):
            if isinstance(item.tags, list):
                tags_json = json.dumps(item.tags)
            elif isinstance(item.tags, str):
                # If it's already a string, check if it's valid JSON
                try:
                    # Try to parse and re-serialize to ensure valid JSON
                    parsed = json.loads(item.tags)
                    tags_json = json.dumps(parsed)
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, treat as comma-separated and convert to JSON
                    tags_list = [tag.strip() for tag in item.tags.split(',') if tag.strip()]
                    tags_json = json.dumps(tags_list)
            else:
                tags_json = '[]'
        else:
            tags_json = '[]'
        
        params = (
            item.portsummaryid, item.tokenid, item.chainname,
            item.name, item.tokenage, str(item.mcap),
            str(item.currentprice), str(item.avgprice),
            str(item.smartbalance), item.walletsinvesting1000,
            item.walletsinvesting5000, item.walletsinvesting10000,
            str(item.qtychange1d), str(item.qtychange7d),
            str(item.qtychange30d), item.status,
            tags_json,
            item_createdat, current_time  # Use safe createdat value
        )

        if cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text(query), params)
            else:
                cursor.execute(query, params)
        else:
            with self.conn_manager.transaction() as cur:
                if config.DB_TYPE == 'postgres':
                    cur.execute(text(query), params)
                else:
                    cur.execute(query, params)

    def getTokenData(self, token_ids: List[str]) -> List[PortfolioSummary]:
        """
        Get token data by token IDs without filtering by status
        
        Args:
            token_ids: List of token IDs to retrieve
            
        Returns:
            List of PortfolioSummary objects for the requested token IDs
        """
        config = get_config()
        
        if config.DB_TYPE == 'postgres':
            placeholders = ', '.join(['%s'] * len(token_ids))
        else:
            placeholders = ','.join(['?'] * len(token_ids))
            
        query = f"""
            SELECT * FROM portsummary 
            WHERE tokenid IN ({placeholders})
        """
        
        with self.conn_manager.transaction() as cursor:
            try:
                # Log the query and parameters for debugging
                logger.debug(f"Executing query: {query}")
                logger.debug(f"Parameters: token_ids={token_ids}")
                
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text(query), token_ids)
                else:
                    cursor.execute(query, token_ids)
                
                rows = cursor.fetchall()
                
                # Log the number of rows returned
                logger.debug(f"Found {len(rows)} rows for token_ids {token_ids}")
                
                return [PortfolioSummary(**dict(row)) for row in rows]
                
            except Exception as e:
                logger.error(f"Error in getTokenData: {str(e)}")
                raise

    def getActivePortfolioTokens(self) -> List[Dict]:
        config = get_config()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM portsummary 
                    WHERE status = %s
                """), (PortfolioStatus.ACTIVE.statuscode,))
            else:
                cursor.execute("""
                    SELECT * FROM portsummary 
                    WHERE status = ?
                """, (PortfolioStatus.ACTIVE.statuscode,))
            
            return [dict(row) for row in cursor.fetchall()]

    def getTokenDataFromPortSummary(self, tokenId: str) -> Optional[Dict]:
        """
        Get token data by token ID without filtering by status
        
        Args:
            tokenId: Token identifier
            
        Returns:
            Dict containing token data or None if not found
        """
        config = get_config()
        
        try:
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT 
                            portsummaryid,
                            tokenid,
                            status
                        FROM portsummary
                        WHERE tokenid = %s
                    """), (tokenId,))
                else:
                    cursor.execute("""
                        SELECT 
                            portsummaryid,
                            tokenid,
                            status
                        FROM portsummary
                        WHERE tokenid = ?
                    """, (tokenId,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get token portsummary: {str(e)}")
            return None

    def deactivateTokensLostSMBalance(self, cursor: Optional[Any] = None) -> int:
        """
        Mark tokens as inactive (status=2) if they haven't been seen for 2+ days
        
        Args:
            cursor: Optional database cursor. If not provided, a new transaction will be created.
            
        Returns:
            int: Number of records marked as inactive
        """
        try:
            # Use provided cursor or create a new transaction
            if cursor is None:
                with self.conn_manager.transaction() as cursor:
                    return self.performDeactivation(cursor)
            else:
                return self.performDeactivation(cursor)
                
        except Exception as e:
            logger.error(f"Failed to deactivate tokens that lost SM balance: {str(e)}")
            raise

    def performDeactivation(self, cursor) -> int:
        """
        Internal method to perform the actual deactivation
        
        Args:
            cursor: Database cursor
            
        Returns:
            int: Number of records marked as inactive
        """
        currentTime = datetime.now()
        cutoffDate = (currentTime - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Deactivating tokens not seen since: {cutoffDate}")
        
        # Find tokens to deactivate
        cursor.execute("""
            SELECT portsummaryid, tokenid, name, lastseen
            FROM portsummary 
            WHERE status = ?  -- Active records only
            AND lastseen < ?  -- More than 2 days old
            AND (markedinactive IS NULL OR status != ?)  -- Not already marked inactive
        """, (PortfolioStatus.ACTIVE.statuscode, cutoffDate, PortfolioStatus.INACTIVE.statuscode))
        
        tokensToDeactivate = cursor.fetchall()
        
        if not tokensToDeactivate:
            logger.info("No tokens found to deactivate")
            return 0
            
        # Log tokens that will be deactivated
        logger.info(f"Found {len(tokensToDeactivate)} tokens to deactivate:")
        tokenIds = []
        
        for token in tokensToDeactivate:
            tokenIds.append(token['portsummaryid'])
            logger.info(f"Will deactivate token: {token['name']} (ID: {token['tokenid']}) "
                      f"Last seen: {token['lastseen']}")
        
        # Update the status of these tokens
        placeholders = ','.join(['?'] * len(tokenIds))
        updateQuery = f"""
            UPDATE portsummary 
            SET 
                status = ?,  -- Set to inactive
                markedinactive = ?,  -- Record when it was marked inactive
                updatedat = ?
            WHERE portsummaryid IN ({placeholders})
        """
        
        cursor.execute(updateQuery, [PortfolioStatus.INACTIVE.statuscode, currentTime, currentTime] + tokenIds)
        affectedRows = cursor.rowcount
        
        logger.info(f"Successfully deactivated {affectedRows} tokens")
        return affectedRows

    def getActiveTokensSince(self, timestamp: datetime) -> List[PortfolioSummary]:
        """Get active tokens since given timestamp"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute("""
                SELECT * FROM portsummary 
                WHERE status = ? 
                AND lastseen >= ?
            """, (PortfolioStatus.ACTIVE.statuscode, timestamp.strftime('%Y-%m-%d %H:%M:%S')))
            return [PortfolioSummary(**dict(row)) for row in cursor.fetchall()]

    def updateTokenTags(self, cursor: Any, tokenId: str, tags: str, timestamp: datetime) -> None:
        """Update tags for a specific token"""
        config = get_config()
        
        if config.DB_TYPE == 'postgres':
            query = """
                UPDATE portsummary
                SET tags = %s, updatedat = %s
                WHERE tokenid = %s
            """
        else:
            query = """
                UPDATE portsummary
                SET tags = ?, updatedat = ?
                WHERE tokenid = ?
            """
        
        params = (tags, timestamp, tokenId)
        
        if config.DB_TYPE == 'postgres':
            cursor.execute(text(query), params)
        else:
            cursor.execute(query, params)

    def get_token_history(self, token_id: str, limit: int = 24) -> List[PortfolioSummary]:
        """
        Get historical records for a token
        
        Args:
            token_id: Token identifier
            limit: Maximum number of records to return
            
        Returns:
            List of historical portfolio summary records
        """
        with self.conn_manager.transaction() as cursor:
            cursor.execute("""
                SELECT * FROM portsummaryhistory 
                WHERE tokenid = ?
                ORDER BY createdat DESC
                LIMIT ?
            """, (token_id, limit))
            return [PortfolioSummary(**dict(row)) for row in cursor.fetchall()]

    def getTokenDataForAnalysis(self, tokenId: str, status: Optional[int] = None) -> Optional[Dict]:
        """
        Get comprehensive token data for analytics framework
        
        Args:
            tokenId: Token identifier
            status: Optional status filter. If provided, only returns tokens with this status
            
        Returns:
            Dict containing token data or None if not found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                if status is not None:
                    cursor.execute("""
                        SELECT * FROM portsummary
                        WHERE tokenid = ?
                        AND status = ?
                    """, (tokenId, status))
                else:
                    cursor.execute("""
                        SELECT * FROM portsummary
                        WHERE tokenid = ?
                    """, (tokenId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return dict(row)
                
        except Exception as e:
            logger.error(f"Failed to get token data for analysis: {str(e)}")
            return None

    def markTokensInactiveDuringUpdate(self, tokens_to_mark_inactive: Set[str], cursor: Optional[Any] = None) -> int:
        """
        Mark specific tokens as inactive during a mass update
        
        Args:
            tokens_to_mark_inactive: Set of token IDs to mark as inactive
            cursor: Optional database cursor
            
        Returns:
            int: Number of tokens marked as inactive
        """
        currentTime = datetime.now()
        
        if not tokens_to_mark_inactive:
            return 0
            
        try:
            # Use provided cursor or create a new transaction
            if cursor is None:
                with self.conn_manager.transaction() as cursor:
                    return self._execute_mark_inactive(cursor, tokens_to_mark_inactive, currentTime)
            else:
                return self._execute_mark_inactive(cursor, tokens_to_mark_inactive, currentTime)
                
        except Exception as e:
            logger.error(f"Failed to mark tokens as inactive: {str(e)}")
            return 0

    def _execute_mark_inactive(self, cursor: Any, tokens_to_mark_inactive: Set[str], timestamp: datetime) -> int:
        """
        Execute the update to mark tokens as inactive
        
        Args:
            cursor: Database cursor
            tokens_to_mark_inactive: Set of token IDs to mark inactive
            timestamp: Current timestamp
            
        Returns:
            int: Number of rows affected
        """
        config = get_config()
        token_list = list(tokens_to_mark_inactive)
        
        if config.DB_TYPE == 'postgres':
            placeholders = ', '.join(['%s'] * len(token_list))
            query = f"""
                UPDATE portsummary
                SET status = %s, updatedat = %s, markedinactive = %s
                WHERE tokenid IN ({placeholders})
                AND status = %s
            """
            params = [PortfolioStatus.INACTIVE.statuscode, timestamp, timestamp] + token_list + [PortfolioStatus.ACTIVE.statuscode]
            cursor.execute(text(query), params)
        else:
            placeholders = ','.join(['?'] * len(token_list))
            query = f"""
                UPDATE portsummary
                SET status = ?, updatedat = ?, markedinactive = ?
                WHERE tokenid IN ({placeholders})
                AND status = ?
            """
            params = (PortfolioStatus.INACTIVE.statuscode, timestamp, timestamp) + tuple(token_list) + (PortfolioStatus.ACTIVE.statuscode,)
            cursor.execute(query, params)
        
        # Get number of rows affected
        rowcount = cursor.rowcount
        
        if rowcount > 0:
            logger.info(f"Marked {rowcount} tokens as inactive during update")
            
        return rowcount

    def persistPortfolioSummaryData(self, items: List[PortfolioSummary], market_age: list) -> Dict[str, int]:
        """
        Persist portfolio items to database with transaction management
        
        Args:
            items: List of PortfolioSummary objects to persist
            market_age: Market age filter used for this API call
            
        Returns:
            Dict: Stats about the operation (updated and inserted counts)
            
        Note:
            Uses transaction to ensure atomic updates
            Handles both new insertions and updates to existing records
        """
        if not items:
            logger.warning(f"No items to persist for market age {market_age}")
            return {"updated": 0, "inserted": 0}
            
        try:
            tokenIds = [item.tokenid for item in items]
            existingRecords = self.getTokenData(tokenIds)
            existingMap = {record.tokenid: record for record in existingRecords}
            current_time = datetime.now()
            
            updated_count = 0
            inserted_count = 0

            with self.conn_manager.transaction() as cursor:
                for item in items:
                    try:
                        # Ensure status is set to ACTIVE
                        item.status = PortfolioStatus.ACTIVE.statuscode
                        
                        # Ensure createdat and updatedat are set
                        if not hasattr(item, 'createdat') or item.createdat is None:
                            item.createdat = current_time
                        if not hasattr(item, 'updatedat') or item.updatedat is None:
                            item.updatedat = current_time
                        
                        if item.tokenid in existingMap:
                            # Insert history record first
                            existing_item = existingMap[item.tokenid]
                            # Preserve original createdat from existing record
                            if hasattr(existing_item, 'createdat') and existing_item.createdat is not None:
                                item.createdat = existing_item.createdat
                            self.insertHistory(existing_item, cursor)
                            # Then update current record
                            self.updateSummary(item, cursor)
                            updated_count += 1
                            logger.info(f"Updated existing record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}")
                        else:
                            # Insert new record
                            self.insertSummary(item, cursor)
                            inserted_count += 1
                            logger.info(f"Inserted new record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}")
                    except Exception as e:
                        logger.error(f"Failed to persist item {item.tokenid} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}: {str(e)}")
                        raise

            logger.info(f"Successfully persisted {len(items)} items (updated: {updated_count}, inserted: {inserted_count}) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}")
            return {"updated": updated_count, "inserted": inserted_count}
            
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise 