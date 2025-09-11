import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import time

from models.job import CrawlJob, PipelineState, PipelineStage as PipelineStageEnum, JobStatus
from models.page import Page, PageStatus
from pipeline.base import PipelineStage
from pipeline.discovery import URLDiscoveryStage, LinkDiscoveryStage
from pipeline.fetcher import HTTPFetcherStage
from pipeline.extractor import ContentExtractionStage
from storage.checkpoints import CheckpointManager, URLQueue
from storage.data_store import DataStore
from config import CrawlConfig
from utils.time import get_current_time


class PipelineManager:
    """Orchestrates the entire crawling pipeline"""
    
    def __init__(self, config: CrawlConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Storage components
        self.checkpoint_manager = CheckpointManager()
        self.data_store = DataStore()
        
        # Pipeline stages
        self.stages: Dict[str, PipelineStage] = {
            'url_discovery': URLDiscoveryStage(config),
            'link_discovery': LinkDiscoveryStage(config),
            'http_fetcher': HTTPFetcherStage(config),
            'content_extractor': ContentExtractionStage(config.dict() if hasattr(config, 'dict') else {})
        }
        
        # Current job state
        self.current_job: Optional[CrawlJob] = None
        self.pipeline_state: Optional[PipelineState] = None
        self.url_queue: Optional[URLQueue] = None
        
        # Runtime tracking
        self.start_time: Optional[datetime] = None
        self.last_checkpoint: Optional[datetime] = None
        
    def start_new_job(self, domain: str, job_id: str = None) -> CrawlJob:
        """Start a new crawling job"""
        # Create job
        job = CrawlJob(
            job_id=job_id or self._generate_job_id(),
            domain=domain,
            config=dict(self.config.__dict__)  # Convert to regular dict
        )
        
        # Initialize pipeline state
        pipeline_state = PipelineState(
            job_id=job.job_id,
            current_stage=PipelineStageEnum.DISCOVERY
        )
        
        # Initialize URL queue
        url_queue = URLQueue(job.job_id)
        
        self.current_job = job
        self.pipeline_state = pipeline_state
        self.url_queue = url_queue
        
        # Save initial checkpoint
        self._save_checkpoint()
        
        self.logger.info(f"Started new job {job.job_id} for domain {domain}")
        return job
    
    def resume_job(self, job_id: str) -> Optional[CrawlJob]:
        """Resume a job from checkpoint"""
        checkpoint = self.checkpoint_manager.load_checkpoint(job_id)
        
        if not checkpoint:
            self.logger.error(f"No checkpoint found for job {job_id}")
            return None
        
        self.current_job = checkpoint['job']
        self.pipeline_state = checkpoint['pipeline_state']
        self.url_queue = URLQueue(job_id)
        
        # Restore URL queues from checkpoint
        if checkpoint.get('pending_pages'):
            self.url_queue.add_pending(checkpoint['pending_pages'])
        
        self.logger.info(f"Resumed job {job_id} from {checkpoint['checkpoint_time']}")
        return self.current_job
    
    def run_pipeline(self, max_duration_hours: Optional[int] = None) -> bool:
        """Run the complete pipeline"""
        if not self.current_job:
            self.logger.error("No job to run")
            return False
        
        from utils.time import get_current_time
        self.start_time = get_current_time()
        self.current_job.start()
        
        max_duration = max_duration_hours or self.config.timeout_hours
        end_time = self.start_time + timedelta(hours=max_duration)
        
        try:
            # Stage 1: URL Discovery (if starting fresh)
            if self.pipeline_state.current_stage == PipelineStageEnum.DISCOVERY:
                self._run_url_discovery()
                self.pipeline_state.advance_stage(PipelineStageEnum.FETCH)
                self._save_checkpoint()
            
            # Stage 2: Fetch and Link Discovery Loop
            if self.pipeline_state.current_stage == PipelineStageEnum.FETCH:
                success = self._run_fetch_loop(end_time)
                
                if not success:
                    self.current_job.fail()
                    return False
            
            # Complete job
            self.current_job.complete()
            self._save_final_results()
            
            duration = (get_current_time() - self.start_time).total_seconds()
            self.logger.info(f"Job {self.current_job.job_id} completed in {duration:.1f} seconds")
            return True
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            self.current_job.fail()
            self._save_checkpoint()
            raise
    
    def _run_url_discovery(self) -> None:
        """Run initial URL discovery from domain"""
        self.logger.info("Starting URL discovery phase")
        
        discovery_stage = self.stages['url_discovery']
        seed_url = f"https://{self.current_job.domain}"
        
        # Discover initial URLs
        discovered_pages = list(discovery_stage.process_item(seed_url, self.current_job))
        
        if discovered_pages:
            self.url_queue.add_pending(discovered_pages)
            self.current_job.total_pages = len(discovered_pages)
            self.logger.info(f"Discovered {len(discovered_pages)} initial URLs")
        else:
            # Fallback: just crawl the main domain
            main_page = Page(url=seed_url, job_id=self.current_job.job_id)
            self.url_queue.add_pending([main_page])
            self.current_job.total_pages = 1
            self.logger.warning("No URLs from sitemap, starting with domain homepage")
    
    def _run_fetch_loop(self, end_time: datetime) -> bool:
        """Main fetch and discovery loop"""
        self.logger.info("Starting fetch loop")
        
        fetcher_stage = self.stages['http_fetcher']
        link_discovery_stage = self.stages['link_discovery']
        content_extractor_stage = self.stages['content_extractor']
        
        processed_count = 0
        consecutive_empty_batches = 0
        
        while get_current_time() < end_time and consecutive_empty_batches < 5:
            # Get batch of pages to process
            batch = self.url_queue.get_pending_batch(batch_size=10)
            
            if not batch:
                consecutive_empty_batches += 1
                time.sleep(1)
                continue
            
            consecutive_empty_batches = 0
            completed_pages = []
            failed_pages = []
            new_pages = []
            
            # Process batch
            for page in batch:
                try:
                    # Fetch page
                    fetched_page = fetcher_stage.process_item(page, self.current_job)
                    
                    if fetched_page.status == PageStatus.FETCHED:
                        # Extract content from the fetched page
                        extracted_page = content_extractor_stage.process_item(fetched_page, self.current_job)
                        
                        # Discover new links
                        link_results = list(link_discovery_stage.process_item(extracted_page, self.current_job))
                        
                        # Separate the original page from newly discovered pages
                        for result in link_results:
                            if result.url == extracted_page.url:
                                completed_pages.append(result)
                            else:
                                new_pages.append(result)
                        
                        processed_count += 1
                        
                    else:
                        failed_pages.append(fetched_page)
                    
                except Exception as e:
                    self.logger.error(f"Error processing {page.url}: {e}")
                    page.mark_failed(str(e))
                    failed_pages.append(page)
            
            # Update queues
            if completed_pages:
                self.url_queue.mark_completed(completed_pages)
            if failed_pages:
                self.url_queue.mark_failed(failed_pages)
            if new_pages:
                # Filter new pages to avoid duplicates and respect limits
                filtered_new_pages = self._filter_new_pages(new_pages)
                if filtered_new_pages:
                    self.url_queue.add_pending(filtered_new_pages)
                    self.current_job.total_pages += len(filtered_new_pages)
            
            # Update job statistics
            self.current_job.processed_pages = processed_count
            self.current_job.failed_pages = len(failed_pages)
            
            # Checkpoint periodically
            if processed_count % self.config.checkpoint_interval == 0:
                self._save_checkpoint()
                self.logger.info(f"Processed {processed_count} pages, "
                               f"queue status: {self.url_queue.get_counts()}")
            
            # Check limits
            if self.current_job.total_pages >= self.config.max_pages:
                self.logger.info(f"Reached page limit ({self.config.max_pages})")
                break
        
        # Final checkpoint
        self._save_checkpoint()
        
        if get_current_time() >= end_time:
            self.logger.warning("Reached time limit")
            return True  # Still successful, just time-limited
        
        return True
    
    def _filter_new_pages(self, pages: List[Page]) -> List[Page]:
        """Filter new pages to avoid duplicates and respect crawling policies"""
        # For now, basic filtering - could be enhanced
        seen_urls = set()
        filtered_pages = []
        
        for page in pages:
            if (page.url not in seen_urls and 
                self.current_job.total_pages + len(filtered_pages) < self.config.max_pages):
                seen_urls.add(page.url)
                filtered_pages.append(page)
        
        return filtered_pages
    
    def _save_checkpoint(self) -> None:
        """Save current pipeline state"""
        if not self.current_job or not self.pipeline_state:
            return
        
        try:
            # Get current queue counts
            counts = self.url_queue.get_counts()
            self.pipeline_state.update_progress(
                pending=counts['pending'],
                processing=counts['processing'], 
                completed=counts['completed'],
                failed=counts['failed']
            )
            
            # Save checkpoint
            self.checkpoint_manager.save_checkpoint(
                self.current_job,
                self.pipeline_state
            )
            
            self.last_checkpoint = get_current_time()
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
    
    def _save_final_results(self) -> None:
        """Save final crawl results"""
        if not self.current_job:
            return
        
        try:
            # Load all completed pages
            completed_pages = self._load_all_completed_pages()
            
            # Save pages data
            self.data_store.save_pages_csv(self.current_job.job_id, completed_pages)
            self.data_store.save_pages_json(self.current_job.job_id, completed_pages)
            
            # Save contacts
            self.data_store.save_contacts_csv(self.current_job.job_id, completed_pages)
            
            # Create summary report
            self.data_store.create_summary_report(
                self.current_job.job_id, 
                self.current_job, 
                completed_pages
            )
            
            self.logger.info(f"Final results saved for job {self.current_job.job_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save final results: {e}")
    
    def _load_all_completed_pages(self) -> List[Page]:
        """Load all completed pages from storage"""
        if not self.url_queue:
            return []
        
        # Load completed pages from the queue file
        completed_file = self.url_queue.completed_file
        if completed_file.exists():
            return self.url_queue._load_pages(completed_file)
        
        return []
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        from utils.common import get_timestamp_string
        timestamp = get_timestamp_string()
        return f"job_{timestamp}"
    
    def get_job_status(self) -> Optional[Dict[str, Any]]:
        """Get current job status"""
        if not self.current_job:
            return None
        
        counts = self.url_queue.get_counts() if self.url_queue else {}
        
        status = {
            'job_id': self.current_job.job_id,
            'domain': self.current_job.domain,
            'status': self.current_job.status.value,
            'current_stage': self.pipeline_state.current_stage.value if self.pipeline_state else None,
            'total_pages': self.current_job.total_pages,
            'processed_pages': self.current_job.processed_pages,
            'failed_pages': self.current_job.failed_pages,
            'queue_status': counts,
            'started_at': self.current_job.started_at.isoformat() if self.current_job.started_at else None,
            'last_checkpoint': self.last_checkpoint.isoformat() if self.last_checkpoint else None
        }
        
        if self.start_time:
            status['elapsed_seconds'] = (get_current_time() - self.start_time).total_seconds()
        
        return status
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all available jobs"""
        job_ids = self.checkpoint_manager.list_jobs()
        jobs = []
        
        for job_id in job_ids:
            status = self.checkpoint_manager.get_job_status(job_id)
            if status:
                jobs.append(status)
        
        return jobs
    
    def pause_job(self) -> bool:
        """Pause current job"""
        if self.current_job:
            self.current_job.pause()
            self._save_checkpoint()
            self.logger.info(f"Paused job {self.current_job.job_id}")
            return True
        return False
    
    def stop_job(self) -> bool:
        """Stop current job gracefully"""
        if self.current_job:
            if self.current_job.status == JobStatus.RUNNING:
                self.current_job.complete()
            self._save_checkpoint()
            self._save_final_results()
            self.logger.info(f"Stopped job {self.current_job.job_id}")
            return True
        return False