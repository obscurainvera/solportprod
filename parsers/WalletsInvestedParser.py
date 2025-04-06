from config.Config import get_config
from typing import Dict, Any, Optional, List
from decimal import Decimal, InvalidOperation
from datetime import datetime
from database.operations.schema import WalletsInvested, WalletInvestedStatusEnum
from logs.logger import get_logger

logger = get_logger(__name__)

def _safeDecimal(value: Any) -> Decimal:
    """
    Safely convert value to Decimal, handling special cases
    
    Args:
        value: Value to convert to Decimal
        
    Returns:
        Decimal: Converted value or 0 if conversion fails
    """
    try:
        if value is None or value == '' or value == 'New' or value == '!':
            return Decimal('0')
            
        if isinstance(value, str):
            # Remove any currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '')
            
            # Handle negative values in parentheses
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]
                
            # Handle K/M/B suffixes
            if cleaned.endswith('K'):
                return Decimal(cleaned[:-1]) * 1000
            elif cleaned.endswith('M'):
                return Decimal(cleaned[:-1]) * 1000000
            elif cleaned.endswith('B'):
                return Decimal(cleaned[:-1]) * 1000000000
                
            # Handle non-numeric special cases
            if not any(c.isdigit() or c in '.-' for c in cleaned):
                logger.debug(f"Non-numeric value encountered: {value}, defaulting to 0")
                return Decimal('0')
                
            return Decimal(cleaned)
            
        return Decimal(str(value))
        
    except (InvalidOperation, TypeError, ValueError) as e:
        logger.debug(f"Failed to convert {value} to Decimal: {str(e)}, defaulting to 0")
        return Decimal('0')

def parseWalletsInvestedInASpecificTokenAPIResponse(response: Dict[str, Any], portsummaryId: int, tokenId: str) -> List[WalletsInvested]:
    """
    Parse and validate token analysis API response
    
    Args:
        response: API response containing wallet data
        portsummaryid: Portfolio summary ID
        tokenId: Token address being analyzed
        
    Returns:
        List of TokenAnalysis objects
    """
    results = []
    try:
        data = response.get('table_data', [])
        if not data:
            logger.warning("No table_data found in response")
            return results

        # Iterate through each wallet entry in the response
        for walletData in data:
            try:
                # Validate required fields
                walletAddress = walletData.get('WALLET_ID')
                walletName = walletData.get('WALLETS', '')  # Get wallet name from WALLETS field
                
                if not walletAddress:
                    logger.error(f"Missing required WALLET_ID in data: {walletData}")
                    continue

                # Convert percentage strings to decimals
                qtychange1d = walletData.get('1D QTY CHANGE(%)', '0%').replace('%', '')
                qtychange7d = walletData.get('7D QTY CHANGE(%)', '0%').replace('%', '')
                
                # Handle smart holdings value (convert K to thousands)
                smartHoldings = walletData.get('SMART $ HOLDINGS', '0')
                if isinstance(smartHoldings, str):
                    smartHoldings = smartHoldings.replace('$', '').replace(',', '')
                    if 'K' in smartHoldings:
                        smartHoldings = smartHoldings.replace('K', '')
                        smartHoldings = _safeDecimal(smartHoldings) * 1000
                    else:
                        smartHoldings = _safeDecimal(smartHoldings)

                # Handle realized PNL
                realizedPnl = walletData.get('REALIZED PNL', '0')
                if isinstance(realizedPnl, str):
                    realizedPnl = realizedPnl.replace('$', '').replace(',', '')
                    if 'K' in realizedPnl:
                        realizedPnl = realizedPnl.replace('K', '')
                        realizedPnl = _safeDecimal(realizedPnl) * 1000

                # Create analysis item with validated data
                analysisItem = WalletsInvested(
                    portsummaryid=portsummaryId,
                    tokenid=tokenId,
                    walletaddress=str(walletAddress),
                    walletname=walletName,  # Add wallet name to the object
                    coinquantity=_safeDecimal(walletData.get('coin_qty', 0)),
                    smartholding=smartHoldings,
                    firstbuytime=datetime.strptime(walletData.get('FIRST BUY', '2000-01-01 00:00:00'), '%Y-%m-%d %H:%M:%S') 
                    if walletData.get('FIRST BUY') and walletData.get('FIRST BUY') != '!' 
                    else datetime.now(),
                    totalinvestedamount=_safeDecimal(0),  # Default value as not provided
                    amounttakenout=_safeDecimal(0),
                    totalcoins=_safeDecimal(0),
                    qtychange1d=_safeDecimal(qtychange1d),
                    qtychange7d=_safeDecimal(qtychange7d),
                    avgentry=_safeDecimal(walletData.get('AVERAGE ENTRY', 0)),
                    chainedgepnl=_safeDecimal(walletData.get('total_pnl', 0)),
                    status=WalletInvestedStatusEnum.ACTIVE  # Use enum value
                )

                # Validate the created object
                if not analysisItem.walletaddress:
                    logger.error(f"Invalid analysis item created: {analysisItem}")
                    continue

                results.append(analysisItem)
                logger.debug(f"Successfully parsed wallet {walletAddress} ({walletName})")

            except Exception as e:
                logger.error(f"Failed to parse wallet data: {e}, data: {walletData}")
                continue

        logger.debug(f"Successfully parsed {len(results)} wallet entries for token {tokenId}")
        return results

    except Exception as e:
        logger.error(f"Failed to parse token analysis response: {e}")
        return results 