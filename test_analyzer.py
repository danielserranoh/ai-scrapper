#!/usr/bin/env python3
"""
Test script for the content analysis stage
"""

from models.job import CrawlJob
from models.page import Page, PageStatus
from pipeline.analyzer import ContentAnalysisStage


def test_content_analyzer():
    """Test the content analysis stage with sample data"""
    
    # Create test job
    job = CrawlJob(
        job_id="test_job_123",
        domain="university.edu"
    )
    
    # Create test page with content
    page = Page(
        url="https://engineering.university.edu/faculty/dr-smith",
        job_id=job.job_id,
        status=PageStatus.EXTRACTED,
        title="Dr. Jane Smith - Computer Science Department",
        clean_content="""
        Dr. Jane Smith
        Professor of Computer Science
        
        Contact Information:
        Email: jane.smith@university.edu
        Office: Engineering Building 205
        Phone: (555) 123-4567
        
        Research Interests:
        - Machine Learning and AI
        - Natural Language Processing  
        - Computer Vision
        
        Current Projects:
        Working on NSF-funded research into deep learning applications.
        Collaborating with industry partners on AI commercialization.
        
        Publications:
        Over 50 publications in top-tier conferences.
        
        Social Media:
        Twitter: @DrJaneSmith
        LinkedIn: linkedin.com/in/jane-smith-cs
        
        Recent News:
        Dr. Smith received a $2M grant from the National Science Foundation
        for her research on explainable AI systems.
        """,
        html_content='<html><body><h1>Dr. Jane Smith</h1><p>Professor of Computer Science</p><a href="/research">Research</a><a href="https://external.com">External Link</a></body></html>'
    )
    
    # Create and run analyzer
    analyzer = ContentAnalysisStage()
    
    print("Testing Content Analysis Stage")
    print("=" * 50)
    
    # Process the page
    analyzed_page = analyzer.process_item(page, job)
    
    # Display results
    print(f"Page URL: {analyzed_page.url}")
    print(f"Status: {analyzed_page.status}")
    print(f"Analysis Results: {analyzed_page.analysis_results}")
    print(f"Analyzed at: {analyzed_page.analyzed_at}")
    
    # Get analytics summary
    analytics = analyzer.get_analytics_summary()
    print("\nSite Metrics:")
    print(f"  Domain: {analytics['site_metrics'].domain}")
    print(f"  Total emails found: {analytics['total_emails']}")
    print(f"  Total social profiles: {analytics['total_social_profiles']}")
    print(f"  Total subdomains: {analytics['total_subdomains']}")
    
    print("\nSubdomain Analytics:")
    for subdomain, data in analytics['subdomain_analytics'].items():
        print(f"  {subdomain}:")
        print(f"    Pages: {data.page_count}")
        print(f"    Emails: {len(data.emails)}")
        print(f"    Social profiles: {data.social_profile_count}")
    
    # Test email extraction
    from utils.common import extract_emails, extract_social_media_handles
    
    print("\nUtility Function Tests:")
    emails = extract_emails(page.clean_content)
    print(f"Emails found: {emails}")
    
    social = extract_social_media_handles(page.clean_content)
    print(f"Social media handles: {social}")
    
    return analyzed_page


if __name__ == "__main__":
    test_content_analyzer()