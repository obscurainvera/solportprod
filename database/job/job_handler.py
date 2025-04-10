"""
Job Handler Module

Manages job metadata and execution history in the database, supporting both
PostgreSQL and SQLite with SQLAlchemy.
"""

from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from logs.logger import get_logger
from sqlalchemy import text
from datetime import datetime
from enum import Enum

logger = get_logger(__name__)

class JobStatus(Enum):
    """Enum for job status values."""
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    RECURRING = 5

class JobHandler(BaseDBHandler):
    """Database handler for job scheduling and execution tracking."""
    def __init__(self, conn_manager=None):
        """Initialize with connection manager and create tables."""
        super().__init__(conn_manager or DatabaseConnectionManager())
        self._create_tables()

    def _create_tables(self):
        """Create jobs and job_executions tables if they don't exist."""
        config = get_config()
        is_postgres = config.DB_TYPE == 'postgres'
        
        jobs_sql = """
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                job_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                params TEXT,
                status INTEGER NOT NULL,
                schedule TEXT,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        job_executions_sql = """
            CREATE TABLE IF NOT EXISTS job_executions (
                id SERIAL PRIMARY KEY,
                job_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status INTEGER NOT NULL,
                result TEXT,
                error_message TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
        """
        
        with self.conn_manager.transaction() as cursor:
            cursor.execute(text(jobs_sql))
            cursor.execute(text(job_executions_sql))
            
            # Check if error_message column exists, if not, try to add it
            if is_postgres:
                try:
                    cursor.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name='job_executions' AND column_name='error_message'
                    """))
                    
                    # If error column doesn't exist, add error_message column
                    if not cursor.fetchone():
                        cursor.execute(text("""
                            ALTER TABLE job_executions 
                            ADD COLUMN IF NOT EXISTS error_message TEXT
                        """))
                        
                    # Check if 'error' column exists (old name)
                    cursor.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name='job_executions' AND column_name='error'
                    """))
                    
                    # Rename error to error_message if it exists
                    if cursor.fetchone():
                        cursor.execute(text("""
                            ALTER TABLE job_executions 
                            RENAME COLUMN error TO error_message
                        """))
                        
                except Exception as e:
                    logger.warning(f"Error checking/creating error_message column: {e}")
                    
        logger.info("Job tables created")

    def startJobExecution(self, job_id: str) -> int:
        """Start a job execution and return its ID."""
        config = get_config()
        is_postgres = config.DB_TYPE == 'postgres'
        
        with self.conn_manager.transaction() as cursor:
            if is_postgres:
                cursor.execute(
                    text("INSERT INTO job_executions (job_id, start_time, status) VALUES (%s, %s, %s) RETURNING id"),
                    (job_id, datetime.now(), JobStatus.RUNNING.value)
                )
                return cursor.fetchone()['id']
            else:
                cursor.execute(
                    text("INSERT INTO job_executions (job_id, start_time, status) VALUES (?, ?, ?)"),
                    (job_id, datetime.utcnow(), JobStatus.RUNNING.value)
                )
                return cursor.lastrowid

    def completeJobExecution(self, execution_id: int, status: str, error_message: str = None) -> bool:
        """Complete a job execution with status and optional error."""
        config = get_config()
        is_postgres = config.DB_TYPE == 'postgres'
        
        with self.conn_manager.transaction() as cursor:
            if is_postgres:
                try:
                    # First try with error_message column
                    cursor.execute(
                        text("UPDATE job_executions SET end_time = %s, status = %s, error_message = %s WHERE id = %s"),
                        (datetime.utcnow(), JobStatus[status].value, error_message, execution_id)
                    )
                except Exception:
                    # If error_message column doesn't exist, try without it
                    cursor.execute(
                        text("UPDATE job_executions SET end_time = %s, status = %s WHERE id = %s"),
                        (datetime.utcnow(), JobStatus[status].value, execution_id)
                    )
            else:
                try:
                    cursor.execute(
                        text("UPDATE job_executions SET end_time = ?, status = ?, error_message = ? WHERE id = ?"),
                        (datetime.utcnow(), JobStatus[status].value, error_message, execution_id)
                    )
                except Exception:
                    cursor.execute(
                        text("UPDATE job_executions SET end_time = ?, status = ? WHERE id = ?"),
                        (datetime.utcnow(), JobStatus[status].value, execution_id)
                    )
            return True