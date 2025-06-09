import os
from typing import Dict, Any
import urllib.parse

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    """
    Base configuration class that handles environment variables and provides default values.
    """

    # Flask settings
    DEBUG = False
    TESTING = False

    # Database settings
    DB_TYPE = os.getenv("DB_TYPE", "postgres")  # Default to PostgreSQL

    # Remove http:// or https:// prefix from DB_HOST if present
    _DB_HOST = os.getenv("DB_HOST", "localhost")
    if _DB_HOST.startswith(("http://", "https://")):
        DB_HOST = _DB_HOST.split("://", 1)[1]
    else:
        DB_HOST = _DB_HOST

    # Handle empty DB_PORT by ensuring it has a default
    _DB_PORT = os.getenv("DB_PORT", "5432")
    try:
        DB_PORT = int(_DB_PORT) if _DB_PORT and _DB_PORT.strip() else 5432
    except (ValueError, AttributeError):
        # If conversion fails, use default
        DB_PORT = 5432

    DB_NAME = os.getenv("DB_NAME", "portfolio")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_PATH = os.getenv("DB_PATH", os.path.join(PROJECT_ROOT, "portfolio.db"))
    DB_SSLMODE = os.getenv(
        "DB_SSLMODE", "require"
    )  # SSL mode for PostgreSQL cloud connections
    DB_GSSENCMODE = os.getenv(
        "DB_GSSENCMODE", "disable"
    )  # GSSAPI encryption mode for PostgreSQL

    # Handle empty values for connection pooling parameters
    _DB_POOL_SIZE = os.getenv("DB_POOL_SIZE", "5")
    try:
        DB_POOL_SIZE = (
            int(_DB_POOL_SIZE) if _DB_POOL_SIZE and _DB_POOL_SIZE.strip() else 5
        )
    except ValueError:
        DB_POOL_SIZE = 5

    _DB_MAX_OVERFLOW = os.getenv("DB_MAX_OVERFLOW", "10")
    try:
        DB_MAX_OVERFLOW = (
            int(_DB_MAX_OVERFLOW)
            if _DB_MAX_OVERFLOW and _DB_MAX_OVERFLOW.strip()
            else 10
        )
    except ValueError:
        DB_MAX_OVERFLOW = 10

    _DB_POOL_TIMEOUT = os.getenv("DB_POOL_TIMEOUT", "30")
    try:
        DB_POOL_TIMEOUT = (
            int(_DB_POOL_TIMEOUT)
            if _DB_POOL_TIMEOUT and _DB_POOL_TIMEOUT.strip()
            else 30
        )
    except ValueError:
        DB_POOL_TIMEOUT = 30

    _DB_POOL_RECYCLE = os.getenv("DB_POOL_RECYCLE", "1800")
    try:
        DB_POOL_RECYCLE = (
            int(_DB_POOL_RECYCLE)
            if _DB_POOL_RECYCLE and _DB_POOL_RECYCLE.strip()
            else 1800
        )
    except ValueError:
        DB_POOL_RECYCLE = 1800

    _DB_CONNECT_TIMEOUT = os.getenv("DB_CONNECT_TIMEOUT", "10")
    try:
        DB_CONNECT_TIMEOUT = (
            int(_DB_CONNECT_TIMEOUT)
            if _DB_CONNECT_TIMEOUT and _DB_CONNECT_TIMEOUT.strip()
            else 10
        )
    except ValueError:
        DB_CONNECT_TIMEOUT = 10

    # API settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    _API_PORT = os.getenv("API_PORT", "8080")
    try:
        API_PORT = int(_API_PORT) if _API_PORT and _API_PORT.strip() else 8080
    except ValueError:
        API_PORT = 8080
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")

    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", os.path.join(PROJECT_ROOT, "logs", "app.log"))

    # Job scheduler settings
    JOBS_DB_PATH = os.getenv("JOBS_DB_PATH", os.path.join(PROJECT_ROOT, "jobs.db"))

    JOB_SCHEDULES = {
        "volume_bot_analysis": {"minute": "*/1"},
        "pump_fun_analysis": {"minute": "*/1"}
    }

    VOLUME_COOKIE = os.getenv("VOLUME_COOKIE", "default_volume_cookie")
    PUMPFUN_COOKIE = os.getenv("PUMPFUN_COOKIE", "default_pump_fun_cookie")

    VOLUME_EXPIRY = os.getenv("VOLUME_EXPIRY", "2025-12-31")
    PUMPFUN_EXPIRY = os.getenv("PUMPFUN_EXPIRY", "2023-12-31")

    def get_database_url(self) -> str:
        """
        Get the database URL based on configuration.

        Returns:
            str: Database URL
        """
        if self.DB_TYPE == "sqlite":
            return f"sqlite:///{self.DB_PATH}"
        else:
            # URL encode the password to handle special characters
            password = urllib.parse.quote_plus(self.DB_PASSWORD)

            # Build PostgreSQL connection string with additional parameters for cloud compatibility
            conn_string = f"postgresql://{self.DB_USER}:{password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

            # Add SSL mode and other connection parameters for cloud deployments
            if self.DB_SSLMODE:
                conn_string += f"?sslmode={self.DB_SSLMODE}"

                # Add GSSAPI encryption mode if specified
                if self.DB_GSSENCMODE:
                    conn_string += f"&gssencmode={self.DB_GSSENCMODE}"

            return conn_string

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            "DEBUG": self.DEBUG,
            "TESTING": self.TESTING,
            "DB_TYPE": self.DB_TYPE,
            "DB_HOST": self.DB_HOST,
            "DB_PORT": self.DB_PORT,
            "DB_NAME": self.DB_NAME,
            "DB_USER": self.DB_USER,
            "DB_PATH": self.DB_PATH,
            "DB_SSLMODE": self.DB_SSLMODE,
            "DB_GSSENCMODE": self.DB_GSSENCMODE,
            "DB_POOL_SIZE": self.DB_POOL_SIZE,
            "DB_MAX_OVERFLOW": self.DB_MAX_OVERFLOW,
            "DB_POOL_TIMEOUT": self.DB_POOL_TIMEOUT,
            "DB_POOL_RECYCLE": self.DB_POOL_RECYCLE,
            "API_HOST": self.API_HOST,
            "API_PORT": self.API_PORT,
            "API_BASE_URL": self.API_BASE_URL,
            "CORS_ORIGINS": self.CORS_ORIGINS,
            "LOG_LEVEL": self.LOG_LEVEL,
            "LOG_FILE": self.LOG_FILE,
            "JOBS_DB_PATH": self.JOBS_DB_PATH,
        }


class DevelopmentConfig(Config):
    """
    Development configuration.
    """

    DEBUG = True
    LOG_LEVEL = "DEBUG"
    DB_SSLMODE = "disable"  # Typically no SSL in development


class ProductionConfig(Config):
    """
    Production configuration.
    """

    DB_TYPE = "postgres"  # Always use PostgreSQL in production
    DB_SSLMODE = "disable"  # Disable SSL as requested
    API_BASE_URL = os.getenv(
        "API_BASE_URL", "https://api.solport.com"
    )  # Production API URL
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://solport.com").split(",")
    LOG_LEVEL = "INFO"


def get_config() -> Config:
    """
    Get the appropriate configuration based on environment.

    Returns:
        Config: Configuration instance
    """
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
