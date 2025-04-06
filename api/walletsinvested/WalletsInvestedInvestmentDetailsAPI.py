from config.config import get_config
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
        return handle_options_request()
        
    try:
        # Get parameters from request
        data = request.get_json()
        tokenId = data.get('token_id')
        walletAddress = data.get('wallet_address')

        # Validate required parameters
        if not tokenId or not walletAddress:
            return create_response('error', 'Missing required parameters: token_id and wallet_address', 400)

        db = PortfolioDB()
        
        # Get wallet invested ID using the handler method
        walletInvestedId = db.walletsInvested.getWalletInvestedId(tokenId, walletAddress)
        
        if not walletInvestedId:
            return create_response('error', 
                f'No wallet invested record found for token {tokenId} and wallet {walletAddress}', 404)
            
        # Get valid cookies for transaction analysis
        validCookie = get_valid_solscan_cookie()
        if not validCookie:
            return create_response('error', 'No valid cookies available for transaction analysis', 400)
            
        # Execute transaction analysis
        action = WalletsInvestedInvestmentDetailsAction(db)
        success = action.updateInvestmentData(
            cookie=validCookie,
            walletAddress=walletAddress,
            tokenId=tokenId,
            walletInvestedId=walletInvestedId
        )
        
        if success:
            return create_response('success', 
                f'Transaction analysis completed for wallet {walletAddress} and token {tokenId}',
                200, {'wallet_invested_id': walletInvestedId})
        else:
            return create_response('error', 
                f'Failed to complete transaction analysis for wallet {walletAddress} and token {tokenId}', 500)
            
    except Exception as e:
        logger.error(f"Error in wallet investment details analysis: {str(e)}")
        return create_response('error', f'Internal server error: {str(e)}', 500)

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/token/all', methods=['POST', 'OPTIONS'])
def updateInvestmentDetailsOfAllSMWalletsInvestedInASpecificToken():
    """API endpoint to trigger transaction analysis for all wallets invested in a specific token"""
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        # Get token ID from request
        data = request.get_json()
        tokenId = data.get('token_id')
        
        if not tokenId:
            return create_response('error', 'Missing required parameter: token_id', 400)
            
        # Get valid cookies for transaction analysis
        validCookie = get_valid_solscan_cookie()
        if not validCookie:
            return create_response('error', 'No valid cookies available for transaction analysis', 400)
            
        # Execute transaction analysis for all wallets invested in the token
        scheduler = WalletsInvestedInvestmentDetailsScheduler()
        scheduler.handleInvestmentDetailsOfAllWalletsInvestedInAToken(tokenId, cookie=validCookie)
        
        return create_response('success', 
            f'Transaction analysis initiated for all wallets invested in token {tokenId}')
        
    except Exception as e:
        logger.error(f"Error in wallet investment details analysis for all wallets: {str(e)}")
        return create_response('error', f'Internal server error: {str(e)}', 500)

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/all', methods=['POST', 'OPTIONS'])
def updateInvestmentDetailsOfAllSMWalletsAboveCertainHoldings():
    """
    API endpoint to trigger transaction analysis for all wallets above specified smart holding
    """
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        # Get parameters from request
        data = request.get_json()
        minSmartHolding = data.get('min_smart_holding')

        # Convert to Decimal if provided
        if minSmartHolding:
            try:
                minSmartHolding = Decimal(str(minSmartHolding))
            except Exception as e:
                return create_response('error', f'Invalid min_smart_holding value: {str(e)}', 400)

        db = PortfolioDB()
        scheduler = WalletsInvestedInvestmentDetailsScheduler(db)
        
        # Execute analysis with provided threshold
        scheduler.analyzeSMWalletInvestment(minSmartHolding=minSmartHolding)
        
        return create_response('success', 'Smart wallet analysis scheduled successfully', 200, {
            'data': {
                'min_smart_holding': str(minSmartHolding) if minSmartHolding else str(WalletsInvestedInvestmentDetailsAction.MIN_SMART_HOLDING)
            }
        })

    except Exception as e:
        logger.error(f"Smart wallet analysis API error: {str(e)}")
        return create_response('error', f'Internal server error: {str(e)}', 500)

def get_valid_solscan_cookie():
    """Helper function to get a valid Solscan cookie"""
    validCookies = [
        cookie for cookie in COOKIE_MAP.get('solscan', {})
        if isValidCookie(cookie, 'solscan')
    ]
    
    return validCookies[0] if validCookies else None

def handle_options_request():
    """Helper function to handle OPTIONS requests with CORS headers"""
    response = jsonify({})
    config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
    return response, 200

def create_response(status, message, status_code=200, additional_data=None):
    """Helper function to create consistent API responses with CORS headers"""
    response_data = {
        'status': status,
        'message': message
    }
    
    # Add any additional data to the response
    if additional_data:
        response_data.update(additional_data)
        
    response = jsonify(response_data)
    config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
    
    return response, status_code 