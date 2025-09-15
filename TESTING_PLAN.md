# University Web Crawler - Comprehensive Testing Plan

## Overview
This testing plan covers the complete university web crawler system including the enhanced rate limiting, advanced URL structure analysis, asset categorization, and comprehensive content analysis features. The plan is designed to verify both existing functionality and new enhancements for business intelligence extraction.

## Test Setup

### 1. Prepare Test Environment
```bash
# Ensure you're in the project directory
cd /Users/danielserrano/Tools/ai-scrapper

# Install dependencies (if needed)
pip install -r requirements.txt

# Create output directory
mkdir -p data/output
```

### 2. Quick Unit Test (30 seconds)
First, let's run our isolated test to verify the analysis stage works:

```bash
python test_analyzer.py
```

**Expected Results:**
- Should show page classification as "research"
- Should extract 1 email: `jane.smith@university.edu`
- Should find 3 social media handles
- Should detect funding references and technology transfer indicators
- Status should be `PageStatus.ANALYZED`

---

# ENHANCED FEATURES TESTING (v2.0)

## Test Suite A: Enhanced Rate Limiting System

### A1: Dynamic Delay Adjustment Test
**Duration**: 10-15 minutes  
**Objective**: Verify response time-based rate limiting

```bash
# Test adaptive rate limiting
python main.py crawl cs.stanford.edu --max-pages 25 --verbose
```

**Monitor Console Output For**:
- Response times logged (e.g., "Successfully fetched ... (0.75s, normal)")
- Severity levels: normal → limited → throttled → blocked
- Adaptive delay adjustments

**Success Criteria**:
- ✅ Response times shown for each request
- ✅ Severity escalation when appropriate
- ✅ No crawler crashes from rate limiting

### A2: Blocking Detection Test
**Duration**: 5-10 minutes  
**Objective**: Test graceful handling of HTTP errors

```bash
# Test with a site that may have some blocking
python main.py crawl news.stanford.edu --max-pages 20 --verbose
```

**Look For**:
- HTTP 403/429 errors handled gracefully
- Rate limiter adjusts delays after errors
- Crawler continues with other pages

**Success Criteria**:
- ✅ HTTP errors don't crash the system
- ✅ Blocking severity reported accurately
- ✅ Failed pages tracked but don't stop crawl

### A3: Rate Limiter Statistics Test
**Duration**: 2 minutes  
**Objective**: Verify enhanced statistics reporting

```bash
# After any crawl, check the final statistics
python main.py status [job_id]
```

**Expected Statistics**:
- Per-domain rate limiting status
- Blocking severity breakdown (normal/limited/throttled/blocked)
- Average response times

**Success Criteria**:
- ✅ Detailed rate limiter statistics displayed
- ✅ Severity summary shows distribution
- ✅ Performance metrics included

## Test Suite B: Advanced URL Structure Analysis

### B1: URL Pattern Recognition Test
**Duration**: 15-20 minutes  
**Objective**: Test enhanced URL pattern classification

```bash
# Crawl a university with diverse URL structures
python main.py crawl cs.stanford.edu --max-pages 30 --verbose
```

**Manual Verification**:
1. Export results: `python main.py export [job_id] --format json`
2. Check `analysis_results.url_structure.url_pattern` field
3. Verify pattern classifications:

| URL Type | Expected Pattern |
|----------|------------------|
| `/people/john-doe` | `faculty_profile` |
| `/research/ai-lab` | `research_project` |
| `/departments/cs` | `department_page` |
| `/courses/cs101` | `course_page` |
| `/news/2024/article` | `news_article` |

**Success Criteria**:
- ✅ URL patterns correctly identified (≥85% accuracy)
- ✅ Path depth calculated accurately
- ✅ Academic years extracted when present

### B2: URL Structure Data Test
**Duration**: 5 minutes  
**Objective**: Verify URL structure data completeness

**Check JSON Export For**:
```json
"url_structure": {
  "path_depth": 3,
  "url_pattern": "faculty_profile",
  "academic_year": "2024",
  "file_extension": null
}
```

**Success Criteria**:
- ✅ Path depth matches actual URL structure
- ✅ Academic years extracted from date-based URLs
- ✅ File extensions detected correctly

