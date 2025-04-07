from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from actions.WalletsInvestedAction import WalletsInvestedAction
from scheduler.WalletsInvestedScheduler import WalletsInvestedScheduler
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from decimal import Decimal
from database.operations.schema import WalletInvestedStatusEnum

logger = get_logger(__name__)

# Create a Blueprint for token analysis endpoints
wallets_invested_bp = Blueprint('wallets_invested', __name__)

@wallets_invested_bp.route('/api/walletsinvested/persist/token/<token_id>', methods=['POST', 'OPTIONS'])
def persistAllWalletsInvestedInASpecificPortSummarytoken(token_id):
    """API endpoint to trigger wallets invested analysis"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        if not token_id:
            logger.warning("Token ID missing in request")
            return jsonify({
                'status': 'error',
                'message': 'Token ID is required'
            }), 400
    
        db = PortfolioDB()
        walletInvestedAction = WalletsInvestedAction(db)

        # 1. Check if token exists in portsummary
        tokenInfo = db.portfolio.getTokenDataFromPortSummary(token_id)
        if not tokenInfo:
            logger.warning(f"Token {token_id} not found in portfolio summary")
            return jsonify({
                'status': 'error',
                'message': f'Token {token_id} not found in portfolio summary'
            }), 404

        # 2. Get valid cookie for token analysis
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('walletsinvested', {})
            if isValidCookie(cookie, 'walletsinvested')
        ]

        if not validCookies:
            logger.error("No valid cookies available for wallets invested analysis")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available for wallets invested analysis'
            }), 400

        # 3. Execute token analysis
        logger.info(f"Starting wallets invested analysis for {token_id}")
        result = walletInvestedAction.fetchAndPersistWalletsInvestedInASpecificToken(
            cookie=validCookies[0],
            tokenId=token_id,
            portsummaryId=tokenInfo['portsummaryid']
        )

        if result:
            logger.info(f"Wallets invested analysis completed for {token_id}, found {len(result)} wallets")
            return jsonify({
                'status': 'success',
                'message': f'Wallets invested analysis completed for {token_id}',
                'data': {
                    'token_id': token_id,
                    'portsummary_id': tokenInfo['portsummaryid'],
                    'analysis_count': len(result)
                }
            })
        
        logger.error(f"Failed to get analysis data for token {token_id}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to get analysis data for token {token_id}'
        }), 500

    except Exception as e:
        logger.error(f"Error in wallets invested analysis: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@wallets_invested_bp.route('/api/walletsinvested/persist/all', methods=['POST', 'OPTIONS'])
def persistAllSMWalletsInvestedInAnyPortSummaryToken():
    """API endpoint to trigger wallets invested analysis for all tokens"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        # Execute analysis for all tokens
        logger.info("Starting wallets invested analysis for all tokens")
        db = PortfolioDB()
        scheduler = WalletsInvestedScheduler()
        scheduler.handleWalletsInvestedInPortSummaryTokens()
        
        logger.info("Wallets invested analysis initiated for all tokens")
        return jsonify({
            'status': 'success',
            'message': 'Wallets invested analysis initiated for all tokens'
        })

    except Exception as e:
        logger.error(f"Error in wallets invested analysis for all tokens: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@wallets_invested_bp.route('/api/walletsinvested/token/<token_id>', methods=['GET', 'OPTIONS'])
def getWalletsInvestedInToken(token_id):
    """Get all wallets invested in a specific token with their investment details"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        logger.info(f"Retrieving wallets invested in token {token_id}")
        with PortfolioDB() as db:
            # Get all wallets invested in this token
            # We use a very small minimum balance to get all wallets
            wallets = db.walletsInvested.getWalletsWithHighSMTokenHoldings(
                minBalance=Decimal('0.001'), 
                tokenId=token_id
            )
            
            if not wallets:
                logger.warning(f"No wallets found for token {token_id}")
                return jsonify({
                    'status': 'success',
                    'data': [],
                    'token_id': token_id,
                    'count': 0
                })
        
            # Get detailed information for each wallet
            detailed_wallets = []
            for wallet in wallets:
                wallet_id = wallet.get('walletinvestedid')
                wallet_details = db.walletsInvested.getWalletInvestedById(wallet_id)
                
                if wallet_details:
                    # Format the data to include only the required fields
                    formatted_wallet = {
                        'walletaddress': wallet_details.get('walletaddress'),
                        'walletname': wallet_details.get('walletname'),
                        'coinquantity': wallet_details.get('coinquantity'),
                        'smartholding': wallet_details.get('smartholding'),
                        'totalinvestedamount': wallet_details.get('totalinvestedamount'),
                        'amounttakenout': wallet_details.get('amounttakenout'),
                        'totalcoins': wallet_details.get('totalcoins'),
                        'avgentry': wallet_details.get('avgentry'),
                        'tags': wallet_details.get('tags'),
                        'chainedgepnl': wallet_details.get('chainedgepnl'),
                        'status': wallet_details.get('status')
                    }
                    detailed_wallets.append(formatted_wallet)
            
            # Sort by smartholding in descending order
            detailed_wallets.sort(key=lambda x: float(x.get('smartholding', 0) or 0), reverse=True)
            
            logger.info(f"Retrieved {len(detailed_wallets)} wallets for token {token_id}")
            return jsonify({
                'status': 'success',
                'data': detailed_wallets,
                'token_id': token_id,
                'count': len(detailed_wallets)
            })
            
    except Exception as e:
        logger.error(f"Error getting wallets for token {token_id}: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Failed to retrieve wallets: {str(e)}'
        }), 500 