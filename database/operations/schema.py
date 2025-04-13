from config.Config import get_config
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal
from database.smartmoneywallets.WalletPNLStatusEnum import SmartWalletPnlStatus
from database.smartmoneywallets.TopTokenPNLStatusEnum import TokenStatus
from framework.notificationframework.NotificationEnums import (
    NotificationSource,
    ChatGroup,
    NotificationStatus,
)
from enum import IntEnum, Enum


@dataclass
class PortfolioSummary:
    # Required fields
    chainname: str
    tokenid: str
    name: str
    tokenage: str
    mcap: Decimal
    currentprice: Decimal
    avgprice: Decimal
    smartbalance: Decimal
    walletsinvesting1000: int
    walletsinvesting5000: int
    walletsinvesting10000: int
    qtychange1d: Decimal
    qtychange7d: Decimal
    qtychange30d: Decimal
    markedinactive: bool = False  # Added with default value False

    # Optional fields
    portsummaryid: Optional[int] = None
    status: int = 1
    firstseen: Optional[datetime] = None  # Changed from firstSeen to match column name
    lastseen: Optional[datetime] = None  # Changed from lastSeen to match column name
    createdat: Optional[datetime] = None
    updatedat: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class PortfolioHistory:
    """Historical record of portfolio changes"""

    # Required fields
    portsummaryid: int
    tokenid: str
    chainname: str
    name: str
    tokenage: str
    mcap: Decimal
    currentprice: Decimal
    avgprice: Decimal
    smartbalance: Decimal
    walletsinvesting1000: int
    walletsinvesting5000: int
    walletsinvesting10000: int
    qtychange1d: Decimal
    qtychange7d: Decimal
    qtychange30d: Decimal

    # Optional fields
    historyid: Optional[int] = None
    status: int = 1
    createdat: Optional[datetime] = None  # Changed from createdtime
    updatedat: Optional[datetime] = None  # Changed from updatedtime
    tags: List[str] = field(default_factory=list)


@dataclass
class WalletsInvested:
    """
    Represents token-specific analysis data for each wallet
    Links to portfolio summary through portsummaryid and tokenid
    """

    # Required fields
    portsummaryid: int
    tokenid: str
    walletaddress: str
    walletname: str
    coinquantity: Decimal
    smartholding: Decimal
    firstbuytime: datetime
    totalinvestedamount: Decimal
    amounttakenout: Decimal
    totalcoins: Decimal

    # Optional fields
    walletinvestedid: Optional[int] = None  # Changed from analysisid
    qtychange1d: Optional[Decimal] = None
    qtychange7d: Optional[Decimal] = None
    avgentry: Optional[Decimal] = None
    chainedgepnl: Optional[Decimal] = None
    tags: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    createdat: Optional[datetime] = None  # Changed from createdtime
    updatedat: Optional[datetime] = None  # Changed from updatedtime
    status: int = 1  # Default holding status


@dataclass
class SmartMoneyWallet:
    """Smart money wallet data structure"""

    walletaddress: str
    profitandloss: Decimal
    tradecount: int

    # Optional fields
    id: Optional[int] = None
    status: int = SmartWalletPnlStatus.LOW_PNL_SM.value
    firstseen: Optional[datetime] = None  # Changed from firstSeen to match column name
    lastseen: Optional[datetime] = None  # Changed from lastSeen to match column name
    createdtime: Optional[datetime] = None
    lastupdatetime: Optional[datetime] = None


@dataclass
class SMWalletTopPnlToken:
    """Smart Money Wallet's Top PNL Token data"""

    # Required fields first
    walletaddress: str
    tokenid: str
    name: str
    unprocessedpnl: Decimal
    unprocessedroi: Decimal
    transactionscount: Optional[int] = None  # Changed from transactionsCount
    status: int = TokenStatus.LOW_PNL_TOKEN.value  # Default to LOW_PNL_TOKEN
    amountinvested: Optional[Decimal] = None
    amounttakenout: Optional[Decimal] = None
    remainingcoins: Optional[Decimal] = None
    createdtime: Optional[datetime] = None
    lastupdatedtime: Optional[datetime] = None
    id: Optional[int] = None


