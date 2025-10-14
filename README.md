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
   python main.py resume job_stanford_edu_24091412
   ```

4. **Check status:**
   ```bash
   python main.py status
   python main.py status job_stanford_edu_24091412
   ```

5. **Export results:**
   ```bash
   python main.py export job_stanford_edu_24091412 --csv
   python main.py export job_stanford_edu_24091412 --json
   ```

6. **Analyze results:**
   ```bash
   python main.py get-report job_stanford_edu_24091412
   ```

## What It Does

- **Bot protection handling**: Automatic detection and browser fallback for Radware, Cloudflare, hCaptcha, reCAPTCHA
- **Hybrid fetching**: Fast HTTP requests for normal sites, browser automation for bot-protected/JS-heavy sites
- **Content quality tracking**: 0-1 scoring system with extraction method transparency
- **Advanced URL structure analysis**: Pattern recognition, academic year extraction, path analysis
- **Intelligent asset categorization**: Documents, presentations, media, code repositories (8 categories)
- **Robust contact extraction**: Emails, social media handles with department mapping, handles non-standard page layouts
- **Comprehensive business intelligence**: Funding, collaboration, tech transfer, semantic analysis
- **Granular page classification**: Main types + subtypes (faculty profiles, research centers, etc.)
- **Semantic content analysis**: Academic disciplines, research methods, institutional roles
- **Enhanced rate limiting**: Dynamic adaptation, blocking detection, graceful degradation
- **Smart content extraction**: Dual-path extraction (Crawl4AI + BeautifulSoup) with quality scoring
- **Production-ready exports**: CSV/JSON with extraction metadata and quality metrics
- **Real-time monitoring**: Progress tracking with speed, ETA, and quality statistics

## Architecture

Pipeline-based processing with recovery capabilities:
1. **URL Discovery** → 2. **Fetch** → 3. **Extract** → 4. **Analyze** → 5. **Store** → 6. **Export**

## Key Features

### 🤖 Bot Protection & Browser Automation (v3.0 - NEW!)
- **Automatic Bot Detection**: Identifies Radware, Cloudflare, hCaptcha, reCAPTCHA challenges
- **Seamless Browser Fallback**: Crawl4AI + Playwright integration for bot-protected sites
- **Hybrid Fetching Strategy**: Fast requests (95%+) with browser fallback when needed
- **Memory Efficient**: Lazy browser initialization, automatic restarts every 100 fetches
- **Quality Monitoring**: Track extraction method and content quality (0-1 score)

### 🎯 Enhanced Business Intelligence (v2.0)
- **Advanced URL Structure Analysis**: Pattern recognition for faculty profiles, research projects, department pages
- **Intelligent Asset Categorization**: 8 asset types including documents, presentations, media, code
- **Semantic Content Analysis**: Academic disciplines, research methods, institutional roles detection
- **Enhanced Page Classification**: Main types + granular subtypes for precise categorization

### 🛡️ Production-Ready Crawling
- **Enhanced Rate Limiting**: Dynamic delay adjustment based on response times and server conditions
- **Blocking Detection & Mitigation**: 403/429 detection, rate limit headers analysis, graceful degradation
- **4-Level Severity System**: normal → limited → throttled → blocked with appropriate responses
- **Adaptive Performance**: Timeout adjustment and recovery strategies

### 📊 Comprehensive Analytics
- **Business Intelligence Extraction**: Funding, collaboration, tech transfer indicators
- **Robust Contact Discovery**: Automated email and social media extraction with context, handles diverse page layouts
- **Academic Intelligence**: Research focus, methodologies, institutional structure analysis
- **Asset Intelligence**: Downloadable resource categorization and business value assessment

### 🔧 Technical Excellence
- **Modern CLI**: Click-based interface with clear command separation
- **Recovery System**: Resume from any failure point with enhanced checkpointing
- **Pipeline-aware Architecture**: Maintainable code with clear stage progression
- **Dual Extraction Paths**: Crawl4AI markdown (browser) vs BeautifulSoup (fast) with automatic selection
- **Quality Scoring**: 0-1 content quality metric based on structure, length, and formatting
- **Extensible Export System**: Pluggable format adapters (CSV, JSON) with extraction metadata
- **Enhanced Exports**: Include extraction_method, browser_fetched, markdown_quality fields
- **Clean Data Organization**: Separate crawling outputs from business intelligence reports
- **File-based Storage**: Simple JSON persistence optimized for development and deployment
- **Real-time Progress**: Enhanced dashboard with speed, ETA, quality stats, and queue status at each checkpoint

## Export System

### Data Exports (Crawling Results)
```bash
# Export crawling data to CSV format
python main.py export job_id --csv

# Export crawling data to JSON format
python main.py export job_id --json

# Export to multiple formats
python main.py export job_id --csv --json
```

**Output Location**: `data/output/`
- `{domain}-pages-{timestamp}.csv/json` - Complete page data with analysis results
- `{domain}-contacts-{timestamp}.csv/json` - Extracted contacts and social profiles

### Business Intelligence Reports
```bash
# Generate comprehensive BI reports
python main.py get-report job_id
```

**Output Location**: `bi_reports/`
- Executive summaries and strategic insights
- Sales intelligence and opportunity analysis
- Subdomain and organizational structure analysis
- Technology stack and competitive intelligence

### Export Architecture
- **Extensible Design**: Easy to add new formats (xlsx, md, txt)
- **Database Ready**: Exporter pattern supports future database integration
- **Clean Separation**: Raw data vs business intelligence
- **Format Agnostic**: Same data, multiple output formats

## Configuration

Edit `config.py` for crawling parameters:
- Enhanced rate limiting settings (response time thresholds, blocking detection)
- Content filters and analysis thresholds
- Asset categorization preferences
- Export options and semantic analysis configuration
- Recovery policies and checkpoint intervals
- Progress reporting frequency (`checkpoint_interval` - default: every 100 URLs)

## Testing

Run the comprehensive testing suite:
```bash
# See TESTING_PLAN.md for complete testing instructions
python main.py crawl cs.stanford.edu --max-pages 10 --verbose
```

## Development

See `CLAUDE.md` for development guidelines, `PROJECT_BRIEF.md` for technical specifications, and `TESTING_PLAN.md` for validation procedures.