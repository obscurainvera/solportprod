from config.Config import get_config
from flask import Blueprint, jsonify
from logs.logger import get_logger
import time

logger = get_logger(__name__)

health_bp = Blueprint('health', __name__)

# Store required instances
_job_runner = None
_is_shutting_down = None

def init_health_api(job_runner, is_shutting_down):
    """Initialize health API with required instances"""
    global _job_runner, _is_shutting_down
    _job_runner = job_runner
    _is_shutting_down = is_shutting_down

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Check system health and component status"""
    if _is_shutting_down.is_set():
        return jsonify({
            "status": "shutting_down",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }), 503
        
    return jsonify({
        "status": "healthy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "components": {
            "database": "operational",
            "scheduler": "running" if _job_runner.scheduler.running else "stopped"
        }
    }) 