"""Base HTTP client with retry and circuit breaker support."""
import asyncio
from typing import Optional, Dict, Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
import pybreaker
from app.config import settings
from app.exceptions import ExternalAPIError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class BaseHTTPClient:
    """Base HTTP client with retry logic and circuit breaker."""
    
    def __init__(
        self,
        base_url: str,
        timeout: int = None,
        max_retries: int = None,
        circuit_breaker_failure_threshold: int = 5,
        circuit_breaker_timeout: int = 60
    ):
        """
        Initialize base HTTP client.
        
        Args:
            base_url: Base URL for API
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            circuit_breaker_failure_threshold: Failures before opening circuit
            circuit_breaker_timeout: Seconds before attempting to close circuit
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or settings.http_timeout
        self.max_retries = max_retries or settings.http_max_retries
        
        # Create circuit breaker
        self.circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=circuit_breaker_failure_threshold,
            timeout_duration=circuit_breaker_timeout,
            listeners=[self._circuit_breaker_listener]
        )
        
        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
    
    def _circuit_breaker_listener(self, state: str) -> None:
        """Circuit breaker state change listener."""
        logger.warning("circuit_breaker_state_change", state=state, base_url=self.base_url)
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for httpx request
            
        Returns:
            HTTP response
            
        Raises:
            ExternalAPIError: If request fails after retries
        """
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
            reraise=True
        )
        async def _make_request():
            try:
                # Check circuit breaker
                if self.circuit_breaker.current_state == 'open':
                    raise ExternalAPIError(
                        f"Circuit breaker is open for {self.base_url}",
                        service=self.base_url,
                        status_code=503
                    )
                
                # Make request through circuit breaker
                response = await self.circuit_breaker.call_async(
                    self.client.request,
                    method=method,
                    url=url,
                    **kwargs
                )
                
                # Raise for status codes >= 400
                response.raise_for_status()
                return response
                
            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    raise ExternalAPIError(
                        f"Client error from {self.base_url}: {e.response.status_code}",
                        service=self.base_url,
                        status_code=e.response.status_code,
                        details={"response": e.response.text[:500]}
                    )
                # Retry on server errors (5xx)
                raise
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.warning(
                    "http_request_failed",
                    error=str(e),
                    method=method,
                    url=url,
                    base_url=self.base_url
                )
                raise
            except RetryError as e:
                # All retries exhausted
                raise ExternalAPIError(
                    f"Request to {self.base_url} failed after {self.max_retries} retries",
                    service=self.base_url,
                    status_code=502,
                    details={"last_exception": str(e.last_attempt.exception())}
                )
        
        return await _make_request()
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make POST request."""
        return await self._request_with_retry("POST", url, **kwargs)
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make GET request."""
        return await self._request_with_retry("GET", url, **kwargs)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

