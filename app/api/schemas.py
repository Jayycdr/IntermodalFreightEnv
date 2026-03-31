"""
Pydantic models and schemas for API requests/responses.

Defines data models for validation and serialization.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(default="", description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")


class EnvironmentState(BaseModel):
    """Model representing the state of the freight environment."""
    
    step: int = Field(..., description="Current simulation step")
    nodes: List[Dict[str, Any]] = Field(..., description="Graph nodes")
    edges: List[Dict[str, Any]] = Field(..., description="Graph edges")


class ActionRequest(BaseModel):
    """Model for environment action requests."""
    
    action: Dict[str, Any] = Field(..., description="Action to execute")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Action parameters")


class EvaluationResult(BaseModel):
    """Model for evaluation/grading results."""
    
    score: float = Field(..., description="Evaluation score", ge=0.0, le=1.0)
    metrics: Dict[str, float] = Field(default_factory=dict, description="Detailed metrics")
    feedback: Optional[str] = Field(default=None, description="Evaluation feedback")
