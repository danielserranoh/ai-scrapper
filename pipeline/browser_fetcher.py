"""
Browser-based fetching using Crawl4AI for bot-protected and JS-heavy sites
"""

import asyncio
import logging
from typing import Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from models.page import Page, PageStatus
from models.job import CrawlJob
from config import CrawlConfig
from utils.time import get_current_time


class BrowserFetcher:
    """Handles browser-based fetching with Crawl4AI"""

    def __init__(self, config: CrawlConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.crawler: Optional[AsyncWebCrawler] = None
        self.fetch_count = 0
        self.max_browser_fetches = getattr(config, 'browser_restart_interval', 100)

        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )

    async def initialize(self):
        """Initialize browser instance"""
        if self.crawler is None:
            self.crawler = AsyncWebCrawler(config=self.browser_config)
            await self.crawler.__aenter__()
            self.logger.info("Browser fetcher initialized")

    async def shutdown(self):
        """Clean shutdown of browser"""
        if self.crawler:
            await self.crawler.__aexit__(None, None, None)
            self.crawler = None
            self.logger.info("Browser fetcher shutdown")

    async def fetch(self, page: Page, job: CrawlJob) -> Page:
        """Fetch page using browser automation"""
        try:
            await self.initialize()

            # Get browser timeout from config (with fallback)
            browser_timeout = getattr(self.config, 'browser_timeout', self.config.request_timeout)

            # Configure crawl run
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,  # Always fetch fresh
                wait_for_images=False,  # Speed up - we don't need images
                process_iframes=False,  # Skip iframes for now
                wait_until="networkidle",  # Wait for JS to load
                timeout=browser_timeout * 1000,  # Convert to ms
                remove_overlay_elements=True,  # Remove popups
            )

            self.logger.info(f"Fetching with browser: {page.url}")
            page.status = PageStatus.FETCHING

            # Execute crawl
            result = await self.crawler.arun(
                url=page.url,
                config=run_config
            )

            # Process result
            if result.success:
                page.html_content = result.html
                page.status_code = result.status_code
                page.content_type = "text/html"  # Browser always returns HTML
                page.content_length = len(result.html) if result.html else 0
                page.status = PageStatus.FETCHED
                page.fetched_at = get_current_time()

                # Store Crawl4AI-specific content for Phase 3B
                if hasattr(result, 'cleaned_html') and result.cleaned_html:
                    page.cleaned_html = result.cleaned_html
                if hasattr(result, 'markdown') and result.markdown:
                    page.crawl4ai_markdown = result.markdown

                # Mark extraction method
                page.extraction_method = "browser"
                page.browser_fetched = True

                self.logger.info(
                    f"Browser fetch successful: {page.url} "
                    f"({page.content_length} bytes)"
                )
            else:
                error_msg = result.error_message if hasattr(result, 'error_message') else "Unknown browser fetch error"
                page.mark_failed(f"Browser fetch failed: {error_msg}")
                self.logger.error(f"Browser fetch failed for {page.url}: {error_msg}")

            self.fetch_count += 1

            # Periodically restart browser to prevent memory leaks
            if self.fetch_count >= self.max_browser_fetches:
                self.logger.info(f"Restarting browser after {self.fetch_count} fetches")
                await self.shutdown()
                self.fetch_count = 0

        except Exception as e:
            page.mark_failed(f"Browser fetch error: {str(e)}")
            self.logger.error(f"Browser fetch error for {page.url}: {e}", exc_info=True)

        return page

    def fetch_sync(self, page: Page, job: CrawlJob) -> Page:
        """Synchronous wrapper for fetch"""
        return asyncio.run(self.fetch(page, job))


class BrowserFetcherPool:
    """Manages a pool of browser fetchers for concurrent requests"""

    def __init__(self, config: CrawlConfig, pool_size: int = 1):
        self.config = config
        self.pool_size = pool_size
        self.fetchers = [BrowserFetcher(config) for _ in range(pool_size)]
        self.current_index = 0
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_fetcher(self) -> BrowserFetcher:
        """Round-robin fetcher selection"""
        fetcher = self.fetchers[self.current_index]
        self.current_index = (self.current_index + 1) % self.pool_size
        return fetcher

    def fetch(self, page: Page, job: CrawlJob) -> Page:
        """Fetch using next available fetcher"""
        fetcher = self.get_fetcher()
        return fetcher.fetch_sync(page, job)

    async def shutdown_all(self):
        """Shutdown all browser instances"""
        for fetcher in self.fetchers:
            await fetcher.shutdown()
