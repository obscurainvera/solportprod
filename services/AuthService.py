from config.Config import get_config
import requests
from typing import Dict, Optional
from datetime import datetime
from database.operations.PortfolioDB import PortfolioDB
from database.auth.TokenHandler import TokenHandler
from database.auth.ServiceCredentialsEnum import ServiceCredentials, CredentialType
from logs.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for handling authentication and token management"""

    def __init__(
        self, tokenHandler: TokenHandler, db: PortfolioDB, service: ServiceCredentials
    ):
        """
        Initialize auth service

        Args:
            tokenHandler: Handler for token operations
            db: Database connection
            service: Service credentials configuration
        """
        if not isinstance(service, ServiceCredentials):
            raise ValueError(f"Invalid service configuration: {service}")

        self.tokenHandler = tokenHandler
        self.db = db
        self.service = service

        # Validate service has required metadata
        requiredFields = ["base_url", "web_url"]
        if not all(field in self.service.metadata for field in requiredFields):
            raise ValueError(
                f"Service {service.service_name} missing required metadata: {requiredFields}"
            )

        self.baseUrl = self.service.metadata["base_url"]
        self._credentials = None

    @property
    def credentials(self) -> Optional[Dict]:
        """Get credentials from database, with caching"""
        if not self._credentials:
            self._credentials = self.db.credentials.getCredentialsByType(
                self.service.service_name, self.service.credential_type.value
            )

        if not self._credentials:
            logger.error(
                f"No {self.service.service_name} credentials found in database"
            )
            return None

        # Validate required credential fields
        requiredFields = ["username", "password"]

        if not all(field in self._credentials for field in requiredFields):
            logger.error(f"Invalid credentials format for {self.service.service_name}")
            self._credentials = None
            return None

        return self._credentials

    def login(self) -> Optional[Dict]:
        """Perform initial login and get tokens"""
        try:
            # Get and validate credentials
            creds = self.credentials
            if not creds:
                return None

            headers = {
                "accept": "*/*",
                "accept-language": "en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7",
                "content-type": "application/json",
                "origin": self.service.metadata["web_url"],
                "priority": "u=1, i",
                "referer": f"{self.service.metadata['web_url']}/",
                "sec-ch-ua": '"Microsoft Edge";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
            }

            response = requests.post(
                f"{self.baseUrl}/login/",
                json={"username": creds["username"], "password": creds["password"]},
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            if not all(key in data for key in ["access", "refresh"]):
                logger.error(
                    f"Invalid response format from {self.service.service_name} login"
                )
                return None

            # Store tokens with isNewLogin=True to set new refresh token expiry
            self.tokenHandler.storeTokens(
                self.service.service_name,
                data["access"],
                data["refresh"],
                isNewLogin=True,
            )
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed for {self.service.service_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Login failed for {self.service.service_name}: {e}")
            return None

    def refreshToken(self, refreshToken: str) -> Optional[Dict]:
        """Refresh access token using refresh token"""
        try:
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7",
                "content-type": "application/json",
                "origin": self.service.metadata["web_url"],
                "priority": "u=1, i",
                "referer": f"{self.service.metadata['web_url']}/",
                "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
            }

            response = requests.post(
                f"{self.baseUrl}/token/refresh/",
                json={"refresh": refreshToken},
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()
            if "access" not in data:
                logger.error(
                    f"Invalid response format from {self.service.service_name} token refresh"
                )
                return None

            # Store tokens with isNewLogin=False to keep existing refresh token expiry
            self.tokenHandler.storeTokens(
                self.service.service_name,
                data["access"],
                refreshToken,
                isNewLogin=False,
            )
            return data

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Token refresh request failed for {self.service.service_name}: {e}"
            )
            return None
        except Exception as e:
            logger.error(f"Token refresh failed for {self.service.service_name}: {e}")
            return None

    def getValidAccessToken(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        tokens = self.tokenHandler.getValidTokens(self.service.service_name)

        if not tokens:
            # No tokens stored, need to login
            loginResult = self.login()
            return loginResult["access"] if loginResult else None

        if self.tokenHandler.needsRelogin(self.service.service_name):  # reduce db calls
            # Refresh token expired, need new login
            loginResult = self.login()
            return loginResult["access"] if loginResult else None

        if self.tokenHandler.needsRefresh(self.service.service_name):  # reduce db calls
            # Access token expired, refresh it
            refreshResult = self.refreshToken(tokens["refreshtoken"])
            return refreshResult["access"] if refreshResult else None

        return tokens["accesstoken"]
