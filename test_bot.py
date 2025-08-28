#!/usr/bin/env python3
"""
Test script for the IT Internship Finder bot.
This script helps verify that all components are working correctly.
"""
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from src.bot import Internship, InternshipFinderBot
from src.config import LOGGING_CONFIG
from src.utils.helpers import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

async def test_internship_creation():
    """Test creating and validating Internship objects."""
    print("\n=== Testing Internship Creation ===")
    
    # Test valid internship
    internship = Internship(
        title="Software Engineering Intern",
        company="Tech Corp",
        location="Remote",
        url="https://example.com/internship/123",
        source="Test Source",
        description="Looking for a software engineering intern with Python experience.",
        posted_date=datetime.utcnow() - timedelta(days=1)
    )
    
    print(f"✅ Created internship: {internship}")
    print(f"   Title: {internship.title}")
    print(f"   Company: {internship.company}")
    print(f"   Location: {internship.location}")
    print(f"   URL: {internship.url}")
    print(f"   Source: {internship.source}")
    print(f"   Posted: {internship.posted_date}")
    print(f"   Description: {internship.description[:50]}...")
    
    # Test dictionary conversion
    internship_dict = internship.to_dict()
    print("\n✅ Internship to_dict():", {k: v for k, v in internship_dict.items() if k != 'metadata'})
    
    # Test from_dict
    new_internship = Internship.from_dict(internship_dict)
    print(f"✅ Recreated internship from dict: {new_internship.title} at {new_internship.company}")
    
    return internship

async def test_bot_functionality():
    """Test the main bot functionality with sample data."""
    print("\n=== Testing Bot Functionality ===")
    
    # Initialize the bot
    bot = InternshipFinderBot()
    await bot.initialize()
    
    try:
        # Create test internships
        test_internships = [
            Internship(
                title=f"Software Engineer Intern ({i})",
                company=f"Test Company {i}",
                location="Remote",
                url=f"https://example.com/internship/test-{i}",
                source="Test",
                description=f"Test internship {i} with Python and software development.",
                posted_date=datetime.utcnow() - timedelta(days=i)
            ) for i in range(1, 4)
        ]
        
        # Test saving to database
        print("\n🔹 Testing database operations...")
        for internship in test_internships:
            is_new = await bot.save_internship(internship)
            status = "saved as new" if is_new else "already exists"
            print(f"   - {internship.title}: {status}")
        
        # Test duplicate detection
        print("\n🔹 Testing duplicate detection...")
        is_duplicate = await bot.is_duplicate(test_internships[0].url)
        print(f"   - Is {test_internships[0].title} a duplicate? {is_duplicate}")
        
        # Test fetching all internships
        print("\n🔹 Testing fetching internships...")
        all_internships = await bot.fetch_all_internships()
        print(f"   - Found {len(all_internships)} internships from all sources")
        
        # Test filtering
        print("\n🔹 Testing filtering...")
        filtered = bot.filter_internships(all_internships + test_internships)
        print(f"   - Filtered to {len(filtered)} relevant internships")
        
        # Test notification sending (only if credentials are configured)
        if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
            print("\n🔹 Testing Telegram notification...")
            await bot.send_telegram_notification(test_internships[:1])  # Just test with one
            print("   - Check your Telegram for the test notification")
        else:
            print("\n⚠️  Telegram credentials not configured. Skipping notification test.")
        
    finally:
        # Clean up
        await bot.close()

async def run_tests():
    """Run all tests."""
    print("🚀 Starting IT Internship Finder Bot Tests")
    
    try:
        # Test 1: Internship creation
        test_internship = await test_internship_creation()
        
        # Test 2: Bot functionality
        await test_bot_functionality()
        
        print("\n✅ All tests completed successfully!")
        return 0
        
    except Exception as e:
        logger.exception("Error running tests")
        print(f"\n❌ Tests failed: {e}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(run_tests()))
    except KeyboardInterrupt:
        print("\n👋 Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
