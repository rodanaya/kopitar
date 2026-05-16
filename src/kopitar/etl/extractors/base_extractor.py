"""
Base Extractor

Abstract base class for all data extractors with common functionality
including rate limiting, retry logic, and error handling.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import aiohttp
import redis
from tenacity import retry, stop_after_attempt, wait_exponential
from dataclasses import dataclass

from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """
    Result of a data extraction operation.
    """
    success: bool
    data: Optional[Any]
    error: Optional[str]
    timestamp: datetime
    source: str
    metadata: Dict[str, Any]


class RateLimiter:
    """
    Redis-based rate limiter for API calls.
    """
    
    def __init__(self, redis_client: redis.Redis, requests_per_minute: int = 100):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
    
    async def acquire(self, key: str) -> bool:
        """
        Attempt to acquire a rate limit token.
        
        Args:
            key: Rate limiting key (e.g., 'nhl_api')
            
        Returns:
            bool: True if request allowed, False if rate limited
        """
        current_time = int(datetime.now().timestamp())
        window_start = current_time - self.window_size
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_count = self.redis.zcard(key)
        
        if current_count >= self.requests_per_minute:
            return False
        
        # Add current request
        self.redis.zadd(key, {str(current_time): current_time})
        self.redis.expire(key, self.window_size)
        
        return True
    
    async def wait_for_slot(self, key: str) -> None:
        """
        Wait until a rate limit slot becomes available.
        
        Args:
            key: Rate limiting key
        """
        while not await self.acquire(key):
            await asyncio.sleep(1)


class BaseExtractor(ABC):
    """
    Abstract base class for all data extractors.
    
    Provides common functionality:
    - Rate limiting
    - Retry logic with exponential backoff
    - Error handling and logging
    - Session management
    - Circuit breaker pattern
    """
    
    def __init__(
        self,
        rate_limit_key: str,
        requests_per_minute: int = 100,
        timeout: float = 30.0,
        max_retries: int = 3
    ):
        self.rate_limit_key = rate_limit_key
        self.requests_per_minute = requests_per_minute
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize Redis client for rate limiting
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            self.redis_client,
            requests_per_minute
        )
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        
        # Session will be created when needed
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    async def session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session with proper configuration.
        """
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                keepalive_timeout=30
            )
            
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': f'Kopitar-NHL-Analytics/{settings.APP_VERSION}',
                    'Accept': 'application/json'
                }
            )
        
        return self._session
    
    async def close(self) -> None:
        """
        Clean up resources.
        """
        if self._session and not self._session.closed:
            await self._session.close()
    
    def is_circuit_open(self) -> bool:
        """
        Check if circuit breaker is open (preventing requests).
        """
        if self.failure_count < self.circuit_breaker_threshold:
            return False
        
        if self.last_failure_time is None:
            return False
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() < self.circuit_breaker_timeout
    
    def record_success(self) -> None:
        """
        Record successful operation (reset circuit breaker).
        """
        self.failure_count = 0
        self.last_failure_time = None
    
    def record_failure(self) -> None:
        """
        Record failed operation (increment circuit breaker).
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        logger.warning(
            f"Extractor failure recorded. Count: {self.failure_count}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def make_request(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> aiohttp.ClientResponse:
        """
        Make HTTP request with rate limiting and retry logic.
        
        Args:
            url: Request URL
            method: HTTP method
            **kwargs: Additional request parameters
            
        Returns:
            aiohttp.ClientResponse: HTTP response
            
        Raises:
            Exception: If circuit breaker is open or request fails
        """
        # Check circuit breaker
        if self.is_circuit_open():
            raise Exception(
                f"Circuit breaker open for {self.rate_limit_key}. "
                f"Failures: {self.failure_count}"
            )
        
        # Wait for rate limit slot
        await self.rate_limiter.wait_for_slot(self.rate_limit_key)
        
        try:
            session = await self.session
            
            logger.debug(f"Making {method} request to {url}")
            
            async with session.request(method, url, **kwargs) as response:
                # Check response status
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(
                        f"HTTP {response.status} error for {url}: {error_text}"
                    )
                    
                    if response.status >= 500:
                        self.record_failure()
                        raise Exception(
                            f"Server error {response.status}: {error_text}"
                        )
                    else:
                        raise Exception(
                            f"Client error {response.status}: {error_text}"
                        )
                
                # Success
                self.record_success()
                return response
                
        except asyncio.TimeoutError:
            self.record_failure()
            logger.error(f"Timeout error for {url}")
            raise Exception(f"Request timeout for {url}")
        
        except Exception as e:
            self.record_failure()
            logger.error(f"Request error for {url}: {str(e)}")
            raise
    
    async def extract_json(
        self,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract JSON data from URL.
        
        Args:
            url: Request URL
            **kwargs: Additional request parameters
            
        Returns:
            Dict[str, Any]: Parsed JSON response
        """
        response = await self.make_request(url, **kwargs)
        return await response.json()
    
    @abstractmethod
    async def extract(self, *args, **kwargs) -> ExtractionResult:
        """
        Extract data from source.
        
        Must be implemented by subclasses.
        """
        pass
    
    def create_result(
        self,
        success: bool,
        data: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        Create standardized extraction result.
        
        Args:
            success: Whether extraction succeeded
            data: Extracted data (if successful)
            error: Error message (if failed)
            metadata: Additional metadata
            
        Returns:
            ExtractionResult: Standardized result object
        """
        return ExtractionResult(
            success=success,
            data=data,
            error=error,
            timestamp=datetime.now(),
            source=self.__class__.__name__,
            metadata=metadata or {}
        )
    
    async def __aenter__(self):
        """
        Async context manager entry.
        """
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        await self.close()