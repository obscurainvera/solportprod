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
        "count": "Count of updates",
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
        "lastupdatedat": "Last state update timestamp",
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
        "createdat": "When record was created",
    },
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
        try:
            with self.conn_manager.transaction() as cursor:
                # 1. Base Token Information
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS volumetokeninfo (
                        id SERIAL PRIMARY KEY,
                        tokenid TEXT NOT NULL UNIQUE,
                        name TEXT NOT NULL,
                        tokenname TEXT NOT NULL,
                        chain TEXT NOT NULL,
                        tokendecimals INTEGER,
                        circulatingsupply TEXT,
                        tokenage TEXT,
                        twitterlink TEXT,
                        telegramlink TEXT,
                        websitelink TEXT,
                        firstseenat TIMESTAMP,
                        lastupdatedat TIMESTAMP,
                        count INTEGER DEFAULT 1
                    )
                """
                    )
                )

                # 2. Token Current State
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS volumetokenstates (
                        id SERIAL PRIMARY KEY,
                        tokenid TEXT NOT NULL UNIQUE,
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
                        lastupdatedat TIMESTAMP,
                        FOREIGN KEY(tokenid) REFERENCES volumetokeninfo(tokenid)
                    )
                """
                    )
                )

                # 3. Token History
                cursor.execute(
                    text(
                        """
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
                """
                    )
                )

            # Create indices in separate transactions
            self._createIndex(
                "idx_volumetokeninfo_tokenid", "volumetokeninfo", "tokenid"
            )
            self._createIndex(
                "idx_volumetokenstates_tokenid", "volumetokenstates", "tokenid"
            )
            self._createIndex(
                "idx_volumetokenhistory_tokenid", "volumetokenhistory", "tokenid"
            )
            self._createIndex(
                "idx_volumetokenhistory_snapshot", "volumetokenhistory", "snapshotat"
            )

        except Exception as e:
            logger.error(f"Error creating tables for VolumeHandler: {e}")

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

    def getExistingTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get current token state if exists"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text(
                    """
                SELECT * FROM volumetokenstates 
                WHERE tokenid = %s
            """
                ),
                (tokenId,),
            )
            return cursor.fetchone()

    def moveToHistory(self, tokenState: Dict) -> None:
        """Move current state to history before updating"""
        currentTime = datetime.now()
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text(
                    """
                INSERT INTO volumetokenhistory (
                    tokenid, snapshotat, price, marketcap, liquidity,
                    volume24h, buysolqty, occurrencecount,
                    percentilerankpeats, percentileranksol,
                    dexstatus, change1hpct, createdat
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
                ),
                (
                    tokenState["tokenid"],
                    tokenState["lastupdatedat"],
                    tokenState["price"],
                    tokenState["marketcap"],
                    tokenState["liquidity"],
                    tokenState["volume24h"],
                    tokenState["buysolqty"],
                    tokenState["occurrencecount"],
                    tokenState["percentilerankpeats"],
                    tokenState["percentileranksol"],
                    tokenState["dexstatus"],
                    tokenState["change1hpct"],
                    currentTime,
                ),
            )

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
        cursor.execute(
            text(
                """
            SELECT 
                i.id as info_exists,
                s.id as state_exists,
                s.*
            FROM volumetokeninfo i
            LEFT JOIN volumetokenstates s ON i.tokenid = s.tokenid
            WHERE i.tokenid = %s
        """
            ),
            (token.tokenid,),
        )

        result = cursor.fetchone()

        if not result:
            # New token - insert both records
            logger.info(
                    f"New token {token.name} entry"
                )
            self._insertNewRecords(cursor, token)
        else:
            # Existing token - archive and update
            if not result["state_exists"]:
                logger.info(
                    f"Inconsistent state: Token {token.tokenname} exists in info but not in state table"
                )
                return

            self._updateExistingRecords(cursor, token, result)

    def _insertNewRecords(self, cursor, token: VolumeToken) -> None:
        """Insert new token records in both tables"""
        currentTime = datetime.now()

        # Insert info record
        cursor.execute(
            text(
                """
            INSERT INTO volumetokeninfo (
                tokenid, name, tokenname, chain, tokendecimals,
                circulatingsupply, tokenage, twitterlink, telegramlink,
                websitelink, firstseenat, lastupdatedat, count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
            ),
            (
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
                currentTime,
                currentTime,
            ),
        )

        # Insert state record
        cursor.execute(
            text(
                """
            INSERT INTO volumetokenstates (
                tokenid, price, marketcap, liquidity, volume24h,
                buysolqty, occurrencecount, percentilerankpeats,
                percentileranksol, dexstatus, change1hpct,
                createdat, lastupdatedat
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
            ),
            (
                token.tokenid,
                str(token.price),
                str(token.marketcap),
                str(token.liquidity),
                str(token.volume24h),
                token.buysolqty,
                token.occurrencecount,
                token.percentilerankpeats,
                token.percentileranksol,
                token.dexstatus,
                str(token.change1hpct),
                currentTime,
                currentTime,
            ),
        )

        logger.info(f"Inserted new token {token.tokenname}")

    def _updateExistingRecords(self, cursor, token: VolumeToken, currentState: Dict) -> None:
        """
        Archive current state and update records ONLY if:
        1. The token was seen within the last 20 minutes (timeago ≤ 20 minutes), AND
        2. Key metrics have changed

        If the token was seen more than 20 minutes ago, skip the update regardless of metric changes.

        Key metrics monitored for changes:
        - buysolqty: Number of SOL buy transactions
        - occurrencecount: Number of times token detected
        - percentilerankpeats: Ranking based on occurrences
        - percentileranksol: Ranking based on SOL buys
        """
        currentTime = datetime.now(pytz.UTC)

        # PRIMARY CONDITION: Check if token was seen within the last 20 minutes using timeago field
        if hasattr(token, "timeago") and token.timeago is not None:
            # Ensure timeago is timezone-aware (UTC)
            tokenTimeago = token.timeago
            if tokenTimeago.tzinfo is None:
                tokenTimeago = pytz.UTC.localize(tokenTimeago)

            timeDifference = (
                currentTime - tokenTimeago
            ).total_seconds() / 60  # Convert to minutes

            if timeDifference > 20:
                logger.info(
                    f"Token {token.tokenname} was seen {timeDifference:.2f} minutes ago (UTC), outside 20-minute threshold, skipping update"
                )
                return  # Skip update entirely if token was seen more than 20 minutes ago

            logger.info(
                f"Token {token.tokenname} was seen {timeDifference:.2f} minutes ago (UTC), within 20-minute threshold, checking for changes"
            )
        else:
            # If timeago is None, skip update
            logger.info(f"Token {token.tokenname} has no timeago value, skipping update")
            return

        # SECONDARY CONDITION: Check if any metrics have changed
        shouldUpdate = False
        metricsToCompare = [
            ("buysolqty", token.buysolqty, currentState["buysolqty"]),
            ("occurrencecount", token.occurrencecount, currentState["occurrencecount"]),
            (
                "percentilerankpeats",
                token.percentilerankpeats,
                currentState["percentilerankpeats"],
            ),
            (
                "percentileranksol",
                token.percentileranksol,
                currentState["percentileranksol"],
            ),
        ]

        # Compare metrics and log changes
        changedMetrics = []
        for metricName, newValue, oldValue in metricsToCompare:
            if newValue != oldValue:
                shouldUpdate = True
                changedMetrics.append(f"{metricName}: {oldValue} -> {newValue}")

        if not shouldUpdate:
            logger.info(
                f"No changes detected for token {token.tokenid}, skipping update"
            )
            return

        logger.info(
            f"Changes detected for token {token.tokenid}: {', '.join(changedMetrics)}"
        )

        # 1. Archive current state since we're going to update
        cursor.execute(
            text(
                """
            INSERT INTO volumetokenhistory (
                tokenid, snapshotat, price, marketcap, liquidity,
                volume24h, buysolqty, occurrencecount, percentilerankpeats,
                percentileranksol, dexstatus, change1hpct, createdat
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
            ),
            (
                currentState["tokenid"],
                currentState["lastupdatedat"],
                currentState["price"],
                currentState["marketcap"],
                currentState["liquidity"],
                currentState["volume24h"],
                currentState["buysolqty"],
                currentState["occurrencecount"],
                currentState["percentilerankpeats"],
                currentState["percentileranksol"],
                currentState["dexstatus"],
                currentState["change1hpct"],
                currentTime,
            ),
        )
        
        logger.info(
            f"Updated history for token {token.tokenid}: {', '.join(changedMetrics)}")

        # 2. Update state table
        cursor.execute(
            text(
                """
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
        """
            ),
            (
                str(token.price),
                str(token.marketcap),
                str(token.liquidity),
                str(token.volume24h),
                token.buysolqty,
                token.occurrencecount,
                token.percentilerankpeats,
                token.percentileranksol,
                token.dexstatus,
                str(token.change1hpct),
                currentTime,
                token.tokenid,
            ),
        )
        
        logger.info(
            f"Updated state for token {token.tokenid}: {', '.join(changedMetrics)}")

        # 3. Update info table
        cursor.execute(
            text(
                """
            UPDATE volumetokeninfo SET
                count = count + 1,
                lastupdatedat = %s
            WHERE tokenid = %s
        """
            ),
            (currentTime, token.tokenid),
        )
        logger.info(
            f"Updated info for token {token.tokenid}: {', '.join(changedMetrics)}")

    def getTokenHistory(self, tokenId: str, startTime: datetime, endTime: datetime) -> List[Dict]:
        """Get token history for backtesting"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text(
                    """
                SELECT * FROM volumetokenhistory 
                WHERE tokenid = %s AND snapshotat BETWEEN %s AND %s
                ORDER BY snapshotat ASC
            """
                ),
                (tokenId, startTime, endTime),
            )
            return cursor.fetchall()

    def getTokenInfo(self, tokenId: str) -> Optional[Dict]:
        """Get token basic information"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text("SELECT * FROM volumetokeninfo WHERE tokenid = %s"), (tokenId,)
            )
            return cursor.fetchone()

    def getTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get token current state"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text("SELECT * FROM volumetokenstates WHERE tokenid = %s"), (tokenId,)
            )
            return cursor.fetchone()

    def insertVolumeSignal(self, data: Dict) -> bool:
        """Insert or update volume signal data"""
        try:
            with self.conn_manager.transaction() as cursor:
                # Check if token exists
                existingSignal = self.getExistingTokenState(data["tokenid"])
                currentTime = datetime.now()

                if existingSignal:
                    # Move current state to history
                    self.moveToHistory(existingSignal)

                    # Update existing record
                    cursor.execute(
                        text(
                            """
                        UPDATE volumetokenstates 
                        SET price = %s,
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
                    """
                        ),
                        (
                            str(data["price"]),
                            str(data["marketcap"]),
                            str(data["liquidity"]),
                            str(data["volume24h"]),
                            data["buysolqty"],
                            data["occurrencecount"],
                            data["percentilerankpeats"],
                            data["percentileranksol"],
                            data["dexstatus"],
                            str(data["change1hpct"]),
                            currentTime,
                            data["tokenid"],
                        ),
                    )
                else:
                    # Insert new record with createdat
                    cursor.execute(
                        text(
                            """
                        INSERT INTO volumetokenstates (
                            tokenid, price, marketcap, liquidity, volume24h,
                            buysolqty, occurrencecount, percentilerankpeats,
                            percentileranksol, dexstatus, change1hpct, createdat, lastupdatedat
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                        ),
                        (
                            data["tokenid"],
                            str(data["price"]),
                            str(data["marketcap"]),
                            str(data["liquidity"]),
                            str(data["volume24h"]),
                            data["buysolqty"],
                            data["occurrencecount"],
                            data["percentilerankpeats"],
                            data["percentileranksol"],
                            data["dexstatus"],
                            str(data["change1hpct"]),
                            currentTime,
                            currentTime,
                        ),
                    )
                return True
        except Exception as e:
            logger.error(
                f"Failed to insert volume signal for {data['tokenid']}: {str(e)}"
            )
            return False

    def _insertNewTokenInfo(self, cursor, token: VolumeToken) -> None:
        """Insert new token info with initial count of 1"""
        currentTime = datetime.now()
        cursor.execute(
            text(
                """
            INSERT INTO volumetokeninfo (
                tokenid, name, tokenname, chain, tokendecimals,
                circulatingsupply, tokenage, twitterlink, telegramlink,
                websitelink, firstseenat, lastupdatedat, count
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
        """
            ),
            (
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
                currentTime,
                currentTime,
            ),
        )

    def _incrementTokenInfoCount(self, cursor, tokenId: str) -> None:
        """Increment count and update timestamp in token info"""
        cursor.execute(
            text(
                """
            UPDATE volumetokeninfo SET
                count = count + 1,
                lastupdatedat = CURRENT_TIMESTAMP
            WHERE tokenid = %s
        """
            ),
            (tokenId,),
        )