@dataclass
class AttentionData:
    """Raw attention score data for a token"""

    attentionscore: Decimal
    recordedat: datetime
    datasource: str

    # Fields that might be null
    tokenid: Optional[str] = None
    name: Optional[str] = None
    chain: Optional[str] = None

    # Optional fields for changes
    change1hbps: Optional[int] = None
    change1dbps: Optional[int] = None
    change7dbps: Optional[int] = None
    change30dbps: Optional[int] = None
    id: Optional[int] = None


@dataclass
class InvestmentDetails:
    """Investment details data structure"""

    totalInvested: Decimal
    totalTakenOut: Decimal
    totalCoins: Decimal
    avgEntry: Decimal


@dataclass
class VolumeToken:
    """Volume token data structure for volume signals"""

    # Required fields
    tokenid: str
    name: str  # Trading symbol (e.g., "ROME")
    tokenname: str  # Full name (e.g., "REPUBLIC OF MEME")
    chain: str
    price: Decimal
    marketcap: Decimal
    liquidity: Decimal
    volume24h: Decimal
    buysolqty: int
    occurrencecount: int
    percentilerankpeats: float
    percentileranksol: float
    dexstatus: int
    change1hpct: Decimal

    # Optional fields
    id: Optional[int] = None
    tokendecimals: Optional[int] = None
    circulatingsupply: Optional[str] = None
    tokenage: Optional[str] = None
    twitterlink: Optional[str] = None
    telegramlink: Optional[str] = None
    websitelink: Optional[str] = None
    firstseenat: Optional[datetime] = None
    lastupdatedat: Optional[datetime] = None
    createdat: Optional[datetime] = None
    fdv: Optional[Decimal] = None
    timeago: Optional[datetime] = None


@dataclass
class PumpFunToken:
    """Pump Fun token data structure for pump fun signals"""

    # Required fields
    tokenid: str
    name: str  # Trading symbol
    tokenname: str  # Full name
    chain: str
    price: Decimal
    marketcap: Decimal
    liquidity: Decimal
    volume24h: Decimal
    buysolqty: int
    occurrencecount: int
    percentilerankpeats: float
    percentileranksol: float
    dexstatus: int
    change1hpct: Decimal

    # Optional fields
    id: Optional[int] = None
    tokendecimals: Optional[int] = None
    circulatingsupply: Optional[str] = None
    tokenage: Optional[str] = None
    twitterlink: Optional[str] = None
    telegramlink: Optional[str] = None
    websitelink: Optional[str] = None
    firstseenat: Optional[datetime] = None
    lastupdatedat: Optional[datetime] = None
    createdat: Optional[datetime] = None
    rugcount: Optional[float] = None
    timeago: Optional[datetime] = None


@dataclass
class SmartMoneyWalletBehaviour:
    """Data structure for wallet investment behavior analysis with cluster metrics"""

    walletaddress: str
    totalinvestment: float
    numtokens: int
    avginvestmentpertoken: float
    highconvictionnumtokens: int
    highconvictionavginvestment: float
    highconvictionwinrate: float
    highconvictiontotalinvested: float
    highconvictiontotaltakenout: float
    highconvictionpercentagereturn: float
    mediumconvictionnumtokens: int
    mediumconvictionavginvestment: float
    mediumconvictionwinrate: float
    mediumconvictiontotalinvested: float
    mediumconvictiontotaltakenout: float
    mediumconvictionpercentagereturn: float
    lowconvictionnumtokens: int
    lowconvictionavginvestment: float
    lowconvictionwinrate: float
    lowconvictiontotalinvested: float
    lowconvictiontotaltakenout: float
    lowconvictionpercentagereturn: float
    analysistime: Optional[datetime] = None


@dataclass
class NotificationButton:
    """
    Button data for notification messages
    """

    text: str
    url: str


@dataclass
class Notification:
    """
    Notification message data structure for storing notification records
    """

    # Required fields
    source: str  # From NotificationSource enum
    chatgroup: str  # From ChatGroup enum
    content: str
    status: str = NotificationStatus.PENDING.value  # Default to PENDING

    # Optional fields
    id: Optional[int] = None
    servicetype: Optional[str] = None  # From NotificationServiceType enum
    errordetails: Optional[str] = None
    buttons: List[NotificationButton] = field(
        default_factory=list
    )  # Inline buttons for the message
    createdat: Optional[datetime] = None
    updatedat: Optional[datetime] = None
    sentat: Optional[datetime] = None


class WalletInvestedStatusEnum(IntEnum):
    ACTIVE = 1
    INACTIVE = 2


class AttentionStatusEnum(Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"
