from config.Config import get_config
"Takes all the smart money wallets and stores them in the database"

from typing import Optional, Dict, Any, List
import requests
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger
import time
from datetime import datetime
from parsers.SmartMoneyWalletsParser import parseSmartMoneyWalletsAPIResponse
from database.operations.schema import SmartMoneyWallet
import random
from database.smartmoneywallets.WalletPNLStatusEnum import SmartWalletPnlStatus
from decimal import Decimal

logger = get_logger(__name__)

class SmartMoneyWalletsAction:
    """Handles smart money wallets analysis workflow"""
    
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
            'referer': 'https://app.chainedge.io/insights/',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'x-requested-with': 'XMLHttpRequest'
        }

    def getAllSmartMoneyWallets(self, cookie: str) -> Optional[List[SmartMoneyWallet]]:
        """
        Get all smart money wallets
        Args:
            cookie: Valid cookie for API access
            
        Returns:
            Optional[List[SmartMoneyWallet]]: Parsed and validated smart money wallets data
        """
        startTime = time.time()
        try:
            
            response = self.session.get(
                f"{self.base_url}/walletTokenPnlJsonSolana/",
                headers={**self.headers, 'cookie': cookie},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")

            data = response.json()
            if data:
                smartMoneyWallets = parseSmartMoneyWalletsAPIResponse(data)
                if smartMoneyWallets:
                    self.categorizeAndPersistSmartMoneyWalletData(smartMoneyWallets)
                    logger.info(f"Successfully processed {len(smartMoneyWallets)} smart money wallets")
                    executionTime = time.time() - startTime
                    logger.info(f"Action completed in {executionTime:.2f} seconds")
                    return smartMoneyWallets
            
            return None

        except Exception as e:
            logger.error(f"Failed to analyze smart money wallets: {str(e)}")
            executionTime = time.time() - startTime
            logger.error(f"Action failed after {executionTime:.2f} seconds")
            return None

    def categorizeAndPersistSmartMoneyWalletData(self, smartMoneyWallets: List[SmartMoneyWallet]):
        """
        Categorize wallets based on profit threshold and persist to database
        """
        try:
            with self.db.transaction() as cursor:
                for smartMoneyWallet in smartMoneyWallets:
                    try:
                        profit = float(smartMoneyWallet.profitandloss)  # Convert to float for comparison
                        # Use enum to determine status
                        status = SmartWalletPnlStatus.getSmartWalletPNLStatus(profit)
                        smartMoneyWallet.status = status.value
                        
                        isSMWalletExsisting = self.db.smartMoneyWallets.getSmartMoneyWallet(
                            smartMoneyWallet.walletaddress
                        )
                        
                        if isSMWalletExsisting:
                            logger.info(f"Updating existing smart money wallet: {smartMoneyWallet.walletaddress}")
                            self.db.smartMoneyWallets.updateSmartMoneyWallet(smartMoneyWallet, cursor)
                        else:
                            logger.info(f"Inserting new smart money wallet: {smartMoneyWallet.walletaddress}")
                            self.db.smartMoneyWallets.insertSmartMoneyWallet(smartMoneyWallet, cursor)
                            
                    except Exception as e:
                        logger.error(f"Failed to persist wallet {smartMoneyWallet.walletaddress}: {str(e)}")
                        continue

        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise 