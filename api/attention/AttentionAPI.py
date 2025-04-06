from config.Config import get_config
from flask import Blueprint, jsonify, request
from scheduler.AttentionScheduler import AttentionScheduler
from logs.logger import get_logger
from database.operations.PortfolioDB import PortfolioDB
import time
import requests

logger = get_logger(__name__)

attention_bp = Blueprint('attention', __name__)

class AttentionAPI:
    def __init__(self, db_path=None):
        self.db = PortfolioDB()

@attention_bp.route('/api/attention/analyze', methods=['POST', 'OPTIONS'])
def analyzeAttention():
    """
    Trigger attention analysis manually
    Returns:
        JSON response with execution status and statistics
    """
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    startTime = time.time()
    logger.info("Manual attention analysis triggered")
    
    try:
        # Initialize scheduler and execute
        scheduler = AttentionScheduler()
        result = scheduler.handleAttentionData()
        
        executionTime = time.time() - startTime
        
        if result:
            logger.info(f"Attention analysis completed in {executionTime:.2f} seconds")
            response = jsonify({
                "status": "success",
                "message": "Attention analysis completed successfully",
                "execution_time": f"{executionTime:.2f}s"
            })
            config = get_config()
            response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return response
        
        logger.error("Attention analysis failed - no data processed")
        response = jsonify({
            "status": "error",
            "message": "No attention data processed",
            "execution_time": f"{executionTime:.2f}s"
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Attention analysis failed: {str(e)}"
        logger.error(errorMessage)
        response = jsonify({
            "status": "error",
            "message": errorMessage,
            "execution_time": f"{executionTime:.2f}s"
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

@attention_bp.route('/api/attention/solana/analyze', methods=['POST', 'OPTIONS'])
def analyzeSolanaAttention():
    """
    Trigger Solana-specific attention analysis manually
    Returns:
        JSON response with execution status and statistics
    """
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    startTime = time.time()
    logger.info("Manual Solana attention analysis triggered")
    
    try:
        # Initialize scheduler and execute
        scheduler = AttentionScheduler()
        result = scheduler.persistAttentionDataForSolFromAPI()
        
        executionTime = time.time() - startTime
        
        if result:
            logger.info(f"Solana attention analysis completed in {executionTime:.2f} seconds")
            response = jsonify({
                "status": "success",
                "message": "Solana attention analysis completed successfully",
                "execution_time": f"{executionTime:.2f}s",
                "tokens_processed": result
            })
            config = get_config()
            response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return response
        
        logger.error("Solana attention analysis failed - no data processed")
        response = jsonify({
            "status": "error",
            "message": "No Solana attention data processed",
            "execution_time": f"{executionTime:.2f}s"
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Solana attention analysis failed: {str(e)}"
        logger.error(errorMessage)
        response = jsonify({
            "status": "error",
            "message": errorMessage,
            "execution_time": f"{executionTime:.2f}s"
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500
