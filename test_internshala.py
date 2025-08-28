#!/usr/bin/env python3
"""
Test script for the Internshala fetcher.
"""
import asyncio
import logging
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from src.fetchers.internshala_fetcher import InternshalaFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('internshala_test.log')
    ]
)
logger = logging.getLogger(__name__)

async def test_internshala_fetcher():
    """Test the Internshala fetcher with retries and better error handling."""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries}...")
        fetcher = None
        
        try:
            # Initialize the fetcher with just 1 page for testing
            fetcher = InternshalaFetcher(max_pages=1)
            
            # Fetch internships
            logger.info("Fetching internships...")
            start_time = time.time()
            internships = await fetcher.fetch()
            elapsed = time.time() - start_time
            
            if not internships:
                logger.warning("No internships found. This might be due to rate limiting or captcha.")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    continue
                return
            
            # Display results
            logger.info(f"✅ Successfully fetched {len(internships)} internships in {elapsed:.2f} seconds")
            for i, internship in enumerate(internships[:5], 1):  # Show first 5
                print(f"\n{i}. {internship.title} at {internship.company}")
                print(f"   Location: {internship.location}")
                print(f"   Stipend: {internship.stipend}")
                print(f"   Posted: {internship.posted_date}")
                print(f"   Apply by: {internship.deadline}")
                print(f"   Link: {internship.link}")
            
            # If we got here, we're done
            return
            
        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {e}", exc_info=True)
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("All attempts failed. This might be due to:")
                logger.error("1. Being rate limited by Internshala")
                logger.error("2. Needing to solve a captcha manually")
                logger.error("3. Changes in Internshala's website structure")
                logger.error("\nTry accessing the URL in a browser to check for captchas:")
                logger.error("https://internshala.com/internships/computer-science-internship/")
        
        finally:
            if fetcher:
                await fetcher.close()

async def main():
    """Main entry point for the test script."""
    logger.info("🚀 Starting Internshala fetcher test...")
    start_time = time.time()
    
    try:
        await test_internshala_fetcher()
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        elapsed = time.time() - start_time
        logger.info(f"🏁 Test completed in {elapsed:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
