from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger

logger = get_logger(__name__)

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/api/reports/portsummary', methods=['GET'])
def getPortSummaryReport():
    """API endpoint to get filtered portfolio summary report"""
    try:
        # Get filter parameters
        filters = {
            'tokenid': request.args.get('tokenid'),
            'name': request.args.get('name'),
            'smartbalance_op': request.args.get('smartbalance_op'),
            'smartbalance_val': request.args.get('smartbalance_val'),
            'limit': request.args.get('limit', type=int),
            'offset': request.args.get('offset', type=int)
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Validate smartbalance operator if provided
        if filters.get('smartbalance_op'):
            valid_ops = ['>', '<', '>=', '<=', '=']
            if filters['smartbalance_op'] not in valid_ops:
                return jsonify({
                    'error': f'Invalid operator. Must be one of: {", ".join(valid_ops)}'
                }), 400
        
        # Get report data
        db = PortfolioDB()
        data = db.reports.getPortSummaryReport(filters)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500 