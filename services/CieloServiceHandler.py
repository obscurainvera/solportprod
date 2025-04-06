from config.Config import get_config
"""
Handles all Cielo API related operations including pagination and transaction processing
"""
from typing import Dict, List, Optional, Tuple
import requests
import time
from decimal import Decimal
from logs.logger import get_logger
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import InvestmentDetails
from database.auth.ServiceCredentialsEnum import ServiceCredentials

logger = get_logger(__name__)

class CieloServiceHandler:
    def __init__(self, db: PortfolioDB):
        self.db = db
        self.service = ServiceCredentials.CIELO
        self.baseUrl = self.service.metadata['base_url']
        self.creditsPerCall = self.service.metadata.get('credits_per_call', 3)
        self.session = requests.Session()
        
    def getInvestmentDetails(self, walletAddress: str, tokenId: str) -> Optional[InvestmentDetails]:
        """
       Calculate investment details
        
        Args:
            walletAddress (str): Wallet address to analyze
            tokenAddress (str): Token address to analyze
            
        Returns:
            Optional[InvestmentDetails]: Calculated investment details or None if failed
        """
        try:
            transactions = self.getAllTransactions(walletAddress, tokenId)
            # logger.info(f"Transactions for {walletAddress} and token {tokenId}: {transactions}")
            if not transactions:
                return None
            return self.calculateInvestmentDetails(transactions, tokenId)
            
        except Exception as e:
            logger.error(f"Failed to get transaction details: {e}")
            return None
           
    def getAllTransactions(self, walletAddress: str, tokenId: str) -> Optional[List[Dict]]:
        """
        Get all transactions using pagination
        
        Args:
            walletAddress: Wallet address to analyze
            tokenId: Token address to analyze
            
        Returns:
            Optional[List[Dict]]: List of all transactions or None if failed
        """
        allTransactions = []
        startFrom = None
        
        while True:
            apiKeyData = self.db.credentials.getNextValidApiKey(
                serviceName=self.service.service_name, 
                requiredCredits=self.creditsPerCall
            )
            if not apiKeyData:
                logger.error("No valid API key available")
                return None
                
            # Get page of transactions
            # logger.info(f"Getting transactions for {walletAddress} and token {tokenId} with API key {apiKeyData['apikey']}")
            result = self.getSwaps(
                apiKey=apiKeyData['apikey'],
                walletAddress=walletAddress,
                tokenId=tokenId,
                startFrom=startFrom
            )
            
            if not result:
                break
                
            # Unpack response
            items = result.get('data', {}).get('items', [])
            paging = result.get('data', {}).get('paging', {})
            
            # Update API key credits
            self.db.credentials.deductAPIKeyCredits(apiKeyData['id'], self.creditsPerCall)
            
            # Add transactions to list
            allTransactions.extend(items)
            
            # Check if more pages exist
            hasNextPage = paging.get('has_next_page', False)
            if not hasNextPage:
                break
                
            # Get next cursor for pagination
            startFrom = paging.get('next_cursor')
            time.sleep(1)  # Rate limiting
            
        return allTransactions
         
    def getSwaps(self, apiKey: str, walletAddress: str, 
                             tokenId: str, startFrom: Optional[str] = None) -> Optional[Dict]:
        """
        Get single page of transactions
        
        Args:
            apiKey: Valid Cielo API key
            walletAddress: Wallet address to analyze
            tokenId: Token address to analyze
            startFrom: Pagination cursor from previous request
            
        Returns:
            Optional[Dict]: Raw API response or None if failed
        """
        params = {
            'wallet': walletAddress,
            'tokens': tokenId,
            'limit': 100,
            'txTypes': 'swap'
        }
        
        # Add startFrom parameter only for pagination requests
        if startFrom:
            params['startFrom'] = startFrom
            
        headers = {'accept': 'application/json', 'x-api-key': apiKey}
        
        try:
            response = self.session.get(
                f"{self.baseUrl}/feed",
                headers=headers,
                params=params,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                return data
                
        except Exception as e:
            logger.error(f"Failed to get transactions page: {e}")
            
        return None
        
    def calculateInvestmentDetails(self, transactions: List[Dict], tokenAddress: str) -> InvestmentDetails:
        """
        Calculate investment details from transactions
        
        Args:
            transactions: List of transactions to analyze
            tokenAddress: Token address to track

        # If the token0_address is the same as the token address we get from the parameter,
        # then to find the amount, use token0_amount. To find the value, use 'token1_amount_usd'.
        # If the token1_address is the same as the token address we get from the parameter,
        # then to find the amount, use token1_amount. To find the value, use 'token0_amount_usd'.
            
        Returns:
            InvestmentDetails: Calculated investment metrics
        """
        totalInvested = Decimal('0')
        totalTakenOut = Decimal('0')
        totalCoins = Decimal('0')
        totalTokensBought = Decimal('0')
        
        for tx in transactions:
            try:
                isToken0 = tx.get('token0_address') == tokenAddress #if token0_address is the same as the token address, then the wallet is selling the token
                isToken1 = tx.get('token1_address') == tokenAddress #if token1_address is the same as the token address, then the wallet is buying the token
                
                if not (isToken0 or isToken1):
                    logger.warning(f"Transaction doesn't involve target token: {tokenAddress}")
                    continue
                    
                if isToken0:
                    # Token we're tracking is token0
                    coinsSold = Decimal(str(tx.get('token0_amount', 0)))
                    usdAmount = Decimal(str(tx.get('token1_amount_usd', 0)))
                    totalTakenOut += usdAmount
                    totalCoins -= coinsSold
                else:
                    # Token we're tracking is token1
                    coinsBought = Decimal(str(tx.get('token1_amount', 0)))
                    usdAmount = Decimal(str(tx.get('token0_amount_usd', 0)))
                    totalInvested += usdAmount
                    totalCoins += coinsBought
                    totalTokensBought += coinsBought
                    
            except Exception as e:
                logger.error(f"Failed to process transaction: {e}")
                continue
                
        avgEntry = ((totalInvested - totalTakenOut)/totalCoins) if totalCoins > 0 else Decimal('0')
        
        return InvestmentDetails(
            totalInvested=totalInvested,
            totalTakenOut=totalTakenOut,
            totalCoins=totalCoins,
            avgEntry=avgEntry
        ) 