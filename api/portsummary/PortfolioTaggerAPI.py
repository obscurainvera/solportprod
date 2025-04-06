from config.Config import get_config
from flask import jsonify, Blueprint, request
from database.operations.PortfolioDB import PortfolioDB
from actions.portfolio.PortfolioTaggerAction import PortfolioTaggerAction
from logs.logger import get_logger
import time

logger = get_logger(__name__)

portfolio_tagger_bp = Blueprint('portfolio_tagger', __name__)

@portfolio_tagger_bp.route('/api/portfoliotagger/persist', methods=['POST', 'OPTIONS'])
def tagPortfolioTokens():
    """API endpoint to initiate portfolio token tagging process"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = PortfolioDB()
        tagger = PortfolioTaggerAction(db)
        
        success = tagger.addTagsToActivePortSummaryTokens()
        
        if success:
            response = jsonify({
                'success': True,
                'message': 'Successfully tagged portfolio tokens'
            })
            config = get_config()
            response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return response
            
        response = jsonify({'error': 'Failed to tag portfolio tokens'})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

    except Exception as e:
        logger.error(f"API Error in portfolio tagging: {str(e)}")
        response = jsonify({'error': str(e)})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response, 500

@portfolio_tagger_bp.route('/api/portfoliotagger/getalltags', methods=['GET', 'OPTIONS'])
def getAvailableTags():
    """API endpoint to get list of all available portfolio tags"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        from actions.portfolio.PortfolioTagEnum import PortfolioTokenTag
        
        tags = PortfolioTokenTag.getAllTags()
        response = jsonify({
            'success': True,
            'tags': tags
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response

    except Exception as e:
        logger.error(f"API Error getting portfolio tags: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500

@portfolio_tagger_bp.route('/api/portfoliotagger/token/persist', methods=['POST', 'OPTIONS'])
def evaluateTokenTags():
    """API endpoint to evaluate and update tags for a specific token"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get token ID from request body
        requestData = request.get_json()
        if not requestData or 'token_id' not in requestData:
            response = jsonify({'error': 'token_id is required'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            return response, 400
            
        tokenId = requestData['token_id']
        
        # Initialize database and tagger
        db = PortfolioDB()
        tagger = PortfolioTaggerAction(db)
        
        # Get token data - wrap token_id in a list since getTokenData expects List[str]
        tokens = db.portfolio.getTokenData([tokenId])
        if not tokens:
            response = jsonify({'error': f'Token {tokenId} not found'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            return response, 404
            
        # Use first token since we only expect one
        token = tokens[0]
        
        # Evaluate and update tags
        result = tagger.evaluateAndUpdateTokenTags(token)
        
        response = jsonify({
            'success': True,
            'data': result
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response

    except Exception as e:
        logger.error(f"API Error in token tag evaluation: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500

@portfolio_tagger_bp.route('/api/portfoliotagger/dynamictags', methods=['GET', 'OPTIONS'])
def getDynamicTags():
    """API endpoint to get all dynamic tags currently in use"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = PortfolioDB()
        
        # Query to get all unique tags
        with db.conn_manager.transaction() as cursor:
            cursor.execute("SELECT tags FROM portfoliosummary WHERE tags IS NOT NULL AND tags != ''")
            allTagsRows = cursor.fetchall()
        
        # Extract and flatten all tags
        allTags = set()
        for row in allTagsRows:
            if row['tags']:
                tags = row['tags'].split(',')
                allTags.update(tags)
        
        # Filter for dynamic tags (starting with [ and containing :)
        dynamicTags = [tag for tag in allTags if tag.startswith('[') and ':' in tag]
        
        # Group by PNL range
        groupedTags = {}
        for tag in dynamicTags:
            if '[PNL :' in tag:
                # Extract PNL range
                pnlRange = tag.split('[PNL :')[1].split(']')[0].strip()
                if pnlRange not in groupedTags:
                    groupedTags[pnlRange] = []
                groupedTags[pnlRange].append(tag)
        
        response = jsonify({
            'success': True,
            'dynamicTags': dynamicTags,
            'groupedByPnl': groupedTags
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response

    except Exception as e:
        logger.error(f"API Error getting dynamic tags: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500 