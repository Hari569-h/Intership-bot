#!/usr/bin/env python3
"""
Fixed main script for the IT Internship Finder Bot.
- Uses firebase_admin (sync) but runs blocking Firestore calls in asyncio.to_thread
- Initializes fetchers once and calls their async/sync initialize if present
- Loads seen URLs from Firestore into memory to skip duplicates
- Filters to last 24 hours and sends grouped Telegram messages (chunked)
"""
from __future__ import annotations

import asyncio
import json
import logging
import logging.config
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

import aiohttp
import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

# project imports (adjust paths if your structure differs)
from .config import (FIREBASE_CREDENTIALS, RSS_FEEDS, WEB_SCRAPERS,
                    IT_KEYWORDS, LOGGING_CONFIG, LOCATION_FILTERS)
from .fetchers.rss_fetcher import RssFetcher
from .models.internship import Internship
from .utils.helpers import (setup_logging, format_internship_message,
                           chunk_list, filter_last_24_hours, is_it_related)

# Optional fetchers — import inside function to avoid import-time errors
# from .fetchers.internshala_fetcher import InternshalaFetcher
# from .fetchers.remoteok_fetcher import RemoteOKFetcher
# from .fetchers.remotive_fetcher import RemotiveFetcher
# from .fetchers.wwr_fetcher import WWRFetcher

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class InternshipFinderBot:
    """Main bot class for finding and notifying about internships."""

    def __init__(self):
        # Initialize logging
        setup_logging()
        self.logger = logging.getLogger(__name__)

        # Initialize Firebase (supports either JSON env or file path)
        self._init_firebase()

        # Firestore client (synchronous) and collection
        self.db = firestore.client()
        self.collection = self.db.collection("internships")

        # In-memory seen URL cache (doc IDs or raw URLs)
        self.seen_urls: Set[str] = set()

        # Fetchers list
        self.fetchers = self._initialize_fetchers_once()

        # aiohttp session reused for Telegram posting
        self.aiohttp_session: Optional[aiohttp.ClientSession] = None

    def _init_firebase(self) -> None:
        """
        Initialize firebase_admin app. Supports:
        - FIREBASE_CREDENTIALS_JSON (full JSON contents as env var, preferred for GH Actions)
        - FIREBASE_CREDENTIALS (path to JSON file)
        If neither is present, we will NOT initialize and Firestore calls will fail.
        """
        if firebase_admin._apps:
            return

        cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        cred_path = os.getenv("FIREBASE_CREDENTIALS") or FIREBASE_CREDENTIALS

        try:
            if cred_json:
                # GitHub Actions: secret contains full JSON
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                self.logger.info("Initialized Firebase from FIREBASE_CREDENTIALS_JSON")
            elif cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                self.logger.info("Initialized Firebase from FIREBASE_CREDENTIALS path")
            else:
                # Attempt default application credentials
                firebase_admin.initialize_app()
                self.logger.info("Initialized Firebase using default application credentials")
        except Exception as e:
            # Do not crash here — log and let code handle missing DB
            self.logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)

    def _initialize_fetchers_once(self) -> List[Any]:
        """
        Build fetcher instances based on config. This only *creates* instances.
        Each fetcher may optionally implement an async `initialize()` method which will
        be called during `initialize()`.
        """
        from .fetchers import (
            RssFetcher,
        )

        # dynamic imports for optional fetchers (avoid hard crash if file missing)
        fetchers = []

        # RSS fetcher
        if RSS_FEEDS:
            fetchers.append(RssFetcher(RSS_FEEDS))

        # Conditional add of other fetchers depending on configuration
        try:
            if WEB_SCRAPERS.get("remoteok", {}).get("enabled", True):
                from .fetchers.remoteok_fetcher import RemoteOKFetcher

                cfg = WEB_SCRAPERS.get("remoteok", {})
                fetchers.append(
                    RemoteOKFetcher(
                        max_retries=cfg.get("max_retries", 3),
                        timeout=cfg.get("timeout", 30.0),
                    )
                )
        except Exception:
            self.logger.exception("RemoteOK fetcher not available or failed to import")

        try:
            if WEB_SCRAPERS.get("remotive", {}).get("enabled", True):
                from .fetchers.remotive_fetcher import RemotiveFetcher

                cfg = WEB_SCRAPERS.get("remotive", {})
                fetchers.append(
                    RemotiveFetcher(
                        max_retries=cfg.get("max_retries", 3),
                        timeout=cfg.get("timeout", 30.0),
                    )
                )
        except Exception:
            self.logger.exception("Remotive fetcher not available or failed to import")

        try:
            if WEB_SCRAPERS.get("wwr", {}).get("enabled", True):
                from .fetchers.wwr_fetcher import WWRFetcher

                cfg = WEB_SCRAPERS.get("wwr", {})
                fetchers.append(
                    WWRFetcher(
                        max_retries=cfg.get("max_retries", 3),
                        timeout=cfg.get("timeout", 30.0),
                    )
                )
        except Exception:
            self.logger.exception("WWR fetcher not available or failed to import")

        # Internshala disabled by default due to CAPTCHA; enable only if configured
        try:
            if WEB_SCRAPERS.get("internshala", {}).get("enabled", False):
                from .fetchers.internshala_fetcher import InternshalaFetcher

                cfg = WEB_SCRAPERS.get("internshala", {})
                fetchers.append(
                    InternshalaFetcher(max_pages=cfg.get("max_pages", 3))
                )
        except Exception:
            self.logger.exception("Internshala fetcher not available or failed to import")

        self.logger.info(f"Prepared {len(fetchers)} fetcher instances")
        return fetchers

    async def initialize(self) -> None:
        """Initialize runtime resources and fetchers (call their initialize if present)."""
        # load seen URLs into memory
        await self._load_seen_urls()

        # call initialize() on each fetcher if available (some may be sync)
        initialized = []
        for f in self.fetchers:
            try:
                init = getattr(f, "initialize", None)
                if callable(init):
                    # If initialize is coroutine, await it
                    if asyncio.iscoroutinefunction(init):
                        ok = await init()
                    else:
                        ok = init()
                    if ok is False:
                        self.logger.warning(f"Fetcher {f} reported initialize failure")
                        continue
                initialized.append(f)
            except Exception:
                self.logger.exception(f"Failed to initialize fetcher {f}")
        self.fetchers = initialized
        self.logger.info(f"Initialized {len(self.fetchers)} fetchers")

        # create aiohttp session for sending Telegram messages
        self.aiohttp_session = aiohttp.ClientSession()

    async def cleanup(self) -> None:
        """Cleanup resources."""
        # attempt to close fetchers if they have cleanup()
        for f in self.fetchers:
            try:
                cl = getattr(f, "cleanup", None)
                if callable(cl):
                    if asyncio.iscoroutinefunction(cl):
                        await cl()
                    else:
                        cl()
            except Exception:
                self.logger.exception(f"Error during fetcher cleanup: {f}")

        # close aiohttp session
        if self.aiohttp_session:
            await self.aiohttp_session.close()

    async def _load_seen_urls(self, batch_size: int = 2000) -> None:
        """Load seen URLs from local file or Firestore."""
        self.seen_urls = set()
        
        # Define local file path with absolute path to ensure it works correctly
        local_file = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seen_urls.json'))
        self.logger.info(f"Local seen URLs file path: {local_file}")
        
        # Try to load from local file first
        loaded_from_local = False
        try:
            if os.path.exists(local_file):
                with open(local_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.seen_urls.update(data)
                        self.logger.info(f"Loaded {len(self.seen_urls)} seen URLs from local file")
                        loaded_from_local = True
        except Exception as e:
            self.logger.error(f"Error loading seen URLs from local file: {e}", exc_info=True)
        
        # Try to load from Firestore if local file failed or to merge with local data
        try:
            # Use to_thread because stream() and iteration are sync blocking
            def _fetch_ids():
                try:
                    docs = list(self.collection.stream())
                    return {d.id for d in docs}
                except Exception as e:
                    logger.exception("Error loading seen URLs from Firestore")
                    return set()

            ids = await asyncio.to_thread(_fetch_ids)
            if ids:
                # Merge with existing URLs
                original_count = len(self.seen_urls)
                self.seen_urls.update(ids)
                new_count = len(self.seen_urls) - original_count
                self.logger.info(f"Loaded {len(ids)} seen URLs from Firestore (added {new_count} new URLs)")
                
                # If we loaded from both sources, save the merged set back to local file
                if loaded_from_local and new_count > 0:
                    try:
                        with open(local_file, 'w') as f:
                            json.dump(list(self.seen_urls), f)
                        self.logger.info(f"Saved merged set of {len(self.seen_urls)} URLs to local file")
                    except Exception as e:
                        self.logger.error(f"Failed to save merged URLs to local file: {e}", exc_info=True)
        except Exception as e:
            self.logger.exception(f"Failed to load seen URLs from Firestore: {e}")
            if not self.seen_urls:
                self.logger.warning("Starting with empty set of seen URLs")
                self.seen_urls = set()

    @staticmethod
    def _encode_doc_id(url: str) -> str:
        """Make a safe doc id from URL (reuse logic from seen_jobs)."""
        encoded = re.sub(r"[^a-zA-Z0-9\-_.~]", "_", url)
        if len(encoded) > 1400:
            import hashlib

            return hashlib.sha256(url.encode()).hexdigest()
        return encoded

    async def is_duplicate(self, url: str) -> bool:
        """Check memory cache for duplicates. (Firestore was loaded at startup)."""
        return url in self.seen_urls

    async def save_internship(self, internship: Internship) -> None:
        """Save internship to Firestore and local file."""
        try:
            # Try to save to Firestore
            try:
                doc_id = self._encode_doc_id(internship.url)
                data = {k: v for k, v in internship.to_dict().items() if v is not None}

                def _set():
                    doc_ref = self.collection.document(doc_id)
                    doc_ref.set(data, merge=True)

                await asyncio.to_thread(_set)
                self.logger.debug(f"Saved internship to Firestore: {internship.title}")
            except Exception as e:
                self.logger.error(f"Failed to save internship to Firestore: {e}", exc_info=True)
            
            # Update cache
            self.seen_urls.add(internship.url)
            
            # Save to local file with absolute path
            try:
                local_file = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'seen_urls.json'))
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_file), exist_ok=True)
                with open(local_file, 'w') as f:
                    json.dump(list(self.seen_urls), f)
                self.logger.debug(f"Saved {len(self.seen_urls)} URLs to local file: {local_file}")
            except Exception as e:
                self.logger.error(f"Failed to save URLs to local file: {e}", exc_info=True)
                
            self.logger.debug(f"Saved internship: {internship.title} ({internship.url})")
        except Exception as e:
            self.logger.exception(f"Failed to save internship: {internship.url}: {e}")

    async def _process_fetcher(self, fetcher) -> List[Internship]:
        """Run a single fetcher and return its list of internships (already filtered by fetcher)."""
        try:
            self.logger.info(f"Running fetcher: {fetcher.__class__.__name__}")
            # fetch may be coroutine or sync method
            fetch = getattr(fetcher, "fetch")
            if asyncio.iscoroutinefunction(fetch):
                internships = await fetch()
            else:
                internships = await asyncio.to_thread(fetch)
            return internships or []
        except Exception:
            self.logger.exception(f"Fetcher {fetcher} failed")
            return []

    async def fetch_all_internships(self) -> List[Internship]:
        """Run all fetchers concurrently and collect results."""
        if not self.fetchers:
            self.logger.warning("No fetchers configured")
            return []

        tasks = [self._process_fetcher(f) for f in self.fetchers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_jobs: List[Internship] = []
        for r in results:
            if isinstance(r, Exception):
                self.logger.error(f"Fetcher returned exception: {r}")
            else:
                all_jobs.extend(r)
        self.logger.info(f"Collected {len(all_jobs)} internships from all fetchers")
        return all_jobs

    async def send_telegram_notification(self, internships: List[Internship], is_daily_update: bool = False) -> None:
        """Send grouped Telegram notifications (chunks)."""
        if not internships:
            self.logger.info("No internships to send")
            return

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            self.logger.warning("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in env")
            return

        # create session if not present
        session = self.aiohttp_session or aiohttp.ClientSession()

        chunks = chunk_list(internships, 5)
        for chunk in chunks:
            message = "🎯 *New IT Internships Found!* 🎯\n\n"
            for i, inst in enumerate(chunk, start=1):
                message += format_internship_message(inst, i) + "\n"

            footer = "\n_🔔 Daily update: Check back soon for more opportunities!_" if is_daily_update else "\n_🔔 Check back soon for more opportunities!_"
            message += footer

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            try:
                async with session.post(url, json=payload, timeout=30) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                        self.logger.error(f"Telegram error {resp.status}: {text}")
                    else:
                        self.logger.info(f"Sent Telegram message with {len(chunk)} internships")
            except Exception:
                self.logger.exception("Failed to send message to Telegram")

        if self.aiohttp_session is None:
            await session.close()

    async def run(self) -> None:
        """Main entrypoint: initialize, fetch, filter, dedupe, save and notify."""
        try:
            await self.initialize()

            # Fetch all internships
            all_internships = await self.fetch_all_internships()

            if not all_internships:
                self.logger.info("No internships returned by fetchers")
                await self.send_daily_summary_notification()
                return

            # Filter IT-related (uses helper)
            it_filtered = [
                i for i in all_internships
                if (i.title and is_it_related(i.title, IT_KEYWORDS)) or
                (i.description and is_it_related(i.description, IT_KEYWORDS))
            ]
            self.logger.info(f"Filtered to {len(it_filtered)} IT-related internships")
            
            # Filter by location if LOCATION_FILTERS is not empty
            if LOCATION_FILTERS:
                location_filtered = []
                for internship in it_filtered:
                    if internship.location:
                        location_lower = internship.location.lower()
                        if any(loc.lower() in location_lower for loc in LOCATION_FILTERS):
                            location_filtered.append(internship)
                self.logger.info(f"Filtered to {len(location_filtered)} internships in {', '.join(LOCATION_FILTERS)}")
                it_filtered = location_filtered

            # Convert to dicts and filter last 24 hours (helper expects dicts)
            dicts = [i.to_dict() for i in it_filtered]
            recent_dicts = filter_last_24_hours(dicts)
            recent_urls = {d["url"] for d in recent_dicts if d.get("url")}

            # Keep only Internship objects matching recent urls
            recent_internships = [i for i in it_filtered if i.url in recent_urls]

            # Skip those already seen (by memory cache)
            fresh = []
            for inst in recent_internships:
                if await self.is_duplicate(inst.url):
                    self.logger.debug(f"Skipping already sent job: {inst.url}")
                    continue
                fresh.append(inst)

            if fresh:
                # Save + send
                for inst in fresh:
                    await self.save_internship(inst)
                await self.send_telegram_notification(fresh, is_daily_update=True)
                self.logger.info(f"Sent notifications for {len(fresh)} new internships")
            else:
                await self.send_daily_summary_notification()
                self.logger.info("No new internships to notify")

        except Exception:
            self.logger.exception("Fatal error in run()")
            raise
        finally:
            await self.cleanup()

    async def send_daily_summary_notification(self) -> None:
        """Sends a daily summary when no new internships found."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            self.logger.warning("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in env")
            return

        session = self.aiohttp_session or aiohttp.ClientSession()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": "📅 *Daily Summary: No new IT internships found today!* 📅",
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            async with session.post(url, json=payload, timeout=20) as resp:
                if resp.status != 200:
                    self.logger.error("Failed to send daily summary")
                else:
                    self.logger.info("Daily summary sent")
        except Exception:
            self.logger.exception("Failed to send daily summary")
        if self.aiohttp_session is None:
            await session.close()


if __name__ == "__main__":
    bot = InternshipFinderBot()
    asyncio.run(bot.run())
