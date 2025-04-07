from config.Config import get_config
# api/smwalletsbehaviour/SMWalletBehaviourReportAPI.py
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.smwalletsbehaviour.SmartMoneyWalletBehaviourReportHandler import SmartMoneyWalletBehaviourReportHandler
from logs.logger import get_logger
import time

logger = get_logger(__name__)

# Create Blueprint for wallet behaviour reports
smwalletBehaviourReportBp = Blueprint('smwallet_behaviour_report', __name__)

@smwalletBehaviourReportBp.route('/api/smwalletbehaviour/report/<wallet_address>', methods=['GET', 'OPTIONS'])
def getWalletBehaviourReport(wallet_address):
    """API endpoint to retrieve behaviour report for a specific wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    startTime = time.time()
    logger.info(f"Request received for wallet behaviour report: {wallet_address}")
    
    try:
        # Initialize database connection and report handler
        db = PortfolioDB()
        report_handler = SmartMoneyWalletBehaviourReportHandler(db.conn_manager)
        
        # Get wallet behaviour report
        wallet_report = report_handler.getWalletBehaviourReport(wallet_address)
        executionTime = time.time() - startTime
        
        if not wallet_report:
            logger.warning(f"No behaviour report found for wallet: {wallet_address}")
            return jsonify({
                "status": "error",
                "message": f"No behaviour report found for wallet: {wallet_address}",
                "executionTime": f"{executionTime:.2f}s"
            }), 404
        
        # Return successful response with wallet behaviour report
        logger.info(f"Successfully retrieved wallet behaviour report for {wallet_address} in {executionTime:.2f}s")
        return jsonify({
            "status": "success",
            "data": wallet_report,
            "executionTime": f"{executionTime:.2f}s"
        })
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Failed to retrieve wallet behaviour report for {wallet_address}: {str(e)}"
        logger.error(errorMessage, exc_info=True)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500

@smwalletBehaviourReportBp.route('/api/smwalletbehaviour/reports', methods=['GET', 'OPTIONS'])
def getAllWalletsBehaviourSummary():
    """API endpoint to retrieve behaviour summaries for all wallets with pagination"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    startTime = time.time()
    
    # Get pagination parameters from query string
    limit = request.args.get('limit', default=100, type=int)
    offset = request.args.get('offset', default=0, type=int)
    
    logger.info(f"Request received for all wallets behaviour summaries (limit: {limit}, offset: {offset})")
    
    try:
        # Initialize database connection and report handler
        db = PortfolioDB()
        report_handler = SmartMoneyWalletBehaviourReportHandler(db.conn_manager)
        
        # Get wallet behaviour summaries
        wallet_summaries = report_handler.getAllWalletsBehaviourSummary(limit, offset)
        executionTime = time.time() - startTime
        
        # Return successful response with wallet behaviour summaries
        logger.info(f"Successfully retrieved {len(wallet_summaries)} wallet behaviour summaries in {executionTime:.2f}s")
        return jsonify({
            "status": "success",
            "data": {
                "summaries": wallet_summaries,
                "count": len(wallet_summaries),
                "limit": limit,
                "offset": offset
            },
            "executionTime": f"{executionTime:.2f}s"
        })
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Failed to retrieve wallet behaviour summaries: {str(e)}"
        logger.error(errorMessage, exc_info=True)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500

@smwalletBehaviourReportBp.route('/api/smwalletbehaviour/history/<wallet_address>', methods=['GET', 'OPTIONS'])
def getWalletBehaviourHistory(wallet_address):
    """API endpoint to retrieve historical behaviour reports for a specific wallet"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    startTime = time.time()
    
    # Get limit parameter from query string
    limit = request.args.get('limit', default=10, type=int)
    
    logger.info(f"Request received for wallet behaviour history: {wallet_address} (limit: {limit})")
    
    try:
        # Initialize database connection and report handler
        db = PortfolioDB()
        report_handler = SmartMoneyWalletBehaviourReportHandler(db.conn_manager)
        
        # Get wallet behaviour history
        wallet_history = report_handler.getWalletBehaviourHistory(wallet_address, limit)
        executionTime = time.time() - startTime
        
        # Return successful response with wallet behaviour history
        logger.info(f"Successfully retrieved {len(wallet_history)} historical records for wallet {wallet_address} in {executionTime:.2f}s")
        return jsonify({
            "status": "success",
            "data": {
                "walletAddress": wallet_address,
                "history": wallet_history,
                "count": len(wallet_history),
                "limit": limit
            },
            "executionTime": f"{executionTime:.2f}s"
        })
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Failed to retrieve wallet behaviour history for {wallet_address}: {str(e)}"
        logger.error(errorMessage, exc_info=True)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500 