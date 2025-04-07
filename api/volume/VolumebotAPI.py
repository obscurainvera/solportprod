from config.Config import get_config
from flask import jsonify, Blueprint, request
from scheduler.VolumebotScheduler import VolumeBotScheduler
from actions.VolumebotAction import VolumebotAction
from database.operations.PortfolioDB import PortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

volumebot_bp = Blueprint('volumebot', __name__)

@volumebot_bp.route('/api/volumebot/fetch-tokens-scheduled', methods=['POST', 'OPTIONS'])
def scheduleVolumeTokensFetch():
    """Execute the scheduler's execute_actions function for volume tokens"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        logger.info("Starting scheduled volume tokens fetch")
        scheduler = VolumeBotScheduler()
        scheduler.handleVolumeAnalysisFromAPI()
        
        logger.info("Successfully triggered scheduled volume tokens fetch")
        return jsonify({
            'status': 'success',
            'message': 'Successfully triggered scheduled volume tokens fetch'
        })

    except Exception as e:
        logger.error(f"API Error in scheduleVolumeTokensFetch: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

# Add a new endpoint that matches the one used in the frontend
@volumebot_bp.route('/api/volumebot/fetch', methods=['POST', 'OPTIONS'])
def fetchVolumeTokens():
    """Alias for scheduleVolumeTokensFetch to match frontend endpoint"""
    return scheduleVolumeTokensFetch()

