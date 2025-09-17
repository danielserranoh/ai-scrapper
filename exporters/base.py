"""
Base exporter class for all export formats
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any
from models.page import Page


class BaseExporter(ABC):
    """Base class for all exporters"""

    def __init__(self, output_dir: str = "data/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def export_pages(self, job_id: str, pages: List[Page]) -> str:
        """Export pages data to the target format

        Args:
            job_id: The job identifier
            pages: List of Page objects to export

        Returns:
            Path to the generated file
        """
        pass

    @abstractmethod
    def export_contacts(self, job_id: str, pages: List[Page]) -> str:
        """Export contacts data to the target format

        Args:
            job_id: The job identifier
            pages: List of Page objects to extract contacts from

        Returns:
            Path to the generated file
        """
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """File extension for this format"""
        pass

    def _generate_filename(self, job_id: str, data_type: str) -> str:
        """Generate standardized filename"""
        from utils.time import get_current_time
        timestamp = get_current_time().strftime("%Y%m%d_%H%M%S")
        return f"{job_id}_{data_type}_{timestamp}.{self.file_extension}"