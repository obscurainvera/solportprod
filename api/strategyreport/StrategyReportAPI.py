from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.strategyreport.StrategyReportHandler import StrategyReportHandler
from logs.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

strategy_report_bp = Blueprint('strategy_report', __name__)

@strategy_report_bp.route('/api/reports/strategyreport', methods=['GET', 'OPTIONS'])
def get_strategy_report():
    """API endpoint to get strategy report data with optional filtering"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get query parameters with defaults
        source = request.args.get('source', '')
        strategy_name = request.args.get('strategy_name', '')
        status = request.args.get('status', '')
        active = request.args.get('active')
        
        if active is not None:
            active = active.lower() == 'true'
            
        sort_by = request.args.get('sort_by', 'createdat')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Validate sort order
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # Get data from handler
        with PortfolioDB() as db:
            handler = StrategyReportHandler(db)
            strategies = handler.getAllStrategies(
                source=source if source else None,
                strategyname=strategy_name if strategy_name else None,
                status=status if status else None,
                active=active,
                sortBy=sort_by,
                sortOrder=sort_order
            )
        
        # Return the response
        response = jsonify({
            'status': 'success',
            'data': strategies,
            'count': len(strategies),
            'timestamp': datetime.now().isoformat()
        })
        
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 200
        
    except Exception as e:
        logger.error(f"Error in get_strategy_report: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500


@strategy_report_bp.route('/api/reports/strategyreport/<int:strategy_id>', methods=['GET', 'OPTIONS'])
def get_strategy_detail(strategy_id):
    """API endpoint to get detailed information about a specific strategy"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get data from handler
        with PortfolioDB() as db:
            handler = StrategyReportHandler(db)
            strategy = handler.getStrategyById(strategy_id)
            
        if not strategy:
            response = jsonify({
                'status': 'error',
                'message': f'Strategy with ID {strategy_id} not found',
                'timestamp': datetime.now().isoformat()
            })
            config = get_config()
            response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return response, 404
        
        # Return the response
        response = jsonify({
            'status': 'success',
            'data': strategy,
            'timestamp': datetime.now().isoformat()
        })
        
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 200
        
    except Exception as e:
        logger.error(f"Error in get_strategy_detail: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500


@strategy_report_bp.route('/api/reports/strategyexecutions', methods=['GET', 'OPTIONS'])
def get_strategy_executions_count():
    """API endpoint to get count of executions for each strategy"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get data from handler
        with PortfolioDB() as db:
            handler = StrategyReportHandler(db)
            data = handler.getStrategyExecutionsCount()
        
        # Return the response
        response = jsonify({
            'status': 'success',
            'data': data,
            'count': len(data),
            'timestamp': datetime.now().isoformat()
        })
        
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 200
        
    except Exception as e:
        logger.error(f"Error in get_strategy_executions_count: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500 