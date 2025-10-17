"""Utility functions and helpers for the Knowledge Management System."""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from loguru import logger


def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure loguru logger with custom settings.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
    """
    # Remove default handler
    logger.remove()
    
    # Console handler
    logger.add(
        lambda msg: print(msg, end=""),
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level
    )
    
    # File handler
    if log_file:
        logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=log_level
        )


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = text.strip()
    
    return text


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: Full URL
        
    Returns:
        Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize and make URL absolute.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative links
        
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""
    
    # Make absolute
    if base_url:
        url = urljoin(base_url, url)
    
    # Remove fragment
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def generate_hash(content: str) -> str:
    """
    Generate MD5 hash of content.
    
    Args:
        content: Content to hash
        
    Returns:
        MD5 hash string
    """
    return hashlib.md5(content.encode()).hexdigest()


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text.
    
    Args:
        text: Text containing potential email
        
    Returns:
        Email address or None
    """
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def extract_phone(text: str) -> Optional[str]:
    """
    Extract phone number from text.
    
    Args:
        text: Text containing potential phone number
        
    Returns:
        Phone number or None
    """
    # Simple pattern for various phone formats
    pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime as ISO string.
    
    Args:
        dt: Datetime object (default: now)
        
    Returns:
        ISO formatted timestamp
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO timestamp string.
    
    Args:
        timestamp_str: ISO formatted timestamp
        
    Returns:
        Datetime object
    """
    return datetime.fromisoformat(timestamp_str)


def save_json(data: Any, filepath: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save file
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved data to {filepath}")


def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded data from {filepath}")
    return data


def ensure_dir(directory: str) -> Path:
    """
    Ensure directory exists.
    
    Args:
        directory: Directory path
        
    Returns:
        Path object
    """
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_size_mb(filepath: str) -> float:
    """
    Get file size in MB.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in MB
    """
    return Path(filepath).stat().st_size / (1024 * 1024)


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def deduplicate_list(items: List[str]) -> List[str]:
    """
    Remove duplicates while preserving order.
    
    Args:
        items: List with potential duplicates
        
    Returns:
        Deduplicated list
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


__all__ = [
    'setup_logger',
    'clean_text',
    'extract_domain',
    'normalize_url',
    'generate_hash',
    'truncate_text',
    'extract_email',
    'extract_phone',
    'format_timestamp',
    'parse_timestamp',
    'save_json',
    'load_json',
    'ensure_dir',
    'file_size_mb',
    'chunk_list',
    'deduplicate_list',
]
