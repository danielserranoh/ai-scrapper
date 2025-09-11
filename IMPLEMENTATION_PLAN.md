# Implementation Roadmap

## Phase 1: Foundation (Week 1)
**Goal**: Basic working pipeline with URL discovery and fetching

### Core Components
1. **Project structure**
   ```
   ai-scrapper/
   ├── config.py              # Configuration management
   ├── models/                # Data models
   │   ├── __init__.py
   │   ├── job.py            # CrawlJob, PipelineState
   │   ├── page.py           # Page, Link models  
   │   └── analytics.py      # SiteMetrics, SubdomainAnalytics
   ├── pipeline/             # Pipeline stages
   │   ├── __init__.py
   │   ├── base.py           # Base pipeline stage
   │   ├── discovery.py      # URL discovery stage
   │   ├── fetcher.py        # HTTP fetching stage
   │   └── manager.py        # Pipeline orchestration
   ├── storage/              # Data persistence
   │   ├── __init__.py
   │   ├── database.py       # SQLite operations
   │   └── checkpoints.py    # Recovery state management
   └── main.py               # Entry point
   ```

2. **Basic models** (models/job.py, models/page.py)
3. **URL discovery stage** (pipeline/discovery.py)
4. **HTTP fetching stage** (pipeline/fetcher.py)
5. **Basic checkpointing** (storage/checkpoints.py)
6. **CLI interface** (main.py)

### Success Criteria
- Crawl a small university site (< 1000 pages)
- Generate basic metrics (page count, subdomain list)
- Survive and recover from network interruptions

## Phase 2: Intelligence (Week 2)
**Goal**: Add content extraction and adaptive behavior

### Enhanced Components
1. **Content extraction stage** (pipeline/extractor.py)
   - BeautifulSoup for basic HTML parsing
   - Crawl4AI fallback for JS-heavy pages
   - Content cleaning and markdown conversion

2. **Analysis stage** (pipeline/analyzer.py)
   - Contact extraction (emails, social media)
   - URL structure analysis
   - Asset categorization

3. **Adaptive rate limiting** (pipeline/fetcher.py enhancement)
   - Dynamic delay adjustment
   - Blocking detection and response
   - Exponential backoff

4. **Enhanced checkpointing**
   - Stage-level recovery
   - Failed URL retry strategies
   - Progress monitoring

### Success Criteria
- Extract contacts and social media handles
- Handle rate limiting gracefully
- Generate structured analytics

## Phase 3: Production Ready (Week 3)
**Goal**: Export system and robustness

### Final Components
1. **Export system** (exporters/)
   - CSV exporter for spreadsheet analysis
   - JSON exporter for programmatic access
   - Report templates

2. **Advanced analytics**
   - Subdomain-level breakdowns
   - Link relationship analysis
   - Content categorization

3. **Error handling and monitoring**
   - Comprehensive logging
   - Error classification and reporting
   - Performance metrics

4. **Configuration management**
   - University-specific settings
   - Crawling policy templates
   - Export customization

### Success Criteria
- Process large university sites (50K+ pages)
- Generate actionable business intelligence reports
- Run reliably for 24-hour crawling sessions

## Development Approach

### Start Simple
Begin with basic pipeline skeleton that can:
- Discover URLs from a starting domain
- Fetch HTML content with politeness
- Store basic page metadata
- Resume from interruptions

### Progressive Enhancement
Add functionality incrementally:
- Content extraction → Contact detection → Analytics → Exports

### Testing Strategy
- Unit test each pipeline stage independently
- Integration test with small university sites
- Load test with rate limiting scenarios
- Recovery test with simulated failures

## Key Implementation Notes

### Pipeline Stage Interface
Each stage should implement:
```python
class PipelineStage:
    def process(self, item: Any) -> Any:
        # Process single item
        pass
    
    def handle_error(self, item: Any, error: Exception) -> ErrorAction:
        # Decide retry/skip/fail strategy
        pass
```

### Checkpointing Strategy
- Save state after each processed item
- Store metadata: job_id, stage, timestamp, item_count
- Enable resume from any stage with validation

### Error Classification
- **Retryable**: Network timeouts, temporary rate limiting
- **Skippable**: Content extraction failures, invalid URLs
- **Fatal**: Configuration errors, storage failures

This phased approach ensures we have a working system quickly while building toward full functionality.