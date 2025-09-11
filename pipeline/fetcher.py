import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from pipeline.base import PipelineStage, ErrorAction
from models.job import CrawlJob
from models.page import Page, PageStatus
from config import CrawlConfig
from utils.time import get_current_time


class AdaptiveRateLimiter:
    """Manages request timing with adaptive delays"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.last_request_time: Optional[datetime] = None
        self.consecutive_errors = 0
        self.success_count = 0
        
    def wait(self) -> None:
        """Wait appropriate time before next request"""
        if self.last_request_time:
            elapsed = (get_current_time() - self.last_request_time).total_seconds()
            sleep_time = max(0, self.current_delay - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.last_request_time = get_current_time()
    
    def on_success(self) -> None:
        """Called after successful request"""
        self.consecutive_errors = 0
        self.success_count += 1
        
        # Gradually reduce delay after sustained success
        if self.success_count > 10 and self.current_delay > self.base_delay:
            self.current_delay = max(self.base_delay, self.current_delay * 0.9)
            self.success_count = 0
    
    def on_error(self, status_code: Optional[int] = None) -> None:
        """Called after request error"""
        self.consecutive_errors += 1
        self.success_count = 0
        
        # Increase delay based on error type
        if status_code == 429:  # Too Many Requests
            self.current_delay = min(self.max_delay, self.current_delay * 2)
        elif status_code and status_code >= 500:  # Server errors
            self.current_delay = min(self.max_delay, self.current_delay * 1.5)
        else:  # Other errors
            self.current_delay = min(self.max_delay, self.current_delay * 1.2)
    
    def is_blocked(self) -> bool:
        """Check if we might be blocked (too many consecutive errors)"""
        return self.consecutive_errors > 5


class HTTPFetcherStage(PipelineStage):
    """Fetches web pages with adaptive rate limiting and error handling"""
    
    def __init__(self, config: CrawlConfig):
        super().__init__("http_fetcher", config.__dict__)
        self.crawl_config = config
        
        # Rate limiters per domain
        self.rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
        
        # HTTP session with retries
        self.session = self._create_session()
        
        # Blocking detection
        self.blocked_domains: Dict[str, datetime] = {}
    
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with proper configuration"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers
        session.headers.update({
            'User-Agent': self.crawl_config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def process_item(self, page: Page, job: CrawlJob) -> Page:
        """Fetch HTML content for a page"""
        if page.status != PageStatus.DISCOVERED:
            return page
        
        domain = urlparse(page.url).netloc
        
        # Check if domain is temporarily blocked
        if self._is_domain_blocked(domain):
            self.logger.debug(f"Domain {domain} is temporarily blocked")
            page.mark_failed("Domain temporarily blocked")
            return page
        
        # Get or create rate limiter for domain
        if domain not in self.rate_limiters:
            self.rate_limiters[domain] = AdaptiveRateLimiter(
                self.crawl_config.base_delay,
                self.crawl_config.max_delay
            )
        
        rate_limiter = self.rate_limiters[domain]
        
        # Check if rate limiter detects blocking
        if rate_limiter.is_blocked():
            self.logger.warning(f"Possible blocking detected for {domain}")
            self._mark_domain_blocked(domain)
            page.mark_failed("Possible blocking detected")
            return page
        
        # Wait for rate limiting
        rate_limiter.wait()
        
        page.status = PageStatus.FETCHING
        
        try:
            # Make HTTP request
            response = self.session.get(
                page.url,
                timeout=self.crawl_config.request_timeout,
                allow_redirects=True
            )
            
            # Record response details
            page.status_code = response.status_code
            page.content_type = response.headers.get('content-type', '')
            page.content_length = len(response.content)
            page.fetched_at = get_current_time()
            
            # Log redirect information if any
            if response.history:
                redirect_chain = [r.status_code for r in response.history] + [response.status_code]
                original_url = page.url
                final_url = response.url
                self.logger.debug(f"Page redirected: {original_url} -> {final_url} "
                               f"(chain: {' -> '.join(map(str, redirect_chain))})")
                
                # Update page URL to final URL after redirects
                page.url = final_url
            
            if response.status_code == 200:
                # Success
                page.html_content = response.text
                page.status = PageStatus.FETCHED
                rate_limiter.on_success()
                
                self.logger.debug(f"Successfully fetched {page.url} ({page.content_length} bytes)")
                
            else:
                # HTTP error
                error_msg = f"HTTP {response.status_code}"
                page.mark_failed(error_msg)
                rate_limiter.on_error(response.status_code)
                
                self.logger.warning(f"HTTP {response.status_code} for {page.url}")
        
        except requests.exceptions.Timeout:
            page.mark_failed("Request timeout")
            rate_limiter.on_error()
            self.logger.warning(f"Timeout fetching {page.url}")
            
        except requests.exceptions.ConnectionError as e:
            page.mark_failed(f"Connection error: {e}")
            rate_limiter.on_error()
            self.logger.warning(f"Connection error for {page.url}: {e}")
            
        except requests.exceptions.RequestException as e:
            page.mark_failed(f"Request error: {e}")
            rate_limiter.on_error()
            self.logger.error(f"Request error for {page.url}: {e}")
            
        except Exception as e:
            page.mark_failed(f"Unexpected error: {e}")
            rate_limiter.on_error()
            self.logger.error(f"Unexpected error fetching {page.url}: {e}")
        
        return page
    
    def handle_error(self, item: Page, error: Exception, job: CrawlJob) -> ErrorAction:
        """Handle fetch errors with retry logic"""
        if isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            if item.can_retry():
                item.retry_count += 1
                self.logger.info(f"Retrying {item.url} (attempt {item.retry_count})")
                return ErrorAction.RETRY
        
        return ErrorAction.SKIP
    
    def _is_domain_blocked(self, domain: str) -> bool:
        """Check if domain is in blocking cooldown"""
        if domain in self.blocked_domains:
            blocked_until = self.blocked_domains[domain] + timedelta(hours=1)
            if get_current_time() < blocked_until:
                return True
            else:
                # Cooldown expired
                del self.blocked_domains[domain]
        
        return False
    
    def _mark_domain_blocked(self, domain: str) -> None:
        """Mark domain as blocked for cooldown period"""
        self.blocked_domains[domain] = get_current_time()
        self.logger.warning(f"Marking {domain} as blocked for 1 hour cooldown")
    
    def get_stats(self) -> Dict[str, any]:
        """Get fetcher statistics"""
        stats = {
            'total_processed': self.processed_count,
            'total_failed': self.failed_count,
            'blocked_domains': len(self.blocked_domains),
            'rate_limiter_delays': {}
        }
        
        for domain, limiter in self.rate_limiters.items():
            stats['rate_limiter_delays'][domain] = {
                'current_delay': limiter.current_delay,
                'consecutive_errors': limiter.consecutive_errors,
                'success_count': limiter.success_count
            }
        
        return stats