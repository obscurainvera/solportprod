from config.Config import get_config
from database.smartmoneywallets.WalletPNLStatusEnum import SmartWalletPnlStatus
from database.operations.BaseDBHandler import BaseDBHandler
from typing import Dict, Optional, List, Any
from datetime import datetime
from logs.logger import get_logger
from database.operations.schema import SmartMoneyWallet
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
import json
from sqlalchemy import text
import pytz

logger = get_logger(__name__)

class SmartMoneyWalletsHandler(BaseDBHandler):
    """
    Handler for smart money wallets data.
    Manages smart money wallets data.
    """
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._create_tables()

    def _create_tables(self):
        """Create smartmoneywallets table if it doesn't exist"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()
            
            if config.DB_TYPE == 'postgres':
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS smartmoneywallets (
                        id SERIAL PRIMARY KEY,
                        walletaddress TEXT NOT NULL UNIQUE,
                        walletname TEXT NOT NULL,
                        totalinvested DECIMAL,
                        totalwithdrew DECIMAL,
                        pnl DECIMAL,
                        pnlpercentage DECIMAL,
                        winrate DECIMAL,
                        wincount INTEGER,
                        losscount INTEGER,
                        totaldeals INTEGER,
                        verified INTEGER,
                        chain TEXT,
                        status INTEGER DEFAULT 1,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        issmartmoney INTEGER DEFAULT 1
                    )
                '''))
            else:
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS smartmoneywallets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        walletaddress TEXT NOT NULL UNIQUE,
                        walletname TEXT NOT NULL,
                        totalinvested DECIMAL,
                        totalwithdrew DECIMAL,
                        pnl DECIMAL,
                        pnlpercentage DECIMAL,
                        winrate DECIMAL,
                        wincount INTEGER,
                        losscount INTEGER,
                        totaldeals INTEGER,
                        verified INTEGER,
                        chain TEXT,
                        status INTEGER DEFAULT 1,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        issmartmoney INTEGER DEFAULT 1
                    )
                '''))

    def insertSmartMoneyWallet(self, wallet: SmartMoneyWallet, cursor: Optional[Any] = None) -> Optional[int]:
        """Insert a smart money wallet"""
        try:
            config = get_config()
            current_time = datetime.now()
            
            if config.DB_TYPE == 'postgres':
                query = """
                    INSERT INTO smartmoneywallets (
                        walletaddress, walletname, totalinvested, totalwithdrew,
                        pnl, pnlpercentage, winrate, wincount, losscount,
                        totaldeals, verified, chain, status, createdat, updatedat, issmartmoney
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (walletaddress) DO UPDATE SET
                        walletname = EXCLUDED.walletname,
                        updatedat = EXCLUDED.updatedat
                    RETURNING id
                """
            else:
                query = """
                    INSERT INTO smartmoneywallets (
                        walletaddress, walletname, totalinvested, totalwithdrew,
                        pnl, pnlpercentage, winrate, wincount, losscount,
                        totaldeals, verified, chain, status, createdat, updatedat, issmartmoney
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(walletaddress) DO UPDATE SET
                        walletname = excluded.walletname,
                        updatedat = excluded.updatedat
                """
            
            params = (
                wallet.walletaddress,
                wallet.walletname,
                wallet.totalinvested,
                wallet.totalwithdrew,
                wallet.pnl,
                wallet.pnlpercentage,
                wallet.winrate,
                wallet.wincount,
                wallet.losscount,
                wallet.totaldeals,
                wallet.verified,
                wallet.chain,
                wallet.status,
                current_time,
                current_time,
                wallet.issmartmoney
            )
            
            if cursor:
                if config.DB_TYPE == 'postgres':
                    result = cursor.execute(text(query), params)
                    row = result.fetchone()
                    return row[0] if row else None
                else:
                    cursor.execute(query, params)
                    return cursor.lastrowid
            else:
                with self.conn_manager.transaction() as cur:
                    if config.DB_TYPE == 'postgres':
                        result = cur.execute(text(query), params)
                        row = result.fetchone()
                        return row[0] if row else None
                    else:
                        cur.execute(query, params)
                        return cur.lastrowid
                
        except Exception as e:
            logger.error(f"Error inserting smart money wallet: {str(e)}")
            return None

    def updateSmartMoneyWallet(self, wallet: SmartMoneyWallet, cursor: Optional[Any] = None) -> bool:
        """Update a smart money wallet"""
        try:
            config = get_config()
            current_time = datetime.now()
            
            if config.DB_TYPE == 'postgres':
                query = """
                    UPDATE smartmoneywallets SET
                        walletname = %s,
                        totalinvested = %s,
                        totalwithdrew = %s,
                        pnl = %s,
                        pnlpercentage = %s,
                        winrate = %s,
                        wincount = %s,
                        losscount = %s,
                        totaldeals = %s,
                        verified = %s,
                        chain = %s,
                        status = %s,
                        updatedat = %s,
                        issmartmoney = %s
                    WHERE walletaddress = %s
                """
            else:
                query = """
                    UPDATE smartmoneywallets SET
                        walletname = ?,
                        totalinvested = ?,
                        totalwithdrew = ?,
                        pnl = ?,
                        pnlpercentage = ?,
                        winrate = ?,
                        wincount = ?,
                        losscount = ?,
                        totaldeals = ?,
                        verified = ?,
                        chain = ?,
                        status = ?,
                        updatedat = ?,
                        issmartmoney = ?
                    WHERE walletaddress = ?
                """
            
            params = (
                wallet.walletname,
                wallet.totalinvested,
                wallet.totalwithdrew,
                wallet.pnl,
                wallet.pnlpercentage,
                wallet.winrate,
                wallet.wincount,
                wallet.losscount,
                wallet.totaldeals,
                wallet.verified,
                wallet.chain,
                wallet.status,
                current_time,
                wallet.issmartmoney,
                wallet.walletaddress
            )
            
            if cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text(query), params)
                else:
                    cursor.execute(query, params)
                return cursor.rowcount > 0
            else:
                with self.conn_manager.transaction() as cur:
                    if config.DB_TYPE == 'postgres':
                        cur.execute(text(query), params)
                    else:
                        cur.execute(query, params)
                    return cur.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating smart money wallet: {str(e)}")
            return False

    def getSmartMoneyWalletByAddress(self, wallet_address: str) -> Optional[Dict]:
        """Get a smart money wallet by address"""
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT * FROM smartmoneywallets
                        WHERE walletaddress = %s
                    """), (wallet_address,))
                else:
                    cursor.execute("""
                        SELECT * FROM smartmoneywallets
                        WHERE walletaddress = ?
                    """, (wallet_address,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting smart money wallet: {str(e)}")
            return None

    def getAllSmartMoneyWallets(self, include_inactive: bool = False) -> List[Dict]:
        """Get all smart money wallets"""
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if include_inactive:
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            SELECT * FROM smartmoneywallets
                            ORDER BY pnl DESC
                        """))
                    else:
                        cursor.execute("""
                            SELECT * FROM smartmoneywallets
                            ORDER BY pnl DESC
                        """)
                else:
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            SELECT * FROM smartmoneywallets
                            WHERE status = 1
                            ORDER BY pnl DESC
                        """))
                    else:
                        cursor.execute("""
                            SELECT * FROM smartmoneywallets
                            WHERE status = 1
                            ORDER BY pnl DESC
                        """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting all smart money wallets: {str(e)}")
            return []

    def getAllHighPnlSmartMoneyWallets(self) -> List[Dict]:
        """
        Get wallets with HIGH_PNL_SM status formatted for front-end
        
        Returns:
            List of dictionaries containing wallet data formatted for front-end
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT 
                        walletaddress,
                        profitandloss,
                        status
                    FROM smartmoneywallets
                    WHERE status = ?
                    ORDER BY CAST(profitandloss AS DECIMAL) DESC
                """, (SmartWalletPnlStatus.HIGH_PNL_SM.value,))
                rows = cursor.fetchall()
                
                wallets = []
                for row in rows:
                    wallet = {
                        "walletAddress": row[0],
                        "walletName": row[0],  # Using address as name
                        "profitAndLoss": row[1],
                        "status": row[2],
                        "statusDescription": SmartWalletPnlStatus.getDescription(row[2])
                    }
                    wallets.append(wallet)
                
                return wallets
        except Exception as e:
            logger.error(f"Failed to get high profit smart money wallets: {str(e)}")
            return [] 