"""
Pydantic models and schemas for API requests/responses.

Defines data models for validation and serialization across three tasks:
- Task 1: Travel Time Minimization
- Task 2: Cost Minimization
- Task 3: Multimodal Routing
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# Enums for Task Differentiation
# ============================================================================

class CargoType(str, Enum):
    """Cargo transportation modes (Task 3 specific)."""
    TRUCK = "truck"
    RAIL = "rail"
    SHIP = "ship"
    AIR = "air"


class TaskType(str, Enum):
    """Types of optimization tasks."""
    TASK_1_TIME = "task_1_time"
    TASK_2_COST = "task_2_cost"
    TASK_3_MULTIMODAL = "task_3_multimodal"


# ============================================================================
# Base Response Models
# ============================================================================

class BaseResponse(BaseModel):
    """Base response model for all API responses."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(default="", description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed",
                "data": {}
            }
        }


# ============================================================================
# Network & State Models
# ============================================================================

class NodeData(BaseModel):
    """Represents a network node."""
    
    id: int = Field(..., description="Node identifier")
    location: str = Field(..., description="Location name")
    capacity: Optional[float] = Field(default=None, description="Node capacity")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EdgeData(BaseModel):
    """Represents a network edge with trilemma attributes."""
    
    source: int = Field(..., description="Source node")
    target: int = Field(..., description="Target node")
    time: float = Field(..., description="Transit time in hours", ge=0)
    cost: float = Field(..., description="Monetary cost in dollars", ge=0)
    carbon: float = Field(..., description="CO2 emissions in kg", ge=0)
    disabled: bool = Field(default=False, description="Whether edge is disabled")


class NetworkConfig(BaseModel):
    """Configuration for the freight network."""
    
    nodes: List[NodeData] = Field(..., description="Network nodes")
    edges: List[EdgeData] = Field(..., description="Network edges")


class EnvironmentState(BaseModel):
    """Model representing the current state of the freight environment."""
    
    step: int = Field(..., description="Current simulation step")
    active_cargos: int = Field(..., description="Number of active cargos")
    completed_cargos: int = Field(..., description="Number of completed cargos")
    trilemma: Dict[str, float] = Field(
        ...,
        description="Accumulated trilemma counters (hours, cost, carbon)"
    )
    network: NetworkConfig = Field(..., description="Current network state")


class TrilemmaState(BaseModel):
    """Trilemma counters: time, cost, carbon."""
    
    accumulated_hours: float = Field(ge=0, description="Total transit hours")
    accumulated_cost: float = Field(ge=0, description="Total cost in dollars")
    accumulated_carbon: float = Field(ge=0, description="Total carbon in kg")


# ============================================================================
# Cargo Models
# ============================================================================

class CargoRequest(BaseModel):
    """Request to create or update a cargo."""
    
    origin: int = Field(..., description="Origin node ID")
    destination: int = Field(..., description="Destination node ID")
    quantity: float = Field(..., description="Quantity to transport", gt=0)
    weight: float = Field(..., description="Weight in kg", gt=0)
    priority: int = Field(default=1, description="Priority level: 1=low, 2=med, 3=high", ge=1, le=3)
    deadline: Optional[int] = Field(default=None, description="Optional delivery deadline (steps)")


class CargoResponse(BaseModel):
    """Response containing cargo information."""
    
    cargo_id: int = Field(..., description="Unique cargo identifier")
    origin: int = Field(..., description="Origin node")
    destination: int = Field(..., description="Destination node")
    quantity: float = Field(..., description="Quantity")
    weight: float = Field(..., description="Weight in kg")
    priority: int = Field(..., description="Priority level")
    deadline: Optional[int] = Field(None, description="Deadline in steps")
    created_at: int = Field(..., description="Creation step")


class SplitCargoRequest(BaseModel):
    """Request to split a cargo into multiple shipments."""
    
    cargo_id: int = Field(..., description="Cargo to split")
    quantities: List[float] = Field(
        ...,
        description="Quantities for each split (must sum to original)",
        min_items=2
    )


# ============================================================================
# Task 1: Time Minimization
# ============================================================================

