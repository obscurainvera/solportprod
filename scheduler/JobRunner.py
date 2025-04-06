from config.config import get_config
from logs.logger import get_logger
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler.PortfolioScheduler import PortfolioScheduler
from scheduler.WalletsInvestedScheduler import WalletsInvestedScheduler
from scheduler.VolumebotScheduler import VolumeBotScheduler
from scheduler.PumpfunScheduler import PumpFunScheduler
from actions.WalletsInvestedInvestmentDetailsAction import  WalletsInvestedInvestmentDetailsAction
from database.operations.PortfolioDB import PortfolioDB
from apscheduler.schedulers.base import SchedulerNotRunningError, SchedulerAlreadyRunningError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from config.SchedulerConfig import SCHEDULER_CONFIG
from scheduler.AttentionScheduler import AttentionScheduler
from scheduler.DeactivateLostSMBalanceTokens import DeactiveLostSMBalanceTokens
from scheduler.ExecutionMonitorScheduler import ExecutionMonitorScheduler
import time
import requests
import sqlite3
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logger = get_logger(__name__)

def handleWalletsInvestedInPortSummaryTokens():
    """Standalone function to execute token analysis updates."""
    logger.info("Starting token analysis execution")
    scheduler = None
    try:
        scheduler = WalletsInvestedScheduler()
        scheduler.handleWalletsInvestedInPortSummaryTokens()
        logger.info("Token analysis completed successfully")
    except Exception as e:
        logger.error(f"Token analysis job failed: {e}")
        raise

def handlePortfolioSummary():
    """
    Standalone function to execute portfolio updates.
    Creates fresh instances for each execution to avoid serialization issues.
    """
    logger.info("Starting portfolio update execution")
    scheduler = None
    try:
        scheduler = PortfolioScheduler()
        scheduler.handlePortfolioSummaryUpdate()
        logger.info("Portfolio update completed successfully")
        
    except (requests.exceptions.RequestException, 
            OperationalError,
            SQLAlchemyError,
            TimeoutError,
            ConnectionError) as e:
        logger.warning(f"Encountered retryable error: {e}")
        time.sleep(SCHEDULER_CONFIG['job_defaults'].get('retry_delay', 300))
        
        try:
            if scheduler:
                scheduler.handlePortfolioSummaryUpdate()
                logger.info("Portfolio update completed successfully on retry")
        except Exception as retry_error:
            logger.error(f"Job failed after retry: {retry_error}")
            raise
            
    except Exception as e:
        logger.error(f"Job failed with non-retryable error: {e}")
        raise

def handleTokenDeactivation():
    """Standalone function to execute token deactivation."""
    logger.info("Starting token deactivation execution")
    scheduler = None
    try:
        scheduler = DeactiveLostSMBalanceTokens()
        scheduler.handleTokenDeactivation()
        logger.info("Token deactivation completed successfully")
    except Exception as e:
        logger.error(f"Token deactivation job failed: {e}")
        raise

def handleVolumeBotAnalysis():
    """Standalone function to execute volume bot analysis."""
    logger.info("Starting volume bot analysis execution")

    try:
        scheduler = VolumeBotScheduler()
        scheduler.handleVolumeAnalysisFromJob()
        logger.info("Volume bot analysis completed successfully")
    except Exception as e:
        logger.error(f"Volume bot analysis job failed: {e}")
        raise

def handlePumpFunAnalysis():
    """Standalone function to execute pump fun analysis."""
    logger.info("Starting pump fun analysis execution")
    scheduler = None
    try:
        scheduler = PumpFunScheduler()
        scheduler.handlePumpFunAnalysisFromJob()
        logger.info("Pump fun analysis completed successfully")
    except Exception as e:
        logger.error(f"Pump fun analysis job failed: {e}")
        raise

def handleExecutionMonitoring():
    """Standalone function to execute execution monitoring."""
    logger.info("Starting execution monitoring execution")
    scheduler = None
    try:
        scheduler = ExecutionMonitorScheduler()
        scheduler.handleActiveExecutionsMonitoring()
        logger.info("Execution monitoring completed successfully")
    except Exception as e:
        logger.error(f"Execution monitoring job failed: {e}")
        raise

