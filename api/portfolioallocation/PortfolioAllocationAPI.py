from config.Config import get_config
from flask import Blueprint, jsonify, request
from api.portfolioallocation.PortfolioAllocationModule import portfolioAllocation
from logs.logger import get_logger

logger = get_logger(__name__)

# Create a Blueprint for portfolio allocation endpoints
portfolio_allocation_bp = Blueprint('portfolioAllocation', __name__)

@portfolio_allocation_bp.route('/api/portfolioAllocation/suggestions', methods=['POST', 'OPTIONS'])
def handlePortfolioAllocationSuggestions():
    """API endpoint to get portfolio allocation suggestions"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get input data from request
        inputData = request.json
        
        if not inputData:
            return jsonify({
                'status': 'error',
                'message': 'No input data provided'
            }), 400
        
        # Validate required fields
        requiredFields = ['currentPortfolio', 'targetPortfolio', 'timeHorizon', 'maxLoss', 'tokens']
        missingFields = [field for field in requiredFields if field not in inputData]
        
        if missingFields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missingFields)}'
            }), 400
        
        # Validate numeric values are positive
        if not isinstance(inputData['currentPortfolio'], (int, float)) or inputData['currentPortfolio'] <= 0:
            raise ValueError("Current portfolio value must be positive")
            
        if not isinstance(inputData['targetPortfolio'], (int, float)) or inputData['targetPortfolio'] <= 0:
            raise ValueError("Target portfolio value must be positive")
            
        if not isinstance(inputData['timeHorizon'], (int, float)) or inputData['timeHorizon'] <= 0:
            raise ValueError("Time horizon must be positive")
            
        if not isinstance(inputData['maxLoss'], (int, float)) or inputData['maxLoss'] <= 0:
            raise ValueError("Maximum loss must be positive")
            
        # Validate tokens array
        if not isinstance(inputData['tokens'], list) or len(inputData['tokens']) == 0:
            raise ValueError("Tokens must be a non-empty array")
            
        # Validate stage information if present
        if 'stage' in inputData:
            if not isinstance(inputData['stage'], int) or inputData['stage'] <= 0:
                raise ValueError("Stage must be a positive integer")
                
            # For stage > 1, remainingAmount is required and must be positive
            if inputData['stage'] > 1:
                if 'remainingAmount' not in inputData or not isinstance(inputData['remainingAmount'], (int, float)) or inputData['remainingAmount'] <= 0:
                    raise ValueError("For stage > 1, remainingAmount must be provided and positive")
        
        # Process portfolio allocation
        logger.info("Processing portfolio allocation request")
        result = portfolioAllocation(inputData)
        
        # Return result
        return jsonify({
            'status': 'success',
            'data': result
        })

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Portfolio allocation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500 