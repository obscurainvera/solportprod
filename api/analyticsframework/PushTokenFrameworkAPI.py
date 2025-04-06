from config.Config import get_config        
from flask import Blueprint, jsonify, request
from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticsframework.enums.PushSourceEnum import PushSource
from framework.analyticsframework.models.BaseModels import BaseTokenData
from framework.analyticsframework.models.SourceModels import (
    PortSummaryTokenData, AttentionTokenData, SmartMoneyTokenData,
    VolumeTokenData, PumpFunTokenData
)
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.portsummary.PortfolioHandler import PortfolioHandler
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from framework.analyticsframework.models.StrategyModels import StrategyConfig

logger = get_logger(__name__)

# Create Blueprint for token analysis endpoints
push_token_bp = Blueprint('push_token', __name__)

@push_token_bp.route('/api/analyticsframework/pushtoken', methods=['POST'])
def pushToken():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Validate required fields
        tokenId = data.get('token_id')
        sourceType = data.get('source_type')
        
        if not tokenId or not sourceType:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: token_id and source_type'
            }), 400

        if not SourceType.isValidSource(sourceType):
            return jsonify({
                'status': 'error',
                'message': f'Invalid source type: {sourceType}'
            }), 400

        # Get token data from source
        pushTokenApiInstance = PushTokenAPI()
        tokenData = PushTokenAPI.getSourceTokenDataHandler(sourceType, tokenId)
        if not tokenData:
            return jsonify({
                'status': 'error',
                'message': f'Token {tokenId} not found in {sourceType} source'
            }), 404

        # Get optional description
        description = data.get('description')

        # Analyze token with source type, setting push source as API
        success = pushTokenApiInstance.pushToken(tokenData, sourceType, PushSource.API, description)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Token pushed to framework successfully',
                'data': {
                    'token_id': tokenId, 
                    'source': sourceType,
                    'description': description
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to push token to framework'
            }), 500

    except Exception as e:
        logger.error(f"Token analysis API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@push_token_bp.route('/api/analyticsframework/pushallsourcetokens', methods=['POST'])
def pushAllSourceTokens():
    """
    API endpoint to push all tokens from a specific source type to the analytics framework
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Validate required field
        sourceType = data.get('source_type')
        
        if not sourceType:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: source_type'
            }), 400

        if not SourceType.isValidSource(sourceType):
            return jsonify({
                'status': 'error',
                'message': f'Invalid source type: {sourceType}'
            }), 400
            
        # Initialize database and analytics handler
        pushTokenApiInstance = PushTokenAPI()
        
        # Push all tokens for the specified source
        success, stats = pushTokenApiInstance.pushAllTokens(sourceType)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Successfully pushed tokens from {sourceType} source to analytics framework',
                'data': stats
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to push tokens from {sourceType} source',
                'data': stats
            }), 500

    except Exception as e:
        logger.error(f"Push all tokens API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@push_token_bp.route('/api/analyticsframework/pushtokenstrategy', methods=['POST'])
def pushTokenToStrategy():
    """
    API endpoint to push a token to a specific strategy
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Validate required fields
        tokenId = data.get('token_id')
        sourceType = data.get('source_type')
        strategyId = data.get('strategy_id')
        description = data.get('description')
        
        if not all([tokenId, sourceType, strategyId]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: token_id, source_type, and strategy_id'
            }), 400

        if not SourceType.isValidSource(sourceType):
            return jsonify({
                'status': 'error',
                'message': f'Invalid source type: {sourceType}'
            }), 400

        # Initialize PushTokenAPI and push token to strategy
        pushTokenApiInstance = PushTokenAPI()
        executionId = pushTokenApiInstance.pushTokenToStrategy(
            tokenId=tokenId,
            sourceType=sourceType,
            strategyId=strategyId,
            description=description
        )

        if executionId:
            return jsonify({
                'status': 'success',
                'message': 'Token pushed to strategy successfully',
                'data': {
                    'token_id': tokenId,
                    'source': sourceType,
                    'strategy_id': strategyId,
                    'execution_id': executionId,
                    'description': description
                }
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to push token to strategy'
            }), 500

    except Exception as e:
        logger.error(f"Push token to strategy API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@push_token_bp.route('/api/analyticsframework/strategies', methods=['GET'])
def getStrategies():
    """
    API endpoint to get available strategies for a source type
    """
    try:
        source_type = request.args.get('source_type')
        
        if not source_type:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: source_type'
            }), 400

        if not SourceType.isValidSource(source_type):
            return jsonify({
                'status': 'error',
                'message': f'Invalid source type: {source_type}'
            }), 400

        # Get active strategies for the source type using AnalyticsHandler
        db = PortfolioDB()
        strategies = db.analytics.getActiveStrategiesForSource(source_type)
        
        return jsonify({
            'status': 'success',
            'data': strategies
        }), 200

    except Exception as e:
        logger.error(f"Get strategies API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500 