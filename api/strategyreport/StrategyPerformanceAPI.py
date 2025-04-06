from config.Config import get_config
from flask import Blueprint, request, jsonify
from flask_cors import CORS
from database.strategyreport.StrategyPerformanceHandler import StrategyPerformanceHandler
from database.operations.PortfolioDB import PortfolioDB
from logs.logger import get_logger
import time
from decimal import Decimal
from typing import Dict, Any, Tuple, Optional, List, Callable

# Set up logging
logger = get_logger(__name__)

# Create blueprint
strategyperformance_bp = Blueprint('strategyperformance', __name__)
CORS(strategyperformance_bp)

# Constants
DEFAULT_SORT_BY = "strategyname"
DEFAULT_SORT_ORDER = "asc"
DEFAULT_EXECUTION_SORT_BY = "createdat"
DEFAULT_EXECUTION_SORT_ORDER = "desc"

# Utility functions for API responses
def generate_cors_preflight_response():
    """Generate a CORS preflight response."""
    response = jsonify({})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def generate_success_response(data: Any, timing: float) -> Dict[str, Any]:
    """
    Generate a standardized success response.
    
    Args:
        data: The data to return in the response
        timing: Response time in milliseconds
        
    Returns:
        Dict containing response data and metadata
    """
    return {
        "success": True,
        "data": data,
        "timing": timing
    }

def generate_error_response(message: str, error: Exception = None) -> Dict[str, Any]:
    """
    Generate a standardized error response.
    
    Args:
        message: Error message
        error: Optional exception object
        
    Returns:
        Dict containing error information
    """
    response = {
        "success": False,
        "error": message
    }
    
    if error:
        logger.error(f"{message}: {str(error)}")
    else:
        logger.error(message)
        
    return response

# Parameter parsing utilities
def parse_numeric_param(param_value: Optional[str], default: Optional[float] = None) -> Optional[float]:
    """
    Parse a numeric parameter from string.
    
    Args:
        param_value: The string value to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed float or default value
    """
    if param_value is None:
        return default
        
    try:
        return float(param_value)
    except (ValueError, TypeError):
        return default

def validate_sort_order(sort_order: Optional[str], default: str = "asc") -> str:
    """
    Validate sort order parameter.
    
    Args:
        sort_order: Sort order string to validate
        default: Default value if invalid
        
    Returns:
        Validated sort order ("asc" or "desc")
    """
    if sort_order and sort_order.lower() in ["asc", "desc"]:
        return sort_order.lower()
    return default

def extract_query_params() -> Dict[str, Any]:
    """
    Extract and validate query parameters from the request.
    
    Returns:
        Dict of parsed query parameters
    """
    params = {}
    
    # String parameters
    params["strategy_name"] = request.args.get("strategy_name")
    params["source"] = request.args.get("source")
    params["token_id"] = request.args.get("token_id")
    params["token_name"] = request.args.get("token_name")
    params["status"] = request.args.get("status")
    
    # Sort parameters - handle both camelCase (from API docs) and snake_case (from frontend)
    params["sort_by"] = request.args.get("sortBy") or request.args.get("sort_by")
    params["sort_order"] = validate_sort_order(
        request.args.get("sortOrder") or request.args.get("sort_order"), 
        default=DEFAULT_SORT_ORDER
    )
    
    # Numeric parameters - handle both camelCase and snake_case
    params["min_realized_pnl"] = parse_numeric_param(
        request.args.get("minRealizedPnl") or request.args.get("min_realized_pnl")
    )
    params["min_total_pnl"] = parse_numeric_param(
        request.args.get("minTotalPnl") or request.args.get("min_total_pnl")
    )
    
    return params

