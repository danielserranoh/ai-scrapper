import csv
import json
from pathlib import Path
from typing import List, Dict
import logging

from models.job import CrawlJob
from models.page import Page, PageStatus
from models.analytics import SiteMetrics, SubdomainAnalytics
from storage.checkpoints import JSONEncoder
from utils.time import get_current_time


class DataStore:
    """Handles data storage and export operations"""
    
    def __init__(self, base_dir: str = "data/output"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
    def save_pages_csv(self, job_id: str, pages: List[Page], filename: str = None) -> str:
        """Save pages data to CSV file"""
        if not filename:
            from config import get_current_time
            timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_id}_pages_{timestamp}.csv"
        
        csv_path = self.base_dir / filename
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'url', 'status', 'status_code', 'content_type', 'content_length',
                    'title', 'domain', 'subdomain', 'path', 'discovered_at',
                    'fetched_at', 'processed_at', 'analyzed_at', 'error_message', 'retry_count',
                    'internal_links_count', 'external_links_count', 'emails_count',
                    'social_profiles_count', 'page_type', 'funding_references',
                    'collaboration_indicators', 'technology_transfer', 'industry_connections'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for page in pages:
                    # Extract analysis results if available
                    analysis = page.analysis_results or {}
                    content_indicators = analysis.get('content_indicators', {})
                    
                    row = {
                        'url': page.url,
                        'status': page.status.value,
                        'status_code': page.status_code,
                        'content_type': page.content_type,
                        'content_length': page.content_length,
                        'title': page.title,
                        'domain': page.domain,
                        'subdomain': page.subdomain,
                        'path': page.path,
                        'discovered_at': page.discovered_at.isoformat() if page.discovered_at else None,
                        'fetched_at': page.fetched_at.isoformat() if page.fetched_at else None,
                        'processed_at': page.processed_at.isoformat() if page.processed_at else None,
                        'analyzed_at': page.analyzed_at.isoformat() if page.analyzed_at else None,
                        'error_message': page.error_message,
                        'retry_count': page.retry_count,
                        'internal_links_count': len(page.internal_links),
                        'external_links_count': len(page.external_links),
                        'emails_count': len(page.emails),
                        'social_profiles_count': sum(len(profiles) for profiles in page.social_media.values()),
                        'page_type': analysis.get('page_type', ''),
                        'funding_references': content_indicators.get('funding_references', 0),
                        'collaboration_indicators': content_indicators.get('collaboration_indicators', 0),
                        'technology_transfer': content_indicators.get('technology_transfer', 0),
                        'industry_connections': content_indicators.get('industry_connections', 0)
                    }
                    writer.writerow(row)
            
            self.logger.info(f"Saved {len(pages)} pages to {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save pages CSV: {e}")
            raise
    
    def save_pages_json(self, job_id: str, pages: List[Page], filename: str = None) -> str:
        """Save pages data to JSON file"""
        if not filename:
            from config import get_current_time
            timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_id}_pages_{timestamp}.json"
        
        json_path = self.base_dir / filename
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(pages, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(pages)} pages to {json_path}")
            return str(json_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save pages JSON: {e}")
            raise
    
    def save_contacts_csv(self, job_id: str, pages: List[Page], filename: str = None) -> str:
        """Save extracted contacts to CSV file"""
        if not filename:
            from config import get_current_time
            timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_id}_contacts_{timestamp}.csv"
        
        csv_path = self.base_dir / filename
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'source_url', 'contact_type', 'contact_value', 'subdomain',
                    'page_title', 'discovered_at'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for page in pages:
                    # Email contacts
                    for email in page.emails:
                        writer.writerow({
                            'source_url': page.url,
                            'contact_type': 'email',
                            'contact_value': email,
                            'subdomain': page.subdomain,
                            'page_title': page.title,
                            'discovered_at': page.processed_at.isoformat() if page.processed_at else None
                        })
                    
                    # Social media contacts
                    for platform, profiles in page.social_media.items():
                        for profile in profiles:
                            writer.writerow({
                                'source_url': page.url,
                                'contact_type': platform,
                                'contact_value': profile,
                                'subdomain': page.subdomain,
                                'page_title': page.title,
                                'discovered_at': page.processed_at.isoformat() if page.processed_at else None
                            })
            
            self.logger.info(f"Saved contacts to {csv_path}")
            return str(csv_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save contacts CSV: {e}")
            raise
    
    def save_metrics_json(self, job_id: str, metrics: SiteMetrics, 
                         subdomain_metrics: List[SubdomainAnalytics] = None,
                         filename: str = None) -> str:
        """Save site metrics to JSON file"""
        if not filename:
            from config import get_current_time
            timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
            filename = f"{job_id}_metrics_{timestamp}.json"
        
        json_path = self.base_dir / filename
        
        try:
            from config import get_current_time
            data = {
                'site_metrics': metrics,
                'subdomain_metrics': subdomain_metrics or [],
                'generated_at': get_current_time()
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved metrics to {json_path}")
            return str(json_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save metrics JSON: {e}")
            raise
    
    def create_summary_report(self, job_id: str, job: CrawlJob, pages: List[Page]) -> str:
        """Create a comprehensive summary report"""
        from utils.common import get_timestamp_string
        timestamp = get_timestamp_string()
        report_path = self.base_dir / f"{job_id}_summary_{timestamp}.json"
        
        # Calculate statistics
        total_pages = len(pages)
        # Count pages that were successfully fetched and processed (any status beyond FETCHED)
        successful_statuses = {PageStatus.FETCHED, PageStatus.EXTRACTED, PageStatus.ANALYZED}
        successful_pages = len([p for p in pages if p.status in successful_statuses])
        failed_pages = len([p for p in pages if p.status == PageStatus.FAILED])
        
        # Content type breakdown
        content_types = {}
        for page in pages:
            ct = page.detected_content_type.value
            content_types[ct] = content_types.get(ct, 0) + 1
        
        # Subdomain breakdown
        subdomains = {}
        for page in pages:
            if page.subdomain:
                subdomains[page.subdomain] = subdomains.get(page.subdomain, 0) + 1
        
        # Contact statistics
        total_emails = sum(len(page.emails) for page in pages)
        total_social = sum(sum(len(profiles) for profiles in page.social_media.values()) for page in pages)
        
        # HTTP status code statistics
        status_codes = {}
        redirect_count = 0
        for page in pages:
            if page.status_code:
                status_codes[page.status_code] = status_codes.get(page.status_code, 0) + 1
                # Count pages that were redirected (would have history in original response)
                # For now, we'll detect this from URL changes in fetcher
        
        # Duration calculation
        duration = None
        if job.started_at and job.completed_at:
            duration = (job.completed_at - job.started_at).total_seconds()
        
        summary = {
            'job_info': {
                'job_id': job.job_id,
                'domain': job.domain,
                'status': job.status.value,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'duration_seconds': duration
            },
            'crawl_statistics': {
                'total_pages_discovered': total_pages,
                'pages_successfully_fetched': successful_pages,
                'pages_failed': failed_pages,
                'success_rate': (successful_pages / total_pages * 100) if total_pages > 0 else 0
            },
            'content_breakdown': content_types,
            'subdomain_breakdown': subdomains,
            'contact_statistics': {
                'total_emails_found': total_emails,
                'total_social_profiles_found': total_social
            },
            'http_statistics': {
                'status_codes': status_codes,
                'total_redirects': redirect_count
            },
            'generated_at': get_current_time().isoformat()  # Use UTC for consistency
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Summary report saved to {report_path}")
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create summary report: {e}")
            raise
    
    def load_pages_from_json(self, file_path: str) -> List[Page]:
        """Load pages from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            pages = []
            for page_data in data:
                page = Page(
                    url=page_data['url'],
                    job_id=page_data['job_id'],
                    status=PageStatus(page_data['status'])
                )
                # Restore other fields as needed
                pages.append(page)
            
            return pages
            
        except Exception as e:
            self.logger.error(f"Failed to load pages from {file_path}: {e}")
            return []
    
    def save_analytics_summary(self, job_id: str, analytics_data: dict, filename: str = None) -> str:
        """Save analytics summary to JSON file"""
        if not filename:
            from utils.common import get_timestamp_string
            timestamp = get_timestamp_string()
            filename = f"{job_id}_analytics_{timestamp}.json"
        
        analytics_path = self.base_dir / filename
        
        try:
            # Convert dataclass objects to dictionaries for serialization
            serializable_data = {}
            
            for key, value in analytics_data.items():
                if hasattr(value, '__dict__'):
                    # Handle dataclass objects
                    serializable_data[key] = value.__dict__
                elif isinstance(value, dict):
                    # Handle nested dictionaries with dataclass values
                    serializable_data[key] = {}
                    for sub_key, sub_value in value.items():
                        if hasattr(sub_value, '__dict__'):
                            serializable_data[key][sub_key] = sub_value.__dict__
                        else:
                            serializable_data[key][sub_key] = sub_value
                else:
                    serializable_data[key] = value
            
            with open(analytics_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved analytics summary to {analytics_path}")
            return str(analytics_path)
            
        except Exception as e:
            self.logger.error(f"Failed to save analytics summary: {e}")
            raise
    
    def get_job_files(self, job_id: str) -> Dict[str, List[str]]:
        """Get all files associated with a job"""
        files = {
            'pages': [],
            'contacts': [],
            'metrics': [],
            'summaries': []
        }
        
        for file_path in self.base_dir.glob(f"{job_id}_*"):
            filename = file_path.name
            if '_pages_' in filename:
                files['pages'].append(str(file_path))
            elif '_contacts_' in filename:
                files['contacts'].append(str(file_path))
            elif '_metrics_' in filename:
                files['metrics'].append(str(file_path))
            elif '_summary_' in filename:
                files['summaries'].append(str(file_path))
        
        return files
    
    def cleanup_old_files(self, job_id: str, keep_latest: int = 5) -> None:
        """Clean up old export files, keeping only the most recent"""
        job_files = self.get_job_files(job_id)
        
        for file_type, file_list in job_files.items():
            if len(file_list) > keep_latest:
                # Sort by modification time, keep latest
                sorted_files = sorted(file_list, key=lambda x: Path(x).stat().st_mtime, reverse=True)
                files_to_delete = sorted_files[keep_latest:]
                
                for file_path in files_to_delete:
                    try:
                        Path(file_path).unlink()
                        self.logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete {file_path}: {e}")