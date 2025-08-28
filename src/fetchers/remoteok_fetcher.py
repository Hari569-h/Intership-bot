"""
RemoteOK job fetcher implementation.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx
from bs4 import BeautifulSoup

from ..models.internship import Internship
from .base_fetcher import BaseFetcher

logger = logging.getLogger(__name__)

class RemoteOKFetcher(BaseFetcher):
    """Fetches job listings from RemoteOK API."""
    
    BASE_URL = "https://remoteok.com/api"
    SOURCE_NAME = "RemoteOK"
    
    def __init__(self, max_retries: int = 3, timeout: float = 30.0):
        """Initialize the RemoteOK fetcher.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        super().__init__(source_name="RemoteOK")
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """Initialize the HTTP session with headers."""
        self.session = httpx.AsyncClient(
            http2=True,
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "application/json"
            },
            follow_redirects=True
        )
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.is_closed:
            await self.session.aclose()
    
    async def fetch(self) -> List[Internship]:
        """Fetch job listings from RemoteOK.
        
        Returns:
            List[Internship]: List of job listings
        """
        logger.info("Fetching jobs from RemoteOK...")
        
        try:
            jobs = await self._fetch_jobs()
            internships = []
            
            for job in jobs:
                try:
                    internship = self._parse_job(job)
                    if internship:
                        internships.append(internship)
                except Exception as e:
                    logger.error(f"Error parsing job: {e}", exc_info=True)
            
            # Filter out seen jobs using the base class method
            new_internships = await self.filter_new_internships(internships)
            logger.info(f"Fetched {len(new_internships)} new jobs from RemoteOK")
            return new_internships
            
        except Exception as e:
            logger.error(f"Error fetching from RemoteOK: {e}", exc_info=True)
            return []
    
    async def _fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from the RemoteOK API with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.session.get(self.BASE_URL)
                response.raise_for_status()
                
                # The API returns a JSON array with the first element being metadata
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    # Skip the first element which is metadata
                    return data[1:]
                return []
                
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                continue
        
        logger.error(f"Failed to fetch jobs after {self.max_retries} attempts: {last_error}")
        return []
    
    def _parse_job(self, job_data: Dict[str, Any]) -> Optional[Internship]:
        """Parse a job listing from RemoteOK API into an Internship object."""
        try:
            # Skip if required fields are missing
            if not all(key in job_data for key in ['position', 'company', 'url', 'date']):
                return None
            
            # Extract basic information
            title = job_data.get('position', '').strip()
            company = job_data.get('company', '').strip()
            url = f"https://remoteok.com/remote-jobs/{job_data.get('slug', '')}"
            
            # Parse publication date
            published_date = None
            if 'date' in job_data and job_data['date']:
                try:
                    # Convert from ISO format with timezone
                    published_date = datetime.strptime(
                        job_data['date'], 
                        '%Y-%m-%dT%H:%M:%S%z'
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse date: {job_data['date']}")
            
            # Get location (remote by default for RemoteOK)
            location = 'Remote'
            
            # Get description (combine description and requirements if available)
            description = job_data.get('description', '')
            if 'description' in job_data and job_data['description']:
                try:
                    soup = BeautifulSoup(job_data['description'], 'html.parser')
                    description = soup.get_text(separator='\n').strip()
                except Exception:
                    description = job_data['description']
            
            # Create and return the Internship object
            return Internship(
                title=title,
                company=company,
                location=location,
                url=url,
                source=self.SOURCE_NAME,
                posted_date=published_date,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error parsing job data: {e}", exc_info=True)
            return None


async def main():
    """Example usage."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    fetcher = RemoteOKFetcher()
    try:
        jobs = await fetcher.fetch()
        print(f"Found {len(jobs)} jobs")
        for job in jobs[:5]:  # Print first 5 jobs
            print(f"{job.title} at {job.company} - {job.url}")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
