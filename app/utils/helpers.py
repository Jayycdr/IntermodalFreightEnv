"""
Helper functions to reduce code duplication.

Provides utilities for:
- HTTP requests with error handling and timeouts
- Response creation
- Network/graph operations

Usage:
    from app.utils.helpers import safe_request, success_response, safe_get
    
    response = safe_request("GET", "http://api/endpoint", timeout=5.0)
    api_response = success_response("Operation completed", {"result": data})
    value = safe_get(data, "key", default="default_value")
"""

import requests
from typing import Dict, Any, Optional, List, Type, TypeVar, Callable
from functools import wraps
import time

from app.utils.logger import logger
from app.constants import DEFAULT_REQUEST_TIMEOUT, DEFAULT_RETRY_COUNT, DEFAULT_RETRY_DELAY
from app.exceptions import RequestTimeoutError, RequestFailedError, SchemaValidationError
from app.api.schemas import BaseResponse

T = TypeVar("T")


# ============================================================================
# Type Definitions
# ============================================================================

class HTTPResponse(dict):
    """Type hint for HTTP response dictionaries."""
    pass


class NetworkNode(dict):
    """Type hint for network node configuration."""
    pass


class NetworkEdge(dict):
    """Type hint for network edge configuration."""
    pass


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


# ============================================================================
# Agent Learning Helpers (NEW: For RL Agent Training)
# ============================================================================

