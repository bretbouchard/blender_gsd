"""
Base Data Client

Provides base class for data acquisition with rate limiting,
caching, and retry logic as recommended by Automation Rick.
"""

import time
import json
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Cache entry for API responses."""
    data: Any
    timestamp: float
    ttl_seconds: float
    source_url: str

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.timestamp > self.ttl_seconds


class DataClient(ABC):
    """
    Abstract base class for data clients.

    Provides:
    - Rate limiting
    - Caching
    - Retry logic
    - Error handling
    """

    # Rate limiting (override in subclass)
    RATE_LIMIT: float = 1.0  # seconds between requests
    MAX_RETRIES: int = 3

    # Caching
    CACHE_DIR: Path = Path("data/charlotte/cache")
    CACHE_TTL_DAYS: int = 7

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        rate_limit: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        """Initialize the data client."""
        self.cache_dir = cache_dir or self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.rate_limit = rate_limit if rate_limit is not None else self.RATE_LIMIT
        self.max_retries = max_retries if max_retries is not None else self.MAX_RETRIES

        self._last_request_time: float = 0.0
        self._cache: Dict[str, CacheEntry] = {}

    def _rate_limit_wait(self) -> None:
        """Wait if necessary to respect rate limiting."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from URL and parameters."""
        key_data = url
        if params:
            key_data += json.dumps(params, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get path to cache file."""
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """Load data from cache if available and not expired."""
        # Check memory cache first
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                return entry.data

        # Check file cache
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached = json.load(f)

                entry = CacheEntry(
                    data=cached['data'],
                    timestamp=cached['timestamp'],
                    ttl_seconds=self.CACHE_TTL_DAYS * 24 * 3600,
                    source_url=cached.get('source_url', ''),
                )

                if not entry.is_expired():
                    self._cache[cache_key] = entry
                    return entry.data
            except (json.JSONDecodeError, KeyError):
                pass

        return None

    def _save_to_cache(
        self,
        cache_key: str,
        data: Any,
        source_url: str = "",
    ) -> None:
        """Save data to cache."""
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl_seconds=self.CACHE_TTL_DAYS * 24 * 3600,
            source_url=source_url,
        )

        # Save to memory cache
        self._cache[cache_key] = entry

        # Save to file cache
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'data': data,
                    'timestamp': entry.timestamp,
                    'source_url': source_url,
                }, f)
        except (TypeError, ValueError):
            # Data not JSON serializable, skip file cache
            pass

    def _retry_request(
        self,
        request_func,
        *args,
        **kwargs
    ) -> Any:
        """Execute request with retry logic and exponential backoff."""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                self._rate_limit_wait()
                return request_func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)

        raise last_error

    @abstractmethod
    def fetch(self, *args, **kwargs) -> Any:
        """Fetch data from the source. Override in subclass."""
        pass


class RateLimitedClient(DataClient):
    """
    Rate-limited HTTP client with caching.

    Use for external APIs that require rate limiting.
    """

    def __init__(
        self,
        base_url: str,
        rate_limit: float = 1.0,
        timeout: float = 30.0,
        **kwargs
    ):
        """Initialize the rate-limited client."""
        super().__init__(rate_limit=rate_limit, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

        # Try to import requests
        try:
            import requests
            self._requests = requests
        except ImportError:
            self._requests = None

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        method: str = "GET",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Make HTTP request with caching and retry logic."""
        if self._requests is None:
            raise ImportError("requests library required for HTTP client")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        cache_key = self._get_cache_key(url, params)

        # Check cache
        if use_cache:
            cached = self._load_from_cache(cache_key)
            if cached is not None:
                return cached

        def _request():
            if method.upper() == "GET":
                response = self._requests.get(url, params=params, timeout=self.timeout)
            else:
                response = self._requests.post(url, json=params, timeout=self.timeout)

            response.raise_for_status()
            return response.json()

        result = self._retry_request(_request)

        # Cache result
        if use_cache:
            self._save_to_cache(cache_key, result, url)

        return result

    def fetch(
        self,
        endpoint: str,
        params: Optional[Dict] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Fetch data from endpoint."""
        return self._make_request(endpoint, params, use_cache=use_cache)


__all__ = [
    "CacheEntry",
    "DataClient",
    "RateLimitedClient",
]
