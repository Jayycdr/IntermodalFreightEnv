"""
Main application entry point.

FastAPI application with routes integrated with IntermodalFreightEnv.
Supports three optimization tasks via different action schemas.
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware

from app.utils.logger import logger
from app.api.schemas import (
    BaseResponse,
    TaskType,
    Task1Action,
    Task2Action,
    Task3Action,
    CargoRequest,
    CargoResponse,
    SplitCargoRequest,
    StepRequest,
    StepResponse,
    EvaluationResult,
    ResetRequest,
    ResetResponse,
    EnvironmentState,
    TrilemmaState,
    NetworkConfig,
    NodeData,
    EdgeData,
)
from app.engine.core_env import FreightEnvironment, EnvironmentConfig


# ============================================================================
# Global Environment Instance
# ============================================================================

_env: Optional[FreightEnvironment] = None


def get_env() -> FreightEnvironment:
    """Get or create the global environment instance."""
    global _env
    if _env is None:
        config = EnvironmentConfig()
        _env = FreightEnvironment(config)
        
        # Setup FULLY-CONNECTED network to ensure all cargo pairs have valid paths
        # This prevents random cargo generation from creating unreachable deliveries
        # Metrics are realistic: based on node distances
        nodes = [
            {"id": 0, "location": "Warehouse"},
            {"id": 1, "location": "Port A"},
            {"id": 2, "location": "Rail Hub"},
            {"id": 3, "location": "Air Terminal"},
            {"id": 4, "location": "Truck Terminal"},
            {"id": 5, "location": "Destination"},
        ]
        
        # Build fully-connected network with realistic metrics
        # All node pairs are connected (ensures all cargos are deliverable)
        edges = []
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if i != j:
                    # Calculate distance-based metrics (realistic)
                    distance = abs(i - j)  # Relative distance
                    
                    # Time scales with distance (2-6 hours depending on distance)
                    time = 1.0 + (distance * 0.8)
                    
                    # Cost scales with distance (60-300 depending on distance)
                    cost = 60.0 + (distance * 40.0)
                    
                    # Carbon scales with distance (15-75 depending on distance)
                    carbon = 15.0 + (distance * 10.0)
                    
                    edges.append({
                        "source": i,
                        "target": j,
                        "time": time,
                        "cost": cost,
                        "carbon": carbon
                    })
        
        default_network = {
            "nodes": nodes,
            "edges": edges,
        }
        
        _env.setup_network(default_network)
        # Reset environment after network setup to initialize cargos
        _env.reset()
        logger.info(f"Fully-connected network configured: {len(nodes)} nodes, {len(edges)} edges. "
                   f"All cargo pairs are guaranteed to have valid paths.")
    
    return _env


def _environment_state_to_response(state: dict) -> EnvironmentState:
    """Convert environment state dict to EnvironmentState model."""
    trilemma = state.get("trilemma", {})
    
    # Build network config from state
    network_data = state.get("network", {})
    nodes = [
        NodeData(
            id=n["id"],
            location=n.get("location", f"Node{n.get('id', 0)}"),
            capacity=n.get("capacity"),
            attributes={"disabled": n.get("disabled", False)}
        )
        for n in network_data.get("nodes", [])
    ]
    
    edges = [
        EdgeData(
            source=e["source"],
            target=e["target"],
            time=e["time"],
            cost=e["cost"],
            carbon=e["carbon"],
            disabled=e.get("disabled", False)
        )
        for e in network_data.get("edges", [])
    ]
    
    network = NetworkConfig(nodes=nodes, edges=edges)
    
    return EnvironmentState(
        step=state.get("step", 0),
        active_cargos=state.get("active_cargos", 0),
        completed_cargos=state.get("completed_cargos", 0),
        trilemma=trilemma,
        network=network
    )


# ============================================================================
# FastAPI Application Setup
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="IntermodalFreightEnv API",
        description="Intermodal Freight Environment with Task-Based Optimization",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("FastAPI application initialized with full API layer")

    return app


app = create_app()


# ============================================================================
# Root & Health Endpoints
# ============================================================================

@app.get("/", response_model=BaseResponse)
async def root():
    """Root endpoint - returns API information."""
    return BaseResponse(
        success=True,
        message="Intermodal Freight Environment API",
        data={
            "version": "1.0.0",
            "name": "IntermodalFreightEnv",
            "endpoints": {
                "health": "/health",
                "status": "/status",
                "tasks": "/tasks",
                "modes": "/modes",
                "docs": "/docs",
                "state": "/state"
            }
        }
    )


@app.get("/health", response_model=BaseResponse)
async def health_check():
    """Health check endpoint."""
    return BaseResponse(success=True, message="API healthy")


@app.get("/status", response_model=BaseResponse)
async def status_endpoint():
    """Get API and environment status."""
    env = get_env()
    return BaseResponse(
        success=True,
        message="Environment active",
        data={
            "step": env.current_step,
            "active_cargos": len(env.active_cargos),
            "completed_cargos": len(env.completed_cargos),
        }
    )


@app.get("/state-descriptor", response_model=BaseResponse)
async def get_state_descriptor():
    """
    Get the state space descriptor for agent learning.
    
    Returns information about what the state space contains,
    useful for agents to understand the observation space.
    
    This endpoint helps agents understand:
    - What fields are in the state
    - What ranges/units each field has
    - What metrics are tracked (trilemma)
    - Network structure (nodes, edges)
    """
    return BaseResponse(
        success=True,
        message="State space descriptor for agent learning",
        data={
            "state_fields": {
                "step": {
                    "description": "Current step number in episode",
                    "type": "integer",
                    "min": 0,
                    "max": 1000,
                    "unit": "steps"
                },
                "active_cargos": {
                    "description": "Number of cargos currently being transported",
                    "type": "integer",
                    "min": 0,
                    "max": 100,
                    "unit": "count"
                },
                "completed_cargos": {
                    "description": "Number of cargos successfully delivered",
                    "type": "integer",
                    "min": 0,
                    "max": 100,
                    "unit": "count"
                },
                "trilemma": {
                    "description": "Key optimization metrics",
                    "type": "object",
                    "fields": {
                        "accumulated_hours": {
                            "description": "Total transit time",
                            "type": "float",
                            "min": 0.0,
                            "max": 10000.0,
                            "unit": "hours"
                        },
                        "accumulated_cost": {
                            "description": "Total transportation cost",
                            "type": "float",
                            "min": 0.0,
                            "max": 100000.0,
                            "unit": "dollars"
                        },
                        "accumulated_carbon": {
                            "description": "Total CO2 emissions",
                            "type": "float",
                            "min": 0.0,
                            "max": 10000.0,
                            "unit": "tons"
                        }
                    }
                },
                "network": {
                    "description": "Network topology with nodes and edges",
                    "type": "object",
                    "fields": {
                        "nodes": {
                            "description": "List of network nodes",
                            "type": "array",
                            "item_fields": {
                                "id": "Node identifier",
                                "location": "Geographic location name",
                                "capacity": "Max cargo capacity"
                            }
                        },
                        "edges": {
                            "description": "List of transportation routes",
                            "type": "array",
                            "item_fields": {
                                "source": "Starting node",
                                "target": "Destination node",
                                "time": "Transit time in hours",
                                "cost": "Cost in dollars",
                                "carbon": "CO2 emissions in tons",
                                "disabled": "Whether route is disrupted"
                            }
                        }
                    }
                }
            },
            "reward_function": {
                "type": "weighted_trilemma",
                "description": "Reward = -(0.5*time + 0.3*cost + 0.2*carbon)",
                "formula": "-( WEIGHT_TIME * hours + WEIGHT_COST * dollars + WEIGHT_CARBON * tons )",
                "weights": {
                    "time": 0.5,
                    "cost": 0.3,
                    "carbon": 0.2
                },
                "note": "Negative reward because agents minimize cost; lower cost = higher reward"
            },
            "action_schema": {
                "description": "Actions available to agents",
                "tasks": {
                    "task_1_time": {
                        "objective": "Minimize transit time",
                        "action_fields": ["task_type", "cargo_id", "path"]
                    },
                    "task_2_cost": {
                        "objective": "Minimize cost",
                        "action_fields": ["task_type", "cargo_id", "path"]
                    },
                    "task_3_multimodal": {
                        "objective": "Balance time, cost, and carbon (trilemma)",
                        "action_fields": ["task_type", "cargo_id", "path", "modes"]
                    }
                }
            },
            "episode_mechanics": {
                "max_steps": 1000,
                "reset_clears": ["step", "active_cargos", "completed_cargos", "trilemma"],
                "done_condition": "step >= max_steps or all cargos delivered"
            }
        }
    )


# ============================================================================
# Environment Management Endpoints
# ============================================================================

@app.post("/reset", response_model=ResetResponse)
async def reset_environment(request: ResetRequest = Body(default=None)):
    """
    Reset the environment to initial state.
    
    Applies disruptions based on seed and probability.
    """
    try:
        # Handle empty/null request
        if request is None:
            request = ResetRequest()
        
        env = get_env()
        
        # Update config if provided
        if request.seed is not None:
            env.config.seed = request.seed
        if request.disruption_probability is not None:
            env.config.disruption_probability = request.disruption_probability
        
        # Reset environment
        state = env.reset()
        
        logger.info(f"Environment reset with seed={request.seed}")
        
        return ResetResponse(
            state=_environment_state_to_response(state),
            message="Environment reset successfully"
        )
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state", response_model=EnvironmentState)
async def get_state():
    """Get current environment state."""
    try:
        env = get_env()
        return _environment_state_to_response(env.get_state())
    except Exception as e:
        logger.error(f"Failed to get state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Cargo Management Endpoints
# ============================================================================

@app.post("/cargo/add", response_model=CargoResponse)
async def create_cargo(request: CargoRequest):
    """
    Create a new cargo shipment.
    
    Cargo can be optionally split or routed after creation.
    """
    try:
        env = get_env()
        
        cargo = env.add_cargo(
            origin=request.origin,
            destination=request.destination,
            quantity=request.quantity,
            weight=request.weight,
            priority=request.priority,
            deadline=request.deadline,
        )
        
        logger.info(f"Cargo {cargo.cargo_id} created")
        
        return CargoResponse(
            cargo_id=cargo.cargo_id,
            origin=cargo.origin,
            destination=cargo.destination,
            quantity=cargo.quantity,
            weight=cargo.weight,
            priority=cargo.priority,
            deadline=cargo.deadline,
            created_at=cargo.created_at,
        )
    except Exception as e:
        logger.error(f"Failed to create cargo: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/cargo/split", response_model=BaseResponse)
async def split_cargo(request: SplitCargoRequest):
    """
    Split a cargo into multiple shipments.
    
    Useful for multimodal routing across different transportation modes.
    The total quantity in splits must equal the original cargo quantity.
    """
    try:
        env = get_env()
        
        # Validate sum
        total = sum(request.quantities)
        original = env.cargos[request.cargo_id].quantity
        if abs(total - original) > 0.001:
            raise ValueError(f"Split quantities ({total}) must equal original ({original})")
        
        splits = env.split_cargo(request.cargo_id, request.quantities)
        
        logger.info(f"Cargo {request.cargo_id} split into {len(splits)} cargos")
        
        return BaseResponse(
            success=True,
            message=f"Cargo split into {len(splits)} shipments",
            data={"split_cargo_ids": [s.cargo_id for s in splits]}
        )
    except Exception as e:
        logger.error(f"Failed to split cargo: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Task 1: Time Minimization
# ============================================================================

@app.post("/task1/route", response_model=BaseResponse)
async def task1_route_cargo(action: Task1Action):
    """
    Task 1: Route cargo to minimize travel time.
    
    Objective: Deliver all cargos in minimum total transit hours.
    """
    try:
        env = get_env()
        
        # Validate path
        if action.path[0] != env.cargos[action.cargo_id].origin:
            raise ValueError("Path origin must match cargo origin")
        if action.path[-1] != env.cargos[action.cargo_id].destination:
            raise ValueError("Path destination must match cargo destination")
        
        success = env.route_cargo(action.cargo_id, action.path)
        
        if not success:
            raise ValueError(f"Failed to route cargo {action.cargo_id}")
        
        logger.info(f"Task 1: Cargo {action.cargo_id} routed for time minimization")
        
        return BaseResponse(
            success=True,
            message="Cargo routed for time minimization",
            data={"cargo_id": action.cargo_id, "path": action.path}
        )
    except Exception as e:
        logger.error(f"Task 1 routing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Task 2: Cost Minimization
# ============================================================================

@app.post("/task2/route", response_model=BaseResponse)
async def task2_route_cargo(action: Task2Action):
    """
    Task 2: Route cargo to minimize operational cost.
    
    Objective: Deliver all cargos with minimum total monetary cost.
    """
    try:
        env = get_env()
        
        # Validate path
        if action.path[0] != env.cargos[action.cargo_id].origin:
            raise ValueError("Path origin must match cargo origin")
        if action.path[-1] != env.cargos[action.cargo_id].destination:
            raise ValueError("Path destination must match cargo destination")
        
        success = env.route_cargo(action.cargo_id, action.path)
        
        if not success:
            raise ValueError(f"Failed to route cargo {action.cargo_id}")
        
        logger.info(f"Task 2: Cargo {action.cargo_id} routed for cost minimization")
        
        return BaseResponse(
            success=True,
            message="Cargo routed for cost minimization",
            data={"cargo_id": action.cargo_id, "path": action.path}
        )
    except Exception as e:
        logger.error(f"Task 2 routing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Task 3: Multimodal Routing
# ============================================================================

@app.post("/task3/route", response_model=BaseResponse)
async def task3_route_cargo(action: Task3Action):
    """
    Task 3: Route cargo across multiple transportation modes.
    
    Objective: Optimize multimodal routing while balancing time, cost, and carbon.
    
    STRUCTURALLY DISTINCT: Includes cargo_type (truck/rail/ship/air) enum
    and optional split_at nodes for mode transitions.
    """
    try:
        env = get_env()
        
        if action.cargo_id not in env.cargos:
            raise ValueError(f"Cargo {action.cargo_id} not found")
        
        cargo = env.cargos[action.cargo_id]
        
        # Validate path
        if action.path[0] != cargo.origin:
            raise ValueError("Path origin must match cargo origin")
        if action.path[-1] != cargo.destination:
            raise ValueError("Path destination must match cargo destination")
        
        # Route the cargo
        success = env.route_cargo(action.cargo_id, action.path)
        if not success:
            raise ValueError(f"Failed to route cargo {action.cargo_id}")
        
        logger.info(
            f"Task 3: Cargo {action.cargo_id} routed via {action.cargo_type} "
            f"along path {action.path}"
        )
        
        return BaseResponse(
            success=True,
            message=f"Cargo routed via {action.cargo_type} with multimodal optimization",
            data={
                "cargo_id": action.cargo_id,
                "path": action.path,
                "cargo_type": action.cargo_type,
                "split_at": action.split_at
            }
        )
    except Exception as e:
        logger.error(f"Task 3 routing failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Simulation Endpoints
# ============================================================================

@app.post("/step", response_model=StepResponse)
async def step(request: StepRequest):
    """
    Execute one simulation step.
    
    Moves all active cargos, accumulates costs, and updates environment state.
    """
    try:
        env = get_env()
        
        # Perform step
        state, reward, done, info = env.step(request.action or {})
        
        logger.debug(f"Step {env.current_step}: reward={reward}, done={done}")
        
        return StepResponse(
            state=_environment_state_to_response(state),
            reward=reward,
            done=done,
            info=info
        )
    except Exception as e:
        logger.error(f"Step failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-episode", response_model=BaseResponse)
async def run_episode(max_steps: int = 100):
    """
    Run a complete episode to completion.
    
    Simulates the environment until max_steps or all cargos are delivered.
    """
    try:
        env = get_env()
        
        total_reward = 0
        for step_count in range(max_steps):
            state, reward, done, info = env.step({})
            total_reward += reward
            
            if done:
                logger.info(f"Episode completed in {step_count + 1} steps")
                break
        
        trilemma = env.get_trilemma()
        
        return BaseResponse(
            success=True,
            message="Episode completed",
            data={
                "total_steps": env.current_step,
                "total_reward": total_reward,
                "completed_cargos": len(env.completed_cargos),
                "trilemma": trilemma.to_dict(),
            }
        )
    except Exception as e:
        logger.error(f"Episode failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Evaluation Endpoints
# ============================================================================

@app.post("/evaluate", response_model=EvaluationResult)
async def evaluate(task_type: TaskType):
    """
    Evaluate the current episode for a specific task.
    
    Computes task-specific metrics and performance score.
    """
    try:
        env = get_env()
        trilemma = env.get_trilemma()
        
        # Task-specific evaluation
        if task_type == TaskType.TASK_1_TIME:
            # Task 1: Minimize time
            score = 100.0 - (trilemma.accumulated_hours * 0.5)  # Penalize time
            metrics = {
                "total_hours": trilemma.accumulated_hours,
                "total_cost": trilemma.accumulated_cost,
                "total_carbon": trilemma.accumulated_carbon,
                "cargos_delivered": len(env.completed_cargos),
            }
            feedback = f"Delivered {len(env.completed_cargos)} cargos in {trilemma.accumulated_hours:.1f} hours"
        
        elif task_type == TaskType.TASK_2_COST:
            # Task 2: Minimize cost
            score = 100.0 - (trilemma.accumulated_cost * 0.1)  # Penalize cost
            metrics = {
                "total_hours": trilemma.accumulated_hours,
                "total_cost": trilemma.accumulated_cost,
                "total_carbon": trilemma.accumulated_carbon,
                "cargos_delivered": len(env.completed_cargos),
            }
            feedback = f"Delivered {len(env.completed_cargos)} cargos for ${trilemma.accumulated_cost:.2f}"
        
        else:  # TASK_3_MULTIMODAL
            # Task 3: Balance all three objectives
            max_score = 100.0
            time_penalty = trilemma.accumulated_hours * 0.2
            cost_penalty = trilemma.accumulated_cost * 0.05
            carbon_penalty = trilemma.accumulated_carbon * 0.1
            score = max(0, max_score - time_penalty - cost_penalty - carbon_penalty)
            metrics = {
                "total_hours": trilemma.accumulated_hours,
                "total_cost": trilemma.accumulated_cost,
                "total_carbon": trilemma.accumulated_carbon,
                "cargos_delivered": len(env.completed_cargos),
                "trilemma_balance": (
                    trilemma.accumulated_hours +
                    trilemma.accumulated_cost / 100 +
                    trilemma.accumulated_carbon / 10
                ),
            }
            feedback = f"Delivered {len(env.completed_cargos)} cargos with balanced trilemma"
        
        # Clamp score to valid range
        score = max(0, min(100, score))
        
        logger.info(f"Evaluation complete: task={task_type}, score={score:.1f}")
        
        return EvaluationResult(
            task_type=task_type,
            score=score,
            metrics=metrics,
            feedback=feedback,
            trilemma_final=TrilemmaState(
                accumulated_hours=trilemma.accumulated_hours,
                accumulated_cost=trilemma.accumulated_cost,
                accumulated_carbon=trilemma.accumulated_carbon,
            )
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Pathfinding Utility Endpoints
# ============================================================================

@app.get("/path", response_model=BaseResponse)
async def find_shortest_path(origin: int, destination: int, weight: str = "time"):
    """
    Find shortest path between two nodes.
    
    Supports three weight metrics for trilemma optimization:
    - 'time': Minimum travel hours
    - 'cost': Minimum monetary cost
    - 'carbon': Minimum CO2 emissions
    """
    try:
        if weight not in ["time", "cost", "carbon"]:
            raise ValueError("Weight must be 'time', 'cost', or 'carbon'")
        
        env = get_env()
        path = env.network.get_shortest_path(origin, destination, weight=weight)
        
        if not path:
            raise ValueError(f"No path found from {origin} to {destination}")
        
        # Calculate path metrics
        total_time = 0
        total_cost = 0
        total_carbon = 0
        
        for i in range(len(path) - 1):
            edge = env.network.get_edge(path[i], path[i + 1])
            if edge:
                total_time += edge.time
                total_cost += edge.cost
                total_carbon += edge.carbon
        
        return BaseResponse(
            success=True,
            message=f"Shortest path found (optimized for {weight})",
            data={
                "path": path,
                "total_time": total_time,
                "total_cost": total_cost,
                "total_carbon": total_carbon,
                "optimized_for": weight,
            }
        )
    except Exception as e:
        logger.error(f"Pathfinding failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Task & Grading Endpoints
# ============================================================================

@app.get("/tasks")
async def get_tasks():
    """
    Get all available tasks with their action schemas.
    
    Returns 3 tasks:
    - Task 1: Time Minimization
    - Task 2: Cost Minimization
    - Task 3: Multimodal Optimization
    """
    tasks = [
        {
            "name": "Task 1: Time Minimization",
            "id": "task_1_time",
            "description": "Minimize total transit time while delivering all cargos",
            "objective": "minimize-time",
            "action_schema": {
                "type": "object",
                "properties": {
                    "task_type": {"type": "string", "enum": ["task_1_time"]},
                    "cargo_id": {"type": "integer"},
                    "path": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["task_type", "cargo_id", "path"]
            }
        },
        {
            "name": "Task 2: Cost Minimization",
            "id": "task_2_cost",
            "description": "Minimize total operational cost while delivering all cargos",
            "objective": "minimize-cost",
            "action_schema": {
                "type": "object",
                "properties": {
                    "task_type": {"type": "string", "enum": ["task_2_cost"]},
                    "cargo_id": {"type": "integer"},
                    "path": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["task_type", "cargo_id", "path"]
            }
        },
        {
            "name": "Task 3: Multimodal Optimization",
            "id": "task_3_multimodal",
            "description": "Optimize routing across transportation modes while balancing time, cost, and carbon",
            "objective": "balance-trilemma",
            "action_schema": {
                "type": "object",
                "properties": {
                    "task_type": {"type": "string", "enum": ["task_3_multimodal"]},
                    "cargo_id": {"type": "integer"},
                    "cargo_type": {"type": "string", "enum": ["truck", "rail", "ship", "air"]},
                    "path": {"type": "array", "items": {"type": "string"}},
                    "split_at": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["task_type", "cargo_id", "cargo_type", "path", "split_at"]
            }
        }
    ]
    
    return BaseResponse(
        success=True,
        message="3 tasks available",
        data={"tasks": tasks, "count": 3}
    )


@app.post("/grader")
async def grade_trajectory(trajectory: dict = None):
    """
    Grade a trajectory and return a score.
    
    Accepts a trajectory object with step data and returns a score
    calculated using the weighted formula:
    Score = TRILEMMA_WEIGHT_TIME×time + TRILEMMA_WEIGHT_COST×cost + TRILEMMA_WEIGHT_CARBON×carbon
    
    Score is normalized to [0.0, 1.0] range.
    """
    try:
        from app.api.grader import Grader
        from app.api.schemas import TaskType
        
        # Extract trajectory from request
        trajectory_data = trajectory if isinstance(trajectory, dict) else {}
        trajectory_steps = trajectory_data.get("trajectory", []) or trajectory_data.get("steps", [])
        task_type = trajectory_data.get("task_type", "task_3_multimodal")
        
        # Map task_type to TaskType enum
        task_type_map = {
            "task_1_time": TaskType.TASK_1_TIME,
            "task_2_cost": TaskType.TASK_2_COST,
            "task_3_multimodal": TaskType.TASK_3_MULTIMODAL,
        }
        task = task_type_map.get(task_type, TaskType.TASK_3_MULTIMODAL)
        
        # Initialize grader and evaluate
        grader = Grader()
        grader.load_trajectory(trajectory_steps)
        result = grader.evaluate(task_type=task)
        
        # Normalize score to (0, 1) exclusive - divide by 100 and clamp to strict boundaries
        # EFFICIENCY_SCORE_MIN/MAX ensure raw scores map to valid range
        normalized_score = max(0.001, min(0.999, result.efficiency_score / 100.0))
        
        return BaseResponse(
            success=True,
            message=f"Trajectory graded ({result.task_type.value})",
            data={
                "score": normalized_score,
                "efficiency_score": result.efficiency_score,
                "weighted_score": result.weighted_score,
                "metrics": {
                    "accumulated_hours": result.raw_metrics.accumulated_hours,
                    "accumulated_cost": result.raw_metrics.accumulated_cost,
                    "accumulated_carbon": result.raw_metrics.accumulated_carbon,
                },
                "cargos_delivered": result.cargos_delivered,
                "task_type": result.task_type.value,
            }
        )
    except Exception as e:
        logger.error(f"Grading failed: {str(e)}")
        return BaseResponse(
            success=False,
            message=f"Grading error: {str(e)}",
            data={"score": 0.001}
        )


@app.get("/modes")
async def get_transportation_modes():
    """
    Get characteristics of all transportation modes.
    
    Returns mode profiles for truck, rail, ship, and flight.
    """
    try:
        from app.api.grader import Grader
        
        modes = Grader.get_mode_characteristics()
        
        return BaseResponse(
            success=True,
            message="Transportation modes available",
            data={
                "modes": modes,
                "descriptions": {
                    "truck": "Fast, medium cost, medium capacity. For short-medium distances.",
                    "rail": "Medium speed, low cost, high capacity. For medium-long distances.",
                    "ship": "Slow, lowest cost, highest capacity. For long intercontinental routes.",
                    "flight": "Fastest, highest cost, medium capacity. For urgent long-distance.",
                }
            }
        )
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"Error fetching modes: {str(e)}",
            data={}
        )


@app.post("/modes/example")
async def get_mode_example(request: dict = None):
    """
    Get an example trajectory step for a specific transportation mode.
    
    Request: {"mode": "truck", "distance_km": 500, "cargo_tons": 10}
    """
    try:
        from app.api.grader import Grader
        
        request = request or {}
        mode = request.get("mode", "truck")
        distance = float(request.get("distance_km", 500))
        cargo = float(request.get("cargo_tons", 10))
        
        example = Grader.example_trajectory(mode, distance, cargo)
        
        return BaseResponse(
            success=True,
            message=f"Example trajectory for {mode}",
            data={
                "trajectory": [example],
                "explanation": f"Shipping {cargo} tons by {mode} over {distance} km"
            }
        )
    except Exception as e:
        return BaseResponse(
            success=False,
            message=f"Error generating example: {str(e)}",
            data={}
        )


@app.post("/baseline")
async def run_baseline(config: dict = None):
    """
    Run baseline agents and return baseline scores for all 3 tasks.
    
    This endpoint triggers baseline inference for all 3 tasks and returns
    baseline scores that can be compared against agent performance.
    
    Returns:
        {
            "success": true,
            "message": "Baseline scores computed",
            "data": {
                "task_1_score": float,
                "task_2_score": float,
                "task_3_score": float
            }
        }
    """
    try:
        from app.api.grader import Grader
        from app.api.schemas import TaskType
        from baseline.agent import RandomAgent
        
        config = config or {}
        max_steps = config.get("max_steps", 50)
        num_cargos = config.get("num_cargos", 2)
        
        # Dictionary to store scores for each task
        baseline_scores = {
            "task_1_score": 0.0,
            "task_2_score": 0.0,
            "task_3_score": 0.0,
        }
        
        # Run baseline for each task
        task_configs = [
            ("task_1_time", TaskType.TASK_1_TIME, "task_1_score"),
            ("task_2_cost", TaskType.TASK_2_COST, "task_2_score"),
            ("task_3_multimodal", TaskType.TASK_3_MULTIMODAL, "task_3_score"),
        ]
        
        for task_type_str, task_type_enum, score_key in task_configs:
            try:
                logger.info(f"Running baseline for {task_type_str}")
                
                # Reset environment for this task
                try:
                    reset_response = requests.post(f"http://localhost:8000/reset")
                    reset_response.raise_for_status()
                except Exception as e:
                    logger.warning(f"Reset failed for {task_type_str}: {e}")
                
                # Create a simple random agent trajectory
                trajectory = []
                agent = RandomAgent(agent_id=f"baseline_{task_type_str}", api_url="http://localhost:8000")
                
                # Run for max_steps or until done
                for step in range(max_steps):
                    try:
                        state_response = requests.get("http://localhost:8000/state")
                        state_response.raise_for_status()
                        state = state_response.json()
                        
                        # Get random action from agent
                        action = agent.select_action(state)
                        
                        # Execute action based on task type
                        if task_type_str == "task_1_time":
                            action_response = requests.post(
                                "http://localhost:8000/task1/route",
                                json=action
                            )
                        elif task_type_str == "task_2_cost":
                            action_response = requests.post(
                                "http://localhost:8000/task2/route",
                                json=action
                            )
                        else:  # task_3
                            action_response = requests.post(
                                "http://localhost:8000/task3/route",
                                json=action
                            )
                        
                        if action_response.ok:
                            result = action_response.json()
                            reward = result.get("reward", 0.0)
                            done = result.get("done", False)
                            
                            # Record step
                            trajectory.append({
                                "step": step,
                                "action": action,
                                "reward": reward,
                                "done": done
                            })
                            
                            if done:
                                logger.info(f"Baseline {task_type_str} completed at step {step}")
                                break
                    except Exception as e:
                        logger.warning(f"Step {step} failed for {task_type_str}: {e}")
                        break
                
                # Grade the trajectory
                if trajectory:
                    grader = Grader()
                    grader.load_trajectory(trajectory)
                    evaluation = grader.evaluate(task_type=task_type_enum)
                    
                    # Normalize score to [0, 1]
                    score = max(0.0, min(1.0, evaluation.efficiency_score / 100.0))
                    baseline_scores[score_key] = score
                    
                    logger.info(f"Baseline {task_type_str} score: {score:.4f}")
                else:
                    logger.warning(f"No trajectory collected for {task_type_str}")
                    baseline_scores[score_key] = 0.0
                    
            except Exception as e:
                logger.error(f"Baseline failed for {task_type_str}: {e}")
                baseline_scores[score_key] = 0.0
                # Continue with next task even if this one fails
                continue
        
        return BaseResponse(
            success=True,
            message="Baseline scores computed for all 3 tasks",
            data=baseline_scores
        )
        
    except Exception as e:
        logger.error(f"Baseline endpoint error: {e}")
        return BaseResponse(
            success=False,
            message=f"Baseline error: {str(e)}",
            data={
                "task_1_score": 0.0,
                "task_2_score": 0.0,
                "task_3_score": 0.0,
            }
        )


def main():
    """Entry point for the application server."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
