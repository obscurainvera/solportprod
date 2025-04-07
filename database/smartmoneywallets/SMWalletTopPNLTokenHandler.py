from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import Dict, List, Optional, Any
from datetime import datetime
from logs.logger import get_logger
from database.operations.schema import SMWalletTopPnlToken
from decimal import Decimal
from database.smartmoneywallets.TopTokenPNLStatusEnum import TokenStatus
from sqlalchemy import text

logger = get_logger(__name__)

class SMWalletTopPNLTokenHandler(BaseDBHandler):
    """
    Handler for top PNL token data for smart money wallets.
    Manages token performance data for high-performing wallets.
    """
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._create_tables()

    def _create_tables(self):
        """Create toppnltoken table if it doesn't exist"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()
            
            if config.DB_TYPE == 'postgres':
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS smwallettoppnltoken (
                        id SERIAL PRIMARY KEY,
                        walletaddress TEXT NOT NULL,
                        tokenid TEXT NOT NULL,
                        name TEXT NOT NULL,
                        amountinvested DECIMAL,
                        amounttakenout DECIMAL,
                        remainingcoins DECIMAL,
                        unprocessedpnl DECIMAL,
                        unprocessedroi DECIMAL,
                        transactionscount INTEGER DEFAULT 0,
                        createdtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        lastupdatedtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status INTEGER DEFAULT {TokenStatus.LOW_PNL_TOKEN.value},
                        UNIQUE(walletaddress, tokenid)
                    )
                ''')
            else:
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS smwallettoppnltoken (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        walletaddress TEXT NOT NULL,
                        tokenid TEXT NOT NULL,
                        name TEXT NOT NULL,
                        amountinvested DECIMAL,
                        amounttakenout DECIMAL,
                        remainingcoins DECIMAL,
                        unprocessedpnl DECIMAL,
                        unprocessedroi DECIMAL,
                        transactionscount INTEGER DEFAULT 0,
                        createdtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        lastupdatedtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status INTEGER DEFAULT {TokenStatus.LOW_PNL_TOKEN.value},
                        UNIQUE(walletaddress, tokenid)
                    )
                ''')

    def insertSMWalletToken(self, token_data: SMWalletTopPnlToken, cursor: Optional[Any] = None) -> bool:
        """
        Insert new top PNL token record with initial data
        
        Args:
            token_data: TopPnlToken object containing initial token data
            cursor: Optional database cursor for transaction management
        
        Returns:
            bool: Success status
        """
        try:
            config = get_config()
            
            # Determine status if not already set
            if not hasattr(token_data, 'status') or token_data.status is None:
                status = TokenStatus.getStatusFromPNL(float(token_data.unprocessedpnl))
                token_data.status = status.value

            if config.DB_TYPE == 'postgres':
                query = """
                    INSERT INTO smwallettoppnltoken (
                        walletaddress, tokenid, name, unprocessedpnl, 
                        unprocessedroi, status
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """
            else:
                query = """
                    INSERT INTO smwallettoppnltoken (
                        walletaddress, tokenid, name, unprocessedpnl, 
                        unprocessedroi, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                
            params = (
                token_data.walletaddress,
                token_data.tokenid,
                token_data.name,
                str(token_data.unprocessedpnl),
                str(token_data.unprocessedroi),
                token_data.status
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
            return True
        except Exception as e:
            logger.error(f"Failed to insert top PNL token: {str(e)}")
            return False

    def updateSMWalletToken(self, token_data: SMWalletTopPnlToken, cursor: Optional[Any] = None) -> bool:
        """
        Update existing top PNL token record
        
        Args:
            token_data: TopPnlToken object containing updated data
            cursor: Optional database cursor for transaction management
            
        Returns:
            bool: Success status
        """
        try:
            config = get_config()
            
            if config.DB_TYPE == 'postgres':
                query = """
                    UPDATE smwallettoppnltoken SET
                        name = %s,
                        unprocessedpnl = %s,
                        unprocessedroi = %s,
                        lastupdatedtime = CURRENT_TIMESTAMP
                    WHERE walletaddress = %s
                    AND tokenid = %s
                    AND status = 1
                """
            else:
                query = """
                    UPDATE smwallettoppnltoken SET
                        name = ?,
                        unprocessedpnl = ?,
                        unprocessedroi = ?,
                        lastupdatedtime = CURRENT_TIMESTAMP
                    WHERE walletaddress = ?
                    AND tokenid = ?
                    AND status = 1
                """
                
            params = (
                token_data.name,
                str(token_data.unprocessedpnl) if token_data.unprocessedpnl is not None else None,
                str(token_data.unprocessedroi) if token_data.unprocessedroi is not None else None,
                token_data.walletaddress,
                token_data.tokenid
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
            return True
        except Exception as e:
            logger.error(f"Failed to update top PNL token: {str(e)}")
            return False

    def updateSMWalletTokenInvestmentData(self, token_data: SMWalletTopPnlToken, cursor: Optional[Any] = None) -> bool:
        """
        Update investment-related data for an existing token
        
        Args:
            token_data: TopPnlToken object containing investment data
            cursor: Optional database cursor for transaction management
            
        Returns:
            bool: Success status
        """
        try:
            config = get_config()
            
            if config.DB_TYPE == 'postgres':
                query = """
                    UPDATE smwallettoppnltoken SET
                        amountinvested = %s,
                        amounttakenout = %s,
                        remainingcoins = %s,
                        lastupdatedtime = CURRENT_TIMESTAMP
                    WHERE walletaddress = %s
                    AND tokenid = %s
                    AND status = 1
                """
            else:
                query = """
                    UPDATE smwallettoppnltoken SET
                        amountinvested = ?,
                        amounttakenout = ?,
                        remainingcoins = ?,
                        lastupdatedtime = CURRENT_TIMESTAMP
                    WHERE walletaddress = ?
                    AND tokenid = ?
                    AND status = 1
                """
                
            params = (
                str(token_data.amountinvested) if token_data.amountinvested is not None else None,
                str(token_data.amounttakenout) if token_data.amounttakenout is not None else None,
                str(token_data.remainingcoins) if token_data.remainingcoins is not None else None,
                token_data.walletaddress,
                token_data.tokenid
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
            return True
        except Exception as e:
            logger.error(f"Failed to update token investment data: {str(e)}")
            return False


    def getAllWalletTokens(self, wallet_address: str) -> List[SMWalletTopPnlToken]:
        """
        Get all top PNL tokens for a specific wallet
        
        Args:
            wallet_address: Wallet address to query
            
        Returns:
            List[TopPnlToken]: List of top PNL tokens for the wallet
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT t.*, 
                               CASE 
                                   WHEN t.status = %s THEN %s
                                   ELSE %s
                               END as status_description
                        FROM smwallettoppnltoken t  
                        WHERE t.walletaddress = %s
                        ORDER BY t.unprocessedpnl DESC
                    """), (
                        TokenStatus.HIGH_PNL_TOKEN.value,
                        TokenStatus.HIGH_PNL_TOKEN.description,
                        TokenStatus.LOW_PNL_TOKEN.description,
                        wallet_address
                    ))
                else:
                    cursor.execute("""
                        SELECT t.*, 
                               CASE 
                                   WHEN t.status = ? THEN ?
                                   ELSE ?
                               END as status_description
                        FROM smwallettoppnltoken t  
                        WHERE t.walletaddress = ?
                        ORDER BY t.unprocessedpnl DESC
                    """, (
                        TokenStatus.HIGH_PNL_TOKEN.value,
                        TokenStatus.HIGH_PNL_TOKEN.description,
                        TokenStatus.LOW_PNL_TOKEN.description,
                        wallet_address
                    ))
                return [SMWalletTopPnlToken(**dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get wallet tokens: {str(e)}")
            return []

    def convertRowToObject(self, row: Any) -> Optional[SMWalletTopPnlToken]:
        """
        Maps a database row to SMWalletTopPnlToken object
        
        Args:
            row: Database row
            
        Returns:
            Optional[SMWalletTopPnlToken]: Mapped object or None if row is None
        """
        if not row:
            return None
        
        return SMWalletTopPnlToken(
            id=row['id'],
            walletaddress=row['walletaddress'],
            tokenid=row['tokenid'],
            name=row['name'],
            amountinvested=Decimal(str(row['amountinvested'])) if row['amountinvested'] else Decimal('0'),
            amounttakenout=Decimal(str(row['amounttakenout'])) if row['amounttakenout'] else Decimal('0'),
            remainingcoins=Decimal(str(row['remainingcoins'])) if row['remainingcoins'] else Decimal('0'),
            unprocessedpnl=Decimal(str(row['unprocessedpnl'])) if row['unprocessedpnl'] else Decimal('0'),
            unprocessedroi=Decimal(str(row['unprocessedroi'])) if row['unprocessedroi'] else Decimal('0'),
            transactionscount=row['transactionscount'],
            createdtime=row['createdtime'],
            lastupdatedtime=row['lastupdatedtime'],
            status=row['status']
        )

    def getSMWalletTopPNLToken(self, walletAddress: str, tokenId: str) -> Optional[SMWalletTopPnlToken]:
        """Get token data for a specific wallet and token"""
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text(
                        "SELECT * FROM smwallettoppnltoken WHERE walletaddress = %s AND tokenid = %s"
                    ), (walletAddress, tokenId))
                else:
                    cursor.execute(
                        "SELECT * FROM smwallettoppnltoken WHERE walletaddress = ? AND tokenid = ?",
                        (walletAddress, tokenId)
                    )
                row = cursor.fetchone()
                return self.convertRowToObject(row)
            
        except Exception as e:
            logger.error(f"Failed to get token data for wallet {walletAddress} and token {tokenId}: {str(e)}")
            return None

    def updateInvestementDataForTopPnlToken(self, walletAddress: str, tokenId: str, 
                           amountInvested: Decimal, amountTakenOut: Decimal, 
                           remainingCoins: Decimal, transactionsCount: int) -> bool:
        """Update investment amounts for a token"""
        try:
            config = get_config()
            current_time = datetime.now()
            
            logger.info(f"Updating investment data for {walletAddress} and token {tokenId}")
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        UPDATE smwallettoppnltoken 
                        SET amountinvested = %s,
                            amounttakenout = %s,
                            remainingcoins = %s,
                            transactionscount = %s,
                            lastupdatedtime = %s
                        WHERE walletaddress = %s 
                        AND tokenid = %s
                    """), (
                        str(amountInvested),
                        str(amountTakenOut),
                        str(remainingCoins),
                        transactionsCount,
                        current_time,
                        walletAddress,
                        tokenId
                    ))
                else:
                    cursor.execute("""
                        UPDATE smwallettoppnltoken 
                        SET amountinvested = ?,
                            amounttakenout = ?,
                            remainingcoins = ?,
                            transactionscount = ?,
                            lastupdatedtime = ?
                        WHERE walletaddress = ? 
                        AND tokenid = ?
                    """, (
                        str(amountInvested),
                        str(amountTakenOut),
                        str(remainingCoins),
                        transactionsCount,
                        current_time,
                        walletAddress,
                        tokenId
                    ))
                return True
        except Exception as e:
            logger.error(f"Failed to update token amounts: {str(e)}")
            return False

    def updateTokenStatus(self, token: SMWalletTopPnlToken, cursor: Optional[Any] = None) -> bool:
        """Update token status based on PNL"""
        try:
            config = get_config()
            status = TokenStatus.getStatusFromPNL(float(token.unprocessedpnl))
            
            if config.DB_TYPE == 'postgres':
                query = """
                    UPDATE smwallettoppnltoken 
                    SET status = %s,
                        lastupdatedtime = CURRENT_TIMESTAMP
                    WHERE walletaddress = %s 
                    AND tokenid = %s
                """
            else:
                query = """
                    UPDATE smwallettoppnltoken 
                    SET status = ?,
                        lastupdatedtime = CURRENT_TIMESTAMP
                    WHERE walletaddress = ? 
                    AND tokenid = ?
                """
                
            params = (status.value, token.walletaddress, token.tokenid)

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
            return True
        except Exception as e:
            logger.error(f"Failed to update token status: {str(e)}")
            return False

    def getAllTokensByStatus(self, status: TokenStatus) -> List[SMWalletTopPnlToken]:
        """Get all tokens with specific status"""
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        SELECT * FROM smwallettoppnltoken
                        WHERE status = %s
                        ORDER BY unprocessedpnl DESC
                    """), (status.value,))
                else:
                    cursor.execute("""
                        SELECT * FROM smwallettoppnltoken
                        WHERE status = ?
                        ORDER BY unprocessedpnl DESC
                    """, (status.value,))
                return [SMWalletTopPnlToken(**dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get tokens by status: {str(e)}")
            return []

    def getTransactionCount(self, walletAddress: str, tokenId: str) -> Optional[int]:
        """
        Get transaction count for a specific wallet and token pair
        
        Args:
            wallet_address: Address of the wallet
            token_id: ID of the token
            
        Returns:
            Optional[int]: Number of transactions or None if not found
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text('''
                        SELECT transactionscount 
                        FROM smwallettoppnltoken 
                        WHERE walletaddress = %s 
                        AND tokenid = %s
                    '''), (walletAddress, tokenId))
                else:
                    cursor.execute('''
                        SELECT transactionscount 
                        FROM smwallettoppnltoken 
                        WHERE walletaddress = ? 
                        AND tokenid = ?
                    ''', (walletAddress, tokenId))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Failed to get transaction count for wallet {walletAddress} and token {tokenId}: {str(e)}")
            return None

    def updateTransactionCount(self, walletAddress: str, tokenId: str, transactionsCount: int) -> bool:
        """
        Update only the transaction count for a specific wallet and token pair
        
        Args:
            walletAddress: Address of the wallet
            tokenId: ID of the token
            transactionsCount: New transaction count
            
        Returns:
            bool: Success status
        """
        try:
            config = get_config()
            current_time = datetime.now()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        UPDATE smwallettoppnltoken 
                        SET transactionscount = %s,
                            lastupdatedtime = %s
                        WHERE walletaddress = %s 
                        AND tokenid = %s
                    """), (transactionsCount, current_time, walletAddress, tokenId))
                else:
                    cursor.execute("""
                        UPDATE smwallettoppnltoken 
                        SET transactionscount = ?,
                            lastupdatedtime = ?
                        WHERE walletaddress = ? 
                        AND tokenid = ?
                    """, (transactionsCount, current_time, walletAddress, tokenId))
                
                # Check if any rows were affected
                rowsAffected = cursor.rowcount
                success = rowsAffected > 0
                
                if not success:
                    logger.warning(f"No rows updated for wallet {walletAddress} and token {tokenId}. Token may not exist or have incorrect status.")
                else:
                    logger.info(f"Updated transaction count to {transactionsCount} for wallet {walletAddress} and token {tokenId}")
                    
                return success
                
        except Exception as e:
            logger.error(f"Failed to update transaction count for wallet {walletAddress} and token {tokenId}: {str(e)}")
            return False

    def getTokensForWallet(self, walletAddress: str) -> List[SMWalletTopPnlToken]:
        """
        Get all tokens invested by a specific wallet
        
        Args:
            wallet_address: The wallet address to get tokens for
            
        Returns:
            List[SMWalletTopPnlToken]: List of tokens invested by the wallet
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    rows = cursor.execute(text("""
                        SELECT * FROM smwallettoppnltoken
                        WHERE walletaddress = %s and
                        transactionscount = %s and
                        tokenid != 'So11111111111111111111111111111111111111112'
                        ORDER BY unprocessedpnl DESC
                    """), (walletAddress, 0)).fetchall()
                else:
                    rows = cursor.execute("""
                        SELECT * FROM smwallettoppnltoken
                        WHERE walletaddress = ? and
                        transactionscount = ? and
                        tokenid != 'So11111111111111111111111111111111111111112'
                        ORDER BY unprocessedpnl DESC
                    """, (walletAddress, 0)).fetchall()
                
                tokens = []
                for row in rows:
                    token = self.convertRowToObject(row)
                    if token:
                        tokens.append(token)
                
                return tokens
                
        except Exception as e:
            logger.error(f"Failed to get tokens for wallet {walletAddress}: {str(e)}")
            return [] 