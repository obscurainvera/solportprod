from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.smwalletsbehaviour.SMWalletInvestmentRangeReportHandler import SMWalletInvestmentRangeReportHandler
from logs.logger import get_logger
import time

logger = get_logger(__name__)

smwallet_investment_range_report_bp = Blueprint('smwallet_investment_range_report', __name__)

@smwallet_investment_range_report_bp.route('/api/smwalletbehaviour/investmentrange/<wallet_address>', methods=['GET', 'OPTIONS'])
def get_wallet_investment_range_report(wallet_address):
    """
    Get investment range report for a specific wallet.
    
    Args:
        wallet_address: Wallet address to analyze
        
    Returns:
        JSON report of investment metrics by investment amount ranges
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        startTime = time.time()
        logger.info(f"Processing investment range report request for wallet: {wallet_address}")
        
        with PortfolioDB() as db:
            # Use the handler to fetch data from the database and delegate processing to the action
            handler = SMWalletInvestmentRangeReportHandler(db)
            report = handler.getInvestmentRangeReport(wallet_address)
            
            # Add execution time information
            executionTime = time.time() - startTime
            logger.info(f"Generated investment range report for {wallet_address} in {executionTime:.2f} seconds")
            
            return jsonify({
                "status": "success",
                "data": report,
                "meta": {
                    "executionTime": round(executionTime, 3)
                }
            })
            
    except Exception as e:
        logger.error(f"Error processing investment range report for {wallet_address}: {str(e)}")
        executionTime = time.time() - startTime
        
        return jsonify({
            "status": "error",
            "message": f"Failed to generate investment range report: {str(e)}",
            "meta": {
                "executionTime": round(executionTime, 3)
            }
        }), 500

@smwallet_investment_range_report_bp.route('/api/smwalletbehaviour/investment-range-reports/top/<int:limit>', methods=['GET', 'OPTIONS'])
def get_top_wallets_investment_range_reports(limit):
    """
    Get investment range reports for top wallets by total PNL.
    
    Args:
        limit: Maximum number of top wallets to include
        
    Returns:
        JSON reports of investment metrics for top wallets
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        start_time = time.time()
        logger.info(f"Processing top wallets investment range reports request with limit: {limit}")
        
        # Validate and cap the limit to prevent overloading
        if limit <= 0:
            limit = 10
        elif limit > 100:
            limit = 100
            
        with PortfolioDB() as db:
            # Use the handler to fetch top wallets and generate reports
            handler = SMWalletInvestmentRangeReportHandler(db)
            reports = handler.getTopWalletsInvestmentRangeReport(limit)
            
            # Add execution time information
            execution_time = time.time() - start_time
            logger.info(f"Generated top {limit} wallets investment range reports in {execution_time:.2f} seconds")
            
            return jsonify({
                "status": "success",
                "data": reports,
                "meta": {
                    "executionTime": round(execution_time, 3),
                    "count": len(reports)
                }
            })
            
    except Exception as e:
        logger.error(f"Error processing top wallets investment range reports: {str(e)}")
        execution_time = time.time() - start_time
        
        return jsonify({
            "status": "error",
            "message": f"Failed to generate top wallets investment range reports: {str(e)}",
            "meta": {
                "executionTime": round(execution_time, 3)
            }
        }), 500

@smwallet_investment_range_report_bp.route('/api/smwalletbehaviour/investment-range-reports/batch', methods=['POST', 'OPTIONS'])
def get_batch_investment_range_reports():
    """
    Get investment range reports for multiple wallets.
    
    Request body:
        {
            "walletAddresses": ["address1", "address2", ...]
        }
        
    Returns:
        JSON reports of investment metrics for specified wallets
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        start_time = time.time()
        
        # Get wallet addresses from request body
        request_data = request.get_json()
        
        if not request_data or 'walletAddresses' not in request_data:
            logger.warning("Missing walletAddresses in batch investment range report request")
            return jsonify({
                "status": "error",
                "message": "Request must include 'walletAddresses' array"
            }), 400
            
        wallet_addresses = request_data['walletAddresses']
        
        if not isinstance(wallet_addresses, list) or len(wallet_addresses) == 0:
            logger.warning("Invalid walletAddresses format in batch investment range report request")
            return jsonify({
                "status": "error",
                "message": "'walletAddresses' must be a non-empty array"
            }), 400
            
        # Limit batch size to prevent overloading
        max_batch_size = 20
        if len(wallet_addresses) > max_batch_size:
            wallet_addresses = wallet_addresses[:max_batch_size]
            logger.warning(f"Batch request truncated to {max_batch_size} wallets")
            
        logger.info(f"Processing batch investment range reports for {len(wallet_addresses)} wallets")
        
        with PortfolioDB() as db:
            # Use the handler to generate batch reports
            handler = SMWalletInvestmentRangeReportHandler(db)
            reports = handler.getInvestmentRangeReportForWallets(wallet_addresses)
            
            # Add execution time information
            execution_time = time.time() - start_time
            logger.info(f"Generated batch investment range reports for {len(wallet_addresses)} wallets in {execution_time:.2f} seconds")
            
            return jsonify({
                "status": "success",
                "data": reports,
                "meta": {
                    "executionTime": round(execution_time, 3),
                    "count": len(reports)
                }
            })
            
    except Exception as e:
        logger.error(f"Error processing batch investment range reports: {str(e)}")
        execution_time = time.time() - start_time
        
        return jsonify({
            "status": "error",
            "message": f"Failed to generate batch investment range reports: {str(e)}",
            "meta": {
                "executionTime": round(execution_time, 3)
            }
        }), 500

@smwallet_investment_range_report_bp.route('/api/smwalletbehaviour/tokens-by-range/<wallet_address>/<range_id>', methods=['GET', 'OPTIONS'])
def get_tokens_by_range(wallet_address, range_id):
    """
    Get tokens for a specific wallet and investment range.
    
    Args:
        wallet_address: Wallet address to analyze
        range_id: ID of the investment range
        
    Returns:
        JSON list of tokens in the specified range
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        start_time = time.time()
        
        # Check if range_id is valid
        if not range_id or range_id == 'undefined':
            logger.warning(f"Invalid range ID: {range_id}")
            execution_time = time.time() - start_time
            
            return jsonify({
                "status": "error",
                "message": f"Invalid range ID: {range_id}",
                "data": [],
                "meta": {
                    "executionTime": round(execution_time, 3),
                    "count": 0
                }
            }), 400
        
        logger.info(f"Processing tokens by range request for wallet: {wallet_address}, range: {range_id}")
        
        with PortfolioDB() as db:
            # Use the handler to fetch tokens for the specified range
            handler = SMWalletInvestmentRangeReportHandler(db)
            tokens = handler.getTokensByRange(wallet_address, range_id)
            
            # Add execution time information
            execution_time = time.time() - start_time
            logger.info(f"Retrieved {len(tokens)} tokens for wallet {wallet_address}, range {range_id} in {execution_time:.2f} seconds")
            
            return jsonify({
                "status": "success",
                "data": tokens,
                "meta": {
                    "executionTime": round(execution_time, 3),
                    "count": len(tokens)
                }
            })
            
    except Exception as e:
        logger.error(f"Error retrieving tokens by range for {wallet_address}, range {range_id}: {str(e)}")
        execution_time = time.time() - start_time
        
        return jsonify({
            "status": "error",
            "message": f"Failed to retrieve tokens by range: {str(e)}",
            "meta": {
                "executionTime": round(execution_time, 3)
            }
        }), 500 