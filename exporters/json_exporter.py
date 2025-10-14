"""
JSON exporter implementation
"""

import json
from typing import List
from .base import BaseExporter
from models.page import Page
from storage.checkpoints import JSONEncoder


class JSONExporter(BaseExporter):
    """Exports data to JSON format"""

    @property
    def file_extension(self) -> str:
        return "json"

    def export_pages(self, job_id: str, pages: List[Page]) -> str:
        """Export pages data to JSON"""
        filename = self._generate_filename(job_id, "pages")
        json_path = self.output_dir / filename

        pages_data = []
        for page in pages:
            page_dict = {
                'url': page.url,
                'job_id': page.job_id,
                'status': page.status.value if page.status else '',
                'status_code': page.status_code,
                'content_type': page.content_type.value if page.content_type else '',
                'content_length': page.content_length,
                'title': page.title,
                'domain': page.domain,
                'subdomain': page.subdomain,
                'path': page.path,
                'discovered_at': page.discovered_at,
                'fetched_at': page.fetched_at,
                'processed_at': page.processed_at,
                'analyzed_at': page.analyzed_at,
                'error_message': page.error_message,
                'retry_count': page.retry_count,
                'internal_links': list(page.internal_links),
                'external_links': list(page.external_links),
                'analysis_results': page.analysis_results,
                # Phase 3B: Extraction quality metadata
                'extraction_method': page.extraction_method,
                'browser_fetched': page.browser_fetched,
                'markdown_quality_score': page.markdown_quality_score
            }
            pages_data.append(page_dict)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(pages_data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)

        return str(json_path)

    def export_contacts(self, job_id: str, pages: List[Page]) -> str:
        """Export contacts data to JSON"""
        filename = self._generate_filename(job_id, "contacts")
        json_path = self.output_dir / filename

        contacts_data = {
            'job_id': job_id,
            'exported_at': None,  # Will be set by JSONEncoder
            'total_pages_analyzed': len(pages),
            'contacts': []
        }

        from utils.time import get_current_time
        contacts_data['exported_at'] = get_current_time()

        for page in pages:
            if not page.analysis_results:
                continue

            analysis = page.analysis_results
            page_contacts = {
                'source_url': page.url,
                'subdomain': page.subdomain,
                'page_title': page.title,
                'discovered_at': page.processed_at,
                'emails': analysis.get('emails_found', []),
                'social_profiles': analysis.get('social_profiles_found', {})
            }

            # Only include pages that have contacts
            if page_contacts['emails'] or page_contacts['social_profiles']:
                contacts_data['contacts'].append(page_contacts)

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(contacts_data, f, cls=JSONEncoder, indent=2, ensure_ascii=False)

        return str(json_path)