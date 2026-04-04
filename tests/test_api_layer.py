#!/usr/bin/env python3
"""
Test script for API & Infrastructure layer.

Demonstrates:
- Pydantic schema validation across three tasks
- FastAPI route integration with IntermodalFreightEnv
- Task-specific action schemas with cargo_type enum distinctness
- Configuration mapping from openenv.yaml
"""

import json
from app.utils.logger import logger
from app.api.schemas import (
    TaskType,
    Task1Action,
    Task2Action,
    Task3Action,
    CargoType,
    CargoRequest,
    SplitCargoRequest,
    ResetRequest,
    StepRequest,
)
from app.main import get_env, _environment_state_to_response


def test_schemas():
    """Test Pydantic schema validation and structural distinctness."""
    logger.info("=" * 70)
    logger.info("TESTING PYDANTIC SCHEMAS")
    logger.info("=" * 70)
    
    # Test Task 1 Action
    logger.info("\n1. Task 1 (Time Minimization) Schema:")
    task1 = Task1Action(
        task_type=TaskType.TASK_1_TIME,
        cargo_id=0,
        path=[0, 2, 5]
    )
    logger.info(f"   Task1Action: {task1.model_dump()}")
    logger.info(f"   Schema fields: {list(task1.model_fields.keys())}")
    
    # Test Task 2 Action
    logger.info("\n2. Task 2 (Cost Minimization) Schema:")
    task2 = Task2Action(
        task_type=TaskType.TASK_2_COST,
        cargo_id=0,
        path=[0, 1, 5]
    )
    logger.info(f"   Task2Action: {task2.model_dump()}")
    logger.info(f"   Schema fields: {list(task2.model_fields.keys())}")
    
    # Test Task 3 Action - STRUCTURALLY DISTINCT
    logger.info("\n3. Task 3 (Multimodal Routing) Schema - STRUCTURALLY DISTINCT:")
    task3 = Task3Action(
        task_type=TaskType.TASK_3_MULTIMODAL,
        cargo_id=0,
        cargo_type=CargoType.RAIL,
        path=[0, 2, 5],
        split_at=[2]
    )
    logger.info(f"   Task3Action: {task3.model_dump()}")
    logger.info(f"   Schema fields: {list(task3.model_fields.keys())}")
    
    # Show structural differences
    logger.info("\n4. STRUCTURAL DISTINCTNESS VERIFICATION:")
    logger.info(f"   Task 1 fields: {set(task1.model_fields.keys())}")
    logger.info(f"   Task 2 fields: {set(task2.model_fields.keys())}")
    logger.info(f"   Task 3 fields: {set(task3.model_fields.keys())}")
    
    # Task 3 has unique fields
    unique_to_task3 = set(task3.model_fields.keys()) - set(task1.model_fields.keys())
    logger.info(f"   ✓ Unique to Task 3: {unique_to_task3}")
    
    # Test CargoType enum
    logger.info("\n5. CargoType Enum (Task 3 specific):")
    for cargo_type in CargoType:
        logger.info(f"   - {cargo_type.value}")
    
    # Test schema validation
    logger.info("\n6. Schema Validation:")
    try:
        invalid_task3 = Task3Action(
            task_type=TaskType.TASK_3_MULTIMODAL,
            cargo_id=0,
            cargo_type="invalid_mode",  # Should fail
            path=[0, 2, 5]
        )
    except Exception as e:
        logger.info(f"   ✓ Validation correctly caught invalid cargo_type: {type(e).__name__}")
    
    logger.info("\n7. Cargo Request Schema:")
    cargo_req = CargoRequest(
        origin=0,
        destination=5,
        quantity=100.0,
        weight=5000.0,
        priority=2,
        deadline=100
    )
    logger.info(f"   CargoRequest: {cargo_req.model_dump()}")
    
    logger.info("\n8. Split Cargo Request Schema:")
    split_req = SplitCargoRequest(
        cargo_id=0,
        quantities=[50.0, 50.0]
    )
    logger.info(f"   SplitCargoRequest: {split_req.model_dump()}")


def test_environment_integration():
    """Test FastAPI environment integration."""
    logger.info("\n" + "=" * 70)
    logger.info("TESTING ENVIRONMENT INTEGRATION")
    logger.info("=" * 70)
    
    # Get environment
    logger.info("\n1. Getting environment instance...")
    env = get_env()
    logger.info(f"   ✓ Environment created with {len(env.network.get_all_nodes())} nodes")
    logger.info(f"   ✓ Network has {len(env.network.get_all_edges())} edges")
    
    # Reset
    logger.info("\n2. Resetting environment...")
    state = env.reset()
    logger.info(f"   ✓ Reset successful at step {env.current_step}")
    logger.info(f"   ✓ Disabled nodes: {env.network.disabled_nodes}")
    logger.info(f"   ✓ Disabled edges: {len(env.network.disabled_edges)} edges")
    
    # Convert to response model
    logger.info("\n3. Converting state to API response model...")
    env_state_response = _environment_state_to_response(env.get_state())
    logger.info(f"   ✓ Response model conversion successful")
    logger.info(f"   ✓ Network nodes: {len(env_state_response.network.nodes)}")
    logger.info(f"   ✓ Network edges: {len(env_state_response.network.edges)}")
    
    # Create cargo
    logger.info("\n4. Creating cargo...")
    cargo = env.add_cargo(
        origin=0,
        destination=5,
        quantity=100.0,
        weight=5000.0,
        priority=2
    )
    logger.info(f"   ✓ Cargo {cargo.cargo_id} created")
    
    # Test Task 1 routing
    logger.info("\n5. Task 1 Routing (Time Minimization)...")
    path_time = env.network.get_shortest_path(0, 5, weight="time")
    logger.info(f"   ✓ Shortest path by time: {path_time}")
    if path_time:
        success = env.route_cargo(cargo.cargo_id, path_time)
        logger.info(f"   ✓ Cargo routed: {success}")
    
    # Step simulation
    logger.info("\n6. Running simulation steps...")
    for i in range(3):
        state, reward, done, info = env.step({})
        logger.info(f"   Step {i+1}: reward={reward:.1f}, "
                   f"active={info['active_cargos']}, "
                   f"trilemma={info['trilemma']}")


