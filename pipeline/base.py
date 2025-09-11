from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional, Dict
from enum import Enum
import logging
from datetime import datetime

from models.job import CrawlJob
from models.page import Page
from utils.time import get_current_time


class ErrorAction(Enum):
    RETRY = "retry"
    SKIP = "skip" 
    FAIL = "fail"


class PipelineStage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"pipeline.{name}")
        self.processed_count = 0
        self.failed_count = 0
        self.started_at: Optional[datetime] = None
        
    @abstractmethod
    def process_item(self, item: Any, job: CrawlJob) -> Any:
        """Process a single item through this stage"""
        pass
    
    def handle_error(self, item: Any, error: Exception, job: CrawlJob) -> ErrorAction:
        """Handle an error that occurred during processing"""
        self.logger.error(f"Error processing {item}: {error}")
        
        # Default error handling logic
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorAction.RETRY
        elif isinstance(error, ValueError):
            return ErrorAction.SKIP
        else:
            return ErrorAction.FAIL
    
    def should_process(self, item: Any, job: CrawlJob) -> bool:
        """Determine if this item should be processed by this stage"""
        return True
    
    def before_processing(self, job: CrawlJob) -> None:
        """Called before processing begins"""
        self.started_at = get_current_time()
        self.logger.info(f"Starting {self.name} stage for job {job.job_id}")
    
    def after_processing(self, job: CrawlJob) -> None:
        """Called after processing completes"""
        duration = (get_current_time() - self.started_at).total_seconds()
        self.logger.info(f"Completed {self.name} stage: {self.processed_count} processed, "
                        f"{self.failed_count} failed in {duration:.1f}s")
    
    def process_batch(self, items: Iterator[Any], job: CrawlJob, 
                     checkpoint_callback: callable = None) -> Iterator[Any]:
        """Process a batch of items with error handling and checkpointing"""
        self.before_processing(job)
        
        for item in items:
            try:
                if not self.should_process(item, job):
                    yield item
                    continue
                
                result = self.process_item(item, job)
                self.processed_count += 1
                
                # Checkpoint periodically
                if checkpoint_callback and self.processed_count % 10 == 0:
                    checkpoint_callback(job, self, item)
                
                yield result
                
            except Exception as error:
                action = self.handle_error(item, error, job)
                self.failed_count += 1
                
                if action == ErrorAction.RETRY:
                    # Simple retry logic - could be enhanced
                    try:
                        result = self.process_item(item, job)
                        self.processed_count += 1
                        yield result
                    except Exception as retry_error:
                        self.logger.error(f"Retry failed for {item}: {retry_error}")
                        if isinstance(item, Page):
                            item.mark_failed(str(retry_error))
                        yield item
                        
                elif action == ErrorAction.SKIP:
                    self.logger.warning(f"Skipping {item} due to error: {error}")
                    if isinstance(item, Page):
                        item.mark_failed(str(error))
                    yield item
                    
                elif action == ErrorAction.FAIL:
                    self.logger.critical(f"Fatal error processing {item}: {error}")
                    raise
        
        self.after_processing(job)


class FilterStage(PipelineStage):
    """Base class for stages that filter items"""
    
    @abstractmethod
    def should_include(self, item: Any, job: CrawlJob) -> bool:
        """Determine if this item should pass through the filter"""
        pass
    
    def process_item(self, item: Any, job: CrawlJob) -> Any:
        """Filter implementation - just return the item if it passes"""
        return item
    
    def process_batch(self, items: Iterator[Any], job: CrawlJob, 
                     checkpoint_callback: callable = None) -> Iterator[Any]:
        """Override to implement filtering logic"""
        self.before_processing(job)
        
        for item in items:
            if self.should_include(item, job):
                self.processed_count += 1
                yield item
            else:
                self.failed_count += 1  # Filtered items count as "failed"
        
        self.after_processing(job)


class TransformStage(PipelineStage):
    """Base class for stages that transform items"""
    
    @abstractmethod
    def transform(self, item: Any, job: CrawlJob) -> Any:
        """Transform the input item to output item"""
        pass
    
    def process_item(self, item: Any, job: CrawlJob) -> Any:
        """Transform implementation"""
        return self.transform(item, job)