from config.Config import get_config
"""
Finds invested amount, taken out amount and total coins for high pnl wallets
for a particular token
"""
from typing import List, Dict, Optional
from decimal import Decimal
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import InvestmentDetails
from logs.logger import get_logger
from services.SolscanServiceHandler import SolscanServiceHandler
from services.CieloServiceHandler import CieloServiceHandler
from database.auth.ServiceCredentialsEnum import ServiceCredentials
import random
import time

logger = get_logger(__name__)

class SMWalletTopPNLTokensInvestmentDetailsAction:
    """Updates SMWalletTopPNLToken records with detailed transaction data"""
    
    def __init__(self, db: PortfolioDB):
        """Initialize action with database instance"""
        self.db = db
        self.solscan_service = SolscanServiceHandler(db)
        self.cielo_service = CieloServiceHandler(db)

    def filter_tokens_by_performance(self, tokens, top_percent=0.3, bottom_percent=0.2):
        """
        Filter tokens to get top and bottom performers based on percentiles.
        
        Args:
            tokens: List of token objects with unprocessedpnl attribute
            top_percent: Percentage of top performers to select (0.3 = top 30%)
            bottom_percent: Percentage of bottom performers to select (0.2 = bottom 20%)
            
        Returns:
            List of filtered tokens containing top and bottom performers
        """
        if not tokens:
            return []
            
        # Sort tokens by unprocessedpnl
        sortedTokens = sorted(tokens, key=lambda x: float(x.unprocessedpnl), reverse=True)
        
        # Calculate indices for top and bottom percentiles
        topCount = max(1, int(len(sortedTokens) * top_percent))
        bottomCount = max(1, int(len(sortedTokens) * bottom_percent))
        
        # Get top and bottom performers
        topTokens = sortedTokens[:topCount]
        bottomTokens = sortedTokens[-bottomCount:]
        
        # Combine the lists
        filteredTokens = topTokens + bottomTokens
        
        logger.info(f"Selected {len(filteredTokens)} tokens for processing: " +
                    f"{len(topTokens)} top performers and {len(bottomTokens)} bottom performers")
                    
        return filteredTokens
    
    def handleInvestmentDetailsOfAllHighPNLSMWallets(self, cookie: str, 
                                                    service: ServiceCredentials = ServiceCredentials.CIELO) -> bool:
        """Process investment details for tokens of high PNL wallets"""
        try:
            # Step 1: Get high PNL wallets
            highPnlWallets = self.db.smartMoneyWallets.getAllHighPnlSmartMoneyWallets()
            if not highPnlWallets:
                logger.warning("No high PNL wallets found")
                return False
            
            logger.info(f"Found {len(highPnlWallets)} high PNL wallets")
            
            # Step 2: Iterate through each wallet
            totalProcessed = 0
            for wallet in highPnlWallets:
                try:
                    walletAddress = wallet.get('walletAddress')
                    logger.info(f"Processing wallet: {walletAddress}")
                    
                    # Step 3: Get all tokens invested by this wallet
                    tokens = self.db.smWalletTopPNLToken.getTokensForWallet(walletAddress)
                    if not tokens:
                        logger.warning(f"No tokens found for wallet {walletAddress}")
                        continue
                    
                    logger.info(f"Found {len(tokens)} tokens for wallet {walletAddress}")
                    
                    # Step 4: Filter tokens to get top 30% and bottom 20% by unprocessedpnl
                    # filteredTokens = self.filter_tokens_by_performance(tokens)
                    filteredTokens = tokens
                    # Step 5: Process each filtered token
                    for token in filteredTokens:
                        try:
                            logger.info(f"Processing token: {token.name} (PNL: {token.unprocessedpnl}) for wallet {walletAddress}")
                            success = self.findInvestmentDataForToken(
                                walletAddress=walletAddress,
                                tokenId=token.tokenid,
                                cookie=cookie,
                                service=service
                            )
                            
                            if success:
                                totalProcessed += 1
                                logger.info(f"Successfully processed token {token.tokenid} ({token.name}) for wallet {walletAddress}")
                            else:
                                logger.info(f"Failed to process token {token.tokenid} ({token.name}) for wallet {walletAddress}")
                            
                        except Exception as e:
                            logger.error(f"Failed to process token {token.tokenid} for wallet {walletAddress}: {str(e)}")
                            continue
                    
                    # Sleep between wallets
                    # delay = random.uniform(1, 5)
                    # logger.info(f"Completed wallet {walletAddress}. Sleeping for {delay} seconds before next wallet")
                    # time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"Failed to process wallet {wallet.get('walletaddress', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Total tokens processed successfully: {totalProcessed}")
            return totalProcessed > 0
            
        except Exception as e:
            logger.error(f"Failed to handle investment details: {str(e)}")
            return False

    def handleInvestmentDetailsOfASpecificWallet(self, walletAddress: str, cookie: str,
                                                service: ServiceCredentials = ServiceCredentials.CIELO) -> bool:
        """
        Process all tokens for a specific wallet
        
        Args:
            walletAddress: The wallet address to process
            cookie: Authentication cookie for the service
            service: Service to use for fetching data (default: CIELO)
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Processing investment details for wallet: {walletAddress}")
        return self.findHighPNLTokenInvestmentDataForWallet(walletAddress, cookie, service)

    def findHighPNLTokenInvestmentDataForWallet(self, walletAddress: str, cookie: str, service: ServiceCredentials = ServiceCredentials.CIELO) -> bool:
        """Process all tokens for a specific wallet"""
        try:
            tokens = self.db.smWalletTopPNLToken.getTokensForWallet(walletAddress)
            if not tokens:
                logger.warning(f"No tokens found for wallet {walletAddress}")
                return False
            
            for token in tokens:
                try:
                    success = self.findInvestmentDataForToken(
                        walletAddress=walletAddress,
                        tokenId=token.tokenid,
                        cookie=cookie,
                        service=service
                    )
                    if not success:
                        logger.warning(f"Failed to process token {token.tokenid}")
                        continue
                    
                except Exception as e:
                    logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
                    continue
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute wallet update: {str(e)}")
            return False

    def findInvestmentDataForToken(self, walletAddress: str, tokenId: str, 
                                 cookie: str, service: ServiceCredentials = ServiceCredentials.CIELO) -> bool:
        """Process a specific wallet-token combination"""
        try:
            # Get token data from database
            token = self.db.smWalletTopPNLToken.getSMWalletTopPNLToken(walletAddress, tokenId)
            if not token:
                logger.warning(f"No token found for wallet {walletAddress} and token {tokenId}")
                return False

            # Get current count from database
            dbTransactionsCount = self.db.smWalletTopPNLToken.getTransactionCount(
                walletAddress,
                tokenId
            )
            
            # Get transaction count from Solscan API (always use Solscan for count)
            logger.info(f"Getting transaction count for {walletAddress} and token {tokenId}")
            apiTransactionsCount = self.solscan_service.getTransactionCountFromAPI(
                cookie,
                walletAddress,
                tokenId
            )
            logger.info(f"Transaction count for {walletAddress} and token {tokenId}: {apiTransactionsCount}")
            

            # Skip if no new transactions
            if dbTransactionsCount and dbTransactionsCount >= apiTransactionsCount:
                logger.info(f"No new transactions for {walletAddress} and token {tokenId}. DB: {dbTransactionsCount}, API: {apiTransactionsCount}")
                return True
            
            # UPDATE TRANSACTION COUNT IN DB BEFORE PROCEEDING - This is the critical change
            # Update the transaction count in DB to ensure it's synchronized even if investment details call fails
            logger.info(f"Updating transaction count in DB for {walletAddress} and token {tokenId} from {dbTransactionsCount} to {apiTransactionsCount}")
            isUpdatedInDB = self.db.smWalletTopPNLToken.updateTransactionCount(
                walletAddress=walletAddress,
                tokenId=tokenId,
                transactionsCount=apiTransactionsCount
            )
            
            if not isUpdatedInDB:
                logger.warning(f"Failed to update transaction count in DB for {walletAddress} and token {tokenId}")
                # Continue anyway since we'll try to update the full data later

            # Get investment details from selected service
            result: Optional[InvestmentDetails] = None
            if service == ServiceCredentials.CIELO:
                result = self.cielo_service.getInvestmentDetails(
                    walletAddress=walletAddress,
                    tokenId=tokenId
                )
            else:  # default to solscan
                result = self.solscan_service.getInvestmentDetails(
                    cookie=cookie,
                    walletAddress=walletAddress,
                    tokenAddress=tokenId,
                    totalTransactions=apiTransactionsCount
                )
            # logger.info(f"Investment details for {walletAddress} and token {tokenId}: {result}")

            if not result:
                logger.warning(f"Failed to get investment details for {walletAddress}")
                return False

            # Update database with investment results
            self.db.smWalletTopPNLToken.updateInvestementDataForTopPnlToken(
                walletAddress=walletAddress,
                tokenId=tokenId,
                amountInvested=result.totalInvested,
                amountTakenOut=result.totalTakenOut,
                remainingCoins=result.totalCoins,
                transactionsCount=apiTransactionsCount  # Include transaction count for completeness
            )

            return True

        except Exception as e:
            logger.error(f"Failed to get investment details for {walletAddress} and token {tokenId}: {str(e)}")
            return False

    def handleInvestmentDetailsOfAllTokens(self, cookie, service='solscan'):
        """
        Process investment details for ALL tokens of high PNL wallets without filtering.
        
        Args:
            cookie: Cookie for the service API
            service: Service name (default: 'solscan')
            
        Returns:
            Boolean indicating success
        """
        try:
            # Step 1: Get high PNL wallets
            highPnlWallets = self.db.smartMoneyWallets.getAllHighPnlSmartMoneyWallets()
            if not highPnlWallets:
                logger.warning("No high PNL wallets found")
                return False
            
            logger.info(f"Found {len(highPnlWallets)} high PNL wallets")
            
            # Step 2: Iterate through each wallet
            totalProcessed = 0
            for wallet in highPnlWallets:
                try:
                    walletAddress = wallet['walletaddress']
                    logger.info(f"Processing wallet: {walletAddress}")
                    
                    # Step 3: Get all tokens invested by this wallet
                    tokens = self.db.smWalletTopPNLToken.getTokensForWallet(walletAddress)
                    if not tokens:
                        logger.warning(f"No tokens found for wallet {walletAddress}")
                        continue
                    
                    logger.info(f"Found {len(tokens)} tokens for wallet {walletAddress}")
                    
                    # Step 4: Process ALL tokens (no filtering)
                    for token in tokens:
                        try:
                            # Process using our improved findInvestmentDataForToken method
                            # which now properly updates transaction counts
                            logger.info(f"Processing token: {token.name} (PNL: {token.unprocessedpnl}) for wallet {walletAddress}")
                            success = self.findInvestmentDataForToken(
                                walletAddress=walletAddress,
                                tokenId=token.tokenid,
                                cookie=cookie,
                                service=service
                            )
                            
                            if success:
                                totalProcessed += 1
                            else:
                                logger.warning(f"Failed to process token {token.tokenid} ({token.name}) for wallet {walletAddress}")
                            
                        except Exception as e:
                            logger.error(f"Failed to process token {token.tokenid} for wallet {walletAddress}: {str(e)}")
                            continue
                
                except Exception as e:
                    logger.error(f"Failed to process wallet {wallet.get('walletaddress', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Total tokens processed successfully: {totalProcessed}")
            return totalProcessed > 0
            
        except Exception as e:
            logger.error(f"Failed to handle investment details of all tokens: {str(e)}")
            return False
            
    def handleInvestmentDetailsForWallet(self, walletAddress, cookie, service='solscan', filter_tokens=True, top_percent=0.3, bottom_percent=0.2):
        """
        Process investment details for tokens of a specific wallet with optional filtering.
        
        Args:
            walletAddress: Address of the wallet to process
            cookie: Cookie for the service API
            service: Service name (default: 'solscan')
            filter_tokens: Whether to filter tokens by performance (default: True)
            top_percent: Percentage of top performers to select if filtering (default: 0.3)
            bottom_percent: Percentage of bottom performers to select if filtering (default: 0.2)
            
        Returns:
            Boolean indicating success
        """
        try:
            # Get all tokens invested by this wallet
            tokens = self.db.smWalletTopPNLToken.getTokensForWallet(walletAddress)
            if not tokens:
                logger.warning(f"No tokens found for wallet {walletAddress}")
                return False
            
            logger.info(f"Found {len(tokens)} tokens for wallet {walletAddress}")
            
            # Apply filtering if requested
            if filter_tokens:
                tokens_to_process = self.filter_tokens_by_performance(tokens, top_percent, bottom_percent)
            else:
                tokens_to_process = tokens
                logger.info(f"Processing all {len(tokens)} tokens for wallet {walletAddress}")
            
            # Process each token
            totalProcessed = 0
            for token in tokens_to_process:
                try:
                    # Use our improved findInvestmentDataForToken method
                    # which now properly updates transaction counts
                    logger.info(f"Processing token: {token.name} (PNL: {token.unprocessedpnl}) for wallet {walletAddress}")
                    success = self.findInvestmentDataForToken(
                        walletAddress=walletAddress,
                        tokenId=token.tokenid,
                        cookie=cookie,
                        service=service
                    )
                    
                    if success:
                        totalProcessed += 1
                    else:
                        logger.warning(f"Failed to process token {token.tokenid} ({token.name}) for wallet {walletAddress}")
                    
                except Exception as e:
                    logger.error(f"Failed to process token {token.tokenid} for wallet {walletAddress}: {str(e)}")
                    continue
            
            logger.info(f"Total tokens processed successfully for wallet {walletAddress}: {totalProcessed}")
            return totalProcessed > 0
            
        except Exception as e:
            logger.error(f"Failed to handle investment details for wallet {walletAddress}: {str(e)}")
            return False

   