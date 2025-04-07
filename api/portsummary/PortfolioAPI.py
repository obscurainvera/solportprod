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

@portfolio_bp.route('/api/portfolio/update', methods=['POST', 'OPTIONS'])
def handlePortSummaryUpdate():
    """API endpoint to manually trigger portfolio update"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        db = PortfolioDB()
        portfolioScheduler = PortfolioScheduler(db)

        # Execute portfolio analysis
        logger.info("Starting manual portfolio update")
        result = portfolioScheduler.handlePortfolioSummaryUpdate()

        return jsonify({
            'status': 'success',
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

    except Exception as e:
        logger.error(f"Manual portfolio update error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@portfolio_bp.route('/api/portfolio/status', methods=['GET', 'OPTIONS'])
def getPortfolioStatusTypes():
    """API endpoint to get all portfolio status types"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
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
        
        return jsonify({
            'status': 'success',
            'data': statuses
        })
        
    except Exception as e:
        logger.error(f"Error getting portfolio statuses: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

