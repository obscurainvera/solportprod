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
from sqlalchemy.engine.url import URL
import psycopg2
from psycopg2.extras import RealDictCursor

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
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        timingType = data.get('timing_type')
        value = data.get('value')
        
        if not all([jobId, timingType, value]):
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Job {jobId} not found'
            }), 404
            
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
        
        return jsonify({
            'success': True,
            'status': 'success',
            'message': f'Successfully updated {cron_param} for job {jobId}'
        })
        
    except Exception as e:
        logger.error(f"Error updating job timing: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@scheduler_bp.route('/api/scheduler/jobs', methods=['GET', 'OPTIONS'])
def getJobs():
    """Get list of all scheduled jobs"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
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
        
        return jsonify({
            'success': True,
            'jobs': jobList
        })
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@scheduler_bp.route('/api/scheduler/run-job', methods=['POST', 'OPTIONS'])
def runJob():
    """Run a specific job immediately"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        
        if not jobId:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Missing job_id parameter'
            }), 400
            
        # Get the global scheduler
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Job {jobId} not found'
            }), 404
            
        # Create a JobRunner instance and run the job with the global scheduler
        logger.info(f"Manually triggering job {jobId}")
        job_runner = JobRunner()
        
        try:
            success = job_runner.run_job(jobId, external_scheduler=scheduler)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Job {jobId} executed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'status': 'error',
                    'message': f'Job {jobId} not found or could not be executed'
                }), 404
                
        except Exception as job_error:
            logger.error(f"Error executing job {jobId}: {job_error}")
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Error executing job {jobId}: {str(job_error)}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in runJob API: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@scheduler_bp.route('/api/scheduler/pause-job', methods=['POST', 'OPTIONS'])
def pauseJob():
    """Pause a specific job"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        
        if not jobId:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Missing job_id parameter'
            }), 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Job {jobId} not found'
            }), 404
            
        # Pause the job
        scheduler.pause_job(job.id)
        logger.info(f"Paused job {jobId}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully paused job {jobId}'
        })
        
    except Exception as e:
        logger.error(f"Error pausing job: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@scheduler_bp.route('/api/scheduler/resume-job', methods=['POST', 'OPTIONS'])
def resumeJob():
    """Resume a specific job"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        data = request.json
        jobId = data.get('job_id')
        
        if not jobId:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Missing job_id parameter'
            }), 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(jobId)
        
        if not job:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Job {jobId} not found'
            }), 404
            
        # Resume the job
        scheduler.resume_job(job.id)
        logger.info(f"Resumed job {jobId}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully resumed job {jobId}'
        })
        
    except Exception as e:
        logger.error(f"Error resuming job: {e}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@scheduler_bp.route('/api/scheduler/job-history/<job_id>', methods=['GET', 'OPTIONS'])
def getJobHistory(job_id):
    """Get execution history for a specific job"""
    if request.method == 'OPTIONS':
        # Let Flask-CORS handle OPTIONS response
        return jsonify({}), 200
        
    try:
        if not job_id:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': 'Missing job_id parameter'
            }), 400
            
        scheduler = getScheduler()
        job = scheduler.get_job(job_id)
        
        if not job:
            return jsonify({
                'success': False,
                'status': 'error',
                'message': f'Job {job_id} not found'
            }), 404
            
        # Get job execution history from the database
        history = []
        
        # Connect to the jobs database
        config_instance = get_config()
    
        history = []
        try:
            # Direct connection to PostgreSQL
            conn = psycopg2.connect(
                user=config_instance.DB_USER,
                password=config_instance.DB_PASSWORD,
                host=config_instance.DB_HOST,
                port=config_instance.DB_PORT,
                dbname=config_instance.DB_NAME,
                sslmode=config_instance.DB_SSLMODE,
                gssencmode=config_instance.DB_GSSENCMODE
            )
            
            # Use RealDictCursor to get dictionary-like results
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, start_time, end_time, status, error_message, created_at
                    FROM job_executions
                    WHERE job_id = %s
                    ORDER BY start_time DESC
                    LIMIT 10
                """, (job_id,))
                
                # Fetch all results
                history = [dict(row) for row in cur.fetchall()]
            
            conn.close()
            
        except Exception as db_error:
            logger.error(f"Database error getting job history: {str(db_error)}")
            # Return empty history on error
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting job history: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500