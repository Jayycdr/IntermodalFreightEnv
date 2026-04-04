"""
Custom exceptions for the IntermodalFreightEnv application.

Provides specific exception types for better error handling and debugging.
"""


class IntermodalFreightEnvError(Exception):
    """Base exception for all IntermodalFreightEnv errors."""
    pass


# ============================================================================
# Environment Exceptions
# ============================================================================

class EnvironmentError(IntermodalFreightEnvError):
    """Base exception for environment-related errors."""
    pass


class EnvironmentNotInitializedError(EnvironmentError):
    """Raised when environment operations are attempted before initialization."""
    pass


class InvalidNetworkError(EnvironmentError):
    """Raised when network configuration is invalid."""
    pass


class InvalidNetworkNodeError(EnvironmentError):
    """Raised when a network node is invalid."""
    pass


class InvalidNetworkEdgeError(EnvironmentError):
    """Raised when a network edge is invalid."""
    pass


class DisruptionError(EnvironmentError):
    """Raised when network disruption cannot be applied."""
    pass


# ============================================================================
# Action & Agent Exceptions
# ============================================================================

class ActionError(IntermodalFreightEnvError):
    """Base exception for action-related errors."""
    pass


class InvalidActionError(ActionError):
    """Raised when an invalid action is provided."""
    pass


class ActionTimeoutError(ActionError):
    """Raised when action selection exceeds timeout."""
    pass


class PathNotFoundError(ActionError):
    """Raised when no valid path exists between nodes."""
    pass


# ============================================================================
# API & Request Exceptions
# ============================================================================

class APIError(IntermodalFreightEnvError):
    """Base exception for API-related errors."""
    pass


class RequestTimeoutError(APIError):
    """Raised when an HTTP request times out."""
    pass


class RequestFailedError(APIError):
    """Raised when an HTTP request fails."""
    pass


class InvalidEndpointError(APIError):
    """Raised when an invalid endpoint is accessed."""
    pass


class SchemaValidationError(APIError):
    """Raised when input data doesn't match expected schema."""
    pass


# ============================================================================
# Grading & Scoring Exceptions
# ============================================================================

class GradingError(IntermodalFreightEnvError):
    """Base exception for grading-related errors."""
    pass


class InvalidTrajectoryError(GradingError):
    """Raised when trajectory format is invalid."""
    pass


class EvaluationError(GradingError):
    """Raised when evaluation fails."""
    pass


class MetricsCalculationError(GradingError):
    """Raised when metrics calculation fails."""
    pass


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationError(IntermodalFreightEnvError):
    """Base exception for configuration-related errors."""
    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""
    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""
    pass
