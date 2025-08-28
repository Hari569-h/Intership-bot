"""
Base class for all fetchers.
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.internship import Internship
from ..utils.seen_jobs import (
    get_seen_jobs,
    initialize_seen_jobs,
    cleanup_seen_jobs,
    close_seen_jobs,
    has_seen,
    mark_seen
)
from ..utils.helpers import setup_logging

class BaseFetcher:
    """Base class for all job fetchers."""
    
    def __init__(self, source_name: str, max_days_old: int = 7):
        """Initialize the base fetcher.
        
        Args:
            source_name: Name of the job source (e.g., 'internshala', 'remoteok')
            max_days_old: Maximum number of days old a job can be to be included
        """
        self.source_name = source_name
        self.max_days_old = max_days_old
        self.logger = logging.getLogger(f"fetchers.{source_name}")
        self.seen_jobs = None
        
    async def initialize(self):
        """Initialize the fetcher and its dependencies."""
        try:
            # Ensure logging is set up
            if not logging.getLogger().hasHandlers():
                setup_logging()
                
            # Re-initialize logger after setting up logging
            self.logger = logging.getLogger(f"fetchers.{self.source_name}")
            
            # Initialize seen jobs
            self.seen_jobs = await get_seen_jobs()
            self.logger.info(f"Initialized {self.source_name} fetcher")
            return True
        except Exception as e:
            # Ensure we have a logger even if initialization fails
            if not hasattr(self, 'logger') or self.logger is None:
                self.logger = logging.getLogger(f"fetchers.{self.source_name}")
            self.logger.error(f"Failed to initialize {self.source_name} fetcher: {e}", exc_info=True)
            return False
    
    async def cleanup(self):
        """Clean up resources used by the fetcher."""
        try:
            if self.seen_jobs:
                await cleanup_seen_jobs()
                await close_seen_jobs()
                self.logger.info(f"Cleaned up {self.source_name} fetcher")
        except Exception as e:
            self.logger.error(f"Error during cleanup of {self.source_name} fetcher: {e}")
    
    async def fetch(self) -> List[Internship]:
        """Fetch all internships from this source.
        
        This method should be implemented by subclasses.
        
        Returns:
            List of Internship objects
        """
        raise NotImplementedError("Subclasses must implement fetch()")
    
    async def filter_new_internships(self, internships: List[Internship]) -> List[Internship]:
        """Filter out already seen internships.
        
        Args:
            internships: List of internships to filter
            
        Returns:
            List of new internships that haven't been seen before
        """
        if not self.seen_jobs:
            self.logger.warning("Seen jobs not initialized, skipping filtering")
            return internships
            
        new_internships = []
        for internship in internships:
            if not await self.seen_jobs.has_seen(internship.url):
                new_internships.append(internship)
                
        self.logger.info(f"Filtered {len(internships) - len(new_internships)} seen internships from {self.source_name}")
        return new_internships
    
    async def mark_internships_seen(self, internships: List[Internship]) -> None:
        """Mark internships as seen.
        
        Args:
            internships: List of internships to mark as seen
        """
        if not self.seen_jobs:
            self.logger.warning("Seen jobs not initialized, cannot mark as seen")
            return
            
        for internship in internships:
            await self.seen_jobs.mark_seen(internship.url)
            
        self.logger.debug(f"Marked {len(internships)} internships as seen from {self.source_name}")
