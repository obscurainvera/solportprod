from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.attention.AttentionReportHandler import AttentionReportHandler
from logs.logger import get_logger

logger = get_logger(__name__)

attention_report_bp = Blueprint('attention_report', __name__)

@attention_report_bp.route('/api/reports/attention', methods=['GET', 'OPTIONS'])
def get_attention_report():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
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
            return jsonify({
                'status': 'error',
                'message': "Handler 'attention_report' not found"
            }), 500
                
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

        # Create standardized success response
        return jsonify({
            'status': 'success',
            'data': attentionData,
            'count': len(attentionData) if attentionData else 0,
            'timestamp': db.get_current_timestamp()
        })

    except Exception as e:
        logger.error(f"Error in attention report API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@attention_report_bp.route('/api/reports/attention/history/<tokenId>', methods=['GET', 'OPTIONS'])
def get_attention_history(tokenId):
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Use the handler to get the data
        with PortfolioDB() as db:
            handler = AttentionReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'attention_report' not found")
                return jsonify({
                    'status': 'error',
                    'message': "Handler 'attention_report' not found"
                }), 500
                
            historyData = handler.getAttentionHistoryById(tokenId)

            if not historyData:
                logger.warning(f"No attention history found for token ID: {tokenId}")
                return jsonify({
                    'status': 'success',
                    'data': [],
                    'count': 0,
                    'message': f"No attention history found for token ID: {tokenId}"
                })

            # Create standardized success response
            return jsonify({
                'status': 'success',
                'data': historyData,
                'count': len(historyData),
                'timestamp': db.get_current_timestamp()
            })

    except Exception as e:
        logger.error(f"Error in attention history API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@attention_report_bp.route('/api/reports/attention/filters', methods=['GET', 'OPTIONS'])
def get_attention_filters():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Use the handler to get the filter options
        with PortfolioDB() as db:
            handler = AttentionReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'attention_report' not found")
                return jsonify({
                    'status': 'error',
                    'message': "Handler 'attention_report' not found"
                }), 500
                
            statusOptions = handler.getAttentionStatusOptions()
            chainOptions = handler.getChainOptions()
            
            filterOptions = {
                'statusOptions': statusOptions,
                'chainOptions': chainOptions
            }

            # Create standardized success response
            return jsonify({
                'status': 'success',
                'data': filterOptions,
                'timestamp': db.get_current_timestamp()
            })

    except Exception as e:
        logger.error(f"Error getting attention filter options: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 