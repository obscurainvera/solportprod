from config.Config import get_config
"""
Takes all the tokens in portfolio summary and stores them in portfolio_summary table and
in case of duplicate tokens, it updates the record and records the history
in the history table
"""

from typing import Optional, Dict, Any, List, Union, Set
from actions.portfolio.PortfolioTagEnum import PortfolioTokenTag
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import PortfolioSummary
import logging
import parsers.PortSummaryParser as PortSummaryParser
import requests
from config.Security import COOKIE_MAP, isValidCookie
from config.PortfolioStatusEnum import PortfolioStatus
from decimal import Decimal
import time
from datetime import datetime
from logs.logger import get_logger
from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from framework.analyticsframework.enums.SourceTypeEnum import SourceType    

logger = get_logger(__name__)

class PortfolioSummaryAction:
    """Handles complete portfolio summary request workflow"""
    
    def __init__(self, db: PortfolioDB):
        """
        Initialize action with required security parameters
        Args:
            db: Database handler for authentication
        """
        self.db = db
        self.session = requests.Session()
        self._configureHeaders()
        self.timeout = 60
        self.maxRetries = 3

    def _configureHeaders(self):
        """Set headers from endpoint configuration"""
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': "https://app.chainedge.io",
            'Priority ': 'u=1, i',
            'Referer': "https://app.chainedge.io/portfolio_summary/",
            'Sec-Ch-Ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'X-Requested-With': 'XMLHttpRequest'
        }

    def getPortfolioSummaryAPIData(self, cookie: str, marketAge: list, pnlWallet: int, ownership: int) -> Dict[str, Any]:
        """
        Execute portfolio request with retry on failure
        
        Args:
            cookie: Authentication cookie
            marketAge: Market age category
            pnlWallet: PNL wallet threshold
            ownership: Ownership threshold
            
        Returns:
            Dict[str, Any]: Dictionary containing token IDs and persistence statistics
        """
        startTime = time.time()
        try:
            payload = self._buildPayload(marketAge, pnlWallet, ownership)
            
            response = self.session.post(
                'https://app.chainedge.io/god_portfoliojson/',
                headers={**self.headers, 'Cookie': cookie},
                data=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")

            parsedItems = PortSummaryParser.parsePortSummaryAPIResponse(response.json())
            
            if parsedItems:
                # Process tokens and return stats and token IDs
                stats = self.processPortfolioTokens(parsedItems, marketAge)
                
                logger.debug(f"Successfully processed {len(parsedItems)} items")
                executionTime = time.time() - startTime
                logger.debug(f"Action completed in {executionTime:.2f} seconds for market age {marketAge}")
                return stats
            else:
                logger.warning(f"\nNo valid items to persist\nMarket Age: {marketAge}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                executionTime = time.time() - startTime
                logger.debug(f"Action completed in {executionTime:.2f} seconds for market age {marketAge}")
                return {"tokenIds": [], "processed": 0, "inserted": 0, "updated": 0, "reactivated": 0}
                
        except (requests.RequestException, ValueError) as e:
            # Only retry on request/response errors
            for attempt in range(1, self.maxRetries):
                logger.error(f"Request failed (attempt {attempt}/{self.maxRetries}): {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
                try:
                    response = self.session.post(
                        'https://app.chainedge.io/god_portfoliojson/',
                        headers={**self.headers, 'Cookie': cookie},
                        data=payload,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    
                    if not response.content:
                        continue  # Try next attempt if empty response
                        
                    parsedItems = PortSummaryParser.parsePortSummaryAPIResponse(response.json())
                    if parsedItems:
                        # Process tokens and return stats and token IDs
                        stats = self.processPortfolioTokens(parsedItems, marketAge)
                        
                        logger.info(f"Successfully processed {len(parsedItems)} items on retry {attempt}")
                        execution_time = time.time() - startTime
                        logger.info(f"Action completed in {execution_time:.2f} seconds for market age {marketAge}")
                        return stats
                        
                except Exception as retry_error:
                    logger.error(f"Retry failed: {str(retry_error)}")
                    continue
                    
            logger.error("All retry attempts failed")
            execution_time = time.time() - startTime
            logger.error(f"Action failed after {execution_time:.2f} seconds: {str(e)}")
            return {"tokenIds": [], "processed": 0, "inserted": 0, "updated": 0, "reactivated": 0}
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            execution_time = time.time() - startTime
            logger.error(f"Action failed after {execution_time:.2f} seconds: {str(e)}")
            return {"tokenIds": [], "processed": 0, "inserted": 0, "updated": 0, "reactivated": 0}

    def processPortfolioTokens(self, items: List[PortfolioSummary], marketAge: list) -> Dict[str, Any]:
        """
        Process portfolio tokens by persisting them to the database
        
        Args:
            items: List of portfolio summary objects to process
            marketAge: Market age filter used for this API call
            
        Returns:
            Dict[str, Any]: Dictionary containing token IDs and persistence statistics
        """
        try:
            # Get token IDs from the items
            tokenIds = [item.tokenid for item in items]
            
            # Persist tokens to the database
            stats = self.persistPortfolioSummaryData(items, marketAge)
            
            logger.info(f"Portfolio tokens processed for market age {marketAge}. "
                      f"Updated: {stats['updated']}, "
                      f"Inserted: {stats['inserted']}, "
                      f"Reactivated: {stats['reactivated']}")
            
            # Return the dictionary containing token IDs and persistence statistics
            return stats
                
        except Exception as e:
            logger.error(f"Error in processing portfolio tokens: {str(e)}", exc_info=True)
            return {"tokenIds": [], "processed": 0, "inserted": 0, "updated": 0, "reactivated": 0}

    def markInactiveTokens(self, receivedTokenIds: List[str]) -> int:
        """
        Mark tokens as inactive that were not found in any API response
        
        Args:
            receivedTokenIds: List of token IDs received from all API calls
            
        Returns:
            int: Number of tokens marked as inactive
        """
        try:
            # Get all active tokens from the database
            activeTokens = self.db.portfolio.getActivePortfolioTokens()
            activeTokenIds = {token['tokenid'] for token in activeTokens}
            
            # Convert received tokens to a set for faster comparison
            receivedTokenIdSet = set(receivedTokenIds)
            
            # Find tokens that are in the database but not in any response
            tokensToMarkInactive = activeTokenIds - receivedTokenIdSet
            
            affectedCount = 0
            if tokensToMarkInactive:
                affectedCount = self.db.portfolio.markTokensInactiveDuringUpdate(tokensToMarkInactive)
                
            logger.info(f"Completed marking inactive tokens. "
                      f"Tokens in database: {len(activeTokenIds)}, "
                      f"Tokens from API: {len(receivedTokenIdSet)}, "
                      f"Marked inactive: {affectedCount}")
            
            return affectedCount
            
        except Exception as e:
            logger.error(f"Error marking inactive tokens: {str(e)}", exc_info=True)
            return 0

    def _buildPayload(self, marketAge: list, pnlWallet: int, ownership: int) -> Dict[str, str]:
        """
        Construct payload with dynamic parameters
        
        Args:
            marketAge (List[str]): List of market age ranges
            pnlWallet (Union[int, float, Decimal]): PNL wallet threshold value
            ownership (Union[int, float, Decimal]): Ownership threshold value
        """
        # Base payload structure
        payload = {
            'draw': '4',
            'start': '0',
            'length': '40',
            'search[value]': '',
            'search[regex]': 'false',
            'solana': '1',
            'portfolio_topfilter_id': '1000',
            'order[0][column]': '1',
            'order[0][dir]': 'desc',
            'market_age': str(marketAge),
            'pnl_wallet': str(float(pnlWallet)),
            'ownership': str(float(ownership))
        }

        # Add column configurations
        columns = [
            {'data': 'name', 'orderable': 'false'},
            {'data': 'smart_balance', 'orderable': 'true'},
            {'data': 'd1_chg_pct', 'orderable': 'true'},
            {'data': 'd7_chg_pct', 'orderable': 'true'},
            {'data': 'd30_chg_pct', 'orderable': 'true'},
            {'data': 'avg_buy_price', 'orderable': 'true'},
            {'data': 'price_1h', 'orderable': 'false'},
            {'data': 'fdv_or_mcap', 'orderable': 'false'},
            {'data': 'liquidity', 'orderable': 'false'},
            {'data': 'tokenagetoday', 'orderable': 'true'},
            {'data': 'w_countgrt_1000', 'orderable': 'true'},
            {'data': 'w_countgrt_5000', 'orderable': 'true'},
            {'data': 'w_countgrt_10000', 'orderable': 'true'},
            {'data': 'change_pct_1h', 'orderable': 'false'},
            {'data': 'change_pct_30d', 'orderable': 'false'},
            {'data': 'change_pct_24h', 'orderable': 'false'},
            {'data': 'volume24', 'orderable': 'false'}
        ]

        for i, col in enumerate(columns):
            payload[f'columns[{i}][data]'] = col['data']
            payload[f'columns[{i}][name]'] = ''
            payload[f'columns[{i}][searchable]'] = 'true'
            payload[f'columns[{i}][orderable]'] = col['orderable']
            payload[f'columns[{i}][search][value]'] = ''
            payload[f'columns[{i}][search][regex]'] = 'false'

        return payload

    def persistPortfolioSummaryData(self, items: List[PortfolioSummary], marketAge: list) -> Dict[str, Any]:
        """
        Persist portfolio items to database
        
        Args:
            items: List of PortfolioSummary objects to persist
            marketAge: Market age filter used
            
        Returns:
            Dict: Stats about the operation including token IDs and counts
        """
        if not items:
            logger.warning(f"No items to persist for market age {marketAge}")
            return {"tokenIds": [], "processed": 0, "updated": 0, "inserted": 0, "reactivated": 0}
            
        try:
            tokenIds = [item.tokenid for item in items]
            existingRecords = self.db.portfolio.getTokenData(tokenIds)
            existingMap = {record.tokenid: record for record in existingRecords}
            currentTime = datetime.now()
            
            updatedCount = 0
            insertedCount = 0
            reactivatedCount = 0

            with self.db.transaction() as cursor:
                for item in items:
                    try:
                        # Ensure status is set to ACTIVE
                        item.status = PortfolioStatus.ACTIVE.statuscode
                        
                        # Ensure createdat and updatedat are set
                        if not hasattr(item, 'createdat') or item.createdat is None:
                            item.createdat = currentTime
                        if not hasattr(item, 'updatedat') or item.updatedat is None:
                            item.updatedat = currentTime
                        
                        if item.tokenid in existingMap:
                            # Insert history record first
                            existingItem = existingMap[item.tokenid]
                            
                            # Check if we're reactivating an inactive token
                            wasInactive = hasattr(existingItem, 'status') and existingItem.status != PortfolioStatus.ACTIVE.statuscode
                            
                            # Preserve original createdat from existing record
                            if hasattr(existingItem, 'createdat') and existingItem.createdat is not None:
                                item.createdat = existingItem.createdat
                                
                            self.db.portfolio.insertHistory(existingItem, cursor)
                            
                            # Then update current record
                            self.db.portfolio.updateSummary(item, cursor)
                            
                            if wasInactive:
                                reactivatedCount += 1
                                logger.info(f"Reactivated existing record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {marketAge}")
                            else:
                                updatedCount += 1
                                logger.info(f"Updated existing record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {marketAge}")
                        else:
                            # Insert new record
                            self.db.portfolio.insertSummary(item, cursor)
                            insertedCount += 1
                            logger.info(f"Inserted new record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {marketAge}")
                    except Exception as e:
                        logger.error(f"Failed to persist item {item.tokenid} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {marketAge}: {str(e)}")
                        raise

            logger.info(f"Successfully persisted {len(items)} items (updated: {updatedCount}, inserted: {insertedCount}, reactivated: {reactivatedCount}) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {marketAge}")
            return {
                "tokenIds": tokenIds,
                "processed": len(items),
                "updated": updatedCount, 
                "inserted": insertedCount, 
                "reactivated": reactivatedCount
            }
            
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise
        
    def pushPortSummaryTokensToStrategyFramework(self):
        """
        Pushes the portfolio summary tokens to the strategy framework
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
    
            # Initialize analytics handler and push token API
            pushTokenApi = PushTokenAPI()
            
            # Use the pushAllPortSummaryTokens method directly
            success, stats = pushTokenApi.pushAllPortSummaryTokens()
            
            if success:
                logger.info(f"Successfully pushed {stats['success']}/{stats['total']} tokens to strategy framework")
                return True
            else:
                logger.warning(f"Failed to push tokens to strategy framework. Stats: {stats}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to push portfolio summary tokens to strategy framework: {str(e)}", exc_info=True)
            return False
