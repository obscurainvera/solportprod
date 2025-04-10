from config.Config import get_config
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
"""
Handler for notification database operations
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import sqlite3
import pytz
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.schema import Notification, NotificationButton
from framework.notificationframework.NotificationEnums import NotificationStatus
from logs.logger import get_logger
from sqlalchemy import text


logger = get_logger(__name__)

class NotificationHandler(BaseDBHandler):
    """
    Handler for notification database operations
    """
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        """Initialize with connection manager"""
        super().__init__(conn_manager)
        self.tableName = 'notification'
        self._ensureTableExists()
    
    def _ensureTableExists(self) -> None:
        """Ensure the notification table exists"""
        config = get_config()
        
        try:
            with self.conn_manager.transaction() as cursor:
                table_name = self.tableName
                default_status = NotificationStatus.PENDING.value
                
                if config.DB_TYPE == 'postgres':
                    # PostgreSQL syntax - use %s instead of named parameters
                    cursor.execute(text("""
                        CREATE TABLE IF NOT EXISTS notification (
                            id SERIAL PRIMARY KEY,
                            source TEXT NOT NULL,
                            chatgroup TEXT NOT NULL,
                            content TEXT NOT NULL,
                            status TEXT NOT NULL DEFAULT %s,
                            servicetype TEXT,
                            errordetails TEXT,
                            buttons TEXT,
                            createdat TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP,
                            sentat TIMESTAMP
                        )
                    """), (default_status,))
                    
                    # Create index for faster queries
                    cursor.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_notification_status
                        ON notification (status)
                    """))
                else:
                    # SQLite syntax
                    cursor.execute(text("""
                        CREATE TABLE IF NOT EXISTS notification (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source TEXT NOT NULL,
                            chatgroup TEXT NOT NULL,
                            content TEXT NOT NULL,
                            status TEXT NOT NULL DEFAULT ?,
                            servicetype TEXT,
                            errordetails TEXT,
                            buttons TEXT,
                            createdat TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updatedat TIMESTAMP,
                            sentat TIMESTAMP
                        )
                    """), (default_status,))
                    
                    # Create index for faster queries
                    cursor.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_notification_status
                        ON notification (status)
                    """))
        except Exception as e:
            logger.error(f"Error ensuring notification table exists: {e}")
            # Don't re-raise, as we want to allow graceful fallback
    
    def createNotification(self, notification: Notification) -> Optional[Notification]:
        """
        Create a new notification record
        
        Args:
            notification: Notification object to save
            
        Returns:
            Optional[Notification]: Saved notification with ID or None if failed
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                now = self.getCurrentIstTime()
                
                # Set timestamps
                notification.createdat = now
                notification.updatedat = now
                
                # Serialize buttons to JSON if present
                buttons_json = json.dumps([{"text": btn.text, "url": btn.url} for btn in notification.buttons]) if notification.buttons else None
                
                # Insert into database
                if config.DB_TYPE == 'postgres':
                    insert_sql = f'''
                        INSERT INTO {self.tableName} 
                        (source, chatgroup, content, status, servicetype, errordetails, buttons, createdat, updatedat, sentat)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    '''
                    result = cursor.execute(text(insert_sql), (
                        notification.source,
                        notification.chatgroup,
                        notification.content,
                        notification.status,
                        notification.servicetype,
                        notification.errordetails,
                        buttons_json,
                        notification.createdat,
                        notification.updatedat,
                        notification.sentat
                    ))
                    row = result.fetchone()
                    notification.id = row['id'] if row else None
                else:
                    insert_sql = f'''
                        INSERT INTO {self.tableName} 
                        (source, chatgroup, content, status, servicetype, errordetails, buttons, createdat, updatedat, sentat)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    cursor.execute(text(insert_sql), (
                        notification.source,
                        notification.chatgroup,
                        notification.content,
                        notification.status,
                        notification.servicetype,
                        notification.errordetails,
                        buttons_json,
                        notification.createdat,
                        notification.updatedat,
                        notification.sentat
                    ))
                    
                    # Get the ID of the inserted row
                    notification.id = cursor.lastrowid
                
                return notification
                
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    def updateNotification(self, notification: Notification) -> bool:
        """
        Update an existing notification record
        
        Args:
            notification: Notification object to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            config = get_config()
            
            if not notification.id:
                logger.error("Cannot update notification without an ID")
                return False
            
            with self.conn_manager.transaction() as cursor:
                # Update timestamp
                notification.updatedat = self.getCurrentIstTime()
                
                # Serialize buttons to JSON if present
                buttons_json = json.dumps([{"text": btn.text, "url": btn.url} for btn in notification.buttons]) if notification.buttons else None
                
                # Update record
                if config.DB_TYPE == 'postgres':
                    update_sql = f'''
                        UPDATE {self.tableName}
                        SET source = %s,
                            chatgroup = %s,
                            content = %s,
                            status = %s,
                            servicetype = %s,
                            errordetails = %s,
                            buttons = %s,
                            updatedat = %s,
                            sentat = %s
                        WHERE id = %s
                    '''
                    cursor.execute(text(update_sql), (
                        notification.source,
                        notification.chatgroup,
                        notification.content,
                        notification.status,
                        notification.servicetype,
                        notification.errordetails,
                        buttons_json,
                        notification.updatedat,
                        notification.sentat,
                        notification.id
                    ))
                else:
                    update_sql = f'''
                        UPDATE {self.tableName}
                        SET source = ?,
                            chatgroup = ?,
                            content = ?,
                            status = ?,
                            servicetype = ?,
                            errordetails = ?,
                            buttons = ?,
                            updatedat = ?,
                            sentat = ?
                        WHERE id = ?
                    '''
                    cursor.execute(text(update_sql), (
                        notification.source,
                        notification.chatgroup,
                        notification.content,
                        notification.status,
                        notification.servicetype,
                        notification.errordetails,
                        buttons_json,
                        notification.updatedat,
                        notification.sentat,
                        notification.id
                    ))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update notification: {e}")
            return False
    
    def getNotificationById(self, notificationId: int) -> Optional[Notification]:
        """
        Get a notification by ID
        
        Args:
            notificationId: ID of the notification to retrieve
            
        Returns:
            Optional[Notification]: Notification object if found, None otherwise
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE id = %s
                    '''
                    cursor.execute(text(select_sql), (notificationId,))
                else:
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE id = ?
                    '''
                    cursor.execute(text(select_sql), (notificationId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._rowToNotification(row)
                
        except Exception as e:
            logger.error(f"Failed to get notification by ID: {e}")
            return None
    
    def getPendingNotifications(self, limit: int = 10) -> List[Notification]:
        """
        Get pending notifications to be sent
        
        Args:
            limit: Maximum number of notifications to retrieve
            
        Returns:
            List[Notification]: List of pending notifications
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE status = %s
                        ORDER BY createdat ASC
                        LIMIT %s
                    '''
                    cursor.execute(text(select_sql), (NotificationStatus.PENDING.value, limit))
                else:
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE status = ?
                        ORDER BY createdat ASC
                        LIMIT ?
                    '''
                    cursor.execute(text(select_sql), (NotificationStatus.PENDING.value, limit))
                
                rows = cursor.fetchall()
                return [self._rowToNotification(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {e}")
            return []
    
    def getFailedNotifications(self, limit: int = 10) -> List[Notification]:
        """
        Get failed notifications
        
        Args:
            limit: Maximum number of notifications to retrieve
            
        Returns:
            List[Notification]: List of failed notifications
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE status = %s
                        ORDER BY updatedat DESC
                        LIMIT %s
                    '''
                    cursor.execute(text(select_sql), (NotificationStatus.FAILED.value, limit))
                else:
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE status = ?
                        ORDER BY updatedat DESC
                        LIMIT ?
                    '''
                    cursor.execute(text(select_sql), (NotificationStatus.FAILED.value, limit))
                
                rows = cursor.fetchall()
                return [self._rowToNotification(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get failed notifications: {e}")
            return []
    
    def getNotificationsBySource(self, source: str, limit: int = 10) -> List[Notification]:
        """
        Get notifications by source
        
        Args:
            source: Source of the notifications
            limit: Maximum number of notifications to retrieve
            
        Returns:
            List[Notification]: List of notifications from the specified source
        """
        try:
            config = get_config()
            
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == 'postgres':
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE source = %s
                        ORDER BY createdat DESC
                        LIMIT %s
                    '''
                    cursor.execute(text(select_sql), (source, limit))
                else:
                    select_sql = f'''
                        SELECT id, source, chatgroup, content, status, servicetype, 
                               errordetails, buttons, createdat, updatedat, sentat
                        FROM {self.tableName}
                        WHERE source = ?
                        ORDER BY createdat DESC
                        LIMIT ?
                    '''
                    cursor.execute(text(select_sql), (source, limit))
                
                rows = cursor.fetchall()
                return [self._rowToNotification(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get notifications by source: {e}")
            return []
    
    def _rowToNotification(self, row: Tuple) -> Notification:
        """
        Convert a database row to a Notification object
        
        Args:
            row: Database row tuple
            
        Returns:
            Notification: Notification object
        """
        # Parse buttons JSON
        buttons = []
        if row[7]:  # buttons field
            try:
                buttons_data = json.loads(row[7])
                buttons = [NotificationButton(text=btn["text"], url=btn["url"]) for btn in buttons_data]
            except Exception as e:
                logger.error(f"Failed to parse buttons JSON: {e}")
        
        return Notification(
            id=row[0],
            source=row[1],
            chatgroup=row[2],
            content=row[3],
            status=row[4],
            servicetype=row[5],
            errordetails=row[6],
            buttons=buttons,
            createdat=row[8] if row[8] else None,
            updatedat=row[9] if row[9] else None,
            sentat=row[10] if row[10] else None
        ) 