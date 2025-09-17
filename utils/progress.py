"""
Progress tracking utilities for the crawler
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from utils.time import get_current_time


@dataclass
class ProgressStats:
    """Progress statistics for a crawl job"""
    total_urls: int
    completed_urls: int
    failed_urls: int
    pending_urls: int
    processing_urls: int
    start_time: datetime
    pages_discovered: int = 0

    @property
    def processed_urls(self) -> int:
        """Total processed URLs (completed + failed)"""
        return self.completed_urls + self.failed_urls

    @property
    def remaining_urls(self) -> int:
        """Remaining URLs to process"""
        return self.pending_urls + self.processing_urls

    @property
    def completion_percentage(self) -> float:
        """Completion percentage"""
        if self.total_urls == 0:
            return 0.0
        return (self.processed_urls / self.total_urls) * 100

    @property
    def pages_percentage(self) -> float:
        """Pages completion percentage (estimate based on total progress)"""
        if self.pages_discovered == 0:
            return 0.0
        # Estimate pages processed based on overall completion percentage
        estimated_pages_processed = (self.processed_urls / self.total_urls) * self.pages_discovered
        return (estimated_pages_processed / self.pages_discovered) * 100

    @property
    def elapsed_time(self) -> timedelta:
        """Time elapsed since start"""
        return get_current_time() - self.start_time

    @property
    def processing_speed(self) -> float:
        """Processing speed in URLs per second"""
        elapsed_seconds = self.elapsed_time.total_seconds()
        if elapsed_seconds == 0:
            return 0.0
        return self.processed_urls / elapsed_seconds

    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimated time remaining"""
        speed = self.processing_speed
        if speed == 0 or self.remaining_urls == 0:
            return None

        remaining_seconds = self.remaining_urls / speed
        return timedelta(seconds=remaining_seconds)

    def format_duration(self, duration: timedelta) -> str:
        """Format duration as human-readable string"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def format_speed(self) -> str:
        """Format processing speed"""
        speed = self.processing_speed
        if speed >= 1:
            return f"{speed:.1f} URLs/sec"
        else:
            urls_per_minute = speed * 60
            return f"{urls_per_minute:.1f} URLs/min"

    def get_progress_summary(self, job_id: str, domain: str) -> str:
        """Get formatted progress summary"""
        lines = [
            f"🔄 {domain} | Job: {job_id}",
            f"📊 Progress: {self.processed_urls:,}/{self.total_urls:,} URLs ({self.completion_percentage:.1f}%) | ⏱️ {self.format_duration(self.elapsed_time)} elapsed",
            f"📈 Speed: {self.format_speed()}"
        ]

        # Add ETA if available
        eta = self.estimated_time_remaining
        if eta:
            lines[2] += f" | 🕒 ETA: {self.format_duration(eta)} remaining"

        lines.extend([
            f"✅ Completed: {self.completed_urls:,} | ❌ Failed: {self.failed_urls:,} | 📝 Pending: {self.pending_urls:,}",
            f"📄 Pages: ~{int((self.processed_urls / self.total_urls) * self.pages_discovered):,}/{self.pages_discovered:,} ({self.pages_percentage:.1f}%) | 💾 Checkpoint saved"
        ])

        return "\n".join(lines)


class ProgressTracker:
    """Track and format progress for crawler jobs"""

    def __init__(self, job_id: str, domain: str, start_time: datetime):
        self.job_id = job_id
        self.domain = domain
        self.start_time = start_time

    def get_queue_stats(self, url_queue) -> ProgressStats:
        """Get current progress statistics from URL queue"""
        # Get queue counts
        completed_count = len(url_queue.completed)
        failed_count = len(url_queue.failed)
        pending_count = len(url_queue.pending)
        processing_count = len(url_queue.processing)

        total_count = completed_count + failed_count + pending_count + processing_count

        return ProgressStats(
            total_urls=total_count,
            completed_urls=completed_count,
            failed_urls=failed_count,
            pending_urls=pending_count,
            processing_urls=processing_count,
            start_time=self.start_time,
            pages_discovered=total_count  # For now, assume all URLs are pages
        )

    def format_progress_message(self, url_queue) -> str:
        """Format progress message for console output"""
        stats = self.get_queue_stats(url_queue)
        return stats.get_progress_summary(self.job_id, self.domain)