def ensure_pnl_calculations(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure PNL calculations are correctly applied before returning the response.
    This fixes any discrepancies in PNL calculations returned from the database.
    
    Args:
        data: List of strategy or execution records
        
    Returns:
        List of records with corrected PNL calculations
    """
    for item in data:
        # For strategy config records
        if 'amountInvested' in item and 'amountTakenOut' in item:
            amount_invested = float(item.get('amountInvested', 0) or 0)
            amount_taken_out = float(item.get('amountTakenOut', 0) or 0)
            remaining_value = float(item.get('remainingCoinsValue', 0) or 0)
            
            # Recalculate realized PNL
            item['realizedPnl'] = amount_taken_out - amount_invested
            
            # Recalculate total PNL
            item['pnl'] = item['realizedPnl'] + remaining_value
        
        # For execution records
        elif 'investedamount' in item and 'amounttakenout' in item:
            amount_invested = float(item.get('investedamount', 0) or 0)
            amount_taken_out = float(item.get('amounttakenout', 0) or 0)
            remaining_value = float(item.get('remainingValue', 0) or 0)
            
            # Recalculate realized PNL
            item['realizedPnl'] = amount_taken_out - amount_invested
            
            # Recalculate total PNL
            item['pnl'] = item['realizedPnl'] + remaining_value
            
    return data

# Route handlers
@strategyperformance_bp.route('/api/reports/strategyperformance/config', methods=['GET', 'OPTIONS'])
def strategy_config_report():
    """Endpoint to get strategy configuration report with performance metrics."""
    if request.method == "OPTIONS":
        return generate_cors_preflight_response()
        
    start_time = time.time()
    
    try:
        # Extract query parameters
        params = extract_query_params()
        
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Get strategy configurations
            strategies = handler.getStrategyConfigReport(
                strategy_name=params["strategy_name"],
                source=params["source"],
                min_realized_pnl=params["min_realized_pnl"],
                min_total_pnl=params["min_total_pnl"],
                sortBy=params["sort_by"] or DEFAULT_SORT_BY,
                sortOrder=params["sort_order"]
            )
            
            # Update with current token prices
            if strategies:
                strategies = handler.updateStrategyTokenPrices(strategies)
                
                # Apply consistent PNL calculations
                strategies = ensure_pnl_calculations(strategies)
        
        # Generate response
        timing = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Strategy config report generated in {timing}ms with {len(strategies)} results.")
        
        return jsonify(generate_success_response(strategies, timing))
        
    except Exception as e:
        return jsonify(generate_error_response("Failed to generate strategy config report", e))

@strategyperformance_bp.route('/api/reports/strategyperformance/executions', methods=['GET', 'OPTIONS'])
def strategy_executions():
    """Endpoint to get all strategy executions with optional filters."""
    if request.method == "OPTIONS":
        return generate_cors_preflight_response()
        
    start_time = time.time()
    
    try:
        # Extract query parameters
        params = extract_query_params()
        
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Get executions
            executions = handler.getAllExecutions(
                strategy_name=params["strategy_name"],
                source=params["source"],
                token_id=params["token_id"],
                token_name=params["token_name"],
                min_realized_pnl=params["min_realized_pnl"],
                min_total_pnl=params["min_total_pnl"],
                sortBy=params["sort_by"] or DEFAULT_EXECUTION_SORT_BY,
                sortOrder=params["sort_order"] or DEFAULT_EXECUTION_SORT_ORDER
            )
            
            # Update with current token prices
            if executions:
                executions = handler.updateExecutionPrices(executions)
                
                # Apply consistent PNL calculations
                executions = ensure_pnl_calculations(executions)
        
        # Generate response
        timing = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Strategy executions report generated in {timing}ms with {len(executions)} results.")
        
        return jsonify(generate_success_response(executions, timing))
        
    except Exception as e:
        return jsonify(generate_error_response("Failed to generate strategy executions report", e))

@strategyperformance_bp.route('/api/reports/strategyperformance/config/<int:strategy_id>/executions', methods=['GET', 'OPTIONS'])
def strategy_executions_by_id(strategy_id):
    """Endpoint to get executions for a specific strategy."""
    if request.method == "OPTIONS":
        return generate_cors_preflight_response()
        
    start_time = time.time()
    
    try:
        # Extract query parameters
        min_realized_pnl = parse_numeric_param(request.args.get("minRealizedPnl"))
        min_total_pnl = parse_numeric_param(request.args.get("minTotalPnl"))
        
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Get executions for the strategy
            executions = handler.getStrategyExecutions(
                strategyId=strategy_id,
                min_realized_pnl=min_realized_pnl,
                min_total_pnl=min_total_pnl
            )
            
            # Update with current token prices
            if executions:
                executions = handler.updateExecutionPrices(executions)
                
                # Apply consistent PNL calculations
                executions = ensure_pnl_calculations(executions)
        
        # Generate response
        timing = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Strategy executions for ID {strategy_id} generated in {timing}ms with {len(executions)} results.")
        
        return jsonify(generate_success_response(executions, timing))
        
    except Exception as e:
        return jsonify(generate_error_response(f"Failed to generate executions for strategy ID {strategy_id}", e))

@strategyperformance_bp.route('/api/reports/strategyperformance/config/<int:strategy_id>', methods=['GET', 'OPTIONS'])
def strategy_config_by_id(strategy_id):
    """Endpoint to get detailed configuration for a specific strategy."""
    if request.method == "OPTIONS":
        return generate_cors_preflight_response()
        
    start_time = time.time()
    
    try:
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Get strategy configuration
            strategy = handler.getStrategyConfigById(strategy_id)
            
            if not strategy:
                return jsonify(generate_error_response(f"Strategy with ID {strategy_id} not found"))
                
        # Generate response
        timing = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Strategy config for ID {strategy_id} retrieved in {timing}ms")
        
        return jsonify(generate_success_response(strategy, timing))
        
    except Exception as e:
        return jsonify(generate_error_response(f"Failed to retrieve strategy configuration for ID {strategy_id}", e)) 