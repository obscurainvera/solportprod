from config.Config import get_config

"""Parsers for onchain data"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
import re
from logs.logger import get_logger
from datetime import datetime
from database.operations.schema import OnchainInfo
from actions.DexscrennerAction import DexScreenerAction, TokenPrice
import pytz

logger = get_logger(__name__)


def parseOnchainResponse(response: Dict) -> List[OnchainInfo]:
    """
    Parse response from onchain API and convert to OnchainInfo objects
    Only include tokens where chain_raw = Sol and sort by change_pct_1h
    Use DexscreennerAction to get price, marketcap, and liquidity data
    
    Args:
        response: API response dictionary
        
    Returns:
        List[OnchainInfo]: List of parsed OnchainInfo objects
    """
    try:
        items = response.get("data", [])
        if not items:
            logger.warning("No items found in response")
            return []

        # Filter for SOL tokens only
        sol_items = [item for item in items if item.get("chain_raw") == "Sol"]
        if not sol_items:
            logger.warning("No SOL tokens found in response")
            return []
            
        # Sort by change_pct_1h_raw in descending order
        sorted_items = sorted(
            sol_items, 
            key=lambda x: float(_parseDecimal(x.get("change_pct_1h", "0"))), 
            reverse=True
        )
        
        # Initialize DexScreener service
        dexScreener = DexScreenerAction()
        
        # Get all token IDs for batch processing
        token_ids = [item.get("token_id") for item in sorted_items if item.get("token_id")]
        
        # Get price data for all tokens in batches
        logger.info(f"Fetching price data for {len(token_ids)} tokens from DexScreener")
        price_data_map = dexScreener.getBatchTokenPrices(token_ids)
        logger.info(f"Successfully fetched price data for {sum(1 for v in price_data_map.values() if v is not None)} tokens")
        
        # Assign ranks starting from 1
        result = []
        for rank, item in enumerate(sorted_items, 1):
            try:
                # Create OnchainInfo object
                tokenId = item.get("token_id")
                if not tokenId:
                    logger.warning("Skipping item without token_id")
                    continue

                # Convert to IST timezone
                ist = pytz.timezone('Asia/Kolkata')
                now = datetime.now(ist)
                
                # Parse makers value - it could be a formatted string like "5,155" or a raw number
                makers_value = item.get("makers_raw", 0)
                if isinstance(makers_value, str) and ',' in makers_value:
                    makers_value = int(makers_value.replace(',', ''))
                
                # Get price data from DexScreener
                price_data = price_data_map.get(tokenId)
                
                # Use DexScreener data if available, otherwise fallback to API data
                price = Decimal(str(price_data.price)) if price_data else _parseDecimal(item["price_1h_raw"])
                marketcap = Decimal(str(price_data.marketCap)) if price_data else _parseDecimal(item["marketCap_raw"])
                
                # For liquidity, we need to use the API data as DexScreener doesn't provide it directly
                liquidity = _parseDecimal(item["liquidity_raw"])
                
                onchainInfo = OnchainInfo(
                    tokenid=tokenId,
                    name=item["token_symbol"],
                    chain=item["chain_raw"],
                    price=price,
                    marketcap=marketcap,
                    liquidity=liquidity,
                    makers=int(makers_value),
                    price1h=_parseDecimal(item["change_pct_1h"]),
                    rank=rank,  # Assigned rank based on sorting
                    age=item.get("token_age_raw"),
                    createdat=now,
                    updatedat=now,
                )

                result.append(onchainInfo)
                logger.info(
                    f"Successfully parsed token {tokenId} - {item['token_symbol']} with rank {rank}, using DexScreener data: {price_data is not None}"
                )

            except Exception as e:
                logger.error(f"Failed to parse item: {str(e)}, item: {item}")
                continue

        return result

    except Exception as e:
        logger.error(f"Failed to parse onchain response: {str(e)}")
        return []


def _parseDecimal(value: str) -> Decimal:
    """Parse string to Decimal, handling None and empty strings"""
    if not value or value == "null" or value == "undefined":
        return Decimal("0")
    return Decimal(str(value).replace(",", ""))


def _parseDatetime(value: str) -> Optional[datetime]:
    """Parse datetime string to datetime object in IST timezone"""
    if not value or value == "null" or value == "undefined":
        return None
    try:
        # Parse the datetime and convert to IST
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        ist = pytz.timezone('Asia/Kolkata')
        return dt.astimezone(ist)
    except (ValueError, TypeError):
        return None
