from config.Config import get_config
from typing import Optional, Dict, Any, List, Union
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import OnchainInfo
import parsers.OnchainParser as onchainParsers
import requests
from decimal import Decimal
import time
from datetime import datetime
from logs.logger import get_logger
from database.onchain.OnchainHandler import OnchainHandler
from services.AuthService import AuthService
from database.auth.ServiceCredentialsEnum import ServiceCredentials, CredentialType
import pytz
logger = get_logger(__name__)

class OnchainAction:
    """Handles complete onchain data request workflow"""
    
    def __init__(self, db: PortfolioDB):
        """
        Initialize action with required parameters
        Args:
            db: Database handler for persistence
        """
        self.db = db
        self.service = ServiceCredentials.CHAINEDGE
        self.baseUrl = self.service.metadata['base_url']
        self.tokenHandler = self.db.token

    def processOnchainTokens(self, cookie: str) -> bool:
        """
        Fetch and persist onchain tokens
        Args:
            cookie: Validated cookie for API request
        Returns:
            bool: Success status
        """
        try:
            # Make API request with provided cookie
            response = self.hitAPI(cookie)
            if not response:
                logger.error("API request failed")
                return False

            # Parse response into OnchainInfo objects
            onchainTokens = onchainParsers.parseOnchainResponse(response)
            if not onchainTokens:
                logger.error("No valid items found in response")
                return False

            # Persist to database and get successfully persisted tokens
            persistedTokens = self.persistTokens(onchainTokens)
                
            return len(persistedTokens) > 0

        except Exception as e:
            logger.error(f"Onchain data action failed: {str(e)}")
            return False

    def hitAPI(self, cookie: str) -> Optional[Dict]:
        """Make onchain API request"""
        try:
            # Get fresh access token using service credentials
            authService = AuthService(
                self.tokenHandler, 
                self.db,
                self.service
            )
            accessToken = authService.getValidAccessToken()
            
            if not accessToken:
                logger.error("Failed to get valid access token")
                return None
            
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
                'authorization': f'Bearer {accessToken}',
                'cookie': cookie,
                'origin': 'https://trading.chainedge.io',
                'priority': 'u=1, i',
                'referer': 'https://trading.chainedge.io/',
                'sec-ch-ua': '"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0'
            }

            params = {
                'filter_name': 'fdv_lt_one_mil_filter',
                'refresh': '0',
                'chain': ''
            }

            # Use the correct API URL from the curl command
            url = 'https://trading-api-ce111.chainedge.io/api/tokensToWatch/'
            
            # Log the request URL for debugging
            logger.info(f"Making request to: {url} with params: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
            
            # For testing with local file
            # import json
            # with open('/Users/obscurainvera/Desktop/solportprod/onchainstrength.json', 'r') as f:
            #     return json.load(f)

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return None

    def persistTokens(self, onchainTokens: List[OnchainInfo]) -> List[OnchainInfo]:
        """
        Persist OnchainInfo objects to database
        
        Args:
            onchainTokens: List of OnchainInfo objects to persist
            
        Returns:
            List[OnchainInfo]: List of tokens that were successfully persisted
        """
        successfulTokens = []
        
        for token in onchainTokens:
            try:
                self.db.onchain.insertTokenData(token)
                successfulTokens.append(token)
            except Exception as token_error:
                logger.error(f"Failed to persist token {token.tokenid}: {str(token_error)}")
                continue
                    
        logger.info(f"Successfully persisted {len(successfulTokens)} onchain tokens")
        return successfulTokens
