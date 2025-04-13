from config.Config import get_config

"""Parsers for pump fun signals data"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
import re
from logs.logger import get_logger
from datetime import datetime
from actions.DexscrennerAction import DexScreenerAction
from database.operations.schema import PumpFunToken

logger = get_logger(__name__)


def parsePumpFunResponse(response: Dict) -> List[PumpFunToken]:
    """
    Parse pump fun signals API response into PumpFunToken objects

    Args:
        response: Raw API response with format:
        {
            "data": [
                {
                    "token_id": "...",
                    "symbol": "...",
                    ...
                }
            ]
        }

    Returns:
        List[PumpFunToken]: List of parsed pump fun token objects
    """
    try:
        items = response.get("data", [])
        if not items:
            logger.warning("No items found in response")
            return []

        # Initialize DexScreener service
        dexScreener = DexScreenerAction()
        result = []

        for item in items:
            try:
                # Get token ID, preferring token_address if available
                tokenId = item.get("token_address") or item.get("token_id")
                if not tokenId:
                    logger.warning("Skipping item without token_id")
                    continue

                # Parse social links
                socialLinks = item.get("token_socialLinks", {})

                # Get price data from DexScreener
                try:
                    priceData = dexScreener.getTokenPrice(tokenId)
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch DexScreener data for {tokenId}: {str(e)}"
                    )
                    priceData = None

                # Create PumpFunToken object
                pumpFunToken = PumpFunToken(
                    tokenid=tokenId,
                    name=item["token_symbol"],
                    tokenname=item["token_name"],
                    chain=item["chain_raw"],
                    # Use DexScreener price if available, fallback to API price
                    price=(
                        Decimal(str(priceData.price))
                        if priceData
                        else _parseDecimal(item["price_1h_raw"])
                    ),
                    marketcap=(
                        Decimal(str(priceData.marketCap))
                        if priceData
                        else _parseDecimal(item["marketCap_raw"])
                    ),
                    liquidity=_parseDecimal(item["liquidity_raw"]),
                    volume24h=_parseDecimal(item["volume24_raw"]),
                    buysolqty=int(item["buy_sol_qty"]),
                    occurrencecount=int(item["occurrence_count"]),
                    percentilerankpeats=float(item["percentile_rank_repeats"]),
                    percentileranksol=float(item["percentile_rank_sol"]),
                    dexstatus=1 if item["dex_status"] == " " else 0,
                    change1hpct=_parseDecimal(item["change_pct_1h_raw"]),
                    tokendecimals=int(item["token_decimals"]),
                    circulatingsupply=item["token_info_circulatingSupply"],
                    tokenage=item["ageCat"],
                    twitterlink=socialLinks.get("twitter"),
                    telegramlink=socialLinks.get("telegram"),
                    websitelink=socialLinks.get("website"),
                    firstseenat=_parseDatetime(item["createdAt_time"]),
                    lastupdatedat=datetime.now(),
                    createdat=datetime.now(),
                    rugcount=float(item.get("rugcount", 0)),
                    timeago=_parseDatetime(item["time_ago"]),
                )

                result.append(pumpFunToken)
                logger.info(
                    f"Successfully parsed token {tokenId} - {item['token_name']} with DexScreener data: {bool(priceData)}"
                )

            except Exception as e:
                logger.error(f"Failed to parse item: {str(e)}, item: {item}")
                continue

        return result

    except Exception as e:
        logger.error(f"Failed to parse pump fun response: {str(e)}")
        return []


def _parseDecimal(value: str) -> Decimal:
    """Parse string to Decimal, handling None and empty strings"""
    if not value or value == "null" or value == "undefined":
        return Decimal("0")
    return Decimal(str(value).replace(",", ""))


def _parseDatetime(value: str) -> Optional[datetime]:
    """Parse datetime string to datetime object"""
    if not value or value == "null" or value == "undefined":
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def validatePumpFunSymbol(item: Dict) -> bool:
    """Validate pump fun signal data"""
    # Required fields must exist and have valid values
    requiredFields = ["token_id", "symbol", "name", "chain"]
    if not all(item.get(field) for field in requiredFields):
        return False

    # Minimum thresholds
    if item["liquidity"] < Decimal("1000"):  # $1K min liquidity
        return False

    if item["volume24h"] < Decimal("10000"):  # $10K min 24h volume
        return False

    return True
