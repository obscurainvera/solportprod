from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from actions.WalletsInvestedInvestmentDetailsAction import WalletsInvestedInvestmentDetailsAction
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from decimal import Decimal
from scheduler.WalletsInvestedInvestmentDetailsScheduler import WalletsInvestedInvestmentDetailsScheduler

logger = get_logger(__name__)

wallets_invested_investement_details_bp = Blueprint('wallets_invested_investement_details', __name__)

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/token/wallet', methods=['POST', 'OPTIONS'])
def updateWalletInvesmentDetailsOfASMWalletForASpecificToken():
    """API endpoint to trigger transaction analysis for specific wallet and token"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get parameters from request
        data = request.get_json()
        tokenId = data.get('token_id')
        walletAddress = data.get('wallet_address')

        # Validate required parameters
        if not tokenId or not walletAddress:
            logger.warning(f"Missing required parameters: token_id={tokenId}, wallet_address={walletAddress}")
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: token_id and wallet_address'
            }), 400

        db = PortfolioDB()
        
        # Get wallet invested ID using the handler method
        walletInvestedId = db.walletsInvested.getWalletInvestedId(tokenId, walletAddress)
        
        if not walletInvestedId:
            logger.warning(f"No wallet invested record found for token {tokenId} and wallet {walletAddress}")
            return jsonify({
                'status': 'error',
                'message': f'No wallet invested record found for token {tokenId} and wallet {walletAddress}'
            }), 404
            
        # Get valid cookies for transaction analysis
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]
        
        if not validCookies:
            logger.error("No valid cookies available for transaction analysis")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available for transaction analysis'
            }), 400
            
        # Execute transaction analysis
        logger.info(f"Starting transaction analysis for wallet {walletAddress} and token {tokenId}")
        action = WalletsInvestedInvestmentDetailsAction(db)
        success = action.updateInvestmentData(
            cookie=validCookies[0],
            walletAddress=walletAddress,
            tokenId=tokenId,
            walletInvestedId=walletInvestedId
        )
        
        if success:
            logger.info(f"Transaction analysis completed for wallet {walletAddress} and token {tokenId}")
            return jsonify({
                'status': 'success',
                'message': f'Transaction analysis completed for wallet {walletAddress} and token {tokenId}',
                'data': {
                    'wallet_invested_id': walletInvestedId
                }
            })
        else:
            logger.error(f"Failed to complete transaction analysis for wallet {walletAddress} and token {tokenId}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to complete transaction analysis for wallet {walletAddress} and token {tokenId}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in wallet investment details analysis: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/token/all', methods=['POST', 'OPTIONS'])
def updateInvestmentDetailsOfAllSMWalletsInvestedInASpecificToken():
    """API endpoint to trigger transaction analysis for all wallets invested in a specific token"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get token ID from request
        data = request.get_json()
        tokenId = data.get('token_id')
        
        if not tokenId:
            logger.warning("Missing required parameter: token_id")
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: token_id'
            }), 400
            
        # Get valid cookies for transaction analysis
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]
        
        if not validCookies:
            logger.error("No valid cookies available for transaction analysis")
            return jsonify({
                'status': 'error',
                'message': 'No valid cookies available for transaction analysis'
            }), 400
            
        # Execute transaction analysis for all wallets invested in the token
        logger.info(f"Starting transaction analysis for all wallets invested in token {tokenId}")
        scheduler = WalletsInvestedInvestmentDetailsScheduler()
        scheduler.handleInvestmentDetailsOfAllWalletsInvestedInAToken(tokenId, cookie=validCookies[0])
        
        logger.info(f"Transaction analysis initiated for all wallets invested in token {tokenId}")
        return jsonify({
            'status': 'success',
            'message': f'Transaction analysis initiated for all wallets invested in token {tokenId}'
        })
        
    except Exception as e:
        logger.error(f"Error in wallet investment details analysis for all wallets: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/all', methods=['POST', 'OPTIONS'])
def updateInvestmentDetailsOfAllSMWalletsAboveCertainHoldings():
    """
    API endpoint to trigger transaction analysis for all wallets above specified smart holding
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get parameters from request
        data = request.get_json()
        minSmartHolding = data.get('min_smart_holding')

        # Convert to Decimal if provided
        if minSmartHolding:
            try:
                minSmartHolding = Decimal(str(minSmartHolding))
            except Exception as e:
                logger.warning(f"Invalid min_smart_holding value: {minSmartHolding}")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid min_smart_holding value: {str(e)}'
                }), 400

        logger.info(f"Starting smart wallet analysis with min_smart_holding: {minSmartHolding or 'default'}")
        db = PortfolioDB()
        scheduler = WalletsInvestedInvestmentDetailsScheduler(db)
        
        # Execute analysis with provided threshold
        scheduler.analyzeSMWalletInvestment(minSmartHolding=minSmartHolding)
        
        logger.info("Smart wallet analysis scheduled successfully")
        return jsonify({
            'status': 'success',
            'message': 'Smart wallet analysis scheduled successfully',
            'data': {
                'min_smart_holding': str(minSmartHolding) if minSmartHolding else str(WalletsInvestedInvestmentDetailsAction.MIN_SMART_HOLDING)
            }
        })

    except Exception as e:
        logger.error(f"Smart wallet analysis API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500 