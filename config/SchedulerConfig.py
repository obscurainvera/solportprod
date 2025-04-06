"""
Scheduler configuration settings
"""
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from config.Config import get_config
import logging
from logs.logger import get_logger

logger = get_logger(__name__)

# Get database configuration
config = get_config()
try:
    db_url = config.get_database_url()
    # Configure job store
    job_store = SQLAlchemyJobStore(url=db_url)
    
    # APScheduler configuration
    SCHEDULER_CONFIG = {
        'jobstores': {
            'default': job_store  # Use the same database URL as the main application
        },
        'executors': {
            'default': ThreadPoolExecutor(20)
        },
        'job_defaults': {
            'coalesce': True,          # Combine multiple pending runs into one
            'max_instances': 1,        # Only one instance of each job can run at a time
            'misfire_grace_time': 3600,  # How long after missed run time a job should still run
            'max_retries': 3,          # Maximum number of retry attempts
            'retry_delay': 300         # Delay between retry attempts (in seconds)
        },
        'timezone': 'UTC'
    }
except Exception as e:
    logger.error(f"Error configuring SQLAlchemyJobStore: {e}")
    # Fallback configuration without jobstore
    SCHEDULER_CONFIG = {
        'executors': {
            'default': ThreadPoolExecutor(20)
        },
        'job_defaults': {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 3600,
            'max_retries': 3,
            'retry_delay': 300
        },
        'timezone': 'UTC'
    }

# Job retry settings
JOB_RETRY_ATTEMPTS = 3
JOB_RETRY_DELAY = 300  # 5 minutes 