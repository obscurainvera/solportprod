"""
Enum for analysis status codes
Defines valid status values for portfolio analysis entries
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple

@dataclass
class StatusInfo:
    """
    Status information container
    
    Attributes:
        statusname: Human readable status name
        statuscode: Integer status code
    """
    statusname: str
    statuscode: int

class AnalysisStatus(Enum):
    """
    Analysis status enum with name and code
    
    Each enum value contains:
    - statusname: String description of the status
    - statuscode: Integer code for database storage
    """

    # Define status values
    ACTIVE = ("active", 1)
    
    def __init__(self, statusname: str, statuscode: int):
        self.statusname = statusname
        self.statuscode = statuscode
    
    def get_info(self) -> StatusInfo:
        """Returns status information as a dataclass"""
        return StatusInfo(self.statusname, self.statuscode)
    
    @classmethod
    def from_code(cls, code: int) -> 'AnalysisStatus':
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
        return f"AnalysisStatus.{self.name}" 