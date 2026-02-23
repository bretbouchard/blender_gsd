"""
Data Acquisition Module

Base classes and utilities for data acquisition from external APIs.
"""

from .base_client import DataClient, RateLimitedClient
from .osm_downloader import OSMDownloader
from .overpass_client import OverpassClient
from .elevation_fetcher import ElevationFetcher
from .poi_extractor import POIExtractor

__all__ = [
    "DataClient",
    "RateLimitedClient",
    "OSMDownloader",
    "OverpassClient",
    "ElevationFetcher",
    "POIExtractor",
]
