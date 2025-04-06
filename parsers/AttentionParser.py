from config.Config import get_config
from typing import List, Optional, Dict, Any
from database.operations.schema import AttentionData
from decimal import Decimal
from datetime import datetime
from logs.logger import get_logger
import pytz
import hashlib

logger = get_logger(__name__)

def parseAttentionData(apiResponse: Dict[str, Any]) -> Optional[List[AttentionData]]:
    """
    Parse attention data from the API response.
    
    Args:
        apiResponse: The JSON response from the API
        
    Returns:
        Optional[List[AttentionData]]: List of parsed attention data items or None if no valid items
    """
    # Get current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    currentTime = datetime.now(ist)
    parsedItems = []
    
    logger.info(f"Processing API response with {len(apiResponse.keys())} data keys")
    
    # Track counts for different formats
    formatCounts = {
        'chain_x_format': 0,
        'token_id_x_format': 0,
        'perps_format': 0,
        'unknown_format': 0,
        'skipped_att_score_norm': 0
    }
    
    # Process all data keys that contain token information
    for key in apiResponse.keys():
        if not key.startswith('data'):
            continue
            
        dataItems = apiResponse.get(key, [])
        if not dataItems or not isinstance(dataItems, list):
            logger.debug(f"Skipping {key}: not a list or empty")
            continue
            
        logger.info(f"Processing {key} with {len(dataItems)} items")
        
        # Process each item in the data key
        for item in dataItems:
            try:
                # Skip items that contain att_score_norm
                if 'att_score_norm' in item:
                    formatCounts['skipped_att_score_norm'] += 1
                    logger.debug(f"Skipping item with att_score_norm: {item.get('token_symbol', 'unknown')}")
                    continue

                attentionData = None
                
                # Process based on format type
                if 'chain_x' in item and 'token_id' in item: #for all onchain tokens
                    attentionData = _parse_chain_x_format(item, currentTime)
                    formatCounts['chain_x_format'] += 1
                    
                elif 'token_id_x' in item:
                    attentionData = _parse_token_id_x_format(item, currentTime)
                    formatCounts['token_id_x_format'] += 1
                
                elif 'token_symbol' in item and ('att_score_pct' in item): #for all perps tokens
                    attentionData = _parse_perps_format(item, currentTime)
                    formatCounts['perps_format'] += 1
                
                else:
                    # Unknown format
                    logger.warning(f"Unknown item format in {key}: {item}")
                    formatCounts['unknown_format'] += 1
                    continue
                
                if attentionData:
                    parsedItems.append(attentionData)
                    
            except Exception as e:
                logger.error(f"Failed to parse item: {str(e)}, raw item: {item}")
                continue
    
    # Log format counts
    logger.info(f"Format counts - Chain_x: {formatCounts['chain_x_format']}, " +
                f"Token_id_x: {formatCounts['token_id_x_format']}, " +
                f"Perps: {formatCounts['perps_format']}, " +
                f"Unknown: {formatCounts['unknown_format']}, " +
                f"Skipped att_score_norm: {formatCounts['skipped_att_score_norm']}")
    
    logger.info(f"Successfully parsed {len(parsedItems)} attention data items")
    return parsedItems if parsedItems else None


def _parse_chain_x_format(item: Dict[str, Any], currentTime: datetime) -> Optional[AttentionData]:
    """
    Parse an item with chain_x and token_id format.
    
    Args:
        item: The item to parse
        currentTime: The current time
        
    Returns:
        Optional[AttentionData]: The parsed attention data or None if parsing fails
    """
    chain = item.get('chain_x', '').lower()
    token_id = item.get('token_id', '')
    token_symbol = item.get('token_symbol', '')
    
    logger.debug(f"Processing token {token_symbol} ({token_id}) on chain {chain}")
    
    # Skip non-solana tokens if needed
    # if chain != 'sol':
    #    logger.debug(f"Skipping non-solana token: {token_symbol} on {chain}")
    #    return None
    
    # Get attention score from either att_score_pct or att_score_norm
    attention_score = _get_attention_score(item)
    
    return AttentionData(
        tokenid=str(token_id),
        name=str(token_symbol),
        chain=chain,
        attentionscore=Decimal(str(attention_score)),
        recordedat=currentTime,
        datasource='chainedge',
        change1dbps=_convertToBps(item.get('1d_chg_bps')),
        change7dbps=_convertToBps(item.get('7d_chg_bps')),
        change30dbps=_convertToBps(item.get('30d_chg_bps'))
    )


def _parse_token_id_x_format(item: Dict[str, Any], currentTime: datetime) -> Optional[AttentionData]:
    """
    Parse an item with token_id_x format.
    
    Args:
        item: The item to parse
        currentTime: The current time
        
    Returns:
        Optional[AttentionData]: The parsed attention data or None if parsing fails
    """
    token_id = item.get('token_id_x', '')
    token_symbol = item.get('token_symbol', '')
    
    logger.debug(f"Processing token with old format: {token_symbol} ({token_id})")
    
    # Get attention score from either att_score_pct or att_score_norm
    attention_score = _get_attention_score(item)
    
    return AttentionData(
        tokenid=str(token_id),
        name=str(token_symbol),
        chain='solana',
        attentionscore=Decimal(str(attention_score)),
        recordedat=currentTime,
        datasource='chainedge',
        change1dbps=_convertToBps(item.get('1d_chg_bps')),
        change7dbps=_convertToBps(item.get('7d_chg_bps')),
        change30dbps=_convertToBps(item.get('30d_chg_bps'))
    )


