from config.Config import get_config
from flask import Blueprint, jsonify, request
from database.operations.PortfolioDB import PortfolioDB
from database.portsummary.PortSummaryReportHandler import PortSummaryReportHandler
from logs.logger import get_logger
from datetime import datetime
from actions.DexscrennerAction import DexScreenerAction
import time

logger = get_logger(__name__)

port_summary_report_bp = Blueprint('port_summary_report', __name__)

@port_summary_report_bp.route('/api/reports/portsummary', methods=['GET', 'OPTIONS'])
def get_port_summary():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        # Get query parameters with defaults
        tokenId = request.args.get('token_id', '')
        name = request.args.get('name', '')
        chainName = request.args.get('chain_name', '')
        minMarketCap = request.args.get('min_market_cap', type=float)
        maxMarketCap = request.args.get('max_market_cap', type=float)
        minTokenAge = request.args.get('min_token_age', type=float)
        maxTokenAge = request.args.get('max_token_age', type=float)
        sortBy = request.args.get('sort_by', 'smartbalance')
        sortOrder = request.args.get('sort_order', 'desc')
        selectedTags = request.args.getlist('selected_tags')  # Get list of selected tags
        
        # Log selected tags to help debugging
        if selectedTags:
            logger.info(f"Filtering by tags: {selectedTags}")
        
        # Use the handler to get the data
        with PortfolioDB() as db:
            handler = PortSummaryReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'port_summary_report' not found")
                return jsonify({
                    'status': 'error',
                    'message': "Handler 'port_summary_report' not found"
                }), 500
                
            portSummaryData = handler.getPortSummaryReport(
                tokenId=tokenId,
                name=name,
                chainName=chainName,
                minMarketCap=minMarketCap,
                maxMarketCap=maxMarketCap,
                minTokenAge=minTokenAge,
                maxTokenAge=maxTokenAge,
                sortBy=sortBy,
                sortOrder=sortOrder,
                selectedTags=selectedTags if selectedTags else None  # Pass selected tags to handler
            )
            
            # Initialize DexScreener action to fetch current prices
            dexScreener = DexScreenerAction()
            
            # Extract all token IDs for batch processing
            tokenIds = [record.get('tokenid') for record in portSummaryData if record.get('tokenid')]
            
            try:
                logger.info(f"Starting batch price fetching for {len(tokenIds)} tokens")
                startTime = time.time()
                
                # Fetch current prices for all tokens in batches
                tokenPrices = dexScreener.getBatchTokenPrices(tokenIds)
                
                endTime = time.time()
                logger.info(f"Completed batch price fetching in {endTime - startTime:.2f} seconds")
                
                # Update each record with the price data
                for record in portSummaryData:
                    tokenId = record.get('tokenid')
                    avgPrice = record.get('avgprice')
                    
                    if tokenId and tokenId in tokenPrices and tokenPrices[tokenId]:
                        priceData = tokenPrices[tokenId]
                        
                        # Add current price to the record
                        record['currentprice'] = priceData.price
                        
                        # Calculate percentage change if avg_price exists
                        if avgPrice and avgPrice > 0:
                            pctChange = ((priceData.price - avgPrice) / avgPrice) * 100
                            record['pricechange'] = round(pctChange, 2)
                    else:
                        # Set default values if price data is not available
                        record['currentprice'] = None
                        record['pricechange'] = None
            except Exception as e:
                logger.error(f"Error during batch price fetching: {str(e)}")
                # Set default values for all records if batch fetching fails
                for record in portSummaryData:
                    record['currentprice'] = None
                    record['pricechange'] = None
            
            # Log the first record to debug tags
            if portSummaryData and len(portSummaryData) > 0:
                logger.info(f"First record tags: {portSummaryData[0].get('tags', 'No tags field')}")
                # Log the type of tags for the first few records
                for i, record in enumerate(portSummaryData[:3]):
                    tags = record.get('tags', [])
                    logger.info(f"Record {i+1} tags type: {type(tags)}, value: {tags}")

        # Return data as JSON
        return jsonify({
            "status": "success",
            "data": portSummaryData
        })

    except Exception as e:
        logger.error(f"Error in port summary report API: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@port_summary_report_bp.route('/api/reports/portsummary/history/<token_id>', methods=['GET', 'OPTIONS'])
def get_token_history(token_id):
    """Get historical data for a specific token to display in the overlay chart."""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        logger.info(f"Fetching history data for token ID: {token_id}")
        
        with PortfolioDB() as db:
            handler = PortSummaryReportHandler(db)
            
            if handler is None:
                logger.error("Handler 'port_summary_report' not found")
                return jsonify({
                    'status': 'error',
                    'message': "Handler 'port_summary_report' not found"
                }), 500
                
            # Get historical data for the token
            history_data = handler.getTokenHistory(token_id)
            
            if not history_data:
                logger.warning(f"No history data found for token ID: {token_id}")
                return jsonify({
                    'status': 'success',
                    'data': []
                })
                
            logger.info(f"Retrieved {len(history_data)} history records for token ID: {token_id}")
            
            # Format the data for the chart
            formatted_data = []
            for record in history_data:
                formatted_record = {
                    'date': record.get('updated_at'),
                    'smartbalance': record.get('smartbalance'),
                    'mcap': record.get('mcap'),
                    'price': record.get('price')
                }
                formatted_data.append(formatted_record)
            
            # Log the first few records for debugging
            if formatted_data:
                logger.info(f"First record: {formatted_data[0]}")
                if len(formatted_data) > 1:
                    logger.info(f"Last record: {formatted_data[-1]}")
            
            return jsonify({
                'status': 'success',
                'data': formatted_data
            })
            
    except Exception as e:
        logger.error(f"Error fetching token history: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500