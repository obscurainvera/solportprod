from config.Config import get_config
from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
import json
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.operations.schema import VolumeToken
from logs.logger import get_logger
import pytz
from sqlalchemy import text

logger = get_logger(__name__)

# Table Schema Documentation
SCHEMA_DOCS = {
    "volumetokeninfo": {
        "id": "Internal unique ID",
        "tokenid": "Token's contract address",
        "name": "Trading symbol (e.g., 'ROME')",
        "tokenname": "Full name (e.g., 'REPUBLIC OF MEME')",
        "chain": "Blockchain (e.g., 'SOL')",
        "tokendecimals": "Token decimal places",
        "circulatingsupply": "Available supply",
        "tokenage": "Time since launch",
        "twitterlink": "Social media link",
        "telegramlink": "Community chat link",
        "websitelink": "Project website",
        "firstseenat": "When bot first detected",
        "lastupdatedat": "Last data update",
        "count": "Count of updates"
    },

    "volumetokenstates": {
        "id": "Internal unique ID",
        "tokenid": "Reference to volumetokeninfo.tokenid",
        "price": "Current token price in USD",
        "marketcap": "Total market capitalization",
        "liquidity": "Available trading liquidity",
        "volume24h": "24-hour trading volume",
        "buysolqty": "Number of SOL buy transactions",
        "occurrencecount": "Number of times token detected",
        "percentilerankpeats": "Ranking based on occurrences (0-1)",
        "percentileranksol": "Ranking based on SOL buys (0-1)",
        "dexstatus": "Trading status (true=active, false=inactive)",
        "change1hpct": "1-hour price change percentage",
        "createdat": "When record was created",
        "lastupdatedat": "Last state update timestamp"
    },

    "volumetokenhistory": {
        "id": "Internal unique ID",
        "tokenid": "Reference to volumetokeninfo.tokenid",
        "snapshotat": "When this snapshot was taken",
        "price": "Token price at snapshot",
        "marketcap": "Market cap at snapshot",
        "liquidity": "Liquidity at snapshot",
        "volume24h": "24h volume at snapshot",
        "buysolqty": "SOL buys at snapshot",
        "occurrencecount": "Occurrences at snapshot",
        "percentilerankpeats": "Occurrence ranking at snapshot",
        "percentileranksol": "SOL buys ranking at snapshot",
        "dexstatus": "Trading status at snapshot",
        "change1hpct": "1h price change at snapshot",
        "createdat": "When record was created"
    
    }
}