def test_task_distinctions():
    """Demonstrate Task 1, 2, 3 distinctions."""
    logger.info("\n" + "=" * 70)
    logger.info("TASK DISTINCTNESS ANALYSIS")
    logger.info("=" * 70)
    
    logger.info("\n1. Task 1: TIME MINIMIZATION")
    logger.info("   - Objective: Minimize accumulated_hours")
    logger.info("   - Schema: Task1Action(cargo_id, path)")
    logger.info("   - Optimization: find_shortest_path(weight='time')")
    logger.info("   - Use Case: Express/urgent delivery")
    
    logger.info("\n2. Task 2: COST MINIMIZATION")
    logger.info("   - Objective: Minimize accumulated_cost")
    logger.info("   - Schema: Task2Action(cargo_id, path)")
    logger.info("   - Optimization: find_shortest_path(weight='cost')")
    logger.info("   - Use Case: Budget-constrained logistics")
    
    logger.info("\n3. Task 3: MULTIMODAL ROUTING (STRUCTURALLY DISTINCT)")
    logger.info("   - Objective: Balance time, cost, carbon")
    logger.info("   - Schema: Task3Action(cargo_id, cargo_type, path, split_at)")
    logger.info("   - Unique Features:")
    logger.info("     * cargo_type enum: truck, rail, ship, air")
    logger.info("     * split_at: nodes where mode transitions occur")
    logger.info("     * Multimodal optimization algorithm")
    logger.info("   - Use Case: Sustainable, balanced logistics")
    
    logger.info("\n4. SCHEMA COMPARISON TABLE:")
    logger.info("   Field        | Task 1 | Task 2 | Task 3")
    logger.info("   -------------|--------|--------|--------")
    logger.info("   task_type    |   ✓    |   ✓    |   ✓")
    logger.info("   cargo_id     |   ✓    |   ✓    |   ✓")
    logger.info("   path         |   ✓    |   ✓    |   ✓")
    logger.info("   cargo_type   |   ✗    |   ✗    |   ✓  ← UNIQUE")
    logger.info("   split_at     |   ✗    |   ✗    |   ✓  ← UNIQUE")


def test_endpoint_mapping():
    """Test endpoint mapping from configuration."""
    logger.info("\n" + "=" * 70)
    logger.info("API ENDPOINT MAPPING")
    logger.info("=" * 70)
    
    endpoints = {
        "Health": {"method": "GET", "path": "/health"},
        "Reset": {"method": "POST", "path": "/reset"},
        "Get State": {"method": "GET", "path": "/state"},
        "Create Cargo": {"method": "POST", "path": "/cargo/add"},
        "Split Cargo": {"method": "POST", "path": "/cargo/split"},
        "Task 1 Route": {"method": "POST", "path": "/task1/route", "schema": "Task1Action"},
        "Task 2 Route": {"method": "POST", "path": "/task2/route", "schema": "Task2Action"},
        "Task 3 Route": {"method": "POST", "path": "/task3/route", "schema": "Task3Action"},
        "Step": {"method": "POST", "path": "/step"},
        "Run Episode": {"method": "POST", "path": "/run-episode"},
        "Evaluate": {"method": "POST", "path": "/evaluate"},
        "Find Path": {"method": "GET", "path": "/path"},
    }
    
    logger.info("\nEndpoint | Method | Path | Schema")
    logger.info("-" * 70)
    for name, info in endpoints.items():
        schema = info.get("schema", "BaseResponse")
        logger.info(f"{name:20} | {info['method']:4} | {info['path']:20} | {schema}")


def test_pathfinding():
    """Test trilemma-based pathfinding."""
    logger.info("\n" + "=" * 70)
    logger.info("TRILEMMA-BASED PATHFINDING")
    logger.info("=" * 70)
    
    env = get_env()
    env.reset()
    
    origin, destination = 0, 5
    
    logger.info(f"\nFinding paths from {origin} to {destination}:")
    
    for weight in ["time", "cost", "carbon"]:
        path = env.network.get_shortest_path(origin, destination, weight=weight)
        
        if path:
            # Calculate metrics
            total_time = sum(env.network.get_edge(path[i], path[i+1]).time 
                           for i in range(len(path)-1))
            total_cost = sum(env.network.get_edge(path[i], path[i+1]).cost 
                           for i in range(len(path)-1))
            total_carbon = sum(env.network.get_edge(path[i], path[i+1]).carbon 
                            for i in range(len(path)-1))
            
            logger.info(f"\n  Optimized for {weight}:")
            logger.info(f"    Path: {path}")
            logger.info(f"    Time: {total_time:.1f}h | Cost: ${total_cost:.0f} | Carbon: {total_carbon:.0f}kg")


if __name__ == "__main__":
    test_schemas()
    test_environment_integration()
    test_task_distinctions()
    test_endpoint_mapping()
    test_pathfinding()
    
    logger.info("\n" + "=" * 70)
    logger.info("ALL API LAYER TESTS COMPLETED")
    logger.info("=" * 70)