## Test Suite C: Asset Categorization System

### C1: Asset Detection Test
**Duration**: 10-15 minutes  
**Objective**: Test linked asset detection and categorization

```bash
# Crawl pages likely to have downloadable content
python main.py crawl cs.stanford.edu --max-pages 20 --verbose
```

**Asset Types to Verify**:
- **Documents**: PDFs, syllabi, handbooks (.pdf, .doc, .txt)
- **Presentations**: Lecture slides (.ppt, .pptx)
- **Media**: Images, photos (.jpg, .png, .gif)
- **Archives**: Downloads (.zip, .tar)
- **Code**: Source files (.py, .js, .html)

**Success Criteria**:
- ✅ Asset breakdown populated with counts
- ✅ linked_assets_count > 0 for content-rich pages
- ✅ Asset categorization accuracy ≥80%

### C2: Asset Intelligence Test
**Duration**: 5 minutes  
**Objective**: Verify business value of asset data

**Check Export For**:
```json
"asset_breakdown": {
  "documents": 5,
  "presentations": 2,
  "media": 8,
  "code": 1
}
```

**Business Intelligence Value**:
- Document counts indicate content richness
- Presentation files suggest educational resources
- Code repositories indicate technical depth

**Success Criteria**:
- ✅ Asset breakdown provides actionable insights
- ✅ Categories align with university content types
- ✅ Counts help assess institutional resources

## Test Suite D: Enhanced Page Classification

### D1: Page Type and Subtype Test
**Duration**: 15-20 minutes  
**Objective**: Test improved page classification granularity

```bash
# Test with diverse university content
python main.py crawl cs.stanford.edu --max-pages 25 --verbose
```

**Verify Classification Accuracy**:

| Page Type | Subtypes | Example URLs |
|-----------|----------|--------------|
| `faculty` | `individual_profile`, `faculty_listing` | `/people/jane-doe`, `/faculty` |
| `department` | `department_home`, `program_page` | `/cs`, `/programs/phd` |
| `research` | `research_center`, `research_project` | `/labs/ai`, `/research/project1` |
| `admissions` | `undergraduate`, `graduate` | `/admissions/undergrad` |
| `academics` | `course_catalog`, `degree_requirements` | `/courses`, `/requirements` |
| `student_life` | `housing`, `activities` | `/housing`, `/clubs` |

**Success Criteria**:
- ✅ Main types classified correctly (≥90% accuracy)
- ✅ Subtypes provide meaningful granularity
- ✅ New categories (academics, student_life) work

### D2: Semantic Content Analysis Test
**Duration**: 10 minutes  
**Objective**: Test semantic pattern detection

**Check JSON Export For**:
```json
"semantic_indicators": {
  "academic_focus": 3,
  "research_methods": 1,
  "institutional_roles": 2,
  "academic_activities": 1
}
```

**Semantic Categories**:
- **Academic Focus**: Disciplines (AI, engineering, medicine)
- **Research Methods**: Methodologies (experimental, survey)
- **Institutional Roles**: Positions (dean, professor, director)
- **Academic Activities**: Events (conference, workshop, seminar)

**Success Criteria**:
- ✅ Semantic indicators populated on relevant pages
- ✅ Academic disciplines correctly identified
- ✅ Content context detected accurately

## Test Suite E: Enhanced Export and Data Quality

### E1: Enhanced CSV Export Test
**Duration**: 5 minutes  
**Objective**: Verify new analysis fields in CSV

```bash
python main.py export [job_id] --format csv
```

**New CSV Columns to Verify**:
- `page_subtype`
- `url_pattern`
- `path_depth`
- `academic_year`
- `linked_assets_count`
- `asset_breakdown_summary`
- `semantic_indicators_summary`

**Success Criteria**:
- ✅ All new columns present and populated
- ✅ Data properly formatted and readable
- ✅ Business intelligence value evident

### E2: Complete JSON Export Test
**Duration**: 5 minutes  
**Objective**: Test full enhanced data structure

```bash
python main.py export [job_id] --format json
```

**Verify Complete Structure**:
```json
{
  "analysis_results": {
    "page_type": "faculty",
    "page_subtype": "individual_profile",
    "url_structure": { ... },
    "linked_assets_count": 3,
    "asset_breakdown": { ... },
    "semantic_indicators": { ... }
  }
}
```

