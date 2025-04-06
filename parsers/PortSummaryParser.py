from config.Config import get_config
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
from logs.logger import get_logger
from database.operations.schema import PortfolioSummary
from config.PortfolioStatusEnum import PortfolioStatus
from decimal import Decimal, InvalidOperation
from datetime import datetime

logger = get_logger(__name__)

def parsePortSummaryAPIResponse(response: Dict[str, Any]) -> List[PortfolioSummary]:
    """Parse and validate portfolio summary API response"""
    results = []
    current_time = datetime.now()
    
    for rawItem in response.get('data', []):
        try:
            # Create PortfolioSummary object with exact database column names
            summaryItem = PortfolioSummary(
                chainname=str(rawItem['chain_name']),
                tokenid=str(rawItem['token_id']),
                name=str(rawItem['name']),
                tokenage=str(rawItem.get('tokenagetoday', '')),
                mcap=_convertKmString(rawItem['fdv_or_mcap']),
                currentprice=_safeDecimal(rawItem.get('price_1h', '0')),
                avgprice=_safeDecimal(rawItem['avg_buy_price']),
                smartbalance=_convertKmString(rawItem['smart_balance']),
                walletsinvesting1000=int(rawItem.get('w_countgrt_1000', 0)),
                walletsinvesting5000=int(rawItem.get('w_countgrt_5000', 0)),
                walletsinvesting10000=int(rawItem.get('w_countgrt_10000', 0)),
                qtychange1d=_safeDecimal(rawItem['d1_chg_pct']),
                qtychange7d=_safeDecimal(rawItem['d7_chg_pct']),
                qtychange30d=_safeDecimal(rawItem['d30_chg_pct']),
                status=PortfolioStatus.ACTIVE.statuscode,
                tags=[],
                # Add timestamp fields
                firstseen=current_time,
                lastseen=current_time,
                createdat=current_time,
                updatedat=current_time
            )
            
            if filterPortfolioItems(summaryItem):
                results.append(summaryItem)
                logger.info(f"Parsed token {summaryItem.tokenid} - {summaryItem.name} with status {PortfolioStatus.ACTIVE}")
                
        except Exception as e:
            logger.error(f"Failed to parse item: {e}")
            continue
            
    return results

def _safeDecimal(value: Any) -> Decimal:
    """Safely convert value to Decimal"""
    try:
        if value is None or value == '':
            return Decimal('0')
            
        if isinstance(value, str):
            # Remove any currency symbols, commas, and spaces
            cleaned = value.replace('$', '').replace(',', '').replace(' ', '')
            # Handle percentage values
            if '%' in cleaned:
                cleaned = cleaned.replace('%', '')
                return Decimal(cleaned) / 100
            # Handle empty or invalid strings
            if not cleaned or cleaned.lower() in ['na', 'n/a', '-']:
                return Decimal('0')
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                logger.warning(f"Could not convert string value to decimal: {value}")
                return Decimal('0')
                
        return Decimal(str(value))
        
    except (InvalidOperation, TypeError, ValueError) as e:
        logger.warning(f"Failed to convert value to decimal: {value}, Error: {e}")
        return Decimal('0')

def _convertKmString(value: Any) -> float:
    """Handle numeric inputs and various string formats (K, M, B)"""
    if not value:
        return 0.0
    strValue = str(value).upper().replace(',', '').strip()
    if match := re.match(r"^([\d.]+)([KMB]?)$", strValue):
        number, suffix = match.groups()
        multiplier = {'K': 1e3, 'M': 1e6, 'B': 1e9}.get(suffix, 1)
        return float(number) * multiplier
    return 0.0

def filterPortfolioItems(item: PortfolioSummary) -> bool:
    """Filter out invalid or unwanted portfolio items"""
    # Minimum smart balance threshold
    if item.smartbalance < 100_000:
        return False
    
    # Ensure required fields have valid values
    if not all([
        item.tokenid,
        item.name,
        item.chainname,
        item.tokenage
    ]):
        return False
        
    return True

def _parseMarketcap(value: Any) -> str:
    """Handle marketcap normalization"""
    strValue = str(value).lower().replace('mil', 'million')
    return re.sub(r'\s+', '_', strValue)