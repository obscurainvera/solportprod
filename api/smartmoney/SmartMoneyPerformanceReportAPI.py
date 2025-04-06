from config.Config import get_config
from flask import Blueprint, request, jsonify
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger
from api.utils.cors import add_cors_headers

logger = get_logger(__name__)

# Create Blueprint
smartMoneyPerformanceReportBp = Blueprint('smartMoneyPerformanceReport', __name__)

@smartMoneyPerformanceReportBp.route('/api/reports/smartmoneyperformance', methods=['GET', 'OPTIONS'])
def get_smart_money_performance():
    """
    Get Smart Money Performance Report with optional filters
    
    Query Parameters:
        wallet_address: Filter by wallet address (optional)
        min_profit_and_loss: Minimum profit and loss (optional)
        max_profit_and_loss: Maximum profit and loss (optional)
        min_trade_count: Minimum trade count (optional)
        max_trade_count: Maximum trade count (optional)
        min_invested_amount: Minimum invested amount for win rate calculation (optional)
        sort_by: Field to sort by (default: profitandloss)
        sort_order: Sort order (asc or desc, default: desc)
        
    Returns:
        JSON response with report data
    """
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))
    
    try:
        # Get query parameters
        wallet_address = request.args.get('wallet_address')
        min_profit_and_loss = request.args.get('min_profit_and_loss')
        max_profit_and_loss = request.args.get('max_profit_and_loss')
        min_trade_count = request.args.get('min_trade_count')
        max_trade_count = request.args.get('max_trade_count')
        min_invested_amount = request.args.get('min_invested_amount')
        sort_by = request.args.get('sort_by', 'profitandloss')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Convert numeric parameters
        try:
            if min_profit_and_loss is not None:
                min_profit_and_loss = float(min_profit_and_loss)
            if max_profit_and_loss is not None:
                max_profit_and_loss = float(max_profit_and_loss)
            if min_trade_count is not None:
                min_trade_count = int(min_trade_count)
            if max_trade_count is not None:
                max_trade_count = int(max_trade_count)
            if min_invested_amount is not None:
                min_invested_amount = float(min_invested_amount)
        except (ValueError, TypeError) as e:
            logger.error(f"Parameter conversion error: {str(e)}")
            return add_cors_headers(jsonify({
                'error': 'Invalid parameter value',
                'message': str(e)
            }), 400)
        
        # Get database connection
        db = PortfolioDB()
        
        # Get report data
        report_data = db.smartMoneyPerformanceReport.getSmartMoneyPerformanceReport(
            walletAddress=wallet_address,
            minProfitAndLoss=min_profit_and_loss,
            maxProfitAndLoss=max_profit_and_loss,
            minTradeCount=min_trade_count,
            maxTradeCount=max_trade_count,
            minInvestedAmount=min_invested_amount,
            sortBy=sort_by,
            sortOrder=sort_order
        )
        
        # Return response
        return add_cors_headers(jsonify(report_data))
        
    except Exception as e:
        logger.error(f"Failed to get Smart Money Performance Report: {str(e)}")
        return add_cors_headers(jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500)

@smartMoneyPerformanceReportBp.route('/api/reports/smartmoneyperformance/top', methods=['GET', 'OPTIONS'])
def get_top_performers():
    """
    Get top performing wallets
    
    Query Parameters:
        limit: Number of wallets to return (default: 10)
        
    Returns:
        JSON response with top performers data
    """
    if request.method == 'OPTIONS':
        return add_cors_headers(jsonify({}))
    
    try:
        # Get query parameters
        limit = request.args.get('limit', 10)
        
        # Convert limit to integer
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 10
        
        # Get database connection
        db = PortfolioDB()
        
        # Get top performers
        top_performers = db.smartMoneyPerformanceReport.getTopPerformers(limit=limit)
        
        # Return response
        return add_cors_headers(jsonify(top_performers))
        
    except Exception as e:
        logger.error(f"Failed to get top performers: {str(e)}")
        return add_cors_headers(jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500) 