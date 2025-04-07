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
import psycopg2
import sqlalchemy

logger = get_logger(__name__)

# Initialize default scheduler configuration with memory job store
job_store = MemoryJobStore()

# Get database configuration
config = get_config()
try:
    db_url = config.get_database_url()
    logger.info(f"Attempting to connect using database URL type: {config.DB_TYPE}")
    
    # Check if we're using SQLite
    if config.DB_TYPE == 'sqlite':
        # Make sure the directory exists
        db_dir = os.path.dirname(os.path.abspath(config.DB_PATH))
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        job_store = SQLAlchemyJobStore(url=f'sqlite:///{config.DB_PATH}')
    else:
        # Validate required PostgreSQL parameters
        if not config.DB_PORT:
            logger.error("Error configuring SQLAlchemyJobStore: DB_PORT is empty")
            logger.info("Falling back to MemoryJobStore for scheduler")
        else:
            # Using PostgreSQL - do a basic connection test first
            try:
                # Test direct connection
                conn = psycopg2.connect(
                    user=config.DB_USER,
                    password=config.DB_PASSWORD,
                    host=config.DB_HOST,
                    port=config.DB_PORT,
                    dbname=config.DB_NAME,
                    sslmode=config.DB_SSLMODE,
                    gssencmode=config.DB_GSSENCMODE
                )
                conn.close()
                logger.info(f"Successfully connected to PostgreSQL with user {config.DB_USER}")
                
                # Use the SQLAlchemy store if connection succeeded
                job_store = SQLAlchemyJobStore(url=db_url)
                
            except (psycopg2.OperationalError, sqlalchemy.exc.OperationalError) as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                logger.warning("Using memory-based job store due to connection failure")
    
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
    logger.info(f"Scheduler configured with jobstore type: {type(job_store).__name__}")
    
except Exception as e:
    logger.error(f"Error configuring SQLAlchemyJobStore: {e}")
    logger.info("Falling back to MemoryJobStore for scheduler")
    
    # Fallback configuration with in-memory storage
    SCHEDULER_CONFIG = {
        'jobstores': {
            'default': MemoryJobStore()
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
    logger.info("Scheduler configured with memory-based job store")

# Job retry settings
JOB_RETRY_ATTEMPTS = 3
JOB_RETRY_DELAY = 300  # 5 minutes 