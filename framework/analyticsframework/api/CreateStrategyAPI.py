from config.Config import get_config
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import json
from framework.analyticsframework.models.StrategyModels import (
    StrategyConfig,
    StrategyEntryConditions,
    ChartConditions,
    InvestmentInstructions,
    ProfitTakingInstructions,
    RiskManagementInstructions,
    TokenConvictionEnum,
)
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from logs.logger import get_logger

logger = get_logger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)


class CreateStrategyAPI:
    def __init__(self, analyticsHandler: AnalyticsHandler):
        self.analyticsHandler = analyticsHandler

    def addStrategy(self, strategyData: Dict[str, Any]) -> Optional[int]:
        """Add a new strategy configuration"""
        try:
            # Log incoming data
            logger.info(f"Received strategy data: {json.dumps(strategyData, indent=2)}")

            # Validate required fields
            requiredFields = [
                "strategy_name",
                "source_type",
                "entry_conditions",
                "investment_instructions",
                "profit_taking_instructions",
                "risk_management_instructions",
            ]

            # Log validation checks
            for field in requiredFields:
                logger.debug(f"Checking required field: {field}")
                if field not in strategyData:
                    logger.error(f"Missing required field: {field}")
                    raise ValueError(f"Missing required field: {field}")

            # Validate source type
            logger.debug(f"Validating source type: {strategyData['source_type']}")
            if not SourceType.isValidSource(strategyData["source_type"]):
                logger.error(f"Invalid source type: {strategyData['source_type']}")
                raise ValueError(f"Invalid source type: {strategyData['source_type']}")

            # Convert token conviction to enum value
            tokenConviction = TokenConvictionEnum[
                strategyData.get("token_conviction", "HIGH")
            ]

            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create strategy config
            strategyConfig = {
                "strategyname": strategyData["strategy_name"],
                "source": strategyData["source_type"],
                "description": strategyData.get("description", ""),
                "strategyentryconditions": self._serializeEntryConditions(
                    strategyData["entry_conditions"]
                ),
                "chartconditions": self._serializeChartConditions(
                    strategyData.get("chart_conditions")
                ),
                "investmentinstructions": self._serializeInvestmentRules(
                    strategyData["investment_instructions"]
                ),
                "profittakinginstructions": self._serializeProfitInstructions(
                    strategyData["profit_taking_instructions"]
                ),
                "riskmanagementinstructions": self._serializeRiskInstructions(
                    strategyData["risk_management_instructions"]
                ),
                "moonbaginstructions": self._serializeMoonBagRules(
                    strategyData.get("moon_bag_instructions")
                ),
                "additionalinstructions": json.dumps(
                    strategyData.get("additional_instructions", {})
                ),
                "status": tokenConviction.value,
                "active": 1,
                "superuser": strategyData.get("superuser", False),
                "createdtime": current_time,
                "updatedtime": current_time,
            }

            # Log final config
            logger.info(
                f"Prepared strategy config: {json.dumps(strategyConfig, indent=2)}"
            )

            # Save to database
            strategyId = self.analyticsHandler.createStrategy(strategyConfig)
            if not strategyId:
                logger.error("Failed to create strategy in database")
                raise ValueError("Failed to create strategy in database")

            logger.info(f"Successfully created strategy with ID: {strategyId}")
            return strategyId

        except ValueError as e:
            logger.error(f"Validation error creating strategy: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating strategy: {str(e)}", exc_info=True)
            raise ValueError(f"Error creating strategy: {str(e)}")

    # Helper methods for serializing data
    def _serializeEntryConditions(self, data: Dict) -> str:
        """Serialize entry conditions"""
        try:
            # Validate required fields for entry conditions
            requiredFields = ["required_tags"]
            for field in requiredFields:
                if field not in data:
                    raise ValueError(
                        f"Missing required field in entry conditions: {field}"
                    )

            # Convert to database column names
            entryConditions = {
                "requiredtags": data.get("required_tags", []),
                "minmarketcap": float(data.get("min_market_cap", 0)),
                "minliquidity": float(data.get("min_liquidity", 0)),
                "minsmartbalance": float(data.get("min_smart_balance", 0)),
                "minage": int(data.get("min_age", 0)),
                "maxage": int(data.get("max_age", 0)),
                "attentioninfo": {
                    "isavailable": bool(
                        data.get("attention_info", {}).get("is_available", False)
                    ),
                    "attentionscore": float(
                        data.get("attention_info", {}).get("attention_score", 0)
                    ),
                    "repeats": int(data.get("attention_info", {}).get("repeats", 0)),
                    "attentionstatus": data.get("attention_info", {}).get(
                        "attention_status", []
                    ),
                },
            }
            return json.dumps(entryConditions)
        except Exception as e:
            raise ValueError(f"Invalid entry conditions format: {str(e)}")

    def _serializeChartConditions(self, data: Optional[Dict]) -> Optional[str]:
        """Serialize chart conditions"""
        try:
            return json.dumps(data) if data else None
        except Exception as e:
            raise ValueError(f"Invalid chart conditions format: {str(e)}")

    def _serializeInvestmentRules(self, data: Dict) -> str:
        """Serialize investment rules"""
        try:
            # Validate required fields for investment instructions
            requiredFields = ["entry_type", "allocated_amount"]
            for field in requiredFields:
                if field not in data:
                    raise ValueError(
                        f"Missing required field in investment instructions: {field}"
                    )

            # Convert to database column names
            investmentRules = {
                "entrytype": data.get("entry_type", "BULK"),
                "allocatedamount": str(data.get("allocated_amount", "0")),
                "maxpositionsize": (
                    str(data.get("max_position_size"))
                    if data.get("max_position_size")
                    else None
                ),
                "maxportfolioallocation": (
                    str(data.get("max_portfolio_allocation"))
                    if data.get("max_portfolio_allocation")
                    else None
                ),
                "maxtokenallocation": (
                    str(data.get("max_token_allocation"))
                    if data.get("max_token_allocation")
                    else None
                ),
            }

            # Handle DCA rules if present
            if "dca_rules" in data and data["dca_rules"]:
                dca_data = data["dca_rules"]
                investmentRules["dcarules"] = {
                    "intervals": dca_data.get("intervals", 1),
                    "intervaldelay": dca_data.get("interval_delay_minutes", 60),
                    "amountperinterval": str(dca_data.get("amount_per_interval", "0")),
                    "pricedeviationlimit": (
                        str(dca_data.get("price_deviation_limit_pct"))
                        if dca_data.get("price_deviation_limit_pct")
                        else None
                    ),
                }

            return json.dumps(investmentRules)
        except Exception as e:
            raise ValueError(f"Invalid investment rules format: {str(e)}")

    def _serializeProfitInstructions(self, data: list) -> str:
        """Serialize profit taking rules"""
        try:
            # Validate each profit taking target
            for target in data:
                if "price_target_pct" not in target or "sell_amount_pct" not in target:
                    raise ValueError(
                        "Each profit target must have price_target_pct and sell_amount_pct"
                    )

            # Convert to database column names
            profitTargets = []
            for target in data:
                profitTargets.append(
                    {
                        "pricepct": str(target["price_target_pct"]),
                        "sizepct": str(target["sell_amount_pct"]),
                    }
                )

            return json.dumps(profitTargets)
        except Exception as e:
            raise ValueError(f"Invalid profit taking instructions format: {str(e)}")

    def _serializeRiskInstructions(self, data: Dict) -> str:
        """Serialize risk management rules"""
        try:
            # Validate required fields for risk management
            requiredFields = ["stop_loss_pct"]
            for field in requiredFields:
                if field not in data:
                    raise ValueError(
                        f"Missing required field in risk management: {field}"
                    )

            # Convert to database column names
            riskInstructions = {
                "stoplossenabled": data.get("enabled", True),
                "stoplosspct": data.get("stop_loss_pct", "5"),
            }

            return json.dumps(riskInstructions)
        except Exception as e:
            raise ValueError(f"Invalid risk management instructions format: {str(e)}")

    def _serializeMoonBagRules(self, data: Optional[Dict]) -> Optional[str]:
        """Serialize moon bag rules"""
        try:
            if not data:
                return None

            # Validate required fields for moon bag
            requiredFields = ["enabled", "size_pct"]
            for field in requiredFields:
                if field not in data:
                    raise ValueError(
                        f"Missing required field in moon bag instructions: {field}"
                    )

            # Convert to database column names
            moonBagRules = {
                "enabled": data.get("enabled", False),
                "sizepct": str(data.get("size_pct", "0")),
                "targetpricepct": str(data.get("target_price_pct", "0")),
            }

            return json.dumps(moonBagRules)
        except Exception as e:
            raise ValueError(f"Invalid moon bag instructions format: {str(e)}")
