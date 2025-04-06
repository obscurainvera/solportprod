from config.config import get_config
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
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()
            
            if config.DB_TYPE == 'postgres':
                # PostgreSQL syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_registry (
                        id SERIAL PRIMARY KEY,
                        token_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        chain TEXT NOT NULL,
                        first_seen TIMESTAMP NOT NULL,
                        last_analyzed TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_metrics (
                        id SERIAL PRIMARY KEY,
                        token_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        attention_score NUMERIC NOT NULL,
                        social_score NUMERIC NOT NULL,
                        market_score NUMERIC NOT NULL,
                        rank INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (token_id) REFERENCES attention_registry(token_id) ON DELETE CASCADE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_metrics_history (
                        historyid SERIAL PRIMARY KEY,
                        metric_id INTEGER NOT NULL,
                        token_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        attention_score NUMERIC NOT NULL,
                        social_score NUMERIC NOT NULL,
                        market_score NUMERIC NOT NULL,
                        rank INTEGER,
                        created_at TIMESTAMP NOT NULL,
                        snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (token_id) REFERENCES attention_registry(token_id) ON DELETE CASCADE
                    )
                ''')
            else:
                # SQLite syntax
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_id TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        chain TEXT NOT NULL,
                        first_seen TIMESTAMP NOT NULL,
                        last_analyzed TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        attention_score NUMERIC NOT NULL,
                        social_score NUMERIC NOT NULL,
                        market_score NUMERIC NOT NULL,
                        rank INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (token_id) REFERENCES attention_registry(token_id) ON DELETE CASCADE
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS attention_metrics_history (
                        historyid INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_id INTEGER NOT NULL,
                        token_id TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        attention_score NUMERIC NOT NULL,
                        social_score NUMERIC NOT NULL,
                        market_score NUMERIC NOT NULL,
                        rank INTEGER,
                        created_at TIMESTAMP NOT NULL,
                        snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (token_id) REFERENCES attention_registry(token_id) ON DELETE CASCADE
                    )
                ''')

    def register_token(self, token_id: str, name: str, chain: str) -> Optional[int]:
        """
        Register a token for attention tracking
        
        Args:
            token_id: Unique token identifier
            name: Token name
            chain: Blockchain name
            
        Returns:
            Optional[int]: Registry ID or None if failed
        """
        try:
            config = get_config()
            current_time = datetime.now()
            
            with self.conn_manager.transaction() as cursor:
                # Check if token already exists
                existing_token = self._get_existing_token_registry_entry(cursor, token_id)
                
                if existing_token:
                    logger.info(f"Token {token_id} already registered with ID {existing_token['id']}")
                    return existing_token['id']
                
                # Insert new token
                if config.DB_TYPE == 'postgres':
                    result = cursor.execute(text("""
                        INSERT INTO attention_registry
                        (token_id, name, chain, first_seen, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """), (token_id, name, chain, current_time, current_time))
                    row = result.fetchone()
                    return row[0] if row else None
                else:
                    cursor.execute("""
                        INSERT INTO attention_registry
                        (token_id, name, chain, first_seen, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (token_id, name, chain, current_time, current_time))
                    return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to register token {token_id}: {e}")
            return None

    def _get_existing_token_registry_entry(self, cursor, token_id: str) -> Optional[Dict]:
        """
        Check if token is already registered
        
        Args:
            cursor: Database cursor
            token_id: Token identifier
            
        Returns:
            Optional[Dict]: Existing token entry or None
        """
        config = get_config()
        
        try:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM attention_registry
                    WHERE token_id = %s
                """), (token_id,))
            else:
                cursor.execute("""
                    SELECT * FROM attention_registry
                    WHERE token_id = ?
                """, (token_id,))
                
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error checking token registry: {e}")
            return None

    def save_attention_metrics(self, token_id: str, timestamp: datetime, 
                              attention_score: float, social_score: float, 
                              market_score: float, rank: Optional[int] = None) -> Optional[int]:
        """
        Save attention metrics for a token
        
        Args:
            token_id: Token identifier
            timestamp: Timestamp of the metrics
            attention_score: Overall attention score
            social_score: Social media attention score
            market_score: Market attention score
            rank: Optional ranking
            
        Returns:
            Optional[int]: Metric ID or None if failed
        """
        try:
            config = get_config()
            current_time = datetime.now()
            
            with self.conn_manager.transaction() as cursor:
                # Update last analyzed time in registry
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        UPDATE attention_registry
                        SET last_analyzed = %s
                        WHERE token_id = %s
                    """), (current_time, token_id))
                else:
                    cursor.execute("""
                        UPDATE attention_registry
                        SET last_analyzed = ?
                        WHERE token_id = ?
                    """, (current_time, token_id))
                
                # Check if metrics already exist for this timestamp
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT * FROM attention_metrics
                        WHERE token_id = %s
                        AND timestamp = %s
                    """), (token_id, timestamp))
                else:
                    cursor.execute("""
                        SELECT * FROM attention_metrics
                        WHERE token_id = ?
                        AND timestamp = ?
                    """, (token_id, timestamp))
                    
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # Save existing record to history
                    self._persist_record_to_history(cursor, existing_record)
                    
                    # Update existing record
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            UPDATE attention_metrics
                            SET attention_score = %s,
                                social_score = %s,
                                market_score = %s,
                                rank = %s
                            WHERE id = %s
                        """), (attention_score, social_score, market_score, rank, existing_record['id']))
                    else:
                        cursor.execute("""
                            UPDATE attention_metrics
                            SET attention_score = ?,
                                social_score = ?,
                                market_score = ?,
                                rank = ?
                            WHERE id = ?
                        """, (attention_score, social_score, market_score, rank, existing_record['id']))
                    
                    return existing_record['id']
                else:
                    # Insert new record
                    if config.DB_TYPE == 'postgres':
                        result = cursor.execute(text("""
                            INSERT INTO attention_metrics
                            (token_id, timestamp, attention_score, social_score, market_score, rank, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """), (token_id, timestamp, attention_score, social_score, market_score, rank, current_time))
                        row = result.fetchone()
                        return row[0] if row else None
                    else:
                        cursor.execute("""
                            INSERT INTO attention_metrics
                            (token_id, timestamp, attention_score, social_score, market_score, rank, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (token_id, timestamp, attention_score, social_score, market_score, rank, current_time))
                        return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Failed to save attention metrics for {token_id}: {e}")
            return None

    def get_attention_history(self, token_id: str, limit: int = 30) -> List[Dict]:
        """
        Get attention history for a token
        
        Args:
            token_id: Token identifier
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: List of attention metric records
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT * FROM attention_metrics
                        WHERE token_id = %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """), (token_id, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM attention_metrics
                        WHERE token_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (token_id, limit))
                    
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get attention history for {token_id}: {e}")
            return []

    def get_latest_attention(self, token_id: str) -> Optional[Dict]:
        """
        Get the most recent attention record for a token
        
        Args:
            token_id: Token identifier
            
        Returns:
            Optional[Dict]: Latest attention record or None
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                return self._get_last_attention_record(cursor, token_id)
                
        except Exception as e:
            logger.error(f"Failed to get latest attention for {token_id}: {e}")
            return None

    def _get_last_attention_record(self, cursor, token_id: str) -> Optional[Dict]:
        """
        Get the most recent attention record using an existing cursor
        
        Args:
            cursor: Database cursor
            token_id: Token identifier
            
        Returns:
            Optional[Dict]: Most recent record or None
        """
        config = get_config()
        
        try:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM attention_metrics
                    WHERE token_id = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """), (token_id,))
            else:
                cursor.execute("""
                    SELECT * FROM attention_metrics
                    WHERE token_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (token_id,))
                
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting last attention record: {e}")
            return None

    def _persist_record_to_history(self, cursor, record: Dict) -> None:
        """
        Save an attention metric record to history
        
        Args:
            cursor: Database cursor
            record: Attention metric record
        """
        config = get_config()
        current_time = datetime.now()
        
        try:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    INSERT INTO attention_metrics_history
                    (metric_id, token_id, timestamp, attention_score, social_score, 
                    market_score, rank, created_at, snapshot_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """), (
                    record['id'],
                    record['token_id'],
                    record['timestamp'],
                    record['attention_score'],
                    record['social_score'],
                    record['market_score'],
                    record['rank'],
                    record['created_at'],
                    current_time
                ))
            else:
                cursor.execute("""
                    INSERT INTO attention_metrics_history
                    (metric_id, token_id, timestamp, attention_score, social_score, 
                    market_score, rank, created_at, snapshot_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record['id'],
                    record['token_id'],
                    record['timestamp'],
                    record['attention_score'],
                    record['social_score'],
                    record['market_score'],
                    record['rank'],
                    record['created_at'],
                    current_time
                ))
        except Exception as e:
            logger.error(f"Error persisting record to history: {e}")

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
                            SELECT DISTINCT ON (token_id) 
                                m.token_id,
                                m.attention_score,
                                m.social_score,
                                m.market_score,
                                m.rank,
                                m.timestamp,
                                r.name,
                                r.chain
                            FROM attention_metrics m
                            JOIN attention_registry r ON m.token_id = r.token_id
                            ORDER BY m.token_id, m.timestamp DESC
                        )
                        SELECT * FROM latest_metrics
                        ORDER BY attention_score DESC
                        LIMIT %s
                    """), (limit,))
                else:
                    cursor.execute("""
                        WITH latest_metrics AS (
                            SELECT m.token_id, m.attention_score, m.social_score, 
                                   m.market_score, m.rank, m.timestamp, r.name, r.chain
                            FROM attention_metrics m
                            JOIN attention_registry r ON m.token_id = r.token_id
                            WHERE m.timestamp = (
                                SELECT MAX(timestamp) 
                                FROM attention_metrics 
                                WHERE token_id = m.token_id
                            )
                        )
                        SELECT * FROM latest_metrics
                        ORDER BY attention_score DESC
                        LIMIT ?
                    """, (limit,))
                    
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get top tokens by attention: {e}")
            return []

    def get_token_info(self, token_id: str) -> Optional[Dict]:
        """
        Get token registry information
        
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
                        SELECT * FROM attention_registry
                        WHERE token_id = %s
                    """), (token_id,))
                else:
                    cursor.execute("""
                        SELECT * FROM attention_registry
                        WHERE token_id = ?
                    """, (token_id,))
                    
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get token info for {token_id}: {e}")
            return None