def handleAttentionAnalysis():
    """Standalone function to execute attention analysis."""
    logger.info("Starting attention analysis execution")
    scheduler = None
    try:
        scheduler = AttentionScheduler()
        scheduler.handleAttentionData()
        logger.info("Attention analysis completed successfully")
    except Exception as e:
        logger.error(f"Attention analysis job failed: {e}")
        raise

class JobRunner:
    """
    Manages all scheduled jobs in the application with persistent storage.
    Handles multiple jobs accessing same database tables with proper locking.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize job runner with configuration
        
        Args:
            db_path: Path to portfolio database or database URL (Used for job store URL, not scheduler init)
        """
        config_instance = get_config()
      
        db_url = config_instance.get_database_url()
            
        self.db_path = db_url # Store the actual DB URL/path used
        # Initialize schedulers without db_path
        self.portfolio_scheduler = PortfolioScheduler() 
        self.scheduler = BackgroundScheduler(**SCHEDULER_CONFIG)
        
        # Use the correct db_url for the job store
        if self.db_path.startswith('postgresql'):
            jobstore_url = self.db_path
        else:
            # Assuming SQLite if not PostgreSQL
            jobstore_url = f'sqlite:///{self.db_path}'
            
        self.scheduler.add_jobstore(SQLAlchemyJobStore(url=jobstore_url), 'default')
        
        # Add event listener for job monitoring
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )
        logger.info("JobRunner initialized")

    def addPortfolioSummaryJobs(self):
        """
        Add portfolio related jobs with retry mechanism
        """
        self.scheduler.add_job(
            func=handlePortfolioSummary,
            trigger='cron',
            hour='*/4',  # Every 4 hours
            id='portfolio_summary',
            name='Portfolio Summary Update',
            replace_existing=True
        )
        logger.info("Added portfolio summary job")

    def addWalletsInvestedInATokenJobs(self):
        """
        Add token analysis jobs
        """
        self.scheduler.add_job(
            func=handleWalletsInvestedInPortSummaryTokens,
            trigger='cron',
            hour='*/6',  # Every 6 hours
            id='token_analysis',
            name='Token Analysis Update',
            replace_existing=True
        )
        logger.info("Added token analysis job")

    def addAttentionAnalysisJobs(self):
        """
        Add attention analysis jobs
        """
        self.scheduler.add_job(
            func=handleAttentionAnalysis,
            trigger='cron',
            hour='*/2',  # Every 2 hours
            id='attention_analysis',
            name='Attention Analysis Update',
            replace_existing=True
        )
        logger.info("Added attention analysis job")

    def addTokenDeactivationJob(self):
        """
        Add token deactivation job
        """
        self.scheduler.add_job(
            func=handleTokenDeactivation,
            trigger='cron',
            hour='*/12',  # Every 12 hours
            id='token_deactivation',
            name='Token Deactivation',
            replace_existing=True
        )
        logger.info("Added token deactivation job")

    def addVolumeBotJobs(self):
        """
        Add volume bot analysis jobs
        """
        self.scheduler.add_job(
            func=handleVolumeBotAnalysis,
            trigger='cron',
            minute='*/30',  # Every 30 minutes
            id='volume_bot_analysis',
            name='Volume Bot Analysis',
            replace_existing=True
        )
        logger.info("Added volume bot analysis job")

    def addPumpFunJobs(self):
        """
        Add pump fun analysis jobs
        """
        self.scheduler.add_job(
            func=handlePumpFunAnalysis,
            trigger='cron',
            minute='*/15',  # Every 15 minutes
            id='pump_fun_analysis',
            name='Pump Fun Analysis',
            replace_existing=True
        )
        logger.info("Added pump fun analysis job")

    def addExecutionMonitoringJobs(self):
        """
        Add execution monitoring jobs
        """
        self.scheduler.add_job(
            func=handleExecutionMonitoring,
            trigger='cron',
            minute='*/5',  # Every 5 minutes
            id='execution_monitoring',
            name='Execution Monitoring',
            replace_existing=True
        )
        logger.info("Added execution monitoring job")

    def setup_jobs(self):
        try:
            existing_jobs = self.scheduler.get_jobs()
            job_ids = [job.id for job in existing_jobs]
            
            # Add all jobs
            if 'portfolio_summary' not in job_ids:
                self.addPortfolioSummaryJobs()
            
            if 'token_analysis' not in job_ids:
                self.addWalletsInvestedInATokenJobs()
            
            if 'attention_analysis' not in job_ids:
                self.addAttentionAnalysisJobs()

            if 'token_deactivation' not in job_ids:
                self.addTokenDeactivationJob()

            if 'volume_bot_analysis' not in job_ids:
                self.addVolumeBotJobs()

            if 'pump_fun_analysis' not in job_ids:
                self.addPumpFunJobs()
            
            if 'execution_monitoring' not in job_ids:
                self.addExecutionMonitoringJobs()
            
            logger.info("All jobs configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup jobs: {e}")
            raise

    def _job_listener(self, event):
        """Handle job execution events"""
        if event.exception:
            logger.error(f"Job {event.job_id} raised an exception: {event.exception}")
            self._record_job_execution(event.job_id, 'error', str(event.exception))
        else:
            logger.info(f"Job {event.job_id} executed successfully")
            self._record_job_execution(event.job_id, 'success')
            
    def _record_job_execution(self, job_id, status, error_message=None, start_time=None):
        """Record job execution in the database using JobHandler"""
        try:
            from database.operations.PortfolioDB import PortfolioDB
            
            # Use the JobHandler to record the execution
            with PortfolioDB() as db:
                if hasattr(db, 'job') and db.job is not None:
                    job_handler = db.job
                    
                    if status == 'success':
                        # For successful executions, we need to start and complete in one go
                        execution_id = job_handler.startJobExecution(job_id)
                        job_handler.completeJobExecution(execution_id, 'COMPLETED')
                        logger.info(f"Recorded successful execution for job {job_id}")
                    elif status == 'error':
                        # For failed executions, record with error message
                        execution_id = job_handler.startJobExecution(job_id)
                        job_handler.completeJobExecution(execution_id, 'FAILED', error_message)
                        logger.info(f"Recorded failed execution for job {job_id}")
                else:
                    logger.error("JobHandler not available in database connection")
        except Exception as e:
            logger.error(f"Error recording job execution: {e}")

    def start(self):
        """Start the scheduler"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler started successfully")
            else:
                logger.info("Scheduler is already running")
        except SchedulerAlreadyRunningError:
            logger.info("Scheduler is already running")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler shut down successfully")
            else:
                logger.info("Scheduler is not running")
        except Exception as e:
            logger.error(f"Failed to shut down scheduler: {e}")
            raise

    def update_job_schedule(self, job_id: str, **schedule_args):
        """
        Update the schedule for a specific job
        
        Args:
            job_id: ID of the job to update
            schedule_args: Dictionary of schedule parameters
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.reschedule(**schedule_args)
                logger.info(f"Updated schedule for job {job_id}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to update job schedule: {e}")
            return False

    def modify_job_timing(self, job_id: str, timing_type: str, value: str):
        """
        Modify the timing of a specific job
        
        Args:
            job_id: ID of the job to modify
            timing_type: Type of timing to modify (hour, minute, day, etc.)
            value: New value for the timing
        """
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found")
                return False
                
            # Get current trigger args
            trigger_args = {}
            for field in job.trigger.fields:
                field_name = field.name
                if field_name != timing_type:
                    trigger_args[field_name] = str(field)
            
            # Add new timing value
            trigger_args[timing_type] = value
            
            # Reschedule job
            job.reschedule(trigger='cron', **trigger_args)
            logger.info(f"Updated {timing_type} to {value} for job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to modify job timing: {e}")
            return False

    def run_job(self, job_id: str, external_scheduler=None):
        """
        Run a specific job immediately
        
        Args:
            job_id: ID of the job to run
            external_scheduler: Optional external scheduler to use
            
        Returns:
            bool: True if job was found and executed, False otherwise
        """
        try:
            # Use provided scheduler or the default one
            scheduler = external_scheduler or self.scheduler
            job = scheduler.get_job(job_id)
            
            if not job:
                logger.warning(f"Job {job_id} not found")
                return False
                
            # Get the job function and args
            job_func = job.func
            job_args = job.args or []
            job_kwargs = job.kwargs or {}
            
            # Execute the job
            logger.info(f"Running job {job_id} immediately")
            job_func(*job_args, **job_kwargs)
            
            # Record the execution
            self._record_job_execution(job_id, 'success')
            
            return True
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            self._record_job_execution(job_id, 'error', str(e))
            return False

