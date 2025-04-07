from config.Config import get_config
from flask import jsonify, Blueprint, request
from scheduler.SMWalletTopPNLTokenScheduler import SMWalletTopPNLTokenScheduler
from actions.SMWalletTopPNLTokenAction import SMWalletTopPNLTokenAction
from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

smwallet_top_pnl_token_bp = Blueprint('smwallet_top_pnl_token', __name__)

@smwallet_top_pnl_token_bp.route('/api/smwallettoppnltoken/persist', methods=['POST', 'OPTIONS'])
def persistAllSMWalletTopPNLTokens():
    """Persist all top PNL tokens for all the smart money wallets"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        scheduler = SMWalletTopPNLTokenScheduler()
        scheduler.persistAllTopPNLTokensForHighPNLSMWallets()
        
        logger.info("Successfully triggered top PNL token analysis for all eligible wallets")
        return jsonify({
            'status': 'success',
            'message': 'Successfully triggered top PNL token analysis for all eligible wallets'
        })

    except Exception as e:
        logger.error(f"API Error in persistAllSMWalletTopPNLTokens: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@smwallet_top_pnl_token_bp.route('/api/smwallettoppnltoken/wallet/persist', methods=['POST', 'OPTIONS'])
def analyzeTopPNLTokensForASpecificWallet():
    """Persist all top PNL tokens for a specific smart money wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.get_json()
        walletAddress = data.get('wallet_address')
        
        if not walletAddress:
            logger.warning("Wallet address missing in request")
            return jsonify({
                'status': 'error',
                'message': 'Wallet address is required'
            }), 400

        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('smwallettoppnltoken', {})
            if isValidCookie(cookie, 'smwallettoppnltoken')
        ]

        if not validCookies:
            logger.error("No valid cookies available for smwallettoppnltoken")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available'
            }), 400

        # Initialize action and execute
        db = PortfolioDB()
        action = SMWalletTopPNLTokenAction(db)
        
        result = action.persistAllTopPNLTokensForASMWallet(
            cookie=validCookies[0],
            walletAddress=walletAddress,
            lookbackDays=180
        )
        
        if result:
            logger.info(f"Successfully analyzed top PNL tokens for wallet {walletAddress}, found {len(result)} tokens")
            return jsonify({
                'status': 'success',
                'message': f'Successfully analyzed top PNL tokens for wallet {walletAddress}',
                'tokens_analyzed': len(result)
            })
        
        logger.warning(f"No tokens found or analysis failed for wallet {walletAddress}")
        return jsonify({
            'status': 'error',
            'message': f'No tokens found or analysis failed for wallet {walletAddress}'
        }), 404

    except Exception as e:
        logger.error(f"API Error in analyzeTopPNLTokensForASpecificWallet: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500 