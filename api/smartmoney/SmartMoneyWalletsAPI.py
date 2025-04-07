from config.Config import get_config
from flask import jsonify, Blueprint, request
from database.operations.PortfolioDB import PortfolioDB
from actions.SmartMoneyWalletsAction import SmartMoneyWalletsAction
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from database.smartmoneywallets.WalletPNLStatusEnum import SmartWalletPnlStatus
from scheduler.SmartMoneyWalletScheduler import SmartMoneyWalletScheduler
logger = get_logger(__name__)

smart_money_wallets_bp = Blueprint('smart_money_wallets', __name__)

@smart_money_wallets_bp.route('/api/smartmoneywallets/persist', methods=['POST', 'OPTIONS'])
def persistAllSmartMoneyWallets():
    """Persist all smart money wallets"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        logger.info("Starting smart money wallets persistence")
        scheduler = SmartMoneyWalletScheduler()
        result = scheduler.persistAllSmartMoneyWallets()
        
        if not result:
            logger.warning("Smart money wallets persistence returned empty result")
            return jsonify({
                'status': 'error',
                'message': 'No wallets processed or configuration issue'
            }), 500
        
        total_wallets = result.get('total_processed', 0)
        logger.info(f"Successfully persisted {total_wallets} smart money wallets")
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully persisted {total_wallets} smart money wallets',
            'results': {
                'total_processed': total_wallets,
                'wallets_added': result.get('wallets_added', 0),
                'wallets_updated': result.get('wallets_updated', 0),
                'wallets_unchanged': result.get('wallets_unchanged', 0),
                'wallets_failed': result.get('wallets_failed', 0)
            }
        })

    except Exception as e:
        logger.error(f"Error persisting smart money wallets: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@smart_money_wallets_bp.route('/api/smartmoneywallets/persist/<wallet_address>', methods=['POST', 'OPTIONS'])
def persistSingleSmartMoneyWallet(wallet_address):
    """Persist a specific smart money wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        if not wallet_address:
            logger.warning("Wallet address is missing")
            return jsonify({
                'status': 'error',
                'message': 'Wallet address is required'
            }), 400
            
        logger.info(f"Starting persistence for smart money wallet: {wallet_address}")
        scheduler = SmartMoneyWalletScheduler()
        result = scheduler.persistSingleSmartMoneyWallet(wallet_address)
        
        if not result:
            logger.warning(f"Failed to persist wallet {wallet_address}: No data returned")
            return jsonify({
                'status': 'error',
                'message': f'Failed to persist wallet {wallet_address}'
            }), 500
            
        logger.info(f"Successfully persisted smart money wallet: {wallet_address}")
        return jsonify({
            'status': 'success',
            'message': f'Successfully persisted smart money wallet: {wallet_address}',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error persisting smart money wallet {wallet_address}: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@smart_money_wallets_bp.route('/api/smartmoneywallets/list', methods=['GET', 'OPTIONS'])
def getWalletBehaviours():
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = PortfolioDB()
        wallets = db.smartMoneyWallets.getAllSmartMoneyWallets()
        
        response = jsonify({
            'wallets': [{
                'address': w['walletaddress'],
                'pnl': float(w['profitandloss']),
                'trades': w['tradecount'],
                'lastUpdate': w['lastupdatetime'],
                'status': w['status'],
                'statusDescription': SmartWalletPnlStatus.getDescription(w['status'])
            } for w in wallets]
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        response = jsonify({'error': str(e)})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500 