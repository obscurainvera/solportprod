from config.Config import get_config
"""
Action to tag portfolio tokens based on defined conditions
"""

from typing import List, Set, Dict
from datetime import datetime, timedelta
import pytz
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import PortfolioSummary, WalletInvestedStatusEnum
from actions.portfolio.PortfolioTagEnum import PortfolioTokenTag
from logs.logger import get_logger

logger = get_logger(__name__)
IST = pytz.timezone('Asia/Kolkata')

class PortfolioTaggerAction:
    """Handles tagging of portfolio tokens"""
    
    def __init__(self, db: PortfolioDB):
        """Initialize with database connection"""
        self.db = db
        self.tagMap = PortfolioTokenTag.getTagMap()
        
    def getCurrentTags(self, token: PortfolioSummary) -> Set[str]:
        """Get current tags for a token from database"""
        try:
            if not token.tags:
                return set()
            return set(token.tags.split(','))
        except Exception as e:
            logger.error(f"Error parsing existing tags for token {token.tokenid}: {str(e)}")
            return set()

    def getWalletData(self, tokenId: str) -> List[Dict]:
        """Get wallet data with PNL for a token"""
        try:
            with self.db.conn_manager.transaction() as cursor:
                query = '''
                    SELECT 
                        wi.walletaddress,
                        wi.totalinvestedamount,
                        wi.amounttakenout,
                        sm.profitandloss as chainedgepnl
                    FROM walletsinvested wi
                    LEFT JOIN smartmoneywallets sm ON wi.walletaddress = sm.walletaddress
                    WHERE wi.tokenid = ? AND wi.status = ?
                '''
                cursor.execute(query, (tokenId,WalletInvestedStatusEnum.ACTIVE.value))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching wallet data for {tokenId}: {str(e)}")
            return []
    
    def separateStaticAndDynamicTags(self, tags: Set[str]) -> Dict[str, Set[str]]:
        """
        Separate static and dynamic tags based on tag format
        
        Args:
            tags: Set of tags to separate
            
        Returns:
            Dict with 'static' and 'dynamic' keys containing respective sets of tags
        """
        staticTags = set()
        dynamicTags = set()
        
        for tag in tags:
            # Dynamic tags start with [ and contain : characters
            if tag.startswith('[') and ':' in tag:
                dynamicTags.add(tag)
            else:
                staticTags.add(tag)
                
        return {
            'static': staticTags,
            'dynamic': dynamicTags
        }
    
    def updateTagsWithPreservingDynamicTags(self, currentTags: Set[str], newStaticTags: Set[str], newDynamicTags: Set[str]) -> Set[str]:
        """
        Update tags while preserving dynamic tags that still apply
        
        Args:
            currentTags: Current tags from the database
            newStaticTags: New static tags from evaluation
            newDynamicTags: New dynamic tags from evaluation
            
        Returns:
            Updated set of tags
        """
        # Separate current tags
        currentSeparated = self.separateStaticAndDynamicTags(currentTags)
        
        # Keep all new tags
        updatedTags = newStaticTags.union(newDynamicTags)
        
        return updatedTags
            
    def evaluateNewTags(self, token: PortfolioSummary) -> Set[str]:
        """Evaluate and get new tags for a token"""
        try:
            # Get wallet data once
            walletData = self.getWalletData(token.tokenid)
            
            # Evaluate all tags with the wallet data
            newTags = set()
            for tagName, checkFunc in self.tagMap.items():
                try:
                    result = checkFunc(token, self.db, walletData)
                    if isinstance(result, set):
                        newTags.update(result)
                    elif result:  # Boolean result
                        newTags.add(tagName)
                except Exception as e:
                    logger.error(f"Error evaluating tag {tagName} for token {token.tokenid}: {str(e)}")
                    continue
            return newTags
        except Exception as e:
            logger.error(f"Error evaluating tags for token {token.tokenid}: {str(e)}")
            return set()

    def addTagsToActivePortSummaryTokens(self) -> bool:
        """
        Tag all active portfolio tokens from the last 24 hours
        
        Returns:
            bool: Success status
        """
        try:
            # Get active tokens from last 24 hours using IST
            oneDayAgo = datetime.now(IST) - timedelta(days=1)
            activeTokens = self.db.portfolio.getActiveTokensSince(oneDayAgo)
            
            if not activeTokens:
                logger.info("No active tokens found for tagging")
                return True
                
            logger.info(f"Found {len(activeTokens)} active tokens to process")
            
            with self.db.transaction() as cursor:
                for token in activeTokens:
                    try:
                        result = self.evaluateAndUpdateTokenTags(token, cursor)
                        if result['tagsChanged']:
                            logger.info(f"Updated tags for token {token.tokenid}")
                        else:
                            logger.debug(f"No tag changes for token {token.tokenid}")
                    except Exception as e:
                        logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
                        continue
                        
            return True
            
        except Exception as e:
            logger.error(f"Token tagging failed: {str(e)}")
            return False

    def evaluateAndUpdateTokenTags(self, token, cursor=None) -> dict:
        """
        Evaluate and update tags for a specific token
        
        Args:
            token: Token to evaluate and update tags for
            cursor: Optional database cursor for transaction
            
        Returns:
            dict: Result of tag evaluation and update
        """
        try:
            # Get current tags
            currentTags = self.getCurrentTags(token)
            
            # Evaluate new tags
            newTags = self.evaluateNewTags(token)
            
            # Separate tags by type
            currentSeparated = self.separateStaticAndDynamicTags(currentTags)
            newSeparated = self.separateStaticAndDynamicTags(newTags)
            
            # Calculate effective tags set (all new tags)
            effectiveTags = newTags
            
            # Flag to track changes
            tagsChanged = effectiveTags != currentTags
            
            result = {
                'tokenId': token.tokenid,
                'currentTags': list(currentTags),
                'newTags': list(newTags),
                'tagsChanged': tagsChanged,
                'updated': False
            }
            
            # Compare tags
            if tagsChanged:
                logger.info(f"Tags changed for token {token.tokenid}")
                logger.info(f"Old tags: {currentTags}")
                logger.info(f"New tags: {newTags}")
                
                # Use transaction if cursor provided, otherwise create new one
                with self.db.transaction() as cur:
                    cursor = cursor or cur
                    
                    # First, persist current state to history
                    self.db.portfolio.insertHistory(token, cursor)
                    
                    # Update tags in main table with IST timestamp
                    tags = ','.join(sorted(effectiveTags)) if effectiveTags else ''
                    currentTime = datetime.now(IST)
                    self.db.portfolio.updateTokenTags(cursor, token.tokenid, tags, currentTime)
                    
                    result['updated'] = True
                    logger.info(f"Updated token {token.tokenid} with new tags at {currentTime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                logger.debug(f"No tag changes for token {token.tokenid}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
            raise