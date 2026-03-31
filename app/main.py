"""
Main application entry point.

FastAPI application with routes integrated with IntermodalFreightEnv.
Supports three optimization tasks via different action schemas.
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from app.engine.core_env import FreightEnvironment, EnvironmentConfig, TrilemmaCounters


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
        
        # Setup default network
        default_network = {
            "nodes": [
                {"id": 0, "location": "Warehouse"},
                {"id": 1, "location": "Port A"},
                {"id": 2, "location": "Rail Hub"},
                {"id": 3, "location": "Air Terminal"},
                {"id": 4, "location": "Truck Terminal"},
                {"id": 5, "location": "Destination"},
            ],
            "edges": [
                {"source": 0, "target": 1, "time": 2.0, "cost": 100.0, "carbon": 30.0},
                {"source": 0, "target": 2, "time": 1.5, "cost": 80.0, "carbon": 20.0},
                {"source": 0, "target": 3, "time": 0.5, "cost": 200.0, "carbon": 80.0},
                {"source": 0, "target": 4, "time": 1.0, "cost": 60.0, "carbon": 25.0},
                {"source": 1, "target": 5, "time": 3.0, "cost": 150.0, "carbon": 50.0},
                {"source": 2, "target": 5, "time": 2.5, "cost": 120.0, "carbon": 35.0},
                {"source": 3, "target": 5, "time": 1.5, "cost": 180.0, "carbon": 60.0},
                {"source": 4, "target": 5, "time": 2.0, "cost": 100.0, "carbon": 30.0},
                {"source": 1, "target": 2, "time": 1.0, "cost": 50.0, "carbon": 15.0},
                {"source": 2, "target": 4, "time": 0.5, "cost": 30.0, "carbon": 10.0},
            ],
        }
        _env.setup_network(default_network)
        logger.info("Default network configured")
    
    return _env


def _environment_state_to_response(state: dict) -> EnvironmentState:
    """Convert environment state dict to EnvironmentState model."""
    trilemma = state.get("trilemma", {})
    
    # Build network config from state
    network_data = state.get("network", {})
    nodes = [
        NodeData(
            id=n[0],
            location=n[1].get("location", f"Node{n[0]}"),
            capacity=n[1].get("capacity"),
            attributes={k: v for k, v in n[1].items() if k not in ["location", "capacity"]}
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
        active_cargos=len(state.get("active_cargos", [])),
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
# Health & Status Endpoints
# ============================================================================

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


# ============================================================================
# Environment Management Endpoints
# ============================================================================

@app.post("/reset", response_model=ResetResponse)
async def reset_environment(request: ResetRequest):
    """
    Reset the environment to initial state.
    
    Applies disruptions based on seed and probability.
    """
    try:
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
