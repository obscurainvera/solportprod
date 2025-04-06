from config.Config import get_config
from enum import Enum
from decimal import Decimal
from typing import Optional, Set, Callable, Dict, List, Tuple
from database.operations.PortfolioDB import PortfolioDB
from database.operations.schema import PortfolioSummary, WalletsInvested, SmartMoneyWallet
from logs.logger import get_logger
from dataclasses import dataclass

logger = get_logger(__name__)

# Type hint for condition functions
TagCondition = Callable[[PortfolioSummary, PortfolioDB, Optional[List[Dict]]], Set[str]]

@dataclass
class WalletMetrics:
    """Helper class to store wallet metrics"""
    chainedgePnl: Decimal
    totalInvested: Decimal
    totalTakenOut: Decimal
    walletAddress: str

class PortfolioTokenTag(Enum):
    """Enum to add necessary tags to portfolio tokens"""

    def _checkBalance100k(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if smart balance is greater than 100K"""
        try:
            return (token.smartbalance is not None and
                    Decimal(token.smartbalance) > Decimal('100000'))
        except Exception as e:
            logger.error(f"Error checking balance 100k for {token.tokenid}: {str(e)}")
            return False

    def _checkBalance500k(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if smart balance is greater than 500K"""
        try:
            return (token.smartbalance is not None and
                    Decimal(token.smartbalance) > Decimal('500000'))
        except Exception as e:
            logger.error(f"Error checking balance 500k for {token.tokenid}: {str(e)}")
            return False

    def _checkBalance1m(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if smart balance is greater than 1M"""
        try:
            return (token.smartbalance is not None and
                    Decimal(token.smartbalance) > Decimal('1000000'))
        except Exception as e:
            logger.error(f"Error checking balance 1M for {token.tokenid}: {str(e)}")
            return False
    
    def _checkHuge1dChange(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if 1d change is beyond ±20%"""
        try:
            return (token.qtychange1d is not None and
                    abs(Decimal(token.qtychange1d)) > Decimal('20'))
        except Exception as e:
            logger.error(f"Error checking 1d change for {token.tokenid}: {str(e)}")
            return False

    def _checkHuge7dChange(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if 7d change is beyond ±20%"""
        try:
            return (token.qtychange7d is not None and
                    abs(Decimal(token.qtychange7d)) > Decimal('20'))
        except Exception as e:
            logger.error(f"Error checking 7d change for {token.tokenid}: {str(e)}")
            return False

    def _checkHuge30dChange(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if 30d change is beyond ±20%"""
        try:
            return (token.qtychange30d is not None and
                    abs(Decimal(token.qtychange30d)) > Decimal('20'))
        except Exception as e:
            logger.error(f"Error checking 30d change for {token.tokenid}: {str(e)}")
            return False

    def _checkPriceWithinRange(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if current price is within 20% increase or decrease of avg price"""
        try:
            return (token.currentprice is not None and
                    token.avgprice is not None and
                    Decimal(token.currentprice) <= Decimal(token.avgprice) * Decimal('1.20') and
                    Decimal(token.currentprice) >= Decimal(token.avgprice) * Decimal('0.80'))
        except Exception as e:
            logger.error(f"Error checking price range for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap0To1m(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 0-1M"""
        try:
            return (token.mcap is not None and
                    Decimal('0') <= Decimal(token.mcap) < Decimal('1000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 0-1M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap1mTo10m(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 1M-10M"""
        try:
            return (token.mcap is not None and
                    Decimal('1000000') <= Decimal(token.mcap) < Decimal('10000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 1M-10M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap10mTo50m(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 10M-50M"""
        try:
            return (token.mcap is not None and
                    Decimal('10000000') <= Decimal(token.mcap) < Decimal('50000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 10M-50M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap50mTo100m(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 50M-100M"""
        try:
            return (token.mcap is not None and
                    Decimal('50000000') <= Decimal(token.mcap) < Decimal('100000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 50M-100M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcapAbove100m(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is above 100M"""
        try:
            return (token.mcap is not None and
                    Decimal(token.mcap) >= Decimal('100000000'))
        except Exception as e:
            logger.error(f"Error checking mcap above 100M for {token.tokenid}: {str(e)}")
            return False

    def _getSmartWalletsCount(token: PortfolioSummary, db: PortfolioDB,
                             minPnl: Decimal, minInvestment: Decimal,
                             walletData: List[Dict]) -> int:
        """Helper function to count smart wallets meeting criteria"""
        try:
            if not walletData:
                return 0
                
            smartWallets = 0
            for wallet in walletData:
                try:
                    # Check PNL from smartmoneywallets table
                    if wallet['chainedgepnl'] is None or Decimal(str(wallet['chainedgepnl'])) < minPnl:
                        continue
                        
                    # Calculate net investment from walletsinvested table
                    # Handle cases where values might be None, null, or 0
                    invested = Decimal('0')
                    if wallet.get('totalinvestedamount') is not None and wallet['totalinvestedamount'] != '':
                        invested = Decimal(str(wallet['totalinvestedamount']))
                    
                    takenOut = Decimal('0')
                    if wallet.get('amounttakenout') is not None and wallet['amounttakenout'] != '':
                        takenOut = Decimal(str(wallet['amounttakenout']))
                    
                    netInvestment = invested - takenOut
                    
                    if netInvestment >= minInvestment:
                        smartWallets += 1
                        
                except Exception as e:
                    # Catch all exceptions to ensure processing continues
                    logger.error(f"Error processing wallet {wallet.get('walletaddress', 'unknown')}: {str(e)}")
                    continue
                    
            return smartWallets
            
        except Exception as e:
            logger.error(f"Error getting smart wallets for {token.tokenid}: {str(e)}")
            return 0

    def _check300kTo10k(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Check smart wallets with >300K PNL and >10K investment"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getSmartWalletsCount(
                token, db,
                minPnl=Decimal('300000'),
                minInvestment=Decimal('10000'),
                walletData=walletData
            )
            
            if walletCount >= 3:
                return {"SMART_300K_10K_3"}
            elif walletCount >= 2:
                return {"SMART_300K_10K_2"}
            elif walletCount >= 1:
                return {"SMART_300K_10K_1"}
            return set()
        except Exception as e:
            logger.error(f"Error checking 300K/10K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _check500kTo30k(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Check smart wallets with >500K PNL and >30K investment"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getSmartWalletsCount(
                token, db,
                minPnl=Decimal('500000'),
                minInvestment=Decimal('30000'),
                walletData=walletData
            )
            
            if walletCount >= 3:
                return {"SMART_500K_30K_3"}
            elif walletCount >= 2:
                return {"SMART_500K_30K_2"}
            elif walletCount >= 1:
                return {"SMART_500K_30K_1"}
            return set()
        except Exception as e:
            logger.error(f"Error checking 500K/30K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _check1mTo100k(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Check smart wallets with >1M PNL and >100K investment"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getSmartWalletsCount(
                token, db,
                minPnl=Decimal('1000000'),
                minInvestment=Decimal('100000'),
                walletData=walletData
            )
            
            if walletCount >= 3:
                return {"SMART_1M_100K_3"}
            elif walletCount >= 2:
                return {"SMART_1M_100K_2"}
            elif walletCount >= 1:
                return {"SMART_1M_100K_1"}
            return set()
        except Exception as e:
            logger.error(f"Error checking 1M/100K wallets for {token.tokenid}: {str(e)}")
            return set()

    @staticmethod
    def _formatAmount(amount: Decimal) -> str:
        """Format amount with appropriate unit (K, M, B) based on magnitude"""
        if amount >= Decimal('1000000000'):  # Billions
            return f"{int(amount / 1000000000)}B"
        elif amount >= Decimal('1000000'):  # Millions
            return f"{int(amount / 1000000)}M"
        else:  # Thousands or less
            # Round to nearest K
            k_value = int(amount / 1000)
            return f"{k_value}K"

    @staticmethod
    def _generateDynamicPnlTags(token: PortfolioSummary, db: PortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Generate dynamic tags based on PNL ranges and investment amounts"""
        try:
            if not walletData:
                return set()
                
            # Define PNL ranges
            pnlRanges = [
                (Decimal('0'), Decimal('300000'), "0-300K"),
                (Decimal('300000'), Decimal('500000'), "300K-500K"),
                (Decimal('500000'), Decimal('1000000'), "500K-1M"),
                (Decimal('1000000'), None, ">1M")
            ]
            
            # Define minimum investment threshold to consider (1000 = 1K)
            MIN_INVESTMENT_THRESHOLD = Decimal('1000')
            
            # Initialize data structure to hold wallet metrics by PNL range
            rangeStats = {}
            for minPnl, maxPnl, label in pnlRanges:
                rangeStats[label] = {
                    'all': {
                        'wallets': [],
                        'total_invested': Decimal('0'),
                        'count': 0
                    },
                    'filtered': {
                        'wallets': [],
                        'investments': [],
                        'total_invested': Decimal('0'),
                        'count': 0
                    }
                }
            
            # Single pass through wallet data
            for wallet in walletData:
                # Skip if no PNL data
                if wallet.get('chainedgepnl') is None:
                    continue
                    
                pnl = Decimal(str(wallet['chainedgepnl']))
                
                # Calculate investment values
                invested = Decimal('0')
                if wallet.get('totalinvestedamount') is not None and wallet['totalinvestedamount'] != '':
                    invested = Decimal(str(wallet['totalinvestedamount']))
                
                takenOut = Decimal('0')
                if wallet.get('amounttakenout') is not None and wallet['amounttakenout'] != '':
                    takenOut = Decimal(str(wallet['amounttakenout']))
                
                # Skip wallets with no investment
                if invested <= Decimal('0'):
                    logger.debug(f"Skipping wallet {wallet.get('walletaddress', 'unknown')} - zero investment")
                    continue
                
                # Check which PNL range this wallet belongs to
                for minPnl, maxPnl, label in pnlRanges:
                    if pnl < minPnl:
                        continue
                    if maxPnl is not None and pnl >= maxPnl:
                        continue
                    
                    # This wallet belongs to this PNL range
                    wallet_data = {
                        'walletAddress': wallet.get('walletaddress'),
                        'pnl': pnl,
                        'invested': invested,
                        'takenOut': takenOut
                    }
                    
                    # Add to all wallets for this range
                    rangeStats[label]['all']['wallets'].append(wallet_data)
                    rangeStats[label]['all']['total_invested'] += invested
                    rangeStats[label]['all']['count'] += 1
                    
                    # Check if this wallet should be in filtered set
                    # (hasn't taken out more than 50% of invested amount)
                    if takenOut <= invested * Decimal('0.5'):
                        rangeStats[label]['filtered']['wallets'].append(wallet_data)
                        rangeStats[label]['filtered']['investments'].append(invested)
                        rangeStats[label]['filtered']['total_invested'] += invested
                        rangeStats[label]['filtered']['count'] += 1
                    
                    # We found the right range, so break the loop
                    break
            
            # Generate tags from collected data
            dynamicTags = set()
            
            for label, stats in rangeStats.items():
                # Format 2 tag for all wallets (unfiltered)
                # Skip if total invested is below threshold or there are no wallets
                if stats['all']['count'] == 0 or stats['all']['total_invested'] < MIN_INVESTMENT_THRESHOLD:
                    logger.debug(f"Skipping Format 2 tag for {label} - no wallets or investment below threshold: {stats['all']['total_invested']}")
                    continue
                
                totalFormatted = PortfolioTokenTag._formatAmount(stats['all']['total_invested'])
                
                # Double check that the formatted amount isn't "0K"
                if totalFormatted == "0K":
                    logger.debug(f"Skipping Format 2 tag for {label} - total formatted as 0K despite being {stats['all']['total_invested']}")
                    continue
                    
                walletCount = stats['all']['count']
                format2Tag = f"[PNL : {label}]- [T : {totalFormatted}]- [W : {walletCount}]"
                dynamicTags.add(format2Tag)
                
                # Format 1 tag for filtered wallets
                # Skip if total invested is below threshold or there are no wallets
                if stats['filtered']['count'] == 0 or stats['filtered']['total_invested'] < MIN_INVESTMENT_THRESHOLD:
                    logger.debug(f"Skipping Format 1 tag for {label} - no filtered wallets or investment below threshold: {stats['filtered']['total_invested']}")
                    continue
                
                investments = stats['filtered']['investments']
                if not investments:
                    logger.debug(f"Skipping Format 1 tag for {label} - empty investments list")
                    continue
                    
                minInvestment = min(investments)
                maxInvestment = max(investments)
                avgInvestment = sum(investments) / len(investments)
                totalInvestment = stats['filtered']['total_invested']
                
                # Skip if individual metrics are too small (would show as 0K)
                if minInvestment < MIN_INVESTMENT_THRESHOLD or maxInvestment < MIN_INVESTMENT_THRESHOLD or avgInvestment < MIN_INVESTMENT_THRESHOLD:
                    logger.debug(f"Skipping Format 1 tag for {label} - some metrics below threshold: min={minInvestment}, max={maxInvestment}, avg={avgInvestment}")
                    continue
                    
                # Format with appropriate units
                minFormatted = PortfolioTokenTag._formatAmount(minInvestment)
                maxFormatted = PortfolioTokenTag._formatAmount(maxInvestment)
                avgFormatted = PortfolioTokenTag._formatAmount(avgInvestment)
                totalFormatted = PortfolioTokenTag._formatAmount(totalInvestment)
                
                # Double check none of the formatted values are "0K"
                if "0K" in [minFormatted, maxFormatted, avgFormatted, totalFormatted]:
                    logger.debug(f"Skipping Format 1 tag for {label} - some values formatted as 0K: min={minFormatted}, max={maxFormatted}, avg={avgFormatted}, total={totalFormatted}")
                    continue
                
                format1Tag = f"[PNL : {label}]-[{minFormatted} - {maxFormatted}]-[Avg : {avgFormatted}]-[T : {totalFormatted}]-[W : {len(investments)}]"
                dynamicTags.add(format1Tag)
            
            return dynamicTags
                
        except Exception as e:
            logger.error(f"Error generating dynamic PNL tags for {token.tokenid}: {str(e)}")
            return set()

    # Balance tags
    BALANCE_100K = ("BALANCE_100K", _checkBalance100k)
    BALANCE_500K = ("BALANCE_500K", _checkBalance500k)
    BALANCE_1M = ("BALANCE_1M", _checkBalance1m)
    
    # Price change tags
    HUGE_1D_CHANGE = ("HUGE_1D_CHANGE", _checkHuge1dChange)
    HUGE_7D_CHANGE = ("HUGE_7D_CHANGE", _checkHuge7dChange)
    HUGE_30D_CHANGE = ("HUGE_30D_CHANGE", _checkHuge30dChange)
    PRICE_WITHIN_RANGE = ("PRICE_WITHIN_RANGE", _checkPriceWithinRange)
    
    # Market cap range tags
    MCAP_0_1M = ("MCAP_0_1M", _checkMcap0To1m)
    MCAP_1M_10M = ("MCAP_1M_10M", _checkMcap1mTo10m)
    MCAP_10M_50M = ("MCAP_10M_50M", _checkMcap10mTo50m)
    MCAP_50M_100M = ("MCAP_50M_100M", _checkMcap50mTo100m)
    MCAP_ABOVE_100M = ("MCAP_ABOVE_100M", _checkMcapAbove100m)

    # Smart wallet investment tags
    SMART_300K_10K = ("SMART_300K_10K", _check300kTo10k)
    SMART_500K_30K = ("SMART_500K_30K", _check500kTo30k)
    SMART_1M_100K = ("SMART_1M_100K", _check1mTo100k)
    
    # Add the dynamic tag generator to the enum
    DYNAMIC_PNL_TAGS = ("DYNAMIC_PNL_TAGS", _generateDynamicPnlTags)

    def __init__(self, tagName: str, conditionFunc: TagCondition):
        self.tagName = tagName
        self.conditionFunc = conditionFunc

    @classmethod
    def getTagMap(cls) -> Dict[str, TagCondition]:
        """Get mapping of all tags to their condition functions"""
        return {tag.tagName: tag.conditionFunc for tag in cls}

    def __str__(self) -> str:
        return self.tagName
        
    @classmethod
    def getAllTags(cls) -> List[str]:
        """Get list of all tag values"""
        return [tag.tagName for tag in cls]