def _parse_perps_format(item: Dict[str, Any], currentTime: datetime) -> Optional[AttentionData]:
    """
    Parse an item with perps format (no chain or token_id).
    
    Args:
        item: The item to parse
        currentTime: The current time
        
    Returns:
        Optional[AttentionData]: The parsed attention data or None if parsing fails
    """
    token_symbol = item.get('token_symbol', '')
    
    logger.info(f"Processing token in perps format: {token_symbol}")
    
    # Generate a deterministic token ID based on the symbol if needed
    # Note: We're making tokenid optional now, so we can leave it empty
    # But for backward compatibility, we'll generate one
    token_id = ""
    if token_symbol:
        token_id = f"perps_{hashlib.md5(token_symbol.encode()).hexdigest()}"
    
    # Get attention score
    attention_score = _get_attention_score(item)
    
    return AttentionData(
        tokenid=token_id,  # This can be empty
        name=str(token_symbol),
        chain='perps',  # Set chain as 'perps' for this format
        attentionscore=Decimal(str(attention_score)),
        recordedat=currentTime,
        datasource='chainedge',
        change1dbps=_convertToBps(item.get('1d_chg_bps')),
        change7dbps=_convertToBps(item.get('7d_chg_bps')),
        change30dbps=_convertToBps(item.get('30d_chg_bps'))
    )


def _get_attention_score(item: Dict[str, Any]) -> float:
    """
    Extract the attention score from an item.
    Only accepts att_score_pct as valid score type.
    
    Args:
        item: The item to extract the attention score from
        
    Returns:
        float: The attention score or 0 if not found
    """
    return item.get('att_score_pct', 0)


def _convertToBps(value) -> Optional[int]:
    """
    Convert various input formats to basis points (bps)
    
    Args:
        value: Input value that could be string 'Np', float, or other formats
        
    Returns:
        Optional[int]: Converted bps value or None if conversion fails
    """
    try:
        # Handle None case
        if value is None:
            return None
            
        # Handle 'Np' case (Not present) or empty string
        if isinstance(value, str):
            if value.lower() == 'np' or value.strip() == '':
                return None
                
            # Try to convert string to number
            try:
                return int(float(value))
            except (ValueError, TypeError):
                logger.warning(f"Could not convert string value to bps: {value}")
                return None
            
        # Handle numeric case (float or int)
        if isinstance(value, (float, int)):
            return int(value)
                
        # If we get here, we don't know how to handle the value
        logger.warning(f"Unknown bps value type: {type(value)}, value: {value}")
        return None
        
    except Exception as e:
        logger.error(f"Failed to convert bps value: {str(e)}, value: {value}")
        return None


def parseSolanaAttentionData(apiResponse: Dict[str, Any]) -> Optional[List[AttentionData]]:
    """
    Parse Solana attention data from the API response of attention_score_query_sol endpoint.
    
    Args:
        apiResponse: The JSON response from the API
        
    Returns:
        Optional[List[AttentionData]]: List of parsed attention data items or None if no valid items
    """
    # Get current time in IST
    ist = pytz.timezone('Asia/Kolkata')
    currentTime = datetime.now(ist)
    parsedItems = []
    
    logger.info(f"Processing Solana attention score API response")
    
    # The API returns data with key 'data10' and visualization data with key 'sol_default_30d'
    # We only care about the 'data10' part for parsing
    dataItems = apiResponse.get('data10', [])
    
    if not dataItems or not isinstance(dataItems, list):
        logger.warning(f"No valid data found in 'data10' key or it's not a list")
        return None
        
    logger.info(f"Found {len(dataItems)} items in 'data10'")
    
    # Track count of successfully parsed items
    successfully_parsed = 0
    
    # Process each item in data10
    for item in dataItems:
        try:
            # The Solana API format typically has token_id_x and chain_x 
            if 'token_id_x' in item and 'chain_x' in item:
                token_id = item.get('token_id_x', '')
                token_symbol = item.get('token_symbol', '')
                
                logger.debug(f"Processing Solana token {token_symbol} ({token_id})")
                
                # Get attention score
                attention_score = _get_attention_score(item)
                
                # Create AttentionData object
                attentionData = AttentionData(
                    tokenid=str(token_id),
                    name=str(token_symbol),
                    chain='solana',  # Always use 'solana' for this endpoint
                    attentionscore=Decimal(str(attention_score)),
                    recordedat=currentTime,
                    datasource='chainedge',  # Distinguish from the original datasource
                    change1dbps=_convertToBps(item.get('1d_chg_bps')),
                    change7dbps=_convertToBps(item.get('7d_chg_bps')),
                    change30dbps=_convertToBps(item.get('30d_chg_bps'))
                )
                
                if attentionData:
                    parsedItems.append(attentionData)
                    successfully_parsed += 1
            else:
                logger.warning(f"Item missing required fields: {item}")
                
        except Exception as e:
            logger.error(f"Failed to parse Solana attention item: {str(e)}, raw item: {item}")
            continue
    
    logger.info(f"Successfully parsed {successfully_parsed} Solana attention data items")
    return parsedItems if parsedItems else None 