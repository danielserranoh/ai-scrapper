import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup, Comment
import html2text

from pipeline.base import PipelineStage, ErrorAction
from models.job import CrawlJob
from models.page import Page, PageStatus
from utils.time import get_current_time


class ContentExtractionStage(PipelineStage):
    """Extracts clean content from HTML pages"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("content_extraction", config)
        
        # Configure html2text for markdown conversion
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0  # Don't wrap lines
        self.html_converter.unicode_snob = True
        self.html_converter.ignore_emphasis = False
        
    def should_process(self, page: Page, job: CrawlJob) -> bool:
        """Only process successfully fetched HTML pages"""
        return (page.status == PageStatus.FETCHED and 
                page.html_content and 
                page.content_type and 
                'text/html' in page.content_type)
    
    def process_item(self, page: Page, job: CrawlJob) -> Page:
        """Extract and clean content from HTML"""
        try:
            soup = BeautifulSoup(page.html_content, 'html.parser')
            
            # Extract page title
            page.title = self._extract_title(soup)
            
            # Clean and extract main content
            page.clean_content = self._extract_clean_text(soup)
            
            # Convert to markdown
            page.markdown_content = self._convert_to_markdown(soup)
            
            # Update status
            page.status = PageStatus.EXTRACTED
            page.processed_at = get_current_time()
            
            self.logger.debug(f"Extracted content from {page.url}: "
                            f"{len(page.clean_content) if page.clean_content else 0} chars clean text, "
                            f"{len(page.markdown_content) if page.markdown_content else 0} chars markdown")
            
        except Exception as e:
            self.logger.error(f"Content extraction failed for {page.url}: {e}")
            page.mark_failed(f"Content extraction error: {e}")
        
        return page
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title with fallbacks"""
        # Try <title> tag first
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Try <h1> as fallback
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        # Try meta title
        meta_title = soup.find('meta', {'name': 'title'}) or soup.find('meta', {'property': 'og:title'})
        if meta_title and meta_title.get('content'):
            return meta_title['content'].strip()
        
        return None
    
    def _extract_clean_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract clean text content, removing navigation and boilerplate"""
        # Create a copy to avoid modifying original
        content_soup = soup.__copy__()
        
        # Remove unwanted elements
        unwanted_tags = [
            'script', 'style', 'nav', 'header', 'footer', 
            'aside', 'noscript', 'iframe', 'object', 'embed',
            # Common class/id patterns for navigation and ads
            'button', 'input', 'select', 'textarea', 'form'
        ]
        
        for tag_name in unwanted_tags:
            for element in content_soup.find_all(tag_name):
                element.decompose()
        
        # Skip aggressive class/ID removal for now - let's see if this fixes the issue
        # TODO: Re-enable with more targeted patterns later
        
        # # Remove elements with specific unwanted class/id patterns (more targeted)
        # unwanted_patterns = [
        #     r'^nav$', r'^menu$', r'^sidebar$', r'^footer$', r'^header$',
        #     r'advertisement', r'\bad\b', r'banner', r'popup',
        #     r'cookie', r'consent', r'social-share', r'breadcrumb'
        # ]
        # 
        # for pattern in unwanted_patterns:
        #     # Remove by class (exact match or word boundaries)
        #     for element in content_soup.find_all(class_=re.compile(pattern, re.I)):
        #         element.decompose()
        #     # Remove by id (exact match or word boundaries)
        #     for element in content_soup.find_all(id=re.compile(pattern, re.I)):
        #         element.decompose()
        
        # Remove comments
        for comment in content_soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Try to find main content area with improved fallback strategy
        main_content = (
            content_soup.find('main') or
            content_soup.find('article') or
            content_soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
            content_soup.find('div', id=re.compile(r'content|main|body', re.I)) or
            content_soup.find('body') or
            content_soup
        )

        # If main content area has no text, fall back to body directly
        if main_content and len(main_content.get_text(strip=True)) == 0:
            self.logger.debug("Main content area is empty, falling back to body")
            main_content = content_soup.find('body') or content_soup
        
        if main_content:
            # Extract text and clean whitespace
            text = main_content.get_text(separator=' ', strip=True)
            self.logger.debug(f"Raw extracted text length: {len(text)}")
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text)
            self.logger.debug(f"After normalization length: {len(text)}")
            # Remove very short content (likely navigation remnants)
            if len(text.strip()) > 50:
                self.logger.debug(f"Clean text extraction successful: {len(text)} characters")
                return text.strip()
            else:
                self.logger.debug(f"Clean text too short: {len(text)} characters")
        else:
            self.logger.debug("No main content area found")
        
        return None
    
    def _convert_to_markdown(self, soup: BeautifulSoup) -> Optional[str]:
        """Convert HTML to clean markdown"""
        try:
            # Create a copy and clean it similar to text extraction
            markdown_soup = soup.__copy__()
            
            # Remove unwanted elements (same as clean text but preserve more structure)
            unwanted_tags = [
                'script', 'style', 'nav', 'header', 'footer', 
                'aside', 'noscript', 'iframe', 'object', 'embed'
            ]
            
            for tag_name in unwanted_tags:
                for element in markdown_soup.find_all(tag_name):
                    element.decompose()
            
            # Try to find main content for markdown conversion with improved fallback
            main_content = (
                markdown_soup.find('main') or
                markdown_soup.find('article') or
                markdown_soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
                markdown_soup.find('body') or
                markdown_soup
            )

            # If main content area has no text, fall back to body directly
            if main_content and len(main_content.get_text(strip=True)) == 0:
                main_content = markdown_soup.find('body') or markdown_soup
            
            if main_content:
                # Convert to markdown
                markdown = self.html_converter.handle(str(main_content))
                
                # Clean up markdown
                markdown = self._clean_markdown(markdown)
                
                if len(markdown.strip()) > 50:
                    return markdown.strip()
            
        except Exception as e:
            self.logger.debug(f"Markdown conversion failed: {e}")
        
        return None
    
    def _clean_markdown(self, markdown: str) -> str:
        """Clean up converted markdown"""
        # Remove excessive empty lines
        markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
        
        # Remove lines with only whitespace
        lines = []
        for line in markdown.split('\n'):
            stripped = line.strip()
            if stripped or (lines and lines[-1].strip()):  # Keep empty lines if previous line had content
                lines.append(line)
        
        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()
        
        return '\n'.join(lines)
    
    
    def handle_error(self, page: Page, error: Exception, job: CrawlJob) -> ErrorAction:
        """Handle extraction errors"""
        if isinstance(error, (AttributeError, TypeError)):
            # Likely HTML parsing issues - skip
            return ErrorAction.SKIP
        elif isinstance(error, MemoryError):
            # Content too large - skip
            self.logger.warning(f"Content too large for {page.url}")
            return ErrorAction.SKIP
        else:
            # Other errors - retry once
            return ErrorAction.RETRY