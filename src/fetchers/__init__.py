"""
Fetchers package for the IT Internship Finder application.
"""
from .base_fetcher import BaseFetcher
from .internshala_fetcher import InternshalaFetcher
from .rss_fetcher import RssFetcher
from .remoteok_fetcher import RemoteOKFetcher
from .remotive_fetcher import RemotiveFetcher
from .wwr_fetcher import WWRFetcher

__all__ = [
    'BaseFetcher',
    'InternshalaFetcher',
    'RssFetcher',
    'RemoteOKFetcher',
    'RemotiveFetcher',
    'WWRFetcher'
]
