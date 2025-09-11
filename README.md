# University Web Crawler

A business intelligence tool for extracting comprehensive information from university websites.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run basic crawl:**
   ```bash
   python main.py crawl university.edu
   ```

3. **Resume failed job:**
   ```bash
   python main.py resume job_20240101_120000
   ```

4. **Check status:**
   ```bash
   python main.py status
   python main.py status job_20240101_120000
   ```

5. **Export results:**
   ```bash
   python main.py export job_20240101_120000 --format csv
   ```

## What It Does

- **Analyzes website structure**: Pages, subdomains, assets, link relationships
- **Extracts contact information**: Emails, social media handles by department  
- **Creates clean content**: HTML to Markdown for AI knowledge bases
- **Generates business reports**: CSV exports for sales team analysis

## Architecture

Pipeline-based processing with recovery capabilities:
1. **URL Discovery** → 2. **Fetch** → 3. **Extract** → 4. **Analyze** → 5. **Store** → 6. **Export**

## Key Features

- **Modern CLI**: Click-based interface with improved command structure
- **Adaptive crawling**: Intelligent rate limiting and blocking detection  
- **Recovery system**: Resume from any failure point with checkpointing
- **DRY Architecture**: Centralized utilities and error handling
- **Content cleaning**: BeautifulSoup + html2text extraction
- **Export flexibility**: Multiple formats (CSV, JSON, etc.)
- **File-based Storage**: Simple JSON persistence for rapid development

## Configuration

Edit `config.py` for crawling parameters:
- Rate limiting settings
- Content filters  
- Export options
- Recovery policies

## Development

See `CLAUDE.md` for development guidelines and `PROJECT_BRIEF.md` for full technical specifications.