from config.Config import get_config
from enum import Enum
from typing import Dict

class CredentialType(Enum):
    """Types of credentials supported"""
    API_KEY = "API_KEY"
    USER_PASS = "USER_PASS"
    CHAT_ID = "CHAT_ID"

class ServiceCredentials(Enum):
    """
    Enum mapping services to their credential types and metadata
    """
    
    OPENAI = {
        "service_name": "openai",
        "credential_type": CredentialType.API_KEY,
        "requires_credits": True,
        "metadata": {
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-3.5-turbo", "gpt-4"]
        }
    }
    
    CHAINEDGE = {
        "service_name": "chainedge",
        "credential_type": CredentialType.USER_PASS,
        "requires_credits": False,
        "metadata": {
            "base_url": "https://trading-api-ce111.chainedge.io/api",
            "web_url": "https://trading.chainedge.io"
        }
    }
    
    SOLSCAN = {
        "service_name": "solscan",
        "credential_type": CredentialType.API_KEY,
        "requires_credits": True,
        "metadata": {
            "base_url": "https://api.solscan.io",
            "rate_limit": 100
        }
    }

    CIELO = {
        "service_name": "cielo",
        "credential_type": CredentialType.API_KEY,
        "requires_credits": True,
        "metadata": {
            "base_url": "https://feed-api.cielo.finance/api/v1",
            "credits_per_call": 3,
            "rate_limit": 100
        }
    }

    TELEGRAM = {
        "service_name": "telegram",
        "credential_type": CredentialType.API_KEY,
        "requires_credits": False,
        "metadata": {
            "base_url": "https://api.telegram.org/bot{token}/sendMessage",
            "description": "Telegram Bot API for sending notifications",
            "credential_types": [CredentialType.API_KEY, CredentialType.CHAT_ID]
        }
    }

    def __init__(self, config: Dict):
        self.service_name = config["service_name"]
        self.credential_type = config["credential_type"]
        self.requires_credits = config["requires_credits"]
        self.metadata = config["metadata"]

    @classmethod
    def get_by_name(cls, service_name: str) -> "ServiceCredentials":
        """Get service configuration by service name"""
        for service in cls:
            if service.service_name == service_name:
                return service
        raise ValueError(f"Unknown service: {service_name}")

    @classmethod
    def get_all_services(cls) -> Dict[str, "ServiceCredentials"]:
        """Get mapping of all service names to their configurations"""
        return {service.service_name: service for service in cls}

    def __str__(self) -> str:
        return f"{self.service_name} ({self.credential_type.value})" 