**Success Criteria**:
- ✅ JSON structure validates correctly
- ✅ All enhanced fields populated
- ✅ Data relationships logical and complete

## Test Suite F: Integration and Performance

### F1: Full Pipeline Integration Test
**Duration**: 20-30 minutes  
**Objective**: Test complete enhanced pipeline

```bash
# Large scale test with all features
python main.py crawl www.stanford.edu --max-pages 50 --verbose
```

**Monitor Throughout**:
- Rate limiting adaptation
- URL pattern recognition
- Asset detection
- Page classification
- Performance metrics

**Success Criteria**:
- ✅ All features work together seamlessly
- ✅ No performance degradation >20%
- ✅ Enhanced data quality maintained at scale

### F2: Recovery and Checkpoint Test
**Duration**: 15 minutes  
**Objective**: Test enhanced features with recovery

```bash
# Start crawl
python main.py crawl cs.stanford.edu --max-pages 30

# Interrupt after 15 pages (Ctrl+C)
# Resume
python main.py resume [job_id]
```

**Success Criteria**:
- ✅ Enhanced analysis continues after resume
- ✅ All enhanced data preserved
- ✅ No feature regression in recovered session

## Enhanced Success Criteria Checklist

### Core Functionality (Must Pass)
- [ ] Enhanced rate limiting prevents blocking
- [ ] URL structure analysis accuracy ≥85%
- [ ] Asset categorization accuracy ≥80%
- [ ] Page type classification accuracy ≥90%
- [ ] Export data includes all enhanced fields
- [ ] Performance impact ≤20% vs baseline

### Business Intelligence Quality (Should Pass)
- [ ] Faculty contact extraction rate >70%
- [ ] Research funding detection >20% on research pages
- [ ] Asset intelligence provides actionable insights
- [ ] Semantic analysis identifies academic context
- [ ] URL patterns help understand site structure

### Advanced Features (Nice to Have)
- [ ] Academic year extraction from URLs
- [ ] Subtype classification adds value
- [ ] Rate limiter statistics help optimization
- [ ] Asset breakdown guides content assessment
- [ ] Semantic indicators support targeting

## Quick Validation Commands

After completing tests, run these for quick validation:

```bash
# Get latest job
JOB_ID=$(python main.py list | grep "job_" | head -1 | awk '{print $1}')

# Export and analyze
python main.py export $JOB_ID --format csv
CSV_FILE=$(ls data/output/${JOB_ID}_pages_*.csv | head -1)

# Enhanced analysis
echo "=== ENHANCED CRAWLER VALIDATION ==="
echo "Job ID: $JOB_ID"
echo "Total pages: $(tail -n +2 $CSV_FILE | wc -l)"
echo "Faculty pages: $(grep -c 'faculty' $CSV_FILE)"
echo "Research pages: $(grep -c 'research' $CSV_FILE)" 
echo "Pages with assets: $(awk -F',' 'NR>1 && $NF>0 {count++} END {print count+0}' $CSV_FILE)"
echo "Unique URL patterns: $(awk -F',' 'NR>1 {print $X}' $CSV_FILE | sort | uniq | wc -l)"
echo "=== VALIDATION COMPLETE ==="
```

## Full Pipeline Tests

### Test 1: Small University Site (5-10 minutes)
Let's test with a small, well-structured university site:

```bash
# Start a crawl with limited pages for testing
python main.py crawl cs.stanford.edu --max-pages 50 --delay 2 --verbose
```

**What to expect:**
- The crawler will discover URLs, fetch pages, extract content, and **analyze** them
- You'll see log messages about analysis happening
- Process should complete in 5-10 minutes with 50 pages max

**Monitor progress:**
```bash
# In another terminal, check status
python main.py status

# Or check current job status
python main.py status current
```

### Test 2: Faculty-Rich Department (10-15 minutes)
Test with a department likely to have lots of faculty contacts:

```bash
# Try a computer science or engineering department
python main.py crawl ece.cmu.edu --max-pages 100 --delay 1.5 --verbose
```