def normalize_state(
    state: Dict[str, Any],
    min_vals: Optional[Dict[str, float]] = None,
    max_vals: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Normalize environment state for agent learning.
    
    Converts raw state values to [0, 1] range using min-max normalization.
    This helps agents learn better by having bounded, comparable features.
    
    Args:
        state: Raw environment state
        min_vals: Optional dict of minimum values per key
        max_vals: Optional dict of maximum values per key
        
    Returns:
        Normalized state dict with values in [0, 1] range
        
    Example:
        >>> state = {"distance": 500, "cost": 150, "carbon": 50}
        >>> min_v = {"distance": 0, "cost": 0, "carbon": 0}
        >>> max_v = {"distance": 1000, "cost": 500, "carbon": 100}
        >>> normalized = normalize_state(state, min_v, max_v)
        >>> # Result: {"distance": 0.5, "cost": 0.3, "carbon": 0.5}
    """
    normalized = {}
    
    for key, value in state.items():
        if isinstance(value, (int, float)):
            # Use provided bounds or default to open interval
            min_val = min_vals.get(key, 0.0) if min_vals else 0.0
            max_val = max_vals.get(key, 1.0) if max_vals else 1.0
            
            # Handle edge case where min == max
            if max_val - min_val == 0:
                normalized[key] = 0.5  # Default to middle
            else:
                # Min-max normalization to [0, 1]
                norm_value = (value - min_val) / (max_val - min_val)
                # Clip to [0, 1] range
                normalized[key] = max(0.0, min(1.0, norm_value))
        else:
            # Keep non-numeric values as-is
            normalized[key] = value
    
    return normalized


def state_to_vector(state: Dict[str, Any], key_order: Optional[List[str]] = None) -> List[float]:
    """
    Convert normalized state dict to feature vector for neural networks.
    
    Args:
        state: Normalized state dictionary
        key_order: Specific order for extracting features (for consistency)
        
    Returns:
        List of float values for use in ML models
        
    Example:
        >>> state = {"distance": 0.5, "cost": 0.3, "carbon": 0.5}
        >>> vector = state_to_vector(state, ["distance", "cost", "carbon"])
        >>> # Result: [0.5, 0.3, 0.5]
    """
    if key_order is None:
        # Use sorted keys for consistency
        key_order = sorted([k for k, v in state.items() if isinstance(v, (int, float))])
    
    vector = []
    for key in key_order:
        if key in state and isinstance(state[key], (int, float)):
            vector.append(float(state[key]))
    
    return vector


def calculate_state_statistics(
    states: List[Dict[str, Any]]
) -> tuple:
    """
    Calculate min/max values from a list of states for normalization.
    
    Useful for determining the bounds needed for normalize_state().
    
    Args:
        states: List of state dictionaries from multiple episodes
        
    Returns:
        Tuple of (min_vals, max_vals) dictionaries
        
    Example:
        >>> states = [
        ...     {"distance": 100, "cost": 50},
        ...     {"distance": 500, "cost": 150},
        ...     {"distance": 300, "cost": 80},
        ... ]
        >>> min_v, max_v = calculate_state_statistics(states)
        >>> # min_v: {"distance": 100, "cost": 50}
        >>> # max_v: {"distance": 500, "cost": 150}
    """
    if not states:
        return {}, {}
    
    min_vals = {}
    max_vals = {}
    
    for state in states:
        for key, value in state.items():
            if isinstance(value, (int, float)):
                if key not in min_vals:
                    min_vals[key] = value
                    max_vals[key] = value
                else:
                    min_vals[key] = min(min_vals[key], value)
                    max_vals[key] = max(max_vals[key], value)
    
    return min_vals, max_vals


def extract_trilemma_metrics(state: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract trilemma metrics (time, cost, carbon) from environment state.
    
    Makes it easy for agents to access the three key optimization metrics.
    
    Args:
        state: Environment state from API
        
    Returns:
        Dict with 'time', 'cost', 'carbon' keys (normalized to [0, 1])
        
    Example:
        >>> state = {"trilemma": {"accumulated_hours": 10.0, ...}}
        >>> metrics = extract_trilemma_metrics(state)
        >>> # Can use for reward calculation or state representation
    """
    trilemma = state.get("trilemma", {})
    
    return {
        "time": trilemma.get("accumulated_hours", 0.0),
        "cost": trilemma.get("accumulated_cost", 0.0),
        "carbon": trilemma.get("accumulated_carbon", 0.0),
    }


def format_for_agent_logging(
    episode: int,
    step: int,
    reward: float,
    state: Dict[str, Any],
    done: bool
) -> str:
    """
    Format episode data for agent learning logs.
    
    Args:
        episode: Episode number
        step: Step number
        reward: Step reward
        state: Environment state
        done: Whether episode is done
        
    Returns:
        Formatted log string
    """
    trilemma = state.get("trilemma", {})
    return (
        f"Episode {episode:3d} | Step {step:4d} | "
        f"Reward {reward:7.4f} | "
        f"Time {trilemma.get('accumulated_hours', 0.0):6.2f}h | "
        f"Cost ${trilemma.get('accumulated_cost', 0.0):7.2f} | "
        f"Carbon {trilemma.get('accumulated_carbon', 0.0):6.2f}t | "
        f"Done {done}"
    )


# ============================================================================
# Agent Action Helpers
# ============================================================================

def build_task1_action(cargo_id: int, path: List[int]) -> Dict[str, Any]:
    """
    Build a Task 1 (time minimization) action.
    
    Args:
        cargo_id: ID of cargo to route
        path: List of node IDs for route
        
    Returns:
        Task 1 action dictionary
    """
    return {
        "task_type": "task_1_time",
        "cargo_id": cargo_id,
        "path": path,
    }


def build_task2_action(cargo_id: int, path: List[int]) -> Dict[str, Any]:
    """
    Build a Task 2 (cost minimization) action.
    
    Args:
        cargo_id: ID of cargo to route
        path: List of node IDs for route
        
    Returns:
        Task 2 action dictionary
    """
    return {
        "task_type": "task_2_cost",
        "cargo_id": cargo_id,
        "path": path,
    }


def build_task3_action(cargo_id: int, modes: List[str], path: List[int]) -> Dict[str, Any]:
    """
    Build a Task 3 (multimodal optimization) action.
    
    Args:
        cargo_id: ID of cargo to route
        modes: List of transportation modes per edge
        path: List of node IDs for route
        
    Returns:
        Task 3 action dictionary
    """
    return {
        "task_type": "task_3_multimodal",
        "cargo_id": cargo_id,
        "modes": modes,
        "path": path,
    }
