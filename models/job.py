from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
import uuid


# Remove duplicate - use centralized time service
from utils.time import get_current_time as _get_current_time


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStage(Enum):
    DISCOVERY = "discovery"
    FETCH = "fetch"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    STORE = "store"
    EXPORT = "export"


@dataclass
class CrawlJob:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: str = ""
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: _get_current_time())
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    total_pages: int = 0
    processed_pages: int = 0
    failed_pages: int = 0
    subdomains_found: int = 0
    
    def start(self) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = _get_current_time()
    
    def complete(self) -> None:
        self.status = JobStatus.COMPLETED
        self.completed_at = _get_current_time()
    
    def fail(self) -> None:
        self.status = JobStatus.FAILED
        self.completed_at = _get_current_time()
    
    def pause(self) -> None:
        self.status = JobStatus.PAUSED


@dataclass
class PipelineState:
    job_id: str
    current_stage: PipelineStage
    stage_progress: Dict[str, Any] = field(default_factory=dict)
    last_checkpoint: datetime = field(default_factory=lambda: _get_current_time())
    pending_urls: int = 0
    processing_urls: int = 0
    completed_urls: int = 0
    failed_urls: int = 0
    
    def update_progress(self, pending: int = None, processing: int = None, 
                       completed: int = None, failed: int = None) -> None:
        if pending is not None:
            self.pending_urls = pending
        if processing is not None:
            self.processing_urls = processing
        if completed is not None:
            self.completed_urls = completed
        if failed is not None:
            self.failed_urls = failed
        self.last_checkpoint = _get_current_time()
    
    def advance_stage(self, stage: PipelineStage) -> None:
        self.current_stage = stage
        self.last_checkpoint = _get_current_time()