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
        
        # Build SQL strings outside of text() function
        jobs_sql = f"""
            CREATE TABLE IF NOT EXISTS jobs (
                id {is_postgres and 'SERIAL' or 'INTEGER'} PRIMARY KEY {is_postgres and '' or 'AUTOINCREMENT'},
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
        
        job_executions_sql = f"""
            CREATE TABLE IF NOT EXISTS job_executions (
                id {is_postgres and 'SERIAL' or 'INTEGER'} PRIMARY KEY {is_postgres and '' or 'AUTOINCREMENT'},
                job_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status INTEGER NOT NULL,
                result TEXT,
                error TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
        """
        
        with self.conn_manager.transaction() as cursor:
            cursor.execute(text(jobs_sql))
            cursor.execute(text(job_executions_sql))
        logger.info("Job tables created")

    def startJobExecution(self, job_id: str) -> int:
        """Start a job execution and return its ID."""
        config = get_config()
        is_postgres = config.DB_TYPE == 'postgres'
        
        with self.conn_manager.transaction() as cursor:
            if is_postgres:
                cursor.execute(
                    text("INSERT INTO job_executions (job_id, start_time, status) VALUES (:job_id, :start_time, :status) RETURNING id"),
                    {'job_id': job_id, 'start_time': datetime.utcnow(), 'status': JobStatus.RUNNING.value}
                )
                return cursor.fetchone()['id']
            else:
                cursor.execute(
                    text("INSERT INTO job_executions (job_id, start_time, status) VALUES (:job_id, :start_time, :status)"),
                    {'job_id': job_id, 'start_time': datetime.utcnow(), 'status': JobStatus.RUNNING.value}
                )
                return cursor.lastrowid

    def completeJobExecution(self, execution_id: int, status: str, error_message: str = None) -> bool:
        """Complete a job execution with status and optional error."""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(
                text("UPDATE job_executions SET end_time = :end_time, status = :status, error = :error WHERE id = :id"),
                {'end_time': datetime.utcnow(), 'status': JobStatus[status].value, 'error': error_message, 'id': execution_id}
            )
            return True