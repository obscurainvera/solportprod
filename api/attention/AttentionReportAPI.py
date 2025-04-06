from config.config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.attention.AttentionReportHandler import AttentionReportHandler
from logs.logger import get_logger

logger = get_logger(__name__)

attention_report_bp = Blueprint('attention_report', __name__)

@attention_report_bp.route('/api/reports/attention', methods=['GET', 'OPTIONS'])
def get_attention_report():
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')  # Allow any origin for development
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get query parameters with defaults
        tokenId = request.args.get('tokenId', '')
        name = request.args.get('name', '')
        chain = request.args.get('chain', '')
        currentStatus = request.args.get('currentStatus', '')
        minAttentionCount = request.args.get('minAttentionCount', type=int)
        maxAttentionCount = request.args.get('maxAttentionCount', type=int)
        sortBy = request.args.get('sortBy', 'attentioncount')
        sortOrder = request.args.get('sortOrder', 'desc')

        # Use the handler to get the data
        db = PortfolioDB()
        handler = AttentionReportHandler(db)
            
        # Check if handler is None
        if handler is None:
            logger.error("Handler 'attention_report' not found")
            response = jsonify({
                'error': 'Configuration error',
                'message': "Handler 'attention_report' not found"
            })
            config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return response, 500
                
        attentionData = handler.getAttentionReport(
            tokenId=tokenId,
            name=name,
            chain=chain,
            currentStatus=currentStatus,
            minAttentionCount=minAttentionCount,
            maxAttentionCount=maxAttentionCount,
            sortBy=sortBy,
            sortOrder=sortOrder
        )

        # Create response with proper CORS headers
        response = jsonify(attentionData)
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')  # Allow any origin for development
        return response

    except Exception as e:
        logger.error(f"Error in attention report API: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

@attention_report_bp.route('/api/reports/attention/history/<tokenId>', methods=['GET', 'OPTIONS'])
def get_attention_history(tokenId):
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Use the handler to get the data
        with PortfolioDB() as db:
            handler = AttentionReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'attention_report' not found")
                response = jsonify({
                    'error': 'Configuration error',
                    'message': "Handler 'attention_report' not found"
                })
                config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
                return response, 500
                
            historyData = handler.getAttentionHistoryById(tokenId)

        # Create response with proper CORS headers
        response = jsonify(historyData)
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response

    except Exception as e:
        logger.error(f"Error in attention history API: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

@attention_report_bp.route('/api/reports/attention/filters', methods=['GET', 'OPTIONS'])
def get_attention_filters():
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Use the handler to get the filter options
        with PortfolioDB() as db:
            handler = AttentionReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'attention_report' not found")
                response = jsonify({
                    'error': 'Configuration error',
                    'message': "Handler 'attention_report' not found"
                })
                config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
                return response, 500
                
            statusOptions = handler.getAttentionStatusOptions()
            chainOptions = handler.getChainOptions()
            
            filterOptions = {
                'statusOptions': statusOptions,
                'chainOptions': chainOptions
            }

        # Create response with proper CORS headers
        response = jsonify(filterOptions)
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response

    except Exception as e:
        logger.error(f"Error getting attention filter options: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500 