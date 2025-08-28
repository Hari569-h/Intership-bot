"""Utilities for tracking seen job postings.
"""
import asyncio
import logging
import os
import json
import firebase_admin
from firebase_admin import firestore
from typing import Dict, Any, Set, Optional

logger = logging.getLogger(__name__)

# Global seen jobs cache
_seen_jobs_cache: Set[str] = set()
_db = None

# Local file for storing seen jobs when Firebase is not available
_LOCAL_SEEN_JOBS_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'seen_jobs.json'))
logger.info(f"Local seen jobs file path: {_LOCAL_SEEN_JOBS_FILE}")

async def initialize_seen_jobs() -> None:
    """Initialize the seen jobs tracking system."""
    global _db
    try:
        if not firebase_admin._apps:
            try:
                firebase_admin.initialize_app()
                _db = firestore.client()
                logger.info("Firebase initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                logger.info("Will use local file storage for seen jobs")
                _db = None
    except Exception as e:
        logger.error(f"Error during Firebase initialization: {e}")
        _db = None
    
    await load_seen_jobs()

async def load_seen_jobs() -> Set[str]:
    """Load seen job URLs from Firestore or local file."""
    global _seen_jobs_cache
    
    # Try loading from Firestore if available
    if _db:
        try:
            docs = _db.collection("seen_jobs").limit(10000).stream()
            for doc in docs:
                _seen_jobs_cache.add(doc.id)
            logger.info(f"Loaded {len(_seen_jobs_cache)} seen job URLs from Firestore")
            return _seen_jobs_cache
        except Exception as e:
            logger.error(f"Error loading seen jobs from Firestore: {e}")
    
    # Fall back to local file if Firestore is not available
    try:
        if os.path.exists(_LOCAL_SEEN_JOBS_FILE):
            with open(_LOCAL_SEEN_JOBS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    _seen_jobs_cache.update(data)
                    logger.info(f"Loaded {len(_seen_jobs_cache)} seen job URLs from local file")
    except Exception as e:
        logger.error(f"Error loading seen jobs from local file: {e}")
    
    return _seen_jobs_cache

async def get_seen_jobs() -> Set[str]:
    """Get the set of seen job URLs."""
    if not _seen_jobs_cache and _db is None:
        await initialize_seen_jobs()
    return _seen_jobs_cache

async def mark_seen(url: str, data: Optional[Dict[str, Any]] = None) -> None:
    """Mark a job URL as seen."""
    if not url:
        return
    
    logger.debug(f"Marking job as seen: {url}")
    _seen_jobs_cache.add(url)
    
    # Try to store in Firestore if available
    if _db:
        try:
            doc_ref = _db.collection("seen_jobs").document(url)
            await asyncio.to_thread(
                doc_ref.set,
                {"url": url, "seen_at": firestore.SERVER_TIMESTAMP, **(data or {})}
            )
        except Exception as e:
            logger.error(f"Error marking job as seen in Firestore: {e}")
    
    # Always save to local file as backup
    try:
        # Save directly without using asyncio.to_thread to debug
        _save_to_local_file()
        logger.debug(f"Saved {len(_seen_jobs_cache)} jobs to local file after marking {url} as seen")
    except Exception as e:
        logger.error(f"Error saving seen jobs to local file: {e}", exc_info=True)

async def has_seen(url: str) -> bool:
    """Check if a job URL has been seen."""
    return url in _seen_jobs_cache

async def cleanup_seen_jobs(days: int = 30) -> None:
    """Remove seen jobs older than the specified number of days."""
    if not _db:
        return
    
    try:
        # Calculate cutoff date
        import datetime
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # Query for old documents
        old_docs = _db.collection("seen_jobs").where("seen_at", "<", cutoff).limit(1000).stream()
        
        # Delete old documents
        batch = _db.batch()
        count = 0
        for doc in old_docs:
            batch.delete(doc.reference)
            if doc.id in _seen_jobs_cache:
                _seen_jobs_cache.remove(doc.id)
            count += 1
            
            # Commit batch when it reaches 500 operations
            if count % 500 == 0:
                await asyncio.to_thread(batch.commit)
                batch = _db.batch()
        
        # Commit any remaining operations
        if count % 500 != 0:
            await asyncio.to_thread(batch.commit)
            
        logger.info(f"Cleaned up {count} old seen job records")
    except Exception as e:
        logger.error(f"Error cleaning up seen jobs: {e}")

def _save_to_local_file() -> None:
    """Save seen jobs to local file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(_LOCAL_SEEN_JOBS_FILE), exist_ok=True)
        logger.debug(f"Saving {len(_seen_jobs_cache)} jobs to {_LOCAL_SEEN_JOBS_FILE}")
        with open(_LOCAL_SEEN_JOBS_FILE, 'w') as f:
            json.dump(list(_seen_jobs_cache), f)
        logger.info(f"Saved {len(_seen_jobs_cache)} seen jobs to {_LOCAL_SEEN_JOBS_FILE}")
    except Exception as e:
        logger.error(f"Error saving seen jobs to local file: {e}", exc_info=True)

async def close_seen_jobs() -> None:
    """Close the seen jobs tracking system."""
    global _db
    
    # Save to local file before closing
    try:
        _save_to_local_file()
    except Exception as e:
        logger.error(f"Error saving seen jobs during close: {e}", exc_info=True)
    
    _db = None
