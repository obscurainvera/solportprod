from config.Config import get_config
"""
Takes all the transactions of a wallet and token and calculates 
the total invested, 
total taken out, 
and average entry price
"""
from typing import Dict, List, Optional
from decimal import Decimal
from logs.logger import get_logger
from database.operations.PortfolioDB import PortfolioDB
from services.SolscanServiceHandler import SolscanServiceHandler
from services.CieloServiceHandler import CieloServiceHandler
from database.operations.schema import InvestmentDetails

logger = get_logger(__name__)

class WalletsInvestedInvestmentDetailsAction:
    """Handles transaction analysis workflow"""
    
    # Add constant at class level
    MIN_SMART_HOLDING = Decimal('1000')  # Minimum smart holding threshold
    
    def __init__(self, db: PortfolioDB):
        """
        Initialize action with database instance
        
        Args:
            db: Database handler
        """
        self.db = db
        self.solscanService = SolscanServiceHandler(db)
        self.cieloService = CieloServiceHandler(db)

    def updateInvestmentData(self, cookie: str, walletAddress: str, tokenId: str, walletInvestedId: int, service: str = 'cielo') -> bool:

        try:
            # Get current transaction count from database
            dbTransactionsCount = self.db.walletsInvested.getTransactionsCountFromDB(walletInvestedId)
            
            # Get total transaction count from Solscan API (always use Solscan for count)
            apiTransactionsCount = self.solscanService.getTransactionCountFromAPI(
                cookie, 
                walletAddress, 
                tokenId
            )
            if not apiTransactionsCount:
                return False

            # Skip processing if no new transactions
            if dbTransactionsCount is not None and dbTransactionsCount == apiTransactionsCount:
                logger.info(f"No new transactions found for wallet: {walletAddress} and token: {tokenId}")
                return True

            # Update total transactions in database
            self.db.walletsInvested.updateTransactionsCountInDB(walletInvestedId, apiTransactionsCount)

            # Get transactions and calculate details based on selected service
            result: Optional[InvestmentDetails] = None
            if service == 'cielo':
                result = self.cieloService.getInvestmentDetails(
                    walletAddress,
                    tokenId
                )
            else:  # default to solscan
                result = self.solscanService.getInvestmentDetails(
                    cookie,
                    walletAddress,
                    tokenId,
                    apiTransactionsCount
                )

            if not result:
                logger.error(f"Failed to get transaction details from {service}")
                return False

            # Update database with results
            self.db.walletsInvested.updateWalletInvestmentData(
                walletInvestedId,
                totalInvested=result.totalInvested,
                amountTakenOut=result.totalTakenOut,
                avgEntry=result.avgEntry,
                totalCoins=result.totalCoins
            )

            return True

        except Exception as e:
            logger.error(f"Failed to analyze transactions: {str(e)}")
            return False

