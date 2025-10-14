import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from pipeline.base import PipelineStage, ErrorAction
from models.job import CrawlJob
from models.page import Page, PageStatus
from config import CrawlConfig
from utils.time import get_current_time

# Import browser fetcher (lazy to avoid import overhead if not needed)
_browser_fetcher_pool = None


class BotDetector:
    """Detects bot protection and challenge pages"""

    CHALLENGE_DOMAINS = {
        'validate.perfdrive.com',  # Radware Bot Manager
        'challenges.cloudflare.com',  # Cloudflare
        'www.google.com/recaptcha',  # reCAPTCHA
        'hcaptcha.com',  # hCaptcha
        'geo.captcha-delivery.com',  # Generic CAPTCHA
    }

    CHALLENGE_INDICATORS = [
        'bot detection',
        'bot manager',
        'automated access',
        'verify you are human',
        'cloudflare',
        'checking your browser',
        'enable javascript',
        'radware',
        'please verify',
        'security check',
        'access denied',
        'captcha',
    ]

    @staticmethod
    def is_bot_challenge_response(response: requests.Response) -> bool:
        """Detect if HTTP response is a bot challenge page"""
        # Check for redirect to challenge domain
        final_url = response.url.lower()
        if any(domain in final_url for domain in BotDetector.CHALLENGE_DOMAINS):
            return True

        # Check for challenge indicators in content
        if response.text:
            content_lower = response.text.lower()
            # Need at least 2 indicators to avoid false positives
            matches = sum(1 for indicator in BotDetector.CHALLENGE_INDICATORS if indicator in content_lower)
            if matches >= 2:
                return True

        # Check for specific status codes + headers combination
        if response.status_code == 403:
            server = response.headers.get('server', '').lower()
            if 'cloudflare' in server or 'radware' in server:
                return True

        return False

    @staticmethod
    def should_use_browser(page: Page) -> bool:
        """Decide if page needs browser-based fetching"""
        # Always use browser if previous attempt detected bot challenge
        if page.error_message:
            if 'bot challenge' in page.error_message.lower():
                return True
            if 'bot detection' in page.error_message.lower():
                return True

        # Use browser if retry count > 1 and still failing with 403/429
        if page.retry_count > 1 and page.status == PageStatus.FAILED:
            if page.status_code in [403, 429]:
                return True

        return False