**What to expect:**
- More faculty pages = more contact extraction
- Should classify pages as faculty, research, department types
- Higher email and social media extraction rates

## Results Analysis

### 1. Check Job Status and Progress
```bash
# List all jobs
python main.py list

# Get detailed status of latest job
python main.py status [job_id_from_list]
```

### 2. Export and Examine Results

#### CSV Export (Business Intelligence Focus)
```bash
# Export results to CSV with analysis data
python main.py export [job_id] --format csv
```

**Look for these new columns in the CSV:**
- `analyzed_at`: Timestamp when analysis completed
- `page_type`: faculty, research, department, contact, etc.
- `funding_references`: Count of funding/grant mentions
- `collaboration_indicators`: Partnership mentions
- `technology_transfer`: Patent/licensing mentions  
- `industry_connections`: Corporate relationship indicators
- `emails_count`: Number of emails found on page
- `social_profiles_count`: Social media handles found

#### JSON Export (Full Details)
```bash
# Export full JSON data
python main.py export [job_id] --format json
```

**In the JSON, look for:**
- `analysis_results` field on each page object
- `analyzed_at` timestamps
- Detailed content indicators breakdown

### 3. Check Output Files
The crawler saves results in the `data/output/` directory:

```bash
# List all output files
ls -la data/output/

# Look for files like:
# - [job_id]_pages_[timestamp].csv
# - [job_id]_pages_[timestamp].json
# - [job_id]_analytics_[timestamp].json (if created)
```

## What to Look For

### 1. Contact Extraction Success
**In CSV, examine pages where:**
- `page_type` = "faculty" or "contact"
- `emails_count` > 0
- `social_profiles_count` > 0

**Sample commands to analyze:**
```bash
# Count total emails found
grep -o '[a-zA-Z0-9._%+-]\+@[a-zA-Z0-9.-]\+\.[a-zA-Z]\{2,\}' data/output/[job_id]_pages_*.csv | wc -l

# Find faculty pages
grep "faculty" data/output/[job_id]_pages_*.csv

# Find research pages with funding indicators
grep "research" data/output/[job_id]_pages_*.csv | grep -v ",0,0,0,0"
```

### 2. Page Classification Quality
Look for logical page type distribution:
- University homepages → "about" or "general"
- Faculty directories → "faculty" 
- Research labs → "research"
- Admissions pages → "admissions"
- Contact pages → "contact"

### 3. Business Intelligence Indicators
**High-value pages should show:**
- `funding_references` > 0 (NSF, NIH, grant mentions)
- `technology_transfer` > 0 (patents, licensing)  
- `collaboration_indicators` > 0 (partnerships)
- `industry_connections` > 0 (corporate relationships)

### 4. Performance Metrics
Monitor in the status output:
- **Total pages processed** vs **analyzed pages** (should be close)
- **Analysis stage completion rate** (check for failures)
- **Processing time** per page (analysis adds ~100-200ms per page)

## Expected Results by University Type

### Research Universities (Stanford, CMU, MIT)
- **High funding references**: 20-40% of research pages
- **Many faculty contacts**: 50+ emails typical
- **Technology transfer activity**: 5-15% of pages
- **Page types**: Strong faculty, research, department classification

### Liberal Arts Colleges  
- **Moderate contact density**: 10-30 emails typical
- **Page types**: More "about", "admissions" focus
- **Lower research indicators**: Limited funding references

### Community Colleges
- **Contact-heavy**: High "contact" and "admissions" page ratio
- **Lower research activity**: Minimal funding/tech transfer
- **Department focus**: Academic program pages

## Troubleshooting

### If Analysis Isn't Running
```bash
# Check if analyzer stage loads correctly
python -c "from pipeline.analyzer import ContentAnalysisStage; print('✅ Analyzer imports successfully')"

# Check full pipeline integration
python -c "from pipeline.manager import PipelineManager; from config import get_config; print('✅ Pipeline integrates analyzer')"
```

### If No Analysis Results in Export
1. **Check page status**: Look for `ANALYZED` status in CSV
2. **Check extraction first**: Ensure pages have `clean_content`  
3. **Verify content length**: Analysis requires >100 characters
4. **Check error messages**: Look for analysis errors in logs