class VolumeHandler(BaseDBHandler):
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self.schema = SCHEMA_DOCS
        self._createTables()
        
    def _createTables(self):
        """Creates all necessary tables for the system"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()
            
            # 1. Base Token Information
            if config.DB_TYPE == 'postgres':
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volumetokeninfo (
                        id SERIAL PRIMARY KEY,  -- Internal unique ID
                        tokenid TEXT NOT NULL UNIQUE,          -- Token's contract address
                        name TEXT NOT NULL,                    -- Trading symbol (e.g., "ROME")
                        tokenname TEXT NOT NULL,               -- Full name ("REPUBLIC OF MEME")
                        chain TEXT NOT NULL,                   -- Blockchain (e.g., "SOL")
                        tokendecimals INTEGER,                 -- Token decimal places
                        circulatingsupply TEXT,                -- Available supply
                        tokenage TEXT,                         -- Time since launch
                        twitterlink TEXT,                      -- Social media links
                        telegramlink TEXT,                     -- for due diligence
                        websitelink TEXT,                      -- and research
                        firstseenat TIMESTAMP,                 -- When bot first detected
                        lastupdatedat TIMESTAMP,               -- Last data update
                        count INTEGER DEFAULT 1                -- Count of updates
                    )
                ''')

                # 2. Token Current State
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volumetokenstates (
                        id SERIAL PRIMARY KEY,
                        tokenid TEXT NOT NULL UNIQUE,          -- Links to volumetokeninfo
                        price DECIMAL NOT NULL,                -- Current price
                        marketcap DECIMAL NOT NULL,            -- Total value
                        liquidity DECIMAL NOT NULL,            -- Available trading liquidity
                        volume24h DECIMAL NOT NULL,            -- 24hr trading volume
                        buysolqty INTEGER NOT NULL,            -- SOL buy pressure
                        occurrencecount INTEGER NOT NULL,      -- Times seen by bot
                        percentilerankpeats DECIMAL,           -- Ranking by occurrences
                        percentileranksol DECIMAL,             -- Ranking by SOL buys
                        dexstatus INTEGER NOT NULL,            -- Trading status
                        change1hpct DECIMAL NOT NULL,          -- 1hr price change
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When record was created
                        lastupdatedat TIMESTAMP,               -- Last update time
                        FOREIGN KEY(tokenid) REFERENCES volumetokeninfo(tokenid)
                    )
                ''')

                # 3. Token History
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volumetokenhistory (
                        id SERIAL PRIMARY KEY,
                        tokenid TEXT NOT NULL,
                        snapshotat TIMESTAMP NOT NULL,
                        price DECIMAL NOT NULL,
                        marketcap DECIMAL NOT NULL,
                        liquidity DECIMAL NOT NULL,
                        volume24h DECIMAL NOT NULL,
                        buysolqty INTEGER NOT NULL,
                        occurrencecount INTEGER NOT NULL,
                        percentilerankpeats DECIMAL,
                        percentileranksol DECIMAL,
                        dexstatus INTEGER NOT NULL,
                        change1hpct DECIMAL NOT NULL,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(tokenid) REFERENCES volumetokeninfo(tokenid)
                    )
                ''')
            else:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volumetokeninfo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Internal unique ID
                        tokenid TEXT NOT NULL UNIQUE,          -- Token's contract address
                        name TEXT NOT NULL,                    -- Trading symbol (e.g., "ROME")
                        tokenname TEXT NOT NULL,               -- Full name ("REPUBLIC OF MEME")
                        chain TEXT NOT NULL,                   -- Blockchain (e.g., "SOL")
                        tokendecimals INTEGER,                 -- Token decimal places
                        circulatingsupply TEXT,                -- Available supply
                        tokenage TEXT,                         -- Time since launch
                        twitterlink TEXT,                      -- Social media links
                        telegramlink TEXT,                     -- for due diligence
                        websitelink TEXT,                      -- and research
                        firstseenat TIMESTAMP,                 -- When bot first detected
                        lastupdatedat TIMESTAMP,               -- Last data update
                        count INTEGER DEFAULT 1                -- Count of updates
                    )
                ''')

                # 2. Token Current State
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volumetokenstates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tokenid TEXT NOT NULL UNIQUE,          -- Links to volumetokeninfo
                        price DECIMAL NOT NULL,                -- Current price
                        marketcap DECIMAL NOT NULL,            -- Total value
                        liquidity DECIMAL NOT NULL,            -- Available trading liquidity
                        volume24h DECIMAL NOT NULL,            -- 24hr trading volume
                        buysolqty INTEGER NOT NULL,            -- SOL buy pressure
                        occurrencecount INTEGER NOT NULL,      -- Times seen by bot
                        percentilerankpeats DECIMAL,           -- Ranking by occurrences
                        percentileranksol DECIMAL,             -- Ranking by SOL buys
                        dexstatus INTEGER NOT NULL,            -- Trading status
                        change1hpct DECIMAL NOT NULL,          -- 1hr price change
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When record was created
                        lastupdatedat TIMESTAMP,               -- Last update time
                        FOREIGN KEY(tokenid) REFERENCES volumetokeninfo(tokenid)
                    )
                ''')

                # 3. Token History
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS volumetokenhistory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tokenid TEXT NOT NULL,
                        snapshotat TIMESTAMP NOT NULL,
                        price DECIMAL NOT NULL,
                        marketcap DECIMAL NOT NULL,
                        liquidity DECIMAL NOT NULL,
                        volume24h DECIMAL NOT NULL,
                        buysolqty INTEGER NOT NULL,
                        occurrencecount INTEGER NOT NULL,
                        percentilerankpeats DECIMAL,
                        percentileranksol DECIMAL,
                        dexstatus INTEGER NOT NULL,
                        change1hpct DECIMAL NOT NULL,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(tokenid) REFERENCES volumetokeninfo(tokenid)
                    )
                ''')

            # Create indices for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_volumetokeninfo_tokenid ON volumetokeninfo(tokenid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_volumetokenstates_tokenid ON volumetokenstates(tokenid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_volumetokenhistory_tokenid ON volumetokenhistory(tokenid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_volumetokenhistory_snapshot ON volumetokenhistory(snapshotat)')
            
    def resetTables(self):
        """Drops and recreates all tables - Use with caution!"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('DROP TABLE IF EXISTS position_exits')
            cursor.execute('DROP TABLE IF EXISTS positionupdates')
            cursor.execute('DROP TABLE IF EXISTS tradesimulations')
            cursor.execute('DROP TABLE IF EXISTS strategyconditions')
            cursor.execute('DROP TABLE IF EXISTS strategies')
            cursor.execute('DROP TABLE IF EXISTS volumetokenhistory')
            cursor.execute('DROP TABLE IF EXISTS volumetokenstates')
            cursor.execute('DROP TABLE IF EXISTS volumetokeninfo')
        self._createTables()

    def checkTables(self):
        """Checks if all required tables exist"""
        config = get_config()
        requiredTables = [
            'volumetokeninfo', 'volumetokenstates', 'volumetokenhistory', 
            'strategies', 'strategyconditions', 
            'tradesimulations', 'positionupdates', 'position_exits'
        ]
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                
            existingTables = [row['table_name' if config.DB_TYPE == 'postgres' else 'name'] for row in cursor.fetchall()]
            
            missingTables = [table for table in requiredTables if table not in existingTables]
            
            if missingTables:
                raise Exception(f"Missing tables: {', '.join(missingTables)}")
            return True

    def getTableDocumentation(self, tableName: str) -> dict:
        """Get documentation for a specific table"""
        return self.schema.get(tableName, {})

    def getColumnDescription(self, tableName: str, columnName: str) -> str:
        """Get description for a specific column"""
        tableSchema = self.schema.get(tableName, {})
        return tableSchema.get(columnName, "No description available")

    def getExistingTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get current token state if exists"""
        config = get_config()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text('''
                    SELECT * FROM volumetokenstates 
                    WHERE tokenid = %s
                '''), (tokenId,))
            else:
                cursor.execute('''
                    SELECT * FROM volumetokenstates 
                    WHERE tokenid = ?
                ''', (tokenId,))
            return cursor.fetchone()

    def moveToHistory(self, tokenState: Dict) -> None:
        """Move current state to history before updating"""
        config = get_config()
        currentTime = datetime.now()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text('''
                    INSERT INTO volumetokenhistory (
                        tokenid, snapshotat, price, marketcap, liquidity,
                        volume24h, buysolqty, occurrencecount,
                        percentilerankpeats, percentileranksol,
                        dexstatus, change1hpct, createdat
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                '''), (
                    tokenState['tokenid'],
                    tokenState['lastupdatedat'],  # Use the last update time as snapshot
                    tokenState['price'],
                    tokenState['marketcap'],
                    tokenState['liquidity'],
                    tokenState['volume24h'],
                    tokenState['buysolqty'],
                    tokenState['occurrencecount'],
                    tokenState['percentilerankpeats'],
                    tokenState['percentileranksol'],
                    tokenState['dexstatus'],
                    tokenState['change1hpct'],
                    currentTime  # Add createdat value
                ))
            else:
                cursor.execute('''
                    INSERT INTO volumetokenhistory (
                        tokenid, snapshotat, price, marketcap, liquidity,
                        volume24h, buysolqty, occurrencecount,
                        percentilerankpeats, percentileranksol,
                        dexstatus, change1hpct, createdat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tokenState['tokenid'],
                    tokenState['lastupdatedat'],  # Use the last update time as snapshot
                    tokenState['price'],
                    tokenState['marketcap'],
                    tokenState['liquidity'],
                    tokenState['volume24h'],
                    tokenState['buysolqty'],
                    tokenState['occurrencecount'],
                    tokenState['percentilerankpeats'],
                    tokenState['percentileranksol'],
                    tokenState['dexstatus'],
                    tokenState['change1hpct'],
                    currentTime  # Add createdat value
                ))

    def insertTokenData(self, token: VolumeToken) -> None:
        """
        Insert or update token data:
        1. New token: Add to info and state tables
        2. Existing token: Archive current state, update state, increment count
        
        Args:
            token: VolumeToken object to persist
        """
        try:
            with self.conn_manager.transaction() as cursor:
                self._handleTokenData(cursor, token)
        except Exception as e:
            logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
            raise

    def _handleTokenData(self, cursor, token: VolumeToken) -> None:
        """Handle token data insertion or update"""
        config = get_config()
        
        # Check token existence and get current state in one query
        if config.DB_TYPE == 'postgres':
            cursor.execute(text('''
                SELECT 
                    i.id as info_exists,
                    s.id as state_exists,
                    s.*
                FROM volumetokeninfo i
                LEFT JOIN volumetokenstates s ON i.tokenid = s.tokenid
                WHERE i.tokenid = %s
            '''), (token.tokenid,))
        else:
            cursor.execute('''
                SELECT 
                    i.id as info_exists,
                    s.id as state_exists,
                    s.*
                FROM volumetokeninfo i
                LEFT JOIN volumetokenstates s ON i.tokenid = s.tokenid
                WHERE i.tokenid = ?
            ''', (token.tokenid,))
        
        result = cursor.fetchone()
        
        if not result:
            # New token - insert both records
            self._insertNewRecords(cursor, token)
        else:
            # Existing token - archive and update
            if not result['state_exists']:
                logger.error(f"Inconsistent state: Token {token.tokenid} exists in info but not in state table")
                return
            
            self._updateExistingRecords(cursor, token, result)

    def _insertNewRecords(self, cursor, token: VolumeToken) -> None:
        """Insert new token records in both tables"""
        config = get_config()
        currentTime = datetime.now()
        
        # Insert info record
        if config.DB_TYPE == 'postgres':
            cursor.execute(text('''
                INSERT INTO volumetokeninfo (
                    tokenid, name, tokenname, chain, tokendecimals,
                    circulatingsupply, tokenage, twitterlink, telegramlink,
                    websitelink, firstseenat, lastupdatedat, count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            '''), (
                token.tokenid, token.name, token.tokenname, token.chain,
                token.tokendecimals, token.circulatingsupply, token.tokenage,
                token.twitterlink, token.telegramlink, token.websitelink,
                currentTime, currentTime
            ))
            
            # Insert state record
            cursor.execute(text('''
                INSERT INTO volumetokenstates (
                    tokenid, price, marketcap, liquidity, volume24h,
                    buysolqty, occurrencecount, percentilerankpeats,
                    percentileranksol, dexstatus, change1hpct,
                    createdat, lastupdatedat
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''), (
                token.tokenid, str(token.price), str(token.marketcap),
                str(token.liquidity), str(token.volume24h), token.buysolqty,
                token.occurrencecount, token.percentilerankpeats,
                token.percentileranksol, token.dexstatus,
                str(token.change1hpct), currentTime, currentTime
            ))
        else:
            cursor.execute('''
                INSERT INTO volumetokeninfo (
                    tokenid, name, tokenname, chain, tokendecimals,
                    circulatingsupply, tokenage, twitterlink, telegramlink,
                    websitelink, firstseenat, lastupdatedat, count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (
                token.tokenid, token.name, token.tokenname, token.chain,
                token.tokendecimals, token.circulatingsupply, token.tokenage,
                token.twitterlink, token.telegramlink, token.websitelink,
                currentTime, currentTime
            ))
            
            # Insert state record
            cursor.execute('''
                INSERT INTO volumetokenstates (
                    tokenid, price, marketcap, liquidity, volume24h,
                    buysolqty, occurrencecount, percentilerankpeats,
                    percentileranksol, dexstatus, change1hpct,
                    createdat, lastupdatedat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token.tokenid, str(token.price), str(token.marketcap),
                str(token.liquidity), str(token.volume24h), token.buysolqty,
                token.occurrencecount, token.percentilerankpeats,
                token.percentileranksol, token.dexstatus,
                str(token.change1hpct), currentTime, currentTime
            ))
        
        logger.info(f"Inserted new token {token.tokenid}")

    def _updateExistingRecords(self, cursor, token: VolumeToken, currentState: Dict) -> None:
        """
        Archive current state and update records ONLY if:
        1. The token was seen within the last 10 minutes (timeago ≤ 10 minutes), AND
        2. Key metrics have changed
        
        If the token was seen more than 10 minutes ago, skip the update regardless of metric changes.
        
        Key metrics monitored for changes:
        - buysolqty: Number of SOL buy transactions
        - occurrencecount: Number of times token detected
        - percentilerankpeats: Ranking based on occurrences
        - percentileranksol: Ranking based on SOL buys
        """
        config = get_config()
        currentTime = datetime.now(pytz.UTC)
        
        # PRIMARY CONDITION: Check if token was seen within the last 10 minutes using timeago field
        if token.timeago is not None:
            # Ensure timeago is timezone-aware (UTC)
            tokenTimeago = token.timeago
            if tokenTimeago.tzinfo is None:
                tokenTimeago = pytz.UTC.localize(tokenTimeago)
            
            timeDifference = (currentTime - tokenTimeago).total_seconds() / 60  # Convert to minutes
            
            if timeDifference > 20:
                logger.info(f"Token {token.tokenid} was seen {timeDifference:.2f} minutes ago (UTC), outside 10-minute threshold, skipping update")
                return  # Skip update entirely if token was seen more than 10 minutes ago
                
            logger.info(f"Token {token.tokenid} was seen {timeDifference:.2f} minutes ago (UTC), within 10-minute threshold, checking for changes")
        else:
            # If timeago is None, skip update
            logger.info(f"Token {token.tokenid} has no timeago value, skipping update")
            return
        
        # SECONDARY CONDITION: Check if any metrics have changed
        shouldUpdate = False
        metricsToCompare = [
            ('buysolqty', token.buysolqty, currentState['buysolqty']),
            ('occurrencecount', token.occurrencecount, currentState['occurrencecount']),
            ('percentilerankpeats', token.percentilerankpeats, currentState['percentilerankpeats']),
            ('percentileranksol', token.percentileranksol, currentState['percentileranksol'])
        ]
        
        # Compare metrics and log changes
        changedMetrics = []
        for metricName, newValue, oldValue in metricsToCompare:
            if newValue != oldValue:
                shouldUpdate = True
                changedMetrics.append(f"{metricName}: {oldValue} -> {newValue}")
        
        if not shouldUpdate:
            logger.info(f"No changes detected for token {token.tokenid}, skipping update")
            return
            
        logger.info(f"Changes detected for token {token.tokenid}: {', '.join(changedMetrics)}")
        
        # 1. Archive current state since we're going to update
        if config.DB_TYPE == 'postgres':
            cursor.execute(text('''
                INSERT INTO volumetokenhistory (
                    tokenid, snapshotat, price, marketcap, liquidity,
                    volume24h, buysolqty, occurrencecount, percentilerankpeats,
                    percentileranksol, dexstatus, change1hpct, createdat
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''), (
                currentState['tokenid'], currentState['lastupdatedat'],
                currentState['price'], currentState['marketcap'],
                currentState['liquidity'], currentState['volume24h'],
                currentState['buysolqty'], currentState['occurrencecount'],
                currentState['percentilerankpeats'], currentState['percentileranksol'],
                currentState['dexstatus'], currentState['change1hpct'], currentTime
            ))
            
            # 2. Update state table
            cursor.execute(text('''
                UPDATE volumetokenstates SET
                    price = %s,
                    marketcap = %s,
                    liquidity = %s,
                    volume24h = %s,
                    buysolqty = %s,
                    occurrencecount = %s,
                    percentilerankpeats = %s,
                    percentileranksol = %s,
                    dexstatus = %s,
                    change1hpct = %s,
                    lastupdatedat = %s
                WHERE tokenid = %s
            '''), (
                str(token.price), str(token.marketcap), str(token.liquidity),
                str(token.volume24h), token.buysolqty, token.occurrencecount,
                token.percentilerankpeats, token.percentileranksol,
                token.dexstatus, str(token.change1hpct), currentTime,
                token.tokenid
            ))
            
            # 3. Update info table
            cursor.execute(text('''
                UPDATE volumetokeninfo SET
                    count = count + 1,
                    lastupdatedat = %s
                WHERE tokenid = %s
            '''), (currentTime, token.tokenid))
        else:
            cursor.execute('''
                INSERT INTO volumetokenhistory (
                    tokenid, snapshotat, price, marketcap, liquidity,
                    volume24h, buysolqty, occurrencecount, percentilerankpeats,
                    percentileranksol, dexstatus, change1hpct, createdat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                currentState['tokenid'], currentState['lastupdatedat'],
                currentState['price'], currentState['marketcap'],
                currentState['liquidity'], currentState['volume24h'],
                currentState['buysolqty'], currentState['occurrencecount'],
                currentState['percentilerankpeats'], currentState['percentileranksol'],
                currentState['dexstatus'], currentState['change1hpct'], currentTime
            ))
            
            # 2. Update state table
            cursor.execute('''
                UPDATE volumetokenstates SET
                    price = ?,
                    marketcap = ?,
                    liquidity = ?,
                    volume24h = ?,
                    buysolqty = ?,
                    occurrencecount = ?,
                    percentilerankpeats = ?,
                    percentileranksol = ?,
                    dexstatus = ?,
                    change1hpct = ?,
                    lastupdatedat = ?
                WHERE tokenid = ?
            ''', (
                str(token.price), str(token.marketcap), str(token.liquidity),
                str(token.volume24h), token.buysolqty, token.occurrencecount,
                token.percentilerankpeats, token.percentileranksol,
                token.dexstatus, str(token.change1hpct), currentTime,
                token.tokenid
            ))
            
            # 3. Update info table
            cursor.execute('''
                UPDATE volumetokeninfo SET
                    count = count + 1,
                    lastupdatedat = ?
                WHERE tokenid = ?
            ''', (currentTime, token.tokenid))

    def getTokenHistory(self, tokenId: str, startTime: datetime, endTime: datetime) -> List[Dict]:
        """Get token history for backtesting"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                SELECT * FROM volumetokenhistory 
                WHERE tokenid = ? AND snapshotat BETWEEN ? AND ?
                ORDER BY snapshotat ASC
            ''', (tokenId, startTime, endTime))
            return cursor.fetchall()

    def getTokenInfo(self, tokenId: str) -> Optional[Dict]:
        """Get token basic information"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('SELECT * FROM volumetokeninfo WHERE tokenid = ?', (tokenId,))
            return cursor.fetchone()

    def getTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get token current state"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('SELECT * FROM volumetokenstates WHERE tokenid = ?', (tokenId,))
            return cursor.fetchone()

    def insertVolumeSignal(self, data: Dict) -> bool:
        """Insert or update volume signal data"""
        try:
            with self.conn_manager.transaction() as cursor:
                # Check if token exists
                existingSignal = self.getVolumeSignal(data['tokenid'])
                currentTime = datetime.now()
                
                if existingSignal:
                    # Move current state to history
                    self.moveToHistory(existingSignal)
                    
                    # Update existing record
                    cursor.execute('''
                        UPDATE volumetokenstates 
                        SET price = ?,
                            marketcap = ?,
                            liquidity = ?,
                            volume24h = ?,
                            buysolqty = ?,
                            occurrencecount = ?,
                            percentilerankpeats = ?,
                            percentileranksol = ?,
                            dexstatus = ?,
                            change1hpct = ?,
                            lastupdatedat = ?
                        WHERE tokenid = ?
                    ''', (
                        str(data['price']),
                        str(data['marketcap']),
                        str(data['liquidity']),
                        str(data['volume24h']),
                        data['buysolqty'],
                        data['occurrencecount'],
                        data['percentilerankpeats'],
                        data['percentileranksol'],
                        data['dexstatus'],
                        str(data['change1h']),
                        currentTime,
                        data['tokenid']
                    ))
                else:
                    # Insert new record with createdat
                    cursor.execute('''
                        INSERT INTO volumetokenstates (
                            tokenid, price, marketcap, liquidity, volume24h,
                            buysolqty, occurrencecount, percentilerankpeats,
                            percentileranksol, dexstatus, change1hpct, createdat, lastupdatedat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        data['tokenid'],
                        str(data['price']),
                        str(data['marketcap']),
                        str(data['liquidity']),
                        str(data['volume24h']),
                        data['buysolqty'],
                        data['occurrencecount'],
                        data['percentilerankpeats'],
                        data['percentileranksol'],
                        data['dexstatus'],
                        str(data['change1h']),
                        currentTime,  # createdat
                        currentTime   # lastupdatedat
                    ))
                return True
        except Exception as e:
            logger.error(f"Failed to insert volume signal for {data['tokenid']}: {str(e)}")
            return False

    def moveToHistory(self, data: Dict) -> None:
        """Move current state to history before updating"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    INSERT INTO volumetokenhistory (
                        tokenid, price, marketcap, liquidity, volume24h,
                        buysolqty, occurrencecount, percentilerankpeats,
                        percentileranksol, dexstatus, change1hpct, snapshotat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data['tokenid'],
                    data['price'],
                    data['marketcap'],
                    data['liquidity'],
                    data['volume24h'],
                    data['buysolqty'],
                    data['occurrencecount'],
                    data['percentilerankpeats'],
                    data['percentileranksol'],
                    data['dexstatus'],
                    data['change1hpct'],
                    data['lastupdatedat']
                ))
        except Exception as e:
            logger.error(f"Failed to move volume data to history for {data['tokenid']}: {str(e)}")
            raise

    def _insertNewTokenInfo(self, cursor, token: VolumeToken) -> None:
        """Insert new token info with initial count of 1"""
        cursor.execute('''
            INSERT INTO volumetokeninfo (
                tokenid, name, tokenname, chain, tokendecimals,
                circulatingsupply, tokenage, twitterlink, telegramlink,
                websitelink, firstseenat, lastupdatedat, count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            token.tokenid,
            token.name,
            token.tokenname,
            token.chain,
            token.tokendecimals,
            token.circulatingsupply,
            token.tokenage,
            token.twitterlink,
            token.telegramlink,
            token.websitelink,
            datetime.now(),  # firstseenat
            datetime.now()   # lastupdatedat
        ))

    def _incrementTokenInfoCount(self, cursor, tokenId: str) -> None:
        """Increment count and update timestamp in token info"""
        cursor.execute('''
            UPDATE volumetokeninfo SET
                count = count + 1,
                lastupdatedat = CURRENT_TIMESTAMP
            WHERE tokenid = ?
        ''', (tokenId,))

    