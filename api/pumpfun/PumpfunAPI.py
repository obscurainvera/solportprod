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
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
         
    try:
        scheduler = PumpFunScheduler()
        scheduler.handlePumpFunAnalysisFromAPI()
        
        response = jsonify({
            'success': True,
            'message': 'Successfully triggered scheduled pumpfun tokens fetch'
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response

    except Exception as e:
        logger.error(f"API Error in schedulePumpfunTokensFetch: {str(e)}")
        response = jsonify({'error': str(e)})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500 

# Add a new endpoint that matches the one used in the frontend
@pumpfun_bp.route('/api/pumpfun/fetch', methods=['POST', 'OPTIONS'])
def fetchPumpfunTokens():
    """Alias for schedulePumpfunTokensFetch to match frontend endpoint"""
    return schedulePumpfunTokensFetch() 