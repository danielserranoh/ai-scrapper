import re
from typing import Set, Iterator
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup

from pipeline.base import PipelineStage
from models.job import CrawlJob
from models.page import Page, PageStatus
from config import CrawlConfig


class URLDiscoveryStage(PipelineStage):
    """Discovers URLs by crawling sitemaps and following links"""
    
    def __init__(self, config: CrawlConfig):
        super().__init__("url_discovery", config.__dict__)
        self.crawl_config = config
        self.discovered_urls: Set[str] = set()
        self.robots_cache: dict = {}
        
    def process_item(self, seed_url: str, job: CrawlJob) -> Iterator[Page]:
        """Start discovery from a seed URL (domain)"""
        domain = urlparse(seed_url).netloc
        
        # Try sitemap first
        sitemap_urls = self._discover_from_sitemap(domain)
        self.logger.info(f"Found {len(sitemap_urls)} URLs from sitemaps")
        
        # Add seed URL if not in sitemap
        if not sitemap_urls:
            sitemap_urls = {f"https://{domain}"}
        
        # Yield discovered pages
        for url in sitemap_urls:
            if self._should_crawl_url(url, job):
                page = Page(url=url, job_id=job.job_id)
                self.discovered_urls.add(url)
                yield page
    
    def _discover_from_sitemap(self, domain: str) -> Set[str]:
        """Discover URLs from sitemap.xml files"""
        urls = set()
        
        # Common sitemap locations
        sitemap_urls = [
            f"https://{domain}/sitemap.xml",
            f"https://{domain}/sitemap_index.xml", 
            f"https://{domain}/sitemaps.xml",
            f"https://www.{domain}/sitemap.xml" if not domain.startswith('www.') else None
        ]
        
        for sitemap_url in filter(None, sitemap_urls):
            try:
                self.logger.info(f"Checking sitemap: {sitemap_url}")
                response = requests.get(sitemap_url, timeout=10, allow_redirects=True)
                
                # Log redirect information
                if response.history:
                    redirect_chain = [r.status_code for r in response.history] + [response.status_code]
                    final_url = response.url
                    self.logger.info(f"Sitemap redirected: {sitemap_url} -> {final_url} "
                                   f"(chain: {' -> '.join(map(str, redirect_chain))})")
                
                if response.status_code != 200:
                    self.logger.debug(f"Sitemap not found: {response.status_code} at {response.url}")
                    continue
                
                # Parse sitemap XML
                soup = BeautifulSoup(response.content, 'xml')
                
                # Handle sitemap index
                sitemaps = soup.find_all('sitemap')
                if sitemaps:
                    for sitemap in sitemaps:
                        loc = sitemap.find('loc')
                        if loc:
                            sub_urls = self._parse_sitemap(loc.text)
                            urls.update(sub_urls)
                else:
                    # Direct sitemap
                    sitemap_urls_found = self._parse_sitemap(sitemap_url)
                    urls.update(sitemap_urls_found)
                    
                if urls:
                    break  # Found working sitemap
                    
            except Exception as e:
                self.logger.debug(f"Failed to fetch sitemap {sitemap_url}: {e}")
                continue
        
        return urls
    
    def _parse_sitemap(self, sitemap_url: str) -> Set[str]:
        """Parse individual sitemap file"""
        urls = set()
        
        try:
            response = requests.get(sitemap_url, timeout=10, allow_redirects=True)
            
            # Log redirect information
            if response.history:
                redirect_chain = [r.status_code for r in response.history] + [response.status_code]
                final_url = response.url
                self.logger.debug(f"Sitemap sub-file redirected: {sitemap_url} -> {final_url} "
                               f"(chain: {' -> '.join(map(str, redirect_chain))})")
            
            if response.status_code != 200:
                self.logger.debug(f"Sitemap not found: {response.status_code} at {response.url}")
                return urls
            
            soup = BeautifulSoup(response.content, 'xml')
            
            # Extract URLs from <loc> tags
            for url_elem in soup.find_all('url'):
                loc = url_elem.find('loc')
                if loc and loc.text:
                    urls.add(loc.text.strip())
                    
        except Exception as e:
            self.logger.debug(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return urls
    
    def _should_crawl_url(self, url: str, job: CrawlJob) -> bool:
        """Determine if URL should be crawled based on filters"""
        parsed = urlparse(url)
        
        # Must be same domain or allowed subdomain
        if not self._is_allowed_domain(parsed.netloc, job.domain):
            return False
        
        # Check robots.txt
        if not self._robots_allows(url):
            self.logger.debug(f"Robots.txt disallows: {url}")
            return False
        
        # Check file extension filters
        if any(url.lower().endswith(ext) for ext in self.crawl_config.exclude_extensions):
            return False
        
        # Check URL pattern filters
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in self.crawl_config.exclude_patterns):
            return False
        
        # Check if already discovered
        if url in self.discovered_urls:
            return False
        
        return True
    
    def _is_allowed_domain(self, url_domain: str, job_domain: str) -> bool:
        """Check if URL domain is allowed for crawling"""
        if url_domain == job_domain:
            return True
        
        # Check if it's an allowed subdomain
        if url_domain.endswith(f".{job_domain}"):
            subdomain = url_domain[:-len(job_domain)-1]
            
            # Check against allowlist if configured
            if self.crawl_config.subdomain_allowlist:
                return subdomain in self.crawl_config.subdomain_allowlist
            
            # Default: allow reasonable subdomains (no deep nesting)
            return '.' not in subdomain
        
        return False
    
    def _robots_allows(self, url: str) -> bool:
        """Check if robots.txt allows crawling this URL"""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Cache robots.txt per domain
        if domain not in self.robots_cache:
            try:
                # Try to fetch robots.txt with redirect support
                robots_url = f"{parsed.scheme}://{domain}/robots.txt"
                self.logger.debug(f"Fetching robots.txt: {robots_url}")
                
                response = requests.get(robots_url, timeout=10, allow_redirects=True)
                
                # Log redirect information for robots.txt
                if response.history:
                    redirect_chain = [r.status_code for r in response.history] + [response.status_code]
                    final_url = response.url
                    self.logger.debug(f"Robots.txt redirected: {robots_url} -> {final_url} "
                                   f"(chain: {' -> '.join(map(str, redirect_chain))})")
                
                if response.status_code == 200:
                    # Parse robots.txt content
                    rp = RobotFileParser()
                    rp.set_url(response.url)  # Use final URL after redirects
                    
                    # Write content to temporary file for parsing
                    import tempfile
                    import os
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_file:
                        tmp_file.write(response.text)
                        tmp_file_path = tmp_file.name
                    
                    try:
                        with open(tmp_file_path, 'r') as f:
                            rp.read_file = f.readlines
                            rp.read()
                    finally:
                        os.unlink(tmp_file_path)
                    
                    self.robots_cache[domain] = rp
                    self.logger.debug(f"Loaded robots.txt for {domain} (status: {response.status_code})")
                else:
                    self.logger.debug(f"Robots.txt not found for {domain} (status: {response.status_code})")
                    self.robots_cache[domain] = None
                    
            except Exception as e:
                self.logger.debug(f"Could not load robots.txt for {domain}: {e}")
                # Assume allowed if robots.txt unavailable
                self.robots_cache[domain] = None
        
        robots = self.robots_cache[domain]
        if robots:
            return robots.can_fetch(self.crawl_config.user_agent, url)
        
        return True


