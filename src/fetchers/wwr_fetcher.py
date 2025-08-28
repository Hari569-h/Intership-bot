"""
WeWorkRemotely job fetcher implementation.
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from ..models.internship import Internship
from .base_fetcher import BaseFetcher

logger = logging.getLogger(__name__)

class WWRFetcher(BaseFetcher):
    """Fetches job listings from WeWorkRemotely RSS feed."""
    
    FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    
    def __init__(self, max_retries: int = 3, timeout: float = 30.0):
        """Initialize the WeWorkRemotely fetcher.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        super().__init__(source_name="WeWorkRemotely")
        self.max_retries = max_retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
    
    async def _fetch_feed(self) -> Dict[str, Any]:
        """Fetch and parse the RSS feed with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.get(self.FEED_URL) as response:
                    if response.status != 200:
                        raise aiohttp.ClientError(f"HTTP {response.status}")
                    content = await response.text()
                    return feedparser.parse(content)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to fetch feed after {self.max_retries} attempts: {last_error}")
        return {'entries': []}
    
    async def fetch(self) -> List[Internship]:
        """Fetch job listings from WeWorkRemotely.
        
        Returns:
            List[Internship]: List of job listings
        """
        logger.info("Fetching jobs from WeWorkRemotely...")
        
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        try:
            feed = await self._fetch_feed()
            entries = feed.get('entries', [])
            
            internships = []
            for entry in entries:
                try:
                    internship = self._parse_entry(entry)
                    if internship:
                        internships.append(internship)
                except Exception as e:
                    logger.error(f"Error parsing entry: {e}", exc_info=True)
            
            # Filter out seen jobs using the base class method
            new_internships = await self.filter_new_internships(internships)
            logger.info(f"Fetched {len(internships)} jobs from WeWorkRemotely, {len(new_internships)} are new")
            return new_internships
            
        except Exception as e:
            logger.error(f"Error fetching from WeWorkRemotely: {e}", exc_info=True)
            return []
        finally:
            await self.close()
    
    def _parse_entry(self, entry: Dict[str, Any]) -> Optional[Internship]:
        """Parse an RSS entry into an Internship object."""
        try:
            title = entry.get('title', '').strip()
            if not title:
                return None
                
            # Extract company from the title (format: "Job Title at Company")
            company = "Unknown"
            if ' at ' in title:
                company = title.split(' at ')[-1].strip()
                title = title.split(' at ')[0].strip()
                
            url = entry.get('link', '').strip()
            if not url:
                return None
                
            # Get location (usually remote for WeWorkRemotely)
            location = "Remote"
            
            # Parse the published date
            published = entry.get('published_parsed')
            if published and isinstance(published, (tuple, list)) and len(published) >= 6:
                # Convert time.struct_time to datetime
                posted_date = datetime(*published[:6])
            else:
                posted_date = datetime.utcnow()
            
            # Get description and clean it up
            description = entry.get('description', '')
            if description:
                try:
                    soup = BeautifulSoup(description, 'html.parser')
                    # Remove the first ul which usually contains metadata
                    first_ul = soup.find('ul')
                    if first_ul:
                        first_ul.decompose()
                    description = soup.get_text(separator='\n').strip()
                except Exception:
                    pass
            
            # Create the Internship object with additional metadata
            metadata = {
                'original_data': {k: v for k, v in entry.items() 
                               if k not in ['title', 'link', 'description', 'published_parsed']}
            }
            
            return Internship(
                title=title,
                company=company,
                location=location,
                url=url,
                source=self.source_name,
                posted_date=posted_date,
                description=description,
                **metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing entry: {e}", exc_info=True)
            return None
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


async def main():
    """Example usage."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    fetcher = WWRFetcher()
    try:
        jobs = await fetcher.fetch()
        print(f"Found {len(jobs)} jobs:")
        for i, job in enumerate(jobs[:5], 1):  # Show first 5
            print(f"{i}. {job.title} at {job.company}")
            print(f"   Location: {job.location}")
            print(f"   Posted: {job.posted_date}")
            print(f"   URL: {job.url}\n")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
