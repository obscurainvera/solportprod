from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from datetime import datetime, timedelta
from typing import Optional, Dict
from logs.logger import get_logger
from config.Security import (
    ACCESS_TOKEN_EXPIRY_MINUTES,  # 15 minutes for access token
    REFRESH_TOKEN_EXPIRY_HOURS,  # 12 hours for refresh token
    TOKEN_REFRESH_BUFFER_MINUTES,  # 1 minute buffer before access token refresh
    RELOGIN_BUFFER_MINUTES,  # 5 minutes buffer before refresh token expires
)
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from sqlalchemy import text


logger = get_logger(__name__)


class TokenHandler(BaseDBHandler):
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._createTables()

    def _createTables(self):
        """Creates the auth tokens table"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()

            if config.DB_TYPE == "postgres":
                # PostgreSQL syntax
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS authtokens (
                        id SERIAL PRIMARY KEY,
                        servicename VARCHAR(50) NOT NULL UNIQUE,
                        accesstoken TEXT NOT NULL,
                        refreshtoken TEXT NOT NULL,
                        accesstokenexpiresat TIMESTAMP NOT NULL,
                        refreshtokenexpiresat TIMESTAMP NOT NULL,
                        logintime TIMESTAMP NOT NULL,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )
            else:
                # SQLite syntax
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS authtokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        servicename VARCHAR(50) NOT NULL UNIQUE,
                        accesstoken TEXT NOT NULL,
                        refreshtoken TEXT NOT NULL,
                        accesstokenexpiresat TIMESTAMP NOT NULL,
                        refreshtokenexpiresat TIMESTAMP NOT NULL,
                        logintime TIMESTAMP NOT NULL,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                    )
                )

    def storeTokens(self,serviceName: str,accessToken: str,refreshToken: str,isNewLogin: bool = False,) -> None:
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                now = datetime.now()

                if isNewLogin:
                    loginTime = now
                    refreshExpires = now + timedelta(hours=REFRESH_TOKEN_EXPIRY_HOURS)
                else:
                    if config.DB_TYPE == "postgres":
                        cursor.execute(
                            text(
                                """
                                SELECT logintime, refreshtokenexpiresat
                                FROM authtokens
                                WHERE servicename = %s
                            """
                            ),
                            (serviceName,),
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT logintime, refreshtokenexpiresat
                            FROM authtokens
                            WHERE servicename = ?
                        """,
                            (serviceName,),
                        )

                    result = cursor.fetchone()
                    if result:
                        loginTime = result["logintime"]
                        if isinstance(loginTime, str):
                            loginTime = datetime.fromisoformat(
                                loginTime.replace("Z", "+00:00")
                            )
                        elif not isinstance(loginTime, datetime):
                            raise ValueError(
                                f"Unexpected type for logintime: {type(loginTime)}"
                            )

                        refreshExpires = result["refreshtokenexpiresat"]
                        if isinstance(refreshExpires, str):
                            refreshExpires = datetime.fromisoformat(
                                refreshExpires.replace("Z", "+00:00")
                            )
                        elif not isinstance(refreshExpires, datetime):
                            raise ValueError(
                                f"Unexpected type for refreshtokenexpiresat: {type(refreshExpires)}"
                            )
                    else:
                        loginTime = now
                        refreshExpires = now + timedelta(hours=12)

                accessExpires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)

                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                            INSERT INTO authtokens (
                                servicename, accesstoken, refreshtoken,
                                accesstokenexpiresat, refreshtokenexpiresat,
                                logintime, updatedat
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT(servicename) DO UPDATE SET
                                accesstoken=EXCLUDED.accesstoken,
                                refreshtoken=EXCLUDED.refreshtoken,
                                accesstokenexpiresat=EXCLUDED.accesstokenexpiresat,
                                refreshtokenexpiresat=EXCLUDED.refreshtokenexpiresat,
                                logintime=EXCLUDED.logintime,
                                updatedat=EXCLUDED.updatedat
                        """
                        ),
                        (
                            serviceName,
                            accessToken,
                            refreshToken,
                            accessExpires,
                            refreshExpires,
                            loginTime,
                            now,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO authtokens (
                            servicename, accesstoken, refreshtoken,
                            accesstokenexpiresat, refreshtokenexpiresat,
                            logintime, updatedat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(servicename) DO UPDATE SET
                            accesstoken=excluded.accesstoken,
                            refreshtoken=excluded.refreshtoken,
                            accesstokenexpiresat=excluded.accesstokenexpiresat,
                            refreshtokenexpiresat=excluded.refreshtokenexpiresat,
                            logintime=excluded.logintime,
                            updatedat=excluded.updatedat
                    """,
                        (
                            serviceName,
                            accessToken,
                            refreshToken,
                            accessExpires,
                            refreshExpires,
                            loginTime,
                            now,
                        ),
                    )
        except Exception as e:
            logger.error(f"Failed to store tokens: {str(e)}")
            raise

    def getValidTokens(self, serviceName: str) -> Optional[Dict]:
        """Get valid tokens for a service"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        SELECT 
                            accesstoken,
                            refreshtoken,
                            accesstokenexpiresat,
                            refreshtokenexpiresat,
                            logintime
                        FROM authtokens
                        WHERE servicename = %s
                    """
                        ),
                        (serviceName,),
                    )

                result = cursor.fetchone()
                if not result:
                    return None

                # Safely convert datetime strings to datetime objects
                def safe_parse_datetime(dt_value) -> Optional[datetime]:
                    if dt_value is None:
                        return None
                    if isinstance(dt_value, datetime):
                        return dt_value
                    if isinstance(dt_value, str):
                        return datetime.fromisoformat(dt_value.replace("Z", "+00:00"))
                    logger.warning(f"Unexpected datetime value type: {type(dt_value)}")
                    return None

                return {
                    "accesstoken": result["accesstoken"],
                    "refreshtoken": result["refreshtoken"],
                    "accesstokenexpiresat": safe_parse_datetime(result["accesstokenexpiresat"]),
                    "refreshtokenexpiresat": safe_parse_datetime(result["refreshtokenexpiresat"]),
                    "logintime": safe_parse_datetime(result["logintime"]),
                }

        except Exception as e:
            logger.error(f"Failed to get tokens: {str(e)}")
            return None

    def needsRefresh(self, serviceName: str) -> bool:
        """Check if access token needs refresh (within 1 minute of expiry)"""
        tokens = self.getValidTokens(serviceName)
        if not tokens:
            return True

        # Use TOKEN_REFRESH_BUFFER_MINUTES (1 minute) as buffer before refresh
        bufferTime = timedelta(minutes=TOKEN_REFRESH_BUFFER_MINUTES)
        return datetime.now() + bufferTime >= tokens["accesstokenexpiresat"]

    def needsRelogin(self, serviceName: str) -> bool:
        """Check if refresh token is expired or about to expire"""
        tokens = self.getValidTokens(serviceName)
        if not tokens:
            return True

        # Use RELOGIN_BUFFER_MINUTES (5 minutes) as buffer before relogin
        bufferTime = timedelta(minutes=RELOGIN_BUFFER_MINUTES)
        return datetime.now() + bufferTime >= tokens["refreshtokenexpiresat"]
