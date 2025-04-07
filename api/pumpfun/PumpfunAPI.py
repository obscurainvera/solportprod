from config.Config import get_config
from flask import jsonify, Blueprint, request
from scheduler.PumpfunScheduler import PumpFunScheduler
from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

pumpfun_bp = Blueprint('pumpfun', __name__)

@pumpfun_bp.route('/api/pumpfun/fetch-tokens-scheduled', methods=['POST', 'OPTIONS'])
def schedulePumpfunTokensFetch():
    """Execute the scheduler's execute_actions function for pumpfun tokens"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
         
    try:
        scheduler = PumpFunScheduler()
        scheduler.handlePumpFunAnalysisFromAPI()
        
        logger.info("Successfully triggered scheduled pumpfun tokens fetch")
        return jsonify({
            'status': 'success',
            'message': 'Successfully triggered scheduled pumpfun tokens fetch'
        })

    except Exception as e:
        logger.error(f"API Error in schedulePumpfunTokensFetch: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500 

# Add a new endpoint that matches the one used in the frontend
@pumpfun_bp.route('/api/pumpfun/fetch', methods=['POST', 'OPTIONS'])
def fetchPumpfunTokens():
    """Alias for schedulePumpfunTokensFetch to match frontend endpoint"""
    return schedulePumpfunTokensFetch() 