from config.Config import get_config
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime
from enum import Enum
import json
import logging
from enum import IntEnum

logger = logging.getLogger(__name__)

class EntryType(Enum):
    """Type of entry strategy"""
    BULK = "BULK"
    DCA = "DCA"

@dataclass
class DCARule:
    """DCA (Dollar Cost Average) configuration"""
    intervals: int  # Number of entries
    intervaldelay: int  # Time between entries in minutes
    amountperinterval: Decimal  # Amount per entry
    pricedeviationlimit: Optional[Decimal] = None  # Max allowed price deviation

@dataclass
class ProfitTarget:
    """Individual profit target configuration"""
    pricepct: Decimal  # Target price percentage increase
    sizepct: Decimal  # Percentage of position to sell
    trailingstoppct: Optional[Decimal] = None  # Optional trailing stop percentage


@dataclass
class AttentionInfo:
    """Contails all data related to attention metrics"""
    isavailable: bool
    attentionscore: Decimal
    repeats: int
    attentionstatus: str

@dataclass
class TokenConvictionEnum(IntEnum):
    """Enum for token conviction levels"""
    HIGH = 1
    MEDIUM = 2
    LOW = 3
   
    
@dataclass
class StrategyEntryConditions:
    """Entry conditions for a strategy"""
    requiredtags: List[str] = field(default_factory=list)
    minmarketcap: float = 0.0
    minliquidity: float = 0.0
    minsmartbalance: float = 0.0
    minage: int = -1
    maxage: int = -1
    attentioninfo: Optional[AttentionInfo] = None

    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyEntryConditions':
        """Create EntryConditions from JSON string"""
        if isinstance(json_str, str):
            data = json.loads(json_str)
            return cls(**data)
        return json_str  # Already deserialized

@dataclass
class ChartConditions:
    """Technical analysis conditions"""
    timeframe: str = "1h"
    minpricechange: Optional[Decimal] = None
    maxpricechange: Optional[Decimal] = None
    rsiconditions: Optional[Dict[str, Decimal]] = None
    maconditions: Optional[Dict[str, List[int]]] = None
    volumeconditions: Optional[Dict[str, Decimal]] = None
    patternconditions: Optional[List[str]] = None

    @classmethod
    def from_json(cls, json_str: str) -> Optional['ChartConditions']:
        if isinstance(json_str, str):
            data = json.loads(json_str)
            return cls(**data)
        return json_str

@dataclass
class InvestmentInstructions:
    """Position sizing and investment rules"""
    entrytype: str
    allocatedamount: Decimal
    maxpositionsize: Optional[Decimal] = None
    maxportfolioallocation: Optional[Decimal] = None
    maxtokenallocation: Optional[Decimal] = None
    dcarules: Optional[DCARule] = None

    @classmethod
    def from_json(cls, json_str: str) -> 'InvestmentInstructions':
        if isinstance(json_str, str):
            data = json.loads(json_str)
            if 'dca_rules' in data and data['dca_rules']:
                data['dcarules'] = DCARule(**data['dca_rules'])
            elif 'dcaRules' in data and data['dcaRules']:
                data['dcarules'] = DCARule(**data['dcaRules'])
            elif 'dcarules' in data and data['dcarules']:
                data['dcarules'] = DCARule(**data['dcarules'])
            return cls(**data)
        return json_str

@dataclass
class  MoonBagInstructions:
    """Configuration for moon bag handling"""
    enabled: bool = False  # Whether moon bag is enabled for this strategy
    sizepct: Decimal = Decimal('0')  # Percentage of position to keep as moon bag
    minprofitpct: Decimal = Decimal('0')  # Minimum profit before moon bag can be activated
    trailingstoppct: Optional[Decimal] = None  # Optional trailing stop for moon bag
    takeprofitpct: Optional[Decimal] = None  # Optional take profit for moon bag
    maxtimeminutes: Optional[int] = None  # Optional maximum hold time

    @classmethod
    def from_json(cls, json_str: str) -> Optional['MoonBagInstructions']:
        if isinstance(json_str, str):
            data = json.loads(json_str)
            return cls(**data)
        return json_str

