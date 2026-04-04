"""
Helper functions to reduce code duplication.

Provides utilities for:
- HTTP requests with error handling and timeouts
- Response creation
- Network/graph operations
"""

import requests
from typing import Dict, Any, Optional, List, Type, TypeVar
from functools import wraps
import time

from app.utils.logger import logger
from app.constants import DEFAULT_REQUEST_TIMEOUT, DEFAULT_RETRY_COUNT, DEFAULT_RETRY_DELAY
from app.exceptions import RequestTimeoutError, RequestFailedError, SchemaValidationError
from app.api.schemas import BaseResponse

T = TypeVar("T")


# ============================================================================
# HTTP Request Helpers
# ============================================================================

def safe_request(
    method: str,
    url: str,
    timeout: float = DEFAULT_REQUEST_TIMEOUT,
    max_retries: int = DEFAULT_RETRY_COUNT,
    **kwargs
) -> requests.Response:
    """
    Make an HTTP request with timeout, retries, and error handling.
    
    Args:
        method: HTTP method ('GET', 'POST', 'PUT', 'DELETE')
        url: URL to request
        timeout: Request timeout in seconds
        max_retries: Number of retries on failure
        **kwargs: Additional arguments to pass to requests
        
    Returns:
        requests.Response object
        
    Raises:
        RequestTimeoutError: If request times out
        RequestFailedError: If request fails after retries
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.Timeout as e:
            last_exception = RequestTimeoutError(f"Request to {url} timed out after {timeout}s")
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: Timeout - {e}")
            
        except requests.exceptions.ConnectionError as e:
            last_exception = RequestFailedError(f"Connection failed: {e}")
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: Connection error - {e}")
            
        except requests.exceptions.HTTPError as e:
            last_exception = RequestFailedError(f"HTTP {e.response.status_code}: {e}")
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: HTTP error - {e}")
            
        except Exception as e:
            last_exception = RequestFailedError(f"Request failed: {e}")
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: Unexpected error - {e}")
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:
            time.sleep(DEFAULT_RETRY_DELAY)
    
    # All retries exhausted
    if last_exception:
        raise last_exception
    else:
        raise RequestFailedError(f"Request to {url} failed after {max_retries} attempts")


def get_json(url: str, **kwargs) -> Dict[str, Any]:
    """
    Make a GET request and return JSON response.
    
    Args:
        url: URL to GET
        **kwargs: Additional arguments to pass to safe_request
        
    Returns:
        Parsed JSON response
    """
    response = safe_request("GET", url, **kwargs)
    try:
        return response.json()
    except ValueError as e:
        raise RequestFailedError(f"Invalid JSON response from {url}: {e}")


def post_json(url: str, data: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """
    Make a POST request with JSON body and return JSON response.
    
    Args:
        url: URL to POST to
        data: JSON body data
        **kwargs: Additional arguments to pass to safe_request
        
    Returns:
        Parsed JSON response
    """
    kwargs["json"] = data or {}
    response = safe_request("POST", url, **kwargs)
    try:
        return response.json()
    except ValueError as e:
        raise RequestFailedError(f"Invalid JSON response from {url}: {e}")


# ============================================================================
# Response Helpers
# ============================================================================

def create_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    **extra_fields
) -> BaseResponse:
    """
    Create a standardized API response.
    
    Args:
        success: Whether the operation was successful
        message: Response message
        data: Response data (optional)
        **extra_fields: Additional fields to include in response
        
    Returns:
        BaseResponse object
    """
    return BaseResponse(
        success=success,
        message=message,
        data=data,
        **extra_fields
    )


def success_response(message: str, data: Optional[Dict[str, Any]] = None) -> BaseResponse:
    """Create a success response."""
    return create_response(success=True, message=message, data=data)


def error_response(message: str, data: Optional[Dict[str, Any]] = None) -> BaseResponse:
    """Create an error response."""
    return create_response(success=False, message=message, data=data)


# ============================================================================
# Network/Graph Helpers
# ============================================================================

def create_default_network_nodes() -> List[Dict[str, Any]]:
    """
    Create default network node configuration.
    
    Returns list of node dictionaries with location and capacity.
    This centralizes the network topology definition.
    
    Returns:
        List of node configuration dicts
    """
    from app.constants import DEFAULT_NETWORK_NODES_CONFIG
    return DEFAULT_NETWORK_NODES_CONFIG.copy()


def create_default_network_edges() -> List[Dict[str, Any]]:
    """
    Create default network edge configuration.
    
    Returns list of edge dictionaries with time, cost, and carbon metrics.
    
    Returns:
        List of edge configuration dicts
    """
    # Standard edge configuration (can be customized)
    return [
        # From Warehouse
        {"source": 0, "target": 1, "time": 2.0, "cost": 100.0, "carbon": 50.0},
        {"source": 0, "target": 2, "time": 1.5, "cost": 80.0, "carbon": 30.0},
        {"source": 0, "target": 3, "time": 1.0, "cost": 120.0, "carbon": 60.0},
        {"source": 0, "target": 4, "time": 0.5, "cost": 50.0, "carbon": 20.0},
        
        # From Port A
        {"source": 1, "target": 5, "time": 3.0, "cost": 150.0, "carbon": 75.0},
        {"source": 1, "target": 0, "time": 2.0, "cost": 100.0, "carbon": 50.0},
        
        # From Rail Hub
        {"source": 2, "target": 5, "time": 2.0, "cost": 90.0, "carbon": 25.0},
        {"source": 2, "target": 0, "time": 1.5, "cost": 80.0, "carbon": 30.0},
        
        # From Air Terminal
        {"source": 3, "target": 5, "time": 0.5, "cost": 200.0, "carbon": 100.0},
        {"source": 3, "target": 0, "time": 1.0, "cost": 120.0, "carbon": 60.0},
        
        # From Truck Terminal
        {"source": 4, "target": 5, "time": 1.0, "cost": 60.0, "carbon": 25.0},
        {"source": 4, "target": 0, "time": 0.5, "cost": 50.0, "carbon": 20.0},
        
        # From Destination (return routes)
        {"source": 5, "target": 0, "time": 2.5, "cost": 110.0, "carbon": 55.0},
        {"source": 5, "target": 1, "time": 3.0, "cost": 150.0, "carbon": 75.0},
        {"source": 5, "target": 2, "time": 2.0, "cost": 90.0, "carbon": 25.0},
        {"source": 5, "target": 3, "time": 0.5, "cost": 200.0, "carbon": 100.0},
        {"source": 5, "target": 4, "time": 1.0, "cost": 60.0, "carbon": 25.0},
    ]


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_schema(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields exist in data.
    
    Args:
        data: Data to validate
        required_fields: List of required field names
        
    Raises:
        SchemaValidationError: If required fields are missing
    """
    missing = [field for field in required_fields if field not in data]
    if missing:
        raise SchemaValidationError(f"Missing required fields: {', '.join(missing)}")


def safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary with a default fallback.
    
    Args:
        data: Dictionary to get from
        key: Key to retrieve
        default: Default value if key not found
        
    Returns:
        Value from dictionary or default
    """
    return data.get(key, default)


# ============================================================================
# Retry Decorator
# ============================================================================

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 1.0):
    """
    Decorator to retry a function on exception.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed: {e}"
                    )
                    
                    if attempt < max_attempts:
                        time.sleep(attempt_delay)
                        attempt_delay *= backoff
            
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator
