from config.Config import get_config
from flask import jsonify, Blueprint, request
from database.operations.PortfolioDB import PortfolioDB
from actions.SMWalletTopPNLTokensInvestmentDetailsAction import SMWalletTopPNLTokensInvestmentDetailsAction
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

smwallet_top_pnl_token_investment_bp = Blueprint('smwallet_top_pnl_token_investment', __name__)

@smwallet_top_pnl_token_investment_bp.route('/api/smwallettoppnltokeninvestment/persist/all', methods=['POST', 'OPTIONS'])
def persistInvestmentDetailsForAllTopPNLTokens():
    """
    API endpoint to persist investment details for all top PNL tokens of high PNL smart money wallets
    
    This endpoint:
    1. Gets all high PNL wallets
    2. For each wallet, gets all tokens they've invested in
    3. Filters to only include the top 30% and bottom 20% of tokens by unprocessedpnl
    4. Processes and persists investment details for these filtered tokens
    
    Returns:
        JSON response with success status
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]

        if not validCookies:
            logger.error("No valid cookies available for investment detail processing")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available'
            }), 400

        db = PortfolioDB()
        action = SMWalletTopPNLTokensInvestmentDetailsAction(db)
        
        success = action.handleInvestmentDetailsOfAllHighPNLSMWallets(cookie=validCookies[0])
        
        if success:
            logger.info("Successfully updated investment details for top/bottom performing tokens")
            return jsonify({
                'status': 'success',
                'message': 'Successfully updated investment details for top and bottom performing tokens of high PNL wallets'
            })
        
        logger.error("Failed to update investment details for tokens")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update investment details for tokens'
        }), 500

    except Exception as e:
        logger.error(f"API Error in persist/all: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@smwallet_top_pnl_token_investment_bp.route('/api/smwallettoppnltokeninvestment/persist/wallet', methods=['POST', 'OPTIONS'])
def persistInvestmentDetailsForAllTopPNLTokensForASpecificWallet():
    """Update all tokens for a specific wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.get_json()
        walletAddress = data.get('wallet_address')
        
        if not walletAddress:
            logger.warning("Wallet address missing in investment details request")
            return jsonify({
                'status': 'error',
                'message': 'Wallet address is required'
            }), 400

        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]

        if not validCookies:
            logger.error("No valid cookies available for wallet-specific investment detail processing")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available'
            }), 400

        db = PortfolioDB()
        action = SMWalletTopPNLTokensInvestmentDetailsAction(db)
        
        success = action.handleInvestmentDetailsOfASpecificWallet(walletAddress, cookie=validCookies[0])
        
        if success:
            logger.info(f"Successfully updated tokens for wallet {walletAddress}")
            return jsonify({
                'status': 'success',
                'message': f'Successfully updated tokens for wallet {walletAddress}'
            })
        
        logger.error(f"Failed to update tokens for wallet {walletAddress}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to update tokens for wallet {walletAddress}'
        }), 500

    except Exception as e:
        logger.error(f"API Error in persist/wallet: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@smwallet_top_pnl_token_investment_bp.route('/api/smwallettoppnltokeninvestment/persist/wallet/token', methods=['POST', 'OPTIONS'])
def persistInvestmentDetailsForASpecificTokenHeldByASMWallet():
    """Update a specific token for a specific wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.get_json()
        walletAddress = data.get('wallet_address')
        tokenAddress = data.get('token_address')
        
        if not walletAddress or not tokenAddress:
            logger.warning("Wallet or token address missing in token investment details request")
            return jsonify({
                'status': 'error',
                'message': 'Wallet address and token address are required'
            }), 400

        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]

        if not validCookies:
            logger.error("No valid cookies available for specific token investment detail processing")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available'
            }), 400

        db = PortfolioDB()
        action = SMWalletTopPNLTokensInvestmentDetailsAction(db)
        
        success = action.findInvestmentDataForToken(walletAddress, tokenAddress, cookie=validCookies[0])
        
        if success:
            logger.info(f"Successfully updated token {tokenAddress} for wallet {walletAddress}")
            return jsonify({
                'status': 'success',
                'message': f'Successfully updated token {tokenAddress} for wallet {walletAddress}'
            })
        
        logger.error(f"Failed to update token {tokenAddress} for wallet {walletAddress}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to update token {tokenAddress} for wallet {walletAddress}'
        }), 500

    except Exception as e:
        logger.error(f"API Error in persist/wallet/token: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@smwallet_top_pnl_token_investment_bp.route('/api/smwallettoppnltokeninvestment/persist/all/notokensfilter', methods=['POST', 'OPTIONS'])
def persistInvestmentDetailsForAllTokensNoFiltering():
    """
    API endpoint to persist investment details for ALL tokens of high PNL wallets without filtering.
    This processes every token instead of just top 30% and bottom 20%.
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]

        if not validCookies:
            logger.error("No valid cookies available for unfiltered investment detail processing")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available'
            }), 400

        db = PortfolioDB()
        action = SMWalletTopPNLTokensInvestmentDetailsAction(db)
        
        # Use the new function that processes all tokens without filtering
        success = action.handleInvestmentDetailsOfAllTokens(cookie=validCookies[0])
        
        if success:
            logger.info("Successfully updated investment details for ALL tokens (no filtering)")
            return jsonify({
                'status': 'success',
                'message': 'Successfully updated investment details for ALL tokens of high PNL wallets (no filtering)'
            })
        
        logger.error("Failed to update investment details for unfiltered tokens")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update investment details for tokens'
        }), 500

    except Exception as e:
        logger.error(f"API Error in persist/all/notokensfilter: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@smwallet_top_pnl_token_investment_bp.route('/api/smwallettoppnltokeninvestment/persist/wallet/filtered', methods=['POST', 'OPTIONS'])
def persistInvestmentDetailsForWalletWithCustomFiltering():
    """
    API endpoint to persist investment details for a specific wallet with custom filtering options.
    Allows specifying whether to filter tokens and the percentiles to use.
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.json
        wallet_address = data.get('walletAddress')
        filter_tokens = data.get('filterTokens', True)
        top_percent = float(data.get('topPercent', 0.3))
        bottom_percent = float(data.get('bottomPercent', 0.2))
        
        if not wallet_address:
            logger.warning("Wallet address missing in custom filtering request")
            return jsonify({
                'status': 'error',
                'message': 'Wallet address is required'
            }), 400
            
        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]

        if not validCookies:
            logger.error("No valid cookies available for custom filtered investment detail processing")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available'
            }), 400

        db = PortfolioDB()
        action = SMWalletTopPNLTokensInvestmentDetailsAction(db)
        
        # Use the new flexible wallet processing function with optional filtering
        success = action.handleInvestmentDetailsForWallet(
            walletAddress=wallet_address,
            cookie=validCookies[0],
            filter_tokens=filter_tokens,
            top_percent=top_percent,
            bottom_percent=bottom_percent
        )
        
        filter_msg = f"top {int(top_percent*100)}% and bottom {int(bottom_percent*100)}%" if filter_tokens else "no filtering"
        
        if success:
            logger.info(f"Successfully updated investment details for wallet {wallet_address} with {filter_msg}")
            return jsonify({
                'status': 'success',
                'message': f'Successfully updated investment details for wallet {wallet_address} with {filter_msg}'
            })
        
        logger.error(f"Failed to update investment details for wallet {wallet_address} with {filter_msg}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to update investment details for wallet {wallet_address}'
        }), 500

    except Exception as e:
        logger.error(f"API Error in persist/wallet/filtered: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 