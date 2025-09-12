#!/usr/bin/env python3
"""
Helper script to analyze crawler results and show business intelligence insights
"""

import csv
import sys
from pathlib import Path
from collections import defaultdict, Counter


def analyze_csv_results(csv_path: str):
    """Analyze CSV results and show business intelligence insights"""
    
    print(f"📊 Analyzing results from: {Path(csv_path).name}")
    print("=" * 80)
    
    # Read CSV data
    pages = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        pages = list(reader)
    
    if not pages:
        print("❌ No data found in CSV file")
        return
    
    print(f"📄 Total Pages: {len(pages)}")
    
    # Status breakdown
    status_counts = Counter(page['status'] for page in pages)
    print("\n📋 Page Status Breakdown:")
    for status, count in status_counts.most_common():
        percentage = (count / len(pages)) * 100
        print(f"  {status}: {count} ({percentage:.1f}%)")
    
    # Analysis completion rate
    analyzed_pages = [p for p in pages if p.get('analyzed_at')]
    analysis_rate = (len(analyzed_pages) / len(pages)) * 100
    print(f"\n🔍 Analysis Completion Rate: {len(analyzed_pages)}/{len(pages)} ({analysis_rate:.1f}%)")
    
    if not analyzed_pages:
        print("⚠️ No pages were analyzed. Check if analysis stage is running.")
        return
    
    # Page type classification
    page_types = Counter(page.get('page_type', 'unknown') for page in analyzed_pages)
    print("\n📑 Page Type Classification:")
    for page_type, count in page_types.most_common():
        if page_type and page_type != 'unknown':
            percentage = (count / len(analyzed_pages)) * 100
            print(f"  {page_type}: {count} ({percentage:.1f}%)")
    
    # Contact extraction results
    pages_with_emails = [p for p in analyzed_pages if int(p.get('emails_count', 0)) > 0]
    pages_with_social = [p for p in analyzed_pages if int(p.get('social_profiles_count', 0)) > 0]
    
    total_emails = sum(int(p.get('emails_count', 0)) for p in analyzed_pages)
    total_social = sum(int(p.get('social_profiles_count', 0)) for p in analyzed_pages)
    
    print("\n📧 Contact Extraction Results:")
    print(f"  Total emails found: {total_emails}")
    print(f"  Pages with emails: {len(pages_with_emails)} ({len(pages_with_emails)/len(analyzed_pages)*100:.1f}%)")
    print(f"  Total social profiles: {total_social}")
    print(f"  Pages with social profiles: {len(pages_with_social)} ({len(pages_with_social)/len(analyzed_pages)*100:.1f}%)")
    
    # Business intelligence indicators
    funding_pages = [p for p in analyzed_pages if int(p.get('funding_references', 0)) > 0]
    collab_pages = [p for p in analyzed_pages if int(p.get('collaboration_indicators', 0)) > 0]
    tech_transfer_pages = [p for p in analyzed_pages if int(p.get('technology_transfer', 0)) > 0]
    industry_pages = [p for p in analyzed_pages if int(p.get('industry_connections', 0)) > 0]
    
    print("\n🎯 Business Intelligence Indicators:")
    print(f"  Pages with funding references: {len(funding_pages)} ({len(funding_pages)/len(analyzed_pages)*100:.1f}%)")
    print(f"  Pages with collaboration indicators: {len(collab_pages)} ({len(collab_pages)/len(analyzed_pages)*100:.1f}%)")
    print(f"  Pages with technology transfer: {len(tech_transfer_pages)} ({len(tech_transfer_pages)/len(analyzed_pages)*100:.1f}%)")
    print(f"  Pages with industry connections: {len(industry_pages)} ({len(industry_pages)/len(analyzed_pages)*100:.1f}%)")
    
    # Top contact pages
    contact_rich_pages = sorted(
        [(p['url'], int(p.get('emails_count', 0)), p.get('page_type', '')) 
         for p in analyzed_pages if int(p.get('emails_count', 0)) > 0],
        key=lambda x: x[1], reverse=True
    )[:10]
    
    if contact_rich_pages:
        print("\n📋 Top Contact-Rich Pages:")
        for url, email_count, page_type in contact_rich_pages:
            print(f"  {email_count} emails | {page_type:10} | {url[:80]}{'...' if len(url) > 80 else ''}")
    
    # High-value business intelligence pages
    bi_pages = []
    for page in analyzed_pages:
        funding = int(page.get('funding_references', 0))
        collab = int(page.get('collaboration_indicators', 0))
        tech = int(page.get('technology_transfer', 0))
        industry = int(page.get('industry_connections', 0))
        
        total_bi_score = funding + collab + tech + industry
        if total_bi_score > 0:
            bi_pages.append((page['url'], page.get('page_type', ''), total_bi_score, funding, collab, tech, industry))
    
    bi_pages.sort(key=lambda x: x[2], reverse=True)
    
    if bi_pages:
        print("\n🏆 High-Value Business Intelligence Pages:")
        print("    Score | Type       | Fund | Coll | Tech | Ind  | URL")
        print("    ------|------------|------|------|------|------|----")
        for url, page_type, score, fund, coll, tech, ind in bi_pages[:15]:
            print(f"    {score:5} | {page_type:10} | {fund:4} | {coll:4} | {tech:4} | {ind:4} | {url[:50]}{'...' if len(url) > 50 else ''}")
    
    # Subdomain breakdown
    subdomain_stats = defaultdict(lambda: {'pages': 0, 'emails': 0, 'social': 0})
    for page in analyzed_pages:
        subdomain = page.get('subdomain', 'www')
        subdomain_stats[subdomain]['pages'] += 1
        subdomain_stats[subdomain]['emails'] += int(page.get('emails_count', 0))
        subdomain_stats[subdomain]['social'] += int(page.get('social_profiles_count', 0))
    
    print("\n🌐 Subdomain Analysis:")
    for subdomain, stats in sorted(subdomain_stats.items(), key=lambda x: x[1]['pages'], reverse=True)[:10]:
        print(f"  {subdomain:15} | {stats['pages']:3} pages | {stats['emails']:3} emails | {stats['social']:3} social")


