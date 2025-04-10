"""
Job Runner Module

Manages background job scheduling using APScheduler for periodic tasks like
portfolio updates, token analysis, and volume monitoring.
"""

from config.Config import get_config
from logs.logger import get_logger
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from config.SchedulerConfig import SCHEDULER_CONFIG
from scheduler.PortfolioScheduler import PortfolioScheduler
from scheduler.WalletsInvestedScheduler import WalletsInvestedScheduler
from scheduler.VolumebotScheduler import VolumeBotScheduler
from scheduler.PumpfunScheduler import PumpFunScheduler
from scheduler.AttentionScheduler import AttentionScheduler
from scheduler.DeactivateLostSMBalanceTokens import DeactiveLostSMBalanceTokens
from scheduler.ExecutionMonitorScheduler import ExecutionMonitorScheduler
from database.operations.PortfolioDB import PortfolioDB
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.job.job_handler import JobHandler
import time
import requests
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import threading


logger = get_logger(__name__)

# Default retry settings
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds

def with_retries(job_func, scheduler_class):
    """Wrapper for job execution with retry logic."""
    logger.info(f"Starting {job_func.__name__} execution")
    for attempt in range(MAX_RETRIES):
        try:
            scheduler = scheduler_class()
            job_func(scheduler)
            logger.info(f"{job_func.__name__} completed successfully")
            break
        except (requests.exceptions.RequestException, OperationalError, SQLAlchemyError, TimeoutError, ConnectionError) as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Retryable error on attempt {attempt + 1}: {e}")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"{job_func.__name__} failed after {MAX_RETRIES} attempts: {e}")
                raise


def run_volume_bot_analysis_job():
    """Run volume bot analysis with retry logic."""
    with_retries(VolumeBotScheduler.handleVolumeAnalysisFromJob, VolumeBotScheduler)

def run_pump_fun_analysis_job():
    """Run pump fun analysis with retry logic."""
    with_retries(PumpFunScheduler.handlePumpFunAnalysisFromJob, PumpFunScheduler)

def run_execution_monitoring_job():
    """Monitor active executions with retry logic."""
    with_retries(ExecutionMonitorScheduler.handleActiveExecutionsMonitoring, ExecutionMonitorScheduler)

class JobRunner:
    """
    Manages APScheduler for scheduling and executing background jobs.
    
    Features:
    - Configurable job schedules via config
    - Persistent job store with SQLAlchemy
    - Job execution monitoring and logging
    """
    def __init__(self):
        """Initialize scheduler with job store and event listeners."""
        config = get_config()
        self.scheduler = BackgroundScheduler(**SCHEDULER_CONFIG)
        try:
            db_url = config.get_database_url()
            if 'jobstores' not in SCHEDULER_CONFIG:
                self.scheduler.add_jobstore(SQLAlchemyJobStore(url=db_url), 'default')
                logger.info("Added SQLAlchemy job store")
            self.scheduler.add_listener(self._job_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
            self.setup_jobs()
            logger.info("JobRunner initialized")
        except Exception as e:
            logger.error(f"Failed to initialize JobRunner: {e}")
            logger.warning("Using in-memory job store")

    def setup_jobs(self):
        """Configure all scheduled jobs with configurable triggers."""
        config = get_config()
        jobs = [
            ('volume_bot_analysis', {'minute': '*/10'}),
            ('pump_fun_analysis', {'minute': '*/10'}),
            ('execution_monitoring', {'minute': '*/1'})
        ]
        for job_id, default_schedule in jobs:
            schedule = config.JOB_SCHEDULES.get(job_id, default_schedule)
            
            # Use named functions instead of lambdas
            if job_id == 'volume_bot_analysis':
                job_func = run_volume_bot_analysis_job
            elif job_id == 'pump_fun_analysis':
                job_func = run_pump_fun_analysis_job
            elif job_id == 'execution_monitoring':
                job_func = run_execution_monitoring_job
            
            self.scheduler.add_job(
                func=job_func,
                trigger='cron',
                **schedule,
                id=job_id,
                name=job_id.replace('_', ' ').title(),
                replace_existing=True
            )
            logger.info(f"Added job: {job_id}")

    def _job_listener(self, event):
        """Log and record job execution events."""
        job_id = event.job_id
        if event.exception:
            logger.error(f"Job {job_id} failed: {event.exception}")
            self._record_job_execution(job_id, 'error', str(event.exception))
        else:
            logger.info(f"Job {job_id} succeeded")
            self._record_job_execution(job_id, 'success')

    def _record_job_execution(self, job_id, status, error_message=None):
        """
        Record job execution status in the database.
        Prevents recursion by using a simple flag to avoid nested calls.
        """
        # Use a thread-local storage instead of class attribute for recursion detection
        thread_local = threading.local()
        
        # Check if we're already inside this method for this thread
        if hasattr(thread_local, 'recording_job'):
            # We're already recording a job execution, don't recurse
            logger.warning(f"Avoiding recursive call to _record_job_execution for job {job_id}")
            return
        
        try:
            # Set flag to prevent recursion
            thread_local.recording_job = True
            
            # Create a connection manager that doesn't rely on the scheduler's connection
            try:
                # Create a fresh connection manager
                conn_manager = DatabaseConnectionManager()
                
                # Create a job handler directly with this connection
                job_handler = JobHandler(conn_manager)
                
                # Record the job execution
                try:
                    execution_id = job_handler.startJobExecution(job_id)
                    job_handler.completeJobExecution(execution_id, 'COMPLETED' if status == 'success' else 'FAILED', error_message)
                    logger.info(f"Recorded {status} for job {job_id}")
                except Exception as e:
                    logger.error(f"Error recording job execution details: {str(e)}")
                    
                # Ensure we properly close the connection
                try:
                    conn_manager.close()
                except Exception as close_error:
                    logger.error(f"Error closing connection manager: {str(close_error)}")
                    
            except Exception as e:
                logger.error(f"Failed to record job execution: {str(e)}")
                
        finally:
            # Always clean up the thread-local flag
            if hasattr(thread_local, 'recording_job'):
                delattr(thread_local, 'recording_job')

    def start(self):
        """Start the scheduler if not already running."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")