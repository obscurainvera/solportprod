from config.Config import get_config
"""
Takes all the tokens in volume signals and stores them in volume_signals table and
in case of duplicate tokens, it updates the record and records the history
in the history table
"""

from typing import Optional, Dict, Any, List, Union
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import VolumeToken
import parsers.VolumebotParser as volumeParsers
import requests
from decimal import Decimal
import time
from datetime import datetime
from logs.logger import get_logger
from database.volume.VolumeHandler import VolumeHandler
from services.AuthService import AuthService
from database.auth.ServiceCredentialsEnum import ServiceCredentials, CredentialType
from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from database.auth.TokenHandler import TokenHandler
import pytz
logger = get_logger(__name__)

class VolumebotAction:
    """Handles complete volume signals request workflow"""
    
    def __init__(self, db: PortfolioDB):
        """
        Initialize action with required parameters
        Args:
            db: Database handler for persistence
        """
        self.db = db
        self.service = ServiceCredentials.CHAINEDGE
        self.baseUrl = self.service.metadata['base_url']
        self.tokenHandler = TokenHandler(self.db.conn_manager)

    def processVolumebotTokens(self, cookie: str) -> bool:
        """
        Fetch and persist volume tokens
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

            # Parse response into VolumeToken objects
            volumeTokens = volumeParsers.parseVolumeResponse(response)
            if not volumeTokens:
                logger.error("No valid items found in response")
                return False

            # Persist to database and get successfully persisted tokens
            persistedTokens = self.persistTokens(volumeTokens)
        
                
            return len(persistedTokens) > 0

        except Exception as e:
            logger.error(f"Volume signals action failed: {str(e)}")
            return False

    def hitAPI(self, cookie: str) -> Optional[Dict]:
        """Make volume signals API request"""
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
                'origin': self.service.metadata['web_url'],
                'referer': f"{self.service.metadata['web_url']}/",
                'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0'
            }

            params = {
                'filter_name': 'volume_signals',
                'refresh': '0'
            }

            # Fix the URL by appending the correct endpoint path
            url = f"{self.baseUrl}/tokensToWatch/"
            
            # Log the request URL for debugging
            logger.info(f"Making request to: {url} with params: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return None

    def persistTokens(self, volumeTokens: List[VolumeToken]) -> List[VolumeToken]:
        """
        Persist VolumeToken objects to database
        
        Args:
            volumeTokens: List of VolumeToken objects to persist
            
        Returns:
            List[VolumeToken]: List of tokens that were successfully persisted
        """
        successfulTokens = []
        
        for token in volumeTokens:
            try:
                self.db.volume.insertTokenData(token)
                successfulTokens.append(token)
            except Exception as token_error:
                logger.error(f"Failed to persist token {token.name}: {str(token_error)}")
                continue
                    
        logger.info(f"Successfully persisted {len(successfulTokens)} volume tokens")
        return successfulTokens

    def pushVolumeTokensToStrategyFramework(self, volumeTokens: List[VolumeToken]) -> bool:
        """
        Maps volume tokens to VolumeTokenData objects and pushes them to the strategy framework
        Only pushes tokens that have timeago within 5 minutes from the current time
        
        Args:
            volumeTokens: List of VolumeToken objects to push to the strategy framework
            
        Returns:
            bool: True if at least one token was successfully pushed, False otherwise
        """
        try:
            if not volumeTokens:
                logger.info("No volume tokens to push to strategy framework")
                return False
                
            logger.info(f"Checking {len(volumeTokens)} volume tokens for recent timeago")
            
            # Get current time in UTC
            currentTime = datetime.now(pytz.UTC)
            # Define the time threshold (5 minutes = 300 seconds)
            timeThresholdSeconds = 300
            
            # Initialize analytics handler and push token API
            pushTokenAPI = PushTokenAPI()
            
            # Process each token
            successCount = 0
            filteredCount = 0
            for token in volumeTokens:
                try:
                    # Check if timeago is within the threshold
                    if token.timeago is None:
                        logger.warning(f"Token {token.tokenname} has no timeago value, skipping")
                        continue
                    
                    # Ensure timeago is timezone-aware (UTC)
                    tokenTimeago = token.timeago
                    if tokenTimeago.tzinfo is None:
                        tokenTimeago = pytz.UTC.localize(tokenTimeago)
                    
                    # Calculate time difference in seconds
                    timeDiff = (currentTime - tokenTimeago).total_seconds()
                    
                    # Skip if timeago is older than 5 minutes
                    if timeDiff > timeThresholdSeconds:
                        logger.info(f"Token {token.tokenname} timeago is {timeDiff} seconds old (UTC), exceeds threshold of {timeThresholdSeconds} seconds")
                        filteredCount += 1
                        continue
                        
                    # Get the current state of the token from the database
                    tokenState = self.db.volume.getTokenState(token.tokenid)
                    if not tokenState:
                        logger.warning(f"Token state not found for {token.tokenname}, skipping")
                        continue
                        
                    # Get token info
                    tokenInfo = self.db.volume.getTokenInfo(token.tokenid)
                    if not tokenInfo:
                        logger.warning(f"Token info not found for {token.tokenname}, skipping")
                        continue
                    
                    # Combine token state and info into a single dictionary
                    combinedTokenData = {**tokenState, **tokenInfo}
                    
                    # Convert to VolumeTokenData
                    tokenData = PushTokenAPI.mapVolumeTokenData(combinedTokenData)
                    
                    # Push to strategy framework
                    success = pushTokenAPI.pushToken(
                        tokenData=tokenData,
                        sourceType=SourceType.VOLUME.value
                    )
                    
                    if success:
                        successCount += 1
                        logger.info(f"Successfully pushed token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework (timeago: {timeDiff} seconds)")
                    else:
                        logger.warning(f"Failed to push token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework")
                
                except Exception as token_error:
                    logger.error(f"Error processing token {token.tokenid}: {str(token_error)}")
                    continue
            
            logger.info(f"Successfully pushed {successCount}/{len(volumeTokens)} tokens to strategy framework. Filtered out {filteredCount} tokens older than 5 minutes.")
            return successCount > 0
            
        except Exception as e:
            logger.error(f"Failed to push volume tokens to strategy framework: {str(e)}", exc_info=True)
            return False

    