from dataclasses import dataclass, field
from typing import List, Set
from datetime import timezone, timedelta, datetime
import os


@dataclass
class CrawlConfig:
    # Basic crawling settings
    base_delay: float = 1.0  # Base delay between requests in seconds
    max_delay: float = 30.0  # Maximum delay when backing off
    delay_multiplier: float = 1.5  # Backoff multiplier
    max_pages: int = 200_000  # Maximum pages to crawl
    timeout_hours: int = 24  # Maximum crawl duration
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0
    
    # Request settings
    request_timeout: int = 30
    user_agent: str = "UniversityCrawler/1.0 (Business Intelligence Tool)"
    
    # Content filtering
    exclude_extensions: Set[str] = field(default_factory=lambda: {
        '.zip', '.tar', '.gz', '.rar', '.exe', '.dmg', '.iso',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'
    })
    
    # URL filtering patterns
    exclude_patterns: List[str] = field(default_factory=lambda: [
        r'/calendar/',
        r'/events/',
        r'\?date=',
        r'\?year=',
        r'\?month=',
        r'/search\?',
        r'/login',
        r'/admin',
        r'/wp-admin',
        r'/wp-content/uploads/',
    ])
    
    # Subdomain handling
    max_subdomains: int = 50
    subdomain_allowlist: Set[str] = field(default_factory=lambda: {
        'www', 'admissions', 'academics', 'research', 'library',
        'student', 'faculty', 'staff', 'alumni', 'news', 'events',
        'athletics', 'grad', 'undergraduate', 'graduate'
    })
    
    # Storage settings
    checkpoint_interval: int = 100  # Save state every N processed items
    database_path: str = "data/crawler.db"
    
    # Export settings
    export_formats: List[str] = field(default_factory=lambda: ['csv', 'json'])
    
    # Timezone settings
    timezone_offset_hours: int = 2  # Default to CEST (UTC+2)
    timezone_name: str = "CEST"
    
    @property
    def timezone(self) -> timezone:
        """Get timezone object from configuration"""
        return timezone(timedelta(hours=self.timezone_offset_hours))
    
    def now(self) -> datetime:
        """Get current time in configured timezone"""
        return datetime.now(self.timezone)
    
    @classmethod
    def from_domain(cls, domain: str) -> 'CrawlConfig':
        """Create domain-specific configuration"""
        config = cls()
        
        # University-specific adjustments
        if 'harvard.edu' in domain or 'stanford.edu' in domain:
            # Large universities - more conservative
            config.base_delay = 2.0
            config.max_pages = 300_000
            config.max_subdomains = 100
        elif any(term in domain for term in ['.cc.', 'community']):
            # Community colleges - faster crawling
            config.base_delay = 0.5
            config.max_pages = 50_000
            config.max_subdomains = 20
        
        return config


@dataclass 
class DatabaseConfig:
    path: str = "data/crawler.db"
    backup_interval: int = 1000  # Backup every N operations
    
    def ensure_directory(self) -> None:
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/crawler.log"
    max_file_size: int = 10_000_000  # 10MB
    backup_count: int = 5
    
    def ensure_directory(self) -> None:
        """Ensure the log directory exists"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)


# Global configuration instance
DEFAULT_CONFIG = CrawlConfig()
DB_CONFIG = DatabaseConfig()
LOG_CONFIG = LoggingConfig()


def get_config(domain: str = None) -> CrawlConfig:
    """Get configuration for a specific domain or default"""
    if domain:
        return CrawlConfig.from_domain(domain)
    return DEFAULT_CONFIG


def get_current_time() -> datetime:
    """Get current time in configured timezone"""
    from utils.time import time_service
    return time_service.now()


def get_timezone() -> timezone:
    """Get configured timezone"""
    return DEFAULT_CONFIG.timezone


# Configure the global time service with our timezone
def _configure_global_time_service():
    """Configure the global time service with our timezone"""
    from utils.time import configure_timezone
    configure_timezone(DEFAULT_CONFIG.timezone)

# Initialize time service
_configure_global_time_service()