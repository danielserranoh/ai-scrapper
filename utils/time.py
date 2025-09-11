"""
Centralized time utilities following DRY principles
"""
from datetime import datetime, timezone
from typing import Optional


class TimeService:
    """Centralized time service to avoid repeated datetime logic"""
    
    def __init__(self, tz: Optional[timezone] = None):
        self._timezone = tz or timezone.utc
    
    def now(self) -> datetime:
        """Get current time in configured timezone"""
        return datetime.now(self._timezone)
    
    def utc_now(self) -> datetime:
        """Get current time in UTC"""
        return datetime.now(timezone.utc)
    
    @property
    def timezone(self) -> timezone:
        """Get configured timezone"""
        return self._timezone


# Global time service instance - can be configured once
time_service = TimeService()

def get_current_time() -> datetime:
    """Global function to get current time - maintains backward compatibility"""
    return time_service.now()

def configure_timezone(tz: timezone) -> None:
    """Configure the global timezone"""
    global time_service
    time_service = TimeService(tz)