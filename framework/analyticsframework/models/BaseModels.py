from config.Config import get_config
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime
from abc import ABC, abstractmethod

from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus
from framework.analyticsframework.models.StrategyModels import InvestmentInstructions, StrategyEntryConditions, ChartConditions, ProfitTakingInstructions, RiskManagementInstructions, MoonBagInstructions, RiskManagementInstructions

@dataclass
class BaseTokenData(ABC):
    """Base class for all token data across sources"""
    tokenid: str
    tokenname: str
    price: Decimal
    marketcap: Decimal
    holders: int
    chainname: str

@dataclass
class BaseStrategyConfig:
      """Base configuration for all strategies"""
      strategyid: int
      strategyname: str
      source: str
      description: Optional[str] = None
      strategyentryconditions: StrategyEntryConditions = field(default_factory=StrategyEntryConditions)
      chartconditions: Optional[ChartConditions] = None  
      investmentinstructions: InvestmentInstructions = field(default_factory=InvestmentInstructions)
      profittakinginstructions: ProfitTakingInstructions = field(default_factory=ProfitTakingInstructions)
      riskmanagementinstructions: RiskManagementInstructions = field(default_factory=RiskManagementInstructions)
      moonbaginstructions: Optional[MoonBagInstructions] = None
      additionalinstructions: Optional[Dict[str, Any]] = None
      status: int = 1
      active: bool = True
      superuser: bool = False
      createdat: datetime = field(default_factory=datetime.now)
      updatedat: datetime = field(default_factory=datetime.now)
 
      def __post_init__(self):
          """Convert JSON strings or dictionaries to objects after initialization"""
          # Handle strategy entry conditions
          if isinstance(self.strategyentryconditions, dict):
              self.strategyentryconditions = StrategyEntryConditions(**self.strategyentryconditions)
          elif isinstance(self.strategyentryconditions, str):
              self.strategyentryconditions = StrategyEntryConditions.from_json(self.strategyentryconditions)
             
          # Handle chart conditions
          if isinstance(self.chartconditions, dict):
              self.chartconditions = ChartConditions(**self.chartconditions)
          elif isinstance(self.chartconditions, str):
              self.chartconditions = ChartConditions.from_json(self.chartconditions)
             
          # Handle investment instructions
          if isinstance(self.investmentinstructions, dict):
              self.investmentinstructions = InvestmentInstructions(**self.investmentinstructions)
          elif isinstance(self.investmentinstructions, str):
              self.investmentinstructions = InvestmentInstructions.from_json(self.investmentinstructions)
             
          # Handle profit taking instructions
          if isinstance(self.profittakinginstructions, (dict, list)):
              self.profittakinginstructions = ProfitTakingInstructions.from_json(self.profittakinginstructions)
          elif isinstance(self.profittakinginstructions, str):
              self.profittakinginstructions = ProfitTakingInstructions.from_json(self.profittakinginstructions)
             
          # Handle risk management instructions
          if isinstance(self.riskmanagementinstructions, dict):
              self.riskmanagementinstructions = RiskManagementInstructions(**self.riskmanagementinstructions)
          elif isinstance(self.riskmanagementinstructions, str):
              self.riskmanagementinstructions = RiskManagementInstructions.from_json(self.riskmanagementinstructions)
             
          # Handle moon bag instructions
          if isinstance(self.moonbaginstructions, dict):
              self.moonbaginstructions = MoonBagInstructions(**self.moonbaginstructions)
          elif isinstance(self.moonbaginstructions, str) and self.moonbaginstructions:
              self.moonbaginstructions = MoonBagInstructions.from_json(self.moonbaginstructions)

@dataclass
class ExecutionState:
    """Current state of strategy execution"""
    executionid: int
    strategyid: int
    tokenid: str
    tokenname: str
    status: ExecutionStatus
    allotedamount: Decimal
    description: Optional[str] = None
    remainingcoins: Optional[Decimal] = None
    investedamount: Optional[Decimal] = None
    avgentryprice: Optional[Decimal] = None
    amounttakenout: Optional[Decimal] = None
    realizedpnl: Optional[Decimal] = None
    realizedpnlpercent: Optional[Decimal] = None
    notes: Optional[str] = None
    createdat: datetime = field(default_factory=datetime.now)
    updatedat: datetime = field(default_factory=datetime.now)


@dataclass
class TradeLog:
    """Record of individual trades"""
    executionid: int
    tokenid: str
    tokenname: str
    tradetype: str  # BUY/SELL
    amount: Decimal
    tokenprice: Decimal
    coins: Decimal = Decimal('0')
    description: Optional[str] = None
    createdat: Optional[datetime] = None  # Auto-filled by DB
    lastupdatedat: Optional[datetime] = None  # Auto-filled by DB
    tradeid: Optional[int] = None
