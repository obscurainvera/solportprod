"""
Enum for portfolio status codes
Defines valid status values for portfolio summary entries
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple

@dataclass
class PortfolioStatusInfo:
    """
    Portfolio status information container
    
    Attributes:
        statusname: Human readable status name
        statuscode: Integer status code
    """
    statusname: str
    statuscode: int

class PortfolioStatus(Enum):
    """
    Portfolio status enum with name and code
    
    Each enum value contains:
    - statusname: String description of the status
    - statuscode: Integer code for database storage
    """

    # Define status values
    ACTIVE = ("active", 1)
    INACTIVE = ("inactive", 2)
    MARKED_INACTIVE_DURING_UPDATE = ("marked_inactive_during_update", 3)
    
    def __init__(self, statusname: str, statuscode: int):
        self.statusname = statusname
        self.statuscode = statuscode
    
    def get_info(self) -> PortfolioStatusInfo:
        """Returns status information as a dataclass"""
        return PortfolioStatusInfo(self.statusname, self.statuscode)
    
    @classmethod
    def from_code(cls, code: int) -> 'PortfolioStatus':
        """Get status enum from status code"""
        for status in cls:
            if status.statuscode == code:
                return status
        raise ValueError(f"No status found for code: {code}")

    def __str__(self) -> str:
        """String representation of status"""
        return f"{self.name}({self.statusname}:{self.statuscode})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"PortfolioStatus.{self.name}" 