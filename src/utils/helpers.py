"""
Utility functions for the IT Internship Finder.
"""
import re
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the application.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('internship_finder.log')
        ]
    )


def parse_relative_date(date_str: str) -> datetime:
    """Convert relative date strings to datetime objects.
    
    Args:
        date_str: Relative date string (e.g., '2 days ago', '1 week ago')
        
    Returns:
        datetime: Parsed datetime object
    """
    if not date_str:
        return datetime.utcnow()
    
    now = datetime.utcnow()
    date_str = date_str.lower().strip()
    
    if 'today' in date_str:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if 'yesterday' in date_str:
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Match patterns like '2 days ago', '1 week ago', '3 months ago'
    match = re.search(r'(\d+)\s+(day|week|month|hour|minute)s?\s+ago', date_str)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'day':
            return now - timedelta(days=num)
        elif unit == 'week':
            return now - timedelta(weeks=num)
        elif unit == 'month':
            # Approximate month as 30 days
            return now - timedelta(days=30 * num)
        elif unit == 'hour':
            return now - timedelta(hours=num)
        elif unit == 'minute':
            return now - timedelta(minutes=num)
    
    # Try to parse as a regular date string
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        pass
    
    # If all else fails, return current time
    return now


def clean_text(text: str) -> str:
    """Clean and normalize text by removing extra whitespace and special characters.
    
    Args:
        text: Input text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ''
    
    # Replace multiple whitespace with a single space
    text = ' '.join(text.split())
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    return text.strip()


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text.
    
    Args:
        text: Input text to search for emails
        
    Returns:
        List[str]: List of found email addresses
    """
    if not text:
        return []
    
    # Simple email regex pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)


def is_it_related(text: str, keywords: List[str]) -> bool:
    """Check if text is related to IT based on keywords.
    
    Args:
        text: Text to check
        keywords: List of IT-related keywords
        
    Returns:
        bool: True if text contains IT-related keywords, False otherwise
    """
    if not text:
        return False
    
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


async def fetch_url(url: str, session: Optional[aiohttp.ClientSession] = None, **kwargs) -> str:
    """Fetch content from a URL with error handling.
    
    Args:
        url: URL to fetch
        session: Optional aiohttp ClientSession
        **kwargs: Additional arguments to pass to session.get()
        
    Returns:
        str: Fetched content
        
    Raises:
        aiohttp.ClientError: If the request fails
    """
    close_session = False
    if session is None:
        session = aiohttp.ClientSession()
        close_session = True
    
    try:
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()
    finally:
        if close_session:
            await session.close()


def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract JSON-LD structured data from a BeautifulSoup object.
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        List[Dict[str, Any]]: Extracted JSON-LD data
    """
    results = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string, strict=False)
            if isinstance(data, dict):
                results.append(data)
            elif isinstance(data, list):
                results.extend(data)
        except (json.JSONDecodeError, TypeError):
            continue
    return results


def format_internship_message(internship: 'Internship', index: int = None) -> str:
    """Format an internship as a message string.
    
    Args:
        internship: Internship object
        index: Optional index number
        
    Returns:
        str: Formatted message
    """
    prefix = f"{index}. " if index is not None else ""
    
    message = [
        f"{prefix}*{internship.title}*",
        f"🏢 *Company:* {internship.company}",
        f"📍 *Location:* {internship.location}",
    ]
    
    if internship.posted_date:
        message.append(f"📅 *Posted:* {internship.posted_date.strftime('%Y-%m-%d')}")
    
    message.append(f"🔗 [Apply Here]({internship.url})\n")
    
    return "\n".join(message)


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size.
    
    Args:
        lst: List to split
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(dictionary: Dict[Any, Any], *keys, default: Any = None) -> Any:
    """Safely get a value from a nested dictionary.
    
    Args:
        dictionary: Dictionary to search in
        *keys: Keys to traverse
        default: Default value if key not found
        
    Returns:
        Value if found, otherwise default
    """
    current = dictionary
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is default:
            break
    return current


def filter_last_24_hours(internships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter internships to only include those posted in the last 24 hours.
    
    Args:
        internships: List of internship dictionaries, each containing a 'posted_date' field
        
    Returns:
        List of internships from the last 24 hours
    """
    from datetime import datetime, timedelta, timezone
    
    if not internships:
        return []
        
    current_time = datetime.now(timezone.utc)
    twenty_four_hours_ago = current_time - timedelta(hours=24)
    
    recent_internships = []
    
    for internship in internships:
        try:
            if 'posted_date' not in internship or not internship['posted_date']:
                continue
                
            posted_date = internship['posted_date']
            
            # Convert string to datetime if needed
            if isinstance(posted_date, str):
                posted_date = datetime.fromisoformat(posted_date)
            
            # Ensure timezone awareness
            if posted_date.tzinfo is None:
                posted_date = posted_date.replace(tzinfo=timezone.utc)
                
            if posted_date >= twenty_four_hours_ago:
                recent_internships.append(internship)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error processing date for internship: {e}")
            continue
            
    return recent_internships
