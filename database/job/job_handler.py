from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import Dict, List, Optional, Any
from datetime import datetime
import pytz
from logs.logger import get_logger
from enum import Enum
from sqlalchemy import text

logger = get_logger(__name__)

class JobStatus(Enum):
    """Status codes for job entries"""
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    RECURRING = 5

class JobHandler(BaseDBHandler):
    """Handler for job scheduling and tracking"""

    def __init__(self, conn_manager=None):
        """Initialize with optional connection manager"""
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()
            
            # Check if we're using PostgreSQL or SQLite
            if config.DB_TYPE == 'postgres':
                cursor.execute(text('''
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
                '''))
                
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS job_executions (
                        id SERIAL PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        status INTEGER NOT NULL,
                        result TEXT,
                        error TEXT,
                        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
                    )
                '''))
            else:
                # SQLite syntax
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                '''))
                
                cursor.execute(text('''
                    CREATE TABLE IF NOT EXISTS job_executions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        status INTEGER NOT NULL,
                        result TEXT,
                        error TEXT,
                        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
                    )
                '''))

    def get_all_jobs(self) -> List[Dict]:
        """Get all job records"""
        config = get_config()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM jobs ORDER BY created_at DESC
                """))
            else:
                cursor.execute(text("""
                    SELECT * FROM jobs ORDER BY created_at DESC
                """))
            
            return [dict(row) for row in cursor.fetchall()]

    def get_job_by_id(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        config = get_config()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM jobs WHERE job_id = %s
                """), (job_id,))
            else:
                cursor.execute(text("""
                    SELECT * FROM jobs WHERE job_id = ?
                """), (job_id,))
                
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_pending_jobs(self) -> List[Dict]:
        """Get all pending jobs due for execution"""
        config = get_config()
        current_time = datetime.now()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM jobs 
                    WHERE (status = %s OR status = %s) 
                    AND (next_run IS NULL OR next_run <= %s)
                """), (JobStatus.PENDING.value, JobStatus.RECURRING.value, current_time))
            else:
                cursor.execute(text("""
                    SELECT * FROM jobs 
                    WHERE (status = ? OR status = ?) 
                    AND (next_run IS NULL OR next_run <= ?)
                """), (JobStatus.PENDING.value, JobStatus.RECURRING.value, current_time))
                
            return [dict(row) for row in cursor.fetchall()]

    def insert_job(self, job_data: Dict) -> Optional[str]:
        """Insert a new job"""
        config = get_config()
        current_time = datetime.now()
        
        job_data['created_at'] = current_time
        job_data['updated_at'] = current_time
        
        try:
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        INSERT INTO jobs (
                            job_id, name, description, params, 
                            status, schedule, next_run, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """), (
                        job_data['job_id'],
                        job_data['name'],
                        job_data.get('description'),
                        job_data.get('params'),
                        job_data['status'],
                        job_data.get('schedule'),
                        job_data.get('next_run'),
                        job_data['created_at'],
                        job_data['updated_at']
                    ))
                else:
                    cursor.execute(text("""
                        INSERT INTO jobs (
                            job_id, name, description, params, 
                            status, schedule, next_run, created_at, updated_at
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """), (
                        job_data['job_id'],
                        job_data['name'],
                        job_data.get('description'),
                        job_data.get('params'),
                        job_data['status'],
                        job_data.get('schedule'),
                        job_data.get('next_run'),
                        job_data['created_at'],
                        job_data['updated_at']
                    ))
                    
            return job_data['job_id']
        except Exception as e:
            logger.error(f"Failed to insert job: {str(e)}")
            return None

    def update_job_status(self, job_id: str, status: JobStatus, next_run: Optional[datetime] = None) -> bool:
        """Update job status and optionally next run time"""
        config = get_config()
        current_time = datetime.now()
        
        try:
            with self.conn_manager.transaction() as cursor:
                if next_run:
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            UPDATE jobs 
                            SET status = %s, 
                                last_run = %s, 
                                next_run = %s,
                                updated_at = %s
                            WHERE job_id = %s
                        """), (status.value, current_time, next_run, current_time, job_id))
                    else:
                        cursor.execute(text("""
                            UPDATE jobs 
                            SET status = ?, 
                                last_run = ?, 
                                next_run = ?,
                                updated_at = ?
                            WHERE job_id = ?
                        """), (status.value, current_time, next_run, current_time, job_id))
                else:
                    if config.DB_TYPE == 'postgres':
                        cursor.execute(text("""
                            UPDATE jobs 
                            SET status = %s, 
                                last_run = %s,
                                updated_at = %s
                            WHERE job_id = %s
                        """), (status.value, current_time, current_time, job_id))
                    else:
                        cursor.execute(text("""
                            UPDATE jobs 
                            SET status = ?, 
                                last_run = ?,
                                updated_at = ?
                            WHERE job_id = ?
                        """), (status.value, current_time, current_time, job_id))
                
            return True
        except Exception as e:
            logger.error(f"Failed to update job status: {str(e)}")
            return False

    def record_job_execution(self, job_id: str, start_time: datetime, 
                            end_time: Optional[datetime] = None, 
                            status: JobStatus = JobStatus.RUNNING,
                            result: Optional[str] = None,
                            error: Optional[str] = None) -> Optional[int]:
        """Record job execution details"""
        config = get_config()
        
        try:
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        INSERT INTO job_executions (
                            job_id, start_time, end_time, status, result, error
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                    """), (
                        job_id, start_time, end_time, status.value, result, error
                    ))
                    row = cursor.fetchone()
                    return row[0] if row else None
                else:
                    cursor.execute(text("""
                        INSERT INTO job_executions (
                            job_id, start_time, end_time, status, result, error
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?
                        )
                    """), (
                        job_id, start_time, end_time, status.value, result, error
                    ))
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to record job execution: {str(e)}")
            return None

    def update_job_execution(self, execution_id: int, end_time: datetime,
                           status: JobStatus, result: Optional[str] = None,
                           error: Optional[str] = None) -> bool:
        """Update existing job execution record"""
        config = get_config()
        
        try:
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    cursor.execute(text("""
                        UPDATE job_executions
                        SET end_time = %s,
                            status = %s,
                            result = %s,
                            error = %s
                        WHERE id = %s
                    """), (end_time, status.value, result, error, execution_id))
                else:
                    cursor.execute(text("""
                        UPDATE job_executions
                        SET end_time = ?,
                            status = ?,
                            result = ?,
                            error = ?
                        WHERE id = ?
                    """), (end_time, status.value, result, error, execution_id))
                
            return True
        except Exception as e:
            logger.error(f"Failed to update job execution: {str(e)}")
            return False

    def get_job_executions(self, job_id: str, limit: int = 10) -> List[Dict]:
        """Get recent job executions"""
        config = get_config()
        
        with self.conn_manager.transaction() as cursor:
            if config.DB_TYPE == 'postgres':
                cursor.execute(text("""
                    SELECT * FROM job_executions
                    WHERE job_id = %s
                    ORDER BY start_time DESC
                    LIMIT %s
                """), (job_id, limit))
            else:
                cursor.execute(text("""
                    SELECT * FROM job_executions
                    WHERE job_id = ?
                    ORDER BY start_time DESC
                    LIMIT ?
                """), (job_id, limit))
                
            return [dict(row) for row in cursor.fetchall()]

    def delete_job(self, job_id: str) -> bool:
        """Delete a job and its executions"""
        config = get_config()
        
        try:
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    # In PostgreSQL, cascade should handle this automatically because of the constraint
                    cursor.execute(text("DELETE FROM jobs WHERE job_id = %s"), (job_id,))
                else:
                    # Delete executions first (SQLite might need this explicitly depending on constraints)
                    cursor.execute(text("DELETE FROM job_executions WHERE job_id = ?"), (job_id,))
                    cursor.execute(text("DELETE FROM jobs WHERE job_id = ?"), (job_id,))
                
            return True
        except Exception as e:
            logger.error(f"Failed to delete job: {str(e)}")
            return False 