# Analysis Stage Testing Plan

## Overview
This testing plan will help you verify that the new content analysis stage correctly extracts business intelligence from university websites, including contacts, page classification, and content indicators.

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

## Success Criteria

✅ **Analysis Integration**: Pages show `ANALYZED` status  
✅ **Contact Extraction**: Email addresses found and counted  
✅ **Page Classification**: Logical page types assigned  
✅ **Business Intelligence**: Content indicators populated  
✅ **Export Enhancement**: New analysis columns in CSV  
✅ **Performance**: Analysis doesn't significantly slow crawling

The analysis stage should provide actionable business intelligence that helps identify partnership opportunities, research collaborations, and key contacts at target universities.