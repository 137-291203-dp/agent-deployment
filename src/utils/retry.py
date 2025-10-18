"""
Retry logic utilities with exponential backoff.

This module provides retry functionality for HTTP requests and other operations.
"""

import asyncio
from typing import Callable, Any, Optional
import httpx

from src.core.logging import get_logger

logger = get_logger(__name__)


async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay after each attempt
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Result from func
        
    Raises:
        Last exception if all attempts fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"Succeeded on attempt {attempt}")
            return result
            
        except Exception as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(f"All {max_attempts} attempts failed: {e}")
                raise
            
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            
            # Exponential backoff
            delay = min(delay * backoff_factor, max_delay)
    
    raise last_exception


async def post_with_retry(
    url: str,
    json_data: dict,
    max_attempts: int = 5,
    timeout: float = 30.0
) -> httpx.Response:
    """
    POST JSON data with retry logic.
    
    Args:
        url: URL to POST to
        json_data: JSON data to send
        max_attempts: Maximum number of attempts
        timeout: Request timeout in seconds
        
    Returns:
        httpx.Response object
        
    Raises:
        Exception if all attempts fail
    """
    async def _post():
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=json_data)
            response.raise_for_status()  # Raise exception for 4xx/5xx
            return response
    
    return await retry_with_backoff(
        _post,
        max_attempts=max_attempts,
        initial_delay=1.0,
        backoff_factor=2.0
    )


async def get_with_retry(
    url: str,
    max_attempts: int = 3,
    timeout: float = 30.0
) -> httpx.Response:
    """
    GET with retry logic.
    
    Args:
        url: URL to GET
        max_attempts: Maximum number of attempts
        timeout: Request timeout in seconds
        
    Returns:
        httpx.Response object
        
    Raises:
        Exception if all attempts fail
    """
    async def _get():
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response
    
    return await retry_with_backoff(
        _get,
        max_attempts=max_attempts,
        initial_delay=1.0,
        backoff_factor=2.0
    )
