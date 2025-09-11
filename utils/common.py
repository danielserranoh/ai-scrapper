"""
Common utilities for the crawler project
"""

import re
from pathlib import Path
from typing import Optional, List, Union
from urllib.parse import urljoin, urlparse, urlunparse
from utils.time import get_current_time


def get_timestamp_string() -> str:
    """Get current timestamp as string for filenames/IDs"""
    return get_current_time().strftime("%Y%m%d_%H%M%S")


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """Normalize URL handling relative paths and fragments"""
    if base_url:
        url = urljoin(base_url, url)
    
    # Parse and rebuild to normalize
    parsed = urlparse(url)
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path,
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))
    
    return normalized


def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc.lower()


def is_valid_url(url: str) -> bool:
    """Check if URL is valid and crawlable"""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def clean_filename(filename: str) -> str:
    """Clean filename for safe filesystem use"""
    # Remove or replace invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(cleaned) > 255:
        name, ext = Path(cleaned).stem, Path(cleaned).suffix
        cleaned = name[:255-len(ext)] + ext
    return cleaned


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if needed"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text content"""
    return re.sub(r'\s+', ' ', text.strip())


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(email_pattern, text, re.IGNORECASE)))


def extract_social_media_handles(text: str) -> dict:
    """Extract social media handles/URLs from text"""
    patterns = {
        'twitter': r'(?:twitter\.com/|@)([A-Za-z0-9_]+)',
        'facebook': r'facebook\.com/([A-Za-z0-9._]+)',
        'linkedin': r'linkedin\.com/(?:in/|company/)([A-Za-z0-9-]+)',
        'instagram': r'instagram\.com/([A-Za-z0-9_.]+)',
        'youtube': r'youtube\.com/(?:user/|channel/|c/)([A-Za-z0-9_-]+)'
    }
    
    results = {}
    for platform, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            results[platform] = list(set(matches))
    
    return results


def format_bytes(bytes_count: int) -> str:
    """Format byte count as human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f}{unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f}TB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds as human readable string"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds//60:.0f}m {seconds%60:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"