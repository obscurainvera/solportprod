from config.Config import get_config
from typing import List, Optional, Dict, Union
from database.operations.schema import SmartMoneyWallet
from decimal import Decimal, InvalidOperation
from logs.logger import get_logger

logger = get_logger(__name__)

def safeDecimalConvert(value: Union[str, int, float]) -> Decimal:
    """
    Safely convert a value to Decimal
    
    Args:
        value: Value to convert (string, int, or float)
        
    Returns:
        Decimal: Converted value or Decimal(0) if conversion fails
    """
    try:
        # Handle None or empty string
        if value is None or (isinstance(value, str) and not value.strip()):
            return Decimal('0')
            
        # Remove any currency symbols or commas
        if isinstance(value, str):
            value = value.replace('$', '').replace(',', '').strip()
            
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        logger.warning(f"Failed to convert {value} to Decimal, using 0")
        return Decimal('0')

def parseSmartMoneyWalletsAPIResponse(responseData: Union[Dict, List]) -> Optional[List[SmartMoneyWallet]]:
    """
    Parse wallet behaviour data from API response
    
    Args:
        responseData: Raw API response data (either dict or list)
        
    Returns:
        Optional[List[WalletBehaviour]]: List of parsed wallet behaviours or None if parsing fails
    """
    try:
        parsedItems = []
        
        # Handle dictionary response
        if isinstance(responseData, dict):
            # Extract data array from the response
            data = responseData.get('data', [])
            if not data:
                logger.error("No data found in response")
                return None

            for item in data:
                try:
                    # Use 'Wallet' field for wallet address
                    walletAddress = str(item.get('Wallet', ''))
                    pnl = safeDecimalConvert(item.get('pnl', 0))
                    tradeCount = int(item.get('trade_count', 0))
                    
                    # Log the raw data for debugging
                    logger.debug(f"Processing wallet item: {item}")
                    
                    if not walletAddress:
                        logger.warning("Skipping item with empty wallet address")
                        continue
                        
                    wallet = SmartMoneyWallet(
                        walletaddress=walletAddress,
                        profitandloss=pnl,
                        tradecount=tradeCount
                    )
                    parsedItems.append(wallet)
                    
                except Exception as e:
                    logger.error(f"Failed to parse wallet item: {str(e)}, raw data: {item}")
                    continue

        # Handle list response (if needed)
        elif isinstance(responseData, list):
            for item in responseData:
                try:
                    if isinstance(item, list) and len(item) >= 3:
                        wallet = SmartMoneyWallet(
                            walletaddress=str(item[0]),
                            profitandloss=safeDecimalConvert(item[1]),
                            tradecount=int(item[2])
                        )
                        parsedItems.append(wallet)
                except Exception as e:
                    logger.error(f"Failed to parse wallet item: {str(e)}, raw data: {item}")
                    continue
        else:
            logger.error(f"Unexpected response type: {type(responseData)}")
            return None

        if not parsedItems:
            logger.warning("No valid wallet items were parsed")
            return None

        logger.info(f"Successfully parsed {len(parsedItems)} wallet items")
        return parsedItems

    except Exception as e:
        logger.error(f"Failed to parse wallet behaviour response: {str(e)}")
        logger.error(f"Raw response data: {responseData}")
        return None 