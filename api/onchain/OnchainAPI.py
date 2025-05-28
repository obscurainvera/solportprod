from config.Config import get_config
from flask import jsonify, Blueprint, request
from scheduler.OnchainScheduler import OnchainScheduler
from actions.OnchainAction import OnchainAction
from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

onchain_bp = Blueprint('onchain', __name__)

@onchain_bp.route('/api/onchain/fetch-data-scheduled', methods=['POST', 'OPTIONS'])
def scheduleOnchainDataFetch():
    """Execute the scheduler's execute_actions function for onchain data"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        logger.info("Starting scheduled onchain data fetch")
        scheduler = OnchainScheduler()
        scheduler.handleOnchainAnalysisFromAPI()
        
        logger.info("Successfully triggered scheduled onchain data fetch")
        return jsonify({
            'status': 'success',
            'message': 'Successfully triggered scheduled onchain data fetch'
        })

    except Exception as e:
        logger.error(f"API Error in scheduleOnchainDataFetch: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

# Add a new endpoint that matches the one used in the frontend
@onchain_bp.route('/api/onchain/fetch', methods=['POST', 'OPTIONS'])
def fetchOnchainData():
    """Alias for scheduleOnchainDataFetch to match frontend endpoint"""
    return scheduleOnchainDataFetch()
