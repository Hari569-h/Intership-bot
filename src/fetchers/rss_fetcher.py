"""
RSS feed fetcher for internships.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional

import aiohttp
import feedparser
from dateutil import parser

from ..models.internship import Internship
from .base_fetcher import BaseFetcher  # Use relative import


class RssFetcher(BaseFetcher):
    """Fetches internships from RSS feeds."""
    
    def __init__(self, rss_urls: Dict[str, str]):
        """Initialize the RSS fetcher with a dictionary of source names to RSS URLs.
        
        Args:
            rss_urls: Dictionary mapping source names to RSS feed URLs
        """
        # Use the first source name from the URLs as the source_name
        source_name = next(iter(rss_urls.keys()), "rss")
        super().__init__(source_name=source_name)
        self.rss_urls = rss_urls
        self.session = None
    
    async def _fetch_feed(self, session: aiohttp.ClientSession, url: str) -> Dict[str, Any]:
        """Fetch and parse an RSS feed."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    return {'entries': []}
                content = await response.text()
                return feedparser.parse(content)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return {'entries': []}
    
    def _parse_entry(self, entry: Dict[str, Any], source: str) -> Optional[Internship]:
        """Parse an RSS entry into an Internship object."""
        try:
            # Extract title and link
            title = entry.get('title', 'No Title')
            link = entry.get('link', '')
            
            # Skip if no link (can't be a valid job posting)
            if not link:
                return None
                
            # Extract company (if available in author or other fields)
            company = entry.get('author', 'Unknown Company')
            if not company or company == 'Unknown Company':
                # Try to extract company from title if not in author
                title_parts = title.split(' at ')
                if len(title_parts) > 1:
                    title = title_parts[0].strip()
                    company = title_parts[1].strip()
            
            # Extract description
            description = ''
            if 'summary' in entry:
                description = entry.summary
            elif 'description' in entry:
                description = entry.description
            
            # Extract published date
            published = None
            if 'published_parsed' in entry and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif 'updated_parsed' in entry and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            
            # Create and return the Internship object
            return Internship(
                title=title,
                company=company,
                location='Remote',  # Most RSS feed jobs are remote
                url=link,
                source=source,
                posted_date=published,
                description=description
            )
            
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    async def fetch(self) -> List[Internship]:
        """Fetch internships from all configured RSS feeds."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
        all_entries = []
        
        # Fetch all feeds concurrently
        tasks = [self._fetch_feed(self.session, url) for url in self.rss_urls.values()]
        results = await asyncio.gather(*tasks)
        
        # Process all entries
        for feed_result, source_name in zip(results, self.rss_urls.keys()):
            entries = feed_result.get('entries', [])
            for entry in entries:
                internship = self._parse_entry(entry, source_name)
                if internship:
                    all_entries.append(internship)
        
        # Filter out seen jobs using the base class method
        new_internships = await self.filter_new_internships(all_entries)
        
        return new_internships
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


# Example usage:
if __name__ == "__main__":
    # Example RSS feeds (you can add more)
    rss_feeds = {
        "We Work Remotely": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        "RemoteOK": "https://remoteok.io/remote-dev-jobs.rss"
    }
    
    async def main():
        fetcher = RssFetcher(rss_feeds)
        try:
            jobs = await fetcher.fetch()
            print(f"Found {len(jobs)} jobs")
            for job in jobs[:5]:  # Print first 5 jobs
                print(f"{job.title} at {job.company} - {job.url}")
        finally:
            await fetcher.close()
    
    asyncio.run(main())
