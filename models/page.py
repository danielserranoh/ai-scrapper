from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Set
from urllib.parse import urlparse


# Remove duplicate - use centralized time service
from utils.time import get_current_time as _get_current_time


class PageStatus(Enum):
    DISCOVERED = "discovered"
    FETCHING = "fetching"
    FETCHED = "fetched"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    FAILED = "failed"


class ContentType(Enum):
    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    CSS = "css"
    JS = "javascript"
    OTHER = "other"


@dataclass
class Page:
    url: str
    job_id: str
    status: PageStatus = PageStatus.DISCOVERED
    discovered_at: datetime = field(default_factory=lambda: _get_current_time())
    fetched_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # HTTP response data
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    html_content: Optional[str] = None
    
    # Extracted data
    title: Optional[str] = None
    clean_content: Optional[str] = None
    markdown_content: Optional[str] = None

    # Browser/Crawl4AI-specific content (Phase 3A/3B)
    extraction_method: Optional[str] = None  # "requests" | "browser"
    browser_fetched: bool = False
    cleaned_html: Optional[str] = None  # Crawl4AI's cleaned HTML
    crawl4ai_markdown: Optional[str] = None  # Crawl4AI's pre-generated markdown
    markdown_quality_score: Optional[float] = None  # 0-1 quality indicator

    # Links and relationships
    internal_links: Set[str] = field(default_factory=set)
    external_links: Set[str] = field(default_factory=set)
    
    # Contacts found
    emails: Set[str] = field(default_factory=set)
    social_media: Dict[str, Set[str]] = field(default_factory=dict)
    
    # Analysis results
    analysis_results: Optional[Dict] = None
    analyzed_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    @property
    def domain(self) -> str:
        return urlparse(self.url).netloc
    
    @property
    def subdomain(self) -> str:
        domain_parts = self.domain.split('.')
        if len(domain_parts) > 2:
            return domain_parts[0]
        return ""
    
    @property
    def path(self) -> str:
        return urlparse(self.url).path
    
    @property
    def detected_content_type(self) -> ContentType:
        if self.content_type:
            if 'text/html' in self.content_type:
                return ContentType.HTML
            elif 'application/pdf' in self.content_type:
                return ContentType.PDF
            elif 'image/' in self.content_type:
                return ContentType.IMAGE
            elif 'text/css' in self.content_type:
                return ContentType.CSS
            elif 'javascript' in self.content_type:
                return ContentType.JS
        
        # Fallback to URL extension
        if self.url.lower().endswith('.pdf'):
            return ContentType.PDF
        elif self.url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            return ContentType.IMAGE
        elif self.url.lower().endswith('.css'):
            return ContentType.CSS
        elif self.url.lower().endswith('.js'):
            return ContentType.JS
            
        return ContentType.OTHER
    
    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries
    
    def mark_failed(self, error: str) -> None:
        self.status = PageStatus.FAILED
        self.error_message = error
        self.processed_at = _get_current_time()
    
    def add_error(self, error: str) -> None:
        """Add error without changing status (for non-fatal errors)"""
        if self.error_message:
            self.error_message += f"; {error}"
        else:
            self.error_message = error


@dataclass
class Link:
    source_url: str
    target_url: str
    job_id: str
    anchor_text: Optional[str] = None
    is_internal: bool = True
    discovered_at: datetime = field(default_factory=lambda: _get_current_time())


@dataclass 
class Contact:
    job_id: str
    source_url: str
    contact_type: str  # "email", "twitter", "linkedin", etc.
    value: str
    context: Optional[str] = None  # surrounding text for context
    discovered_at: datetime = field(default_factory=lambda: _get_current_time())