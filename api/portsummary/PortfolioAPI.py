from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from scheduler.PortfolioScheduler import PortfolioScheduler
from config.Security import COOKIE_MAP, isValidCookie
from config.PortfolioStatusEnum import PortfolioStatus
from logs.logger import get_logger

logger = get_logger(__name__)

# Create a Blueprint for portfolio endpoints
portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/api/portsummary/update', methods=['POST', 'OPTIONS'])
def handlePortSummaryUpdate():
    """API endpoint to manually trigger portfolio update"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = PortfolioDB()
        portfolioScheduler = PortfolioScheduler(db)

        # Execute portfolio analysis
        logger.info("Starting manual portfolio update")
        result = portfolioScheduler.handlePortfolioSummaryUpdate()

        response = jsonify({
            'success': True,
            'message': 'Portfolio summary updated successfully',
            'stats': {
                'categoriesProcessed': result.get('categoriesProcessed', 0),
                'totalTokensProcessed': result.get('totalTokensProcessed', 0),
                'uniqueTokensProcessed': result.get('uniqueTokensProcessed', 0),
                'tokensInserted': result.get('tokensInserted', 0),
                'tokensUpdated': result.get('tokensUpdated', 0),
                'tokensReactivated': result.get('tokensReactivated', 0),
                'tokensMarkedInactive': result.get('tokensMarkedInactive', 0)
            }
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response

    except Exception as e:
        logger.error(f"Manual portfolio update error: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

@portfolio_bp.route('/api/portsummary/status', methods=['GET'])
def getPortfolioStatusTypes():
    """API endpoint to get all portfolio status types"""
    try:
        # Convert enum values to a list of dictionaries
        statuses = [
            {
                'code': status.statuscode,
                'name': status.statusname,
                'enum_name': status.name
            }
            for status in PortfolioStatus
        ]
        
        response = jsonify({
            'success': True,
            'data': statuses
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response
        
    except Exception as e:
        logger.error(f"Error getting portfolio statuses: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

