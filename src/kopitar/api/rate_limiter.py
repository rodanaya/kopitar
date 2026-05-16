"""
Rate Limiting for NHL API Requests

Implements token bucket algorithm for API rate limiting with configurable
limits and burst handling.
"""

import time
import asyncio
from typing import Optional
from threading import Lock
from dataclasses import dataclass
from .exceptions import RateLimitError


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 100
    burst_size: int = 10
    backoff_factor: float = 2.0
    max_retries: int = 3


class RateLimiter:
    """
    Token bucket rate limiter for NHL API requests.
    
    Ensures we don't exceed NHL API rate limits while allowing
    for reasonable burst capacity.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._tokens = float(self.config.burst_size)
        self._last_update = time.time()
        self._lock = Lock()
        
        # Calculate token replenishment rate
        self._replenish_rate = self.config.requests_per_minute / 60.0
        
    def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens for API request.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            True if tokens acquired, False if rate limited
        """
        with self._lock:
            now = time.time()
            time_passed = now - self._last_update
            
            # Add tokens based on time passed
            self._tokens = min(
                self.config.burst_size,
                self._tokens + time_passed * self._replenish_rate
            )
            self._last_update = now
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False
    
    def wait_time(self, tokens: int = 1) -> float:
        """
        Calculate wait time until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Time to wait in seconds
        """
        with self._lock:
            if self._tokens >= tokens:
                return 0.0
                
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / self._replenish_rate
            return max(0.0, wait_time)
    
    async def acquire_async(self, tokens: int = 1) -> None:
        """
        Asynchronously acquire tokens, waiting if necessary.
        
        Args:
            tokens: Number of tokens to acquire
        """
        while not self.acquire(tokens):
            wait_time = self.wait_time(tokens)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
    
    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        with self._lock:
            self._tokens = float(self.config.burst_size)
            self._last_update = time.time()


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts based on API responses.
    
    Automatically backs off when rate limit errors are encountered
    and gradually increases rate when successful.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config)
        self._current_rate = self.config.requests_per_minute
        self._consecutive_successes = 0
        self._consecutive_failures = 0
        
    def on_success(self) -> None:
        """Called when API request succeeds."""
        self._consecutive_successes += 1
        self._consecutive_failures = 0
        
        # Gradually increase rate after sustained success
        if self._consecutive_successes >= 10:
            self._current_rate = min(
                self.config.requests_per_minute,
                self._current_rate * 1.1
            )
            self._consecutive_successes = 0
            self._update_replenish_rate()
    
    def on_rate_limit(self) -> None:
        """Called when rate limit error occurs."""
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        
        # Exponentially back off
        backoff_factor = self.config.backoff_factor ** self._consecutive_failures
        self._current_rate = max(
            self.config.requests_per_minute * 0.1,  # Minimum 10% of original rate
            self._current_rate / backoff_factor
        )
        self._update_replenish_rate()
    
    def _update_replenish_rate(self) -> None:
        """Update token replenishment rate based on current rate."""
        with self._lock:
            self._replenish_rate = self._current_rate / 60.0
    
    @property
    def current_rate(self) -> float:
        """Get current effective rate limit."""
        return self._current_rate


class CircuitBreaker:
    """
    Circuit breaker pattern for API reliability.
    
    Prevents cascading failures by temporarily stopping requests
    when error rate is too high.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = RateLimitError
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open
        self._lock = Lock()
    
    def __enter__(self):
        with self._lock:
            if self._state == "open":
                if (time.time() - self._last_failure_time) > self.recovery_timeout:
                    self._state = "half-open"
                else:
                    raise RateLimitError("Circuit breaker is open")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        with self._lock:
            if exc_type is None:
                # Success
                self._on_success()
            elif issubclass(exc_type, self.expected_exception):
                # Expected failure
                self._on_failure()
            # Let other exceptions propagate
    
    def _on_success(self) -> None:
        """Handle successful request."""
        self._failure_count = 0
        self._state = "closed"
    
    def _on_failure(self) -> None:
        """Handle failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = "open"
    
    @property
    def state(self) -> str:
        """Get current circuit breaker state."""
        return self._state