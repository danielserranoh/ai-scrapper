"""
Content analysis stage for extracting business intelligence
"""

import re
from typing import Dict, Set, Optional, List, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from collections import Counter

from pipeline.base import PipelineStage, ErrorAction
from models.job import CrawlJob
from models.page import Page, PageStatus
from models.analytics import SiteMetrics, SubdomainAnalytics
from utils.common import extract_emails, extract_social_media_handles, get_domain_from_url
from utils.time import get_current_time


@dataclass
class URLStructure:
    """URL structure analysis"""
    path_depth: int
    path_segments: List[str]
    has_parameters: bool
    file_extension: Optional[str]
    url_pattern: str  # categorized pattern like 'faculty_profile', 'department_listing'
    academic_year: Optional[str]  # extracted academic year if present


@dataclass
class AssetInfo:
    """Information about linked assets"""
    url: str
    asset_type: str  # pdf, image, video, document, etc.
    size_estimate: Optional[int]  # if available from headers
    description: Optional[str]  # from link text or alt text


@dataclass
class PageAnalysis:
    """Enhanced analysis results for a single page"""
    url: str
    page_type: str
    page_subtype: Optional[str]  # more specific classification
    emails: Set[str]
    social_media: Dict[str, Set[str]]
    internal_links: int
    external_links: int
    external_domains: Set[str]
    content_indicators: Dict[str, int]  # department, research, etc.
    url_structure: URLStructure
    linked_assets: List[AssetInfo]
    semantic_indicators: Dict[str, List[str]]  # semantic content analysis


