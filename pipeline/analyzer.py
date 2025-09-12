"""
Content analysis stage for extracting business intelligence
"""

import re
from typing import Dict, Set, Optional
from urllib.parse import urlparse
from dataclasses import dataclass

from pipeline.base import PipelineStage, ErrorAction
from models.job import CrawlJob
from models.page import Page, PageStatus
from models.analytics import SiteMetrics, SubdomainAnalytics
from utils.common import extract_emails, extract_social_media_handles, get_domain_from_url
from utils.time import get_current_time


@dataclass
class PageAnalysis:
    """Analysis results for a single page"""
    url: str
    page_type: str
    emails: Set[str]
    social_media: Dict[str, Set[str]]
    internal_links: int
    external_links: int
    external_domains: Set[str]
    content_indicators: Dict[str, int]  # department, research, etc.


class ContentAnalysisStage(PipelineStage):
    """Analyzes page content for business intelligence extraction"""
    
    def __init__(self, config: Dict = None):
        super().__init__("content_analysis", config)
        
        # Page type classification patterns
        self.page_type_patterns = {
            'faculty': [
                r'faculty', r'professors?', r'staff', r'people', r'directory',
                r'bio', r'profile', r'cv', r'resume', r'research.*team'
            ],
            'department': [
                r'department', r'school.*of', r'college.*of', r'division',
                r'program', r'academic.*unit'
            ],
            'research': [
                r'research', r'lab', r'laboratory', r'center.*for', r'institute',
                r'project', r'publication', r'paper'
            ],
            'admissions': [
                r'admissions?', r'apply', r'application', r'prospective',
                r'undergraduate', r'graduate', r'degree'
            ],
            'news': [
                r'news', r'press', r'announcement', r'event', r'calendar'
            ],
            'about': [
                r'about', r'mission', r'history', r'overview', r'welcome'
            ],
            'contact': [
                r'contact', r'location', r'address', r'phone', r'email', r'directory'
            ]
        }
        
        # Content indicators for business intelligence
        self.content_indicators = {
            'funding_references': [
                r'grant', r'funding', r'nsf', r'nih', r'darpa', r'dod', r'doe',
                r'foundation', r'award', r'sponsored'
            ],
            'collaboration_indicators': [
                r'partnership', r'collaboration', r'joint.*venture', r'consortium',
                r'alliance', r'cooperat'
            ],
            'technology_transfer': [
                r'patent', r'license', r'commerciali[sz]', r'startup', r'spinoff',
                r'technology.*transfer', r'intellectual.*property'
            ],
            'industry_connections': [
                r'industry', r'corporate', r'business', r'commercial', r'enterprise'
            ]
        }
        
        # Initialize analytics tracking
        self.site_metrics: Optional[SiteMetrics] = None
        self.subdomain_analytics: Dict[str, SubdomainAnalytics] = {}
        
    def should_process(self, page: Page, job: CrawlJob) -> bool:
        """Only process pages that have been successfully extracted but not yet analyzed"""
        return (page.status == PageStatus.EXTRACTED and 
                page.clean_content and 
                len(page.clean_content.strip()) > 100 and  # Minimum content threshold
                page.analysis_results is None)  # Only analyze if not already analyzed
    
    def process_item(self, page: Page, job: CrawlJob) -> Page:
        """Analyze page content for business intelligence"""
        try:
            # Initialize site metrics if not exists
            if not self.site_metrics:
                self.site_metrics = SiteMetrics(
                    job_id=job.job_id,
                    domain=job.domain
                )
            
            # Analyze the page
            analysis = self._analyze_page_content(page, job)
            
            # Update page with extracted contacts
            page.emails.update(analysis.emails)
            for platform, handles in analysis.social_media.items():
                if platform not in page.social_media:
                    page.social_media[platform] = set()
                page.social_media[platform].update(handles)
            
            # Update page with analysis results
            page.analysis_results = {
                'page_type': analysis.page_type,
                'emails_found': len(analysis.emails),
                'social_profiles_found': sum(len(profiles) for profiles in analysis.social_media.values()),
                'content_indicators': analysis.content_indicators
            }
            
            # Update site-wide metrics
            self._update_site_metrics(analysis, page)
            
            # Update subdomain analytics
            subdomain = self._extract_subdomain(page.url, job.domain)
            self._update_subdomain_analytics(subdomain, analysis, page, job)
            
            # Mark as analyzed
            page.status = PageStatus.ANALYZED if page.status == PageStatus.EXTRACTED else page.status
            page.analyzed_at = get_current_time()
            
            self.logger.debug(f"Analyzed {page.url}: {analysis.page_type} page, "
                            f"{len(analysis.emails)} emails, "
                            f"{sum(len(p) for p in analysis.social_media.values())} social profiles")
            
        except Exception as e:
            self.logger.error(f"Analysis failed for {page.url}: {e}")
            page.add_error(f"Analysis error: {e}")
        
        return page
    
    def _analyze_page_content(self, page: Page, job: CrawlJob) -> PageAnalysis:
        """Perform comprehensive content analysis"""
        content = page.clean_content or ""
        html_content = page.html_content or ""
        url_text = page.url.lower()
        title_text = (page.title or "").lower()
        
        # Combine text for analysis
        full_text = f"{content} {title_text} {url_text}"
        
        # Extract contacts
        emails = set(extract_emails(content))
        social_media = extract_social_media_handles(content)
        
        # Convert social media lists to sets for consistency
        social_media_sets = {}
        for platform, handles in social_media.items():
            social_media_sets[platform] = set(handles) if isinstance(handles, list) else handles
        
        # Classify page type
        page_type = self._classify_page_type(full_text, url_text)
        
        # Analyze links
        internal_links, external_links, external_domains = self._analyze_links(html_content, job.domain)
        
        # Extract content indicators
        content_indicators = self._extract_content_indicators(content)
        
        return PageAnalysis(
            url=page.url,
            page_type=page_type,
            emails=emails,
            social_media=social_media_sets,
            internal_links=internal_links,
            external_links=external_links,
            external_domains=external_domains,
            content_indicators=content_indicators
        )
    
    def _classify_page_type(self, full_text: str, url_text: str) -> str:
        """Classify page type based on content and URL patterns"""
        scores = {}
        
        for page_type, patterns in self.page_type_patterns.items():
            score = 0
            for pattern in patterns:
                # URL gets higher weight
                url_matches = len(re.findall(pattern, url_text, re.IGNORECASE))
                content_matches = len(re.findall(pattern, full_text, re.IGNORECASE))
                score += url_matches * 3 + content_matches
            scores[page_type] = score
        
        # Return the type with highest score, or 'general' if no strong matches
        if scores and max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'general'
    
    def _analyze_links(self, html_content: str, domain: str) -> tuple:
        """Analyze internal vs external links in HTML content"""
        if not html_content:
            return 0, 0, set()
        
        # Simple regex to find links - could be enhanced with proper HTML parsing
        link_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        internal_count = 0
        external_count = 0
        external_domains = set()
        
        for link in links:
            if link.startswith('http'):
                link_domain = get_domain_from_url(link)
                if domain in link_domain or link_domain.endswith('.' + domain):
                    internal_count += 1
                else:
                    external_count += 1
                    external_domains.add(link_domain)
            elif link.startswith('/') or not link.startswith('#'):
                # Relative links are internal
                internal_count += 1
        
        return internal_count, external_count, external_domains
    
    def _extract_content_indicators(self, content: str) -> Dict[str, int]:
        """Extract business intelligence indicators from content"""
        indicators = {}
        
        for indicator_type, patterns in self.content_indicators.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                count += len(matches)
            indicators[indicator_type] = count
        
        return indicators
    
    def _extract_subdomain(self, url: str, main_domain: str) -> str:
        """Extract subdomain from URL"""
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        
        if hostname == main_domain:
            return 'www'  # Main domain
        elif hostname.endswith('.' + main_domain):
            # Extract subdomain part
            subdomain = hostname[:-len('.' + main_domain)]
            return subdomain
        else:
            return 'external'  # Shouldn't happen in normal crawling
    
    def _update_site_metrics(self, analysis: PageAnalysis, page: Page):
        """Update site-wide metrics with page analysis"""
        content_type = 'html'  # We're only analyzing HTML pages in this stage
        
        self.site_metrics.add_page_stats(
            content_type=content_type,
            internal_links=analysis.internal_links,
            external_links=analysis.external_links,
            external_domains=analysis.external_domains,
            subdomain=self._extract_subdomain(page.url, self.site_metrics.domain)
        )
        
        # Update contact counts
        self.site_metrics.emails_found += len(analysis.emails)
        self.site_metrics.social_profiles_found += sum(len(profiles) for profiles in analysis.social_media.values())
    
    def _update_subdomain_analytics(self, subdomain: str, analysis: PageAnalysis, 
                                  page: Page, job: CrawlJob):
        """Update subdomain-specific analytics"""
        if subdomain not in self.subdomain_analytics:
            self.subdomain_analytics[subdomain] = SubdomainAnalytics(
                job_id=job.job_id,
                subdomain=subdomain,
                domain=job.domain
            )
        
        subdomain_analytics = self.subdomain_analytics[subdomain]
        
        subdomain_analytics.add_page(
            url=page.url,
            content_type='html',
            internal_links=analysis.internal_links,
            emails=analysis.emails,
            social=analysis.social_media
        )
    
    def get_analytics_summary(self) -> Dict:
        """Get comprehensive analytics summary"""
        return {
            'site_metrics': self.site_metrics,
            'subdomain_analytics': dict(self.subdomain_analytics),
            'total_subdomains': len(self.subdomain_analytics),
            'total_emails': self.site_metrics.emails_found if self.site_metrics else 0,
            'total_social_profiles': self.site_metrics.social_profiles_found if self.site_metrics else 0
        }
    
    def handle_error(self, page: Page, error: Exception, job: CrawlJob) -> ErrorAction:
        """Handle analysis errors"""
        if isinstance(error, (AttributeError, ValueError, TypeError)):
            # Content parsing issues - skip this page
            return ErrorAction.SKIP
        elif isinstance(error, MemoryError):
            # Content too large - skip
            self.logger.warning(f"Content too large for analysis: {page.url}")
            return ErrorAction.SKIP
        else:
            # Other errors - retry once
            return ErrorAction.RETRY