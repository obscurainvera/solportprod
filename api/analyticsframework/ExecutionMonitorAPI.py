from config.Config import get_config
"""
API endpoints for strategy execution monitoring
"""
from flask import Blueprint, jsonify, request
from framework.analyticsframework.ExecutionMonitor import ExecutionMonitor
from logs.logger import get_logger
import time
from scheduler.JobRunner import JobRunner

logger = get_logger(__name__)

# Create a Blueprint for execution monitoring endpoints
execution_monitor_bp = Blueprint('execution_monitor', __name__)

@execution_monitor_bp.route('/api/analyticsframework/triggerexecutionmonitoring', methods=['POST', 'OPTIONS'])
def triggerExecutionMonitoring():
    """
    API endpoint to manually trigger execution monitoring
    
    Checks all active strategy executions for profit targets and stop losses,
    executing trades as needed.
    
    Returns:
        JSON response with monitoring statistics and execution status
    """
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    startTime = time.time()
    logger.info("Manual execution monitoring triggered via API")
    
    try:
        # Temporarily pause scheduler
        jobRunner = JobRunner()
        wasRunning = jobRunner.scheduler.running
        if wasRunning:
            jobRunner.scheduler.pause()
        
        executionMonitor = ExecutionMonitor()
        
        # Execute monitoring process
        stats = executionMonitor.monitorActiveExecutions()
        
        # Ensure stats is a dictionary
        if stats is None:
            stats = {}
        
        # Calculate total execution time
        executionTime = time.time() - startTime
        stats['apiExecutionTimeSec'] = round(executionTime, 2)
        
        # Prepare response message
        message = (
            f"Monitoring completed in {stats['apiExecutionTimeSec']}s: "
            f"Processed {stats.get('executions_processed', 0)} executions, "
            f"Stop losses: {stats.get('stop_losses_triggered', 0)}, "
            f"Profit targets: {stats.get('profit_targets_hit', 0)}"
        )
        
        logger.info(message)
        
        # Resume scheduler when done
        if wasRunning:
            jobRunner.scheduler.resume()
        
        return jsonify({
            "status": "success",
            "message": message,
            "statistics": stats
        })
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"Execution monitoring failed: {str(e)}"
        logger.error(errorMessage, exc_info=True)
        
        # Resume scheduler when done
        if wasRunning:
            jobRunner.scheduler.resume()
        
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTimeSec": round(executionTime, 2)
        }), 500 