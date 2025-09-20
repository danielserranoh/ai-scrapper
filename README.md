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

- **Advanced URL structure analysis**: Pattern recognition, academic year extraction, path analysis
- **Intelligent asset categorization**: Documents, presentations, media, code repositories (8 categories)
- **Robust contact extraction**: Emails, social media handles with department mapping, handles non-standard page layouts
- **Comprehensive business intelligence**: Funding, collaboration, tech transfer, semantic analysis
- **Granular page classification**: Main types + subtypes (faculty profiles, research centers, etc.)
- **Semantic content analysis**: Academic disciplines, research methods, institutional roles
- **Enhanced rate limiting**: Dynamic adaptation, blocking detection, graceful degradation
- **Smart content extraction**: HTML to Markdown conversion with fallback strategies for diverse page structures
- **Production-ready exports**: CSV/JSON with parsed and cleaned data
- **Business Intelligence reports**: Comprehensive business intelligence analysis reports

## Architecture

Pipeline-based processing with recovery capabilities:
1. **URL Discovery** → 2. **Fetch** → 3. **Extract** → 4. **Analyze** → 5. **Store** → 6. **Export**

## Key Features

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
- **Smart Content Extraction**: BeautifulSoup + html2text with fallback strategies for diverse page structures
- **Extensible Export System**: Pluggable format adapters (CSV, JSON, future: xlsx, md, txt)
- **Clean Data Organization**: Separate crawling outputs from business intelligence reports
- **File-based Storage**: Simple JSON persistence optimized for development and deployment
- **Real-time Progress**: Enhanced dashboard with speed, ETA, and queue status at each checkpoint

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