class LinkDiscoveryStage(PipelineStage):
    """Discovers additional URLs by following links in fetched pages"""
    
    def __init__(self, config: CrawlConfig):
        super().__init__("link_discovery", config.__dict__)
        self.crawl_config = config
        self.seen_urls: Set[str] = set()
    
    def process_item(self, page: Page, job: CrawlJob) -> Iterator[Page]:
        """Extract links from a fetched page and create new Page objects"""
        if not page.html_content or page.status != PageStatus.FETCHED:
            yield page
            return
        
        try:
            soup = BeautifulSoup(page.html_content, 'html.parser')
            
            # Find all links
            links = soup.find_all('a', href=True)
            
            discovered_count = 0
            for link in links:
                href = link['href'].strip()
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                absolute_url = urljoin(page.url, href)
                
                # Clean up URL (remove fragments, normalize)
                clean_url = self._clean_url(absolute_url)
                
                if self._should_discover_url(clean_url, job, page.url):
                    # Create new page object
                    new_page = Page(url=clean_url, job_id=job.job_id)
                    self.seen_urls.add(clean_url)
                    discovered_count += 1
                    yield new_page
            
            self.logger.debug(f"Discovered {discovered_count} new URLs from {page.url}")
            
        except Exception as e:
            self.logger.error(f"Failed to extract links from {page.url}: {e}")
        
        # Always yield the original page
        yield page
    
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        parsed = urlparse(url)
        
        # Remove fragment
        clean_parsed = parsed._replace(fragment='')
        
        # Remove common tracking parameters
        if clean_parsed.query:
            params = []
            for param in clean_parsed.query.split('&'):
                key = param.split('=')[0].lower()
                if key not in ['utm_source', 'utm_medium', 'utm_campaign', 
                              'utm_content', 'utm_term', 'fbclid', 'gclid']:
                    params.append(param)
            clean_parsed = clean_parsed._replace(query='&'.join(params))
        
        return urlunparse(clean_parsed)
    
    def _should_discover_url(self, url: str, job: CrawlJob, source_url: str) -> bool:
        """Check if URL should be added to discovery queue"""
        if url in self.seen_urls:
            return False
        
        parsed = urlparse(url)
        
        # Basic URL validation
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # Only HTTP/HTTPS
        if parsed.scheme not in ('http', 'https'):
            return False
        
        # Same domain/subdomain check
        job_domain = urlparse(f"https://{job.domain}").netloc
        if not self._is_same_site(parsed.netloc, job_domain):
            return False
        
        # File extension check
        if any(url.lower().endswith(ext) for ext in self.crawl_config.exclude_extensions):
            return False
        
        # Pattern exclusions
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in self.crawl_config.exclude_patterns):
            return False
        
        return True
    
    def _is_same_site(self, url_domain: str, job_domain: str) -> bool:
        """Check if domains belong to the same site"""
        if url_domain == job_domain:
            return True
        
        # Allow subdomains
        return url_domain.endswith(f'.{job_domain}') or job_domain.endswith(f'.{url_domain}')