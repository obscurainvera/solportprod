from config.Config import get_config
# api/smwallet_behaviour/smwallet_behaviour_api.py
from flask import Blueprint, jsonify, request
from scheduler.SMWalletBehaviourScheduler import SMWalletBehaviourScheduler
from logs.logger import get_logger
import time

logger = get_logger(__name__)

smartMoneyWalletBehaviourBp = Blueprint('smwallet_behaviour', __name__)

@smartMoneyWalletBehaviourBp.route('/api/smwalletbehaviour/analyze', methods=['POST', 'OPTIONS'])
def analyzeSMWalletBehaviour():
    """Trigger SM wallet behaviour analysis manually, optionally for a specific wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    startTime = time.time()
    data = request.get_json() or {}
    walletAddress = data.get('walletAddress')
    logger.info(f"Manual SM wallet behaviour analysis triggered{' for wallet ' + walletAddress if walletAddress else ''}")
    
    try:
        scheduler = SMWalletBehaviourScheduler()
        result = scheduler.runAnalysis(walletAddress)
        executionTime = time.time() - startTime
        
        if result:
            logger.info(f"SM wallet behaviour analysis completed in {executionTime:.2f} seconds{' for wallet ' + walletAddress if walletAddress else ''}")
            return jsonify({
                "status": "success",
                "message": f"SM wallet behaviour analysis completed successfully{' for wallet ' + walletAddress if walletAddress else ''}",
                "executionTime": f"{executionTime:.2f}s"
            })
        
        logger.error(f"SM wallet behaviour analysis failed - no data processed{' for wallet ' + walletAddress if walletAddress else ''}")
        return jsonify({
            "status": "error",
            "message": f"No SM wallet behaviour data processed{' for wallet ' + walletAddress if walletAddress else ''}",
            "executionTime": f"{executionTime:.2f}s"
        }), 500
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"SM wallet behaviour analysis failed{' for wallet ' + walletAddress if walletAddress else ''}: {str(e)}"
        logger.error(errorMessage, exc_info=True)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500