class AdaptiveRateLimiter:
    """Manages request timing with adaptive delays and intelligent blocking detection"""
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 30.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.last_request_time: Optional[datetime] = None
        self.consecutive_errors = 0
        self.success_count = 0
        
        # Response time tracking for dynamic adjustment
        self.response_times: List[float] = []
        self.max_response_history = 50
        self.fast_response_threshold = 0.5  # seconds
        self.slow_response_threshold = 3.0  # seconds
        
        # Blocking detection state
        self.rate_limit_violations = 0
        self.last_rate_limit_time: Optional[datetime] = None
        self.server_error_count = 0
        self.blocking_indicators = 0
        
    def wait(self) -> None:
        """Wait appropriate time before next request"""
        if self.last_request_time:
            elapsed = (get_current_time() - self.last_request_time).total_seconds()
            sleep_time = max(0, self.current_delay - elapsed)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.last_request_time = get_current_time()
    
    def on_success(self, response_time: float = 0.0) -> None:
        """Called after successful request with response time"""
        self.consecutive_errors = 0
        self.success_count += 1
        self.server_error_count = 0  # Reset server error count on success
        
        # Track response time
        if response_time > 0:
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_history:
                self.response_times.pop(0)
        
        # Dynamic delay adjustment based on response times
        self._adjust_delay_from_response_time(response_time)
        
        # Gradually reduce delay after sustained success
        if self.success_count > 10 and self.current_delay > self.base_delay:
            self.current_delay = max(self.base_delay, self.current_delay * 0.9)
            self.success_count = 0
    
    def on_error(self, status_code: Optional[int] = None, headers: Dict[str, str] = None) -> None:
        """Called after request error with enhanced blocking detection"""
        self.consecutive_errors += 1
        self.success_count = 0
        
        # Analyze error patterns for blocking detection
        self._analyze_blocking_indicators(status_code, headers)
        
        # Increase delay based on error type
        if status_code == 429:  # Too Many Requests
            self.rate_limit_violations += 1
            self.last_rate_limit_time = get_current_time()
            self.current_delay = min(self.max_delay, self.current_delay * 2.5)
            self.blocking_indicators += 2
            
        elif status_code == 403:  # Forbidden - potential blocking
            self.blocking_indicators += 3
            self.current_delay = min(self.max_delay, self.current_delay * 2)
            
        elif status_code and status_code >= 500:  # Server errors
            self.server_error_count += 1
            self.current_delay = min(self.max_delay, self.current_delay * 1.5)
            if self.server_error_count > 3:
                self.blocking_indicators += 1
                
        elif status_code == 404:  # Not Found - less severe
            self.current_delay = min(self.max_delay, self.current_delay * 1.1)
            
        else:  # Other errors
            self.current_delay = min(self.max_delay, self.current_delay * 1.2)
            self.blocking_indicators += 1
    
    def is_blocked(self) -> bool:
        """Check if we might be blocked using multiple indicators"""
        # Traditional consecutive error check
        if self.consecutive_errors > 5:
            return True
            
        # Recent rate limit violations
        if self.rate_limit_violations > 2:
            return True
            
        # High blocking indicator score
        if self.blocking_indicators > 8:
            return True
            
        # Recent rate limit with ongoing issues
        if (self.last_rate_limit_time and 
            get_current_time() - self.last_rate_limit_time < timedelta(minutes=10) and
            self.consecutive_errors > 2):
            return True
            
        return False
    
    def get_blocking_severity(self) -> str:
        """Get current blocking severity level"""
        if self.is_blocked():
            return "blocked"
        elif self.blocking_indicators > 4 or self.consecutive_errors > 3:
            return "throttled"
        elif self.current_delay > self.base_delay * 2:
            return "limited"
        else:
            return "normal"
    
    def _adjust_delay_from_response_time(self, response_time: float) -> None:
        """Adjust delay based on server response time"""
        if not self.response_times or len(self.response_times) < 5:
            return
            
        # Calculate average response time from recent requests
        avg_response_time = sum(self.response_times[-10:]) / min(len(self.response_times), 10)
        
        # If responses are consistently fast, we can be more aggressive
        if avg_response_time < self.fast_response_threshold and response_time < self.fast_response_threshold:
            if self.current_delay > self.base_delay:
                self.current_delay = max(self.base_delay, self.current_delay * 0.95)
                
        # If responses are consistently slow, back off more
        elif avg_response_time > self.slow_response_threshold:
            self.current_delay = min(self.max_delay, self.current_delay * 1.1)
    
    def _analyze_blocking_indicators(self, status_code: Optional[int], headers: Dict[str, str] = None) -> None:
        """Analyze response for blocking indicators"""
        if not headers:
            headers = {}
        
        # Check for rate limiting headers
        rate_limit_headers = [
            'x-ratelimit-remaining', 'x-rate-limit-remaining',
            'ratelimit-remaining', 'x-ratelimit-limit'
        ]
        
        for header in rate_limit_headers:
            if header.lower() in {k.lower() for k in headers.keys()}:
                value = headers.get(header, '').strip()
                try:
                    if value and int(value) == 0:
                        self.blocking_indicators += 2
                except ValueError:
                    pass
        
        # Check for retry-after header
        if 'retry-after' in {k.lower() for k in headers.keys()}:
            self.blocking_indicators += 2
            
        # Check for cloudflare or other protection services
        protection_headers = ['cf-ray', 'x-sucuri-id', 'x-drupal-cache']
        for header in protection_headers:
            if header.lower() in {k.lower() for k in headers.keys()}:
                # Presence of protection doesn't mean blocking, but increases suspicion
                if status_code in [403, 429, 503]:
                    self.blocking_indicators += 1


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

        # Bot detection
        self.detector = BotDetector()

        # Browser fetcher pool (lazy initialization)
        self.browser_pool = None
        self.browser_fetch_count = 0
        self.total_fetch_count = 0
    
        
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

    def _get_browser_pool(self):
        """Lazy initialize browser pool"""
        if self.browser_pool is None:
            # Check if browser fallback is enabled
            if not getattr(self.crawl_config, 'enable_browser_fallback', True):
                return None

            self.logger.info("Initializing browser fetcher pool")
            from pipeline.browser_fetcher import BrowserFetcherPool

            pool_size = getattr(self.crawl_config, 'browser_pool_size', 1)
            self.browser_pool = BrowserFetcherPool(self.crawl_config, pool_size=pool_size)

        return self.browser_pool

    def _fetch_with_browser(self, page: Page, job: CrawlJob) -> Page:
        """Fetch page using browser automation"""
        try:
            pool = self._get_browser_pool()
            if pool is None:
                page.mark_failed("Browser fallback disabled in configuration")
                return page

            page = pool.fetch(page, job)
            self.browser_fetch_count += 1

            # Mark extraction method for requests-based fetches
            if page.status == PageStatus.FETCHED and not page.extraction_method:
                page.extraction_method = "browser"

            # Log browser usage statistics
            browser_percentage = (
                (self.browser_fetch_count / self.total_fetch_count * 100)
                if self.total_fetch_count > 0
                else 0
            )
            self.logger.info(
                f"Browser fetches: {self.browser_fetch_count}/{self.total_fetch_count} "
                f"({browser_percentage:.1f}%)"
            )

        except Exception as e:
            self.logger.error(f"Browser fetch failed for {page.url}: {e}")
            page.mark_failed(f"Browser fetch error: {str(e)}")

        return page

    def process_item(self, page: Page, job: CrawlJob) -> Page:
        """Fetch HTML content for a page with automatic browser fallback"""
        if page.status != PageStatus.DISCOVERED:
            return page

        # Check if we should use browser directly (based on previous failures)
        if self.detector.should_use_browser(page):
            self.logger.info(f"Using browser fetcher for {page.url} (previous bot challenge)")
            return self._fetch_with_browser(page, job)

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
        
        # Check if rate limiter detects blocking and apply degradation
        severity = rate_limiter.get_blocking_severity()
        
        if rate_limiter.is_blocked():
            self.logger.warning(f"Blocking detected for {domain}, applying degradation strategy")
            self._apply_degradation_strategy(domain, rate_limiter, "blocked")
            page.mark_failed("Domain blocked - applying cooldown")
            return page
        elif severity == "throttled":
            self.logger.info(f"Throttling detected for {domain}, increasing delays")
            self._apply_degradation_strategy(domain, rate_limiter, "throttled")
        
        # Wait for rate limiting
        rate_limiter.wait()
        
        page.status = PageStatus.FETCHING
        request_start_time = time.time()
        
        try:
            # Use adaptive timeout based on current conditions
            adaptive_timeout = self._get_adaptive_timeout(rate_limiter)
            
            # Make HTTP request
            response = self.session.get(
                page.url,
                timeout=adaptive_timeout,
                allow_redirects=True
            )
            
            # Calculate response time
            response_time = time.time() - request_start_time
            
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
                # Check for bot challenge in successful response
                if self.detector.is_bot_challenge_response(response):
                    self.logger.warning(f"Bot challenge detected for {page.url}, retrying with browser")
                    page.error_message = "Bot challenge detected"
                    page.status = PageStatus.DISCOVERED  # Reset for retry with browser
                    return self._fetch_with_browser(page, job)

                # Success - store content
                page.html_content = response.text
                page.status = PageStatus.FETCHED
                page.extraction_method = "requests"  # Mark standard fetching
                rate_limiter.on_success(response_time)
                self.total_fetch_count += 1

                # Log additional insights in verbose mode
                severity = rate_limiter.get_blocking_severity()
                self.logger.debug(f"Successfully fetched {page.url} ({page.content_length} bytes, "
                               f"{response_time:.2f}s, {severity})")
                
            else:
                # HTTP error
                error_msg = f"HTTP {response.status_code}"
                page.mark_failed(error_msg)
                rate_limiter.on_error(response.status_code, dict(response.headers))
                
                severity = rate_limiter.get_blocking_severity()
                self.logger.warning(f"HTTP {response.status_code} for {page.url} "
                                  f"({response_time:.2f}s, {severity})")
        
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
    
    def _apply_degradation_strategy(self, domain: str, rate_limiter: AdaptiveRateLimiter, 
                                   severity: str) -> None:
        """Apply graduated degradation strategies based on blocking severity"""
        
        if severity == "blocked":
            # Severe blocking - long cooldown and reset indicators
            self._mark_domain_blocked(domain)
            rate_limiter.current_delay = min(rate_limiter.max_delay, rate_limiter.current_delay * 3)
            
            # Reset indicators after cooldown to allow recovery
            rate_limiter.blocking_indicators = max(0, rate_limiter.blocking_indicators - 5)
            rate_limiter.consecutive_errors = max(0, rate_limiter.consecutive_errors - 3)
            
        elif severity == "throttled":
            # Moderate throttling - increase delays and wait longer
            rate_limiter.current_delay = min(rate_limiter.max_delay, rate_limiter.current_delay * 1.8)
            
            # Add extra wait time for throttled requests
            extra_wait = min(10, rate_limiter.current_delay * 0.5)
            time.sleep(extra_wait)
            
        elif severity == "limited":
            # Light limiting - slight increase in delays
            rate_limiter.current_delay = min(rate_limiter.max_delay, rate_limiter.current_delay * 1.3)
    
    def _should_skip_request(self, domain: str, rate_limiter: AdaptiveRateLimiter) -> bool:
        """Determine if we should skip this request entirely"""
        severity = rate_limiter.get_blocking_severity()
        
        # Skip if we're blocked
        if severity == "blocked":
            return True
            
        # Skip if we have too many recent rate limit violations
        if (rate_limiter.last_rate_limit_time and
            get_current_time() - rate_limiter.last_rate_limit_time < timedelta(minutes=5) and
            rate_limiter.rate_limit_violations > 3):
            return True
            
        return False
    
    def _get_adaptive_timeout(self, rate_limiter: AdaptiveRateLimiter) -> int:
        """Get adaptive timeout based on current conditions"""
        base_timeout = self.crawl_config.request_timeout
        severity = rate_limiter.get_blocking_severity()
        
        if severity == "blocked":
            return base_timeout * 3
        elif severity == "throttled":
            return base_timeout * 2  
        elif severity == "limited":
            return int(base_timeout * 1.5)
        else:
            return base_timeout
    
    def get_stats(self) -> Dict[str, any]:
        """Get enhanced fetcher statistics with blocking intelligence and browser usage"""
        stats = {
            'total_processed': self.processed_count,
            'total_failed': self.failed_count,
            'blocked_domains': len(self.blocked_domains),
            'browser_fetches': self.browser_fetch_count,
            'requests_fetches': self.total_fetch_count - self.browser_fetch_count,
            'browser_percentage': (
                (self.browser_fetch_count / self.total_fetch_count * 100)
                if self.total_fetch_count > 0
                else 0
            ),
            'rate_limiter_status': {},
            'blocking_summary': {}
        }
        
        # Collect detailed rate limiter information
        for domain, limiter in self.rate_limiters.items():
            severity = limiter.get_blocking_severity()
            avg_response_time = (sum(limiter.response_times[-10:]) / min(len(limiter.response_times), 10)
                               if limiter.response_times else 0)
            
            stats['rate_limiter_status'][domain] = {
                'current_delay': round(limiter.current_delay, 2),
                'base_delay': limiter.base_delay,
                'consecutive_errors': limiter.consecutive_errors,
                'success_count': limiter.success_count,
                'blocking_severity': severity,
                'blocking_indicators': limiter.blocking_indicators,
                'rate_limit_violations': limiter.rate_limit_violations,
                'avg_response_time': round(avg_response_time, 2) if avg_response_time else None,
                'server_error_count': limiter.server_error_count
            }
        
        # Summary statistics
        severities = [limiter.get_blocking_severity() for limiter in self.rate_limiters.values()]
        stats['blocking_summary'] = {
            'normal': severities.count('normal'),
            'limited': severities.count('limited'),
            'throttled': severities.count('throttled'),
            'blocked': severities.count('blocked')
        }
        
        return stats