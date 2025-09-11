import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict, is_dataclass
from pathlib import Path
import logging

from models.job import CrawlJob, PipelineState, PipelineStage, JobStatus
from models.page import Page, PageStatus
from enum import Enum
from utils.time import get_current_time


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for dataclasses and datetime objects"""
    
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value  # Serialize enum as its value
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, (dict, type({}.__class__.__dict__))):  # Handle mappingproxy
            return dict(obj)
        elif callable(obj):  # Skip functions and methods
            return f"<function: {obj.__name__}>"
        elif hasattr(obj, '__dict__'):
            # Filter out callable attributes when converting to dict
            filtered_dict = {}
            for key, value in obj.__dict__.items():
                if not callable(value):
                    filtered_dict[key] = value
            return filtered_dict
        return super().default(obj)


class CheckpointManager:
    """Manages job checkpoints using JSON files"""
    
    def __init__(self, base_dir: str = "data/checkpoints"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def save_checkpoint(self, job: CrawlJob, pipeline_state: PipelineState,
                       pending_pages: List[Page] = None,
                       processing_pages: List[Page] = None,
                       completed_pages: List[Page] = None,
                       failed_pages: List[Page] = None) -> None:
        """Save complete job checkpoint"""
        
        checkpoint_data = {
            'job': job,
            'pipeline_state': pipeline_state,
            'pending_pages': pending_pages or [],
            'processing_pages': processing_pages or [],
            'completed_pages': completed_pages or [],
            'failed_pages': failed_pages or [],
            'checkpoint_time': get_current_time(),
        }
        
        checkpoint_file = self.base_dir / f"{job.job_id}_checkpoint.json"
        
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, cls=JSONEncoder, indent=2)
            
            self.logger.info(f"Checkpoint saved for job {job.job_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint for job {job.job_id}: {e}")
            raise
    
    def load_checkpoint(self, job_id: str) -> Optional[Dict]:
        """Load job checkpoint from file"""
        checkpoint_file = self.base_dir / f"{job_id}_checkpoint.json"
        
        if not checkpoint_file.exists():
            self.logger.warning(f"No checkpoint found for job {job_id}")
            return None
        
        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to objects
            checkpoint = self._deserialize_checkpoint(data)
            self.logger.info(f"Checkpoint loaded for job {job_id}")
            return checkpoint
            
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint for job {job_id}: {e}")
            return None
    
    def _deserialize_checkpoint(self, data: Dict) -> Dict:
        """Convert JSON data back to objects"""
        
        # Restore job
        job_data = data['job']
        job = CrawlJob(
            job_id=job_data['job_id'],
            domain=job_data['domain'],
            status=JobStatus(job_data['status']),
            created_at=datetime.fromisoformat(job_data['created_at']),
            started_at=datetime.fromisoformat(job_data['started_at']) if job_data.get('started_at') else None,
            completed_at=datetime.fromisoformat(job_data['completed_at']) if job_data.get('completed_at') else None,
            config=job_data.get('config', {}),
            total_pages=job_data.get('total_pages', 0),
            processed_pages=job_data.get('processed_pages', 0),
            failed_pages=job_data.get('failed_pages', 0),
            subdomains_found=job_data.get('subdomains_found', 0)
        )
        
        # Restore pipeline state
        ps_data = data['pipeline_state']
        pipeline_state = PipelineState(
            job_id=ps_data['job_id'],
            current_stage=PipelineStage(ps_data['current_stage']),
            stage_progress=ps_data.get('stage_progress', {}),
            last_checkpoint=datetime.fromisoformat(ps_data['last_checkpoint']),
            pending_urls=ps_data.get('pending_urls', 0),
            processing_urls=ps_data.get('processing_urls', 0),
            completed_urls=ps_data.get('completed_urls', 0),
            failed_urls=ps_data.get('failed_urls', 0)
        )
        
        # Restore pages
        def restore_pages(pages_data: List[Dict]) -> List[Page]:
            pages = []
            for page_data in pages_data:
                page = Page(
                    url=page_data['url'],
                    job_id=page_data['job_id'],
                    status=PageStatus(page_data['status']),
                    discovered_at=datetime.fromisoformat(page_data['discovered_at'])
                )
                
                # Optional fields
                for field in ['fetched_at', 'processed_at', 'status_code', 'content_type', 
                             'content_length', 'html_content', 'title', 'clean_content',
                             'markdown_content', 'error_message', 'retry_count', 'max_retries']:
                    if field in page_data and page_data[field] is not None:
                        if field in ['fetched_at', 'processed_at']:
                            setattr(page, field, datetime.fromisoformat(page_data[field]))
                        else:
                            setattr(page, field, page_data[field])
                
                # Set fields
                if 'internal_links' in page_data:
                    page.internal_links = set(page_data['internal_links'])
                if 'external_links' in page_data:
                    page.external_links = set(page_data['external_links'])
                if 'emails' in page_data:
                    page.emails = set(page_data['emails'])
                if 'social_media' in page_data:
                    page.social_media = {k: set(v) for k, v in page_data['social_media'].items()}
                
                pages.append(page)
            return pages
        
        return {
            'job': job,
            'pipeline_state': pipeline_state,
            'pending_pages': restore_pages(data.get('pending_pages', [])),
            'processing_pages': restore_pages(data.get('processing_pages', [])),
            'completed_pages': restore_pages(data.get('completed_pages', [])),
            'failed_pages': restore_pages(data.get('failed_pages', [])),
            'checkpoint_time': datetime.fromisoformat(data['checkpoint_time'])
        }
    
    def list_jobs(self) -> List[str]:
        """List all available job IDs with checkpoints"""
        jobs = []
        for checkpoint_file in self.base_dir.glob("*_checkpoint.json"):
            job_id = checkpoint_file.stem.replace('_checkpoint', '')
            jobs.append(job_id)
        return sorted(jobs)
    
    def delete_checkpoint(self, job_id: str) -> bool:
        """Delete checkpoint file for job"""
        checkpoint_file = self.base_dir / f"{job_id}_checkpoint.json"
        
        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                self.logger.info(f"Deleted checkpoint for job {job_id}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to delete checkpoint for job {job_id}: {e}")
        
        return False
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get basic job status without loading full checkpoint"""
        checkpoint_file = self.base_dir / f"{job_id}_checkpoint.json"
        
        if not checkpoint_file.exists():
            return None
        
        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            
            job_data = data['job']
            pipeline_data = data['pipeline_state']
            
            return {
                'job_id': job_id,
                'domain': job_data['domain'],
                'status': job_data['status'],
                'current_stage': pipeline_data['current_stage'],
                'total_pages': job_data.get('total_pages', 0),
                'processed_pages': job_data.get('processed_pages', 0),
                'failed_pages': job_data.get('failed_pages', 0),
                'last_checkpoint': pipeline_data['last_checkpoint'],
                'pending_urls': pipeline_data.get('pending_urls', 0),
                'completed_urls': pipeline_data.get('completed_urls', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get status for job {job_id}: {e}")
            return None


class URLQueue:
    """Manages URL queues using JSON files"""
    
    def __init__(self, job_id: str, base_dir: str = "data/queues"):
        self.job_id = job_id
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.pending_file = self.base_dir / f"{job_id}_pending.json"
        self.processing_file = self.base_dir / f"{job_id}_processing.json"
        self.completed_file = self.base_dir / f"{job_id}_completed.json"
        self.failed_file = self.base_dir / f"{job_id}_failed.json"
        
        self.logger = logging.getLogger(__name__)
    
    def add_pending(self, pages: List[Page]) -> None:
        """Add pages to pending queue"""
        self._append_to_file(self.pending_file, pages)
    
    def get_pending_batch(self, batch_size: int = 10) -> List[Page]:
        """Get batch of pending pages and move to processing"""
        pending_pages = self._load_pages(self.pending_file)
        
        if not pending_pages:
            return []
        
        # Get batch
        batch = pending_pages[:batch_size]
        remaining = pending_pages[batch_size:]
        
        # Update files
        self._save_pages(self.pending_file, remaining)
        self._append_to_file(self.processing_file, batch)
        
        return batch
    
    def mark_completed(self, pages: List[Page]) -> None:
        """Move pages from processing to completed"""
        processing_pages = self._load_pages(self.processing_file)
        completed_urls = {p.url for p in pages}
        
        # Remove from processing
        remaining_processing = [p for p in processing_pages if p.url not in completed_urls]
        self._save_pages(self.processing_file, remaining_processing)
        
        # Add to completed
        self._append_to_file(self.completed_file, pages)
    
    def mark_failed(self, pages: List[Page]) -> None:
        """Move pages from processing to failed"""
        processing_pages = self._load_pages(self.processing_file)
        failed_urls = {p.url for p in pages}
        
        # Remove from processing
        remaining_processing = [p for p in processing_pages if p.url not in failed_urls]
        self._save_pages(self.processing_file, remaining_processing)
        
        # Add to failed
        self._append_to_file(self.failed_file, pages)
    
    def get_counts(self) -> Dict[str, int]:
        """Get counts for each queue"""
        return {
            'pending': len(self._load_pages(self.pending_file)),
            'processing': len(self._load_pages(self.processing_file)),
            'completed': len(self._load_pages(self.completed_file)),
            'failed': len(self._load_pages(self.failed_file))
        }
    
    def _load_pages(self, file_path: Path) -> List[Page]:
        """Load pages from JSON file"""
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            pages = []
            for page_data in data:
                page = Page(
                    url=page_data['url'],
                    job_id=page_data['job_id'],
                    status=PageStatus(page_data['status']),
                    discovered_at=datetime.fromisoformat(page_data['discovered_at']) if page_data.get('discovered_at') else get_current_time()
                )
                
                # Restore all optional fields
                for field in ['fetched_at', 'processed_at', 'status_code', 'content_type', 
                             'content_length', 'html_content', 'title', 'clean_content',
                             'markdown_content', 'error_message', 'retry_count', 'max_retries']:
                    if field in page_data and page_data[field] is not None:
                        if field in ['fetched_at', 'processed_at']:
                            setattr(page, field, datetime.fromisoformat(page_data[field]))
                        else:
                            setattr(page, field, page_data[field])
                
                # Restore set fields
                if 'internal_links' in page_data and page_data['internal_links']:
                    page.internal_links = set(page_data['internal_links'])
                if 'external_links' in page_data and page_data['external_links']:
                    page.external_links = set(page_data['external_links'])
                if 'emails' in page_data and page_data['emails']:
                    page.emails = set(page_data['emails'])
                if 'social_media' in page_data and page_data['social_media']:
                    page.social_media = {k: set(v) for k, v in page_data['social_media'].items()}
                
                pages.append(page)
            
            return pages
            
        except Exception as e:
            self.logger.error(f"Failed to load pages from {file_path}: {e}")
            return []
    
    def _save_pages(self, file_path: Path, pages: List[Page]) -> None:
        """Save pages to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(pages, f, cls=JSONEncoder, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save pages to {file_path}: {e}")
    
    def _append_to_file(self, file_path: Path, pages: List[Page]) -> None:
        """Append pages to JSON file"""
        existing_pages = self._load_pages(file_path)
        existing_pages.extend(pages)
        self._save_pages(file_path, existing_pages)