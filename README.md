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

- **Advanced URL structure analysis**: Pattern recognition, academic year extraction, path analysis
- **Intelligent asset categorization**: Documents, presentations, media, code repositories (8 categories)
- **Enhanced contact extraction**: Emails, social media handles with department mapping  
- **Comprehensive business intelligence**: Funding, collaboration, tech transfer, semantic analysis
- **Granular page classification**: Main types + subtypes (faculty profiles, research centers, etc.)
- **Semantic content analysis**: Academic disciplines, research methods, institutional roles
- **Enhanced rate limiting**: Dynamic adaptation, blocking detection, graceful degradation
- **Creates clean content**: HTML to Markdown for AI knowledge bases
- **Production-ready exports**: CSV/JSON with comprehensive business intelligence data

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
- **Contact Discovery**: Automated email and social media extraction with context
- **Academic Intelligence**: Research focus, methodologies, institutional structure analysis
- **Asset Intelligence**: Downloadable resource categorization and business value assessment

### 🔧 Technical Excellence
- **Modern CLI**: Click-based interface with comprehensive command structure
- **Recovery System**: Resume from any failure point with enhanced checkpointing
- **Pipeline-aware Architecture**: Maintainable code with clear stage progression
- **Content Cleaning**: BeautifulSoup + html2text extraction with enhanced analysis
- **Export Flexibility**: Rich CSV/JSON exports with enhanced business intelligence fields
- **File-based Storage**: Simple JSON persistence optimized for development and deployment
- **Real-time Progress**: Enhanced dashboard with speed, ETA, and queue status at each checkpoint

## Enhanced Data Output

### CSV Export (Business Intelligence Ready)
New enhanced fields include:
- `page_subtype`: Granular classification (individual_profile, research_center, etc.)
- `url_pattern`: Recognized URL structure (faculty_profile, department_page, etc.)
- `path_depth`: URL hierarchy analysis
- `academic_year`: Extracted academic year context
- `linked_assets_count`: Number of downloadable resources
- `asset_breakdown_summary`: Asset categories and counts
- `semantic_indicators_summary`: Academic context indicators

### JSON Export (Complete Analysis)
Full analysis results include:
```json
{
  "analysis_results": {
    "page_type": "faculty",
    "page_subtype": "individual_profile", 
    "url_structure": {
      "path_depth": 3,
      "url_pattern": "faculty_profile",
      "academic_year": "2024"
    },
    "linked_assets_count": 5,
    "asset_breakdown": {
      "documents": 3,
      "presentations": 1,
      "media": 1
    },
    "semantic_indicators": {
      "academic_focus": 2,
      "research_methods": 1,
      "institutional_roles": 1
    }
  }
}
```

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