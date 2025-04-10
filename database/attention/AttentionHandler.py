from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import List, Dict, Optional, Any, Union
from decimal import Decimal
from datetime import datetime, timedelta
from logs.logger import get_logger
from database.operations.schema import AttentionData, AttentionStatusEnum
import pytz
import json
from sqlalchemy import text

logger = get_logger(__name__)

class AttentionHandler(BaseDBHandler):
    """
    Handler for token attention metrics.
    Tracks attention scores over time.
    """
    
    def __init__(self, conn_manager=None):
        """Initialize with optional connection manager"""
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._createTables()
    
    def _createTables(self):
        """Creates all required tables for attention tracking"""
        try:
            config = get_config()
            
            # Create registry table
            self._createAttentionRegistryTable()
            
            # Create attention data table
            self._createAttentionDataTable()
            
            # Create history table
            self._createAttentionHistoryTable()
            
        except Exception as e:
            logger.error(f"Error creating attention tables: {e}")
            # Don't re-raise to allow initialization to continue
    
    def _createAttentionRegistryTable(self):
        """Create the attention token registry table"""
        try:
            with self.conn_manager.transaction() as cursor:
                config = get_config()
                
                if config.DB_TYPE == 'postgres':
                    # PostgreSQL syntax
                    cursor.execute(text('''
                        CREATE TABLE IF NOT EXISTS attentiontokenregistry (
                            id SERIAL PRIMARY KEY,
                            tokenid TEXT NOT NULL UNIQUE,
                            name TEXT NOT NULL,
                            chain TEXT NOT NULL,
                            firstseenat TIMESTAMP NOT NULL,
                            lastseenat TIMESTAMP NOT NULL,
                            currentstatus VARCHAR(20) DEFAULT 'NEW',
                            attentioncount INT DEFAULT 1,
                            createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    '''))
                else:
                    # SQLite syntax
                    cursor.execute(text('''
                        CREATE TABLE IF NOT EXISTS attentiontokenregistry (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            tokenid VARCHAR(255) UNIQUE,
                            name VARCHAR(100),
                            chain VARCHAR(50),
                            firstseenat TIMESTAMP NOT NULL,
                            lastseenat TIMESTAMP NOT NULL,
                            currentstatus VARCHAR(20) DEFAULT 'NEW',
                            attentioncount INT DEFAULT 1,
                            createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    '''))
        except Exception as e:
            logger.error(f"Error creating attention registry table: {e}")
    
    def _createAttentionDataTable(self):
        """Create the attention data table"""
        try:
            with self.conn_manager.transaction() as cursor:
                config = get_config()
                
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text('''
                        CREATE TABLE IF NOT EXISTS attentiondata (
                            id SERIAL PRIMARY KEY,
                            tokenid TEXT NOT NULL,
                            name TEXT,
                            chain TEXT,
                            attentionscore NUMERIC NOT NULL,
                            change1hbps INTEGER,
                            change1dbps INTEGER,
                            change7dbps INTEGER,
                            change30dbps INTEGER,
                            recordedat TIMESTAMP NOT NULL,
                            datasource VARCHAR(50),
                            registryid INTEGER,
                            createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (tokenid) REFERENCES attentiontokenregistry(tokenid) ON DELETE CASCADE
                        )
                    '''))
                else:
                    cursor.execute(text('''
                        CREATE TABLE IF NOT EXISTS attentiondata (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            tokenid VARCHAR(255),
                            name VARCHAR(100),
                            chain VARCHAR(50),
                            attentionscore TEXT NOT NULL,
                            change1hbps INTEGER,
                            change1dbps INTEGER,
                            change7dbps INTEGER,
                            change30dbps INTEGER,
                            recordedat TIMESTAMP NOT NULL,
                            datasource VARCHAR(50),
                            registryid INTEGER,
                            createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (registryid) REFERENCES attentiontokenregistry(id)
                        )
                    '''))
        except Exception as e:
            logger.error(f"Error creating attention data table: {e}")
    
    def _createAttentionHistoryTable(self):
        """Create the attention history table"""
        try:
            with self.conn_manager.transaction() as cursor:
                config = get_config()
                
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text('''
                        CREATE TABLE IF NOT EXISTS attentiondatahistory (
                            historyid SERIAL PRIMARY KEY,
                            attentiondataid INTEGER NOT NULL,
                            tokenid TEXT NOT NULL,
                            name TEXT,
                            chain TEXT,
                            attentionscore NUMERIC NOT NULL,
                            change1hbps INTEGER,
                            change1dbps INTEGER,
                            change7dbps INTEGER,
                            change30dbps INTEGER,
                            recordedat TIMESTAMP NOT NULL,
                            datasource VARCHAR(50),
                            createdat TIMESTAMP NOT NULL,
                            updatedat TIMESTAMP NOT NULL,
                            FOREIGN KEY (tokenid) REFERENCES attentiontokenregistry(tokenid) ON DELETE CASCADE
                        )
                    '''))
                else:
                    cursor.execute(text('''
                        CREATE TABLE IF NOT EXISTS attentiondatahistory (
                            historyid INTEGER PRIMARY KEY AUTOINCREMENT,
                            attentiondataid INTEGER NOT NULL,
                            tokenid VARCHAR(255),
                            name VARCHAR(100),
                            chain VARCHAR(50),
                            attentionscore TEXT NOT NULL,
                            change1hbps INTEGER,
                            change1dbps INTEGER,
                            change7dbps INTEGER,
                            change30dbps INTEGER,
                            recordedat TIMESTAMP NOT NULL,
                            datasource VARCHAR(50),
                            createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (attentiondataid) REFERENCES attentiondata(id)
                        )
                    '''))
        except Exception as e:
            logger.error(f"Error creating attention history table: {e}")

    def updateTokenRegistry(self, data: AttentionData) -> Optional[int]:
        """
        Update or create token registry entry
        
        Args:
            data: Attention data to register
            
        Returns:
            Optional[int]: Registry ID or None if failed
        """
        try:
            # Skip if no tokenid is provided
            if not data.tokenid:
                logger.warning(f"Skipping token registry update for token with no ID: {data.name}")
                return None
            
            config = get_config()
            currentTime = datetime.now()
            
            with self.conn_manager.transaction() as cursor:
                # Check if token exists
                existing = self._getExistingTokenRegistryEntry(cursor, data.tokenid)
                status = existing['currentstatus'] if existing else AttentionStatusEnum.NEW.value
                if status == AttentionStatusEnum.INACTIVE.value:
                    status = AttentionStatusEnum.NEW.value
                
                if existing:
                    # Update existing token
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            UPDATE attentiontokenregistry
                            SET lastseenat = %s,
                                updatedat = %s,
                                attentioncount = attentioncount + 1,
                                currentstatus = %s
                            WHERE tokenid = %s
                        """), (currentTime, currentTime, status, data.tokenid))
                    else:
                        cursor.execute("""
                            UPDATE attentiontokenregistry
                            SET lastseenat = ?,
                                updatedat = ?,
                                attentioncount = attentioncount + 1,
                                currentstatus = ?
                            WHERE tokenid = ?
                        """, (currentTime, currentTime, status, data.tokenid))
                    
                    logger.info(f"Updated existing token registry entry for {data.tokenid}")
                    return existing['id']
                else:
                    # Insert new token
                    if config.DB_TYPE == 'postgres':
                        result = cursor.execute(text("""
                            INSERT INTO attentiontokenregistry
                            (tokenid, name, chain, firstseenat, lastseenat, currentstatus, createdat, updatedat)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """), (data.tokenid, data.name, data.chain, currentTime, currentTime, 
                               AttentionStatusEnum.NEW.value, currentTime, currentTime))
                        row = result.fetchone()
                        registry_id = row['id'] if row else None
                    else:
                        cursor.execute("""
                            INSERT INTO attentiontokenregistry
                            (tokenid, name, chain, firstseenat, lastseenat, currentstatus, createdat, updatedat)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (data.tokenid, data.name, data.chain, currentTime, currentTime, 
                              AttentionStatusEnum.NEW.value, currentTime, currentTime))
                        registry_id = cursor.lastrowid
                    
                    logger.info(f"Created new token registry entry for {data.tokenid}")
                    return registry_id
                
        except Exception as e:
            logger.error(f"Failed to update token registry for {data.tokenid or data.name}: {str(e)}")
            return None

    def _getExistingTokenRegistryEntry(self, cursor, tokenid: str) -> Optional[Dict]:
        """
        Check if a token exists in the registry
        
        Args:
            cursor: Database cursor
            tokenid: Token ID to check
            
        Returns:
            Optional[Dict]: Existing token entry or None
        """
        config = get_config()
        
        if not tokenid:
            return None
        
        try:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT id, tokenid, chain, currentstatus, lastseenat
                    FROM attentiontokenregistry
                    WHERE tokenid = %s
                """), (tokenid,))
            else:
                cursor.execute("""
                    SELECT id, tokenid, chain, currentstatus, lastseenat
                    FROM attentiontokenregistry
                    WHERE tokenid = ?
                """, (tokenid,))
                
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error checking token registry: {e}")
            return None

    def storeCurrentAttentionData(self, data: AttentionData) -> None:
        """
        Store raw attention data and calculate hourly change
        
        Args:
            data: Attention data to store
        """
        try:
            config = get_config()
            currentTime = datetime.now()
            
            with self.conn_manager.transaction() as cursor:
                # Step 1: Update or create token registry entry to get registry ID
                registry_id = None
                if data.tokenid:
                    registry_id = self.updateTokenRegistry(data)
                
                # Step 2: Get the last record for this token (for change calculation)
                lastRecord = None
                if data.tokenid:
                    lastRecord = self._getLastAttentionRecord(cursor, data.tokenid)
                
                # Step 3: Calculate hourly change if previous record exists
                change1hbps = self._calculateHourlyChange(lastRecord, data.attentionscore)
                
                # Step 4: If we have a previous record, store it in history
                if lastRecord:
                    self._persistRecordToHistory(cursor, lastRecord)
                    logger.info(f"Stored previous record (ID: {lastRecord['id']}) in history for token {data.tokenid or data.name}")
                    
                    # Step 5a: Update the existing record
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            UPDATE attentiondata SET
                                attentionscore = %s,
                                change1hbps = %s,
                                change1dbps = %s,
                                change7dbps = %s,
                                change30dbps = %s,
                                datasource = %s,
                                registryid = %s,
                                updatedat = %s
                            WHERE id = %s
                        """), (
                            str(data.attentionscore), 
                            change1hbps,
                            data.change1dbps, 
                            data.change7dbps,
                            data.change30dbps, 
                            data.datasource,
                            registry_id,
                            currentTime,
                            lastRecord['id']
                        ))
                    else:
                        cursor.execute("""
                            UPDATE attentiondata SET
                                attentionscore = ?,
                                change1hbps = ?,
                                change1dbps = ?,
                                change7dbps = ?,
                                change30dbps = ?,
                                datasource = ?,
                                registryid = ?,
                                updatedat = ?
                            WHERE id = ?
                        """, (
                            str(data.attentionscore), 
                            change1hbps,
                            data.change1dbps, 
                            data.change7dbps,
                            data.change30dbps, 
                            data.datasource,
                            registry_id,
                            currentTime,
                            lastRecord['id']
                        ))
                    
                    logger.info(f"Updated existing record (ID: {lastRecord['id']}) for token {data.tokenid or data.name}")
                else:
                    # Step 5b: Insert a new record if no previous record exists
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            INSERT INTO attentiondata (
                                tokenid, name, chain,
                                attentionscore, change1hbps,
                                change1dbps, change7dbps,
                                change30dbps, recordedat,
                                datasource, registryid,
                                createdat, updatedat
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """), (
                            data.tokenid if data.tokenid else None, 
                            data.name if data.name else None, 
                            data.chain if data.chain else None,
                            str(data.attentionscore), 
                            change1hbps,
                            data.change1dbps, 
                            data.change7dbps,
                            data.change30dbps, 
                            data.recordedat,
                            data.datasource,
                            registry_id,
                            currentTime,
                            currentTime
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO attentiondata (
                                tokenid, name, chain,
                                attentionscore, change1hbps,
                                change1dbps, change7dbps,
                                change30dbps, recordedat,
                                datasource, registryid,
                                createdat, updatedat
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data.tokenid if data.tokenid else None, 
                            data.name if data.name else None, 
                            data.chain if data.chain else None,
                            str(data.attentionscore), 
                            change1hbps,
                            data.change1dbps, 
                            data.change7dbps,
                            data.change30dbps, 
                            data.recordedat,
                            data.datasource,
                            registry_id,
                            currentTime,
                            currentTime
                        ))
                    
                    logger.info(f"Inserted new record for token {data.tokenid or data.name}")
                
        except Exception as e:
            logger.error(f"Failed to store attention data for {data.tokenid or data.name}: {str(e)}")
            raise

    def _getLastAttentionRecord(self, cursor, tokenid: str) -> Optional[Dict]:
        """
        Get the most recent record for a token
        
        Args:
            cursor: Database cursor
            tokenid: Token ID to look up
            
        Returns:
            Optional[Dict]: Most recent record or None
        """
        config = get_config()
        
        if not tokenid:
            return None
        
        try:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * 
                    FROM attentiondata 
                    WHERE tokenid = %s 
                    ORDER BY recordedat DESC 
                    LIMIT 1
                """), (tokenid,))
            else:
                cursor.execute("""
                    SELECT * 
                    FROM attentiondata 
                    WHERE tokenid = ? 
                    ORDER BY recordedat DESC 
                    LIMIT 1
                """, (tokenid,))
                
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting last attention record: {e}")
            return None

    def _calculateHourlyChange(self, lastRecord, currentScore: Decimal) -> Optional[int]:
        """Calculate hourly change in basis points"""
        if not lastRecord or not lastRecord['attentionscore']:
            return None
            
        prevScore = Decimal(lastRecord['attentionscore'])
        if prevScore <= 0:  # Avoid division by zero
            return None
            
        return int((currentScore - prevScore) * 10000 / prevScore)

    def _persistRecordToHistory(self, cursor, record: Dict) -> None:
        """
        Store an existing record in the history table
        
        Args:
            cursor: Database cursor
            record: Record to store in history
        """
        config = get_config()
        currentTime = datetime.now()
        
        try:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    INSERT INTO attentiondatahistory (
                        attentiondataid, tokenid, name, chain,
                        attentionscore, change1hbps,
                        change1dbps, change7dbps,
                        change30dbps, recordedat,
                        datasource, createdat, updatedat
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    record['id'], 
                    record['tokenid'], 
                    record.get('name'),
                    record.get('chain'),
                    record['attentionscore'], 
                    record.get('change1hbps'),
                    record.get('change1dbps'), 
                    record.get('change7dbps'),
                    record.get('change30dbps'), 
                    record['recordedat'],
                    record.get('datasource'),
                    currentTime,
                    currentTime
                ))
            else:
                cursor.execute("""
                    INSERT INTO attentiondatahistory (
                        attentiondataid, tokenid, name, chain,
                        attentionscore, change1hbps,
                        change1dbps, change7dbps,
                        change30dbps, recordedat,
                        datasource, createdat, updatedat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['id'], 
                    record['tokenid'], 
                    record.get('name'),
                    record.get('chain'),
                    record['attentionscore'], 
                    record.get('change1hbps'),
                    record.get('change1dbps'), 
                    record.get('change7dbps'),
                    record.get('change30dbps'), 
                    record['recordedat'],
                    record.get('datasource'),
                    currentTime,
                    currentTime
                ))
        except Exception as e:
            logger.error(f"Error persisting record to history: {e}")

    def updateInactiveTokens(self) -> None:
        """
        Update status of tokens that haven't been seen for more than 1 day
        """
        try:
            config = get_config()
            currentTime = datetime.now()
            twoDaysAgo = currentTime - timedelta(days=1)
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        UPDATE attentiontokenregistry 
                        SET currentstatus = %s,
                            attentioncount = 0
                        WHERE lastseenat < %s 
                        AND currentstatus != %s
                    """), (
                        AttentionStatusEnum.INACTIVE.value,
                        twoDaysAgo,
                        AttentionStatusEnum.INACTIVE.value
                    ))
                else:
                    cursor.execute("""
                        UPDATE attentiontokenregistry 
                        SET currentstatus = ?,
                            attentioncount = 0
                        WHERE lastseenat < ? 
                        AND currentstatus != ?
                    """, (
                        AttentionStatusEnum.INACTIVE.value,
                        twoDaysAgo,
                        AttentionStatusEnum.INACTIVE.value
                    ))
                
                updatedCount = cursor.rowcount
                logger.info(f"Updated {updatedCount} inactive tokens")
                
        except Exception as e:
            logger.error(f"Failed to update inactive tokens: {str(e)}")
            raise

    def getTokenDataForAnalysis(self, tokenid: str) -> Optional[Dict]:
        """
        Get comprehensive token data for analytics framework
        
        Args:
            tokenid: Token identifier
            
        Returns:
            Dict containing token data or None if not found
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                # Get the most recent attention data for the token
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT * FROM attentiondata
                        WHERE tokenid = %s
                        ORDER BY recordedat DESC
                        LIMIT 1
                    """), (tokenid,))
                else:
                    cursor.execute("""
                        SELECT * FROM attentiondata
                        WHERE tokenid = ?
                        ORDER BY recordedat DESC
                        LIMIT 1
                    """, (tokenid,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                row_dict = dict(row)
                
                # Get registry data if available
                registryData = {}
                if row_dict.get('registryid'):
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            SELECT * FROM attentiontokenregistry
                            WHERE id = %s
                        """), (row_dict['registryid'],))
                    else:
                        cursor.execute("""
                            SELECT * FROM attentiontokenregistry
                            WHERE id = ?
                        """, (row_dict['registryid'],))
                
                    registryRow = cursor.fetchone()
                    if registryRow:
                        registryData = dict(registryRow)
                
                # Combine data
                result = row_dict
                result.update({
                    'firstseenat': registryData.get('firstseenat'),
                    'lastseenat': registryData.get('lastseenat'),
                    'currentstatus': registryData.get('currentstatus'),
                    'attentioncount': registryData.get('attentioncount')
                })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get token data for analysis: {str(e)}")
            return None

    def getAttentionInfo(self, tokenid: str) -> Optional[Dict]:
        """
        Get attention info for a token
        
        Args:
            tokenid: Token identifier
            
        Returns:
            Dict containing attention info or None if not found
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                # Get the most recent attention data and registry info
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT 
                            a.attentionscore,
                            a.change1hbps,
                            a.change1dbps,
                            a.change7dbps,
                            a.change30dbps,
                            r.currentstatus,
                            r.attentioncount,
                            r.firstseenat,
                            r.lastseenat
                        FROM attentiondata a
                        INNER JOIN attentiontokenregistry r ON a.tokenid = r.tokenid
                        WHERE a.tokenid = %s
                        ORDER BY a.updatedat DESC
                        LIMIT 1
                    """), (tokenid,))
                else:
                    cursor.execute("""
                        SELECT 
                            a.attentionscore,
                            a.change1hbps,
                            a.change1dbps,
                            a.change7dbps,
                            a.change30dbps,
                            r.currentstatus,
                            r.attentioncount,
                            r.firstseenat,
                            r.lastseenat
                        FROM attentiondata a
                        INNER JOIN attentiontokenregistry r ON a.tokenid = r.tokenid
                        WHERE a.tokenid = ?
                        ORDER BY a.updatedat DESC
                        LIMIT 1
                    """, (tokenid,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Map to dictionary
                return {
                    'attentionscore': float(row[0]) if row[0] else 0,
                    'change1hbps': row[1],
                    'change1dbps': row[2],
                    'change7dbps': row[3],
                    'change30dbps': row[4],
                    'currentstatus': row[5],
                    'attentioncount': row[6],
                    'firstseenat': row[7],
                    'lastseenat': row[8],
                    'consecutiverecords': row[6]  # Using attentioncount from registry
                }
                
        except Exception as e:
            logger.error(f"Failed to get attention info for token {tokenid}: {str(e)}")
            return None

    # For backward compatibility
    def register_token(self, token_id: str, name: str, chain: str) -> Optional[int]:
        """
        Register a token for attention tracking (legacy method)
        
        Args:
            token_id: Unique token identifier
            name: Token name
            chain: Blockchain name
            
        Returns:
            Optional[int]: Registry ID or None if failed
        """
        data = AttentionData(
            tokenid=token_id,
            name=name,
            chain=chain,
            attentionscore=Decimal('0'),
            recordedat=datetime.now()
        )
        return self.updateTokenRegistry(data)

    # For backward compatibility
    def get_top_tokens_by_attention(self, limit: int = 20) -> List[Dict]:
        """
        Get tokens with highest recent attention scores
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List[Dict]: List of tokens with attention data
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        WITH latest_metrics AS (
                            SELECT DISTINCT ON (tokenid) 
                                a.tokenid,
                                a.attentionscore,
                                a.change1hbps,
                                a.change1dbps,
                                a.change7dbps,
                                a.change30dbps,
                                a.recordedat,
                                r.name,
                                r.chain
                            FROM attentiondata a
                            JOIN attentiontokenregistry r ON a.tokenid = r.tokenid
                            ORDER BY a.tokenid, a.recordedat DESC
                        )
                        SELECT * FROM latest_metrics
                        ORDER BY attentionscore DESC
                        LIMIT %s
                    """), (limit,))
                else:
                    cursor.execute("""
                        WITH latest_metrics AS (
                            SELECT a.tokenid, a.attentionscore, a.change1hbps, 
                                   a.change1dbps, a.change7dbps, a.change30dbps,
                                   a.recordedat, r.name, r.chain
                            FROM attentiondata a
                            JOIN attentiontokenregistry r ON a.tokenid = r.tokenid
                            WHERE a.recordedat = (
                                SELECT MAX(recordedat) 
                                FROM attentiondata 
                                WHERE tokenid = a.tokenid
                            )
                        )
                        SELECT * FROM latest_metrics
                        ORDER BY attentionscore DESC
                        LIMIT ?
                    """, (limit,))
                    
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get top tokens by attention: {e}")
            return []

    # For backward compatibility
    def get_token_info(self, token_id: str) -> Optional[Dict]:
        """
        Get token registry information (legacy method)
        
        Args:
            token_id: Token identifier
            
        Returns:
            Optional[Dict]: Token registry data or None
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT * FROM attentiontokenregistry
                        WHERE tokenid = %s
                    """), (token_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM attentiontokenregistry
                        WHERE tokenid = ?
                    """, (token_id,))
                    
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get token info for {token_id}: {e}")
            return None