class ContentAnalysisStage(PipelineStage):
    """Analyzes page content for business intelligence extraction"""
    
    def __init__(self, config: Dict = None):
        super().__init__("content_analysis", config)
        
        # Enhanced page type classification patterns with subtypes
        self.page_type_patterns = {
            'faculty': {
                'patterns': [
                    r'faculty', r'professors?', r'staff', r'people', r'directory',
                    r'bio', r'profile', r'cv', r'resume', r'research.*team'
                ],
                'subtypes': {
                    'individual_profile': [r'/people/[^/]+$', r'/faculty/[^/]+$', r'/staff/[^/]+$'],
                    'faculty_listing': [r'/faculty/?$', r'/people/?$', r'/staff/?$'],
                    'department_faculty': [r'/faculty/[^/]+/[^/]+$', r'department.*faculty']
                }
            },
            'department': {
                'patterns': [
                    r'department', r'school.*of', r'college.*of', r'division',
                    r'program', r'academic.*unit'
                ],
                'subtypes': {
                    'department_home': [r'^/(dept|department|school)/?$'],
                    'program_page': [r'/programs?/[^/]+', r'/majors?/[^/]+'],
                    'curriculum': [r'curriculum', r'courses?', r'requirements']
                }
            },
            'research': {
                'patterns': [
                    r'research', r'lab', r'laboratory', r'center.*for', r'institute',
                    r'project', r'publication', r'paper'
                ],
                'subtypes': {
                    'research_center': [r'/centers?/', r'/institutes?/', r'/labs?/'],
                    'research_project': [r'/projects?/', r'/research/[^/]+'],
                    'publications': [r'publications?', r'papers?', r'bibliography']
                }
            },
            'admissions': {
                'patterns': [
                    r'admissions?', r'apply', r'application', r'prospective',
                    r'undergraduate', r'graduate', r'degree'
                ],
                'subtypes': {
                    'undergraduate': [r'undergraduate', r'bachelors?', r'bs.*degree'],
                    'graduate': [r'graduate', r'masters?', r'phd', r'doctoral'],
                    'application_form': [r'apply.*now', r'application.*form']
                }
            },
            'academics': {
                'patterns': [
                    r'academics?', r'curriculum', r'courses?', r'degree',
                    r'majors?', r'minors?', r'concentrations?'
                ],
                'subtypes': {
                    'course_catalog': [r'catalog', r'courses?/?$', r'schedule'],
                    'degree_requirements': [r'requirements', r'checklist', r'plan.*study'],
                    'academic_calendar': [r'calendar', r'semester', r'quarter']
                }
            },
            'student_life': {
                'patterns': [
                    r'student.*life', r'campus.*life', r'activities', r'clubs',
                    r'organizations', r'housing', r'dining'
                ],
                'subtypes': {
                    'housing': [r'housing', r'residence', r'dormitor'],
                    'activities': [r'activities', r'clubs', r'organizations'],
                    'services': [r'services', r'support', r'counseling']
                }
            },
            'news': {
                'patterns': [
                    r'news', r'press', r'announcement', r'event', r'calendar'
                ],
                'subtypes': {
                    'news_article': [r'/news/\d{4}/', r'/press/\d{4}/', r'article'],
                    'events': [r'events?', r'calendar', r'upcoming'],
                    'press_release': [r'press.*release', r'media.*kit']
                }
            },
            'about': {
                'patterns': [
                    r'about', r'mission', r'history', r'overview', r'welcome'
                ],
                'subtypes': {
                    'mission': [r'mission', r'vision', r'values'],
                    'history': [r'history', r'timeline', r'founded'],
                    'leadership': [r'leadership', r'administration', r'board']
                }
            },
            'contact': {
                'patterns': [
                    r'contact', r'location', r'address', r'phone', r'email', r'directory'
                ],
                'subtypes': {
                    'directory': [r'directory', r'phonebook', r'contacts'],
                    'location': [r'location', r'address', r'map', r'directions'],
                    'contact_form': [r'contact.*form', r'get.*touch']
                }
            }
        }
        
        # URL pattern recognition for site structure analysis
        self.url_patterns = {
            'faculty_profile': r'/(?:faculty|people|staff)/([^/]+)/?$',
            'department_page': r'/(?:dept|department|school)/([^/]+)/?$',
            'course_page': r'/(?:courses?|classes?)/([^/]+)',
            'research_project': r'/(?:research|projects?)/([^/]+)',
            'news_article': r'/(?:news|press)/(\d{4})/([^/]+)',
            'academic_year': r'/(\d{4}[-/]\d{4}|\d{4})/',
            'file_download': r'\.(?:pdf|doc|docx|ppt|pptx|xls|xlsx)$',
            'media_file': r'\.(?:jpg|jpeg|png|gif|svg|mp4|avi|mov)$'
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
        
        # Asset categorization patterns
        self.asset_categories = {
            'documents': {
                'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
                'patterns': [r'syllabus', r'curriculum', r'handbook', r'manual', r'guide']
            },
            'presentations': {
                'extensions': ['.ppt', '.pptx', '.key'],
                'patterns': [r'slides', r'presentation', r'lecture']
            },
            'spreadsheets': {
                'extensions': ['.xls', '.xlsx', '.csv'],
                'patterns': [r'data', r'spreadsheet', r'budget', r'roster']
            },
            'media': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'],
                'patterns': [r'photo', r'image', r'gallery', r'picture']
            },
            'videos': {
                'extensions': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
                'patterns': [r'video', r'lecture.*recording', r'webinar']
            },
            'audio': {
                'extensions': ['.mp3', '.wav', '.m4a', '.ogg'],
                'patterns': [r'audio', r'podcast', r'recording']
            },
            'archives': {
                'extensions': ['.zip', '.tar', '.gz', '.rar', '.7z'],
                'patterns': [r'download', r'archive', r'backup']
            },
            'code': {
                'extensions': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c'],
                'patterns': [r'source.*code', r'github', r'repository']
            }
        }
        
        # Semantic analysis patterns for enhanced content understanding
        self.semantic_patterns = {
            'academic_focus': [
                r'artificial.*intelligence', r'machine.*learning', r'computer.*science',
                r'engineering', r'mathematics', r'physics', r'chemistry', r'biology',
                r'psychology', r'sociology', r'economics', r'business', r'medicine'
            ],
            'research_methods': [
                r'qualitative', r'quantitative', r'experimental', r'survey',
                r'case.*study', r'ethnographic', r'statistical.*analysis'
            ],
            'academic_levels': [
                r'undergraduate', r'graduate', r'doctoral', r'postdoctoral',
                r'bachelors?', r'masters?', r'phd', r'certificate'
            ],
            'institutional_roles': [
                r'dean', r'provost', r'chancellor', r'president', r'chair',
                r'director', r'coordinator', r'administrator'
            ],
            'academic_activities': [
                r'conference', r'symposium', r'workshop', r'seminar',
                r'colloquium', r'lecture.*series', r'guest.*speaker'
            ]
        }
        
        # Initialize analytics tracking
        self.site_metrics: Optional[SiteMetrics] = None
        self.subdomain_analytics: Dict[str, SubdomainAnalytics] = {}
        
    def should_process(self, page: Page, job: CrawlJob) -> bool:
        """Only process pages that have been successfully extracted but not yet analyzed"""
        return (page.status == PageStatus.EXTRACTED and 
                page.clean_content and 
                len(page.clean_content.strip()) > 50 and  # Lowered minimum content threshold
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
            
            # Update page with enhanced analysis results
            page.analysis_results = {
                'page_type': analysis.page_type,
                'page_subtype': analysis.page_subtype,
                'emails_found': len(analysis.emails),
                'social_profiles_found': sum(len(profiles) for profiles in analysis.social_media.values()),
                'content_indicators': analysis.content_indicators,
                'url_structure': {
                    'path_depth': analysis.url_structure.path_depth,
                    'url_pattern': analysis.url_structure.url_pattern,
                    'academic_year': analysis.url_structure.academic_year,
                    'file_extension': analysis.url_structure.file_extension
                },
                'linked_assets_count': len(analysis.linked_assets),
                'asset_breakdown': self._get_asset_breakdown(analysis.linked_assets),
                'semantic_indicators': {k: len(v) for k, v in analysis.semantic_indicators.items()}  # Just counts for JSON compatibility
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
        """Perform comprehensive enhanced content analysis"""
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
        
        # Enhanced page classification with subtypes
        page_type, page_subtype = self._classify_page_type_enhanced(full_text, url_text)
        
        # Analyze URL structure
        url_structure = self._analyze_url_structure(page.url)
        
        # Analyze links and extract assets
        internal_links, external_links, external_domains = self._analyze_links(html_content, job.domain)
        linked_assets = self._extract_linked_assets(html_content, page.url)
        
        # Extract content indicators
        content_indicators = self._extract_content_indicators(content)
        
        # Perform semantic analysis
        semantic_indicators = self._analyze_semantic_content(content)
        
        return PageAnalysis(
            url=page.url,
            page_type=page_type,
            page_subtype=page_subtype,
            emails=emails,
            social_media=social_media_sets,
            internal_links=internal_links,
            external_links=external_links,
            external_domains=external_domains,
            content_indicators=content_indicators,
            url_structure=url_structure,
            linked_assets=linked_assets,
            semantic_indicators=semantic_indicators
        )
    
    def _classify_page_type_enhanced(self, full_text: str, url_text: str) -> Tuple[str, Optional[str]]:
        """Enhanced page type classification with subtypes"""
        scores = {}
        
        # Score main page types
        for page_type, config in self.page_type_patterns.items():
            score = 0
            for pattern in config['patterns']:
                # URL gets higher weight
                url_matches = len(re.findall(pattern, url_text, re.IGNORECASE))
                content_matches = len(re.findall(pattern, full_text, re.IGNORECASE))
                score += url_matches * 3 + content_matches
            scores[page_type] = score
        
        # Determine main page type
        if not scores or max(scores.values()) == 0:
            return 'general', None
            
        main_type = max(scores, key=scores.get)
        
        # Find subtype within the main type
        subtype = None
        if main_type in self.page_type_patterns:
            subtype_scores = {}
            subtypes = self.page_type_patterns[main_type].get('subtypes', {})
            
            for subtype_name, patterns in subtypes.items():
                subtype_score = 0
                for pattern in patterns:
                    url_matches = len(re.findall(pattern, url_text, re.IGNORECASE))
                    content_matches = len(re.findall(pattern, full_text, re.IGNORECASE))
                    subtype_score += url_matches * 2 + content_matches
                subtype_scores[subtype_name] = subtype_score
            
            if subtype_scores and max(subtype_scores.values()) > 0:
                subtype = max(subtype_scores, key=subtype_scores.get)
        
        return main_type, subtype
    
    def _analyze_url_structure(self, url: str) -> URLStructure:
        """Analyze URL structure and patterns"""
        parsed = urlparse(url)
        path = parsed.path
        
        # Extract path segments
        segments = [seg for seg in path.split('/') if seg]
        path_depth = len(segments)
        
        # Check for parameters
        has_parameters = bool(parsed.query)
        
        # Extract file extension
        file_extension = None
        if path and '.' in path:
            potential_ext = path.split('.')[-1].lower()
            if len(potential_ext) <= 5:  # reasonable extension length
                file_extension = f".{potential_ext}"
        
        # Determine URL pattern
        url_pattern = self._categorize_url_pattern(url)
        
        # Extract academic year if present
        academic_year = self._extract_academic_year(url)
        
        return URLStructure(
            path_depth=path_depth,
            path_segments=segments,
            has_parameters=has_parameters,
            file_extension=file_extension,
            url_pattern=url_pattern,
            academic_year=academic_year
        )
    
    def _categorize_url_pattern(self, url: str) -> str:
        """Categorize URL based on common university patterns"""
        url_lower = url.lower()
        
        for pattern_name, pattern in self.url_patterns.items():
            if re.search(pattern, url_lower):
                return pattern_name
        
        # Fallback categorization based on path structure
        if '/people/' in url_lower or '/faculty/' in url_lower:
            return 'faculty_profile'
        elif '/departments/' in url_lower or '/dept/' in url_lower:
            return 'department_page'
        elif '/courses/' in url_lower or '/classes/' in url_lower:
            return 'course_page'
        elif '/research/' in url_lower:
            return 'research_project'
        elif '/news/' in url_lower:
            return 'news_article'
        else:
            return 'general'
    
    def _extract_academic_year(self, url: str) -> Optional[str]:
        """Extract academic year from URL"""
        # Look for 4-digit years or academic year patterns
        year_pattern = r'(\d{4}(?:[-/]\d{4})?)'
        matches = re.findall(year_pattern, url)
        
        for match in matches:
            year = int(match.split('-')[0].split('/')[0])
            # Only consider reasonable academic years
            if 1990 <= year <= 2030:
                return match
                
        return None
    
    def _extract_linked_assets(self, html_content: str, base_url: str) -> List[AssetInfo]:
        """Extract and categorize linked assets from HTML"""
        if not html_content:
            return []
        
        assets = []
        
        # Pattern to find links with href attributes
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
        matches = re.findall(link_pattern, html_content, re.IGNORECASE)
        
        for url, link_text in matches:
            # Resolve relative URLs
            full_url = urljoin(base_url, url)
            
            # Categorize asset
            asset_type = self._categorize_asset(full_url, link_text)
            
            if asset_type != 'webpage':  # Only track non-webpage assets
                assets.append(AssetInfo(
                    url=full_url,
                    asset_type=asset_type,
                    size_estimate=None,  # Could be enhanced with HEAD requests
                    description=link_text.strip() if link_text.strip() else None
                ))
        
        return assets
    
    def _categorize_asset(self, url: str, link_text: str = "") -> str:
        """Categorize an asset based on URL and context"""
        url_lower = url.lower()
        text_lower = link_text.lower()
        
        # Check file extension first
        for asset_type, config in self.asset_categories.items():
            for ext in config['extensions']:
                if url_lower.endswith(ext):
                    return asset_type
        
        # Check content patterns
        for asset_type, config in self.asset_categories.items():
            for pattern in config['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE) or re.search(pattern, url_lower, re.IGNORECASE):
                    return asset_type
        
        return 'webpage'  # Default for regular web pages
    
    def _analyze_semantic_content(self, content: str) -> Dict[str, List[str]]:
        """Perform semantic analysis of content"""
        semantic_results = {}
        
        for category, patterns in self.semantic_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, content, re.IGNORECASE)
                matches.extend(found)
            
            # Remove duplicates and normalize
            unique_matches = list(set(match.lower() for match in matches))
            semantic_results[category] = unique_matches[:10]  # Limit to top 10 matches
        
        return semantic_results
    
    def _get_asset_breakdown(self, assets: List[AssetInfo]) -> Dict[str, int]:
        """Get breakdown of assets by type"""
        breakdown = Counter(asset.asset_type for asset in assets)
        return dict(breakdown)
    
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