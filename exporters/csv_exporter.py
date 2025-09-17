"""
CSV exporter implementation
"""

import csv
from typing import List
from .base import BaseExporter
from models.page import Page


class CSVExporter(BaseExporter):
    """Exports data to CSV format"""

    @property
    def file_extension(self) -> str:
        return "csv"

    def export_pages(self, job_id: str, pages: List[Page]) -> str:
        """Export pages data to CSV"""
        filename = self._generate_filename(job_id, "pages")
        csv_path = self.output_dir / filename

        fieldnames = [
            'url', 'status', 'status_code', 'content_type', 'content_length',
            'title', 'domain', 'subdomain', 'path', 'discovered_at',
            'fetched_at', 'processed_at', 'analyzed_at', 'error_message', 'retry_count',
            'internal_links_count', 'external_links_count', 'emails_count',
            'social_profiles_count', 'page_type', 'funding_references',
            'collaboration_indicators', 'technology_transfer', 'industry_connections'
        ]

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for page in pages:
                # Extract analysis results if available
                analysis = page.analysis_results or {}
                content_indicators = analysis.get('content_indicators', {})

                row = {
                    'url': page.url,
                    'status': page.status.value if page.status else '',
                    'status_code': page.status_code or '',
                    'content_type': page.content_type.value if page.content_type else '',
                    'content_length': page.content_length or '',
                    'title': page.title or '',
                    'domain': page.domain,
                    'subdomain': page.subdomain,
                    'path': page.path,
                    'discovered_at': page.discovered_at.isoformat() if page.discovered_at else '',
                    'fetched_at': page.fetched_at.isoformat() if page.fetched_at else '',
                    'processed_at': page.processed_at.isoformat() if page.processed_at else '',
                    'analyzed_at': page.analyzed_at.isoformat() if page.analyzed_at else '',
                    'error_message': page.error_message or '',
                    'retry_count': page.retry_count,
                    'internal_links_count': len(page.internal_links),
                    'external_links_count': len(page.external_links),
                    'emails_count': len(analysis.get('emails_found', [])) if analysis and isinstance(analysis.get('emails_found'), list) else 0,
                    'social_profiles_count': len(analysis.get('social_profiles_found', {})) if analysis and isinstance(analysis.get('social_profiles_found'), dict) else 0,
                    'page_type': analysis.get('page_type', '') if analysis else '',
                    'funding_references': content_indicators.get('funding_references', 0),
                    'collaboration_indicators': content_indicators.get('collaboration_indicators', 0),
                    'technology_transfer': content_indicators.get('technology_transfer', 0),
                    'industry_connections': content_indicators.get('industry_connections', 0)
                }
                writer.writerow(row)

        return str(csv_path)

    def export_contacts(self, job_id: str, pages: List[Page]) -> str:
        """Export contacts data to CSV"""
        filename = self._generate_filename(job_id, "contacts")
        csv_path = self.output_dir / filename

        fieldnames = ['source_url', 'contact_type', 'contact_value', 'subdomain', 'page_title', 'discovered_at']

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for page in pages:
                if not page.analysis_results:
                    continue

                analysis = page.analysis_results

                # Export emails
                emails = analysis.get('emails_found', [])
                if emails and isinstance(emails, list):
                    for email in emails:
                        writer.writerow({
                            'source_url': page.url,
                            'contact_type': 'email',
                            'contact_value': email,
                            'subdomain': page.subdomain,
                            'page_title': page.title or '',
                            'discovered_at': page.processed_at.isoformat() if page.processed_at else ''
                        })

                # Export social profiles
                social_profiles = analysis.get('social_profiles_found', {})
                if social_profiles and isinstance(social_profiles, dict):
                    for platform, profiles in social_profiles.items():
                        if profiles:
                            for profile in profiles:
                                writer.writerow({
                                    'source_url': page.url,
                                    'contact_type': platform,
                                    'contact_value': profile,
                                    'subdomain': page.subdomain,
                                    'page_title': page.title or '',
                                    'discovered_at': page.processed_at.isoformat() if page.processed_at else ''
                                })

        return str(csv_path)