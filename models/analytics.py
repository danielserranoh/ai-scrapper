from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Set, List
from collections import defaultdict


# Remove duplicate - use centralized time service
from utils.time import get_current_time as _get_current_time


@dataclass
class SiteMetrics:
    job_id: str
    domain: str
    total_pages: int = 0
    html_pages: int = 0
    pdf_pages: int = 0
    image_pages: int = 0
    other_pages: int = 0
    total_internal_links: int = 0
    total_external_links: int = 0
    unique_external_domains: Set[str] = field(default_factory=set)
    subdomains: Set[str] = field(default_factory=set)
    emails_found: int = 0
    social_profiles_found: int = 0
    
    # HTTP Status Code tracking
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    redirect_chains: List[Dict[str, str]] = field(default_factory=list)
    
    generated_at: datetime = field(default_factory=lambda: _get_current_time())
    
    def add_page_stats(self, content_type: str, internal_links: int, 
                      external_links: int, external_domains: Set[str],
                      subdomain: str = None) -> None:
        self.total_pages += 1
        
        if content_type == 'html':
            self.html_pages += 1
        elif content_type == 'pdf':
            self.pdf_pages += 1
        elif content_type == 'image':
            self.image_pages += 1
        else:
            self.other_pages += 1
            
        self.total_internal_links += internal_links
        self.total_external_links += external_links
        self.unique_external_domains.update(external_domains)
        
        if subdomain:
            self.subdomains.add(subdomain)
    
    def add_status_code(self, status_code: int) -> None:
        """Track HTTP status code"""
        self.status_codes[status_code] += 1
    
    def add_redirect_chain(self, original_url: str, final_url: str, 
                          redirect_count: int, status_codes: List[int]) -> None:
        """Track redirect chain"""
        self.redirect_chains.append({
            'original_url': original_url,
            'final_url': final_url,
            'redirect_count': redirect_count,
            'status_codes': status_codes,
            'timestamp': _get_current_time()
        })


@dataclass
class SubdomainAnalytics:
    job_id: str
    subdomain: str
    domain: str
    page_count: int = 0
    content_breakdown: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    emails: Set[str] = field(default_factory=set)
    social_profiles: Dict[str, Set[str]] = field(default_factory=lambda: defaultdict(set))
    top_pages: Dict[str, int] = field(default_factory=dict)  # URL -> internal link count
    generated_at: datetime = field(default_factory=lambda: _get_current_time())
    
    def add_page(self, url: str, content_type: str, internal_links: int,
                 emails: Set[str] = None, social: Dict[str, Set[str]] = None) -> None:
        self.page_count += 1
        self.content_breakdown[content_type] += 1
        self.top_pages[url] = internal_links
        
        if emails:
            self.emails.update(emails)
            
        if social:
            for platform, profiles in social.items():
                self.social_profiles[platform].update(profiles)
    
    @property
    def email_count(self) -> int:
        return len(self.emails)
    
    @property
    def social_profile_count(self) -> int:
        return sum(len(profiles) for profiles in self.social_profiles.values())
    
    def get_top_pages(self, limit: int = 10) -> Dict[str, int]:
        return dict(sorted(self.top_pages.items(), 
                          key=lambda x: x[1], reverse=True)[:limit])