@dataclass
class ProfitTakingInstructions:
    """Profit taking configuration"""
    targets: List[ProfitTarget] = field(default_factory=list)
    minprofitpct: Decimal = Decimal('1.0')
    maxtimeminutes: Optional[int] = 1440  # Default 24 hours
    trailingstoppct: Optional[Decimal] = None
    dynamictargets: bool = False
    moonbaginstructions: Optional[MoonBagInstructions] = None

    @classmethod
    def from_json(cls, json_str: str) -> 'ProfitTakingInstructions':
        """Create ProfitTakingInstructions from JSON string"""
        try:
            logger.info(f"Parsing profit taking instructions: {json_str}")
            
            # Handle input data
            if isinstance(json_str, str):
                data = json.loads(json_str)
            else:
                data = json_str

            # Handle list format (from create_strategy_api)
            if isinstance(data, list):
                # Check if we have any items in the list
                if not data:
                    logger.warning("Empty profit targets list")
                    return cls()
                    
                # Check what format the list items are in
                first_item = data[0]
                logger.debug(f"First profit target item: {first_item}")
                
                # Create targets based on the keys present in the data
                targets = []
                for t in data:
                    # Try different key formats
                    if 'pricepct' in t and 'sizepct' in t:
                        # Database format
                        targets.append(ProfitTarget(
                            pricepct=Decimal(str(t['pricepct'])),
                            sizepct=Decimal(str(t['sizepct'])),
                            trailingstoppct=None
                        ))
                    elif 'price_target_pct' in t and 'sell_amount_pct' in t:
                        # API format
                        targets.append(ProfitTarget(
                            pricepct=Decimal(str(t['price_target_pct'])),
                            sizepct=Decimal(str(t['sell_amount_pct'])),
                            trailingstoppct=None
                        ))
                    elif 'price_pct' in t and 'size_pct' in t:
                        # Alternative format
                        targets.append(ProfitTarget(
                            pricepct=Decimal(str(t['price_pct'])),
                            sizepct=Decimal(str(t['size_pct'])),
                            trailingstoppct=None
                        ))
                    else:
                        logger.warning(f"Unknown profit target format: {t}")
                
                if not targets:
                    logger.warning("No valid profit targets found in the list")
                    return cls()
                    
                logger.debug(f"Created {len(targets)} profit targets")
                return cls(
                    targets=targets,
                    minprofitpct=Decimal('1.0'),  # Default values
                    maxtimeminutes=1440,  # 24 hours
                    trailingstoppct=None,
                    dynamictargets=False,
                    moonbaginstructions=None
                )

            # Handle dictionary format (from database)
            if not isinstance(data, dict):
                raise ValueError(f"Expected dictionary or list, got {type(data)}")

            # Create a new dict with properly converted values
            converted_data = {
                'minprofitpct': Decimal(str(data.get('min_profit_pct', '1.0'))),
                'maxtimeminutes': int(data['max_time_minutes']) if data.get('max_time_minutes') else None,
                'trailingstoppct': Decimal(str(data['trailing_stop_pct'])) if data.get('trailing_stop_pct') else None,
                'dynamictargets': bool(data.get('dynamic_targets', False)),
                'targets': [],
                'moonbaginstructions': None
            }

            # Handle targets
            targets = data.get('targets', [])
            if isinstance(targets, str):
                targets = json.loads(targets)

            converted_data['targets'] = [
                ProfitTarget(
                    pricepct=Decimal(str(t.get('price_target_pct') or t.get('price_pct', 0))),
                    sizepct=Decimal(str(t.get('sell_amount_pct') or t.get('size_pct', 0))),
                    trailingstoppct=Decimal(str(t['trailing_stop_pct'])) if t.get('trailing_stop_pct') else None
                ) for t in targets
            ]

            # Handle moon_bag_rules
            if moon_bag_data := data.get('moon_bag_instructions'):
                if isinstance(moon_bag_data, str):
                    moon_bag_data = json.loads(moon_bag_data)
                converted_data['moonbaginstructions'] = MoonBagInstructions(**moon_bag_data)

            logger.debug(f"Final converted data: {converted_data}")
            return cls(**converted_data)

        except Exception as e: 
            logger.info(f"Error parsing ProfitTakingInstructions: {str(e)}", exc_info=True)
            logger.info(f"Input data was: {json_str}")
            # Return default instance instead of raising an error
            return cls()

@dataclass
class RiskManagementInstructions:  # Fixed class name spelling
    """Risk management configuration"""
    stoplosspct: Decimal = Decimal('5.0')  # Default 5% stop loss
    stoplossenabled: bool = True

    @classmethod
    def from_json(cls, json_str: str) -> 'RiskManagementInstructions':
        try:
            # Handle input data
            if isinstance(json_str, str):
                data = json.loads(json_str)
            else:
                data = json_str
                
            # Handle dictionary format
            if isinstance(data, dict):
                # Map database field names to class field names
                return cls(
                    stoplosspct=Decimal(str(data.get('stoplosspct', data.get('stop_loss_pct', '5.0')))),
                    stoplossenabled=bool(data.get('stoplossenabled', data.get('enabled', True)))
                )
            
            # If we got here, return the input if it's already an instance, otherwise default
            if isinstance(json_str, cls):
                return json_str
            
            logger.warning(f"Unexpected risk management data format: {type(json_str)}")
            return cls()  # Return default instance
            
        except Exception as e:
            logger.error(f"Error parsing RiskManagementInstructions: {str(e)}", exc_info=True)
            logger.debug(f"Input data was: {json_str}")
            return cls()  # Return default instance instead of raising an error

@dataclass
class StrategyConfig:
    """Configuration for a strategy"""
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
    status: int = TokenConvictionEnum.HIGH.value
    active: bool = True
    superuser: bool = False
    createdat: datetime = field(default_factory=datetime.now)
    updatedat: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Convert JSON strings to objects after initialization"""
        if isinstance(self.strategyentryconditions, str):
            self.strategyentryconditions = StrategyEntryConditions.from_json(self.strategyentryconditions)
        if isinstance(self.chartconditions, str):
            self.chartconditions = ChartConditions.from_json(self.chartconditions)
        if isinstance(self.investmentinstructions, str):
            self.investmentinstructions = InvestmentInstructions.from_json(self.investmentinstructions)
        if isinstance(self.profittakinginstructions, str):
            self.profittakinginstructions = ProfitTakingInstructions.from_json(self.profittakinginstructions)
        if isinstance(self.riskmanagementinstructions, str):
            self.riskmanagementinstructions = RiskManagementInstructions.from_json(self.riskmanagementinstructions)
        if isinstance(self.moonbaginstructions, str):
            self.moonbaginstructions = MoonBagInstructions.from_json(self.moonbaginstructions) if self.moonbaginstructions else None

@dataclass
class ExecutionMetrics:
    """Execution performance metrics"""
    executionid: int
    strategyid: int
    tokenid: str
    maxprofitpct: Decimal
    maxlosspct: Decimal
    holdingperiodhours: int
    avgpositionsize: Decimal
    totaltrades: int
    profitabletrades: int
    realizedpnl: Decimal
    realizedpnlpct: Decimal
    feespaid: Decimal
    slippagecost: Decimal
    createdtime: datetime
    updatedtime: datetime 