from config.Config import get_config
from enum import Enum, auto

class SourceType(Enum):
    """Enum for different data sources"""
    
    # Token Discovery Sources
    ATTENTION = "ATTENTION"         # Attention and momentum tracking
    PORTSUMMARY = "PORTSUMMARY"     # Portfolio and wallet analysis
    VOLUME = "VOLUME"               # Volume and liquidity tracking
    PUMPFUN = "PUMPFUN"            # Pump and meme detection
    SMARTMONEY = "SMARTMONEY"       # Smart money tracking
    
    # Market Data Sources
    DEX = "DEX"                     # Decentralized exchange data
    CEX = "CEX"                     # Centralized exchange data
    AGGREGATOR = "AGGREGATOR"       # Data aggregator feeds
    
    # Social Sources
    TWITTER = "TWITTER"             # Twitter/X social data
    TELEGRAM = "TELEGRAM"           # Telegram group data
    DISCORD = "DISCORD"             # Discord community data
    
    # On-chain Sources
    BLOCKCHAIN = "BLOCKCHAIN"       # Direct blockchain data
    MEMPOOL = "MEMPOOL"            # Mempool transaction data
    NFT = "NFT"                    # NFT marketplace data
    
    # Analysis Sources
    TECHNICAL = "TECHNICAL"         # Technical analysis
    FUNDAMENTAL = "FUNDAMENTAL"     # Fundamental analysis
    SENTIMENT = "SENTIMENT"         # Market sentiment analysis
    
    @classmethod
    def get_discovery_sources(cls) -> list:
        """Get list of token discovery sources"""
        return [
            cls.ATTENTION,
            cls.PORTSUMMARY,
            cls.VOLUME,
            cls.PUMPFUN,
            cls.SMARTMONEY
        ]
    
    @classmethod
    def get_market_sources(cls) -> list:
        """Get list of market data sources"""
        return [
            cls.DEX,
            cls.CEX,
            cls.AGGREGATOR
        ]
    
    @classmethod
    def get_social_sources(cls) -> list:
        """Get list of social data sources"""
        return [
            cls.TWITTER,
            cls.TELEGRAM,
            cls.DISCORD
        ]
    
    @classmethod
    def get_onchain_sources(cls) -> list:
        """Get list of on-chain data sources"""
        return [
            cls.BLOCKCHAIN,
            cls.MEMPOOL,
            cls.NFT
        ]
    
    @classmethod
    def get_analysis_sources(cls) -> list:
        """Get list of analysis sources"""
        return [
            cls.TECHNICAL,
            cls.FUNDAMENTAL,
            cls.SENTIMENT
        ]
    
    @classmethod
    def isValidSource(cls, source: str) -> bool:
        """Check if a source type is valid"""
        try:
            return bool(cls(source))
        except ValueError:
            return False
    
    def __str__(self) -> str:
        return self.value 