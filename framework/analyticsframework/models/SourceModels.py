from config.Config import get_config
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from framework.analyticsframework.models.BaseModels import BaseTokenData
from framework.analyticsframework.models.StrategyModels import AttentionInfo
@dataclass
class AttentionTokenData(BaseTokenData):
    """Attention-specific token data"""
    attentionscore: Decimal
    attentioncount: int
    change1hbps: int
    change1dbps: int
    change7dbps: int
    change30dbps: int
    createdat: datetime
    updatedat: datetime

    
@dataclass
class PortSummaryTokenData(BaseTokenData):
    """Token data specific to portfolio summary analysis"""
    # Inherits from BaseTokenData:
    # - tokenid
    # - tokenname
    # - chainname
    # - price
    # - marketcap
    # - holders

    # Additional fields specific to PortSummary
    tokenage: str
    avgprice: float
    smartbalance: float
    walletsinvesting1000: int
    walletsinvesting5000: int
    walletsinvesting10000: int
    qtychange1d: float
    qtychange7d: float
    qtychange30d: float
    status: int
    attentioninfo: Optional[AttentionInfo] = None
    portsummaryid: Optional[int] = None
    tags: Optional[str] = None
    markedinactive: Optional[datetime] = None

    
@dataclass
class SmartMoneyTokenData(BaseTokenData):
    """SmartMoney-specific token data"""
    smartmoneywallets: int
    smartmoneybalance: Decimal
    smartmoneytransactions: int
    firstsmartmoneytime: datetime
    smartmoneyconviction: Decimal

    
@dataclass
class VolumeTokenData(BaseTokenData):
    """Volume-specific token data"""
    buysolqty: Decimal
    occurrencecount: int
    percentilerankpepeats: Decimal
    percentileranksol: Decimal
    dexstatus: str
    change1hpct: Decimal
    avgvolume24h: Decimal
    volumespikepct: Decimal

    

@dataclass
class PumpFunTokenData(BaseTokenData):
    """PumpFun-specific token data"""
    buysolqty: Decimal
    occurrencecount: int
    percentilerankpepeats: Decimal
    percentileranksol: Decimal
    dexstatus: str
    change1hpct: Decimal
    avgvolume24h: Decimal
    volumespikepct: Decimal