### If Contact Extraction Seems Low
1. **Verify page types**: Faculty pages should have higher extraction
2. **Check content quality**: Some pages may have minimal text
3. **Look at specific examples**: Examine individual high-contact pages
4. **Consider obfuscation**: Some sites hide emails from crawlers

## Sample Analysis Commands

Once you have results, try these analysis commands:

```bash
# Get job ID from latest crawl
JOB_ID=$(python main.py list | grep "job_" | head -1 | cut -d' ' -f2)

# Show summary stats
echo "Analyzing job: $JOB_ID"
python main.py status $JOB_ID

# Export and analyze CSV
python main.py export $JOB_ID --format csv
CSV_FILE=$(ls data/output/${JOB_ID}_pages_*.csv | head -1)

echo "CSV Analysis:"
echo "Total pages: $(tail -n +2 $CSV_FILE | wc -l)"
echo "Analyzed pages: $(grep 'ANALYZED' $CSV_FILE | wc -l)" 
echo "Pages with emails: $(awk -F',' '$18 > 0 { count++ } END { print count+0 }' $CSV_FILE)"
echo "Faculty pages: $(grep -c 'faculty' $CSV_FILE)"
echo "Research pages: $(grep -c 'research' $CSV_FILE)"
echo "Pages with funding refs: $(awk -F',' '$20 > 0 { count++ } END { print count+0 }' $CSV_FILE)"
```

## Legacy Success Criteria (v1.0)

✅ **Analysis Integration**: Pages show `ANALYZED` status  
✅ **Contact Extraction**: Email addresses found and counted  
✅ **Page Classification**: Logical page types assigned  
✅ **Business Intelligence**: Content indicators populated  
✅ **Export Enhancement**: New analysis columns in CSV  
✅ **Performance**: Analysis doesn't significantly slow crawling

## Enhanced Success Criteria (v2.0)

✅ **Enhanced Rate Limiting**: Dynamic adaptation and blocking prevention  
✅ **URL Structure Analysis**: Pattern recognition and academic context  
✅ **Asset Categorization**: Intelligent resource classification  
✅ **Advanced Page Types**: Granular classification with subtypes  
✅ **Semantic Analysis**: Academic content understanding  
✅ **Enhanced Exports**: Comprehensive business intelligence data

---

## Testing Report Template

Use this template to document your testing results:

```markdown
# Testing Report - [Date]

## Test Environment
- Python Version: 
- Dependencies: Latest
- Test Duration: [X] hours
- Tester: [Name]

## Test Results Summary

### Enhanced Rate Limiting (Test Suite A)
- [ ] A1: Dynamic Delay Adjustment - [PASS/FAIL]
- [ ] A2: Blocking Detection - [PASS/FAIL] 
- [ ] A3: Rate Limiter Statistics - [PASS/FAIL]

### URL Structure Analysis (Test Suite B)
- [ ] B1: URL Pattern Recognition - [PASS/FAIL]
- [ ] B2: URL Structure Data - [PASS/FAIL]

### Asset Categorization (Test Suite C)
- [ ] C1: Asset Detection - [PASS/FAIL]
- [ ] C2: Asset Intelligence - [PASS/FAIL]

### Enhanced Page Classification (Test Suite D)
- [ ] D1: Page Type and Subtype - [PASS/FAIL]
- [ ] D2: Semantic Content Analysis - [PASS/FAIL]

### Export and Data Quality (Test Suite E)
- [ ] E1: Enhanced CSV Export - [PASS/FAIL]
- [ ] E2: Complete JSON Export - [PASS/FAIL]

### Integration and Performance (Test Suite F)
- [ ] F1: Full Pipeline Integration - [PASS/FAIL]
- [ ] F2: Recovery and Checkpoint - [PASS/FAIL]

## Key Findings
- Performance Impact: [X]% vs baseline
- URL Pattern Accuracy: [X]%
- Asset Detection Rate: [X]%
- Page Classification Accuracy: [X]%

## Critical Issues Found
1. [Issue 1 description]
2. [Issue 2 description]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Overall Assessment
[PASS/FAIL with rationale]
```

The enhanced crawler system should provide comprehensive business intelligence that significantly improves sales team targeting and partnership identification for university outreach.