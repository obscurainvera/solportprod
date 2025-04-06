"""
Scheduler configuration settings
"""
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from config.Config import get_config
import logging
from logs.logger import get_logger
import os

logger = get_logger(__name__)

# Get database configuration
config = get_config()
try:
    db_url = config.get_database_url()
    # Check if we're using SQLite
    if config.DB_TYPE == 'sqlite':
        # Make sure the directory exists
        db_dir = os.path.dirname(os.path.abspath(config.DB_PATH))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        job_store = SQLAlchemyJobStore(url=f'sqlite:///{config.DB_PATH}')
    else:
        # Using PostgreSQL
        job_store = SQLAlchemyJobStore(url=db_url)
    
    # APScheduler configuration
    SCHEDULER_CONFIG = {
        'jobstores': {
            'default': job_store  # Use the configured database URL
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
    logger.info(f"Scheduler configured with database jobstore: {config.DB_TYPE}")
    
except Exception as e:
    logger.error(f"Error configuring SQLAlchemyJobStore: {e}")
    logger.info("Falling back to MemoryJobStore for scheduler")
    # Fallback configuration with memory jobstore
    SCHEDULER_CONFIG = {
        'jobstores': {
            'default': MemoryJobStore()  # In-memory job store as fallback
        },
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