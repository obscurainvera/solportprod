from config.Config import get_config
from flask import Blueprint, jsonify, request
from actions.DexscrennerAction import DexScreenerAction
from logs.logger import get_logger
import time

logger = get_logger(__name__)

dexscrenner_bp = Blueprint('dexscrenner', __name__)

class DexScrennerAPI:
    def __init__(self):
        self.dexScreener = DexScreenerAction()

@dexscrenner_bp.route('/api/price/tokens', methods=['POST', 'OPTIONS'])
def getTokenPrices():
    """
    Get price information for a list of tokens
    Expected request body:
    {
        "tokenAddresses": ["address1", "address2", ...],
        "chainId": "solana"  # optional, defaults to "solana"
    }
    Returns:
        JSON response with price information for each token
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    startTime = time.time()
    logger.info("Token price request received")

    try:
        data = request.get_json()
        if not data or 'tokenAddresses' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing tokenAddresses in request body"
            }), 400

        tokenAddresses = data.get('tokenAddresses', [])
        chainId = data.get('chainId', 'solana')

        if not isinstance(tokenAddresses, list):
            return jsonify({
                "status": "error",
                "message": "tokenAddresses must be a list"
            }), 400

        if not tokenAddresses:
            return jsonify({
                "status": "error",
                "message": "tokenAddresses list cannot be empty"
            }), 400

        # Initialize API and get prices
        priceApi = DexScrennerAPI()
        result = priceApi.dexScreener.getBatchTokenPrices(tokenAddresses, chainId)

        executionTime = time.time() - startTime

        # Format response
        formattedResult = {}
        for address, priceData in result.items():
            if priceData:
                formattedResult[address] = {
                    "price": priceData.price,
                    "fdv": priceData.fdv,
                    "marketCap": priceData.marketCap,
                    "name": priceData.name,
                    "symbol": priceData.symbol
                }
            else:
                formattedResult[address] = None

        return jsonify({
            "status": "success",
            "data": formattedResult,
            "executionTime": f"{executionTime:.2f}s"
        })

    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Failed to get token prices: {str(e)}"
        logger.error(errorMessage)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500

@dexscrenner_bp.route('/api/price/token/<tokenAddress>', methods=['GET', 'OPTIONS'])
def getSingleTokenPrice(tokenAddress):
    """
    Get price information for a single token
    Args:
        tokenAddress: The address of the token to query
    Returns:
        JSON response with price information for the token
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    startTime = time.time()
    logger.info(f"Single token price request received for {tokenAddress}")

    try:
        # Initialize API and get price
        priceApi = DexScrennerAPI()
        result = priceApi.dexScreener.getTokenPrice(tokenAddress)

        executionTime = time.time() - startTime

        if result:
            return jsonify({
                "status": "success",
                "data": {
                    "price": result.price,
                    "fdv": result.fdv,
                    "marketCap": result.marketCap,
                    "name": result.name,
                    "symbol": result.symbol
                },
                "executionTime": f"{executionTime:.2f}s"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No price data found for token",
                "executionTime": f"{executionTime:.2f}s"
            }), 404

    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Failed to get token price: {str(e)}"
        logger.error(errorMessage)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500 