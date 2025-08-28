"""
Utility functions and classes for the IT Internship Finder.
"""
from .helpers import (
    setup_logging,
    parse_relative_date,
    clean_text,
    extract_emails,
    is_it_related,
    fetch_url,
    extract_json_ld,
    format_internship_message,
    chunk_list,
    safe_get,
    filter_last_24_hours
)

from .seen_jobs import (
    get_seen_jobs,
    initialize_seen_jobs,
    cleanup_seen_jobs,
    close_seen_jobs,
    mark_seen,
    has_seen
)

__all__ = [
    'setup_logging',
    'parse_relative_date',
    'clean_text',
    'extract_emails',
    'get_seen_jobs',
    'initialize_seen_jobs',
    'cleanup_seen_jobs',
    'close_seen_jobs',
    'mark_seen',
    'has_seen',
    'is_it_related',
    'fetch_url',
    'extract_json_ld',
    'format_internship_message',
    'chunk_list',
    'safe_get',
    'filter_last_24_hours',
    'SeenJobs',
    'get_seen_jobs',
    'initialize_seen_jobs',
    'cleanup_seen_jobs',
    'close_seen_jobs'
]
