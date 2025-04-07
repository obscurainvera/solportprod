from config.Config import get_config
from flask import Blueprint, request, jsonify
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

# Constants
DEFAULT_SORT_BY = "strategyname"
DEFAULT_SORT_ORDER = "asc"
DEFAULT_EXECUTION_SORT_BY = "createdat"
DEFAULT_EXECUTION_SORT_ORDER = "desc"

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
        return jsonify({}), 200
        
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
            
            # Fix PNL calculations if needed
            strategies = ensure_pnl_calculations(strategies)
            
            # Return response
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"Strategy config report generated in {processing_time:.2f}ms, found {len(strategies)} strategies")
            
            return jsonify({
                "status": "success",
                "data": strategies,
                "count": len(strategies),
                "timing": f"{processing_time:.2f}ms"
            })
            
    except Exception as e:
        logger.error(f"Error generating strategy config report: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@strategyperformance_bp.route('/api/reports/strategyperformance/executions', methods=['GET', 'OPTIONS'])
def strategy_executions():
    """Endpoint to get all strategy executions."""
    if request.method == "OPTIONS":
        return jsonify({}), 200
        
    start_time = time.time()
    
    try:
        # Extract query parameters
        params = extract_query_params()
        
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Use getAllExecutions instead of getStrategyExecutions for all executions with filters
            executions = handler.getAllExecutions(
                strategy_name=params["strategy_name"],
                source=params["source"],
                token_id=params["token_id"],
                token_name=params["token_name"],
                min_realized_pnl=params["min_realized_pnl"],
                min_total_pnl=params["min_total_pnl"],
                sortBy=params["sort_by"] or DEFAULT_EXECUTION_SORT_BY,
                sortOrder=params["sort_order"]
            )
            
            # Fix PNL calculations if needed
            executions = ensure_pnl_calculations(executions)
            
            # Return response
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"Strategy executions report generated in {processing_time:.2f}ms, found {len(executions)} executions")
            
            return jsonify({
                "status": "success",
                "data": executions,
                "count": len(executions),
                "timing": f"{processing_time:.2f}ms"
            })
            
    except Exception as e:
        logger.error(f"Error generating strategy executions report: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@strategyperformance_bp.route('/api/reports/strategyperformance/config/<int:strategy_id>/executions', methods=['GET', 'OPTIONS'])
def strategy_executions_by_id(strategy_id):
    """Endpoint to get executions for a specific strategy by ID."""
    if request.method == "OPTIONS":
        return jsonify({}), 200
        
    start_time = time.time()
    
    try:
        # Extract query parameters
        params = extract_query_params()
        
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Get strategy executions for specific strategy
            executions = handler.getStrategyExecutions(
                strategyId=strategy_id,
                min_realized_pnl=params["min_realized_pnl"],
                min_total_pnl=params["min_total_pnl"]
            )
            
            # Fix PNL calculations if needed
            executions = ensure_pnl_calculations(executions)
            
            # Return response
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"Executions for strategy {strategy_id} generated in {processing_time:.2f}ms, found {len(executions)} executions")
            
            return jsonify({
                "status": "success",
                "data": executions,
                "count": len(executions),
                "strategy_id": strategy_id,
                "timing": f"{processing_time:.2f}ms"
            })
            
    except Exception as e:
        logger.error(f"Error generating executions for strategy {strategy_id}: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@strategyperformance_bp.route('/api/reports/strategyperformance/config/<int:strategy_id>', methods=['GET', 'OPTIONS'])
def strategy_config_by_id(strategy_id):
    """Endpoint to get strategy configuration details by ID."""
    if request.method == "OPTIONS":
        return jsonify({}), 200
        
    start_time = time.time()
    
    try:
        # Connect to database and get handler
        with PortfolioDB() as db:
            handler = StrategyPerformanceHandler(db)
            
            # Get strategy configuration
            strategy = handler.getStrategyConfigById(strategy_id)
            
            if not strategy:
                logger.warning(f"Strategy with ID {strategy_id} not found")
                return jsonify({
                    "status": "error",
                    "message": f"Strategy with ID {strategy_id} not found"
                }), 404
            
            # Fix PNL calculations if needed
            strategy = ensure_pnl_calculations([strategy])[0]
            
            # Return response
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            logger.info(f"Strategy config details for ID {strategy_id} generated in {processing_time:.2f}ms")
            
            return jsonify({
                "status": "success",
                "data": strategy,
                "strategy_id": strategy_id,
                "timing": f"{processing_time:.2f}ms"
            })
            
    except Exception as e:
        logger.error(f"Error retrieving strategy configuration for ID {strategy_id}: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500 