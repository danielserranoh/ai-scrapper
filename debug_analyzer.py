#!/usr/bin/env python3
"""
Debug script to isolate the analyzer issue
"""

import json
import traceback
from models.page import Page, PageStatus  
from models.job import CrawlJob
from pipeline.analyzer import ContentAnalysisStage

def debug_analyzer():
    """Debug the analyzer with real data that failed"""
    
    # Load the problematic page data
    with open('data/output/job_20250911_233201_pages_20250911_233224.json', 'r') as f:
        pages = json.load(f)
    
    # Find the Aviad page that should have worked
    aviad_data = None
    for page_data in pages:
        if 'aviad-rubinstein' in page_data['url']:
            aviad_data = page_data
            break
    
    if not aviad_data:
        print("❌ Could not find Aviad page in data")
        return
    
    print(f"🔍 Debugging page: {aviad_data['url']}")
    print(f"Original status: {aviad_data['status']}")
    print(f"Clean content length: {len(aviad_data.get('clean_content', ''))}")
    
    # Create Page object with exact same data
    page = Page(
        url=aviad_data['url'],
        job_id=aviad_data['job_id'],
        status=PageStatus.EXTRACTED,  # Set to EXTRACTED so analyzer will process
        clean_content=aviad_data.get('clean_content'),
        html_content=aviad_data.get('html_content'),
        title=aviad_data.get('title')
    )
    
    job = CrawlJob(
        job_id=aviad_data['job_id'],
        domain='cs.stanford.edu'
    )
    
    print("\n📋 Testing analyzer with reconstructed page:")
    print(f"  Status: {page.status}")
    print(f"  Has clean content: {bool(page.clean_content)}")
    print(f"  Content preview: {page.clean_content[:100] if page.clean_content else 'None'}")
    
    # Test analyzer
    analyzer = ContentAnalysisStage()
    
    print("\n🔬 Running analysis...")
    print(f"  Should process: {analyzer.should_process(page, job)}")
    
    try:
        # Run the analysis with detailed debugging
        result_page = analyzer.process_item(page, job)
        
        print("\n✅ Analysis completed:")
        print(f"  Final status: {result_page.status}")
        print(f"  Analysis results: {result_page.analysis_results}")
        print(f"  Analyzed at: {result_page.analyzed_at}")
        print(f"  Error message: {result_page.error_message}")
        
        # Test each step manually
        print("\n🧪 Manual analysis breakdown:")
        analysis = analyzer._analyze_page_content(result_page, job)
        print(f"  Page type: {analysis.page_type}")
        print(f"  Emails found: {analysis.emails}")  
        print(f"  Social media: {analysis.social_media}")
        print(f"  Content indicators: {analysis.content_indicators}")
        
    except Exception as e:
        print("❌ Analysis failed with exception:")
        print(f"  Error: {e}")
        print("  Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    debug_analyzer()