def show_sample_pages(csv_path: str, page_type: str = None, limit: int = 5):
    """Show sample pages of a specific type with their analysis results"""
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        pages = list(reader)
    
    if page_type:
        pages = [p for p in pages if p.get('page_type') == page_type]
        print(f"\n📄 Sample {page_type.title()} Pages:")
    else:
        pages = [p for p in pages if p.get('analyzed_at')]
        print("\n📄 Sample Analyzed Pages:")
    
    print("=" * 80)
    
    for i, page in enumerate(pages[:limit]):
        print(f"\n{i+1}. {page.get('page_type', 'unknown').upper()} PAGE")
        print(f"   URL: {page['url']}")
        print(f"   Title: {page.get('title', 'N/A')}")
        print(f"   Status: {page['status']}")
        print(f"   Emails: {page.get('emails_count', 0)}")
        print(f"   Social: {page.get('social_profiles_count', 0)}")
        
        # Business intelligence indicators
        funding = int(page.get('funding_references', 0))
        collab = int(page.get('collaboration_indicators', 0))
        tech = int(page.get('technology_transfer', 0))
        industry = int(page.get('industry_connections', 0))
        
        if any([funding, collab, tech, industry]):
            print(f"   BI Indicators: Funding({funding}) Collab({collab}) Tech({tech}) Industry({industry})")


def main():
    """Main analysis function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <csv_file> [page_type]")
        print("\nExamples:")
        print("  python analyze_results.py data/output/job_20240101_120000_pages_*.csv")
        print("  python analyze_results.py data/output/job_20240101_120000_pages_*.csv faculty")
        print("\nAvailable page types: faculty, research, department, contact, admissions, news, about, general")
        return
    
    csv_path = sys.argv[1]
    
    if not Path(csv_path).exists():
        print(f"❌ File not found: {csv_path}")
        
        # Try to find similar files
        pattern = Path(csv_path).name.replace('*', '')
        similar_files = list(Path("data/output").glob(f"*{pattern}*"))
        if similar_files:
            print("\n💡 Did you mean one of these files?")
            for f in similar_files:
                print(f"   {f}")
        return
    
    # Run main analysis
    analyze_csv_results(csv_path)
    
    # Show sample pages if page type specified
    if len(sys.argv) > 2:
        page_type = sys.argv[2].lower()
        show_sample_pages(csv_path, page_type)


if __name__ == "__main__":
    main()