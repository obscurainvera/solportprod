from config.Config import get_config
"""
Takes attention scores for tokens and stores them in the database with analysis
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from database.operations.PortfolioDB import PortfolioDB
import parsers.AttentionParser as attentionParser
from database.operations.schema import AttentionData
import requests
import time
from logs.logger import get_logger

logger = get_logger(__name__)

class AttentionAction:
    """Handles complete attention score tracking workflow"""
    
    def __init__(self, db: PortfolioDB):
        """Initialize action with database instance"""
        self.db = db
        self.session = requests.Session()
        self._configure_headers()
        self.timeout = 60
        self.max_retries = 3
        self.api_url = "https://app.chainedge.io/attention_score_query/"
    
    def _configure_headers(self):
        """Set up request headers"""
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
            'origin': "https://app.chainedge.io",
            'priority': 'u=1, i',
            'referer': f'https://app.chainedge.io/attention_score/',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
            'x-requested-with': 'XMLHttpRequest'
        }
    
    def persistAttentionDataFromAPI(self, cookie: str) -> Optional[List[AttentionData]]:
        """
        Execute attention score request and process the response
        
        Args:
            cookie: Authentication cookie for the API
            
        Returns:
            Optional[List[AttentionData]]: List of processed attention data or None if failed
        """
        startTime = time.time()
        try:
            # Fetch data from API
            responseJson = self._fetchDataFromAPI(cookie)
            if not responseJson:
                return None
                
            # Log API response structure
            self._logAPIResponseStructure(responseJson)

            # Parse the response
            attentionData = attentionParser.parseAttentionData(responseJson)
            
            if attentionData:
                # Store the data in the database
                self.persistAttentionData(attentionData)
                
                # Log success
                logger.info(f"Successfully processed {len(attentionData)} attention scores at {datetime.now()}")
                executionTime = time.time() - startTime
                logger.info(f"Action completed in {executionTime:.2f} seconds")
                return attentionData
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch attention scores: {str(e)}")
            executionTime = time.time() - startTime
            logger.error(f"Action failed after {executionTime:.2f} seconds")
            return None
    
    def _fetchDataFromAPI(self, cookie: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the API
        
        Args:
            cookie: Authentication cookie for the API
            
        Returns:
            Optional[Dict[str, Any]]: API response as JSON or None if failed
        """
        try:
            response = self.session.post(
                self.api_url,
                headers={**self.headers, 'Cookie': cookie},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return None
    
    def _logAPIResponseStructure(self, responseJson: Dict[str, Any]) -> None:
        """
        Log the structure of the API response for debugging
        
        Args:
            response_json: The API response as JSON
        """
        logger.info(f"Received API response with {len(responseJson.keys())} data keys")
        
        # Log the keys in the response
        dataKeys = [key for key in responseJson.keys() if key.startswith('data')]
        logger.info(f"Data keys in response: {', '.join(dataKeys)}")
        
        # Log sample items from each data key to understand the structure
        for key in dataKeys:
            items = responseJson.get(key, [])
            if items and isinstance(items, list) and len(items) > 0:
                sampleItem = items[0]
                logger.debug(f"Sample item from {key}: {sampleItem.keys() if isinstance(sampleItem, dict) else 'not a dict'}")

    def persistAttentionData(self, items: List[AttentionData]) -> None:
        """
        Process batch of attention data points
        
        Args:
            items: List of attention data items to process
        """
        try:
            for item in items:
                self._processAttentionDataItem(item)
                
        except Exception as e:
            logger.error(f"Failed to process attention data batch: {str(e)}")
    
    def _processAttentionDataItem(self, item: AttentionData) -> None:
        """
        Process a single attention data item
        
        Args:
            item: The attention data item to process
        """
        try:
            logger.info(f"Updating token registry for token: {item.name}")
            self.db.attention.updateTokenRegistry(item)
            
            logger.info(f"Storing raw data for token: {item.name}")
            self.db.attention.storeCurrentAttentionData(item)
            
        except Exception as e:
            logger.error(f"Failed to process attention data item {item.name}: {str(e)}")

    def persistAttentionDataForSolFromAPI(self, cookie: str) -> Optional[List[AttentionData]]:
        """
        Execute attention score request and process the response
        
        Args:
            cookie: Authentication cookie for the API
            
        Returns:
            Optional[List[AttentionData]]: List of processed attention data or None if failed
        """
        startTime = time.time()
        try:
            # Fetch data from API
            responseJson = self._fetchDataForSolFromAPI(cookie)
            if not responseJson:
                return None
                
            # Log API response structure
            self._logAPIResponseStructure(responseJson)

            # Parse the response
            attentionData = attentionParser.parseSolanaAttentionData(responseJson)
            
            if attentionData:
                # Store the data in the database
                self.persistAttentionData(attentionData)
                
                # Log success
                logger.info(f"Successfully processed {len(attentionData)} attention scores at {datetime.now()}")
                executionTime = time.time() - startTime
                logger.info(f"Action completed in {executionTime:.2f} seconds")
                return attentionData
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch attention scores: {str(e)}")
            executionTime = time.time() - startTime
            logger.error(f"Action failed after {executionTime:.2f} seconds")
            return None
        

    def _fetchDataForSolFromAPI(self, cookie: str) -> Optional[Dict[str, Any]]:
        """
        Fetch data from the API
        
        Args:
            cookie: Authentication cookie for the API
            
        Returns:
            Optional[Dict[str, Any]]: API response as JSON or None if failed
        """
        try:
            response = self.session.post(
                "https://app.chainedge.io/attention_score_query_sol/",
                headers={**self.headers, 'Cookie': cookie},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return None
    