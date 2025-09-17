# University Web Crawler - Project Brief

## Project Overview
A business intelligence tool for sales teams to extract comprehensive information from university websites. The system analyzes website structure, extracts contact information, and provides clean content for AI knowledge bases.

This document describes what the final solucion should look like, not what it could be during  development. This document should serve as the northe star, and in order to evaluate gaps of the current situation towards this final state.

## Core Objectives
1. **Website Metrics**: Analyze site size (pages, subdomains, assets) and structure
2. **Contact Extraction**: Find emails and social media handles across all departments
3. **Content Processing**: Convert HTML to clean Markdown for AI consumption
4. **Business Intelligence**: Generate reports for sales team planning

## Technical Requirements

### Architecture: Pipeline-based Processing
- **Recovery-first design**: Resume from any failure point
- **Adaptive crawling**: Intelligent rate limiting and blocking detection
- **Modular extraction**: Pluggable content processors and exporters

### Pipeline Stages
1. **URL Discovery**: Find pages and subdomains within university domain
2. **Fetch**: HTTP requests with adaptive rate limiting
3. **Extract**: Content extraction (BeautifulSoup → Crawl4AI fallback)
4. **Analyze**: Structure analysis and contact detection
5. **Store**: Data persistence with checkpointing
6. **Export**: On-demand reporting in multiple formats

### Key Features
- **Scope**: Main domain + discovered subdomains only
- **Politeness**: 1-second base delay, adaptive adjustment
- **Limits**: 200K pages max, 24-hour timeout
- **Recovery**: Resume from checkpoints after failures
- **Filtering**: Exclude date-based parametrized URLs
- **Content Priority**: Metrics > Contacts > Markdown

### Target Scale
- **Current**: 1-2 universities per week
- **Goal**: 1 university per day
- **Processing**: Batch processing, on-demand exports

## Technology Stack

### Core Libraries
- **Scrapy**: Web crawling framework with built-in politeness
- **Crawl4AI**: Advanced content extraction and cleaning
- **BeautifulSoup4**: HTML parsing fallback
- **SQLite**: Local data storage
- **pandas**: Data analysis and export

### Architecture Components
- **Python config**: Configuration management
- **Pipeline stages**: Modular processing components
- **Checkpoint system**: Recovery state management
- **Export managers**: Multiple output formats (CSV, JSON, etc.)

## Data Models

### Core Entities
- **CrawlJob**: Job metadata and configuration
- **PipelineState**: Recovery and progress tracking  
- **Page**: Individual page data and extracted content
- **SiteMetrics**: Aggregate statistics per domain/subdomain
- **Contact**: Emails and social media profiles
- **Link**: Internal/external link relationships

### Key Analytics
- **Subdomain breakdown**: Separate metrics per department
- **Social media mess**: Multiple instances per platform
- **URL structure**: SEO-based content categorization
- **Asset inventory**: Count by type (HTML, PDF, images, etc.)

## Implementation Priority
1. **Pipeline skeleton** with basic URL discovery
2. **Fetching stage** with rate limiting and error handling
3. **Checkpoint system** for recovery
4. **Content extraction** with BeautifulSoup/Crawl4AI fallback
5. **CSV export** for immediate spreadsheet analysis
6. **Enhanced analytics** and reporting

## Success Criteria
- Successfully crawl and analyze 1-2 universities per week
- Generate actionable business intelligence reports
- Provide clean content for AI knowledge base creation
- Handle university protection mechanisms gracefully
- Enable recovery from partial failures