class Task1Action(BaseModel):
    """Action schema for Task 1: Time Minimization.
    
    Minimize total transit time while delivering all cargos.
    """
    
    task_type: TaskType = Field(
        default=TaskType.TASK_1_TIME,
        description="Must be TASK_1_TIME"
    )
    cargo_id: int = Field(..., description="Cargo to route")
    path: List[int] = Field(
        ...,
        description="Sequence of nodes from origin to destination",
        min_items=2
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "task_1_time",
                "cargo_id": 0,
                "path": [0, 1, 5]
            }
        }


# ============================================================================
# Task 2: Cost Minimization
# ============================================================================

class Task2Action(BaseModel):
    """Action schema for Task 2: Cost Minimization.
    
    Minimize total operational cost while delivering all cargos.
    """
    
    task_type: TaskType = Field(
        default=TaskType.TASK_2_COST,
        description="Must be TASK_2_COST"
    )
    cargo_id: int = Field(..., description="Cargo to route")
    path: List[int] = Field(
        ...,
        description="Sequence of nodes from origin to destination",
        min_items=2
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "task_2_cost",
                "cargo_id": 0,
                "path": [0, 2, 5]
            }
        }


# ============================================================================
# Task 3: Multimodal Routing (STRUCTURAL DISTINCTNESS)
# ============================================================================

class Task3Action(BaseModel):
    """Action schema for Task 3: Multimodal Routing.
    
    Optimize routing across multiple transportation modes (truck, rail, ship, air)
    while balancing time, cost, and carbon objectives.
    
    STRUCTURAL DISTINCTNESS: Includes cargo_type enum, making this schema
    fundamentally different from Task 1 and Task 2 action schemas.
    """
    
    task_type: TaskType = Field(
        default=TaskType.TASK_3_MULTIMODAL,
        description="Must be TASK_3_MULTIMODAL"
    )
    cargo_id: int = Field(..., description="Cargo to route")
    cargo_type: CargoType = Field(
        ...,
        description="Transportation mode: truck, rail, ship, or air"
    )
    path: List[int] = Field(
        ...,
        description="Sequence of nodes from origin to destination",
        min_items=2
    )
    split_at: Optional[List[int]] = Field(
        default=None,
        description="Optional nodes where cargo is split across modes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_type": "task_3_multimodal",
                "cargo_id": 0,
                "cargo_type": "rail",
                "path": [0, 1, 4, 5],
                "split_at": [1]
            }
        }


class MultimodalStrategy(BaseModel):
    """Multi-leg routing strategy with different modes."""
    
    leg_index: int = Field(..., description="Leg number")
    nodes: List[int] = Field(..., description="Nodes for this leg")
    cargo_type: CargoType = Field(..., description="Cargo type for this leg")
    trilemma_focus: str = Field(
        ...,
        description="Optimization focus: 'time', 'cost', or 'carbon'"
    )


# ============================================================================
# Step and Evaluation Models
# ============================================================================

class StepRequest(BaseModel):
    """Request to perform one environment step."""
    
    action: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional action(s) to execute"
    )


class StepResponse(BaseModel):
    """Response from environment step."""
    
    state: EnvironmentState = Field(..., description="Updated environment state")
    reward: float = Field(..., description="Reward for this step")
    done: bool = Field(..., description="Whether episode is complete")
    info: Dict[str, Any] = Field(..., description="Additional step information")


class EvaluationResult(BaseModel):
    """Model for evaluation/grading results."""
    
    task_type: TaskType = Field(..., description="Which task was evaluated")
    score: float = Field(..., description="Evaluation score", ge=0.0, le=100.0)
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Detailed performance metrics"
    )
    feedback: Optional[str] = Field(None, description="Evaluation feedback")
    trilemma_final: TrilemmaState = Field(..., description="Final trilemma state")


class ResetRequest(BaseModel):
    """Request to reset the environment."""
    
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    disruption_probability: Optional[float] = Field(
        None,
        description="Probability of node/edge disruption (0-1)",
        ge=0.0,
        le=1.0
    )


class ResetResponse(BaseModel):
    """Response from environment reset."""
    
    state: EnvironmentState = Field(..., description="Initial environment state")
    message: str = Field(..., description="Status message")
