#!/usr/bin/env python3
"""
Main entry point for the IT Internship Finder bot.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from src.bot import InternshipFinderBot
from src.config import LOGGING_CONFIG
from src.utils.helpers import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

async def _async_main():
    """Run the IT Internship Finder bot."""
    logger.info("🚀 Starting IT Internship Finder Bot")
    
    try:
        # Initialize and run the bot
        bot = InternshipFinderBot()
        await bot.run()
        
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)
        return 1
    
    logger.info("✅ Bot finished successfully")
    return 0

def main():
    """Entry point for the console script."""
    try:
        return asyncio.run(_async_main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
        return 0
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
