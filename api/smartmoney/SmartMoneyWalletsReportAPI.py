from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.smartmoneywallets.SmartMoneyWalletsReportHandler import SmartMoneyWalletsReportHandler
from logs.logger import get_logger

logger = get_logger(__name__)

smartMoneyWalletsReportBp = Blueprint('smart_money_wallets_report', __name__)

@smartMoneyWalletsReportBp.route('/api/reports/smartmoneywallet/<wallet_address>', methods=['GET', 'OPTIONS'])
def get_wallet_token_details(wallet_address):
    """
    Get smart money wallet report for a specific wallet address.
    Includes overall wallet PNL from smartmoneywallet table and
    token-specific PNL data from smwallettoppnltoken table.
    
    Args:
        wallet_address: The wallet address to get details for
        
    Query Parameters:
        sort_by: Field to sort tokens by (default: profitandloss)
        sort_order: Sort order (asc or desc)
        
    Returns:
        JSON response with wallet PNL data and token details
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get query parameters
        sortBy = request.args.get('sort_by', 'profitandloss')
        sortOrder = request.args.get('sort_order', 'desc')
        
        # Use the handler to get the data
        with PortfolioDB() as db:
            handler = SmartMoneyWalletsReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'smart_money_wallets_report' not found")
                return jsonify({
                    'status': 'error',
                    'message': "Handler 'smart_money_wallets_report' not found"
                }), 500
                
            report_data = handler.getSmartMoneyWalletReport(
                walletAddress=wallet_address,
                sortBy=sortBy,
                sortOrder=sortOrder
            )
            
            # Return data with standardized success response
            return jsonify({
                'status': 'success',
                'data': report_data,
                'timestamp': db.get_current_timestamp()
            })
            
    except Exception as e:
        logger.error(f"Error in smart money wallets report API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@smartMoneyWalletsReportBp.route('/api/reports/smartmoneywallets/top', methods=['GET', 'OPTIONS'])
def get_top_smart_money_wallets():
    """
    Get top smart money wallets by PNL.
    
    Query Parameters:
        limit: Maximum number of wallets to return (default: 10)
        
    Returns:
        JSON response with top smart money wallets
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        
        # Use the handler to get the data
        with PortfolioDB() as db:
            handler = SmartMoneyWalletsReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'smart_money_wallets_report' not found")
                return jsonify({
                    'status': 'error',
                    'message': "Handler 'smart_money_wallets_report' not found"
                }), 500
                
            wallets = handler.getTopSmartMoneyWallets(limit=limit)
            
            # Return data with standardized success response
            return jsonify({
                'status': 'success',
                'data': {'wallets': wallets},
                'count': len(wallets),
                'timestamp': db.get_current_timestamp()
            })
            
    except Exception as e:
        logger.error(f"Error in top smart money wallets API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 