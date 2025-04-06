from config.Config import get_config
"""
Takes all the smart wallets and stores them in the database
""" 

from typing import Optional, Dict, Any, List
import requests
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import SMWalletTopPnlToken
from datetime import datetime
import time
from logs.logger import get_logger
from parsers.SMWalletTopPNLTokenParser import parseSMWalletTopPNLTokensAPIResponse

logger = get_logger(__name__)

class SMWalletTopPNLTokenAction:
    """Handles top PNL token analysis workflow for smart money wallets"""
    
    def __init__(self, db: PortfolioDB):
        """Initialize action with database instance"""
        self.db = db
        self.session = requests.Session()
        self._configure_headers()
        self.timeout = 60
        self.max_retries = 3
        self.base_url = "https://app.chainedge.io"

    def _configure_headers(self):
        """Set up request headers"""
        self.headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
            'priority': 'u=1, i',
            'referer': 'https://app.chainedge.io/search_solana_wallet/',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'x-requested-with': 'XMLHttpRequest'
        }

    def persistAllTopPNLTokensForASMWallet(self, cookie: str, walletAddress: str, lookbackDays: int = 180) -> Optional[List[SMWalletTopPnlToken]]:
        """
        Get all top PNL tokens for a smart money wallet
        
        Args:
            cookie: Valid cookie for API access
            walletAddress: Wallet address to analyze
            lookbackDays: Number of days to look back (default: 180)
            
        Returns:
            Optional[List[TopPnlToken]]: Parsed and validated top PNL token data
        """
        startTime = time.time()
        try:
            # Construct URL with parameters - Matching exact curl parameters
            url = f"{self.base_url}/load_30_d_pnl_data_solana/"  # Keep the trailing slash
            params = {
                'search': walletAddress,        # Keep as 'search'
                'search_type': 'our_data',      # Keep as 'search_type'
                'min_ts': '0',
                'lkback': str(lookbackDays),
                'days': str(lookbackDays)
            }

            # Make request
            response = self.session.get(
                url,
                params=params,
                headers={**self.headers, 'cookie': cookie},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")

            # Log the raw response for debugging
            logger.debug(f"Raw response for wallet {walletAddress}: {response.text[:200]}...")
            
            try:
                data = response.json()
            except ValueError as json_err:
                # Handle JSON parsing errors more gracefully
                logger.error(f"JSON parsing error for wallet {walletAddress}: {str(json_err)}")
                logger.error(f"Response content: {response.text[:500]}...")
                return None
                
            if data:
                topPNLTokensOfASMWallet = parseSMWalletTopPNLTokensAPIResponse(data, walletAddress)
                if topPNLTokensOfASMWallet:
                    self.persistSMWalletTopPNLTokensData(topPNLTokensOfASMWallet)
                    logger.info(f"Successfully processed {len(topPNLTokensOfASMWallet)} top PNL tokens for wallet {walletAddress}")
                    executionTime = time.time() - startTime
                    logger.info(f"Action completed in {executionTime:.2f} seconds")
                    return topPNLTokensOfASMWallet
            
            return None

        except Exception as e:
            logger.error(f"Failed to analyze top PNL tokens for wallet {walletAddress}: {str(e)}")
            executionTime = time.time() - startTime
            logger.error(f"Action failed after {executionTime:.2f} seconds")
            return None

    def persistSMWalletTopPNLTokensData(self, items: List[SMWalletTopPnlToken]):
        """
        Persist top PNL token data to database
        
        Args:
            items: List of TopPnlToken objects to persist
        """
        try:
            with self.db.transaction() as cursor:
                for item in items:
                    try:
                        # Check if token exists for this wallet
                        isTokenDataAlreadyAvailable = self.db.smWalletTopPNLToken.getSMWalletTopPNLToken(
                            item.walletaddress,
                            item.tokenid
                        )
                        
                        if isTokenDataAlreadyAvailable:
                            logger.info(f"Token data already available for wallet {item.walletaddress} and token {item.tokenid}. Updating the data.")
                            self.db.smWalletTopPNLToken.updateSMWalletToken(item, cursor)
                        else:
                            logger.info(f"Token data not available for wallet {item.walletaddress} and token {item.tokenid}. Inserting the data.")
                            self.db.smWalletTopPNLToken.insertSMWalletToken(item, cursor)
                            
                    except Exception as e:
                        logger.error(f"Failed to persist token {item.tokenid} for wallet {item.walletaddress}: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise 