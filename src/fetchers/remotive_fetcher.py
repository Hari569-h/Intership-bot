"""
Remotive job fetcher implementation.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx

from ..models.internship import Internship
from .base_fetcher import BaseFetcher

logger = logging.getLogger(__name__)

class RemotiveFetcher(BaseFetcher):
    """Fetches job listings from Remotive API."""
    
    BASE_URL = "https://remotive.com/api/remote-jobs"
    SOURCE_NAME = "Remotive"
    
    def __init__(self, max_retries: int = 3, timeout: float = 30.0):
        """Initialize the Remotive fetcher.
        
        Args:
            max_retries: Maximum number of retry attempts for failed requests
            timeout: Request timeout in seconds
        """
        super().__init__(source_name="Remotive")
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
        """Fetch job listings from Remotive.
        
        Returns:
            List[Internship]: List of job listings
        """
        logger.info("Fetching jobs from Remotive...")
        
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
            logger.info(f"Fetched {len(new_internships)} new jobs from Remotive")
            return new_internships
            
        except Exception as e:
            logger.error(f"Error fetching from Remotive: {e}", exc_info=True)
            return []
    
    async def _fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from the Remotive API with retry logic."""
        last_error = None
        params = {
            'limit': 100,  # Maximum allowed by the API
            'category': 'software-dev'  # Focus on software development jobs
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.session.get(self.BASE_URL, params=params)
                response.raise_for_status()
                
                data = response.json()
                if isinstance(data, dict) and 'jobs' in data:
                    return data['jobs']
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
        """Parse a job listing from Remotive API into an Internship object."""
        try:
            # Extract basic information
            title = job_data.get('title', '').strip()
            company = job_data.get('company_name', '').strip()
            url = job_data.get('url', '').strip()
            
            if not all([title, company, url]):
                return None
                
            # Parse publication date
            published_str = job_data.get('publication_date', '')
            published_date = None
            if published_str:
                try:
                    published_date = datetime.strptime(published_str, '%Y-%m-%dT%H:%M:%S%z')
                except (ValueError, TypeError):
                    pass
            
            # Get location (usually remote for Remotive)
            location = job_data.get('candidate_required_location', 'Remote')
            if not location or location.lower() == 'anywhere':
                location = 'Remote'
            
            # Get description
            description = job_data.get('description', '')
            
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
    
    fetcher = RemotiveFetcher()
    try:
        jobs = await fetcher.fetch()
        print(f"Found {len(jobs)} jobs")
        for job in jobs[:5]:  # Print first 5 jobs
            print(f"{job.title} at {job.company} - {job.url}")
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
