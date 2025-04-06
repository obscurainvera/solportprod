from config.Config import get_config
from flask import Blueprint, jsonify, request, current_app
from logs.logger import get_logger
from scheduler.JobRunner import JobRunner
from apscheduler.schedulers.background import BackgroundScheduler
from config.SchedulerConfig import SCHEDULER_CONFIG
from sqlalchemy import create_engine, text
import time
import json
from datetime import datetime

logger = get_logger(__name__)

scheduler_bp = Blueprint('scheduler', __name__)

# Create a single global scheduler instance
_scheduler = None

def getScheduler() -> BackgroundScheduler:
    """Get the running scheduler instance"""
    global _scheduler
    try:
        if _scheduler is None:
            _scheduler = BackgroundScheduler(**SCHEDULER_CONFIG)
            _scheduler.start()
            logger.info("Created new scheduler instance")
        return _scheduler
    except Exception as e:
        logger.error(f"Error getting scheduler: {e}")
        raise

@scheduler_bp.route('/api/scheduler/update-timing', methods=['POST', 'OPTIONS'])
def updateJobTiming():
    """Update the timing of a specific job"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        timingType = data.get('timing_type')
        value = data.get('value')
        
        if not all([jobId, timingType, value]):
            error_response = jsonify({'error': 'Missing required parameters'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            error_response = jsonify({'error': f'Job {jobId} not found'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 404
            
        # Map timing_type to the correct parameter name for CronTrigger
        cron_param_map = {
            'minutes': 'minute',
            'hours': 'hour',
            'days': 'day',
            'months': 'month'
        }
        
        # Get the correct parameter name for CronTrigger
        cron_param = cron_param_map.get(timingType, timingType)
        
        # Get current trigger args
        triggerArgs = {}
        for field in job.trigger.fields:
            field_name = field.name
            if field_name != cron_param:
                triggerArgs[field_name] = str(field)
        
        # Add new timing value
        triggerArgs[cron_param] = value
        
        # Reschedule job
        job.reschedule(trigger='cron', **triggerArgs)
        logger.info(f"Successfully updated {cron_param} to {value} for job {jobId}")
        
        response = jsonify({
            'success': True,
            'message': f'Successfully updated {cron_param} for job {jobId}'
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response
        
    except Exception as e:
        logger.error(f"Error updating job timing: {e}")
        error_response = jsonify({'error': str(e)})
        config = get_config()
        error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return error_response, 500

@scheduler_bp.route('/api/scheduler/jobs', methods=['GET', 'OPTIONS'])
def getJobs():
    """Get list of all scheduled jobs"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        scheduler = getScheduler()
        jobs = scheduler.get_jobs()
        
        jobList = []
        for job in jobs:
            triggerFields = {}
            for field in job.trigger.fields:
                triggerFields[field.name] = str(field)
                
            jobList.append({
                'id': job.id,
                'name': job.name,
                'nextRun': str(job.next_run_time) if job.next_run_time else None,
                'trigger': triggerFields
            })
        
        response = jsonify({
            'success': True,
            'jobs': jobList
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        error_response = jsonify({'error': str(e)})
        config = get_config()
        error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return error_response, 500

@scheduler_bp.route('/api/scheduler/run-job', methods=['POST', 'OPTIONS'])
def runJob():
    """Run a specific job immediately"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        
        if not jobId:
            error_response = jsonify({'error': 'Missing job_id parameter'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 400
            
        # Get the global scheduler
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            error_response = jsonify({'error': f'Job {jobId} not found'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 404
            
        # Create a JobRunner instance and run the job with the global scheduler
        logger.info(f"Manually triggering job {jobId}")
        job_runner = JobRunner()
        
        try:
            success = job_runner.run_job(jobId, external_scheduler=scheduler)
            
            if success:
                response = jsonify({
                    'success': True,
                    'message': f'Job {jobId} executed successfully'
                })
            else:
                response = jsonify({
                    'success': False,
                    'message': f'Job {jobId} not found or could not be executed'
                })
                
            config = get_config()
            response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return response
            
        except Exception as job_error:
            logger.error(f"Error executing job {jobId}: {job_error}")
            error_response = jsonify({
                'success': False,
                'error': str(job_error),
                'message': f'Error executing job {jobId}'
            })
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 500
        
    except Exception as e:
        logger.error(f"Error in runJob API: {e}")
        error_response = jsonify({'error': str(e)})
        config = get_config()
        error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return error_response, 500

@scheduler_bp.route('/api/scheduler/pause-job', methods=['POST', 'OPTIONS'])
def pauseJob():
    """Pause a specific job"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        
        if not jobId:
            error_response = jsonify({'error': 'Missing job_id parameter'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            error_response = jsonify({'error': f'Job {jobId} not found'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 404
            
        # Pause the job
        scheduler.pause_job(job.id)
        logger.info(f"Paused job {jobId}")
        
        response = jsonify({
            'success': True,
            'message': f'Successfully paused job {jobId}'
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response
        
    except Exception as e:
        logger.error(f"Error pausing job: {e}")
        error_response = jsonify({'error': str(e)})
        config = get_config()
        error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return error_response, 500

@scheduler_bp.route('/api/scheduler/resume-job', methods=['POST', 'OPTIONS'])
def resumeJob():
    """Resume a specific job"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        
        if not jobId:
            error_response = jsonify({'error': 'Missing job_id parameter'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            error_response = jsonify({'error': f'Job {jobId} not found'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 404
            
        # Resume the job
        scheduler.resume_job(job.id)
        logger.info(f"Resumed job {jobId}")
        
        response = jsonify({
            'success': True,
            'message': f'Successfully resumed job {jobId}'
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response
        
    except Exception as e:
        logger.error(f"Error resuming job: {e}")
        error_response = jsonify({'error': str(e)})
        config = get_config()
        error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return error_response, 500

@scheduler_bp.route('/api/scheduler/job-history/<job_id>', methods=['GET', 'OPTIONS'])
def getJobHistory(job_id):
    """Get execution history for a specific job"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        if not job_id:
            error_response = jsonify({'error': 'Missing job_id parameter'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(job_id)
        
        if not job:
            error_response = jsonify({'error': f'Job {job_id} not found'})
            config = get_config()
            error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
            return error_response, 404
            
        # Get job execution history from the database
        history = []
        
        # Connect to the jobs database
        config_instance = get_config()
        
        # Use SQLAlchemy for database access (compatible with both SQLite and PostgreSQL)
        engine = create_engine(config_instance.get_database_url())
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, start_time, end_time, status, error_message, created_at
                    FROM job_executions
                    WHERE job_id = :job_id
                    ORDER BY start_time DESC
                    LIMIT 10
                """),
                {"job_id": job_id}
            )
            
            # Convert to list of dictionaries
            for row in result:
                history.append({
                    'id': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'status': row[3],
                    'error_message': row[4],
                    'created_at': row[5]
                })
        
        response = jsonify({
            'success': True,
            'job_id': job_id,
            'history': history
        })
        config = get_config()
        response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return response
        
    except Exception as e:
        logger.error(f"Error getting job history: {str(e)}")
        error_response = jsonify({'error': str(e)})
        config = get_config()
        error_response.headers.add('Access-Control-Allow-Origin', config.CORS_ORIGINS[0] if config.CORS_ORIGINS else '*')
        return error_response, 500