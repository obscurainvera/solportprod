from config.Config import get_config
from database.auth.ServiceCredentialsEnum import ServiceCredentials
from database.operations.BaseDBHandler import BaseDBHandler
from typing import Dict, Optional, Any
from datetime import datetime
from logs.logger import get_logger
import json
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from sqlalchemy import text

logger = get_logger(__name__)


class CredentialsHandler(BaseDBHandler):
    """
    Handler for managing service credentials including API keys and username/password pairs.
    Supports tracking API credits and other metadata.
    """

    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._createTables()

    def _createTables(self):
        """Creates the credentials tables"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()

            if config.DB_TYPE == "postgres":
                # PostgreSQL syntax
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS servicecredentials (
                        id SERIAL PRIMARY KEY,
                        servicename VARCHAR(100) NOT NULL,
                        credentialtype VARCHAR(20) NOT NULL,
                        isactive INTEGER DEFAULT 1,
                        metadata TEXT,
                        apikey TEXT,   
                        apisecret TEXT,
                        availablecredits INTEGER,
                        username TEXT,
                        password TEXT,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        lastusedat TIMESTAMP,
                        expiresat TIMESTAMP,                    
                        UNIQUE(servicename, apikey),
                        UNIQUE(servicename, username)
                    )
                """
                    )
                )
            else:
                # SQLite syntax
                cursor.execute(
                    text(
                        """
                    CREATE TABLE IF NOT EXISTS servicecredentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        servicename VARCHAR(100) NOT NULL,
                        credentialtype VARCHAR(20) NOT NULL,
                        isactive BOOLEAN DEFAULT 1,
                        metadata TEXT,
                        apikey TEXT,   
                        apisecret TEXT,
                        availablecredits INTEGER,
                        username TEXT,
                        password TEXT,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        lastusedat TIMESTAMP,
                        expiresat TIMESTAMP,                    
                        UNIQUE(servicename, apikey),
                        UNIQUE(servicename, username)
                    )
                """
                    )
                )

    def storeApiCredentials(
        self,
        serviceName: str,
        apiKey: str,
        apiSecret: Optional[str] = None,
        availableCredits: Optional[int] = None,
        metadata: Optional[Dict] = None,
        expiresAt: Optional[datetime] = None,
    ) -> bool:
        """Store or update API key-based credentials"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        INSERT INTO servicecredentials (
                            servicename, credentialtype, apikey, apisecret,
                            availablecredits, metadata, expiresat, updatedat
                        ) VALUES (%s, 'API_KEY', %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT(servicename, apikey) DO UPDATE SET
                            apisecret=EXCLUDED.apisecret,
                            availablecredits=EXCLUDED.availablecredits,
                            metadata=EXCLUDED.metadata,
                            expiresat=EXCLUDED.expiresat,
                            updatedat=CURRENT_TIMESTAMP
                    """
                        ),
                        (
                            serviceName,
                            apiKey,
                            apiSecret,
                            availableCredits,
                            json.dumps(metadata) if metadata else None,
                            expiresAt,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO servicecredentials (
                            servicename, credentialtype, apikey, apisecret,
                            availablecredits, metadata, expiresat, updatedat
                        ) VALUES (?, 'API_KEY', ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(servicename, apikey) DO UPDATE SET
                            apisecret=excluded.apisecret,
                            availablecredits=excluded.availablecredits,
                            metadata=excluded.metadata,
                            expiresat=excluded.expiresat,
                            updatedat=CURRENT_TIMESTAMP
                    """,
                        (
                            serviceName,
                            apiKey,
                            apiSecret,
                            availableCredits,
                            json.dumps(metadata) if metadata else None,
                            expiresAt,
                        ),
                    )
                return True
        except Exception as e:
            logger.error(f"Failed to store API credentials for {serviceName}: {str(e)}")
            return False

    def storeUserCredentials(
        self,
        serviceName: str,
        username: str,
        password: str,
        metadata: Optional[Dict] = None,
        expiresAt: Optional[datetime] = None,
    ) -> bool:
        """Store or update username/password credentials"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        INSERT INTO servicecredentials (
                            servicename, credentialtype, username, password,
                            metadata, expiresat, updatedat
                        ) VALUES (%s, 'USER_PASS', %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT(servicename, username) DO UPDATE SET
                            password=EXCLUDED.password,
                            metadata=EXCLUDED.metadata,
                            expiresat=EXCLUDED.expiresat,
                            updatedat=CURRENT_TIMESTAMP
                    """
                        ),
                        (
                            serviceName,
                            username,
                            password,
                            json.dumps(metadata) if metadata else None,
                            expiresAt,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO servicecredentials (
                            servicename, credentialtype, username, password,
                            metadata, expiresat, updatedat
                        ) VALUES (?, 'USER_PASS', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(servicename, username) DO UPDATE SET
                            password=excluded.password,
                            metadata=excluded.metadata,
                            expiresat=excluded.expiresat,
                            updatedat=CURRENT_TIMESTAMP
                    """,
                        (
                            serviceName,
                            username,
                            password,
                            json.dumps(metadata) if metadata else None,
                            expiresAt,
                        ),
                    )
                return True
        except Exception as e:
            logger.error(
                f"Failed to store user credentials for {serviceName}: {str(e)}"
            )
            return False

    def getCredentials(
        self, serviceName: str, identifier: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get credentials for a service. If identifier (api_key or username) is provided,
        returns specific credentials, otherwise returns the first active credentials.
        """
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if identifier:
                    if config.DB_TYPE == "postgres":
                        cursor.execute(
                            text(
                                """
                            SELECT * FROM servicecredentials
                            WHERE servicename = %s
                            AND (apikey = %s OR username = %s)
                            AND isactive = 1
                        """
                            ),
                            (serviceName, identifier, identifier),
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT * FROM servicecredentials
                            WHERE servicename = ?
                            AND (apikey = ? OR username = ?)
                            AND isactive = 1
                        """,
                            (serviceName, identifier, identifier),
                        )
                else:
                    if config.DB_TYPE == "postgres":
                        cursor.execute(
                            text(
                                """
                            SELECT * FROM servicecredentials
                            WHERE servicename = %s
                            AND isactive = 1
                            ORDER BY updatedat DESC
                            LIMIT 1
                        """
                            ),
                            (serviceName,),
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT * FROM servicecredentials
                            WHERE servicename = ?
                            AND isactive = 1
                            ORDER BY updatedat DESC
                            LIMIT 1
                        """,
                            (serviceName,),
                        )

                result = cursor.fetchone()
                if result:
                    creds = dict(result)
                    if creds["metadata"]:
                        creds["metadata"] = json.loads(creds["metadata"])
                    return creds
                return None
        except Exception as e:
            logger.error(f"Failed to get credentials for {serviceName}: {str(e)}")
            return None

    def updateCredits(self, serviceName: str, apiKey: str, credits: int) -> bool:
        """Update available credits for an API key"""
        try:
            config = get_config()
            current_time = datetime.now()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        UPDATE servicecredentials
                        SET availablecredits = %s,
                            updatedat = %s
                        WHERE servicename = %s AND apikey = %s
                    """
                        ),
                        (credits, current_time, serviceName, apiKey),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE servicecredentials
                        SET availablecredits = ?,
                            updatedat = ?
                        WHERE servicename = ? AND apikey = ?
                    """,
                        (credits, current_time, serviceName, apiKey),
                    )
                return True
        except Exception as e:
            logger.error(f"Failed to update credits for {serviceName}: {str(e)}")
            return False

    def deactivateCredentials(self, serviceName: str, identifier: str) -> bool:
        """Deactivate specific credentials (by api_key or username)"""
        try:
            config = get_config()
            current_time = datetime.now()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        UPDATE servicecredentials
                        SET isactive = 0,
                            updatedat = %s
                        WHERE servicename = %s AND (apikey = %s OR username = %s)
                    """
                        ),
                        (current_time, serviceName, identifier, identifier),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE servicecredentials
                        SET isactive = 0,
                            updatedat = ?
                        WHERE servicename = ? AND (apikey = ? OR username = ?)
                    """,
                        (current_time, serviceName, identifier, identifier),
                    )
                return True
        except Exception as e:
            logger.error(
                f"Failed to deactivate credentials for {serviceName}: {str(e)}"
            )
            return False

    def getCredentialsByType(self, serviceName: str, credentialType: str) -> Optional[Dict[str, Any]]:
        """
        Get credentials for a service by credential type

        Args:
            serviceName: Name of the service
            credentialType: Type of credential to get (e.g., API_KEY, CHAT_ID)

        Returns:
            Optional[Dict[str, Any]]: Credential data or None if not found
        """
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        SELECT * FROM servicecredentials
                        WHERE servicename = %s
                        AND credentialtype = %s
                        AND isactive = 1
                        ORDER BY updatedat DESC
                        LIMIT 1
                    """
                        ),
                        (serviceName, credentialType),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM servicecredentials
                        WHERE servicename = ?
                        AND credentialtype = ?
                        AND isactive = 1
                        ORDER BY updatedat DESC
                        LIMIT 1
                    """,
                        (serviceName, credentialType),
                    )

                result = cursor.fetchone()
                if result:
                    creds = dict(result)
                    if creds["metadata"]:
                        creds["metadata"] = json.loads(creds["metadata"])
                    return creds
                return None
        except Exception as e:
            logger.error(
                f"Failed to get credentials for {serviceName} with type {credentialType}: {str(e)}"
            )
            return None

    def reduceCredits(self, serviceName: str, amount: int = 1) -> bool:
        """
        Reduce available credits for an API key-based service

        Args:
            serviceName: Name of the service
            amount: Amount of credits to reduce (default: 1)

        Returns:
            bool: True if credits were successfully reduced, False otherwise
        """
        try:
            config = get_config()
            current_time = datetime.now()
            with self.conn_manager.transaction() as cursor:
                # First, get current credits
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        SELECT id, availablecredits 
                        FROM servicecredentials
                        WHERE servicename = %s
                        AND credentialtype = 'API_KEY'
                        AND isactive = 1
                        ORDER BY updatedat DESC
                        LIMIT 1
                    """
                        ),
                        (serviceName,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, availablecredits 
                        FROM servicecredentials
                        WHERE servicename = ?
                        AND credentialtype = 'API_KEY'
                        AND isactive = 1
                        ORDER BY updatedat DESC
                        LIMIT 1
                    """,
                        (serviceName,),
                    )

                result = cursor.fetchone()
                if not result:
                    logger.error(f"No active API key found for {serviceName}")
                    return False

                currentCredits = result["availablecredits"]
                if currentCredits is None:
                    logger.warning(f"Credits not tracked for {serviceName}")
                    return True

                if currentCredits < amount:
                    logger.error(
                        f"Insufficient credits for {serviceName}: {currentCredits} < {amount}"
                    )
                    return False

                # Update credits
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        UPDATE servicecredentials
                        SET availablecredits = availablecredits - %s,
                            updatedat = %s,
                            lastusedat = %s
                        WHERE id = %s
                    """
                        ),
                        (amount, current_time, current_time, result["id"]),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE servicecredentials
                        SET availablecredits = availablecredits - ?,
                            updatedat = ?,
                            lastusedat = ?
                        WHERE id = ?
                    """,
                        (amount, current_time, current_time, result["id"]),
                    )

                return True

        except Exception as e:
            logger.error(f"Failed to reduce credits for {serviceName}: {str(e)}")
            return False

    def getNextValidApiKey(
        self, serviceName: str, requiredCredits: int
    ) -> Optional[Dict]:
        """
        Get next API key with sufficient credits

        Args:
            serviceName: Name of the service (e.g., 'cielo')
            requiredCredits: Minimum credits needed

        Returns:
            Optional[Dict]: API key details if found, None otherwise
        """
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        SELECT id, apikey, availablecredits 
                        FROM servicecredentials
                        WHERE servicename = %s
                        AND credentialtype = 'API_KEY'
                        AND isactive = 1
                        AND availablecredits >= %s
                        ORDER BY lastusedat ASC NULLS FIRST
                        LIMIT 1
                    """
                        ),
                        (serviceName, requiredCredits),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, apikey, availablecredits 
                        FROM servicecredentials
                        WHERE servicename = ?
                        AND credentialtype = 'API_KEY'
                        AND isactive = 1
                        AND availablecredits >= ?
                        ORDER BY lastusedat ASC
                        LIMIT 1
                    """,
                        (serviceName, requiredCredits),
                    )

                result = cursor.fetchone()
                return dict(result) if result else None

        except Exception as e:
            logger.error(
                f"Failed to get next valid API key for {serviceName}: {str(e)}"
            )
            return None

    def deductAPIKeyCredits(self, keyId: int, creditsUsed: int) -> bool:
        """
        Update credits for used API key

        Args:
            keyId: ID of the API key
            creditsUsed: Number of credits to deduct

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            config = get_config()
            current_time = datetime.now()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        UPDATE servicecredentials
                        SET availablecredits = availablecredits - %s,
                            lastusedat = %s
                        WHERE id = %s
                    """
                        ),
                        (creditsUsed, current_time, keyId),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE servicecredentials
                        SET availablecredits = availablecredits - ?,
                            lastusedat = ?
                        WHERE id = ?
                    """,
                        (creditsUsed, current_time, keyId),
                    )
                return True
        except Exception as e:
            logger.error(f"Failed to update API key credits for key {keyId}: {str(e)}")
            return False

    def storeCredentialWithType(
        self,
        serviceName: str,
        credentialType: str,
        apiKey: Optional[str] = None,
        apiSecret: Optional[str] = None,
        availableCredits: Optional[int] = None,
        metadata: Optional[Dict] = None,
        expiresAt: Optional[datetime] = None,
    ) -> bool:
        """
        Store credentials with specific credential type

        Args:
            serviceName: Service name from ServiceCredentials enum
            credentialType: Credential type (API_KEY, CHAT_ID, etc.)
            apiKey: API key or other primary credential
            apiSecret: API secret or other secondary credential
            availableCredits: Credits available for this key
            metadata: Additional metadata as dictionary
            expiresAt: Expiration date

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            config = get_config()
            now = datetime.now()

            # Validate service exists
            try:
                ServiceCredentials.get_by_name(serviceName)
            except ValueError:
                logger.error(f"Invalid service name: {serviceName}")
                return False

            # Serialize metadata if provided
            metadata_json = None
            if metadata:
                metadata_json = json.dumps(metadata)

            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    cursor.execute(
                        text(
                            """
                        INSERT INTO servicecredentials (
                            servicename, credentialtype, apikey, 
                            apisecret, availablecredits, metadata, 
                            expiresat, createdat, updatedat, isactive
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
                    """
                        ),
                        (
                            serviceName,
                            credentialType,
                            apiKey,
                            apiSecret,
                            availableCredits,
                            metadata_json,
                            expiresAt,
                            now,
                            now,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO servicecredentials (
                            servicename, credentialtype, apikey, 
                            apisecret, availablecredits, metadata, 
                            expiresat, createdat, updatedat, isactive
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                        (
                            serviceName,
                            credentialType,
                            apiKey,
                            apiSecret,
                            availableCredits,
                            metadata_json,
                            expiresAt,
                            now,
                            now,
                        ),
                    )

                return True

        except Exception as e:
            logger.error(f"Failed to store credentials for {serviceName}: {str(e)}")
            return False

    