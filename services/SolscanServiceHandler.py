from config.Config import get_config
"""
Handles all Solscan API related operations including transaction processing
"""
from typing import Dict, List, Optional
import requests
import time
from decimal import Decimal
from logs.logger import get_logger
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import InvestmentDetails

logger = get_logger(__name__)

class SolscanServiceHandler:
    def __init__(self, db: PortfolioDB):
        """
        Initialize Solscan service handler
        
        Args:
            db: Database handler instance
        """
        self.db = db
        self.baseUrl = "https://api-v2.solscan.io/v2"
        self.session = requests.Session()
        self.maxRetries = 3
        self.retryDelay = 2
        
    def getTransactionCountFromAPI(self, cookie: str, walletAddress: str, tokenAddress: str) -> Optional[int]:
        """
        Get total number of transactions for a wallet-token pair
        
        Args:
            cookie: Valid solscan cookie
            walletAddress: Wallet address to analyze
            tokenAddress: Token address to analyze
            
        Returns:
            Optional[int]: Total number of transactions or None if failed
        """
        headers = self.getHeaders(cookie)
        params = {
            'address': walletAddress,
            'token': tokenAddress,
            'remove_spam': 'false',
            'exclude_amount_zero': 'false'
        }
        
        for attempt in range(self.maxRetries):
            try:
                response = self.session.get(
                    f"{self.baseUrl}/account/transfer/total",
                    headers=headers,
                    params=params,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('success'):
                    return data.get('data', 0) #{"success":true,"data":"number of transactions will be here","metadata":{}}
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{self.maxRetries} failed: {e}")
                if attempt < self.maxRetries - 1:
                    time.sleep(self.retryDelay * (attempt + 1))
                    
        return None
        
    def getInvestmentDetails(self, cookie: str, walletAddress: str, 
                                    tokenAddress: str, totalTransactions: int) -> Optional[Dict]:
        """
        Get all transactions and calculate investment details
        
        Args:
            cookie: Valid solscan cookie
            walletAddress: Wallet address to analyze
            tokenAddress: Token address to analyze
            totalTransactions: Total number of transactions to fetch
            
        Returns:
            Optional[Dict]: Calculated investment details or None if failed
        """
        try:
            transactions = self.getAllTransactions(cookie, walletAddress, tokenAddress, totalTransactions)
            if not transactions:
                return None
                
            return self.calculateInvestmentDetails(transactions)
            
        except Exception as e:
            logger.error(f"Failed to get transaction details: {e}")
            return None
            
    def getAllTransactions(self, cookie: str, walletAddress: str, 
                            tokenAddress: str, totalTransactions: int) -> Optional[List[Dict]]:
        """Get all transactions using pagination"""
        allTransactions = []
        pageSize = 100
        totalPages = (totalTransactions + pageSize - 1) // pageSize
        
        for page in range(1, totalPages + 1):
            transactions = self.getTransactions(
                cookie,
                walletAddress,
                tokenAddress,
                page,
                pageSize
            )
            
            if not transactions:
                continue
                
            allTransactions.extend(transactions)
            
            if page < totalPages:
                time.sleep(1)  # Rate limiting
                
        return allTransactions
        
    def getTransactions(self, cookie: str, walletAddress: str, 
                             tokenAddress: str, page: int, pageSize: int) -> Optional[List[Dict]]:
        """Get single page of transactions"""
        headers = self.getHeaders(cookie)
        params = {
            'address': walletAddress,
            'token': tokenAddress,
            'page': page,
            'page_size': pageSize,
            'remove_spam': 'false',
            'exclude_amount_zero': 'false'
        }
        
        for attempt in range(self.maxRetries):
            try:
                response = self.session.get(
                    f"{self.baseUrl}/account/transfer",
                    headers=headers,
                    params=params,
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('success'):
                    return data.get('data', [])
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{self.maxRetries} failed: {e}")
                if attempt < self.maxRetries - 1:
                    time.sleep(self.retryDelay * (attempt + 1))
                    
        return None
        
    def calculateInvestmentDetails(self, transactions: List[Dict]) -> InvestmentDetails:
        """Calculate investment details from transactions"""
        totalInvested = Decimal('0')
        totalTakenOut = Decimal('0')
        totalCoins = Decimal('0')
        
        for tx in transactions:
            try:
                amount = Decimal(str(tx.get('amount', 0)))
                value = Decimal(str(tx.get('value', 0)))
                decimals = int(tx.get('token_decimals', 0))
                flow = tx.get('flow', '')

                coinAmount = amount / Decimal(str(10 ** decimals))

                if flow == 'in':
                    totalInvested += value
                    totalCoins += coinAmount
                elif flow == 'out':
                    totalTakenOut += value
                    totalCoins -= coinAmount
                    
            except Exception as e:
                logger.error(f"Failed to process transaction: {e}")
                continue
                
        avgEntry = (totalInvested / totalCoins) if totalCoins > 0 else Decimal('0')
        
        return InvestmentDetails(
            totalInvested=totalInvested,
            totalTakenOut=totalTakenOut,
            totalCoins=totalCoins,
            avgEntry=avgEntry
        )
        
    def getHeaders(self, cookie: str) -> Dict:
        """Get headers for Solscan API"""
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
            'origin': 'https://solscan.io',
            'priority': 'u=1, i',
            'referer': 'https://solscan.io/',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sol-aut': 'SO2TkJCB9dls0fKdPC6CV2Q2uXKRltCTsW-7JodG',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
            'cookie': cookie
        } 