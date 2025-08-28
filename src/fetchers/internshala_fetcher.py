"""
Internshala job scraper for internships using aiohttp for better header handling.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup

from .base_fetcher import BaseFetcher
from ..models.internship import Internship
from ..utils.helpers import (
    clean_text,
    extract_emails,
    parse_relative_date
)

# These functions might need to be implemented if they don't exist
async def fetch_url(url, session=None, **kwargs):
    """Fetch URL content with error handling."""
    if session is None:
        async with aiohttp.ClientSession() as session:
            return await fetch_url(url, session, **kwargs)
    
    try:
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return None

def safe_get(data, *keys, default=None):
    """Safely get a nested value from a dictionary."""
    for key in keys:
        if not isinstance(data, dict) or key not in data:
            return default
        data = data[key]
    return data

class InternshalaFetcher(BaseFetcher):
    """Fetches internships from Internshala."""
    
    BASE_URL = "https://internshala.com"
    SEARCH_URL = f"{BASE_URL}/internships/computer-science-internship"
    
    def __init__(self, max_pages: int = 3):
        """Initialize the Internshala fetcher.
        
        Args:
            max_pages: Maximum number of pages to scrape (default: 3)
        """
        super().__init__("internshala")
        self.max_pages = max_pages
        self.session = None
        
    async def initialize(self):
        """Initialize the fetcher."""
        await super().initialize()
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': self.BASE_URL,
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
    
    async def cleanup(self):
        """Clean up resources."""
        await super().cleanup()
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch(self) -> List[Internship]:
        """Fetch all internships from Internshala."""
        try:
            self.logger.info(f"Fetching up to {self.max_pages} pages from Internshala...")
            
            internships = []
            
            # Fetch each page
            for page in range(1, self.max_pages + 1):
                url = f"{self.SEARCH_URL}/page-{page}" if page > 1 else self.SEARCH_URL
                
                # Get the search page
                html = await fetch_url(url, self.session)
                if not html:
                    self.logger.error(f"Failed to fetch Internshala search page {page}")
                    continue
                    
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all internship listings
                listings = soup.select('.internship_meta')
                if not listings:
                    self.logger.info(f"No more listings found on page {page}")
                    break
                    
                self.logger.info(f"Found {len(listings)} internship listings on page {page}")
                
                for listing in listings:
                    try:
                        internship = await self._parse_internship(listing)
                        if internship:
                            internships.append(internship)
                    except Exception as e:
                        self.logger.error(f"Error parsing internship: {e}", exc_info=True)
                
                # Add a small delay between page requests
                if page < self.max_pages:
                    await asyncio.sleep(1)
            
            # Filter out seen jobs
            new_internships = await self.filter_new_internships(internships)
            
            # Mark new internships as seen
            if new_internships:
                await self.mark_internships_seen(new_internships)
            
            return new_internships
                
        except Exception as e:
            self.logger.error(f"Error fetching internships: {e}", exc_info=True)
            return []
    
    async def _parse_internship(self, listing) -> Optional[Internship]:
        """Parse an internship listing into an Internship object."""
        try:
            # Extract basic details
            title_elem = listing.select_one('.heading_4_5')
            if not title_elem:
                return None
                
            title = clean_text(title_elem.text.strip())
            
            # Extract company
            company_elem = listing.select_one('.heading_6')
            company = clean_text(company_elem.text.strip()) if company_elem else "Not specified"
            
            # Extract location
            location_elem = listing.select_one('.location_link')
            location = clean_text(location_elem.text.strip()) if location_elem else "Remote"
            
            # Extract URL
            url_elem = listing.select_one('a.view_detail_button')
            if not url_elem or 'href' not in url_elem.attrs:
                return None
                
            url = self.BASE_URL + url_elem['href'] if not url_elem['href'].startswith('http') else url_elem['href']
            
            # Extract posted date
            posted_elem = listing.select_one('.posted_by_container')
            posted_text = clean_text(posted_elem.text.strip()) if posted_elem else ""
            posted_date = parse_relative_date(posted_text) if posted_text else datetime.utcnow()
            
            # Extract duration and stipend
            details = listing.select('.item_body')
            duration = clean_text(details[1].text.strip()) if len(details) > 1 else "Not specified"
            stipend = clean_text(details[2].text.strip()) if len(details) > 2 else "Not specified"
            
            # Create internship object
            return Internship(
                title=title,
                company=company,
                location=location,
                url=url,
                posted_date=posted_date,
                source="Internshala",
                description=f"Duration: {duration}\nStipend: {stipend}"
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing internship listing: {e}", exc_info=True)
            return None
