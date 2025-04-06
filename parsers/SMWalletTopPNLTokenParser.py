from config.Config import get_config
from typing import List, Dict, Any, Optional
from decimal import Decimal
from database.operations.schema import SMWalletTopPnlToken
from database.smartmoneywallets.TopTokenPNLStatusEnum  import TokenStatus
from logs.logger import get_logger

logger = get_logger(__name__)

def parseSMWalletTopPNLTokensAPIResponse(response: Dict[str, Any], walletAddress: str) -> Optional[List[SMWalletTopPnlToken]]:
    """Parse and validate top PNL token API response"""
    results = []
    
    try:
        # Get the pnl_data array from the nested structure
        pnlData = response.get('pnl_data', {}).get('pnl_data', [])
        
        for rawItem in pnlData:
            try:
                # Convert PNL to float for status determination
                pnl = float(rawItem.get('Pnl', 0))
                # Get status based on PNL threshold
                status = TokenStatus.getStatusFromPNL(pnl)
                
                # Create TopPnlToken object with validated data
                tokenItem = SMWalletTopPnlToken(
                    walletaddress=walletAddress,
                    tokenid=str(rawItem['tokenname']),  # Changed from token_id to tokenname
                    name=str(rawItem['Ticker']),        # Changed from token_name to Ticker
                    unprocessedpnl=Decimal(str(rawItem.get('Pnl', 0))),      # Changed from pnl to Pnl
                    unprocessedroi=Decimal(str(rawItem.get('roi', 0))),      # roi stays the same
                    status=status.value
                )
                
                results.append(tokenItem)
                
            except Exception as e:
                logger.error(f"Failed to parse top PNL token item: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Failed to parse top PNL token response: {e}")
        
    return results if results else None